"""Typed configuration loaded from YAML.

Replaces PIMPA's module-level mutable ``global_parameters`` dict. A run is
described by a single YAML file under ``configs/``; the resolved configuration
is snapshotted into each run manifest for traceability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .paths import ProjectPaths, project_paths


@dataclass
class Config:
    """Resolved configuration for a single run."""

    seed: int = 233423
    n_paths: int = 10_000
    settlement_currency: str = "USD"
    date_format: str = "%Y-%m-%d"
    # Any additional, less-structured settings from the YAML file:
    extra: dict[str, Any] = field(default_factory=dict)
    # Resolved project locations (not serialized verbatim — see ``to_dict``):
    paths: ProjectPaths | None = None

    def to_dict(self) -> dict[str, Any]:
        """A JSON-safe snapshot for the run manifest."""
        out: dict[str, Any] = {
            "seed": self.seed,
            "n_paths": self.n_paths,
            "settlement_currency": self.settlement_currency,
            "date_format": self.date_format,
            "extra": self.extra,
        }
        if self.paths is not None:
            out["project_root"] = str(self.paths.root)
        return out


_KNOWN_FIELDS = ("seed", "n_paths", "settlement_currency", "date_format")


def load_config(path: str | Path | None = None) -> Config:
    """Load a :class:`Config` from a YAML file.

    If ``path`` is ``None``, loads ``configs/default.yaml`` from the project root.
    Unknown keys are preserved under :attr:`Config.extra`.
    """
    paths = project_paths()
    if path is None:
        path = paths.configs / "default.yaml"
    path = Path(path)

    data: dict[str, Any] = {}
    if path.exists():
        data = yaml.safe_load(path.read_text()) or {}

    known = {k: data.pop(k) for k in _KNOWN_FIELDS if k in data}
    return Config(paths=paths, extra=data, **known)
