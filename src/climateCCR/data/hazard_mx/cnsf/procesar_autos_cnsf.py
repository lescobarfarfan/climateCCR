"""
procesar_autos_cnsf.py
======================
Procesa las bases Access (.mdb, dentro de .zip) de Automóviles de la CNSF y
produce CSV consolidados por subsector (individual / flotillas), resolviendo los
códigos contra sus catálogos. Es INDEPENDIENTE del consolidador de los sectores
xlsx; la descarga/verificación (sha256, manifest, _estado.json) la hace el
scraper, que ya reconoce los .zip.

Para cada subsector y cada tabla de hecho (Emisión, Siniestros, Unidades
Expuestas) une todos los años en un solo CSV:
  - esquema canónico = año más reciente (config anio_canonico),
  - 2007 se excluye (formato ancho incompatible; config anios_excluir),
  - cada columna-código se conserva y se le AGREGA su cruce `_desc`
    (Marca se expande a Marca_desc + Tipo_desc),
  - faltantes/centinelas ("ND", "N/A", ...) -> etiqueta configurable, fila
    conservada (resolución tipo LEFT JOIN; nunca se pierden filas),
  - procesamiento POR AÑO y en CHUNKS (Emisión llega a millones de filas),
  - salida opcionalmente comprimida (gzip recomendado).

Config: catalogos_autos_cnsf.json (uniones columna->catálogo, llaves, centinelas).
Requiere: mdbtools (mdb-export) en el PATH, y pandas.
"""

from __future__ import annotations

import argparse
import bz2
import csv as _csv
import gzip
import io
import json
import logging
import lzma
import re
import shutil
import subprocess
import tempfile
import zipfile
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

# Vocabulario compartido con el consolidador (mismo directorio; los scripts CNSF
# se importan entre sí por nombre plano — ver tests/conftest.py, OQ-HAZ-15).
from consolidar_cnsf import _sin_acentos, _slug

log = logging.getLogger("cnsf.autos")

RE_ANIO = re.compile(r"(?<!\d)(19|20)\d{2}(?!\d)")  # no \b: el '_' rompería el match
EXT_COMPRESION = {"none": "", "gzip": ".gz", "bz2": ".bz2", "xz": ".xz"}
CHUNK = 200_000


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #


def _norm(v) -> str:
    return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip()


def _clave_col(s: str) -> str:
    """Normaliza un nombre de columna para emparejar uniones entre subsectores
    (insensible a mayúsculas y acentos; colapsa espacios). Así 'Tipo de Poliza',
    'Tipo de poliza' y 'TIPO DE POLIZA' se tratan igual."""
    return re.sub(r"\s+", " ", _sin_acentos(str(s)).strip().lower())


def _abrir_salida(path: Path, compresion: str):
    enc = "utf-8-sig" if compresion == "none" else "utf-8"
    if compresion == "none":
        return open(path, "w", encoding=enc, newline="")
    if compresion == "gzip":
        return gzip.open(path, "wt", encoding=enc, newline="")
    if compresion == "bz2":
        return bz2.open(path, "wt", encoding=enc, newline="")
    if compresion == "xz":
        return lzma.open(path, "wt", encoding=enc, newline="")
    raise ValueError(f"compresión no soportada: {compresion}")


# --------------------------------------------------------------------------- #
# Acceso al .mdb (costuras aisladas para poder probar sin mdbtools/zip)
# --------------------------------------------------------------------------- #


def _descomprimir(zip_path: Path, destino: Path) -> Path | None:
    """Extrae el .mdb del .zip y devuelve su ruta."""
    try:
        with zipfile.ZipFile(zip_path) as z:
            mdbs = [n for n in z.namelist() if n.lower().endswith(".mdb")]
            if not mdbs:
                return None
            z.extract(mdbs[0], destino)
            return destino / mdbs[0]
    except Exception as e:  # noqa: BLE001
        log.error("No pude descomprimir %s: %s", zip_path, e)
        return None


def _columnas(mdb: Path, tabla: str) -> list[str] | None:
    """Encabezados de una tabla (lee solo la primera línea de mdb-export)."""
    try:
        p = subprocess.Popen(["mdb-export", str(mdb), tabla], stdout=subprocess.PIPE, text=True)
        linea = p.stdout.readline()  # type: ignore
        p.stdout.close()
        p.terminate()  # type: ignore
    except Exception:  # noqa: BLE001
        return None
    if not linea:
        return None
    return next(_csv.reader([linea]))


