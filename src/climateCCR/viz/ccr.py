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
    "uncollateralized_pfe_0.99": "Uncollateralised PFE 99%",
    "collateralized_ee": "Collateralised EE",
    "collateralized_pe_0.99": "Collateralised PE 99%",
}

PE_COLUMN = "uncollateralized_pe_0.99"
PFE_COLUMN = "uncollateralized_pfe_0.99"


def with_supervisory_pfe(comparison: pd.DataFrame) -> pd.DataFrame:
    """Comparison frame plus derived supervisory-PFE columns (floored at zero).

    The engine's PE is the raw path-value quantile — negative when the netting
    set is a net liability at that date, which is information owed *to* the
    counterparty (DVA territory), not credit exposure. Reported figures use the
    supervisory convention PFE = max(quantile, 0), derived here at the
    reporting seam so the engine output and its golden baselines stay raw
    (CCR-RISK-03). Baseline and climate floor independently; the shift is the
    difference of the floored profiles.
    """
    out = comparison.copy()
    base = out[f"{PE_COLUMN}_baseline"].clip(lower=0.0)
    climate = out[f"{PE_COLUMN}_climate"].clip(lower=0.0)
    out[f"{PFE_COLUMN}_baseline"] = base
    out[f"{PFE_COLUMN}_climate"] = climate
    out[f"{PFE_COLUMN}_shift"] = climate - base
    return out


def epe_summary(comparison: pd.DataFrame, metric: str = "uncollateralized_ee") -> pd.DataFrame:
    """Time-averaged exposure (EPE) per counterparty, plus a whole-book row.

    Trapezoid average of the ``metric`` profile over the reporting grid in year
    fractions — the single-number summary of a profile the results chapter
    leads with (INT-23). Returns one row per counterparty and a final ``BOOK``
    row (EPEs are means of sums, so the book row is the sum of the rows), with
    ``epe_baseline`` / ``epe_climate`` / ``epe_shift`` / ``epe_shift_pct``.
    """

    def _epe(block: pd.DataFrame, column: str) -> float:
        years = (
            pd.to_datetime(block["default_times"]) - pd.to_datetime(block["default_times"].iloc[0])
        ).dt.days.to_numpy() / 365.25
        values = block[column].to_numpy(dtype=float)
        if years[-1] == 0:
            return float(values[0])
        return float(np.trapezoid(values, years) / years[-1])

    rows = [
        {
            "netting_agreement_id": str(naid),
            "epe_baseline": _epe(block, f"{metric}_baseline"),
            "epe_climate": _epe(block, f"{metric}_climate"),
        }
        for naid, block in comparison.sort_values("default_times").groupby("netting_agreement_id")
    ]
    out = pd.DataFrame(rows)
    book = pd.DataFrame(
        [
            {
                "netting_agreement_id": "BOOK",
                "epe_baseline": out["epe_baseline"].sum(),
                "epe_climate": out["epe_climate"].sum(),
            }
        ]
    )
    out = pd.concat([out, book], ignore_index=True)
    out["epe_shift"] = out["epe_climate"] - out["epe_baseline"]
    out["epe_shift_pct"] = (
        100.0 * out["epe_shift"] / out["epe_baseline"].where(out["epe_baseline"] != 0)
    )
    return out


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


