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


def _jump_config(target_scales: dict | None) -> dict:
    block = {
        "median": 0.006864,
        "sigma": 1.2106,
        "sign": -1.0,
        "targets": ["A_SHARE", "B_SHARE", "C_SHARE"],
    }
    if target_scales is not None:
        block["target_scales"] = target_scales
    return {"intensity": 3.0, "equity_marks": block}


def test_target_scales_rescale_marks_exactly():
    # OQ-INT-11 mechanism proof: scaling a lognormal median by gamma multiplies
    # every mark by gamma under the same seed — event counts and the draws of
    # every other target are untouched.
    gammas = {"A_SHARE": 2.5, "C_SHARE": 0.25}
    uniform = ClimateJumpProcess.from_config(_jump_config(None)).generate(DATES, 64, SEED)
    scaled = ClimateJumpProcess.from_config(_jump_config(gammas)).generate(DATES, 64, SEED)
    np.testing.assert_array_equal(uniform.event_counts, scaled.event_counts)
    np.testing.assert_allclose(scaled.step_marks["A_SHARE"], 2.5 * uniform.step_marks["A_SHARE"])
    np.testing.assert_allclose(scaled.step_marks["C_SHARE"], 0.25 * uniform.step_marks["C_SHARE"])
    np.testing.assert_array_equal(scaled.step_marks["B_SHARE"], uniform.step_marks["B_SHARE"])


def test_target_scales_absent_or_unity_is_uniform():
    uniform = ClimateJumpProcess.from_config(_jump_config(None)).generate(DATES, 32, SEED)
    unity = ClimateJumpProcess.from_config(
        _jump_config({"A_SHARE": 1.0, "B_SHARE": 1.0, "C_SHARE": 1.0})
    ).generate(DATES, 32, SEED)
    for name in ("A_SHARE", "B_SHARE", "C_SHARE"):
        np.testing.assert_array_equal(uniform.step_marks[name], unity.step_marks[name])


def test_target_scales_unknown_target_raises():
    with pytest.raises(ValueError, match="TYPO_SHARE"):
        ClimateJumpProcess.from_config(_jump_config({"TYPO_SHARE": 1.5}))


# ---------------------------------------------------------------------------
# Peril-typed events (OQ-INT-11 Phase B)
# ---------------------------------------------------------------------------


def _peril_config(mix: dict, scales: dict, sigma: float = 1.2106) -> dict:
    return {
        "intensity": 3.0,
        "equity_marks": {
            "median": 0.006864,
            "sigma": sigma,
            "sign": -1.0,
            "targets": sorted(scales),
            "peril_mix": mix,
            "target_peril_scales": scales,
        },
    }


def test_peril_typing_preserves_event_counts():
    # The label draw happens after the Poisson counts, so arrivals are identical
    # with typing on or off under the same master seed.
    uniform = ClimateJumpProcess.from_config(_jump_config(None)).generate(DATES, 64, SEED)
    typed = ClimateJumpProcess.from_config(
        _peril_config(
            {"hidro": 1.0}, {n: {"hidro": 1.0} for n in ("A_SHARE", "B_SHARE", "C_SHARE")}
        )
    ).generate(DATES, 64, SEED)
    np.testing.assert_array_equal(uniform.event_counts, typed.event_counts)


def test_zero_susceptibility_masks_all_events():
    # "Only susceptible sectors take the hit": c = 0 -> the name never moves,
    # even though events arrive and hit the other target.
    scenario = ClimateJumpProcess.from_config(
        _peril_config({"hidro": 1.0}, {"A_SHARE": {"hidro": 0.0}, "B_SHARE": {"hidro": 2.0}})
    ).generate(DATES, 64, SEED)
    assert scenario.event_counts.sum() > 0
    np.testing.assert_array_equal(scenario.step_marks["A_SHARE"], 0.0)
    assert np.any(scenario.step_marks["B_SHARE"] != 0.0)


