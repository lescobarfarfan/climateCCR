"""Build per-scenario Mexican book overlays with NGFS-shocked curves.

For each scenario in ``configs/ngfs_shock.yaml``: derive the two-anchor peak
deltas from the tidy NGFS data (short = EIRIN policy rate vs Baseline, long =
CLIMACRED Mexican sovereign adjustment incl. policy), shift the zero pillars
of the book's HW1F curve CSVs (RFE + pricing) via
``scenario_shock.shock_zero_pillars``, and write a complete copy of the book
data-root under ``data/ccr_book_mx_ngfs/<scenario_lower>/`` differing only in
those CSVs. A summary of anchors + shocked pillars lands in
``results/ngfs_shock_curves/`` with a run manifest.

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

    summaries = []
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
        built += 1

    if built:
        summary_dir.mkdir(parents=True, exist_ok=True)
        summary = pd.concat(summaries, ignore_index=True)
        summary_csv = summary_dir / "shock_summary.csv"
        summary.to_csv(summary_csv, index=False)
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
