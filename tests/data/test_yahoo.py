"""Yahoo Finance chart client (data.market.yahoo): parsing and error paths."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from climateCCR.data.market.yahoo import fetch_daily_closes


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class FakeSession:
    """Answers every request with one canned chart payload."""

    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.requests: list[dict] = []

    def get(self, url, params=None, timeout=None):
        self.requests.append({"url": url, "params": params})
        return FakeResponse(self.payload, self.status_code)


def _chart_payload(timestamps, closes, adjcloses=None):
    indicators = {"quote": [{"close": closes}]}
    if adjcloses is not None:
        indicators["adjclose"] = [{"adjclose": adjcloses}]
    return {
        "chart": {
            "result": [{"timestamp": timestamps, "indicators": indicators}],
            "error": None,
        }
    }


def test_parses_closes_and_drops_nulls():
    # 2024-01-02 and 2024-01-03, 14:30 UTC (08:30 Mexico City open).
    payload = _chart_payload(
        [1704205800, 1704292200, 1704378600],
        [57000.5, None, 57500.25],
        [57000.5, None, 57500.25],
    )
    frame = fetch_daily_closes("^MXX", "2024-01-01", "2024-01-05", session=FakeSession(payload))
    assert list(frame.index) == [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-04")]
    assert frame.index.name == "Fecha"
    assert frame["Close"].tolist() == [57000.5, 57500.25]
    assert frame["AdjClose"].tolist() == [57000.5, 57500.25]


def test_missing_adjclose_falls_back_to_close():
    payload = _chart_payload([1704205800], [100.0])
    frame = fetch_daily_closes("^MXX", "2024-01-01", session=FakeSession(payload))
    assert frame["AdjClose"].iloc[0] == 100.0


def test_http_error_raises():
    with pytest.raises(RuntimeError, match="failed"):
        fetch_daily_closes("^MXX", "2024-01-01", session=FakeSession({}, status_code=500))


def test_payload_error_raises():
    payload = {"chart": {"result": None, "error": {"code": "Not Found"}}}
    with pytest.raises(RuntimeError, match="error"):
        fetch_daily_closes("BOGUS", "2024-01-01", session=FakeSession(payload))


def test_empty_result_raises():
    payload = {"chart": {"result": [{"timestamp": []}], "error": None}}
    with pytest.raises(RuntimeError, match="no data"):
        fetch_daily_closes("^MXX", "2024-01-01", session=FakeSession(payload))


def test_request_carries_range_params():
    payload = _chart_payload([1704205800], [1.0])
    session = FakeSession(payload)
    fetch_daily_closes("^MXX", "2024-01-01", "2024-02-01", session=session)
    params = session.requests[0]["params"]
    assert params["interval"] == "1d"
    assert params["period2"] > params["period1"]


@pytest.mark.network
def test_live_smoke_ipc():
    frame = fetch_daily_closes("^MXX", "2024-01-01", "2024-03-01")
    assert len(frame) > 30
    assert (frame["Close"] > 40000).all()  # IPC level range
    assert not np.isnan(frame["Close"]).any()