def _leer_completa(mdb: Path, tabla: str) -> pd.DataFrame | None:
    """Lee una tabla completa (para catálogos, que son chicos)."""
    try:
        r = subprocess.run(
            ["mdb-export", str(mdb), tabla], capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError:
        return None
    if not r.stdout.strip():
        return None
    return pd.read_csv(io.StringIO(r.stdout), dtype=object)


def _iter_chunks(mdb: Path, tabla: str, chunksize: int = CHUNK) -> Iterator[pd.DataFrame]:
    """Itera una tabla en bloques (streaming; para tablas enormes como Emisión)."""
    p = subprocess.Popen(["mdb-export", str(mdb), tabla], stdout=subprocess.PIPE, text=True)
    try:
        yield from pd.read_csv(p.stdout, dtype=object, chunksize=chunksize)  # type: ignore
    finally:
        if p.stdout:
            p.stdout.close()
        p.wait()


# --------------------------------------------------------------------------- #
# Catálogos
# --------------------------------------------------------------------------- #


def _build_lookup(dfc: pd.DataFrame, llave: str, descs: list[str], llave_tipo: str | None) -> dict:
    d = {}
    for _, row in dfc.iterrows():
        k = row.get(llave)
        if llave_tipo == "entero":
            try:
                k = str(int(float(k)))  # type: ignore
            except (TypeError, ValueError):
                k = _norm(k)
        else:
            k = _norm(k)
        d[k] = tuple(row.get(dc) for dc in descs)
    return d


def _desc_out_names(factcol: str, descs: list[str]) -> list[str]:
    """Nombres de las columnas _desc. Multi-desc (Marca) -> por campo: Marca_desc, Tipo_desc."""
    if len(descs) == 1:
        return [f"{factcol}_desc"]
    return [f"{d.capitalize()}_desc" for d in descs]


def cargar_catalogos(mdb: Path, config: dict) -> dict:
    lookups = {}
    for catname, spec in config["catalogos"].items():
        dfc = None
        for alias in spec["alias"]:
            dfc = _leer_completa(mdb, alias)
            if dfc is not None and not dfc.empty:
                break
        lookups[catname] = (
            None
            if dfc is None or dfc.empty
            else _build_lookup(dfc, spec["llave"], spec["desc"], spec.get("llave_tipo"))
        )
    return lookups


# --------------------------------------------------------------------------- #
# Resolución de un chunk
# --------------------------------------------------------------------------- #


def resolver_chunk(
    chunk: pd.DataFrame, tabla: str, config: dict, lookups: dict, centinelas: set, etiqueta: str
) -> pd.DataFrame:
    joins = config["uniones"].get(tabla, {})
    # mapa: nombre-de-columna-normalizado del config -> catálogo
    jn = {_clave_col(k): cat for k, cat in joins.items()}
    for col in list(chunk.columns):
        catname = jn.get(_clave_col(col))
        if catname is None:
            continue
        descs = config["catalogos"][catname]["desc"]
        outnames = _desc_out_names(col, descs)
        lk = lookups.get(catname)
        keys = chunk[col].map(_norm)
        n_descs = len(descs)

        def resolver(k, _lk=lk, _n=n_descs):
            if k.upper() in centinelas:
                return tuple([etiqueta] * _n)
            if _lk is None:
                return tuple([pd.NA] * _n)
            t = _lk.get(k)
            if t is None:
                return tuple([pd.NA] * _n)
            return tuple((t[i] if i < len(t) else pd.NA) for i in range(_n))

        resueltos = [resolver(k) for k in keys]
        for i, o in enumerate(outnames):
            chunk[o] = [r[i] for r in resueltos]
    return chunk


def _orden_salida(canon: list[str], tabla: str, config: dict) -> list[str]:
    joins = config["uniones"].get(tabla, {})
    jn = {_clave_col(k): cat for k, cat in joins.items()}
    orden = []
    for c in canon:
        orden.append(c)
        catname = jn.get(_clave_col(c))
        if catname:
            orden.extend(_desc_out_names(c, config["catalogos"][catname]["desc"]))
    return orden


# --------------------------------------------------------------------------- #
# Procesamiento
# --------------------------------------------------------------------------- #


@dataclass
class ReporteTabla:
    tabla: str
    salida: str = ""
    anios: list = field(default_factory=list)
    filas_por_anio: dict = field(default_factory=dict)
    columnas_salida: list = field(default_factory=list)
    deriva_por_anio: dict = field(default_factory=dict)


def _año_de(nombre: str) -> int | None:
    m = RE_ANIO.search(nombre)
    return int(m.group(0)) if m else None


def descubrir_zips(root: Path, config: dict) -> dict:
    """{subsector: {anio: zip_path}} respetando la diferenciación por subsector.

    Prioriza **subcarpetas** por subsector: una carpeta cuyo nombre contenga el
    patrón del subsector (p. ej. 'individual', 'flotilla' o 'flotillas') asigna
    todos sus .zip a ese subsector. Como respaldo (compatibilidad), también
    detecta .zip sueltos en la raíz y los clasifica por el patrón en su nombre.
    Insensible a mayúsculas (.zip/.ZIP). El año se toma del nombre del .zip.
    Ignora archivos sin año o sin patrón (p. ej. 'salida_mdb.zip').
    """
    subs = config["subsectores"]
    out: dict = {name: {} for name in subs}
    sin_anio: list = []

    def _es_zip(p: Path) -> bool:
        return p.is_file() and p.suffix.lower() == ".zip"

    def _clasificar(name: str, p: Path) -> None:
        anio = _año_de(p.name)
        if anio is None:
            sin_anio.append(p)
        else:
            out[name].setdefault(anio, p)  # las subcarpetas (1) ganan sobre sueltos (2)

    # (1) subcarpetas por subsector
    if root.exists():
        for name, spec in subs.items():
            pat = spec["patron_archivo"].lower()
            for d in sorted(root.iterdir()):
                if d.is_dir() and pat in d.name.lower():
                    for p in sorted(d.glob("*")):
                        if _es_zip(p):
                            _clasificar(name, p)

    # (2) respaldo: .zip sueltos en la raíz, clasificados por el nombre
    for p in sorted(root.glob("*")):
        if not _es_zip(p):
            continue
        low = p.name.lower()
        for name, spec in subs.items():
            if spec["patron_archivo"].lower() in low:
                _clasificar(name, p)

    if sin_anio:
        log.warning(
            "Zips con patrón de subsector pero SIN año reconocible " "(NO se procesaron): %s",
            ", ".join(sorted({p.name for p in sin_anio})),
        )
    return {s: v for s, v in out.items() if v}


def procesar_tabla(
    subsector: str,
    zips: dict,
    tabla: str,
    config: dict,
    out_dir: Path,
    *,
    compresion: str,
    centinelas: set,
    etiqueta: str,
    tmpbase: Path,
) -> ReporteTabla | None:
    excluir = set(config.get("anios_excluir", []))
    anios = sorted(a for a in zips if a not in excluir)
    if not anios:
        return None
    canon_anio = config.get("anio_canonico") if config.get("anio_canonico") in anios else anios[-1]

    rep = ReporteTabla(tabla=tabla, anios=anios)

    # Columnas canónicas (del año canónico).
    with tempfile.TemporaryDirectory(dir=tmpbase) as td:
        mdb = _descomprimir(zips[canon_anio], Path(td))
        if mdb is None:
            log.error("[%s/%s] no pude leer el año canónico %s", subsector, tabla, canon_anio)
            return None
        canon = _columnas(mdb, tabla)
    if not canon:
        log.warning("[%s/%s] la tabla no existe en el año canónico; se omite", subsector, tabla)
        return None

    orden = ["subsector", "anio", "archivo_origen"] + _orden_salida(canon, tabla, config)
    rep.columnas_salida = orden

    base = _slug(tabla)
    salida = out_dir / f"{base}.csv{EXT_COMPRESION[compresion]}"
    rep.salida = str(salida)

    primero = True
    fh = _abrir_salida(salida, compresion)
    try:
        for anio in anios:
            with tempfile.TemporaryDirectory(dir=tmpbase) as td:
                mdb = _descomprimir(zips[anio], Path(td))
                if mdb is None:
                    continue
                cols_anio = _columnas(mdb, tabla)
                if not cols_anio:
                    continue
                faltantes = [c for c in canon if c not in cols_anio]
                extras = [c for c in cols_anio if c not in canon]
                if faltantes or extras:
                    rep.deriva_por_anio[anio] = {
                        "faltantes_rellenadas_vacio": faltantes,
                        "extras_ignoradas": extras,
                    }
                lookups = cargar_catalogos(mdb, config)
                filas = 0
                for chunk in _iter_chunks(mdb, tabla):
                    # alinear a columnas canónicas
                    for c in canon:
                        if c not in chunk.columns:
                            chunk[c] = pd.NA
                    chunk = resolver_chunk(chunk, tabla, config, lookups, centinelas, etiqueta)
                    chunk.insert(0, "archivo_origen", zips[anio].name)
                    chunk.insert(0, "anio", anio)
                    chunk.insert(0, "subsector", subsector)
                    chunk = chunk.reindex(columns=orden)
                    chunk.to_csv(fh, index=False, header=primero)
                    primero = False
                    filas += len(chunk)
                rep.filas_por_anio[anio] = filas
                log.info("[%s/%s] %s -> %d filas", subsector, tabla, anio, filas)
    finally:
        fh.close()
    return rep


def procesar(
    root: Path,
    out_dir: Path,
    config: dict,
    *,
    subsectores: Iterable[str] | None = None,
    compresion: str = "none",
) -> dict:
    centinelas = {str(s).strip().upper() for s in config.get("centinelas_faltante", ["ND"])}
    etiqueta = config.get("etiqueta_faltante", "No disponible")
    zips_por_sub = descubrir_zips(root, config)
    if subsectores:
        zips_por_sub = {s: v for s, v in zips_por_sub.items() if s in set(subsectores)}

    out_dir.mkdir(parents=True, exist_ok=True)
    tmpbase = out_dir / "_tmp"
    tmpbase.mkdir(exist_ok=True)
    resumen = []
    try:
        for sub, zips in zips_por_sub.items():
            sub_dir = out_dir / f"automoviles_{sub}"
            sub_dir.mkdir(parents=True, exist_ok=True)
            log.info("Subsector %s: años %s", sub, sorted(zips))
            reportes = []
            for tabla in config["tablas_hecho"]:
                rep = procesar_tabla(
                    sub,
                    zips,
                    tabla,
                    config,
                    sub_dir,
                    compresion=compresion,
                    centinelas=centinelas,
                    etiqueta=etiqueta,
                    tmpbase=tmpbase,
                )
                if rep:
                    reportes.append(rep.__dict__)
            (sub_dir / "_reporte.json").write_text(
                json.dumps(
                    {"subsector": sub, "anios": sorted(zips), "tablas": reportes},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            resumen.append(
                {
                    "subsector": sub,
                    "carpeta": str(sub_dir),
                    "tablas": [r["tabla"] for r in reportes],
                }
            )
    finally:
        shutil.rmtree(tmpbase, ignore_errors=True)

    reporte = {"root": str(root), "out_dir": str(out_dir), "subsectores": resumen}
    (out_dir / "reporte_autos.json").write_text(
        json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return reporte


def main():
    ap = argparse.ArgumentParser(description="Procesador de Automóviles CNSF (MDB -> CSV)")
    ap.add_argument("--root", default="datos/datos_CNSF/automoviles", help="carpeta con los .zip")
    ap.add_argument("--out-dir", default="datos/datos_CNSF/consolidados")
    ap.add_argument("--config", default="src/catalogos_autos_cnsf.json")
    ap.add_argument("--subsectores", nargs="*", help="individual flotillas (default: ambos)")
    ap.add_argument(
        "--comprimir",
        choices=list(EXT_COMPRESION),
        default="none",
        help="comprime los CSV (recomendado: gzip)",
    )
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    procesar(
        Path(args.root),
        Path(args.out_dir),
        config,
        subsectores=args.subsectores,
        compresion=args.comprimir,
    )
    log.info("Listo.")


if __name__ == "__main__":
    main()
