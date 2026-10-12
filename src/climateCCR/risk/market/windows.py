"""Backtest window helpers — the BCBS 2010 ¶13 non-overlapping forecast grid (INT-40)."""

from __future__ import annotations

from collections.abc import Mapping

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


def last_obs(series: pd.Series, t: pd.Timestamp, max_stale_days: int) -> tuple | None:
    """Last ``(date, value)`` at or before ``t`` if at most ``max_stale_days`` old, else None."""
    sub = series[series.index <= t]
    if sub.empty or (t - sub.index[-1]).days > max_stale_days:
        return None
    return sub.index[-1], float(sub.iloc[-1])


__all__ = ["horizon_end", "init_dates", "last_obs"]
