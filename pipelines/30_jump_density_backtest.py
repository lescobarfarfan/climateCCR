"""Jump-on vs jump-off predictive densities on realised returns — tier D of INT-40.

The climate jump channel turns each book equity's GBM into a Merton
jump-diffusion (INT-14): over a horizon the log return is the diffusion plus the
summed marks of the Poisson events that landed (peril-typed, c_ip-scaled,
per-label severity — the adopted DC-CCR-SIM-2 configuration). This pipeline asks
the standard density-forecast question of that channel: **do realised BMV
returns look more like the jump-on density than the jump-off one?**

- realised non-overlapping h-period log returns per name (1M, 1Y) over the
  name's history;
- jump-off density ``N((mu - sigma^2/2) tau, sigma^2 tau)`` with the adopted
  engine parameters (``RFE_GBM_Calibration.csv``);
- jump-on density = the Gaussian mixture over the engine's own jump totals ``J``
  (``ClimateJumpProcess.generate`` on a one-step grid of length ``h``, so peril
  labels, ``c_ip`` and per-label severity enter exactly as simulated;
  Rao-Blackwellised through ``log_score_mixture``);
- variants: ``engine`` — the overlay as applied (uncompensated: the expected
  drag ``E[exp(J)] - 1`` is part of the claim); ``compensated`` — the mixture
  location shifted by ``-log E[exp(J)]`` so the realised drift is matched and
  only the *shape* (fat left tail) is scored;
- per name the Diebold–Mariano test on the log-score differential
  (``on - off``; = Amisano–Giacomini 2007 on densities), CRPS both ways, the
  expected drag; pooled across names by the per-date cross-name mean
  differential; the rate leg scores the F-TIIE under the adopted Vasicek with
  and without the rate marks.

Expected reading (plan 2026-10-12): the ``engine`` density is rejected for
high-gamma names — realised prices do not carry the loss-ratio drag — which is
the H1 null in density form, not a model failure: the jump channel is a
loss-transmission overlay (INT-17/37), not a price forecast; ``compensated``
tells whether at least the shape helps.

Deterministic given ``seed``; idempotent, rerun with ``--forzar``.

    python pipelines/30_jump_density_backtest.py [--config CFG] [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "jump_density_backtest.yaml"
DAYS_PER_YEAR = 365.0


def realised_windows(series: pd.Series, dates, spec, max_stale_days: int) -> pd.DataFrame:
    """Non-overlapping ``(init_date, end_date, tau_years, start, end)`` rows a series realises."""
    from climateCCR.risk.market import horizon_end, last_obs

    rows = []
    for t in dates:
        a = last_obs(series, t, max_stale_days)
        b = last_obs(series, horizon_end(t, spec), max_stale_days)
        if a is None or b is None or b[0] <= a[0]:
            continue
        rows.append(
            {
                "init_date": t,
                "end_date": b[0],
                "tau_years": (b[0] - a[0]).days / DAYS_PER_YEAR,
                "start": a[1],
                "end": b[1],
            }
        )
    return pd.DataFrame(rows)


def jump_totals(jump_config: dict, spec, n_sims: int, seed: int) -> dict[str, np.ndarray]:
    """Summed marks per target over one horizon step, drawn as the engine draws them."""
    from climateCCR.processes.jumps.climate_jump_process import ClimateJumpProcess
    from climateCCR.risk.market import horizon_end

    process = ClimateJumpProcess.from_config(jump_config["climate_jumps"])
    t0 = pd.Timestamp(str(jump_config["valuation_date"]))
    dates = [t0.to_pydatetime(), horizon_end(t0, spec).to_pydatetime()]
    scenario = process.generate(dates, n_sims, seed)
    return {name: marks[:, 0] for name, marks in scenario.step_marks.items()}


def score_series(
    y: np.ndarray,
    mean: np.ndarray,
    sd: np.ndarray,
    jumps: np.ndarray,
    rng: np.random.Generator,
    dm_lag: int,
) -> dict[str, dict]:
    """Log-score / CRPS of jump-off vs jump-on (engine and compensated) + Diebold–Mariano."""
    from climateCCR.risk.market import (
        crps_from_samples,
        crps_normal,
        diebold_mariano,
        log_score_mixture,
        log_score_normal,
    )

    off_ls = log_score_normal(y, mean, sd)
    off_crps = crps_normal(y, mean, sd)
    drag = float(np.log(np.mean(np.exp(jumps))))  # log E[exp(J)]: the expected multiplicative drag
    z = rng.standard_normal(jumps.size)
    out = {}
    for variant, shift in (("engine", 0.0), ("compensated", -drag)):
        loc = mean + shift
        on_ls = log_score_mixture(y, jumps, loc, sd)
        samples = loc[None, :] + sd[None, :] * z[:, None] + jumps[:, None]
        on_crps = crps_from_samples(samples, y)
        diff = on_ls - off_ls
        dm = diebold_mariano(diff, lag=dm_lag)
        out[variant] = {
            "n_obs": int(y.size),
            "log_score_off": float(off_ls.mean()),
            "log_score_on": float(on_ls.mean()),
            "mean_diff": float(diff.mean()),
            "dm_stat": dm.statistic,
            "dm_p": dm.p_value,
            "crps_off": float(off_crps.mean()),
            "crps_on": float(on_crps.mean()),
            "expected_drag_pct": 100.0 * (np.exp(drag) - 1.0),
            "_diff": diff,
        }
    return out


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
    from climateCCR.infra import RunManifest, get_logger, get_stream_rng, load_config
    from climateCCR.risk.market import diebold_mariano, init_dates
    from climateCCR.viz.style import COLOR_BASELINE, COLOR_CLIMATE, TEXT_SECONDARY
    from matplotlib import pyplot as plt

    config = load_config(args.config)
    config.paths.ensure()
    logger = get_logger("climateCCR.jump_density_backtest", log_dir=config.paths.logs)
    extra = config.extra
    root = config.paths.root
    out_dir = config.paths.results / str(extra.get("out_dir", "jump_density_backtest"))
    out_csv = out_dir / "dm_tests.csv"
    if out_csv.exists() and not args.forzar:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", out_csv)
        return

    horizons = {str(k): dict(v) for k, v in extra["horizons"].items()}
    n_sims, dm_lag = int(extra["n_sims"]), int(extra["dm_lag"])
    start, end, max_stale = str(extra["start"]), str(extra["end"]), int(extra["max_stale_days"])
    params = pd.read_csv(root / extra["params_csv"]).set_index("name")
    gammas = pd.read_csv(root / extra["target_scales_csv"]).set_index("rf")["gamma"]
    book_dir = root / extra["book_dir"]
    jump_cfgs = {
        band: yaml.safe_load((root / path).read_text(encoding="utf-8"))
        for band, path in extra["jump_configs"].items()
    }

    # Rate leg inputs: the adopted Vasicek headline cell (pipelines/18 convention).
    mc = yaml.safe_load((root / extra["market_calibration_config"]).read_text(encoding="utf-8"))
    cell_spec = mc["hw1f"]["headline"]
    by_window = pd.read_csv(root / extra["rate"]["by_window_csv"])
    cell = by_window[
        (by_window["proxy"] == cell_spec["proxy"])
        & (by_window["window"] == cell_spec["window"])
        & (by_window["sampling"] == cell_spec["sampling"])
        & (by_window["method"] == cell_spec["method"])
        & (by_window["crisis_excluded"] == bool(cell_spec["crisis_excluded"]))
    ]
    if len(cell) != 1:
        sys.exit(f"Headline cell {cell_spec} matches {len(cell)} rows in hw1f_by_window.csv")
    a, b, s_rate = (float(cell.iloc[0][k]) for k in ("alpha", "level", "sigma"))
    quotes = _read_series(root / extra["rate"]["csv"], str(extra["rate"]["column"])) / 100.0
    rate = pd.Series(
        simple_to_continuous(quotes.to_numpy(), float(extra["rate"]["tenor_days"])),
        index=quotes.index,
    )
    rate_target = str(extra["rate"]["target"])

    rows, pooled_rows, diffs_by_key = [], [], {}
    for h_key, spec in horizons.items():
        dates = init_dates(start, end, spec)
        rate_dates = init_dates(str(extra["rate"]["start"]), end, spec)
        for band, jump_cfg in jump_cfgs.items():
            totals = jump_totals(jump_cfg, spec, n_sims, config.seed)
            rng = get_stream_rng(config.seed, 7)
            for name, jumps in totals.items():
                if name == rate_target:
                    windows = realised_windows(rate, rate_dates, spec, max_stale)
                    if windows.empty:
                        continue
                    tau = windows["tau_years"].to_numpy()
                    decay = np.exp(-a * tau)
                    mean = b + (windows["start"].to_numpy() - b) * decay
                    sd = np.sqrt(s_rate**2 * (1.0 - decay**2) / (2.0 * a))
                    y = windows["end"].to_numpy()
                    gamma = float("nan")
                else:
                    csv = book_dir / f"{name}.csv"
                    if not csv.exists() or name not in params.index:
                        logger.warning("%s: no closes or no GBM parameters, skipped", name)
                        continue
                    windows = realised_windows(
                        _read_series(csv, str(extra["price_column"])), dates, spec, max_stale
                    )
                    if windows.empty:
                        continue
                    tau = windows["tau_years"].to_numpy()
                    mu, sigma = float(params.loc[name, "drift"]), float(
                        params.loc[name, "volatility"]
                    )
                    mean = (mu - 0.5 * sigma**2) * tau
                    sd = sigma * np.sqrt(tau)
                    y = np.log(windows["end"].to_numpy() / windows["start"].to_numpy())
                    gamma = float(gammas.get(name, float("nan")))
                scored = score_series(y, mean, sd, jumps, rng, dm_lag)
                for variant, res in scored.items():
                    diff = res.pop("_diff")
                    rows.append(
                        {
                            "horizon": h_key,
                            "band": band,
                            "variant": variant,
                            "name": name,
                            "gamma": gamma,
                        }
                        | res
                    )
                    if name != rate_target:
                        diffs_by_key.setdefault((h_key, band, variant), []).append(
                            pd.Series(diff, index=windows["init_date"].to_numpy())
                        )
            logger.info("%s / %s: %d names scored", h_key, band, len(totals))
    table = pd.DataFrame(rows)

    for (h_key, band, variant), series_list in diffs_by_key.items():
        panel = pd.concat(series_list, axis=1).sort_index()
        pooled = panel.mean(axis=1).dropna()
        dm = diebold_mariano(pooled.to_numpy(), lag=dm_lag)
        pooled_rows.append(
            {
                "horizon": h_key,
                "band": band,
                "variant": variant,
                "n_dates": int(pooled.size),
                "n_names": int(panel.shape[1]),
                "mean_diff": float(pooled.mean()),
                "dm_stat": dm.statistic,
                "dm_p": dm.p_value,
                "names_rejecting_on_5pct": int(
                    (
                        (table["horizon"] == h_key)
                        & (table["band"] == band)
                        & (table["variant"] == variant)
                        & (table["name"] != rate_target)
                        & (table["dm_stat"] < 0)
                        & (table["dm_p"] < 0.05)
                    ).sum()
                ),
            }
        )
    pooled_table = pd.DataFrame(pooled_rows)
    for _, r in pooled_table.iterrows():
        logger.info(
            "%s / %s / %s: pooled DM %.2f (p=%.3f), mean log-score diff %+.4f over %d names, "
            "%d names reject jump-on at 5 %%",
            r["horizon"],
            r["band"],
            r["variant"],
            r["dm_stat"],
            r["dm_p"],
            r["mean_diff"],
            r["n_names"],
            r["names_rejecting_on_5pct"],
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    table.round(6).to_csv(out_csv, index=False)
    pooled_table.round(6).to_csv(out_dir / "dm_pooled.csv", index=False)
    viz.apply_style()
    written: list[Path] = []
    for h_key in horizons:
        fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.6), sharey=True)
        for ax, variant in zip(axes, ("engine", "compensated"), strict=True):
            for band, color in (("headline", COLOR_CLIMATE), ("floor", COLOR_BASELINE)):
                sub = table[
                    (table["horizon"] == h_key)
                    & (table["variant"] == variant)
                    & (table["band"] == band)
                    & (table["name"] != rate_target)
                ]
                ax.scatter(sub["gamma"], sub["dm_stat"], s=18, color=color, alpha=0.8, label=band)
            ax.axhline(0.0, color=TEXT_SECONDARY, linewidth=0.8)
            ax.axhline(-1.96, color=TEXT_SECONDARY, linewidth=0.8, linestyle="--")
            ax.set_xscale("log")
            ax.set_xlabel("gamma (sector sensitivity, Mexican anchor)")
            ax.set_title(f"{variant} variant, {h_key}")
        axes[0].set_ylabel("Diebold–Mariano statistic (jump-on − jump-off log score)")
        axes[0].legend(frameon=False, fontsize=8)
        fig.suptitle(
            "Jump-on vs jump-off density on realised returns — negative = jump-on scores worse",
            fontweight="bold",
            x=0.01,
            ha="left",
        )
        written.extend(viz.save_figure(fig, out_dir / f"dm_vs_gamma_{h_key}"))
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=root)
    manifest_path = manifest.write(config.paths.manifests)
    print(pooled_table.round(3).to_string(index=False))
    print(f"\nTables:   {out_dir}\nFigures:  {len(written)} files\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
