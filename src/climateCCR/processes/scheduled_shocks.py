"""Deterministic scheduled scenario shocks applied through the jump-overlay seam.

OQ-INT-12 Phase 1: an NGFS transition path enters the simulation *at its own
dates* instead of as an instantaneous t=0 state. The overlay is deterministic —
every Monte-Carlo path receives identical marks (one scenario trajectory, not
path heterogeneity) and **zero RNG is consumed**, so both the diffusion stream
and the climate-jump Poisson substream are bit-for-bit unchanged whether the
block is present or absent (the INT-14 regression discipline).

Conventions fixed by the OQ-INT-12 design ruling:

- **t=0 stays the observed market.** The overlay is pinned to 0 at the
  valuation date; the path value prevailing at each later grid date applies
  from the first simulation step onward. For every grid date ``t_i >= t_1``
  the overlay equals the scenario path exactly, so a constant path reproduces
  the nivel (t=0 peak) state at every reporting date after 0D — the
  MKT-NGFS-09 flat-reduction invariant one level up.
- **Rate leg:** the (policy-rate) delta path lands on the short-rate factor
  and moves the future curve through the model's own B(t,T)/alpha loading.
  The HW1F overlay decays marks through the mean reversion, so the schedule
  compensates by inverting the recursion — ``m_i = D(t_{i+1}) -
  D(t_i)*exp(-alpha*dt_i)`` — and the overlay *tracks* ``D(t)`` at grid dates.
- **Equity leg:** log factors ``log(1 + adjustment)`` accumulate through the
  GBM multiplicative overlay; step marks are the increments of the pinned
  path.
- Times are Act/365 year-fractions from the valuation date; values before the
  first observation hold its value, values beyond the last are held constant
  (the ``np.interp`` end clamps — the MKT-NGFS-09 hold-beyond-window rule).
  The producer pipeline owns the NGFS calendar-year -> year-fraction bridge;
  this module is calendar-free.

Unlike the jump channel — which draws marks for every configured target so the
event stream is identical across portfolios and silently skips targets a
portfolio does not simulate — a scheduled target that is not simulated is a
config error and fails loudly (there is no stream to keep stable).
"""

from __future__ import annotations

import numpy as np

from climateCCR.utils.calendar_utils import transform_dates_to_time_differences

_CHANNEL_VALUE_KEYS = {"rate_shocks": "deltas", "equity_shocks": "log_factors"}


