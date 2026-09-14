"""SIE compounding check — MKT-SIE-04 verified on Banxico's own series (OQ-MKT-01).

Banxico defines the *TIIE de Fondeo compuesta por adelantado a T días* as
``[(I_D / I_{D-28})^{T/28} - 1] * 36000 / T`` on the business-day-composition
*Índice de TIIE de Fondeo* — a simple Act/360 annualisation of the trailing
28-day index ratio ([BanxicoTIIEFondeoNota]; official source Circular 3/2012).
This script rebuilds the index from the overnight F-TIIE fixings
(``tiies.csv``), reproduces the three published term series
(``tiies_compuestas.csv``) under the simple reading, and shows that the
annually-compounded reading behind the rejected ``(365/360)*ln(1+r)``
conversion does not reproduce them.

Writes ``results/sie_compounding_check/resumen.csv`` — one row per plazo:
``plazo, n_obs, mad_bp_simple, max_bp_simple, mad_bp_compuesta_anual,
max_bp_compuesta_anual, index_dev_bp`` (the last = max relative gap between the
rebuilt index and Banxico's published one, in bp) — plus a run manifest.
Deterministic; idempotent (GEN-05): skips if the output exists, rerun with
--forzar/--force.

    python pipelines/25_sie_compounding_check.py [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SIE_CONFIG = REPO_ROOT / "configs" / "sie_series.yaml"
#: Published term series (configs/sie_series.yaml ``tiies_compuestas``) -> plazo in days.
PLAZOS = {"FTIIE28C": 28, "FTIIE91C": 91, "FTIIE182C": 182}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    args = parser.parse_args()

    from climateCCR.calibration.financial.hull_white import term_rate_readings, tiie_fondeo_index
    from climateCCR.infra import RunManifest, get_logger, load_config

    config = load_config(SIE_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.sie_compounding_check", log_dir=config.paths.logs)

    out_dir = config.paths.results / "sie_compounding_check"
    out_csv = out_dir / "resumen.csv"
    if out_csv.exists() and not args.forzar:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", out_csv)
        return

    sie_dir = config.paths.root / config.extra["sie_dir"]

    def read(group: str) -> pd.DataFrame:
        path = sie_dir / f"{group}.csv"
        if not path.exists():
            sys.exit(f"SIE series not found: {path} (run pipelines/05_download_sie_series.py)")
        return pd.read_csv(path, parse_dates=["Fecha"], index_col="Fecha")

    overnight = read("tiies")["FTIIE"]
    published = read("tiies_compuestas")
    index = tiie_fondeo_index(overnight)

    # The rebuilt index vs Banxico's published one: ratios must agree to rounding,
    # otherwise the term-rate comparison below is testing the wrong object.
    official = published["IndiceHabiles"].dropna()
    common = index.index.intersection(official.index)
    index_dev_bp = ((index.loc[common] / official.loc[common] - 1.0).abs() * 1e4).max()
    logger.info(
        "rebuilt index vs published: max |ratio - 1| = %.4f bp (%d dates)",
        index_dev_bp,
        len(common),
    )

    rows = []
    for column, days in PLAZOS.items():
        readings = term_rate_readings(index, days)
        joined = readings.join(published[column].dropna().rename("publicada"), how="inner")
        diff_bp = joined[["simple", "compuesta_anual"]].sub(joined["publicada"], axis=0) * 100.0
        rows.append(
            {
                "plazo": days,
                "n_obs": len(joined),
                "mad_bp_simple": diff_bp["simple"].abs().mean(),
                "max_bp_simple": diff_bp["simple"].abs().max(),
                "mad_bp_compuesta_anual": diff_bp["compuesta_anual"].abs().mean(),
                "max_bp_compuesta_anual": diff_bp["compuesta_anual"].abs().max(),
                "index_dev_bp": index_dev_bp,
            }
        )
        logger.info(
            "plazo %d: %d obs, simple MAD %.3f bp", days, len(joined), rows[-1]["mad_bp_simple"]
        )

    table = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_csv, index=False)
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)
    print(table.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    print(f"\nResumen:  {out_csv}\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
