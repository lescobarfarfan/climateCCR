"""Expiry-date pricing of EquityEuropeanOption: intrinsic value, no warnings.

When a valuation date lands exactly on the option maturity (t = 0) the
Black-Scholes formula degenerates (d1 = log(S/K)/0). The pricer must return
the intrinsic value explicitly — same numbers the cdf(+/-inf) limit produced,
minus the divide-by-zero RuntimeWarning (observed on the Mexican book, whose
2y option maturities coincide with the B3 2Y grid date).
"""

import warnings
from datetime import datetime

import numpy as np
import pandas as pd
from climateCCR.data.market.surface import Surface
from climateCCR.risk.ccr.pricing_models.equity_european_option_pricer import (
    EquityEuropeanOptionPricer,
)

SHARE = "TEST_SHARE"
SURFACE = "TEST_IMPLIED_VOLATILITY_SURFACE"
CURVE = "MXN_ZERO_YIELD_CURVE"
MATURITY = datetime(2028, 7, 17)
N_PATHS = 3


class _StubTrade:
    def __init__(self, put_call, long_short):
        self.trade_id = "O001"
        self.trade_underlyings = [SHARE, CURVE, SURFACE]
        self._attributes = {
            "underlying": SHARE,
            "notional": 10.0,
            "K": 100.0,
            "put/call": put_call,
            "long/short": long_short,
            "maturity": MATURITY,
        }

    def get_attribute(self, attribute):
        return self._attributes[attribute]


def _price_at_expiry(put_call, long_short, spots):
    surface = Surface(pd.DataFrame(0.2, index=[0.7, 1.0, 1.3], columns=["1M", "1Y", "5Y"]))
    scenarios = {
        SHARE: np.asarray(spots, dtype=float).reshape(-1, 1),
        CURVE: np.full((N_PATHS, 1), 0.05),
    }
    pricer = EquityEuropeanOptionPricer("EQ_EUR_OPT_Pricer")
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        return pricer.price_single_trade(
            _StubTrade(put_call, long_short),
            [MATURITY],  # valuation date == maturity -> t = 0
            scenarios,
            {"equity_implied_volatility_surface": {SURFACE: surface}},
            {"n_paths": N_PATHS},
        )


def test_call_at_expiry_is_intrinsic_without_warnings():
    mtms = _price_at_expiry("call", "long", [80.0, 100.0, 130.0])
    np.testing.assert_allclose(mtms[:, 0], 10.0 * np.array([0.0, 0.0, 30.0]))


def test_put_at_expiry_is_intrinsic_without_warnings():
    mtms = _price_at_expiry("put", "long", [80.0, 100.0, 130.0])
    np.testing.assert_allclose(mtms[:, 0], 10.0 * np.array([20.0, 0.0, 0.0]))


def test_short_position_flips_intrinsic_sign():
    long_mtms = _price_at_expiry("put", "long", [80.0, 100.0, 130.0])
    short_mtms = _price_at_expiry("put", "short", [80.0, 100.0, 130.0])
    np.testing.assert_allclose(short_mtms, -long_mtms)
