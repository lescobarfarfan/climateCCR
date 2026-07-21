"""Yahoo Finance daily-closes client (DC-CCR-DATA-1: public market/price source).

One entry point, :func:`fetch_daily_closes`, pulls the v8 chart API for a
symbol (e.g. ``^MXX``, the S&P/BMV IPC) into a ``Fecha``-indexed frame with
``Close`` and ``AdjClose``. Reuses the SIE client's retry/backoff session; no
key needed. Values land as published; provenance is the caller's job
(GEN-02), as with the SIE pipeline.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import requests

from climateCCR.data.market.sie import build_session

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
_TIMEOUT_S = 60
#: The exchange timezone: bar timestamps map to trading dates in local time.
_EXCHANGE_TZ = "America/Mexico_City"


def fetch_daily_closes(
    symbol: str,
    start: str,
    end: str | None = None,
    *,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Daily ``Close``/``AdjClose`` for ``symbol`` between ISO dates (inclusive).

    Rows with a null close (exchange holidays inside the range) are dropped.
    Raises ``RuntimeError`` on HTTP or payload errors — no silent empties.
    """
    session = session or build_session()
    period1 = int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp())
    end_dt = (
        datetime.now(timezone.utc)
        if end is None
        else (datetime.fromisoformat(end).replace(tzinfo=timezone.utc) + pd.Timedelta(days=1))
    )
    response = session.get(
        CHART_URL.format(symbol=symbol),
        params={
            "period1": period1,
            "period2": int(end_dt.timestamp()),
            "interval": "1d",
            "events": "div,split",
        },
        timeout=_TIMEOUT_S,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Yahoo chart request failed ({response.status_code}): {symbol}")
    payload = response.json().get("chart", {})
    if payload.get("error"):
        raise RuntimeError(f"Yahoo chart error for {symbol}: {payload['error']}")
    results = payload.get("result") or []
    if not results or not results[0].get("timestamp"):
        raise RuntimeError(f"Yahoo chart returned no data for {symbol}")
    result = results[0]

    dates = (
        pd.to_datetime(result["timestamp"], unit="s", utc=True)
        .tz_convert(_EXCHANGE_TZ)
        .normalize()
        .tz_localize(None)
    )
    quote = result["indicators"]["quote"][0]
    adjclose = result["indicators"].get("adjclose", [{}])[0].get("adjclose")
    frame = pd.DataFrame(
        {
            "Close": pd.to_numeric(pd.Series(quote["close"]), errors="coerce").to_numpy(),
            "AdjClose": pd.to_numeric(
                pd.Series(adjclose if adjclose is not None else quote["close"]), errors="coerce"
            ).to_numpy(),
        },
        index=dates,
    )
    frame.index.name = "Fecha"
    return frame.dropna(subset=["Close"]).sort_index()
