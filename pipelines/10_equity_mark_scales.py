"""Sector-differentiated equity mark scales — OQ-INT-11 (DC-XWALK-4, DC-CCR-SIM-2).

Composes per-name relative sensitivities ``gamma_i`` for the Mexican book
equities (G x S x H per ``configs/equity_mark_scales.yaml``), renormalized so
the book-notional-weighted mean is exactly 1 — the INT-17 book-level mark is
redistributed, never re-estimated. Emits the ``target_scales:`` YAML block for
``configs/climate_jump_real_mexican*.yaml`` plus the CNSF hidro USO x evento
evidence table backing the S-matrix ordering.

Deterministic (no RNG); idempotent (GEN-05): skips if the output exists, rerun
with --forzar/--force.

    python pipelines/10_equity_mark_scales.py [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCALES_CONFIG = REPO_ROOT / "configs" / "equity_mark_scales.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    args = parser.parse_args()

    from climateCCR.calibration.impact.sector_scales import (
        book_equity_weights,
        cnsf_uso_peril_evidence,
        compose_scales,
        load_damage_intensity,
    )
    from climateCCR.infra import RunManifest, get_logger, load_config

    config = load_config(SCALES_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.equity_mark_scales", log_dir=config.paths.logs)

    out_dir = config.paths.results / "equity_mark_scales"
    out_csv = out_dir / "target_scales.csv"
    if out_csv.exists() and not args.forzar:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", out_csv)
        return

    extra = config.extra
    deflator_file = config.paths.root / extra["deflator"]
    deflator = {
        int(y): float(v) for y, v in yaml.safe_load(deflator_file.read_text())["inpc"].items()
    }
    book = yaml.safe_load((config.paths.root / extra["book_config"]).read_text())
    equities = book["equities"]

    intensity = load_damage_intensity(
        config.paths.root / extra["cenapred_panel"],
        deflator=deflator,
        peril_groups=extra["peril_groups"],
        population=extra["poblacion_2020"],
        start_year=int(extra["window"]["start_year"]),
        end_year=int(extra["window"]["end_year"]),
    )
    weights = book_equity_weights(
        config.paths.root / extra["eq_desk"], [eq["rf"] for eq in equities]
    )
    scales = compose_scales(
        equities,
        susceptibility=extra["susceptibility"],
        geo_exposure=extra["exposicion_geografica"],
        population=extra["poblacion_2020"],
        intensity=intensity,
        weights=weights,
    )
    anchor = float((weights.reindex(scales.index) * scales["gamma"]).sum())
    if abs(anchor - 1.0) > 1e-9:
        sys.exit(f"renormalization broken: sum w*gamma = {anchor!r} != 1")
    logger.info(
        "gamma composed for %d names (sum w*gamma = %.12f); range %.3f (%s) - %.3f (%s)",
        len(scales),
        anchor,
        scales["gamma"].min(),
        scales["gamma"].idxmin(),
        scales["gamma"].max(),
        scales["gamma"].idxmax(),
    )

    evidence = cnsf_uso_peril_evidence(config.paths.root / extra["cnsf_hidro_siniestros"])

    out_dir.mkdir(parents=True, exist_ok=True)
    scales.round(6).to_csv(out_csv)
    by_sector = (
        scales.groupby("sector")["gamma"].agg(["mean", "min", "max", "count"]).sort_values("mean")
    )
    by_sector.round(6).to_csv(out_dir / "sector_scales.csv")
    intensity.round(9).to_csv(out_dir / "damage_intensity_state_peril.csv")
    evidence.round(6).to_csv(out_dir / "cnsf_uso_peril_shares.csv")
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)

    print(scales.round(4).to_string())
    print(f"\nsum w*gamma = {anchor:.12f}")
    print("\n# --- paste into equity_marks of configs/climate_jump_real_mexican*.yaml ---")
    print("    target_scales:  # pipelines/10, results/equity_mark_scales (OQ-INT-11)")
    for name, gamma in scales["gamma"].items():
        print(f"      {name}: {gamma:.6f}")
    print(f"\nScales:   {out_csv}\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
