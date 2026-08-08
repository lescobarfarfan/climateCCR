"""Cross-run results-distribution figures — the OQ-GEN-02 (b) comparison layer.

Reads STORED artifacts only (no engine re-runs): each configured run's
``ee_pe_climate_shift.csv`` comparison frame, summarized through
``viz.epe_summary``, plus the NGFS readout CSV. Emits:

- ``epe_delta_matrix`` — the INT-30/31 scenario x lambda-band book-EPE table
  as an annotated matrix (transition-only / combined / jump-within);
- ``epe_shift_distribution_<group>`` — per-counterparty EPE-shift strips per
  labelled run (BOOK as a diamond), one figure per config group.

Deterministic; the manifest records the config (GEN-06). Idempotent, rerun
with ``--forzar``. ``--root`` points data/results at another checkout.

    python pipelines/19_results_distribution_figures.py [--config CFG] [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "results_distributions.yaml"


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
    logger = get_logger("climateCCR.results_distributions", log_dir=config.paths.logs)
    extra = config.extra

    out_dir = config.paths.results / "figures" / str(extra["run_name"])
    if (out_dir / "epe_delta_matrix.png").exists() and not args.forzar:
        logger.info("Figures exist, nothing to do (rerun with --forzar): %s", out_dir)
        return

    viz.apply_style()
    written: list[Path] = []

    readout_csv = config.paths.root / str(extra["readout_csv"])
    if readout_csv.exists():
        written.extend(
            viz.save_figure(
                viz.plot_epe_delta_matrix(pd.read_csv(readout_csv)),
                out_dir / "epe_delta_matrix",
            )
        )
    else:
        logger.warning("NGFS readout missing, matrix skipped: %s", readout_csv)

    for group, runs in dict(extra["groups"]).items():
        summaries: dict[str, pd.DataFrame] = {}
        for label, run_dir in runs.items():
            frame_csv = config.paths.results / str(run_dir) / "ee_pe_climate_shift.csv"
            if not frame_csv.exists():
                sys.exit(f"Missing comparison frame for '{label}': {frame_csv}")
            summary = viz.epe_summary(pd.read_csv(frame_csv))
            book = summary.loc[summary["netting_agreement_id"] == "BOOK", "epe_shift_pct"]
            logger.info("%s / %s: BOOK EPE shift %.2f%%", group, label, float(book.iloc[0]))
            summaries[str(label)] = summary
        written.extend(
            viz.save_figure(
                viz.plot_epe_shift_distribution(summaries),
                out_dir / f"epe_shift_distribution_{group}",
            )
        )

    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)
    logger.info("Wrote %d files to %s; manifest %s", len(written), out_dir, manifest_path)
    print(f"{len(written)} figure files -> {out_dir}\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
