"""Deterministic reconstructor for the PIMPA EE/PE regression baseline (GEN-04).

Runs the migrated `risk.ccr` engine on the prototype fixture portfolio and returns
the per-counterparty EE/PE profiles. Used by the regression test to compare against
the locked baseline, and runnable as a script to regenerate that baseline:

    python tests/risk_ccr/pimpa_baseline.py          # regenerate ee_pe_baseline.csv

The baseline is locked at seed 233423 / n_paths 10000 (from the fixture
global_parameters) and valuation date TODAY_DATE below (CCR-MIG-03).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "pimpa"
BASELINE_CSV = FIXTURE / "baselines" / "ee_pe_baseline.csv"
CONFIG = REPO_ROOT / "configs" / "pimpa_fixture.yaml"

# Valuation as-of date — the latest Historical_Fixings date in the fixture; not
# recorded in the original PIMPA, fixed here for reproducibility (confirmed 2026-06-28).
TODAY_DATE = "2020-01-01"


def _load_global_parameters() -> dict:
    # Parameters come from a YAML Config (GEN-08); data paths anchor to the fixture
    # tree via ProjectPaths, not a CWD-relative GLOBAL_DATA_PATH (CCR-ARCH-04).
    from climateCCR.infra import load_config
    from climateCCR.risk.ccr.config import build_global_parameters

    config = load_config(CONFIG)
    return build_global_parameters(config, data_root=FIXTURE)


def run_all(climate_jumps=None) -> pd.DataFrame:
    """Run the EE/PE engine for every counterparty in the fixture ledger.

    ``climate_jumps`` optionally injects a
    :class:`~climateCCR.processes.jumps.ClimateJumpProcess` (DC-CCR-SIM-2); the
    default ``None`` is the jump-off golden baseline (CCR-MIG-03), which the jump
    overlay leaves bit-for-bit unchanged. The jump-on fixture configuration lives
    in ``climate_jump_baseline.py``.
    """
    # Imports are local so `conftest` can put `src/` on the path first.
    from climateCCR.risk.ccr.evaluators.ccr_valuation_session import CCR_Valuation_Session
    from climateCCR.risk.ccr.trade_models.portfolio import Portfolio

    gp = _load_global_parameters()
    if climate_jumps is not None:
        gp["climate_jumps"] = climate_jumps
    ledger = pd.read_csv(
        FIXTURE / "portfolio_data" / "positions_keeping_system" / "master_ledger.csv"
    )
    frames = []
    for naid in sorted(ledger["netting_agreement_id"].unique()):
        portfolio = Portfolio(naid)
        portfolio.load(gp)
        session = CCR_Valuation_Session(portfolio)
        session.run(TODAY_DATE, gp)
        exposures = session.get_exposures().copy()
        exposures.insert(0, "netting_agreement_id", naid)
        frames.append(exposures)
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(REPO_ROOT / "src"))
    result = run_all()
    BASELINE_CSV.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(BASELINE_CSV, index=False)
    print(f"Wrote {BASELINE_CSV} ({result.shape[0]} rows x {result.shape[1]} cols)")