def test_peril_labels_are_shared_and_exhaustive():
    # sigma=0 makes the base draw the constant -median, so marks reveal the
    # labels: complementary c rows must tile every event exactly once (X takes
    # a-events, Y takes b-events, together every event), and the realized label
    # frequencies must match the declared mix.
    scenario = ClimateJumpProcess.from_config(
        _peril_config(
            {"a": 0.75, "b": 0.25},
            {"X_SHARE": {"a": 1.0, "b": 0.0}, "Y_SHARE": {"a": 0.0, "b": 1.0}},
            sigma=0.0,
        )
    ).generate(DATES, n_paths=2_000, master_seed=SEED)
    total = scenario.step_marks["X_SHARE"] + scenario.step_marks["Y_SHARE"]
    np.testing.assert_allclose(total, -0.006864 * scenario.event_counts)
    assert scenario.event_counts.sum() > 1_000
    share_a = scenario.step_marks["X_SHARE"].sum() / total.sum()
    np.testing.assert_allclose(share_a, 0.75, rtol=0.05)


def test_peril_typed_mean_matches_anchor_identity():
    # sum_p pi_p c_ip is the name's flat gamma: with sigma=0 the realized mean
    # mark per event converges to -median * gamma (the Phase A per-name mean).
    mix = {"a": 0.5, "b": 0.5}
    scales = {"Z_SHARE": {"a": 2.0, "b": 0.5}}  # gamma = 1.25
    scenario = ClimateJumpProcess.from_config(_peril_config(mix, scales, sigma=0.0)).generate(
        DATES, n_paths=2_000, master_seed=SEED
    )
    mean_per_event = scenario.step_marks["Z_SHARE"].sum() / scenario.event_counts.sum()
    np.testing.assert_allclose(mean_per_event, -0.006864 * 1.25, rtol=0.02)


def test_peril_config_validation():
    good_mix = {"a": 0.5, "b": 0.5}
    good_scales = {"A_SHARE": {"a": 1.0, "b": 1.0}}

    config = _peril_config(good_mix, good_scales)
    del config["equity_marks"]["target_peril_scales"]
    with pytest.raises(ValueError, match="both-or-neither"):
        ClimateJumpProcess.from_config(config)

    config = _peril_config(good_mix, good_scales)
    config["equity_marks"]["target_scales"] = {"A_SHARE": 1.5}
    with pytest.raises(ValueError, match="mutually"):
        ClimateJumpProcess.from_config(config)

    both = {"A_SHARE": {"a": 1.0, "b": 1.0}, "TYPO_SHARE": {"a": 1.0, "b": 1.0}}
    config = _peril_config(good_mix, both)
    config["equity_marks"]["targets"] = ["A_SHARE"]
    with pytest.raises(ValueError, match="TYPO_SHARE"):
        ClimateJumpProcess.from_config(config)

    with pytest.raises(ValueError, match="sum to 1"):
        ClimateJumpProcess.from_config(_peril_config({"a": 0.5, "b": 0.4}, good_scales))

    with pytest.raises(ValueError, match="groups"):
        ClimateJumpProcess.from_config(_peril_config(good_mix, {"A_SHARE": {"a": 1.0}}))

    with pytest.raises(ValueError, match=">= 0"):
        ClimateJumpProcess.from_config(_peril_config(good_mix, {"A_SHARE": {"a": -1.0, "b": 1.0}}))

    config = _peril_config(good_mix, good_scales)
    config["rate_marks"] = {
        "median": 1e-6,
        "sigma": 1.0,
        "sign": 1.0,
        "targets": ["CURVE"],
        "peril_mix": good_mix,
        "target_peril_scales": {"CURVE": {"a": 1.0, "b": 1.0}},
    }
    with pytest.raises(ValueError, match="one channel"):
        ClimateJumpProcess.from_config(config)


