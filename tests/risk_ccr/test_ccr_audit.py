"""OQ-CCR-06 audit tests — lock the numerical internals' correct economics.

Covers the four audited components (IRS pricer, Curve, Surface,
CorrelationMatrix) plus their HW1F bond-reconstruction dependency. The IRS
tests pin the 2026-08-12 corrected semantics under the 2026-08-20 OQ-CCR-10
convention: per-period **Act/360** accrual on every cashflow,
valuation-date-conditional **simple Act/360** forwards (the MKT-SIE-04 TIIE
convention shared with the FRN pricer), and the real previous fixing (with
notional and accrual) on a spliced first period.
"""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from climateCCR.data.market.curve import Curve
from climateCCR.data.market.surface import Surface
from climateCCR.risk.ccr.pricing_models.interest_rate_swap_pricer import InterestRateSwapPricer
from climateCCR.simulation.correlation_matrix import CorrelationMatrix
from climateCCR.simulation.simulated_hw1f_curve import SimulatedHW1FCurve
from climateCCR.utils.calendar_utils import (
    generate_fixings_and_payments_schedule,
    time_step_from_frequency,
    transform_dates_to_time_differences,
)

RATE = 0.03
T0 = datetime(2020, 1, 1)
GP = {"n_paths": 3, "date_format": "%Y-%m-%d"}

# Shape of the real MXN pricing curve (2026-07-17 strip) — values are a test
# fixture here, exercised only as a representative steep-then-flat shape.
MXN_SHAPE = {
    "1D": 0.06580,
    "28D": 0.06832,
    "91D": 0.06829,
    "182D": 0.06825,
    "342D": 0.06777,
    "2Y": 0.07418,
    "3Y": 0.07896,
    "5Y": 0.08605,
    "7Y": 0.09033,
    "10Y": 0.09390,
    "20Y": 0.09821,
    "30Y": 0.09964,
}


def flat_curve(r: float = RATE) -> Curve:
    return Curve({"1D": r, "1Y": r, "10Y": r, "30Y": r})


def flat_calibration(alpha: float = 0.05, sigma: float = 0.01) -> dict:
    return {"alpha": alpha, "volatility": sigma, "rate_curve": flat_curve()}


def make_irs(
    first_fixing: datetime,
    last_fixing: datetime,
    first_payment: datetime,
    last_payment: datetime,
    k: float = 0.02,
    notional: float = 100.0,
    direction: str = "payer",
):
    from climateCCR.risk.ccr.trade_models.interest_rate_swap import InterestRateSwap

    trade = InterestRateSwap("AUDIT")
    fixings, payments = generate_fixings_and_payments_schedule(
        first_fixing, last_fixing, first_payment, last_payment, "quarterly"
    )
    trade.trade_attributes = {
        "notional": notional,
        "currency": "USD",
        "floating_rate": "USD_ZERO_YIELD_CURVE",
        "K": k,
        "payer/receiver": direction,
        "payments_frequency": "quarterly",
        "maturity": payments[-1],
        "fixings_schedule": fixings,
        "payments_schedule": payments,
    }
    trade.trade_underlyings = ["USD_ZERO_YIELD_CURVE"]
    return trade


def make_pricer() -> InterestRateSwapPricer:
    pricer = InterestRateSwapPricer("IRS_Pricer")
    pricer.calibration = {"USD_ZERO_YIELD_CURVE": flat_calibration()}
    return pricer


def scenarios_at(rates: list[float]) -> dict:
    return {"USD_ZERO_YIELD_CURVE": np.tile(np.asarray(rates), (GP["n_paths"], 1))}


# --------------------------------------------------------------------------- IRS


