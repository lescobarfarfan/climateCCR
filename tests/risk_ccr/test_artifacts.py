"""Units for the optional per-path value artifacts (OQ-GEN-02 c)."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
from climateCCR.risk.ccr.evaluators.artifacts import (
    grid_dates,
    read_per_path_values,
    reporting_slice,
    write_per_path_values,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_reporting_slice_picks_grid_columns_in_order():
    simulation_dates = ["2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01"]
    grid = ["2026-02-01", "2026-04-01"]
    values = np.arange(8, dtype=float).reshape(2, 4)
    sliced = reporting_slice(simulation_dates, grid, values)
    np.testing.assert_array_equal(sliced, values[:, [1, 3]])
    with pytest.raises(ValueError, match="Reporting grid"):
        reporting_slice(simulation_dates[:2], grid, values[:, :2])


def test_write_read_round_trip(tmp_path):
    store = {
        "23": (grid_dates(["2026-01-01", "2026-07-01"]), np.array([[1.0, -2.0], [3.0, 4.0]])),
        "42": (grid_dates(["2026-01-01", "2026-07-01"]), np.zeros((2, 2))),
    }
    path = write_per_path_values(store, tmp_path / "per_path_values_baseline.npz")
    back = read_per_path_values(path)
    assert set(back) == {"23", "42"}
    dates, values = back["23"]
    assert list(dates) == ["2026-01-01", "2026-07-01"]
    np.testing.assert_array_equal(values, store["23"][1])
    with pytest.raises(ValueError, match="empty"):
        write_per_path_values({}, tmp_path / "empty.npz")
    with pytest.raises(ValueError, match="do not match"):
        write_per_path_values(
            {"1": (grid_dates(["2026-01-01"]), np.zeros((2, 3)))}, tmp_path / "bad.npz"
        )


def _load_pipeline_20():
    spec = importlib.util.spec_from_file_location(
        "aggregate_loss_figures", REPO_ROOT / "pipelines" / "20_aggregate_loss_figures.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_book_exposure_sums_positive_parts_across_counterparties():
    pipeline = _load_pipeline_20()
    dates = grid_dates(["2026-01-01", "2026-07-01"])
    per_path = {
        "1": (dates, np.array([[1.0, -5.0], [2.0, 3.0]])),
        "2": (dates, np.array([[-1.0, 4.0], [1.0, -3.0]])),
    }
    got_dates, book = pipeline.book_exposure(per_path)
    np.testing.assert_array_equal(got_dates, dates)
    np.testing.assert_array_equal(book, np.array([[1.0, 4.0], [3.0, 3.0]]))
    with pytest.raises(ValueError, match="grid differs"):
        pipeline.book_exposure(
            {
                "1": (dates, np.zeros((1, 2))),
                "2": (grid_dates(["2026-01-01", "2026-08-01"]), np.zeros((1, 2))),
            }
        )


def test_simulate_annual_losses_matches_compound_poisson_moments():
    pipeline = _load_pipeline_20()
    rng = np.random.default_rng(7)
    lam, median, sigma = 2.0, 100.0, 0.8
    losses = pipeline.simulate_annual_losses(lam, median, sigma, 200_000, rng)
    mean_severity = median * np.exp(sigma**2 / 2)
    assert losses.mean() == pytest.approx(lam * mean_severity, rel=0.02)
    assert (losses == 0).mean() == pytest.approx(np.exp(-lam), rel=0.05)
