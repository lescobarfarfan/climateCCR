"""Sector event study around cyclone episodes — the OQ-INT-11 Phase C validation.

The INT-24/25 marks assert an *ordering*: on a cyclone event, high-``c_ciclon``
names (ASUR, HOTEL) should move more than low-``c`` names (GCC, VISTA). This
module tests that ordering against realized equity returns, reusing the
INT-18/19 event-study conventions (market model estimated on a pre-event
window, CARs summed over post-event business days, episode construction via
:func:`~climateCCR.calibration.impact.rate_response.build_episodes`) with the
market model on daily *log returns* against the IPC instead of yield changes
against a US control.

The test statistic is Kendall's tau between per-name mean CAR and the name's
``c_ciclon`` (H1: tau < 0 — climate-sensitive names lose more), with the
gating p-value from an *episode-level* bootstrap: names share each episode's
residual sector co-movement, so resampling episodes — not (name, episode)
cells — is what respects the panel dependence (the INT-18 pairs-bootstrap
pattern one level up). Adoption is gated by the pre-registered criterion
pinned in ``configs/sector_event_study.yaml``, never decided after seeing the
numbers; a null is reportable (INT-19 precedent). [MacKinlay1997]
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def episode_cars(
    log_prices: pd.Series,
    log_market: pd.Series,
    episodes: pd.DataFrame,
    *,
    estimation_window_bd: tuple[int, int] = (-120, -10),
    event_window_bd: int = 5,
    min_estimation_obs: int = 60,
    max_missing_frac: float = 0.4,
) -> pd.DataFrame:
    """Per-episode market-model CARs for one name (log-return convention).

    ``log_prices``/``log_market`` are daily log levels indexed by date; the
    trading grid is the *name's* own calendar (market days reindex onto it).
    Episode date maps to the first trading day at or after ``fecha``; an
    episode is skipped when the estimation window is short, the event window
    too sparse, or the name is not yet listed — same rules as
    ``rate_response.event_study``, so the two studies share one convention.
    Returns a frame indexed by episode ``fecha`` with ``car`` and ``n_days``.
    """
    grid = log_prices.sort_index()
    dy = grid.diff()
    dm = log_market.sort_index().diff().reindex(dy.index)
    est_lo, est_hi = estimation_window_bd
    rows: list[dict] = []

    for _, episode in episodes.iterrows():
        day0 = int(np.searchsorted(dy.index.to_numpy(), np.datetime64(episode["fecha"])))
        if day0 + est_lo < 0 or day0 + event_window_bd >= len(dy):
            continue
        est = pd.DataFrame(
            {
                "dy": dy.iloc[day0 + est_lo : day0 + est_hi + 1],
                "dm": dm.iloc[day0 + est_lo : day0 + est_hi + 1],
            }
        ).dropna()
        if len(est) < min_estimation_obs:
            continue
        slope, intercept = np.polyfit(est["dm"], est["dy"], 1)
        window = pd.DataFrame(
            {
                "dy": dy.iloc[day0 : day0 + event_window_bd + 1],
                "dm": dm.iloc[day0 : day0 + event_window_bd + 1],
            }
        ).dropna()
        if len(window) < (1 - max_missing_frac) * (event_window_bd + 1):
            continue
        abnormal = window["dy"] - (intercept + slope * window["dm"])
        rows.append(
            {"fecha": episode["fecha"], "car": float(abnormal.sum()), "n_days": len(window)}
        )
    return pd.DataFrame(rows, columns=["fecha", "car", "n_days"]).set_index("fecha")


def ordering_stat(mean_cars: pd.Series, scales: pd.Series) -> tuple[float, float]:
    """Kendall tau between per-name mean CAR and sensitivity; one-sided p for tau < 0.

    The exact/asymptotic Kendall p treats names as independent draws — it
    ignores the shared-episode dependence, so it is *reported*, while the gate
    runs on :func:`episode_bootstrap_p`.
    """
    aligned = pd.concat([mean_cars.rename("car"), scales.rename("c")], axis=1).dropna()
    if len(aligned) < 3:
        raise ValueError(f"need >= 3 names for an ordering test, got {len(aligned)}")
    tau, p_two = stats.kendalltau(aligned["c"], aligned["car"])
    p_one = p_two / 2 if tau < 0 else 1 - p_two / 2
    return float(tau), float(p_one)


def episode_bootstrap_p(
    car_panel: pd.DataFrame,
    scales: pd.Series,
    *,
    n_draws: int = 10_000,
    rng: np.random.Generator,
) -> float:
    """Episode-resampling p-value for H1 tau < 0: ``P(tau* >= 0)``.

    ``car_panel`` is episodes x names (NaN where a name has no valid CAR).
    Episodes are drawn with replacement; per-name means recompute NaN-aware on
    the *fixed* name universe (eligibility is decided once, on the original
    sample — pre-registered), and resamples where tau is undefined (a name
    loses all its episodes, or all-tied ranks) are dropped from the tally.
    """
    names = [n for n in car_panel.columns if n in scales.index]
    panel = car_panel[names].to_numpy()
    c = scales.reindex(names).to_numpy()
    filled = np.nan_to_num(panel)
    present = ~np.isnan(panel)
    taus: list[float] = []
    for _ in range(n_draws):
        idx = rng.integers(0, len(panel), size=len(panel))
        counts = present[idx].sum(axis=0)
        with np.errstate(invalid="ignore"):
            means = np.where(counts > 0, filled[idx].sum(axis=0) / counts, np.nan)
        ok = counts > 0
        if ok.sum() < 3:
            continue
        tau, _ = stats.kendalltau(c[ok], means[ok])
        if not np.isnan(tau):
            taus.append(tau)
    if not taus:
        return float("nan")
    return float((np.asarray(taus) >= 0).mean())
