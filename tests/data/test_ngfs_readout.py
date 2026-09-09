"""Units for the NGFS EPE readout (pipelines/17) — per-pillar profile + the fase 0D pin."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DATES = ("2026-07-17", "2027-07-17", "2031-07-17")


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def readout():
    return _load("ngfs_epe_readout", "pipelines/17_ngfs_epe_readout.py")


def _frame(off: dict[int, list[float]], on: dict[int, list[float]]) -> pd.DataFrame:
    """Comparison frame (DC-CCR-RISK-3) for two netting sets on three pillars."""
    rows = []
    for naid, values in off.items():
        for date, ee_off, ee_on in zip(DATES, values, on[naid], strict=True):
            rows.append(
                {
                    "netting_agreement_id": naid,
                    "default_times": date,
                    "uncollateralized_ee_baseline": ee_off,
                    "uncollateralized_ee_climate": ee_on,
                    "uncollateralized_ee_shift": ee_on - ee_off,
                }
            )
    return pd.DataFrame(rows)


def _write(root: Path, run: str, frame: pd.DataFrame) -> None:
    (root / run).mkdir(parents=True)
    frame.to_csv(root / run / "ee_pe_climate_shift.csv", index=False)


def test_book_profile_sums_netting_sets_per_pillar(readout, tmp_path):
    off = {1: [10.0, 8.0, 2.0], 2: [5.0, 4.0, 0.0]}
    on = {1: [10.0, 7.0, 1.5], 2: [5.0, 3.5, 0.0]}
    _write(tmp_path, "base", _frame(off, on))
    profile = readout.book_profile(tmp_path, "base")
    assert list(profile.columns) == ["book_ee_off", "book_ee_on"]
    assert [d.strftime("%Y-%m-%d") for d in profile.index] == list(DATES)
    np.testing.assert_allclose(profile["book_ee_off"], [15.0, 12.0, 2.0])
    np.testing.assert_allclose(profile["book_ee_on"], [15.0, 10.5, 1.5])


def test_fase_pin_passes_on_identical_0d_and_fails_on_any_0d_delta(readout, tmp_path):
    off = {1: [10.0, 8.0, 2.0], 2: [5.0, 4.0, 0.0]}
    on = {1: [10.0, 7.0, 1.5], 2: [5.0, 3.5, 0.0]}
    _write(tmp_path, "base", _frame(off, on))
    # A fase cell: the 0D pillar identical per NAID, later pillars shocked.
    fase_off = {1: [10.0, 7.5, 1.9], 2: [5.0, 3.9, 0.0]}
    _write(tmp_path, "fase_ok", _frame(fase_off, on))
    readout.assert_fase_pin(tmp_path, "base", "fase_ok")
    # A nivel-like cell revalues the book at 0D — the pin must fire loudly.
    nivel_off = {1: [9.0, 7.5, 1.9], 2: [5.0, 3.9, 0.0]}
    _write(tmp_path, "nivel", _frame(nivel_off, on))
    with pytest.raises(ValueError, match="0D"):
        readout.assert_fase_pin(tmp_path, "base", "nivel")
