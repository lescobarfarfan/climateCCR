"""Multi-seed Monte-Carlo precision of the band headline — the GEN-30 tail caveat quantified.

Every reported metric is a statistic of ``n_paths`` simulated paths under one master
seed (233423, the band configs' own). Means (EE / EPE / EEPE) are tight; a 99 %
quantile is an order statistic decided by the ~100 most extreme paths and moved by
~10 % between two equally valid realizations of the same model (GEN-30, 2026-10-03).
This runner re-runs each adopted band config under extra master seeds with ONLY
``seed`` changed (asserted per generated config), reads the canonical realization
from the stored adopted runs, and summarizes the spread across seeds of:

- BOOK EPE (baseline / climate / shift %), the INT-23 headline, and Effective EPE
  (CCR-RISK-08);
- the time-averaged supervisory PFE99 per counterparty and summed (CCR-RISK-03);
- the per-path book-exposure quantile at the configured horizons, both legs and
  the paired delta % (the GEN-34 object, from the ``--trayectorias`` npz artifacts).

Within a seed the jump-OFF and jump-ON legs share the diffusion stream, so the
paired climate deltas are far tighter than the tail *levels* — the distinction the
manuscript draws between reporting a level and reporting a delta. Generated configs
live under results/ (unversioned; this runner is their deterministic reconstructor,
GEN-04) and every simulated seed writes its own pipelines/01 manifest.

    python pipelines/24_seed_sensitivity.py [--config ...] [--forzar] [--ejecutar-bandas]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "seed_sensitivity.yaml"
BAND_PREFIX = "climate_jump_real_mexican"
PFE_COLUMN = "uncollateralized_pfe_0.99"
KEYS = ["band", "metric", "netting_agreement_id"]
INTERVAL_COLUMNS = [
    "n_seeds",
    "canonical_value",
    "mean",
    "sd",
    "rel_sd",
    "min",
    "max",
    "q025",
    "q975",
]


def band_label(stem: str) -> str:
    """``climate_jump_real_mexican_floor`` -> ``floor``; the bare headline stem -> ``headline``."""
    return stem.removeprefix(BAND_PREFIX).strip("_") or "headline"


def write_seed_config(adopted: Path, seed: int, out_dir: Path) -> Path:
    """``<stem>__seed<seed>.yaml``: the adopted config with only ``seed`` changed (asserted)."""
    base = yaml.safe_load(adopted.read_text())
    want = base | {"seed": int(seed)}
    text = yaml.safe_dump(want, sort_keys=False, allow_unicode=True)
    if yaml.safe_load(text) != want:
        raise ValueError(f"{adopted.name}: generated config differs beyond `seed`")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{adopted.stem}__seed{int(seed)}.yaml"
    path.write_text(text)
    return path


def run_metrics(run_dir: Path, horizons_years: Sequence[float], quantile: float) -> pd.DataFrame:
    """Long ``metric, netting_agreement_id, value`` table for one pipelines/01 run.

    EPE / EEPE / time-averaged supervisory PFE99 per counterparty + ``BOOK`` from the
    comparison frame (DC-CCR-RISK-3); ``book_q<q>_<h>y_{baseline,climate,shift_pct}``
    at ``BOOK`` from the per-path artifacts (DC-CCR-RISK-5, the pipelines/20 recipe).
    """
    from climateCCR.risk.ccr.evaluators.artifacts import (
        book_exposure,
        horizon_index,
        read_per_path_values,
    )
    from climateCCR.viz.ccr import effective_epe_summary, epe_summary, with_supervisory_pfe

    frame = pd.read_csv(run_dir / "ee_pe_climate_shift.csv")
    tables = [
        epe_summary(frame),
        effective_epe_summary(frame),
        epe_summary(with_supervisory_pfe(frame), metric=PFE_COLUMN).rename(
            columns=lambda c: c.replace("epe_", "pfe99_")
        ),
    ]
    long = pd.concat(
        [
            t.melt(id_vars="netting_agreement_id", var_name="metric", value_name="value")
            for t in tables
        ]
    )
    legs = {
        leg: book_exposure(read_per_path_values(run_dir / f"per_path_values_{leg}.npz"))
        for leg in ("baseline", "climate")
    }
    q = int(round(100 * quantile))
    rows = []
    for years in horizons_years:
        pos = horizon_index(legs["baseline"][0], float(years))
        base, climate = (
            float(np.quantile(legs[leg][1][:, pos], quantile)) for leg in ("baseline", "climate")
        )
        stem = f"book_q{q}_{float(years):g}y"
        rows += [
            (f"{stem}_baseline", base),
            (f"{stem}_climate", climate),
            (f"{stem}_shift_pct", 100.0 * (climate - base) / base),
        ]
    tail = pd.DataFrame(rows, columns=["metric", "value"]).assign(netting_agreement_id="BOOK")
    return pd.concat([long, tail], ignore_index=True)[["metric", "netting_agreement_id", "value"]]


def seed_intervals(metrics: pd.DataFrame) -> pd.DataFrame:
    """Spread across seeds per ``(band, metric, netting_agreement_id)``.

    ``sd`` is the sample standard deviation (ddof 1) of the statistic across
    realizations — the Monte-Carlo uncertainty of a single ``n_paths`` estimate;
    ``rel_sd`` = sd / |mean|. With ~10 seeds ``q025`` / ``q975`` sit near min / max.
    Exactly one canonical row per key is required (its value is reported alongside).
    """
    if metrics.groupby(KEYS)["canonical"].sum().ne(1).any():
        raise ValueError(
            "every (band, metric, netting_agreement_id) needs exactly one canonical row"
        )
    out = metrics.groupby(KEYS)["value"].agg(
        n_seeds="count",
        mean="mean",
        sd="std",
        min="min",
        max="max",
        q025=lambda v: v.quantile(0.025),
        q975=lambda v: v.quantile(0.975),
    )
    out["canonical_value"] = metrics.loc[metrics["canonical"]].set_index(KEYS)["value"]
    out["rel_sd"] = out["sd"] / out["mean"].abs()
    return out.reset_index()[KEYS + INTERVAL_COLUMNS]


def plot_seed_spread(metrics: pd.DataFrame, quantile: float, years: float, out_stem: Path):
    """Two rows x one column per band: tail levels per seed, then paired deltas vs EPE shift."""
    import matplotlib.pyplot as plt
    from climateCCR.viz.style import (
        COLOR_BASELINE,
        COLOR_CLIMATE,
        TEXT_SECONDARY,
        apply_style,
        save_figure,
    )

    apply_style()
    q = int(round(100 * quantile))
    stem = f"book_q{q}_{float(years):g}y"
    book = metrics[metrics["netting_agreement_id"] == "BOOK"]
    wide = book.pivot_table(index=["band", "seed"], columns="metric", values="value")
    bands = list(dict.fromkeys(book["band"]))
    fig, axes = plt.subplots(2, len(bands), figsize=(3.4 * len(bands), 6.4), squeeze=False)
    for j, band in enumerate(bands):
        rows = wide.loc[band]
        canonical = int(book.loc[(book["band"] == band) & book["canonical"], "seed"].iloc[0])
        rows = rows.loc[[canonical] + sorted(s for s in rows.index if s != canonical)]
        x = np.arange(len(rows))
        top, bottom = axes[0, j], axes[1, j]
        top.plot(x, rows[f"{stem}_baseline"] / 1e6, "o", color=COLOR_BASELINE, label="baseline")
        top.plot(x, rows[f"{stem}_climate"] / 1e6, "o", color=COLOR_CLIMATE, label="climate")
        top.plot(0, rows[f"{stem}_baseline"].iloc[0] / 1e6, "o", mfc="none", mec="black", ms=11)
        top.set_title(f"{band}: {years:g}y book-exposure q{q} by seed")
        bottom.axhline(0, color="black", lw=0.6)
        bottom.plot(
            x, rows[f"{stem}_shift_pct"], "o", color=COLOR_CLIMATE, label=f"q{q} paired delta"
        )
        bottom.plot(x, rows["epe_shift_pct"], "s", color=TEXT_SECONDARY, label="BOOK EPE shift")
        bottom.plot(0, rows[f"{stem}_shift_pct"].iloc[0], "o", mfc="none", mec="black", ms=11)
        for ax in (top, bottom):
            ax.set_xticks(x, [str(s) for s in rows.index], rotation=90, fontsize=6)
        if j == 0:
            top.set_ylabel("level (MXN m)")
            bottom.set_ylabel("climate shift (%)")
            top.legend(fontsize=7)
            bottom.legend(fontsize=7)
    fig.suptitle("Monte-Carlo precision across master seeds (ring = canonical seed)")
    paths = save_figure(fig, out_stem)
    plt.close(fig)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    parser.add_argument(
        "--ejecutar-bandas",
        "--run-bands",
        action="store_true",
        help="also simulate every band x extra seed via pipelines/01 --trayectorias",
    )
    args = parser.parse_args()

    from climateCCR.infra import RunManifest, get_logger, load_config

    config = load_config(args.config)
    config.paths.ensure()
    logger = get_logger("climateCCR.seed_sensitivity", log_dir=config.paths.logs)
    extra = config.extra
    out_dir = config.paths.results / "seed_sensitivity"
    intervals_csv = out_dir / "seed_intervals.csv"
    if intervals_csv.exists() and not args.forzar and not args.ejecutar_bandas:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", intervals_csv)
        return

    bands = [str(b) for b in extra["bands"]]
    seeds = [int(s) for s in extra["extra_seeds"]]
    if len(set(seeds)) != len(seeds) or config.seed in seeds:
        sys.exit("extra_seeds must be unique and differ from the canonical seed")
    for band in bands:
        adopted = REPO_ROOT / "configs" / f"{band}.yaml"
        if int(yaml.safe_load(adopted.read_text())["seed"]) != config.seed:
            sys.exit(f"{adopted.name}: seed != {config.seed}; the stored run is not canonical")
    config_dir = out_dir / "configs"
    generated = [
        write_seed_config(REPO_ROOT / "configs" / f"{band}.yaml", seed, config_dir)
        for band in bands
        for seed in seeds
    ]
    logger.info("generated %d seed configs under %s", len(generated), config_dir)

    if args.ejecutar_bandas:
        for cfg in generated:
            logger.info("running %s", cfg.stem)
            cmd = [
                sys.executable,
                str(REPO_ROOT / "pipelines" / "01_climate_jump_demo.py"),
                "--config",
                str(cfg),
                "--data-root",
                "data/ccr_book_mx",
                "--book-config",
                "configs/mexican_book.yaml",
                "--horizonte",
                "largo",
                "--trayectorias",
            ]
            if args.forzar:  # otherwise pipelines/01's own skip makes the batch resumable
                cmd.append("--forzar")
            subprocess.run(cmd, check=True, cwd=REPO_ROOT)

    # --------------------------------------------------------------- collector
    horizons = [float(h) for h in extra["horizons_years"]]
    quantile = float(extra["quantile"])
    frames = []
    for band in bands:
        runs = [(config.seed, band)] + [(seed, f"{band}__seed{seed}") for seed in seeds]
        for seed, stem in runs:
            run_dir = config.paths.results / stem
            canonical = seed == config.seed
            if not (run_dir / "ee_pe_climate_shift.csv").exists():
                if canonical:
                    sys.exit(
                        f"canonical run missing: {run_dir} — pipelines/01 --config configs/"
                        f"{band}.yaml --data-root data/ccr_book_mx --book-config "
                        "configs/mexican_book.yaml --trayectorias"
                    )
                logger.info("%s: seed %d not simulated yet (--ejecutar-bandas)", band, seed)
                continue
            if not all(
                (run_dir / f"per_path_values_{leg}.npz").exists() for leg in ("baseline", "climate")
            ):
                sys.exit(f"{run_dir}: no per-path artifacts — rerun with --trayectorias")
            frames.append(
                run_metrics(run_dir, horizons, quantile).assign(
                    band=band_label(band), seed=int(seed), canonical=canonical
                )
            )
    metrics = pd.concat(frames, ignore_index=True)[
        ["band", "seed", "canonical", "metric", "netting_agreement_id", "value"]
    ]

    # Pairing tripwire: the jump-OFF leg is lambda-independent, so per seed the baseline
    # levels must agree across bands; a mismatch means runs from different stacks (GEN-30/37).
    book = metrics[metrics["netting_agreement_id"] == "BOOK"]
    q = int(round(100 * quantile))
    for metric in ("epe_baseline", f"book_q{q}_{horizons[0]:g}y_baseline"):
        wide = book[book["metric"] == metric].pivot(index="seed", columns="band", values="value")
        wide = wide.dropna()
        if not np.allclose(wide.to_numpy(), wide.iloc[:, [0]].to_numpy(), rtol=0.0, atol=1e-6):
            sys.exit(f"{metric} differs across bands for the same seed:\n{wide}")

    out_dir.mkdir(parents=True, exist_ok=True)
    metrics.round(6).to_csv(out_dir / "seed_metrics.csv", index=False)
    intervals = seed_intervals(metrics)
    intervals.round(6).to_csv(intervals_csv, index=False)
    written = plot_seed_spread(metrics, quantile, horizons[0], out_dir / "seed_sensitivity")

    config.extra["collected"] = {
        band: sorted(int(s) for s in group["seed"].unique())
        for band, group in metrics.groupby("band")
    }
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)
    summary = intervals[intervals["netting_agreement_id"] == "BOOK"].set_index(["metric", "band"])
    print(summary[["n_seeds", "canonical_value", "mean", "sd", "rel_sd"]].round(4).to_string())
    print(f"\nOutputs: {out_dir} ({len(written)} figure files)\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
