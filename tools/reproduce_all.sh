#!/usr/bin/env bash
# tools/reproduce_all.sh — regenerate every stored artifact from the raw data roots, in
# dependency order: the chain-level reconstructor (GEN-04/05/06). Run with the climateCCR
# env active (GEN-30/37), from any directory:
#
#   tools/reproduce_all.sh                       # every stage, in order
#   tools/reproduce_all.sh --from cells          # resume at a stage
#   tools/reproduce_all.sh --to mkt              # stop after a stage
#   tools/reproduce_all.sh --only studies        # one stage
#   tools/reproduce_all.sh --jobs 6 --dry-run    # print the commands only
#   CLIMATECCR_REF=~/climateCCR_ref tools/reproduce_all.sh --only readouts
#
# Stages, in order: preflight haz hazcal mkt books ngfs cells studies readouts.
# One log per step under results/logs/reproduce/. Every pipeline is idempotent (GEN-05), so a
# finished step is skipped by the pipeline itself and re-running a stage is cheap.
# Runs that HEAD cannot regenerate — the historic mark states (*_uniforme/_fase_a/_fase_b),
# the pre-spread fase legs (*_fase_sin_spread), the archived readouts and results/_archive —
# are copied from a reference tree (--ref / CLIMATECCR_REF) because pipelines 19 and 21 read
# them; without a reference those two steps fail and everything else still runs.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export PYTHONUTF8=1 PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=2 MPLBACKEND=Agg
PY=${PYTHON:-python}
JOBS=4 FROM="" TO="" ONLY="" DRY=0 REF=${CLIMATECCR_REF:-}
while (($#)); do
  case $1 in
    --from) FROM=$2; shift 2 ;;
    --to) TO=$2; shift 2 ;;
    --only) ONLY=$2; shift 2 ;;
    --jobs) JOBS=$2; shift 2 ;;
    --ref) REF=$2; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
STAGES=(preflight haz hazcal mkt books ngfs cells studies readouts)
LOGDIR=results/logs/reproduce
mkdir -p "$LOGDIR"
HAZ=src/climateCCR/data/hazard_mx
CEN=data/hazard_mx/datos_CENAPRED
CNSF=data/hazard_mx/datos_CNSF
BASE_2000_2024=$CEN/crudos/pdfs_procesados_2016-2024/BASE_IMPACTO_SOCIOECONOMICO_DESASTRES_2000_2024.csv
MX="--book-config configs/mexican_book.yaml --data-root data/ccr_book_mx"
CMP="--book-config configs/comparison_book.yaml --data-root data/ccr_book_cmp"
export PY LOGDIR DRY

enabled() {
  local s=$1 seen=0 x
  if [[ -n $ONLY ]]; then [[ $s == "$ONLY" ]]; return; fi
  [[ -z $FROM ]] && seen=1
  for x in "${STAGES[@]}"; do
    [[ $x == "$FROM" ]] && seen=1
    [[ $x == "$s" ]] && return $((1 - seen))
    [[ $x == "$TO" ]] && seen=0
  done
  return 1
}

step() { # step <log-name> <command...>
  local name=$1 t0=$SECONDS
  shift
  if ((DRY)); then echo "[dry] $name: $*"; return 0; fi
  if "$@" >"$LOGDIR/$name.log" 2>&1; then
    printf 'ok   %-52s %5ds\n' "$name" $((SECONDS - t0))
  else
    printf 'FAIL %-52s %5ds  -> %s\n' "$name" $((SECONDS - t0)) "$LOGDIR/$name.log"
    return 1
  fi
}
cell() { step "cell.$1" "$PY" pipelines/01_climate_jump_demo.py "${@:2}"; }
export -f step cell

wait_all() { # wait for background steps; fail if any failed
  local fail=0 p
  for p in "$@"; do wait "$p" || fail=1; done
  ((fail == 0))
}

