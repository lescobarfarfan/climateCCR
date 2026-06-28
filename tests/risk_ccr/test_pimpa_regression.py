"""PIMPA EE/PE regression test — locks the engine's baseline before any refactor.

Asserts the migrated `risk.ccr` engine reproduces the saved EE/PE profiles
bit-for-bit (within float tolerance) on the prototype fixture portfolio. This is
the safety net that protects the Step-2 decomposition and the YAML/paths rewiring
(CCR-MIG-03, GEN-11). Regenerate the baseline with:

    python -m tests.risk_ccr.pimpa_baseline
"""
import numpy as np
import pandas as pd
import pytest

from pimpa_baseline import BASELINE_CSV, run_all

VALUE_COLS = [
    "uncollateralized_ee",
    "uncollateralized_pe_0.99",
    "collateralized_ee",
    "collateralized_pe_0.99",
]


@pytest.mark.integration
def test_pimpa_ee_pe_matches_baseline():
    got = run_all()
    expected = pd.read_csv(BASELINE_CSV)

    # Same shape and columns.
    assert list(got.columns) == list(expected.columns)
    assert got.shape == expected.shape

    # Same counterparties and time grid (dates compared as strings).
    np.testing.assert_array_equal(
        got["netting_agreement_id"].to_numpy(),
        expected["netting_agreement_id"].to_numpy(),
    )
    np.testing.assert_array_equal(
        got["default_times"].astype(str).to_numpy(),
        expected["default_times"].astype(str).to_numpy(),
    )

    # EE/PE values match (NaN where a counterparty has no collateral agreement).
    for col in VALUE_COLS:
        np.testing.assert_allclose(
            got[col].to_numpy(dtype=float),
            expected[col].to_numpy(dtype=float),
            rtol=1e-9,
            atol=1e-6,
            equal_nan=True,
            err_msg=f"EE/PE mismatch in column {col!r}",
        )
