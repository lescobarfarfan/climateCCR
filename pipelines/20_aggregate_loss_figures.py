"""Aggregate-loss distribution figures — the OQ-GEN-02 (c) robustness reads.

Two families, both INT-23 "robustness mention" objects next to the EE-family
headline:

- ``book_exposure_<run>`` — per-path whole-book exposure distributions
  (baseline vs climate legs, q99 marked) at configured horizons, from the
  ``pipelines/01 --trayectorias`` npz artifacts (settlement currency).
- ``annual_aggregate_loss`` — the compound-Poisson annual aggregate loss
  ``S = sum of severities`` per lambda leg, simulated directly from the fitted
  jump parameters (real MDP-2025; the classic aggregate-loss object
  [Klugman2019]) — no engine involvement.

Deterministic given the config seed (GEN-06/07). Idempotent, rerun with
``--forzar``.

    python pipelines/20_aggregate_loss_figures.py [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "aggregate_loss.yaml"


def book_exposure(
    per_path: dict[str, tuple[np.ndarray, np.ndarray]]
) -> tuple[np.ndarray, np.ndarray]:
    """(dates, book values): sum over counterparties of ``max(V, 0)`` per path/date."""
    dates = None
    total = None
    for naid, (naid_dates, values) in per_path.items():
        if dates is None:
            dates, total = naid_dates, np.maximum(values, 0.0)
        else:
            if not np.array_equal(naid_dates, dates):
                raise ValueError(f"Counterparty {naid!r} reporting grid differs from the book's")
            total = total + np.maximum(values, 0.0)
    return dates, total


def simulate_annual_losses(
    intensity_per_yr: float, sev_median: float, sev_sigma: float, n_sims: int, rng
) -> np.ndarray:
    """Compound-Poisson annual aggregate: N ~ Poisson, severities lognormal."""
    counts = rng.poisson(intensity_per_yr, n_sims)
    draws = rng.lognormal(mean=np.log(sev_median), sigma=sev_sigma, size=int(counts.sum()))
    owner = np.repeat(np.arange(n_sims), counts)
    return np.bincount(owner, weights=draws, minlength=n_sims)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the figures exist"
    )
    args = parser.parse_args()

    from climateCCR import viz
    from climateCCR.infra import RunManifest, get_logger, get_rng, load_config
    from climateCCR.risk.ccr.evaluators.artifacts import read_per_path_values

    config = load_config(args.config)
    config.paths.ensure()
    logger = get_logger("climateCCR.aggregate_loss", log_dir=config.paths.logs)
    extra = config.extra

    out_dir = config.paths.results / "figures" / str(extra["run_name"])
    if (out_dir / "annual_aggregate_loss.png").exists() and not args.forzar:
        logger.info("Figures exist, nothing to do (rerun with --forzar): %s", out_dir)
        return

    viz.apply_style()
    written: list[Path] = []

    pp_cfg = extra["per_path"]
    quantile = float(pp_cfg["quantile"])
    for label, run_dir in dict(pp_cfg["runs"]).items():
        legs = {}
        for leg in ("baseline", "climate"):
            npz = config.paths.results / str(run_dir) / f"per_path_values_{leg}.npz"
            if not npz.exists():
                sys.exit(f"Missing per-path artifact (pipelines/01 --trayectorias): {npz}")
            legs[leg] = book_exposure(read_per_path_values(npz))
        dates = pd.to_datetime(pd.Series(legs["baseline"][0]))
        panels = {}
        for years in list(pp_cfg["horizons_years"]):
            target = dates.iloc[0] + pd.Timedelta(days=round(365.25 * float(years)))
            pos = int((dates - target).abs().idxmin())
            panels[f"{years:g}y ({dates.iloc[pos].date()})"] = {
                leg: values[:, pos] for leg, (_, values) in legs.items()
            }
            for leg in ("baseline", "climate"):
                q = float(np.quantile(legs[leg][1][:, pos], quantile))
                logger.info("%s %sy %s: q%.0f%% %.2f", label, years, leg, 100 * quantile, q)
        slug = str(run_dir).removeprefix("climate_jump_real_mexican").strip("_") or "headline"
        written.extend(
            viz.save_figure(
                viz.plot_book_exposure_distribution(panels, quantile=quantile),
                out_dir / f"book_exposure_{slug}",
            )
        )

    cp_cfg = extra["compound_poisson"]
    parameters = pd.read_csv(config.paths.root / str(cp_cfg["parameters_csv"])).set_index("variant")
    rng = get_rng(config.seed)
    losses = {}
    for label, rows in dict(cp_cfg["legs"]).items():
        lam = float(parameters.loc[str(rows["intensity_row"]), "intensity_per_yr"])
        severity = parameters.loc[str(rows["severity_row"])]
        losses[str(label)] = simulate_annual_losses(
            lam,
            float(severity["sev_median_mdp"]),
            float(severity["sev_sigma"]),
            int(extra["n_sims"]),
            rng,
        )
        logger.info(
            "%s: lambda %.4f, sev median %.1f sigma %.4f -> mean S %.0f, q99 %.0f",
            label,
            lam,
            severity["sev_median_mdp"],
            severity["sev_sigma"],
            losses[str(label)].mean(),
            np.quantile(losses[str(label)], 0.99),
        )
    written.extend(
        viz.save_figure(
            viz.plot_annual_aggregate_loss(losses, quantiles=tuple(cp_cfg["quantiles"])),
            out_dir / "annual_aggregate_loss",
        )
    )

    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)
    logger.info("Wrote %d files to %s; manifest %s", len(written), out_dir, manifest_path)
    print(f"{len(written)} figure files -> {out_dir}\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
