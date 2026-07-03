"""Jump-mark samplers — the per-event impact distributions (DC-CCR-SIM-2).

A *mark* is the size of the shock a climate event applies to its target process:
an additive short-rate move for HW1F (decimal units, e.g. +0.0050 = +50 bp) or a
log-return move for GBM (e.g. -0.05 ≈ a 4.9% price drop). Samplers are injected
into :class:`~climateCCR.processes.jumps.climate_jump_process.ClimateJumpProcess`,
so the HAZ-calibrated impact distribution (OQ-INT-07, DC-XWALK-4) can replace the
placeholder families below without any engine change.

Sign convention: the sampler carries the sign. Adverse means *negative* log-return
marks for prices and (typically) *positive* rate marks.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class MarkSampler(ABC):
    """Draws i.i.d. jump marks; one draw per climate event."""

    @abstractmethod
    def sample(self, rng: np.random.Generator, n: int) -> np.ndarray:
        """Return ``n`` marks drawn with ``rng``.

        Implementations must consume randomness only through ``rng`` (GEN-07) so a
        run is fully determined by the master seed.
        """

    @abstractmethod
    def __repr__(self) -> str: ...


class DeterministicMark(MarkSampler):
    """Every event carries the same fixed mark.

    Not a model — scaffolding for the regression fixture (GEN-04/11): with random
    arrival times but a fixed, documented impact, the jump-on vs jump-off shift in
    EE/PE is fully auditable. It is also the degenerate case of every other family.
    """

    def __init__(self, size: float) -> None:
        self.size = float(size)

    def sample(self, rng: np.random.Generator, n: int) -> np.ndarray:
        return np.full(n, self.size)

    def __repr__(self) -> str:
        return f"DeterministicMark(size={self.size})"


class GaussianMark(MarkSampler):
    """Merton-style Gaussian marks, ``N(mean, std**2)`` [ContTankov2004].

    Symmetric — suited to rate targets, where post-event moves can take either sign.
    """

    def __init__(self, mean: float, std: float) -> None:
        if std < 0:
            raise ValueError(f"std must be >= 0, got {std}")
        self.mean = float(mean)
        self.std = float(std)

    def sample(self, rng: np.random.Generator, n: int) -> np.ndarray:
        return rng.normal(loc=self.mean, scale=self.std, size=n)

    def __repr__(self) -> str:
        return f"GaussianMark(mean={self.mean}, std={self.std})"


class LognormalMark(MarkSampler):
    """One-sided lognormal marks: ``sign * exp(ln(median) + sigma * Z)``.

    The adverse family: every event moves the target in one direction, with
    heavy-tailed severity — the classical shape of catastrophe losses and the
    family a HAZ loss-severity calibration is most likely to land in
    (compound-Poisson actuarial tradition). ``median`` is the median absolute
    mark (more interpretable than the lognormal ``mu``); ``sign=-1`` for price
    targets (value drops), ``+1`` for rate targets (yields rise).
    """

    def __init__(self, median: float, sigma: float, sign: float = -1.0) -> None:
        if median <= 0:
            raise ValueError(f"median must be > 0, got {median}")
        if sigma < 0:
            raise ValueError(f"sigma must be >= 0, got {sigma}")
        if sign not in (-1.0, 1.0):
            raise ValueError(f"sign must be -1.0 or +1.0, got {sign}")
        self.median = float(median)
        self.sigma = float(sigma)
        self.sign = float(sign)

    def sample(self, rng: np.random.Generator, n: int) -> np.ndarray:
        return self.sign * np.exp(np.log(self.median) + self.sigma * rng.standard_normal(n))

    def __repr__(self) -> str:
        return f"LognormalMark(median={self.median}, sigma={self.sigma}, sign={self.sign})"
