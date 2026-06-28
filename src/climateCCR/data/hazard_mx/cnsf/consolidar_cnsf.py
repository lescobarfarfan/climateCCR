"""
consolidar_cnsf.py
==================
Consolida las bases de la CNSF descargadas por `scraper_cnsf.py`: une TODOS los
años de UNA categoría en un CSV por cada hoja de datos (Emisión / Suma Asegurada
/ Siniestros), manejando los cambios de estructura a lo largo del tiempo, y corre
una VERIFICACIÓN post-consolidación.

Salida: <out_dir>/<categoria>/<hoja>.csv  +  <out_dir>/<categoria>/_reporte.json
        +  <out_dir>/reporte_consolidacion.json (resumen global)

QUÉ SE CORRIGIÓ / AÑADIÓ EN ESTA VERSIÓN
----------------------------------------
1. FUSIÓN DE HOJAS POR NOMBRE NORMALIZADO. Antes, "Emisión" (años viejos) y
   "Emision" (años recientes) se trataban como hojas distintas y AMBAS escribían
   `emision.csv`, una sobreescribiendo a la otra (pérdida de datos). Ahora las
   hojas se agrupan por nombre normalizado (sin acentos / espacios), así todos
   los años de "emision/emisión" se consolidan juntos.

2. VERIFICACIÓN POST-CONSOLIDACIÓN (sección `validaciones` del reporte):
   - reconciliación de filas (suma por año == total),
   - columnas canónicas que quedaron 100% vacías (posible desalineación/parsing),
   - columnas sin encabezado,
   - posibles columnas duplicadas por typo/variante (sugerencias de alias),
   - columnas de MEDIDA con valores no numéricos (posible error de lectura),
   - colisión de archivos de salida.

3. ALIAS POR ÁMBITO para fusionar variantes de encabezado (typos). El JSON puede
   ser plano (global) o por ámbito: claves "_global", "<categoria>", o
   "<categoria>/<hoja>". Ver `aliases_cnsf.json` de ejemplo.

4. LIMPIEZA OPCIONAL DE ENCABEZADOS (--limpiar-encabezados): colapsa saltos de
   línea y espacios dobles en los nombres de columna de salida (mejor para Power
   Query). El emparejamiento entre años NO depende de esto (usa la clave
   normalizada), solo cambia el texto del encabezado del CSV.

DEPENDENCIAS:  pip install pandas openpyxl xlrd
"""

from __future__ import annotations

import argparse
import difflib
import json
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

log = logging.getLogger("cnsf.consolidar")

HOJAS_IGNORAR = {"indice"}                 # glosario (normalizado: sin acentos)
PROVENANCIA = ["categoria", "anio", "archivo_origen"]
RE_ANIO = re.compile(r"(?<!\d)(19|20)\d{2}(?!\d)")  # no \b: el '_' rompería el match
MAX_FILAS_XLSX = 1_048_575

# Métodos de compresión soportados por pandas.to_csv -> sufijo de archivo.
EXT_COMPRESION = {"none": "", "gzip": ".gz", "bz2": ".bz2", "xz": ".xz", "zstd": ".zst"}

# Correcciones de typos en los encabezados canónicos (los del año más reciente).
# CLAVE = forma normalizada (clave_col) del encabezado canónico con typo.
# VALOR = nombre corregido tal cual debe salir (puede llevar acentos y mayúsculas).
# Se aplica a la salida tras emparejar/aliasar, así que no afecta el emparejamiento.
CORRECCIONES_CANONICAS = {
    "MONTO DEL SINIESTRO OCOURRIDO": "MONTO DEL SINIESTRO OCURRIDO",   # 2024 trae 'OCOURRIDO'
    # Para corregir más, agrega aquí  "<clave_col del canónico>": "Nombre corregido".
    # Ejemplo (descomenta si quieres que la salida diga 'GIRO DE LA UBICACIÓN'):
    # "GIRO LA UBICACION": "GIRO DE LA UBICACIÓN",
}

