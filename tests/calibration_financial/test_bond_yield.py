"""Bonos M yield solver: round-trip, conventions, roll masking."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from climateCCR.calibration.financial.bond_yield import (
    COUPON_PERIOD_DAYS,
    bono_dirty_price,
    bono_yield_panel,
    roll_mask,
    solve_bono_yield,
)


@pytest.mark.parametrize("plazo", [91.0, 182.0, 364.0, 3 * 182.0, 3641.0, 10920.0])
@pytest.mark.parametrize("cupon", [0.0, 0.045, 0.10])
@pytest.mark.parametrize("y", [0.02, 0.075, 0.15])
def test_price_yield_round_trip(plazo, cupon, y):
    price = bono_dirty_price(y, plazo, cupon)
    assert solve_bono_yield(price, plazo, cupon) == pytest.approx(y, abs=1e-10)


def test_par_bond_at_full_period():
    # plazo = exact multiple of 182 and y == cupon -> price == par exactly.
    y = 0.08
    price = bono_dirty_price(y, 10 * COUPON_PERIOD_DAYS, y)
    assert price == pytest.approx(100.0, abs=1e-9)


def test_price_decreases_in_yield():
    prices = [bono_dirty_price(y, 1820, 0.075) for y in (0.02, 0.05, 0.10)]
    assert prices == sorted(prices, reverse=True)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        bono_dirty_price(0.05, 0.0, 0.075)
    with pytest.raises(ValueError):
        bono_dirty_price(0.05, 182.0, -0.01)
    with pytest.raises(ValueError):
        solve_bono_yield(0.0, 182.0, 0.075)


def test_roll_mask_flags_upward_plazo_jumps():
    plazo = pd.Series([1000.0, 999.0, 998.0, 1820.0, 1819.0])
    assert roll_mask(plazo).tolist() == [False, False, False, True, False]


def test_panel_masks_rolls_and_reports_medians():
    dates = pd.bdate_range("2010-01-04", periods=4)
    y_true = 0.07
    rows = []
    for fecha, plazo in zip(dates, [1000.0, 999.0, 1820.0, 1819.0], strict=True):
        rows.append(
            {
                "Fecha": fecha,
                "Serie": "BonosM_7_10",
                "Plazo": plazo,
                "Cupon": 7.5,  # percent, as published
                "Valor": bono_dirty_price(y_true, plazo, 0.075),
            }
        )
    rows.append(  # a second bucket with a missing price -> NaN, not a crash
        {"Fecha": dates[0], "Serie": "BonosM_20_30", "Plazo": 9000.0, "Cupon": 8.0, "Valor": np.nan}
    )
    panel = bono_yield_panel(pd.DataFrame(rows))
    assert panel.loc[dates[1], "BonosM_7_10"] == pytest.approx(y_true, abs=1e-8)
    assert np.isnan(panel.loc[dates[2], "BonosM_7_10"])  # the roll day
    assert np.isnan(panel.loc[dates[0], "BonosM_20_30"])
    # median over the full window, post-roll days included (the bucket's effective T)
    assert panel.attrs["plazo_median_days"]["BonosM_7_10"] == pytest.approx(1409.5)
    assert panel.attrs["n_failed"] == {"BonosM_7_10": 0, "BonosM_20_30": 0}
