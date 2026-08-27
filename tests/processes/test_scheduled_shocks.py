"""Unit tests for the deterministic scheduled-shock overlay (OQ-INT-12 Phase 1).

Covers the config parsing/validation, the grid interpolation with the t=0 pin
and hold-beyond-window clamp, the two load-bearing invariants — the HW1F
decay-compensated marks *track* the scenario path exactly at grid dates, and a
constant path reproduces the nivel state at every date after t=0 — plus the
MultiRiskFactorSimulation wiring: zero RNG consumed, diffusion draws
bit-identical with the block on or off, loud errors on unsimulated targets.
"""

from datetime import datetime

import numpy as np
import pytest
from climateCCR.processes.diffusions.geometric_brownian_motion import GeometricBrownianMotion
from climateCCR.processes.diffusions.hw1f import HW1F
from climateCCR.processes.jumps import ClimateJumpProcess, DeterministicMark
from climateCCR.processes.scheduled_shocks import ScheduledShockOverlay
from climateCCR.simulation.correlation_matrix import CorrelationMatrix
from climateCCR.simulation.multi_risk_factor_simulation import MultiRiskFactorSimulation
from climateCCR.simulation.risk_factor import RiskFactor
from climateCCR.utils.calendar_utils import transform_dates_to_time_differences

SEED = 233423
DATES = [datetime(2020, 1, 1), datetime(2020, 7, 1), datetime(2021, 1, 1), datetime(2023, 1, 1)]
TIMES = np.asarray(transform_dates_to_time_differences(DATES[0], DATES))
ALPHA = 0.0758  # the MKT-CALIB-08 headline, any positive value works


def _overlay(rate=None, equity=None):
    block = {}
    if rate is not None:
        times, values = rate
        block["rate_shocks"] = {
            "targets": ["R"],
            "times_years": list(times),
            "deltas": {"R": list(values)},
        }
    if equity is not None:
        times, values = equity
        block["equity_shocks"] = {
            "targets": ["A"],
            "times_years": list(times),
            "log_factors": {"A": list(values)},
        }
    return ScheduledShockOverlay.from_config(block)


def _pinned(path_times, values):
    target = np.interp(TIMES, path_times, values)
    target[0] = 0.0
    return target


# ---------------------------------------------------------------------------
# Interpolation, pin, clamp
# ---------------------------------------------------------------------------


def test_equity_marks_are_increments_of_the_pinned_path():
    path = (np.array([0.0, 1.0, 2.0]), np.array([0.00, -0.02, -0.05]))
    marks = _overlay(equity=path).step_marks(DATES, {})
    np.testing.assert_allclose(marks["A"], np.diff(_pinned(*path)))


def test_path_holds_first_value_before_and_last_value_beyond_the_window():
    # Observations only inside (t_1, t_2): earlier dates hold the first value,
    # later dates hold the last (the np.interp end clamps, MKT-NGFS-09 rule).
    path = (np.array([0.6, 0.9]), np.array([-0.02, -0.04]))
    marks = _overlay(equity=path).step_marks(DATES, {})
    overlay = np.concatenate(([0.0], np.cumsum(marks["A"])))
    np.testing.assert_allclose(overlay, [0.0, -0.02, -0.04, -0.04])


def test_t0_is_pinned_to_the_observed_market():
    # A path already at its peak at t=0 leaves the valuation date unshocked;
    # the prevailing value applies from the first simulation step onward.
    path = (np.array([0.0, 3.5]), np.array([-0.03, -0.03]))
    marks = _overlay(equity=path).step_marks(DATES, {})
    overlay = np.concatenate(([0.0], np.cumsum(marks["A"])))
    np.testing.assert_allclose(overlay, [0.0, -0.03, -0.03, -0.03])


# ---------------------------------------------------------------------------
# The two load-bearing invariants
# ---------------------------------------------------------------------------


def test_rate_marks_track_the_delta_path_exactly_through_the_hw1f_overlay():
    path = (np.array([0.0, 0.4, 1.3, 2.8]), np.array([0.0, 0.011, 0.023, 0.007]))
    marks = _overlay(rate=path).step_marks(DATES, {"R": ALPHA})

    model = HW1F("R")
    model.calibration = {"alpha": ALPHA, "volatility": 0.01}
    zero_paths = np.zeros((3, len(DATES)))
    overlaid = model.apply_jump_overlay(
        zero_paths, np.broadcast_to(marks["R"], (3, len(marks["R"]))), DATES
    )
    expected = _pinned(*path)
    for row in overlaid:
        np.testing.assert_allclose(row, expected, rtol=1e-12, atol=1e-15)


