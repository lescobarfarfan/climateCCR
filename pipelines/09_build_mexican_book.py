"""Mexican counterparty-book builder — the fixture-book swap (OQ-INT-04, OQ-MKT-12c).

Deterministic reconstructor (GEN-*): reads ``configs/mexican_book.yaml`` and writes
the complete CCR book data-root (``data/ccr_book_mx/``) in the PIMPA fixture
schemas (DC-CCR-RISK-2 layout), so ``pipelines/01_climate_jump_demo.py
--book-config configs/mexican_book.yaml --data-root data/ccr_book_mx`` runs the
engine on Mexican targets with no engine change beyond the additive DEBT desk.

Stages:
  1. Yahoo daily closes per BMV ticker (cached once + ``_procedencia.json``,
     GEN-02/05); the thin-ticker minimum-data rule drops names that fail it.
  2. Per-name GBM fits (``fit_gbm``, crisis windows excluded per MKT-CALIB-03)
     + the MXN_USD_FX_RATE GBM from Banxico FIX (DC-XWALK-5).
  3. Correlation matrix over (curve factor, FX, equities) from the joint daily
     panel — pairwise-complete sample correlation, eigenvalue-clipped to PSD.
  4. Book data-root: desks (IRS / EQ options / BONDS), counterparties + VM
     terms, master ledger, All_RFs_Mapping, market data (fixings, spots, proxy
     IV surfaces), direct_input calibration CSVs (MKT-CALIB-05/07 outputs).
  5. The Mexican-alpha ``S_rate_eff`` recompute (INT-18 inversion with the
     MKT-CALIB-05 alpha) -> ``results/loss_to_rate_scale_mx/scale.csv``.

Idempotent: skips if the book exists; rerun with --forzar/--force.

    python pipelines/09_build_mexican_book.py [--forzar]
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
BOOK_CONFIG = REPO_ROOT / "configs" / "mexican_book.yaml"

RF_COLUMNS = [
    "name",
    "asset_class",
    "type",
    "currency",
    "issuer",
    "simulated",
    "model",
    "reference",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nearest_psd_correlation(corr: pd.DataFrame, floor: float = 1e-8) -> tuple[pd.DataFrame, float]:
    """Eigenvalue-clip a correlation matrix to PSD, unit diagonal preserved.

    Returns the repaired matrix and the smallest eigenvalue before repair.
    # ponytail: eig-clip + renormalize; Ledoit-Wolf shrinkage if structure matters
    """
    a = (corr.to_numpy(dtype=float) + corr.to_numpy(dtype=float).T) / 2.0
    min_eig_before = float(np.linalg.eigvalsh(a).min())
    for _ in range(100):
        eigenvalues, eigenvectors = np.linalg.eigh(a)
        if eigenvalues.min() >= floor:
            break
        clipped = np.clip(eigenvalues, floor, None)
        a = eigenvectors @ np.diag(clipped) @ eigenvectors.T
        scale = np.sqrt(np.diag(a))
        a = a / np.outer(scale, scale)
        a = (a + a.T) / 2.0
        np.fill_diagonal(a, 1.0)
    return pd.DataFrame(a, index=corr.index, columns=corr.columns), min_eig_before


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="rebuild even if the book exists"
    )
    args = parser.parse_args()

    from climateCCR.calibration.financial.gbm import fit_gbm
    from climateCCR.calibration.financial.hull_white import exclude_windows, simple_to_continuous
    from climateCCR.calibration.impact.rate_response import rate_scale_from_beta
    from climateCCR.data.market.yahoo import CHART_URL, fetch_daily_closes
    from climateCCR.infra import RunManifest, get_logger, load_config
    from dateutil.relativedelta import relativedelta

    config = load_config(BOOK_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.mexican_book", log_dir=config.paths.logs)
    extra = config.extra

    book_root = config.paths.root / extra["book_root"]
    if (book_root / "RFs_attributes" / "All_RFs_Mapping.csv").exists() and not args.forzar:
        logger.info("Book exists, nothing to do (rerun with --forzar): %s", book_root)
        return

    valuation_date = pd.Timestamp(extra["valuation_date"])
    crisis_windows = [tuple(w) for w in extra["crisis_windows"].values()]

    hw1f_csv = config.paths.root / extra["inputs"]["hw1f_direct_input"]
    fix_csv = config.paths.root / extra["inputs"]["sie_fix"]
    tiies_csv = config.paths.root / extra["inputs"]["sie_tiies"]
    scale_csv = config.paths.root / extra["inputs"]["scale_csv"]
    for required in (hw1f_csv, fix_csv, tiies_csv, scale_csv):
        if not required.exists():
            sys.exit(f"Missing {required}; run pipelines 05/06/07 first.")

    # --- Stage 1: Yahoo closes, cached once with provenance (GEN-02/05) -----
    cache_dir = config.paths.root / extra["fetch"]["cache_subdir"]
    cache_dir.mkdir(parents=True, exist_ok=True)
    start = str(extra["fetch"]["start"])
    end = str(extra["valuation_date"])

    closes_by_rf: dict[str, pd.Series] = {}
    report_rows: list[dict] = []
    procedencia_files: dict[str, dict] = {}
    for eq in extra["equities"]:
        ticker, rf = eq["ticker"], eq["rf"]
        cache_path = cache_dir / f"{rf}.csv"
        try:
            if not cache_path.exists():
                logger.info("Downloading %s from Yahoo Finance ...", ticker)
                fetched = fetch_daily_closes(ticker, start, end)
                fetched.to_csv(cache_path)
            frame = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            procedencia_files[cache_path.name] = {
                "sha256": _sha256(cache_path),
                "bytes": cache_path.stat().st_size,
                "simbolo": ticker,
            }
            closes_by_rf[rf] = frame["Close"].dropna().loc[:valuation_date]
        except Exception as error:  # noqa: BLE001 — a dead ticker must not kill the build
            logger.warning("%s (%s): fetch failed, dropped: %s", ticker, rf, error)
            report_rows.append(
                {"ticker": ticker, "rf": rf, "status": "fallo_descarga", "motivo": str(error)}
            )

    (cache_dir / "_procedencia.json").write_text(
        json.dumps(
            {
                "descargado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "fuente": "Yahoo Finance, v8 chart API",
                "url_base": CHART_URL,
                "rango": [start, end],
                "archivos": procedencia_files,
            },
            indent=2,
            sort_keys=True,
        )
    )

    # --- minimum-data rule (thin tickers; user decision 2026-07-25) ---------
    min_years = float(extra["min_data"]["min_years"])
    max_gap_frac = float(extra["min_data"]["max_gap_frac"])
    union_calendar = pd.DatetimeIndex(
        sorted(set().union(*[s.index for s in closes_by_rf.values()]))
    )
    survivors: dict[str, pd.Series] = {}
    for eq in extra["equities"]:
        rf = eq["rf"]
        if rf not in closes_by_rf:
            continue
        series = closes_by_rf[rf]
        span_years = (series.index.max() - series.index.min()).days / 365.25
        own_calendar = union_calendar[
            (union_calendar >= series.index.min()) & (union_calendar <= series.index.max())
        ]
        missing_frac = 1.0 - len(series) / max(len(own_calendar), 1)
        row = {
            "ticker": eq["ticker"],
            "rf": rf,
            "n_obs": len(series),
            "primera": str(series.index.min().date()),
            "ultima": str(series.index.max().date()),
            "span_anios": round(span_years, 2),
            "frac_faltante": round(missing_frac, 4),
        }
        stale_days = (valuation_date - series.index.max()).days
        if span_years < min_years or missing_frac > max_gap_frac or stale_days > 30:
            row["status"] = "descartado"
            row["motivo"] = (
                f"span {span_years:.1f}y < {min_years}"
                if span_years < min_years
                else (
                    f"faltante {missing_frac:.1%} > {max_gap_frac:.0%}"
                    if missing_frac > max_gap_frac
                    else f"ultima observacion {stale_days}d antes de la valuacion"
                )
            )
            logger.warning("%s dropped: %s", rf, row["motivo"])
        else:
            row["status"] = "ok"
            survivors[rf] = series
        report_rows.append(row)

    if len(survivors) < 2:
        sys.exit(f"Only {len(survivors)} equities survive the minimum-data rule; aborting.")

    # --- Stage 2: GBM fits (crisis-excluded, MKT-CALIB-03) ------------------
    gbm_rows: list[dict] = []
    for rf, series in survivors.items():
        fit = fit_gbm(exclude_windows(series, crisis_windows))
        s0 = float(series.iloc[-1])
        gbm_rows.append(
            {"name": rf, "initial_value": s0, "drift": fit.drift, "volatility": fit.volatility}
        )
    for row in report_rows:
        match = next((g for g in gbm_rows if g["name"] == row.get("rf")), None)
        if match:
            row.update(
                s0=round(match["initial_value"], 4),
                drift=round(match["drift"], 4),
                volatility=round(match["volatility"], 4),
            )

    fix = pd.read_csv(fix_csv, index_col=0, parse_dates=True)["FIX"].dropna().loc[:valuation_date]
    fx_rf = extra["fx"]["rf"]
    fx_fit = fit_gbm(exclude_windows(fix, crisis_windows))
    gbm_rows.append(
        {
            "name": fx_rf,
            "initial_value": float(fix.iloc[-1]),
            "drift": fx_fit.drift,
            "volatility": fx_fit.volatility,
        }
    )
    gbm_frame = pd.DataFrame(gbm_rows)
    logger.info("GBM fits: %d equities + %s", len(gbm_frame) - 1, fx_rf)

    # --- Stage 3: correlation matrix (curve, FX, equities) ------------------
    curve_rf = extra["curve"]["rf"]
    tiies = pd.read_csv(tiies_csv, index_col=0, parse_dates=True)
    ftiie = tiies["FTIIE"].dropna().loc[:valuation_date] / 100.0
    ftiie_continuous = pd.Series(
        simple_to_continuous(ftiie.to_numpy(), tenor_days=1.0), index=ftiie.index
    )

    panel = pd.DataFrame(
        {
            curve_rf: exclude_windows(ftiie_continuous, crisis_windows).diff(),
            fx_rf: np.log(exclude_windows(fix, crisis_windows)).diff(),
            **{
                rf: np.log(exclude_windows(series, crisis_windows)).diff()
                for rf, series in survivors.items()
            },
        }
    )
    correlation = panel.corr(min_periods=252)  # pairwise-complete sample correlation
    if correlation.isna().any().any():
        logger.warning("Correlation pairs with <252 joint obs set to 0.")
        repaired = correlation.fillna(0.0).to_numpy()
        np.fill_diagonal(repaired, 1.0)
        correlation = pd.DataFrame(repaired, index=correlation.index, columns=correlation.columns)
    correlation, min_eig_before = nearest_psd_correlation(correlation)
    eigenvalues = np.linalg.eigvalsh(correlation.to_numpy())
    logger.info(
        "Correlation %dx%d: min eig before/after repair %.2e / %.2e, condition number %.1f",
        *correlation.shape,
        min_eig_before,
        eigenvalues.min(),
        eigenvalues.max() / eigenvalues.min(),
    )

    # --- Stage 4: write the book data-root ----------------------------------
    for subdir in (
        "portfolio_data/desks/IR",
        "portfolio_data/desks/EQ",
        "portfolio_data/desks/DEBT",
        "portfolio_data/counterparties",
        "portfolio_data/positions_keeping_system",
        "market_data",
        "calibration_data/pricing_models",
        "calibration_data/RFE_models",
        "calibration_data/collateral_models",
        "RFs_attributes",
        "backtesting_Data",
    ):
        (book_root / subdir).mkdir(parents=True, exist_ok=True)

    # Risk-factor attributes: curve + FX + equity spots + IV surfaces.
    rf_rows = [
        [curve_rf, "IR", "DISCOUNT_CURVE", "MXN", "NOT_AVAILABLE", "YES", "HW1F", "NOT_AVAILABLE"],
        [fx_rf, "FX", "SPOT", "MXN", "NOT_AVAILABLE", "YES", "GBM", "NOT_AVAILABLE"],
    ]
    issuer_by_rf = {eq["rf"]: eq["issuer"] for eq in extra["equities"]}
    for rf in survivors:
        rf_rows.append([rf, "EQ", "SPOT", "MXN", issuer_by_rf[rf], "YES", "GBM", "NOT_AVAILABLE"])
        rf_rows.append(
            [
                rf[:-6] + "_IMPLIED_VOLATILITY_SURFACE",
                "EQ_VOL",
                "SURFACE",
                "NOT_AVAILABLE",
                issuer_by_rf[rf],
                "NO",
                "NOT_AVAILABLE",
                "NOT_AVAILABLE",
            ]
        )
    pd.DataFrame(rf_rows, columns=RF_COLUMNS).to_csv(
        book_root / "RFs_attributes" / "All_RFs_Mapping.csv", index=False
    )

    # Calibration CSVs: HW1F verbatim from MKT-CALIB-05/CURVE-05; GBM from the fits.
    hw1f_frame = pd.read_csv(hw1f_csv)
    alpha_mx = float(hw1f_frame["alpha"].iloc[0])
    for target in (
        "RFE_models/RFE_HW1F_Calibration.csv",
        "pricing_models/Pricing_HW1F_Calibration.csv",
    ):
        hw1f_frame.to_csv(book_root / "calibration_data" / target, index=False)
    for target in (
        "RFE_models/RFE_GBM_Calibration.csv",
        "pricing_models/Pricing_GBM_Calibration.csv",
    ):
        gbm_frame.to_csv(book_root / "calibration_data" / target, index=False)
    correlation.to_csv(book_root / "calibration_data" / "RFE_models" / "RFE_Correlation_Matrix.csv")

    # Collateral haircuts: fixture values + MXN cash (loaded, not consumed downstream).
    pd.DataFrame(
        [
            {
                "product": "CASH_MXN",
                "currency": "MXN",
                "OE_haircut_posted": 1.0,
                "OE_haircut_received": 1.0,
            },
            {
                "product": "CASH_USD",
                "currency": "USD",
                "OE_haircut_posted": 1.0,
                "OE_haircut_received": 1.0,
            },
            {
                "product": "GOV_BOND_MXN",
                "currency": "MXN",
                "OE_haircut_posted": 1.02,
                "OE_haircut_received": 0.98,
            },
        ]
    ).to_csv(book_root / "calibration_data" / "collateral_models" / "OE_haircuts.csv", index=False)

    # Market data: spots (record), flat proxy IV surfaces [eng], fixings, zero spread row.
    pd.DataFrame(
        [{"name": g["name"], "spot": g["initial_value"]} for g in gbm_rows if g["name"] != fx_rf]
    ).to_csv(book_root / "market_data" / "Equity_Spot.csv", index=False)

    tenors = extra["iv_surface"]["tenors"]
    moneyness = extra["iv_surface"]["moneyness"]
    surface_rows = []
    for g in gbm_rows:
        if g["name"] == fx_rf:
            continue
        row: dict[str, object] = {"name": g["name"][:-6] + "_IMPLIED_VOLATILITY_SURFACE"}
        for v_index in range(len(tenors) * len(moneyness)):
            row[f"IMPLIED_VOLATILITY_SURFACE_V{v_index + 1}"] = g["volatility"]
        for t_index, tenor in enumerate(tenors):
            row[f"IMPLIED_VOLATILITY_SURFACE_T{t_index + 1}"] = tenor
        for k_index, strike in enumerate(moneyness):
            row[f"IMPLIED_VOLATILITY_SURFACE_K{k_index + 1}"] = strike
        surface_rows.append(row)
    pd.DataFrame(surface_rows).to_csv(
        book_root / "market_data" / "Equity_Implied_Volatility_Surface.csv", index=False
    )

    fixings = pd.DataFrame(
        {curve_rf: ftiie_continuous.round(8).to_numpy()},
        index=ftiie_continuous.index.strftime(config.date_format),
    )
    fixings.index.name = "Fecha"
    fixings.to_csv(book_root / "market_data" / "Historical_Fixings.csv")

    zero_spread = {"name": "MXN_TIIE28_CURVE"}
    spread_tenors = ["1M", "1Y", "5Y", "10Y", "30Y"]
    zero_spread.update({f"rate_curve_V{i + 1}": 0.0 for i in range(len(spread_tenors))})
    zero_spread.update({f"rate_curve_T{i + 1}": t for i, t in enumerate(spread_tenors)})
    pd.DataFrame([zero_spread]).to_csv(
        book_root / "market_data" / "Spread_to_Discount_Curve.csv", index=False
    )

    # Portfolio: deterministic trades per counterparty (config rules, no randomness).
    rules = extra["trade_rules"]
    s0_by_rf = {g["name"]: g["initial_value"] for g in gbm_rows}
    valuation_dt = datetime.strptime(extra["valuation_date"], config.date_format)
    lag = relativedelta(days=int(rules["irs"]["settlement_lag_days"]))

    irs_rows, option_rows, bond_rows, ledger_rows = [], [], [], []

    def _ledger(trade_id: int, feed: str, naid: int, vm_agreement: str) -> None:
        ledger_rows.append(
            {
                "trade_id": trade_id,
                "feed": feed,
                "netting_agreement_id": naid,
                "netting_set": "MAIN",
                "vm_agreement": vm_agreement,
                "im_agreement": "NOT_AVAILABLE",
                "tl_ia_agreement": "NOT_AVAILABLE",
            }
        )

    option_index = 0
    bond_id = 5000
    for cp_index, cp in enumerate(extra["counterparties"]):
        naid = cp["naid"]
        vm_agreement = "VM_1" if cp.get("vm") else "NOT_AVAILABLE"

        equity_rf = cp.get("equity_rf")
        if equity_rf:  # one IRS per listed issuer (debt-only NAIDs carry bonds alone)
            tenor = rules["irs"]["tenor_cycle"][cp_index % len(rules["irs"]["tenor_cycle"])]
            direction = rules["irs"]["direction_cycle"][
                cp_index % len(rules["irs"]["direction_cycle"])
            ]
            n_periods = 4 * tenor
            first_fixing = valuation_dt
            last_fixing = first_fixing + relativedelta(months=3 * (n_periods - 1))
            first_payment = first_fixing + relativedelta(months=3) + lag
            last_payment = first_fixing + relativedelta(months=3 * n_periods) + lag
            irs_id = 3000 + cp_index
            irs_rows.append(
                {
                    "trade_id": irs_id,
                    "notional": rules["irs"]["notional_mxn"],
                    "currency": "MXN",
                    "floating_rate": curve_rf,
                    "K": rules["irs"]["fixed_rate_by_tenor"][tenor],
                    "payer/receiver": direction,
                    "first_fixing_date": first_fixing.strftime(config.date_format),
                    "last_fixing_date": last_fixing.strftime(config.date_format),
                    "first_payment_date": first_payment.strftime(config.date_format),
                    "last_payment_date": last_payment.strftime(config.date_format),
                    "payments_frequency": "quarterly",
                    "maturity": last_payment.strftime(config.date_format),
                }
            )
            _ledger(irs_id, "IRS", naid, vm_agreement)

        if equity_rf and equity_rf in survivors:
            s0 = s0_by_rf[equity_rf]
            for leg in rules["options"]["legs"]:
                option_id = 4000 + option_index
                option_index += 1
                maturity = valuation_dt + relativedelta(years=int(leg["tenor_years"]))
                option_rows.append(
                    {
                        "trade_id": option_id,
                        "notional": max(round(rules["options"]["target_position_mxn"] / s0), 1),
                        "currency": "MXN",
                        "underlying": equity_rf,
                        "K": round(leg["moneyness"] * s0, 2),
                        "put/call": leg["type"],
                        "long/short": leg["long_short"],
                        "maturity": maturity.strftime(config.date_format),
                    }
                )
                _ledger(option_id, "EQ_EUR_OPT", naid, vm_agreement)

        for coupon, maturity, spread_bp in cp.get("bonds", []):
            bond_rows.append(
                {
                    "trade_id": bond_id,
                    "notional": rules["bonds"]["default_face"],
                    "currency": "MXN",
                    "coupon": coupon,
                    "spread": spread_bp / 10000.0,
                    "payments_frequency": "semi-annual",
                    "maturity": maturity,
                    "long/short": "long",
                    "issuer_name": cp["issuer"],
                }
            )
            _ledger(bond_id, "BOND_FIXED", naid, vm_agreement)
            bond_id += 1

        cp_dir = book_root / "portfolio_data" / "counterparties" / str(naid)
        cp_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([{"netting_agreement_id": naid, "settlement_currency": "MXN"}]).to_csv(
            cp_dir / "counterparty_properties.csv", index=False
        )
        if cp.get("vm"):
            pd.DataFrame([extra["vm_terms"]]).to_csv(cp_dir / "VM_1_terms.csv", index=False)

    pd.DataFrame(irs_rows).to_csv(
        book_root / "portfolio_data" / "desks" / "IR" / "IRS.csv", index=False
    )
    pd.DataFrame(option_rows).to_csv(
        book_root / "portfolio_data" / "desks" / "EQ" / "EQ_EUROPEAN_OPTIONS.csv", index=False
    )
    pd.DataFrame(bond_rows).to_csv(
        book_root / "portfolio_data" / "desks" / "DEBT" / "BONDS.csv", index=False
    )
    ledger = pd.DataFrame(ledger_rows)
    ledger.to_csv(
        book_root / "portfolio_data" / "positions_keeping_system" / "master_ledger.csv",
        index=False,
    )

    # --- self-validation: name binding + ledger integrity (fails the build) --
    mapping = pd.read_csv(book_root / "RFs_attributes" / "All_RFs_Mapping.csv")
    simulated = mapping[mapping["simulated"] == "YES"]
    gbm_names = set(gbm_frame["name"])
    for _, rf_row in simulated.iterrows():
        source = gbm_names if rf_row["model"] == "GBM" else set(hw1f_frame["name"])
        assert rf_row["name"] in source, f"{rf_row['name']} lacks a calibration row"
        assert (
            rf_row["name"] in extra["calibration_parameters"][f"RFE_{rf_row['model']}_calibration"]
        ), f"{rf_row['name']} lacks a calibration_parameters entry"
        assert rf_row["name"] in correlation.index, f"{rf_row['name']} missing from correlation"
    desk_ids = set(
        pd.concat([pd.DataFrame(r) for r in (irs_rows, option_rows, bond_rows)])["trade_id"]
    )
    assert set(ledger["trade_id"]) == desk_ids, "ledger trade_ids != desk trade_ids"
    surface_names = {r["name"] for r in surface_rows}
    for opt in option_rows:
        assert opt["underlying"][:-6] + "_IMPLIED_VOLATILITY_SURFACE" in surface_names

    # --- Stage 5: S_rate_eff with the Mexican alpha (OQ-MKT-12c) ------------
    scale = pd.read_csv(scale_csv).iloc[0]
    j_per_mdp_mx, s_rate_eff_mx = rate_scale_from_beta(
        float(scale["beta_adopted_per_bn"]), float(scale["t_years"]), alpha_mx
    )
    out_scale_dir = config.paths.root / extra["rate_scale_output_dir"]
    out_scale_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "fuente": "literatura (recompute con alpha mexicana, OQ-MKT-12c)",
                "base_scale_csv": str(scale_csv.relative_to(config.paths.root)),
                "beta_adopted_per_bn": float(scale["beta_adopted_per_bn"]),
                "t_years": float(scale["t_years"]),
                "hw1f_alpha": alpha_mx,
                "j_per_mdp": j_per_mdp_mx,
                "s_rate_eff_mdp": s_rate_eff_mx,
                "s_rate_eff_engine_alpha_mdp": float(scale["s_rate_eff_mdp"]),
                "ratio_vs_engine_alpha": s_rate_eff_mx / float(scale["s_rate_eff_mdp"]),
            }
        ]
    ).to_csv(out_scale_dir / "scale.csv", index=False)
    logger.info(
        "S_rate_eff (alpha=%.4f): %.0f MDP-2025 (%.1f%% vs engine alpha %.2f)",
        alpha_mx,
        s_rate_eff_mx,
        100.0 * (s_rate_eff_mx / float(scale["s_rate_eff_mdp"]) - 1.0),
        float(scale["hw1f_alpha"]),
    )

    # --- report + manifest ---------------------------------------------------
    pd.DataFrame(report_rows).to_csv(book_root / "build_report.csv", index=False)
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)
    logger.info(
        "Mexican book built: %s\n  equities %d/%d survive, %d IRS, %d options, %d bonds, "
        "%d counterparties\n  manifest %s",
        book_root,
        len(survivors),
        len(extra["equities"]),
        len(irs_rows),
        len(option_rows),
        len(bond_rows),
        len(extra["counterparties"]),
        manifest_path,
    )
    print(f"Book: {book_root}")
    print(f"S_rate_eff_MX: {s_rate_eff_mx:,.0f} MDP-2025")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
