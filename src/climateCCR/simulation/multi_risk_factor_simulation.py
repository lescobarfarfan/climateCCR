import numpy as np

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
        nr_risk_drivers = sum(rf.model.number_of_risk_drivers for rf in self.simulated_risk_factors)
        n_paths = simulation_parameters["n_paths"]
        n_steps = len(valuation_dates) - 1

        # Correlated Gaussian increments, path-major (DC-CONV-10). The standard
        # normals come from infra's single seeding entry point (GEN-07) on the legacy
        # RandomState stream of CCR-MIG-08, and are coloured by the Cholesky factor of
        # the correlation matrix (CCR-SIM-02). Cholesky is unique and continuous in the
        # matrix, so no BLAS/OS build can flip the factor <-> stream assignment the way
        # an SVD/eigen ordering tie-break can (the 2026-09-24 macOS/Accelerate incident).
        rng = get_legacy_rng(simulation_parameters["random_state"])
        standard_normals = rng.standard_normal((n_paths, n_steps, nr_risk_drivers))
        cholesky_factor = np.linalg.cholesky(np.asarray(self.correlation_matrix, dtype=float))
        random_increments = standard_normals @ cholesky_factor.T

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
            # for every configured target either way, so two portfolios on the SAME
            # grid see identical event streams. Portfolios on different grids draw
            # different Poisson counts — the reason the book is simulated once on
            # the union grid by default (CCR-SIM-03, `simulate_book`).
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
            # GBM multiplies). A book-wide overlay applies to whatever THIS
            # portfolio simulates — the jump-channel skip (a netting set holds a
            # subset of the book's factors, so the INT-33 per-target fail-loud
            # is unworkable at per-NAID grain; superseded 2026-08-27). An
            # overlay touching NOTHING simulated is still a loud config error.
            simulated = {rf.name: rf for rf in self.simulated_risk_factors}
            present = scheduled_shocks.target_names & set(simulated)
            if not present:
                raise ValueError(
                    "scheduled_shocks: no overlay target is simulated by this portfolio "
                    f"(overlay: {sorted(scheduled_shocks.target_names)}; "
                    f"simulated: {sorted(simulated)})"
                )
            alphas = {}
            for name in scheduled_shocks.rate_targets & present:
                calibration = getattr(simulated[name].model, "calibration", {})
                if "alpha" not in calibration:
                    raise ValueError(
                        f"scheduled_shocks.rate_shocks target {name} has no mean-reversion "
                        "alpha (not an HW1F-style model)"
                    )
                alphas[name] = calibration["alpha"]
            shock_marks = scheduled_shocks.step_marks(valuation_dates, alphas, targets=present)
            for name, marks in shock_marks.items():
                random_paths[name] = simulated[name].model.apply_jump_overlay(
                    random_paths[name],
                    np.broadcast_to(marks, (n_paths, len(marks))),
                    valuation_dates,
                )

        return random_paths


def slice_scenarios(joint, risk_factor_names, valuation_dates):
    """A netting set's view of a book-wide ``generate_scenarios`` dict (CCR-SIM-03).

    Returns the same ``{name: (n_paths, n_dates), name + "_dates": dates}`` layout on
    ``valuation_dates``, every one of which must lie on the joint grid. Only the
    named factors are returned (the pricers tell simulated underlyings from spread
    inputs by name membership). Copies by fancy indexing and consumes no RNG; a
    missing factor or date is a loud error, never a silent re-draw.
    """
    out = {}
    for name in risk_factor_names:
        if name not in joint:
            raise ValueError(f"joint scenarios do not simulate {name}")
        column = {date: i for i, date in enumerate(joint[name + "_dates"])}
        missing = [date for date in valuation_dates if date not in column]
        if missing:
            raise ValueError(
                f"{len(missing)} valuation date(s) of {name} are not on the joint grid "
                f"(first: {missing[0]})"
            )
        out[name] = joint[name][:, [column[date] for date in valuation_dates]]
        out[name + "_dates"] = valuation_dates
    return out
