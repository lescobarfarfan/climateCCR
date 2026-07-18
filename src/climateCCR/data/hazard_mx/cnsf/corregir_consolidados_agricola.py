"""
corregir_consolidados_agricola.py
=================================
Aplica las correcciones de magnitud del ramo agrícola (`limpieza_cnsf` §6; decisiones en
`referencias_riesgo_catastrofico.md` §4, recuadro agrícola) sobre los consolidados CNSF y
escribe copias corregidas + auditoría. Los consolidados originales NO se tocan (siguen
siendo el "as published" de la CNSF); re-ejecutar es idempotente porque siempre parte de
los originales.

Salidas (en el mismo directorio de consolidados):
  - emision_corregida.csv / siniestros_corregida.csv   (con columnas `dq_correccion`,
    `dq_valor_original` en los renglones tocados)
  - _correcciones_dq.csv                               (auditoría: un renglón por corrección)

Uso: python corregir_consolidados_agricola.py [--dir RUTA_CONSOLIDADOS_AGRICOLA]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from limpieza_cnsf import (
    corregir_magnitudes_agricola_emision,
    corregir_magnitudes_agricola_siniestros,
)

DIR_DEFAULT = (
    Path(__file__).resolve().parents[5]
    / "data/hazard_mx/datos_CNSF/consolidados/agricola_y_animales"
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", type=Path, default=DIR_DEFAULT, help="directorio de consolidados")
    d = ap.parse_args().dir

    em = pd.read_csv(d / "emision.csv", encoding="utf-8-sig", low_memory=False)
    si = pd.read_csv(d / "siniestros.csv", encoding="utf-8-sig", low_memory=False)

    em_c, aud_em = corregir_magnitudes_agricola_emision(em)
    si_c, aud_si = corregir_magnitudes_agricola_siniestros(si, emision_corregida=em_c)
    aud_em["archivo"], aud_si["archivo"] = "emision", "siniestros"
    aud = pd.concat([aud_em, aud_si], ignore_index=True)

    em_c.to_csv(d / "emision_corregida.csv", index=False, encoding="utf-8-sig")
    si_c.to_csv(d / "siniestros_corregida.csv", index=False, encoding="utf-8-sig")
    aud.to_csv(d / "_correcciones_dq.csv", index=False, encoding="utf-8-sig")

    resumen = aud.groupby(["archivo", "regla"]).size()
    print(resumen.to_string())
    print(f"total correcciones: {len(aud)} -> {d}")


if __name__ == "__main__":
    main()
