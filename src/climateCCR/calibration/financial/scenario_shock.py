"""Two-anchor curve shock for NGFS scenario deltas (MKT-NGFS-01/02).

The shock lands on the *current* market zero curve (never a level
replacement): each pillar moves by a tenor-interpolated delta anchored at the
short end by the policy-rate delta and at the long end by the sovereign-yield
delta, both in percentage points (converted to decimals here). Flat before the
short anchor and beyond the long anchor, linear in tenor between — the
Fed-CSA-style translation of scenario deltas onto current conditions
[FedCSA2024] [Vermeulen2021].

Two flavors (INT-12):

- ``shock_zero_pillars`` — the fixed/nivel flavor: every pillar takes the
  anchors' single signed-peak delta (the stress-standard most-adverse point).
- ``shock_zero_pillars_trajectory`` — the trajectory flavor (OQ-MKT-13 a):
  every pillar absorbs the anchor *paths at its own maturity date* — tenor T
  reads the deltas at calendar time t0 + T, linear in time between published
  points and held constant beyond the last in-window observation (the
  hold-constant rule). The tenor blend between the anchors is unchanged, so
  flat paths reduce exactly to the fixed flavor.
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


def maturity_dated_deltas(
    tenors_years: np.ndarray,
    *,
    short_times: np.ndarray,
    short_pp_path: np.ndarray,
    long_times: np.ndarray,
    long_pp_path: np.ndarray,
    t0_decimal_year: float,
    window: tuple[float, float] = (2025.0, 2030.0),
) -> tuple[np.ndarray, np.ndarray]:
    """Per-pillar anchor deltas read off the paths at each pillar's maturity date.

    Pillar tenor T reads both anchor paths at calendar time ``t0 + T`` (decimal
    years, the NGFS time axis), linear in time between published points.
    Observations at or beyond ``window[1] + 1.0`` are discarded — the same
    ``[lo, hi + 1)`` convention the fixed flavor's peak scan uses — and
    ``np.interp``'s end clamping *is* the hold-constant rule: maturities beyond
    the last kept observation hold its value.

    Args:
        tenors_years: Pillar tenors in years (ascending).
        short_times: Published times of the short-anchor path (decimal years,
            strictly increasing).
        short_pp_path: Short-anchor deltas at ``short_times``, in pp.
        long_times: Published times of the long-anchor path.
        long_pp_path: Long-anchor deltas at ``long_times``, in pp.
        t0_decimal_year: The curve valuation date on the NGFS time axis.
        window: The scenario window ``(lo, hi)``; only ``hi`` binds here.

    Returns:
        ``(short_at_maturity, long_at_maturity)`` in pp, one value per pillar.
    """
    tenors = np.asarray(tenors_years, dtype=float)
    hi = window[1]

    def _clipped(times, values, label: str) -> tuple[np.ndarray, np.ndarray]:
        t = np.asarray(times, dtype=float)
        v = np.asarray(values, dtype=float)
        if t.ndim != 1 or t.shape != v.shape or t.size == 0:
            raise ValueError(f"{label} path must be two equal-length 1-D arrays, non-empty")
        if not np.all(np.diff(t) > 0):
            raise ValueError(f"{label} path times must be strictly increasing")
        keep = t < hi + 1.0
        if not keep.any():
            raise ValueError(f"No {label} path observations before {hi + 1.0}")
        return t[keep], v[keep]

    s_t, s_v = _clipped(short_times, short_pp_path, "short")
    l_t, l_v = _clipped(long_times, long_pp_path, "long")
    maturity_time = t0_decimal_year + tenors
    return np.interp(maturity_time, s_t, s_v), np.interp(maturity_time, l_t, l_v)


def shock_zero_pillars_trajectory(
    tenors_years: np.ndarray,
    zero_rates: np.ndarray,
    *,
    short_times: np.ndarray,
    short_pp_path: np.ndarray,
    long_times: np.ndarray,
    long_pp_path: np.ndarray,
    t0_decimal_year: float,
    short_tenor: float = 0.0833,
    long_tenor: float = 10.0,
    window: tuple[float, float] = (2025.0, 2030.0),
) -> np.ndarray:
    """Shift zero-curve pillars by the maturity-dated two-anchor deltas.

    The trajectory flavor of ``shock_zero_pillars``: identical tenor blend
    (flat outside the anchors, linear between), but each pillar's anchor
    deltas come from ``maturity_dated_deltas`` — the paths evaluated at that
    pillar's own maturity date — instead of the single signed peak. Paths that
    are flat over the window therefore reduce exactly to the fixed flavor.

    Args/returns: as ``shock_zero_pillars`` + ``maturity_dated_deltas``.
    """
    tenors = np.asarray(tenors_years, dtype=float)
    zeros = np.asarray(zero_rates, dtype=float)
    if tenors.shape != zeros.shape:
        raise ValueError(f"Shape mismatch: tenors {tenors.shape} vs zeros {zeros.shape}")
    if not (short_tenor < long_tenor):
        raise ValueError(f"short_tenor ({short_tenor}) must be below long_tenor ({long_tenor})")
    short_at, long_at = maturity_dated_deltas(
        tenors,
        short_times=short_times,
        short_pp_path=short_pp_path,
        long_times=long_times,
        long_pp_path=long_pp_path,
        t0_decimal_year=t0_decimal_year,
        window=window,
    )
    weight = np.clip((tenors - short_tenor) / (long_tenor - short_tenor), 0.0, 1.0)
    delta_pp = (1.0 - weight) * short_at + weight * long_at
    return zeros + delta_pp / 100.0
