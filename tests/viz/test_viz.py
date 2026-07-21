"""Smoke tests for the viz layer: contract-shaped synthetic inputs -> figures.

Each plot function gets the smallest input honouring its contract (path-major
arrays, the comparison-frame schema) and must return a well-formed Figure;
``save_figure`` must write one file per format. Rendering correctness is
reviewed visually via pipelines/02_climate_jump_figures.py, not asserted here.
"""

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest
from climateCCR import viz
from matplotlib import pyplot as plt

N_PATHS, N_STEPS = 8, 12


@pytest.fixture(autouse=True)
def _style_and_cleanup():
    viz.apply_style()
    yield
    plt.close("all")


@pytest.fixture
def comparison() -> pd.DataFrame:
    """Two counterparties x three grid dates in the comparison-frame schema."""
    rows = []
    rng = np.random.default_rng(7)
    for naid in (23, 24):
        for date in ("2020-01-01", "2021-01-01", "2022-01-01"):
            base_ee, base_pe = rng.uniform(0, 50, size=2)
            shift_ee, shift_pe = rng.uniform(-5, 10, size=2)
            rows.append(
                {
                    "netting_agreement_id": naid,
                    "default_times": date,
                    "uncollateralized_ee_baseline": base_ee,
                    "uncollateralized_ee_climate": base_ee + shift_ee,
                    "uncollateralized_ee_shift": shift_ee,
                    "uncollateralized_pe_0.99_baseline": base_pe,
                    "uncollateralized_pe_0.99_climate": base_pe + shift_pe,
                    "uncollateralized_pe_0.99_shift": shift_pe,
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture
def path_data():
    """Path-major arrays on an (N_STEPS + 1)-date grid, with sparse jump events."""
    rng = np.random.default_rng(11)
    dates = pd.date_range("2020-01-01", periods=N_STEPS + 1, freq="MS").to_pydatetime()
    baseline = 100.0 + rng.normal(0, 1, size=(N_PATHS, N_STEPS + 1)).cumsum(axis=1)
    events = rng.poisson(0.15, size=(N_PATHS, N_STEPS))
    climate = baseline - 2.0 * np.pad(events, ((0, 0), (1, 0))).cumsum(axis=1)
    return dates, baseline, climate, events


def test_apply_style_sets_thesis_defaults():
    assert matplotlib.rcParams["axes.spines.top"] is False
    assert matplotlib.rcParams["axes.axisbelow"] is True


def test_save_figure_writes_one_file_per_format(tmp_path):
    fig, _ = plt.subplots()
    written = viz.save_figure(fig, tmp_path / "nested" / "figure", formats=("png", "pdf"))
    assert [p.suffix for p in written] == [".png", ".pdf"]
    assert all(p.exists() and p.stat().st_size > 0 for p in written)


def test_save_figure_dpi_override_scales_pixels(tmp_path):
    from matplotlib.image import imread

    fig, _ = plt.subplots(figsize=(2, 1))
    lo = viz.save_figure(fig, tmp_path / "lo", formats=("png",), dpi=100)[0]
    hi = viz.save_figure(fig, tmp_path / "hi", formats=("png",), dpi=200)[0]
    assert abs(imread(hi).shape[0] - 2 * imread(lo).shape[0]) <= 2


def test_exposure_profiles_one_panel_per_counterparty(comparison):
    fig = viz.plot_exposure_profiles(comparison)
    visible = [ax for ax in fig.axes if ax.get_visible()]
    assert len(visible) == comparison["netting_agreement_id"].nunique()
    assert all(len(ax.lines) == 2 for ax in visible)  # baseline + climate


def test_exposure_shift_and_summary_build(comparison):
    assert viz.plot_exposure_shift(comparison).axes
    fig = viz.plot_mean_shift_summary(comparison)
    assert len(fig.axes) == 2  # EE + PE99 panels


def test_sample_paths_marks_events_only_on_climate_paths(path_data):
    dates, baseline, climate, events = path_data
    fig = viz.plot_sample_paths(dates, baseline, climate, event_counts=events, n_show=3)
    (ax,) = fig.axes
    markers = [ln for ln in ax.lines if ln.get_linestyle() == "None"]
    shown_events = int(sum((events[p] > 0).sum() for p in range(3)))
    assert sum(len(ln.get_xdata()) for ln in markers) == shown_events


def test_sample_paths_none_draws_every_trajectory(path_data):
    dates, baseline, climate, events = path_data
    fig = viz.plot_sample_paths(dates, baseline, climate, event_counts=events, n_show=None)
    (ax,) = fig.axes
    solid = [ln for ln in ax.lines if ln.get_linestyle() == "-"]
    assert len(solid) == 2 * N_PATHS  # baseline + climate for every path


def test_fan_comparison_and_event_arrivals_build(path_data):
    dates, baseline, climate, events = path_data
    fig = viz.plot_fan_comparison(dates, baseline, climate, ylabel="value")
    assert len(fig.axes[0].collections) == 2  # one band per scenario
    fig = viz.plot_event_arrivals(dates, events, intensity=0.6)
    assert len(fig.axes[0].lines) == 2  # observed + expected


def test_rate_path_fan_draws_all_paths_and_overlays(path_data):
    dates, baseline, _, _ = path_data
    mean = baseline.mean(axis=0)
    sd = baseline.std(axis=0)
    fig = viz.plot_rate_path_fan(dates, baseline, mean, sd)
    (ax,) = fig.axes
    # N_PATHS trajectories + MC mean + analytic mean + two sd bounds.
    assert len(ax.lines) == N_PATHS + 4


def test_estimator_fan_comparison_one_ribbon_per_series(path_data):
    dates, baseline, climate, _ = path_data
    means = [baseline.mean(axis=0), climate.mean(axis=0)]
    sds = [baseline.std(axis=0), climate.std(axis=0)]
    fig = viz.plot_estimator_fan_comparison(dates, means, sds, ["AR(1)", "MLE"])
    (ax,) = fig.axes
    assert len(ax.collections) == 2  # one band per estimator
    assert len(ax.lines) == 2
    with pytest.raises(ValueError, match="same length"):
        viz.plot_estimator_fan_comparison(dates, means, sds, ["only-one"])


def test_jump_decay_halves_at_half_life():
    alphas = {"a=0.10": 0.10, "a=0.05": 0.05}
    fig = viz.plot_jump_decay(alphas, jump_bp=100.0)
    (ax,) = fig.axes
    curves = [ln for ln in ax.lines if len(ln.get_xdata()) > 10]
    assert len(curves) == len(alphas)
    t = curves[0].get_xdata()
    y = curves[0].get_ydata()
    import numpy as _np

    half_life = _np.log(2.0) / 0.10
    assert _np.interp(half_life, t, y) == pytest.approx(50.0, rel=1e-3)
    with pytest.raises(ValueError, match="empty"):
        viz.plot_jump_decay({})
