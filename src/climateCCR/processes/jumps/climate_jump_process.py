"""Climate-driven compound-Poisson jump overlay (DC-CCR-SIM-2, INT-10).

One climate event stream per Monte-Carlo path, shared across all shocked risk
factors: each arrival hits every configured target with a mark drawn from that
target's sampler. Arrivals are counted per simulation step (an event inside
``(t_{i}, t_{i+1}]`` lands on the grid date ``t_{i+1}``, the engine's discrete
resolution), so the overlay is a per-step *total mark* array that each diffusion
superimposes on its own dynamics via
:meth:`~climateCCR.processes.diffusions.risk_factor_evolution.RiskFactorEvolution.apply_jump_overlay`.

Provisional configuration vs interface (OQ-INT-03, resolved provisionally
2026-07-02): the interface accepts a constant intensity, a deterministic
trajectory ``lambda(t)`` (per-step array, the INT-12 "trajectory" flavor), or
pre-simulated per-path Cox intensity paths — the first shipped configuration
runs a homogeneous Poisson. Jump<->diffusion dependence and cross-target mark
dependence exist as constructor knobs but only ``"independent"`` is implemented;
richer transmission channels are desirable to-dos pending real-data calibration.

Randomness: a substream derived from the run's master seed
(:func:`climateCCR.infra.get_stream_rng`), so switching the overlay on leaves the
diffusion draws bit-for-bit unchanged and jump-on minus jump-off isolates the
climate component (INT-09, GEN-07). Marks are drawn for every configured target
in sorted-name order regardless of which factors a given portfolio simulates, so
the stream is stable across portfolios. [ContTankov2004]
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from climateCCR.infra import get_stream_rng
from climateCCR.utils.calendar_utils import transform_dates_to_time_differences

from .marks import MarkSampler

# Fixed spawn key for the climate-jump substream of the master seed. Never reuse
# for another component (each new consumer of get_stream_rng gets its own key).
CLIMATE_JUMP_STREAM = 1


@dataclass
class ClimateJumpScenario:
    """Realized climate shocks for one Monte-Carlo run.

    ``event_counts``: events per (path, step), shape ``(n_paths, n_steps)``.
    ``step_marks``: per target name, the summed marks landing at each step, same
    shape; consumed by ``RiskFactorEvolution.apply_jump_overlay``.
    """

    event_counts: np.ndarray
    step_marks: dict[str, np.ndarray]


class ClimateJumpProcess:
    """Compound-Poisson climate shock generator with shared event times.

    Args:
        intensity: Arrival intensity in events per year (Act/365 grid time).
            A scalar is a homogeneous Poisson; a 1-D array of length
            ``n_steps`` is a deterministic trajectory ``lambda(t)``; a 2-D
            ``(n_paths, n_steps)`` array is a pre-simulated Cox intensity.
        targets: Risk-factor name -> mark sampler. Every arrival hits every
            target (shared event times); marks are independent across targets.
        diffusion_dependence: Only ``"independent"`` is implemented — jumps are
            independent of the Brownian drivers (Merton assumption), which keeps
            the jump-on vs baseline readout purely the climate component.
        mark_dependence: Only ``"independent"`` is implemented — per-event marks
            are independent across targets given the shared arrival.
    """

    def __init__(
        self,
        intensity: float | np.ndarray,
        targets: dict[str, MarkSampler],
        diffusion_dependence: str = "independent",
        mark_dependence: str = "independent",
    ) -> None:
        if not targets:
            raise ValueError("targets must map at least one risk-factor name to a MarkSampler")
        if diffusion_dependence != "independent":
            raise NotImplementedError(
                f"diffusion_dependence={diffusion_dependence!r}: only 'independent' is "
                "implemented (OQ-INT-03 provisional; correlated transmission is a "
                "desirable to-do pending real-data calibration)"
            )
        if mark_dependence != "independent":
            raise NotImplementedError(
                f"mark_dependence={mark_dependence!r}: only 'independent' is implemented "
                "(cross-target mark dependence is a desirable to-do, OQ-INT-03)"
            )
        self.intensity = intensity
        self.targets = dict(targets)
        self.diffusion_dependence = diffusion_dependence
        self.mark_dependence = mark_dependence

    def _step_intensities(self, n_paths: int, step_sizes: np.ndarray) -> np.ndarray:
        """Expected events per (path, step): ``lambda_i * dt_i``, broadcast checked."""
        n_steps = len(step_sizes)
        intensity = np.asarray(self.intensity, dtype=float)
        if np.any(intensity < 0):
            raise ValueError("intensity must be non-negative")
        if intensity.ndim == 0:
            per_step = np.broadcast_to(intensity * step_sizes, (n_paths, n_steps))
        elif intensity.ndim == 1:
            if intensity.shape[0] != n_steps:
                raise ValueError(
                    f"trajectory intensity has length {intensity.shape[0]}, "
                    f"expected n_steps={n_steps}"
                )
            per_step = np.broadcast_to(intensity * step_sizes, (n_paths, n_steps))
        elif intensity.ndim == 2:
            if intensity.shape != (n_paths, n_steps):
                raise ValueError(
                    f"per-path intensity has shape {intensity.shape}, "
                    f"expected (n_paths, n_steps)=({n_paths}, {n_steps})"
                )
            per_step = intensity * step_sizes
        else:
            raise ValueError(f"intensity must be scalar, 1-D, or 2-D; got ndim={intensity.ndim}")
        return per_step

    def generate(self, valuation_dates, n_paths: int, master_seed: int) -> ClimateJumpScenario:
        """Draw shared event counts and per-target summed marks for all paths.

        ``valuation_dates`` is the simulation grid (the same argument
        ``generate_scenarios`` receives); marks for events in ``(t_i, t_{i+1}]``
        land at ``t_{i+1}``, i.e. step column ``i``.
        """
        simulation_times = transform_dates_to_time_differences(valuation_dates[0], valuation_dates)
        step_sizes = np.diff(simulation_times)
        rng = get_stream_rng(master_seed, CLIMATE_JUMP_STREAM)

        event_counts = rng.poisson(lam=self._step_intensities(n_paths, step_sizes))
        total_events = int(event_counts.sum())

        step_marks: dict[str, np.ndarray] = {}
        # Sorted-name order keeps the draw sequence independent of dict insertion
        # order, so a fixture's mark stream is stable across configurations.
        flat_counts = event_counts.ravel()
        cell_index = np.repeat(np.arange(flat_counts.size), flat_counts)
        for name in sorted(self.targets):
            marks = self.targets[name].sample(rng, total_events)
            flat_sum = np.zeros(flat_counts.size)
            np.add.at(flat_sum, cell_index, marks)
            step_marks[name] = flat_sum.reshape(event_counts.shape)
        return ClimateJumpScenario(event_counts=event_counts, step_marks=step_marks)
