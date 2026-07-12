"""Climate jump figures — visualize the DC-CCR-SIM-2 demo (Phase 5.1).

Renders the climate-vs-baseline story behind pipelines/01_climate_jump_demo.py:
EE/PE profiles and shifts per counterparty (from the demo's comparison CSV),
plus process-level views — simulated HW1F short-rate and GBM share paths
jump-off vs jump-on with the shared master seed, so each climate path deviates
from its baseline twin only at the marked jump events (INT-09) — and the
Poisson-arrival mechanism check.

Requires the demo output (run pipeline 01 with the same horizon first). Same
config, same seed: figures reproduce bit-for-bit (GEN-06/07). The analysis
horizon (--horizonte largo|corto, a key of the config's `horizons` block)
selects the B3 reporting grid; figures land in results/figures/<run_name>/.
Idempotent; rerun with --forzar/--force.

    python pipelines/02_climate_jump_figures.py [--forzar] [--horizonte corto]
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

# One representative factor per diffusion family (the fixture book is USD-only:
# its IRS books simulate the USD curve, its option books the CS share). The
# counterparty that simulates each is found from the fixture ledger, not hardcoded.
PATH_FACTORS = {
    "USD_ZERO_YIELD_CURVE": "HW1F short rate",
    "CREDIT_SUISSE_SHARE": "GBM share price",
}


def find_counterparty_simulating(factor: str, global_parameters: dict) -> int:
    """First netting agreement whose portfolio simulates ``factor``."""
    from climateCCR.risk.ccr.trade_models.portfolio import Portfolio

    ledger = pd.read_csv(
        FIXTURE / "portfolio_data" / "positions_keeping_system" / "master_ledger.csv"
    )
    for naid in sorted(ledger["netting_agreement_id"].unique()):
        portfolio = Portfolio(naid)
        portfolio.load(global_parameters)
        if factor in portfolio.portfolio_underlyings:
            return naid
    raise ValueError(f"No fixture counterparty simulates {factor!r}")


def run_scenarios(global_parameters: dict, today_date: str, naid: int):
    """Run one counterparty's session; return (simulation_dates, scenarios, default_grid)."""
    from climateCCR.risk.ccr.evaluators.ccr_valuation_session import CCR_Valuation_Session
    from climateCCR.risk.ccr.trade_models.portfolio import Portfolio

    portfolio = Portfolio(naid)
    portfolio.load(global_parameters)
    session = CCR_Valuation_Session(portfolio)
    session.run(today_date, global_parameters)
    return session.simulation_dates, session.scenarios, session.b3_default_grid


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the figures exist"
    )
    parser.add_argument(
        "--horizonte",
        "--horizon",
        default="largo",
        help="analysis horizon: a key of the config's `horizons` block (largo | corto)",
    )
    args = parser.parse_args()

    from climateCCR import viz
    from climateCCR.infra import RunManifest, get_logger, load_config
    from climateCCR.processes.jumps import ClimateJumpProcess
    from climateCCR.risk.ccr.config import build_global_parameters

    config = load_config(DEMO_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.climate_jump_figures", log_dir=config.paths.logs)

    horizons = config.extra["horizons"]
    if args.horizonte not in horizons:
        parser.error(f"--horizonte must be one of {sorted(horizons)}, got {args.horizonte!r}")
    b3_grid = horizons[args.horizonte]["b3_grid"]
    run_name = (
        "climate_jump_demo" if args.horizonte == "largo" else f"climate_jump_demo_{args.horizonte}"
    )

    comparison_csv = config.paths.results / run_name / "ee_pe_climate_shift.csv"
    if not comparison_csv.exists():
        logger.error(
            "Demo output missing: %s — run `python pipelines/01_climate_jump_demo.py "
            "--horizonte %s` first.",
            comparison_csv,
            args.horizonte,
        )
        sys.exit(1)

    out_dir = config.paths.results / "figures" / run_name
    done_marker = out_dir / "event_arrivals.png"
    if done_marker.exists() and not args.forzar:
        logger.info("Figures exist, nothing to do (rerun with --forzar): %s", out_dir)
        return

    viz.apply_style()
    written: list[Path] = []

    # -- CCR result figures, straight from the comparison-frame contract.
    comparison = pd.read_csv(comparison_csv)
    written += viz.save_figure(viz.plot_exposure_profiles(comparison), out_dir / "ee_profiles")
    written += viz.save_figure(
        viz.plot_exposure_profiles(comparison, metric="uncollateralized_pe_0.99"),
        out_dir / "pe99_profiles",
    )
    written += viz.save_figure(viz.plot_exposure_shift(comparison), out_dir / "ee_shift")
    written += viz.save_figure(
        viz.plot_mean_shift_summary(comparison), out_dir / "mean_shift_summary"
    )

    # -- Process-level figures: re-simulate under the demo config (same master
    #    seed as pipeline 01, so these paths are the ones behind the CSV).
    today_date = config.extra["valuation_date"]
    jump_process = ClimateJumpProcess.from_config(config.extra["climate_jumps"])
    fixture_config = load_config(FIXTURE_CONFIG)
    gp = build_global_parameters(fixture_config, data_root=FIXTURE)
    gp["n_paths"] = config.n_paths
    gp["random_state"] = config.seed
    if b3_grid is not None:
        gp["B3_grid"] = list(b3_grid)
    max_step_days = horizons[args.horizonte].get("max_step_days")
    if max_step_days:
        gp["simulation_max_step_days"] = int(max_step_days)

    intensity = config.extra["climate_jumps"]["intensity"]
    for factor, family in PATH_FACTORS.items():
        naid = find_counterparty_simulating(factor, gp)
        logger.info("Simulating %s (%s) via counterparty %s ...", factor, family, naid)
        gp.pop("climate_jumps", None)
        dates, baseline, default_grid = run_scenarios(gp, today_date, naid)
        gp["climate_jumps"] = jump_process
        _, jumped, _ = run_scenarios(gp, today_date, naid)
        events = jump_process.generate(dates, config.n_paths, config.seed).event_counts

        # Clip the figures to the reporting horizon: the simulation always runs
        # to trade maturity (pricing needs it), but the analysis window is the
        # B3 default grid, so the plots end at its last date.
        horizon_end = max(default_grid)
        n_keep = sum(1 for d in dates if d <= horizon_end)
        dates = dates[:n_keep]
        baseline_paths = baseline[factor][:, :n_keep]
        jumped_paths = jumped[factor][:, :n_keep]
        events = events[:, : n_keep - 1]

        slug = factor.lower()
        written += viz.save_figure(
            viz.plot_sample_paths(
                dates,
                baseline_paths,
                jumped_paths,
                event_counts=events,
                n_show=4,
                ylabel=family,
                title=f"{factor} — sample paths, climate jump-on vs baseline",
            ),
            out_dir / f"paths_{slug}",
        )
        written += viz.save_figure(
            viz.plot_fan_comparison(
                dates,
                baseline_paths,
                jumped_paths,
                ylabel=family,
                title=f"{factor} — distribution fan, climate jump-on vs baseline",
            ),
            out_dir / f"fan_{slug}",
        )
        # Full trajectory set (n_show=None): the two scenario envelopes. PNG
        # only — a vector PDF of n_paths*2 lines is unusably heavy — at high
        # dpi so it stays crisp in LaTeX/slides.
        written += viz.save_figure(
            viz.plot_sample_paths(
                dates,
                baseline_paths,
                jumped_paths,
                n_show=None,
                ylabel=family,
                title=f"{factor} — all {config.n_paths} trajectories, climate jump-on vs baseline",
            ),
            out_dir / f"paths_{slug}_all",
            formats=("png",),
            dpi=600,
        )

    # Arrival diagnostic on the last grid (rates and equity share the event
    # stream by construction; the grid only sets where counts are binned).
    written += viz.save_figure(
        viz.plot_event_arrivals(dates, events, intensity=intensity),
        out_dir / "event_arrivals",
    )

    gp.pop("climate_jumps", None)
    # Record the horizon actually run, so the manifest pins the reporting grid.
    config.extra["selected_horizon"] = {
        "name": args.horizonte,
        "b3_grid": gp["B3_grid"],
        "max_step_days": max_step_days,
    }
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)
    logger.info("Wrote %d files to %s; manifest %s", len(written), out_dir, manifest_path)
    print(f"{len(written)} figure files -> {out_dir}\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
