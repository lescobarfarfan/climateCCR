"""S-tier sensitivity for the OQ-INT-11 scales — the (d) robustness (Phase A+B).

The S matrix's tier *levels* are ordinal author judgment ([eng]; the hidro
ordering is CNSF-pinned). This runner quantifies how much the gamma ordering and
the band headline depend on them, two ways:

1. **Tier-jitter Monte Carlo** (analytic, no simulation): every nonzero S cell
   moves one step up/down/stay (1/3 each) on the observed tier ladder;
   structural zeros stay zero (they encode "no channel", not a level). N draws
   of the full gamma vector -> per-name ranges and the Kendall tau of each
   draw's ordering vs the baseline. Emits CSVs + one viz-standard figure.

2. **Structured variants**, each re-deriving gamma / per-peril scales and (with
   ``--ejecutar-bandas``) re-running the full 3-config band via pipelines/01:

   - ``hidro_merged``  — ciclón+lluvia+inundación collapsed to one column
     (S damage-weighted, H summed, pi summed): the joint-cyclone-attribution
     check (a "Ciclón tropical" row bundles wind+surge+rain, impactcal-mx
     CAL-BAYES-10; the boundary between the three hidro labels is fuzzy).
   - ``fluvial_merged`` — lluvia+inundación only: the surgical check for the
     2016 INUND->LLUV relabeling (CAL-TARGET-06 import; post-2016 fluvial
     damage all lands under lluvia, so that split of H is regime-dependent).
   - ``flatten`` / ``sharpen`` — S^(1/2) / S^2 on nonzero cells: contrast
     compression/amplification bounds on the ordinal levels.
   - ``drop_alex``     — H minus Hurricane Alex's Nuevo León row
     (CEN-2010-03494/96 registry id CEN-2010-03496, 21,501 MDP nominal 2010):
     H[NL, ciclón] is ~74% this one event, the "history = one draw"
     concentration check.

   Variant band configs are generated under results/ (unversioned; this runner
   is their deterministic reconstructor, GEN-04) and reuse pipelines/01
   unchanged, so every simulated variant writes its own manifest.

The collector (also idempotent) reads whichever variant bands exist and writes
``band_epe_deltas.csv``: book-EPE shift %% per variant x band member, plus the
gamma Kendall tau vs baseline — the robustness table for the manuscript.

    python pipelines/11_s_tier_sensitivity.py [--forzar] [--ejecutar-bandas]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import kendalltau

REPO_ROOT = Path(__file__).resolve().parents[1]
SCALES_CONFIG = REPO_ROOT / "configs" / "equity_mark_scales.yaml"
BAND_CONFIGS = [
    "climate_jump_real_mexican",
    "climate_jump_real_mexican_ct_anchor",
    "climate_jump_real_mexican_floor",
]
N_JITTER = 500
HIDRO = ["ciclon_tropical", "lluvia", "inundacion"]
FLUVIAL = ["lluvia", "inundacion"]
ALEX_NL = {"entidad": "Nuevo León", "peril": "ciclon_tropical", "anio": 2010, "danio_mdp": 21501.0}


def _merged_inputs(susceptibility, intensity, mix, population, merge: list[str], name: str):
    """Merge ``merge`` peril columns into one ``name`` column across S, H, pi."""
    pop = pd.Series(population).astype(float).reindex(intensity.index)
    damage_weight = intensity[merge].mul(pop, axis=0).sum(axis=0)  # national damage per group
    s_v = {}
    for sector, row in susceptibility.items():
        merged_tier = float(sum(damage_weight[p] * row[p] for p in merge) / damage_weight.sum())
        s_v[sector] = {p: v for p, v in row.items() if p not in merge} | {name: merged_tier}
    h_v = intensity.drop(columns=merge).assign(**{name: intensity[merge].sum(axis=1)})
    mix_v = mix.drop(merge)
    mix_v[name] = mix[merge].sum()
    return s_v, h_v, mix_v.sort_index()


def _powered(susceptibility, exponent: float):
    return {
        sector: {p: float(v) ** exponent if v > 0 else 0.0 for p, v in row.items()}
        for sector, row in susceptibility.items()
    }


def _drop_alex_intensity(intensity, deflator, population):
    """H minus the Alex NL registry row's per-capita contribution (sanity-checked)."""
    base = max(deflator)
    real = ALEX_NL["danio_mdp"] * deflator[base] / deflator[ALEX_NL["anio"]]
    per_capita = real / float(population[ALEX_NL["entidad"]])
    h_v = intensity.copy()
    cell = h_v.loc[ALEX_NL["entidad"], ALEX_NL["peril"]]
    if cell < per_capita:
        raise ValueError(f"H[NL, ciclón] {cell} < Alex contribution {per_capita}")
    h_v.loc[ALEX_NL["entidad"], ALEX_NL["peril"]] = cell - per_capita
    return h_v


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    parser.add_argument(
        "--ejecutar-bandas",
        "--run-bands",
        action="store_true",
        help="also run the full 3-config band per structured variant (15 sims, pipelines/01)",
    )
    args = parser.parse_args()

    from climateCCR.calibration.impact.sector_scales import (
        book_equity_weights,
        compose_scales,
        load_damage_intensity,
        peril_mix_from_events,
    )
    from climateCCR.infra import RunManifest, get_logger, get_rng, load_config
    from climateCCR.viz.ccr import epe_summary
    from climateCCR.viz.style import apply_style, save_figure

    config = load_config(SCALES_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.s_tier_sensitivity", log_dir=config.paths.logs)
    out_dir = config.paths.results / "s_tier_sensitivity"
    jitter_csv = out_dir / "s_tier_jitter_gamma.csv"
    if jitter_csv.exists() and not args.forzar and not args.ejecutar_bandas:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", jitter_csv)
        return

    extra = config.extra
    deflator_file = config.paths.root / extra["deflator"]
    deflator = {
        int(y): float(v) for y, v in yaml.safe_load(deflator_file.read_text())["inpc"].items()
    }
    book = yaml.safe_load((config.paths.root / extra["book_config"]).read_text())
    equities = book["equities"]
    susceptibility = {s: dict(row) for s, row in extra["susceptibility"].items()}
    population = extra["poblacion_2020"]

    intensity = load_damage_intensity(
        config.paths.root / extra["cenapred_panel"],
        deflator=deflator,
        peril_groups=extra["peril_groups"],
        population=population,
        start_year=int(extra["window"]["start_year"]),
        end_year=int(extra["window"]["end_year"]),
    )
    weights = book_equity_weights(config.paths.root / extra["eq_desk"], [e["rf"] for e in equities])
    mix_spec = extra["peril_mix_events"]
    mix = peril_mix_from_events(
        config.paths.root / mix_spec["events_csv"],
        deflator=deflator,
        peril_groups=extra["peril_groups"],
        start_year=int(mix_spec["window"]["start_year"]),
        end_year=int(mix_spec["window"]["end_year"]),
        min_damage_mdp=float(mix_spec["min_damage_mdp"]),
    )

    def compose(s_dict, h_frame):
        return compose_scales(
            equities,
            susceptibility=s_dict,
            geo_exposure=extra["exposicion_geografica"],
            population=population,
            intensity=h_frame,
            weights=weights,
        )

    baseline = compose(susceptibility, intensity)
    gamma0 = baseline["gamma"]

    # ------------------------------------------------------------------ jitter
    ladder = np.array(
        sorted({float(v) for row in susceptibility.values() for v in row.values() if v > 0})
    )
    rng = get_rng(config.seed)
    draws = np.empty((N_JITTER, len(gamma0)))
    taus = np.empty(N_JITTER)
    for k in range(N_JITTER):
        s_k = {}
        for sector, row in susceptibility.items():
            s_k[sector] = {}
            for p, v in row.items():
                if v <= 0:
                    s_k[sector][p] = 0.0  # structural zero: no channel, not a level
                    continue
                idx = int(np.abs(ladder - float(v)).argmin())
                idx = int(np.clip(idx + rng.integers(-1, 2), 0, len(ladder) - 1))
                s_k[sector][p] = float(ladder[idx])
        gamma_k = compose(s_k, intensity)["gamma"].reindex(gamma0.index)
        draws[k] = gamma_k.to_numpy()
        taus[k] = kendalltau(gamma0.to_numpy(), draws[k]).statistic
    jitter = pd.DataFrame(
        {
            "gamma_base": gamma0,
            "gamma_min": draws.min(axis=0),
            "gamma_p05": np.quantile(draws, 0.05, axis=0),
            "gamma_median": np.median(draws, axis=0),
            "gamma_p95": np.quantile(draws, 0.95, axis=0),
            "gamma_max": draws.max(axis=0),
        },
        index=gamma0.index,
    ).sort_values("gamma_base", ascending=False)
    out_dir.mkdir(parents=True, exist_ok=True)
    jitter.round(6).to_csv(jitter_csv)
    pd.Series(taus, name="kendall_tau").round(6).to_csv(out_dir / "s_tier_jitter_tau.csv")
    logger.info(
        "tier jitter (N=%d): Kendall tau median %.3f [min %.3f]; gamma rank-1 name stable in "
        "%.1f%% of draws",
        N_JITTER,
        float(np.median(taus)),
        float(taus.min()),
        100.0 * float((draws.argmax(axis=1) == int(np.argmax(gamma0.to_numpy()))).mean()),
    )

    apply_style()
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.0, 6.0))
    y = np.arange(len(jitter))[::-1]
    ax.hlines(y, jitter["gamma_p05"], jitter["gamma_p95"], lw=3, alpha=0.6)
    ax.plot(jitter["gamma_base"], y, "o", ms=4)
    ax.set_yticks(y, [n.replace("_SHARE", "") for n in jitter.index], fontsize=7)
    ax.set_xlabel("gamma (book-anchored)")
    ax.set_title(
        f"S-tier jitter (±1 tier, N={N_JITTER}): gamma p05–p95 vs base\n"
        f"ordering Kendall tau median {np.median(taus):.3f}, min {taus.min():.3f}"
    )
    save_figure(fig, out_dir / "s_tier_jitter_gamma")
    plt.close(fig)

    # ---------------------------------------------------------------- variants
    variants = {
        "hidro_merged": _merged_inputs(susceptibility, intensity, mix, population, HIDRO, "hidro"),
        "fluvial_merged": _merged_inputs(
            susceptibility, intensity, mix, population, FLUVIAL, "fluvial"
        ),
        "flatten": (_powered(susceptibility, 0.5), intensity, mix),
        "sharpen": (_powered(susceptibility, 2.0), intensity, mix),
        "drop_alex": (susceptibility, _drop_alex_intensity(intensity, deflator, population), mix),
    }
    config_dir = out_dir / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    variant_rows = []
    for vname, (s_v, h_v, mix_v) in variants.items():
        scales_v = compose(s_v, h_v)
        gamma_v = scales_v["gamma"]
        peril_cols = list(h_v.columns)
        gamma_p = scales_v[[f"gamma_{p}" for p in peril_cols]].copy()
        gamma_p.columns = peril_cols
        c_v = gamma_p.div(mix_v.reindex(peril_cols), axis=1)
        identity = (c_v * mix_v.reindex(peril_cols)).sum(axis=1) - gamma_v
        if identity.abs().max() > 1e-12:
            sys.exit(f"{vname}: anchor identity broken ({identity.abs().max()})")
        vdir = out_dir / vname
        vdir.mkdir(parents=True, exist_ok=True)
        scales_v.round(6).to_csv(vdir / "target_scales.csv")
        c_v.round(6).to_csv(vdir / "target_peril_scales.csv")
        mix_v.rename("pi").round(8).to_csv(vdir / "peril_mix.csv")
        tau_v = kendalltau(gamma0.to_numpy(), gamma_v.reindex(gamma0.index).to_numpy()).statistic
        variant_rows.append({"variant": vname, "gamma_kendall_tau_vs_base": tau_v})
        logger.info(
            "%s: gamma tau vs base %.3f; range %.3f-%.3f",
            vname,
            tau_v,
            gamma_v.min(),
            gamma_v.max(),
        )

        for band in BAND_CONFIGS:
            band_cfg = yaml.safe_load((REPO_ROOT / "configs" / f"{band}.yaml").read_text())
            eq = band_cfg["climate_jumps"]["equity_marks"]
            eq["peril_mix"] = {p: round(float(mix_v[p]), 8) for p in peril_cols}
            eq["target_peril_scales"] = {
                name: {p: round(float(c_v.loc[name, p]), 6) for p in peril_cols}
                for name in c_v.index
            }
            (config_dir / f"{band}__{vname}.yaml").write_text(
                yaml.safe_dump(band_cfg, sort_keys=False, allow_unicode=True)
            )

    if args.ejecutar_bandas:
        for cfg in sorted(config_dir.glob("*.yaml")):
            logger.info("running band %s", cfg.stem)
            subprocess.run(
                [
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
                    "--forzar",
                ],
                check=True,
                cwd=REPO_ROOT,
            )

    # --------------------------------------------------------------- collector
    tau_by_variant = {r["variant"]: r["gamma_kendall_tau_vs_base"] for r in variant_rows}
    delta_rows = []
    for vname in ["base"] + list(variants):
        for band in BAND_CONFIGS:
            stem = band if vname == "base" else f"{band}__{vname}"
            shift_csv = config.paths.results / stem / "ee_pe_climate_shift.csv"
            if not shift_csv.exists():
                continue
            book = epe_summary(pd.read_csv(shift_csv)).set_index("netting_agreement_id").loc["BOOK"]
            delta_rows.append(
                {
                    "variant": vname,
                    "band": band.replace("climate_jump_real_mexican", "").strip("_") or "headline",
                    "book_epe_shift_pct": book["epe_shift_pct"],
                    "gamma_kendall_tau_vs_base": tau_by_variant.get(vname, 1.0),
                }
            )
    deltas = pd.DataFrame(delta_rows)
    deltas.round(6).to_csv(out_dir / "band_epe_deltas.csv", index=False)

    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)
    print(jitter.round(4).to_string())
    print(f"\nKendall tau (jitter): median {np.median(taus):.3f}, min {taus.min():.3f}")
    if not deltas.empty:
        print("\nBand EPE deltas by variant (%):")
        print(
            deltas.pivot(index="variant", columns="band", values="book_epe_shift_pct")
            .round(2)
            .to_string()
        )
    print(f"\nOutputs: {out_dir}\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
