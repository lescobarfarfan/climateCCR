"""Static representative-portfolio back-pricing — tier E of INT-40 (BCBS 2010 ¶33/¶34/¶41).

The exposure model is backtested the way the sound-practices paper asks for a
CCR model: a **static hypothetical representative portfolio** (¶33) re-struck at
past initialisation dates (¶34 — option strikes ATM at the dated spot, IRS fixed
rates and fixed-bond coupons read off the dated curve, every maturity shifted by
the same offset so tenors keep their original meaning), **re-calibrated strictly
on pre-date data** (¶24 / ¶41 back-pricing: pipelines/07 and 09 on dated
configs this pipeline writes), simulated jump-off / jump-on to the backtest grid
(pipelines/01 ``--horizonte backtest --trayectorias``), and finally **repriced on
the realised market path** — the engine's joint-scenario seam fed one path of
observed closes, FIX and F-TIIE (as the short-rate state) — so the realised
netted MtM per counterparty and reporting date can be scored against the
forecast distribution: PIT, reliability at several percentiles (¶25 / ¶31),
central coverage, and the realised exposure against the forecast EE, aggregated
across counterparties, horizons and initialisation dates (¶17).

Caveats carried in the outputs: the rate side is **model-mapped** (the pricers
rebuild the curve from the realised short rate through the HW1F ``B(t, T)``
loading, not from the realised curve); options price on the flat fitted-sigma
surface; names failing the min-data rule at a past date drop out of that date's
book (the build report says which); the bond legs are representative re-strikes.
Significance is not expected at 2–3-year horizons (¶38) — reasonableness is.

Stages (all idempotent; the generated configs under ``results/<out_dir>/configs``
are reconstructor outputs, GEN-04):

    python pipelines/31_static_book_backtest.py --ejecutar   # per date: 07 -> 09 -> 01 x bands
    python pipelines/31_static_book_backtest.py              # realised reprice + scoring
"""

from __future__ import annotations

import argparse
import copy
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "static_book_backtest.yaml"
DAYS_PER_YEAR = 365.25
BAND_SUFFIX = {"headline": "", "ct_anchor": "_ct_anchor", "floor": "_floor"}


def tag(date: str) -> str:
    """``2016-07-15`` -> ``bt_2016_07_15`` (config / artifact stem suffix)."""
    return "bt_" + str(date).replace("-", "_")


def zero_at(pillars_csv: Path, t_years: float) -> float:
    """Continuous zero rate at ``t_years`` interpolated on the dated stripped pillars."""
    table = pd.read_csv(pillars_csv).sort_values("t_years")
    return float(np.interp(t_years, table["t_years"].to_numpy(), table["zero"].to_numpy()))


def dated_calibration_config(market_calibration: dict, date: str, output_dir: str) -> dict:
    """The market-calibration config at ``date``: every window ends there, curve dated."""
    cfg = copy.deepcopy(market_calibration)
    cfg["output_dir"] = output_dir
    cfg["curve"]["valuation_date"] = date
    cfg["windows"] = {name: [span[0], date] for name, span in market_calibration["windows"].items()}
    return cfg


def _bond_fields(bond) -> dict:
    """Normalise a config bond row (legacy triple or dict) to its fields."""
    if isinstance(bond, list | tuple):
        coupon, maturity, spread_bp = bond
        return {
            "tipo": "fija",
            "cupon": float(coupon),
            "vencimiento": str(maturity),
            "spread_bp": spread_bp,
        }
    return dict(bond)