# Palabras que delatan una columna de MEDIDA (debe ser numérica).
RE_MEDIDA = re.compile(
    r"PRIMA|MONTO|SUMA ASEGURADA|GASTO|SALVAMENTO|COMISI|DEDUCIBLE|COASEGURO|"
    r"REASEGURO|RECUPERAC|VALORES TOTALES|LIMITE MAXIMO|SUPERFICIE|UNIDADES|"
    r"NUMERO DE")


def _sin_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(s))
                   if not unicodedata.combining(c))


def clave_col(nombre) -> str:
    """Clave estable para emparejar columnas/hojas entre años."""
    s = _sin_acentos("" if nombre is None else str(nombre)).upper()
    s = re.sub(r"\s+", " ", s).strip().rstrip(".")
    return s


def _slug(texto: str) -> str:
    t = _sin_acentos(str(texto)).lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_") or "x"


def _limpiar_encabezado(nombre: str) -> str:
    return re.sub(r"\s+", " ", str(nombre)).strip()


def _corregir_encabezado(nombre: str) -> str:
    """Corrige typos conocidos del encabezado canónico (ver CORRECCIONES_CANONICAS)."""
    return CORRECCIONES_CANONICAS.get(clave_col(nombre), nombre)


# --------------------------------------------------------------------------- #
# Lectura de hojas
# --------------------------------------------------------------------------- #

def _motor(path: Path) -> str:
    return "xlrd" if path.suffix.lower() == ".xls" else "openpyxl"


def _detectar_encabezado(crudo: pd.DataFrame, max_scan: int = 8) -> int:
    mejor_i, mejor_n = 0, -1
    for i in range(min(max_scan, len(crudo))):
        n = crudo.iloc[i].notna().sum()
        if n > mejor_n:
            mejor_i, mejor_n = i, n
    return mejor_i


def _resolver_hoja(path: Path, hoja_key: str) -> Optional[str]:
    """Nombre real de la hoja en `path` cuyo nombre normalizado == hoja_key."""
    xls = pd.ExcelFile(path, engine=_motor(path)) # type: ignore
    for h in xls.sheet_names:
        if clave_col(h) == hoja_key:
            return h # type: ignore
    return None


def _unicos(nombres: list[str]) -> list[str]:
    """Hace únicas las etiquetas repetidas añadiendo sufijo ' (2)', ' (3)'…
    Evita que df[etiqueta] devuelva un DataFrame (causa de errores aguas abajo)."""
    vistos: dict[str, int] = {}
    out = []
    for n in nombres:
        if n in vistos:
            vistos[n] += 1
            out.append(f"{n} ({vistos[n]})")
        else:
            vistos[n] = 1
            out.append(n)
    return out


def _col_vacia(col: pd.Series) -> bool:
    """True si la columna no tiene datos reales: todo NaN o solo espacios en blanco."""
    return bool(col.map(lambda v: pd.isna(v) or str(v).strip() == "").all())


def leer_hoja(path: Path, hoja: str) -> Optional[pd.DataFrame]:
    """Lee la hoja `hoja` con encabezados reales, sin filas ni columnas vacías.

    Robusto ante encabezados DUPLICADOS (p. ej. varias columnas en blanco): la
    selección de columnas se hace por POSICIÓN y los nombres finales se hacen
    únicos, para no romper con 'truth value of a Series is ambiguous'. Las columnas
    SIN encabezado que solo tienen NaN o espacios (spacers de SharePoint) se
    descartan aunque contengan un ' ' literal.
    """
    try:
        crudo = pd.read_excel(path, sheet_name=hoja, header=None,
                              engine=_motor(path), dtype=object) # type: ignore
    except ValueError:
        return None
    if crudo.empty:
        return None
    h = _detectar_encabezado(crudo)
    cols = [str(c).strip() if pd.notna(c) else "" for c in crudo.iloc[h].tolist()]
    df = crudo.iloc[h + 1:].reset_index(drop=True)
    df = df.dropna(how="all").reset_index(drop=True)

    # Selección por POSICIÓN: descarta columnas SIN encabezado que además están
    # vacías o solo con espacios. No usa df[etiqueta] para tolerar duplicados.
    keep, finales = [], []
    for i, c in enumerate(cols):
        if i >= df.shape[1]:
            break
        es_spacer = (c == "" or c.startswith("COL_"))
        if es_spacer and _col_vacia(df.iloc[:, i]):
            continue
        keep.append(i)
        finales.append(c if c != "" else "(sin encabezado)")
    df = df.iloc[:, keep].copy()
    df.columns = _unicos(finales)        # nombres únicos (las columnas en blanco con datos reales se reportan luego)
    return df


