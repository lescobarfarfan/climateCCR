"""Reproducibility helpers.

Every stochastic operation in the project should obtain its randomness from
here, so that a single integer seed fully determines a run. ``set_seed`` seeds
the legacy global generators (needed by libraries such as SciPy that accept an
integer ``random_state``, e.g. PIMPA's ``multivariate_normal``) *and* returns a
modern :class:`numpy.random.Generator` for new code to use explicitly.
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
    """Return an independent generator without touching global state."""
    return np.random.default_rng(seed)
