"""Loss->mark seam backtest against realised CNSF loss ratios — tier B of INT-40.

The INT-17 translation reads a trigger-set event loss ``L`` as an insured
loss-ratio contribution ``beta * L / K`` of the climate-exposed CNSF book (hidro +
agro). Summed over a year the modelled mark is ``beta * S / K`` — an annual
insured loss ratio — and CNSF publishes the realised ratio ``paid / premium``
every year 2008–2024 with no publication break (the measurement the CENAPRED
stream lacks after 2016). This pipeline scores that prediction, the magnitude
check of the H2 channel:

- realised ``LR_y = paid_y / premium_y`` (``annual_real_amounts`` over the
  configured consolidados, both sides real MDP-2025 so the ratio is unit-free);
- modelled ``LR_y ~ beta * S / premium_y`` with ``S ~ CP(lambda, lognormal)`` from
  the registry rows (the homogeneous headline calibration); variant ``k_fixed``
  divides by the mark's own ``K`` (the k_year premium) instead of the year's;
- the **trigger-share bridge**: ``beta`` was estimated as ``sum(paid) /
  sum(damage of ALL discrete climate events)`` on the beta window while ``S``
  covers only the >= threshold trigger set, so ``share = damage(trigger) /
  damage(all)`` on that window and the bridged model is ``raw / share``;
- the **attritional floor**: the minimum in-sample realised ratio is treated as
  the non-catastrophe claims baseline and subtracted from the realised ratio
  before scoring against the raw (cat-only) model — the third reading.

Scored per year: PIT, central-band membership, CRPS; per variant x window
(in-sample = the beta window, out-of-time = 2016–2024): central coverage, mean
CRPS, actual/expected on the mean and the median, KS of the PITs. None of the
three readings is "the" answer — the table says so by carrying all three.

Deterministic given ``seed``; idempotent, rerun with ``--forzar``.

    python pipelines/28_loss_ratio_backtest.py [--config CFG] [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "loss_ratio_backtest.yaml"
_TYPED_KEYS = {"seed", "n_paths", "settlement_currency", "date_format"}


def trigger_share(
    all_damage: pd.Series, trigger_damage: pd.Series, window: tuple[int, int]
) -> float:
    """Share of the window's discrete climate damage carried by the trigger set."""
    years = range(window[0], window[1] + 1)
    total = float(all_damage.reindex(years, fill_value=0.0).sum())
    part = float(trigger_damage.reindex(years, fill_value=0.0).sum())
    if total <= 0 or part <= 0:
        raise ValueError(f"damage must be positive on the window: all={total}, trigger={part}")
    return part / total


