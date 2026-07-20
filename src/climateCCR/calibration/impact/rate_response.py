"""Loss->rate event study around CENAPRED events (OQ-INT-09; DC-XWALK-4 rate leg).

The price leg of the climate jump channel has an estimated scale (INT-17:
``mark = -L / K_eff``); this module estimates its rate-leg analog. Around each
major climate event, the abnormal daily change of a Mexican sovereign yield
pillar is measured against a market model on the matched US Treasury series
(MacKinlay-style event study), and the cumulative abnormal change is regressed
on the event's real loss:

    CAR_i = alpha + beta * L_i,   L_i in billions of MDP (real, deflated)

``beta`` (decimal yield change per bn MDP) is then converted to an equivalent
HW1F *short-rate* jump: a jump ``J`` decaying at the mean reversion ``a`` moves
the T-maturity zero yield by ``J * (1 - exp(-aT)) / (aT)``, so

    J_per_MDP = (beta / 1e3) * aT / (1 - exp(-aT)),   S_rate_eff = 1 / J_per_MDP

and ``LognormalSeverityFit.to_mark_sampler(S_rate_eff, sign=+1.0)`` yields the
``rate_marks`` block with the fitted severity shape transferring exactly.

Events clustered inside a business-day merge window collapse into *episodes*
(hurricane-season arrivals overlap event windows); long-duration events
(droughts) are excluded — they carry no date-localized news. The adoption of
the estimate is gated by a pre-registered criterion pinned in
``configs/loss_to_rate_scale.yaml``, never decided after seeing the numbers.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


def build_episodes(
    events: pd.DataFrame,
    *,
    max_duration_days: float = 30.0,
    merge_window_bd: int = 5,
) -> pd.DataFrame:
    """Collapse dated events into non-overlapping episodes.

    ``events`` comes from :func:`~climateCCR.calibration.impact.load_climate_events`
    (real ``danio_mdp``, day-level ``fecha_inicio``). Events longer than
    ``max_duration_days`` are dropped (count in ``.attrs["n_excluded_duration"]``);
    events starting within ``merge_window_bd`` business days of the episode's
    latest member merge into it. Episode date = first ``fecha_inicio`` (the
    market learns at first impact); loss = sum of member losses.
    """
    frame = events.copy()
    too_long = frame["duracion_dias"].notna() & (frame["duracion_dias"] > max_duration_days)
    frame = frame.loc[~too_long]
    fechas = pd.to_datetime(frame["fecha_inicio"], errors="coerce")
    frame = frame.assign(_fecha=fechas).dropna(subset=["_fecha"]).sort_values("_fecha")

    episodes: list[dict] = []
    last_date: np.datetime64 | None = None
    for _, row in frame.iterrows():
        fecha = row["_fecha"]
        loss = float(row["danio_mdp"]) if pd.notna(row["danio_mdp"]) else 0.0
        gap = (
            np.busday_count(last_date, fecha.to_numpy().astype("datetime64[D]"))
            if last_date is not None
            else None
        )
        if gap is not None and gap <= merge_window_bd:
            episodes[-1]["danio_mdp"] += loss
            episodes[-1]["n_eventos"] += 1
        else:
            episodes.append({"fecha": fecha, "danio_mdp": loss, "n_eventos": 1})
        last_date = fecha.to_numpy().astype("datetime64[D]")
    out = pd.DataFrame(episodes, columns=["fecha", "danio_mdp", "n_eventos"])
    out.attrs["n_excluded_duration"] = int(too_long.sum())
    return out


@dataclass(frozen=True)
class EventStudyResult:
    """One pillar x window cell of the beta(T) table."""

    pillar: str
    window_bd: int
    beta_per_bn: float  # decimal yield change per bn MDP of real loss
    se_hc1: float
    p_one_sided: float  # H1: beta > 0 (adverse events push yields up)
    p_bootstrap: float  # pairs-bootstrap P(beta* <= 0); reported, never gating
    alpha_intercept: float
    n_episodes: int
    t_years: float  # effective pillar maturity, for the HW1F conversion


def _ols_hc1(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    n = len(x)
    design = np.column_stack([np.ones(n), x])
    xtx_inv = np.linalg.inv(design.T @ design)
    coef = xtx_inv @ design.T @ y
    resid = y - design @ coef
    meat = design.T @ (design * resid[:, None] ** 2)
    cov = xtx_inv @ meat @ xtx_inv * (n / (n - 2))
    return float(coef[0]), float(coef[1]), float(np.sqrt(cov[1, 1]))


def _bootstrap_p(x: np.ndarray, y: np.ndarray, n_draws: int, rng: np.random.Generator) -> float:
    idx = rng.integers(0, len(x), size=(n_draws, len(x)))
    xs, ys = x[idx], y[idx]
    xc = xs - xs.mean(axis=1, keepdims=True)
    yc = ys - ys.mean(axis=1, keepdims=True)
    var = (xc**2).sum(axis=1)
    ok = var > 0  # degenerate resamples (a single episode repeated) carry no slope
    slopes = (xc[ok] * yc[ok]).sum(axis=1) / var[ok]
    return float((slopes <= 0).mean()) if len(slopes) else float("nan")


def event_study(
    yields: pd.Series,
    control: pd.Series,
    episodes: pd.DataFrame,
    *,
    pillar: str,
    t_years: float,
    estimation_window_bd: tuple[int, int] = (-120, -10),
    event_window_bd: int = 5,
    min_estimation_obs: int = 60,
    max_missing_frac: float = 0.4,
    n_bootstrap: int = 10_000,
    rng: np.random.Generator | None = None,
) -> EventStudyResult | None:
    """Cross-sectional event study of one yield pillar; ``None`` if under-identified.

    ``yields``/``control`` are daily *levels* in decimal, indexed by date; the
    trading grid is the MX pillar's own calendar (control days reindex onto it,
    NaN where the US market is closed — those days drop from both the market
    model and the CAR sums; an episode x pillar cell with more than
    ``max_missing_frac`` of its window missing is excluded).
    """
    grid = yields.sort_index()
    dy = grid.diff()
    dus = control.sort_index().diff().reindex(dy.index)
    est_lo, est_hi = estimation_window_bd
    cars: list[float] = []
    losses: list[float] = []

    for _, episode in episodes.iterrows():
        day0 = int(np.searchsorted(dy.index.to_numpy(), np.datetime64(episode["fecha"])))
        if day0 + est_lo < 0 or day0 + event_window_bd >= len(dy):
            continue
        est = pd.DataFrame(
            {
                "dy": dy.iloc[day0 + est_lo : day0 + est_hi + 1],
                "dus": dus.iloc[day0 + est_lo : day0 + est_hi + 1],
            }
        ).dropna()
        if len(est) < min_estimation_obs:
            continue
        slope, intercept = np.polyfit(est["dus"], est["dy"], 1)
        window = pd.DataFrame(
            {
                "dy": dy.iloc[day0 : day0 + event_window_bd + 1],
                "dus": dus.iloc[day0 : day0 + event_window_bd + 1],
            }
        ).dropna()
        if len(window) < (1 - max_missing_frac) * (event_window_bd + 1):
            continue
        abnormal = window["dy"] - (intercept + slope * window["dus"])
        cars.append(float(abnormal.sum()))
        losses.append(float(episode["danio_mdp"]) / 1e3)  # bn MDP

    if len(cars) < 3:
        return None
    x, y = np.asarray(losses), np.asarray(cars)
    alpha_hat, beta_hat, se = _ols_hc1(x, y)
    t_stat = beta_hat / se
    return EventStudyResult(
        pillar=pillar,
        window_bd=event_window_bd,
        beta_per_bn=beta_hat,
        se_hc1=se,
        p_one_sided=float(stats.t.sf(t_stat, df=len(x) - 2)),
        p_bootstrap=_bootstrap_p(x, y, n_bootstrap, rng or np.random.default_rng(0)),
        alpha_intercept=alpha_hat,
        n_episodes=len(x),
        t_years=t_years,
    )


def rate_scale_from_beta(
    beta_per_bn: float, t_years: float, hw_alpha: float
) -> tuple[float, float]:
    """(short-rate jump per MDP, ``S_rate_eff``) from a pillar-yield slope.

    Inverts the HW1F yield loading ``B(T) = (1 - exp(-aT)) / (aT)`` (a jump on
    the short rate decays through the mean reversion, so the T-yield moves less
    than the short rate; ``a -> 0`` gives ``B -> 1``). Uses the *engine's* mean
    reversion deliberately: the injected jump then reproduces the observed
    pillar move inside the engine's own dynamics.
    """
    if beta_per_bn <= 0:
        raise ValueError(f"beta_per_bn must be > 0 to define a scale, got {beta_per_bn}")
    if t_years <= 0 or hw_alpha < 0:
        raise ValueError(f"need t_years > 0 and hw_alpha >= 0, got {t_years}, {hw_alpha}")
    at = hw_alpha * t_years
    loading = -np.expm1(-at) / at if at > 0 else 1.0
    j_per_mdp = (beta_per_bn / 1e3) / loading
    return float(j_per_mdp), float(1.0 / j_per_mdp)
