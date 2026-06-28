"""
explorar_xlsx_cnsf.py
=====================
Explorador de ESTRUCTURA para los sectores en Excel (Agrícola, Incendio, Hidro…),
análogo a la exploración de los `.mdb` de Automóviles. Es de SOLO LECTURA: no
consolida ni escribe CSV; solo levanta el contexto de cómo cambian las columnas
en el tiempo, para decidir alias y entender los avisos del consolidador.

Por cada (categoría, hoja) reporta, a lo largo de los años:
  - columnas por año (en orden),
  - matriz de presencia: en qué años aparece cada columna (clave normalizada),
  - columnas SIN encabezado pero CON datos (posición + valores de muestra),
  - encabezados DUPLICADOS por año,
  - candidatos a alias: columnas históricas parecidas (≥0.88) a una canónica
    (la del año más reciente) — listas para agregar a aliases_cnsf.json.

Reutiliza las primitivas de `consolidar_cnsf.py` (misma detección de encabezado y
normalización), así que lo que ve aquí coincide con lo que ve la consolidación.

Uso:
    python explorar_xlsx_cnsf.py --root datos/cnsf [--categorias agricola hidro]
    python explorar_xlsx_cnsf.py --root datos/cnsf --out reporte_estructura.json
"""

from __future__ import annotations

import argparse
import difflib
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Optional

import pandas as pd

import consolidar_cnsf as C   # primitivas compartidas

log = logging.getLogger("cnsf.estructura")

UMBRAL_ALIAS = 0.88
MUESTRA_DEFECTO = 200


def _estructura_hoja(path: Path, hoja: str, muestra: int) -> Optional[dict]:
    """Lee solo las primeras `muestra` filas para deducir encabezados y muestras
    (rápido; no carga la hoja completa)."""
    try:
        crudo = pd.read_excel(path, sheet_name=hoja, header=None,
                              engine=C._motor(path), dtype=object, nrows=muestra) # type: ignore
    except ValueError:
        return None
    if crudo.empty:
        return None
    h = C._detectar_encabezado(crudo)
    cols = [str(c).strip() if pd.notna(c) else "" for c in crudo.iloc[h].tolist()]
    datos = crudo.iloc[h + 1:].reset_index(drop=True)
    info = []
    for i, c in enumerate(cols):
        col = datos.iloc[:, i] if i < datos.shape[1] else pd.Series([], dtype=object)
        # "reales" = no NaN y no solo espacios (los spacers de SharePoint traen ' ')
        reales = col[col.map(lambda v: not (pd.isna(v) or str(v).strip() == ""))]
        ej = [str(v) for v in pd.unique(reales)[:3]]
        info.append({"pos": i, "encabezado": c, "no_nulos_muestra": int(len(reales)), "muestra": ej})
    return {"cols": cols, "info": info}


