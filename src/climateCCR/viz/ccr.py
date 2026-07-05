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
from collections.abc import Sequence

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from .style import (
    COLOR_BASELINE,
    COLOR_CLIMATE,
    COLOR_SHIFT_DOWN,
    COLOR_SHIFT_UP,
    TEXT_SECONDARY,
)

LABEL_BASELINE = "Baseline (jump-off)"
LABEL_CLIMATE = "Climate (jump-on)"

# Display names for the metric column stems used by the comparison frame.
METRIC_LABELS = {
    "uncollateralized_ee": "Uncollateralised EE",
    "uncollateralized_pe_0.99": "Uncollateralised PE 99%",
    "collateralized_ee": "Collateralised EE",
    "collateralized_pe_0.99": "Collateralised PE 99%",
}


def _counterparty_panels(
    comparison: pd.DataFrame, counterparties: Sequence[int] | None
) -> tuple[list[int], Figure, np.ndarray]:
    """One panel per counterparty, two columns, shared x."""
    ids = list(counterparties or sorted(comparison["netting_agreement_id"].unique()))
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
    ids, fig, axes = _counterparty_panels(comparison, counterparties)
    label = METRIC_LABELS.get(metric, metric)
    for ax, naid in zip(axes.flat, ids, strict=False):
        block = comparison[comparison["netting_agreement_id"] == naid]
        dates = pd.to_datetime(block["default_times"])
        ax.plot(dates, block[f"{metric}_baseline"], color=COLOR_BASELINE, label=LABEL_BASELINE)
        ax.plot(dates, block[f"{metric}_climate"], color=COLOR_CLIMATE, label=LABEL_CLIMATE)
        ax.set_title(f"Counterparty {naid}")
    axes.flat[0].legend()
    fig.supylabel(label, fontsize=9, color=TEXT_SECONDARY)
    fig.suptitle(f"{label} — climate jump-on vs baseline", fontsize=11, fontweight="bold")
    fig.autofmt_xdate(rotation=30, ha="right")
    return fig


def plot_exposure_shift(
    comparison: pd.DataFrame,
    metric: str = "uncollateralized_ee",
    counterparties: Sequence[int] | None = None,
) -> Figure:
    """The climate component alone: ``metric`` shift (jump-on − baseline) per counterparty."""
    ids, fig, axes = _counterparty_panels(comparison, counterparties)
    label = METRIC_LABELS.get(metric, metric)
    for ax, naid in zip(axes.flat, ids, strict=False):
        block = comparison[comparison["netting_agreement_id"] == naid]
        dates = pd.to_datetime(block["default_times"])
        shift = block[f"{metric}_shift"].to_numpy()
        ax.axhline(0.0, color=TEXT_SECONDARY, linewidth=0.8)
        ax.fill_between(
            dates, shift, 0.0, where=shift >= 0, color=COLOR_SHIFT_UP, alpha=0.30, interpolate=True
        )
        ax.fill_between(
            dates,
            shift,
            0.0,
            where=shift <= 0,
            color=COLOR_SHIFT_DOWN,
            alpha=0.30,
            interpolate=True,
        )
        ax.plot(dates, shift, color=TEXT_SECONDARY, linewidth=1.2)
        ax.set_title(f"Counterparty {naid}")
    fig.supylabel(f"{label} shift", fontsize=9, color=TEXT_SECONDARY)
    fig.suptitle(f"{label} — climate shift (jump-on − baseline)", fontsize=11, fontweight="bold")
    fig.autofmt_xdate(rotation=30, ha="right")
    return fig


def plot_mean_shift_summary(
    comparison: pd.DataFrame,
    metrics: Sequence[str] = ("uncollateralized_ee", "uncollateralized_pe_0.99"),
) -> Figure:
    """Book overview: mean shift per counterparty, one panel per metric."""
    means = comparison.groupby("netting_agreement_id")[[f"{m}_shift" for m in metrics]].mean()
    fig, axes = plt.subplots(1, len(metrics), figsize=(4.2 * len(metrics), 2.6), squeeze=False)
    for ax, metric in zip(axes.flat, metrics, strict=False):
        values = means[f"{metric}_shift"]
        colors = [COLOR_SHIFT_UP if v > 0 else COLOR_SHIFT_DOWN for v in values]
        bars = ax.barh([str(i) for i in values.index], values.to_numpy(), color=colors, height=0.55)
        ax.axvline(0.0, color=TEXT_SECONDARY, linewidth=0.8)
        ax.bar_label(bars, fmt="%+.1f", fontsize=8, color=TEXT_SECONDARY, padding=3)
        ax.set_title(METRIC_LABELS.get(metric, metric))
        ax.set_ylabel("Counterparty")
        ax.margins(x=0.15)
    fig.suptitle("Mean climate shift by counterparty", fontsize=11, fontweight="bold")
    return fig
