"""Backtest window helpers — the BCBS 2010 ¶13 non-overlapping forecast grid (INT-40)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd


def horizon_end(t: pd.Timestamp, spec: Mapping[str, int]) -> pd.Timestamp:
    """Initialisation date plus the horizon: ``{"days": n}`` or ``{"months": n}``."""
    if "days" in spec:
        return pd.Timestamp(t) + pd.Timedelta(days=int(spec["days"]))
    if "months" in spec:
        return pd.Timestamp(t) + pd.DateOffset(months=int(spec["months"]))
    raise ValueError(f"horizon spec needs 'days' or 'months': {dict(spec)}")


def init_dates(start: str, end: str, spec: Mapping[str, int]) -> list[pd.Timestamp]:
    """Non-overlapping initialisation dates spaced by the horizon, realising by ``end``."""
    dates: list[pd.Timestamp] = []
    t = pd.Timestamp(start)
    stop = pd.Timestamp(end)
    while horizon_end(t, spec) <= stop:
        dates.append(t)
        t = horizon_end(t, spec)
    return dates


def horizon_spec(label: str) -> dict[str, int]:
    """B3 tenor label -> ``horizon_end`` spec, the letters ``generate_time_grids`` reads.

    ``"1W"`` -> ``{"days": 7}``, ``"3M"`` -> ``{"months": 3}``, ``"2Y"`` -> ``{"months": 24}``,
    ``"0D"`` -> ``{"days": 0}``.
    """
    number, unit = int(label[:-1]), label[-1]
    if unit == "D":
        return {"days": number}
    if unit == "W":
        return {"days": 7 * number}
    if unit == "M":
        return {"months": number}
    if unit == "Y":
        return {"months": 12 * number}
    raise ValueError(f"unknown tenor unit in {label!r}")


def non_overlapping(dates: Sequence, spec: Mapping[str, int]) -> list[pd.Timestamp]:
    """Greedy BCBS 2010 ¶13 subset of a given grid: keep a date iff it is at or after the
    previous kept date's ``horizon_end``.

    ``init_dates`` generates a regular non-overlapping grid; this filters a config-driven,
    possibly irregular one (the annual tier-E grid scored per horizon).
    """
    kept: list[pd.Timestamp] = []
    for t in sorted(pd.Timestamp(d) for d in dates):
        if not kept or t >= horizon_end(kept[-1], spec):
            kept.append(t)
    return kept


def last_obs(series: pd.Series, t: pd.Timestamp, max_stale_days: int) -> tuple | None:
    """Last ``(date, value)`` at or before ``t`` if at most ``max_stale_days`` old, else None."""
    sub = series[series.index <= t]
    if sub.empty or (t - sub.index[-1]).days > max_stale_days:
        return None
    return sub.index[-1], float(sub.iloc[-1])


__all__ = ["horizon_end", "horizon_spec", "init_dates", "last_obs", "non_overlapping"]
