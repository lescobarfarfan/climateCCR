"""Book-EPE readout across the NGFS scenario run matrix (INT-23 seam).

Reads the pipelines/01 comparison CSVs named in ``configs/ngfs_shock.yaml``
(``readout`` block) and derives, per scenario x band config, the three deltas
the results chapter needs — all against the unshocked jump-off book EPE:

- ``transition_pct``  — scenario jump-off vs base jump-off (the pure
  transition-channel delta; identical across band configs by construction).
- ``combined_pct``    — scenario jump-on vs base jump-off (transition +
  physical jump).
- ``jump_within_pct`` — the scenario run's own jump-on vs jump-off (the
  physical band re-read under the shocked curve; compare INT-23's
  unshocked band).

DAPS_NAM reports the transition column only (jump-off comparison, never
combined — combining NGFS physical narratives with the HAZ jump would
double-count physical risk; see the OQ-INT-03 c channel-separation ruling).

    python pipelines/17_ngfs_epe_readout.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SHOCK_CONFIG = REPO_ROOT / "configs" / "ngfs_shock.yaml"

COMPARISON = "ee_pe_climate_shift.csv"


def book_epe(results_root: Path, run: str) -> tuple[float, float]:
    """(jump-off, jump-on) whole-book EPE for one pipelines/01 run."""
    from climateCCR.viz import epe_summary

    comparison = pd.read_csv(results_root / run / COMPARISON)
    book = epe_summary(comparison).set_index("netting_agreement_id").loc["BOOK"]
    return float(book["epe_baseline"]), float(book["epe_climate"])


def main() -> None:
    from climateCCR.infra import RunManifest, get_logger, load_config

    config = load_config(SHOCK_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.ngfs_epe_readout", log_dir=config.paths.logs)
    readout = config.extra["readout"]

    base_off, _ = book_epe(config.paths.results, readout["base_run"])
    rows = []
    for entry in readout["scenario_runs"]:
        off, on = book_epe(config.paths.results, entry["run"])
        physical_only = entry["scenario"] == "DAPS_NAM"
        rows.append(
            {
                "scenario": entry["scenario"],
                "band": entry["band"],
                "book_epe_base_off": base_off,
                "book_epe_scen_off": off,
                "transition_pct": 100.0 * (off - base_off) / base_off,
                "book_epe_scen_on": None if physical_only else on,
                "combined_pct": None if physical_only else 100.0 * (on - base_off) / base_off,
                "jump_within_pct": None if physical_only else 100.0 * (on - off) / off,
            }
        )
    summary = pd.DataFrame(rows)

    out_dir = config.paths.root / readout["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "book_epe_deltas.csv"
    summary.to_csv(out_csv, index=False)
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)
    logger.info("Wrote %s and manifest %s", out_csv, manifest_path)
    print(summary.to_string(index=False, float_format=lambda v: f"{v:,.2f}"))
    print(f"\nReadout: {out_csv}\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
