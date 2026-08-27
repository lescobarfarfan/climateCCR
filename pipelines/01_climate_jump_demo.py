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
With ``--trayectorias``, both legs also materialize the per-path portfolio
values at the reporting dates (``per_path_values_{baseline,climate}.npz``,
the OQ-GEN-02 c artifact) — the profiles themselves are byte-identical.
With ``--choques-programados <fragmento>``, the INT-33 scheduled overlay
(a pipelines/22 fragment) applies to BOTH legs — the "fase" NGFS state
(OQ-INT-12 a) — so the jump-ON vs jump-OFF contrast stays the pure physical
channel; the fragment's valuation_date must match the run config's.

    python pipelines/01_climate_jump_demo.py [--forzar] [--horizonte corto] [--trayectorias]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "pimpa"
DEMO_CONFIG = REPO_ROOT / "configs" / "climate_jump_demo.yaml"
FIXTURE_CONFIG = REPO_ROOT / "configs" / "pimpa_fixture.yaml"

VALUE_COLS = ["uncollateralized_ee", "uncollateralized_pe_0.99"]


def run_book(
    global_parameters: dict,
    today_date: str,
    data_root: Path = FIXTURE,
    per_path_store: dict | None = None,
) -> pd.DataFrame:
    """EE/PE profiles for every counterparty in the book's ledger.

    With ``per_path_store`` a dict, each counterparty's per-path netted
    portfolio values at the reporting dates land there as
    ``naid -> (dates, values)`` — the OQ-GEN-02 c artifact seam. The engine
    run is unchanged either way (the values are read off the session after
    ``run``, no extra draws).
    """
    from climateCCR.risk.ccr.evaluators.artifacts import grid_dates, reporting_slice
    from climateCCR.risk.ccr.evaluators.ccr_valuation_session import CCR_Valuation_Session
    from climateCCR.risk.ccr.trade_models.portfolio import Portfolio

    ledger = pd.read_csv(
        data_root / "portfolio_data" / "positions_keeping_system" / "master_ledger.csv"
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
        if per_path_store is not None:
            per_path_store[str(naid)] = (
                grid_dates(session.b3_default_grid),
                reporting_slice(
                    session.simulation_dates,
                    session.b3_default_grid,
                    session.scenarios_portfolio_values,
                ),
            )
    return pd.concat(frames, ignore_index=True)


def load_scheduled_fragment(path: Path, today_date: str) -> dict:
    """Read a pipelines/22 fragment, failing loudly on a valuation-date mismatch.

    The fragment's times_years are Act/365 fractions from ITS valuation date;
    injecting them into a run valued elsewhere would silently shift the whole
    scenario calendar (OQ-INT-12 a).
    """
    fragment = yaml.safe_load(path.read_text())
    frag_date = fragment.get("provenance", {}).get("valuation_date")
    if frag_date != today_date:
        raise ValueError(
            f"scheduled_shocks fragment valuation_date {frag_date!r} != run "
            f"valuation_date {today_date!r} — regenerate with pipelines/22"
        )
    return fragment


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
    parser.add_argument(
        "--config",
        type=Path,
        default=DEMO_CONFIG,
        help="climate-jump config (default: the placeholder demo; "
        "configs/climate_jump_real.yaml = the estimated parameters)",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=FIXTURE,
        help="book data root (default: the PIMPA fixture; "
        "data/ccr_book_mx = the Mexican book, OQ-INT-04)",
    )
    parser.add_argument(
        "--trayectorias",
        action="store_true",
        help="materializa además los valores de cartera por trayectoria en las fechas de "
        "reporte (per_path_values_{baseline,climate}.npz por corrida; OQ-GEN-02 c)",
    )
    parser.add_argument(
        "--book-config",
        type=Path,
        default=FIXTURE_CONFIG,
        help="book layout config (default: configs/pimpa_fixture.yaml)",
    )
    parser.add_argument(
        "--etiqueta",
        "--label",
        default=None,
        help="run-name suffix distinguishing runs that share a config but not a "
        "data root (e.g. an NGFS scenario overlay: --etiqueta ngfs_hwtp)",
    )
    parser.add_argument(
        "--choques-programados",
        "--scheduled-shocks",
        type=Path,
        default=None,
        help="fragmento scheduled_shocks de pipelines/22 aplicado a AMBAS corridas "
        "(jump-OFF y jump-ON) — el estado 'fase' del mundo NGFS (OQ-INT-12 a); "
        "el contraste ON-OFF queda como el canal físico puro",
    )
    args = parser.parse_args()

    from climateCCR.infra import RunManifest, get_logger, load_config
    from climateCCR.processes.jumps import ClimateJumpProcess
    from climateCCR.risk.ccr.config import build_global_parameters

    config = load_config(args.config)
    config.paths.ensure()
    logger = get_logger("climateCCR.climate_jump_demo", log_dir=config.paths.logs)

    horizons = config.extra["horizons"]
    if args.horizonte not in horizons:
        parser.error(f"--horizonte must be one of {sorted(horizons)}, got {args.horizonte!r}")
    b3_grid = horizons[args.horizonte]["b3_grid"]  # None = the fixture's long default grid

    run_name = (
        args.config.stem if args.horizonte == "largo" else f"{args.config.stem}_{args.horizonte}"
    )
    if args.etiqueta:
        run_name = f"{run_name}_{args.etiqueta}"
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

    fixture_config = load_config(args.book_config)
    gp = build_global_parameters(fixture_config, data_root=args.data_root)
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

    if args.choques_programados:
        from climateCCR.processes.scheduled_shocks import ScheduledShockOverlay

        fragment = load_scheduled_fragment(args.choques_programados, today_date)
        gp["scheduled_shocks"] = ScheduledShockOverlay.from_config(fragment["scheduled_shocks"])
        # Manifest completeness (GEN-06): the resolved fragment rides the manifest.
        config.extra["scheduled_shocks"] = fragment
        logger.info("Scheduled shocks (fase) from %s -> both legs", args.choques_programados)

    baseline_store: dict | None = {} if args.trayectorias else None
    jumped_store: dict | None = {} if args.trayectorias else None
    logger.info("Running jump-OFF (baseline) ...")
    baseline = run_book(gp, today_date, data_root=args.data_root, per_path_store=baseline_store)
    logger.info("Running jump-ON (climate) ...")
    gp["climate_jumps"] = jump_process
    jumped = run_book(gp, today_date, data_root=args.data_root, per_path_store=jumped_store)

    comparison = baseline[["netting_agreement_id", "default_times"]].copy()
    for col in VALUE_COLS:
        comparison[f"{col}_baseline"] = baseline[col]
        comparison[f"{col}_climate"] = jumped[col]
        comparison[f"{col}_shift"] = jumped[col] - baseline[col]

    out_dir.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(out_csv, index=False)
    if args.trayectorias:
        from climateCCR.risk.ccr.evaluators.artifacts import write_per_path_values

        for leg, store in (("baseline", baseline_store), ("climate", jumped_store)):
            leg_path = write_per_path_values(store, out_dir / f"per_path_values_{leg}.npz")
            logger.info("Per-path portfolio values (%s) -> %s", leg, leg_path)
    # Record the horizon actually run, so the manifest pins the reporting grid —
    # and the data root + label, so scenario-overlay runs (--etiqueta) are
    # distinguishable in the manifest from the config alone.
    config.extra["selected_horizon"] = {
        "name": args.horizonte,
        "b3_grid": gp["B3_grid"],
        "max_step_days": max_step_days,
    }
    config.extra["data_root"] = str(args.data_root)
    if args.etiqueta:
        config.extra["run_label"] = args.etiqueta
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
