"""Known-answer tests for the backtesting statistics (risk.market.backtest, INT-40)."""

from __future__ import annotations

import numpy as np
import pytest
from climateCCR.risk.market import (
    berkowitz_lr,
    central_coverage,
    christoffersen_cc,
    christoffersen_independence,
    coverage_by_percentile,
    crps_from_samples,
    crps_normal,
    diebold_mariano,
    ks_uniform,
    kupiec_pof,
    log_score_mixture,
    log_score_normal,
    pit_discrete,
    pit_normal,
    pit_values,
)


def test_kupiec_matches_hand_computed_likelihood_ratio():
    # 10 exceptions in 250 days at 1 %: LR = -2 [10 ln .01 + 240 ln .99 - 10 ln .04 - 240 ln .96]
    res = kupiec_pof(10, 250, 0.01)
    expected = -2.0 * (
        10 * np.log(0.01) + 240 * np.log(0.99) - 10 * np.log(0.04) - 240 * np.log(0.96)
    )
    assert res.statistic == pytest.approx(expected, rel=1e-12)
    assert res.statistic == pytest.approx(12.955, abs=1e-3)
    assert res.p_value < 1e-3 and res.df == 1 and res.n == 250


def test_kupiec_is_zero_at_the_nominal_rate_and_validates():
    assert kupiec_pof(50, 1000, 0.05).statistic == 0.0
    assert kupiec_pof(0, 100, 0.01).p_value > 0.1  # zero exceptions is consistent with 1 %
    with pytest.raises(ValueError):
        kupiec_pof(5, 4, 0.01)


def test_christoffersen_rejects_clustered_and_accepts_independent_hits():
    clustered = np.array([1] * 10 + [0] * 240)
    assert christoffersen_independence(clustered).p_value < 1e-3
    rng = np.random.default_rng(3)
    iid = (rng.uniform(size=5000) < 0.05).astype(int)
    assert christoffersen_independence(iid).p_value > 0.05
    # Conditional coverage = POF + independence (chi2(2)); at the realised hit rate
    # the POF term vanishes and only the independence evidence remains.
    cc = christoffersen_cc(iid, 0.05)
    assert cc.df == 2
    assert cc.statistic == pytest.approx(
        kupiec_pof(int(iid.sum()), iid.size, 0.05).statistic
        + christoffersen_independence(iid).statistic
    )
    at_realised = christoffersen_cc(iid, float(iid.mean()))
    assert at_realised.statistic == pytest.approx(christoffersen_independence(iid).statistic)
    assert at_realised.p_value > 0.05


def test_pit_normal_whole_distribution_tests_pass_true_model_and_fail_misscaled():
    rng = np.random.default_rng(11)
    y = rng.standard_normal(2000)
    good = pit_normal(y, np.zeros_like(y), np.ones_like(y))
    assert ks_uniform(good).p_value > 0.05
    assert berkowitz_lr(good).p_value > 0.05
    bad = pit_normal(y, np.zeros_like(y), 1.5 * np.ones_like(y))  # too wide a forecast
    assert ks_uniform(bad).p_value < 1e-3
    assert berkowitz_lr(bad).p_value < 1e-3
    assert berkowitz_lr(bad).df == 3


def test_coverage_tables_are_exact_on_a_uniform_grid():
    n = 1000
    pit = (np.arange(n) + 0.5) / n
    table = coverage_by_percentile(pit, probs=(0.05, 0.5, 0.95))
    assert list(table.columns) == ["nominal", "empirical", "n", "binom_se"]
    np.testing.assert_allclose(table["empirical"], table["nominal"], atol=1.0 / n)
    assert table["binom_se"].iloc[1] == pytest.approx(np.sqrt(0.25 / n))
    central = central_coverage(pit, levels=(0.5, 0.95))
    np.testing.assert_allclose(central["empirical"], central["nominal"], atol=2.0 / n)
    with pytest.raises(ValueError):
        coverage_by_percentile(pit, probs=(0.0,))


def test_pit_values_reads_sample_quantiles_and_splits_ties():
    samples = np.tile(np.linspace(0.0, 1.0, 1001)[:, None], (1, 2))
    pit = pit_values(samples, [0.3, 0.9])
    np.testing.assert_allclose(pit, [0.3, 0.9], atol=1e-3)
    atom = np.zeros((100, 1))
    assert pit_values(atom, [0.0])[0] == pytest.approx(0.5)  # midpoint of the tie mass
    assert pit_discrete([0.6], [0.2])[0] == pytest.approx(0.4)
    rng = np.random.default_rng(0)
    assert 0.2 <= pit_discrete([0.6], [0.2], rng)[0] <= 0.6
    with pytest.raises(ValueError):
        pit_values(samples, [0.3])


def test_crps_sample_form_matches_closed_form_and_point_mass():
    rng = np.random.default_rng(5)
    y = np.array([-1.0, 0.0, 2.0])
    samples = rng.standard_normal((40_000, 3))
    sampled = crps_from_samples(samples, y)
    closed = crps_normal(y, np.zeros(3), np.ones(3))
    np.testing.assert_allclose(sampled, closed, rtol=0.02)
    point_mass = np.full((50, 1), 1.5)
    assert crps_from_samples(point_mass, [-0.5])[0] == pytest.approx(2.0)


def test_log_score_mixture_with_zero_shifts_is_the_normal_log_score():
    y = np.array([-0.3, 0.4, 1.2])
    mean, sd = np.array([0.1, 0.1, 0.1]), np.array([0.5, 0.5, 0.5])
    np.testing.assert_allclose(
        log_score_mixture(y, np.zeros(8), mean, sd), log_score_normal(y, mean, sd), rtol=1e-12
    )
    # A downward jump mass lowers the score of an upward realisation.
    shifted = log_score_mixture(y, np.full(8, -0.8), mean, sd)
    assert shifted[2] < log_score_normal(y, mean, sd)[2]


def test_diebold_mariano_scales_with_the_mean_differential():
    rng = np.random.default_rng(21)
    n, delta = 400, 0.5
    signal = diebold_mariano(delta + rng.standard_normal(n))
    assert 7.0 < signal.statistic < 13.0  # ~ delta * sqrt(n) = 10
    assert signal.p_value < 1e-6
    noise = diebold_mariano(rng.standard_normal(n), lag=2)
    assert abs(noise.statistic) < 3.0
    with pytest.raises(ValueError):
        diebold_mariano(np.ones(10))  # zero long-run variance
