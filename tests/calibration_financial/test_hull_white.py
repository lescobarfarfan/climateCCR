"""Vasicek AR(1)/MLE estimators and SIE rate conversion (MKT-CALIB-02, MKT-SIE-04)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from climateCCR.calibration.financial.hull_white import (
    DAYS_PER_YEAR,
    exclude_windows,
    fit_vasicek_ar1,
    fit_vasicek_mle,
    simple_to_continuous,
)
from climateCCR.infra import get_rng

TRUE_ALPHA, TRUE_LEVEL, TRUE_SIGMA = 1.2, 0.06, 0.015


def _exact_ou_path(index: pd.DatetimeIndex, seed: int = 7) -> pd.Series:
    """Exact OU transitions over the index's true Act/365 gaps."""
    rng = get_rng(seed)
    dt = np.diff(index.to_numpy()) / np.timedelta64(1, "D") / DAYS_PER_YEAR
    rates = np.empty(len(index))
    rates[0] = TRUE_LEVEL
    for i, step in enumerate(dt):
        decay = np.exp(-TRUE_ALPHA * step)
        sd = TRUE_SIGMA * np.sqrt((1.0 - decay**2) / (2.0 * TRUE_ALPHA))
        rates[i + 1] = TRUE_LEVEL + (rates[i] - TRUE_LEVEL) * decay + sd * rng.standard_normal()
    return pd.Series(rates, index=index)


@pytest.fixture(scope="module")
def ou_series() -> pd.Series:
    return _exact_ou_path(pd.bdate_range("2006-01-02", periods=6000))


def test_simple_to_continuous_round_trip():
    rate, days = 0.08, 364.0
    z = simple_to_continuous(rate, days)
    assert np.exp(-z * days / 365.0) == pytest.approx(1.0 / (1.0 + rate * days / 360.0))
    with pytest.raises(ValueError, match="tenor_days"):
        simple_to_continuous(rate, 0.0)


def test_ar1_and_mle_recover_and_agree(ou_series):
    ar1 = fit_vasicek_ar1(ou_series)
    mle = fit_vasicek_mle(ou_series)
    for fit in (ar1, mle):
        # alpha is weakly identified (MKT-CALIB-04); sigma and level are sharp.
        # AR(1) assumes 252 uniform steps/year while the bdate grid has ~261
        # with 3-day weekends, a ~2 % sigma wedge the MLE does not carry.
        assert fit.alpha == pytest.approx(TRUE_ALPHA, rel=0.25)
        assert fit.level == pytest.approx(TRUE_LEVEL, abs=0.01)
        assert fit.sigma == pytest.approx(TRUE_SIGMA, rel=0.03)
    # The MKT-CALIB-02 cross-check: the two estimators agree within a few percent.
    assert mle.alpha == pytest.approx(ar1.alpha, rel=0.05)
    assert mle.sigma == pytest.approx(ar1.sigma, rel=0.03)
    assert ar1.half_life_years == pytest.approx(np.log(2) / ar1.alpha)


def test_mle_handles_irregular_gaps(ou_series):
    # Punch a hole (a crisis exclusion) — the bridging pair must be dropped,
    # and the estimate should stay close to the full-sample one.
    holed = exclude_windows(ou_series, [("2010-01-01", "2011-06-30")])
    fit = fit_vasicek_mle(holed)
    assert fit.n_pairs_dropped >= 1
    assert fit.sigma == pytest.approx(TRUE_SIGMA, rel=0.03)


def test_exclude_windows_drops_closed_range(ou_series):
    trimmed = exclude_windows(ou_series, [("2010-01-01", "2010-12-31")])
    assert not trimmed.index.to_series().between("2010-01-01", "2010-12-31").any()
    assert len(trimmed) < len(ou_series)
    assert exclude_windows(ou_series, None) is ou_series


def test_non_stationary_sample_raises():
    explosive = pd.Series(
        0.02 * 1.001 ** np.arange(500), index=pd.bdate_range("2020-01-01", periods=500)
    )
    with pytest.raises(ValueError, match="non-stationary"):
        fit_vasicek_ar1(explosive)


def test_too_few_observations_raises():
    short = pd.Series([0.05, 0.06], index=pd.bdate_range("2020-01-01", periods=2))
    with pytest.raises(ValueError, match=">= 3"):
        fit_vasicek_ar1(short)
