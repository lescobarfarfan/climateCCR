"""Book-EPE readout across the NGFS scenario run matrix (INT-23 seam).

Reads the pipelines/01 comparison CSVs named in the readout config (the
``readout`` block of ``configs/ngfs_shock.yaml`` — nivel — or of the
trayectoria / fase sibling configs) and derives, per scenario x band config,
the three deltas the results chapter needs — all against the unshocked
jump-off book EPE:

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

Two artifacts per readout: ``book_epe_deltas.csv`` — the time-averaged book
EPE per row, the INT-23 metric — and ``book_profile_deltas.csv`` — the same
three deltas per reporting pillar (whole-book EE summed over the netting sets;
``pillar_index`` 0 = the 0D valuation date). Under the fase flavor
(``readout.flavor: fase``, OQ-INT-12 c) the 0D pillar is zero-delta by
construction — the INT-33 t=0 pin — so the readout asserts it per NAID and
fails loudly otherwise; per-pillar fase-vs-nivel comparisons start at the
first post-0D pillar.

    python pipelines/17_ngfs_epe_readout.py [--config configs/ngfs_shock_trayectoria.yaml]
    python pipelines/17_ngfs_epe_readout.py --config configs/ngfs_scheduled.yaml   # fase
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SHOCK_CONFIG = REPO_ROOT / "configs" / "ngfs_shock.yaml"

COMPARISON = "ee_pe_climate_shift.csv"
EE_OFF = "uncollateralized_ee_baseline"
EE_ON = "uncollateralized_ee_climate"


def book_epe(results_root: Path, run: str) -> tuple[float, float]:
    """(jump-off, jump-on) whole-book EPE for one pipelines/01 run."""
    from climateCCR.viz import epe_summary

    comparison = pd.read_csv(results_root / run / COMPARISON)
    book = epe_summary(comparison).set_index("netting_agreement_id").loc["BOOK"]
    return float(book["epe_baseline"]), float(book["epe_climate"])


def book_profile(results_root: Path, run: str) -> pd.DataFrame:
    """Whole-book EE per reporting pillar (jump-off, jump-on) for one pipelines/01 run."""
    comparison = pd.read_csv(results_root / run / COMPARISON)
    comparison["default_times"] = pd.to_datetime(comparison["default_times"])
    grouped = comparison.groupby("default_times", sort=True)
    return pd.DataFrame({"book_ee_off": grouped[EE_OFF].sum(), "book_ee_on": grouped[EE_ON].sum()})


def assert_fase_pin(results_root: Path, base_run: str, run: str) -> None:
    """The fase 0D pillar must equal the base run's per NAID exactly (INT-33 t=0 pin)."""

    def first_pillar(name: str) -> pd.Series:
        frame = pd.read_csv(results_root / name / COMPARISON)
        dates = pd.to_datetime(frame["default_times"])
        rows = frame[dates == dates.min()]
        return rows.set_index("netting_agreement_id")[EE_OFF].sort_index()

    base, scen = first_pillar(base_run), first_pillar(run)
    if not (base.index.equals(scen.index) and np.array_equal(base.to_numpy(), scen.to_numpy())):
        raise ValueError(
            f"fase 0D delta != 0 for {run} vs {base_run} — a bug signal, not a result "
            "(INT-33 t=0 pin: the valuation-date book is the observed market in every flavor)"
        )


def _pct(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    """100 * numerator / denominator, NaN where the book carries no exposure."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(denominator != 0.0, 100.0 * numerator / denominator, np.nan)


def profile_deltas(base: pd.DataFrame, scen: pd.DataFrame, physical_only: bool) -> pd.DataFrame:
    """Per-pillar transition / combined / jump-within deltas (%) of one run vs the base run."""
    if not base.index.equals(scen.index):
        raise ValueError("scenario run's reporting grid differs from the base run's")
    b = base["book_ee_off"].to_numpy(dtype=float)
    off = scen["book_ee_off"].to_numpy(dtype=float)
    on = scen["book_ee_on"].to_numpy(dtype=float)
    return pd.DataFrame(
        {
            "default_times": scen.index.strftime("%Y-%m-%d"),
            "pillar_index": np.arange(len(scen)),
            "book_ee_base_off": b,
            "book_ee_scen_off": off,
            "transition_pct": _pct(off - b, b),
            "book_ee_scen_on": np.nan if physical_only else on,
            "combined_pct": np.nan if physical_only else _pct(on - b, b),
            "jump_within_pct": np.nan if physical_only else _pct(on - off, off),
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--config",
        type=Path,
        default=SHOCK_CONFIG,
        help="config carrying the readout block (default: configs/ngfs_shock.yaml)",
    )
    args = parser.parse_args()

    from climateCCR.infra import RunManifest, get_logger, load_config

    config = load_config(args.config)
    config.paths.ensure()
    logger = get_logger("climateCCR.ngfs_epe_readout", log_dir=config.paths.logs)
    readout = config.extra["readout"]
    flavor = str(readout.get("flavor", "nivel"))
    results = config.paths.results

    base_off, _ = book_epe(results, readout["base_run"])
    base_profile = book_profile(results, readout["base_run"])
    rows = []
    pillars = []
    for entry in readout["scenario_runs"]:
        if flavor == "fase":
            assert_fase_pin(results, readout["base_run"], entry["run"])
        off, on = book_epe(results, entry["run"])
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
        pillars.append(
            profile_deltas(base_profile, book_profile(results, entry["run"]), physical_only).assign(
                scenario=entry["scenario"], band=entry["band"]
            )
        )
    summary = pd.DataFrame(rows)
    profiles = pd.concat(pillars, ignore_index=True)
    leading = ["scenario", "band"]
    profiles = profiles[leading + [c for c in profiles.columns if c not in leading]]

    out_dir = config.paths.root / readout["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "book_epe_deltas.csv"
    summary.to_csv(out_csv, index=False)
    profile_csv = out_dir / "book_profile_deltas.csv"
    profiles.to_csv(profile_csv, index=False)
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)
    logger.info("Wrote %s, %s and manifest %s", out_csv, profile_csv, manifest_path)
    print(summary.to_string(index=False, float_format=lambda v: f"{v:,.2f}"))
    print(f"\nReadout ({flavor}): {out_csv}\nPer-pillar: {profile_csv}\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
