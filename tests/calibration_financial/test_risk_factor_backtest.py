"""Units for the risk-factor forecast backtest (pipelines/29) — INT-40 tier C."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from climateCCR.infra import get_rng

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def backtest():
    return _load("risk_factor_backtest", "pipelines/29_risk_factor_backtest.py")


@pytest.fixture(scope="module")
def gbm_closes() -> pd.Series:
    """Twelve years of daily GBM closes (mu 0.08, sigma 0.25) on a business-day calendar."""
    index = pd.bdate_range("2010-01-04", "2021-12-31")
    rng = get_rng(17)
    dt = np.diff(index.to_numpy()) / np.timedelta64(1, "D") / 365.0
    steps = (0.08 - 0.5 * 0.25**2) * dt + 0.25 * np.sqrt(dt) * rng.standard_normal(len(dt))
    return pd.Series(100.0 * np.exp(np.concatenate([[0.0], np.cumsum(steps)])), index=index)


def test_init_dates_are_non_overlapping_and_spaced_by_the_horizon(backtest):
    weekly = backtest.init_dates("2020-01-01", "2020-03-01", {"days": 7})
    assert weekly[0] == pd.Timestamp("2020-01-01") and len(weekly) == 8
    assert all((b - a).days == 7 for a, b in zip(weekly[:-1], weekly[1:], strict=True))
    assert backtest.horizon_end(weekly[-1], {"days": 7}) <= pd.Timestamp("2020-03-01")
    monthly = backtest.init_dates("2020-01-31", "2020-06-30", {"months": 1})
    assert [d.month for d in monthly] == [1, 2, 3, 4, 5]


def test_gbm_forecast_pits_are_uniform_under_the_true_model(backtest, gbm_closes):
    crisis = [("2015-01-01", "2015-03-31")]
    pits = []
    for t in backtest.init_dates("2014-01-02", "2021-12-31", {"days": 7}):
        fc = backtest.gbm_forecast(
            gbm_closes,
            t,
            backtest.horizon_end(t, {"days": 7}),
            crisis,
            min_history_years=3.0,
            max_stale_days=7,
        )
        if fc is not None:
            assert fc["fit_method"] == "gbm_mle" and fc["sd"] > 0
            from scipy import stats

            pits.append(stats.norm.cdf((fc["realised"] - fc["mean"]) / fc["sd"]))
    pits = np.asarray(pits)
    assert len(pits) > 350
    assert 0.9 < np.mean((pits >= 0.025) & (pits <= 0.975)) < 0.99
    # No history before the series start -> no forecast.
    assert (
        backtest.gbm_forecast(
            gbm_closes,
            pd.Timestamp("2011-01-03"),
            pd.Timestamp("2011-01-10"),
            None,
            min_history_years=3.0,
            max_stale_days=7,
        )
        is None
    )


def test_vasicek_forecast_recovers_an_ou_cone(backtest):
    rng = get_rng(5)
    index = pd.bdate_range("2006-01-02", "2019-12-31")
    a, b, s = 0.5, 0.07, 0.01
    r = np.empty(len(index))
    r[0] = 0.05
    for i in range(1, len(index)):
        dt = (index[i] - index[i - 1]).days / 365.0
        decay = np.exp(-a * dt)
        r[i] = (
            b
            + (r[i - 1] - b) * decay
            + s * np.sqrt((1 - decay**2) / (2 * a)) * rng.standard_normal()
        )
    rates = pd.Series(r, index=index)
    t = pd.Timestamp("2016-06-01")
    fc = backtest.vasicek_forecast(
        rates,
        t,
        t + pd.DateOffset(months=3),
        None,
        anchor="W-WED",
        min_history_years=3.0,
        max_stale_days=7,
    )
    assert fc is not None and fc["fit_method"] in {"mle", "mle_restart", "ar1"}
    stationary_sd = s / np.sqrt(2 * a)
    assert 0.3 * stationary_sd < fc["sd"] < 1.2 * stationary_sd
    assert abs(fc["mean"] - b) < 0.02


def test_daily_var_hits_match_the_nominal_rate(backtest, gbm_closes):
    hits = backtest.daily_var_hits(gbm_closes, 0.95, None, "2014-01-02", "2021-12-31", 3.0)
    assert hits.size > 1800
    assert 0.03 < hits.mean() < 0.075
