"""HW1F ``a``/``sigma`` from the Mexican short-rate series (OQ-MKT-12a).

Vasicek is the estimation device for the Hull-White mean reversion and
volatility (MKT-IR-01): the model reproduces today's curve through ``theta(t)``
regardless of the drift level, so ``a`` and ``sigma`` come from the time series
of a short-rate proxy — F-TIIE overnight (MKT-CALIB-01) — and the cross-section
enters only through the curve fit (``calibration.financial.yield_curve``).

Two estimators, per MKT-CALIB-02 (never MLE on rate levels):

- :func:`fit_vasicek_ar1` — OLS of ``r_{t+1}`` on ``r_t`` (the discrete-Vasicek
  AR(1); for equally-spaced Gaussian data this *is* the conditional MLE);
- :func:`fit_vasicek_mle` — exact transition-density MLE with per-pair
  ``Delta t``, which handles the irregular spacing left behind by the crisis
  -window exclusions (MKT-CALIB-03) instead of pretending every step is one
  business day.

The two must agree within a few percent; an order-of-magnitude gap flags a
non-stationary sample (MKT-CALIB-02, [JamesWebber2000]). ``a`` is weakly
identified either way — report across estimation windows, not one point
(MKT-CALIB-04). SIE quotes convert via the simple-interest Act/360 form
(MKT-SIE-04), never ``(365/360)*ln(1+r)``.

Outputs are plain decimals ready for the ``'direct_input'`` seam
(``alpha``/``volatility``, DC-CCR-CAL-1). [BrigoMercurio2006] [Hull1990]
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import optimize

#: Continuous-compounding day count of the internal HW math (DC-MKT-SIE-3).
DAYS_PER_YEAR = 365.0
#: Business-day year fraction for the equally-spaced AR(1) step.
TRADING_DAYS_PER_YEAR = 252


def simple_to_continuous(rate: float | np.ndarray, tenor_days: float) -> float | np.ndarray:
    """Simple-interest Act/360 quote -> continuous Act/365 zero (MKT-SIE-04).

    ``P = 1/(1 + r*d/360)`` and ``P = exp(-z*d/365)`` give
    ``z = (365/d) * ln(1 + r*d/360)``. ``rate`` is decimal (e.g. ``0.08``).
    """
    if tenor_days <= 0:
        raise ValueError(f"tenor_days must be > 0, got {tenor_days}")
    return (DAYS_PER_YEAR / tenor_days) * np.log1p(rate * tenor_days / 360.0)


def exclude_windows(series: pd.Series, windows: Iterable[tuple[str, str]] | None) -> pd.Series:
    """Drop observations inside the closed ``[start, end]`` crisis windows.

    The estimators below then drop any observation pair whose gap exceeds
    ``max_gap_days``, so no pair silently bridges an excluded window with one
    giant step (MKT-CALIB-03).
    """
    if not windows:
        return series
    keep = pd.Series(True, index=series.index)
    for start, end in windows:
        keep &= ~series.index.to_series().between(pd.Timestamp(start), pd.Timestamp(end))
    return series[keep]


def _pairs(
    series: pd.Series, max_gap_days: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    """Consecutive observation pairs ``(r0, r1, gap_days)`` within ``max_gap_days``."""
    clean = series.dropna().sort_index()
    if len(clean) < 3:
        raise ValueError(f"need >= 3 observations, got {len(clean)}")
    values = clean.to_numpy(dtype=float)
    gaps = np.diff(clean.index.to_numpy()) / np.timedelta64(1, "D")
    keep = gaps <= max_gap_days
    n_dropped = int((~keep).sum())
    return values[:-1][keep], values[1:][keep], gaps[keep], n_dropped


@dataclass(frozen=True)
class VasicekFit:
    """``dr = alpha*(level - r)dt + sigma dW`` estimates (annualized decimals)."""

    alpha: float
    level: float
    sigma: float
    method: str
    n_pairs: int
    n_pairs_dropped: int

    @property
    def half_life_years(self) -> float:
        """Time for a rate displacement to decay by half: ``ln(2)/alpha``."""
        return float(np.log(2.0) / self.alpha)


def fit_vasicek_ar1(
    rates: pd.Series,
    *,
    dt_years: float = 1.0 / TRADING_DAYS_PER_YEAR,
    max_gap_days: float = 7.0,
) -> VasicekFit:
    """Discrete-Vasicek AR(1): OLS of ``r_{t+1}`` on ``r_t`` at a fixed step.

    ``phi = exp(-a*dt)``, ``c = b*(1-phi)``, ``Var(eps) = sigma^2*(1-phi^2)/(2a)``.
    Pairs spanning more than ``max_gap_days`` calendar days (holiday runs,
    excluded crisis windows) are dropped — the fixed-``dt`` assumption is the
    point of this estimator; the MLE handles the gaps. Raises ``ValueError``
    when ``phi`` falls outside ``(0, 1)`` (non-stationary sample, MKT-CALIB-02).
    """
    r0, r1, _, n_dropped = _pairs(rates, max_gap_days)
    if len(r0) < 3:
        raise ValueError(f"only {len(r0)} pairs within max_gap_days={max_gap_days}")
    design = np.column_stack([np.ones_like(r0), r0])
    (c, phi), *_ = np.linalg.lstsq(design, r1, rcond=None)
    if not 0.0 < phi < 1.0:
        raise ValueError(f"AR(1) coefficient {phi:.6f} outside (0, 1): non-stationary sample")
    residuals = r1 - c - phi * r0
    s2 = float(residuals @ residuals) / (len(r0) - 2)
    alpha = -np.log(phi) / dt_years
    sigma = float(np.sqrt(s2 * 2.0 * alpha / (1.0 - phi**2)))
    return VasicekFit(
        alpha=float(alpha),
        level=float(c / (1.0 - phi)),
        sigma=sigma,
        method="ar1",
        n_pairs=len(r0),
        n_pairs_dropped=n_dropped,
    )


def fit_vasicek_mle(
    rates: pd.Series,
    *,
    max_gap_days: float = 30.0,
    start: VasicekFit | None = None,
) -> VasicekFit:
    """Exact Gaussian transition-density MLE with per-pair ``Delta t`` (Act/365).

    ``r_{t+D} | r_t ~ N(b + (r_t - b)e^{-aD}, sigma^2 (1 - e^{-2aD}) / (2a))``
    — exact for any spacing, so weekends and post-exclusion gaps enter with
    their true ``Delta t`` instead of a one-step lie. Pairs wider than
    ``max_gap_days`` are still dropped: the OU bridge across a *structural*
    exclusion (COVID, GFC) is not a hypothesis we want in the likelihood.
    Starts from :func:`fit_vasicek_ar1` unless ``start`` is given.
    """
    r0, r1, gaps, n_dropped = _pairs(rates, max_gap_days)
    if len(r0) < 3:
        raise ValueError(f"only {len(r0)} pairs within max_gap_days={max_gap_days}")
    dt = gaps / DAYS_PER_YEAR
    start = start or fit_vasicek_ar1(rates, max_gap_days=min(7.0, max_gap_days))

    def negative_log_likelihood(params: np.ndarray) -> float:
        alpha, level, sigma = np.exp(params[0]), params[1], np.exp(params[2])
        decay = np.exp(-alpha * dt)
        mean = level + (r0 - level) * decay
        variance = sigma**2 * (1.0 - decay**2) / (2.0 * alpha)
        return float(0.5 * np.sum(np.log(2.0 * np.pi * variance) + (r1 - mean) ** 2 / variance))

    result = optimize.minimize(
        negative_log_likelihood,
        x0=[np.log(start.alpha), start.level, np.log(start.sigma)],
        method="Nelder-Mead",
        options={"xatol": 1e-8, "fatol": 1e-10, "maxiter": 5000},
    )
    if not result.success:
        raise ValueError(f"Vasicek MLE did not converge: {result.message}")
    return VasicekFit(
        alpha=float(np.exp(result.x[0])),
        level=float(result.x[1]),
        sigma=float(np.exp(result.x[2])),
        method="mle",
        n_pairs=len(r0),
        n_pairs_dropped=n_dropped,
    )
