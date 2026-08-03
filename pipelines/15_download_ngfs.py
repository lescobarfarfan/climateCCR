"""Download NGFS short-term scenario data from the IIASA Scenario Explorer.

Pulls the EIRIN policy-rate paths and the CLIMACRED Mexican sovereign
adjustments named in ``configs/ngfs_short_term.yaml`` (guest token, no
credentials — the pyam flow [Huppmann2021] replayed with requests) and lands
them AS PUBLISHED as tidy CSVs under ``data/scenarios_mx/ngfs_short_term/``
with a ``_procedencia.json`` (GEN-02: application, run ids + versions, sha256).
Idempotent per output file (GEN-05): existing files are skipped, rerun with
``--forzar``.

    python pipelines/15_download_ngfs.py [--forzar]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
NGFS_CONFIG = REPO_ROOT / "configs" / "ngfs_short_term.yaml"

TIDY_COLUMNS = ["model", "scenario", "region", "variable", "unit", "year", "subannual", "value"]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _get_json(url: str, token: str | None = None, timeout: int = 60):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_application_base_url(auth_url: str, application: str, token: str) -> str:
    """Resolve the per-application REST base URL from the IIASA manager."""
    config = _get_json(f"{auth_url}/legacy/applications/{application}/config", token)
    return next(e["value"] for e in config if e["path"] == "baseUrl")


def fetch_runs(base_url: str, token: str) -> pd.DataFrame:
    """The application's run index: one row per (model, scenario) default run."""
    runs = _get_json(f"{base_url}/runs?getOnlyDefaultRuns=true&includeMetadata=false", token)
    return pd.DataFrame(runs)[["run_id", "model", "scenario", "version"]]


def fetch_timeseries(
    base_url: str, token: str, run_ids: list[int], variables: list[str], regions: list[str]
) -> pd.DataFrame:
    """Bulk timeseries for the given runs, tidied to TIDY_COLUMNS."""
    payload = {
        "filters": {
            "runs": run_ids,
            "variables": variables,
            "regions": regions,
            "years": [],
            "units": [],
            "timeslices": [],
        }
    }
    response = requests.post(
        f"{base_url}/runs/bulk/ts",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=300,
    )
    response.raise_for_status()
    frame = pd.DataFrame(response.json())
    if frame.empty:
        raise RuntimeError(f"Empty result for runs={run_ids} variables={variables}")
    return frame[TIDY_COLUMNS].sort_values(TIDY_COLUMNS[:7]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="re-download even if the output exists"
    )
    args = parser.parse_args()

    from climateCCR.infra import get_logger, load_config

    config = load_config(NGFS_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.download_ngfs", log_dir=config.paths.logs)

    out_dir = config.paths.root / config.extra["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    auth_url = config.extra["auth_url"]
    application = config.extra["application"]

    outputs = {p["model"]: out_dir / f"{p['model'].lower()}.csv" for p in config.extra["pulls"]}
    if all(p.exists() for p in outputs.values()) and not args.forzar:
        logger.info("Outputs exist, nothing to do (rerun with --forzar): %s", sorted(outputs))
        return

    token = _get_json(f"{auth_url}/legacy/anonym/")
    base_url = fetch_application_base_url(auth_url, application, token)
    runs = fetch_runs(base_url, token)
    logger.info("Application %s -> %s (%d runs)", application, base_url, len(runs))

    pulled_runs: dict[str, dict[str, list[int]]] = {}
    for pull in config.extra["pulls"]:
        model, out = pull["model"], outputs[pull["model"]]
        if out.exists() and not args.forzar:
            logger.info("Exists, skipping (rerun with --forzar): %s", out.name)
            continue
        index = runs[runs["model"] == model].set_index("scenario")
        missing = sorted(set(pull["scenarios"]) - set(index.index))
        if missing:
            raise RuntimeError(f"Scenarios not in the {model} run index: {missing}")
        run_ids = [int(index.loc[s, "run_id"]) for s in pull["scenarios"]]
        frame = fetch_timeseries(base_url, token, run_ids, pull["variables"], pull["regions"])
        frame.to_csv(out, index=False)
        pulled_runs[model] = {
            s: [int(index.loc[s, "run_id"]), int(index.loc[s, "version"])]
            for s in pull["scenarios"]
        }
        logger.info(
            "%s: %d rows, scenarios %s, %d variables",
            out.name,
            len(frame),
            sorted(frame["scenario"].unique()),
            frame["variable"].nunique(),
        )

    if pulled_runs:
        files = {
            p.name: {"sha256": _sha256(p), "bytes": p.stat().st_size}
            for p in sorted(out_dir.glob("*.csv"))
        }
        provenance = {
            "descargado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "fuente": "NGFS Short-term Climate Scenarios (May 2025, V1.0), IIASA Scenario Explorer",
            "aplicacion": application,
            "url_base": base_url,
            "runs": pulled_runs,  # run_id + version per (model, scenario): the vintage pin
            "archivos": files,
            "nota": "valores como los publica la base (Policy rate en %, ajustes en pp vs BAU)",
        }
        (out_dir / "_procedencia.json").write_text(json.dumps(provenance, indent=2, sort_keys=True))
        logger.info("Provenance written for %d file(s)", len(pulled_runs))
    print(f"NGFS short-term data -> {out_dir}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
