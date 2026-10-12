"""Units for the static-book back-pricing (pipelines/31) — INT-40 tier E generators and seams."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def pipeline():
    return _load("static_book_backtest", "pipelines/31_static_book_backtest.py")


@pytest.fixture
def pillars_csv(tmp_path):
    path = tmp_path / "zero_curve_pillars.csv"
    pd.DataFrame({"t_years": [0.1, 1.0, 5.0, 10.0], "zero": [0.04, 0.045, 0.05, 0.06]}).to_csv(
        path, index=False
    )
    return path


def test_dated_calibration_config_ends_every_window_at_the_date(pipeline):
    mc = {
        "windows": {"full_2006": ["2006-01-02", None], "last10y": ["2016-01-01", None]},
        "curve": {"valuation_date": None, "lookback_bd": 10},
        "other": 1,
    }
    cfg = pipeline.dated_calibration_config(mc, "2016-07-15", "market_calibration_bt_2016_07_15")
    assert cfg["windows"] == {
        "full_2006": ["2006-01-02", "2016-07-15"],
        "last10y": ["2016-01-01", "2016-07-15"],
    }
    assert cfg["curve"]["valuation_date"] == "2016-07-15"
    assert cfg["output_dir"] == "market_calibration_bt_2016_07_15"
    assert mc["windows"]["full_2006"][1] is None  # the input is untouched


def test_restrike_shifts_maturities_and_reads_rates_off_the_dated_curve(pipeline, pillars_csv):
    book = {
        "valuation_date": "2026-07-17",
        "book_root": "data/ccr_book_mx",
        "fetch": {"start": "2001-01-01", "cache_subdir": "data/market_mx/yahoo/book"},
        "inputs": {"hw1f_direct_input": "x.csv"},
        "rate_scale_output_dir": "results/loss_to_rate_scale_mx",
        "trade_rules": {"irs": {"fixed_rate_by_tenor": {5: 0.0875, 10: 0.0940}}},
        "counterparties": [
            {"naid": 1, "issuer": "A", "bonds": [[0.0980, "2031-06-15", 240]]},
            {
                "naid": 2,
                "issuer": "B",
                "bonds": [
                    {"tipo": "frn", "sobretasa": 0.0039, "vencimiento": "2029-07-16", "fuente": "u"}
                ],
            },
            {"naid": 3, "issuer": "C"},
        ],
    }
    cfg = pipeline.restrike_book_config(
        book,
        "2016-07-15",
        "2026-07-17",
        pillars_csv,
        book_root="data/ccr_book_mx_bt",
        cache_subdir="data/market_mx/yahoo/book_bt",
        hw1f_direct_input="results/cal/direct_input/RFE_HW1F_Calibration_MX.csv",
        rate_scale_output_dir="results/scale_bt",
    )
    assert cfg["valuation_date"] == "2016-07-15" and cfg["book_root"] == "data/ccr_book_mx_bt"
    assert cfg["trade_rules"]["irs"]["fixed_rate_by_tenor"] == {5: 0.05, 10: 0.06}
    fija = cfg["counterparties"][0]["bonds"][0]
    assert fija["vencimiento"] == "2021-06-13"  # shifted by the same 3,654-day offset
    tenor = (pd.Timestamp("2021-06-13") - pd.Timestamp("2016-07-15")).days / 365.25
    assert fija["cupon"] == pytest.approx(pipeline.zero_at(pillars_csv, tenor) + 0.024, abs=1e-6)
    frn = cfg["counterparties"][1]["bonds"][0]
    assert frn == {"tipo": "frn", "sobretasa": 0.0039, "vencimiento": "2019-07-15"}
    assert "bonds" not in cfg["counterparties"][2]
    assert book["counterparties"][0]["bonds"] == [[0.0980, "2031-06-15", 240]]  # input untouched


def test_dated_jump_config_reinverts_rate_marks_and_sets_the_backtest_grid(pipeline):
    jump = {
        "valuation_date": "2026-07-17",
        "horizons": {"largo": {"b3_grid": None, "max_step_days": None}},
        "climate_jumps": {"intensity": 19.2857, "rate_marks": {"median": 5.1658e-6}},
    }
    cfg = pipeline.dated_jump_config(jump, "2019-07-15", ["0D", "1W", "1Y"], 175.0, 140.0)
    assert cfg["horizons"] == {"backtest": {"b3_grid": ["0D", "1W", "1Y"], "max_step_days": None}}
    assert cfg["climate_jumps"]["rate_marks"]["median"] == pytest.approx(5.1658e-6 * 1.25)
    assert jump["horizons"] == {"largo": {"b3_grid": None, "max_step_days": None}}


def test_realised_scenarios_slice_like_a_joint_draw(pipeline):
    from climateCCR.simulation.multi_risk_factor_simulation import slice_scenarios

    index = pd.bdate_range("2016-07-11", "2016-08-19")
    series = {
        "A_SHARE": pd.Series(np.arange(len(index), dtype=float) + 100.0, index=index),
        "MXN_ZERO_YIELD_CURVE": pd.Series(0.04, index=index),
    }
    union = [pd.Timestamp("2016-07-15"), pd.Timestamp("2016-07-24"), pd.Timestamp("2016-08-15")]
    joint = pipeline.realised_scenarios(list(series), union, series, 10)
    assert joint["A_SHARE"].shape == (1, 3)
    assert joint["A_SHARE"][0, 1] == series["A_SHARE"].loc["2016-07-22"]  # Sunday -> Friday close
    sliced = slice_scenarios(joint, ["A_SHARE"], union[::2])
    np.testing.assert_array_equal(sliced["A_SHARE"], joint["A_SHARE"][:, [0, 2]])
    with pytest.raises(ValueError, match="no observation"):
        pipeline.realised_scenarios(["A_SHARE"], [pd.Timestamp("2017-01-01")], series, 10)
