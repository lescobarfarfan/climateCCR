"""Simulation-grid densification (`simulation_max_step_days`).

Absent, the grid must be the legacy event-driven schedule bit-for-bit (the
golden-baseline guarantee, CCR-MIG-03); set to N, no two consecutive
simulation dates may be more than N days apart and every legacy date must
still be present (reporting stays exact).
"""

from datetime import timedelta
from types import SimpleNamespace

from climateCCR.risk.ccr.evaluators.ccr_valuation_session import CCR_Valuation_Session

BASE_GP = {"date_format": "%Y-%m-%d", "B3_grid": ["0D", "1D", "1W", "1M", "6M", "1Y", "2Y"]}


def build_grid(extra_gp: dict | None = None) -> list:
    session = CCR_Valuation_Session(SimpleNamespace(portfolio_valuation_dates=[]))
    session.mpor_d = 14
    session.generate_time_grids("2020-01-01", {**BASE_GP, **(extra_gp or {})})
    return session.simulation_dates


def test_absent_key_keeps_legacy_grid():
    assert build_grid() == build_grid({"simulation_max_step_days": None})


def test_daily_cap_bounds_every_step_and_keeps_legacy_dates():
    legacy = build_grid()
    dense = build_grid({"simulation_max_step_days": 1})
    steps = [b - a for a, b in zip(dense, dense[1:], strict=False)]
    assert max(steps) <= timedelta(days=1)
    assert set(legacy) <= set(dense)
    assert dense[0] == legacy[0] and dense[-1] == legacy[-1]


def test_weekly_cap_bounds_every_step():
    dense = build_grid({"simulation_max_step_days": 7})
    steps = [b - a for a, b in zip(dense, dense[1:], strict=False)]
    assert max(steps) <= timedelta(days=7)
