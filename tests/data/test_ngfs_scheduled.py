"""Units for the fase producer (pipelines/22) — calendar bridge, raw basing, fragments."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REGION = "EIRIN 1.0|North America"
VALUATION = "2026-07-17"
WINDOW = (2025.0, 2030.0)


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def producer():
    return _load("ngfs_scheduled_shocks", "pipelines/22_ngfs_scheduled_shocks.py")


@pytest.fixture(scope="module")
def demo():
    return _load("climate_jump_demo", "pipelines/01_climate_jump_demo.py")


def tidy_frame() -> pd.DataFrame:
    """Miniature tidy frame: linear policy ramp + two linear equity sectors."""
    offsets = {"Q1": 0.0, "Q2": 0.25, "Q3": 0.5, "Q4": 0.75, "Year": 0.5}
    rows = []
    for scenario in ("Baseline", "HWTP"):
        for year in range(2025, 2031):
            for quarter in ("Q1", "Q2", "Q3", "Q4"):
                t = year + offsets[quarter]
                value = 5.0 if scenario == "Baseline" else 5.0 + 0.2 * (t - 2025.0)
                rows.append(
                    {
                        "model": "EIRIN",
                        "scenario": scenario,
                        "region": REGION,
                        "variable": "Policy rate",
                        "unit": "%",
                        "year": year,
                        "subannual": quarter,
                        "value": value,
                    }
                )
    for sector, slope in (("Market Services", -2.0), ("Consumer Goods Industries", 1.0)):
        for year in range(2023, 2031):
            rows.append(
                {
                    "model": "CLIMACRED",
                    "scenario": "HWTP",
                    "region": "Mexico - MEX",
                    "variable": f"equity_relative_adjustment|{sector}",
                    "unit": "% vs BAU",
                    "year": year,
                    "subannual": "Year",
                    "value": slope * (year - 2023),
                }
            )
    frame = pd.DataFrame(rows)
    frame["time"] = frame["year"] + frame["subannual"].map(offsets)
    return frame


def test_calendar_bridge_round_trip(producer):
    # decimal year -> date is the nearest-day inverse of pipelines/16's
    # _decimal_year (<= 12 h quantization), and the Act/365 fraction matches
    # the engine's (d - t0).days / 365 at that date exactly.
    for t in (2025.0, 2026.75, 2027.5, 2030.25):
        date = producer.decimal_year_to_date(t)
        assert abs(producer._decimal_year(str(date.date())) - t) <= 0.5 / 365.0 + 1e-9
    valuation = pd.Timestamp(VALUATION)
    frac = producer.act365_from(valuation, [2026.75])[0]
    expected = (producer.decimal_year_to_date(2026.75) - valuation).days / 365.0
    assert frac == pytest.approx(expected)


def test_scheduled_path_raw_basing_and_clip(producer):
    times = np.array([2025.0, 2026.0, 2027.0, 2031.0, 2031.5])
    values = np.array([0.0, 1.0, 2.0, 6.0, 7.0])
    t, v = producer.scheduled_path(times, values, VALUATION, WINDOW)
    # Raw basing: t=0 carries the interpolated published value at the
    # valuation date (the engine pins the overlay there; step 1 = catch-up).
    assert t[0] == 0.0
    t0 = producer._decimal_year(VALUATION)
    assert v[0] == pytest.approx(np.interp(t0, times, values))
    # Clip: points at/above window[1] + 1.0 = 2031.0 dropped (_signed_peak rule).
    assert len(t) == 2 and v[-1] == 2.0
    assert all(np.diff(t) > 0)
    with pytest.raises(ValueError):  # valuation outside the published span
        producer.scheduled_path(np.array([2028.0, 2029.0]), np.array([0.0, 1.0]), VALUATION, WINDOW)


def test_equity_paths_log_units_shared_axis_crosswalk(producer):
    frame = tidy_frame()
    leg = {
        "variable_family": "equity_relative_adjustment",
        "sectors": {
            "WALMEX_SHARE": "Market Services",
            "HCITY_SHARE": "Market Services",
            "FEMSA_SHARE": "Consumer Goods Industries",
        },
    }
    by_name = producer.equity_paths(frame, "HWTP", leg, VALUATION, WINDOW)
    assert set(by_name) == set(leg["sectors"])
    t_w, v_w = by_name["WALMEX_SHARE"]
    t_h, v_h = by_name["HCITY_SHARE"]
    t_f, v_f = by_name["FEMSA_SHARE"]
    assert t_w == t_h == t_f  # one shared axis per channel
    assert v_w == v_h and v_w != v_f  # same sector -> same path
    # Log units on the published % vs BAU: last kept point is 2030.5 -> -14 %.
    assert v_w[-1] == pytest.approx(np.log1p(-14.0 / 100.0))


def test_build_fragment_units_and_overlay_round_trip(producer):
    from climateCCR.processes.scheduled_shocks import ScheduledShockOverlay

    frame = tidy_frame()
    shock = {
        "window": list(WINDOW),
        "curve_name": "MXN_ZERO_YIELD_CURVE",
        "region": REGION,
        "scenarios": ["HWTP"],
        "equity_leg": {
            "variable_family": "equity_relative_adjustment",
            "sectors": {"WALMEX_SHARE": "Market Services"},
        },
    }
    block = producer.build_fragment(frame, "HWTP", shock, VALUATION)
    ScheduledShockOverlay.from_config(block)  # engine-schema round trip
    # Rate units pp -> decimal: the linear ramp is exact under interpolation.
    t0 = producer._decimal_year(VALUATION)
    delta_t0 = block["rate_shocks"]["deltas"]["MXN_ZERO_YIELD_CURVE"][0]
    assert delta_t0 == pytest.approx(0.2 * (t0 - 2025.0) / 100.0)
    assert block["equity_shocks"]["targets"] == ["WALMEX_SHARE"]


def test_fragment_guard_valuation_mismatch(demo, tmp_path):
    bad = tmp_path / "frag.yaml"
    bad.write_text("provenance:\n  valuation_date: '2020-01-01'\nscheduled_shocks: {}\n")
    with pytest.raises(ValueError, match="valuation_date"):
        demo.load_scheduled_fragment(bad, VALUATION)
    ok = tmp_path / "ok.yaml"
    ok.write_text(f"provenance:\n  valuation_date: '{VALUATION}'\nscheduled_shocks: {{a: 1}}\n")
    assert demo.load_scheduled_fragment(ok, VALUATION)["scheduled_shocks"] == {"a": 1}