def plot_epe_delta_matrix(deltas: pd.DataFrame) -> Figure:
    """Annotated scenario × band matrix of book-EPE deltas (%) vs base jump-off.

    Input: the NGFS readout artifact (``book_epe_deltas.csv`` — one row per
    ``scenario`` × ``band`` with ``transition_pct`` / ``combined_pct`` /
    ``jump_within_pct``). Renders the INT-30/31 results table as a figure:
    transition-only per scenario, then combined and jump-within per lambda
    band. Cells the matrix does not define (physical-embedding narratives run
    jump-off only, INT-29) print an em dash. Diverging color around zero uses
    the shift poles: orange = exposure up, green = down.
    """
    if deltas.empty:
        raise ValueError("deltas is empty: pass the book_epe_deltas readout frame")
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

    scenarios = list(dict.fromkeys(deltas["scenario"]))
    bands = list(dict.fromkeys(deltas["band"]))
    columns: list[tuple[str, str]] = [("transition_pct", "")]
    columns += [("combined_pct", b) for b in bands]
    columns += [("jump_within_pct", b) for b in bands]
    titles = {
        "transition_pct": "Transition\nonly",
        "combined_pct": "Combined",
        "jump_within_pct": "Jump within",
    }
    matrix = np.full((len(scenarios), len(columns)), np.nan)
    for i, scen in enumerate(scenarios):
        block = deltas[deltas["scenario"] == scen]
        for j, (metric, band) in enumerate(columns):
            rows = block if band == "" else block[block["band"] == band]
            values = rows[metric].dropna().unique()
            if len(values):
                matrix[i, j] = float(values[0])

    cmap = LinearSegmentedColormap.from_list(
        "epe_delta", [COLOR_SHIFT_DOWN, "#ffffff", COLOR_SHIFT_UP]
    )
    bound = float(np.nanmax(np.abs(matrix))) or 1.0
    norm = TwoSlopeNorm(vcenter=0.0, vmin=-bound, vmax=bound)
    fig, ax = plt.subplots(figsize=(1.6 + 1.15 * len(columns), 1.2 + 0.6 * len(scenarios)))
    ax.imshow(matrix, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(range(len(columns)))
    ax.set_xticklabels([f"{titles[m]}\n{b}" if b else titles[m] for m, b in columns], fontsize=8)
    ax.set_yticks(range(len(scenarios)))
    ax.set_yticklabels(scenarios, fontsize=9)
    ax.grid(False)
    for i in range(len(scenarios)):
        for j in range(len(columns)):
            value = matrix[i, j]
            dark = not np.isnan(value) and abs(value) > 0.6 * bound
            ax.text(
                j,
                i,
                "—" if np.isnan(value) else f"{value:+.2f}",
                ha="center",
                va="center",
                fontsize=8,
                color="white" if dark else TEXT_SECONDARY,
            )
    ax.set_title("Book-EPE delta vs base jump-off (%)")
    return fig


def plot_stage_walk_epe(walk: Mapping[str, Mapping[str, pd.DataFrame]]) -> Figure:
    """Book EPE shift walked across methodology stages, one line per lambda leg.

    Input: ``stage -> (leg -> epe_summary frame)`` (:func:`epe_summary`
    output), both orderings the caller's — stages left to right in re-base
    order, legs one line each. Every stage must carry the same legs. Each
    point is that stage's BOOK ``epe_shift_pct`` vs its *own contemporaneous
    baseline* (the INT-23 chain convention: archived states keep their era's
    calibration basis), so the walk shows how each methodology step moved the
    headline number — not a same-basis re-run.
    """
    if not walk:
        raise ValueError("walk is empty: pass stage -> (leg -> epe_summary frame)")
    stages = list(walk)
    legs = list(next(iter(walk.values())))
    for stage, by_leg in walk.items():
        if list(by_leg) != legs:
            raise ValueError(f"Stage {stage!r} legs {list(by_leg)} != {legs}")

    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    x = np.arange(len(stages))
    ax.axhline(0.0, color=TEXT_SECONDARY, linewidth=0.8)
    for color, leg in zip(SERIES_COLORS, legs, strict=False):
        y = []
        for stage in stages:
            summary = walk[stage][leg]
            book = summary.loc[summary["netting_agreement_id"] == "BOOK", "epe_shift_pct"]
            y.append(float(book.iloc[0]))
        ax.plot(x, y, marker="o", markersize=5, color=color, label=leg)
        for xi, yi in zip(x, y, strict=False):
            ax.annotate(
                f"{yi:+.2f}",
                (xi, yi),
                textcoords="offset points",
                xytext=(0, 6),
                fontsize=7.5,
                color=TEXT_SECONDARY,
                ha="center",
            )
    ax.set_xticks(x, stages, fontsize=8.5)
    ax.margins(x=0.06)
    ax.set_ylabel("Book EPE shift vs own baseline (%)")
    ax.legend(title="Arrival-intensity leg")
    ax.set_title("Book-EPE climate delta across mark-state stages")
    return fig


def plot_epe_shift_distribution(summaries: Mapping[str, pd.DataFrame]) -> Figure:
    """Per-counterparty EPE-shift distributions across labelled runs.

    Input: ``label -> epe_summary frame`` (:func:`epe_summary` output — per-NAID
    rows plus a ``BOOK`` row). Each run is one horizontal strip of per-NAID
    ``epe_shift_pct`` points with the BOOK shift as a diamond, so the chapter
    can compare how the whole cross-section — not just the book mean — moves
    across mark states, lambda bands, and NGFS legs. Percentages are vs each
    run's own contemporaneous baseline (the INT-23 chain convention).
    """
    if not summaries:
        raise ValueError("summaries is empty: pass at least one labelled epe_summary frame")
    from matplotlib.lines import Line2D

    fig, ax = plt.subplots(figsize=(7.2, 1.0 + 0.55 * len(summaries)))
    ax.axvline(0.0, color=TEXT_SECONDARY, linewidth=0.8)
    labels = list(summaries)
    for y, label in enumerate(labels):
        summary = summaries[label]
        naids = summary[summary["netting_agreement_id"] != "BOOK"]
        values = naids["epe_shift_pct"].dropna().to_numpy(dtype=float)
        ax.plot(
            values,
            np.full(values.shape, y),
            linestyle="none",
            marker="o",
            markersize=4,
            color=COLOR_BASELINE,
            alpha=0.45,
        )
        book = summary.loc[summary["netting_agreement_id"] == "BOOK", "epe_shift_pct"]
        if book.notna().any():
            ax.plot(
                float(book.iloc[0]),
                y,
                linestyle="none",
                marker="D",
                markersize=7,
                color=COLOR_CLIMATE,
                markeredgecolor="white",
                markeredgewidth=0.8,
            )
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("EPE shift vs own baseline (%)")
    ax.legend(
        handles=[
            Line2D(
                [],
                [],
                linestyle="none",
                marker="o",
                color=COLOR_BASELINE,
                alpha=0.45,
                label="Counterparty",
            ),
            Line2D(
                [],
                [],
                linestyle="none",
                marker="D",
                color=COLOR_CLIMATE,
                markeredgecolor="white",
                label="BOOK",
            ),
        ],
        loc="lower left",
    )
    ax.set_title("Per-counterparty EPE shifts across runs")
    return fig
