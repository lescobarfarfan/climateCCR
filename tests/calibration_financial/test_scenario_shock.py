"""Units for the two-anchor curve shock + the pipelines/16 CSV rewrite."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from climateCCR.calibration.financial.scenario_shock import shock_zero_pillars

REPO_ROOT = Path(__file__).resolve().parents[2]

TENORS = np.array([0.00274, 0.0833, 1.0, 5.0417, 10.0, 30.0])
ZEROS = np.array([0.066, 0.068, 0.068, 0.086, 0.094, 0.100])


def test_shock_clamps_flat_outside_anchors():
    shocked = shock_zero_pillars(TENORS, ZEROS, short_pp=1.0, long_pp=3.0)
    np.testing.assert_allclose(shocked[:2] - ZEROS[:2], 0.01)  # at/below the short anchor
    np.testing.assert_allclose(shocked[-2:] - ZEROS[-2:], 0.03)  # at/beyond the long anchor


def test_shock_linear_between_anchors():
    shocked = shock_zero_pillars(TENORS, ZEROS, short_pp=1.0, long_pp=3.0)
    weight = (5.0417 - 0.0833) / (10.0 - 0.0833)
    expected_pp = 1.0 + weight * 2.0
    assert shocked[3] - ZEROS[3] == pytest.approx(expected_pp / 100.0)


def test_shock_preserves_sign_and_shape():
    shocked = shock_zero_pillars(TENORS, ZEROS, short_pp=-0.5, long_pp=-0.5)
    np.testing.assert_allclose(shocked, ZEROS - 0.005)
    with pytest.raises(ValueError):
        shock_zero_pillars(TENORS, ZEROS[:-1], short_pp=1.0, long_pp=1.0)
    with pytest.raises(ValueError):
        shock_zero_pillars(TENORS, ZEROS, short_pp=1.0, long_pp=1.0, short_tenor=10, long_tenor=1)


def _load_pipeline_16():
    spec = importlib.util.spec_from_file_location(
        "ngfs_shock_curves", REPO_ROOT / "pipelines" / "16_ngfs_shock_curves.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_shock_direct_input_csv_rewrites_only_the_pillars(tmp_path):
    """The direct_input rewrite: V* shift by the anchor profile, all else verbatim."""
    pipeline = _load_pipeline_16()
    tenors = ["1D", "28D", "2Y", "10Y", "30Y"]
    zeros = [0.066, 0.068, 0.074, 0.094, 0.100]
    row = {f"rate_curve_V{i + 1}": z for i, z in enumerate(zeros)}
    row |= {f"rate_curve_T{i + 1}": t for i, t in enumerate(tenors)}
    row |= {"alpha": 0.0758, "volatility": 0.0081}
    csv = tmp_path / "RFE_HW1F_Calibration.csv"
    pd.DataFrame([row], index=pd.Index(["MXN_ZERO_YIELD_CURVE"], name="name")).to_csv(csv)

    anchors = {"short_tenor_years": 0.0833, "long_tenor_years": 10.0}
    pillars = pipeline.shock_direct_input_csv(csv, "MXN_ZERO_YIELD_CURVE", 1.0, 3.0, anchors)

    rewritten = pd.read_csv(csv, index_col=0).loc["MXN_ZERO_YIELD_CURVE"]
    assert rewritten["alpha"] == pytest.approx(0.0758)  # dynamics untouched
    assert rewritten["volatility"] == pytest.approx(0.0081)
    assert list(rewritten[[f"rate_curve_T{i + 1}" for i in range(5)]]) == tenors
    assert rewritten["rate_curve_V1"] == pytest.approx(0.066 + 0.01)  # short anchor
    assert rewritten["rate_curve_V4"] == pytest.approx(0.094 + 0.03)  # long anchor
    assert rewritten["rate_curve_V5"] == pytest.approx(0.100 + 0.03)  # flat beyond
    assert (pillars["zero_shocked"] > pillars["zero"]).all()

    with pytest.raises(KeyError):
        pipeline.shock_direct_input_csv(csv, "NO_SUCH_CURVE", 1.0, 3.0, anchors)


EQUITY_LEG = {
    "spot_file": "market_data/Equity_Spot.csv",
    "gbm_files": [
        "calibration_data/RFE_models/RFE_GBM_Calibration.csv",
        "calibration_data/pricing_models/Pricing_GBM_Calibration.csv",
    ],
}
BOND_LEG = {"bonds_file": "portfolio_data/desks/DEBT/BONDS.csv"}


def _mini_overlay(tmp_path):
    """A miniature book overlay: 2 equities + FX in the GBM tables, 3 cebures."""
    overlay = tmp_path / "overlay"
    spot = pd.DataFrame({"name": ["A_SHARE", "B_SHARE"], "spot": [10.0, 20.0]})
    gbm = pd.DataFrame(
        {
            "initial_value": [10.0, 20.0, 18.3],
            "drift": [0.1, 0.2, 0.0],
            "volatility": [0.3, 0.2, 0.1],
        },
        index=pd.Index(["A_SHARE", "B_SHARE", "MXN_USD_FX_RATE"], name="name"),
    )
    bonds = pd.DataFrame(
        {
            "trade_id": [1, 2, 3],
            "notional": [100.0, 100.0, 100.0],
            "coupon": [0.09, 0.096, 0.099],
            "spread": [0.024, 0.016, 0.0185],
            "issuer_name": ["X", "Y", "Y"],
        }
    )
    (overlay / "market_data").mkdir(parents=True)
    spot.to_csv(overlay / EQUITY_LEG["spot_file"], index=False)
    for rel in EQUITY_LEG["gbm_files"]:
        (overlay / rel).parent.mkdir(parents=True, exist_ok=True)
        gbm.to_csv(overlay / rel)
    (overlay / BOND_LEG["bonds_file"]).parent.mkdir(parents=True)
    bonds.to_csv(overlay / BOND_LEG["bonds_file"], index=False)
    return overlay


def test_shock_equity_csvs_revalues_named_spots_only(tmp_path):
    pipeline = _load_pipeline_16()
    overlay = _mini_overlay(tmp_path)
    pipeline.shock_equity_csvs(overlay, {"A_SHARE": -20.0}, EQUITY_LEG)

    spot = pd.read_csv(overlay / EQUITY_LEG["spot_file"]).set_index("name")["spot"]
    assert spot["A_SHARE"] == pytest.approx(8.0)  # -20% revaluation
    assert spot["B_SHARE"] == pytest.approx(20.0)  # unmapped name untouched
    for rel in EQUITY_LEG["gbm_files"]:
        table = pd.read_csv(overlay / rel, index_col=0)
        assert table.loc["A_SHARE", "initial_value"] == pytest.approx(8.0)
        assert table.loc["MXN_USD_FX_RATE", "initial_value"] == pytest.approx(18.3)  # FX never
        assert table.loc["A_SHARE", "drift"] == pytest.approx(0.1)  # dynamics untouched
        assert table.loc["A_SHARE", "volatility"] == pytest.approx(0.3)

    with pytest.raises(KeyError):
        pipeline.shock_equity_csvs(overlay, {"NO_SUCH_SHARE": -1.0}, EQUITY_LEG)
    with pytest.raises(ValueError):
        pipeline.shock_equity_csvs(overlay, {"A_SHARE": -100.0}, EQUITY_LEG)


def test_shock_bond_spreads_additive_with_zero_floor(tmp_path):
    pipeline = _load_pipeline_16()
    overlay = _mini_overlay(tmp_path)
    floors = pipeline.shock_bond_spreads(overlay, {"X": 2.5, "Y": -3.0}, BOND_LEG)

    bonds = pd.read_csv(overlay / BOND_LEG["bonds_file"])
    assert bonds.loc[0, "spread"] == pytest.approx(0.049)  # 240 bp + 250 bp
    assert bonds.loc[1, "spread"] == pytest.approx(0.0)  # 160 bp - 300 bp -> floored
    assert bonds.loc[2, "spread"] == pytest.approx(0.0)
    assert floors == {"Y": 2}
    assert bonds.loc[0, "coupon"] == pytest.approx(0.09)  # other columns untouched

    with pytest.raises(KeyError):
        pipeline.shock_bond_spreads(overlay, {"NO_SUCH_ISSUER": 1.0}, BOND_LEG)


def test_zero_deltas_are_a_no_op(tmp_path):
    pipeline = _load_pipeline_16()
    overlay = _mini_overlay(tmp_path)
    before = {
        rel: (overlay / rel).read_bytes()
        for rel in [EQUITY_LEG["spot_file"], *EQUITY_LEG["gbm_files"], BOND_LEG["bonds_file"]]
    }
    pipeline.shock_equity_csvs(overlay, {"A_SHARE": 0.0, "B_SHARE": 0.0}, EQUITY_LEG)
    floors = pipeline.shock_bond_spreads(overlay, {"X": 0.0, "Y": 0.0}, BOND_LEG)
    assert floors == {}
    for rel, blob in before.items():
        assert (overlay / rel).read_bytes() == blob, f"zero-delta rewrite changed {rel}"
