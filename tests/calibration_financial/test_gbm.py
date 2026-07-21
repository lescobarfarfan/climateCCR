"""GBM drift/vol MLE on daily closes (OQ-MKT-12b)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from climateCCR.calibration.financial.gbm import fit_gbm
from climateCCR.infra import get_rng

TRUE_MU, TRUE_SIGMA = 0.12, 0.22


@pytest.fixture(scope="module")
def gbm_series() -> pd.Series:
    index = pd.bdate_range("2005-01-03", periods=5000)
    dt = 1.0 / 252
    rng = get_rng(11)
    log_returns = (TRUE_MU - TRUE_SIGMA**2 / 2) * dt + TRUE_SIGMA * np.sqrt(
        dt
    ) * rng.standard_normal(len(index) - 1)
    return pd.Series(45000.0 * np.exp(np.concatenate([[0.0], np.cumsum(log_returns)])), index=index)


def test_recovers_parameters(gbm_series):
    fit = fit_gbm(gbm_series)
    assert fit.volatility == pytest.approx(TRUE_SIGMA, rel=0.03)
    # Drift carries se ~ sigma/sqrt(T) ~ 0.05 — a loose check by nature.
    assert fit.drift == pytest.approx(TRUE_MU, abs=0.12)
    assert fit.n_returns == len(gbm_series) - 1


def test_formulas_match_hand_computation(gbm_series):
    fit = fit_gbm(gbm_series)
    x = np.diff(np.log(gbm_series.to_numpy()))
    sigma2 = np.var(x, ddof=1) * 252
    assert fit.volatility == pytest.approx(np.sqrt(sigma2))
    assert fit.drift == pytest.approx(np.mean(x) * 252 + sigma2 / 2)  # Ito term back


def test_gap_returns_dropped(gbm_series):
    holed = gbm_series.drop(gbm_series.index[100:130])
    fit = fit_gbm(holed)
    assert fit.n_returns_dropped == 1
    assert fit.n_returns == len(holed) - 2


def test_non_positive_prices_dropped(gbm_series):
    dirty = gbm_series.copy()
    dirty.iloc[10] = 0.0
    dirty.iloc[20] = np.nan
    fit = fit_gbm(dirty)
    # Each dropped mid-series price merges its two returns into one short-gap
    # return that stays within max_gap_days: 4999 - 2 = 4997 usable returns.
    assert fit.n_returns == len(gbm_series) - 3
    assert fit.n_returns_dropped == 0


def test_too_short_raises():
    with pytest.raises(ValueError, match="positive closes"):
        fit_gbm(pd.Series([100.0], index=pd.bdate_range("2020-01-01", periods=1)))
