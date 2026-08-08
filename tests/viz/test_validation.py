"""Smoke tests for viz.validation: synthetic contract-shaped inputs -> figures."""

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest
from climateCCR import viz
from matplotlib import pyplot as plt

N_PATHS, N_STEPS = 20, 30


@pytest.fixture(autouse=True)
def _style_and_cleanup():
    viz.apply_style()
    yield
    plt.close("all")


@pytest.fixture
def fan_data():
    """Daily grid, path-major simulations, and an observed series inside the span."""
    rng = np.random.default_rng(5)
    dates = pd.date_range("2020-01-01", periods=N_STEPS + 1, freq="D")
    paths = 0.08 + rng.normal(0, 0.002, size=(N_PATHS, N_STEPS + 1)).cumsum(axis=1)
    observed = pd.Series(0.08 + rng.normal(0, 0.001, N_STEPS + 1).cumsum(), index=dates)
    return dates, paths, observed


def test_paths_vs_observed_draws_bands_median_observed_and_coverage(fan_data):
    dates, paths, observed = fan_data
    fig = viz.plot_paths_vs_observed(dates, paths, observed, ylabel="rate", title="t")
    ax = fig.axes[0]
    assert len(ax.collections) == 3  # one fill per nested band
    assert len(ax.lines) == 2  # model median + observed
    assert any("coverage" in t.get_text() for t in ax.texts)


def test_paths_vs_observed_spaghetti_adds_path_lines(fan_data):
    dates, paths, observed = fan_data
    fig = viz.plot_paths_vs_observed(dates, paths, observed, show_paths=True)
    assert len(fig.axes[0].lines) == N_PATHS + 2


def test_paths_vs_observed_grid_one_panel_per_item(fan_data):
    dates, paths, observed = fan_data
    panels = [
        {"dates": dates, "paths": paths, "observed": observed, "label": f"P{i}"} for i in range(4)
    ]
    fig = viz.plot_paths_vs_observed_grid(panels, ncols=3)
    visible = [ax for ax in fig.axes if ax.get_visible()]
    assert len(visible) == 4
    assert all("cov" in ax.get_title(loc="left") for ax in visible)


def test_paths_vs_observed_grid_rejects_empty():
    with pytest.raises(ValueError, match="empty"):
        viz.plot_paths_vs_observed_grid([])


def test_arrival_staircase_regime_bands_and_break_line():
    rng = np.random.default_rng(3)
    events = pd.to_datetime("2002-01-01") + pd.to_timedelta(
        np.sort(rng.uniform(0, 5000, 40)), unit="D"
    )
    regimes = [
        {"start": "2002-01-01", "end": "2009-12-31", "intensity": 4.0, "label": "A"},
        {"start": "2010-01-01", "end": "2015-12-31", "intensity": 2.0, "label": "B"},
    ]
    fig = viz.plot_arrival_staircase(events, regimes)
    ax = fig.axes[0]
    assert len(ax.collections) == 2  # one Poisson band per regime
    assert len(ax.lines) == 1 + 2 + 1  # observed step + two lambda lines + break line
    # The second regime's band re-anchors at the observed count, not at zero.
    band = ax.collections[1].get_paths()[0].vertices[:, 1]
    assert band.max() > (events < pd.Timestamp("2010-01-01")).sum()


def test_marked_arrivals_two_log_panels():
    rng = np.random.default_rng(9)
    obs_dates = pd.date_range("2002-01-01", periods=15, freq="90D")
    sim_dates = pd.date_range("2002-01-01", periods=12, freq="110D")
    fig = viz.plot_marked_arrivals(
        obs_dates, rng.lognormal(6, 1, 15), sim_dates, rng.lognormal(6, 1, 12)
    )
    assert len(fig.axes) == 2
    assert all(ax.get_yscale() == "log" for ax in fig.axes)


def test_marked_arrivals_rejects_all_nonpositive_marks():
    dates = pd.date_range("2002-01-01", periods=3, freq="D")
    with pytest.raises(ValueError, match="positive"):
        viz.plot_marked_arrivals(dates, [0.0, -1.0, 0.0], dates, [0.0, 0.0, 0.0])


def test_qq_scatter_plus_reference_line():
    q = np.linspace(0.1, 3.0, 25)
    fig = viz.plot_qq(q * 1.05, q, xlabel="theory", ylabel="sample")
    ax = fig.axes[0]
    assert len(ax.lines) == 2  # reference line + scatter (drawn via plot)


def test_qq_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="shape"):
        viz.plot_qq([1.0, 2.0], [1.0, 2.0, 3.0])


def test_band_coverage_full_inside_and_outside_span(fan_data):
    dates, paths, _ = fan_data
    inside = pd.Series(np.median(paths, axis=0), index=dates)
    assert viz.band_coverage(dates, paths, inside) == 1.0
    outside = pd.Series([0.1], index=[pd.Timestamp("1999-01-01")])
    assert viz.band_coverage(dates, paths, outside) is None
