"""Units for the two-book comparison readout (pipelines/26): guards, MC yardstick, deltas."""

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
def readout():
    return _load("book_comparison_readout", "pipelines/26_book_comparison_readout.py")


def test_equity_targets_and_book_equities(tmp_path, readout):
    cfg = tmp_path / "jump.yaml"
    cfg.write_text(
        "climate_jumps:\n  intensity: 1.0\n  rate_marks:\n    targets: [MXN_ZERO_YIELD_CURVE]\n"
        "  equity_marks:\n    targets: [A_SHARE, B_SHARE]\n"
    )
    assert readout.equity_targets(cfg) == {"A_SHARE", "B_SHARE"}
    rate_only = tmp_path / "rate.yaml"
    rate_only.write_text("climate_jumps:\n  intensity: 1.0\n  rate_marks:\n    targets: [X]\n")
    assert readout.equity_targets(rate_only) == set()
    rfe = tmp_path / "calibration_data" / "RFE_models"
    rfe.mkdir(parents=True)
    pd.DataFrame(
        {"name": ["A_SHARE", "MXN_USD_FX_RATE", "B_SHARE"], "drift": [0.1, 0.0, 0.2]}
    ).to_csv(rfe / "RFE_GBM_Calibration.csv", index=False)
    assert readout.book_equities(tmp_path) == {"A_SHARE", "B_SHARE"}


def test_mc_sd_reads_the_book_shift_row_or_returns_nan(tmp_path, readout):
    csv = tmp_path / "seed_intervals.csv"
    pd.DataFrame(
        {
            "band": ["headline", "headline", "floor"],
            "metric": ["epe_shift_pct", "epe_baseline", "epe_shift_pct"],
            "netting_agreement_id": ["BOOK", "BOOK", "BOOK"],
            "n_seeds": [11, 11, 11],
            "sd": [0.02, 50.0, 0.03],
        }
    ).to_csv(csv, index=False)
    assert readout.mc_sd(csv, "headline") == (0.02, 11)
    sd, n = readout.mc_sd(csv, "ct_anchor")
    assert np.isnan(sd) and n == 0
    sd, n = readout.mc_sd(tmp_path / "missing.csv", "headline")
    assert np.isnan(sd) and n == 0


def test_band_deltas_difference_and_unpaired_yardstick(readout):
    table = pd.DataFrame(
        {
            "band": ["headline", "headline"],
            "band_label": ["H", "H"],
            "book": ["mexican", "comparison"],
            "epe_shift_pct": [-9.0, -3.0],
            "equity_component_pp": [-7.0, -1.0],
            "sum_w_gamma": [1.0, 0.24],
            "mc_sd_pp": [0.03, 0.04],
        }
    )
    out = readout.band_deltas(table, "mexican", "comparison")
    row = out.iloc[0]
    assert row["delta_pp"] == pytest.approx(-6.0)
    assert row["equity_component_delta_pp"] == pytest.approx(-6.0)
    assert row["mc_yardstick_pp"] == pytest.approx(0.05)
    assert row["z"] == pytest.approx(-120.0)
    assert (row["sum_w_gamma_first"], row["sum_w_gamma_second"]) == (1.0, 0.24)
