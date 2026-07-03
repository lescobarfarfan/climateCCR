"""Unit tests for the climate jump-injection channel (DC-CCR-SIM-2, INT-10).

Covers the compound-Poisson generator (shared event times, reproducible
substream), the per-diffusion overlays (GBM multiplicative, HW1F mean-reverting),
and the MultiRiskFactorSimulation wiring — in particular the load-bearing
property that switching jumps on leaves the diffusion draws bit-for-bit
unchanged (INT-09, GEN-07).
"""

from datetime import datetime

import numpy as np
import pytest
from climateCCR.processes.diffusions.geometric_brownian_motion import GeometricBrownianMotion
from climateCCR.processes.diffusions.hw1f import HW1F
from climateCCR.processes.jumps import (
    ClimateJumpProcess,
    DeterministicMark,
    GaussianMark,
    LognormalMark,
)
from climateCCR.simulation.correlation_matrix import CorrelationMatrix
from climateCCR.simulation.multi_risk_factor_simulation import MultiRiskFactorSimulation
from climateCCR.simulation.risk_factor import RiskFactor
from climateCCR.utils.calendar_utils import transform_dates_to_time_differences

SEED = 233423
DATES = [datetime(2020, 1, 1), datetime(2021, 1, 1), datetime(2022, 1, 1), datetime(2023, 1, 1)]


def _gbm_risk_factor(name: str) -> RiskFactor:
    rf = RiskFactor(name, "EQ", "SPOT", "USD", True, "GBM")
    rf.model.calibration = {"initial_value": 100.0, "drift": 0.0, "volatility": 0.2}
    return rf


# ---------------------------------------------------------------------------
# Mark samplers
# ---------------------------------------------------------------------------


def test_deterministic_mark_is_constant():
    rng = np.random.default_rng(0)
    np.testing.assert_array_equal(DeterministicMark(-0.05).sample(rng, 4), np.full(4, -0.05))


def test_lognormal_mark_sign_and_median():
    rng = np.random.default_rng(0)
    draws = LognormalMark(median=0.04, sigma=0.7, sign=-1.0).sample(rng, 20_000)
    assert np.all(draws < 0)
    np.testing.assert_allclose(np.median(-draws), 0.04, rtol=0.05)


def test_gaussian_mark_moments():
    rng = np.random.default_rng(0)
    draws = GaussianMark(mean=0.002, std=0.001).sample(rng, 50_000)
    np.testing.assert_allclose(draws.mean(), 0.002, rtol=0.05)
    np.testing.assert_allclose(draws.std(), 0.001, rtol=0.05)


def test_mark_validation():
    with pytest.raises(ValueError):
        LognormalMark(median=-0.01, sigma=0.5)
    with pytest.raises(ValueError):
        LognormalMark(median=0.01, sigma=0.5, sign=2.0)
    with pytest.raises(ValueError):
        GaussianMark(mean=0.0, std=-1.0)


# ---------------------------------------------------------------------------
# ClimateJumpProcess
# ---------------------------------------------------------------------------


def test_zero_intensity_yields_no_events():
    process = ClimateJumpProcess(0.0, {"A": DeterministicMark(-0.1)})
    scenario = process.generate(DATES, n_paths=16, master_seed=SEED)
    assert scenario.event_counts.sum() == 0
    np.testing.assert_array_equal(scenario.step_marks["A"], 0.0)


def test_same_seed_reproduces_scenario():
    process = ClimateJumpProcess(2.0, {"A": LognormalMark(0.04, 0.7)})
    first = process.generate(DATES, n_paths=32, master_seed=SEED)
    second = process.generate(DATES, n_paths=32, master_seed=SEED)
    np.testing.assert_array_equal(first.event_counts, second.event_counts)
    np.testing.assert_array_equal(first.step_marks["A"], second.step_marks["A"])


def test_shared_event_times_across_targets():
    process = ClimateJumpProcess(3.0, {"A": DeterministicMark(-0.1), "B": DeterministicMark(0.005)})
    scenario = process.generate(DATES, n_paths=64, master_seed=SEED)
    # With deterministic marks the summed mark must be count * mark for BOTH
    # targets — same arrival stream, per-target impacts.
    np.testing.assert_allclose(scenario.step_marks["A"], scenario.event_counts * -0.1)
    np.testing.assert_allclose(scenario.step_marks["B"], scenario.event_counts * 0.005)


def test_expected_event_count_matches_intensity():
    process = ClimateJumpProcess(0.5, {"A": DeterministicMark(-0.1)})
    scenario = process.generate(DATES, n_paths=20_000, master_seed=SEED)
    horizon_years = transform_dates_to_time_differences(DATES[0], DATES)[-1]
    mean_events = scenario.event_counts.sum(axis=1).mean()
    np.testing.assert_allclose(mean_events, 0.5 * horizon_years, rtol=0.05)


