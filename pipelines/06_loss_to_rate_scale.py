"""Loss->rate scale via event study — OQ-INT-09 (DC-XWALK-4 rate leg).

Regresses cumulative abnormal Mexican yield changes around major CENAPRED
climate episodes on episode losses, per pillar and event window (the beta(T)
term structure), evaluates the PRE-REGISTERED criterion pinned in
``configs/loss_to_rate_scale.yaml``, and writes:

- ``results/loss_to_rate_scale/beta_by_pillar.csv`` — every pillar x window
  cell plus the robustness variants (``variante`` column);
- ``results/loss_to_rate_scale/scale.csv`` — one row: the adopted branch
  (``estimado`` | ``literatura``), beta, and the derived ``s_rate_eff_mdp``.

Needs pipelines/05_download_sie_series.py to have run. Deterministic given the
downloaded data (bootstrap seeded from the config); idempotent (GEN-05).

    python pipelines/06_loss_to_rate_scale.py [--forzar]
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCALE_CONFIG = REPO_ROOT / "configs" / "loss_to_rate_scale.yaml"


def _fred_series(path: Path) -> pd.Series:
    """A fredgraph CSV (DATE/observation_date + one value column) as decimal levels."""
    frame = pd.read_csv(path, na_values=".")
    return pd.Series(
        pd.to_numeric(frame.iloc[:, 1], errors="coerce").to_numpy() / 100.0,
        index=pd.to_datetime(frame.iloc[:, 0]),
    ).sort_index()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    args = parser.parse_args()

    from climateCCR.calibration.financial.bond_yield import bono_yield_panel
    from climateCCR.calibration.impact import (
        build_episodes,
        event_study,
        load_climate_events,
        rate_scale_from_beta,
    )
    from climateCCR.infra import RunManifest, get_logger, get_rng, load_config

    config = load_config(SCALE_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.loss_to_rate_scale", log_dir=config.paths.logs)

    out_dir = config.paths.results / "loss_to_rate_scale"
    out_scale = out_dir / "scale.csv"
    if out_scale.exists() and not args.forzar:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", out_scale)
        return

    sie_dir = config.paths.root / config.extra["sie_dir"]
    fred_dir = config.paths.root / config.extra["fred_dir"]
    for required in (sie_dir / "tiies.csv", sie_dir / "bonos_m.csv"):
        if not required.exists():
            sys.exit(f"Missing {required}; run pipelines/05_download_sie_series.py first.")

    deflator_file = config.paths.root / config.extra["deflator"]
    deflator = {
        int(y): float(v) for y, v in yaml.safe_load(deflator_file.read_text())["inpc"].items()
    }
    event_set = config.extra["event_set"]
    episode_cfg = config.extra["episode"]

    def episodes_for(min_damage: float) -> pd.DataFrame:
        events = load_climate_events(
            config.paths.root / config.extra["events_csv"],
            start_year=int(event_set["start"]),
            end_year=int(event_set["end"]),
            min_damage_mdp=float(min_damage),
            deflator=deflator,
        )
        return build_episodes(
            events,
            max_duration_days=float(episode_cfg["max_duration_days"]),
            merge_window_bd=int(episode_cfg["merge_window_bd"]),
        )

    episodes = episodes_for(float(event_set["min_damage_mdp"]))
    logger.info(
        "Episodes: %d (from >=%.0f MDP-2025 events; %d long-duration excluded)",
        len(episodes),
        event_set["min_damage_mdp"],
        episodes.attrs["n_excluded_duration"],
    )

    # --- daily series, all in decimal ------------------------------------
    groups: dict[str, pd.DataFrame] = {}
    for group in ("tiies", "cetes364"):
        groups[group] = pd.read_csv(sie_dir / f"{group}.csv", index_col="Fecha", parse_dates=True)
    bonos_panel = bono_yield_panel(pd.read_csv(sie_dir / "bonos_m.csv"))
    plazo_median = bonos_panel.attrs["plazo_median_days"]
    logger.info(
        "Bonos M yields solved: %s",
        {
            s: f"{bonos_panel[s].notna().sum()} obs, T~{plazo_median[s] / 365:.1f}y"
            for s in bonos_panel.columns
        },
    )
    fred = {
        sid: _fred_series(fred_dir / f"{sid}.csv")
        for sid in config.extra["fred"]
        if (fred_dir / f"{sid}.csv").exists()
    }

    def pillar_series(name: str, spec: dict) -> tuple[pd.Series, float] | None:
        if spec["grupo"] == "bonos_m":
            if name not in bonos_panel.columns:
                return None
            return bonos_panel[name].dropna(), float(plazo_median[name]) / 365.0
        series = groups[spec["grupo"]][spec["columna"]].dropna() / 100.0
        return series, float(spec["t_dias"]) / 365.0

    # --- the beta(T) table -----------------------------------------------
    study = config.extra["study"]
    lead = config.extra["lead"]
    robustness = config.extra["robustness"]
    gfc_lo, gfc_hi = (pd.Timestamp(d) for d in robustness["gfc_exclusion"])
    variants: dict[str, pd.DataFrame] = {
        "principal": episodes,
        "sin_gfc": episodes[(episodes["fecha"] < gfc_lo) | (episodes["fecha"] > gfc_hi)],
        f"mayores_{int(robustness['min_damage_alt'])}mdp": episodes_for(
            float(robustness["min_damage_alt"])
        ),
    }

    rows = []
    for variante, eps in variants.items():
        windows = study["event_windows_bd"] if variante == "principal" else [lead["window_bd"]]
        for name, spec in config.extra["pillars"].items():
            resolved = pillar_series(name, spec)
            if resolved is None or spec["control"] not in fred:
                logger.warning("Pillar %s skipped (no data/control)", name)
                continue
            series, t_years = resolved
            for window in windows:
                result = event_study(
                    series,
                    fred[spec["control"]],
                    eps,
                    pillar=name,
                    t_years=t_years,
                    estimation_window_bd=tuple(study["estimation_window_bd"]),
                    event_window_bd=int(window),
                    min_estimation_obs=int(study["min_estimation_obs"]),
                    max_missing_frac=float(study["max_missing_frac"]),
                    n_bootstrap=int(study["n_bootstrap"]),
                    rng=get_rng(config.seed),
                )
                if result is not None:
                    rows.append({"variante": variante, **asdict(result)})
    table = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_dir / "beta_by_pillar.csv", index=False)

    # --- the pre-registered gate (see the config header; it never bends) --
    lead_cell = None
    principal = table[
        (table["variante"] == "principal") & (table["window_bd"] == lead["window_bd"])
    ]
    for pillar in lead["pillar_order"]:
        candidate = principal[principal["pillar"] == pillar]
        if len(candidate) and int(candidate.iloc[0]["n_episodes"]) >= int(lead["min_episodes"]):
            lead_cell = candidate.iloc[0]
            break
    if lead_cell is None:
        sys.exit("No lead pillar reached min_episodes; check the downloaded data window.")
    passed = bool(
        lead_cell["beta_per_bn"] > 0 and lead_cell["p_one_sided"] < float(lead["p_threshold"])
    )
    logger.info(
        "Lead cell %s [0,+%d]: beta=%.3e per bn MDP (HC1 se %.3e), p=%.4f, n=%d -> %s",
        lead_cell["pillar"],
        lead["window_bd"],
        lead_cell["beta_per_bn"],
        lead_cell["se_hc1"],
        lead_cell["p_one_sided"],
        lead_cell["n_episodes"],
        "PASA" if passed else "FALLA",
    )

    hw_alpha = float(config.extra["hw1f_alpha"])
    if passed:
        fuente, beta, t_years = (
            "estimado",
            float(lead_cell["beta_per_bn"]),
            float(lead_cell["t_years"]),
        )
    else:
        fallback = config.extra["fallback"]
        beta = fallback["beta_per_bn_mdp"] and float(fallback["beta_per_bn_mdp"])
        t_years = float(fallback["t_years"])
        fuente = "literatura"
    if beta:
        j_per_mdp, s_rate_eff = rate_scale_from_beta(beta, t_years, hw_alpha)
    else:
        j_per_mdp = s_rate_eff = float("nan")

    scale_row = pd.DataFrame(
        [
            {
                "fuente": fuente,
                "criterion_passed": passed,
                "pillar": lead_cell["pillar"],
                "t_years": t_years,
                "window_bd": int(lead["window_bd"]),
                "n_episodes": int(lead_cell["n_episodes"]),
                "beta_adopted_per_bn": beta if beta else float("nan"),
                "beta_lead_per_bn": float(lead_cell["beta_per_bn"]),
                "se_hc1_lead": float(lead_cell["se_hc1"]),
                "p_one_sided_lead": float(lead_cell["p_one_sided"]),
                "p_bootstrap_lead": float(lead_cell["p_bootstrap"]),
                "hw1f_alpha": hw_alpha,
                "j_per_mdp": j_per_mdp,
                "s_rate_eff_mdp": s_rate_eff,
            }
        ]
    )
    scale_row.to_csv(out_scale, index=False)
    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)

    print(table.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    print(
        f"\nCRITERIO: {'PASA' if passed else 'FALLA'} ({lead_cell['pillar']}, "
        f"p={lead_cell['p_one_sided']:.4f}, n={int(lead_cell['n_episodes'])})"
    )
    if np.isfinite(s_rate_eff):
        print(
            f"rate_marks.median for a severity fit = sev_median_mdp / {s_rate_eff:.6g}"
            f"\nrate_marks.sign = +1.0  (adverse event -> sovereign yields UP)"
        )
    else:
        print(
            "Gate FAILed and fallback.beta_per_bn_mdp is unset: verify the literature "
            "number (Klomp2020/Klusak2023) before wiring rate_marks (GEN-01)."
        )
    print(
        f"Tabla:    {out_dir / 'beta_by_pillar.csv'}\nEscala:   {out_scale}"
        f"\nManifest: {manifest_path}"
    )


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
