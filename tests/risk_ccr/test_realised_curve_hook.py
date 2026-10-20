"""The rate pricers' ``discount_factors`` hook (OQ-INT-14 a).

By default the hook is the unchanged HW1F reconstruction off the simulated short
rate; when ``global_parameters["realised_curves"]`` maps the valuation date to a
``NelsonSiegelFit`` the discount factors come from that observed zero curve
instead (the realised reprice of pipelines/31). Absent or unmapped keys must
price bit-identically; a flat observed curve must reproduce the flat HW1F curve
at t = 0 (where the reconstruction collapses to exp(-r tau)); an observed curve
at another level must move the price to it regardless of the simulated rate.
"""

from datetime import datetime

import numpy as np
import pytest
from climateCCR.calibration.financial.bond_yield import bono_cashflows
from climateCCR.calibration.financial.yield_curve import NelsonSiegelFit
from climateCCR.data.market.curve import Curve
from climateCCR.risk.ccr.pricing_models.fixed_coupon_bond_pricer import FixedCouponBondPricer
from climateCCR.risk.ccr.pricing_models.floating_rate_note_pricer import FloatingRateNotePricer

FLAT_RATE = 0.05
CURVE_NAME = "MXN_ZERO_YIELD_CURVE"
VALUATION_DATE = datetime(2026, 7, 17)
MATURITY = datetime(2031, 7, 17)
BOND = {"notional": 1000.0, "coupon": 0.065, "spread": 0.012, "long/short": "long"}
FRN = {"notional": 1000.0, "coupon": 0.0125, "spread": 0.0125, "long/short": "long"}
PRICERS = [
    (FixedCouponBondPricer, "BOND_FIXED_Pricer", BOND),
    (FloatingRateNotePricer, "BOND_FRN_Pricer", FRN),
]


class _StubTrade:
    def __init__(self, **attributes):
        self.trade_id = "T001"
        self.trade_underlyings = [CURVE_NAME]
        self._attributes = attributes | {"maturity": MATURITY}

    def get_attribute(self, attribute):
        return self._attributes[attribute]


def _pricer(cls, name):
    flat_curve = Curve({"1M": FLAT_RATE, "1Y": FLAT_RATE, "10Y": FLAT_RATE, "30Y": FLAT_RATE})
    pricer = cls(name)
    pricer.calibrate(
        market_data={
            "Pricing_HW1F_calibration": {
                CURVE_NAME: {"alpha": 0.122, "volatility": 0.011, "rate_curve": flat_curve}
            }
        },
        calibration_parameters={
            "Pricing_HW1F_calibration": {name: {"calibration_method": "direct_input"}}
        },
    )
    return pricer


def _price(cls, name, attrs, gp_extra=None, rate=FLAT_RATE, n_paths=3):
    scenarios = {CURVE_NAME: np.full((n_paths, 1), rate)}
    gp = {"n_paths": n_paths} | (gp_extra or {})
    return _pricer(cls, name).price_single_trade(
        _StubTrade(**attrs), [VALUATION_DATE], scenarios, {}, gp
    )


def _flat_fit(rate):
    return NelsonSiegelFit(beta0=rate, beta1=0.0, beta2=0.0, tau=1.0, rmse=0.0, n_pillars=4)


@pytest.mark.parametrize("cls,name,attrs", PRICERS)
def test_absent_or_unmapped_realised_curves_price_bit_identically(cls, name, attrs):
    base = _price(cls, name, attrs)
    np.testing.assert_array_equal(_price(cls, name, attrs, {"realised_curves": {}}), base)
    elsewhere = {datetime(2027, 1, 1): _flat_fit(0.09)}
    np.testing.assert_array_equal(_price(cls, name, attrs, {"realised_curves": elsewhere}), base)


@pytest.mark.parametrize("cls,name,attrs", PRICERS)
def test_a_flat_observed_curve_reproduces_the_flat_hw1f_curve_at_t0(cls, name, attrs):
    model = _price(cls, name, attrs, n_paths=1)
    realised = _price(
        cls, name, attrs, {"realised_curves": {VALUATION_DATE: _flat_fit(FLAT_RATE)}}, n_paths=1
    )
    np.testing.assert_allclose(realised, model, rtol=1e-5)  # the Curve interpolation's precision


def test_an_observed_curve_moves_the_bond_to_its_level_whatever_the_simulated_rate():
    mapped = {"realised_curves": {VALUATION_DATE: _flat_fit(0.09)}}
    realised = _price(FixedCouponBondPricer, "BOND_FIXED_Pricer", BOND, mapped, n_paths=1)
    times_days, amounts = bono_cashflows((MATURITY - VALUATION_DATE).days, BOND["coupon"])
    tau = times_days / 365.0
    hand = BOND["notional"] / 100.0 * np.sum(amounts * np.exp(-(0.09 + BOND["spread"]) * tau))
    assert realised[0, 0] == pytest.approx(hand, rel=1e-12)
    moved = _price(FixedCouponBondPricer, "BOND_FIXED_Pricer", BOND, mapped, rate=0.02, n_paths=1)
    assert moved[0, 0] == pytest.approx(realised[0, 0], rel=1e-12)


def test_discount_factors_hook_shape_and_values():
    pricer = _pricer(FixedCouponBondPricer, "BOND_FIXED_Pricer")
    horizons = np.array([0.5, 1.0, 2.0])
    factors = pricer.discount_factors(
        CURVE_NAME,
        np.array([0.05]),
        0.25,
        0.25 + horizons,
        VALUATION_DATE,
        {"realised_curves": {VALUATION_DATE: _flat_fit(0.07)}},
    )
    assert factors.shape == (1, 3)
    np.testing.assert_allclose(factors[0], np.exp(-0.07 * horizons))
