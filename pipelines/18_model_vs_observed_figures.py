"""Model-vs-observed validation figures — calibrated models against reality.

The OQ-GEN-02 (a) backtest overlays: simulations from the ADOPTED calibrations
drawn over the observed series they model, with empirical band coverage
annotated (the fan-chart backtest), plus the climate-jump point-process
diagnostics against the CENAPRED record:

- ``fan_ftiie_insample`` / ``fan_ftiie_conditional`` — P-measure Vasicek
  short-rate cone (weekly-MLE ``a``/``level``/``sigma``, MKT-CALIB-08) vs
  observed F-TIIE, from the fit-window start and conditionally from
  ``r(conditional_start)`` (a true <= cutoff refit is unidentified — see the
  config note). ``*_all`` = the all-trajectory render (PNG-only, 600 dpi,
  GEN-22);
- ``fan_equities_headline`` / ``fan_equities_holdout`` / ``fan_equities_all``
  / ``fan_equities_holdout_all`` —
  per-name GBM cones (book RFE params) vs observed closes, panel grids;
- ``jump_staircase`` — observed cumulative arrivals vs per-regime Poisson
  bands across the 2016 publication break (HAZ-CENAPRED-10);
- ``jump_marked_arrivals`` — observed vs one simulated marked path;
- ``jump_qq_interarrival`` / ``jump_qq_severity`` — Exponential(lambda) and
  fitted-lognormal QQ on the registry trigger set;
- ``jump_paths_daily`` / ``jump_fan_daily`` — jump-on vs jump-off price
  trajectories at DAILY grain for one book name, using the engine's own
  ``ClimateJumpProcess`` (peril scaling included) and the multiplicative
  overlay convention — the fine-grain companion to pipelines/02's B3-ladder
  paths, whose sparse far pillars turn trajectories into multi-year chords.

Same config + seed -> same figures (GEN-06/07); idempotent, rerun with
``--forzar``. ``--root`` points data/results at another checkout (worktree runs).

    python pipelines/18_model_vs_observed_figures.py [--config CFG] [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "model_vs_observed.yaml"


def _simulate_gbm(
    s0: float,
    drift: float,
    volatility: float,
    grid: pd.DatetimeIndex,
    n_paths: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Exact lognormal GBM paths on ``grid`` (path-major), Act/365 like the engine."""
    dt = (np.diff(grid.to_numpy()) / np.timedelta64(1, "D")) / 365.0
    steps = (drift - 0.5 * volatility**2) * dt + volatility * np.sqrt(dt) * rng.standard_normal(
        (int(n_paths), len(dt))
    )
    log_paths = np.concatenate([np.zeros((int(n_paths), 1)), np.cumsum(steps, axis=1)], axis=1)
    return float(s0) * np.exp(log_paths)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the figures exist"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="project root for data/ and results/ (defaults to auto-discovery)",
    )
    args = parser.parse_args()

    import yaml
    from climateCCR import viz
    from climateCCR.calibration.financial.gbm import fit_gbm
    from climateCCR.calibration.financial.hull_white import (
        VasicekFit,
        exclude_windows,
        simple_to_continuous,
    )
    from climateCCR.calibration.impact.hazard_jump import load_climate_events
    from climateCCR.infra import ProjectPaths, RunManifest, get_logger, get_rng, load_config
    from climateCCR.processes.jumps.climate_jump_process import ClimateJumpProcess
    from scipy import stats

    config = load_config(args.config)
    if args.root is not None:
        config.paths = ProjectPaths(root=args.root.resolve())
    config.paths.ensure()
    logger = get_logger("climateCCR.model_vs_observed", log_dir=config.paths.logs)
    root = config.paths.root
    extra = config.extra

    out_dir = config.paths.results / "figures" / str(extra["run_name"])
    if (out_dir / "fan_ftiie_insample.png").exists() and not args.forzar:
        logger.info("Figures exist, nothing to do (rerun with --forzar): %s", out_dir)
        return

    quantiles = tuple(float(q) for q in extra["quantiles"])
    coverage_band = float(extra["coverage_band"])
    n_paths = int(config.n_paths)
    viz.apply_style()
    written: list[Path] = []

    mc = yaml.safe_load((root / extra["market_calibration_config"]).read_text())
    crisis_windows = [tuple(w) for w in mc["crisis_windows"].values()]
    headline_cell = mc["hw1f"]["headline"]

    # --- rates: P-measure Vasicek vs observed F-TIIE ----------------------
    rates_cfg = extra["rates"]
    tiies = pd.read_csv(root / rates_cfg["tiies_csv"], index_col=0, parse_dates=True)
    quotes = tiies[str(rates_cfg["proxy"])].dropna() / 100.0
    observed_rate = pd.Series(
        simple_to_continuous(quotes.to_numpy(), float(rates_cfg["tenor_days"])),
        index=quotes.index,
    )

    by_window = pd.read_csv(root / rates_cfg["by_window_csv"])
    cell = by_window[
        (by_window["proxy"] == headline_cell["proxy"])
        & (by_window["window"] == headline_cell["window"])
        & (by_window["sampling"] == headline_cell["sampling"])
        & (by_window["method"] == headline_cell["method"])
        & (by_window["crisis_excluded"] == bool(headline_cell["crisis_excluded"]))
    ]
    if len(cell) != 1:
        sys.exit(f"Headline cell {headline_cell} matches {len(cell)} rows in hw1f_by_window.csv")
    row = cell.iloc[0]
    fit_insample = VasicekFit(
        alpha=float(row["alpha"]),
        level=float(row["level"]),
        sigma=float(row["sigma"]),
        method=str(row["method"]),
        n_pairs=int(row["n_pairs"]),
        n_pairs_dropped=int(row["n_pairs_dropped"]),
    )

    def rate_fan(fit: VasicekFit, start: pd.Timestamp, slug: str, framing: str) -> None:
        grid = pd.date_range(start, observed_rate.index.max(), freq="D")
        window_obs = observed_rate[observed_rate.index >= start]
        r0 = float(window_obs.iloc[0])
        paths = fit.simulate(grid, n_paths, get_rng(config.seed)) * 100.0
        obs_pct = observed_rate * 100.0
        coverage = viz.band_coverage(grid, paths, obs_pct, coverage_band)
        logger.info(
            "%s: a=%.4f level=%.4f sigma=%.4f r0=%.4f | coverage(%.0f%%)=%s",
            slug,
            fit.alpha,
            fit.level,
            fit.sigma,
            r0,
            coverage_band * 100,
            f"{coverage:.1%}" if coverage is not None else "n/a",
        )
        title = (
            f"F-TIIE vs the fitted Vasicek (P measure, {framing}) — "
            f"a={fit.alpha:.3f}, b={fit.level:.3%}, $\\sigma$={fit.sigma:.4f}"
        )
        written.extend(
            viz.save_figure(
                viz.plot_paths_vs_observed(
                    grid,
                    paths,
                    obs_pct,
                    quantiles=quantiles,
                    coverage_band=coverage_band,
                    ylabel="Short rate (%)",
                    title=title,
                ),
                out_dir / f"fan_ftiie_{slug}",
            )
        )
        written.extend(
            viz.save_figure(
                viz.plot_paths_vs_observed(
                    grid,
                    paths,
                    obs_pct,
                    quantiles=quantiles,
                    show_paths=True,
                    coverage_band=coverage_band,
                    ylabel="Short rate (%)",
                    title=f"{title} — all {n_paths} trajectories",
                ),
                out_dir / f"fan_ftiie_{slug}_all",
                formats=("png",),
                dpi=600,
            )
        )

    rate_fan(fit_insample, pd.Timestamp(str(row["start"])), "insample", "in-sample")

    # A true <= cutoff refit is unidentified on this series: the truncated window
    # ends mid-hiking-cycle, the AR(1) seed is explosive (phi > 1) and the exact
    # MLE degenerates to a near-unit root (alpha -> 0 with an unbounded level),
    # so the rate leg validates the ADOPTED calibration's *conditional* forward
    # cone from the observed r(cutoff) instead — the equities below carry the
    # true holdout refits.
    cutoff = pd.Timestamp(str(rates_cfg["conditional_start"]))
    conditional_start = observed_rate.index[observed_rate.index <= cutoff].max()
    rate_fan(
        fit_insample,
        conditional_start,
        "conditional",
        f"adopted fit, conditional cone from {conditional_start.date()}",
    )

    # --- equities: per-name GBM cones vs observed closes ------------------
    eq_cfg = extra["equities"]
    params = pd.read_csv(root / eq_cfg["params_csv"]).set_index("name")
    price_col = str(eq_cfg["price_column"])
    book_dir = root / eq_cfg["book_dir"]

    def closes_for(name: str) -> pd.Series:
        frame = pd.read_csv(book_dir / f"{name}.csv", index_col=0, parse_dates=True)
        return frame[price_col].dropna()

    def insample_panel(name: str, closes: pd.Series, drift: float, vol: float) -> dict:
        grid = pd.date_range(closes.index[0], closes.index[-1], freq="D")
        paths = _simulate_gbm(
            float(closes.iloc[0]), drift, vol, grid, n_paths, get_rng(config.seed)
        )
        return {
            "dates": grid,
            "paths": paths,
            "observed": closes,
            "label": name.removesuffix("_SHARE"),
        }

    headline_names = [str(n) for n in eq_cfg["headline"]]
    panels = [
        insample_panel(
            name,
            closes_for(name),
            float(params.loc[name, "drift"]),
            float(params.loc[name, "volatility"]),
        )
        for name in headline_names
    ]
    ipc_cfg = eq_cfg["ipc"]
    ipc_params = pd.read_csv(root / ipc_cfg["params_csv"]).set_index("name")
    ipc_closes = pd.read_csv(root / ipc_cfg["csv"], index_col=0, parse_dates=True)[
        price_col
    ].dropna()
    panels.append(
        insample_panel(
            str(ipc_cfg["name"]),
            ipc_closes,
            float(ipc_params.loc[str(ipc_cfg["name"]), "drift"]),
            float(ipc_params.loc[str(ipc_cfg["name"]), "volatility"]),
        )
    )
    written.extend(
        viz.save_figure(
            viz.plot_paths_vs_observed_grid(
                panels,
                ncols=3,
                quantiles=quantiles,
                coverage_band=coverage_band,
                yscale="log",
                title="Observed prices vs the fitted GBM cones (in-sample, headline set)",
            ),
            out_dir / "fan_equities_headline",
        )
    )

    if bool(eq_cfg.get("appendix_all", False)):
        all_names = [n for n in params.index if (book_dir / f"{n}.csv").exists()]
        all_panels = [
            insample_panel(
                name,
                closes_for(name),
                float(params.loc[name, "drift"]),
                float(params.loc[name, "volatility"]),
            )
            for name in all_names
        ]
        written.extend(
            viz.save_figure(
                viz.plot_paths_vs_observed_grid(
                    all_panels,
                    ncols=4,
                    quantiles=quantiles,
                    coverage_band=coverage_band,
                    yscale="log",
                    title="Observed prices vs the fitted GBM cones (in-sample, full book)",
                ),
                out_dir / "fan_equities_all",
            )
        )

    eq_cutoff = pd.Timestamp(str(eq_cfg["holdout_cutoff"]))

    def holdout_panel(name: str) -> dict:
        closes = closes_for(name)
        pre = exclude_windows(closes[closes.index <= eq_cutoff], crisis_windows)
        refit = fit_gbm(pre)
        anchor_date = closes.index[closes.index <= eq_cutoff].max()
        grid = pd.date_range(anchor_date, closes.index[-1], freq="D")
        paths = _simulate_gbm(
            float(closes.loc[anchor_date]),
            refit.drift,
            refit.volatility,
            grid,
            n_paths,
            get_rng(config.seed),
        )
        logger.info(
            "holdout %s: mu=%.4f sigma=%.4f (n=%d) vs headline mu=%.4f sigma=%.4f",
            name,
            refit.drift,
            refit.volatility,
            refit.n_returns,
            float(params.loc[name, "drift"]),
            float(params.loc[name, "volatility"]),
        )
        return {
            "dates": grid,
            "paths": paths,
            "observed": closes,
            "label": name.removesuffix("_SHARE"),
        }

    written.extend(
        viz.save_figure(
            viz.plot_paths_vs_observed_grid(
                [holdout_panel(name) for name in headline_names],
                ncols=3,
                quantiles=quantiles,
                coverage_band=coverage_band,
                yscale="log",
                title=(
                    "Observed prices vs GBM cones refit on data "
                    f"$\\leq$ {eq_cutoff.date()} (holdout)"
                ),
            ),
            out_dir / "fan_equities_holdout",
        )
    )

    if bool(eq_cfg.get("holdout_all", False)):
        all_names = [n for n in params.index if (book_dir / f"{n}.csv").exists()]
        written.extend(
            viz.save_figure(
                viz.plot_paths_vs_observed_grid(
                    [holdout_panel(name) for name in all_names],
                    ncols=4,
                    quantiles=quantiles,
                    coverage_band=coverage_band,
                    yscale="log",
                    title=(
                        "Observed prices vs GBM cones refit on data "
                        f"$\\leq$ {eq_cutoff.date()} (holdout, full book)"
                    ),
                ),
                out_dir / "fan_equities_holdout_all",
            )
        )

    # --- jumps: point-process diagnostics vs the CENAPRED record ----------
    jump_cfg = extra["jumps"]
    deflator = {
        int(y): float(v)
        for y, v in yaml.safe_load((root / jump_cfg["deflator"]).read_text())["inpc"].items()
    }
    regimes_cfg = list(jump_cfg["regimes"])
    window_start = min(pd.Timestamp(str(r["start"])).year for r in regimes_cfg)
    window_end = max(pd.Timestamp(str(r["end"])).year for r in regimes_cfg)
    events = load_climate_events(
        root / jump_cfg["events_csv"],
        start_year=window_start,
        end_year=window_end,
        min_damage_mdp=float(jump_cfg["min_damage_mdp"]),
        deflator=deflator,
    )
    event_dates = pd.to_datetime(events["fecha_inicio"], errors="coerce")
    dropped = int(event_dates.isna().sum())
    if dropped:
        logger.info("Dropped %d/%d trigger events without a start date", dropped, len(events))
    events = events.loc[event_dates.notna()].assign(fecha=event_dates.dropna())

    fits = pd.read_csv(root / jump_cfg["parameters_csv"]).set_index("variant")
    regimes = [
        {
            "start": str(r["start"]),
            "end": str(r["end"]),
            "intensity": float(fits.loc[str(r["row"]), "intensity_per_yr"]),
            "label": str(r["label"]),
        }
        for r in regimes_cfg
    ]
    written.extend(
        viz.save_figure(
            viz.plot_arrival_staircase(
                events["fecha"],
                regimes,
                envelope=float(jump_cfg["envelope"]),
                title=(
                    "Observed CENAPRED trigger arrivals vs the fitted Poisson bands "
                    "(events $\\geq$ 200 MDP-2025)"
                ),
            ),
            out_dir / "jump_staircase",
        )
    )

    diag_row = fits.loc[str(jump_cfg["diagnostics_row"])]
    diag_start = pd.Timestamp(int(diag_row["window_start"]), 1, 1)
    diag_end = pd.Timestamp(int(diag_row["window_end"]), 12, 31)
    lam = float(diag_row["intensity_per_yr"])
    sev_median = float(diag_row["sev_median_mdp"])
    sev_sigma = float(diag_row["sev_sigma"])
    registry = events[(events["fecha"] >= diag_start) & (events["fecha"] <= diag_end)]
    obs_dates = registry["fecha"].sort_values()
    obs_marks = registry.loc[obs_dates.index, "danio_mdp"].to_numpy(dtype=float)

    rng = get_rng(config.seed)
    horizon_years = (diag_end - diag_start).days / 365.0
    n_sim = int(rng.poisson(lam * horizon_years))
    sim_dates = diag_start + pd.to_timedelta(
        np.sort(rng.uniform(0.0, (diag_end - diag_start).days, n_sim)), unit="D"
    )
    sim_marks = np.exp(np.log(sev_median) + sev_sigma * rng.standard_normal(n_sim))
    written.extend(
        viz.save_figure(
            viz.plot_marked_arrivals(
                obs_dates,
                obs_marks,
                sim_dates,
                sim_marks,
                mark_label="Per-event loss (MDP, 2025 pesos)",
                title=(
                    "Marked arrivals, registry window — observed vs one draw of the "
                    f"calibrated process ($\\lambda$={lam:.2f}/yr, lognormal severity)"
                ),
            ),
            out_dir / "jump_marked_arrivals",
        )
    )

    gaps_years = np.sort(np.diff(obs_dates.to_numpy()) / np.timedelta64(1, "D")) / 365.0
    pp = (np.arange(1, len(gaps_years) + 1) - 0.5) / len(gaps_years)
    written.extend(
        viz.save_figure(
            viz.plot_qq(
                gaps_years,
                stats.expon.ppf(pp, scale=1.0 / lam),
                xlabel=f"Exponential($\\lambda$={lam:.2f}/yr) quantiles (years)",
                ylabel="Observed inter-arrival times (years)",
                title="Inter-arrival QQ — registry trigger set",
            ),
            out_dir / "jump_qq_interarrival",
        )
    )
    log_losses = np.sort(np.log(obs_marks[obs_marks > 0]))
    pp = (np.arange(1, len(log_losses) + 1) - 0.5) / len(log_losses)
    written.extend(
        viz.save_figure(
            viz.plot_qq(
                log_losses,
                stats.norm.ppf(pp, loc=np.log(sev_median), scale=sev_sigma),
                xlabel=f"Fitted lognormal quantiles (log MDP; $\\sigma$={sev_sigma:.2f})",
                ylabel="Observed log per-event losses",
                title="Severity QQ — registry trigger set",
            ),
            out_dir / "jump_qq_severity",
        )
    )

    # --- daily-grain jump-on/off price trajectories (engine jump channel) --
    illus = jump_cfg["path_illustration"]
    jump_yaml = yaml.safe_load((root / illus["jump_config"]).read_text())
    target = str(illus["target"])
    process = ClimateJumpProcess.from_config(jump_yaml["climate_jumps"])
    anchor = pd.Timestamp(str(jump_yaml["valuation_date"]))
    daily = pd.date_range(anchor, anchor + pd.Timedelta(days=round(float(illus["years"]) * 365)))
    scenario = process.generate(list(daily), n_paths, config.seed)
    step_marks = scenario.step_marks[target]
    gbm_row = params.loc[target]
    baseline_paths = _simulate_gbm(
        float(gbm_row["initial_value"]),
        float(gbm_row["drift"]),
        float(gbm_row["volatility"]),
        daily,
        n_paths,
        get_rng(config.seed),
    )
    # The engine's equity overlay convention (INT-14): multiplicative in price.
    climate_paths = baseline_paths * np.exp(np.cumsum(np.pad(step_marks, ((0, 0), (1, 0))), axis=1))
    event_rate = float(scenario.event_counts.sum()) / n_paths / float(illus["years"])
    logger.info(
        "jump paths %s: engine lambda %.2f/yr realized %.2f/yr | mean 3y jump-on/off ratio %.4f",
        target,
        float(jump_yaml["climate_jumps"]["intensity"]),
        event_rate,
        float(climate_paths[:, -1].mean() / baseline_paths[:, -1].mean()),
    )
    label = target.removesuffix("_SHARE")
    written.extend(
        viz.save_figure(
            viz.plot_sample_paths(
                daily,
                baseline_paths,
                climate_paths,
                event_counts=scenario.event_counts,
                n_show=int(illus["n_show"]),
                ylabel=f"{label} share price",
                title=(
                    f"{label} — daily jump-diffusion paths, climate jump-on vs baseline "
                    f"($\\lambda$={float(jump_yaml['climate_jumps']['intensity']):.2f}/yr)"
                ),
            ),
            out_dir / "jump_paths_daily",
        )
    )
    written.extend(
        viz.save_figure(
            viz.plot_fan_comparison(
                daily,
                baseline_paths,
                climate_paths,
                ylabel=f"{label} share price",
                title=f"{label} — daily jump-on vs baseline distribution fan",
            ),
            out_dir / "jump_fan_daily",
        )
    )

    manifest = RunManifest.create(seed=config.seed, config=config, project_root=root)
    manifest_path = manifest.write(config.paths.manifests)
    logger.info("Wrote %d files to %s; manifest %s", len(written), out_dir, manifest_path)
    print(f"{len(written)} figure files -> {out_dir}\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
