"""Mexican market calibration — HW1F a/sigma, MXN curve, IPC GBM (OQ-MKT-12 a/b).

Consumes the downloaded SIE root (pipelines/05) and the IPC closes (fetched
here once if missing, GEN-05), and writes to ``results/market_calibration/``:

- ``hw1f_by_window.csv`` — Vasicek AR(1) + exact-MLE ``a``/``sigma`` per proxy
  x window x crisis-exclusion (MKT-CALIB-01/02/03/04);
- ``zero_curve_pillars.csv``, ``nelson_siegel.csv``, ``theta_grid.csv`` — the
  stripped MXN curve, its NS fit, and the HW1F ``theta(t)`` (MKT-CURVE-*,
  MKT-IR-02);
- ``gbm_by_window.csv`` — IPC drift/vol per window x exclusion;
- ``direct_input/RFE_HW1F_Calibration_MX.csv`` + ``RFE_GBM_Calibration_MX.csv``
  — the DC-CCR-CAL-1 emission (headline rows; the engine stays untouched).

Deterministic given the data; idempotent (rerun with ``--forzar``).

    python pipelines/07_market_calibration.py [--forzar]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
CALIBRATION_CONFIG = REPO_ROOT / "configs" / "market_calibration.yaml"

SHORT_TENOR_DAYS = {"FTIIE": 1.0, "TIIE28": 28.0, "TIIE91": 91.0, "TIIE182": 182.0}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    args = parser.parse_args()

    from climateCCR.calibration.financial.gbm import fit_gbm
    from climateCCR.calibration.financial.hull_white import (
        exclude_windows,
        fit_vasicek_ar1,
        fit_vasicek_mle,
        simple_to_continuous,
    )
    from climateCCR.calibration.financial.yield_curve import fit_nelson_siegel, strip_zero_curve
    from climateCCR.infra import RunManifest, get_logger, load_config
    from climateCCR.utils.calendar_utils import translate_tenor_to_years

    config = load_config(CALIBRATION_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.market_calibration", log_dir=config.paths.logs)

    out_dir = config.paths.results / "market_calibration"
    out_direct = out_dir / "direct_input"
    if (out_direct / "RFE_HW1F_Calibration_MX.csv").exists() and not args.forzar:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", out_direct)
        return

    sie_dir = config.paths.root / config.extra["sie_dir"]
    for required in (sie_dir / "tiies.csv", sie_dir / "cetes364.csv", sie_dir / "bonos_m.csv"):
        if not required.exists():
            sys.exit(f"Missing {required}; run pipelines/05_download_sie_series.py first.")

    # --- IPC closes: fetched once, with provenance (GEN-02/05) -----------
    ipc_path = config.paths.root / config.extra["ipc_csv"]
    ipc_cfg = config.extra["ipc"]
    if not ipc_path.exists():
        from climateCCR.data.market.yahoo import CHART_URL, fetch_daily_closes

        logger.info("Downloading %s from Yahoo Finance ...", ipc_cfg["symbol"])
        closes = fetch_daily_closes(ipc_cfg["symbol"], str(ipc_cfg["start"]))
        ipc_path.parent.mkdir(parents=True, exist_ok=True)
        closes.to_csv(ipc_path)
        (ipc_path.parent / "_procedencia.json").write_text(
            json.dumps(
                {
                    "descargado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "fuente": "Yahoo Finance, v8 chart API",
                    "url_base": CHART_URL,
                    "simbolo": ipc_cfg["symbol"],
                    "rango": [str(ipc_cfg["start"]), str(closes.index.max().date())],
                    "archivos": {
                        ipc_path.name: {
                            "sha256": _sha256(ipc_path),
                            "bytes": ipc_path.stat().st_size,
                        }
                    },
                },
                indent=2,
                sort_keys=True,
            )
        )
        logger.info(
            "%s: %d rows, %s..%s",
            ipc_path.name,
            len(closes),
            closes.index.min(),
            closes.index.max(),
        )

    # --- daily inputs ----------------------------------------------------
    tiies = pd.read_csv(sie_dir / "tiies.csv", index_col="Fecha", parse_dates=True)
    cetes = pd.read_csv(sie_dir / "cetes364.csv", index_col="Fecha", parse_dates=True)
    bonos = pd.read_csv(sie_dir / "bonos_m.csv", parse_dates=["Fecha"])
    ipc = pd.read_csv(ipc_path, index_col="Fecha", parse_dates=True)

    crisis = [tuple(w) for w in config.extra["crisis_windows"].values()]
    windows = config.extra["windows"]

    def window_slice(series: pd.Series, name: str) -> pd.Series:
        start, end = windows[name]
        return series.loc[pd.Timestamp(start) : pd.Timestamp(end) if end else None]

    # --- (a) HW1F a/sigma across proxies x windows x exclusions ----------
    hw_rows = []
    for proxy, spec in config.extra["hw1f"]["proxies"].items():
        quotes = tiies[proxy].dropna() / 100.0
        z = pd.Series(
            simple_to_continuous(quotes.to_numpy(), float(spec["tenor_days"])), index=quotes.index
        )
        for window in spec["windows"]:
            sub = window_slice(z, window)
            for crisis_excluded in (True, False):
                series = exclude_windows(sub, crisis if crisis_excluded else None)
                for method, fitter in (("ar1", fit_vasicek_ar1), ("mle", fit_vasicek_mle)):
                    try:
                        fit = fitter(series)
                    except ValueError as error:
                        logger.warning(
                            "%s/%s/excl=%s/%s failed: %s",
                            proxy,
                            window,
                            crisis_excluded,
                            method,
                            error,
                        )
                        continue
                    hw_rows.append(
                        {
                            "proxy": proxy,
                            "window": window,
                            "start": str(series.index.min().date()),
                            "end": str(series.index.max().date()),
                            "crisis_excluded": crisis_excluded,
                            "method": method,
                            "alpha": fit.alpha,
                            "level": fit.level,
                            "sigma": fit.sigma,
                            "half_life_years": fit.half_life_years,
                            "n_pairs": fit.n_pairs,
                            "n_pairs_dropped": fit.n_pairs_dropped,
                        }
                    )
    hw_table = pd.DataFrame(hw_rows)
    # MKT-CALIB-02 agreement check: MLE vs AR(1) alpha, same cell.
    ar1_alpha = hw_table[hw_table["method"] == "ar1"].set_index(
        ["proxy", "window", "crisis_excluded"]
    )["alpha"]
    keys = pd.MultiIndex.from_frame(hw_table[["proxy", "window", "crisis_excluded"]])
    matched = ar1_alpha.reindex(keys).to_numpy()
    hw_table["alpha_rel_diff_vs_ar1"] = np.where(
        hw_table["method"] == "mle", hw_table["alpha"] / matched - 1.0, np.nan
    )

    head = config.extra["hw1f"]["headline"]
    headline = hw_table[
        (hw_table["proxy"] == head["proxy"])
        & (hw_table["window"] == head["window"])
        & (hw_table["method"] == head["method"])
        & (hw_table["crisis_excluded"] == bool(head["crisis_excluded"]))
    ]
    if headline.empty:
        sys.exit(f"Headline HW1F cell {head} produced no fit; see the log.")
    headline = headline.iloc[0]
    logger.info(
        "HW1F headline (%s, %s, excl=%s, %s): a=%.4f (half-life %.2fy), sigma=%.4f, n=%d",
        head["proxy"],
        head["window"],
        head["crisis_excluded"],
        head["method"],
        headline["alpha"],
        headline["half_life_years"],
        headline["sigma"],
        headline["n_pairs"],
    )

    # --- the MXN zero curve at the valuation date ------------------------
    curve_cfg = config.extra["curve"]
    short_block = (tiies[list(SHORT_TENOR_DAYS)] / 100.0).join(
        cetes[["TasaRendimiento", "Plazo"]].rename(
            columns={"TasaRendimiento": "CETES364", "Plazo": "cetes_plazo"}
        )
    )
    short_block["CETES364"] /= 100.0
    bonos_by_date = bonos.dropna(subset=["Plazo", "Cupon", "Valor"]).groupby("Fecha")
    bonos_counts = bonos_by_date.size()

    requested = curve_cfg["valuation_date"]
    latest = pd.Timestamp(requested) if requested else bonos_counts.index.max()
    complete = short_block.dropna().index.intersection(
        bonos_counts[bonos_counts >= int(curve_cfg["min_bonos_buckets"])].index
    )
    candidates = complete[complete <= latest]
    if candidates.empty:
        sys.exit(f"No date <= {latest.date()} has a full short block + bonos quotes.")
    valuation_date = candidates.max()
    if (latest - valuation_date).days > int(curve_cfg["lookback_bd"]) * 2:
        sys.exit(f"Nearest complete date {valuation_date.date()} is too far from {latest.date()}.")

    row = short_block.loc[valuation_date]
    short_quotes = {days: float(row[name]) for name, days in SHORT_TENOR_DAYS.items()}
    short_quotes[float(row["cetes_plazo"])] = float(row["CETES364"])
    bonos_today = bonos_by_date.get_group(valuation_date)
    pillars = strip_zero_curve(short_quotes, bonos_today)
    ns = fit_nelson_siegel(pillars)
    pillars["ns_zero"] = ns.zero(pillars["t_years"].to_numpy())
    pillars["ns_diff_bp"] = (pillars["ns_zero"] - pillars["zero"]) * 1e4
    logger.info(
        "Curve %s: %d pillars stripped (%s), NS rmse %.1f bp (tau %.2f)",
        valuation_date.date(),
        len(pillars),
        ", ".join(pillars["source"].tail(len(bonos_today))),
        ns.rmse * 1e4,
        ns.tau,
    )

    alpha_hw, sigma_hw = float(headline["alpha"]), float(headline["sigma"])
    grid = np.arange(
        float(curve_cfg["theta_grid_step_years"]),
        float(curve_cfg["theta_grid_years"]) + 1e-9,
        float(curve_cfg["theta_grid_step_years"]),
    )
    theta_grid = pd.DataFrame(
        {
            "t_years": grid,
            "zero": ns.zero(grid),
            "forward": ns.forward(grid),
            "theta": ns.theta(grid, alpha_hw, sigma_hw),
        }
    )

    # --- (b) GBM on the IPC ----------------------------------------------
    closes = ipc[config.extra["ipc"]["price_column"]].dropna()
    gbm_rows = []
    for window in config.extra["gbm"]["windows"]:
        sub = window_slice(closes, window)
        for crisis_excluded in (True, False):
            series = exclude_windows(sub, crisis if crisis_excluded else None)
            fit = fit_gbm(series)
            gbm_rows.append(
                {
                    "window": window,
                    "start": str(series.index.min().date()),
                    "end": str(series.index.max().date()),
                    "crisis_excluded": crisis_excluded,
                    "drift": fit.drift,
                    "volatility": fit.volatility,
                    "n_returns": fit.n_returns,
                    "n_returns_dropped": fit.n_returns_dropped,
                }
            )
    gbm_table = pd.DataFrame(gbm_rows)
    ghead = config.extra["gbm"]["headline"]
    gbm_headline = gbm_table[
        (gbm_table["window"] == ghead["window"])
        & (gbm_table["crisis_excluded"] == bool(ghead["crisis_excluded"]))
    ].iloc[0]
    initial_value = float(closes[closes.index <= valuation_date].iloc[-1])
    logger.info(
        "GBM headline (%s, excl=%s): mu=%.4f, sigma=%.4f, n=%d; S0=%.0f",
        ghead["window"],
        ghead["crisis_excluded"],
        gbm_headline["drift"],
        gbm_headline["volatility"],
        gbm_headline["n_returns"],
        initial_value,
    )

    # --- write everything ------------------------------------------------
    out_dir.mkdir(parents=True, exist_ok=True)
    out_direct.mkdir(parents=True, exist_ok=True)
    hw_table.to_csv(out_dir / "hw1f_by_window.csv", index=False)
    pillars.insert(0, "valuation_date", str(valuation_date.date()))
    pillars.to_csv(out_dir / "zero_curve_pillars.csv", index=False)
    pd.DataFrame(
        [
            {
                "valuation_date": str(valuation_date.date()),
                "beta0": ns.beta0,
                "beta1": ns.beta1,
                "beta2": ns.beta2,
                "tau": ns.tau,
                "rmse_bp": ns.rmse * 1e4,
                "n_pillars": ns.n_pillars,
                "hw1f_alpha": alpha_hw,
                "hw1f_sigma": sigma_hw,
            }
        ]
    ).to_csv(out_dir / "nelson_siegel.csv", index=False)
    theta_grid.to_csv(out_dir / "theta_grid.csv", index=False)
    gbm_table.to_csv(out_dir / "gbm_by_window.csv", index=False)

    # The DC-CCR-CAL-1 emission: short pillars verbatim (day labels), long
    # canonical tenors off the NS fit (MKT-CURVE-03); engine-parseable labels.
    tenor_labels = [f"{int(round(d))}D" for d in sorted(short_quotes)] + [
        str(t) for t in curve_cfg["canonical_tenors"]
    ]
    tenor_values = [
        float(simple_to_continuous(short_quotes[d], d)) for d in sorted(short_quotes)
    ] + [float(ns.zero(translate_tenor_to_years(str(t)))) for t in curve_cfg["canonical_tenors"]]
    names = config.extra["direct_input"]
    hw_row: dict[str, object] = {"name": names["hw1f_name"]}
    hw_row.update({f"rate_curve_V{i}": v for i, v in enumerate(tenor_values, start=1)})
    hw_row.update({"alpha": alpha_hw, "volatility": sigma_hw})
    hw_row.update({f"rate_curve_T{i}": t for i, t in enumerate(tenor_labels, start=1)})
    pd.DataFrame([hw_row]).to_csv(out_direct / "RFE_HW1F_Calibration_MX.csv", index=False)
    pd.DataFrame(
        [
            {
                "name": names["gbm_name"],
                "initial_value": initial_value,
                "drift": float(gbm_headline["drift"]),
                "volatility": float(gbm_headline["volatility"]),
            }
        ]
    ).to_csv(out_direct / "RFE_GBM_Calibration_MX.csv", index=False)

    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)

    print(hw_table.to_string(index=False, float_format=lambda v: f"{v:.5g}"))
    print()
    print(gbm_table.to_string(index=False, float_format=lambda v: f"{v:.5g}"))
    print(
        f"\nHW1F direct_input: alpha={alpha_hw:.4f}, sigma={sigma_hw:.4f}, "
        f"curve {len(tenor_labels)} pillars @ {valuation_date.date()} "
        f"(NS rmse {ns.rmse * 1e4:.1f} bp)"
        f"\nGBM  direct_input: mu={float(gbm_headline['drift']):.4f}, "
        f"sigma={float(gbm_headline['volatility']):.4f}, S0={initial_value:.0f}"
        f"\nSalidas:  {out_dir}\nManifest: {manifest_path}"
    )


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
