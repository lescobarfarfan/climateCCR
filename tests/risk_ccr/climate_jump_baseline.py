"""Deterministic reconstructor for the climate-jump EE/PE baseline (DC-CCR-SIM-2).

The jump-off run IS the golden PIMPA baseline (``ee_pe_baseline.csv``, untouched
— the overlay draws from its own seed substream, so switching it on leaves every
diffusion draw bit-for-bit identical, INT-09). This module locks the jump-ON
counterpart: same engine, same seed 233423 / 10000 paths / valuation date, plus
the fixture climate-jump configuration below (GEN-04/11).

Fixture configuration (OQ-INT-03 provisional, 2026-07-02): homogeneous Poisson
arrivals shared across targets; every HW1F discount curve takes a fixed +50 bp
short-rate mark and every GBM share a fixed -5% log-return mark per event.
Deterministic marks are auditable scaffolding, not a model — the real impact
distribution is HAZ's to estimate (OQ-INT-07, DC-XWALK-4); the lognormal demo
lives in ``pipelines/01_climate_jump_demo.py``. Fixture values are arbitrary [eng].

    python tests/risk_ccr/climate_jump_baseline.py   # regenerate ee_pe_jump_baseline.csv
"""

from __future__ import annotations

import pandas as pd
from pimpa_baseline import FIXTURE, REPO_ROOT, run_all

JUMP_BASELINE_CSV = FIXTURE / "baselines" / "ee_pe_jump_baseline.csv"

FIXTURE_INTENSITY = 0.5  # events per year
FIXTURE_RATE_MARK = 0.0050  # +50 bp on the short rate, per event
FIXTURE_EQUITY_MARK = -0.05  # -5% log-return (~-4.9% price), per event


def fixture_jump_process():
    """Build the locked fixture jump configuration (both targets, shared events)."""
    from climateCCR.processes.jumps import ClimateJumpProcess, DeterministicMark

    rate_targets = {
        name: DeterministicMark(FIXTURE_RATE_MARK)
        for name in ("EUR_ZERO_YIELD_CURVE", "GBP_ZERO_YIELD_CURVE", "USD_ZERO_YIELD_CURVE")
    }
    equity_targets = {
        name: DeterministicMark(FIXTURE_EQUITY_MARK)
        for name in (
            "CREDIT_SUISSE_SHARE",
            "CREDIT_SUISSE_PREFERRED_SHARE",
            "UBS_SHARE",
            "JULIUS_BAER_SHARE",
        )
    }
    return ClimateJumpProcess(FIXTURE_INTENSITY, {**rate_targets, **equity_targets})


def run_all_with_jumps() -> pd.DataFrame:
    """Jump-on counterpart of ``pimpa_baseline.run_all`` (same seed, paths, date)."""
    return run_all(climate_jumps=fixture_jump_process())


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(REPO_ROOT / "src"))
    result = run_all_with_jumps()
    JUMP_BASELINE_CSV.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(JUMP_BASELINE_CSV, index=False)
    print(f"Wrote {JUMP_BASELINE_CSV} ({result.shape[0]} rows x {result.shape[1]} cols)")
