"""Run manifests.

Each experiment writes a manifest capturing everything needed to reproduce it:
the resolved config, the git commit (and whether the tree was dirty), the seed,
package versions, the Python/OS platform and the BLAS backend numpy runs on, and
timestamps. This is the backbone of the project's reproducibility contract —
every figure or table in the thesis should be traceable to one manifest.

The platform and BLAS fields are the ``GEN-30`` tripwire: byte-identity claims
hold within one numerics stack, and an OS update can replace the system BLAS
underneath an otherwise unchanged environment (macOS 27 / Accelerate, 2026-09-24).
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any

# Packages whose versions are worth pinning into the manifest.
_TRACKED_PACKAGES = ("numpy", "pandas", "scipy", "matplotlib", "pyyaml")


def _git_commit(root: Path | None = None) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root) if root else None,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _git_dirty(root: Path | None = None) -> bool | None:
    """True when tracked files differ from HEAD (untracked files are ignored)."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=str(root) if root else None,
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in _TRACKED_PACKAGES:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def _blas_backend() -> str | None:
    """Name the BLAS/LAPACK implementation behind numpy's linear algebra.

    PyPI wheels report their bundled or system library directly (``openblas``,
    ``accelerate``). conda-forge builds link the generic netlib interface and
    report ``blas``; there the implementation is the ``libblas`` variant recorded
    in the environment's ``conda-meta`` (e.g. ``9_h51639a9_openblas``).
    """
    try:
        import numpy as np

        build_deps = np.show_config(mode="dicts").get("Build Dependencies", {})
        name = build_deps.get("blas", {}).get("name")
    except Exception:  # show_config is best-effort diagnostics, never a run blocker
        return None
    if name in (None, "blas", "lapack"):
        for meta_file in Path(sys.prefix).glob("conda-meta/libblas-*.json"):
            try:
                build = json.loads(meta_file.read_text()).get("build", "")
            except (OSError, ValueError):
                continue
            if build:
                return f"libblas {build}"
    return name


@dataclass
class RunManifest:
    """A reproducibility record for a single run."""

    run_id: str
    created_at: str
    seed: int
    config: dict[str, Any]
    git_commit: str | None
    python_version: str
    platform: str
    packages: dict[str, str | None] = field(default_factory=dict)
    git_dirty: bool | None = None
    env_prefix: str | None = None
    blas: str | None = None

    @classmethod
    def create(
        cls,
        seed: int,
        config: dict[str, Any] | Any,
        project_root: Path | None = None,
    ) -> RunManifest:
        """Build a manifest from a seed and a config (dict or ``Config``)."""
        if hasattr(config, "to_dict"):
            config = config.to_dict()
        now = datetime.now(UTC)
        run_id = f"{now:%Y%m%dT%H%M%SZ}_{uuid.uuid4().hex[:8]}"
        return cls(
            run_id=run_id,
            created_at=now.isoformat(),
            seed=seed,
            config=config,
            git_commit=_git_commit(project_root),
            python_version=sys.version.split()[0],
            platform=platform.platform(),
            packages=_package_versions(),
            git_dirty=_git_dirty(project_root),
            env_prefix=sys.prefix,
            blas=_blas_backend(),
        )

    def write(self, manifests_dir: str | Path) -> Path:
        """Write the manifest as JSON and return its path."""
        manifests_dir = Path(manifests_dir)
        manifests_dir.mkdir(parents=True, exist_ok=True)
        out_path = manifests_dir / f"{self.run_id}.json"
        out_path.write_text(json.dumps(asdict(self), indent=2, sort_keys=True))
        return out_path
