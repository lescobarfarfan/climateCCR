"""Jump-channel inputs estimated from the CENAPRED event panel (OQ-INT-07, OQ-HAZ-12).

The climate jump channel (DC-CCR-SIM-2, DC-XWALK-4) needs two HAZ estimates: the
arrival intensity ``lambda`` and the per-event jump-mark distribution. This module
fits both from the consolidated CENAPRED climate-event table
(``eventos_cenapred_climada.csv``, DC-HAZ-CENAPRED-2/3):

- **Frequency** — annual national event counts -> homogeneous-Poisson MLE with an
  exact (Garwood) confidence interval, plus a log-linear trend
  ``lambda(year) = exp(level + growth * (year - year_ref))`` whose likelihood-ratio
  test answers whether arrivals are rising (OQ-INT-07). ``intensity_at`` projects
  the trend onto simulation-grid years as the 1-D trajectory intensity the built
  channel already accepts (INT-13).
- **Severity** — per-event losses ``danio_mdp`` -> lognormal fit by MLE (the INT-13
  adverse mark family). Losses are millions of *current* MXN (GEN-13); pass
  ``deflator`` (a price index by year, e.g. INEGI INPC) to fit in real terms.
  The loss->mark translation stays an explicit seam: ``to_mark_sampler(K)`` maps a
  loss ``L`` onto a mark ``L / K``, so the fitted ``sigma`` transfers exactly and
  only the median rescales; fixing ``K`` — the loss-absorbing scale of the target
  portfolio — is the open decision OQ-INT-04 / OQ-INT-07.

Spanish column names are the data contract, kept verbatim (INT-07).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats

from climateCCR.processes.jumps import LognormalMark

#: Rows spanning (almost) a full year are annual state aggregates (e.g. the
#: CONAFOR forest-fire rows), not discrete events — excluded from per-event fits.
ANNUAL_AGGREGATE_MIN_DAYS = 360.0

_REQUIRED_COLUMNS = (
    "anio",
    "duracion_dias",
    "peril_canonico",
    "en_alcance_climatico",
    "danio_mdp",
)


def load_climate_events(
    csv_path: str | Path,
    *,
    start_year: int = 2002,
    end_year: int = 2015,
    perils: Iterable[str] | None = None,
    min_damage_mdp: float | None = None,
) -> pd.DataFrame:
    """Discrete climate-scope CENAPRED events for the estimation window.

    The default window drops 2000-01 (reporting ramp-in: 32 and 11 events vs
    ~150-240/yr afterwards) and ends at 2015, the extent of the event-level base
    (DC-HAZ-CENAPRED-1). Filters applied:

    - ``en_alcance_climatico == "si"`` (GEN-12);
    - discrete events only — ``duracion_dias`` missing or below
      :data:`ANNUAL_AGGREGATE_MIN_DAYS`;
    - optionally a ``peril_canonico`` subset and a minimum ``danio_mdp`` —
      together the "which events trigger a jump" knob.

    The window is stamped on ``.attrs["window"]`` so downstream counts keep the
    zero-event years in the exposure time.
    """
    if start_year > end_year:
        raise ValueError(f"start_year {start_year} > end_year {end_year}")
    events = pd.read_csv(csv_path, low_memory=False)
    missing = [c for c in _REQUIRED_COLUMNS if c not in events.columns]
    if missing:
        raise ValueError(f"{csv_path}: missing required columns {missing}")

    mask = (
        (events["en_alcance_climatico"] == "si")
        & (events["duracion_dias"].isna() | (events["duracion_dias"] < ANNUAL_AGGREGATE_MIN_DAYS))
        & events["anio"].between(start_year, end_year)
    )
    if perils is not None:
        mask &= events["peril_canonico"].isin(list(perils))
    if min_damage_mdp is not None:
        mask &= events["danio_mdp"] >= min_damage_mdp
    out = events.loc[mask].copy()
    out.attrs["window"] = (int(start_year), int(end_year))
    return out


def annual_event_counts(
    events: pd.DataFrame,
    start_year: int | None = None,
    end_year: int | None = None,
) -> pd.Series:
    """Events per calendar year, zero-filled over the full window.

    Zero-filling matters: a year with no qualifying events still contributes
    exposure time to the Poisson fit. The window defaults to the one stamped by
    :func:`load_climate_events`.
    """
    if start_year is None or end_year is None:
        window = events.attrs.get("window")
        if window is None:
            raise ValueError("events carry no window; pass start_year and end_year")
        start_year, end_year = window
    counts = events["anio"].astype(int).value_counts()
    years = pd.RangeIndex(int(start_year), int(end_year) + 1, name="anio")
    return counts.reindex(years, fill_value=0).astype(int)


@dataclass(frozen=True)
class PoissonIntensityFit:
    """Homogeneous-Poisson arrival intensity in events/year (the INT-13 scalar knob)."""

    intensity: float
    ci_low: float
    ci_high: float
    alpha: float
    n_events: int
    n_years: int


def estimate_intensity(counts: pd.Series, *, alpha: float = 0.05) -> PoissonIntensityFit:
    """MLE ``N / T`` with the exact (Garwood) chi-square confidence interval."""
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    t = len(counts)
    if t == 0:
        raise ValueError("counts is empty")
    n = int(counts.sum())
    ci_low = float(stats.chi2.ppf(alpha / 2, 2 * n) / (2 * t)) if n > 0 else 0.0
    ci_high = float(stats.chi2.ppf(1 - alpha / 2, 2 * n + 2) / (2 * t))
    return PoissonIntensityFit(
        intensity=n / t, ci_low=ci_low, ci_high=ci_high, alpha=alpha, n_events=n, n_years=t
    )


@dataclass(frozen=True)
class IntensityTrendFit:
    """Log-linear Poisson trend ``lambda(year) = exp(level + growth * (year - year_ref))``.

    ``growth`` is the log-growth per year (``expm1(growth)`` = fractional change);
    ``p_value`` is the likelihood-ratio test of ``growth == 0`` — the "are arrivals
    rising" question of OQ-INT-07.
    """

    level: float
    growth: float
    year_ref: int
    p_value: float

    def intensity_at(self, years: float | np.ndarray) -> np.ndarray:
        """Trend intensity at calendar ``years`` — the 1-D trajectory feed (INT-13)."""
        return np.exp(self.level + self.growth * (np.asarray(years, dtype=float) - self.year_ref))


def fit_intensity_trend(counts: pd.Series) -> IntensityTrendFit:
    """Fit the log-linear Poisson trend by MLE on the annual counts."""
    if len(counts) < 3:
        raise ValueError(f"need >= 3 years to fit a trend, got {len(counts)}")
    n = counts.to_numpy(dtype=float)
    if n.sum() == 0:
        raise ValueError("no events in counts")
    years = counts.index.to_numpy(dtype=float)
    year_ref = years[0]
    x = years - year_ref

    def negll(params: np.ndarray) -> float:
        log_lam = params[0] + params[1] * x
        return float(np.sum(np.exp(log_lam) - n * log_lam))

    def grad(params: np.ndarray) -> np.ndarray:
        resid = np.exp(params[0] + params[1] * x) - n
        return np.array([resid.sum(), (resid * x).sum()])

    flat = np.array([np.log(n.mean()), 0.0])  # the flat model's own MLE
    res = optimize.minimize(negll, x0=flat, jac=grad, method="BFGS")
    if not res.success:
        raise RuntimeError(f"Poisson trend fit did not converge: {res.message}")
    deviance = max(0.0, 2.0 * (negll(flat) - negll(res.x)))
    return IntensityTrendFit(
        level=float(res.x[0]),
        growth=float(res.x[1]),
        year_ref=int(year_ref),
        p_value=float(stats.chi2.sf(deviance, df=1)),
    )


@dataclass(frozen=True)
class LognormalSeverityFit:
    """Lognormal per-event loss severity (the INT-13 adverse mark family).

    ``median`` is in millions of MXN — *current* pesos unless ``deflated``
    (GEN-13). ``trend_growth``/``trend_p_value`` are the OLS slope of log-loss on
    year: the severity-trend diagnostic that would motivate time-aware marks
    (OQ-INT-07's step-aware sampler extension).
    """

    median: float
    sigma: float
    n_events: int
    n_dropped: int
    deflated: bool
    trend_growth: float
    trend_p_value: float

    def to_mark_sampler(self, loss_to_mark_scale: float, *, sign: float = -1.0) -> LognormalMark:
        """The DC-XWALK-4 hand-off: a loss of ``L`` becomes a mark of ``L / scale``.

        Dividing a lognormal by a constant rescales the median and preserves
        ``sigma``, so the fitted shape carries over exactly; choosing the scale —
        the loss-absorbing size of the target portfolio — is OQ-INT-04/OQ-INT-07.
        """
        if loss_to_mark_scale <= 0:
            raise ValueError(f"loss_to_mark_scale must be > 0, got {loss_to_mark_scale}")
        return LognormalMark(median=self.median / loss_to_mark_scale, sigma=self.sigma, sign=sign)


def fit_severity(
    events: pd.DataFrame,
    *,
    deflator: Mapping[int, float] | pd.Series | None = None,
) -> LognormalSeverityFit:
    """Fit the lognormal severity by MLE on per-event ``danio_mdp``.

    Non-positive / missing losses are dropped (reported via ``n_dropped``) — an
    event with no recorded damage carries no information about severity size.
    ``deflator`` is a price index by calendar year (e.g. INEGI INPC); losses are
    restated to the *latest* year in the index. Without it the fit is on current
    pesos and inflation stays inside ``sigma`` and the trend (``deflated=False``).
    """
    keep = events["danio_mdp"].notna() & (events["danio_mdp"] > 0)
    losses = events.loc[keep, "danio_mdp"].astype(float)
    years = events.loc[keep, "anio"].astype(int)
    n_dropped = int((~keep).sum())
    if len(losses) < 2:
        raise ValueError(f"need >= 2 positive losses to fit severity, got {len(losses)}")

    if deflator is not None:
        index = pd.Series(deflator).astype(float)
        missing_years = sorted(set(years.unique()) - set(index.index))
        if missing_years:
            raise ValueError(f"deflator missing years: {missing_years}")
        base = index.loc[index.index.max()]
        losses = losses * (base / index.loc[years].to_numpy())

    logs = np.log(losses.to_numpy())
    if years.nunique() >= 2:
        trend = stats.linregress(years.to_numpy(dtype=float), logs)
        trend_growth, trend_p = float(trend.slope), float(trend.pvalue)
    else:
        trend_growth, trend_p = float("nan"), float("nan")
    return LognormalSeverityFit(
        median=float(np.exp(logs.mean())),
        sigma=float(logs.std(ddof=0)),  # MLE
        n_events=int(len(logs)),
        n_dropped=n_dropped,
        deflated=deflator is not None,
        trend_growth=trend_growth,
        trend_p_value=trend_p,
    )
