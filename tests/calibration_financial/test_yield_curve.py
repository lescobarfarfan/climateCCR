"""MXN curve strip, Nelson-Siegel, theta(t) (MKT-CURVE-01/02/03, MKT-IR-02)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from climateCCR.calibration.financial.bond_yield import bono_cashflows
from climateCCR.calibration.financial.hull_white import DAYS_PER_YEAR
from climateCCR.calibration.financial.yield_curve import (
    NelsonSiegelFit,
    fit_nelson_siegel,
    strip_zero_curve,
)

SIE_DIR = Path(__file__).resolve().parents[2] / "data" / "market_mx" / "sie"


def _true_zero(t: np.ndarray | float) -> np.ndarray:
    """A smooth test curve (decimal, continuous Act/365)."""
    return 0.06 + 0.005 * np.log1p(np.asarray(t, dtype=float))


def _synthetic_market() -> tuple[dict[float, float], pd.DataFrame]:
    short_days = [1.0, 28.0, 91.0, 182.0, 364.0]
    short_quotes = {}
    for d in short_days:
        z = float(_true_zero(d / DAYS_PER_YEAR))
        short_quotes[d] = (np.exp(z * d / DAYS_PER_YEAR) - 1.0) * 360.0 / d
    rows = []
    for serie, plazo, cupon_pct in (
        ("B3", 1092.0, 8.0),
        ("B5", 1820.0, 7.5),
        ("B10", 3640.0, 8.5),
    ):
        times_d, amounts = bono_cashflows(plazo, cupon_pct / 100.0)
        times = times_d / DAYS_PER_YEAR
        dirty = float(amounts @ np.exp(-_true_zero(times) * times))
        rows.append({"Serie": serie, "Plazo": plazo, "Cupon": cupon_pct, "Valor": dirty})
    return short_quotes, pd.DataFrame(rows)


def test_strip_recovers_known_curve():
    short_quotes, bonos = _synthetic_market()
    pillars = strip_zero_curve(short_quotes, bonos)
    assert len(pillars) == len(short_quotes) + len(bonos)
    true = _true_zero(pillars["t_years"].to_numpy())
    # < 5 bp everywhere: linear-in-z coupon interpolation vs the smooth truth.
    assert np.abs(pillars["zero"].to_numpy() - true).max() < 5e-4


def test_strip_reprices_exactly():
    short_quotes, bonos = _synthetic_market()
    pillars = strip_zero_curve(short_quotes, bonos)
    grid_t = pillars["t_years"].to_numpy()
    grid_z = pillars["zero"].to_numpy()
    for _, row in bonos.iterrows():
        times_d, amounts = bono_cashflows(row["Plazo"], row["Cupon"] / 100.0)
        times = times_d / DAYS_PER_YEAR
        pv = float(amounts @ np.exp(-np.interp(times, grid_t, grid_z) * times))
        assert pv == pytest.approx(row["Valor"], abs=1e-8)  # DC-MKT-SIE-4


def test_strip_requires_outward_bootstrap():
    short_quotes, bonos = _synthetic_market()
    inside = bonos.assign(Plazo=[200.0, 1820.0, 3640.0])
    with pytest.raises(ValueError, match="beyond the last pillar"):
        strip_zero_curve(short_quotes, inside)


def test_nelson_siegel_recovers_itself():
    true = NelsonSiegelFit(beta0=0.08, beta1=-0.02, beta2=0.015, tau=1.5, rmse=0.0, n_pillars=0)
    t = np.array([0.08, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0])
    fit = fit_nelson_siegel(pd.DataFrame({"t_years": t, "zero": true.zero(t)}))
    probe = np.linspace(0.1, 30.0, 200)
    assert np.abs(fit.zero(probe) - true.zero(probe)).max() < 2e-4  # < 2 bp
    assert fit.rmse < 5e-5  # tau lands on the nearest grid point, not exactly 1.5
    assert float(fit.zero(0.0)) == pytest.approx(true.beta0 + true.beta1, abs=1e-3)


def test_theta_flat_curve_closed_form():
    flat = NelsonSiegelFit(beta0=0.07, beta1=0.0, beta2=0.0, tau=2.0, rmse=0.0, n_pillars=0)
    alpha, sigma = 0.8, 0.012
    t = np.array([0.5, 1.0, 5.0, 20.0])
    expected = alpha * 0.07 + sigma**2 / (2 * alpha) * (1 - np.exp(-2 * alpha * t))
    assert np.allclose(flat.theta(t, alpha, sigma), expected)
    assert np.allclose(flat.forward(t), 0.07)
    assert np.allclose(flat.forward_slope(t), 0.0)


@pytest.mark.integration
@pytest.mark.skipif(not (SIE_DIR / "bonos_m.csv").exists(), reason="SIE data not downloaded")
def test_worked_check_2008_01_23():
    """MKT-CURVE-02 golden: 2008-01-23 -> z(~1.92y) = 7.4187 %.

    The legacy workbook stripped Bonos_0_3 discounting its sub-1Y coupons off
    the short block; the short block here uses the TIIE quotes, which sit a
    few bp off the compounded F-TIIE the workbook used, so the tolerance is
    10 bp — a level check, not a bit-for-bit reproduction.
    """
    date = pd.Timestamp("2008-01-23")
    tiies = pd.read_csv(SIE_DIR / "tiies.csv", index_col="Fecha", parse_dates=True).loc[date]
    cetes = pd.read_csv(SIE_DIR / "cetes364.csv", index_col="Fecha", parse_dates=True).loc[date]
    bonos = pd.read_csv(SIE_DIR / "bonos_m.csv", parse_dates=["Fecha"])
    bucket = bonos[(bonos["Fecha"] == date) & (bonos["Serie"] == "BonosM_0_3")]
    candidates = {
        1.0: tiies["FTIIE"] / 100.0,
        28.0: tiies["TIIE28"] / 100.0,
        91.0: tiies["TIIE91"] / 100.0,  # not quoted that day
        182.0: tiies["TIIE182"] / 100.0,  # series starts 2011
        float(cetes["Plazo"]): cetes["TasaRendimiento"] / 100.0,
    }
    short_quotes = {d: q for d, q in candidates.items() if pd.notna(q)}
    pillars = strip_zero_curve(short_quotes, bucket)
    stripped = pillars.iloc[-1]
    assert stripped["t_years"] == pytest.approx(1.92, abs=0.02)
    assert stripped["zero"] == pytest.approx(0.074187, abs=10e-4)
