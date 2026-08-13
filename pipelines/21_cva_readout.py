"""CVA readout — unilateral CVA per NAID + BOOK over the stored EE runs (OQ-CCR-04).

Consumes the DC-CCR-RISK-3 comparison frames of the band and NGFS runs, the
CLIMACRED annual PD families (DC-MKT-NGFS-2), and each leg's own pricing curve;
emits per-leg CVA levels (LGD 0.45/0.60/0.75), the scenario-delta channel
decomposition (exposure / credit / interaction — the INT-23/INT-31 wrong-way
readout), and the credit-triangle cross-check of the cebur discount margins
against the CLIMACRED country PD.

    python pipelines/21_cva_readout.py [--config configs/cva.yaml] [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "cva.yaml"
COMPARISON = "ee_pe_climate_shift.csv"
DAYS_PER_YEAR = 365.25  # the reporting-grid convention (viz.epe_summary)


def naid_sector_map(
    book_extra: dict, shock_extra: dict, overrides: dict[int, str] | None = None
) -> dict[int, str]:
    """NAID -> GEM-E3 sector via the existing crosswalks; hard-fails on gaps.

    ``overrides`` (cva.yaml ``sector_overrides``) covers book names outside the
    NGFS shock crosswalks — a PD-sector assignment only, never a shock scope.
    """
    by_rf = shock_extra["equity_leg"]["sectors"]
    by_issuer = shock_extra["bond_leg"]["sectors"]
    overrides = {int(k): v for k, v in (overrides or {}).items()}
    mapping: dict[int, str] = {}
    missing = []
    for row in book_extra["counterparties"]:
        naid = int(row["naid"])
        sector = (
            by_rf.get(row.get("equity_rf")) or by_issuer.get(row["issuer"]) or overrides.get(naid)
        )
        if sector is None:
            missing.append(naid)
        else:
            mapping[naid] = sector
    if missing:
        raise ValueError(f"NAIDs without a GEM-E3 sector in the crosswalks: {missing}")
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    args = parser.parse_args()

    import numpy as np
    import pandas as pd
    from climateCCR.calibration.financial.market_data_builder import MarketDataBuilder
    from climateCCR.data.scenarios.ngfs import annual_series, load_short_term
    from climateCCR.infra import RunManifest, get_logger, load_config
    from climateCCR.risk.ccr.xva import (
        cva_decomposition,
        cva_unilateral,
        implied_pd_from_spread,
        survival_from_annual_pd,
    )

    config = load_config(args.config)
    config.paths.ensure()
    logger = get_logger("climateCCR.cva_readout", log_dir=config.paths.logs)
    root = config.paths.root
    out_dir = root / config.extra["out_dir"]
    summary_csv = out_dir / "cva_summary.csv"
    if summary_csv.exists() and not args.forzar:
        print(f"{summary_csv} existe; usa --forzar para recomputar.")
        return

    book = load_config(root / config.extra["book_config"])
    shock = load_config(root / config.extra["shock_config"])
    sectors = naid_sector_map(book.extra, shock.extra, config.extra.get("sector_overrides"))
    t0 = datetime.strptime(book.extra["valuation_date"], "%Y-%m-%d")

    lgds: dict[str, float] = config.extra["lgd"]
    lgd_headline = float(lgds["headline"])

    # ---- PD paths: country baseline + per-sector scenario adjustments ---------
    frame = load_short_term(root / config.extra["ngfs_data_dir"])
    reference = config.extra["pd_reference_scenario"]

    def pd_path(sector: str, scenario: str | None) -> tuple[np.ndarray, np.ndarray]:
        """(segment_starts_in_years_from_t0, annual PD pp) for one sector/leg."""
        base = annual_series(frame, reference, variable=f"baseline_pd|{sector}")
        pd_pp = base["value"].to_numpy(dtype=float)
        years = base["time"].astype(int).to_numpy()  # 'Year' rows sit at Y + 0.5
        if scenario is not None:
            adj = annual_series(frame, scenario, variable=f"pd_adjustment|{sector}")
            merged = base.merge(adj, on="time", how="left", suffixes=("", "_adj"))
            if merged["value_adj"].isna().any():
                missing = merged.loc[merged["value_adj"].isna(), "time"].tolist()
                raise ValueError(f"pd_adjustment|{sector} missing for times {missing}")
            pd_pp = pd_pp + merged["value_adj"].to_numpy(dtype=float)
        starts = np.array([(datetime(int(y), 1, 1) - t0).days / DAYS_PER_YEAR for y in years])
        return starts, np.clip(pd_pp, 0.0, None)

    # ---- discount factors per curve key on each NAID's reporting grid ---------
    builder = MarketDataBuilder()
    curves = {
        key: builder.load_row_with_one_curve(
            pd.read_csv(root / path, index_col=0).loc["MXN_ZERO_YIELD_CURVE"]
        )["rate_curve"]
        for key, path in config.extra["discount_curves"].items()
    }

    def leg_frames(run: str) -> pd.DataFrame:
        csv = config.paths.results / run / COMPARISON
        if not csv.exists():
            raise FileNotFoundError(f"{csv} — corre pipelines/01 para esa pata primero")
        out = pd.read_csv(csv)
        out["default_times"] = pd.to_datetime(out["default_times"])
        return out

    # ---- per-leg CVA levels ----------------------------------------------------
    survival_cache: dict[tuple[str, str | None], dict[int, np.ndarray]] = {}
    profiles: dict[str, dict[int, np.ndarray]] = {}  # leg -> naid -> discounted EE
    summary_rows = []
    for leg in config.extra["legs"]:
        name, column = leg["name"], leg["column"]
        scenario = None if leg["pd"] == "bau" else leg["pd"]
        curve = curves[leg["curve"]]
        comparison = leg_frames(leg["run"])
        discounted: dict[int, np.ndarray] = {}
        survivals = survival_cache.setdefault((leg["pd"], scenario), {})
        for naid, block in comparison.groupby("netting_agreement_id"):
            block = block.sort_values("default_times")
            grid = (block["default_times"] - pd.Timestamp(t0)).dt.days.to_numpy() / DAYS_PER_YEAR
            if grid[0] != 0.0:
                raise ValueError(f"run {leg['run']} NAID {naid}: grid does not start at t0")
            ee = block[f"uncollateralized_ee_{column}"].to_numpy(dtype=float)
            df = curve.get_interpolated_discount_factor(grid)
            df[0] = 1.0  # exp(-0*r) up to float noise
            discounted[int(naid)] = ee * df
            if int(naid) not in survivals:
                starts, pd_pp = pd_path(sectors[int(naid)], scenario)
                survivals[int(naid)] = survival_from_annual_pd(starts, pd_pp, grid)
            row = {"leg": name, "netting_agreement_id": int(naid), "sector": sectors[int(naid)]}
            for label, lgd in lgds.items():
                row[f"cva_lgd_{label}"] = cva_unilateral(
                    ee, df, survivals[int(naid)], lgd=float(lgd)
                )
            summary_rows.append(row)
        profiles[name] = discounted
        book_row = {"leg": name, "netting_agreement_id": "BOOK", "sector": ""}
        for label in lgds:
            book_row[f"cva_lgd_{label}"] = sum(
                r[f"cva_lgd_{label}"] for r in summary_rows if r["leg"] == name
            )
        summary_rows.append(book_row)
    summary = pd.DataFrame(summary_rows)

    # ---- scenario-delta decompositions vs the base leg -------------------------
    ones_cache: dict[int, np.ndarray] = {}
    base_surv = survival_cache[("bau", None)]
    decomposition_rows = []
    for entry in config.extra["decomposition"]:
        leg = next(x for x in config.extra["legs"] if x["name"] == entry["leg"])
        scenario = None if leg["pd"] == "bau" else leg["pd"]
        scen_surv = survival_cache[(leg["pd"], scenario)]
        totals: dict[str, float] = {}
        for naid, disc_scen in profiles[entry["leg"]].items():
            disc_base = profiles["base"][naid]
            ones = ones_cache.setdefault(disc_base.size, np.ones(disc_base.size))
            parts = cva_decomposition(
                disc_base, disc_scen, base_surv[naid], scen_surv[naid], ones, lgd=lgd_headline
            )
            decomposition_rows.append(
                {"label": entry["label"], "netting_agreement_id": naid, **parts}
            )
            for key, value in parts.items():
                totals[key] = totals.get(key, 0.0) + value
        decomposition_rows.append(
            {"label": entry["label"], "netting_agreement_id": "BOOK", **totals}
        )
    decomposition = pd.DataFrame(decomposition_rows)

    # ---- credit-triangle cross-check on the cebur discount margins -------------
    recovery = float(config.extra["recovery_crosscheck"])
    bonds = pd.read_csv(
        root / book.extra["book_root"] / "portfolio_data" / "desks" / "DEBT" / "BONDS.csv"
    )
    issuer_naid = {row["issuer"]: int(row["naid"]) for row in book.extra["counterparties"]}
    by_issuer = shock.extra["bond_leg"]["sectors"]
    country_pd = annual_series(frame, reference, variable="baseline_pd|Crude Oil")
    pd_t0 = float(country_pd.loc[country_pd["time"].astype(int) == t0.year, "value"].iloc[0])
    crosscheck_rows = []
    for _, bond in bonds.iterrows():
        hazard, pd_1y = implied_pd_from_spread(float(bond["spread"]), recovery=recovery)
        crosscheck_rows.append(
            {
                "trade_id": bond["trade_id"],
                "issuer": bond["issuer_name"],
                "netting_agreement_id": issuer_naid.get(bond["issuer_name"]),
                "sector": by_issuer.get(bond["issuer_name"]),
                "spread_bp": 1e4 * float(bond["spread"]),
                "implied_hazard": hazard,
                "implied_pd_1y_pct": 100.0 * pd_1y,
                "climacred_country_pd_pct": pd_t0,
                "ratio_implied_over_climacred": 100.0 * pd_1y / pd_t0,
            }
        )
    crosscheck = pd.DataFrame(crosscheck_rows)

    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(summary_csv, index=False)
    decomposition.to_csv(out_dir / "cva_decomposition.csv", index=False)
    crosscheck.to_csv(out_dir / "pd_crosscheck.csv", index=False)
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=root)
    manifest_path = manifest.write(config.paths.manifests)
    logger.info("Wrote %s (+2) and manifest %s", summary_csv, manifest_path)

    book_view = summary[summary["netting_agreement_id"] == "BOOK"].set_index("leg")
    print("BOOK CVA (MXN, LGD headline):")
    print(book_view[["cva_lgd_headline"]].to_string(float_format=lambda v: f"{v:,.2f}"))
    print("\nBOOK decomposition (MXN, LGD headline):")
    book_decomp = decomposition[decomposition["netting_agreement_id"] == "BOOK"].set_index("label")
    cols = [
        "cva_base",
        "cva_scenario",
        "cva_delta",
        "exposure_channel",
        "credit_channel",
        "interaction",
    ]
    print(book_decomp[cols].to_string(float_format=lambda v: f"{v:,.2f}"))
    print(f"\nSalida: {out_dir}\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
