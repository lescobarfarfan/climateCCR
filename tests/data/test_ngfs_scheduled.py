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
    families = (
        ("equity_relative_adjustment", "% vs BAU", {"Market Services": -2.0}),
        ("equity_relative_adjustment", "% vs BAU", {"Consumer Goods Industries": 1.0}),
        ("corporate_bond_spread_adjustment", "pp vs BAU", {"Market Services": 0.5}),
        ("corporate_bond_spread_adjustment", "pp vs BAU", {"Consumer Goods Industries": -0.05}),
    )
    for family, unit, slopes in families:
        for sector, slope in slopes.items():
            for year in range(2023, 2031):
                rows.append(
                    {
                        "model": "CLIMACRED",
                        "scenario": "HWTP",
                        "region": "Mexico - MEX",
                        "variable": f"{family}|{sector}",
                        "unit": unit,
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
    log_units = producer.SECTOR_CHANNELS[0][3]
    by_name = producer.sector_paths(frame, "HWTP", leg, VALUATION, WINDOW, log_units)
    assert set(by_name) == set(leg["sectors"])
    t_w, v_w = by_name["WALMEX_SHARE"]
    t_h, v_h = by_name["HCITY_SHARE"]
    t_f, v_f = by_name["FEMSA_SHARE"]
    assert t_w == t_h == t_f  # one shared axis per channel
    assert v_w == v_h and v_w != v_f  # same sector -> same path
    # Log units on the published % vs BAU: last kept point is 2030.5 -> -14 %.
    assert v_w[-1] == pytest.approx(np.log1p(-14.0 / 100.0))


def test_spread_paths_linear_units_shared_axis_issuer_fan_out(producer):
    frame = tidy_frame()
    leg = {
        "variable_family": "corporate_bond_spread_adjustment",
        "sectors": {
            "FIBRAHOTEL": "Market Services",
            "ALSEA": "Market Services",
            "FEMSA": "Consumer Goods Industries",
        },
    }
    pp_units = producer.SECTOR_CHANNELS[1][3]
    by_issuer = producer.sector_paths(frame, "HWTP", leg, VALUATION, WINDOW, pp_units)
    assert set(by_issuer) == set(leg["sectors"])
    t_h, v_h = by_issuer["FIBRAHOTEL"]
    assert by_issuer["ALSEA"] == (t_h, v_h)  # same sector -> same path
    assert t_h == by_issuer["FEMSA"][0]  # one shared axis
    # Linear units (pp -> decimal, no log): last kept point 2030.5 -> +3.5 pp -> 0.035.
    assert v_h[-1] == pytest.approx(0.5 * (2030 - 2023) / 100.0)
    # Raw basing: t=0 carries the published pp interpolated at the valuation date.
    years = [y + 0.5 for y in range(2023, 2031)]  # annual rows sit at mid-year
    published_pp = [0.5 * k for k in range(len(years))]
    t0 = producer._decimal_year(VALUATION)
    assert v_h[0] == pytest.approx(np.interp(t0, years, published_pp) / 100.0)


def test_build_fragment_units_and_overlay_round_trip(producer):
    from climateCCR.processes.scheduled_shocks import ScheduledShockOverlay, SpreadSchedule

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
        "bond_leg": {
            "variable_family": "corporate_bond_spread_adjustment",
            "sectors": {"FEMSA": "Consumer Goods Industries"},
        },
    }
    block = producer.build_fragment(frame, "HWTP", shock, VALUATION)
    overlay = ScheduledShockOverlay.from_config(block)  # engine-schema round trip
    assert overlay.target_names == {"MXN_ZERO_YIELD_CURVE", "WALMEX_SHARE"}  # no issuers
    assert SpreadSchedule.from_config(block["spread_shocks"]).target_names == {"FEMSA"}
    # Rate units pp -> decimal: the linear ramp is exact under interpolation.
    t0 = producer._decimal_year(VALUATION)
    delta_t0 = block["rate_shocks"]["deltas"]["MXN_ZERO_YIELD_CURVE"][0]
    assert delta_t0 == pytest.approx(0.2 * (t0 - 2025.0) / 100.0)
    assert block["equity_shocks"]["targets"] == ["WALMEX_SHARE"]
    assert block["spread_shocks"]["targets"] == ["FEMSA"]
    assert block["spread_shocks"]["spreads"]["FEMSA"][-1] == pytest.approx(-0.05 * 7 / 100.0)


def test_book_spread_schedule_guard(demo, tmp_path):
    (tmp_path / "BONDS.csv").write_text("trade_id,issuer_name,spread\n1,FEMSA,0.01\n")
    gp = {
        "prototype_data_paths": {"trades": {"DEBT": str(tmp_path) + "/"}},
        "prototype_data_files": {
            "trades": {"DEBT": {"BOND_FIXED": "BONDS.csv", "BOND_FRN": "BONDS.csv"}}
        },
    }
    block = {"targets": ["FEMSA"], "times_years": [0.0, 1.0], "spreads": {"FEMSA": [0.0, 0.01]}}
    assert demo.book_spread_schedule(block, gp).target_names == frozenset({"FEMSA"})
    disjoint = {"targets": ["PEMEX"], "times_years": [0.0], "spreads": {"PEMEX": [0.0]}}
    with pytest.raises(ValueError, match="no issuer"):
        demo.book_spread_schedule(disjoint, gp)
    no_debt = {"prototype_data_paths": {"trades": {}}, "prototype_data_files": {"trades": {}}}
    with pytest.raises(ValueError, match="no issuer"):  # a book without a DEBT desk
        demo.book_spread_schedule(block, no_debt)


def test_fragment_guard_valuation_mismatch(demo, tmp_path):
    bad = tmp_path / "frag.yaml"
    bad.write_text("provenance:\n  valuation_date: '2020-01-01'\nscheduled_shocks: {}\n")
    with pytest.raises(ValueError, match="valuation_date"):
        demo.load_scheduled_fragment(bad, VALUATION)
    ok = tmp_path / "ok.yaml"
    ok.write_text(f"provenance:\n  valuation_date: '{VALUATION}'\nscheduled_shocks: {{a: 1}}\n")
    assert demo.load_scheduled_fragment(ok, VALUATION)["scheduled_shocks"] == {"a": 1}
