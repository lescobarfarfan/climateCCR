"""
descarga_cenapred.py
====================
Descarga los datos CRUDOS del impacto socioeconómico de desastres de CENAPRED y
registra su PROCEDENCIA para reproducibilidad total (mismo patrón que CNSF/IBTrACS).

Fuentes:
  1) Base abierta a NIVEL EVENTO (machine-readable), 2000-2015:
     https://www.cenapred.unam.mx/DatosAbiertos/BASE_IMPACTO_SOCIOECONOMICO_DESASTRES_2000_2015.csv
  2) Resúmenes ejecutivos anuales (PDF), 2016+ (datos posteriores al CSV):
     https://www.cenapred.gob.mx/es/Publicaciones/archivos/{NNN}-RESUMENEJECUTIVOIMPACTO{AAAA}.PDF
     (la numeración NNN varía por año; se descubre desde la página de publicaciones)

Diseño:
  datos/datos_CENAPRED/
    crudos/                          <- NUNCA se modifica
      BASE_IMPACTO_SOCIOECONOMICO_DESASTRES_2000_2015.csv
      RESUMENEJECUTIVOIMPACTO2016.pdf ... 2024.pdf (los que existan)
      _procedencia.json              <- manifiesto reproducible (URL, sha256, fecha, bytes)
    consolidados/                    <- salidas de procesar_cenapred.py
  _log_cenapred.log                  <- log de control de cada corrida

Modos (como scraper_cnsf.py):
  --modo sync      : descubre lo disponible, descarga SOLO lo faltante/cambiado
  --modo verificar : compara checksums locales vs _procedencia.json (sin red)
  --modo descargar : re-descarga todo (--force)

Nota de entorno: cenapred.unam.mx / cenapred.gob.mx pueden estar bloqueados en el
sandbox de desarrollo; la descarga real se corre en la máquina del usuario (igual que CNSF).
"""

from __future__ import annotations
import argparse
import hashlib
import json
import logging
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ----------------------------------------------------------------------------- #
# Configuración
# ----------------------------------------------------------------------------- #
URL_CSV = ("https://www.cenapred.unam.mx/DatosAbiertos/"
           "BASE_IMPACTO_SOCIOECONOMICO_DESASTRES_2000_2015.csv")

# Páginas donde se listan las publicaciones (para descubrir PDFs nuevos).
# La 1ª es un ÍNDICE APACHE navegable (descubre TODO por regex); las demás, respaldo.
PAGINAS_PUBLICACIONES = [
    "https://olmeca.cenapred.unam.mx/es/Publicaciones/archivos/",
    "https://www.cenapred.gob.mx/es/Publicaciones/",
]

# --- RESÚMENES EJECUTIVOS con URL verificada (semilla; sync puede descubrir más). ---
# 2016-2021 verificados manualmente por el usuario; 2022-2023 verificados en búsqueda.
# Nota: conviven varios dominios (cenapred.unam.mx, olmeca.cenapred.unam.mx,
# cenapred.gob.mx); olmeca expone además el índice completo del directorio.
PDFS_CONOCIDOS = {
    2016: "https://www.cenapred.unam.mx/es/Publicaciones/archivos/368-RESUMENEJECUTIVOIMPACTO2016.PDF",
    2017: "https://www.cenapred.unam.mx/es/Publicaciones/archivos/403-NO.19-RESUMENEJECUTIVOIMPACTO2017.PDF",
    2018: "https://olmeca.cenapred.unam.mx/es/Publicaciones/archivos/409-RESUMENEJECUTIVOIMPACTO2018.PDF",
    2019: "https://www.cenapred.unam.mx/es/Publicaciones/archivos/429-RESUMENEJECUTIVOIMPACTO2019.PDF",
    2020: "https://www.cenapred.gob.mx/es/Publicaciones/archivos/455-RESUMENEJECUTIVOIMPACTO2020.PDF",
    2021: "https://www.cenapred.unam.mx/es/Publicaciones/archivos/487-RESUMENEJECUTIVOIMPACTO2021.PDF",
    2022: "https://www.cenapred.gob.mx/es/Publicaciones/archivos/494-RESUMENEJECUTIVOIMPACTO2022.pdf",
    2023: "https://www.cenapred.gob.mx/es/Publicaciones/archivos/504-RESUMENEJECUTIVOIMPACTO2023.PDF",
}