def test_peril_severity_pooled_params_reproduce_phase_b_bitwise():
    # The load-bearing seam property: a peril_severity block carrying the pooled
    # (median, sigma) in every label consumes the same draws and produces the
    # same marks as no block at all — the refinement is purely additive.
    mix = {"a": 0.6, "b": 0.4}
    scales = {"X_SHARE": {"a": 2.0, "b": 0.5}, "Y_SHARE": {"a": 0.0, "b": 1.5}}
    plain = ClimateJumpProcess.from_config(_peril_config(mix, scales)).generate(DATES, 64, SEED)
    config = _peril_config(mix, scales)
    config["equity_marks"]["peril_severity"] = {
        g: {"median": 0.006864, "sigma": 1.2106} for g in mix
    }
    typed = ClimateJumpProcess.from_config(config).generate(DATES, 64, SEED)
    np.testing.assert_array_equal(plain.event_counts, typed.event_counts)
    for name in scales:
        np.testing.assert_array_equal(plain.step_marks[name], typed.step_marks[name])


def test_peril_severity_selects_params_by_label():
    # sigma=0 per-label severity makes marks reveal which label's parameters
    # each event drew: complementary c rows must tile every event with the
    # label's own median.
    mix = {"a": 0.5, "b": 0.5}
    scales = {"X_SHARE": {"a": 1.0, "b": 0.0}, "Y_SHARE": {"a": 0.0, "b": 1.0}}
    config = _peril_config(mix, scales)
    config["equity_marks"]["peril_severity"] = {
        "a": {"median": 0.01, "sigma": 0.0},
        "b": {"median": 0.04, "sigma": 0.0},
    }
    scenario = ClimateJumpProcess.from_config(config).generate(DATES, 2_000, SEED)
    a_events = scenario.step_marks["X_SHARE"] / -0.01
    b_events = scenario.step_marks["Y_SHARE"] / -0.04
    np.testing.assert_allclose(a_events + b_events, scenario.event_counts)
    assert a_events.sum() > 0 and b_events.sum() > 0


def test_peril_severity_mean_matched_preserves_per_name_mean():
    # Mean-matched labels (E[L_p] = E[L] via median_p = median * exp((s2-sp2)/2))
    # leave the per-name expected mark at -median * exp(sigma^2/2) * gamma — the
    # Phase A/B level — while the conditional shape differs by label.
    base_sigma = 0.8
    mix = {"a": 0.5, "b": 0.5}
    scales = {"Z_SHARE": {"a": 1.0, "b": 1.0}}
    config = _peril_config(mix, scales, sigma=base_sigma)
    config["equity_marks"]["peril_severity"] = {
        "a": {"median": 0.006864 * np.exp((base_sigma**2 - 0.4**2) / 2), "sigma": 0.4},
        "b": {"median": 0.006864 * np.exp((base_sigma**2 - 1.2**2) / 2), "sigma": 1.2},
    }
    scenario = ClimateJumpProcess.from_config(config).generate(DATES, 6_000, SEED)
    mean_per_event = scenario.step_marks["Z_SHARE"].sum() / scenario.event_counts.sum()
    np.testing.assert_allclose(mean_per_event, -0.006864 * np.exp(base_sigma**2 / 2), rtol=0.05)


def test_peril_severity_validation():
    mix = {"a": 0.5, "b": 0.5}
    scales = {"A_SHARE": {"a": 1.0, "b": 1.0}}

    config = _jump_config(None)
    config["equity_marks"]["peril_severity"] = {"a": {"median": 0.01, "sigma": 0.5}}
    with pytest.raises(ValueError, match="requires peril_mix"):
        ClimateJumpProcess.from_config(config)

    config = _peril_config(mix, scales)
    config["equity_marks"]["peril_severity"] = {"a": {"median": 0.01, "sigma": 0.5}}
    with pytest.raises(ValueError, match="groups"):
        ClimateJumpProcess.from_config(config)

    config = _peril_config(mix, scales)
    config["equity_marks"]["peril_severity"] = {
        "a": {"median": -0.01, "sigma": 0.5},
        "b": {"median": 0.01, "sigma": 0.5},
    }
    with pytest.raises(ValueError, match="median > 0"):
        ClimateJumpProcess.from_config(config)

    with pytest.raises(ValueError, match="LognormalMark"):
        ClimateJumpProcess(
            1.0,
            {"A": DeterministicMark(-0.1)},
            peril_mix={"a": 1.0},
            target_peril_scales={"A": {"a": 1.0}},
            peril_severity={"a": {"median": 0.01, "sigma": 0.5}},
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
