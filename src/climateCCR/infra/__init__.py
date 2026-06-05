"""Cross-cutting infrastructure: configuration, logging, reproducibility, paths.

Every other ``climateCCR`` module depends on this layer so that seeds, run
manifests, and parameter logging are enforced by construction.
"""

from .config import Config, load_config
from .logging_utils import get_logger
from .manifest import RunManifest
from .paths import ProjectPaths, find_project_root, project_paths
from .reproducibility import DEFAULT_SEED, get_rng, set_seed

__all__ = [
    "Config",
    "load_config",
    "get_logger",
    "RunManifest",
    "ProjectPaths",
    "find_project_root",
    "project_paths",
    "DEFAULT_SEED",
    "get_rng",
    "set_seed",
]
