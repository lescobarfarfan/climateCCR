"""Storm-clustered sensitivity for the jump calibration — the OQ-INT-11 (f) robustness.

CENAPRED registers a named storm once per affected state, so the INT-20 lambda
and the INT-16/26 severity fits treat Hurricane Alex as 3 independent arrivals
and Ernesto as 6. ``load_climate_events(cluster_storms=True)`` merges same-storm
rows — one event per ``(anio, nombre_evento, peril_canonico)``, damage summed,
after the trigger filters — so total damage (hence ``lambda * E[L]``) is
conserved exactly and only the grain moves: fewer, larger events (registro
trigger set 270 -> 252, report-regime floor 65 -> 42, CT bridge 229 -> 164).
The *tail* is not invariant — that is the question this sensitivity answers
with a full 3-config band re-run vs the adopted base.

Each clustered variant re-derives exactly what its adopted config carries
(the INT-25/26 structure preserved):

- ``headline``  — clustered registro lambda + pooled marks + pi/c + per-label
  severity (registro window);
- ``ct_anchor`` — the headline's marks with only the clustered CT-bridge lambda
  swapped in (INT-20: the CT fit anchors the arrival *level* only);
- ``floor``     — clustered floor lambda + floor-regime pooled marks + reporte
  per-label severity; pi/c stay the headline's (the adopted configs share them).

gamma and its per-peril components are damage-panel climatology (INT-24) —
re-graining events does not touch them; only pi (hence ``c = gamma^p / pi``),
lambda and the severity fits move. Loss->mark scales are read from their
reconstructor artifacts (K_eff, INT-17; S_rate_eff_MX, INT-22) — yearly
aggregates, invariant under clustering.

Outputs under ``results/storm_cluster_sensitivity/`` (variant band configs
under ``configs/``; this runner is their deterministic reconstructor, GEN-04);
``--ejecutar-bandas`` runs the 3 bands via pipelines/01 (each writes its own
manifest). The collector reads whichever comparison frames exist and writes
``band_epe_deltas.csv`` (book-EPE shift %% base vs clustered), the supervisory
PFE99 tail readout ``per_naid_tail_shift.csv`` (CCR-RISK-03 floor at read
time), and ``nota.md``.

    python pipelines/14_storm_cluster_sensitivity.py [--forzar] [--ejecutar-bandas]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCALES_CONFIG = REPO_ROOT / "configs" / "equity_mark_scales.yaml"
VARIANT = "storm_clustered"
#: band config stem -> (event set that supplies lambda, event set that supplies marks).
BANDS = {
    "climate_jump_real_mexican": ("registro", "registro"),
    "climate_jump_real_mexican_ct_anchor": ("ct", "registro"),
    "climate_jump_real_mexican_floor": ("reporte", "reporte"),
}
#: CT bridge spec (INT-20): pooled ciclon 2002-2024, unthresholded — lambda only.
CT_SPEC = {"start_year": 2002, "end_year": 2024, "perils": ["Ciclón tropical"]}
#: Row-grain expectations (2026-08-01 profiling of the INT-25-era base). A
#: mismatch means the underlying event base changed — re-profile before trusting
#: this sensitivity (the pipelines/12 pattern: loud failure demands fresh triage).
EXPECTED_EVENTS = {"registro": (270, 252), "reporte": (65, 42), "ct": (229, 164)}


def _scale_from_artifact(path: Path, column: str) -> float:
    """One positive scalar from a reconstructor artifact, loudly."""
    if not path.exists():
        sys.exit(f"missing scale artifact {path} — run its reconstructor pipeline first")
    value = float(pd.read_csv(path)[column].iloc[0])
    if not value > 0:
        sys.exit(f"{path}: {column} = {value} is not a positive scale")
    return value


def _storm_audit(base: pd.DataFrame, set_key: str) -> pd.DataFrame:
    """Per merged-group audit rows from the *unclustered* frame."""
    name = base["nombre_evento"]
    named = base[name.notna() & name.astype(str).str.strip().ne("")]
    if named.empty:
        return pd.DataFrame()
    grouped = named.groupby(["anio", "nombre_evento", "peril_canonico"], sort=False).agg(
        n_filas=("danio_mdp", "size"),
        danio_mdp_real=("danio_mdp", "sum"),
        estados=("estados", lambda s: "|".join(dict.fromkeys(map(str, s)))),
    )
    multi = grouped[grouped["n_filas"] > 1].reset_index()
    multi.insert(0, "conjunto", set_key)
    return multi.sort_values("n_filas", ascending=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--forzar", "--force", action="store_true", help="recompute even if the output exists"
    )
    parser.add_argument(
        "--ejecutar-bandas",
        "--run-bands",
        action="store_true",
        help="also run the clustered 3-config band via pipelines/01 (3 sims)",
    )
    args = parser.parse_args()

    from climateCCR.calibration.impact.hazard_jump import (
        annual_event_counts,
        estimate_intensity,
        fit_peril_severity,
        fit_severity,
        load_climate_events,
    )
    from climateCCR.calibration.impact.sector_scales import (
        book_equity_weights,
        compose_scales,
        load_damage_intensity,
        peril_mix_from_events,
    )
    from climateCCR.infra import RunManifest, get_logger, load_config
    from climateCCR.viz.ccr import epe_summary, with_supervisory_pfe

    config = load_config(SCALES_CONFIG)
    config.paths.ensure()
    logger = get_logger("climateCCR.storm_cluster_sensitivity", log_dir=config.paths.logs)
    out_dir = config.paths.results / "storm_cluster_sensitivity"
    param_csv = out_dir / "parameter_summary.csv"
    if param_csv.exists() and not args.forzar and not args.ejecutar_bandas:
        logger.info("Output exists, nothing to do (rerun with --forzar): %s", param_csv)
        return

    extra = config.extra
    deflator_file = config.paths.root / extra["deflator"]
    deflator = {
        int(y): float(v) for y, v in yaml.safe_load(deflator_file.read_text())["inpc"].items()
    }
    book = yaml.safe_load((config.paths.root / extra["book_config"]).read_text())
    equities = book["equities"]
    peril_groups = extra["peril_groups"]
    mix_spec = extra["peril_mix_events"]
    sev_spec = extra["peril_severity"]
    events_csv = config.paths.root / mix_spec["events_csv"]
    min_damage = float(mix_spec["min_damage_mdp"])

    set_specs: dict[str, dict] = {
        key: {
            "start_year": int(sev_spec["variants"][key]["window"]["start_year"]),
            "end_year": int(sev_spec["variants"][key]["window"]["end_year"]),
            "min_damage_mdp": min_damage,
        }
        for key in ("registro", "reporte")
    }
    set_specs["ct"] = dict(CT_SPEC)

    k_eff = _scale_from_artifact(
        config.paths.results / "loss_to_mark_scale" / "scale.csv", "k_eff_mdp"
    )
    s_rate_eff = _scale_from_artifact(
        config.paths.results / "loss_to_rate_scale_mx" / "scale.csv", "s_rate_eff_mdp"
    )

    # ------------------------------------------------------- fits, base vs clustered
    fits: dict[str, dict] = {}
    audits, param_rows = [], []
    for key, spec in set_specs.items():
        base = load_climate_events(events_csv, deflator=deflator, **spec)
        clus = load_climate_events(events_csv, deflator=deflator, cluster_storms=True, **spec)
        if (len(base), len(clus)) != EXPECTED_EVENTS[key]:
            sys.exit(
                f"{key}: events {len(base)} -> {len(clus)}, expected "
                f"{EXPECTED_EVENTS[key]} — the event base changed, re-profile the grain"
            )
        if abs(base["danio_mdp"].sum() - clus["danio_mdp"].sum()) > 1e-6:
            sys.exit(f"{key}: clustering did not conserve total damage")
        lam_b, lam_c = (estimate_intensity(annual_event_counts(f)) for f in (base, clus))
        sev_b, sev_c = (fit_severity(f, deflated=True) for f in (base, clus))
        fits[key] = {"clus_events": clus, "lam_b": lam_b, "lam_c": lam_c, "sev_c": sev_c}
        audits.append(_storm_audit(base, key))
        param_rows.append(
            {
                "conjunto": key,
                "n_base": lam_b.n_events,
                "n_agrupado": lam_c.n_events,
                "lambda_base": lam_b.intensity,
                "lambda_agrupado": lam_c.intensity,
                "sev_median_base": sev_b.median,
                "sev_median_agrupado": sev_c.median,
                "sev_sigma_base": sev_b.sigma,
                "sev_sigma_agrupado": sev_c.sigma,
                "media_ajustada_base": sev_b.median * np.exp(sev_b.sigma**2 / 2),
                "media_ajustada_agrupado": sev_c.median * np.exp(sev_c.sigma**2 / 2),
                "danio_total_mdp": base["danio_mdp"].sum(),
            }
        )
        logger.info(
            "%s: %d -> %d events; lambda %.4f -> %.4f; sev (median, sigma) "
            "(%.2f, %.4f) -> (%.2f, %.4f)",
            key,
            lam_b.n_events,
            lam_c.n_events,
            lam_b.intensity,
            lam_c.intensity,
            sev_b.median,
            sev_b.sigma,
            sev_c.median,
            sev_c.sigma,
        )
        # Wiring guard: the adopted config this set feeds must carry the *base*
        # fit (else the window/threshold spec above drifted from the canon).
        for band, (lam_key, marks_key) in BANDS.items():
            cfg = yaml.safe_load((REPO_ROOT / "configs" / f"{band}.yaml").read_text())
            if lam_key == key and not np.isclose(
                float(cfg["climate_jumps"]["intensity"]), lam_b.intensity, rtol=1e-4
            ):
                sys.exit(f"{band}: adopted intensity != {key} base lambda {lam_b.intensity:.4f}")
            if marks_key == key and not np.isclose(
                float(cfg["climate_jumps"]["equity_marks"]["median"]),
                sev_b.median / k_eff,
                rtol=1e-3,
            ):
                sys.exit(f"{band}: adopted equity median != {key} base fit / K_eff")

    # Diagnostic: cluster-then-threshold would additionally pull sub-threshold
    # member rows of >=200-total storms into the registro set — count them.
    reg = set_specs["registro"]
    unthr = load_climate_events(
        events_csv,
        deflator=deflator,
        start_year=reg["start_year"],
        end_year=reg["end_year"],
    )
    name = unthr["nombre_evento"]
    named = unthr[name.notna() & name.astype(str).str.strip().ne("")]
    g = named.groupby(["anio", "nombre_evento", "peril_canonico"])["danio_mdp"].agg(
        ["sum", "size", lambda s: int((s >= min_damage).sum())]
    )
    g.columns = ["total", "n", "n_umbral"]
    joiners = g[(g["total"] >= min_damage) & (g["n_umbral"] < g["n"])]
    extra_rows = int((joiners["n"] - joiners["n_umbral"]).sum())
    logger.info(
        "cluster-then-threshold diagnostic: %d storm groups would pull %d sub-threshold "
        "rows into the registro set (not implemented; threshold-then-cluster keeps "
        "lambda*E[L] exactly invariant)",
        len(joiners),
        extra_rows,
    )

    # --------------------------------------------- clustered pi, c and per-label sev
    mix_c = peril_mix_from_events(
        events_csv,
        deflator=deflator,
        peril_groups=peril_groups,
        start_year=set_specs["registro"]["start_year"],
        end_year=set_specs["registro"]["end_year"],
        min_damage_mdp=min_damage,
        cluster_storms=True,
    )
    intensity_panel = load_damage_intensity(
        config.paths.root / extra["cenapred_panel"],
        deflator=deflator,
        peril_groups=peril_groups,
        population=extra["poblacion_2020"],
        start_year=int(extra["window"]["start_year"]),
        end_year=int(extra["window"]["end_year"]),
    )
    weights = book_equity_weights(config.paths.root / extra["eq_desk"], [e["rf"] for e in equities])
    scales = compose_scales(
        equities,
        susceptibility={s: dict(row) for s, row in extra["susceptibility"].items()},
        geo_exposure=extra["exposicion_geografica"],
        population=extra["poblacion_2020"],
        intensity=intensity_panel,
        weights=weights,
    )
    peril_cols = list(mix_c.index)
    missing_groups = [p for p in peril_cols if f"gamma_{p}" not in scales.columns]
    if missing_groups or set(peril_cols) != set(intensity_panel.columns):
        sys.exit(f"peril groups drifted between mix and panel: {missing_groups}")
    gamma_p = scales[[f"gamma_{p}" for p in peril_cols]].copy()
    gamma_p.columns = peril_cols
    c_c = gamma_p.div(mix_c.reindex(peril_cols), axis=1)
    identity = (c_c * mix_c.reindex(peril_cols)).sum(axis=1) - scales["gamma"]
    if identity.abs().max() > 1e-12:
        sys.exit(f"anchor identity broken under clustered pi ({identity.abs().max()})")

    sev_tables = {
        key: fit_peril_severity(
            fits[key]["clus_events"],
            peril_groups=peril_groups,
            pooled=fits[key]["sev_c"],
            min_events=int(sev_spec["min_events"]),
        )
        for key in ("registro", "reporte")
    }

    # ------------------------------------------------------------- artifacts + configs
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(param_rows).round(6).to_csv(param_csv, index=False)
    pd.concat([a for a in audits if not a.empty]).round(3).to_csv(
        out_dir / "cluster_audit.csv", index=False
    )
    mix_c.rename("pi").round(8).to_csv(out_dir / "peril_mix.csv")
    c_c.round(6).to_csv(out_dir / "target_peril_scales.csv")
    pd.concat(
        [t.assign(variant=k, pooled_sigma=fits[k]["sev_c"].sigma) for k, t in sev_tables.items()]
    ).round(6).to_csv(out_dir / "peril_severity.csv")

    config_dir = out_dir / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    for band, (lam_key, marks_key) in BANDS.items():
        band_cfg = yaml.safe_load((REPO_ROOT / "configs" / f"{band}.yaml").read_text())
        cj = band_cfg["climate_jumps"]
        sev_c = fits[marks_key]["sev_c"]
        cj["intensity"] = round(float(fits[lam_key]["lam_c"].intensity), 4)
        cj["rate_marks"]["median"] = float(f"{sev_c.median / s_rate_eff:.6g}")
        cj["rate_marks"]["sigma"] = round(float(sev_c.sigma), 4)
        eq = cj["equity_marks"]
        eq["median"] = round(float(sev_c.median / k_eff), 6)
        eq["sigma"] = round(float(sev_c.sigma), 4)
        eq["peril_mix"] = {p: round(float(mix_c[p]), 8) for p in peril_cols}
        eq["target_peril_scales"] = {
            rf: {p: round(float(c_c.loc[rf, p]), 6) for p in peril_cols} for rf in c_c.index
        }
        table = sev_tables[marks_key]
        eq["peril_severity"] = {
            p: {
                "median": round(float(eq["median"] * table.loc[p, "median_multiplier"]), 7),
                "sigma": round(float(table.loc[p, "sigma"]), 4),
            }
            for p in peril_cols
        }
        (config_dir / f"{band}__{VARIANT}.yaml").write_text(
            yaml.safe_dump(band_cfg, sort_keys=False, allow_unicode=True)
        )
        logger.info(
            "config %s__%s: lambda %.4f, marks from %s", band, VARIANT, cj["intensity"], marks_key
        )

    # ------------------------------------------------------------------ band runs
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

    # ------------------------------------------------------------------ collector
    delta_rows, tail_rows = [], []
    for band in BANDS:
        for variant, stem in (("base", band), ("agrupado", f"{band}__{VARIANT}")):
            shift_csv = config.paths.results / stem / "ee_pe_climate_shift.csv"
            if not shift_csv.exists():
                continue
            frame = pd.read_csv(shift_csv)
            band_label = band.replace("climate_jump_real_mexican", "").strip("_") or "headline"
            book = epe_summary(frame).set_index("netting_agreement_id").loc["BOOK"]
            delta_rows.append(
                {
                    "band": band_label,
                    "variant": variant,
                    "book_epe_shift_pct": book["epe_shift_pct"],
                    "book_epe_shift": book["epe_shift"],
                }
            )
            pfe = with_supervisory_pfe(frame)
            per_naid = pfe.groupby("netting_agreement_id")["uncollateralized_pfe_0.99_shift"].agg(
                ["mean", "min", "max"]
            )
            per_naid.columns = ["pfe99_shift_mean", "pfe99_shift_min", "pfe99_shift_max"]
            tail_rows.append(per_naid.assign(band=band_label, variant=variant).reset_index())
    deltas = pd.DataFrame(delta_rows)
    deltas.round(6).to_csv(out_dir / "band_epe_deltas.csv", index=False)
    if tail_rows:
        pd.concat(tail_rows).round(4).to_csv(out_dir / "per_naid_tail_shift.csv", index=False)

    if not deltas.empty and deltas["variant"].nunique() == 2:
        pivot = deltas.pivot(index="band", columns="variant", values="book_epe_shift_pct")
        params = pd.DataFrame(param_rows).set_index("conjunto")
        nota = out_dir / "nota.md"
        nota.write_text(
            "# Sensibilidad de agrupamiento por tormenta (OQ-INT-11 f)\n\n"
            "Grano: una fila CENAPRED por estado entra a los ajustes como un evento "
            "independiente; aquí cada tormenta nombrada se fusiona en un evento por "
            "`(anio, nombre_evento, peril_canonico)` con el danio sumado, después de los "
            "filtros del conjunto disparador — el danio total (y por tanto lambda*E[L]) se "
            "conserva exactamente; solo cambia el grano y con el, la cola.\n\n"
            "## Parametros (base -> agrupado)\n\n"
            f"```\n{params.round(4).to_string()}\n```\n\n"
            "## Banda EPE del libro (% shift)\n\n"
            f"```\n{pivot.round(4).to_string()}\n```\n\n"
            f"Diferencias (agrupado - base, pp): "
            f"{(pivot['agrupado'] - pivot['base']).round(4).to_dict()}\n\n"
            "## Diagnosticos\n\n"
            f"- cluster-then-threshold: {len(joiners)} grupos con {extra_rows} filas "
            "sub-umbral que entrarian si el umbral se aplicara al total de la tormenta "
            "(no implementado: el orden umbral->fusion conserva lambda*E[L] exacto).\n"
            "- Cola por contraparte: `per_naid_tail_shift.csv` (PFE99 supervisorio, "
            "CCR-RISK-03).\n"
            "- Auditoria de fusiones: `cluster_audit.csv`.\n\n"
            "La media por nombre y libro se preserva por construccion (INT-24/25/26); "
            "la lectura esperada es una banda EPE ~estable con colas mas pesadas por "
            "evento (menos eventos, mas grandes).\n"
        )
        logger.info("nota written: %s", nota)

    manifest = RunManifest.create(seed=config.seed, config=config, project_root=config.paths.root)
    manifest_path = manifest.write(config.paths.manifests)
    print(pd.DataFrame(param_rows).round(4).to_string(index=False))
    if not deltas.empty:
        print("\nBand EPE deltas (%):")
        print(
            deltas.pivot(index="band", columns="variant", values="book_epe_shift_pct")
            .round(2)
            .to_string()
        )
    print(f"\nOutputs: {out_dir}\nManifest: {manifest_path}")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT / "src"))
    main()
