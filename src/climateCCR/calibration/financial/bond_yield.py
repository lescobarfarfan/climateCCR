"""Bonos M yield-to-maturity from SIE dirty prices (DC-MKT-SIE-3, MKT-SIE-03).

The SIE publishes the on-the-run Bonos M buckets as daily dirty prices
(``Valor``, per 100 face) with residual maturity (``Plazo``, days) and the
current coupon (``Cupon``, percent). The OQ-INT-09 event study needs daily
*yield changes*, so this module solves the standard Bonos M valuation for the
yield: 182-day coupon periods paying ``cupon * 182/360 * 100`` per 100 face,
per-period discount ``v = 1 / (1 + y * 182/360)``, fractional first period.

On-the-run buckets roll to a new benchmark bond (``Plazo`` jumps up); a yield
change across a roll compares two different bonds, so roll days are masked to
NaN in the panel (MKT-SIE-05) and any Δy spanning them drops out downstream.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import optimize

#: Contractual Bonos M coupon period in days (182-day rule, DC-MKT-SIE-3).
COUPON_PERIOD_DAYS = 182


def bono_dirty_price(y: float, plazo_dias: float, cupon: float) -> float:
    """Dirty price per 100 face of a Bonos M with ``plazo_dias`` to maturity.

    ``y`` and ``cupon`` are decimal annual rates (e.g. ``0.075``). Explicit
    cashflow sum over the remaining ``ceil(plazo/182)`` coupons — N <= 60,
    clarity over the closed form.
    """
    if plazo_dias <= 0:
        raise ValueError(f"plazo_dias must be > 0, got {plazo_dias}")
    if cupon < 0:
        raise ValueError(f"cupon must be >= 0, got {cupon}")
    n = math.ceil(plazo_dias / COUPON_PERIOD_DAYS)
    d1 = plazo_dias - (n - 1) * COUPON_PERIOD_DAYS  # days to the next coupon
    coupon_payment = cupon * COUPON_PERIOD_DAYS / 360 * 100
    v = 1.0 / (1.0 + y * COUPON_PERIOD_DAYS / 360)
    times = d1 / COUPON_PERIOD_DAYS + np.arange(n)  # in coupon periods
    discounts = v**times
    return float(coupon_payment * discounts.sum() + 100.0 * discounts[-1])


def solve_bono_yield(dirty_price: float, plazo_dias: float, cupon: float) -> float:
    """Invert :func:`bono_dirty_price` for the decimal annual yield (brentq)."""
    if dirty_price <= 0:
        raise ValueError(f"dirty_price must be > 0, got {dirty_price}")
    return float(
        optimize.brentq(lambda y: bono_dirty_price(y, plazo_dias, cupon) - dirty_price, 1e-9, 2.0)
    )


def roll_mask(plazo: pd.Series) -> pd.Series:
    """True on benchmark-roll days: the residual maturity jumped up (MKT-SIE-05)."""
    return plazo.diff() > 0


def bono_yield_panel(bonos_m: pd.DataFrame) -> pd.DataFrame:
    """Daily decimal yields, wide ``Fecha x Serie``, roll days masked to NaN.

    ``bonos_m`` is the long SIE extract (``Fecha, Serie, Plazo, Cupon, Valor``)
    with values as published (``Cupon`` percent, ``Valor`` dirty price per 100).
    Rows with missing inputs or an unsolvable price are NaN (count per bucket in
    ``.attrs["n_failed"]``); ``.attrs["plazo_median_days"]`` carries each
    bucket's median residual maturity — the effective T of the pillar.
    """
    frame = bonos_m.copy()
    frame["Fecha"] = pd.to_datetime(frame["Fecha"])
    n_failed: dict[str, int] = {}
    columns: dict[str, pd.Series] = {}
    medians: dict[str, float] = {}
    for serie, group in frame.groupby("Serie", sort=False):
        group = group.set_index("Fecha").sort_index()
        yields = pd.Series(np.nan, index=group.index)
        valid = group[["Plazo", "Cupon", "Valor"]].notna().all(axis=1) & (group["Plazo"] > 0)
        failed = 0
        for fecha in group.index[valid]:
            row = group.loc[fecha]
            try:
                yields[fecha] = solve_bono_yield(row["Valor"], row["Plazo"], row["Cupon"] / 100)
            except ValueError:
                failed += 1
        yields[roll_mask(group["Plazo"])] = np.nan
        columns[serie] = yields
        medians[serie] = float(group.loc[valid, "Plazo"].median())
        n_failed[serie] = failed
    out = pd.DataFrame(columns)
    out.index.name = "Fecha"
    out.attrs["plazo_median_days"] = medians
    out.attrs["n_failed"] = n_failed
    return out.sort_index()
