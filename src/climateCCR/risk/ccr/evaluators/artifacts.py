"""Optional per-run artifacts of the exposure pipeline (OQ-GEN-02 c).

The valuation session computes per-path netted portfolio values (settlement
currency) on the full simulation grid but exports only summary exposures
(``CCR_Valuation_Session.get_exposures``). ``pipelines/01 --trayectorias``
materializes the reporting-date slice per counterparty — one compressed
``.npz`` per run leg — from which the aggregate-loss / distribution figures
draw (``pipelines/20``). Plain numeric/string arrays only, never pickles
(GEN-04); the run's manifest covers provenance (GEN-06).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

PerPathStore = Mapping[str, tuple[np.ndarray, np.ndarray]]


def reporting_slice(
    simulation_dates: Sequence, b3_default_grid: Sequence, portfolio_values: np.ndarray
) -> np.ndarray:
    """The ``(n_paths, n_reporting_dates)`` slice of the simulation-grid values.

    Mirrors the date walk of ``compute_exposures``: reporting dates keep their
    simulation-grid order. Raises if any reporting date is missing from the
    simulation grid.
    """
    grid = set(b3_default_grid)
    idx = [i for i, date in enumerate(simulation_dates) if date in grid]
    if len(idx) != len(b3_default_grid):
        raise ValueError(
            f"Reporting grid has {len(b3_default_grid)} dates but only {len(idx)} "
            "are on the simulation grid"
        )
    return np.asarray(portfolio_values, dtype=float)[:, idx]


def grid_dates(b3_default_grid: Sequence) -> np.ndarray:
    """Reporting dates as ISO-day strings (the npz-safe date encoding)."""
    return np.asarray([pd.Timestamp(date).strftime("%Y-%m-%d") for date in b3_default_grid])


def write_per_path_values(store: PerPathStore, out_path: Path | str) -> Path:
    """One compressed npz: ``dates_<naid>`` (ISO strings) + ``values_<naid>``.

    ``store`` maps counterparty id -> ``(dates, values)`` with ``values`` of
    shape ``(n_paths, n_dates)`` — the :func:`reporting_slice` output.
    """
    if not store:
        raise ValueError("store is empty: nothing to write")
    arrays: dict[str, np.ndarray] = {}
    for naid, (dates, values) in store.items():
        values = np.asarray(values, dtype=float)
        if values.ndim != 2 or values.shape[1] != len(dates):
            raise ValueError(
                f"Counterparty {naid!r}: values {values.shape} do not match {len(dates)} dates"
            )
        arrays[f"dates_{naid}"] = np.asarray(dates)
        arrays[f"values_{naid}"] = values
    out_path = Path(out_path)
    np.savez_compressed(out_path, **arrays)
    return out_path


def read_per_path_values(path: Path | str) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Inverse of :func:`write_per_path_values`: ``naid -> (dates, values)``."""
    out: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    with np.load(path) as archive:
        for key in archive.files:
            if key.startswith("values_"):
                naid = key.removeprefix("values_")
                out[naid] = (archive[f"dates_{naid}"], archive[key])
    if not out:
        raise ValueError(f"No per-path arrays in {path}")
    return out
