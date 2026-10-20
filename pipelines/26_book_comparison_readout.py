"""Two-book climate-impact comparison readout — INT-39 (the control book vs the climate book).

Per lambda band x book, from the stored DC-CCR-RISK-3 comparison frames:

- BOOK EPE baseline / climate / shift % (``viz.epe_summary``; each run against its
  own jump-off baseline — the INT-23 convention);
- the rate-channel-only shift (the ``*_solo_tasas`` run: same seed and book, equity
  channel removed) = the component common to both books, and the equity (sector)
  component as the residual ``shift - rate_only`` — a residual, not an additive
  decomposition (the max(V, 0) exposure kink couples the channels);
- ``sum_w_gamma``: 1 for the anchor (Mexican) book by construction, ``anchor.csv``
  for the comparison book, whose equity sensitivities sit on the Mexican absolute
  scale (pipelines/10 --config configs/equity_mark_scales_comparison.yaml);
- the Monte-Carlo sd of the BOOK shift across master seeds from each book's seed
  study (pipelines/24; NaN until that study has run).

Then, per band, the first-minus-second book difference in pp with the UNPAIRED
yardstick ``sqrt(sd_a^2 + sd_b^2)`` (the two books draw different paths under one
seed) and ``z = delta / yardstick`` — the Monte-Carlo floor under the heterogeneity
statement; parameter and S-tier uncertainty sit on top of it.

Guard: every equity of a book (its ``RFE_GBM_Calibration.csv``) must appear in the
band config's ``equity_marks.targets`` — targets a book does not simulate are
skipped silently by the engine, so a book run on the other book's jump config would
report a rate-only shift as if it were the full channel.

Deterministic; idempotent (rerun with ``--forzar``). Outputs under
``results/<out_dir>/``: ``book_epe_shift_comparison.csv`` (band x book rows),
``book_epe_shift_delta.csv`` (per-band differences), ``book_comparison`` (figure).

    python pipelines/26_book_comparison_readout.py [--config CFG] [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "book_comparison.yaml"
ROW_COLUMNS = [
    "band",
    "band_label",
    "book",
    "book_label",
    "run",
    "epe_baseline",
    "epe_climate",
    "epe_shift_pct",
    "rate_only_shift_pct",
    "equity_component_pp",
    "sum_w_gamma",
    "mc_sd_pp",
    "n_seeds",
]


def equity_targets(jump_config: Path) -> set[str]:
    """Equity-channel targets of a jump config (empty for a rate-only config)."""
    marks = (
        yaml.safe_load(jump_config.read_text(encoding="utf-8"))["climate_jumps"].get("equity_marks")
        or {}
    )
    return {str(name) for name in marks.get("targets", [])}


def book_equities(data_root: Path) -> set[str]:
    """Simulated equity risk factors of a book root (``*_SHARE`` rows of its GBM calibration)."""
    frame = pd.read_csv(data_root / "calibration_data" / "RFE_models" / "RFE_GBM_Calibration.csv")
    names = frame.iloc[:, 0].astype(str)
    return {name for name in names if name.endswith("_SHARE")}


def book_row(run_dir: Path, epe_summary) -> pd.Series:
    """The BOOK row of ``viz.epe_summary`` for one pipelines/01 run directory."""
    frame = pd.read_csv(run_dir / "ee_pe_climate_shift.csv")
    summary = epe_summary(frame)
    if "netting_agreement_id" in summary.columns:
        rows = summary[summary["netting_agreement_id"].astype(str) == "BOOK"]
    else:
        rows = summary[summary.index.astype(str) == "BOOK"]
    if len(rows) != 1:
        raise ValueError(f"{run_dir}: expected one BOOK row, found {len(rows)}")
    return rows.iloc[0]


def mc_sd(seed_intervals_csv: Path, band: str) -> tuple[float, int]:
    """(sd, n_seeds) of the BOOK ``epe_shift_pct`` across master seeds; (NaN, 0) if absent."""
    if not seed_intervals_csv.exists():
        return float("nan"), 0
    table = pd.read_csv(seed_intervals_csv)
    row = table[
        (table["band"].astype(str) == band)
        & (table["metric"] == "epe_shift_pct")
        & (table["netting_agreement_id"].astype(str) == "BOOK")
    ]
    if row.empty:
        return float("nan"), 0
    return float(row["sd"].iloc[0]), int(row["n_seeds"].iloc[0])


def band_deltas(table: pd.DataFrame, first: str, second: str) -> pd.DataFrame:
    """Per-band ``first - second`` BOOK shift differences with the unpaired MC yardstick."""
    rows = []
    for band, group in table.groupby("band", sort=False):
        a = group[group["book"] == first].iloc[0]
        b = group[group["book"] == second].iloc[0]
        yardstick = float(np.sqrt(a["mc_sd_pp"] ** 2 + b["mc_sd_pp"] ** 2))
        delta = float(a["epe_shift_pct"] - b["epe_shift_pct"])
        rows.append(
            {
                "band": band,
                "band_label": a["band_label"],
                "first": first,
                "second": second,
                "shift_first_pct": float(a["epe_shift_pct"]),
                "shift_second_pct": float(b["epe_shift_pct"]),
                "delta_pp": delta,
                "equity_component_delta_pp": float(
                    a["equity_component_pp"] - b["equity_component_pp"]
                ),
                "sum_w_gamma_first": float(a["sum_w_gamma"]),
                "sum_w_gamma_second": float(b["sum_w_gamma"]),
                "mc_yardstick_pp": yardstick,
                "z": delta / yardstick if yardstick > 0 else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def plot_book_comparison(table: pd.DataFrame, books: dict[str, str]):
    """Grouped bars of the BOOK EPE shift per band and book, rate-only component marked."""
    from climateCCR.viz.style import COLOR_BASELINE, COLOR_CLIMATE, TEXT_SECONDARY
    from matplotlib import pyplot as plt

    bands = list(dict.fromkeys(table["band"]))
    keys = list(books)
    colors = {keys[0]: COLOR_CLIMATE, keys[1]: COLOR_BASELINE}
    width = 0.36
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    x = np.arange(len(bands))
    for i, key in enumerate(keys):
        sub = table[table["book"] == key].set_index("band").reindex(bands)
        offset = (i - 0.5) * width
        ax.bar(
            x + offset,
            sub["epe_shift_pct"],
            width,
            color=colors[key],
            alpha=0.85,
            label=books[key],
            yerr=2.0 * sub["mc_sd_pp"].fillna(0.0),
            capsize=2,
            error_kw={"linewidth": 0.8, "color": TEXT_SECONDARY},
        )
        ax.plot(
            x + offset,
            sub["rate_only_shift_pct"],
            linestyle="none",
            marker="_",
            markersize=14,
            markeredgewidth=1.6,
            color=TEXT_SECONDARY,
            label="rate channel only" if i == 0 else None,
            zorder=4,
        )
        pairs = zip(sub["epe_shift_pct"], sub["sum_w_gamma"], strict=False)
        for xi, (shift, swg) in enumerate(pairs):
            ax.annotate(
                f"{shift:+.2f} %\nΣwγ {swg:.2f}",
                (xi + offset, shift),
                textcoords="offset points",
                xytext=(0, -14 if shift < 0 else 4),
                ha="center",
                va="top" if shift < 0 else "bottom",
                fontsize=7,
                color=TEXT_SECONDARY,
            )
    ax.axhline(0.0, color=TEXT_SECONDARY, linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(table.drop_duplicates("band")["band_label"].tolist(), fontsize=8)
    ax.set_ylabel("BOOK EPE shift, climate vs baseline (%)")
    ax.set_title("Climate book vs control book — physical jump band (±2 MC sd)")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    args = parser.parse_args()

    from climateCCR import viz
    from climateCCR.infra import RunManifest, get_logger, load_config

    config = load_config(args.config)
    config.paths.ensure()
    logger = get_logger("climateCCR.book_comparison", log_dir=config.paths.logs)
    extra = config.extra
    root = config.paths.root
    out_dir = config.paths.results / str(extra.get("out_dir", "book_comparison"))
    out_csv = out_dir / "book_epe_shift_comparison.csv"
    if out_csv.exists() and not args.forzar:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", out_csv)
        return

    bands = {str(k): str(v) for k, v in extra["bands"].items()}
    books = extra["books"]
    if len(books) != 2:
        sys.exit(f"book_comparison.yaml must name exactly two books, got {list(books)}")

    rows = []
    for book_key, book in books.items():
        equities = book_equities(root / book["data_root"])
        anchor_csv = book.get("anchor_csv")
        sum_w_gamma = (
            1.0 if not anchor_csv else float(pd.read_csv(root / anchor_csv)["sum_w_gamma"].iloc[0])
        )
        rate_dir = config.paths.results / str(book["rate_only_run"])
        if (rate_dir / "ee_pe_climate_shift.csv").exists():
            rate_only = float(book_row(rate_dir, viz.epe_summary)["epe_shift_pct"])
        else:
            logger.warning("%s: rate-only run missing (%s)", book_key, rate_dir)
            rate_only = float("nan")
        for band_key, band_label in bands.items():
            run = str(book["runs"][band_key])
            targets = equity_targets(root / "configs" / f"{run}.yaml")
            missing = sorted(equities - targets)
            if missing:
                sys.exit(
                    f"{run}: book equities absent from equity_marks.targets {missing} — "
                    "the silent no-jump trap (INT-39); fix the jump config"
                )
            row = book_row(config.paths.results / run, viz.epe_summary)
            sd, n_seeds = mc_sd(root / book["seed_intervals"], band_key)
            shift = float(row["epe_shift_pct"])
            rows.append(
                {
                    "band": band_key,
                    "band_label": band_label,
                    "book": book_key,
                    "book_label": str(book["label"]),
                    "run": run,
                    "epe_baseline": float(row["epe_baseline"]),
                    "epe_climate": float(row["epe_climate"]),
                    "epe_shift_pct": shift,
                    "rate_only_shift_pct": rate_only,
                    "equity_component_pp": shift - rate_only,
                    "sum_w_gamma": sum_w_gamma,
                    "mc_sd_pp": sd,
                    "n_seeds": n_seeds,
                }
            )
            logger.info(
                "%s | %s: BOOK EPE shift %+.3f %% (rate-only %+.3f, equity component %+.3f pp; "
                "sum w*gamma %.3f; MC sd %.3f pp over %d seeds)",
                book_key,
                band_key,
                shift,
                rate_only,
                shift - rate_only,
                sum_w_gamma,
                sd,
                n_seeds,
            )
    table = pd.DataFrame(rows)[ROW_COLUMNS]
    first, second = list(books)
    deltas = band_deltas(table, first, second)
    for _, d in deltas.iterrows():
        logger.info(
            "%s: %s - %s = %+.3f pp (equity component %+.3f pp) | MC yardstick %.3f pp, z = %.1f",
            d["band"],
            first,
            second,
            d["delta_pp"],
            d["equity_component_delta_pp"],
            d["mc_yardstick_pp"],
            d["z"],
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    table.round(6).to_csv(out_csv, index=False)
    deltas.round(6).to_csv(out_dir / "book_epe_shift_delta.csv", index=False)
    viz.apply_style()
    fig = plot_book_comparison(table, {k: str(v["label"]) for k, v in books.items()})
    written = viz.save_figure(fig, out_dir / "book_comparison")
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=root)
    manifest_path = manifest.write(config.paths.manifests)
    print(table.round(3).to_string(index=False))
    print()
    print(deltas.round(3).to_string(index=False))
    print(f"\nTable:    {out_csv}\nFigures:  {', '.join(str(p) for p in written)}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
