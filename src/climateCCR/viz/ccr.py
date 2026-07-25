"""CCR result figures: EE/PE profiles and climate-vs-baseline shifts.

Input contract: the *comparison frame* written by the climate-jump pipelines —
one row per ``(netting_agreement_id, default_times)`` with, per metric,
``<metric>_baseline``, ``<metric>_climate``, and ``<metric>_shift`` columns
(``pipelines/01_climate_jump_demo.py``; grid and metrics per DC-CCR-RISK-2).
Functions take DataFrames, never engine objects, so any run that emits the
schema is plottable regardless of the models behind it.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from .style import (
    COLOR_BASELINE,
    COLOR_CLIMATE,
    COLOR_SHIFT_DOWN,
    COLOR_SHIFT_UP,
    SERIES_COLORS,
    TEXT_SECONDARY,
)

LABEL_BASELINE = "Baseline (jump-off)"
LABEL_CLIMATE = "Climate (jump-on)"

# Panel grids stay readable up to this many counterparties; the Mexican book
# carries 30 netting agreements (INT-21), so beyond it the panels show the
# most-shifted ones — the counterparties the climate channel actually moves.
MAX_PANELS = 6

# Display names for the metric column stems used by the comparison frame.
METRIC_LABELS = {
    "uncollateralized_ee": "Uncollateralised EE",
    "uncollateralized_pe_0.99": "Uncollateralised PE 99%",
    "collateralized_ee": "Collateralised EE",
    "collateralized_pe_0.99": "Collateralised PE 99%",
}


def _grid_axis(ax, dates, max_ticks: int = 8) -> np.ndarray:
    """Evenly spaced x positions for a B3 reporting grid; ticks keep the dates.

    The default grid is a *tenor* grid (0D … 30Y), so in calendar time its last
    pillars sit decades apart: on the Mexican book (grid to 2077, INT-21) a date
    axis squeezes every informative pillar into the left edge. One position per
    pillar gives each equal width, which is how B3 exposure profiles are read.
    """
    # Full dates: the near pillars are days apart, so a coarser format repeats.
    labels = pd.to_datetime(pd.Series(list(dates))).dt.strftime("%Y-%m-%d")
    x = np.arange(len(labels))
    step = max(1, math.ceil(len(x) / max_ticks))
    ax.set_xticks(x[::step], labels.iloc[::step], rotation=30, ha="right")
    return x


def _mean_shift(comparison: pd.DataFrame, metric: str) -> pd.Series:
    """Mean ``metric`` shift per counterparty, over the reporting grid."""
    return comparison.groupby("netting_agreement_id")[f"{metric}_shift"].mean()


def _selection_note(shown: Sequence[int], comparison: pd.DataFrame) -> str:
    """Title suffix disclosing a truncated panel selection (empty when complete)."""
    total = comparison["netting_agreement_id"].nunique()
    return "" if len(shown) == total else f" — {len(shown)} most-shifted of {total} counterparties"


def _counterparty_panels(
    comparison: pd.DataFrame, counterparties: Sequence[int] | None, metric: str
) -> tuple[list[int], Figure, np.ndarray]:
    """One panel per counterparty, two columns, shared x.

    Without an explicit selection, books larger than ``MAX_PANELS`` are cut to
    the counterparties with the largest ``|mean shift|`` in ``metric``.
    """
    if counterparties is not None:
        ids = list(counterparties)
    else:
        ranked = _mean_shift(comparison, metric).abs().sort_values(ascending=False)
        ids = sorted(ranked.index[:MAX_PANELS])
    ncols = min(2, len(ids))
    nrows = math.ceil(len(ids) / ncols)
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(4.6 * ncols, 2.9 * nrows), sharex=True, squeeze=False
    )
    for ax in axes.flat[len(ids) :]:
        ax.set_visible(False)
    return ids, fig, axes


def plot_exposure_profiles(
    comparison: pd.DataFrame,
    metric: str = "uncollateralized_ee",
    counterparties: Sequence[int] | None = None,
) -> Figure:
    """Baseline vs climate profile of ``metric``, one panel per counterparty."""
    ids, fig, axes = _counterparty_panels(comparison, counterparties, metric)
    label = METRIC_LABELS.get(metric, metric)
    for ax, naid in zip(axes.flat, ids, strict=False):
        block = comparison[comparison["netting_agreement_id"] == naid]
        x = _grid_axis(ax, block["default_times"])
        ax.plot(x, block[f"{metric}_baseline"], color=COLOR_BASELINE, label=LABEL_BASELINE)
        ax.plot(x, block[f"{metric}_climate"], color=COLOR_CLIMATE, label=LABEL_CLIMATE)
        ax.set_title(f"Counterparty {naid}")
    axes.flat[0].legend()
    fig.supylabel(label, fontsize=9, color=TEXT_SECONDARY)
    fig.suptitle(
        f"{label} — climate jump-on vs baseline{_selection_note(ids, comparison)}",
        fontsize=11,
        fontweight="bold",
    )
    return fig


def plot_exposure_shift(
    comparison: pd.DataFrame,
    metric: str = "uncollateralized_ee",
    counterparties: Sequence[int] | None = None,
) -> Figure:
    """The climate component alone: ``metric`` shift (jump-on − baseline) per counterparty."""
    ids, fig, axes = _counterparty_panels(comparison, counterparties, metric)
    label = METRIC_LABELS.get(metric, metric)
    for ax, naid in zip(axes.flat, ids, strict=False):
        block = comparison[comparison["netting_agreement_id"] == naid]
        x = _grid_axis(ax, block["default_times"])
        shift = block[f"{metric}_shift"].to_numpy()
        ax.axhline(0.0, color=TEXT_SECONDARY, linewidth=0.8)
        ax.fill_between(
            x, shift, 0.0, where=shift >= 0, color=COLOR_SHIFT_UP, alpha=0.30, interpolate=True
        )
        ax.fill_between(
            x,
            shift,
            0.0,
            where=shift <= 0,
            color=COLOR_SHIFT_DOWN,
            alpha=0.30,
            interpolate=True,
        )
        ax.plot(x, shift, color=TEXT_SECONDARY, linewidth=1.2)
        ax.set_title(f"Counterparty {naid}")
    fig.supylabel(f"{label} shift", fontsize=9, color=TEXT_SECONDARY)
    fig.suptitle(
        f"{label} — climate shift (jump-on − baseline){_selection_note(ids, comparison)}",
        fontsize=11,
        fontweight="bold",
    )
    return fig


def plot_mean_shift_summary(
    comparison: pd.DataFrame,
    metrics: Sequence[str] = ("uncollateralized_ee", "uncollateralized_pe_0.99"),
) -> Figure:
    """Book overview: mean shift per counterparty, one panel per metric.

    Every counterparty is shown — this is the whole-book view — so the panel
    grows with the book rather than truncating it.
    """
    means = comparison.groupby("netting_agreement_id")[[f"{m}_shift" for m in metrics]].mean()
    height = max(2.6, 0.22 * len(means))
    fig, axes = plt.subplots(1, len(metrics), figsize=(4.2 * len(metrics), height), squeeze=False)
    for ax, metric in zip(axes.flat, metrics, strict=False):
        values = means[f"{metric}_shift"]
        colors = [COLOR_SHIFT_UP if v > 0 else COLOR_SHIFT_DOWN for v in values]
        bars = ax.barh([str(i) for i in values.index], values.to_numpy(), color=colors, height=0.55)
        ax.axvline(0.0, color=TEXT_SECONDARY, linewidth=0.8)
        # Decimals help fixture-scale shifts and only clutter MXN-scale ones.
        fmt = "%+.0f" if values.abs().max() >= 100 else "%+.1f"
        ax.bar_label(bars, fmt=fmt, fontsize=8, color=TEXT_SECONDARY, padding=3)
        ax.set_title(METRIC_LABELS.get(metric, metric))
        ax.set_ylabel("Counterparty")
        ax.margins(x=0.15)
    fig.suptitle("Mean climate shift by counterparty", fontsize=11, fontweight="bold")
    return fig


def plot_scenario_band(
    frames: Mapping[str, pd.DataFrame],
    metric: str = "uncollateralized_ee",
) -> Figure:
    """Book-mean ``metric`` shift over the grid, one line per scenario.

    The λ-sensitivity view (INT-20/INT-21): each comparison frame is one
    arrival-intensity scenario run on the *same* book and seed, so the spread
    between the lines is the climate channel's sensitivity to λ alone. Scenario
    order is the caller's (headline first); each legend entry carries that
    scenario's mean shift — the number the results chapter reports.
    """
    if not frames:
        raise ValueError("frames is empty: pass at least one scenario comparison frame")
    label = METRIC_LABELS.get(metric, metric)
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    ax.axhline(0.0, color=TEXT_SECONDARY, linewidth=0.8)
    for color, (name, frame) in zip(SERIES_COLORS, frames.items(), strict=False):
        profile = frame.groupby("default_times")[f"{metric}_shift"].mean()
        x = _grid_axis(ax, profile.index)
        ax.plot(x, profile.to_numpy(), color=color, label=f"{name} (mean {profile.mean():+,.0f})")
    ax.set_ylabel(f"{label} shift, book mean")
    ax.legend(title="Arrival-intensity scenario")
    fig.suptitle(
        f"{label} — climate shift across arrival-intensity scenarios",
        fontsize=11,
        fontweight="bold",
    )
    return fig
