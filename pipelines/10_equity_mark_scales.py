"""Sector-differentiated equity mark scales — OQ-INT-11 (DC-XWALK-4, DC-CCR-SIM-2).

Composes per-name relative sensitivities ``gamma_i`` for the Mexican book
equities (G x S x H per ``configs/equity_mark_scales.yaml``), renormalized so
the book-notional-weighted mean is exactly 1 — the INT-17 book-level mark is
redistributed, never re-estimated. Emits the ``target_scales:`` YAML block for
``configs/climate_jump_real_mexican*.yaml`` plus the CNSF hidro USO x evento
evidence table backing the S-matrix ordering.

Phase B (peril-typed events): also estimates the trigger-set frequency peril
mix ``pi`` (measurement-consistent with the INT-20 lambda) and the per-name
per-peril scales ``c[i, p] = gamma_i^p / pi_p`` consumed by
``ClimateJumpProcess`` — validated so ``sum_p pi_p c[i, p] == gamma_i`` to
float precision (the Phase A per-name mean is preserved exactly; peril typing
only redistributes impact across events).

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
        peril_mix_from_events,
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

    # Phase B: trigger-set frequency peril mix + per-name per-peril scales.
    mix_spec = extra["peril_mix_events"]
    mix = peril_mix_from_events(
        config.paths.root / mix_spec["events_csv"],
        deflator=deflator,
        peril_groups=extra["peril_groups"],
        start_year=int(mix_spec["window"]["start_year"]),
        end_year=int(mix_spec["window"]["end_year"]),
        min_damage_mdp=float(mix_spec["min_damage_mdp"]),
    )
    peril_cols = list(intensity.columns)
    missing_groups = sorted(set(peril_cols) - set(mix.index))
    if missing_groups:
        # A group with damage in H but no trigger-set arrivals would make c
        # undefined; its gamma component would be unreachable. Fail loudly.
        sys.exit(f"peril groups absent from the trigger set: {missing_groups}")
    gamma_p = scales[[f"gamma_{p}" for p in peril_cols]].copy()
    gamma_p.columns = peril_cols
    c_scales = gamma_p.div(mix.reindex(peril_cols), axis=1)
    identity = (c_scales * mix.reindex(peril_cols)).sum(axis=1) - scales["gamma"]
    if identity.abs().max() > 1e-12:
        worst = identity.abs().max()
        sys.exit(f"anchor identity broken: max |sum_p pi_p c_ip - gamma_i| = {worst}")
    logger.info(
        "peril mix (trigger-set frequency): %s",
        ", ".join(f"{p}={mix[p]:.4f}" for p in peril_cols),
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    scales.round(6).to_csv(out_csv)
    by_sector = (
        scales.groupby("sector")["gamma"].agg(["mean", "min", "max", "count"]).sort_values("mean")
    )
    by_sector.round(6).to_csv(out_dir / "sector_scales.csv")
    intensity.round(9).to_csv(out_dir / "damage_intensity_state_peril.csv")
    evidence.round(6).to_csv(out_dir / "cnsf_uso_peril_shares.csv")
    mix.rename("pi").round(6).to_csv(out_dir / "peril_mix.csv")
    c_scales.round(6).to_csv(out_dir / "target_peril_scales.csv")
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)

    print(scales.round(4).to_string())
    print(f"\nsum w*gamma = {anchor:.12f}")
    print(f"max |sum_p pi_p c_ip - gamma_i| = {identity.abs().max():.2e}")
    print("\n# --- paste into equity_marks of configs/climate_jump_real_mexican*.yaml ---")
    print("    peril_mix:  # trigger-set frequency shares (pipelines/10, OQ-INT-11 Phase B)")
    for p in peril_cols:
        # 8 decimals: six rounded probabilities must still sum to 1 within the
        # engine's 1e-6 validation tolerance.
        print(f"      {p}: {mix[p]:.8f}")
    print("    target_peril_scales:  # c_ip = gamma_i^p / pi_p; sum_p pi_p c_ip = gamma_i")
    for name, row in c_scales.iterrows():
        inner = ", ".join(f"{p}: {row[p]:.6f}" for p in peril_cols)
        print(f"      {name}: {{{inner}}}")
    print(f"\nScales:   {out_csv}\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