def test_irs_t0_matches_hand_dcf():
    """Fresh at-market-window swap at t=0 equals the static-replication DCF."""
    trade = make_irs(
        T0, datetime(2029, 10, 1), datetime(2020, 4, 3), datetime(2030, 1, 3), direction="receiver"
    )
    mtm = make_pricer().price_single_trade(trade, [T0], scenarios_at([RATE]), {}, GP)

    step = time_step_from_frequency("quarterly")
    fixings = list(trade.get_attribute("fixings_schedule"))
    payments = list(trade.get_attribute("payments_schedule"))
    delta365 = np.array([((d + step) - d).days / 365 for d in fixings])
    delta360 = np.array([((d + step) - d).days / 360 for d in fixings])
    tau_pay = np.array([(d - T0).days / 365 for d in payments])
    # flat cc curve: the simple Act/360 forward satisfies F*delta360 = exp(r*delta365) - 1
    hand = 100.0 * np.sum((np.expm1(RATE * delta365) - 0.02 * delta360) * np.exp(-RATE * tau_pay))
    assert_allclose(mtm[:, 0], -hand, rtol=1e-6)  # receiver receives K, pays floating


def test_irs_future_floating_is_the_conditional_forward():
    """At a future valuation state the floating rate must come from bonds
    conditioned on r(t_val), not from the fixing-date formula — and it is the
    simple Act/360 forward, verbatim the FRN pricer's MKT-SIE-04 convention
    (the OQ-CCR-10 cross-desk alignment)."""
    trade = make_irs(
        datetime(2025, 1, 1),
        datetime(2025, 2, 1),
        datetime(2025, 4, 3),
        datetime(2025, 5, 3),
        direction="payer",
    )
    assert len(trade.get_attribute("payments_schedule")) == 1
    t_val = datetime(2022, 1, 1)
    r_tv = 0.045  # away from the curve so the state-dependence bites
    pricer = make_pricer()
    mtm = pricer.price_single_trade(trade, [T0, t_val], scenarios_at([RATE, r_tv]), {}, GP)

    calib = pricer.calibration["USD_ZERO_YIELD_CURVE"]
    sim = SimulatedHW1FCurve(np.array([r_tv]))
    tv = transform_dates_to_time_differences(T0, t_val)
    fixing = trade.get_attribute("fixings_schedule")[0]
    payment = trade.get_attribute("payments_schedule")[0]
    accrual_end = fixing + time_step_from_frequency("quarterly")
    t_fix = transform_dates_to_time_differences(T0, fixing)
    t_end = transform_dates_to_time_differences(T0, accrual_end)
    t_pay = transform_dates_to_time_differences(T0, payment)

    def bond(T):
        return sim.get_value(
            calibration=calib, t_date=tv, T_date=np.array([T]), initial_date=None, return_log=False
        )[0, 0]

    delta360 = (t_end - t_fix) * 365.0 / 360.0
    forward = (bond(t_fix) / bond(t_end) - 1.0) / delta360
    hand = 100.0 * delta360 * (forward - 0.02) * bond(t_pay)
    assert_allclose(mtm[:, 1], hand, rtol=1e-9)


def test_irs_spliced_first_period_uses_previous_fixing_with_notional_and_accrual():
    """Valuation inside the first period: the running coupon pays the *previous*
    fixing's historical rate, scaled by notional and its own accrual."""
    trade = make_irs(
        datetime(2019, 10, 1),
        datetime(2020, 4, 1),
        datetime(2020, 1, 3),
        datetime(2020, 7, 3),
        direction="payer",
    )
    hist = pd.Series({"2019-10-01": 0.025, "2020-01-01": 0.031, "2020-04-01": 0.028})
    market_data = {"historical_fixings": {"USD_ZERO_YIELD_CURVE": hist}}
    pricer = make_pricer()
    mtm = pricer.price_single_trade(trade, [T0], scenarios_at([RATE]), market_data, GP)

    step = time_step_from_frequency("quarterly")
    payments = list(trade.get_attribute("payments_schedule"))
    residual_fixings = [d for d in trade.get_attribute("fixings_schedule") if d >= T0]
    assert len(residual_fixings) == len(payments) - 1  # the spliced configuration
    tau_pay = np.array([(d - T0).days / 365 for d in payments])
    df = np.exp(-RATE * tau_pay)
    d0_360 = ((datetime(2019, 10, 1) + step) - datetime(2019, 10, 1)).days / 360
    splice = 100.0 * d0_360 * (0.025 - 0.02) * df[0]  # previous fixing, NOT 0.031
    deltas365 = np.array([((d + step) - d).days / 365 for d in residual_fixings])
    deltas360 = np.array([((d + step) - d).days / 360 for d in residual_fixings])
    future = 100.0 * np.sum((np.expm1(RATE * deltas365) - 0.02 * deltas360) * df[1:])
    assert_allclose(mtm[:, 0], splice + future, rtol=1e-6)


