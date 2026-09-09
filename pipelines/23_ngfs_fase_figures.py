"""NGFS fase figure set — the phased application flavor, end to end (OQ-INT-12 c).

Reads STORED artifacts only (no engine runs): the pipelines/22 scenario
fragments (``results/ngfs_scheduled_shocks/<SCEN>.yaml``), the
trajectory-lambda(t) rider configs, and the pipelines/17 readouts of every
application flavor (nivel / trayectoria / fase). Emits, under
``results/figures/<run_name>/``:

- ``scheduled_shock_paths`` — the scenario paths the fase engine consumes:
  policy-rate delta per scenario and equity adjustment per GEM-E3 sector
  (spread deltas per issuer sector once the Phase-2 channel is present);
- ``intensity_paths`` — the lambda(t) riders vs the constant headline lambda,
  with the expected cumulative arrivals (the deferred trajectory-lambda visuals);
- ``flavor_comparison`` — transition-only book-EPE delta per scenario, one
  bar per application flavor;
- ``epe_delta_matrix_<flavor>`` — the scenario x band matrix per flavor;
- ``transition_profiles`` — the per-pillar transition delta per scenario,
  one line per flavor, from the first post-0D pillar (fase 0D rows are
  zero-delta by construction — the INT-33 t=0 pin).

Deterministic; the manifest records the config (GEN-06). Idempotent, rerun
with ``--forzar``. ``--root`` points data/results at another checkout.

    python pipelines/23_ngfs_fase_figures.py [--config CFG] [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "ngfs_fase_figures.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the figures exist"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="project root for data/ and results/ (defaults to auto-discovery)",
    )
    args = parser.parse_args()

    from climateCCR import viz
    from climateCCR.infra import ProjectPaths, RunManifest, get_logger, load_config

    config = load_config(args.config)
    if args.root is not None:
        config.paths = ProjectPaths(root=args.root.resolve())
    config.paths.ensure()
    logger = get_logger("climateCCR.ngfs_fase_figures", log_dir=config.paths.logs)
    extra = config.extra
    root = config.paths.root

    out_dir = config.paths.results / "figures" / str(extra["run_name"])
    if (out_dir / "flavor_comparison.png").exists() and not args.forzar:
        logger.info("Figures exist, nothing to do (rerun with --forzar): %s", out_dir)
        return

    viz.apply_style()
    written: list[Path] = []

    # -- The scheduled paths themselves, straight from the fragments (no engine).
    fragments: dict[str, dict] = {}
    for scenario in extra["scenarios"]:
        path = root / str(extra["fragments_dir"]) / f"{scenario}.yaml"
        if not path.exists():
            sys.exit(f"Missing fragment {path} — run pipelines/22 first")
        fragments[str(scenario)] = yaml.safe_load(path.read_text())["scheduled_shocks"]
    shock = yaml.safe_load((root / str(extra["shock_config"])).read_text())
    groups: dict[str, str] = {}
    for leg in ("equity_leg", "bond_leg"):
        groups.update((shock.get(leg) or {}).get("sectors", {}))
    written += viz.save_figure(
        viz.plot_scheduled_shock_paths(fragments, groups), out_dir / "scheduled_shock_paths"
    )

    # -- The trajectory-lambda(t) riders vs the constant headline (INT-34).
    riders: dict[str, dict] = {}
    for label, rider_config in dict(extra["riders"]).items():
        intensity = load_config(root / str(rider_config)).extra["climate_jumps"]["intensity"]
        if not isinstance(intensity, dict):
            sys.exit(f"{rider_config}: intensity is not a {{times_years, values}} trajectory")
        riders[str(label)] = intensity
    written += viz.save_figure(
        viz.plot_intensity_paths(
            riders, float(extra["headline_intensity"]), float(extra["horizon_years"])
        ),
        out_dir / "intensity_paths",
    )

    # -- One readout per application flavor: matrices, the flavor comparison,
    #    and the per-pillar profiles (post-0D).
    deltas: dict[str, pd.DataFrame] = {}
    profiles: dict[str, pd.DataFrame] = {}
    for flavor, readout_dir in dict(extra["readouts"]).items():
        readout = root / str(readout_dir)
        summary_csv = readout / "book_epe_deltas.csv"
        if not summary_csv.exists():
            logger.warning("%s readout missing, skipped: %s", flavor, summary_csv)
            continue
        deltas[str(flavor)] = pd.read_csv(summary_csv)
        written += viz.save_figure(
            viz.plot_epe_delta_matrix(
                deltas[str(flavor)], title=f"Book-EPE delta vs base jump-off (%) — {flavor}"
            ),
            out_dir / f"epe_delta_matrix_{flavor}",
        )
        profile_csv = readout / "book_profile_deltas.csv"
        if profile_csv.exists():
            profiles[str(flavor)] = pd.read_csv(profile_csv)
        else:
            logger.warning("%s per-pillar readout missing (rerun 17): %s", flavor, profile_csv)
    if not deltas:
        sys.exit("No readout found — run pipelines/17 for at least one flavor first")
    for flavor, frame in deltas.items():
        for _, row in frame[frame["band"] == "headline"].iterrows():
            logger.info(
                "%s / %s: transition %.2f%%", flavor, row["scenario"], row["transition_pct"]
            )
    written += viz.save_figure(viz.plot_flavor_comparison(deltas), out_dir / "flavor_comparison")
    if profiles:
        written += viz.save_figure(
            viz.plot_transition_profiles(profiles, scenarios=[str(s) for s in extra["scenarios"]]),
            out_dir / "transition_profiles",
        )

    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)
    logger.info("Wrote %d files to %s; manifest %s", len(written), out_dir, manifest_path)
    print(f"{len(written)} figure files -> {out_dir}\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
