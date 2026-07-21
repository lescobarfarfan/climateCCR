"""Market-arm figures: rate-path fans and calibration diagnostics (INT-15).

Input contract: path-major arrays (DC-CONV-10) plus plain per-grid analytic
arrays — never model objects. The HW1F diagnostics here visualize the
MKT-CALIB-02 estimator cross-check: simulated trajectories against the model's
own expectation ``E[r(t)] = f(0,t) + curvature`` and marginal ``sd(t)``
(both computable by any conforming model), and the practical spread between
two parameter sets fitted to the same data.
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

from .style import SERIES_COLORS, TEXT_PRIMARY, TEXT_SECONDARY


def _as_datetime_index(dates: Sequence[datetime]) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(pd.to_datetime(list(dates)))


def plot_rate_path_fan(
    dates: Sequence[datetime],
    paths: np.ndarray,
    analytic_mean: np.ndarray,
    analytic_sd: np.ndarray,
    *,
    n_sd: float = 2.0,
    ylabel: str = "Short rate (%)",
    title: str = "",
) -> Figure:
    """Every trajectory at low opacity, MC mean highlighted, analytic overlay.

    ``paths`` is ``(n_paths, n_grid)``; ``analytic_mean``/``analytic_sd`` are
    the model's marginal expectation and standard deviation on the same grid.
    The Monte-Carlo mean (solid) should sit on the analytic expectation
    (dashed) within MC error — drawing both is the point: the simulator is
    checked against its own closed form.
    """
    grid = _as_datetime_index(dates)
    n_paths = paths.shape[0]
    alpha = float(np.clip(30.0 / n_paths, 0.02, 0.4))
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.plot(grid, paths.T, color=SERIES_COLORS[0], linewidth=0.4, alpha=alpha)
    ax.plot(grid, paths.mean(axis=0), color=SERIES_COLORS[0], linewidth=2.2)
    ax.plot(grid, analytic_mean, color=TEXT_PRIMARY, linestyle="--", linewidth=1.4)
    for sign in (-1.0, 1.0):
        ax.plot(
            grid,
            analytic_mean + sign * n_sd * analytic_sd,
            color=TEXT_PRIMARY,
            linestyle=":",
            linewidth=1.1,
        )
    ax.legend(
        handles=[
            Line2D([], [], color=SERIES_COLORS[0], linewidth=0.8, alpha=0.6, label="Trajectories"),
            Line2D([], [], color=SERIES_COLORS[0], linewidth=2.2, label="Monte-Carlo mean"),
            Line2D([], [], color=TEXT_PRIMARY, linestyle="--", label="Model $E[r(t)]$"),
            Line2D(
                [],
                [],
                color=TEXT_PRIMARY,
                linestyle=":",
                label=f"$E[r(t)] \\pm {n_sd:.0f}\\,sd(t)$",
            ),
        ],
        loc="upper left",
    )
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    return fig


def plot_estimator_fan_comparison(
    dates: Sequence[datetime],
    means: Sequence[np.ndarray],
    sds: Sequence[np.ndarray],
    labels: Sequence[str],
    *,
    n_sd: float = 2.0,
    ylabel: str = "Short rate (%)",
    title: str = "",
) -> Figure:
    """Analytic mean ±n·sd ribbons for competing parameter sets, one axis.

    Series colors follow the fixed categorical order (never re-sorted), so
    "estimator k" keeps its hue across every figure of a document.
    """
    if not len(means) == len(sds) == len(labels):
        raise ValueError("means, sds and labels must have the same length")
    grid = _as_datetime_index(dates)
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    handles = []
    for mean, sd, label, color in zip(means, sds, labels, SERIES_COLORS, strict=False):
        ax.fill_between(
            grid, mean - n_sd * sd, mean + n_sd * sd, color=color, alpha=0.15, linewidth=0
        )
        ax.plot(grid, mean, color=color)
        handles.append(Line2D([], [], color=color, label=label))
    handles.append(
        Patch(facecolor=TEXT_SECONDARY, alpha=0.15, label=f"mean $\\pm {n_sd:.0f}\\,sd(t)$")
    )
    ax.legend(handles=handles, loc="upper left")
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    return fig


def plot_jump_decay(
    alphas: Mapping[str, float],
    *,
    horizon_years: float = 15.0,
    jump_bp: float = 100.0,
    title: str = "",
) -> Figure:
    """How a rate jump fades under each mean reversion: ``jump * exp(-alpha*t)``.

    The climate rate channel injects marks into ``dr`` that decay through the
    HW1F mean reversion (DC-CCR-SIM-2), so ``alpha`` *is* the persistence of a
    climate rate shock; each curve is annotated with its half-life
    ``ln(2)/alpha``.
    """
    if not alphas:
        raise ValueError("alphas is empty")
    t = np.linspace(0.0, horizon_years, 301)
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    for (label, alpha), color in zip(alphas.items(), SERIES_COLORS, strict=False):
        half_life = np.log(2.0) / alpha
        ax.plot(t, jump_bp * np.exp(-alpha * t), color=color, label=label)
        if half_life <= horizon_years:
            ax.plot(
                half_life,
                jump_bp / 2.0,
                marker="o",
                markersize=6,
                markerfacecolor=color,
                markeredgecolor="white",
                markeredgewidth=1.0,
            )
            ax.annotate(
                f"{half_life:.1f}y",
                (half_life, jump_bp / 2.0),
                textcoords="offset points",
                xytext=(6, 6),
                fontsize=8,
                color=TEXT_SECONDARY,
            )
    ax.axhline(jump_bp / 2.0, color=TEXT_SECONDARY, linewidth=0.8, linestyle=":")
    ax.set_xlabel("Years after the jump")
    ax.set_ylabel(f"Remaining rate impact (bp of {jump_bp:.0f})")
    ax.legend(loc="upper right")
    if title:
        ax.set_title(title)
    return fig
