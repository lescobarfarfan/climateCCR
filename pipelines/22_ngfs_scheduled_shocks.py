"""Emit per-scenario NGFS scheduled_shocks fragments — the fase producer (OQ-INT-12 a).

For each scenario in the shared shock config: read the tidy NGFS ST paths and
emit a YAML fragment carrying the INT-33 ``scheduled_shocks`` block that
``pipelines/01 --choques-programados`` injects into the simulation — the
"fase" (phased-application) state of the NGFS world, vs the t=0 "nivel"
overlays of pipelines/16:

- **rate channel** — the quarterly EIRIN policy-rate delta path (scenario −
  Baseline, pp -> decimal) on ``curve_name``. The sovereign long anchor is
  NOT carried: in the single-factor HW1F world an in-simulation r(t) overlay
  propagates to the whole future curve through B(t,T)/alpha, so a separate
  long anchor cannot be imposed at future dates (INT-33 manuscript note).
- **equity channel** — the annual CLIMACRED ``equity_relative_adjustment``
  sector paths (% vs BAU -> cumulative ``log(1 + pct/100)``) mapped to the
  book names through the shock config's ``equity_leg.sectors`` crosswalk;
  interpolation happens in log space, matching how the engine interpolates
  the ``log_factors`` it is handed.

Conventions (INT-33 + the 2026-08-27 rulings): **raw published deltas** — the
fragment's t=0 point carries the scenario delta already accumulated at the
valuation date (the engine pins the overlay to 0 at t=0, so the first
simulation step applies that value as the catch-up and the path is tracked
thereafter); the producer owns the **calendar bridge** (NGFS decimal years ->
calendar dates, nearest-day quantization <= 12 h -> Act/365 year-fractions
from the valuation date — the engine's own axis); points at or beyond
``window[1] + 1.0`` (decimal 2031.0) are dropped and the engine's np.interp
clamp holds the last value (the MKT-NGFS-09 clip). The credit-spread leg is
valuation-side and deliberately absent (OQ-INT-12 b, Phase 2).

Fragments are deterministic (provenance carries the source sha256s, no
timestamps — byte-identical re-runs, GEN-30 discipline) and validated through
``ScheduledShockOverlay.from_config`` before writing. Idempotent (GEN-05):
existing fragments are skipped, rerun with ``--forzar``. A ``resumen.csv``
and a run manifest land beside them.

    python pipelines/22_ngfs_scheduled_shocks.py [--forzar] \\
        [--config configs/ngfs_scheduled.yaml]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PRODUCER_CONFIG = REPO_ROOT / "configs" / "ngfs_scheduled.yaml"


def _decimal_year(date_str: str) -> float:
    """Calendar date -> decimal year on the NGFS time axis (as pipelines/16). [eng]"""
    ts = pd.Timestamp(date_str)
    return ts.year + (ts.dayofyear - 1) / 365.0


def decimal_year_to_date(t: float) -> pd.Timestamp:
    """Inverse of ``_decimal_year``, quantized to the nearest day (<= 12 h off). [eng]"""
    year = int(np.floor(t))
    day_of_year = int(round((t - year) * 365.0)) + 1
    return pd.Timestamp(year, 1, 1) + pd.Timedelta(days=day_of_year - 1)


def act365_from(valuation: pd.Timestamp, ngfs_times) -> list[float]:
    """NGFS decimal-year points -> Act/365 year-fractions from the valuation date.

    Routes through calendar dates so the fragment axis is byte-consistent with
    the engine's ``transform_dates_to_time_differences`` ((d - t0).days / 365)
    at those dates, leap days included — the exact calendar bridge of INT-33.
    """
    return [
        (decimal_year_to_date(t) - valuation).days / 365.0
        for t in np.asarray(ngfs_times, dtype=float)
    ]


def scheduled_path(
    times_pub, values_pub, valuation_date: str, window: tuple[float, float]
) -> tuple[list[float], list[float]]:
    """Raw-based fragment path: ``[0.0]`` + published points in (t0, hi + 1.0).

    The value at the valuation date is interpolated from the published path
    and carried at t=0 (raw basing, user ruling 2026-08-27): the engine pins
    the overlay to 0 there and the first step applies it as the catch-up;
    later points keep their published values on the Act/365 axis.
    """
    times_pub = np.asarray(times_pub, dtype=float)
    values_pub = np.asarray(values_pub, dtype=float)
    t0 = _decimal_year(valuation_date)
    if not times_pub.min() <= t0 <= times_pub.max():
        raise ValueError(
            f"valuation date {valuation_date} (decimal {t0:.3f}) is outside the "
            f"published path [{times_pub.min():.2f}, {times_pub.max():.2f}]"
        )
    at_t0 = float(np.interp(t0, times_pub, values_pub))
    keep = (times_pub > t0) & (times_pub < window[1] + 1.0)  # the _signed_peak window rule
    times = [0.0] + act365_from(pd.Timestamp(valuation_date), times_pub[keep])
    return times, [at_t0] + [float(v) for v in values_pub[keep]]


def equity_paths(
    frame: pd.DataFrame, scenario: str, leg: dict, valuation_date: str, window: tuple[float, float]
) -> dict[str, tuple[list[float], list[float]]]:
    """Per-name cumulative log(1 + pct/100) paths on one shared annual axis."""
    from climateCCR.data.scenarios.ngfs import annual_series

    family = leg["variable_family"]
    shared_times: np.ndarray | None = None
    by_sector: dict[str, tuple[list[float], list[float]]] = {}
    for sector in sorted(set(leg["sectors"].values())):
        series = annual_series(frame, scenario, variable=f"{family}|{sector}")
        times = series["time"].to_numpy(dtype=float)
        if shared_times is None:
            shared_times = times
        elif not np.array_equal(times, shared_times):
            raise ValueError(
                f"{family}|{sector} ({scenario}): time axis differs from the other sectors — "
                "the equity channel needs one shared times_years"
            )
        log_values = np.log1p(series["value"].to_numpy(dtype=float) / 100.0)
        by_sector[sector] = scheduled_path(times, log_values, valuation_date, window)
    return {name: by_sector[sector] for name, sector in leg["sectors"].items()}


def build_fragment(frame: pd.DataFrame, scenario: str, shock: dict, valuation_date: str) -> dict:
    """The INT-33 ``scheduled_shocks`` block for one scenario (rate + equity channels)."""
    from climateCCR.data.scenarios import policy_rate_delta

    window = tuple(shock["window"])
    curve = shock["curve_name"]
    rate = policy_rate_delta(frame, scenario, region=shock["region"])
    rate_times, rate_pp = scheduled_path(
        rate["time"].to_numpy(), rate["delta_pp"].to_numpy(), valuation_date, window
    )
    block: dict = {
        "rate_shocks": {
            "targets": [curve],
            "times_years": rate_times,
            "deltas": {curve: [pp / 100.0 for pp in rate_pp]},
        }
    }
    leg = shock.get("equity_leg")
    if leg:
        by_name = equity_paths(frame, scenario, leg, valuation_date, window)
        names = sorted(by_name)
        block["equity_shocks"] = {
            "targets": names,
            "times_years": by_name[names[0]][0],
            "log_factors": {name: by_name[name][1] for name in names},
        }
    return block


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="rebuild fragments even if they exist"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PRODUCER_CONFIG,
        help="producer config (default: configs/ngfs_scheduled.yaml)",
    )
    args = parser.parse_args()

    from climateCCR.data.scenarios import load_short_term
    from climateCCR.infra import RunManifest, get_logger, load_config
    from climateCCR.processes.scheduled_shocks import ScheduledShockOverlay

    config = load_config(args.config)
    config.paths.ensure()
    logger = get_logger("climateCCR.ngfs_scheduled_shocks", log_dir=config.paths.logs)

    extra = config.extra
    shock = yaml.safe_load((config.paths.root / extra["shock_config"]).read_text())
    valuation_date = extra["valuation_date"]
    ngfs_dir = config.paths.root / extra["ngfs_dir"]
    out_root = config.paths.root / extra["out_root"]

    frame = load_short_term(ngfs_dir)
    procedencia = json.loads((ngfs_dir / "_procedencia.json").read_text())
    archivos_sha256 = {
        name: meta["sha256"] for name, meta in sorted(procedencia.get("archivos", {}).items())
    }

    rows = []
    built = 0
    for scenario in shock["scenarios"]:
        out_path = out_root / f"{scenario}.yaml"
        if out_path.exists() and not args.forzar:
            logger.info("Fragment exists, skipping (rerun with --forzar): %s", out_path)
            continue
        block = build_fragment(frame, scenario, shock, valuation_date)
        ScheduledShockOverlay.from_config(block)  # fail here, not at simulation time
        fragment = {
            "provenance": {
                "producer": "pipelines/22_ngfs_scheduled_shocks.py",
                "scenario": scenario,
                "valuation_date": valuation_date,
                "window": list(shock["window"]),
                "basing": "raw_published_deltas",  # user ruling 2026-08-27
                "fuente": procedencia.get("fuente"),
                "archivos_sha256": archivos_sha256,
            },
            "scheduled_shocks": block,
        }
        out_root.mkdir(parents=True, exist_ok=True)
        out_path.write_text(yaml.safe_dump(fragment, sort_keys=False, width=100))
        built += 1
        for channel in ("rate_shocks", "equity_shocks"):
            ch = block.get(channel)
            if not ch:
                continue
            values = np.asarray(list((ch.get("deltas") or ch["log_factors"]).values()))
            rows.append(
                {
                    "scenario": scenario,
                    "channel": channel,
                    "n_targets": len(ch["targets"]),
                    "n_points": len(ch["times_years"]),
                    "t_last": ch["times_years"][-1],
                    "value_t0_min": float(values[:, 0].min()),
                    "value_t0_max": float(values[:, 0].max()),
                    "value_last_min": float(values[:, -1].min()),
                    "value_last_max": float(values[:, -1].max()),
                }
            )
        logger.info(
            "%s -> %s (%d rate points, %d equity names)",
            scenario,
            out_path,
            len(block["rate_shocks"]["times_years"]),
            len(block.get("equity_shocks", {}).get("targets", [])),
        )

    if built:
        resumen = pd.DataFrame(rows)
        resumen_csv = out_root / "resumen.csv"
        resumen.to_csv(resumen_csv, index=False)
        # Manifest completeness: the resolved shared keys ride the run manifest.
        config.extra["resolved_shock_keys"] = {
            "scenarios": shock["scenarios"],
            "region": shock["region"],
            "window": list(shock["window"]),
            "curve_name": shock["curve_name"],
            "equity_sectors": (shock.get("equity_leg") or {}).get("sectors", {}),
        }
        manifest = RunManifest.create(
            seed=config.seed, config=config, project_root=config.paths.root
        )
        manifest_path = manifest.write(config.paths.manifests)
        logger.info("Wrote %s and manifest %s", resumen_csv, manifest_path)
        print(resumen.to_string(index=False, float_format=lambda v: f"{v:+.6f}"))
    print(f"Fragments -> {out_root} ({built} built)")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
