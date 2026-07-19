"""Loss->mark scale derivation — OQ-INT-04 / OQ-INT-07a (DC-XWALK-4).

Fixes the translation from a CENAPRED event loss ``L`` (real MDP) to a jump
mark on the price target: ``mark = beta * L / K = L / K_eff``. ``beta`` is the
pass-through (insured payouts of the climate-exposed CNSF book over CENAPRED
discrete damage on the overlap window); ``K`` is the book's annual real premium
volume in ``k_year``. ``K_eff`` feeds ``LognormalSeverityFit.to_mark_sampler``
unchanged, so the fitted severity shape transfers exactly.

Writes one row to ``results/loss_to_mark_scale/scale.csv``. Deterministic;
idempotent (GEN-05): skips if the output exists, rerun with --forzar/--force.

    python pipelines/04_loss_to_mark_scale.py [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCALE_CONFIG = REPO_ROOT / "configs" / "loss_to_mark_scale.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    args = parser.parse_args()

    from climateCCR.calibration.impact import (
        annual_real_amounts,
        derive_loss_to_mark_scale,
        load_climate_events,
    )
    from climateCCR.infra import RunManifest, get_logger, load_config

    config = load_config(SCALE_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.loss_to_mark_scale", log_dir=config.paths.logs)

    out_dir = config.paths.results / "loss_to_mark_scale"
    out_csv = out_dir / "scale.csv"
    if out_csv.exists() and not args.forzar:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", out_csv)
        return

    deflator_file = config.paths.root / config.extra["deflator"]
    deflator = {
        int(y): float(v) for y, v in yaml.safe_load(deflator_file.read_text())["inpc"].items()
    }

    def panel(entries: list[dict]) -> pd.Series:
        total = pd.Series(dtype=float)
        for entry in entries:
            path = config.paths.root / entry["file"]
            if not path.exists():
                sys.exit(
                    f"CNSF consolidado not found: {path}\n"
                    "data/hazard_mx is git-ignored (GEN-24); corrected agro copies come "
                    "from corregir_consolidados_agricola.py (DC-HAZ-CNSF-6)."
                )
            total = total.add(annual_real_amounts(path, entry["column"], deflator), fill_value=0.0)
        return total

    paid = panel(config.extra["cnsf"]["paid"])
    premium = panel(config.extra["cnsf"]["premium"])

    beta_window = (
        int(config.extra["beta_window"]["start"]),
        int(config.extra["beta_window"]["end"]),
    )
    events = load_climate_events(
        config.paths.root / config.extra["events_csv"],
        start_year=beta_window[0],
        end_year=beta_window[1],
        deflator=deflator,
    )
    damage = events.assign(_d=events["danio_mdp"].fillna(0.0)).groupby("anio")["_d"].sum()

    scale = derive_loss_to_mark_scale(
        paid, premium, damage, beta_window=beta_window, k_year=int(config.extra["k_year"])
    )
    logger.info(
        "beta=%.4f (paid %.0f / damage %.0f MDP, %d-%d; yearly ratio %.3f-%.3f), "
        "K=%.0f MDP (%d premium), K_eff=%.0f MDP",
        scale.beta,
        scale.paid_mdp,
        scale.damage_mdp,
        scale.beta_start,
        scale.beta_end,
        scale.yearly_ratio_min,
        scale.yearly_ratio_max,
        scale.k_mdp,
        scale.k_year,
        scale.k_eff_mdp,
    )

    table = pd.DataFrame([asdict(scale)])
    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_csv, index=False)
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)
    print(table.to_string(index=False, float_format=lambda v: f"{v:.6g}"))
    print(
        f"\nequity_marks.median for a severity fit = sev_median_mdp / {scale.k_eff_mdp:.0f}"
        f"\nScale:    {out_csv}\nManifest: {manifest_path}"
    )


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
