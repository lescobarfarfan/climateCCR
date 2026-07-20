"""Banxico SIE client (data.market.sie): chunking, parsing, token handling."""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest
from climateCCR.data.market.sie import (
    MAX_SERIES_PER_REQUEST,
    TOKEN_ENV,
    _date_chunks,
    fetch_series,
)


class FakeSession:
    """Records every request and answers with one canned observation per series."""

    def __init__(self, datos_by_id: dict[str, list[dict]] | None = None):
        self.urls: list[str] = []
        self.headers_seen: list[dict] = []
        self.datos_by_id = datos_by_id

    def get(self, url, headers=None, timeout=None):
        self.urls.append(url)
        self.headers_seen.append(headers or {})
        ids = url.split("/series/")[1].split("/datos/")[0].split(",")
        series = []
        for sid in ids:
            if self.datos_by_id is None:
                datos = [{"fecha": "02/01/2006", "dato": "8.59"}]
            else:
                datos = self.datos_by_id.get(sid, [])
            series.append({"idSerie": sid, "datos": datos})
        return FakeResponse({"bmx": {"series": series}})


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_requests_chunk_by_series_and_date():
    ids = {f"S{i}": f"SF{i:05d}" for i in range(MAX_SERIES_PER_REQUEST + 3)}
    session = FakeSession()
    token = "SECRET-TOKEN-0X9"
    fetch_series(ids, "2001-06-01", "2026-07-19", token=token, session=session)
    # 23 series -> 2 batches; ~25 years -> 3 date windows; every pair requested.
    assert len(session.urls) == 2 * 3
    assert all(h.get("Bmx-Token") == token for h in session.headers_seen)
    assert all(token not in url for url in session.urls)  # token never in the URL


def test_date_chunks_cover_range_without_overlap():
    from datetime import date

    chunks = _date_chunks(date(2001, 6, 1), date(2026, 7, 19), 10)
    assert chunks[0][0] == date(2001, 6, 1)
    assert chunks[-1][1] == date(2026, 7, 19)
    for (_, hi), (lo, _) in zip(chunks, chunks[1:], strict=False):
        assert (lo - hi).days == 1


def test_parsing_ne_thousands_and_dates():
    datos = {
        "SF00001": [
            {"fecha": "02/01/2006", "dato": "8.59"},
            {"fecha": "03/01/2006", "dato": "N/E"},
            {"fecha": "04/01/2006", "dato": "1,234.56"},
        ],
        "SF00002": [],  # a series with no data in range stays an all-NaN column
    }
    frame = fetch_series(
        {"A": "SF00001", "B": "SF00002"},
        "2006-01-01",
        "2006-01-31",
        token="t",
        session=FakeSession(datos),
    )
    assert list(frame.columns) == ["A", "B"]
    assert frame.index.name == "Fecha"
    assert frame.loc[pd.Timestamp("2006-01-02"), "A"] == pytest.approx(8.59)
    assert np.isnan(frame.loc[pd.Timestamp("2006-01-03"), "A"])
    assert frame.loc[pd.Timestamp("2006-01-04"), "A"] == pytest.approx(1234.56)
    assert frame["B"].isna().all()


def test_missing_token_raises(monkeypatch):
    monkeypatch.delenv(TOKEN_ENV, raising=False)
    with pytest.raises(RuntimeError, match=TOKEN_ENV):
        fetch_series({"A": "SF00001"}, "2006-01-01", "2006-01-31", session=FakeSession())


def test_duplicate_ids_rejected():
    with pytest.raises(ValueError, match="duplicated"):
        fetch_series(
            {"A": "SF1", "B": "SF1"}, "2006-01-01", "2006-01-31", token="t", session=FakeSession()
        )


@pytest.mark.network
@pytest.mark.skipif(not os.environ.get(TOKEN_ENV), reason=f"no {TOKEN_ENV} in env")
def test_live_smoke_tiie28():
    frame = fetch_series({"TIIE28": "SF43783"}, "2006-01-02", "2006-01-31")
    assert len(frame) > 15  # ~daily business observations
    assert frame["TIIE28"].dropna().between(5, 12).all()  # percent units, 2006 levels