def test_irs_payer_receiver_sign_flip():
    kw = dict(
        first_fixing=T0,
        last_fixing=datetime(2024, 10, 1),
        first_payment=datetime(2020, 4, 3),
        last_payment=datetime(2025, 1, 3),
    )
    pricer = make_pricer()
    payer = pricer.price_single_trade(
        make_irs(direction="payer", **kw), [T0], scenarios_at([RATE]), {}, GP
    )
    receiver = pricer.price_single_trade(
        make_irs(direction="receiver", **kw), [T0], scenarios_at([RATE]), {}, GP
    )
    assert_allclose(payer, -receiver, rtol=1e-12)


def test_irs_matured_trade_is_zero():
    trade = make_irs(T0, datetime(2020, 7, 1), datetime(2020, 4, 3), datetime(2020, 10, 3))
    mtm = make_pricer().price_single_trade(
        trade, [T0, datetime(2031, 1, 1)], scenarios_at([RATE, RATE]), {}, GP
    )
    assert np.all(mtm[:, 1] == 0.0)


# ------------------------------------------------------------------------- Curve


def test_curve_flat_discount_factors_and_forward_identity():
    c = flat_curve()
    t = np.array([0.5, 1.0, 5.0, 17.3, 29.0])
    assert_allclose(c.get_interpolated_discount_factor(t), np.exp(-RATE * t), rtol=1e-12)
    f = c.get_interpolated_instantaneous_forward_rate()
    grid = np.linspace(0.01, 29.9, 400)
    assert np.max(np.abs(f(grid) - RATE)) < 1e-7  # < 0.001 bp


def test_curve_flat_extrapolation_beyond_pillars():
    c = Curve(MXN_SHAPE)
    assert_allclose(c.get_interpolated_rates(50.0), MXN_SHAPE["30Y"], rtol=1e-12)
    assert_allclose(c.get_interpolated_rates(1e-5), MXN_SHAPE["1D"], rtol=1e-12)


def test_curve_quadratic_interpolation_stays_within_pillar_envelope():
    """The real MXN 12-pillar shape must not overshoot (audit scan: 0 bp)."""
    c = Curve(MXN_SHAPE)
    dense = c.get_interpolated_rates(np.linspace(1e-3, 30.0, 4000))
    lo, hi = min(MXN_SHAPE.values()), max(MXN_SHAPE.values())
    assert dense.min() >= lo - 1e-4 and dense.max() <= hi + 1e-4  # 1 bp head-room


# ----------------------------------------------------------------------- Surface


def surface_2x2() -> Surface:
    grid = pd.DataFrame([[0.20, 0.30], [0.40, 0.60]], index=[0.9, 1.1], columns=["1M", "1Y"])
    return Surface(grid)


def test_surface_bilinear_known_point_and_shapes():
    s = surface_2x2()
    t_mid = (1 / 12 + 1.0) / 2
    v = s.get_interpolated_surface(1.0, t_mid)
    assert_allclose(v[0], 0.375, rtol=1e-12)  # mean of the four corners
    assert s.get_interpolated_surface(1.0, np.array([0.5, 0.9])).shape == (2,)
    assert_allclose(s.get_interpolated_surface(0.9, 1 / 12)[0], 0.20, rtol=1e-12)


def test_surface_off_grid_queries_clamp_to_the_boundary():
    """RectBivariateSpline evaluates outside the knot span at the boundary —
    the engine's exercised behaviour (fixture option at K/S0 = 1.4): clamped,
    never extrapolated into negative vols."""
    s = surface_2x2()
    assert_allclose(s.get_interpolated_surface(5.0, 30.0)[0], 0.60, rtol=1e-12)
    assert_allclose(s.get_interpolated_surface(0.05, 1e-4)[0], 0.20, rtol=1e-12)
    assert_allclose(s.get_interpolated_surface(1.4, 1.0)[0], 0.60, rtol=1e-12)


