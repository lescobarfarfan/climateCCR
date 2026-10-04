"""Reproducibility helpers.

Every stochastic operation in the project should obtain its randomness from
here, so that a single integer seed fully determines a run. ``set_seed`` seeds
the legacy global generators (for third-party code that still reads them) *and*
returns a modern :class:`numpy.random.Generator` for new code to use explicitly;
``get_legacy_rng`` hands the CCR engine its MT19937 ``RandomState`` stream
(CCR-MIG-08) and ``get_stream_rng`` derives independent substreams (the climate
jump overlay, DC-CCR-SIM-2).
"""

from __future__ import annotations

import os
import random

import numpy as np

DEFAULT_SEED = 233423  # inherited from PIMPA's global_parameters['random_state']


def set_seed(seed: int = DEFAULT_SEED) -> np.random.Generator:
    """Seed Python, NumPy (legacy global), and ``PYTHONHASHSEED``.

    Returns a fresh :class:`numpy.random.Generator` seeded with the same value.
    Prefer the returned generator in new code; the legacy global seeding exists
    only for third-party libraries that still read it.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    return np.random.default_rng(seed)


def get_rng(seed: int | None = None) -> np.random.Generator:
    """Return an independent modern generator without touching global state."""
    return np.random.default_rng(seed)


def get_stream_rng(seed: int, stream: int) -> np.random.Generator:
    """Derive an independent, reproducible substream from a master seed.

    Distinct ``stream`` keys yield statistically independent generators from the
    same master ``seed`` (NumPy ``SeedSequence`` spawning). This lets an optional
    stochastic component (e.g. the climate jump overlay, ``DC-CCR-SIM-2``) draw
    from the run's single seed *without consuming or shifting* another
    component's stream: with the jump overlay on, the diffusion increments stay
    bit-for-bit identical, so jump-on minus jump-off isolates the climate
    component exactly (GEN-07, INT-09).
    """
    return np.random.default_rng(np.random.SeedSequence(entropy=seed, spawn_key=(stream,)))


def get_legacy_rng(seed: int | None = None) -> np.random.RandomState:
    """Return an independent legacy ``RandomState`` without touching global state.

    The single seeding entry point for the CCR engine's correlated draw
    (``simulation.MultiRiskFactorSimulation``): ``RandomState(seed)`` is the MT19937
    stream PIMPA's integer ``random_state`` always produced, so the standard
    normals behind the locked EE/PE baselines are preserved bit-for-bit while the
    seed stays under ``infra`` control (``GEN-07``, ``CCR-MIG-08``). Prefer
    :func:`get_rng` in new code; this exists for that legacy consumer only.
    """
    return np.random.RandomState(seed)
