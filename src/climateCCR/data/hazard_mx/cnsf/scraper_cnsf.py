"""
scraper_cnsf.py
===============
Pipeline de ingesta de las "Bases de datos" del sector asegurador de la CNSF.
Orquesta DESDE ESTE main: verificación contra red, descarga incremental y
consolidación, según el modo elegido.

Fuente (SharePoint):
    .../InstitucionesSociedadesMutualistas/Paginas/DetalladaSeguros.aspx

MODOS (--modo)
--------------
  verificar  : consulta la red y reporta qué está nuevo/cambiado/igual.
               NO descarga ni consolida (dry-run).
  descargar  : verifica y descarga solo lo nuevo o lo cambiado. NO consolida.
  consolidar : solo consolida lo ya descargado (sin red).
  sync       : descargar + reconsolidar las categorías que cambiaron (default).

POR QUÉ NO HACE FALTA POST NI __VIEWSTATE
-----------------------------------------
El portal es SharePoint. El vínculo `javascript:__doPostBack(...)` de cada
categoría solo expande/ordena el grupo; NO trae datos. El HTML del servidor ya
incluye los enlaces DIRECTOS y ESTÁTICOS a cada archivo por año, p. ej.:
    .../AyA Bases/2024 Agricola Bases.xlsx
Flujo: GET de la página .aspx -> extraer <a> a .xls/.xlsx -> GET del binario.

DETECCIÓN DE CAMBIOS E INTEGRIDAD (SHA-256)
-------------------------------------------
  - Estado persistente en  <out_dir>/_estado.json  (acumulativo entre corridas):
    por archivo guarda sha256, bytes, tamaño reportado, Last-Modified/ETag, fecha.
  - Para decidir si bajar SIN descargar todo: se comparan señales baratas de red
    (tamaño del listado y, vía HEAD, Content-Length/Last-Modified/ETag) contra el
    estado previo. Tras descargar, el SHA-256 CONFIRMA si el contenido cambió.
  - Si un archivo cambió de contenido, la versión previa se archiva en
    <out_dir>/_versiones/<categoria>/  (retención/auditoría) antes de reemplazar.

DEPENDENCIAS
------------
    pip install requests beautifulsoup4         # descarga
    pip install pandas openpyxl xlrd            # solo si se consolida (modos sync/consolidar)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import random
import re
import shutil
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

import requests
from bs4 import BeautifulSoup

log = logging.getLogger("cnsf")

# --------------------------------------------------------------------------- #
# Configuración
# --------------------------------------------------------------------------- #

BASE = "https://www.cnsf.gob.mx"
URL_INDICE = (
    BASE
    + "/EntidadesSupervisadas/InstitucionesSociedadesMutualistas/Paginas/DetalladaSeguros.aspx"
)
EXTENSIONES_DATOS = (
    ".xlsx",
    ".xls",
    ".xlsm",
    ".xlsb",
    ".zip",
)  # .zip = bases MDB (autos)
ASPX_IGNORAR = {"detalladaseguros.aspx", "authenticate.aspx"}

# Categorías cuyo crudo es .zip/.mdb y se procesan con procesar_autos_cnsf
# (no con el consolidador de xlsx). El slug es _slug("Automóviles").
CATEGORIAS_MDB = {"automoviles"}

# Subsectores dentro de una categoría MDB: el patrón (en el nombre del archivo)
# es también el nombre de la subcarpeta en la que se descarga/organiza. Mantén
# estos patrones alineados con "subsectores" en catalogos_autos_cnsf.json.
SUBSECTORES_MDB = ("individual", "flotilla")

# Año de 4 dígitos delimitado por NO-dígitos. No usamos \b porque el guion bajo
# cuenta como carácter de palabra y rompería 'Autos_individual_2018'.
RE_ANIO = re.compile(r"(?<!\d)(19|20)\d{2}(?!\d)")
RE_TAMANO_KB = re.compile(r"([\d.,]+)\s*KB", re.IGNORECASE)

try:  # pragma: no cover
    import lxml  # noqa: F401

    _BS_PARSER = "lxml"
except Exception:  # pragma: no cover
    _BS_PARSER = "html.parser"


def _slug(texto: str) -> str:
    t = (
        str(texto)
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )
    t = re.sub(r"[^a-z0-9]+", "_", t).strip("_")
    return t or "x"


def _subsector_de(nombre: str) -> Optional[str]:
    """Devuelve el subsector ('individual'/'flotilla') según el nombre del archivo,
    o None si no aplica. El valor es también el nombre de la subcarpeta."""
    low = str(nombre).lower()
    for pat in SUBSECTORES_MDB:
        if pat in low:
            return pat
    return None


# --------------------------------------------------------------------------- #
# Modelo
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Categoria:
    nombre: str
    url: str

    @property
    def slug(self) -> str:
        return _slug(self.nombre)


@dataclass
class ArchivoCNSF:
    categoria: str
    categoria_slug: str
    anio: Optional[int]
    nombre_archivo: str
    url: str
    ext: str
    tamano_kb: Optional[float] = None

    def ruta_relativa(self) -> Path:
        base = Path(self.categoria_slug)
        if self.categoria_slug in CATEGORIAS_MDB:
            sub = _subsector_de(self.nombre_archivo)
            if sub:
                return base / sub / self.nombre_archivo
        return base / self.nombre_archivo

    def clave(self) -> str:
        return f"{self.categoria_slug}/{self.nombre_archivo}"


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #


def crear_sesion(contacto: str = "contacto@tu-org.mx") -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": f"Mozilla/5.0 (pipeline-agroclimatico CNSF; {contacto})",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-MX,es;q=0.9",
        }
    )
    return s


def _get(
    session: requests.Session,
    url: str,
    *,
    reintentos: int = 3,
    timeout: int = 120,
    stream: bool = False,
) -> requests.Response:
    ultimo: Optional[Exception] = None
    for intento in range(1, reintentos + 1):
        try:
            r = session.get(url, timeout=timeout, stream=stream, allow_redirects=True)
            r.raise_for_status()
            return r
        except Exception as e:  # noqa: BLE001
            ultimo = e
            espera = (2**intento) + random.random()
            log.warning(
                "GET falló (%d/%d) %s: %s; espero %.1fs",
                intento,
                reintentos,
                url,
                e,
                espera,
            )
            time.sleep(espera)
    assert ultimo is not None
    raise ultimo


def _head_meta(session: requests.Session, url: str, timeout: int = 30) -> dict:
    """Metadatos baratos del archivo remoto (sin bajar el cuerpo)."""
    try:
        r = session.head(url, timeout=timeout, allow_redirects=True)
        if r.status_code >= 400:
            return {}
        h = r.headers
        cl = h.get("Content-Length")
        return {
            "bytes": int(cl) if cl and cl.isdigit() else None,
            "last_modified": h.get("Last-Modified"),
            "etag": h.get("ETag"),
        }
    except Exception:  # noqa: BLE001
        return {}


def _descargar_a(
    session: requests.Session,
    url: str,
    tmp_path: Path,
    *,
    reintentos: int = 3,
    timeout: int = 300,
) -> tuple[int, str]:
    """Descarga `url` a `tmp_path` calculando el SHA-256 al vuelo.
    Devuelve (bytes_escritos, sha256_hex). Aislado para poder probarlo sin red."""
    h = hashlib.sha256()
    total = 0
    r = _get(session, url, reintentos=reintentos, timeout=timeout, stream=True)
    with open(tmp_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 16):
            if chunk:
                f.write(chunk)
                h.update(chunk)
                total += len(chunk)
    return total, h.hexdigest()


def _sha256_archivo(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalizar_url(href: str) -> str:
    from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit

    absoluta = urljoin(BASE + "/", href)
    p = urlsplit(absoluta)
    ruta = quote(unquote(p.path), safe="/%")
    return urlunsplit((p.scheme, p.netloc, ruta, p.query, ""))


# --------------------------------------------------------------------------- #
# Descubrimiento y parseo (verificado con test_scraper_cnsf.py)
# --------------------------------------------------------------------------- #


def descubrir_categorias(session, html: Optional[str] = None) -> list[Categoria]:
    if html is None:
        html = _get(session, URL_INDICE).text
    sopa = BeautifulSoup(html, _BS_PARSER)
    cats, vistos = [], set()
    for a in sopa.find_all("a", href=True):
        href = a["href"].strip()  # type: ignore
        low = href.lower()
        if "/paginas/" not in low or not low.endswith(".aspx"):
            continue
        if "institucionessociedadesmutualistas" not in low:
            continue
        nombre = a.get_text(strip=True)
        if not nombre or low.rsplit("/", 1)[-1] in ASPX_IGNORAR:
            continue
        url = _normalizar_url(href)
        if url in vistos:
            continue
        vistos.add(url)
        cats.append(Categoria(nombre=nombre, url=url))
    return cats


def _anio_de(nombre: str, texto_fila: str) -> Optional[int]:
    for fuente in (nombre, texto_fila):
        m = RE_ANIO.search(fuente or "")
        if m:
            return int(m.group(0))
    return None


def _tamano_kb_de(texto_fila: str) -> Optional[float]:
    m = RE_TAMANO_KB.search(texto_fila or "")
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def listar_archivos(
    session, cat: Categoria, html: Optional[str] = None
) -> list[ArchivoCNSF]:
    from urllib.parse import unquote, urlsplit

    if html is None:
        html = _get(session, cat.url).text
    sopa = BeautifulSoup(html, _BS_PARSER)
    archivos, vistos = [], set()
    for a in sopa.find_all("a", href=True):
        href = a["href"].strip()  # type: ignore
        if href.lower().startswith("javascript"):
            continue
        nombre = unquote(urlsplit(href).path.rsplit("/", 1)[-1])
        low = nombre.lower()
        ext = next((e for e in EXTENSIONES_DATOS if low.endswith(e)), None)
        if not ext:
            continue
        url = _normalizar_url(href)
        if url in vistos:
            continue
        vistos.add(url)
        fila = a.find_parent("tr")
        texto = fila.get_text(" ", strip=True) if fila else a.get_text(" ", strip=True)
        archivos.append(
            ArchivoCNSF(
                categoria=cat.nombre,
                categoria_slug=cat.slug,
                anio=_anio_de(nombre, texto),
                nombre_archivo=nombre,
                url=url,
                ext=ext,
                tamano_kb=_tamano_kb_de(texto),
            )
        )
    archivos.sort(key=lambda x: (-(x.anio or 0), x.nombre_archivo))
    return archivos


def _filtrar_categorias(
    todas: list[Categoria], pedidas: Optional[Iterable[str]]
) -> list[Categoria]:
    if not pedidas:
        return todas
    objetivos = {_slug(p) for p in pedidas}
    sel = [
        c for c in todas if c.slug in objetivos or any(o in c.slug for o in objetivos)
    ]
    # un objetivo "se encontró" si es igual a algún slug o substring de alguno
    encontrados = {
        o for o in objetivos if any(o == c.slug or o in c.slug for c in todas)
    }
    faltan = objetivos - encontrados
    if faltan:
        log.warning("Categorías no encontradas: %s", ", ".join(sorted(faltan)))
    return sel


def inventario_remoto(
    session,
    categorias: Optional[Iterable[str]] = None,
    anios: Optional[Iterable[int]] = None,
    crudos_dir: Optional[Path] = None,
    guardar_snapshot: bool = False,
) -> list[ArchivoCNSF]:
    """Lista TODOS los archivos disponibles en la red (con filtros opcionales)."""
    cats = _filtrar_categorias(descubrir_categorias(session), categorias)
    anios_set = {int(a) for a in anios} if anios else None
    if guardar_snapshot and crudos_dir:
        crudos_dir.mkdir(parents=True, exist_ok=True)
    inv: list[ArchivoCNSF] = []
    for cat in cats:
        r = _get(session, cat.url)
        if guardar_snapshot and crudos_dir:
            (crudos_dir / f"{cat.slug}.html").write_text(r.text, encoding="utf-8")
        archs = listar_archivos(session, cat, html=r.text)
        if anios_set is not None:
            archs = [a for a in archs if a.anio in anios_set]
        inv.extend(archs)
    return inv


# --------------------------------------------------------------------------- #
# Estado persistente (acumulativo entre corridas)
# --------------------------------------------------------------------------- #


def cargar_estado(out_dir: Path) -> dict:
    p = out_dir / "_estado.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            log.warning("No pude leer %s; arranco con estado vacío", p)
    return {}


def guardar_estado(out_dir: Path, estado: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "_estado.json").write_text(
        json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _sembrar_estado_local(arch: ArchivoCNSF, destino: Path) -> dict:
    """Crea una entrada de estado a partir de un archivo ya presente en disco."""
    return {
        "url": arch.url,
        "sha256": _sha256_archivo(destino),
        "bytes": destino.stat().st_size,
        "tamano_kb": arch.tamano_kb,
        "last_modified": None,
        "etag": None,
        "fecha": date.today().isoformat(),
    }


# --------------------------------------------------------------------------- #
# Decisión de cambio
# --------------------------------------------------------------------------- #


def evaluar(
    session, arch: ArchivoCNSF, estado: dict, out_dir: Path, forzar: bool
) -> tuple[bool, str, Optional[dict], Optional[dict]]:
    """
    Decide si hay que (re)descargar `arch`.
    Devuelve (descargar, motivo, prev, head):
      - prev : entrada de estado a usar (puede venir sembrada desde disco)
      - head : metadatos HEAD ya consultados (para no repetir la llamada)
    """
    destino = out_dir / arch.ruta_relativa()
    prev = estado.get(arch.clave())

    if forzar:
        return True, "forzado", prev, None
    if prev is None:
        if destino.exists():
            prev = _sembrar_estado_local(
                arch, destino
            )  # teníamos el archivo, no el estado
        else:
            return True, "nuevo", None, None

    motivos = []
    if (
        arch.tamano_kb is not None
        and prev.get("tamano_kb") is not None
        and round(arch.tamano_kb) != round(prev["tamano_kb"])
    ):
        motivos.append("kb")
    head = _head_meta(session, arch.url)
    if (
        head.get("bytes") is not None
        and prev.get("bytes") is not None
        and head["bytes"] != prev["bytes"]
    ):
        motivos.append("content-length")
    if (
        head.get("last_modified")
        and prev.get("last_modified")
        and head["last_modified"] != prev["last_modified"]
    ):
        motivos.append("last-modified")
    if head.get("etag") and prev.get("etag") and head["etag"] != prev["etag"]:
        motivos.append("etag")
    return (bool(motivos), "+".join(motivos) if motivos else "sin_cambio", prev, head)


# --------------------------------------------------------------------------- #
# Sincronización (descarga incremental con SHA-256 y versionado)
# --------------------------------------------------------------------------- #


@dataclass
class SyncResult:
    filas: list[dict] = field(default_factory=list)
    nuevos: int = 0
    cambiados: int = 0
    sin_cambio: int = 0
    errores: int = 0
    categorias_cambiadas: set = field(default_factory=set)


def _archivar_version(
    destino: Path, categoria_slug: str, sha_prev: Optional[str], out_dir: Path
) -> Path:
    vdir = out_dir / "_versiones" / categoria_slug
    vdir.mkdir(parents=True, exist_ok=True)
    sha8 = (sha_prev or "desconocido")[:8]
    dst = vdir / f"{destino.stem}.{date.today().isoformat()}.{sha8}{destino.suffix}"
    shutil.move(str(destino), str(dst))
    return dst


def _fila(
    arch: ArchivoCNSF, estado_str: str, motivo: str, meta: Optional[dict]
) -> dict:
    meta = meta or {}
    return {
        "categoria": arch.categoria,
        "categoria_slug": arch.categoria_slug,
        "anio": arch.anio,
        "nombre_archivo": arch.nombre_archivo,
        "url": arch.url,
        "ruta": str(arch.ruta_relativa()),
        "estado": estado_str,
        "motivo": motivo,
        "sha256": meta.get("sha256"),
        "bytes": meta.get("bytes"),
        "tamano_kb_reportado": arch.tamano_kb,
    }


def sincronizar(
    session,
    inventario: list[ArchivoCNSF],
    out_dir: Path,
    estado: dict,
    *,
    forzar: bool = False,
    pausa: float = 0.5,
    jitter: float = 0.5,
    versionar: bool = True,
) -> SyncResult:
    res = SyncResult()
    for i, arch in enumerate(inventario, 1):
        destino = out_dir / arch.ruta_relativa()
        descargar, motivo, prev, head = evaluar(session, arch, estado, out_dir, forzar)
        if prev is not None and arch.clave() not in estado:
            estado[arch.clave()] = prev  # persiste estado sembrado desde disco

        if not descargar:
            res.sin_cambio += 1
            res.filas.append(
                _fila(arch, "sin_cambio", motivo, estado.get(arch.clave()))
            )
            continue

        destino.parent.mkdir(parents=True, exist_ok=True)
        tmp = destino.with_suffix(destino.suffix + ".part")
        try:
            nbytes, sha = _descargar_a(session, arch.url, tmp)
        except Exception as e:  # noqa: BLE001
            res.errores += 1
            tmp.unlink(missing_ok=True)
            log.error("error %s: %s", arch.clave(), e)
            res.filas.append(_fila(arch, "error", str(e), None))
            continue

        if prev and sha == prev.get("sha256"):
            tmp.unlink(missing_ok=True)  # falsa alarma: contenido idéntico
            estado_str = "sin_cambio"
            res.sin_cambio += 1
        else:
            if destino.exists() and prev:
                if versionar:
                    v = _archivar_version(
                        destino, arch.categoria_slug, prev.get("sha256"), out_dir
                    )
                    log.info("versión previa archivada -> %s", v.name)
                estado_str = "cambiado"
                res.cambiados += 1
            else:
                estado_str = "nuevo"
                res.nuevos += 1
            tmp.replace(destino)
            res.categorias_cambiadas.add(arch.categoria_slug)
            log.info("%s %s (%.1f KB)", estado_str, arch.clave(), nbytes / 1024.0)

        meta = head if head is not None else _head_meta(session, arch.url)
        estado[arch.clave()] = {
            "url": arch.url,
            "sha256": sha,
            "bytes": nbytes,
            "tamano_kb": arch.tamano_kb,
            "last_modified": meta.get("last_modified"),
            "etag": meta.get("etag"),
            "fecha": date.today().isoformat(),
        }
        res.filas.append(_fila(arch, estado_str, motivo, estado[arch.clave()]))
        time.sleep(pausa + random.random() * jitter)
    return res


def escribir_manifest(res: SyncResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    from datetime import datetime

    manifest = {
        "fuente": "CNSF - Bases del sector asegurador",
        "fecha_ejecucion": datetime.now().isoformat(timespec="seconds"),
        "nuevos": res.nuevos,
        "cambiados": res.cambiados,
        "sin_cambio": res.sin_cambio,
        "errores": res.errores,
        "categorias_cambiadas": sorted(res.categorias_cambiadas),
        "archivos": res.filas,
    }
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info(
        "Manifest -> %s (nuevos=%d, cambiados=%d, sin_cambio=%d, errores=%d)",
        path,
        res.nuevos,
        res.cambiados,
        res.sin_cambio,
        res.errores,
    )


# --------------------------------------------------------------------------- #
# Orquestación
# --------------------------------------------------------------------------- #


def _imprimir_categorias(session) -> list[Categoria]:
    """Lista las categorías disponibles en el portal (nombre y slug exacto)."""
    cats = descubrir_categorias(session)
    log.info("Categorías disponibles (%d):", len(cats))
    for c in cats:
        log.info("  %-42s slug=%s", c.nombre, c.slug)
    log.info("Úsalas con --categorias (acepta el slug o parte del nombre).")
    return cats


def _reporte_verificacion(session, inventario, estado, out_dir) -> dict:
    filas = []
    n_nuevos = n_cambio = n_igual = 0
    for arch in inventario:
        descargar, motivo, prev, _ = evaluar(
            session, arch, estado, out_dir, forzar=False
        )
        if descargar and prev is None:
            etiqueta = "nuevo"
            n_nuevos += 1
        elif descargar:
            etiqueta = "cambiado"
            n_cambio += 1
        else:
            etiqueta = "sin_cambio"
            n_igual += 1
        filas.append({"clave": arch.clave(), "estado": etiqueta, "motivo": motivo})
    log.info(
        "Verificación: nuevos=%d, cambiados=%d, sin_cambio=%d (total=%d)",
        n_nuevos,
        n_cambio,
        n_igual,
        len(inventario),
    )
    for f in filas:
        if f["estado"] != "sin_cambio":
            log.info("  [%s] %s (%s)", f["estado"], f["clave"], f["motivo"])
    return {
        "nuevos": n_nuevos,
        "cambiados": n_cambio,
        "sin_cambio": n_igual,
        "detalle": filas,
    }


def _consolidar(
    out_dir: Path,
    consol_dir: Path,
    categorias,
    *,
    aliases,
    estricto,
    xlsx_si_cabe,
    compresion="none",
):
    try:
        import consolidar_cnsf
    except ImportError:
        log.error(
            "No encuentro consolidar_cnsf.py (ponlo junto a este script). "
            "Instala además: pip install pandas openpyxl xlrd"
        )
        raise
    return consolidar_cnsf.consolidar(
        out_dir,
        consol_dir,
        categorias=categorias,
        aliases=aliases,
        estricto=estricto,
        xlsx_si_cabe=xlsx_si_cabe,
        compresion=compresion,
    )


def _procesar_autos(
    out_dir: Path, consol_dir: Path, *, autos_config, compresion="none"
):
    """Procesa las categorías MDB (autos): descomprime .zip, lee .mdb y consolida."""
    try:
        import procesar_autos_cnsf
    except ImportError:
        log.error(
            "No encuentro procesar_autos_cnsf.py (ponlo junto a este script). "
            "Requiere mdbtools en el PATH y: pip install pandas"
        )
        raise
    cfg_path = Path(autos_config)
    if not cfg_path.exists():
        log.error("No encuentro la config de autos: %s", cfg_path)
        raise FileNotFoundError(cfg_path)
    config = json.loads(cfg_path.read_text(encoding="utf-8"))
    resultados = []
    for slug in sorted(CATEGORIAS_MDB):
        root = out_dir / slug
        if not root.exists():
            continue
        log.info("Procesando categoría MDB '%s' (autos)…", slug)
        resultados.append(
            procesar_autos_cnsf.procesar(
                root, consol_dir, config, compresion=compresion
            )
        )
    return resultados


def _es_token_autos(token: str) -> bool:
    """True si un token (slug exacto de sync, o filtro parcial de consolidar)
    apunta a una categoría MDB como 'automoviles'."""
    s = _slug(token)
    return any(s == cat or s in cat or cat in s for cat in CATEGORIAS_MDB)


def _despachar(
    cats,
    out_dir: Path,
    consol_dir: Path,
    *,
    aliases,
    estricto,
    xlsx_si_cabe,
    autos_config,
    compresion,
):
    """Enruta categorías a su procesador: xlsx -> consolidar_cnsf; MDB(autos) -> procesar_autos.

    `cats` = None significa "todas". Para 'todas', el consolidador de xlsx ignora
    autos por sí solo (no halla .xlsx) y el procesador de autos corre si existe la
    carpeta. Para una lista (slugs exactos de sync o filtros parciales de
    consolidar), se separa lo que apunta a autos del resto.
    """
    if cats is None:
        _consolidar(
            out_dir,
            consol_dir,
            None,
            aliases=aliases,
            estricto=estricto,
            xlsx_si_cabe=xlsx_si_cabe,
            compresion=compresion,
        )
        _procesar_autos(
            out_dir, consol_dir, autos_config=autos_config, compresion=compresion
        )
        return
    autos = [c for c in cats if _es_token_autos(c)]
    xlsx = [c for c in cats if not _es_token_autos(c)]
    if xlsx:
        _consolidar(
            out_dir,
            consol_dir,
            xlsx,
            aliases=aliases,
            estricto=estricto,
            xlsx_si_cabe=xlsx_si_cabe,
            compresion=compresion,
        )
    if autos:
        _procesar_autos(
            out_dir, consol_dir, autos_config=autos_config, compresion=compresion
        )


def main():
    ap = argparse.ArgumentParser(
        description="Pipeline CNSF (verificar/descargar/consolidar/sync)"
    )
    ap.add_argument(
        "--modo",
        choices=["sync", "descargar", "consolidar", "verificar"],
        default="sync",
    )
    ap.add_argument(
        "--categorias",
        nargs="*",
        help="enfoca a un subconjunto (nombre o slug; coincidencia parcial). "
        "Aplica a verificar/descargar/sync/consolidar. Default: todas",
    )
    ap.add_argument(
        "--listar-categorias",
        action="store_true",
        help="imprime las categorías disponibles (nombre y slug) y termina",
    )
    ap.add_argument(
        "--anios", nargs="*", type=int, help="filtra por año. Default: todos"
    )
    ap.add_argument(
        "--out-dir", default="datos/datos_CNSF/crudos", help="carpeta de Excel crudos"
    )
    ap.add_argument(
        "--crudos-dir",
        default="datos/datos_CNSF/crudos_snapshots",
        help="snapshots HTML de listados",
    )
    ap.add_argument("--consol-out-dir", default="datos/datos_CNSF/consolidados")
    # descarga
    ap.add_argument(
        "--forzar", action="store_true", help="re-descarga aunque no haya cambios"
    )
    ap.add_argument("--pausa", type=float, default=0.5)
    ap.add_argument("--no-snapshot", action="store_true")
    ap.add_argument(
        "--no-versionar",
        action="store_true",
        help="no archivar la versión previa al reemplazar un archivo cambiado",
    )
    ap.add_argument("--contacto", default="contacto@tu-org.mx")
    # consolidación (pass-through)
    ap.add_argument(
        "--estricto",
        action="store_true",
        help="consolidar descartando columnas solo-históricas",
    )
    ap.add_argument("--xlsx-si-cabe", action="store_true")
    ap.add_argument(
        "--aliases",
        default="src/aliases_cnsf.json",
        help="JSON {clave_normalizada: clave_canonica} para consolidar",
    )
    ap.add_argument(
        "--comprimir",
        choices=["none", "gzip", "bz2", "xz"],
        default="none",
        help="comprime los CSV de salida (xlsx y autos). Recomendado: gzip",
    )
    ap.add_argument(
        "--autos-config",
        default="src/catalogos_autos_cnsf.json",
        help="config de catálogos/uniones para el procesador de autos",
    )
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    out_dir = Path(args.out_dir)
    consol_dir = Path(args.consol_out_dir)
    aliases = (
        json.loads(Path(args.aliases).read_text(encoding="utf-8"))
        if args.aliases
        else None
    )

    # --- listar categorías y salir (requiere red) ---
    if args.listar_categorias:
        _imprimir_categorias(crear_sesion(contacto=args.contacto))
        return

    # --- consolidar: sin red ---
    if args.modo == "consolidar":
        _despachar(
            args.categorias,
            out_dir,
            consol_dir,
            aliases=aliases,
            estricto=args.estricto,
            xlsx_si_cabe=args.xlsx_si_cabe,
            autos_config=args.autos_config,
            compresion=args.comprimir,
        )
        log.info("Listo (consolidar).")
        return

    # --- modos con red ---
    session = crear_sesion(contacto=args.contacto)
    crudos = Path(args.crudos_dir) / date.today().isoformat()
    estado = cargar_estado(out_dir)
    inventario = inventario_remoto(
        session,
        categorias=args.categorias,
        anios=args.anios,
        crudos_dir=crudos,
        guardar_snapshot=not args.no_snapshot,
    )
    log.info("Inventario remoto: %d archivo(s)", len(inventario))

    if args.modo == "verificar":
        rep = _reporte_verificacion(session, inventario, estado, out_dir)
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        (out_dir / f"cnsf_verificacion_{date.today().isoformat()}.json").write_text(
            json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        log.info("Listo (verificar). No se descargó ni consolidó nada.")
        return

    # descargar / sync
    res = sincronizar(
        session,
        inventario,
        out_dir,
        estado,
        forzar=args.forzar,
        pausa=args.pausa,
        versionar=not args.no_versionar,
    )
    guardar_estado(out_dir, estado)
    escribir_manifest(res, out_dir / f"cnsf_manifest_{date.today().isoformat()}.json")

    if args.modo == "sync":
        cats = sorted(res.categorias_cambiadas)
        if not cats:
            log.info("Sin cambios: no hay nada que reconsolidar.")
        else:
            log.info("Reprocesando categorías con cambios: %s", ", ".join(cats))
            _despachar(
                cats,
                out_dir,
                consol_dir,
                aliases=aliases,
                estricto=args.estricto,
                xlsx_si_cabe=args.xlsx_si_cabe,
                autos_config=args.autos_config,
                compresion=args.comprimir,
            )
    log.info("Listo (%s).", args.modo)


if __name__ == "__main__":
    main()
