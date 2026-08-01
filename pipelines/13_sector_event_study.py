"""Sector event study around cyclone episodes — OQ-INT-11 Phase C validation.

Tests the INT-24/25 mark ordering against realized equity returns: per-name
market-model CARs (daily log AdjClose vs the IPC, the rate_response window
conventions) around ciclon-tropical trigger episodes, compared with the adopted
``c_ciclon`` scales via Kendall's tau. The adoption gate — episode-bootstrap
``P(tau* >= 0) < 0.05`` on the [0, +5] window — is PRE-REGISTERED verbatim in
``configs/sector_event_study.yaml`` and committed before the first estimation
run (INT-18 discipline); every other cut is diagnostic. FALLA is reportable
(INT-19 precedent).

Deterministic given the config seed (GEN-07); idempotent (GEN-05): skips if the
output exists, rerun with --forzar/--force.

    python pipelines/13_sector_event_study.py [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
STUDY_CONFIG = REPO_ROOT / "configs" / "sector_event_study.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    args = parser.parse_args()

    import pandas as pd
    from climateCCR.calibration.impact.hazard_jump import load_climate_events
    from climateCCR.calibration.impact.rate_response import build_episodes
    from climateCCR.calibration.impact.sector_response import (
        episode_bootstrap_p,
        episode_cars,
        ordering_stat,
    )
    from climateCCR.infra import RunManifest, get_logger, get_rng, load_config

    config = load_config(STUDY_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.sector_event_study", log_dir=config.paths.logs)
    extra = config.extra

    out_dir = config.paths.results / extra["output_dir"]
    out_resumen = out_dir / "resumen.csv"
    if out_resumen.exists() and not args.forzar:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", out_resumen)
        return

    deflator_file = config.paths.root / extra["deflator"]
    deflator = {
        int(y): float(v) for y, v in yaml.safe_load(deflator_file.read_text())["inpc"].items()
    }

    # Episode set: the pre-registered cyclone trigger spec.
    spec = extra["event_set"]
    events = load_climate_events(
        config.paths.root / extra["events_csv"],
        start_year=int(spec["start"]),
        end_year=int(spec["end"]),
        perils=[spec["peril"]],
        min_damage_mdp=float(spec["min_damage_mdp"]),
        deflator=deflator,
    )
    episodes = build_episodes(
        events,
        max_duration_days=float(spec["max_duration_days"]),
        merge_window_bd=int(spec["merge_window_bd"]),
    )
    logger.info(
        "%d cyclone episodes from %d trigger events (%d excluded by duration)",
        len(episodes),
        len(events),
        episodes.attrs["n_excluded_duration"],
    )

    # Adopted scales from the committed headline jump config: c_ciclon is the
    # tested ordering; the flat gamma (= sum_p pi_p c_ip) is a diagnostic.
    marks = yaml.safe_load((config.paths.root / extra["jump_config"]).read_text())["climate_jumps"][
        "equity_marks"
    ]
    mix = pd.Series(marks["peril_mix"], dtype=float)
    c_rows = pd.DataFrame(marks["target_peril_scales"], dtype=float).T  # names x groups
    c_ciclon = c_rows["ciclon_tropical"].rename("c_ciclon")
    gamma = (c_rows * mix.reindex(c_rows.columns)).sum(axis=1).rename("gamma")

    ipc = pd.read_csv(config.paths.root / extra["ipc_csv"], index_col=0, parse_dates=True)
    log_ipc = np.log(ipc["AdjClose"].dropna())

    study = extra["study"]
    est_window = tuple(int(x) for x in study["estimation_window_bd"])
    windows = [int(w) for w in study["event_windows_bd"]]
    gate_w = int(study["gate_window_bd"])
    if gate_w not in windows:
        sys.exit(f"gate_window_bd {gate_w} must be one of event_windows_bd {windows}")

    panels: dict[int, pd.DataFrame] = {}
    for window in windows:
        cols = {}
        for name in c_ciclon.index:
            prices = pd.read_csv(
                config.paths.root / extra["yahoo_book_dir"] / f"{name}.csv",
                index_col=0,
                parse_dates=True,
            )
            cars = episode_cars(
                np.log(prices["AdjClose"].dropna()),
                log_ipc,
                episodes,
                estimation_window_bd=est_window,
                event_window_bd=window,
                min_estimation_obs=int(study["min_estimation_obs"]),
                max_missing_frac=float(study["max_missing_frac"]),
            )
            cols[name] = cars["car"]
        panels[window] = pd.DataFrame(cols).reindex(episodes["fecha"])

    # Eligibility: fixed once, on the gate window of the original sample.
    counts = panels[gate_w].notna().sum()
    eligible = counts[counts >= int(study["min_episodes_per_name"])].index.tolist()
    excluded = sorted(set(c_ciclon.index) - set(eligible))
    logger.info(
        "name universe: %d eligible, excluded (< %d episodes): %s",
        len(eligible),
        int(study["min_episodes_per_name"]),
        {n: int(counts[n]) for n in excluded} or "none",
    )

    rng = get_rng(config.seed)
    rows = []
    for window in windows:
        panel = panels[window][eligible]
        mean_cars = panel.mean()
        tau, p_exact = ordering_stat(mean_cars, c_ciclon)
        p_boot = (
            episode_bootstrap_p(panel, c_ciclon, n_draws=int(study["n_bootstrap"]), rng=rng)
            if window == gate_w
            else float("nan")
        )
        tau_gamma, p_gamma = ordering_stat(mean_cars, gamma)
        rows.append(
            {
                "window_bd": window,
                "gating": window == gate_w,
                "tau_c_ciclon": tau,
                "p_boot": p_boot,
                "p_exact_kendall": p_exact,
                "tau_gamma": tau_gamma,
                "p_exact_gamma": p_gamma,
                "n_names": len(mean_cars.dropna()),
                "n_episodes": len(panel),
            }
        )
    resumen = pd.DataFrame(rows).set_index("window_bd")

    # Diagnostics on the gate window: tercile spread + drop-largest jackknife.
    gate_panel = panels[gate_w][eligible]
    mean_cars = gate_panel.mean()
    order = c_ciclon.reindex(eligible).sort_values()
    k = max(1, len(order) // 3)
    spread = float(mean_cars[order.index[-k:]].mean() - mean_cars[order.index[:k]].mean())
    largest = episodes.sort_values("danio_mdp").iloc[-1]
    jack_panel = gate_panel.drop(index=largest["fecha"], errors="ignore")
    tau_jack, p_jack = ordering_stat(jack_panel.mean(), c_ciclon)

    gate = resumen.loc[gate_w]
    verdict = "PASA" if gate["p_boot"] < float(extra["alpha"]) else "FALLA"

    out_dir.mkdir(parents=True, exist_ok=True)
    for window, panel in panels.items():
        panel.round(6).to_csv(out_dir / f"car_panel_w{window}.csv")
    per_name = pd.concat(
        [
            c_ciclon,
            gamma,
            counts.rename("n_episodes_w5"),
            panels[gate_w].mean().rename("mean_car_w5"),
        ],
        axis=1,
    )
    per_name.round(6).to_csv(out_dir / "per_name.csv")
    resumen.round(6).to_csv(out_resumen)
    (out_dir / "veredicto.md").write_text(
        f"# Phase C sector event study — veredicto: {verdict}\n\n"
        f"Pre-registered gate (configs/sector_event_study.yaml): episode-bootstrap "
        f"P(tau* >= 0) < {extra['alpha']} on the [0, +{gate_w}] window.\n\n"
        f"- tau(c_ciclon, mean CAR) = {gate['tau_c_ciclon']:.4f}\n"
        f"- p_boot = {gate['p_boot']:.4f} (n_bootstrap = {study['n_bootstrap']})\n"
        f"- exact Kendall p (diagnostic) = {gate['p_exact_kendall']:.4f}\n"
        f"- names {int(gate['n_names'])} / episodes {int(gate['n_episodes'])}; "
        f"excluded: {excluded or 'none'}\n"
        f"- tercile spread (top - bottom c_ciclon) = {spread:.5f} log-return\n"
        f"- drop-largest jackknife (episode {largest['fecha'].date()}, "
        f"{largest['danio_mdp']:.0f} MDP-2025): tau = {tau_jack:.4f}, "
        f"exact p = {p_jack:.4f}\n"
    )
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)

    print(resumen.round(4).to_string())
    print(f"\nveredicto: {verdict}  (gate p_boot = {gate['p_boot']:.4f}, alpha = {extra['alpha']})")
    print(f"tercile spread = {spread:.5f}; jackknife tau = {tau_jack:.4f} (p = {p_jack:.4f})")
    print(f"\nResumen:  {out_resumen}\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
