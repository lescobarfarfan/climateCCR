"""Process-level figures: simulated paths, fans, and jump-event diagnostics.

Input contract: path-major arrays (DC-CONV-10) — ``paths`` of shape
``(n_paths, n_steps + 1)`` on a date grid of length ``n_steps + 1`` — plus the
``event_counts`` array of a ``ClimateJumpScenario`` (``(n_paths, n_steps)``,
events in ``(t_i, t_{i+1}]`` landing on grid date ``t_{i+1}``). Any diffusion
or jump model that emits these shapes is plottable unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from .ccr import LABEL_BASELINE, LABEL_CLIMATE
from .style import COLOR_BASELINE, COLOR_CLIMATE, SERIES_COLORS, TEXT_SECONDARY


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


def _cumulative_intensity(years: np.ndarray, times: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Expected cumulative arrivals of a trajectory intensity on ``years``.

    The intensity prevailing over each step is its value at the step START
    (``ClimateJumpProcess`` draws ``lambda(t_i) * dt_i``), held beyond the last
    point (``np.interp`` clamp) — so this is the engine's own expectation, not
    a smoother quadrature.
    """
    rate = np.interp(years, times, values)
    return np.concatenate([[0.0], np.cumsum(rate[:-1] * np.diff(years))])


def _expected_arrivals(years: np.ndarray, intensity) -> tuple[np.ndarray, str]:
    """(expected cumulative events, legend label) for a scalar or trajectory intensity."""
    if isinstance(intensity, Mapping):
        times = np.asarray(intensity["times_years"], dtype=float)
        values = np.asarray(intensity["values"], dtype=float)
        return _cumulative_intensity(years, times, values), r"Expected $\int_0^t \lambda(u)\,du$"
    return float(intensity) * years, r"Expected $\lambda t$"


def plot_event_arrivals(
    dates: Sequence[datetime],
    event_counts: np.ndarray,
    intensity: float | Mapping[str, Sequence[float]] | None = None,
) -> Figure:
    """Mechanism check: mean cumulative climate events vs the Poisson expectation.

    With a homogeneous intensity the observed mean should track ``lambda * t``
    (Act/365 year fractions, the engine's grid time); a trajectory intensity
    ``{"times_years", "values"}`` (the DC-CCR-SIM-2 config form, years from the
    first grid date) tracks its step-start cumulative ``∫ lambda(u) du``.
    """
    grid = _as_datetime_index(dates)
    mean_cumulative = event_counts.cumsum(axis=1).mean(axis=0)
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    ax.plot(grid[1:], mean_cumulative, color=COLOR_CLIMATE, label="Observed mean (Monte Carlo)")
    if intensity is not None:
        years = (grid - grid[0]).days / 365.0
        expected, label = _expected_arrivals(years, intensity)
        ax.plot(grid, expected, color=TEXT_SECONDARY, linestyle="--", linewidth=1.2, label=label)
    ax.legend(loc="upper left")
    ax.set_ylabel("Cumulative climate events per path")
    ax.set_title("Climate jump arrivals — simulated vs expected")
    return fig