def restrike_book_config(
    book: dict,
    date: str,
    reference_date: str,
    pillars_csv: Path,
    *,
    book_root: str,
    cache_subdir: str,
    hw1f_direct_input: str,
    rate_scale_output_dir: str,
) -> dict:
    """The book config re-struck at ``date`` (BCBS 2010 ¶34) on the dated curve.

    Maturities shift by ``date - reference_date`` (tenors preserved); IRS fixed
    rates become the dated zero rate at the swap tenor; fixed-coupon bonds take
    the dated zero at their (shifted) tenor plus their issuance spread; FRN
    sobretasas are unchanged; option strikes follow the builder's ATM rule at the
    dated spot. Provenance URLs are dropped — the rows are representative
    re-strikes [eng].
    """
    cfg = copy.deepcopy(book)
    cfg["valuation_date"] = date
    cfg["book_root"] = book_root
    cfg["fetch"]["cache_subdir"] = cache_subdir
    cfg["inputs"]["hw1f_direct_input"] = hw1f_direct_input
    cfg["rate_scale_output_dir"] = rate_scale_output_dir
    offset = pd.Timestamp(date) - pd.Timestamp(reference_date)
    irs = cfg["trade_rules"]["irs"]
    irs["fixed_rate_by_tenor"] = {
        int(t): round(zero_at(pillars_csv, float(t)), 6) for t in irs["fixed_rate_by_tenor"]
    }
    for cp in cfg["counterparties"]:
        rows = []
        for bond in cp.get("bonds", []):
            fields = _bond_fields(bond)
            maturity = (pd.Timestamp(fields["vencimiento"]) + offset).strftime("%Y-%m-%d")
            tenor_years = (pd.Timestamp(maturity) - pd.Timestamp(date)).days / DAYS_PER_YEAR
            if fields.get("tipo", "fija") == "frn":
                row = {
                    "tipo": "frn",
                    "sobretasa": float(fields["sobretasa"]),
                    "vencimiento": maturity,
                }
                if "spread_bp" in fields:
                    row["spread_bp"] = fields["spread_bp"]
            else:
                spread_bp = float(fields.get("spread_bp", 0.0))
                row = {
                    "tipo": "fija",
                    "cupon": round(zero_at(pillars_csv, tenor_years) + spread_bp / 1e4, 6),
                    "vencimiento": maturity,
                    "spread_bp": spread_bp,
                }
            rows.append(row)
        if rows:
            cp["bonds"] = rows
    return cfg


def dated_jump_config(jump: dict, date: str, grid: list[str], s_ref: float, s_bt: float) -> dict:
    """The jump config at ``date``: backtest grid only, rate marks re-inverted with the dated S."""
    cfg = copy.deepcopy(jump)
    cfg["valuation_date"] = date
    cfg["horizons"] = {"backtest": {"b3_grid": list(grid), "max_step_days": None}}
    rate = cfg["climate_jumps"].get("rate_marks")
    if rate is not None:
        rate["median"] = float(rate["median"]) * float(s_ref) / float(s_bt)
    return cfg


def realised_scenarios(
    names, union_dates, series_by_name: dict[str, pd.Series], max_stale_days: int
) -> dict:
    """One observed path per factor on the union grid, in the ``slice_scenarios`` layout."""
    from climateCCR.risk.market import last_obs

    out = {}
    for name in names:
        series = series_by_name[name]
        values = []
        for date in union_dates:
            obs = last_obs(series, pd.Timestamp(date), max_stale_days)
            if obs is None:
                raise ValueError(f"{name}: no observation within {max_stale_days} days of {date}")
            values.append(obs[1])
        out[name] = np.asarray(values, dtype=float)[None, :]
        out[name + "_dates"] = list(union_dates)
    return out


def _run(script: str, *args: str, forzar: bool = False) -> None:
    cmd = [sys.executable, str(REPO_ROOT / "pipelines" / script), *args]
    if forzar:
        cmd.append("--forzar")
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)


def _read_series(path: Path, column: str) -> pd.Series:
    frame = pd.read_csv(path, index_col=0, parse_dates=True)
    series = pd.to_numeric(frame[column], errors="coerce").dropna().sort_index()
    return series[~series.index.duplicated(keep="last")]