def test_trajectory_and_cox_intensity_shapes():
    n_steps = len(DATES) - 1
    trajectory = ClimateJumpProcess(np.linspace(0.5, 2.0, n_steps), {"A": DeterministicMark(-0.1)})
    assert trajectory.generate(DATES, 8, SEED).event_counts.shape == (8, n_steps)

    cox_paths = np.full((8, n_steps), 1.5)
    cox = ClimateJumpProcess(cox_paths, {"A": DeterministicMark(-0.1)})
    assert cox.generate(DATES, 8, SEED).event_counts.shape == (8, n_steps)

    with pytest.raises(ValueError):
        ClimateJumpProcess(np.ones(n_steps + 1), {"A": DeterministicMark(-0.1)}).generate(
            DATES, 8, SEED
        )
    with pytest.raises(ValueError):
        ClimateJumpProcess(np.ones((4, n_steps)), {"A": DeterministicMark(-0.1)}).generate(
            DATES, 8, SEED
        )


def test_non_independent_dependence_is_explicitly_unimplemented():
    with pytest.raises(NotImplementedError):
        ClimateJumpProcess(1.0, {"A": DeterministicMark(-0.1)}, diffusion_dependence="correlated")
    with pytest.raises(NotImplementedError):
        ClimateJumpProcess(1.0, {"A": DeterministicMark(-0.1)}, mark_dependence="comonotone")
    with pytest.raises(ValueError):
        ClimateJumpProcess(1.0, {})
    with pytest.raises(ValueError):
        ClimateJumpProcess(-1.0, {"A": DeterministicMark(-0.1)}).generate(DATES, 8, SEED)


# ---------------------------------------------------------------------------
# Per-diffusion overlays
# ---------------------------------------------------------------------------


def test_gbm_overlay_is_multiplicative_in_log():
    model = GeometricBrownianMotion("A")
    paths = np.full((2, len(DATES)), 100.0)
    step_marks = np.zeros((2, len(DATES) - 1))
    step_marks[0, 1] = -0.10  # one event on path 0, landing at date index 2
    jumped = model.apply_jump_overlay(paths, step_marks, DATES)

    np.testing.assert_array_equal(jumped[1], paths[1])  # untouched path
    np.testing.assert_array_equal(jumped[0, :2], paths[0, :2])  # before the event
    np.testing.assert_allclose(jumped[0, 2:], 100.0 * np.exp(-0.10))  # after, permanently
    np.testing.assert_array_equal(paths, 100.0)  # input not mutated


def test_hw1f_overlay_decays_with_mean_reversion():
    model = HW1F("R")
    alpha = 0.5
    model.calibration = {"alpha": alpha, "volatility": 0.01}
    times = transform_dates_to_time_differences(DATES[0], DATES)
    paths = np.zeros((2, len(DATES)))
    step_marks = np.zeros((2, len(DATES) - 1))
    step_marks[0, 0] = 0.0050  # +50 bp landing at date index 1
    jumped = model.apply_jump_overlay(paths, step_marks, DATES)

    np.testing.assert_array_equal(jumped[1], 0.0)
    assert jumped[0, 0] == 0.0
    expected = 0.0050 * np.exp(-alpha * (times[1:] - times[1]))
    np.testing.assert_allclose(jumped[0, 1:], expected)


def test_base_evolution_rejects_overlay():
    from climateCCR.processes.diffusions.brownian_motion import BrownianMotion

    with pytest.raises(NotImplementedError):
        BrownianMotion("X").apply_jump_overlay(np.zeros((1, 2)), np.zeros((1, 1)), DATES[:2])


# ---------------------------------------------------------------------------
# MultiRiskFactorSimulation wiring
# ---------------------------------------------------------------------------


def _simulate(jump_process=None):
    risk_factors = [_gbm_risk_factor("A"), _gbm_risk_factor("B")]
    correlation = CorrelationMatrix(correlation_matrix=np.eye(2), underlyings=["A", "B"])
    engine = MultiRiskFactorSimulation(risk_factors, correlation)
    parameters = {"n_paths": 64, "random_state": SEED}
    if jump_process is not None:
        parameters["climate_jumps"] = jump_process
    return engine.generate_scenarios(DATES, parameters)


@pytest.mark.integration
def test_jump_on_changes_only_the_climate_component():
    baseline = _simulate()
    process = ClimateJumpProcess(2.0, {"A": DeterministicMark(-0.10)})
    jumped = _simulate(process)

    # The non-target factor is bit-for-bit unchanged: the jump draw lives on its
    # own substream and never touches the diffusion stream (INT-09, GEN-07).
    np.testing.assert_array_equal(jumped["B"], baseline["B"])

    # The target factor differs exactly by the overlay of the (reproducible)
    # jump scenario — the diffusive component is identical.
    scenario = process.generate(DATES, 64, SEED)
    log_jumps = np.cumsum(scenario.step_marks["A"], axis=1)
    log_jumps = np.concatenate((np.zeros((64, 1)), log_jumps), axis=1)
    np.testing.assert_allclose(jumped["A"], baseline["A"] * np.exp(log_jumps))
    assert scenario.event_counts.sum() > 0  # the test exercised real shocks


@pytest.mark.integration
def test_targets_not_simulated_by_this_portfolio_are_skipped():
    baseline = _simulate()
    process = ClimateJumpProcess(2.0, {"NOT_IN_PORTFOLIO": DeterministicMark(-0.10)})
    jumped = _simulate(process)
    np.testing.assert_array_equal(jumped["A"], baseline["A"])
    np.testing.assert_array_equal(jumped["B"], baseline["B"])