def explorar(root: Path, categorias: Optional[list] = None,
             muestra: int = MUESTRA_DEFECTO) -> dict:
    grupos = C.descubrir_fuentes(root)
    if categorias:
        filtros = [C._slug(x) for x in categorias]
        grupos = {c: v for c, v in grupos.items()
                  if any(f in c for f in filtros)}
    reporte: dict = {}

    for cat, fuentes in sorted(grupos.items()):
        fuentes = sorted(fuentes, key=lambda f: (f.anio or 0))
        # Hojas de datos (unión de todos los años; clave normalizada -> display reciente)
        hojas: dict[str, str] = {}
        for f in fuentes:
            for h in C.hojas_de_datos(f.path):
                hojas[C.clave_col(h)] = h     # el último (más reciente) deja su display
        cat_rep: dict = {}

        for hkey, hdisp in hojas.items():
            por_anio: dict[int, list] = {}
            sin_enc: dict[str, list] = {}
            dups: dict[str, list] = {}
            for f in fuentes:
                real = C._resolver_hoja(f.path, hkey)
                if real is None:
                    continue
                est = _estructura_hoja(f.path, real, muestra)
                if est is None:
                    continue
                anio = f.anio
                por_anio[anio] = est["cols"] # type: ignore
                be = [{"pos": x["pos"], "muestra": x["muestra"]}
                      for x in est["info"] if x["encabezado"] == "" and x["no_nulos_muestra"] > 0]
                if be:
                    sin_enc[str(anio)] = be
                cnt = Counter(c for c in est["cols"] if c != "")
                d = sorted(n for n, k in cnt.items() if k > 1)
                if d:
                    dups[str(anio)] = d

            if not por_anio:
                continue

            # Matriz de presencia por clave normalizada.
            matriz: dict[str, dict] = {}
            for anio, cols in por_anio.items():
                for c in cols:
                    if c == "":
                        continue
                    m = matriz.setdefault(C.clave_col(c), {"display": c, "anios": set()})
                    m["anios"].add(anio)
            for m in matriz.values():
                m["anios"] = sorted(m["anios"])

            anio_canon = max(por_anio)
            canon_keys = {C.clave_col(c) for c in por_anio[anio_canon] if c != ""}

            # Candidatos a alias: claves NO canónicas parecidas a una canónica.
            alias_cand: dict = {}
            for k, m in matriz.items():
                if k in canon_keys:
                    continue
                mejor = None
                for ck in canon_keys:
                    r = difflib.SequenceMatcher(None, k, ck).ratio()
                    if r >= UMBRAL_ALIAS and (mejor is None or r > mejor[1]):
                        mejor = (ck, r)
                if mejor:
                    alias_cand[k] = {"parecida_a": matriz.get(mejor[0], {}).get("display", mejor[0]),
                                     "clave_canonica": mejor[0], "similitud": round(mejor[1], 3),
                                     "display": m["display"], "anios": m["anios"]}

            # Columnas que aparecen/desaparecen (no presentes en todos los años).
            todos = sorted(por_anio)
            no_universales = {m["display"]: m["anios"] for k, m in matriz.items()
                              if len(m["anios"]) != len(todos)}

            cat_rep[hdisp] = {
                "anios": todos,
                "anio_canonico": anio_canon,
                "n_columnas_canonicas": len(canon_keys),
                "columnas_por_anio": {str(a): por_anio[a] for a in todos},
                "columnas_no_en_todos_los_anios": no_universales,
                "sin_encabezado_con_datos": sin_enc,
                "encabezados_duplicados": dups,
                "alias_candidatos": alias_cand,
            }
        reporte[cat] = cat_rep
    return reporte


def _resumen(reporte: dict) -> None:
    for cat, hojas in reporte.items():
        log.info("══ %s ══", cat)
        for hoja, r in hojas.items():
            log.info("  • %s | años %s | %d cols canónicas (año %s)",
                     hoja, f"{r['anios'][0]}–{r['anios'][-1]}" if r["anios"] else "?",
                     r["n_columnas_canonicas"], r["anio_canonico"])
            if r["alias_candidatos"]:
                for k, a in r["alias_candidatos"].items():
                    log.info("      alias? '%s' (años %s) ~ '%s'  [%.2f]",
                             a["display"], a["anios"], a["parecida_a"], a["similitud"])
            if r["sin_encabezado_con_datos"]:
                for anio, cols in r["sin_encabezado_con_datos"].items():
                    for be in cols:
                        log.info("      sin encabezado %s pos %d, muestra %s",
                                 anio, be["pos"], be["muestra"])
            if r["encabezados_duplicados"]:
                log.info("      encabezados duplicados: %s", r["encabezados_duplicados"])
            faltan = r["columnas_no_en_todos_los_anios"]
            if faltan:
                log.info("      columnas no presentes en todos los años: %d", len(faltan))


def main():
    ap = argparse.ArgumentParser(description="Explorador de estructura de los xlsx de la CNSF")
    ap.add_argument("--root", default="datos/datos_CNSF/crudos", help="carpeta de Excel crudos")
    ap.add_argument("--categorias", nargs="*", help="filtra (coincidencia parcial). Default: todas")
    ap.add_argument("--out", default="reporte_estructura.json", help="ruta del reporte JSON")
    ap.add_argument("--muestra", type=int, default=MUESTRA_DEFECTO,
                    help="filas a leer por hoja para deducir estructura/muestras (default 200)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    reporte = explorar(Path(args.root), categorias=args.categorias, muestra=args.muestra)
    Path(args.out).write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")
    _resumen(reporte)
    log.info("Reporte -> %s", args.out)


if __name__ == "__main__":
    main()
