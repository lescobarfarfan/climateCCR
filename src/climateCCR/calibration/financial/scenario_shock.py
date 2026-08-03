"""Two-anchor curve shock for NGFS scenario deltas (MKT-NGFS-01/02).

The shock lands on the *current* market zero curve (never a level
replacement): each pillar moves by a tenor-interpolated delta anchored at the
short end by the policy-rate delta and at the long end by the sovereign-yield
delta, both in percentage points (converted to decimals here). Flat before the
short anchor and beyond the long anchor, linear in tenor between — the
Fed-CSA-style translation of scenario deltas onto current conditions
[FedCSA2024] [Vermeulen2021].
"""

from __future__ import annotations

import numpy as np


def shock_zero_pillars(
    tenors_years: np.ndarray,
    zero_rates: np.ndarray,
    *,
    short_pp: float,
    long_pp: float,
    short_tenor: float = 0.0833,
    long_tenor: float = 10.0,
) -> np.ndarray:
    """Shift zero-curve pillars by the two-anchor scenario delta.

    Args:
        tenors_years: Pillar tenors in years (ascending).
        zero_rates: Zero rates at the pillars, in decimals.
        short_pp: Short-anchor delta in percentage points (policy rate).
        long_pp: Long-anchor delta in percentage points (sovereign yield).
        short_tenor: Tenor (years) at and below which the short anchor applies.
        long_tenor: Tenor (years) at and beyond which the long anchor applies.

    Returns:
        The shocked zero rates, same shape and units as ``zero_rates``.
    """
    tenors = np.asarray(tenors_years, dtype=float)
    zeros = np.asarray(zero_rates, dtype=float)
    if tenors.shape != zeros.shape:
        raise ValueError(f"Shape mismatch: tenors {tenors.shape} vs zeros {zeros.shape}")
    if not (short_tenor < long_tenor):
        raise ValueError(f"short_tenor ({short_tenor}) must be below long_tenor ({long_tenor})")
    delta_pp = np.interp(tenors, [short_tenor, long_tenor], [short_pp, long_pp])
    return zeros + delta_pp / 100.0