def ejecutar(config, logger, args) -> None:
    """Per initialisation date: dated configs -> pipelines/07 -> 09 -> 01 x bands."""
    extra, root = config.extra, config.paths.root
    out_dir = config.paths.results / str(extra.get("out_dir", "static_book_backtest"))
    config_dir = out_dir / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    mc = yaml.safe_load((root / extra["market_calibration_config"]).read_text())
    book = yaml.safe_load((root / extra["book_config"]).read_text())
    jumps = {
        band: yaml.safe_load((root / path).read_text())
        for band, path in extra["jump_configs"].items()
    }
    s_ref = float(pd.read_csv(root / extra["reference_rate_scale_csv"]).iloc[0]["s_rate_eff_mdp"])
    grid = [str(g) for g in extra["b3_grid"]]
    for date in [str(d) for d in extra["init_dates"]]:
        t = tag(date)
        cal_cfg = config_dir / f"market_calibration_{t}.yaml"
        cal_cfg.write_text(
            yaml.safe_dump(
                dated_calibration_config(mc, date, f"market_calibration_{t}"), sort_keys=False
            )
        )
        _run("07_market_calibration.py", "--config", str(cal_cfg), forzar=args.forzar)
        cal_dir = config.paths.results / f"market_calibration_{t}"
        book_cfg = config_dir / f"mexican_book_{t}.yaml"
        book_cfg.write_text(
            yaml.safe_dump(
                restrike_book_config(
                    book,
                    date,
                    str(extra["reference_valuation_date"]),
                    cal_dir / "zero_curve_pillars.csv",
                    book_root=f"data/ccr_book_mx_{t}",
                    cache_subdir=str(extra["cache_subdir"]),
                    hw1f_direct_input=f"results/market_calibration_{t}/direct_input/"
                    "RFE_HW1F_Calibration_MX.csv",
                    rate_scale_output_dir=f"results/loss_to_rate_scale_{t}",
                ),
                sort_keys=False,
                allow_unicode=True,
            )
        )
        _run("09_build_mexican_book.py", "--config", str(book_cfg), forzar=args.forzar)
        s_bt = float(
            pd.read_csv(config.paths.results / f"loss_to_rate_scale_{t}" / "scale.csv").iloc[0][
                "s_rate_eff_mdp"
            ]
        )
        logger.info(
            "%s: S_rate_eff %.0f (reference %.0f) -> rate marks x%.3f", t, s_bt, s_ref, s_ref / s_bt
        )
        for band, jump in jumps.items():
            jump_cfg = config_dir / f"climate_jump_real_mexican_{t}{BAND_SUFFIX[band]}.yaml"
            jump_cfg.write_text(
                yaml.safe_dump(dated_jump_config(jump, date, grid, s_ref, s_bt), sort_keys=False)
            )
            _run(
                "01_climate_jump_demo.py",
                "--config",
                str(jump_cfg),
                "--book-config",
                str(book_cfg),
                "--data-root",
                f"data/ccr_book_mx_{t}",
                "--horizonte",
                "backtest",
                "--trayectorias",
                forzar=args.forzar,
            )
        logger.info("%s: dated calibration, book and %d band runs done", t, len(jumps))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    parser.add_argument(
        "--ejecutar",
        "--run",
        action="store_true",
        help="write the dated configs and run pipelines/07 -> 09 -> 01 per initialisation date",
    )
    args = parser.parse_args()

    from climateCCR import viz
    from climateCCR.calibration.financial.hull_white import simple_to_continuous
    from climateCCR.infra import RunManifest, get_logger, load_config
    from climateCCR.risk.ccr.config import build_global_parameters
    from climateCCR.risk.ccr.evaluators.artifacts import (
        grid_dates,
        read_per_path_values,
        reporting_slice,
    )
    from climateCCR.risk.ccr.evaluators.ccr_valuation_session import prepare_book
    from climateCCR.risk.market import (
        central_coverage,
        coverage_by_percentile,
        ks_uniform,
        pit_values,
    )

    config = load_config(args.config)
    config.paths.ensure()
    logger = get_logger("climateCCR.static_book_backtest", log_dir=config.paths.logs)
    extra, root = config.extra, config.paths.root
    out_dir = config.paths.results / str(extra.get("out_dir", "static_book_backtest"))
    if args.ejecutar:
        ejecutar(config, logger, args)
        return
    out_csv = out_dir / "pit_long.csv"
    if out_csv.exists() and not args.forzar:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", out_csv)
        return

    grid = [str(g) for g in extra["b3_grid"]]
    real_cfg = extra["realised"]
    max_stale = int(real_cfg["max_stale_days"])
    fix = _read_series(root / real_cfg["fix_csv"], "FIX")
    quotes = _read_series(root / real_cfg["tiies_csv"], str(real_cfg["rate_column"])) / 100.0
    rate = pd.Series(
        simple_to_continuous(quotes.to_numpy(), float(real_cfg["tenor_days"])), index=quotes.index
    )
    cache_dir = root / str(extra["cache_subdir"])
    config_dir = out_dir / "configs"
    rows: list[dict] = []
    pins: list[dict] = []
    for date in [str(d) for d in extra["init_dates"]]:
        t = tag(date)
        book_cfg_path = config_dir / f"mexican_book_{t}.yaml"
        book_config = load_config(book_cfg_path)
        data_root = root / f"data/ccr_book_mx_{t}"
        gp = build_global_parameters(book_config, data_root=data_root)
        gp["n_paths"] = 1
        gp["B3_grid"] = grid
        sessions = prepare_book(date, gp)
        union = sorted(set().union(*(s.simulation_dates for s in sessions)))
        names = []
        for s in sessions:
            for rf in s.scenario_generator.simulated_risk_factors:
                if rf.name not in names:
                    names.append(rf.name)
        curve_rf = str(book_config.extra["curve"]["rf"])
        fx_rf = str(book_config.extra["fx"]["rf"])
        series_by_name = {}
        for name in names:
            if name == curve_rf:
                series_by_name[name] = rate
            elif name == fx_rf:
                series_by_name[name] = fix
            else:
                series_by_name[name] = _read_series(
                    cache_dir / f"{name}.csv", str(real_cfg["price_column"])
                )
        realised = realised_scenarios(names, union, series_by_name, max_stale)
        realised_mtm: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        while sessions:
            s = sessions.pop(0)
            s.simulate(gp, joint_scenarios=realised)
            s.value(gp)
            naid = str(s.portfolio.netting_agreement_id)
            realised_mtm[naid] = (
                grid_dates(s.b3_default_grid),
                reporting_slice(
                    s.simulation_dates, s.b3_default_grid, s.scenarios_portfolio_values
                )[0],
            )
        logger.info(
            "%s: realised reprice of %d netting sets on %d dates", t, len(realised_mtm), len(grid)
        )
        for band, suffix in BAND_SUFFIX.items():
            run_dir = config.paths.results / f"climate_jump_real_mexican_{t}{suffix}_backtest"
            for leg in ("baseline", "climate"):
                store = read_per_path_values(run_dir / f"per_path_values_{leg}.npz")
                for naid, (dates, values) in store.items():
                    real_dates, real_values = realised_mtm[naid]
                    if list(dates) != list(real_dates):
                        raise ValueError(f"{naid}: forecast and realised reporting grids differ")
                    pin_gap = float(abs(values[:, 0].mean() - real_values[0]))
                    pins.append(
                        {
                            "init_date": date,
                            "band": band,
                            "leg": leg,
                            "naid": naid,
                            "pin_gap": pin_gap,
                        }
                    )
                    for j in range(1, len(dates)):
                        forecast = values[:, j]
                        realised_v = float(real_values[j])
                        rows.append(
                            {
                                "init_date": date,
                                "band": band,
                                "leg": leg,
                                "naid": naid,
                                "horizon": grid[j],
                                "date": dates[j],
                                "realised_mtm": realised_v,
                                "forecast_mean": float(forecast.mean()),
                                "forecast_q05": float(np.quantile(forecast, 0.05)),
                                "forecast_q50": float(np.quantile(forecast, 0.50)),
                                "forecast_q95": float(np.quantile(forecast, 0.95)),
                                "forecast_ee": float(np.maximum(forecast, 0.0).mean()),
                                "realised_exposure": max(realised_v, 0.0),
                                "pit": float(pit_values(forecast[:, None], [realised_v])[0]),
                            }
                        )
    table = pd.DataFrame(rows)
    pin_table = pd.DataFrame(pins)
    worst_pin = float(pin_table["pin_gap"].max()) if not pin_table.empty else float("nan")
    logger.info("0D pin: worst |forecast 0D - realised 0D| = %.6g", worst_pin)

    percentiles = [float(p) for p in extra["percentiles"]]
    levels = [float(v) for v in extra["levels"]]
    rel_rows, sum_rows = [], []
    group_keys = [["leg", "band", "horizon"], ["leg", "band"], ["leg", "band", "init_date"]]
    for keys in group_keys:
        for key_values, block in table.groupby(keys, sort=False):
            pit = block["pit"].to_numpy()
            if pit.size < 4:
                continue
            base = dict(zip(keys, key_values, strict=True))
            for r in coverage_by_percentile(pit, percentiles).to_dict(orient="records"):
                rel_rows.append(base | {"grouping": "+".join(keys)} | r)
            central = central_coverage(pit, levels)
            summary = base | {
                "grouping": "+".join(keys),
                "n": int(pit.size),
                "mean_pit": float(pit.mean()),
                "ks_p": ks_uniform(pit).p_value,
                "ae_exposure": float(block["realised_exposure"].sum() / block["forecast_ee"].sum()),
            }
            for level, cov in zip(central["nominal"], central["empirical"], strict=True):
                summary[f"coverage_{int(round(100 * level))}"] = float(cov)
            sum_rows.append(summary)
    reliability = pd.DataFrame(rel_rows)
    summaries = pd.DataFrame(sum_rows)

    out_dir.mkdir(parents=True, exist_ok=True)
    table.round(6).to_csv(out_csv, index=False)
    pin_table.round(6).to_csv(out_dir / "pin_0d.csv", index=False)
    reliability.round(6).to_csv(out_dir / "reliability.csv", index=False)
    summaries.round(6).to_csv(out_dir / "summary.csv", index=False)
    viz.apply_style()
    written: list[Path] = []
    for leg in ("baseline", "climate"):
        sub = reliability[
            (reliability["grouping"] == "leg+band+horizon")
            & (reliability["leg"] == leg)
            & (reliability["band"] == "headline")
        ]
        if sub.empty:
            continue
        series_map = {
            str(h): grp.sort_values("nominal")["empirical"].to_numpy()
            for h, grp in sub.groupby("horizon", sort=False)
        }
        n_pool = int(sub["n"].max())
        se = np.sqrt(np.array(percentiles) * (1 - np.array(percentiles)) / n_pool)
        fig = viz.plot_reliability(
            percentiles,
            series_map,
            se=se,
            title=f"Realised netted MtM vs forecast paths ({leg} leg, headline band), by horizon",
        )
        written.extend(viz.save_figure(fig, out_dir / f"reliability_{leg}"))
        pits = {
            str(h): grp["pit"].to_numpy()
            for h, grp in table[(table["leg"] == leg) & (table["band"] == "headline")].groupby(
                "horizon", sort=False
            )
        }
        fig = viz.plot_pit_histograms(pits, bins=5, ncols=3, title=f"PIT by horizon ({leg} leg)")
        written.extend(viz.save_figure(fig, out_dir / f"pit_hist_{leg}"))
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=root)
    manifest_path = manifest.write(config.paths.manifests)
    show = summaries[summaries["grouping"] == "leg+band"]
    print(show.round(3).to_string(index=False))
    print(f"\n0D pin worst gap: {worst_pin:.6g}")
    print(f"Tables:   {out_dir}\nFigures:  {len(written)} files\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