def plot_intensity_paths(
    paths: Mapping[str, Mapping[str, Sequence[float]]],
    baseline: float,
    horizon_years: float,
) -> Figure:
    """Trajectory arrival intensities vs the constant headline, with cumulative arrivals.

    Input: ``label -> {"times_years", "values"}`` (the DC-CCR-SIM-2 intensity
    trajectory form — Act/365 years from the valuation date, events/yr; each
    path holds its last value beyond its last point, the engine's ``np.interp``
    clamp) plus the constant ``baseline`` intensity. Left: ``lambda(t)`` to
    ``horizon_years`` (the held stretch dotted); right: the expected cumulative
    arrivals per path against ``baseline * t`` — the time-averaged intensity
    the exposure integral actually feels (INT-34: a 43% terminal rise is a
    ~20% average rise over the exposure-weighted horizon).
    """
    if not paths:
        raise ValueError("paths is empty: pass label -> {times_years, values}")
    grid = np.linspace(0.0, float(horizon_years), 401)
    fig, (ax_rate, ax_cum) = plt.subplots(1, 2, figsize=(8.6, 3.2))
    ax_rate.axhline(
        baseline,
        color=TEXT_SECONDARY,
        linestyle="--",
        linewidth=1.2,
        label=f"Headline (constant {baseline:g}/yr)",
    )
    ax_cum.plot(
        grid, baseline * grid, color=TEXT_SECONDARY, linestyle="--", linewidth=1.2, label="Headline"
    )
    for color, (label, path) in zip(SERIES_COLORS, paths.items(), strict=False):
        times = np.asarray(path["times_years"], dtype=float)
        values = np.asarray(path["values"], dtype=float)
        rate = np.interp(grid, times, values)
        inside = grid <= times[-1]
        ax_rate.plot(
            grid[inside],
            rate[inside],
            color=color,
            label=f"{label} ({values[0]:.2f} → {values[-1]:.2f}/yr, held after {times[-1]:.2f}y)",
        )
        ax_rate.plot(grid[~inside], rate[~inside], color=color, linestyle=":", linewidth=1.2)
        ax_cum.plot(grid, _cumulative_intensity(grid, times, values), color=color, label=label)
    ax_rate.set_xlabel("Years from valuation (Act/365)")
    ax_rate.set_ylabel(r"Arrival intensity $\lambda(t)$ (events/yr)")
    ax_rate.legend(fontsize=7.5, loc="upper left")
    ax_cum.set_xlabel("Years from valuation (Act/365)")
    ax_cum.set_ylabel("Expected cumulative events")
    ax_cum.legend(fontsize=7.5, loc="upper left")
    fig.suptitle(
        r"Trajectory $\lambda(t)$ riders vs the constant headline intensity",
        fontsize=11,
        fontweight="bold",
    )
    return fig


# Scheduled-shock channels beyond the rate leg: (channel, value key, display units, y label).
_SCHEDULED_PANELS = (
    ("equity_shocks", "log_factors", lambda v: 100.0 * np.expm1(v), "Equity adjustment (%)"),
    ("spread_shocks", "spreads", lambda v: 100.0 * v, "Credit-spread delta (pp)"),
)


def _first_per_group(targets: Sequence[str], groups: Mapping[str, str] | None) -> dict[str, str]:
    """``label -> representative target``: names sharing a group ride one published path."""
    series: dict[str, str] = {}
    for target in targets:
        series.setdefault(groups.get(target, target) if groups else target, target)
    return series


