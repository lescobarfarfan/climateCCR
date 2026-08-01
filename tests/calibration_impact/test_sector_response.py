"""Units for ``calibration.impact.sector_response`` (Phase C machinery, GEN-11).

Synthetic panels with planted effects throughout; the real-data run is
``pipelines/13_sector_event_study.py`` under its pre-registered gate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from climateCCR.calibration.impact import (
    build_episodes,
    episode_bootstrap_p,
    episode_cars,
    ordering_stat,
)

RNG = np.random.default_rng(233423)


def _market_and_name(
    n_days: int, episode_days: list[int], jump: float, rng: np.random.Generator
) -> tuple[pd.Series, pd.Series, pd.DatetimeIndex]:
    dates = pd.bdate_range("2010-01-04", periods=n_days)
    mkt_ret = rng.normal(0.0, 0.01, size=n_days)
    # Small idio noise: a CAR is the planted jump plus the window's realized
    # idio sum, so the noise budget must stay well inside the test tolerance.
    idio = rng.normal(0.0, 0.001, size=n_days)
    shocks = np.zeros(n_days)
    for day in episode_days:
        shocks[day] = jump
    name = np.cumsum(mkt_ret * 0.9 + idio + shocks)  # beta 0.9 to the market
    return pd.Series(name, index=dates), pd.Series(np.cumsum(mkt_ret), index=dates), dates


class TestEpisodeCars:
    def test_recovers_planted_jump(self):
        episode_days = [300, 500, 700]
        log_name, log_market, dates = _market_and_name(
            900, episode_days, jump=-0.08, rng=np.random.default_rng(7)
        )
        episodes = pd.DataFrame({"fecha": dates[episode_days]})
        cars = episode_cars(log_name, log_market, episodes, event_window_bd=5)
        assert len(cars) == 3
        assert cars["car"].mean() == pytest.approx(-0.08, abs=0.02)
        assert (cars["n_days"] == 6).all()

    def test_skips_pre_listing_and_short_estimation(self):
        log_name, log_market, dates = _market_and_name(
            400, [350], jump=-0.05, rng=np.random.default_rng(8)
        )
        episodes = pd.DataFrame({"fecha": [dates[30], dates[350], dates[399]]})
        cars = episode_cars(log_name, log_market, episodes, event_window_bd=5)
        # Day 30 has no estimation window; day 399 has no full event window.
        assert list(cars.index) == [dates[350]]

    def test_weekend_episode_maps_to_next_trading_day(self):
        log_name, log_market, dates = _market_and_name(
            400, [200], jump=-0.06, rng=np.random.default_rng(9)
        )
        saturday = dates[199] + pd.Timedelta(days=(5 - dates[199].weekday()))
        assert saturday.weekday() >= 5 or saturday not in dates
        episodes = pd.DataFrame({"fecha": [saturday]})
        cars = episode_cars(log_name, log_market, episodes, event_window_bd=5)
        assert len(cars) == 1


class TestOrderingStat:
    def test_negative_association_gets_small_one_sided_p(self):
        scales = pd.Series({f"N{i}": float(i) for i in range(12)})
        cars = pd.Series({f"N{i}": -0.01 * i + 0.001 * ((-1) ** i) for i in range(12)})
        tau, p = ordering_stat(cars, scales)
        assert tau < -0.8
        assert p < 0.01

    def test_positive_association_is_not_significant_for_h1_negative(self):
        scales = pd.Series({f"N{i}": float(i) for i in range(12)})
        cars = pd.Series({f"N{i}": 0.01 * i for i in range(12)})
        tau, p = ordering_stat(cars, scales)
        assert tau > 0
        assert p > 0.95

    def test_too_few_names_raise(self):
        with pytest.raises(ValueError, match=">= 3 names"):
            ordering_stat(pd.Series({"A": 1.0, "B": 2.0}), pd.Series({"A": 1.0, "B": 2.0}))


class TestEpisodeBootstrap:
    @staticmethod
    def _panel(effect: float, rng: np.random.Generator) -> tuple[pd.DataFrame, pd.Series]:
        names = [f"N{i}" for i in range(10)]
        scales = pd.Series({n: float(i) for i, n in enumerate(names)})
        rows = {n: -effect * scales[n] + rng.normal(0, 0.01, size=40) for n in names}
        panel = pd.DataFrame(rows, index=pd.RangeIndex(40))
        panel.iloc[:25, 0] = np.nan  # one name with a short history
        return panel, scales

    def test_planted_ordering_is_detected(self):
        panel, scales = self._panel(effect=0.01, rng=np.random.default_rng(11))
        p = episode_bootstrap_p(panel, scales, n_draws=500, rng=np.random.default_rng(12))
        assert p < 0.05

    def test_null_panel_is_not_detected(self):
        panel, scales = self._panel(effect=0.0, rng=np.random.default_rng(13))
        p = episode_bootstrap_p(panel, scales, n_draws=500, rng=np.random.default_rng(14))
        assert p > 0.05


def test_build_episodes_integrates_with_cyclone_subset():
    # The Phase C episode path: peril-filtered events -> episodes -> CARs.
    events = pd.DataFrame(
        {
            "fecha_inicio": ["2010-09-01", "2010-09-02", "2010-10-15"],
            "danio_mdp": [500.0, 300.0, 900.0],
            "duracion_dias": [2.0, 1.0, 3.0],
        }
    )
    episodes = build_episodes(events)
    assert len(episodes) == 2
    assert set(episodes.columns) == {"fecha", "danio_mdp", "n_eventos"}
