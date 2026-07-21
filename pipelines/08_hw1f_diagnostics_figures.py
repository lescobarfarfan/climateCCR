"""HW1F estimator-disagreement figures — the MKT-CALIB-02 check, visualized.

AR(1) and exact MLE fitted the same F-TIIE sample but split ``a``/``sigma``
differently (pipelines/07). This pipeline makes the disagreement concrete by
running the **engine's own** HW1F (processes.diffusions.hw1f, Andersen-
Piterbarg exact transitions) under both parameter sets with the *same*
Gaussian increments and the calibrated MXN curve, and rendering:

- ``fan_ftiie_mle`` — every trajectory (low opacity) + the Monte-Carlo mean
  vs the model's own ``E[r(t)]`` and ``±2 sd(t)`` (PNG-only, 600 dpi);
- ``estimator_comparison`` — analytic mean ±2 sd ribbons, AR(1) vs MLE: what
  the alpha/sigma split does (and does not) change;
- ``jump_decay`` — a 100 bp climate rate jump fading at ``exp(-alpha*t)``
  under each fitted alpha and the engine fixture's 0.05 (DC-CCR-SIM-2).

Needs pipelines/07_market_calibration.py output. Same config + seed ->
bit-for-bit figures (GEN-06/07); idempotent, rerun with ``--forzar``.

    python pipelines/08_hw1f_diagnostics_figures.py [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DIAG_CONFIG = REPO_ROOT / "configs" / "hw1f_diagnostics.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the figures exist"
    )
    args = parser.parse_args()

    from climateCCR import viz
    from climateCCR.data.market.curve import Curve
    from climateCCR.infra import RunManifest, get_logger, get_rng, load_config
    from climateCCR.processes.diffusions.hw1f import HW1F
    from climateCCR.utils.calendar_utils import transform_dates_to_time_differences

    config = load_config(DIAG_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.hw1f_diagnostics", log_dir=config.paths.logs)

    calib_dir = config.paths.root / config.extra["calibration_dir"]
    by_window_csv = calib_dir / "hw1f_by_window.csv"
    direct_csv = calib_dir / "direct_input" / "RFE_HW1F_Calibration_MX.csv"
    for required in (by_window_csv, direct_csv):
        if not required.exists():
            sys.exit(f"Missing {required}; run pipelines/07_market_calibration.py first.")

    out_dir = config.paths.results / "figures" / "hw1f_diagnostics"
    if (out_dir / "estimator_comparison.png").exists() and not args.forzar:
        logger.info("Figures exist, nothing to do (rerun with --forzar): %s", out_dir)
        return

    # --- the two parameter sets for the same sample ----------------------
    cell = config.extra["compare"]
    table = pd.read_csv(by_window_csv)
    selected = table[
        (table["proxy"] == cell["proxy"])
        & (table["window"] == cell["window"])
        & (table["crisis_excluded"] == bool(cell["crisis_excluded"]))
    ].set_index("method")
    if not {"ar1", "mle"} <= set(selected.index):
        sys.exit(f"Cell {cell} lacks ar1/mle rows in {by_window_csv}.")
    fits = {
        m: (float(selected.loc[m, "alpha"]), float(selected.loc[m, "sigma"]))
        for m in ("ar1", "mle")
    }

    # --- the calibrated MXN curve, as the engine reads it (DC-CCR-CAL-1) --
    row = pd.read_csv(direct_csv).iloc[0]
    tenors = sorted(
        int(k.removeprefix("rate_curve_T")) for k in row.index if k.startswith("rate_curve_T")
    )
    curve = Curve({row[f"rate_curve_T{i}"]: float(row[f"rate_curve_V{i}"]) for i in tenors})
    valuation_date = pd.read_csv(calib_dir / "nelson_siegel.csv")["valuation_date"].iloc[0]

    n_steps = int(
        round(float(config.extra["horizon_years"]) * 365 / int(config.extra["step_days"]))
    )
    dates = list(
        pd.date_range(
            valuation_date, periods=n_steps + 1, freq=f"{int(config.extra['step_days'])}D"
        )
    )
    times = np.asarray(transform_dates_to_time_differences(dates[0], dates))
    increments = get_rng(config.seed).standard_normal((int(config.n_paths), n_steps, 1))

    def engine_model(alpha: float, sigma: float) -> HW1F:
        name = str(row["name"])
        model = HW1F(name)
        market_data = {
            "RFE_HW1F_calibration": {
                name: {"alpha": alpha, "volatility": sigma, "rate_curve": curve}
            }
        }
        parameters = {"RFE_HW1F_calibration": {name: {"calibration_method": "direct_input"}}}
        model.calibrate(market_data, parameters)
        return model

    paths, analytic_mean, analytic_sd = {}, {}, {}
    for method, (alpha, sigma) in fits.items():
        model = engine_model(alpha, sigma)
        paths[method] = model.simulate(dates, increments) * 100.0
        analytic_mean[method] = np.asarray(model.mean(times), dtype=float) * 100.0
        analytic_sd[method] = np.asarray(model.volatility(times), dtype=float) * 100.0
        mc_gap_bp = float(np.abs(paths[method].mean(axis=0) - analytic_mean[method]).max()) * 100.0
        stationary_bp = sigma / np.sqrt(2.0 * alpha) * 1e4
        logger.info(
            "%s: a=%.4f sigma=%.4f | MC mean vs E[r(t)] max gap %.1f bp "
            "(MC se at 10y ~%.1f bp) | sd(10y) %.0f bp, stationary %.0f bp",
            method,
            alpha,
            sigma,
            mc_gap_bp,
            analytic_sd[method][-1] * 100.0 / np.sqrt(config.n_paths),
            analytic_sd[method][-1] * 100.0,
            stationary_bp,
        )

    # --- figures ----------------------------------------------------------
    viz.apply_style()
    written: list[Path] = []
    a_mle, s_mle = fits["mle"]
    written += viz.save_figure(
        viz.plot_rate_path_fan(
            dates,
            paths["mle"],
            analytic_mean["mle"],
            analytic_sd["mle"],
            title=(
                f"HW1F short rate, MXN curve @ {valuation_date} — {config.n_paths} trajectories "
                f"vs the model expectation (MLE: a={a_mle:.3f}, $\\sigma$={s_mle:.4f})"
            ),
        ),
        out_dir / "fan_ftiie_mle",
        formats=("png",),
        dpi=600,
    )
    labels = [
        f"AR(1): a={fits['ar1'][0]:.3f}, $\\sigma$={fits['ar1'][1]:.4f}",
        f"MLE:  a={fits['mle'][0]:.3f}, $\\sigma$={fits['mle'][1]:.4f}",
    ]
    written += viz.save_figure(
        viz.plot_estimator_fan_comparison(
            dates,
            [analytic_mean["ar1"], analytic_mean["mle"]],
            [analytic_sd["ar1"], analytic_sd["mle"]],
            labels,
            title="AR(1) vs exact MLE on the same F-TIIE sample — model mean ±2 sd",
        ),
        out_dir / "estimator_comparison",
    )
    written += viz.save_figure(
        viz.plot_jump_decay(
            {
                f"AR(1) a={fits['ar1'][0]:.3f}": fits["ar1"][0],
                f"MLE a={fits['mle'][0]:.3f}": fits["mle"][0],
                f"Engine fixture a={float(config.extra['engine_alpha']):.2f}": float(
                    config.extra["engine_alpha"]
                ),
            },
            jump_bp=float(config.extra["jump_bp"]),
            title="Climate rate-jump persistence under each mean reversion (DC-CCR-SIM-2)",
        ),
        out_dir / "jump_decay",
    )

    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)
    logger.info("Wrote %d files to %s; manifest %s", len(written), out_dir, manifest_path)
    print(f"{len(written)} figure files -> {out_dir}\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
