"""Risk-factor forecast-distribution backtests — tier C of the INT-40 validation layer.

The BCBS 2010 *Sound practices for backtesting counterparty credit risk models*
applied to every risk-factor model that feeds the EPE engine (¶18–19): for each
horizon (1W, 1M, 3M, 1Y) a set of **non-overlapping** forecasts initialised on
dates spaced by the horizon (¶13), each refit on data strictly before its
initialisation date (¶24, the ¶41 back-pricing discipline), and the realisation's
probability integral transform (PIT) read against several percentiles (¶25 / ¶31):

- equities of the Mexican book, the IPC and the FIX: GBM log-price forecasts
  ``N((mu - sigma^2/2) tau, sigma^2 tau)`` with ``(mu, sigma)`` = ``fit_gbm`` on the
  expanding pre-date window (crisis windows excluded, MKT-CALIB-03), Act/365
  ``tau`` like the engine;
- the F-TIIE short rate: the P-measure Vasicek ``N(b + (r_t - b) e^{-a tau},
  sigma^2 (1 - e^{-2 a tau}) / 2a)`` with the weekly-MLE refit of MKT-CALIB-08
  (AR(1) fallback recorded in ``fit_method``).

Outputs per factor x horizon: the reliability table (empirical share of PIT <= p
vs nominal p), central 50/80/95 coverage, KS and Berkowitz tests; pooled rows
stack all equities (cross-name dependence noted — per-name tests are the honest
unit); daily one-day VaR exceptions at 95/99 % under monthly refits scored with
Kupiec POF and Christoffersen conditional coverage. Figures: one reliability
diagram and one PIT-histogram grid per horizon.

Deterministic (no RNG); idempotent, rerun with ``--forzar``.

    python pipelines/29_risk_factor_backtest.py [--config CFG] [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "risk_factor_backtest.yaml"
DAYS_PER_YEAR = 365.0
WEEK_YEARS = 7.0 / DAYS_PER_YEAR


def gbm_forecast(
    closes: pd.Series,
    t: pd.Timestamp,
    t_end: pd.Timestamp,
    crisis_windows,
    *,
    min_history_years: float,
    max_stale_days: int,
) -> dict | None:
    """GBM log-return forecast over ``[t, t_end]`` from a refit on data strictly before ``t``."""
    from climateCCR.calibration.financial.gbm import fit_gbm
    from climateCCR.calibration.financial.hull_white import exclude_windows
    from climateCCR.risk.market import last_obs

    history = closes[closes.index < t]
    if history.empty or (t - history.index[0]).days < DAYS_PER_YEAR * min_history_years:
        return None
    try:
        fit = fit_gbm(exclude_windows(history, crisis_windows))
    except ValueError:
        return None
    start = last_obs(closes, t, max_stale_days)
    end = last_obs(closes, t_end, max_stale_days)
    if start is None or end is None or end[0] <= start[0] or start[1] <= 0 or end[1] <= 0:
        return None
    tau = (end[0] - start[0]).days / DAYS_PER_YEAR
    return {
        "mean": (fit.drift - 0.5 * fit.volatility**2) * tau,
        "sd": fit.volatility * np.sqrt(tau),
        "realised": float(np.log(end[1] / start[1])),
        "n_fit": fit.n_returns,
        "fit_method": "gbm_mle",
    }


def vasicek_forecast(
    rates: pd.Series,
    t: pd.Timestamp,
    t_end: pd.Timestamp,
    crisis_windows,
    *,
    anchor: str,
    min_history_years: float,
    max_stale_days: int,
) -> dict | None:
    """Vasicek level forecast of ``r(t_end)`` from a weekly refit on data strictly before ``t``."""
    from climateCCR.calibration.financial.hull_white import (
        VasicekFit,
        exclude_windows,
        fit_vasicek_ar1,
        fit_vasicek_mle,
        sample_weekly_last,
    )
    from climateCCR.risk.market import last_obs

    history = rates[rates.index < t]
    if history.empty or (t - history.index[0]).days < DAYS_PER_YEAR * min_history_years:
        return None
    weekly = sample_weekly_last(exclude_windows(history, crisis_windows), anchor)
    fit, method = None, ""
    try:
        fit, method = fit_vasicek_mle(weekly), "mle"
    except (
        Exception
    ):  # noqa: BLE001 — the MLE starts from the AR(1); a near-unit-root window fails both
        restart = VasicekFit(
            alpha=0.1,
            level=float(weekly.mean()),
            sigma=float(weekly.diff().std() / np.sqrt(WEEK_YEARS)),
            method="restart",
            n_pairs=0,
            n_pairs_dropped=0,
        )
        try:
            fit, method = fit_vasicek_mle(weekly, start=restart), "mle_restart"
        except Exception:  # noqa: BLE001
            try:
                fit, method = fit_vasicek_ar1(weekly, dt_years=WEEK_YEARS, max_gap_days=9.0), "ar1"
            except Exception:  # noqa: BLE001
                return None
    start = last_obs(rates, t, max_stale_days)
    end = last_obs(rates, t_end, max_stale_days)
    if start is None or end is None or end[0] <= start[0]:
        return None
    tau = (end[0] - start[0]).days / DAYS_PER_YEAR
    a, b, s = fit.alpha, fit.level, fit.sigma
    if a > 1e-8:
        mean = b + (start[1] - b) * np.exp(-a * tau)
        var = s**2 * (1.0 - np.exp(-2.0 * a * tau)) / (2.0 * a)
    else:  # random-walk limit of an unidentified reversion
        mean, var = start[1], s**2 * tau
    if not var > 0:
        return None
    return {
        "mean": float(mean),
        "sd": float(np.sqrt(var)),
        "realised": end[1],
        "n_fit": fit.n_pairs,
        "fit_method": method,
    }


def daily_var_hits(
    closes: pd.Series, level: float, crisis_windows, start: str, end: str, min_history_years: float
) -> np.ndarray:
    """One-day VaR exception indicators under monthly GBM refits held fixed over the month."""
    from climateCCR.calibration.financial.gbm import fit_gbm
    from climateCCR.calibration.financial.hull_white import exclude_windows
    from scipy import stats

    series = closes[(closes.index >= pd.Timestamp(start)) & (closes.index <= pd.Timestamp(end))]
    z_crit = stats.norm.ppf(1.0 - level)
    hits: list[int] = []
    for month_start, block in series.groupby(series.index.to_period("M")):
        t = month_start.to_timestamp()
        history = closes[closes.index < t]
        if history.empty or (t - history.index[0]).days < DAYS_PER_YEAR * min_history_years:
            continue
        try:
            fit = fit_gbm(exclude_windows(history, crisis_windows))
        except ValueError:
            continue
        prev = closes[closes.index < block.index[0]]
        if prev.empty:
            continue
        values = np.concatenate([[prev.iloc[-1]], block.to_numpy(dtype=float)])
        dates = prev.index[-1:].append(block.index)
        dt = np.diff(dates.to_numpy()) / np.timedelta64(1, "D") / DAYS_PER_YEAR
        returns = np.diff(np.log(values))
        z = (returns - (fit.drift - 0.5 * fit.volatility**2) * dt) / (fit.volatility * np.sqrt(dt))
        hits.extend((z < z_crit).astype(int).tolist())
    return np.asarray(hits, dtype=int)


def _read_series(path: Path, column: str) -> pd.Series:
    frame = pd.read_csv(path, index_col=0, parse_dates=True)
    series = pd.to_numeric(frame[column], errors="coerce").dropna().sort_index()
    return series[~series.index.duplicated(keep="last")]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    args = parser.parse_args()

    from climateCCR import viz
    from climateCCR.calibration.financial.hull_white import simple_to_continuous
    from climateCCR.infra import RunManifest, get_logger, load_config
    from climateCCR.risk.market import (
        berkowitz_lr,
        central_coverage,
        christoffersen_cc,
        christoffersen_independence,
        coverage_by_percentile,
        horizon_end,
        init_dates,
        ks_uniform,
        kupiec_pof,
        pit_normal,
    )

    config = load_config(args.config)
    config.paths.ensure()
    logger = get_logger("climateCCR.risk_factor_backtest", log_dir=config.paths.logs)
    extra = config.extra
    root = config.paths.root
    out_dir = config.paths.results / str(extra.get("out_dir", "risk_factor_backtest"))
    out_csv = out_dir / "pit_long.csv"
    if out_csv.exists() and not args.forzar:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", out_csv)
        return

    mc = yaml.safe_load((root / extra["market_calibration_config"]).read_text())
    crisis_windows = [tuple(w) for w in mc["crisis_windows"].values()]
    start, end = str(extra["start"]), str(extra["end"])
    min_history = float(extra["min_history_years"])
    max_stale = int(extra["max_stale_days"])
    percentiles = [float(p) for p in extra["percentiles"]]
    levels = [float(v) for v in extra["levels"]]
    horizons = {str(k): dict(v) for k, v in extra["horizons"].items()}

    # --- factors ---------------------------------------------------------
    eq_cfg = extra["equities"]
    book_dir = root / eq_cfg["book_dir"]
    names = [str(n) for n in eq_cfg.get("names") or []] or sorted(
        p.stem for p in book_dir.glob("*_SHARE.csv")
    )
    price_factors: dict[str, pd.Series] = {
        name: _read_series(book_dir / f"{name}.csv", str(eq_cfg["price_column"])) for name in names
    }
    price_factors[str(extra["ipc"]["name"])] = _read_series(
        root / extra["ipc"]["csv"], str(extra["ipc"]["column"])
    )
    price_factors[str(extra["fx"]["name"])] = _read_series(
        root / extra["fx"]["csv"], str(extra["fx"]["column"])
    )
    rate_cfg = extra["rate"]
    quotes = _read_series(root / rate_cfg["csv"], str(rate_cfg["column"])) / 100.0
    rate = pd.Series(
        simple_to_continuous(quotes.to_numpy(), float(rate_cfg["tenor_days"])), index=quotes.index
    )
    rate_name = str(rate_cfg["name"])
    logger.info("%d price factors + %s; horizons %s", len(price_factors), rate_name, list(horizons))

    # --- multi-horizon PITs ----------------------------------------------
    pit_rows: list[dict] = []
    for h_key, spec in horizons.items():
        dates = init_dates(start, end, spec)
        for name, series in price_factors.items():
            for t in dates:
                fc = gbm_forecast(
                    series,
                    t,
                    horizon_end(t, spec),
                    crisis_windows,
                    min_history_years=min_history,
                    max_stale_days=max_stale,
                )
                if fc is not None:
                    pit_rows.append({"factor": name, "horizon": h_key, "init_date": t} | fc)
        for t in dates:
            fc = vasicek_forecast(
                rate,
                t,
                horizon_end(t, spec),
                crisis_windows,
                anchor=str(rate_cfg["anchor"]),
                min_history_years=min_history,
                max_stale_days=max_stale,
            )
            if fc is not None:
                pit_rows.append({"factor": rate_name, "horizon": h_key, "init_date": t} | fc)
        logger.info(
            "%s: %d initialisation dates, %d forecasts so far", h_key, len(dates), len(pit_rows)
        )
    pit_long = pd.DataFrame(pit_rows)
    pit_long["pit"] = pit_normal(pit_long["realised"], pit_long["mean"], pit_long["sd"])
    pit_long["kind"] = np.where(pit_long["factor"] == rate_name, "rate", "price")

    # --- reliability tables + tests --------------------------------------
    rel_rows, test_rows = [], []
    groups = list(pit_long.groupby(["horizon", "factor"], sort=False))
    pooled = [
        ((h, "ALL_EQUITIES"), block[block["factor"].isin(names)])
        for h, block in pit_long.groupby("horizon", sort=False)
    ]
    for (h_key, factor), block in groups + pooled:
        pit = block.sort_values("init_date")["pit"].to_numpy()
        if pit.size < 4:
            continue
        rel = coverage_by_percentile(pit, percentiles)
        rel_rows.extend(
            {"horizon": h_key, "factor": factor} | r for r in rel.to_dict(orient="records")
        )
        central = central_coverage(pit, levels)
        ks, berk = ks_uniform(pit), berkowitz_lr(pit)
        row = {
            "horizon": h_key,
            "factor": factor,
            "n": int(pit.size),
            "mean_pit": float(pit.mean()),
            "ks_stat": ks.statistic,
            "ks_p": ks.p_value,
            "berkowitz_stat": berk.statistic,
            "berkowitz_p": berk.p_value,
            "fit_method": "/".join(sorted(block["fit_method"].unique())),
        }
        for level, cov in zip(central["nominal"], central["empirical"], strict=True):
            row[f"coverage_{int(round(100 * level))}"] = float(cov)
        test_rows.append(row)
    reliability = pd.DataFrame(rel_rows)
    tests = pd.DataFrame(test_rows)

    # --- daily VaR exceptions (price factors) ----------------------------
    var_rows = []
    for level in [float(v) for v in extra["daily_var"]["levels"]]:
        for name, series in price_factors.items():
            hits = daily_var_hits(series, level, crisis_windows, start, end, min_history)
            if hits.size < 50:
                continue
            pof = kupiec_pof(int(hits.sum()), int(hits.size), 1.0 - level)
            ind = christoffersen_independence(hits)
            cc = christoffersen_cc(hits, 1.0 - level)
            var_rows.append(
                {
                    "factor": name,
                    "level": level,
                    "n_days": int(hits.size),
                    "n_hits": int(hits.sum()),
                    "hit_rate": float(hits.mean()),
                    "kupiec_stat": pof.statistic,
                    "kupiec_p": pof.p_value,
                    "independence_p": ind.p_value,
                    "cc_p": cc.p_value,
                }
            )
    daily_var = pd.DataFrame(var_rows)

    # --- outputs -----------------------------------------------------------
    out_dir.mkdir(parents=True, exist_ok=True)
    pit_long.round(8).to_csv(out_csv, index=False)
    reliability.round(6).to_csv(out_dir / "reliability.csv", index=False)
    tests.round(6).to_csv(out_dir / "tests.csv", index=False)
    daily_var.round(6).to_csv(out_dir / "daily_var.csv", index=False)
    viz.apply_style()
    written: list[Path] = []
    for h_key in horizons:
        sub = reliability[reliability["horizon"] == h_key]
        if sub.empty:
            continue
        series_map = {
            factor: grp.sort_values("nominal")["empirical"].to_numpy()
            for factor, grp in sub.groupby("factor", sort=False)
        }
        pooled_n = int(sub.loc[sub["factor"] == "ALL_EQUITIES", "n"].iloc[0])
        se = np.sqrt(np.array(percentiles) * (1 - np.array(percentiles)) / pooled_n)
        fig = viz.plot_reliability(
            percentiles,
            series_map,
            se=se,
            title=f"Reliability at {h_key}: {len(series_map)} factors (band = pooled ±2 se)",
        )
        written.extend(viz.save_figure(fig, out_dir / f"reliability_{h_key}"))
        pits = {
            factor: grp["pit"].to_numpy()
            for factor, grp in pit_long[pit_long["horizon"] == h_key].groupby("factor", sort=False)
        }
        fig = viz.plot_pit_histograms(pits, bins=10, ncols=6, title=f"PIT histograms at {h_key}")
        written.extend(viz.save_figure(fig, out_dir / f"pit_hist_{h_key}"))
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=root)
    manifest_path = manifest.write(config.paths.manifests)
    summary = tests[tests["factor"].isin(["ALL_EQUITIES", rate_name, str(extra["fx"]["name"])])]
    print(summary.round(3).to_string(index=False))
    print(f"\nTables:   {out_dir}\nFigures:  {len(written)} files\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
