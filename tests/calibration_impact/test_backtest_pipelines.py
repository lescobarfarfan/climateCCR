"""Units for the hazard (pipelines/27) and loss-ratio (pipelines/28) backtests (INT-40 A/B)."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def hazard():
    return _load("hazard_backtest", "pipelines/27_hazard_backtest.py")


@pytest.fixture(scope="module")
def loss_ratio():
    return _load("loss_ratio_backtest", "pipelines/28_loss_ratio_backtest.py")


def test_count_backtest_at_the_fitted_rate_is_central(hazard):
    fit = pd.Series([10] * 14, index=pd.RangeIndex(2002, 2016, name="anio"))
    test = pd.Series([10] * 9, index=pd.RangeIndex(2016, 2025, name="anio"))
    summary, pit_years = hazard.count_backtest(fit, test, np.random.default_rng(0))
    assert summary["lambda_fit"] == 10.0
    assert summary["predicted_mean"] == 90.0 and summary["n_test_events"] == 90
    assert 0.4 < summary["pit_total"] < 0.6
    assert summary["p_two_sided"] > 0.9
    assert summary["dispersion_ratio_fit"] == 0.0
    assert pit_years.shape == (9,) and np.all((pit_years >= 0) & (pit_years <= 1))
    far = pd.Series([30] * 9, index=test.index)
    assert hazard.count_backtest(fit, far, np.random.default_rng(0))[0]["p_two_sided"] < 1e-6


def test_annual_loss_backtest_covers_realisations_from_the_same_model(hazard):
    from climateCCR.calibration.impact import simulate_annual_losses

    rng = np.random.default_rng(3)
    sims = simulate_annual_losses(8.0, 500.0, 1.0, 50_000, rng)
    realised = pd.Series(
        simulate_annual_losses(8.0, 500.0, 1.0, 400, rng), index=pd.RangeIndex(1, 401)
    )
    rows, summary = hazard.annual_loss_backtest(sims, realised, [0.5, 0.8, 0.95])
    assert len(rows) == 400 and set(rows["pit"]) <= set(np.clip(rows["pit"], 0, 1))
    assert summary["coverage_50"] == pytest.approx(0.5, abs=0.08)
    assert summary["coverage_95"] == pytest.approx(0.95, abs=0.04)
    assert summary["ae_mean"] == pytest.approx(1.0, abs=0.2)
    assert summary["ks_p_pit"] > 0.01


def test_trigger_share_and_score_years(loss_ratio):
    years = pd.RangeIndex(2008, 2011)
    all_damage = pd.Series([1000.0, 500.0, 2500.0], index=years)
    trigger = pd.Series([800.0, 400.0, 2000.0], index=years)
    assert loss_ratio.trigger_share(all_damage, trigger, (2008, 2010)) == pytest.approx(0.8)
    with pytest.raises(ValueError):
        loss_ratio.trigger_share(all_damage * 0.0, trigger, (2008, 2010))
    sims = np.full(1000, 2000.0)  # a point-mass annual loss: ratios are exact
    denominators = pd.Series([10_000.0, 20_000.0], index=pd.RangeIndex(2016, 2018))
    realised = pd.Series([0.05, 0.02], index=denominators.index)
    rows, summary = loss_ratio.score_years(sims, denominators, realised, 0.25, [0.5])
    np.testing.assert_allclose(rows["model_mean_lr"], [0.05, 0.025])
    assert rows["pit"].iloc[0] == pytest.approx(0.5)  # realised equals the point mass
    assert rows["pit"].iloc[1] == pytest.approx(0.0)  # realised below it
    np.testing.assert_allclose(rows["crps"], [0.0, 0.005], atol=1e-12)
    assert summary["ae_mean"] == pytest.approx((0.05 + 0.02) / (0.05 + 0.025) * 1.0, rel=1e-9)
