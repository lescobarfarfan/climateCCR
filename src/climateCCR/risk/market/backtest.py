"""Backtesting statistics for forecast distributions — the INT-40 validation layer.

Pure functions over arrays (no model objects, INT-15): a forecast is represented
either by predictive **samples** (``(n_sims, n_obs)``, column ``j`` = the draws for
observation ``j``) or by a **Gaussian** ``(mean, sd)``; realisations are a plain
``(n_obs,)`` vector. Everything reduces to the probability integral transform (PIT)
— ``F_j(y_j)`` — which is iid U(0, 1) when the forecast densities are the true
conditional densities [DieboldGuntherTay1998]; the Basel reliability criterion
(realised frequency between the p-th and q-th forecast percentiles ≈ q − p,
BCBS 2010 ¶25, assessed at several percentiles, ¶31) is the same object read as
a coverage table.

- coverage / reliability: :func:`coverage_by_percentile`, :func:`central_coverage`;
- exception tests at one level: :func:`kupiec_pof` [Kupiec1995],
  :func:`christoffersen_independence` / :func:`christoffersen_cc` [Christoffersen1998];
- whole-distribution tests: :func:`ks_uniform`, :func:`berkowitz_lr` [Berkowitz2001];
- proper scores: :func:`crps_from_samples` / :func:`crps_normal`,
  :func:`log_score_normal` / :func:`log_score_mixture` [GneitingRaftery2007];
- comparing two forecasts: :func:`diebold_mariano` on a score differential
  [DieboldMariano1995] — on log scores it is the Amisano–Giacomini test
  [AmisanoGiacomini2007].
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import logsumexp, xlogy

DEFAULT_PERCENTILES = (0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)
DEFAULT_CENTRAL_LEVELS = (0.5, 0.8, 0.95)
_PIT_EPS = 1e-10


@dataclass(frozen=True)
class TestResult:
    """A test statistic with its p-value, degrees of freedom and sample size."""

    statistic: float
    p_value: float
    df: int
    n: int


# ------------------------------------------------------------------ PIT values


def pit_values(
    samples: np.ndarray, realised: Sequence[float], rng: np.random.Generator | None = None
) -> np.ndarray:
    """PIT of each realisation under its sample-based predictive distribution.

    ``samples`` is ``(n_sims, n_obs)``; the PIT is the fraction of draws strictly
    below ``y`` plus the tie mass split at its midpoint — or, with ``rng``, a
    uniform draw inside the tie mass (the randomised PIT, exact for atoms such as
    a compound-Poisson zero).
    """
    s = np.asarray(samples, dtype=float)
    y = np.asarray(realised, dtype=float)
    if s.ndim != 2 or y.shape != (s.shape[1],):
        raise ValueError(f"samples must be (n_sims, n_obs) and realised (n_obs,): {s.shape}")
    below = (s < y).mean(axis=0)
    equal = (s == y).mean(axis=0)
    u = 0.5 if rng is None else rng.uniform(size=y.shape)
    return below + u * equal


def pit_discrete(
    cdf_at_y: Sequence[float],
    cdf_below_y: Sequence[float],
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """PIT for count data from ``F(y)`` and ``F(y - 1)``: midpoint, or randomised with ``rng``.

    [CzadoGneitingHeld2009]: ``u ~ U(F(y-1), F(y))`` is uniform under the true
    model; the non-randomised midpoint is the deterministic reading.
    """
    hi = np.asarray(cdf_at_y, dtype=float)
    lo = np.asarray(cdf_below_y, dtype=float)
    if hi.shape != lo.shape or (lo > hi).any():
        raise ValueError("cdf_below_y must be <= cdf_at_y elementwise")
    u = 0.5 if rng is None else rng.uniform(size=hi.shape)
    return lo + u * (hi - lo)


def pit_normal(realised: Sequence[float], mean: Sequence[float], sd: Sequence[float]) -> np.ndarray:
    """PIT under Gaussian forecasts ``N(mean, sd^2)`` (vectorised)."""
    y, m, s = (np.asarray(a, dtype=float) for a in (realised, mean, sd))
    if (s <= 0).any():
        raise ValueError("sd must be positive")
    return stats.norm.cdf((y - m) / s)


# ------------------------------------------------------------ coverage tables


def _binomial_se(p: np.ndarray, n: int) -> np.ndarray:
    return np.sqrt(p * (1.0 - p) / n)


def coverage_by_percentile(
    pit: Sequence[float], probs: Sequence[float] = DEFAULT_PERCENTILES
) -> pd.DataFrame:
    """Reliability table: share of PIT values ``<= p`` against nominal ``p`` (BCBS 2010 ¶25/¶31).

    Columns ``nominal, empirical, n, binom_se``; ``binom_se`` is the iid binomial
    standard error ``sqrt(p (1 - p) / n)`` — a floor when forecasts overlap.
    """
    u = np.asarray(pit, dtype=float)
    p = np.asarray(probs, dtype=float)
    if u.ndim != 1 or not u.size:
        raise ValueError("pit must be a non-empty 1-D array")
    if ((p <= 0) | (p >= 1)).any():
        raise ValueError("percentiles must lie strictly inside (0, 1)")
    empirical = np.array([(u <= q).mean() for q in p])
    return pd.DataFrame(
        {"nominal": p, "empirical": empirical, "n": u.size, "binom_se": _binomial_se(p, u.size)}
    )


def central_coverage(
    pit: Sequence[float], levels: Sequence[float] = DEFAULT_CENTRAL_LEVELS
) -> pd.DataFrame:
    """Share of PIT values inside the central ``level`` band ``[(1-l)/2, 1-(1-l)/2]`` per level."""
    u = np.asarray(pit, dtype=float)
    lv = np.asarray(levels, dtype=float)
    if ((lv <= 0) | (lv >= 1)).any():
        raise ValueError("levels must lie strictly inside (0, 1)")
    lo = (1.0 - lv) / 2.0
    empirical = np.array([((u >= a) & (u <= 1.0 - a)).mean() for a in lo])
    return pd.DataFrame(
        {"nominal": lv, "empirical": empirical, "n": u.size, "binom_se": _binomial_se(lv, u.size)}
    )


# ------------------------------------------------------------ exception tests


def kupiec_pof(n_hits: int, n: int, p: float) -> TestResult:
    """Kupiec (1995) proportion-of-failures likelihood-ratio test, ``chi2(1)``.

    ``n_hits`` exceptions in ``n`` trials against the nominal exception rate ``p``.
    """
    x, n = int(n_hits), int(n)
    if n <= 0 or not 0 < p < 1 or not 0 <= x <= n:
        raise ValueError("need n > 0, 0 < p < 1 and 0 <= n_hits <= n")
    phat = x / n
    ll_null = xlogy(x, p) + xlogy(n - x, 1.0 - p)
    ll_alt = xlogy(x, phat) + xlogy(n - x, 1.0 - phat)
    statistic = float(max(-2.0 * (ll_null - ll_alt), 0.0))
    return TestResult(statistic, float(stats.chi2.sf(statistic, 1)), 1, n)


def _transition_counts(hits: np.ndarray) -> tuple[int, int, int, int]:
    prev, nxt = hits[:-1], hits[1:]
    n00 = int(((prev == 0) & (nxt == 0)).sum())
    n01 = int(((prev == 0) & (nxt == 1)).sum())
    n10 = int(((prev == 1) & (nxt == 0)).sum())
    n11 = int(((prev == 1) & (nxt == 1)).sum())
    return n00, n01, n10, n11


def christoffersen_independence(hits: Sequence[int]) -> TestResult:
    """Christoffersen (1998) independence test: Markov vs iid exceptions, ``chi2(1)``."""
    h = np.asarray(hits, dtype=int)
    if h.ndim != 1 or h.size < 2 or not np.isin(h, (0, 1)).all():
        raise ValueError("hits must be a 0/1 sequence with >= 2 elements")
    n00, n01, n10, n11 = _transition_counts(h)
    pi01 = n01 / (n00 + n01) if n00 + n01 else 0.0
    pi11 = n11 / (n10 + n11) if n10 + n11 else 0.0
    pi = (n01 + n11) / (h.size - 1)
    ll_ind = xlogy(n00 + n10, 1.0 - pi) + xlogy(n01 + n11, pi)
    ll_markov = (
        xlogy(n00, 1.0 - pi01) + xlogy(n01, pi01) + xlogy(n10, 1.0 - pi11) + xlogy(n11, pi11)
    )
    statistic = float(max(-2.0 * (ll_ind - ll_markov), 0.0))
    return TestResult(statistic, float(stats.chi2.sf(statistic, 1)), 1, int(h.size))


def christoffersen_cc(hits: Sequence[int], p: float) -> TestResult:
    """Conditional-coverage test: Kupiec POF + independence, ``chi2(2)`` [Christoffersen1998]."""
    h = np.asarray(hits, dtype=int)
    pof = kupiec_pof(int(h.sum()), int(h.size), p)
    ind = christoffersen_independence(h)
    statistic = pof.statistic + ind.statistic
    return TestResult(statistic, float(stats.chi2.sf(statistic, 2)), 2, int(h.size))


# ------------------------------------------------------ whole-distribution tests


def ks_uniform(pit: Sequence[float]) -> TestResult:
    """Kolmogorov–Smirnov test of the PIT values against U(0, 1)."""
    u = np.asarray(pit, dtype=float)
    res = stats.kstest(u, "uniform")
    return TestResult(float(res.statistic), float(res.pvalue), 0, int(u.size))


def berkowitz_lr(pit: Sequence[float]) -> TestResult:
    """Berkowitz (2001) LR test on ``z = Phi^{-1}(PIT)``: AR(1) vs iid N(0, 1), ``chi2(3)``.

    The conditional (first observation given) Gaussian likelihood of
    ``z_t = mu + rho z_{t-1} + eps_t`` is maximised in closed form (OLS) and
    compared with ``(mu, rho, sigma) = (0, 0, 1)``; ``chi2(3)``. PIT values are
    clipped away from 0/1 so a single tail exception cannot produce an infinite
    normal score.
    """
    u = np.clip(np.asarray(pit, dtype=float), _PIT_EPS, 1.0 - _PIT_EPS)
    if u.ndim != 1 or u.size < 4:
        raise ValueError("need >= 4 PIT values")
    z = stats.norm.ppf(u)
    z0, z1 = z[:-1], z[1:]
    var0 = float(np.var(z0))
    rho = float(np.cov(z0, z1, bias=True)[0, 1] / var0) if var0 > 0 else 0.0
    mu = float(z1.mean() - rho * z0.mean())
    resid = z1 - mu - rho * z0
    sigma = float(np.sqrt(np.mean(resid**2)))
    ll_alt = float(stats.norm.logpdf(resid, 0.0, sigma).sum())
    ll_null = float(stats.norm.logpdf(z1, 0.0, 1.0).sum())
    statistic = float(max(-2.0 * (ll_null - ll_alt), 0.0))
    return TestResult(statistic, float(stats.chi2.sf(statistic, 3)), 3, int(u.size))


# ------------------------------------------------------------- proper scores


def crps_from_samples(samples: np.ndarray, realised: Sequence[float]) -> np.ndarray:
    """CRPS per observation from predictive samples: ``E|X - y| - E|X - X'| / 2``.

    The energy form of [GneitingRaftery2007]; ``E|X - X'|`` uses the sorted-sample
    identity ``(2 / n^2) * sum_i (2 i - n - 1) x_(i)`` (``i`` one-based), so the cost
    is ``O(n log n)`` per column. Lower is better; units of ``y``.
    """
    s = np.asarray(samples, dtype=float)
    y = np.asarray(realised, dtype=float)
    if s.ndim != 2 or y.shape != (s.shape[1],):
        raise ValueError(f"samples must be (n_sims, n_obs) and realised (n_obs,): {s.shape}")
    n = s.shape[0]
    term1 = np.abs(s - y).mean(axis=0)
    ranks = 2.0 * np.arange(1, n + 1) - n - 1.0
    term2 = (np.sort(s, axis=0) * ranks[:, None]).sum(axis=0) * (2.0 / n**2)
    return term1 - 0.5 * term2


def crps_normal(
    realised: Sequence[float], mean: Sequence[float], sd: Sequence[float]
) -> np.ndarray:
    """Closed-form CRPS of Gaussian forecasts ``N(mean, sd^2)`` [GneitingRaftery2007]."""
    y, m, s = (np.asarray(a, dtype=float) for a in (realised, mean, sd))
    if (s <= 0).any():
        raise ValueError("sd must be positive")
    z = (y - m) / s
    tail = 2.0 * stats.norm.pdf(z) - 1.0 / np.sqrt(np.pi)
    return s * (z * (2.0 * stats.norm.cdf(z) - 1.0) + tail)


def log_score_normal(
    realised: Sequence[float], mean: Sequence[float], sd: Sequence[float]
) -> np.ndarray:
    """Log predictive density of Gaussian forecasts at the realisations (higher is better)."""
    y, m, s = (np.asarray(a, dtype=float) for a in (realised, mean, sd))
    if (s <= 0).any():
        raise ValueError("sd must be positive")
    return stats.norm.logpdf(y, m, s)


def log_score_mixture(
    realised: Sequence[float], shifts: Sequence[float], mean: Sequence[float], sd: Sequence[float]
) -> np.ndarray:
    """Log density of the Gaussian mixture ``y ~ N(mean + J, sd^2)``, ``J`` in ``shifts``.

    The Rao-Blackwellised density of a jump-diffusion over one horizon: condition
    on the simulated jump total ``J`` (``(n_sims,)``), average the exact Gaussian
    density over the draws — ``logsumexp`` keeps it finite far in the tails.
    """
    y, m, s = (np.asarray(a, dtype=float) for a in (realised, mean, sd))
    j = np.asarray(shifts, dtype=float)
    if j.ndim != 1 or not j.size:
        raise ValueError("shifts must be a non-empty 1-D array of simulated jump totals")
    if (s <= 0).any():
        raise ValueError("sd must be positive")
    logpdf = stats.norm.logpdf(y[None, :], m[None, :] + j[:, None], np.broadcast_to(s, y.shape))
    return logsumexp(logpdf, axis=0) - np.log(j.size)


# ---------------------------------------------------------- forecast comparison


def diebold_mariano(differential: Sequence[float], lag: int = 0) -> TestResult:
    """Diebold–Mariano test that a score differential has zero mean (two-sided, N(0, 1)).

    ``differential`` is per-observation ``score_A - score_B``; the long-run variance
    uses a Bartlett kernel over ``lag`` autocovariances (``lag = h - 1`` for
    ``h``-step overlapping forecasts). On log-score differences this is the
    Amisano–Giacomini (2007) comparison of two density forecasts.
    """
    d = np.asarray(differential, dtype=float)
    if d.ndim != 1 or d.size < 3:
        raise ValueError("need >= 3 differentials")
    if lag < 0 or lag >= d.size:
        raise ValueError("lag must satisfy 0 <= lag < len(differential)")
    n = d.size
    dbar = float(d.mean())
    centred = d - dbar
    long_run = float(np.dot(centred, centred) / n)
    for k in range(1, lag + 1):
        gamma_k = float(np.dot(centred[k:], centred[:-k]) / n)
        long_run += 2.0 * (1.0 - k / (lag + 1.0)) * gamma_k
    if long_run <= 0:
        raise ValueError("non-positive long-run variance (constant differential?)")
    statistic = dbar / np.sqrt(long_run / n)
    return TestResult(float(statistic), float(2.0 * stats.norm.sf(abs(statistic))), 0, n)


__all__ = [
    "DEFAULT_CENTRAL_LEVELS",
    "DEFAULT_PERCENTILES",
    "TestResult",
    "berkowitz_lr",
    "central_coverage",
    "christoffersen_cc",
    "christoffersen_independence",
    "coverage_by_percentile",
    "crps_from_samples",
    "crps_normal",
    "diebold_mariano",
    "ks_uniform",
    "kupiec_pof",
    "log_score_mixture",
    "log_score_normal",
    "pit_discrete",
    "pit_normal",
    "pit_values",
]
