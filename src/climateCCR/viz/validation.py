"""Model-vs-observed validation figures: calibrated simulations against reality.

Input contract (INT-15): path-major arrays (DC-CONV-10) — ``paths`` of shape
``(n_paths, n_steps + 1)`` on a date grid of length ``n_steps + 1`` — plus tidy
observed series (``pd.Series`` on a ``DatetimeIndex``) and plain event-date /
mark arrays. Never model objects: any estimator whose simulation emits these
shapes is comparable against its data unchanged.

Color semantics (fixed within this module, distinct from the scenario pair):
**model output = deep green** (cone, stems, QQ points), **observed reality =
near-black**. Every fan annotates its empirical band coverage — the fraction of
observed points inside the nominal envelope — the standard fan-chart backtest.
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
from scipy import stats

from .style import COLOR_BASELINE, TEXT_PRIMARY, TEXT_SECONDARY

COLOR_MODEL = COLOR_BASELINE
COLOR_OBSERVED = TEXT_PRIMARY

# Band opacity ladder endpoints: outermost band lightest, innermost darkest.
_BAND_ALPHA_RANGE = (0.12, 0.30)


def _as_datetime_index(dates: Sequence[datetime]) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(pd.to_datetime(list(dates)))


def _band_bounds(central: float) -> tuple[float, float]:
    lo = (1.0 - central) / 2.0
    return lo, 1.0 - lo


def band_coverage(
    dates: Sequence[datetime],
    paths: np.ndarray,
    observed: pd.Series,
    central: float = 0.95,
) -> float | None:
    """Fraction of observed points inside the central ``central`` simulated band.

    The fan-chart backtest statistic: band bounds are per-date path quantiles,
    linearly interpolated in time at the observed dates. Observations outside
    the simulation span are ignored; returns ``None`` if none remain.
    """
    grid = _as_datetime_index(dates)
    obs = observed.dropna().sort_index()
    obs = obs[(obs.index >= grid[0]) & (obs.index <= grid[-1])]
    if not len(obs):
        return None
    lo, hi = _band_bounds(central)
    band = np.quantile(np.asarray(paths), [lo, hi], axis=0)
    grid_t = grid.view("int64").astype(float)
    obs_t = obs.index.view("int64").astype(float)
    lo_at = np.interp(obs_t, grid_t, band[0])
    hi_at = np.interp(obs_t, grid_t, band[1])
    values = obs.to_numpy(dtype=float)
    return float(np.mean((values >= lo_at) & (values <= hi_at)))


def _draw_fan(
    ax,
    grid: pd.DatetimeIndex,
    paths: np.ndarray,
    observed: pd.Series | None,
    quantiles: Sequence[float],
    coverage_band: float,
    show_paths: bool,
) -> float | None:
    """Nested central quantile bands + median + observed overlay on ``ax``.

    Returns the empirical coverage of ``coverage_band`` (fraction of observed
    points inside that nominal envelope), or ``None`` without observations.
    """
    centrals = sorted(quantiles)
    if show_paths:
        n = paths.shape[0]
        alpha = float(np.clip(30.0 / n, 0.02, 0.4))
        ax.plot(grid, paths.T, color=COLOR_MODEL, linewidth=0.4, alpha=alpha, zorder=1)
    band_alphas = np.linspace(*_BAND_ALPHA_RANGE, len(centrals))
    for central, band_alpha in zip(centrals[::-1], band_alphas, strict=True):
        lo, hi = _band_bounds(central)
        band = np.quantile(paths, [lo, hi], axis=0)
        ax.fill_between(grid, band[0], band[1], color=COLOR_MODEL, alpha=band_alpha, linewidth=0)
    ax.plot(grid, np.quantile(paths, 0.5, axis=0), color=COLOR_MODEL, linewidth=1.6, zorder=3)

    coverage = None
    if observed is not None and len(observed):
        obs = observed.dropna().sort_index()
        obs = obs[(obs.index >= grid[0]) & (obs.index <= grid[-1])]
        if len(obs):
            ax.plot(obs.index, obs.to_numpy(), color=COLOR_OBSERVED, linewidth=1.2, zorder=4)
            coverage = band_coverage(grid, paths, obs, coverage_band)
    return coverage


def _coverage_note(coverage: float | None, coverage_band: float) -> str:
    if coverage is None:
        return ""
    return f"coverage: {coverage:.0%} of observations inside the {coverage_band:.0%} band"


def plot_paths_vs_observed(
    dates: Sequence[datetime],
    paths: np.ndarray,
    observed: pd.Series,
    quantiles: Sequence[float] = (0.5, 0.8, 0.95),
    show_paths: bool = False,
    coverage_band: float = 0.95,
    yscale: str = "linear",
    ylabel: str = "",
    title: str = "",
) -> Figure:
    """Simulated fan (nested central bands + median) with the observed path on top.

    ``paths`` are simulations of a **calibrated** model from the first grid
    date; ``observed`` is the realized series over (part of) the same span. The
    annotation reports empirical band coverage vs the nominal ``coverage_band``
    — the fan-chart backtest. Whether the comparison is in-sample or holdout is
    a property of the inputs; say it in ``title``. ``yscale="log"`` suits
    multiplicative (GBM) cones, whose long-horizon quantiles crush a linear
    axis; coverage is computed on values, so the scale never changes it.
    """
    grid = _as_datetime_index(dates)
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    coverage = _draw_fan(ax, grid, paths, observed, quantiles, coverage_band, show_paths)
    ax.set_yscale(yscale)
    band_labels = "/".join(f"{q:.0%}" for q in sorted(quantiles))
    ax.legend(
        handles=[
            Line2D([], [], color=COLOR_OBSERVED, label="Observed"),
            Line2D([], [], color=COLOR_MODEL, label="Model median"),
            Patch(facecolor=COLOR_MODEL, alpha=0.25, label=f"Central {band_labels} bands"),
        ],
        loc="upper left",
    )
    note = _coverage_note(coverage, coverage_band)
    if note:
        ax.text(
            0.99, 0.02, note, transform=ax.transAxes, ha="right", fontsize=8, color=TEXT_SECONDARY
        )
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    return fig


def plot_paths_vs_observed_grid(
    panels: Sequence[Mapping[str, object]],
    ncols: int = 3,
    quantiles: Sequence[float] = (0.5, 0.8, 0.95),
    coverage_band: float = 0.95,
    yscale: str = "linear",
    title: str = "",
) -> Figure:
    """Panel grid of :func:`plot_paths_vs_observed` fans, one per instrument.

    Each panel mapping carries ``dates``, ``paths``, ``observed`` and ``label``;
    the panel title appends its own band coverage. One shared legend serves the
    figure. All panels are drawn — a book-wide grid grows in height rather than
    truncating (GEN-28 companion rule).
    """
    if not panels:
        raise ValueError("panels is empty")
    n = len(panels)
    ncols = min(ncols, n)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(3.4 * ncols, 2.4 * nrows), sharex=False, squeeze=False
    )
    flat = axes.ravel()
    for ax in flat[n:]:
        ax.set_visible(False)
    for ax, panel in zip(flat, panels, strict=False):  # flat may carry hidden spares
        grid = _as_datetime_index(panel["dates"])
        coverage = _draw_fan(
            ax,
            grid,
            np.asarray(panel["paths"]),
            panel.get("observed"),
            quantiles,
            coverage_band,
            show_paths=False,
        )
        label = str(panel.get("label", ""))
        if coverage is not None:
            label = f"{label} — cov {coverage:.0%}"
        ax.set_title(label)
        ax.set_yscale(yscale)
        ax.tick_params(labelsize=6)
    fig.legend(
        handles=[
            Line2D([], [], color=COLOR_OBSERVED, label="Observed"),
            Line2D([], [], color=COLOR_MODEL, label="Model median"),
            Patch(
                facecolor=COLOR_MODEL,
                alpha=0.25,
                label=f"Central {'/'.join(f'{q:.0%}' for q in sorted(quantiles))} bands"
                f" (cov = coverage of the {coverage_band:.0%} band)",
            ),
        ],
        loc="outside upper right",
    )
    if title:
        fig.suptitle(title, fontweight="bold", x=0.01, ha="left")
    return fig


def plot_arrival_staircase(
    event_dates: Sequence[datetime],
    regimes: Sequence[Mapping[str, object]],
    envelope: float = 0.95,
    ylabel: str = "Cumulative observed events",
    title: str = "",
) -> Figure:
    """Observed cumulative event count vs per-regime Poisson expectation bands.

    ``event_dates`` are the observed arrivals; each regime mapping carries
    ``start``, ``end`` (dates), ``intensity`` (events/year) and ``label``. The
    expectation ``N(start) + lambda * (t - start)`` and its central
    ``envelope`` Poisson quantile band re-anchor at the **observed** count at
    each regime start, so every regime is judged against its own fitted
    intensity — the honest reading across a publication-regime break
    (HAZ-CENAPRED-10).
    """
    events = pd.DatetimeIndex(pd.to_datetime(list(event_dates))).sort_values()
    counts = np.arange(1, len(events) + 1)
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.step(events, counts, where="post", color=COLOR_OBSERVED, linewidth=1.4, zorder=4)

    lo_q, hi_q = _band_bounds(envelope)
    for i, regime in enumerate(regimes):
        start = pd.Timestamp(regime["start"])
        end = pd.Timestamp(regime["end"])
        lam = float(regime["intensity"])
        anchor = int((events < start).sum())
        grid = pd.date_range(start, end, freq="D")
        years = (grid - start).days / 365.0
        mu = lam * years
        ax.plot(
            grid,
            anchor + mu,
            color=COLOR_MODEL,
            linestyle="--",
            linewidth=1.4,
            zorder=3,
        )
        ax.fill_between(
            grid,
            anchor + stats.poisson.ppf(lo_q, mu),
            anchor + stats.poisson.ppf(hi_q, mu),
            color=COLOR_MODEL,
            alpha=0.15,
            linewidth=0,
        )
        if i > 0:
            ax.axvline(start, color=TEXT_SECONDARY, linestyle=":", linewidth=1.0)
        ax.annotate(
            f"{regime['label']}\n$\\lambda$={lam:.2f}/yr",
            xy=(start + (end - start) / 2, 1.0),
            xycoords=("data", "axes fraction"),
            xytext=(0, -2),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=8,
            color=TEXT_SECONDARY,
        )
    ax.legend(
        handles=[
            Line2D([], [], color=COLOR_OBSERVED, label="Observed N(t)"),
            Line2D([], [], color=COLOR_MODEL, linestyle="--", label=r"Fitted $\lambda t$"),
            Patch(facecolor=COLOR_MODEL, alpha=0.15, label=f"Central {envelope:.0%} Poisson band"),
        ],
        loc="upper left",
    )
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    return fig


def plot_marked_arrivals(
    observed_dates: Sequence[datetime],
    observed_marks: Sequence[float],
    simulated_dates: Sequence[datetime],
    simulated_marks: Sequence[float],
    mark_label: str = "Per-event loss",
    title: str = "",
) -> Figure:
    """Observed vs one simulated marked-arrival path, as paired stem panels.

    Same time span, shared log mark axis: does a draw from the calibrated
    marked Poisson process *look like* the observed record? One simulated path
    (not an envelope) is the point — eyeball realism, not a fit statistic.
    """
    obs_marks = np.asarray(list(observed_marks), dtype=float)
    sim_marks = np.asarray(list(simulated_marks), dtype=float)
    positive = np.concatenate([obs_marks[obs_marks > 0], sim_marks[sim_marks > 0]])
    if positive.size == 0:
        raise ValueError("no positive marks to draw on a log axis")
    floor = float(positive.min()) / 3.0
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 4.6), sharex=True, sharey=True)
    for ax, dates, marks, color, label in (
        (axes[0], observed_dates, obs_marks, COLOR_OBSERVED, "Observed"),
        (axes[1], simulated_dates, sim_marks, COLOR_MODEL, "Simulated (one path)"),
    ):
        grid = pd.DatetimeIndex(pd.to_datetime(list(dates)))
        ax.vlines(grid, floor, marks, color=color, linewidth=0.9, alpha=0.8)
        ax.plot(grid, marks, linestyle="none", marker="o", markersize=2.6, color=color)
        ax.set_yscale("log")
        ax.set_ylim(bottom=floor)
        ax.set_title(f"{label} — {len(grid)} events")
    fig.supylabel(mark_label, fontsize=9)
    if title:
        fig.suptitle(title, fontweight="bold", x=0.01, ha="left")
    return fig


def plot_qq(
    sample_quantiles: Sequence[float],
    theoretical_quantiles: Sequence[float],
    xlabel: str = "Theoretical quantiles",
    ylabel: str = "Sample quantiles",
    title: str = "",
) -> Figure:
    """QQ scatter against precomputed theoretical quantiles, with the 45° line.

    The caller supplies both quantile vectors (same length, both sorted), so
    any distributional hypothesis — exponential inter-arrivals, lognormal
    severities — plugs in without this function knowing the family.
    """
    sample = np.asarray(list(sample_quantiles), dtype=float)
    theory = np.asarray(list(theoretical_quantiles), dtype=float)
    if sample.shape != theory.shape:
        raise ValueError(f"quantile vectors differ in shape: {sample.shape} vs {theory.shape}")
    fig, ax = plt.subplots(figsize=(4.2, 4.2))
    span = np.array([min(theory.min(), sample.min()), max(theory.max(), sample.max())])
    ax.plot(span, span, color=TEXT_SECONDARY, linestyle="--", linewidth=1.0, zorder=2)
    ax.plot(
        theory,
        sample,
        linestyle="none",
        marker="o",
        markersize=3.5,
        color=COLOR_MODEL,
        alpha=0.7,
        zorder=3,
    )
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    return fig
