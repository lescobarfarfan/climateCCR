"""Climate-jump EE/PE regression test (DC-CCR-SIM-2, GEN-04/11).

Two locked properties of the jump channel on the fixture portfolio:

1. jump-ON reproduces its saved baseline (``ee_pe_jump_baseline.csv``) — the
   documented deterministic shift is stable across refactors;
2. jump-ON actually differs from the jump-OFF golden baseline — the channel is
   live, not silently a no-op.

The jump-OFF ≡ golden-baseline property is already locked by
``test_pimpa_regression.py`` (the overlay never touches the diffusion stream).
Regenerate with:

    python tests/risk_ccr/climate_jump_baseline.py
"""

import numpy as np
import pandas as pd
import pytest
from climate_jump_baseline import JUMP_BASELINE_CSV, run_all_with_jumps
from pimpa_baseline import BASELINE_CSV

VALUE_COLS = [
    "uncollateralized_ee",
    "uncollateralized_pe_0.99",
    "collateralized_ee",
    "collateralized_pe_0.99",
]


@pytest.mark.integration
def test_climate_jump_ee_pe_matches_locked_baseline():
    got = run_all_with_jumps()
    expected = pd.read_csv(JUMP_BASELINE_CSV)

    assert list(got.columns) == list(expected.columns)
    assert got.shape == expected.shape
    np.testing.assert_array_equal(
        got["netting_agreement_id"].to_numpy(),
        expected["netting_agreement_id"].to_numpy(),
    )
    np.testing.assert_array_equal(
        got["default_times"].astype(str).to_numpy(),
        expected["default_times"].astype(str).to_numpy(),
    )
    for col in VALUE_COLS:
        np.testing.assert_allclose(
            got[col].to_numpy(dtype=float),
            expected[col].to_numpy(dtype=float),
            rtol=1e-9,
            atol=1e-6,
            equal_nan=True,
            err_msg=f"jump-on EE/PE mismatch in column {col!r}",
        )


@pytest.mark.integration
def test_climate_jump_shifts_the_golden_baseline():
    jump_on = pd.read_csv(JUMP_BASELINE_CSV)
    jump_off = pd.read_csv(BASELINE_CSV)
    ee_shift = (
        jump_on["uncollateralized_ee"].to_numpy() - jump_off["uncollateralized_ee"].to_numpy()
    )
    assert np.abs(ee_shift).max() > 0.0, "climate jump channel produced no EE shift"