def plot_scheduled_shock_paths(
    fragments: Mapping[str, Mapping[str, Mapping]],
    groups: Mapping[str, str] | None = None,
) -> Figure:
    """The scheduled (fase) scenario paths themselves, straight from the fragments.

    Input: ``scenario -> scheduled_shocks block`` (the DC-CCR-SIM-2 scheduled
    overlay contract, INT-33/34): ``rate_shocks`` ``{targets, times_years,
    deltas}`` in decimal rate, ``equity_shocks`` ``{…, log_factors}`` and,
    once the Phase-2 channel exists, ``spread_shocks`` ``{…, spreads}`` — all
    on Act/365 years from the valuation date, the t=0 point carrying the
    accumulated-to-valuation catch-up the pinned engine applies at step 1,
    held beyond the last point. ``groups`` maps target names to a group (the
    GEM-E3 sector crosswalk): every name in a group rides the same published
    path, so one line per group is exact. Top: the rate delta (pp) per
    scenario (◆ = the t=0 catch-up); below, one panel per scenario and channel.
    """
    if not fragments:
        raise ValueError("fragments is empty: pass scenario -> scheduled_shocks block")
    scenarios = list(fragments)
    panels = [p for p in _SCHEDULED_PANELS if any(p[0] in f for f in fragments.values())]
    nrows, ncols = 1 + len(panels), len(scenarios)
    fig = plt.figure(figsize=(1.0 + 3.1 * ncols, 2.7 * nrows))
    gs = fig.add_gridspec(nrows, ncols)
    ax_rate = fig.add_subplot(gs[0, :])
    ax_rate.axhline(0.0, color=TEXT_SECONDARY, linewidth=0.8)
    for color, scenario in zip(SERIES_COLORS, scenarios, strict=False):
        block = fragments[scenario].get("rate_shocks")
        if not block:
            continue
        times = np.asarray(block["times_years"], dtype=float)
        for target in block["targets"]:
            values = 100.0 * np.asarray(block["deltas"][target], dtype=float)
            ax_rate.plot(times, values, color=color, marker="o", markersize=2.5, label=scenario)
            ax_rate.plot(
                times[:1], values[:1], linestyle="none", marker="D", markersize=6, color=color
            )
    ax_rate.set_ylabel("Rate delta vs baseline (pp)")
    ax_rate.set_xlabel("Years from valuation (Act/365)")
    ax_rate.legend(fontsize=8, title="Scenario")
    ax_rate.set_title("Scheduled policy-rate path (◆ = the t=0 catch-up)", fontsize=10)
    for row, (channel, key, units, ylabel) in enumerate(panels, start=1):
        legend_ax = None
        for col, scenario in enumerate(scenarios):
            ax = fig.add_subplot(gs[row, col])
            ax.axhline(0.0, color=TEXT_SECONDARY, linewidth=0.8)
            block = fragments[scenario].get(channel)
            if block:
                legend_ax = legend_ax or ax
                times = np.asarray(block["times_years"], dtype=float)
                series = _first_per_group(block["targets"], groups)
                for i, (label, target) in enumerate(series.items()):
                    ax.plot(
                        times,
                        units(np.asarray(block[key][target], dtype=float)),
                        color=SERIES_COLORS[i % len(SERIES_COLORS)],
                        linestyle="-" if i < len(SERIES_COLORS) else "--",
                        label=label,
                    )
            ax.set_title(f"{scenario} — {channel.replace('_', ' ')}", fontsize=9)
            ax.set_xlabel("Years from valuation")
            if col == 0:
                ax.set_ylabel(ylabel)
        if legend_ax is not None:  # groups are shared across scenarios: one legend per row
            legend_ax.legend(fontsize=6.5, loc="best")
    fig.suptitle(
        "Scheduled (fase) scenario paths — NGFS short-term, raw published deltas",
        fontsize=11,
        fontweight="bold",
    )
    return fig


def plot_annual_aggregate_loss(
    losses: Mapping[str, np.ndarray], quantiles: Sequence[float] = (0.5, 0.99)
) -> Figure:
    """Simulated annual aggregate climate-loss distributions, one per scenario.

    Input: ``label -> per-simulation annual aggregate loss`` (the
    compound-Poisson ``S = sum of severities`` in real MDP, [Klugman2019]).
    Step histograms share log-spaced bins; each ``quantiles`` entry is marked
    per scenario and quoted in the legend — the aggregate-loss-quantile
    robustness read of the results chapter (INT-23). Zero-loss simulations
    (no events that year) are dropped from the log axis and disclosed in the
    legend when present.
    """
    if not losses:
        raise ValueError("losses is empty: pass label -> per-simulation aggregate losses")
    positives = {
        k: np.asarray(v, dtype=float)[np.asarray(v, dtype=float) > 0] for k, v in losses.items()
    }
    lo = min(v.min() for v in positives.values())
    hi = max(v.max() for v in positives.values())
    bins = np.geomspace(lo, hi, 70)
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    for color, (label, sample) in zip(SERIES_COLORS, losses.items(), strict=False):
        sample = np.asarray(sample, dtype=float)
        zeros = int((sample <= 0).sum())
        marks = ", ".join(f"q{q:.0%} {float(np.quantile(sample, q)):,.0f}" for q in quantiles)
        note = f"; P(S=0) {zeros / sample.size:.2%}" if zeros else ""
        ax.hist(
            positives[label],
            bins=bins,
            density=True,
            histtype="step",
            linewidth=1.4,
            color=color,
            label=f"{label} — {marks}{note}",
        )
        for q in quantiles:
            ax.axvline(float(np.quantile(sample, q)), color=color, linestyle="--", linewidth=0.9)
    ax.set_xscale("log")
    ax.set_xlabel("Annual aggregate loss (MDP 2025)")
    ax.set_ylabel("Density")
    ax.legend(fontsize=8)
    ax.set_title("Annual aggregate climate loss — compound-Poisson simulation")
    return fig
