"""MXN zero curve strip + Nelson-Siegel fit + HW1F ``theta(t)`` (OQ-MKT-12a).

The cross-sectional half of the Hull-White calibration (MKT-IR-02): every SIE
tenor enters here. Pillars are

- the short block — F-TIIE overnight and the TIIE 28/91/182 quotes, converted
  simple Act/360 -> continuous Act/365 (MKT-SIE-04);
- the 364-day Cetes, the clean 1Y zero pillar (MKT-CURVE-01);
- the on-the-run Bonos M buckets, stripped from **dirty price** by a recursive
  root-find linear in the zero rate, discounting sub-pillar coupons off the
  already-known curve (MKT-CURVE-02; worked check 2008-01-23 ->
  ``z(1.92y) = 7.4187 %``).

Canonical tenors are read off the fitted continuous curve, never off the
drifting raw buckets (MKT-CURVE-03): a Nelson-Siegel fit profiled over
``tau`` (linear least squares per ``tau``), whose forward curve is analytic —
so ``theta(t) = df/dt + a*f + sigma^2/(2a)*(1 - e^{-2at})`` needs no numerical
differentiation (MKT-IR-02, [Hull1990]). Piecewise-linear zeros are never the
final curve (garbage forward derivative). [NelsonSiegel1987]
[BrigoMercurio2006]
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import optimize

from climateCCR.calibration.financial.bond_yield import bono_cashflows
from climateCCR.calibration.financial.hull_white import DAYS_PER_YEAR, simple_to_continuous


def strip_zero_curve(
    short_quotes: Mapping[float, float],
    bonos: pd.DataFrame,
) -> pd.DataFrame:
    """Zero pillars (continuous Act/365) for one valuation date.

    ``short_quotes`` maps tenor days -> decimal simple Act/360 quote (F-TIIE,
    TIIEs, Cetes with its actual residual ``Plazo``); ``bonos`` holds that
    date's bucket rows with as-published units (``Serie``, ``Plazo`` days,
    ``Cupon`` percent, ``Valor`` dirty per 100). Buckets bootstrap in maturity
    order: coupons before the last known pillar discount off the known curve,
    the segment up to maturity interpolates linearly in ``z`` against the
    unknown ``z(T)``, and brentq closes the dirty price. Output rows
    ``(t_years, zero, source)`` reprice their instruments exactly by
    construction (DC-MKT-SIE-4).
    """
    if not short_quotes:
        raise ValueError("short_quotes is empty")
    pillar_t = [d / DAYS_PER_YEAR for d in sorted(short_quotes)]
    pillar_z = [float(simple_to_continuous(short_quotes[d], d)) for d in sorted(short_quotes)]
    sources = [f"{int(round(d))}D_simple" for d in sorted(short_quotes)]

    frame = bonos.dropna(subset=["Plazo", "Cupon", "Valor"]).sort_values("Plazo")
    for _, row in frame.iterrows():
        maturity = float(row["Plazo"]) / DAYS_PER_YEAR
        if maturity <= pillar_t[-1]:
            raise ValueError(
                f"{row['Serie']}: maturity {maturity:.2f}y not beyond the last pillar "
                f"{pillar_t[-1]:.2f}y — buckets must bootstrap outward"
            )
        times_d, amounts = bono_cashflows(float(row["Plazo"]), float(row["Cupon"]) / 100.0)
        times = times_d / DAYS_PER_YEAR

        def dirty_minus_target(
            z_maturity: float,
            times: np.ndarray = times,
            amounts: np.ndarray = amounts,
            maturity: float = maturity,
            target: float = float(row["Valor"]),
        ) -> float:
            zeros = np.interp(times, pillar_t + [maturity], pillar_z + [z_maturity])
            return float(amounts @ np.exp(-zeros * times)) - target

        solved = float(optimize.brentq(dirty_minus_target, 1e-9, 2.0))
        pillar_t.append(maturity)
        pillar_z.append(solved)
        sources.append(str(row["Serie"]))

    return pd.DataFrame({"t_years": pillar_t, "zero": pillar_z, "source": sources})


@dataclass(frozen=True)
class NelsonSiegelFit:
    """``z(t) = b0 + b1*h(t) + b2*(h(t) - e^{-t/tau})``, ``h = (1-e^{-t/tau})/(t/tau)``."""

    beta0: float
    beta1: float
    beta2: float
    tau: float
    rmse: float
    n_pillars: int

    def zero(self, t: np.ndarray | float) -> np.ndarray:
        x = np.asarray(t, dtype=float) / self.tau
        with np.errstate(divide="ignore", invalid="ignore"):
            hump = np.where(x > 0, (1.0 - np.exp(-x)) / x, 1.0)  # -> 1 as t -> 0
        return self.beta0 + self.beta1 * hump + self.beta2 * (hump - np.exp(-x))

    def forward(self, t: np.ndarray | float) -> np.ndarray:
        """Instantaneous forward ``f(t) = b0 + b1 e^{-t/tau} + b2 (t/tau) e^{-t/tau}``."""
        x = np.asarray(t, dtype=float) / self.tau
        return self.beta0 + (self.beta1 + self.beta2 * x) * np.exp(-x)

    def forward_slope(self, t: np.ndarray | float) -> np.ndarray:
        """Analytic ``df/dt``."""
        x = np.asarray(t, dtype=float) / self.tau
        return np.exp(-x) / self.tau * (-self.beta1 + self.beta2 * (1.0 - x))

    def theta(self, t: np.ndarray | float, alpha: float, sigma: float) -> np.ndarray:
        """HW1F drift ``theta(t)`` reproducing this curve (MKT-IR-02, [Hull1990])."""
        t = np.asarray(t, dtype=float)
        variance_term = sigma**2 / (2.0 * alpha) * (1.0 - np.exp(-2.0 * alpha * t))
        return self.forward_slope(t) + alpha * self.forward(t) + variance_term


def fit_nelson_siegel(
    pillars: pd.DataFrame,
    *,
    tau_grid: np.ndarray | None = None,
) -> NelsonSiegelFit:
    """Least-squares Nelson-Siegel, ``tau`` profiled over a grid.

    For fixed ``tau`` the betas are a linear problem, so the fit is a small
    ``lstsq`` per grid point — no nonconvex optimizer to diverge. ``pillars``
    is the :func:`strip_zero_curve` output (needs >= 4 points).
    """
    t = pillars["t_years"].to_numpy(dtype=float)
    z = pillars["zero"].to_numpy(dtype=float)
    if len(t) < 4:
        raise ValueError(f"need >= 4 pillars for Nelson-Siegel, got {len(t)}")
    if tau_grid is None:
        tau_grid = np.geomspace(0.05, 10.0, 80)

    best: tuple[float, np.ndarray, float] | None = None
    for tau in tau_grid:
        x = t / tau
        hump = (1.0 - np.exp(-x)) / x
        design = np.column_stack([np.ones_like(t), hump, hump - np.exp(-x)])
        betas, *_ = np.linalg.lstsq(design, z, rcond=None)
        sse = float(np.sum((design @ betas - z) ** 2))
        if best is None or sse < best[0]:
            best = (sse, betas, float(tau))
    sse, betas, tau = best
    return NelsonSiegelFit(
        beta0=float(betas[0]),
        beta1=float(betas[1]),
        beta2=float(betas[2]),
        tau=tau,
        rmse=float(np.sqrt(sse / len(t))),
        n_pillars=len(t),
    )