def test_constant_paths_reduce_to_the_nivel_state_after_t0():
    # Constant scenario paths reproduce the t=0 peak overlay at every grid
    # date >= t_1 (the MKT-NGFS-09 flat-reduction invariant, one level up).
    rate = (np.array([0.0, 3.0]), np.array([0.015, 0.015]))
    equity = (np.array([0.0, 3.0]), np.array([-0.04, -0.04]))
    overlay = _overlay(rate=rate, equity=equity)
    marks = overlay.step_marks(DATES, {"R": ALPHA})

    hw1f = HW1F("R")
    hw1f.calibration = {"alpha": ALPHA, "volatility": 0.01}
    rate_overlaid = hw1f.apply_jump_overlay(
        np.zeros((1, len(DATES))), marks["R"][np.newaxis, :], DATES
    )
    np.testing.assert_allclose(rate_overlaid[0], [0.0, 0.015, 0.015, 0.015], rtol=1e-12)

    gbm = GeometricBrownianMotion("A")
    equity_overlaid = gbm.apply_jump_overlay(
        np.ones((1, len(DATES))), marks["A"][np.newaxis, :], DATES
    )
    np.testing.assert_allclose(equity_overlaid[0], [1.0] + [np.exp(-0.04)] * 3, rtol=1e-12)


# ---------------------------------------------------------------------------
# Determinism and validation
# ---------------------------------------------------------------------------


def test_step_marks_is_deterministic_and_seed_free():
    path = (np.array([0.0, 2.0]), np.array([0.0, -0.03]))
    overlay = _overlay(equity=path)
    first = overlay.step_marks(DATES, {})
    second = overlay.step_marks(DATES, {})
    np.testing.assert_array_equal(first["A"], second["A"])


def test_missing_alpha_for_a_rate_target_raises():
    path = (np.array([0.0, 2.0]), np.array([0.0, 0.01]))
    with pytest.raises(ValueError, match="mean-reversion alpha"):
        _overlay(rate=path).step_marks(DATES, {})


@pytest.mark.parametrize(
    "block",
    [
        {},  # no channel at all
        {  # length mismatch
            "equity_shocks": {
                "targets": ["A"],
                "times_years": [0.0, 1.0],
                "log_factors": {"A": [0.0]},
            }
        },
        {  # non-monotone times
            "equity_shocks": {
                "targets": ["A"],
                "times_years": [1.0, 0.5],
                "log_factors": {"A": [0.0, -0.01]},
            }
        },
        {  # path for an unknown target
            "equity_shocks": {
                "targets": ["A"],
                "times_years": [0.0, 1.0],
                "log_factors": {"A": [0.0, -0.01], "B": [0.0, -0.01]},
            }
        },
        {  # missing path for a listed target
            "equity_shocks": {
                "targets": ["A", "B"],
                "times_years": [0.0, 1.0],
                "log_factors": {"A": [0.0, -0.01]},
            }
        },
    ],
)
def test_invalid_config_blocks_raise(block):
    with pytest.raises((ValueError, KeyError)):
        ScheduledShockOverlay.from_config(block)


def test_a_target_cannot_sit_in_both_channels():
    with pytest.raises(ValueError, match="both channels"):
        ScheduledShockOverlay(
            rate_paths={"X": (np.array([0.0]), np.array([0.0]))},
            equity_paths={"X": (np.array([0.0]), np.array([0.0]))},
        )


# ---------------------------------------------------------------------------
# MultiRiskFactorSimulation wiring
# ---------------------------------------------------------------------------


def _gbm_risk_factor(name: str) -> RiskFactor:
    rf = RiskFactor(name, "EQ", "SPOT", "USD", True, "GBM")
    rf.model.calibration = {"initial_value": 100.0, "drift": 0.0, "volatility": 0.2}
    return rf


def _hw1f_risk_factor(name: str) -> RiskFactor:
    rf = RiskFactor(name, "IR", "YIELD_CURVE", "MXN", True, "HW1F")
    rf.model.calibration = {"alpha": ALPHA, "volatility": 0.01}
    rf.model.instantaneous_forward_rate = np.zeros_like
    return rf


