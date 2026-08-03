"""Build per-scenario Mexican book overlays with NGFS-shocked curves.

For each scenario in ``configs/ngfs_shock.yaml``: derive the two-anchor peak
deltas from the tidy NGFS data (short = EIRIN policy rate vs Baseline, long =
CLIMACRED Mexican sovereign adjustment incl. policy), shift the zero pillars
of the book's HW1F curve CSVs (RFE + pricing) via
``scenario_shock.shock_zero_pillars``, and write a complete copy of the book
data-root under ``data/ccr_book_mx_ngfs/<scenario_lower>/`` differing only in
the shocked CSVs. A summary of anchors + shocked pillars lands in
``results/ngfs_shock_curves/`` with a run manifest.

The equity/corporate leg (OQ-MKT-13 c) rides the same overlays when the
config carries ``equity_leg``/``bond_leg`` blocks: per name, the CLIMACRED
sector's signed-peak ``equity_relative_adjustment`` revalues S0 (spot file +
both GBM calibration CSVs, factor ``1 + peak/100``; drift/vol untouched), and
per issuer the signed-peak excl-policy ``corporate_bond_spread_adjustment``
adds to the cebur sobretasa (``spread + peak_pp/100``, floored at 0 — a
sobretasa below the sovereign curve is outside the static-spread pricer's
semantics; floors are logged and reported). Absent blocks = the curve-only
first build, bit for bit. Per-name applications land in
``sector_shock_summary.csv``.

Idempotent (GEN-05): existing overlays are skipped, rerun with ``--forzar``.

    python pipelines/16_ngfs_shock_curves.py [--forzar]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SHOCK_CONFIG = REPO_ROOT / "configs" / "ngfs_shock.yaml"


def shock_direct_input_csv(
    path: Path, curve_name: str, short_pp: float, long_pp: float, anchors: dict
) -> pd.DataFrame:
    """Rewrite one direct_input CSV in place with shocked rate_curve_V* pillars."""
    from climateCCR.calibration.financial.scenario_shock import shock_zero_pillars
    from climateCCR.utils.calendar_utils import translate_tenor_to_years

    table = pd.read_csv(path, index_col=0)
    if curve_name not in table.index:
        raise KeyError(f"{curve_name!r} not in {path}")
    row = table.loc[curve_name]
    value_cols = sorted(
        (c for c in table.columns if c.startswith("rate_curve_V")), key=lambda c: int(c[12:])
    )
    tenor_cols = [c.replace("_V", "_T") for c in value_cols]
    tenors = np.asarray([translate_tenor_to_years(row[c]) for c in tenor_cols])
    zeros = row[value_cols].to_numpy(dtype=float)
    shocked = shock_zero_pillars(
        tenors,
        zeros,
        short_pp=short_pp,
        long_pp=long_pp,
        short_tenor=anchors["short_tenor_years"],
        long_tenor=anchors["long_tenor_years"],
    )
    table.loc[curve_name, value_cols] = shocked
    table.to_csv(path)
    return pd.DataFrame(
        {
            "tenor": row[tenor_cols].to_numpy(),
            "tenor_years": tenors,
            "zero": zeros,
            "zero_shocked": shocked,
        }
    )


def sector_shocks(
    frame: pd.DataFrame, scenario: str, leg: dict, window: tuple[float, float]
) -> dict[str, tuple[float, float]]:
    """Per-name signed-peak shock for one leg: name -> (peak, peak_time), published units."""
    from climateCCR.data.scenarios import sector_peak

    family = leg["variable_family"]
    by_sector = {
        sector: sector_peak(frame, scenario, variable=f"{family}|{sector}", window=window)
        for sector in sorted(set(leg["sectors"].values()))
    }
    return {name: by_sector[sector] for name, sector in leg["sectors"].items()}


def shock_equity_csvs(overlay: Path, peaks_pct: dict[str, float], leg: dict) -> None:
    """Revalue S0 by (1 + peak%/100) in the spot file and both GBM calibration CSVs."""
    factors = {name: 1.0 + pct / 100.0 for name, pct in peaks_pct.items()}
    bad = {n: f for n, f in factors.items() if not np.isfinite(f) or f <= 0.0}
    if bad:
        raise ValueError(f"Non-positive/non-finite equity factors: {bad}")
    spot_path = overlay / leg["spot_file"]
    spot = pd.read_csv(spot_path)
    missing = set(factors) - set(spot["name"])
    if missing:
        raise KeyError(f"Equity names not in {spot_path}: {sorted(missing)}")
    spot["spot"] = spot["spot"] * spot["name"].map(factors).fillna(1.0)
    spot.to_csv(spot_path, index=False)
    reference = spot.set_index("name")["spot"]
    for rel in leg["gbm_files"]:
        path = overlay / rel
        table = pd.read_csv(path, index_col=0)
        missing = set(factors) - set(table.index)
        if missing:
            raise KeyError(f"Equity names not in {path}: {sorted(missing)}")
        scale = pd.Series(factors).reindex(table.index).fillna(1.0)
        table["initial_value"] = table["initial_value"] * scale
        drift = (table["initial_value"].reindex(reference.index) - reference).abs().max()
        if drift > 1e-9:
            raise AssertionError(f"spot vs initial_value drift {drift:.3e} in {path}")
        table.to_csv(path)


def shock_bond_spreads(overlay: Path, peaks_pp: dict[str, float], leg: dict) -> dict[str, int]:
    """Add peak_pp/100 to each issuer's cebur sobretasa, floored at 0; floors per issuer."""
    path = overlay / leg["bonds_file"]
    bonds = pd.read_csv(path)
    missing = set(peaks_pp) - set(bonds["issuer_name"])
    if missing:
        raise KeyError(f"Issuers not in {path}: {sorted(missing)}")
    delta = bonds["issuer_name"].map({k: v / 100.0 for k, v in peaks_pp.items()}).fillna(0.0)
    shocked = bonds["spread"] + delta
    floored = shocked < 0.0
    bonds["spread"] = shocked.clip(lower=0.0)
    bonds.to_csv(path, index=False)
    return bonds.loc[floored, "issuer_name"].value_counts().to_dict()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="rebuild overlays even if they exist"
    )
    args = parser.parse_args()

    from climateCCR.data.scenarios import anchor_peaks, load_short_term
    from climateCCR.infra import RunManifest, get_logger, load_config

    config = load_config(SHOCK_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.ngfs_shock_curves", log_dir=config.paths.logs)

    extra = config.extra
    frame = load_short_term(config.paths.root / extra["ngfs_dir"])
    book_root = config.paths.root / extra["book_root"]
    out_root = config.paths.root / extra["out_root"]
    summary_dir = config.paths.root / extra["summary_dir"]
    window = tuple(extra["window"])

    equity_leg = extra.get("equity_leg")
    bond_leg = extra.get("bond_leg")

    summaries = []
    sector_rows = []
    built = 0
    for scenario in extra["scenarios"]:
        overlay = out_root / scenario.lower()
        if overlay.exists() and not args.forzar:
            logger.info("Overlay exists, skipping (rerun with --forzar): %s", overlay)
            continue
        deltas = anchor_peaks(frame, scenario, region=extra["region"], window=window)
        logger.info(
            "%s: short anchor %+.3f pp (policy rate, %.2f), long anchor %+.3f pp "
            "(sovereign incl. policy, %.0f)",
            scenario,
            deltas.short_pp,
            deltas.short_peak_time,
            deltas.long_pp,
            deltas.long_peak_time,
        )
        if overlay.exists():
            shutil.rmtree(overlay)
        shutil.copytree(book_root, overlay)
        for rel in extra["hw1f_files"]:
            pillars = shock_direct_input_csv(
                overlay / rel,
                extra["curve_name"],
                deltas.short_pp,
                deltas.long_pp,
                extra["anchors"],
            )
        pillars.insert(0, "scenario", scenario)
        pillars["short_pp"] = deltas.short_pp
        pillars["long_pp"] = deltas.long_pp
        summaries.append(pillars)

        if equity_leg:
            eq_peaks = sector_shocks(frame, scenario, equity_leg, window)
            shock_equity_csvs(overlay, {n: p for n, (p, _) in eq_peaks.items()}, equity_leg)
            logger.info(
                "%s: equity leg — %d names revalued, peak range [%+.2f, %+.2f] %%",
                scenario,
                len(eq_peaks),
                min(p for p, _ in eq_peaks.values()),
                max(p for p, _ in eq_peaks.values()),
            )
            sector_rows += [
                {
                    "scenario": scenario,
                    "leg": "equity",
                    "name": name,
                    "sector": equity_leg["sectors"][name],
                    "peak_published": peak,
                    "peak_time": when,
                    "applied": 1.0 + peak / 100.0,
                    "floored_trades": 0,
                }
                for name, (peak, when) in eq_peaks.items()
            ]
        if bond_leg:
            bd_peaks = sector_shocks(frame, scenario, bond_leg, window)
            floors = shock_bond_spreads(overlay, {n: p for n, (p, _) in bd_peaks.items()}, bond_leg)
            if floors:
                logger.info("%s: bond leg — spread floors at 0 for %s", scenario, floors)
            logger.info(
                "%s: bond leg — %d issuers shocked, peak range [%+.2f, %+.2f] pp",
                scenario,
                len(bd_peaks),
                min(p for p, _ in bd_peaks.values()),
                max(p for p, _ in bd_peaks.values()),
            )
            sector_rows += [
                {
                    "scenario": scenario,
                    "leg": "bond",
                    "name": issuer,
                    "sector": bond_leg["sectors"][issuer],
                    "peak_published": peak,
                    "peak_time": when,
                    "applied": peak / 100.0,
                    "floored_trades": floors.get(issuer, 0),
                }
                for issuer, (peak, when) in bd_peaks.items()
            ]
        built += 1

    if built:
        summary_dir.mkdir(parents=True, exist_ok=True)
        summary = pd.concat(summaries, ignore_index=True)
        summary_csv = summary_dir / "shock_summary.csv"
        summary.to_csv(summary_csv, index=False)
        if sector_rows:
            sector_summary = pd.DataFrame(sector_rows)
            sector_summary.to_csv(summary_dir / "sector_shock_summary.csv", index=False)
        manifest = RunManifest.create(
            seed=config.seed, config=config, project_root=config.paths.root
        )
        manifest_path = manifest.write(config.paths.manifests)
        logger.info("Wrote %s and manifest %s", summary_csv, manifest_path)
        print(summary.to_string(index=False, float_format=lambda v: f"{v:.6f}"))
    print(f"Scenario overlays -> {out_root} ({built} built)")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
