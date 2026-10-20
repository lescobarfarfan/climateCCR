"""The option pricer finds its discount curve by name, not by list position (OQ-CCR-12).

``underlyings[underlyings != S and underlyings != S_implied_vol]`` compared a
list with a string, evaluated to ``underlyings[True]`` and therefore always
picked position 1 — right only because the trade model builds the list as
[share, curve, surface]. The curve is now selected by its ``CURVE`` suffix,
the rule ``get_market_dependencies`` already applies.
"""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from climateCCR.data.market.surface import Surface
from climateCCR.risk.ccr.pricing_models.equity_european_option_pricer import (
    EquityEuropeanOptionPricer,
)

SHARE = "TEST_SHARE"
SURFACE = "TEST_IMPLIED_VOLATILITY_SURFACE"
CURVE = "MXN_ZERO_YIELD_CURVE"
VALUATION = datetime(2027, 7, 17)
MATURITY = datetime(2028, 7, 17)
N_PATHS = 3


class _StubTrade:
    def __init__(self, underlyings):
        self.trade_id = "O002"
        self.trade_underlyings = list(underlyings)
        self._attributes = {
            "underlying": SHARE,
            "notional": 10.0,
            "K": 100.0,
            "put/call": "call",
            "long/short": "long",
            "maturity": MATURITY,
        }

    def get_attribute(self, attribute):
        return self._attributes[attribute]


def _price(underlyings):
    surface = Surface(pd.DataFrame(0.2, index=[0.7, 1.0, 1.3], columns=["1M", "1Y", "5Y"]))
    scenarios = {
        SHARE: np.array([[90.0], [100.0], [110.0]]),
        CURVE: np.full((N_PATHS, 1), 0.05),
    }
    pricer = EquityEuropeanOptionPricer("EQ_EUR_OPT_Pricer")
    return pricer.price_single_trade(
        _StubTrade(underlyings),
        [VALUATION],  # one year to expiry: the curve rate matters
        scenarios,
        {"equity_implied_volatility_surface": {SURFACE: surface}},
        {"n_paths": N_PATHS},
    )


@pytest.mark.parametrize(
    "order", [(CURVE, SHARE, SURFACE), (SHARE, SURFACE, CURVE), (SURFACE, CURVE, SHARE)]
)
def test_discount_curve_is_found_by_name_in_any_order(order):
    np.testing.assert_array_equal(_price(order), _price((SHARE, CURVE, SURFACE)))


def test_call_values_increase_with_spot():
    mtm = _price((SHARE, CURVE, SURFACE))[:, 0]
    assert np.all(mtm > 0) and mtm[2] > mtm[1] > mtm[0]


def test_missing_curve_raises():
    with pytest.raises(ValueError, match="discount curve"):
        _price((SHARE, SURFACE))