# --------------------------------------------------------------------------- #
# Descubrimiento de archivos de entrada
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Fuente:
    categoria_slug: str
    anio: Optional[int]
    path: Path


def descubrir_fuentes(root: Path) -> dict[str, list[Fuente]]:
    grupos: dict[str, list[Fuente]] = {}
    for p in sorted(root.rglob("*")):
        if p.suffix.lower() not in (".xlsx", ".xls", ".xlsm") or p.name.startswith("~$"):
            continue
        m = RE_ANIO.search(p.name)
        grupos.setdefault(p.parent.name, []).append(
            Fuente(p.parent.name, int(m.group(0)) if m else None, p))
    for cat in grupos:
        grupos[cat].sort(key=lambda f: (f.anio or 0))
    return grupos


def hojas_de_datos(path: Path) -> list[str]:
    xls = pd.ExcelFile(path, engine=_motor(path)) # type: ignore
    return [h for h in xls.sheet_names if clave_col(h).lower() not in HOJAS_IGNORAR] # type: ignore


# --------------------------------------------------------------------------- #
# Alias por ámbito
# --------------------------------------------------------------------------- #

def aliases_para(aliases_raw: Optional[dict], cat_slug: str, hoja_slug: str) -> dict:
    """Combina alias _global + <categoria> + <categoria>/<hoja>. Normaliza claves."""
    if not aliases_raw:
        return {}
    # ¿plano (global) o por ámbito?
    por_ambito = all(isinstance(v, dict) for v in aliases_raw.values()) and len(aliases_raw) > 0
    fuentes = []
    if por_ambito:
        for k in ("_global", cat_slug, f"{cat_slug}/{hoja_slug}"):
            if k in aliases_raw:
                fuentes.append(aliases_raw[k])
    else:
        fuentes.append(aliases_raw)
    out = {}
    for d in fuentes:
        for variante, canon in d.items():
            out[clave_col(variante)] = clave_col(canon)
    return out


# --------------------------------------------------------------------------- #
# Consolidación de una (categoría, hoja)
# --------------------------------------------------------------------------- #

@dataclass
class ReporteHoja:
    categoria: str
    hoja: str
    anios: list[int] = field(default_factory=list)
    columnas_canonicas: list[str] = field(default_factory=list)
    columnas_extra_historicas: list[str] = field(default_factory=list)
    deriva_por_anio: dict = field(default_factory=dict)
    filas_totales: int = 0
    filas_por_anio: dict = field(default_factory=dict)
    excede_limite_xlsx: bool = False
    validaciones: dict = field(default_factory=dict)