# ---------------------------------------------------------------- preflight
if enabled preflight; then
  echo "== preflight"
  step preflight.junk bash -c 'find data -name "._*" -o -name ".DS_Store" | xargs -r rm -v; true'
  step preflight.inputs bash -c "for f in $BASE_2000_2024 $CNSF/crudos/riesgos_hidrometereologicos \
    $CNSF/crudos/agricola_y_animales data/market_mx/sie/bonos_m.csv data/market_mx/yahoo/ipc_mxx.csv \
    data/market_mx/yahoo/book data/scenarios_mx/ngfs_short_term/climacred.csv; do
      [ -e \"\$f\" ] || { echo \"missing raw input: \$f\"; exit 1; }; done
    $PY -c 'import xlrd, openpyxl, requests, bs4, lxml'"
  step preflight.cenapred_verificar "$PY" $HAZ/cenapred/descarga_cenapred.py --modo verificar
fi

# ---------------------------------------------------------------- haz: consolidation
if enabled haz; then
  echo "== haz (CENAPRED + CNSF consolidation)"
  step haz.cenapred_2000_2024 "$PY" $HAZ/cenapred/procesar_cenapred.py --crudo $BASE_2000_2024 --cons $CEN/consolidados_2000_2024
  step haz.cenapred_twin "$PY" $HAZ/cenapred/procesar_cenapred.py --crudo $BASE_2000_2024 --cons $CEN/consolidados
  ALIAS=$HAZ/cnsf/aliases_cnsf.json
  step haz.cnsf_hidro "$PY" $HAZ/cnsf/consolidar_cnsf.py --root $CNSF/crudos --out-dir $CNSF/consolidados \
    --categorias riesgos_hidrometereologicos --comprimir gzip --aliases $ALIAS
  step haz.cnsf_agro "$PY" $HAZ/cnsf/consolidar_cnsf.py --root $CNSF/crudos --out-dir $CNSF/consolidados \
    --categorias agricola_y_animales --aliases $ALIAS
  step haz.cnsf_agro_corregir "$PY" $HAZ/cnsf/corregir_consolidados_agricola.py
fi

# ---------------------------------------------------------------- hazcal: HAZ calibration + tiers A/B
if enabled hazcal; then
  echo "== hazcal"
  step hazcal.12_inspeccion_cenapred_base "$PY" pipelines/12_inspeccion_cenapred_base.py
  step hazcal.03_hazard_jump_calibration "$PY" pipelines/03_hazard_jump_calibration.py
  step hazcal.03_hazard_jump_calibration_2000_2024 "$PY" pipelines/03_hazard_jump_calibration.py --config configs/hazard_jump_calibration_2000_2024.yaml
  step hazcal.04_loss_to_mark_scale "$PY" pipelines/04_loss_to_mark_scale.py
  step hazcal.27_hazard_backtest "$PY" pipelines/27_hazard_backtest.py
  step hazcal.28_loss_ratio_backtest "$PY" pipelines/28_loss_ratio_backtest.py
fi

# ---------------------------------------------------------------- mkt: market calibration
if enabled mkt; then
  echo "== mkt"
  step mkt.06_loss_to_rate_scale "$PY" pipelines/06_loss_to_rate_scale.py
  step mkt.06_loss_to_rate_scale_2000_2024 "$PY" pipelines/06_loss_to_rate_scale.py --config configs/loss_to_rate_scale_2000_2024.yaml
  step mkt.06_loss_to_rate_scale_2016_2024 "$PY" pipelines/06_loss_to_rate_scale.py --config configs/loss_to_rate_scale_2016_2024.yaml
  step mkt.07_market_calibration "$PY" pipelines/07_market_calibration.py
  step mkt.08_hw1f_diagnostics "$PY" pipelines/08_hw1f_diagnostics_figures.py
  step mkt.25_sie_compounding_check "$PY" pipelines/25_sie_compounding_check.py
fi

# ---------------------------------------------------------------- books: data roots, scales, market-side validation
if enabled books; then
  echo "== books"
  step books.09_mexican_book "$PY" pipelines/09_build_mexican_book.py
  step books.09_comparison_book "$PY" pipelines/09_build_mexican_book.py --config configs/comparison_book.yaml
  step books.10_equity_mark_scales "$PY" pipelines/10_equity_mark_scales.py
  step books.10_equity_mark_scales_comparison "$PY" pipelines/10_equity_mark_scales.py --config configs/equity_mark_scales_comparison.yaml
  pids=()
  step books.13_sector_event_study "$PY" pipelines/13_sector_event_study.py & pids+=($!)
  step books.29_risk_factor_backtest "$PY" pipelines/29_risk_factor_backtest.py & pids+=($!)
  step books.30_jump_density_backtest "$PY" pipelines/30_jump_density_backtest.py & pids+=($!)
  step books.18_model_vs_observed "$PY" pipelines/18_model_vs_observed_figures.py & pids+=($!)
  wait_all "${pids[@]}"
fi

# ---------------------------------------------------------------- ngfs: scenario overlays + fase fragments
if enabled ngfs; then
  echo "== ngfs"
  step ngfs.16_shock_curves "$PY" pipelines/16_ngfs_shock_curves.py
  step ngfs.16_shock_curves_trayectoria "$PY" pipelines/16_ngfs_shock_curves.py --config configs/ngfs_shock_trayectoria.yaml
  step ngfs.22_scheduled_shocks "$PY" pipelines/22_ngfs_scheduled_shocks.py
fi

# ---------------------------------------------------------------- cells: the direct pipelines/01 matrix
cells() { # one line per cell: <run_name> <pipelines/01 arguments>; run_name = config stem [+ _horizonte] [+ _etiqueta]
  local b s r
  echo "climate_jump_demo --config configs/climate_jump_demo.yaml --horizonte largo"
  echo "climate_jump_demo_corto --config configs/climate_jump_demo.yaml --horizonte corto"
  echo "climate_jump_demo_medio --config configs/climate_jump_demo.yaml --horizonte medio"
  for b in "" _ct_anchor _floor; do
    echo "climate_jump_real$b --config configs/climate_jump_real$b.yaml --horizonte largo"
    echo "climate_jump_real_mexican$b --config configs/climate_jump_real_mexican$b.yaml $MX --horizonte largo --trayectorias"
    echo "climate_jump_real_comparison$b --config configs/climate_jump_real_comparison$b.yaml $CMP --horizonte largo --trayectorias"
    for s in hwtp swuc; do
      echo "climate_jump_real_mexican${b}_ngfs_$s --config configs/climate_jump_real_mexican$b.yaml --book-config configs/mexican_book.yaml --data-root data/ccr_book_mx_ngfs/$s --horizonte largo --etiqueta ngfs_$s"
      echo "climate_jump_real_mexican${b}_ngfs_${s}_fase --config configs/climate_jump_real_mexican$b.yaml $MX --horizonte largo --etiqueta ngfs_${s}_fase --choques-programados results/ngfs_scheduled_shocks/${s^^}.yaml"
    done
  done
  echo "climate_jump_real_mexican_solo_tasas --config configs/climate_jump_real_mexican_solo_tasas.yaml $MX --horizonte largo --trayectorias"
  echo "climate_jump_real_comparison_solo_tasas --config configs/climate_jump_real_comparison_solo_tasas.yaml $CMP --horizonte largo --trayectorias"
  for r in registry ct_bridge; do
    echo "climate_jump_real_mexican_trend_$r --config configs/climate_jump_real_mexican_trend_$r.yaml $MX --horizonte largo"
  done
  echo "climate_jump_real_mexican_ngfs_daps_nam --config configs/climate_jump_real_mexican.yaml --book-config configs/mexican_book.yaml --data-root data/ccr_book_mx_ngfs/daps_nam --horizonte largo --etiqueta ngfs_daps_nam"
  echo "climate_jump_real_mexican_ngfs_daps_nam_fase --config configs/climate_jump_real_mexican.yaml $MX --horizonte largo --etiqueta ngfs_daps_nam_fase --choques-programados results/ngfs_scheduled_shocks/DAPS_NAM.yaml"
  for s in hwtp swuc daps_nam; do
    echo "climate_jump_real_mexican_ngfs_${s}_trayectoria --config configs/climate_jump_real_mexican.yaml --book-config configs/mexican_book.yaml --data-root data/ccr_book_mx_ngfs_trayectoria/$s --horizonte largo --etiqueta ngfs_${s}_trayectoria"
  done
}
if enabled cells; then
  echo "== cells ($(cells | wc -l) pipelines/01 runs, $JOBS at a time)"
  if ((DRY)); then cells | sed 's/^/[dry] cell /'; else
    cells | xargs -P "$JOBS" -L1 bash -c 'cell "$@"' _
  fi
fi

# ---------------------------------------------------------------- studies: the sub-run spawners, concurrently
if enabled studies; then
  echo "== studies (11 S-tier, 14 storm-cluster, 24 seeds x2, 31 tier-E chain; concurrent)"
  pids=()
  step studies.11_s_tier_sensitivity "$PY" pipelines/11_s_tier_sensitivity.py --ejecutar-bandas & pids+=($!)
  step studies.14_storm_cluster_sensitivity "$PY" pipelines/14_storm_cluster_sensitivity.py --ejecutar-bandas & pids+=($!)
  step studies.24_seed_sensitivity "$PY" pipelines/24_seed_sensitivity.py --ejecutar-bandas & pids+=($!)
  step studies.24_seed_sensitivity_comparison "$PY" pipelines/24_seed_sensitivity.py --config configs/seed_sensitivity_comparison.yaml --ejecutar-bandas & pids+=($!)
  step studies.31_static_book_backtest_ejecutar "$PY" pipelines/31_static_book_backtest.py --ejecutar & pids+=($!)
  wait_all "${pids[@]}"
fi

# ---------------------------------------------------------------- readouts: figures, readouts, carried-over archives
carry_over() { # archived runs HEAD cannot reproduce, copied verbatim with their manifests
  if [[ -z $REF ]]; then
    echo "     no --ref / CLIMATECCR_REF: archived runs not copied (pipelines 19 and 21 will fail)"
    return 0
  fi
  local dirs=(_archive chk_baseline_env equity_mark_scales_fase_a ngfs_epe_readout_solo_tasas
    ngfs_epe_readout_fase_sin_spread inspeccion/cenapred_extension_2016_2024
    figures/climate_jump_real_mexican_uniforme figures/climate_jump_real_mexican_fase_a
    climate_jump_real_mexican_ngfs_daps_nam_fase_sin_spread) b d
  for b in climate_jump_real_mexican climate_jump_real_mexican_ct_anchor climate_jump_real_mexican_floor; do
    dirs+=("${b}_uniforme" "${b}_fase_a" "${b}_fase_a_prime" "${b}_fase_b"
      "${b}_ngfs_hwtp_fase_sin_spread" "${b}_ngfs_swuc_fase_sin_spread")
  done
  for d in "${dirs[@]}"; do
    [[ -e $REF/results/$d ]] && { mkdir -p "results/$d"; rsync -a "$REF/results/$d/" "results/$d/"; }
  done
  mkdir -p results/loss_to_rate_scale_2016_2024 results/manifests
  rsync -a --ignore-existing "$REF/results/loss_to_rate_scale_2016_2024/diagnostico_apalancamiento_otis.md" results/loss_to_rate_scale_2016_2024/ 2>/dev/null || true
  grep -lE '(_uniforme|_fase_a|_fase_a_prime|_fase_b|_fase_sin_spread|per_naid_draw|accel_svd)' "$REF"/results/manifests/*.json \
    | xargs -r rsync -a --ignore-existing -t results/manifests/ 2>/dev/null \
    || grep -lE '(_uniforme|_fase_a|_fase_a_prime|_fase_b|_fase_sin_spread|per_naid_draw|accel_svd)' "$REF"/results/manifests/*.json \
    | xargs -r -I{} rsync -a --ignore-existing {} results/manifests/
  echo "     carried over ${#dirs[@]} archived run directories from $REF"
}
if enabled readouts; then
  echo "== readouts"
  step readouts.17_ngfs_epe_readout "$PY" pipelines/17_ngfs_epe_readout.py
  step readouts.17_ngfs_epe_readout_trayectoria "$PY" pipelines/17_ngfs_epe_readout.py --config configs/ngfs_shock_trayectoria.yaml
  step readouts.17_ngfs_epe_readout_fase "$PY" pipelines/17_ngfs_epe_readout.py --config configs/ngfs_scheduled.yaml
  step readouts.02_climate_jump_demo "$PY" pipelines/02_climate_jump_figures.py --config configs/climate_jump_demo.yaml --horizonte largo
  step readouts.02_climate_jump_demo_corto "$PY" pipelines/02_climate_jump_figures.py --config configs/climate_jump_demo.yaml --horizonte corto
  step readouts.02_climate_jump_demo_medio "$PY" pipelines/02_climate_jump_figures.py --config configs/climate_jump_demo.yaml --horizonte medio
  step readouts.02_climate_jump_real_mexican "$PY" pipelines/02_climate_jump_figures.py --config configs/climate_jump_real_mexican.yaml $MX --horizonte largo \
    --escenarios configs/climate_jump_real_mexican_ct_anchor.yaml configs/climate_jump_real_mexican_floor.yaml
  step readouts.02_trend_registry "$PY" pipelines/02_climate_jump_figures.py --config configs/climate_jump_real_mexican_trend_registry.yaml $MX --horizonte largo
  step readouts.02_trend_ct_bridge "$PY" pipelines/02_climate_jump_figures.py --config configs/climate_jump_real_mexican_trend_ct_bridge.yaml $MX --horizonte largo
  step readouts.20_aggregate_loss "$PY" pipelines/20_aggregate_loss_figures.py
  step readouts.23_ngfs_fase_figures "$PY" pipelines/23_ngfs_fase_figures.py
  step readouts.31_static_book_backtest "$PY" pipelines/31_static_book_backtest.py
  step readouts.26_book_comparison "$PY" pipelines/26_book_comparison_readout.py
  ((DRY)) || carry_over
  step readouts.21_cva_readout "$PY" pipelines/21_cva_readout.py
  step readouts.19_results_distributions "$PY" pipelines/19_results_distribution_figures.py
fi
echo "done: $(date -Is)"
