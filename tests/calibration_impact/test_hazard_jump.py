"""Units for ``calibration.impact.hazard_jump`` (GEN-11).

Synthetic fixtures throughout; one smoke test runs against the real CENAPRED
consolidado when ``data/hazard_mx`` is present (GEN-24) and skips otherwise.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from climateCCR.calibration.impact import (
    annual_event_counts,
    estimate_intensity,
    fit_intensity_trend,
    fit_severity,
    load_climate_events,
)
from climateCCR.processes.jumps import LognormalMark

REPO_ROOT = Path(__file__).resolve().parents[2]
EVENTS_CSV = (
    REPO_ROOT
    / "data"
    / "hazard_mx"
    / "datos_CENAPRED"
    / "consolidados"
    / "eventos_cenapred_climada.csv"
)

COLUMNS = ["anio", "duracion_dias", "peril_canonico", "en_alcance_climatico", "danio_mdp"]


def _events_csv(tmp_path: Path, rows: list[tuple]) -> Path:
    path = tmp_path / "eventos.csv"
    pd.DataFrame(rows, columns=COLUMNS).to_csv(path, index=False)
    return path


def _frame(anios, danios) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "anio": anios,
            "duracion_dias": 1.0,
            "peril_canonico": "Ciclón tropical",
            "en_alcance_climatico": "si",
            "danio_mdp": danios,
        }
    )


class TestLoader:
    def test_filters_scope_aggregates_and_window(self, tmp_path):
        path = _events_csv(
            tmp_path,
            [
                (2005, 3.0, "Ciclón tropical", "si", 10.0),  # kept
                (2005, 365.0, "Incendio forestal", "si", 5.0),  # annual aggregate: dropped
                (2005, 2.0, "Sismo", "no", 50.0),  # out of climate scope: dropped
                (2001, 1.0, "Inundación", "si", 8.0),  # before window: dropped
                (2007, np.nan, "Sequía", "si", 2.0),  # missing duration: kept as discrete
            ],
        )
        events = load_climate_events(path, start_year=2002, end_year=2015)
        assert len(events) == 2
        assert events.attrs["window"] == (2002, 2015)

    def test_peril_and_damage_filters(self, tmp_path):
        path = _events_csv(
            tmp_path,
            [
                (2005, 1.0, "Ciclón tropical", "si", 200.0),
                (2006, 1.0, "Ciclón tropical", "si", 5.0),
                (2006, 1.0, "Sequía", "si", 300.0),
            ],
        )
        assert len(load_climate_events(path, perils=["Ciclón tropical"])) == 2
        assert len(load_climate_events(path, min_damage_mdp=100.0)) == 2
        assert len(load_climate_events(path, perils=["Ciclón tropical"], min_damage_mdp=100.0)) == 1

    def test_missing_column_raises(self, tmp_path):
        path = tmp_path / "malo.csv"
        pd.DataFrame({"anio": [2005]}).to_csv(path, index=False)
        with pytest.raises(ValueError, match="missing required columns"):
            load_climate_events(path)

    def test_bad_window_raises(self, tmp_path):
        path = _events_csv(tmp_path, [(2005, 1.0, "Sequía", "si", 1.0)])
        with pytest.raises(ValueError, match="start_year"):
            load_climate_events(path, start_year=2010, end_year=2005)


class TestFrequency:
    def test_counts_zero_fill(self):
        events = _frame([2002, 2002, 2004], [1.0, 1.0, 1.0])
        counts = annual_event_counts(events, 2002, 2005)
        assert counts.tolist() == [2, 0, 1, 0]

    def test_counts_require_window(self):
        with pytest.raises(ValueError, match="window"):
            annual_event_counts(_frame([2002], [1.0]))

    def test_intensity_mle_and_ci(self):
        counts = pd.Series([2] * 14, index=pd.RangeIndex(2002, 2016))
        fit = estimate_intensity(counts)
        assert fit.intensity == pytest.approx(2.0)
        assert fit.ci_low < 2.0 < fit.ci_high
        assert fit.n_events == 28 and fit.n_years == 14

    def test_intensity_zero_events(self):
        fit = estimate_intensity(pd.Series([0, 0, 0], index=pd.RangeIndex(2002, 2005)))
        assert fit.intensity == 0.0
        assert fit.ci_low == 0.0
        assert fit.ci_high > 0.0

    def test_trend_recovers_growth(self):
        years = pd.RangeIndex(2002, 2016)
        x = np.arange(len(years))
        counts = pd.Series(np.round(np.exp(3.0 + 0.08 * x)).astype(int), index=years)
        fit = fit_intensity_trend(counts)
        assert fit.growth == pytest.approx(0.08, abs=0.02)
        assert fit.p_value < 0.01
        # The projection reproduces the fitted level at the reference year.
        assert fit.intensity_at(fit.year_ref) == pytest.approx(np.exp(fit.level))

    def test_trend_flat_counts(self):
        counts = pd.Series([20] * 14, index=pd.RangeIndex(2002, 2016))
        fit = fit_intensity_trend(counts)
        assert fit.growth == pytest.approx(0.0, abs=1e-4)
        assert fit.p_value > 0.5


class TestSeverity:
    def test_recovers_lognormal(self):
        rng = np.random.default_rng(1234)
        median, sigma, n = 5.0, 1.2, 4000
        losses = np.exp(np.log(median) + sigma * rng.standard_normal(n))
        fit = fit_severity(_frame(rng.integers(2002, 2016, size=n), losses))
        assert fit.median == pytest.approx(median, rel=0.10)
        assert fit.sigma == pytest.approx(sigma, rel=0.05)
        assert fit.n_events == n and fit.n_dropped == 0
        assert not fit.deflated

    def test_drops_nonpositive_losses(self):
        fit = fit_severity(_frame([2002, 2003, 2004, 2005], [1.0, 2.0, 0.0, np.nan]))
        assert fit.n_events == 2 and fit.n_dropped == 2

    def test_severity_trend_and_deflator(self):
        years = np.repeat(np.arange(2002, 2016), 30)
        base = np.tile(np.exp(np.linspace(-1, 1, 30)), 14)  # fixed shape, no trend
        losses = base * np.exp(0.10 * (years - 2002))  # 10%/yr nominal growth
        nominal = fit_severity(_frame(years, losses))
        assert nominal.trend_growth == pytest.approx(0.10, abs=0.01)
        assert nominal.trend_p_value < 0.01

        # A deflator matching the growth removes the trend entirely.
        deflator = pd.Series(
            np.exp(0.10 * (np.arange(2002, 2016) - 2002)), index=pd.RangeIndex(2002, 2016)
        )
        real = fit_severity(_frame(years, losses), deflator=deflator)
        assert real.deflated
        assert real.trend_growth == pytest.approx(0.0, abs=0.01)
        assert real.sigma == pytest.approx(nominal.sigma, rel=0.2)

    def test_deflator_missing_year_raises(self):
        with pytest.raises(ValueError, match="deflator missing years"):
            fit_severity(_frame([2002, 2003], [1.0, 2.0]), deflator=pd.Series({2002: 100.0}))

    def test_to_mark_sampler_rescales_median_only(self):
        fit = fit_severity(_frame([2002, 2003, 2004], [10.0, 20.0, 40.0]))
        sampler = fit.to_mark_sampler(1000.0)
        assert isinstance(sampler, LognormalMark)
        assert sampler.median == pytest.approx(fit.median / 1000.0)
        assert sampler.sigma == pytest.approx(fit.sigma)
        assert sampler.sign == -1.0
        with pytest.raises(ValueError, match="loss_to_mark_scale"):
            fit.to_mark_sampler(0.0)


@pytest.mark.skipif(not EVENTS_CSV.exists(), reason="data/hazard_mx not present (GEN-24)")
def test_real_panel_smoke():
    events = load_climate_events(EVENTS_CSV)
    assert len(events) > 1000
    counts = annual_event_counts(events)
    fit = estimate_intensity(counts)
    assert 50 < fit.intensity < 400
    severity = fit_severity(events)
    assert 0.5 < severity.sigma < 4.0
    assert severity.median > 0