# --- DOCUMENTOS EXTENSOS (volúmenes completos) con URL verificada. ---
# 2016-2021 verificados manualmente por el usuario; 2022 verificado en el índice olmeca.
# Estos traen el detalle por fenómeno/evento/estado que los resúmenes NO tienen
# (los resúmenes 2019+ solo dan porcentajes de los estados top y agrupan "otros").
EXTENSOS_CONOCIDOS = {
    2016: "https://www.cenapred.gob.mx/es/Publicaciones/archivos/384-IMPACTO2016OEFINAL12FEBRERO2018.PDF",
    2017: "https://www.cenapred.unam.mx/es/Publicaciones/archivos/415-IMPACTO_SOCIOECONOMICO_2017.PDF",
    2018: "https://www.cenapred.gob.mx/es/Publicaciones/archivos/430-IMPACTO_SOCIOECONOMICO_2018.PDF",
    2019: "https://www.cenapred.gob.mx/es/Publicaciones/archivos/457-IMPACTO_SOCIOECONOMICO_2019.PDF",
    2020: "https://www.cenapred.gob.mx/es/Publicaciones/archivos/482-IMPACTO_SOCIOECONOMICO_2020.PDF",
    2021: "https://www.cenapred.unam.mx/es/Publicaciones/archivos/493-IMPACTO_SOCIOECONOMICO_2021.PDF",
    2022: "https://www.cenapred.gob.mx/es/Publicaciones/archivos/501-IMPACTO_SOCIOECONOMICO_2022.PDF",
    2023: "https://www.cenapred.gob.mx/es/Publicaciones/archivos/517-IMPACTO_SOCIOECONOMICO_2023.PDF",
    # Serie de extensos 2016-2023 COMPLETA (URLs verificadas por el usuario).
    # Hueco real: solo 2024 (sin extenso publicado aún; el sync lo detectará).
    # Nota: cada archivo suele existir espejado en los tres dominios, pero cada dominio
    # bloquea rutas distintas (403) -> _get_con_espejos prueba los espejos en orden.
    # El acervo COMPLETO existe como archivos.zip (4.5 GB) en el índice olmeca, último recurso.
}

# Regex de descubrimiento sobre las páginas/índices: captura resúmenes y extensos.
RE_PDF_IMPACTO = re.compile(
    r'href="([^"]*?(?:RESUMENEJECUTIVOIMPACTO|IMPACTO_?SOCIOECON[A-Z_]*?)[\-_]?(\d{4})\.(?:pdf|PDF))"')

DIR_BASE = Path("datos/datos_CENAPRED")
DIR_CRUDOS = DIR_BASE / "crudos"
ARCHIVO_LOG = DIR_BASE / "_log_cenapred.log"
ARCHIVO_PROCEDENCIA = DIR_CRUDOS / "_procedencia.json"

REINTENTOS = 3
ESPERA_SEG = 5
TIMEOUT = 120
UA = "Mozilla/5.0 (proyecto académico; descarga reproducible CENAPRED)"

log = logging.getLogger("descarga_cenapred")

# --- Contexto SSL ---------------------------------------------------------- #
# macOS: el Python de python.org NO usa los certificados del sistema -> usar
# certifi si está instalado (pip install certifi) o correr una vez
# "/Applications/Python 3.x/Install Certificates.command".
# Además, algunos servidores de gobierno (CENAPRED incluido) sirven la cadena
# de certificados INCOMPLETA; en ese caso ni certifi basta. Para eso existe la
# bandera explícita --inseguro: deshabilita la verificación SOLO bajo decisión
# del usuario, con advertencia en el log; la integridad del archivo queda
# compensada por el sha256 que se registra en _procedencia.json.
import ssl  # noqa: E402

VERIFICAR_SSL = True  # se apaga solo con --inseguro


def _contexto_ssl() -> ssl.SSLContext:
    if not VERIFICAR_SSL:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def configurar_log():
    DIR_BASE.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(ARCHIVO_LOG, encoding="utf-8"),
                  logging.StreamHandler(sys.stdout)])