def consolidar_hoja(categoria: str, fuentes: list[Fuente], hoja_key: str,
                    hoja_display: str, *, aliases: Optional[dict] = None,
                    estricto: bool = False, limpiar: bool = False
                    ) -> tuple[Optional[pd.DataFrame], ReporteHoja]:
    aliases = aliases or {}
    rep = ReporteHoja(categoria=categoria, hoja=hoja_display)

    cargados: list[tuple[Fuente, pd.DataFrame]] = []
    for f in fuentes:
        real = _resolver_hoja(f.path, hoja_key)     # nombre real (Emision/Emisión/...)
        if real is None:
            continue
        df = leer_hoja(f.path, real)
        if df is None or df.empty:
            continue
        cargados.append((f, df))
        if f.anio:
            rep.anios.append(f.anio)
            rep.filas_por_anio[f.anio] = len(df)
    if not cargados:
        return None, rep

    def keyf(c):
        k = clave_col(c)
        return aliases.get(k, k)

    f_canon, df_canon = max(cargados, key=lambda t: (t[0].anio or 0))
    canon_cols = list(df_canon.columns)
    canon_keys = [keyf(c) for c in canon_cols]
    key_a_canon = dict(zip(canon_keys, canon_cols))
    rep.columnas_canonicas = canon_cols

    extra_keys: list[str] = []
    key_a_extra: dict[str, str] = {}
    if not estricto:
        for f, df in cargados:
            for c in df.columns:
                k = keyf(c)
                if k not in key_a_canon and k not in key_a_extra:
                    key_a_extra[k] = c
                    extra_keys.append(k)
        rep.columnas_extra_historicas = [key_a_extra[k] for k in extra_keys]

    salida_cols = canon_cols + [key_a_extra[k] for k in extra_keys]

    piezas = []
    for f, df in cargados:
        kmap = {keyf(c): c for c in df.columns}
        faltantes, extra = [], []
        datos = {}
        for k, nombre_sal in zip(canon_keys, canon_cols):
            if k in kmap:
                datos[nombre_sal] = df[kmap[k]].values
            else:
                datos[nombre_sal] = pd.NA
                faltantes.append(nombre_sal)
        for k in extra_keys:
            datos[key_a_extra[k]] = df[kmap[k]].values if k in kmap else pd.NA
        for c in df.columns:
            if keyf(c) not in canon_keys and keyf(c) not in extra_keys:
                extra.append(c)
        pieza = pd.DataFrame(datos, columns=salida_cols)
        pieza.insert(0, "archivo_origen", f.path.name)
        pieza.insert(0, "anio", f.anio)
        pieza.insert(0, "categoria", categoria)
        piezas.append(pieza)
        if f.anio and (faltantes or extra):
            rep.deriva_por_anio[f.anio] = {
                "faltantes_rellenadas_vacio": faltantes,
                "descartadas_por_estricto": extra,
            }

    out = pd.concat(piezas, ignore_index=True)
    if limpiar:
        ren = {c: _limpiar_encabezado(c) for c in salida_cols}
        out = out.rename(columns=ren)
        rep.columnas_canonicas = [_limpiar_encabezado(c) for c in canon_cols]
        rep.columnas_extra_historicas = [_limpiar_encabezado(c) for c in rep.columnas_extra_historicas]
        salida_cols = [ren[c] for c in salida_cols]

    # Corrige typos en los encabezados canónicos (p. ej. OCOURRIDO -> OCURRIDO).
    # Se omite una corrección si su destino ya existe, para no crear duplicados.
    corr, existentes = {}, set(salida_cols)
    for c in salida_cols:
        nuevo = _corregir_encabezado(c)
        if nuevo != c and nuevo not in existentes:
            corr[c] = nuevo
            existentes.discard(c); existentes.add(nuevo)
    if corr:
        out = out.rename(columns=corr)
        salida_cols = [corr.get(c, c) for c in salida_cols]
        rep.columnas_canonicas = [corr.get(c, c) for c in rep.columnas_canonicas]
        rep.columnas_extra_historicas = [corr.get(c, c) for c in rep.columnas_extra_historicas]

    rep.filas_totales = len(out)
    rep.anios = sorted(set(rep.anios))
    rep.excede_limite_xlsx = rep.filas_totales > MAX_FILAS_XLSX
    rep.validaciones = _validar(out, salida_cols, rep.columnas_canonicas,
                                rep.columnas_extra_historicas, rep)
    return out, rep


# --------------------------------------------------------------------------- #
# Verificación post-consolidación
# --------------------------------------------------------------------------- #

