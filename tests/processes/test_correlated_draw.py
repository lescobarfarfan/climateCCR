"""The correlated Gaussian draw is canonical (CCR-SIM-02).

One check behind the Cholesky colouring: when two factors are uncorrelated, factor
``i`` must ride standard-normal stream ``i`` no matter how close to degenerate the
diagonal is, and for a generic positive-definite matrix the increments must equal
``Z @ cholesky(C).T`` on the engine's own ``RandomState`` stream.

Why it exists: the 2026-09-24 macOS 27 upgrade changed Apple Accelerate, the
PSD repair of the PIMPA fixture correlation came back with two diagonal entries one
ulp apart, and the SVD-based ``multivariate_normal`` draw re-ordered its singular
vectors — swapping the rate and share streams of the two-factor netting sets and
breaking both golden baselines with no code or package change.
"""

from __future__ import annotations

import numpy as np
from climateCCR.infra import get_legacy_rng
from climateCCR.simulation.correlation_matrix import CorrelationMatrix
from climateCCR.simulation.multi_risk_factor_simulation import MultiRiskFactorSimulation

SEED = 233423
N_PATHS, N_STEPS = 32, 6
DATES = list(range(N_STEPS + 1))  # the draw only uses the number of dates


class _Passthrough:
    """A one-driver model that returns its increments, exposing the raw draw."""

    number_of_risk_drivers = 1
    calibration: dict = {}

    def simulate(self, simulation_dates, random_increments):
        return random_increments[:, :, 0]


class _RF:
    def __init__(self, name: str) -> None:
        self.name = name
        self.model = _Passthrough()


def _draw(names: list[str], matrix: np.ndarray) -> np.ndarray:
    correlation = CorrelationMatrix(correlation_matrix=np.asarray(matrix), underlyings=names)
    engine = MultiRiskFactorSimulation([_RF(n) for n in names], correlation)
    paths = engine.generate_scenarios(DATES, {"n_paths": N_PATHS, "random_state": SEED})
    return np.stack([paths[n] for n in names], axis=-1)


def _standard_normals(dim: int) -> np.ndarray:
    return get_legacy_rng(SEED).standard_normal((N_PATHS, N_STEPS, dim))


def test_uncorrelated_factors_keep_their_own_streams_however_the_diagonal_rounds():
    z = _standard_normals(2)
    for diagonal in ([1 - 2e-16, 1 - 1e-16], [1 - 1e-16, 1 - 2e-16], [1.0, 1.0]):
        increments = _draw(["RATE", "SHARE"], np.diag(diagonal))
        for i, variance in enumerate(diagonal):
            np.testing.assert_allclose(
                increments[..., i], z[..., i] * np.sqrt(variance), rtol=0, atol=1e-15
            )


def test_draw_equals_cholesky_colouring_of_the_legacy_stream():
    matrix = np.array([[1.0, 0.5, 0.2], [0.5, 1.0, 0.3], [0.2, 0.3, 1.0]])
    increments = _draw(["A", "B", "C"], matrix)
    expected = _standard_normals(3) @ np.linalg.cholesky(matrix).T
    np.testing.assert_allclose(increments, expected, rtol=1e-12, atol=0)
    assert increments.shape == (N_PATHS, N_STEPS, 3)
