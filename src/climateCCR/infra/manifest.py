"""Run manifests.

Each experiment writes a manifest capturing everything needed to reproduce it:
the resolved config, the git commit, the seed, package versions, and
timestamps. This is the backbone of the project's reproducibility contract —
every figure or table in the thesis should be traceable to one manifest.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

# Packages whose versions are worth pinning into the manifest.
_TRACKED_PACKAGES = ("numpy", "pandas", "scipy", "scikit-learn", "matplotlib", "pyyaml")


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


def _package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in _TRACKED_PACKAGES:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return versions


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

    @classmethod
    def create(
        cls,
        seed: int,
        config: dict[str, Any] | Any,
        project_root: Path | None = None,
    ) -> "RunManifest":
        """Build a manifest from a seed and a config (dict or ``Config``)."""
        if hasattr(config, "to_dict"):
            config = config.to_dict()
        now = datetime.now(timezone.utc)
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
        )

    def write(self, manifests_dir: str | Path) -> Path:
        """Write the manifest as JSON and return its path."""
        manifests_dir = Path(manifests_dir)
        manifests_dir.mkdir(parents=True, exist_ok=True)
        out_path = manifests_dir / f"{self.run_id}.json"
        out_path.write_text(json.dumps(asdict(self), indent=2, sort_keys=True))
        return out_path
