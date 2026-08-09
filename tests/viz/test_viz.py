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


def test_with_supervisory_pfe_floors_only_at_reporting():
    """PFE = max(quantile, 0) derived per side; raw PE kept verbatim (CCR-RISK-03)."""
    frame = pd.DataFrame(
        {
            "netting_agreement_id": [1, 1, 2],
            "default_times": ["2020-01-01", "2021-01-01", "2020-01-01"],
            "uncollateralized_pe_0.99_baseline": [10.0, -4.0, -7.0],
            "uncollateralized_pe_0.99_climate": [6.0, 2.0, -9.0],
            "uncollateralized_pe_0.99_shift": [-4.0, 6.0, -2.0],
        }
    )
    out = viz.with_supervisory_pfe(frame)
    # Positive both sides: passthrough. Straddling: floor bites the negative
    # side only. Negative both sides: zero exposure, zero shift.
    assert list(out["uncollateralized_pfe_0.99_baseline"]) == [10.0, 0.0, 0.0]
    assert list(out["uncollateralized_pfe_0.99_climate"]) == [6.0, 2.0, 0.0]
    assert list(out["uncollateralized_pfe_0.99_shift"]) == [-4.0, 2.0, 0.0]
    assert list(out["uncollateralized_pe_0.99_shift"]) == [-4.0, 6.0, -2.0]
    assert "uncollateralized_pfe_0.99_shift" not in frame.columns  # input not mutated


def test_epe_summary_time_averages_and_totals_the_book():
    dates = ["2020-01-01", "2020-07-01", "2022-01-01"]
    frame = pd.DataFrame(
        {
            "netting_agreement_id": [1] * 3 + [2] * 3,
            "default_times": dates * 2,
            "uncollateralized_ee_baseline": [10.0] * 3 + [0.0, 4.0, 4.0],
            "uncollateralized_ee_climate": [5.0] * 3 + [0.0, 2.0, 2.0],
        }
    )
    out = viz.epe_summary(frame)
    row1 = out[out["netting_agreement_id"] == "1"].iloc[0]
    assert row1["epe_baseline"] == pytest.approx(10.0)  # constant profile -> its level
    assert row1["epe_climate"] == pytest.approx(5.0)
    assert row1["epe_shift_pct"] == pytest.approx(-50.0)
    book = out[out["netting_agreement_id"] == "BOOK"].iloc[0]
    counterparties = out[out["netting_agreement_id"] != "BOOK"]
    assert book["epe_baseline"] == pytest.approx(counterparties["epe_baseline"].sum())
    assert book["epe_shift"] == pytest.approx(counterparties["epe_shift"].sum())


def test_exposure_panels_cap_a_large_book_at_the_most_shifted(comparison):
    """A 30-counterparty book (INT-21) shows the MAX_PANELS largest |mean shift|."""
    from climateCCR.viz.ccr import MAX_PANELS

    book = pd.concat(
        [
            comparison.assign(netting_agreement_id=100 + i, uncollateralized_ee_shift=float(i))
            for i in range(30)
        ],
        ignore_index=True,
    )
    fig = viz.plot_exposure_profiles(book)
    visible = [ax for ax in fig.axes if ax.get_visible()]
    assert len(visible) == MAX_PANELS
    shown = {ax.get_title(loc="left") for ax in visible}  # the thesis style titles left
    assert shown == {f"Counterparty {100 + i}" for i in range(30 - MAX_PANELS, 30)}
    assert "of 30 counterparties" in fig._suptitle.get_text()


def test_scenario_band_one_line_per_scenario(comparison):
    band = {
        "headline": comparison,
        "floor": comparison.assign(
            uncollateralized_ee_shift=comparison["uncollateralized_ee_shift"] / 2
        ),
    }
    fig = viz.plot_scenario_band(band)
    (ax,) = fig.axes
    lines = [ln for ln in ax.lines if not ln.get_label().startswith("_")]  # excl. the zero rule
    assert len(lines) == 2
    # The legend carries each scenario's mean shift — the reported number.
    assert "headline (mean " in ax.get_legend().get_texts()[0].get_text()
    with pytest.raises(ValueError, match="empty"):
        viz.plot_scenario_band({})


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


def test_epe_delta_matrix_annotates_all_cells_and_dashes_undefined():
    deltas = pd.DataFrame(
        {
            "scenario": ["A", "A", "B"],
            "band": ["headline", "floor", "headline"],
            "transition_pct": [-3.0, -3.0, -13.0],
            "combined_pct": [-11.0, -8.0, np.nan],
            "jump_within_pct": [-8.0, -4.0, np.nan],
        }
    )
    fig = viz.plot_epe_delta_matrix(deltas)
    ax = fig.axes[0]
    texts = [t.get_text() for t in ax.texts]
    # 2 scenarios x (transition + 2 bands x 2 metrics) = 10 annotated cells.
    assert len(texts) == 10
    assert "—" in texts and "-11.00" in texts
    with pytest.raises(ValueError, match="empty"):
        viz.plot_epe_delta_matrix(pd.DataFrame(columns=deltas.columns))


def test_epe_shift_distribution_strip_plus_book_diamond_per_run():
    summary = pd.DataFrame(
        {
            "netting_agreement_id": ["1", "2", "BOOK"],
            "epe_baseline": [10.0, 20.0, 30.0],
            "epe_climate": [9.0, 19.0, 28.0],
            "epe_shift": [-1.0, -1.0, -2.0],
            "epe_shift_pct": [-10.0, -5.0, -6.7],
        }
    )
    fig = viz.plot_epe_shift_distribution({"run A": summary, "run B": summary})
    ax = fig.axes[0]
    # zero line + (strip + diamond) per run.
    assert len(ax.lines) == 1 + 2 * 2
    assert [t.get_text() for t in ax.get_yticklabels()] == ["run A", "run B"]
    with pytest.raises(ValueError, match="empty"):
        viz.plot_epe_shift_distribution({})


def test_stage_walk_one_line_per_leg_with_annotations():
    def summary(pct):
        return pd.DataFrame(
            {
                "netting_agreement_id": ["1", "BOOK"],
                "epe_baseline": [10.0, 10.0],
                "epe_climate": [10.0 + pct / 10.0, 10.0 + pct / 10.0],
                "epe_shift": [pct / 10.0, pct / 10.0],
                "epe_shift_pct": [pct, pct],
            }
        )

    walk = {
        "stage 1": {"leg A": summary(-11.0), "leg B": summary(-5.6)},
        "stage 2": {"leg A": summary(-8.4), "leg B": summary(-4.5)},
    }
    fig = viz.plot_stage_walk_epe(walk)
    ax = fig.axes[0]
    assert len(ax.lines) == 1 + 2  # zero line + one line per leg
    leg_a = ax.lines[1]
    np.testing.assert_allclose(leg_a.get_ydata(), [-11.0, -8.4])
    assert [t.get_text() for t in ax.get_xticklabels()] == ["stage 1", "stage 2"]
    assert len(ax.texts) == 4  # one annotation per stage x leg
    with pytest.raises(ValueError, match="empty"):
        viz.plot_stage_walk_epe({})
    with pytest.raises(ValueError, match="legs"):
        viz.plot_stage_walk_epe({"s1": {"leg A": summary(1.0)}, "s2": {"leg B": summary(1.0)}})
