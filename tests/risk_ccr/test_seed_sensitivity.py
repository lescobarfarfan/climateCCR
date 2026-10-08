"""Units for the multi-seed precision study (pipelines/24): config generation + intervals."""

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def seed_study():
    return _load("seed_sensitivity", "pipelines/24_seed_sensitivity.py")


def test_write_seed_config_changes_only_seed(tmp_path, seed_study):
    adopted = tmp_path / "band.yaml"
    adopted.write_text(
        'seed: 1\nn_paths: 10\nvaluation_date: "2026-07-17"\n'
        "climate_jumps:\n  intensity: 19.2857\n  rate_marks:\n    median: 5.1658e-6\n"
        "    targets: [MXN_ZERO_YIELD_CURVE]\n"
    )
    out = seed_study.write_seed_config(adopted, 7, tmp_path / "configs")
    assert out.name == "band__seed7.yaml"
    generated = yaml.safe_load(out.read_text())
    assert generated == yaml.safe_load(adopted.read_text()) | {"seed": 7}
    assert generated["valuation_date"] == "2026-07-17"  # still a string, not a date


def test_seed_intervals_summarizes_across_seeds(seed_study):
    rows = pd.DataFrame(
        {
            "band": "headline",
            "seed": [1, 2, 3],
            "canonical": [True, False, False],
            "metric": "epe_shift_pct",
            "netting_agreement_id": "BOOK",
            "value": [-9.0, -8.0, -10.0],
        }
    )
    out = seed_study.seed_intervals(rows)
    assert list(out.columns) == seed_study.KEYS + seed_study.INTERVAL_COLUMNS
    row = out.iloc[0]
    assert row["n_seeds"] == 3
    assert row["canonical_value"] == -9.0
    assert row["mean"] == pytest.approx(-9.0)
    assert row["sd"] == pytest.approx(1.0)
    assert (row["min"], row["max"]) == (-10.0, -8.0)
    assert row["rel_sd"] == pytest.approx(1.0 / 9.0)
    with pytest.raises(ValueError, match="canonical"):
        seed_study.seed_intervals(rows.assign(canonical=False))


def test_band_label(seed_study):
    assert seed_study.band_label("climate_jump_real_mexican") == "headline"
    assert seed_study.band_label("climate_jump_real_mexican_floor") == "floor"