def test_surface_unsorted_input_is_sorted_consistently():
    # rows/cols arrive unsorted and the values follow their labels
    grid = pd.DataFrame([[0.60, 0.40], [0.30, 0.20]], index=[1.1, 0.9], columns=["1Y", "1M"])
    shuffled = Surface(grid)
    reference = surface_2x2()
    for k, t in ((0.95, 0.3), (1.05, 0.9), (1.0, 0.5)):
        assert_allclose(
            shuffled.get_interpolated_surface(k, t), reference.get_interpolated_surface(k, t)
        )


# ------------------------------------------------------------- CorrelationMatrix


def test_correlation_rebonato_reconstruction_is_a_valid_correlation():
    bad = np.array([[1.0, 0.9, -0.6], [0.9, 1.0, 0.9], [-0.6, 0.9, 1.0]])
    assert np.linalg.eigvalsh(bad).min() < 0  # genuinely indefinite input
    cm = CorrelationMatrix(correlation_matrix=bad, underlyings=["a", "b", "c"])
    fixed = np.asarray(cm.get_correlation_matrix(), dtype=float)
    assert_allclose(np.diag(fixed), 1.0, atol=1e-12)
    assert np.linalg.eigvalsh(fixed).min() >= -1e-10
    assert np.max(np.abs(fixed)) <= 1.0 + 1e-12
    assert_allclose(fixed, fixed.T, atol=1e-12)


def test_correlation_submatrix_extraction_and_recheck():
    mat = np.array([[1.0, 0.5, 0.2], [0.5, 1.0, 0.4], [0.2, 0.4, 1.0]])
    cm = CorrelationMatrix(correlation_matrix=mat, underlyings=["a", "b", "c"])
    sub = cm.get_sub_correlation_matrix(["a", "c"])
    assert_allclose(np.asarray(sub.get_correlation_matrix(), dtype=float), [[1.0, 0.2], [0.2, 1.0]])
    assert sub.get_value("a", "c") == pytest.approx(0.2)
    with pytest.raises(ValueError):
        cm.get_sub_correlation_matrix(["a", "zzz"])


def test_correlation_asymmetric_raises_and_1x1_is_identity():
    with pytest.raises(ValueError):
        CorrelationMatrix(
            correlation_matrix=np.array([[1.0, 0.5], [0.4, 1.0]]), underlyings=["a", "b"]
        )
    one = CorrelationMatrix(correlation_matrix=np.array([[1.0]]), underlyings=["a"])
    assert one.get_value("a", "a") == 1.0


# -------------------------------------------------------------------------- HW1F


def test_hw1f_t0_reconstructs_the_initial_curve():
    calib = flat_calibration()
    sim = SimulatedHW1FCurve(np.array([RATE]))
    horizons = np.array([0.25, 1.0, 5.0, 10.0])
    p = sim.get_value(
        calibration=calib, t_date=0.0, T_date=horizons, initial_date=None, return_log=False
    )
    assert_allclose(p[0], np.exp(-RATE * horizons), rtol=1e-6)


def test_hw1f_a_and_b_match_the_textbook_formulas():
    a, sigma = 0.05, 0.01
    calib = flat_calibration(alpha=a, sigma=sigma)
    sim = SimulatedHW1FCurve(np.array([RATE]))
    t, T = 2.0, 7.5
    b = (1 - np.exp(-a * (T - t))) / a
    assert_allclose(sim.HW1F_B_tT(a, np.array([T - t]))[0, 0], b, rtol=1e-12)
    p_ratio = np.exp(-RATE * T) / np.exp(-RATE * t)
    a_hand = p_ratio * np.exp(b * RATE - (sigma**2) / (4 * a) * (1 - np.exp(-2 * a * t)) * b**2)
    a_code = sim.HW1F_A_tT(calib, t, np.array([T]))[0, 0]
    assert_allclose(a_code, a_hand, rtol=1e-6)  # forward rate off the interp grid
