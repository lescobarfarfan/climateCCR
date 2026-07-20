"""Event-study machinery (calibration.impact.rate_response): merge, recovery, conversion."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from climateCCR.calibration.impact import (
    build_episodes,
    event_study,
    rate_scale_from_beta,
)


def test_episodes_merge_within_window_and_sum_losses():
    events = pd.DataFrame(
        {
            "fecha_inicio": ["2010-09-01", "2010-09-03", "2010-09-06", "2010-11-15"],
            "danio_mdp": [100.0, 200.0, 50.0, 400.0],
            "duracion_dias": [1.0, 0.0, 2.0, 1.0],
        }
    )
    episodes = build_episodes(events, merge_window_bd=5)
    assert len(episodes) == 2
    assert episodes.loc[0, "fecha"] == pd.Timestamp("2010-09-01")
    assert episodes.loc[0, "danio_mdp"] == pytest.approx(350.0)
    assert episodes.loc[0, "n_eventos"] == 3
    assert episodes.loc[1, "danio_mdp"] == pytest.approx(400.0)
    assert episodes.attrs["n_excluded_duration"] == 0


def test_episodes_exclude_long_duration():
    events = pd.DataFrame(
        {
            "fecha_inicio": ["2010-05-01", "2010-08-01"],
            "danio_mdp": [1000.0, 300.0],
            "duracion_dias": [180.0, 3.0],  # a season-long drought and a storm
        }
    )
    episodes = build_episodes(events, max_duration_days=30)
    assert len(episodes) == 1
    assert episodes.loc[0, "danio_mdp"] == pytest.approx(300.0)
    assert episodes.attrs["n_excluded_duration"] == 1


def _synthetic_study(beta_true: float, seed: int = 7):
    dates = pd.bdate_range("2005-01-03", "2012-12-31")
    rng = np.random.default_rng(seed)
    dus = rng.normal(0.0, 2e-4, len(dates))
    us = pd.Series(0.04 + np.cumsum(dus), index=dates)
    dy = 0.4 * dus + rng.normal(0.0, 1e-4, len(dates))
    y = np.full(len(dates), 0.08) + np.cumsum(dy)

    positions = np.arange(150, len(dates) - 20, 150)  # spaced past the estimation window
    losses_bn = rng.uniform(0.2, 30.0, len(positions))
    for pos, loss in zip(positions, losses_bn, strict=True):
        y[pos:] += beta_true * loss  # a permanent level step on the event day
    episodes = pd.DataFrame(
        {"fecha": dates[positions], "danio_mdp": losses_bn * 1e3, "n_eventos": 1}
    )
    return event_study(
        pd.Series(y, index=dates),
        us,
        episodes,
        pillar="TEST",
        t_years=10.0,
        n_bootstrap=2000,
        rng=np.random.default_rng(seed),
    )


def test_beta_recovery_on_synthetic_panel():
    beta_true = 5e-5  # decimal yield per bn MDP
    result = _synthetic_study(beta_true)
    assert result is not None
    assert result.n_episodes >= 10
    assert result.beta_per_bn == pytest.approx(beta_true, rel=0.25)
    assert result.p_one_sided < 0.05
    assert result.p_bootstrap < 0.05


def test_null_beta_does_not_fire_the_gate():
    result = _synthetic_study(0.0)
    assert result is not None
    assert result.p_one_sided > 0.05  # deterministic under the fixed seed


def test_under_identified_returns_none():
    dates = pd.bdate_range("2010-01-04", periods=300)
    y = pd.Series(0.08, index=dates)
    us = pd.Series(0.04, index=dates)
    episodes = pd.DataFrame(
        {"fecha": [dates[10]], "danio_mdp": [500.0], "n_eventos": [1]}
    )  # day0 has no estimation window behind it
    assert event_study(y, us, episodes, pillar="T", t_years=5.0) is None


def test_rate_scale_from_beta_limits_and_units():
    # alpha -> 0: the loading is 1 and J is just beta restated per MDP.
    j, s = rate_scale_from_beta(1e-4, t_years=25.0, hw_alpha=0.0)
    assert j == pytest.approx(1e-7)
    assert s == pytest.approx(1e7)
    # engine case: alpha=0.05, T=25 -> loading (1-e^-1.25)/1.25.
    loading = (1 - np.exp(-1.25)) / 1.25
    j, s = rate_scale_from_beta(1e-4, t_years=25.0, hw_alpha=0.05)
    assert j == pytest.approx(1e-7 / loading)
    assert s == pytest.approx(1e7 * loading)
    with pytest.raises(ValueError):
        rate_scale_from_beta(-1e-4, t_years=25.0, hw_alpha=0.05)
    with pytest.raises(ValueError):
        rate_scale_from_beta(1e-4, t_years=0.0, hw_alpha=0.05)
