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
