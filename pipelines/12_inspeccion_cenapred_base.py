"""Inspección of the 2000-2015 CENAPRED base — the GEN-27 gap closed (OQ-INT-11 session).

The 2016-2024 extension was inspected on arrival (HAZ-CENAPRED-10;
results/inspeccion/cenapred_extension_2016_2024/), but the 2000-2015 open-CSV
base predates the GEN-27 standing rule and never went through the battery.
impactcal-mx's QA (its CAL-TARGET-06) flagged MDP/MDD unit anomalies in this
segment (Chiapas 2003/2010) against consolidados that are byte-identical to
ours — this pipeline runs our own inspección and adds a row-level ratio triage.

Two outputs under results/inspeccion/cenapred_base_2000_2015/:

1. The standard ``data.inspeccion`` battery on the 2000-2015 segment of
   ``eventos_cenapred_climada.csv`` (hallazgos.csv, resumen.md, figuras/).
2. ``triaje_razon_mdp_mdd.csv`` — row-level ``danio_mdp/danio_mdd`` ratio
   triage. The battery's ratio check works on aggregated cells, which can mask
   row-level unit anomalies (two Chiapas 2003 fire rows whose MDD errors offset
   to a sane-looking cell ratio); this annex compares each row's ratio to its
   YEAR MEDIAN (the robust FIX proxy: most rows convert at the published annual
   FIX) and cross-references the ``mayores_200mdp`` trigger set (INT-20) so the
   rows that reach the lambda/severity fits are explicit.

3. ``resolucion_triaje.md`` — the documented resolution rule (user decision
   2026-08-01, OQ-INT-11 g) applied to the annex as a ``resolucion`` column:
   ``danio_mdd`` is discarded as unreliable in the flagged rows (it feeds no
   fit); ``danio_mdp`` is kept where the event is in climate scope and its
   magnitude is justified, else flagged/excluded from diagnostics.

The battery itself still corrects nothing (GEN-27); the resolution is a
documented verdict on the findings, not a data mutation. Deterministic (no
RNG); idempotent (GEN-05): skips if the annex exists, rerun with
--forzar/--force.

    python pipelines/12_inspeccion_cenapred_base.py [--forzar]
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
EVENTS_CSV = (
    REPO_ROOT / "data/hazard_mx/datos_CENAPRED/consolidados_2000_2024/eventos_cenapred_climada.csv"
)
INPC_CONFIG = REPO_ROOT / "configs" / "inpc_anual.yaml"
BASE_END_YEAR = 2015  # the open-CSV registry segment; the extension is QA-clean
TRIGGER_WINDOW = (2002, 2015)  # mayores_200mdp spec (INT-20)
TRIGGER_MIN_REAL_MDP = 200.0

# Resolución del triaje (regla documentada, decisión de usuario 2026-08-01; GEN-27).
# La columna danio_mdd de las filas señaladas es no confiable — el FIX implícito
# (razon) queda lejos de cualquier FIX histórico — y ningún ajuste la consume: se
# descarta. danio_mdp se conserva si el evento está en alcance climático y su
# magnitud está justificada; si no, se excluye de los diagnósticos sin umbral.
_MDP_CORROBORADO = {
    # En el conjunto disparador; magnitud históricamente corroborada (HAZ-CENAPRED-11):
    "CEN-2007-02365",  # deslizamiento Juan de Grijalva 2007 (1,015.9 MDP)
    "CEN-2003-00712",  # tormenta tropical Larry 2003 (298.3 MDP)
}
_MDP_EXCLUIDO_DIAGNOSTICOS = {
    # Incendios forestales Chiapas 2003 (~72-76 MDP nominales): temporada activa
    # confirmada (registro UNAM de la temporada mar-abr 2003) pero la magnitud no
    # es corroborable externamente a 22 años; sub-umbral (<200 MDP-2025), así que
    # los ajustes adoptados no cambian bajo ninguno de los dos veredictos.
    "CEN-2003-00460",
    "CEN-2003-00399",
}


def _resolucion(row: pd.Series) -> str:
    """Verdict per flagged row under the documented rule (resolucion_triaje.md)."""
    if row["en_alcance_climatico"] != "si":
        return "fuera_alcance_climatico"
    if row["danio_mdp"] == 0:
        return "mdp_sin_valor"
    if row["evento_id"] in _MDP_CORROBORADO:
        return "mdp_corroborado"
    if row["evento_id"] in _MDP_EXCLUIDO_DIAGNOSTICOS:
        return "mdp_excluido_diagnosticos"
    return "mdp_aceptado_submaterial"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    args = parser.parse_args()

    from climateCCR.data.inspeccion import inspect_dataset
    from climateCCR.infra import get_logger, project_paths

    paths = project_paths()
    logger = get_logger("climateCCR.inspeccion_cenapred_base", log_dir=paths.logs)
    out_dir = paths.results / "inspeccion" / "cenapred_base_2000_2015"
    annex_csv = out_dir / "triaje_razon_mdp_mdd.csv"
    if annex_csv.exists() and not args.forzar:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", annex_csv)
        return

    ev = pd.read_csv(EVENTS_CSV, low_memory=False)
    base = ev[ev["anio"] <= BASE_END_YEAR].copy()
    logger.info("2000-%d base segment: %d rows of %d", BASE_END_YEAR, len(base), len(ev))

    # 1. The standard battery (GEN-27), on the segment.
    inspect_dataset(
        base,
        out_dir,
        time_col="anio",
        group_cols=("estados", "peril_canonico"),
        ratios=(("danio_mdp", "danio_mdd"),),
        source=f"eventos_cenapred_climada 2000-{BASE_END_YEAR}",
        command=shlex.join(sys.argv),
    )

    # 2. Row-level MDP/MDD ratio triage vs the year-median FIX proxy.
    inpc = {int(y): float(v) for y, v in yaml.safe_load(INPC_CONFIG.read_text())["inpc"].items()}
    inpc_base = inpc[max(inpc)]
    base["danio_mdp_real2025"] = base["danio_mdp"] * base["anio"].map(
        lambda y: inpc_base / inpc[int(y)]
    )
    con_mdd = base[base["danio_mdd"] > 0].copy()
    con_mdd["razon"] = con_mdd["danio_mdp"] / con_mdd["danio_mdd"]
    con_mdd = con_mdd.join(
        con_mdd.groupby("anio")["razon"].median().rename("razon_mediana_anio"), on="anio"
    )
    con_mdd["factor_desvio"] = con_mdd["razon"] / con_mdd["razon_mediana_anio"]
    with np.errstate(divide="ignore"):  # razon = 0 (mdp 0, mdd > 0) -> inf deviation, flagged
        dev = np.abs(np.log10(con_mdd["factor_desvio"]))
    # Bands on |log10(razon/mediana_anio)|: > 1 decade off the year's FIX proxy
    # = error_probable (unit-scale error in one column); 0.5-1 = atipico_a_revisar.
    con_mdd["triaje"] = np.where(
        dev > 1.0, "error_probable", np.where(dev > 0.5, "atipico_a_revisar", "")
    )
    flag = con_mdd[con_mdd["triaje"] != ""].copy()
    trigger_lo, trigger_hi = TRIGGER_WINDOW
    flag["en_conjunto_disparador"] = (
        flag["en_alcance_climatico"].eq("si")
        & (flag["duracion_dias"].isna() | (flag["duracion_dias"] < 360))
        & flag["anio"].between(trigger_lo, trigger_hi)
        & (flag["danio_mdp_real2025"] >= TRIGGER_MIN_REAL_MDP)
    )
    flag["resolucion"] = flag.apply(_resolucion, axis=1)
    # The corroborated set must be exactly the trigger-set intersection: a new
    # trigger-reaching flag in a future re-derivation demands fresh human triage.
    trigger_ids = set(flag.loc[flag["en_conjunto_disparador"], "evento_id"])
    if trigger_ids != _MDP_CORROBORADO:
        sys.exit(
            f"trigger-set flags {sorted(trigger_ids)} != corroborated ids "
            f"{sorted(_MDP_CORROBORADO)} — review the resolution rule before rerunning"
        )
    cols = [
        "evento_id",
        "anio",
        "peril_canonico",
        "en_alcance_climatico",
        "estados",
        "nombre_evento",
        "danio_mdp",
        "danio_mdd",
        "razon",
        "razon_mediana_anio",
        "factor_desvio",
        "danio_mdp_real2025",
        "en_conjunto_disparador",
        "triaje",
        "resolucion",
    ]
    flag = flag[cols].sort_values("danio_mdp_real2025", ascending=False)
    flag.round(6).to_csv(annex_csv, index=False)

    in_trigger = flag[flag["en_conjunto_disparador"]]
    logger.info(
        "%d rows flagged of %d with danio_mdd > 0; %d reach the trigger set",
        len(flag),
        len(con_mdd),
        len(in_trigger),
    )
    print(flag["triaje"].value_counts().to_string())
    print(f"\nen el conjunto disparador (mayores_200mdp): {len(in_trigger)}")
    print(
        in_trigger[
            ["evento_id", "anio", "peril_canonico", "estados", "danio_mdp", "danio_mdd", "razon"]
        ].to_string(index=False)
    )
    conteos = flag["resolucion"].value_counts()
    nota = out_dir / "resolucion_triaje.md"
    nota.write_text(
        "# Resolución del triaje MDP/MDD — regla documentada (OQ-INT-11 g)\n\n"
        "Decisión de usuario 2026-08-01, aplicada por este pipeline como columna "
        "`resolucion` del anexo (GEN-27: los hallazgos requieren triaje humano y solo "
        "las reglas documentadas se aplican; esto es un veredicto sobre los hallazgos, "
        "no una mutación de datos).\n\n"
        "## Regla\n\n"
        "1. La columna `danio_mdd` de las 41 filas señaladas se **descarta** como no "
        "confiable: el FIX implícito (`razon`) queda entre 1.4e-5 y 145,135 MXN/USD "
        "frente a medianas anuales de 9.7-13.5 — ningún FIX histórico lo reproduce, y la "
        "concentración en Chiapas apunta a un defecto sistemático de captura. Ningún "
        "ajuste del proyecto consume `danio_mdd` (HAZ-CENAPRED-11), así que el descarte "
        "no cambia nada aguas abajo.\n"
        "2. `danio_mdp` se conserva si el evento está **en alcance climático** (GEN-12) y "
        "su **magnitud está justificada** frente a datos observados; si no, se excluye de "
        "los diagnósticos sin umbral. Los ajustes adoptados (`mayores_200mdp`) solo tocan "
        "las 2 filas del conjunto disparador, ambas corroboradas.\n\n"
        "## Veredictos\n\n"
        f"{conteos.to_string()}\n\n"
        "- `mdp_corroborado` — CEN-2007-02365 (deslizamiento Juan de Grijalva 2007) y "
        "CEN-2003-00712 (TS Larry 2003): en el conjunto disparador, magnitud MDP "
        "históricamente corroborada (HAZ-CENAPRED-11).\n"
        "- `mdp_excluido_diagnosticos` — CEN-2003-00460 y CEN-2003-00399 (incendios "
        "forestales Chiapas 2003, ~72-76 MDP nominales ≈ 187-196 MDP-2025): la temporada "
        "mar-abr 2003 fue activa en Chiapas (registro UNAM de evaluación de incendios; "
        "SNIF/CONAFOR sin cifras por evento a esta distancia), lo que corrobora la "
        "existencia pero no la magnitud — veredicto conservador según la regla. "
        "Sub-umbral: los ajustes adoptados no cambian bajo ningún veredicto. Para "
        "revertir, mover los ids a `_MDP_CORROBORADO` y re-ejecutar con `--forzar`.\n"
        "- `fuera_alcance_climatico` — accidentes de transporte y toxicidad: nunca "
        "entran a ningún ajuste (GEN-12).\n"
        "- `mdp_sin_valor` — `danio_mdp = 0`: nada que conservar (el ajuste lognormal "
        "descarta no-positivos).\n"
        "- `mdp_aceptado_submaterial` — resto en alcance, sub-umbral y de magnitud "
        "pequeña consistente con su contexto estado-año (z robusta en el anexo); se "
        "conservan para diagnósticos, la bandera queda registrada.\n\n"
        f"Comando: `{shlex.join(sys.argv)}`\n"
    )
    print(f"\nAnnex:  {annex_csv}\nRegla:   {nota}\nBattery: {out_dir / 'resumen.md'}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
