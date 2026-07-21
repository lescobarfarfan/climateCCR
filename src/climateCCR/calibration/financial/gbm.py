"""GBM drift/volatility from daily closes — the price leg (OQ-MKT-12b).

Closed-form MLE on log returns: with ``x_i = ln(S_i/S_{i-1})`` at step ``dt``,
``sigma^2 = Var(x)/dt`` and ``mu = mean(x)/dt + sigma^2/2`` (the Ito
correction back from the log drift). Crisis windows are excluded upstream via
``hull_white.exclude_windows`` (MKT-CALIB-03) and pairs bridging an exclusion
drop through ``max_gap_days``, same discipline as the rate leg. Emits the
``'direct_input'`` GBM fields (``drift``/``volatility``, DC-CCR-CAL-1).
[Glasserman2003]
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from climateCCR.calibration.financial.hull_white import TRADING_DAYS_PER_YEAR


@dataclass(frozen=True)
class GBMFit:
    """``dS/S = drift dt + volatility dW`` estimates (annualized decimals)."""

    drift: float
    volatility: float
    n_returns: int
    n_returns_dropped: int


def fit_gbm(
    closes: pd.Series,
    *,
    dt_years: float = 1.0 / TRADING_DAYS_PER_YEAR,
    max_gap_days: float = 7.0,
) -> GBMFit:
    """MLE of GBM drift and volatility from a daily close series.

    ``closes`` is indexed by date; non-positive and missing prices are dropped
    (a log return needs both ends positive), and returns spanning more than
    ``max_gap_days`` calendar days are excluded so holiday runs and
    crisis-window seams do not enter as fake one-day moves.
    """
    clean = closes.dropna().sort_index()
    clean = clean[clean > 0]
    if len(clean) < 3:
        raise ValueError(f"need >= 3 positive closes, got {len(clean)}")
    gaps = np.diff(clean.index.to_numpy()) / np.timedelta64(1, "D")
    log_returns = np.diff(np.log(clean.to_numpy(dtype=float)))
    keep = gaps <= max_gap_days
    if keep.sum() < 2:
        raise ValueError(f"only {int(keep.sum())} returns within max_gap_days={max_gap_days}")
    kept = log_returns[keep]
    variance = float(np.var(kept, ddof=1)) / dt_years
    return GBMFit(
        drift=float(np.mean(kept)) / dt_years + variance / 2.0,
        volatility=float(np.sqrt(variance)),
        n_returns=int(keep.sum()),
        n_returns_dropped=int((~keep).sum()),
    )