def _validar(df: pd.DataFrame, columnas_datos: list[str],
             canon_cols: list[str], extra_cols: list[str], rep: ReporteHoja) -> dict:
    avisos: list[str] = []

    # 1) reconciliación de filas
    suma = sum(rep.filas_por_anio.values())
    if suma != rep.filas_totales:
        avisos.append(f"Filas no reconcilian: suma_por_año={suma} vs total={rep.filas_totales}")

    # 2) columnas 100% vacías (posible desalineación/parsing)
    vacias = [c for c in columnas_datos if c in df.columns and df[c].isna().all()]

    # 3) columnas sin encabezado
    sin_enc = [c for c in columnas_datos if _limpiar_encabezado(c) in ("", "(sin encabezado)")]

    # 4) posibles variantes a unir con alias: SOLO columnas histórico-only vs canónicas
    #    (comparar canónica-vs-canónica daría falsos positivos como PRIMA EMITIDA/CEDIDA)
    duplicados = []
    for ex in extra_cols:
        kex = clave_col(ex)
        if not kex:
            continue
        mejor = None
        for cn in canon_cols:
            kcn = clave_col(cn)
            if not kcn or kcn == kex:
                continue
            r = difflib.SequenceMatcher(None, kex, kcn).ratio()
            if r >= 0.88 and (mejor is None or r > mejor["similitud"]):
                mejor = {"variante": ex, "canonica": cn, "similitud": round(r, 3)}
        if mejor:
            duplicados.append(mejor)

    # 5) columnas de medida con valores no numéricos
    medidas_sospechosas = []
    for c in columnas_datos:
        if c not in df.columns or not RE_MEDIDA.search(clave_col(c)):
            continue
        s = df[c].dropna()
        if s.empty:
            continue
        no_num = pd.to_numeric(s, errors="coerce").isna()
        frac = float(no_num.mean())
        if frac > 0.10:
            ejemplos = s[no_num].astype(str).unique()[:3].tolist()
            medidas_sospechosas.append(
                {"columna": c, "frac_no_numerico": round(frac, 3), "ejemplos": ejemplos})

    if vacias:
        avisos.append(f"{len(vacias)} columna(s) canónica(s) 100% vacías: {vacias}")
    if sin_enc:
        avisos.append(f"{len(sin_enc)} columna(s) sin encabezado: {sin_enc}")
    if duplicados:
        avisos.append(f"{len(duplicados)} columna(s) histórica(s) parecida(s) a una "
                      f"canónica (posible alias)")
    if medidas_sospechosas:
        avisos.append(f"{len(medidas_sospechosas)} columna(s) de medida con valores no numéricos")

    return {
        "ok": not avisos, "avisos": avisos,
        "columnas_vacias": vacias, "columnas_sin_encabezado": sin_enc,
        "posibles_duplicados": duplicados, "medidas_no_numericas": medidas_sospechosas,
    }


# --------------------------------------------------------------------------- #
# Orquestación
# --------------------------------------------------------------------------- #

