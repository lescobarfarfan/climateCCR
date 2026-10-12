"""Units for the jump-on vs jump-off density backtest (pipelines/30) — INT-40 tier D."""

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
def pipeline():
    return _load("jump_density_backtest", "pipelines/30_jump_density_backtest.py")


def test_jump_totals_draw_the_engine_marks_over_one_horizon_step(pipeline):
    cfg = {
        "valuation_date": "2026-07-17",
        "climate_jumps": {
            "intensity": 12.0,
            "equity_marks": {
                "median": 0.01,
                "sigma": 0.5,
                "sign": -1.0,
                "targets": ["A_SHARE", "B_SHARE"],
            },
        },
    }
    totals = pipeline.jump_totals(cfg, {"months": 12}, 20_000, 233423)
    assert set(totals) == {"A_SHARE", "B_SHARE"}
    j = totals["A_SHARE"]
    assert j.shape == (20_000,) and (j <= 0).all()
    mean_mark = -0.01 * np.exp(0.5**2 / 2)
    assert j.mean() == pytest.approx(12.0 * mean_mark, rel=0.05)  # lambda*h*E[mark], h = 1y
    again = pipeline.jump_totals(cfg, {"months": 12}, 20_000, 233423)["A_SHARE"]
    np.testing.assert_array_equal(j, again)  # same seed -> same draw (GEN-07)


def test_realised_windows_and_scoring_prefer_the_true_model(pipeline):
    rng = np.random.default_rng(2)
    index = pd.bdate_range("2010-01-04", "2024-12-31")
    mu, sigma = 0.08, 0.25
    dt = np.diff(index.to_numpy()) / np.timedelta64(1, "D") / 365.0
    steps = (mu - sigma**2 / 2) * dt + sigma * np.sqrt(dt) * rng.standard_normal(len(dt))
    closes = pd.Series(100.0 * np.exp(np.concatenate([[0.0], np.cumsum(steps)])), index=index)
    from climateCCR.risk.market import init_dates

    dates = init_dates("2010-01-04", "2024-12-31", {"months": 1})
    windows = pipeline.realised_windows(closes, dates, {"months": 1}, 7)
    assert len(windows) > 170
    assert (windows["end_date"] > windows["init_date"]).all()
    tau = windows["tau_years"].to_numpy()
    y = np.log(windows["end"].to_numpy() / windows["start"].to_numpy())
    mean, sd = (mu - sigma**2 / 2) * tau, sigma * np.sqrt(tau)
    jumps = -0.3 * rng.exponential(1.0, 5000)  # a heavy adverse jump mass the data never had
    scored = pipeline.score_series(y, mean, sd, jumps, np.random.default_rng(0), 0)
    engine, comp = scored["engine"], scored["compensated"]
    assert engine["dm_stat"] < -3.0 and engine["dm_p"] < 0.01  # jump-on decisively worse
    assert engine["expected_drag_pct"] < -20.0
    assert comp["log_score_on"] > engine["log_score_on"]  # drift matching helps ...
    assert comp["dm_stat"] < 0.0  # ... but the shape is still wrong for Gaussian data
    assert engine["crps_on"] > engine["crps_off"]
