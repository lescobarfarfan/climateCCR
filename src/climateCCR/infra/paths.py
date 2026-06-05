"""Central path resolution.

Anchors every path to the repository root rather than the current working
directory. This is what removes the fragility of PIMPA's CWD-relative
``GLOBAL_DATA_PATH = 'data/'``: regardless of where a script or notebook runs
from, paths resolve consistently.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    """Walk upwards from ``start`` until a repo marker is found.

    Markers, in priority order: a ``pyproject.toml`` or a ``.git`` directory.
    Falls back to ``start`` if no marker is found (e.g. an installed wheel).
    """
    start = (start or Path.cwd()).resolve()
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").exists() or (candidate / ".git").exists():
            return candidate
    return start


@dataclass(frozen=True)
class ProjectPaths:
    """Resolved, read-only locations for the project's standard folders."""

    root: Path

    @property
    def src(self) -> Path:
        return self.root / "src"

    @property
    def configs(self) -> Path:
        return self.root / "configs"

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def data_raw(self) -> Path:
        return self.data / "raw"

    @property
    def data_interim(self) -> Path:
        return self.data / "interim"

    @property
    def data_processed(self) -> Path:
        return self.data / "processed"

    @property
    def results(self) -> Path:
        return self.root / "results"

    @property
    def logs(self) -> Path:
        return self.results / "logs"

    @property
    def manifests(self) -> Path:
        return self.results / "manifests"

    @property
    def notes(self) -> Path:
        return self.root / "notes"

    def ensure(self) -> "ProjectPaths":
        """Create the writable output folders if they do not yet exist."""
        for p in (self.results, self.logs, self.manifests):
            p.mkdir(parents=True, exist_ok=True)
        return self


def project_paths(start: Path | None = None) -> ProjectPaths:
    return ProjectPaths(root=find_project_root(start))