# ----------------------------------------------------------------------------- #
# Utilidades
# ----------------------------------------------------------------------------- #
def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _get(url: str) -> bytes:
    """GET con reintentos y backoff (patrón del scraper SIAP/CNSF)."""
    ultimo_error = None
    for intento in range(1, REINTENTOS + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=TIMEOUT,
                                        context=_contexto_ssl()) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            ultimo_error = e
            log.warning("intento %d/%d falló para %s: %s", intento, REINTENTOS, url, e)
            if "CERTIFICATE_VERIFY_FAILED" in str(e):
                log.warning(
                    "SUGERENCIA: (1) instalar certifi (`pip install certifi`) o, en macOS, "
                    "correr 'Install Certificates.command' del instalador de Python; "
                    "(2) si persiste (cadena incompleta del servidor de gobierno), "
                    "re-correr con --inseguro: deshabilita la verificación SSL de forma "
                    "EXPLÍCITA; la integridad se valida después con el sha256 de "
                    "_procedencia.json (modo verificar).")
                break  # reintentar no resuelve un error de certificado
            if any(f"Error {c}" in str(e) for c in (403, 404, 410)):
                break  # error definitivo del servidor: reintentar no lo resuelve
            time.sleep(ESPERA_SEG * intento)
    raise RuntimeError(f"No se pudo descargar {url}: {ultimo_error}")


# Los mismos archivos suelen estar espejados en los tres dominios CENAPRED,
# pero cada dominio bloquea rutas distintas con 403 (visto en corrida real:
# olmeca sirve su índice y los PDFs antiguos pero bloquea 501-...2022;
# gob.mx sirve los PDFs pero bloquea su página de listado).
ESPEJOS = ["www.cenapred.gob.mx", "www.cenapred.unam.mx", "olmeca.cenapred.unam.mx"]


def _urls_espejo(url: str) -> list[str]:
    """URL original primero; luego el mismo path en los demás dominios espejo."""
    from urllib.parse import urlsplit, urlunsplit
    p = urlsplit(url)
    if p.netloc not in ESPEJOS:
        return [url]
    otros = [h for h in ESPEJOS if h != p.netloc]
    return [url] + [urlunsplit((p.scheme, h, p.path, p.query, p.fragment)) for h in otros]


def _get_con_espejos(url: str) -> tuple[bytes, str]:
    """Intenta la URL y, si falla, los espejos. Devuelve (datos, url_efectiva)."""
    ultimo = None
    for u in _urls_espejo(url):
        try:
            datos = _get(u)
            if u != url:
                log.info("descargado desde espejo: %s", u)
            return datos, u
        except RuntimeError as e:
            ultimo = e
    raise ultimo


def cargar_procedencia() -> dict:
    if ARCHIVO_PROCEDENCIA.exists():
        return json.loads(ARCHIVO_PROCEDENCIA.read_text(encoding="utf-8"))
    return {"fuente": "CENAPRED — Impacto socioeconómico de los desastres en México",
            "metodologia": "Basada en la metodología DaLA de la CEPAL, adaptada por CENAPRED",
            "archivos": {}}


def guardar_procedencia(proc: dict):
    proc["fecha_actualizacion_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ARCHIVO_PROCEDENCIA.write_text(json.dumps(proc, indent=2, ensure_ascii=False),
                                   encoding="utf-8")
    log.info("procedencia escrita en %s", ARCHIVO_PROCEDENCIA)


# ----------------------------------------------------------------------------- #
# Descubrimiento de PDFs (actualización)
# ----------------------------------------------------------------------------- #
def descubrir_pdfs() -> dict[str, str]:
    """
    Devuelve {clave: url} de publicaciones de impacto, con clave 'resumen_{año}' o
    'extenso_{año}', combinando las semillas verificadas con lo descubierto en los
    índices/páginas de publicaciones (el índice Apache de olmeca lista TODO el
    directorio, así que un año nuevo o un extenso faltante se detecta solo).
    Si una página no es accesible, se usan solo las semillas (queda en el log).
    """
    encontrados = {f"resumen_{a}": u for a, u in PDFS_CONOCIDOS.items()}
    encontrados.update({f"extenso_{a}": u for a, u in EXTENSOS_CONOCIDOS.items()})
    for pagina in PAGINAS_PUBLICACIONES:
        try:
            html = _get(pagina).decode("utf-8", errors="replace")
            base = pagina if pagina.endswith("/") else pagina + "/"
            for m in RE_PDF_IMPACTO.finditer(html):
                url, anio = m.group(1), int(m.group(2))
                if not url.startswith("http"):
                    url = (base + url) if not url.startswith("/") else \
                          "/".join(pagina.split("/")[:3]) + url
                tipo = "resumen" if "RESUMENEJECUTIVO" in url.upper() else "extenso"
                clave = f"{tipo}_{anio}"
                if clave not in encontrados:
                    log.info("descubierto %s nuevo: %d -> %s", tipo, anio, url)
                    encontrados[clave] = url
        except Exception as e:  # noqa: BLE001
            log.warning("no se pudo leer %s (%s); se usan semillas", pagina, e)
    return dict(sorted(encontrados.items()))


