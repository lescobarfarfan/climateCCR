"""CVA reporting-seam correctness (OQ-CCR-04): survival bootstrap, the Gregory
discretization, the exact scenario decomposition, and the credit triangle."""

import numpy as np
import pytest
from climateCCR.risk.ccr.xva import (
    cva_decomposition,
    cva_unilateral,
    implied_pd_from_spread,
    survival_from_annual_pd,
)
from numpy.testing import assert_allclose


def test_cva_matches_hand_computed_toy():
    grid_df = np.exp(-0.03 * np.array([0.0, 1.0, 2.0]))
    ee = np.array([100.0, 100.0, 100.0])
    surv = np.array([1.0, 0.98, 0.9604])  # flat 2% annual PD
    discounted = ee * grid_df
    hand = 0.6 * (
        0.5 * (discounted[0] + discounted[1]) * 0.02
        + 0.5 * (discounted[1] + discounted[2]) * (0.98 - 0.9604)
    )
    assert_allclose(cva_unilateral(ee, grid_df, surv, lgd=0.6), hand, rtol=1e-14)


def test_cva_zero_exposure_is_zero():
    df = np.exp(-0.05 * np.arange(4.0))
    surv = 0.97 ** np.arange(4.0)
    assert cva_unilateral(np.zeros(4), df, surv) == 0.0


def test_survival_flat_pd_is_geometric():
    starts = np.arange(0.0, 6.0)
    surv = survival_from_annual_pd(starts, np.full(6, 5.0), np.array([0.0, 0.5, 1.0, 3.0, 5.0]))
    assert_allclose(surv, 0.95 ** np.array([0.0, 0.5, 1.0, 3.0, 5.0]), rtol=1e-12)


def test_survival_extends_flat_beyond_last_segment():
    surv = survival_from_annual_pd(np.array([0.0, 1.0]), np.array([1.0, 4.0]), np.array([5.0]))
    expected = np.exp(-(-np.log(0.99) - 4.0 * np.log(0.96)))
    assert_allclose(surv[0], expected, rtol=1e-12)


def test_survival_flat_back_before_first_segment():
    # valuation sits mid-calendar-year: the first listed year start is 0.46y away
    surv = survival_from_annual_pd(
        np.array([0.46, 1.46]), np.array([10.0, 20.0]), np.array([0.2, 0.46])
    )
    lam1 = -np.log(0.90)
    assert_allclose(surv, np.exp(-lam1 * np.array([0.2, 0.46])), rtol=1e-12)


def test_decomposition_is_exact_and_interaction_is_the_cross_term():
    df = np.exp(-0.08 * np.array([0.0, 0.5, 1.0, 2.0, 5.0]))
    ee_b = np.array([40.0, 42.0, 45.0, 30.0, 5.0])
    ee_s = np.array([40.0, 38.0, 36.0, 22.0, 2.0])
    grid = np.array([0.0, 0.5, 1.0, 2.0, 5.0])
    s_b = survival_from_annual_pd(np.arange(0.0, 6.0), np.full(6, 11.55), grid)
    s_s = survival_from_annual_pd(np.arange(0.0, 6.0), np.full(6, 19.0), grid)
    out = cva_decomposition(ee_b, ee_s, s_b, s_s, df, lgd=0.6)
    assert_allclose(
        out["cva_delta"],
        out["exposure_channel"] + out["credit_channel"] + out["interaction"],
        rtol=1e-14,
    )
    d_disc = (ee_s - ee_b) * df
    d_pd = -np.diff(s_s) - (-np.diff(s_b))
    cross = 0.6 * np.sum(0.5 * (d_disc[:-1] + d_disc[1:]) * d_pd)
    assert_allclose(out["interaction"], cross, rtol=1e-12)


def test_cva_is_linear_in_lgd():
    df = np.exp(-0.06 * np.arange(3.0))
    ee = np.array([10.0, 20.0, 5.0])
    surv = np.array([1.0, 0.9, 0.85])
    mid = cva_unilateral(ee, df, surv, lgd=0.60)
    lo = cva_unilateral(ee, df, surv, lgd=0.45)
    hi = cva_unilateral(ee, df, surv, lgd=0.75)
    assert_allclose(mid, 0.5 * (lo + hi), rtol=1e-14)
    assert_allclose(lo / 0.45, hi / 0.75, rtol=1e-14)


def test_credit_triangle_roundtrip():
    hazard, pd_1y = implied_pd_from_spread(0.024, recovery=0.40)
    assert_allclose(hazard, 0.04, rtol=1e-14)
    assert_allclose(pd_1y, 1.0 - np.exp(-0.04), rtol=1e-14)
    assert_allclose(hazard * (1.0 - 0.40), 0.024, rtol=1e-14)


def test_cva_input_validation():
    df = np.exp(-0.03 * np.arange(3.0))
    surv = np.array([1.0, 0.95, 0.9])
    with pytest.raises(ValueError):
        cva_unilateral(np.array([1.0, -0.1, 1.0]), df, surv)  # negative EE
    with pytest.raises(ValueError):
        cva_unilateral(np.ones(3), df, np.array([0.9, 0.95, 1.0]))  # increasing survival
    with pytest.raises(ValueError):
        cva_unilateral(np.ones(3), np.array([1.0, 1.2, 0.9]), surv)  # DF > 1
    with pytest.raises(ValueError):
        survival_from_annual_pd(np.array([0.0, 0.0]), np.array([1.0, 2.0]), np.array([1.0]))
