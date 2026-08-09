"""Unit tests for FloatingRateNotePricer (CCR-RISK-04, the FRN cebur leg).

Same trust basis as the fixed-coupon tests: on a flat zero curve with the
short rate at that level, the HW1F reconstruction at t=0 collapses to
exp(-r*tau), so the pricer must reproduce a hand-computed projection-and-
discount sum — plus the two FRN economics checks: near-par at issuance when
the discount margin equals the contractual sobretasa, and rate-level
insensitivity relative to a fixed bond.
"""

import importlib.util
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest
from climateCCR.calibration.financial.bond_yield import frn_cashflow_times
from climateCCR.data.market.curve import Curve
from climateCCR.risk.ccr.pricing_models.fixed_coupon_bond_pricer import FixedCouponBondPricer
from climateCCR.risk.ccr.pricing_models.floating_rate_note_pricer import FloatingRateNotePricer

REPO_ROOT = Path(__file__).resolve().parents[2]
FLAT_RATE = 0.05
CURVE_NAME = "MXN_ZERO_YIELD_CURVE"
VALUATION_DATE = datetime(2026, 7, 17)
MATURITY = datetime(2031, 7, 17)
N_PATHS = 3


class _StubTrade:
    def __init__(self, **attributes):
        self.trade_id = attributes.pop("trade_id", "F001")
        self.trade_underlyings = [CURVE_NAME]
        self._attributes = attributes

    def get_attribute(self, attribute):
        return self._attributes[attribute]


def _make_pricer(cls=FloatingRateNotePricer, name="BOND_FRN_Pricer"):
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


def _price(trade, rate=FLAT_RATE):
    scenarios = {CURVE_NAME: np.full((N_PATHS, 1), rate)}
    return _make_pricer().price_single_trade(
        trade, [VALUATION_DATE], scenarios, {}, {"n_paths": N_PATHS}
    )


def _hand_frn(notional, margin, spread):
    times = frn_cashflow_times((MATURITY - VALUATION_DATE).days)
    tau = times / 365.0
    tau_fix = np.maximum(times - 28.0, 0.0) / 365.0
    p_pay = np.exp(-FLAT_RATE * tau)
    p_fix = np.exp(-FLAT_RATE * tau_fix)
    forward = (p_fix / p_pay - 1.0) * 360.0 / 28.0
    amounts = (forward + margin) * 28.0 / 360.0 * 100.0
    amounts[-1] += 100.0
    return notional / 100.0 * np.sum(p_pay * np.exp(-spread * tau) * amounts)


def _trade(**overrides):
    attributes = {
        "notional": 1000.0,
        "coupon": 0.0125,  # contractual sobretasa over the 28d index
        "spread": 0.0125,  # discount margin (= sobretasa at issuance)
        "long/short": "long",
        "maturity": MATURITY,
    }
    attributes.update(overrides)
    return _StubTrade(**attributes)


def test_frn_schedule_backs_out_from_maturity():
    np.testing.assert_array_equal(frn_cashflow_times(100), [16.0, 44.0, 72.0, 100.0])
    with pytest.raises(ValueError):
        frn_cashflow_times(0)


def test_price_matches_hand_computed_projection_dcf():
    mtms = _price(_trade())
    expected = _hand_frn(1000.0, 0.0125, 0.0125)
    assert mtms.shape == (N_PATHS, 1)
    np.testing.assert_allclose(mtms[:, 0], expected, rtol=1e-5)


def test_prices_near_par_when_discount_margin_equals_sobretasa():
    mtms = _price(_trade())
    assert mtms[0, 0] / 1000.0 == pytest.approx(1.0, abs=0.01)


def test_wider_discount_spread_lowers_price_and_margin_raises_it():
    base = _price(_trade())[0, 0]
    assert _price(_trade(spread=0.03))[0, 0] < base  # credit deterioration
    assert _price(_trade(coupon=0.03))[0, 0] > base  # richer contractual margin


def test_short_position_flips_sign_and_matured_is_zero():
    np.testing.assert_allclose(_price(_trade(**{"long/short": "short"})), -_price(_trade()))
    np.testing.assert_array_equal(_price(_trade(maturity=VALUATION_DATE)), np.zeros((N_PATHS, 1)))


def test_frn_is_rate_insensitive_relative_to_a_fixed_bond():
    frn_move = abs(_price(_trade(), rate=0.09)[0, 0] - _price(_trade(), rate=0.03)[0, 0])
    fixed = _make_pricer(FixedCouponBondPricer, "BOND_FIXED_Pricer")
    fixed_trade = _StubTrade(
        notional=1000.0, coupon=0.09, spread=0.0125, maturity=MATURITY, **{"long/short": "long"}
    )
    fixed_mtms = [
        fixed.price_single_trade(
            fixed_trade,
            [VALUATION_DATE],
            {CURVE_NAME: np.full((N_PATHS, 1), r)},
            {},
            {"n_paths": N_PATHS},
        )[0, 0]
        for r in (0.09, 0.03)
    ]
    assert frn_move < 0.1 * abs(fixed_mtms[0] - fixed_mtms[1])


def test_market_dependencies_declare_the_curve_calibration():
    dependencies = _make_pricer().get_market_dependencies(
        {CURVE_NAME},
        risk_factors=None,
        calibration_parameters={
            "Pricing_HW1F_calibration": {"BOND_FRN_Pricer": {"calibration_method": "direct_input"}}
        },
    )
    assert dependencies == {("Pricing_HW1F_calibration", CURVE_NAME)}


def _load_pipeline_09():
    spec = importlib.util.spec_from_file_location(
        "build_mexican_book", REPO_ROOT / "pipelines" / "09_build_mexican_book.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_bond_hybrid_rows():
    pipeline = _load_pipeline_09()
    legacy = pipeline._parse_bond([0.098, "2031-06-15", 240])
    assert legacy["feed"] == "BOND_FIXED"
    assert legacy["coupon"] == pytest.approx(0.098)
    assert legacy["spread"] == pytest.approx(0.024)

    fija = pipeline._parse_bond(
        {
            "tipo": "fija",
            "cupon": 0.0912,
            "vencimiento": "2036-02-01",
            "spread_bp": 150,
            "fuente": "https://example.test",
        }
    )
    assert fija["feed"] == "BOND_FIXED"
    assert fija["maturity"] == "2036-02-01"

    frn = pipeline._parse_bond(
        {
            "tipo": "frn",
            "sobretasa": 0.0045,
            "vencimiento": "2031-02-15",
            "fuente": "https://example.test",
        }
    )
    assert frn["feed"] == "BOND_FRN"
    assert frn["coupon"] == pytest.approx(0.0045)
    assert frn["spread"] == pytest.approx(0.0045)  # discount margin defaults to the sobretasa
    assert frn["payments_frequency"] == "28-day"

    with pytest.raises(ValueError, match="tipo"):
        pipeline._parse_bond({"tipo": "convertible", "vencimiento": "2030-01-01"})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
