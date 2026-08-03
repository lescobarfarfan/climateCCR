"""NGFS short-term scenario connector (OQ-CCR-03; MKT-NGFS-03; DC-MKT-NGFS-1).

Reads the tidy CSVs written by ``pipelines/15_download_ngfs.py`` and derives
the two curve-shock anchors of MKT-NGFS-02, adapted to what the short-term
vintage actually publishes [NGFS2025ST]:

- **Short anchor** — the EIRIN ``Policy rate`` (quarterly, macro-region grain;
  Mexico rides ``EIRIN 1.0|North America``, see ``configs/ngfs_short_term.yaml``),
  differenced against the package's own IMF-WEO-anchored ``Baseline`` run
  (OQ-MKT-05: the within-model delta).
- **Long anchor** — the CLIMACRED ``sovereign_spread_adjustment_incl_policy|MEX``
  (annual, Mexico country grain), published directly as a delta vs BAU. The
  ``incl_policy`` variant is the *total* sovereign-yield move at the long end
  (policy transmission + spread), so each tenor uses exactly one number and
  nothing is double-counted; the excl-policy variant is kept for decomposition.

The equity/corporate leg (OQ-MKT-13 c) reads the CLIMACRED 50-sector families
the same way: ``equity_relative_adjustment|<sector>`` (% vs BAU) and
``corporate_bond_spread_adjustment|<sector>`` (pp vs BAU, *excl.* policy — the
shocked curve already carries the policy + sovereign move at both anchors, so
the cebur leg takes only the credit-spread component on top; the incl-policy
variant would double-count). ``sector_peak`` extracts their signed peak.

All deltas are in percentage points (or percent, for the ``*_rel_*`` and
equity families), as published; the pp/% -> decimal conversion belongs to the
shock builder (pipelines/16).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

POLICY_RATE = "Policy rate"
SOVEREIGN_INCL_POLICY = "sovereign_spread_adjustment_incl_policy|MEX"
SOVEREIGN_EXCL_POLICY = "sovereign_spread_adjustment|MEX"

_QUARTER_OFFSET = {"Q1": 0.0, "Q2": 0.25, "Q3": 0.5, "Q4": 0.75, "Year": 0.5}


@dataclass(frozen=True)
class AnchorDeltas:
    """Peak curve-shock anchors for one scenario, in percentage points."""

    scenario: str
    short_pp: float
    long_pp: float
    short_peak_time: float  # decimal year of the short-anchor peak
    long_peak_time: float


def load_short_term(data_dir: str | Path) -> pd.DataFrame:
    """Concatenate the per-model tidy CSVs from the download pipeline."""
    data_dir = Path(data_dir)
    files = sorted(data_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No NGFS short-term CSVs under {data_dir} — run pipelines/15_download_ngfs.py first"
        )
    frame = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
    frame["time"] = frame["year"] + frame["subannual"].map(_QUARTER_OFFSET)
    if frame["time"].isna().any():
        bad = sorted(frame.loc[frame["time"].isna(), "subannual"].unique())
        raise ValueError(f"Unknown subannual labels: {bad}")
    return frame


def policy_rate_delta(
    frame: pd.DataFrame, scenario: str, *, region: str, baseline: str = "Baseline"
) -> pd.DataFrame:
    """Quarterly policy-rate delta (scenario − baseline) in pp: columns time, delta_pp."""
    rates = frame[(frame["variable"] == POLICY_RATE) & (frame["region"] == region)]
    wide = rates.pivot_table(index="time", columns="scenario", values="value")
    for name in (scenario, baseline):
        if name not in wide.columns:
            raise KeyError(f"Scenario {name!r} has no {POLICY_RATE!r} rows for region {region!r}")
    delta = (wide[scenario] - wide[baseline]).dropna()
    return delta.rename("delta_pp").reset_index()


def sovereign_adjustment(
    frame: pd.DataFrame, scenario: str, *, variable: str = SOVEREIGN_INCL_POLICY
) -> pd.DataFrame:
    """Annual Mexican sovereign adjustment (already a delta vs BAU) in pp."""
    rows = frame[(frame["variable"] == variable) & (frame["scenario"] == scenario)]
    if rows.empty:
        raise KeyError(f"Scenario {scenario!r} has no {variable!r} rows")
    return (
        rows[["time", "value"]]
        .rename(columns={"value": "delta_pp"})
        .sort_values("time")
        .reset_index(drop=True)
    )


def _signed_peak(path: pd.DataFrame, window: tuple[float, float]) -> tuple[float, float]:
    lo, hi = window
    inside = path[(path["time"] >= lo) & (path["time"] < hi + 1.0)]
    if inside.empty:
        raise ValueError(f"No observations inside the window {window}")
    row = inside.loc[inside["delta_pp"].abs().idxmax()]
    return float(row["delta_pp"]), float(row["time"])


def anchor_peaks(
    frame: pd.DataFrame,
    scenario: str,
    *,
    region: str,
    window: tuple[float, float] = (2025.0, 2030.0),
    long_variable: str = SOVEREIGN_INCL_POLICY,
) -> AnchorDeltas:
    """Peak (max |delta|, sign preserved) anchors over the scenario window.

    The stress-standard "most adverse point" of the fixed flavor (INT-12):
    the short anchor peaks on the quarterly policy path, the long anchor on
    the annual sovereign path — each at its own published grain.
    """
    short_pp, short_time = _signed_peak(policy_rate_delta(frame, scenario, region=region), window)
    long_pp, long_time = _signed_peak(
        sovereign_adjustment(frame, scenario, variable=long_variable), window
    )
    return AnchorDeltas(scenario, short_pp, long_pp, short_time, long_time)


def sector_peak(
    frame: pd.DataFrame,
    scenario: str,
    *,
    variable: str,
    window: tuple[float, float] = (2025.0, 2030.0),
) -> tuple[float, float]:
    """Signed peak (max |value|, sign kept) of an already-delta CLIMACRED series.

    The fixed-flavor extraction of ``anchor_peaks`` for the sector families
    (``equity_relative_adjustment|<sector>``, ``corporate_bond_spread_adjustment
    |<sector>``): no Baseline differencing — CLIMACRED publishes deltas vs BAU.
    Returns ``(peak, decimal_year_of_peak)`` in the series' published unit.
    """
    return _signed_peak(sovereign_adjustment(frame, scenario, variable=variable), window)
