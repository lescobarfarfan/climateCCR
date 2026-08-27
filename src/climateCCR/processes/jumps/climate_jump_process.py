"""Climate-driven compound-Poisson jump overlay (DC-CCR-SIM-2, INT-10).

One climate event stream per Monte-Carlo path, shared across all shocked risk
factors: each arrival hits every configured target with a mark drawn from that
target's sampler — or, with peril typing on (OQ-INT-11 Phase B), scaled by the
target's sensitivity to the event's shared categorical peril label, so only
susceptible sectors move on a given event. Arrivals are counted per simulation
step (an event inside
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

from .marks import LognormalMark, MarkSampler

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
            A dict ``{"times_years", "values"}`` is the grid-free config form
            of the 1-D trajectory (the OQ-INT-12 lambda(t) rider): at generate
            time the values are interpolated onto the step-start grid
            (``np.interp``, hold-beyond clamp — the scheduled-channel
            path-prevailing convention, INT-33) and ride the 1-D branch.
        targets: Risk-factor name -> mark sampler. Every arrival hits every
            target (shared event times); marks are independent across targets.
        diffusion_dependence: Only ``"independent"`` is implemented — jumps are
            independent of the Brownian drivers (Merton assumption), which keeps
            the jump-on vs baseline readout purely the climate component.
        mark_dependence: Only ``"independent"`` is implemented — per-event marks
            are independent across targets given the shared arrival.
        peril_mix: Optional peril-label distribution ``{group: prob}`` (OQ-INT-11
            Phase B). When given, every event draws one shared categorical peril
            label; targets named in ``target_peril_scales`` take that event's
            mark scaled by their per-peril sensitivity ``c[name][group]`` —
            ``c = 0`` means the sector is not susceptible and the name does not
            move on that event. Probabilities must be positive and sum to 1
            (the trigger-set frequency mix, measurement-consistent with the
            INT-20 ``intensity``). Absent -> Phase A behaviour, bit-identical.
        target_peril_scales: ``{name: {group: c}}`` with exactly the
            ``peril_mix`` groups per name; ``sum_p peril_mix[p] * c[name][p]``
            equals the name's flat ``gamma`` (pipelines/10 identity), so the
            per-name expected impact matches Phase A and peril typing only
            redistributes it across events. Both-or-neither with ``peril_mix``.
        peril_severity: Optional per-label severity ``{group: {median, sigma}}``
            (OQ-INT-11 Phase B'), exactly the ``peril_mix`` groups. Targets
            named in ``target_peril_scales`` (which must carry
            :class:`~climateCCR.processes.jumps.marks.LognormalMark` samplers)
            then draw their base mark from the *event label's* lognormal
            instead of the shared pooled one — same single normal draw per
            (target, event), so the stream is unchanged and parameters equal to
            the pooled ``(median, sigma)`` reproduce Phase B bit-for-bit. The
            calibration mean-matches the labels
            (``fit_peril_severity``: ``E[L_p] = E[L]``), so only the
            conditional shape moves and the per-name expected impact is still
            ``gamma_i`` times the pooled mean. Requires ``peril_mix``.
    """

    def __init__(
        self,
        intensity: float | np.ndarray | dict,
        targets: dict[str, MarkSampler],
        diffusion_dependence: str = "independent",
        mark_dependence: str = "independent",
        peril_mix: dict[str, float] | None = None,
        target_peril_scales: dict[str, dict[str, float]] | None = None,
        peril_severity: dict[str, dict[str, float]] | None = None,
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
        self._intensity_path: tuple[np.ndarray, np.ndarray] | None = None
        if isinstance(intensity, dict):
            if set(intensity) != {"times_years", "values"}:
                raise ValueError(
                    "trajectory intensity must be exactly {'times_years', 'values'}, "
                    f"got {sorted(intensity)}"
                )
            times = np.asarray(intensity["times_years"], dtype=float)
            values = np.asarray(intensity["values"], dtype=float)
            if times.ndim != 1 or times.shape != values.shape or times.size == 0:
                raise ValueError(
                    "trajectory intensity times_years/values must be equal-length, non-empty 1-D"
                )
            if not (np.all(np.isfinite(times)) and np.all(np.isfinite(values))):
                raise ValueError("trajectory intensity times_years/values must be finite")
            if np.any(np.diff(times) <= 0.0):
                raise ValueError("trajectory intensity times_years must be strictly increasing")
            if np.any(values < 0.0):
                raise ValueError("intensity must be non-negative")
            self._intensity_path = (times, values)
        self.intensity = intensity
        self.targets = dict(targets)
        self.diffusion_dependence = diffusion_dependence
        self.mark_dependence = mark_dependence

        if (peril_mix is None) != (target_peril_scales is None):
            raise ValueError("peril_mix and target_peril_scales are both-or-neither")
        self.peril_labels: list[str] | None = None
        self._peril_probs: np.ndarray | None = None
        self._peril_scale_rows: dict[str, np.ndarray] = {}
        if peril_mix is not None:
            # Sorted label order: the draw stream depends on the group set, not on
            # config key order (same stability rule as the sorted-target loop).
            self.peril_labels = sorted(peril_mix)
            probs = np.array([float(peril_mix[g]) for g in self.peril_labels])
            if not np.all(np.isfinite(probs)) or np.any(probs <= 0):
                raise ValueError(f"peril_mix probabilities must be finite and > 0: {peril_mix}")
            if abs(probs.sum() - 1.0) > 1e-6:
                raise ValueError(f"peril_mix must sum to 1, got {probs.sum():.8f}")
            self._peril_probs = probs / probs.sum()
            unknown = sorted(set(target_peril_scales) - set(self.targets))
            if unknown:
                raise ValueError(f"target_peril_scales names unknown targets: {unknown}")
            for name, row in target_peril_scales.items():
                if set(row) != set(self.peril_labels):
                    raise ValueError(
                        f"target_peril_scales[{name!r}] groups {sorted(row)} != "
                        f"peril_mix groups {self.peril_labels}"
                    )
                c = np.array([float(row[g]) for g in self.peril_labels])
                if not np.all(np.isfinite(c)) or np.any(c < 0):
                    raise ValueError(
                        f"target_peril_scales[{name!r}] must be finite and >= 0: {row}"
                    )
                self._peril_scale_rows[name] = c

        self._sev_log_median: np.ndarray | None = None
        self._sev_sigma: np.ndarray | None = None
        if peril_severity is not None:
            if self.peril_labels is None:
                raise ValueError("peril_severity requires peril_mix (labels size the severity)")
            if set(peril_severity) != set(self.peril_labels):
                raise ValueError(
                    f"peril_severity groups {sorted(peril_severity)} != "
                    f"peril_mix groups {self.peril_labels}"
                )
            for name in self._peril_scale_rows:
                if not isinstance(self.targets[name], LognormalMark):
                    raise ValueError(
                        f"peril_severity needs LognormalMark targets, {name!r} has "
                        f"{self.targets[name]!r}"
                    )
            medians = np.array([float(peril_severity[g]["median"]) for g in self.peril_labels])
            sigmas = np.array([float(peril_severity[g]["sigma"]) for g in self.peril_labels])
            if np.any(medians <= 0) or np.any(sigmas < 0):
                raise ValueError(
                    f"peril_severity needs median > 0 and sigma >= 0: {peril_severity}"
                )
            self._sev_log_median = np.log(medians)
            self._sev_sigma = sigmas

    @classmethod
    def from_config(cls, jump_config: dict) -> ClimateJumpProcess:
        """Assemble the process from a ``climate_jumps`` config block.

        Schema: ``configs/climate_jump_demo.yaml`` — an ``intensity`` plus the
        ``rate_marks``/``equity_marks`` channels, each mapping its ``targets``
        to one lognormal mark sampler; present channels share the event stream
        (a config may run one channel only, e.g. the estimated price channel
        while the rate translation stays open — OQ-INT-07). ``intensity`` is
        the scalar events/year, or the trajectory dict
        ``{times_years, values}`` (Act/365 years from the run's valuation
        date; the OQ-INT-12 lambda(t) rider — see ``__init__``).

        A channel may carry an optional ``target_scales: {name: gamma}`` mapping
        (OQ-INT-11 Phase A, derived by ``pipelines/10_equity_mark_scales.py``):
        each named target's median is rescaled to ``median * gamma`` with
        ``sigma``/``sign`` unchanged, so its marks are exactly ``gamma *`` the
        uniform marks under the same seed (same draw count per target, stream
        untouched). Unnamed targets keep ``gamma = 1``.

        Alternatively a channel may carry ``peril_mix: {group: prob}`` together
        with ``target_peril_scales: {name: {group: c}}`` (OQ-INT-11 Phase B,
        same pipeline): every event then draws a shared peril label from
        ``peril_mix`` and a named target's mark on a ``p``-event is the base
        draw times ``c[name][p]`` (``c = 0`` -> the name does not move). The
        two forms are mutually exclusive per channel — ``c`` already embeds the
        flat ``gamma`` (``sum_p mix[p] * c[name][p] = gamma``) — and only one
        channel may declare peril typing (the label is a property of the event,
        not of a channel). Unnamed targets take every event with the base
        sampler. Absent blocks == uniform behaviour, bit-identical stream.

        The peril-typed channel may additionally carry ``peril_severity:
        {group: {median, sigma}}`` (mean-matched per-label severity from
        ``fit_peril_severity``, pipelines/10): peril-scaled targets then draw
        their base mark from the event label's lognormal — same draw stream,
        and pooled parameters in every label reproduce the block-absent marks
        bit-for-bit.
        """
        targets: dict[str, MarkSampler] = {}
        peril_mix: dict[str, float] | None = None
        target_peril_scales: dict[str, dict[str, float]] | None = None
        peril_severity: dict[str, dict[str, float]] | None = None
        for channel in ("rate_marks", "equity_marks"):
            block = jump_config.get(channel)
            if block is None:
                continue
            sampler = LognormalMark(
                median=block["median"], sigma=block["sigma"], sign=block["sign"]
            )
            scales = block.get("target_scales") or {}
            mix = block.get("peril_mix")
            peril_scales = block.get("target_peril_scales")
            if (mix is None) != (peril_scales is None):
                raise ValueError(
                    f"{channel}: peril_mix and target_peril_scales are both-or-neither"
                )
            if block.get("peril_severity") is not None and mix is None:
                raise ValueError(f"{channel}: peril_severity requires peril_mix")
            if mix is not None:
                if scales:
                    raise ValueError(
                        f"{channel}: target_scales and target_peril_scales are mutually "
                        "exclusive (the per-peril scales already embed gamma)"
                    )
                if peril_mix is not None:
                    raise ValueError(
                        "only one channel may declare peril_mix (event labels are shared)"
                    )
                unknown = sorted(set(peril_scales) - set(block["targets"]))
                if unknown:
                    raise ValueError(
                        f"{channel}.target_peril_scales names unknown targets {unknown} "
                        f"(not in {channel}.targets)"
                    )
                peril_mix = dict(mix)
                target_peril_scales = {k: dict(v) for k, v in peril_scales.items()}
                severity = block.get("peril_severity")
                if severity is not None:
                    peril_severity = {
                        g: {"median": float(v["median"]), "sigma": float(v["sigma"])}
                        for g, v in severity.items()
                    }
            unknown = sorted(set(scales) - set(block["targets"]))
            if unknown:
                raise ValueError(
                    f"{channel}.target_scales names unknown targets {unknown} "
                    f"(not in {channel}.targets)"
                )
            for name in block["targets"]:
                gamma = float(scales.get(name, 1.0))
                targets[name] = (
                    sampler
                    if gamma == 1.0
                    else LognormalMark(
                        median=block["median"] * gamma,
                        sigma=block["sigma"],
                        sign=block["sign"],
                    )
                )
        if not targets:
            raise ValueError("climate_jumps needs at least one of rate_marks/equity_marks")
        return cls(
            jump_config["intensity"],
            targets,
            peril_mix=peril_mix,
            target_peril_scales=target_peril_scales,
            peril_severity=peril_severity,
        )

    def _step_intensities(
        self, n_paths: int, step_sizes: np.ndarray, step_start_times: np.ndarray | None = None
    ) -> np.ndarray:
        """Expected events per (path, step): ``lambda_i * dt_i``, broadcast checked.

        With a config-form trajectory (``{"times_years", "values"}``), the path
        is interpolated at the step START times — the lambda prevailing over
        ``[t_i, t_{i+1})`` — and rides the 1-D branch below.
        """
        n_steps = len(step_sizes)
        if self._intensity_path is not None:
            if step_start_times is None:
                raise ValueError("trajectory intensity requires step_start_times")
            intensity = np.interp(step_start_times, *self._intensity_path)
        else:
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

        event_counts = rng.poisson(
            lam=self._step_intensities(n_paths, step_sizes, simulation_times[:-1])
        )
        total_events = int(event_counts.sum())

        # One shared peril label per event (Phase B): drawn once, before the
        # per-target mark loop, so every target sees the same event typology.
        # Skipped entirely when peril typing is off — the Phase A stream is
        # bit-identical (golden baselines, CCR-MIG-03).
        labels: np.ndarray | None = None
        if self._peril_probs is not None:
            labels = rng.choice(len(self._peril_probs), size=total_events, p=self._peril_probs)

        step_marks: dict[str, np.ndarray] = {}
        # Sorted-name order keeps the draw sequence independent of dict insertion
        # order, so a fixture's mark stream is stable across configurations.
        flat_counts = event_counts.ravel()
        cell_index = np.repeat(np.arange(flat_counts.size), flat_counts)
        for name in sorted(self.targets):
            if self._sev_sigma is not None and name in self._peril_scale_rows:
                # Per-label severity (Phase B'): same one normal draw per
                # (target, event) as LognormalMark.sample, with the (median,
                # sigma) selected by the event's label — pooled parameters in
                # every label reproduce the pooled marks bit-for-bit.
                z = rng.standard_normal(total_events)
                marks = self.targets[name].sign * np.exp(
                    self._sev_log_median[labels] + self._sev_sigma[labels] * z
                )
            else:
                marks = self.targets[name].sample(rng, total_events)
            if labels is not None and name in self._peril_scale_rows:
                marks = marks * self._peril_scale_rows[name][labels]
            flat_sum = np.zeros(flat_counts.size)
            np.add.at(flat_sum, cell_index, marks)
            step_marks[name] = flat_sum.reshape(event_counts.shape)
        return ClimateJumpScenario(event_counts=event_counts, step_marks=step_marks)
