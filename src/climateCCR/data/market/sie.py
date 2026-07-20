"""Banxico SIE REST client (DC-MKT-SIE-1; the Python port of ``Actualiza_FTIIE.R``).

One entry point, :func:`fetch_series`, pulls daily series from the SIE API
(https://www.banxico.org.mx/SieAPIRest) into a wide ``DataFrame``. The API
token is read from the ``SIEBANXICO_TOKEN`` environment variable (the same
variable the legacy R script used) and travels only in the ``Bmx-Token``
request header — never in URLs, logs, or provenance files (GEN-02).

Values are returned **as published** (rates in percent, prices per 100 face);
unit conversions happen downstream. Requests are chunked to the API's caps
(max series per call, max years per date range) and retried with backoff on
transient failures (HAZ-SCRAPER-CNSF-07 robustness pattern).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import date, timedelta

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SIE_BASE = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"
TOKEN_ENV = "SIEBANXICO_TOKEN"
#: API caps (SIE REST docs): series per request and years per date range.
MAX_SERIES_PER_REQUEST = 20
MAX_YEARS_PER_REQUEST = 10
_TIMEOUT_S = 60


def build_session() -> requests.Session:
    """A session with UA + retry/backoff on transient failures (HAZ-SCRAPER-CNSF-07)."""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1.0, status_forcelist=(429, 500, 502, 503, 504))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = "climateCCR (github.com/lescobarfarfan/climateCCR)"
    return session


def _date_chunks(start: date, end: date, max_years: int) -> list[tuple[date, date]]:
    span = timedelta(days=365 * max_years)  # stays under the cap even across leap days
    chunks = []
    lo = start
    while lo <= end:
        hi = min(end, lo + span - timedelta(days=1))
        chunks.append((lo, hi))
        lo = hi + timedelta(days=1)
    return chunks


def _parse_datos(datos: list[dict]) -> pd.Series:
    frame = pd.DataFrame(datos)
    values = frame["dato"].astype(str).str.replace(",", "", regex=False)
    return pd.Series(
        pd.to_numeric(values, errors="coerce").to_numpy(),  # "N/E" and kin -> NaN
        index=pd.to_datetime(frame["fecha"], format="%d/%m/%Y"),
    )


def fetch_series(
    series_ids: Mapping[str, str],
    start: str,
    end: str,
    *,
    token: str | None = None,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Daily SIE series as a wide frame: index ``fecha``, one column per name.

    ``series_ids`` maps output column names to SIE ids (``{"TIIE28": "SF43783"}``);
    ``start``/``end`` are ``YYYY-MM-DD``. Missing observations ("N/E") are NaN;
    dates on which no requested series has data are absent. ``session`` is an
    injection seam for tests; the default carries retries with backoff.
    """
    token = token or os.environ.get(TOKEN_ENV)
    if not token:
        raise RuntimeError(
            f"No SIE token: export {TOKEN_ENV}=<token> (free registration at "
            "https://www.banxico.org.mx/SieAPIRest; never committed, GEN-02)."
        )
    session = session or build_session()
    start_d, end_d = date.fromisoformat(start), date.fromisoformat(end)
    if start_d > end_d:
        raise ValueError(f"start {start} > end {end}")

    ids = list(series_ids.values())
    names = {sid: name for name, sid in series_ids.items()}
    if len(names) != len(ids):
        raise ValueError("series_ids maps distinct names to a duplicated SIE id")
    columns: dict[str, list[pd.Series]] = {name: [] for name in series_ids}
    for i in range(0, len(ids), MAX_SERIES_PER_REQUEST):
        batch = ids[i : i + MAX_SERIES_PER_REQUEST]
        for lo, hi in _date_chunks(start_d, end_d, MAX_YEARS_PER_REQUEST):
            url = f"{SIE_BASE}/{','.join(batch)}/datos/{lo.isoformat()}/{hi.isoformat()}"
            response = session.get(url, headers={"Bmx-Token": token}, timeout=_TIMEOUT_S)
            if response.status_code != 200:
                raise RuntimeError(f"SIE request failed ({response.status_code}): {response.text}")
            for serie in response.json()["bmx"]["series"]:
                datos = serie.get("datos") or []
                if datos:
                    columns[names[serie["idSerie"]]].append(_parse_datos(datos))

    out = pd.DataFrame(
        {name: pd.concat(parts).sort_index() for name, parts in columns.items() if parts}
    )
    out = out.reindex(columns=list(series_ids))
    out.index.name = "Fecha"
    return out.sort_index()
