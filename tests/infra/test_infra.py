"""Tests for the infra layer.

These establish the project's testing habit from day one: the reproducibility
guarantees (seeding) are pinned by a test, so any regression is caught.
"""

from __future__ import annotations

import numpy as np

from climateCCR.infra import (
    Config,
    RunManifest,
    find_project_root,
    get_rng,
    load_config,
    set_seed,
)


def test_set_seed_is_reproducible():
    rng_a = set_seed(123)
    a = rng_a.standard_normal(5)
    rng_b = set_seed(123)
    b = rng_b.standard_normal(5)
    np.testing.assert_array_equal(a, b)


def test_different_seeds_differ():
    a = set_seed(1).standard_normal(5)
    b = set_seed(2).standard_normal(5)
    assert not np.array_equal(a, b)


def test_get_rng_does_not_touch_global_state():
    set_seed(7)
    global_first = np.random.standard_normal(1)
    set_seed(7)
    _ = get_rng(999).standard_normal(1)  # independent generator
    global_second = np.random.standard_normal(1)
    np.testing.assert_array_equal(global_first, global_second)


def test_load_config_defaults():
    cfg = load_config()
    assert isinstance(cfg, Config)
    assert cfg.seed == 233423
    assert cfg.paths is not None


def test_find_project_root_locates_pyproject():
    root = find_project_root()
    assert (root / "pyproject.toml").exists()


def test_manifest_roundtrip(tmp_path):
    cfg = load_config()
    manifest = RunManifest.create(seed=cfg.seed, config=cfg)
    out = manifest.write(tmp_path)
    assert out.exists()
    assert manifest.seed == cfg.seed
    assert "numpy" in manifest.packages