# ----------------------------------------------------------------------------- #
# Descarga
# ----------------------------------------------------------------------------- #
def descargar_archivo(url: str, destino: Path, proc: dict, clave: str,
                      force: bool = False) -> bool:
    """Descarga un archivo si falta o si force. Actualiza procedencia. True si descargó."""
    if destino.exists() and not force:
        log.info("ya existe, se omite: %s", destino.name)
        # asegura que esté en procedencia aunque no se rebaje
        if clave not in proc["archivos"]:
            proc["archivos"][clave] = {
                "nombre": destino.name, "url": url,
                "sha256": _sha256(destino), "bytes": destino.stat().st_size,
                "fecha_descarga_utc": None}
        return False
    log.info("descargando %s ...", url)
    datos, url_efectiva = _get_con_espejos(url)
    destino.write_bytes(datos)
    proc["archivos"][clave] = {
        "nombre": destino.name, "url": url, "url_efectiva": url_efectiva,
        "sha256": _sha256(destino), "bytes": destino.stat().st_size,
        "fecha_descarga_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    log.info("guardado %s (%d bytes, sha256=%s...)", destino.name,
             len(datos), proc["archivos"][clave]["sha256"][:12])
    return True


def modo_sync(force: bool = False):
    DIR_CRUDOS.mkdir(parents=True, exist_ok=True)
    proc = cargar_procedencia()
    # 1) CSV abierto (nivel evento, 2000-2015)
    destino_csv = DIR_CRUDOS / "BASE_IMPACTO_SOCIOECONOMICO_DESASTRES_2000_2015.csv"
    descargar_archivo(URL_CSV, destino_csv, proc, "csv_2000_2015", force=force)
    # 2) Resúmenes ejecutivos y documentos extensos (2016+)
    pdfs = descubrir_pdfs()
    nuevos = 0
    for clave, url in pdfs.items():
        destino = DIR_CRUDOS / f"{clave.upper()}.pdf"   # p. ej. EXTENSO_2021.pdf
        if descargar_archivo(url, destino, proc, clave, force=force):
            nuevos += 1
    guardar_procedencia(proc)
    log.info("sync terminado: %d publicaciones en catálogo (%d resúmenes, %d extensos), "
             "%d descargadas ahora",
             len(pdfs), sum(k.startswith("resumen") for k in pdfs),
             sum(k.startswith("extenso") for k in pdfs), nuevos)


def modo_verificar() -> bool:
    """Compara checksums locales contra _procedencia.json (sin red). True si todo OK."""
    proc = cargar_procedencia()
    ok = True
    for clave, info in proc.get("archivos", {}).items():
        destino = DIR_CRUDOS / info["nombre"]
        if not destino.exists():
            log.error("FALTA archivo registrado: %s", info["nombre"])
            ok = False
            continue
        sha = _sha256(destino)
        if sha != info["sha256"]:
            log.error("CHECKSUM DIFIERE: %s (local %s... vs registrado %s...)",
                      info["nombre"], sha[:12], info["sha256"][:12])
            ok = False
        else:
            log.info("OK: %s", info["nombre"])
    log.info("verificación %s", "EXITOSA" if ok else "CON ERRORES")
    return ok


if __name__ == "__main__":
    configurar_log()
    p = argparse.ArgumentParser()
    p.add_argument("--modo", choices=["sync", "verificar", "descargar"], default="sync")
    p.add_argument("--inseguro", action="store_true",
                   help="deshabilita la verificación SSL (solo si el servidor sirve la "
                        "cadena de certificados incompleta; la integridad se compensa "
                        "con el sha256 de _procedencia.json)")
    a = p.parse_args()
    if a.inseguro:
        VERIFICAR_SSL = False
        log.warning("=" * 70)
        log.warning("VERIFICACIÓN SSL DESHABILITADA (--inseguro) por decisión del usuario.")
        log.warning("Causa típica: cadena de certificados incompleta del servidor.")
        log.warning("Compensación: validar integridad con `--modo verificar` (sha256).")
        log.warning("=" * 70)
    if a.modo == "verificar":
        sys.exit(0 if modo_verificar() else 1)
    modo_sync(force=(a.modo == "descargar"))