def consolidar(root: Path, out_dir: Path, *,
               categorias: Optional[Iterable[str]] = None,
               aliases: Optional[dict] = None, estricto: bool = False,
               xlsx_si_cabe: bool = False, limpiar_encabezados: bool = False,
               compresion: str = "none") -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    grupos = descubrir_fuentes(root)
    if categorias:
        objetivos = {_slug(c) for c in categorias}
        grupos = {k: v for k, v in grupos.items()
                  if k in objetivos or any(o in k for o in objetivos)}

    resumen_global = []
    for cat, fuentes in grupos.items():
        cat_dir = out_dir / cat
        cat_dir.mkdir(parents=True, exist_ok=True)

        # Agrupa hojas por NOMBRE NORMALIZADO (fusiona Emision/Emisión, etc.).
        grupos_hoja: dict[str, str] = {}      # hoja_key -> display (del año más reciente)
        for f in sorted(fuentes, key=lambda x: -(x.anio or 0)):
            for h in hojas_de_datos(f.path):
                grupos_hoja.setdefault(clave_col(h), h)

        log.info("Categoría %s: años=%s, hojas=%s",
                 cat, [f.anio for f in fuentes], list(grupos_hoja.values()))

        reportes_cat, bases_usadas = [], {}
        for hoja_key, hoja_display in grupos_hoja.items():
            al = aliases_para(aliases, cat, _slug(hoja_display))
            df, rep = consolidar_hoja(cat, fuentes, hoja_key, hoja_display,
                                      aliases=al, estricto=estricto,
                                      limpiar=limpiar_encabezados)
            if df is None:
                continue
            base = _slug(hoja_display)
            if base in bases_usadas:              # guardia anti-colisión (no debería ocurrir)
                base = f"{base}__{hoja_key.lower().replace(' ', '_')}"
                log.warning("Colisión de salida en %s; uso %s.csv", cat, base)
            bases_usadas[base] = hoja_key
            csv_path = cat_dir / f"{base}.csv{EXT_COMPRESION[compresion]}"
            df.to_csv(csv_path, index=False, encoding="utf-8-sig",
                      compression=(None if compresion == "none" else compresion))
            salida = [str(csv_path)]
            hizo_xlsx = xlsx_si_cabe and not rep.excede_limite_xlsx
            if hizo_xlsx:
                xp = cat_dir / f"{base}.xlsx"
                df.to_excel(xp, index=False)
                salida.append(str(xp))
            estado_val = "OK" if rep.validaciones.get("ok") else "REVISAR"
            log.info("  %-18s -> %d filas, %d cols | %s | validación: %s",
                     hoja_display, rep.filas_totales,
                     len(rep.columnas_canonicas) + len(rep.columnas_extra_historicas),
                     "CSV+XLSX" if hizo_xlsx else "CSV", estado_val)
            for a in rep.validaciones.get("avisos", []):
                log.warning("     · %s", a)
            reportes_cat.append({
                "hoja": rep.hoja, "salida": salida, "anios": rep.anios,
                "filas_totales": rep.filas_totales, "filas_por_anio": rep.filas_por_anio,
                "n_columnas_canonicas": len(rep.columnas_canonicas),
                "columnas_canonicas": rep.columnas_canonicas,
                "columnas_extra_historicas": rep.columnas_extra_historicas,
                "deriva_por_anio": rep.deriva_por_anio,
                "excede_limite_xlsx": rep.excede_limite_xlsx,
                "validaciones": rep.validaciones,
            })

        (cat_dir / "_reporte.json").write_text(
            json.dumps({"categoria": cat, "root": str(root), "estricto": estricto,
                        "hojas": reportes_cat}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        resumen_global.append({
            "categoria": cat, "carpeta": str(cat_dir),
            "hojas": [r["hoja"] for r in reportes_cat],
            "filas_por_hoja": {r["hoja"]: r["filas_totales"] for r in reportes_cat},
            "hojas_a_revisar": [r["hoja"] for r in reportes_cat
                                if not r["validaciones"].get("ok")],
        })

    reporte = {"root": str(root), "out_dir": str(out_dir), "estricto": estricto,
               "categorias": resumen_global}
    (out_dir / "reporte_consolidacion.json").write_text(
        json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")
    return reporte


def main():
    ap = argparse.ArgumentParser(description="Consolidador CNSF por (categoría, hoja)")
    ap.add_argument("--root", default="datos/datos_CNSF/crudos")
    ap.add_argument("--out-dir", default="datos/datos_CNSF/consolidados")
    ap.add_argument("--categorias", nargs="*")
    ap.add_argument("--estricto", action="store_true")
    ap.add_argument("--xlsx-si-cabe", action="store_true")
    ap.add_argument("--limpiar-encabezados", action="store_true",
                    help="colapsa saltos de línea/espacios en los encabezados de salida")
    ap.add_argument("--comprimir", choices=list(EXT_COMPRESION), default="none",
                    help="comprime los CSV de salida (recomendado: gzip -> .csv.gz)")
    ap.add_argument("--aliases", default="src/aliases_cnsf.json", help="JSON de alias (plano o por ámbito)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    aliases = json.loads(Path(args.aliases).read_text(encoding="utf-8")) if args.aliases else None
    consolidar(Path(args.root), Path(args.out_dir), categorias=args.categorias,
               aliases=aliases, estricto=args.estricto, xlsx_si_cabe=args.xlsx_si_cabe,
               limpiar_encabezados=args.limpiar_encabezados, compresion=args.comprimir)
    log.info("Listo.")


if __name__ == "__main__":
    main()
