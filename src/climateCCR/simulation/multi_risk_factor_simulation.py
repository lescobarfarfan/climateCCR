import numpy as np
from scipy.stats import multivariate_normal

from climateCCR.infra import get_legacy_rng


class MultiRiskFactorSimulation:
    def __init__(self, risk_factors, correlation_matrix):
        self.simulated_risk_factors = risk_factors
        self.correlation_matrix = correlation_matrix.get_sub_correlation_matrix(
            [rf.name for rf in risk_factors]
        ).get_correlation_matrix()

    def generate_scenarios(self, valuation_dates, simulation_parameters):
        """Simulate all risk factors; optionally superimpose the climate jump overlay.

        If ``simulation_parameters["climate_jumps"]`` holds a
        :class:`~climateCCR.processes.jumps.ClimateJumpProcess`, its shocks are
        applied to the matching simulated factors after the diffusion step
        (DC-CCR-SIM-2). The jump draw uses its own substream of the master seed,
        so the diffusive component of every path is bit-for-bit identical with
        the overlay on or off (INT-09).

        If ``simulation_parameters["scheduled_shocks"]`` holds a
        :class:`~climateCCR.processes.scheduled_shocks.ScheduledShockOverlay`,
        its deterministic scenario marks are applied through the same overlay
        seam (OQ-INT-12) — identical across paths, consuming no RNG, so every
        stream is unchanged with the block on or off.
        """
        nr_risk_drivers = 0
        for rf in self.simulated_risk_factors:
            nr_risk_drivers += rf.model.number_of_risk_drivers

        # Seed the correlated Gaussian draw through infra's single entry point
        # (GEN-07). A legacy RandomState reproduces SciPy's int-seed stream exactly,
        # so the locked EE/PE baseline is unchanged (OQ-CCR-09 resolved, CCR-MIG-03).
        rng = get_legacy_rng(simulation_parameters["random_state"])
        random_increments = multivariate_normal(
            mean=[0] * nr_risk_drivers,
            cov=self.correlation_matrix,
            seed=rng,
        ).rvs(size=(simulation_parameters["n_paths"], len(valuation_dates) - 1))

        if nr_risk_drivers == 1:
            pass_random_increments = random_increments
            random_increments = np.empty(
                (simulation_parameters["n_paths"], len(valuation_dates) - 1, 1)
            )
            random_increments[:, :, 0] = pass_random_increments

        random_paths = {}
        index_risk_drivers = 0
        for rf in self.simulated_risk_factors:
            random_paths[rf.name] = rf.model.simulate(
                valuation_dates,
                random_increments[
                    :,
                    :,
                    index_risk_drivers : (index_risk_drivers + rf.model.number_of_risk_drivers),
                ],
            )
            random_paths[rf.name + "_dates"] = valuation_dates
            index_risk_drivers += rf.model.number_of_risk_drivers

        climate_jumps = simulation_parameters.get("climate_jumps")
        if climate_jumps is not None:
            jump_scenario = climate_jumps.generate(
                valuation_dates,
                simulation_parameters["n_paths"],
                simulation_parameters["random_state"],
            )
            # Targets a portfolio does not simulate are skipped: marks are drawn
            # for every configured target either way, so the jump stream (and any
            # shared factor's shocks) is identical across portfolios.
            for rf in self.simulated_risk_factors:
                if rf.name in jump_scenario.step_marks:
                    random_paths[rf.name] = rf.model.apply_jump_overlay(
                        random_paths[rf.name],
                        jump_scenario.step_marks[rf.name],
                        valuation_dates,
                    )

        scheduled_shocks = simulation_parameters.get("scheduled_shocks")
        if scheduled_shocks is not None:
            # Deterministic scenario overlay (OQ-INT-12): zero RNG, applied after
            # the jump channel; overlays compose order-independently (HW1F adds,
            # GBM multiplies). Unlike jumps, unsimulated targets are config errors.
            simulated = {rf.name: rf for rf in self.simulated_risk_factors}
            missing = sorted(scheduled_shocks.target_names - set(simulated))
            if missing:
                raise ValueError(
                    f"scheduled_shocks targets not simulated by this portfolio: {missing}"
                )
            alphas = {}
            for name in scheduled_shocks.rate_targets:
                calibration = getattr(simulated[name].model, "calibration", {})
                if "alpha" not in calibration:
                    raise ValueError(
                        f"scheduled_shocks.rate_shocks target {name} has no mean-reversion "
                        "alpha (not an HW1F-style model)"
                    )
                alphas[name] = calibration["alpha"]
            shock_marks = scheduled_shocks.step_marks(valuation_dates, alphas)
            n_paths = simulation_parameters["n_paths"]
            for name, marks in shock_marks.items():
                random_paths[name] = simulated[name].model.apply_jump_overlay(
                    random_paths[name],
                    np.broadcast_to(marks, (n_paths, len(marks))),
                    valuation_dates,
                )

        return random_paths
