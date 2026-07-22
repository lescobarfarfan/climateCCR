"""Hazard jump-channel calibration — OQ-INT-07 / OQ-HAZ-12 (DC-XWALK-4).

Per event-set variant of ``configs/hazard_jump_calibration.yaml``, fits the
Poisson arrival intensity (MLE + exact CI + log-linear trend with its
likelihood-ratio p-value) and the lognormal per-event loss severity of the
discrete climate-scope CENAPRED events, writing one parameter row per variant
to ``results/hazard_jump_calibration/parameters.csv``.

The table is the estimation side of the jump channel: ``intensity_per_yr``
plugs into ``climate_jumps.intensity`` (events/year), and the severity maps
onto ``LognormalMark`` once the loss->mark scale ``K`` is fixed (OQ-INT-04):
``median_mark = sev_median_mdp / K``, ``sigma`` unchanged.

Deterministic (no randomness). Idempotent (GEN-05): skips if the output
exists, rerun with --forzar/--force.

    python pipelines/03_hazard_jump_calibration.py [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CALIB_CONFIG = REPO_ROOT / "configs" / "hazard_jump_calibration.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    parser.add_argument("--config", type=Path, default=CALIB_CONFIG, help="calibration config YAML")
    args = parser.parse_args()

    from climateCCR.calibration.impact import (
        annual_event_counts,
        estimate_intensity,
        fit_intensity_trend,
        fit_severity,
        load_climate_events,
    )
    from climateCCR.infra import RunManifest, get_logger, load_config

    config = load_config(args.config)
    config.paths.ensure()
    logger = get_logger("climateCCR.hazard_jump_calibration", log_dir=config.paths.logs)

    out_dir = config.paths.results / config.extra.get("output_dir", "hazard_jump_calibration")
    out_csv = out_dir / "parameters.csv"
    if out_csv.exists() and not args.forzar:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", out_csv)
        return

    events_csv = config.paths.root / config.extra["events_csv"]
    if not events_csv.exists():
        sys.exit(
            f"Event table not found: {events_csv}\n"
            "The CENAPRED consolidado lives under data/hazard_mx (GEN-24, git-ignored); "
            "reconstruct it with the CENAPRED pipeline if missing."
        )
    window = config.extra["window"]
    alpha = float(config.extra["alpha"])

    deflator = None
    base_year = None
    if config.extra.get("deflator"):
        deflator_file = config.paths.root / config.extra["deflator"]
        deflator = {
            int(y): float(v) for y, v in yaml.safe_load(deflator_file.read_text())["inpc"].items()
        }
        base_year = max(deflator)
        logger.info("Deflating losses to %d pesos via %s (GEN-13)", base_year, deflator_file)

    rows = []
    for name, spec in config.extra["variants"].items():
        v_window = spec.get("window", window)
        events = load_climate_events(
            events_csv,
            start_year=int(v_window["start"]),
            end_year=int(v_window["end"]),
            perils=spec.get("perils"),
            min_damage_mdp=spec.get("min_damage_mdp"),
            deflator=deflator,
        )
        counts = annual_event_counts(events)
        intensity = estimate_intensity(counts, alpha=alpha)
        trend = fit_intensity_trend(counts)
        severity = fit_severity(events, deflated=deflator is not None)
        logger.info(
            "%s: %d events, lambda=%.1f/yr [%.1f, %.1f], arrivals growth %+.1f%%/yr (p=%.3f), "
            "severity median %.2f MDP sigma %.2f, severity growth %+.1f%%/yr (p=%.3f)",
            name,
            intensity.n_events,
            intensity.intensity,
            intensity.ci_low,
            intensity.ci_high,
            100 * np.expm1(trend.growth),
            trend.p_value,
            severity.median,
            severity.sigma,
            100 * np.expm1(severity.trend_growth),
            severity.trend_p_value,
        )
        rows.append(
            {
                "variant": name,
                "window_start": int(v_window["start"]),
                "window_end": int(v_window["end"]),
                "n_events": intensity.n_events,
                "n_years": intensity.n_years,
                "intensity_per_yr": intensity.intensity,
                "intensity_ci_low": intensity.ci_low,
                "intensity_ci_high": intensity.ci_high,
                "arrivals_growth_log_yr": trend.growth,
                "arrivals_trend_level": trend.level,
                "arrivals_trend_year_ref": trend.year_ref,
                "arrivals_trend_p": trend.p_value,
                "sev_median_mdp": severity.median,
                "sev_sigma": severity.sigma,
                "sev_n_events": severity.n_events,
                "sev_n_dropped": severity.n_dropped,
                "sev_growth_log_yr": severity.trend_growth,
                "sev_trend_p": severity.trend_p_value,
                "deflated": severity.deflated,
                "deflator_base_year": base_year,
            }
        )

    table = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_csv, index=False)
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)
    logger.info("Wrote %s and manifest %s", out_csv, manifest_path)
    print(table.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    print(f"\nParameters: {out_csv}\nManifest:   {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
