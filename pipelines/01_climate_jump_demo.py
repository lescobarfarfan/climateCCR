"""Climate jump-injection demo — the DC-CCR-SIM-2 mechanism proof (INT-09/10).

Runs the PIMPA fixture book twice with the same master seed — jump-OFF (the
golden EE/PE baseline) and jump-ON (homogeneous Poisson arrivals shared across
both targets, one-sided lognormal adverse marks from
``configs/climate_jump_demo.yaml``) — and reports the per-counterparty EE/PE
shift. Because the jump overlay draws from its own seed substream, the two runs
share every diffusion draw and the shift is purely the climate component.

Jump parameters are arbitrary-but-plausible placeholders [eng]; the calibrated
intensity and impact distribution are HAZ's to deliver (OQ-INT-07, DC-XWALK-4).
The analysis horizon (--horizonte largo|corto, a key of the config's `horizons`
block) selects the B3 default grid the EE/PE profile is reported on; the short
grid serves risk-management horizons, the long one the regulatory/climate view.
Idempotent (GEN-*): skips if the output exists, rerun with --forzar/--force.

    python pipelines/01_climate_jump_demo.py [--forzar] [--horizonte corto]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "pimpa"
DEMO_CONFIG = REPO_ROOT / "configs" / "climate_jump_demo.yaml"
FIXTURE_CONFIG = REPO_ROOT / "configs" / "pimpa_fixture.yaml"

VALUE_COLS = ["uncollateralized_ee", "uncollateralized_pe_0.99"]


def run_book(global_parameters: dict, today_date: str) -> pd.DataFrame:
    """EE/PE profiles for every counterparty in the fixture ledger."""
    from climateCCR.risk.ccr.evaluators.ccr_valuation_session import CCR_Valuation_Session
    from climateCCR.risk.ccr.trade_models.portfolio import Portfolio

    ledger = pd.read_csv(
        FIXTURE / "portfolio_data" / "positions_keeping_system" / "master_ledger.csv"
    )
    frames = []
    for naid in sorted(ledger["netting_agreement_id"].unique()):
        portfolio = Portfolio(naid)
        portfolio.load(global_parameters)
        session = CCR_Valuation_Session(portfolio)
        session.run(today_date, global_parameters)
        exposures = session.get_exposures().copy()
        exposures.insert(0, "netting_agreement_id", naid)
        frames.append(exposures)
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    parser.add_argument(
        "--horizonte",
        "--horizon",
        default="largo",
        help="analysis horizon: a key of the config's `horizons` block (largo | corto)",
    )
    args = parser.parse_args()

    from climateCCR.infra import RunManifest, get_logger, load_config
    from climateCCR.processes.jumps import ClimateJumpProcess
    from climateCCR.risk.ccr.config import build_global_parameters

    config = load_config(DEMO_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.climate_jump_demo", log_dir=config.paths.logs)

    horizons = config.extra["horizons"]
    if args.horizonte not in horizons:
        parser.error(f"--horizonte must be one of {sorted(horizons)}, got {args.horizonte!r}")
    b3_grid = horizons[args.horizonte]["b3_grid"]  # None = the fixture's long default grid

    run_name = (
        "climate_jump_demo" if args.horizonte == "largo" else f"climate_jump_demo_{args.horizonte}"
    )
    out_dir = config.paths.results / run_name
    out_csv = out_dir / "ee_pe_climate_shift.csv"
    if out_csv.exists() and not args.forzar:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", out_csv)
        return

    today_date = config.extra["valuation_date"]
    jump_process = ClimateJumpProcess.from_config(config.extra["climate_jumps"])
    logger.info(
        "Climate jump config: intensity=%s /yr, targets=%s",
        config.extra["climate_jumps"]["intensity"],
        sorted(jump_process.targets),
    )

    fixture_config = load_config(FIXTURE_CONFIG)
    gp = build_global_parameters(fixture_config, data_root=FIXTURE)
    gp["n_paths"] = config.n_paths
    gp["random_state"] = config.seed
    if b3_grid is not None:
        gp["B3_grid"] = list(b3_grid)
    max_step_days = horizons[args.horizonte].get("max_step_days")
    if max_step_days:
        gp["simulation_max_step_days"] = int(max_step_days)
    logger.info(
        "Horizon %r: B3 default grid %s, max simulation step %s",
        args.horizonte,
        gp["B3_grid"],
        max_step_days or "event-driven",
    )

    logger.info("Running jump-OFF (baseline) ...")
    baseline = run_book(gp, today_date)
    logger.info("Running jump-ON (climate) ...")
    gp["climate_jumps"] = jump_process
    jumped = run_book(gp, today_date)

    comparison = baseline[["netting_agreement_id", "default_times"]].copy()
    for col in VALUE_COLS:
        comparison[f"{col}_baseline"] = baseline[col]
        comparison[f"{col}_climate"] = jumped[col]
        comparison[f"{col}_shift"] = jumped[col] - baseline[col]

    out_dir.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(out_csv, index=False)
    # Record the horizon actually run, so the manifest pins the reporting grid.
    config.extra["selected_horizon"] = {
        "name": args.horizonte,
        "b3_grid": gp["B3_grid"],
        "max_step_days": max_step_days,
    }
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)

    summary = comparison.groupby("netting_agreement_id")[
        [f"{col}_shift" for col in VALUE_COLS]
    ].mean()
    logger.info("Mean EE/PE shift by counterparty (climate - baseline):\n%s", summary)
    logger.info("Wrote %s and manifest %s", out_csv, manifest_path)
    print(summary.to_string(float_format=lambda v: f"{v:+.2f}"))
    print(f"\nComparison: {out_csv}\nManifest:   {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
