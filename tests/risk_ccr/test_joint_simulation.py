"""Units for the joint book draw (CCR-SIM-03): the slice, the union grid, the shared scenario."""

import numpy as np
import pytest
from climateCCR.simulation.multi_risk_factor_simulation import slice_scenarios
from pimpa_baseline import TODAY_DATE, _load_global_parameters

DATES = [f"2026-01-0{i}" for i in range(1, 6)]  # toy grid: any hashable date type works


def _toy_store():
    return {
        "A": np.arange(10.0).reshape(2, 5),
        "A_dates": list(DATES),
        "B": np.arange(10.0, 20.0).reshape(2, 5),
        "B_dates": list(DATES),
    }


def test_slice_picks_columns_in_order_and_copies():
    joint = _toy_store()
    wanted = [DATES[0], DATES[2], DATES[4]]
    out = slice_scenarios(joint, ["B", "A"], wanted)
    assert set(out) == {"A", "A_dates", "B", "B_dates"}
    np.testing.assert_array_equal(out["A"], joint["A"][:, [0, 2, 4]])
    np.testing.assert_array_equal(out["B"], joint["B"][:, [0, 2, 4]])
    assert out["A_dates"] == wanted
    out["A"][0, 0] = -1.0
    assert joint["A"][0, 0] == 0.0  # a copy: the store is untouched


def test_slice_fails_loudly():
    joint = _toy_store()
    with pytest.raises(ValueError, match="do not simulate C"):
        slice_scenarios(joint, ["C"], [DATES[0]])
    with pytest.raises(ValueError, match="not on the joint grid"):
        slice_scenarios(joint, ["A"], [DATES[0], "2030-01-01"])


@pytest.mark.integration
def test_fixture_book_shares_one_scenario():
    from climateCCR.processes.jumps import ClimateJumpProcess, DeterministicMark
    from climateCCR.risk.ccr.evaluators.ccr_valuation_session import prepare_book, simulate_book

    gp = _load_global_parameters()
    gp["n_paths"] = 200
    sessions = prepare_book(TODAY_DATE, gp)
    joint = simulate_book(sessions, gp)
    union = list(joint["USD_ZERO_YIELD_CURVE_dates"])
    assert union[0] == sessions[0].simulation_dates[0]
    for session in sessions:
        assert set(session.simulation_dates) <= set(union)
        session.simulate(gp, joint_scenarios=joint)

    # The slice is the store's own columns — no new draw.
    first = sessions[0]
    columns = [union.index(date) for date in first.simulation_dates]
    np.testing.assert_array_equal(
        first.scenarios["USD_ZERO_YIELD_CURVE"], joint["USD_ZERO_YIELD_CURVE"][:, columns]
    )

    # Every netting set that simulates the curve sees the same curve path on common dates.
    curve_sessions = [s for s in sessions if "USD_ZERO_YIELD_CURVE" in s.scenarios]
    assert len(curve_sessions) >= 2
    a, b = curve_sessions[0], curve_sessions[1]
    common = sorted(set(a.simulation_dates) & set(b.simulation_dates))
    assert len(common) > 1
    ia = [a.simulation_dates.index(d) for d in common]
    ib = [b.simulation_dates.index(d) for d in common]
    np.testing.assert_array_equal(
        a.scenarios["USD_ZERO_YIELD_CURVE"][:, ia], b.scenarios["USD_ZERO_YIELD_CURVE"][:, ib]
    )

    # Pairing: the jump-on store shares every diffusion draw with the jump-off store.
    gp["climate_jumps"] = ClimateJumpProcess(0.5, {"CREDIT_SUISSE_SHARE": DeterministicMark(-0.05)})
    jumped = simulate_book(sessions, gp)
    np.testing.assert_array_equal(jumped["USD_ZERO_YIELD_CURVE"], joint["USD_ZERO_YIELD_CURVE"])
    assert not np.array_equal(jumped["CREDIT_SUISSE_SHARE"], joint["CREDIT_SUISSE_SHARE"])