def _simulate(scheduled=None, jumps=None):
    risk_factors = [_gbm_risk_factor("A"), _hw1f_risk_factor("R")]
    correlation = CorrelationMatrix(correlation_matrix=np.eye(2), underlyings=["A", "R"])
    engine = MultiRiskFactorSimulation(risk_factors, correlation)
    parameters = {"n_paths": 64, "random_state": SEED}
    if scheduled is not None:
        parameters["scheduled_shocks"] = scheduled
    if jumps is not None:
        parameters["climate_jumps"] = jumps
    return engine.generate_scenarios(DATES, parameters)


@pytest.mark.integration
def test_scheduled_shocks_shift_paths_by_exactly_the_scenario_and_consume_no_rng():
    rate = (np.array([0.0, 0.4, 1.3, 2.8]), np.array([0.0, 0.011, 0.023, 0.007]))
    equity = (np.array([0.0, 1.0, 2.0]), np.array([0.00, -0.02, -0.05]))
    baseline = _simulate()
    shocked = _simulate(scheduled=_overlay(rate=rate, equity=equity))

    # The difference IS the scenario: rates shift additively by the pinned
    # delta path, equity multiplicatively by exp of the pinned log path —
    # identically on every MC path, so the diffusion draws were untouched.
    np.testing.assert_allclose(
        shocked["R"] - baseline["R"],
        np.broadcast_to(_pinned(*rate), baseline["R"].shape),
        rtol=1e-12,
        atol=1e-15,
    )
    np.testing.assert_allclose(
        shocked["A"] / baseline["A"],
        np.broadcast_to(np.exp(_pinned(*equity)), baseline["A"].shape),
        rtol=1e-12,
    )


@pytest.mark.integration
def test_scheduled_shocks_compose_with_the_jump_channel():
    equity = (np.array([0.0, 2.0]), np.array([0.0, -0.03]))
    jumps = ClimateJumpProcess(2.0, {"A": DeterministicMark(-0.10)})
    jumped = _simulate(jumps=jumps)
    both = _simulate(scheduled=_overlay(equity=equity), jumps=jumps)

    # The scheduled overlay multiplies on top of the jumped paths; the jump
    # stream itself is untouched by the deterministic channel.
    np.testing.assert_allclose(
        both["A"] / jumped["A"],
        np.broadcast_to(np.exp(_pinned(*equity)), jumped["A"].shape),
        rtol=1e-12,
    )
    np.testing.assert_array_equal(both["R"], jumped["R"])


@pytest.mark.integration
def test_partial_overlay_applies_to_the_simulated_subset():
    # A book-wide fragment names factors this netting set does not hold: the
    # overlay applies to what IS simulated and skips the rest (the
    # jump-channel skip; supersedes the INT-33 per-target fail-loud, which is
    # unworkable at per-NAID grain — pipelines/01 runs the book one netting
    # set at a time). Zero RNG either way, so no stream to keep stable.
    equity = (np.array([0.0, 2.0]), np.array([0.0, -0.03]))
    block = {
        "equity_shocks": {
            "targets": ["A", "NOT_IN_PORTFOLIO"],
            "times_years": [0.0, 2.0],
            "log_factors": {"A": [0.0, -0.03], "NOT_IN_PORTFOLIO": [0.0, -0.5]},
        }
    }
    baseline = _simulate()
    shocked = _simulate(scheduled=ScheduledShockOverlay.from_config(block))
    np.testing.assert_allclose(
        shocked["A"] / baseline["A"],
        np.broadcast_to(np.exp(_pinned(*equity)), baseline["A"].shape),
        rtol=1e-12,
    )
    np.testing.assert_array_equal(shocked["R"], baseline["R"])


@pytest.mark.integration
def test_overlay_touching_nothing_simulated_is_a_loud_config_error():
    block = {
        "equity_shocks": {
            "targets": ["NOT_IN_PORTFOLIO"],
            "times_years": [0.0, 1.0],
            "log_factors": {"NOT_IN_PORTFOLIO": [0.0, -0.01]},
        }
    }
    with pytest.raises(ValueError, match="no overlay target"):
        _simulate(scheduled=ScheduledShockOverlay.from_config(block))


@pytest.mark.integration
def test_rate_shocks_on_a_model_without_alpha_are_a_loud_config_error():
    block = {
        "rate_shocks": {
            "targets": ["A"],  # A is a GBM — no mean reversion
            "times_years": [0.0, 1.0],
            "deltas": {"A": [0.0, 0.01]},
        }
    }
    with pytest.raises(ValueError, match="no mean-reversion"):
        _simulate(scheduled=ScheduledShockOverlay.from_config(block))