def _validated_paths(channel: str, block: dict) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Parse one channel block into ``{target: (times_years, values)}``."""
    value_key = _CHANNEL_VALUE_KEYS[channel]
    times = np.asarray(block["times_years"], dtype=float)
    if times.ndim != 1 or len(times) < 1:
        raise ValueError(f"{channel}.times_years must be a non-empty 1-D sequence")
    if not np.all(np.isfinite(times)) or np.any(np.diff(times) <= 0):
        raise ValueError(f"{channel}.times_years must be finite and strictly increasing")
    values = block.get(value_key) or {}
    targets = list(block["targets"])
    unknown = sorted(set(values) - set(targets))
    if unknown:
        raise ValueError(
            f"{channel}.{value_key} names unknown targets {unknown} (not in {channel}.targets)"
        )
    missing = sorted(set(targets) - set(values))
    if missing:
        raise ValueError(f"{channel}.{value_key} missing paths for targets {missing}")
    paths: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for name in targets:
        series = np.asarray(values[name], dtype=float)
        if series.shape != times.shape:
            raise ValueError(
                f"{channel}.{value_key}[{name}] has {series.shape[0] if series.ndim == 1 else '?'}"
                f" values for {len(times)} times"
            )
        if not np.all(np.isfinite(series)):
            raise ValueError(f"{channel}.{value_key}[{name}] has non-finite values")
        paths[name] = (times, series)
    return paths


class ScheduledShockOverlay:
    """Deterministic per-date scenario shocks for simulated risk factors.

    Built from a ``scheduled_shocks`` config block (see :meth:`from_config`).
    ``step_marks`` interpolates each target's path onto the simulation grid and
    returns per-target 1-D mark rows for
    :meth:`~climateCCR.processes.diffusions.risk_factor_evolution.RiskFactorEvolution.apply_jump_overlay`;
    the engine broadcasts them across paths (DC-CCR-SIM-2 extension).
    """

    def __init__(
        self,
        rate_paths: dict[str, tuple[np.ndarray, np.ndarray]] | None = None,
        equity_paths: dict[str, tuple[np.ndarray, np.ndarray]] | None = None,
    ) -> None:
        self.rate_paths = dict(rate_paths or {})
        self.equity_paths = dict(equity_paths or {})
        if not self.rate_paths and not self.equity_paths:
            raise ValueError("scheduled_shocks needs at least one of rate_shocks/equity_shocks")
        shared = sorted(set(self.rate_paths) & set(self.equity_paths))
        if shared:
            raise ValueError(f"targets cannot be in both channels: {shared}")

    @classmethod
    def from_config(cls, block: dict) -> ScheduledShockOverlay:
        """Assemble from a ``scheduled_shocks`` config block.

        Schema (units mirror the ``climate_jumps`` channels — decimal rate
        deltas, equity log factors; one shared time axis per channel)::

            scheduled_shocks:
              rate_shocks:
                targets: [MXN_ZERO_YIELD_CURVE]
                times_years: [0.0, 0.45, ...]
                deltas: {MXN_ZERO_YIELD_CURVE: [0.0, 0.0111, ...]}
              equity_shocks:
                targets: [WALMEX_SHARE]
                times_years: [0.0, 1.0, ...]
                log_factors: {WALMEX_SHARE: [0.0, -0.021, ...]}
        """
        parsed = {
            channel: _validated_paths(channel, block[channel])
            for channel in _CHANNEL_VALUE_KEYS
            if block.get(channel) is not None
        }
        return cls(
            rate_paths=parsed.get("rate_shocks"),
            equity_paths=parsed.get("equity_shocks"),
        )

    @property
    def rate_targets(self) -> frozenset[str]:
        return frozenset(self.rate_paths)

    @property
    def target_names(self) -> frozenset[str]:
        return frozenset(self.rate_paths) | frozenset(self.equity_paths)

    def step_marks(
        self, valuation_dates, alphas: dict[str, float], targets: set[str] | None = None
    ) -> dict[str, np.ndarray]:
        """Per-target 1-D step marks on the simulation grid; consumes no RNG.

        Args:
            valuation_dates: the simulation grid (datetime list, as handed to
                ``generate_scenarios``).
            alphas: mean-reversion speed per rate target (the engine's own
                calibration — one source of truth; required for every rate
                target computed, so the decay compensation matches the overlay
                it feeds).
            targets: optional subset of ``target_names`` to compute. The
                simulation passes each portfolio's simulated factors, so a
                book-wide overlay applies to whatever a netting set actually
                holds (alphas then needed only for the rate targets in the
                subset). ``None`` computes every configured target.

        Returns:
            ``{target: (n_steps,) marks}`` — step ``i`` lands on date ``i+1``.
        """
        times = np.asarray(transform_dates_to_time_differences(valuation_dates[0], valuation_dates))
        step_sizes = np.diff(times)
        marks: dict[str, np.ndarray] = {}
        for name, (path_times, values) in self.equity_paths.items():
            if targets is not None and name not in targets:
                continue
            target = np.interp(times, path_times, values)
            target[0] = 0.0  # t=0 stays the observed market
            marks[name] = np.diff(target)
        for name, (path_times, values) in self.rate_paths.items():
            if targets is not None and name not in targets:
                continue
            if name not in alphas:
                raise ValueError(
                    f"scheduled_shocks.rate_shocks target {name} needs the model's "
                    "mean-reversion alpha for decay compensation"
                )
            target = np.interp(times, path_times, values)
            target[0] = 0.0
            marks[name] = target[1:] - target[:-1] * np.exp(-alphas[name] * step_sizes)
        return marks
