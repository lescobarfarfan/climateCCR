"""Process-level figures: simulated paths, fans, and jump-event diagnostics.

Input contract: path-major arrays (DC-CONV-10) — ``paths`` of shape
``(n_paths, n_steps + 1)`` on a date grid of length ``n_steps + 1`` — plus the
``event_counts`` array of a ``ClimateJumpScenario`` (``(n_paths, n_steps)``,
events in ``(t_i, t_{i+1}]`` landing on grid date ``t_{i+1}``). Any diffusion
or jump model that emits these shapes is plottable unchanged.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from .ccr import LABEL_BASELINE, LABEL_CLIMATE
from .style import COLOR_BASELINE, COLOR_CLIMATE, TEXT_SECONDARY


def _as_datetime_index(dates: Sequence[datetime]) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(pd.to_datetime(list(dates)))


# Above this many paths, per-event markers become noise and are omitted.
_MAX_MARKED_PATHS = 25


def plot_sample_paths(
    dates: Sequence[datetime],
    baseline_paths: np.ndarray,
    climate_paths: np.ndarray,
    event_counts: np.ndarray | None = None,
    n_show: int | None = 6,
    ylabel: str = "",
    title: str = "",
) -> Figure:
    """Paths jump-off vs jump-on, with the jump events marked.

    Both runs share the diffusion draws (INT-09), so each climate path deviates
    from its baseline twin only at (and after) the marked climate events.

    ``n_show`` picks the first N paths; ``None`` draws **every** trajectory
    (line width and opacity thin out adaptively, so the full set reads as the
    two scenario envelopes). Event markers are omitted beyond
    ``_MAX_MARKED_PATHS`` paths — at that density they would cover the plot.
    """
    grid = _as_datetime_index(dates)
    n_total = baseline_paths.shape[0]
    n_show = n_total if n_show is None else min(n_show, n_total)
    few = n_show <= 12
    linewidth = 1.1 if few else 0.5
    alpha = 0.75 if few else float(np.clip(30.0 / n_show, 0.02, 0.4))
    mark_events = event_counts is not None and n_show <= _MAX_MARKED_PATHS
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    for p in range(n_show):
        ax.plot(grid, baseline_paths[p], color=COLOR_BASELINE, linewidth=linewidth, alpha=alpha)
        ax.plot(grid, climate_paths[p], color=COLOR_CLIMATE, linewidth=linewidth, alpha=alpha)
        if mark_events:
            steps = np.flatnonzero(event_counts[p])
            if steps.size:
                ax.plot(
                    grid[steps + 1],
                    climate_paths[p, steps + 1],
                    linestyle="none",
                    marker="o",
                    markersize=5,
                    markerfacecolor=COLOR_CLIMATE,
                    markeredgecolor="white",
                    markeredgewidth=1.0,
                )
    handles = [
        Line2D([], [], color=COLOR_BASELINE, label=LABEL_BASELINE),
        Line2D([], [], color=COLOR_CLIMATE, label=LABEL_CLIMATE),
    ]
    if mark_events:
        handles.append(
            Line2D(
                [],
                [],
                linestyle="none",
                marker="o",
                markersize=5,
                markerfacecolor=COLOR_CLIMATE,
                markeredgecolor="white",
                label="Climate jump event",
            )
        )
    ax.legend(handles=handles, loc="upper left")
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    return fig


def plot_fan_comparison(
    dates: Sequence[datetime],
    baseline_paths: np.ndarray,
    climate_paths: np.ndarray,
    quantiles: tuple[float, float] = (0.05, 0.95),
    ylabel: str = "",
    title: str = "",
) -> Figure:
    """Distribution fan (quantile band + median) of both runs on one axis."""
    grid = _as_datetime_index(dates)
    lo, hi = sorted(quantiles)
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    for paths, color in ((baseline_paths, COLOR_BASELINE), (climate_paths, COLOR_CLIMATE)):
        band = np.quantile(paths, [lo, 0.5, hi], axis=0)
        ax.fill_between(grid, band[0], band[2], color=color, alpha=0.18, linewidth=0)
        ax.plot(grid, band[1], color=color)
    band_pct = f"{lo:.0%}–{hi:.0%}"
    ax.legend(
        handles=[
            Line2D([], [], color=COLOR_BASELINE, label=f"{LABEL_BASELINE} median"),
            Line2D([], [], color=COLOR_CLIMATE, label=f"{LABEL_CLIMATE} median"),
            Patch(facecolor=TEXT_SECONDARY, alpha=0.18, label=f"{band_pct} band"),
        ],
        loc="upper left",
    )
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    return fig


def plot_event_arrivals(
    dates: Sequence[datetime],
    event_counts: np.ndarray,
    intensity: float | None = None,
) -> Figure:
    """Mechanism check: mean cumulative climate events vs the Poisson expectation.

    With a homogeneous intensity the observed mean should track ``lambda * t``
    (Act/365 year fractions, the engine's grid time).
    """
    grid = _as_datetime_index(dates)
    mean_cumulative = event_counts.cumsum(axis=1).mean(axis=0)
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    ax.plot(grid[1:], mean_cumulative, color=COLOR_CLIMATE, label="Observed mean (Monte Carlo)")
    if intensity is not None:
        years = (grid - grid[0]).days / 365.0
        ax.plot(
            grid,
            intensity * years,
            color=TEXT_SECONDARY,
            linestyle="--",
            linewidth=1.2,
            label=r"Expected $\lambda t$",
        )
    ax.legend(loc="upper left")
    ax.set_ylabel("Cumulative climate events per path")
    ax.set_title("Climate jump arrivals — simulated vs expected")
    return fig
