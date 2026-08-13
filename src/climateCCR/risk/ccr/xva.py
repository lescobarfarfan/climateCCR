"""Unilateral CVA at the reporting seam (resolves OQ-CCR-04's placement).

Pure functions over contract-shaped arrays — no engine imports, no model
objects (the INT-15 discipline): the pipeline feeds EE profiles from the
DC-CCR-RISK-3 comparison frames, discount factors off the initial pricing
curve, and survival curves bootstrapped from annual default probabilities
(CLIMACRED ``baseline_pd`` + ``pd_adjustment``, DC-MKT-NGFS-2).

The discretization is the standard one [Gregory_xVA] [PykhtinZhu2007]:

    CVA = LGD * sum_i 0.5 * (EE_{i-1} DF_{i-1} + EE_i DF_i) * (S_{i-1} - S_i)

with EE the uncollateralised expected exposure at the reporting grid (already
floored at zero path-wise, CCR-RISK-03), DF(0, t_i) deterministic off today's
curve (the rate-exposure covariance is future work with stochastic WWR), and
S the piecewise-exponential survival from annual hazards
``lambda_y = -ln(1 - PD_y)``.

CVA is bilinear in the EE profile and the default-probability increments, so a
scenario delta decomposes *exactly* into an exposure channel (moving EE at
base PDs), a credit channel (moving PDs at base EE), and an interaction term —
the scenario-conditional wrong-way readout the INT-23/INT-31 caveat calls for.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "survival_from_annual_pd",
    "cva_unilateral",
    "cva_decomposition",
    "implied_pd_from_spread",
]


def survival_from_annual_pd(
    segment_starts: np.ndarray, pd_pp: np.ndarray, grid_years: np.ndarray
) -> np.ndarray:
    """Survival S(t) at ``grid_years`` from a piecewise-constant annual PD path.

    Args:
        segment_starts: Start of each annual PD segment, in year fractions from
            the valuation date (may be negative for calendar years already begun;
            each PD applies on ``[start_k, start_{k+1})`` and the last extends
            flat — the hold-constant-beyond-the-window rule, MKT-NGFS-09 style).
        pd_pp: One-year default probabilities per segment, in percentage points
            (11.55 = 11.55%). Values are clipped to ``[0, 100)`` — a PD of 100%
            has no finite hazard.
        grid_years: Reporting-grid year fractions (>= 0, ascending) at which to
            evaluate S(t); S(0) = 1.

    Returns:
        Survival probabilities, same shape as ``grid_years``.
    """
    starts = np.asarray(segment_starts, dtype=float)
    pds = np.asarray(pd_pp, dtype=float)
    grid = np.asarray(grid_years, dtype=float)
    if starts.ndim != 1 or starts.size == 0 or starts.size != pds.size:
        raise ValueError("segment_starts and pd_pp must be equal-length 1-D arrays")
    if np.any(np.diff(starts) <= 0):
        raise ValueError("segment_starts must be strictly increasing")
    if np.any(~np.isfinite(pds)):
        raise ValueError("pd_pp contains non-finite values")
    if np.any(grid < 0) or np.any(np.diff(grid) < 0):
        raise ValueError("grid_years must be non-negative and ascending")

    hazards = -np.log1p(-np.clip(pds, 0.0, 100.0 - 1e-9) / 100.0)
    horizon = float(grid.max(initial=0.0)) + 1.0
    # The cumulative hazard is piecewise linear; its knots are t=0, every listed
    # segment start inside (0, horizon), and the horizon itself. Each interval
    # carries the hazard of the segment covering its midpoint (flat-back before
    # the first start, flat-forward after the last).
    interior = starts[(starts > 0.0) & (starts < horizon)]
    knots = np.concatenate([[0.0], interior, [horizon]])
    midpoints = 0.5 * (knots[:-1] + knots[1:])
    segment_index = np.clip(np.searchsorted(starts, midpoints, side="right") - 1, 0, None)
    increments = hazards[segment_index] * np.diff(knots)
    cum_at_knots = np.concatenate([[0.0], np.cumsum(increments)])
    return np.exp(-np.interp(grid, knots, cum_at_knots))


def cva_unilateral(
    ee: np.ndarray, df: np.ndarray, survival: np.ndarray, lgd: float = 0.60
) -> float:
    """Unilateral CVA in the EE profile's currency units.

    ``ee``, ``df`` and ``survival`` share the reporting grid (t_0 = valuation
    date first). EE must already be the floored expected exposure (>= 0).
    """
    ee = np.asarray(ee, dtype=float)
    df = np.asarray(df, dtype=float)
    survival = np.asarray(survival, dtype=float)
    if not (ee.shape == df.shape == survival.shape) or ee.ndim != 1 or ee.size < 2:
        raise ValueError("ee, df and survival must be equal-length 1-D arrays (>= 2 points)")
    if np.any(~np.isfinite(ee)) or np.any(ee < 0):
        raise ValueError("ee must be finite and non-negative (the floored EE profile)")
    if np.any(df <= 0) or np.any(df > 1.0 + 1e-9):
        raise ValueError("df must be discount factors in (0, 1]")
    if np.any(survival < -1e-12) or np.any(survival > 1.0 + 1e-12):
        raise ValueError("survival must lie in [0, 1]")
    if np.any(np.diff(survival) > 1e-12):
        raise ValueError("survival must be non-increasing")
    if not 0.0 <= lgd <= 1.0:
        raise ValueError("lgd must lie in [0, 1]")

    discounted = ee * df
    default_prob = -np.diff(survival)
    return float(lgd * np.sum(0.5 * (discounted[:-1] + discounted[1:]) * default_prob))


def cva_decomposition(
    ee_base: np.ndarray,
    ee_scenario: np.ndarray,
    survival_base: np.ndarray,
    survival_scenario: np.ndarray,
    df: np.ndarray,
    lgd: float = 0.60,
) -> dict[str, float]:
    """Exact scenario-delta split: exposure channel + credit channel + interaction.

    CVA is bilinear in (EE, -dS), so with ``delta = cva_scenario - cva_base``:
    ``exposure_channel`` moves EE at base survival, ``credit_channel`` moves
    survival at base EE, and ``interaction = delta - exposure - credit`` is the
    exact cross term (the scenario-conditional wrong-way component).
    """
    cva_base = cva_unilateral(ee_base, df, survival_base, lgd)
    cva_scenario = cva_unilateral(ee_scenario, df, survival_scenario, lgd)
    exposure = cva_unilateral(ee_scenario, df, survival_base, lgd) - cva_base
    credit = cva_unilateral(ee_base, df, survival_scenario, lgd) - cva_base
    delta = cva_scenario - cva_base
    return {
        "cva_base": cva_base,
        "cva_scenario": cva_scenario,
        "cva_delta": delta,
        "exposure_channel": exposure,
        "credit_channel": credit,
        "interaction": delta - exposure - credit,
    }


def implied_pd_from_spread(spread: float, recovery: float = 0.40) -> tuple[float, float]:
    """Credit-triangle hazard and 1y PD implied by a flat spread.

    ``lambda = s / (1 - R)`` [Gregory_xVA]; ``spread`` decimal per annum
    (0.0240 = 240 bp). Returns ``(hazard, pd_1y)`` with ``pd_1y`` decimal.
    """
    if spread < 0:
        raise ValueError("spread must be non-negative")
    if not 0.0 <= recovery < 1.0:
        raise ValueError("recovery must lie in [0, 1)")
    hazard = spread / (1.0 - recovery)
    return hazard, float(1.0 - np.exp(-hazard))
