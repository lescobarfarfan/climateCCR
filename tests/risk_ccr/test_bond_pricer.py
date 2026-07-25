"""Unit tests for FixedCouponBondPricer (the additive DEBT desk extension).

On a flat zero curve with the short rate at the same level, the HW1F curve
reconstruction at t=0 collapses exactly to exp(-r*tau), so the pricer must
reproduce a hand-computed discounted-cashflow sum.
"""

from datetime import datetime

import numpy as np
import pytest
from climateCCR.calibration.financial.bond_yield import bono_cashflows
from climateCCR.data.market.curve import Curve
from climateCCR.risk.ccr.pricing_models.fixed_coupon_bond_pricer import FixedCouponBondPricer

FLAT_RATE = 0.05
CURVE_NAME = "MXN_ZERO_YIELD_CURVE"
VALUATION_DATE = datetime(2026, 7, 17)
MATURITY = datetime(2031, 7, 17)
N_PATHS = 3


class _StubTrade:
    def __init__(self, **attributes):
        self.trade_id = attributes.pop("trade_id", "B001")
        self.trade_underlyings = [CURVE_NAME]
        self._attributes = attributes

    def get_attribute(self, attribute):
        return self._attributes[attribute]


def _make_pricer():
    flat_curve = Curve({"1M": FLAT_RATE, "1Y": FLAT_RATE, "10Y": FLAT_RATE, "30Y": FLAT_RATE})
    pricer = FixedCouponBondPricer("BOND_FIXED_Pricer")
    pricer.calibrate(
        market_data={
            "Pricing_HW1F_calibration": {
                CURVE_NAME: {"alpha": 0.122, "volatility": 0.011, "rate_curve": flat_curve}
            }
        },
        calibration_parameters={
            "Pricing_HW1F_calibration": {
                "BOND_FIXED_Pricer": {"calibration_method": "direct_input"}
            }
        },
    )
    return pricer


def _price(trade):
    scenarios = {CURVE_NAME: np.full((N_PATHS, 1), FLAT_RATE)}
    return _make_pricer().price_single_trade(
        trade, [VALUATION_DATE], scenarios, {}, {"n_paths": N_PATHS}
    )


def _hand_dcf(notional, coupon, spread):
    times_days, amounts = bono_cashflows((MATURITY - VALUATION_DATE).days, coupon)
    tau = times_days / 365.0
    return notional / 100.0 * np.sum(amounts * np.exp(-(FLAT_RATE + spread) * tau))


def _trade(**overrides):
    attributes = {
        "notional": 1000.0,
        "coupon": 0.065,
        "spread": 0.0120,
        "long/short": "long",
        "maturity": MATURITY,
    }
    attributes.update(overrides)
    return _StubTrade(**attributes)


def test_price_matches_hand_computed_dcf():
    mtms = _price(_trade())
    expected = _hand_dcf(1000.0, 0.065, 0.0120)
    assert mtms.shape == (N_PATHS, 1)
    np.testing.assert_allclose(mtms[:, 0], expected, rtol=1e-5)


def test_zero_spread_reduces_to_curve_dcf():
    mtms = _price(_trade(spread=0.0))
    np.testing.assert_allclose(mtms[:, 0], _hand_dcf(1000.0, 0.065, 0.0), rtol=1e-5)


def test_short_position_flips_sign():
    long_mtms = _price(_trade())
    short_mtms = _price(_trade(**{"long/short": "short"}))
    np.testing.assert_allclose(short_mtms, -long_mtms)


def test_wider_spread_lowers_price():
    tight = _price(_trade(spread=0.001))
    wide = _price(_trade(spread=0.03))
    assert np.all(wide < tight)


def test_matured_bond_prices_at_zero():
    mtms = _price(_trade(maturity=datetime(2026, 7, 17)))
    np.testing.assert_array_equal(mtms, np.zeros((N_PATHS, 1)))


def test_price_is_decreasing_in_simulated_short_rate():
    pricer = _make_pricer()
    scenarios = {CURVE_NAME: np.array([[0.03], [0.05], [0.09]])}
    mtms = pricer.price_single_trade(_trade(), [VALUATION_DATE], scenarios, {}, {"n_paths": 3})
    assert mtms[0, 0] > mtms[1, 0] > mtms[2, 0]


def test_market_dependencies_declare_the_curve_calibration():
    pricer = _make_pricer()
    dependencies = pricer.get_market_dependencies(
        {CURVE_NAME},
        risk_factors=None,
        calibration_parameters={
            "Pricing_HW1F_calibration": {
                "BOND_FIXED_Pricer": {"calibration_method": "direct_input"}
            }
        },
    )
    assert dependencies == {("Pricing_HW1F_calibration", CURVE_NAME)}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
