"""Hazard-model out-of-time backtest — tier A of the INT-40 validation layer.

Fit on the registry window (2002–2015), predict the report window (2016–2024)
the fit never saw, score the realisations — the BCBS 2010 ¶24/¶41 back-pricing
discipline applied to the HAZ frequency–severity estimator (DC-XWALK-4):

- **counts** — the Poisson predictive of the test-window total under
  ``lambda_fit`` (two-sided p, midpoint PIT) and the randomised PIT of every
  test-year count [CzadoGneitingHeld2009]; the fit-window dispersion ratio
  (var/mean of annual counts) as the Poisson-adequacy diagnostic;
- **severity** — PIT of every test-window event loss under the fit-window
  lognormal, KS against U(0, 1); the largest test loss (Otis, 2023) with its PIT;
- **annual aggregate loss** — the compound-Poisson predictive
  (``simulate_annual_losses``) scored per test year: PIT, central 50/80/95
  membership, CRPS; summary coverage, mean CRPS, actual-vs-expected on the mean
  AND the median (a sigma 1.2–2.9 lognormal makes the mean tail-driven,
  [Klugman2019]), KS of the per-year PITs.

Streams: the regime-continuous ciclón stream (unthresholded and >= 200 MDP-2025)
is the fair out-of-time test; the all-perils trigger set is run only as the
censoring illustration (HAZ-CENAPRED-10, registry -> report publication break)
and carries ``censored = True`` in every table.

Deterministic given ``seed`` (GEN-06/07); idempotent, rerun with ``--forzar``.

    python pipelines/27_hazard_backtest.py [--config CFG] [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "hazard_backtest.yaml"


def count_backtest(
    fit_counts: pd.Series, test_counts: pd.Series, rng: np.random.Generator
) -> tuple[dict, np.ndarray]:
    """Poisson predictive of the test window under the fit-window intensity.

    Returns the summary dict (lambda, predicted mean/sd of the test total, the
    realised total, its midpoint PIT and two-sided p-value, the fit-window
    dispersion ratio) and the randomised per-year PIT values.
    """
    from climateCCR.risk.market import pit_discrete

    lam = float(fit_counts.mean())
    n_years = int(len(test_counts))
    total = int(test_counts.sum())
    mean = lam * n_years
    cdf_total = float(stats.poisson.cdf(total, mean))
    cdf_below = float(stats.poisson.cdf(total - 1, mean)) if total > 0 else 0.0
    yearly = test_counts.to_numpy(dtype=int)
    pit_years = pit_discrete(
        stats.poisson.cdf(yearly, lam),
        np.where(yearly > 0, stats.poisson.cdf(yearly - 1, lam), 0.0),
        rng,
    )
    summary = {
        "lambda_fit": lam,
        "n_fit_years": int(len(fit_counts)),
        "n_fit_events": int(fit_counts.sum()),
        "dispersion_ratio_fit": float(fit_counts.var(ddof=1) / fit_counts.mean()),
        "n_test_years": n_years,
        "n_test_events": total,
        "predicted_mean": mean,
        "predicted_sd": float(np.sqrt(mean)),
        "pit_total": float(pit_discrete([cdf_total], [cdf_below])[0]),
        "p_two_sided": float(min(1.0, 2.0 * min(cdf_total, 1.0 - cdf_below))),
    }
    return summary, pit_years


def severity_backtest(fit, test_events: pd.DataFrame) -> tuple[dict, np.ndarray]:
    """PIT of the test-window losses under the fit-window lognormal, with the KS test."""
    from climateCCR.risk.market import ks_uniform

    losses = test_events["danio_mdp"].astype(float)
    losses = losses[losses > 0]
    pit = stats.norm.cdf((np.log(losses.to_numpy()) - np.log(fit.median)) / fit.sigma)
    ks = ks_uniform(pit)
    i_max = int(np.argmax(losses.to_numpy()))
    row = test_events.loc[losses.index[i_max]]
    summary = {
        "median_fit": fit.median,
        "sigma_fit": fit.sigma,
        "n_fit": fit.n_events,
        "n_test": int(losses.size),
        "mean_pit": float(pit.mean()),
        "ks_stat": ks.statistic,
        "ks_p": ks.p_value,
        "max_test_loss_mdp": float(losses.iloc[i_max]),
        "max_test_loss_year": int(row["anio"]),
        "max_test_loss_event": str(row.get("nombre_evento", "")),
        "max_test_loss_pit": float(pit[i_max]),
    }
    return summary, pit


def annual_loss_backtest(
    sims: np.ndarray, realised: pd.Series, levels: list[float]
) -> tuple[pd.DataFrame, dict]:
    """Score realised annual aggregates against one set of compound-Poisson draws."""
    from climateCCR.risk.market import crps_from_samples, ks_uniform, pit_values

    y = realised.to_numpy(dtype=float)
    samples = np.broadcast_to(sims[:, None], (sims.size, y.size))
    pit = pit_values(samples, y)
    crps = crps_from_samples(samples, y)
    quantiles = np.quantile(sims, [0.05, 0.5, 0.95])
    rows = pd.DataFrame(
        {
            "year": realised.index.astype(int),
            "realised_mdp": y,
            "model_mean_mdp": float(sims.mean()),
            "model_q05_mdp": quantiles[0],
            "model_q50_mdp": quantiles[1],
            "model_q95_mdp": quantiles[2],
            "pit": pit,
            "crps_mdp": crps,
        }
    )
    for level in levels:
        lo = (1.0 - level) / 2.0
        rows[f"in_central_{int(round(100 * level))}"] = (pit >= lo) & (pit <= 1.0 - lo)
    summary = {
        "n_test_years": int(y.size),
        "ae_mean": float(y.mean() / sims.mean()),
        "ae_median": float(np.median(y) / np.median(sims)),
        "crps_mean_mdp": float(crps.mean()),
        "ks_p_pit": ks_uniform(pit).p_value,
    }
    for level in levels:
        summary[f"coverage_{int(round(100 * level))}"] = float(
            rows[f"in_central_{int(round(100 * level))}"].mean()
        )
    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    args = parser.parse_args()

    from climateCCR import viz
    from climateCCR.calibration.impact import (
        annual_event_counts,
        estimate_intensity,
        fit_severity,
        load_climate_events,
        simulate_annual_losses,
    )
    from climateCCR.infra import RunManifest, get_logger, get_stream_rng, load_config

    config = load_config(args.config)
    config.paths.ensure()
    logger = get_logger("climateCCR.hazard_backtest", log_dir=config.paths.logs)
    extra = config.extra
    root = config.paths.root
    out_dir = config.paths.results / str(extra.get("out_dir", "hazard_backtest"))
    out_csv = out_dir / "annual_loss.csv"
    if out_csv.exists() and not args.forzar:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", out_csv)
        return

    deflator_file = root / extra["deflator"]
    deflator = {
        int(y): float(v) for y, v in yaml.safe_load(deflator_file.read_text())["inpc"].items()
    }
    events_csv = root / extra["events_csv"]
    fit_w = (int(extra["fit_window"]["start_year"]), int(extra["fit_window"]["end_year"]))
    test_w = (int(extra["test_window"]["start_year"]), int(extra["test_window"]["end_year"]))
    levels = [float(v) for v in extra["levels"]]
    n_sims = int(extra["n_sims"])

    count_rows, severity_rows, loss_rows, loss_summaries = [], [], [], []
    pit_hists: dict[str, np.ndarray] = {}
    written: list[Path] = []
    viz.apply_style()
    for stream_index, (stream_key, spec) in enumerate(extra["streams"].items(), start=1):
        perils = spec.get("perils")
        threshold = spec.get("min_damage_mdp")
        threshold = None if threshold is None else float(threshold)
        kwargs = {"perils": perils, "min_damage_mdp": threshold, "deflator": deflator}
        fit_events = load_climate_events(
            events_csv, start_year=fit_w[0], end_year=fit_w[1], **kwargs
        )
        test_events = load_climate_events(
            events_csv, start_year=test_w[0], end_year=test_w[1], **kwargs
        )
        fit_counts = annual_event_counts(fit_events)
        test_counts = annual_event_counts(test_events)
        rng = get_stream_rng(config.seed, stream_index)  # one substream per stream (GEN-07)
        base = {
            "stream": stream_key,
            "label": str(spec["label"]),
            "censored": bool(spec["censored"]),
        }

        count_summary, pit_years = count_backtest(fit_counts, test_counts, rng)
        intensity = estimate_intensity(fit_counts)
        count_summary.update(
            {"lambda_ci_low": intensity.ci_low, "lambda_ci_high": intensity.ci_high}
        )
        count_rows.append(base | count_summary)
        for year, count, pit in zip(test_counts.index, test_counts, pit_years, strict=True):
            count_rows.append(
                base | {"test_year": int(year), "test_count": int(count), "pit_year": float(pit)}
            )

        fit = fit_severity(fit_events, deflated=True)
        sev_summary, _ = severity_backtest(fit, test_events)
        severity_rows.append(base | sev_summary)

        sims = simulate_annual_losses(
            count_summary["lambda_fit"], fit.median, fit.sigma, n_sims, rng
        )
        realised = (
            test_events.groupby("anio")["danio_mdp"]
            .sum()
            .reindex(range(test_w[0], test_w[1] + 1), fill_value=0.0)
        )
        rows, loss_summary = annual_loss_backtest(sims, realised, levels)
        loss_rows.append(rows.assign(**base))
        loss_summaries.append(base | loss_summary)
        pit_hists[str(spec["label"])] = rows["pit"].to_numpy()
        logger.info(
            "%s%s: lambda_fit %.3f/yr -> test total %d vs %.1f ± %.1f (p=%.2f) | "
            "severity KS p=%.2f (max %s %.0f MDP, PIT %.3f) | "
            "annual S coverage50/80/95 = %.2f/%.2f/%.2f, A/E mean %.2f median %.2f",
            stream_key,
            " [censored]" if spec["censored"] else "",
            count_summary["lambda_fit"],
            count_summary["n_test_events"],
            count_summary["predicted_mean"],
            count_summary["predicted_sd"],
            count_summary["p_two_sided"],
            sev_summary["ks_p"],
            sev_summary["max_test_loss_event"],
            sev_summary["max_test_loss_mdp"],
            sev_summary["max_test_loss_pit"],
            loss_summary["coverage_50"],
            loss_summary["coverage_80"],
            loss_summary["coverage_95"],
            loss_summary["ae_mean"],
            loss_summary["ae_median"],
        )

        all_events = load_climate_events(
            events_csv, start_year=fit_w[0], end_year=test_w[1], **kwargs
        )
        dates = pd.to_datetime(all_events["fecha_inicio"], errors="coerce").dropna()
        fig = viz.plot_arrival_staircase(
            dates,
            [
                {
                    "start": f"{fit_w[0]}-01-01",
                    "end": f"{test_w[1]}-12-31",
                    "intensity": count_summary["lambda_fit"],
                    "label": f"λ fit {fit_w[0]}–{fit_w[1]} = {count_summary['lambda_fit']:.2f}/yr, "
                    "extended (no re-anchor)",
                }
            ],
            title=f"{spec['label']}: arrivals vs the fit-window intensity",
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        written.extend(viz.save_figure(fig, out_dir / f"arrival_staircase_{stream_key}"))

    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(count_rows).round(6).to_csv(out_dir / "counts.csv", index=False)
    pd.DataFrame(severity_rows).round(6).to_csv(out_dir / "severity.csv", index=False)
    pd.concat(loss_rows, ignore_index=True).round(6).to_csv(out_csv, index=False)
    pd.DataFrame(loss_summaries).round(6).to_csv(out_dir / "annual_loss_summary.csv", index=False)
    fig = viz.plot_pit_histograms(
        pit_hists, bins=5, ncols=3, title="Annual aggregate loss: PIT of the test years"
    )
    written.extend(viz.save_figure(fig, out_dir / "annual_loss_pit"))
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=root)
    manifest_path = manifest.write(config.paths.manifests)
    print(pd.DataFrame(loss_summaries).round(3).to_string(index=False))
    print(f"\nTables:   {out_dir}\nFigures:  {len(written)} files\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