def score_years(
    sims: np.ndarray, denominators: pd.Series, realised: pd.Series, scale: float, levels
) -> tuple[pd.DataFrame, dict]:
    """Score realised ratios against ``scale * S / denominator_y`` per year."""
    from climateCCR.risk.market import crps_from_samples, ks_uniform, pit_values

    y = realised.to_numpy(dtype=float)
    samples = scale * sims[:, None] / denominators.to_numpy(dtype=float)[None, :]
    pit = pit_values(samples, y)
    crps = crps_from_samples(samples, y)
    rows = pd.DataFrame(
        {
            "year": realised.index.astype(int),
            "realised_lr": y,
            "model_mean_lr": samples.mean(axis=0),
            "model_q05_lr": np.quantile(samples, 0.05, axis=0),
            "model_q50_lr": np.quantile(samples, 0.50, axis=0),
            "model_q95_lr": np.quantile(samples, 0.95, axis=0),
            "pit": pit,
            "crps": crps,
        }
    )
    for level in levels:
        lo = (1.0 - level) / 2.0
        rows[f"in_central_{int(round(100 * level))}"] = (pit >= lo) & (pit <= 1.0 - lo)
    summary = {
        "n_years": int(y.size),
        "ae_mean": float(y.mean() / samples.mean()),
        "ae_median": float(np.median(y) / np.median(np.median(samples, axis=0))),
        "crps_mean": float(crps.mean()),
        "ks_p_pit": ks_uniform(pit).p_value if y.size >= 3 else float("nan"),
    }
    for level in levels:
        key = f"in_central_{int(round(100 * level))}"
        summary[f"coverage_{int(round(100 * level))}"] = float(rows[key].mean())
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
        annual_real_amounts,
        load_climate_events,
        simulate_annual_losses,
    )
    from climateCCR.infra import RunManifest, get_logger, get_rng, load_config

    config = load_config(args.config)
    config.paths.ensure()
    logger = get_logger("climateCCR.loss_ratio_backtest", log_dir=config.paths.logs)
    root = config.paths.root
    extra = dict(config.extra)
    shared = yaml.safe_load((root / str(extra["shared"])).read_text(encoding="utf-8"))
    extra = {k: v for k, v in shared.items() if k not in _TYPED_KEYS} | extra
    out_dir = config.paths.results / str(extra.get("out_dir", "loss_ratio_backtest"))
    out_csv = out_dir / "loss_ratio_backtest.csv"
    if out_csv.exists() and not args.forzar:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", out_csv)
        return

    deflator_file = root / extra["deflator"]
    deflator = {
        int(y): float(v)
        for y, v in yaml.safe_load(deflator_file.read_text(encoding="utf-8"))["inpc"].items()
    }

    def panel(entries: list[dict]) -> pd.Series:
        total = pd.Series(dtype=float)
        for entry in entries:
            series = annual_real_amounts(root / entry["file"], entry["column"], deflator)
            total = total.add(series, fill_value=0.0)
        return total.sort_index()

    paid = panel(extra["cnsf"]["paid"])
    premium = panel(extra["cnsf"]["premium"])
    realised = (paid / premium).dropna()
    realised.index = realised.index.astype(int)

    in_w = (int(extra["in_sample"]["start_year"]), int(extra["in_sample"]["end_year"]))
    out_w = (int(extra["out_of_time"]["start_year"]), int(extra["out_of_time"]["end_year"]))
    years = [y for y in realised.index if in_w[0] <= y <= out_w[1]]
    realised = realised.loc[years]
    premium = premium.loc[years]

    scale = pd.read_csv(root / extra["scale_csv"]).iloc[0]
    beta, k_mdp = float(scale["beta"]), float(scale["k_mdp"])
    params = pd.read_csv(root / extra["parameters_csv"]).set_index("variant")
    lam = float(params.loc[str(extra["intensity_row"]), "intensity_per_yr"])
    sev_median = float(params.loc[str(extra["severity_row"]), "sev_median_mdp"])
    sev_sigma = float(params.loc[str(extra["severity_row"]), "sev_sigma"])

    events_csv = root / extra["events_csv"]
    threshold = float(extra["trigger_min_damage_mdp"])
    all_events = load_climate_events(
        events_csv, start_year=in_w[0], end_year=in_w[1], deflator=deflator
    )
    trigger_events = load_climate_events(
        events_csv,
        start_year=in_w[0],
        end_year=in_w[1],
        deflator=deflator,
        min_damage_mdp=threshold,
    )
    share = trigger_share(
        all_events.groupby("anio")["danio_mdp"].sum(),
        trigger_events.groupby("anio")["danio_mdp"].sum(),
        in_w,
    )
    floor = float(realised.loc[in_w[0] : in_w[1]].min())
    logger.info(
        "beta %.4f, K %.0f MDP-2025, lambda %.4f/yr, severity median %.2f sigma %.4f; "
        "trigger share of damage %s = %.3f; attritional floor %.3f",
        beta,
        k_mdp,
        lam,
        sev_median,
        sev_sigma,
        in_w,
        share,
        floor,
    )

    n_sims = int(extra["n_sims"])
    levels = [float(v) for v in extra["levels"]]
    sims = simulate_annual_losses(lam, sev_median, sev_sigma, n_sims, get_rng(config.seed))
    k_series = pd.Series(k_mdp, index=realised.index)
    variants = {
        "raw": (premium, realised, beta),
        "bridged": (premium, realised, beta / share),
        "k_fixed": (k_series, realised, beta),
        "cat_excess": (premium, (realised - floor).clip(lower=0.0), beta),
    }
    frames, summaries = [], []
    pits: dict[str, np.ndarray] = {}
    for variant, (denominators, target, factor) in variants.items():
        rows, _ = score_years(sims, denominators, target, factor, levels)
        rows["window"] = np.where(rows["year"] <= in_w[1], "in_sample", "out_of_time")
        rows["variant"] = variant
        frames.append(rows)
        pits[variant] = rows["pit"].to_numpy()
        for window in ("in_sample", "out_of_time", "all"):
            mask = (
                rows["window"] == window if window != "all" else pd.Series(True, index=rows.index)
            )
            sub_target = target[rows.loc[mask, "year"].to_numpy()]
            sub_denom = denominators[rows.loc[mask, "year"].to_numpy()]
            _, summary = score_years(sims, sub_denom, sub_target, factor, levels)
            summaries.append({"variant": variant, "window": window} | summary)
            logger.info(
                "%s / %s: coverage50/80/95 %.2f/%.2f/%.2f, A/E mean %.2f median %.2f, CRPS %.3f",
                variant,
                window,
                summary["coverage_50"],
                summary["coverage_80"],
                summary["coverage_95"],
                summary["ae_mean"],
                summary["ae_median"],
                summary["crps_mean"],
            )

    out_dir.mkdir(parents=True, exist_ok=True)
    table = pd.concat(frames, ignore_index=True)
    table.round(6).to_csv(out_csv, index=False)
    pd.DataFrame(summaries).round(6).to_csv(out_dir / "loss_ratio_summary.csv", index=False)
    pd.DataFrame(
        [
            {
                "beta": beta,
                "k_mdp": k_mdp,
                "lambda": lam,
                "sev_median_mdp": sev_median,
                "sev_sigma": sev_sigma,
                "trigger_share": share,
                "attritional_floor": floor,
                "in_sample": f"{in_w[0]}-{in_w[1]}",
                "out_of_time": f"{out_w[0]}-{out_w[1]}",
            }
        ]
    ).to_csv(out_dir / "inputs.csv", index=False)

    viz.apply_style()
    written: list[Path] = []
    fig = viz.plot_pit_histograms(pits, bins=5, ncols=2, title="Annual loss ratio: PIT per variant")
    written.extend(viz.save_figure(fig, out_dir / "loss_ratio_pit"))
    # Realised ratios over the modelled fan (raw and bridged), year grid = Jan 1.
    grid = pd.DatetimeIndex([pd.Timestamp(year=int(y), month=1, day=1) for y in realised.index])
    observed = pd.Series(realised.to_numpy(dtype=float), index=grid)
    for variant in ("raw", "bridged"):
        factor = beta if variant == "raw" else beta / share
        paths = factor * sims[:, None] / premium.to_numpy(dtype=float)[None, :]
        fig = viz.plot_paths_vs_observed(
            grid,
            paths,
            observed,
            ylabel="Annual loss ratio (paid / premium)",
            title=f"CNSF hidro + agro loss ratio vs the modelled β·S/premium ({variant})",
        )
        written.extend(viz.save_figure(fig, out_dir / f"loss_ratio_fan_{variant}"))
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=root)
    manifest_path = manifest.write(config.paths.manifests)
    print(pd.DataFrame(summaries).round(3).to_string(index=False))
    print(f"\nTables:   {out_dir}\nFigures:  {len(written)} files\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
