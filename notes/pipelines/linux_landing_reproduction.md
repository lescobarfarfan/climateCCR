# Landing the project on a second machine — the Linux x86-64 reproduction (2026-10-20)

Operational note: how climateCCR was landed on an Ubuntu 24.04 / Intel x86-64 machine (i7-8750H, 6C/12T, AVX2) from the macOS / Apple-Silicon machine where every stored result had been produced, what had to change, how every artifact was regenerated from the raw data, and how closely each one reproduces. Decisions: `GEN-37` (amended this session), `GEN-30`, `GEN-04/05/06`. Tools: `tools/reproduce_all.sh`, `tools/compare_results.py`, `tools/headlines.yaml`.

## 1. What travels and what is regenerated

`data/` and `results/` are git-ignored, so a landing needs a copy of both from the producing machine (here: an external drive → `~/Documents/projects/Thesis_MScQF/climateCCR_ref/{data,results}`, 5.3 GB + 4.1 GB without the 5.1 GB drought tree, which nothing on the results chain reads). Copy with `rsync -rltDv --exclude='._*' --exclude='.DS_Store'` and run `dot_clean` on exFAT: AppleDouble files would be globbed by `data/scenarios/ngfs.py`, `consolidar_cnsf.py` and `pipelines/29`.

| Rows of the copy | Into the repo? | Why |
|---|---|---|
| `datos_CENAPRED/crudos/` (PDFs, the 2000–2015 CSV, `pdfs_procesados_2016-2024/` with the hand-captured `BASE_…_2000_2024.csv` + `rows_2024.json`, `captura/`, `_procedencia.json`, the `*_resumen2024_20260721` archive trails) | yes | hand-captured rows and `EXTENSO_2024.pdf` (`url: null`) are not downloadable |
| `datos_CNSF/crudos/`, `crudos_snapshots/`, the `*_reporte.json` | yes | SharePoint dumps, never re-downloaded (`GEN-24`) |
| `market_mx/sie`, `market_mx/fred`, `market_mx/yahoo/{ipc_mxx.csv, book, book_cmp, book_bt_*}` with every `_procedencia.json` | yes | vintage-pinned pulls: `sie_series.yaml` has `end: null`, so a fresh pull moves the curve date and every EE cell; Yahoo restates adjusted closes |
| `scenarios_mx/ngfs_short_term` | yes | pinned by `run_id` + `version` |
| `datos_CENAPRED/consolidados*`, `datos_CNSF/consolidados`, `ccr_book_*`, `ccr_book_mx_ngfs*`, `ccr_book_mx_bt_*` | no — regenerated, the copy is the diff reference | deterministic reconstructors (`GEN-04`) |
| `results/` (182 directories, 522 manifests) | no — regenerated; 16 archived runs are carried over | reference for the numeric diff; `pipelines/19` and `/21` read the archived mark states (`*_uniforme/_fase_a/_fase_b`) and the pre-spread fase legs (`*_fase_sin_spread`), which HEAD has no producer for |

INPC (`configs/inpc_anual.yaml`) and the 2020 population (`configs/equity_mark_scales.yaml`) live in configs. The SIE token stays in the git-ignored `.env` (`SIEBANXICO_TOKEN`); the live SIE and Yahoo download paths were exercised through the two `network` tests, never against the caches.

## 2. Environment

The old `climateCCR` env on the Linux machine was a July pip build (PyPI numpy on scipy-openblas 0.3.31, pandas 3.0.3, black 26.5.1) — renamed `climateCCR_pip_20260707` and replaced by `mamba env create -n climateCCR -f conda-lock.yml` (mamba 2.8 reads the unified lockfile; same package set as `conda-lock install`), then `pip install -e . --no-deps`; `conda list --explicit` equals the lockfile's linux-64 block. One pin had to change: the seven CNSF agro years 2008–2014 are `.xls`, unreadable without `xlrd`, so `xlrd` joined `environment.yml` / the `haz` extra and the lockfile was re-solved with `conda-lock lock --update xlrd` (conda-lock now in the base env) — every numerics package identical on the three platforms, only transitive dev builds refreshed.

## 3. Code changes the landing forced (commits `b179938`, `4408e70`, `b5a587d`, `c2af247`, `f16080e`)

Sort-tie order is CPU-architecture dependent: numpy 2.x sorts numeric keys with x86-simd-sort on x86-64 and introsort on arm64, and pandas' single-key `sort_values` / `value_counts` inherit it. Every such sort whose order reaches an artifact now uses `kind="stable"` on a deterministic input order (`pipelines/10/11/12/13/14`, `data.inspeccion`, `viz.ccr`). One reported number moved: the `pipelines/13` tercile spread, $0.00431 \to 0.00449$ log-return, because five names tie at the bottom cut and three at the top (τ, p and the FALLA verdict unchanged). Directory globs in the sequía scripts and the alias tie-break of `explorar_xlsx_cnsf` are sorted; `save_figure` drops the PDF `CreationDate` so an identical figure gives identical bytes; `set_seed` no longer sets `PYTHONHASHSEED` at runtime (a no-op for the running interpreter — the driver exports it for child processes).

## 4. The regeneration (`tools/reproduce_all.sh`, from raw, one background run)

Stages and wall-clock on this machine with `--jobs 4`, `OPENBLAS_NUM_THREADS=2`: preflight + CENAPRED processing seconds; CNSF hidro consolidation 8 min (openpyxl over 17 workbooks), agro 10 s + corrector 3 s; HAZ calibration + tiers A/B 30 s; market calibration 1 min; book roots, scales, event study seconds, tier C 3.6 min; the 33 direct simulation cells 65 min of CPU (≈ 78 s per joint Mexican cell, 4 at a time → ≈ 20 min; the two daily-grid fixture demos 15 min each); the five studies concurrently 33 min (seed studies 32 + 33 min, S-tier 18, tier E 10, storm-cluster 4); readouts ≈ 15 min. Chain total ≈ 2 h 20 min unattended.

## 5. What reproduces, and how closely

The comparison is `tools/compare_results.py` (differences relative to each column's scale; tied rows order-insensitively; figures by existence) plus the 64 canon cells of `tools/headlines.yaml` at the canon's reported precision. Byte identity across CPU architectures was never on the table (`GEN-37`): the PIMPA goldens pass at rtol 1e-9 but differ at $\le 10^{-13}$ relative, from OpenBLAS kernels, libm and FMA differences, not the OS.

Full-tree comparison of `results/` (1,593 files, manifests and logs aside): **939 identical, 317 within tolerance, 2 order-only, 23 "differs" (every one accounted for in §6), 14 text differences (absolute paths in generated configs, the invoking command in `resumen.md`, one float at the 17th digit in two NGFS fragments, the tercile spread), 180 figures regenerated (bytes not compared), 7 + 11 files present on one side only (stale figure leftovers, two base-config runs the Mac never kept).**

| Artifact family | Result on Linux x86-64 vs the macOS/arm64 reference |
|---|---|
| CENAPRED consolidados (both directories), CNSF agro consolidados + corrected copies, CNSF hidro on the 2008–2024 set | byte-identical (hidro: value-identical; only the gzip header stamp differs) |
| HAZ fits, loss→mark scale ($\beta$, $K$, $K_{\text{eff}}$), tiers A and B, equity scales and peril severities for both books, $\sum w\gamma$ = 0.2414, S-tier variant bands, storm-cluster, NGFS overlays and fragments | identical, or $\le 3\times10^{-14}$ where an optimiser is involved |
| Market calibration | `nelson_siegel`, `theta_grid`, `direct_input` within $9\times10^{-7}$ — the Nelder–Mead $a$ reproduces to seven digits; `hw1f_by_window.csv` MLE rows $\le 10^{-5}$, AR(1) rows identical |
| Book roots (`ccr_book_mx`, `ccr_book_cmp`, the NGFS overlays, the three dated tier-E roots) | identical or $\le 9\times10^{-7}$ (the $a$ propagation) |
| The 33 direct and 87 spawned simulation cells (EE/PE frames, per-path npz) | $\le 10^{-8}$ of the column scale (EE cells move $\le 6\times10^{-4}$ MXN on a $2\times10^{5}$ scale); BOOK EPE baseline 255,735.47 MXN and shift $-8.9965\,\%$ equal to four decimals, control book $-3.4953\,\%$, HWTP jump-within $-9.2619\,\%$ |
| Readouts: the three NGFS flavours, EPE / EEPE summaries, both seed studies, book comparison, CVA, aggregate loss, tier-E scoring | $\le 4\times10^{-7}$; seed-study canonical values and spreads equal to four decimals (1y q99 3,041,356 on both machines) |
| Tier C (29,732 forecasts with pre-date refits) | PIT max abs $8\times10^{-5}$, one of 1,080 coverage cells moved by one forecast, Berkowitz 260.039 → 260.044 — below reported precision |

**Headline cells: 63 of 64 reproduce at the canon's reported precision.** The 64th, `S_rate_eff_MX`, regenerates as 175,293,835 against the canon's 175,293,784 MDP-2025 — $2.9\times10^{-7}$ relative, the $a$ tolerance through the loading $L(a)$: the canon quotes nine digits of a number stable to seven; quote it as 175.29 M MDP-2025. The regenerated manifests carry `platform` Linux, `blas` `libblas 11_h4a7cf45_openblas`, python 3.11.15, numpy 2.4.6, pandas 3.0.6 — the `GEN-30/37` tripwire reads as designed; the 23 macOS-stamped manifests are the carried-over archives.

## 6. Findings that are not reproduction failures

1. **A pending data refresh.** `datos_CNSF/crudos/riesgos_hidrometereologicos/` holds a `2025 Hidro Bases.xlsx` scraped on 2026-09-29 that the stored consolidado (2026-06-04) never saw; a from-raw consolidation adds 95,730 / 366,066 / 11,308 rows to emisión / suma asegurada / siniestros. No stored number can move — every consumer windows the years to 2024 (`loss_to_mark_scale.yaml` `k_year: 2024`, `equity_mark_scales.yaml` `end_year: 2024`) — so the consolidado was re-run on the 2008–2024 file set to land the Mac's vintage; adopting 2025 is a `GEN-31` living-calibration decision, to be taken deliberately with a re-base.
2. **Stale artifacts in the reference tree** (idempotent pipelines never delete what an earlier code state wrote): `results/climate_jump_demo*` and `climate_jump_real{,_ct_anchor,_floor}` are July vintages of the pre-correction engine (EE 141 vs 41 on the IRS counterparty); the S-tier jitter tables (`s_tier_jitter_*.csv`, 2026-10-08) predate the 14 control-book sectors added on 2026-10-12 — the jitter loop draws one tier step per sector in config order, so the extra sectors shift the random stream after the first draw (τ mean $0.897 \to 0.896$, conclusion unchanged); `figures/model_vs_observed/fan_ftiie_holdout*` (2026-08-07) were superseded by the conditional fan; a `VM_1_terms.csv` for control-book NAID 324 survives from a first build two minutes before the final one; agro `.csv.gz` twins and an `Archive.zip`.
3. **Metric amplification, not drift.** `hw1f_by_window.csv` shows up to 5 % "relative" difference only in `alpha_rel_diff_vs_ar1`, a difference of two near-equal numbers ($-7.9\times10^{-6}$ vs $-7.5\times10^{-6}$); the Nelder–Mead MLE fits themselves move $\le 10^{-5}$ relative on a likelihood flat in $a$, the AR(1) rows are identical, and the headline $a$ reproduces to seven digits.

## 7. Backlog surfaced (to `OPEN_QUESTIONS` through `/digest`)

`pipelines/11` jitter draws should not depend on sectors outside the book (substream per sector name, or draw over the book's sectors only); `pipelines/09` should remove stale per-NAID files on rebuild (or fail loudly) and should not re-stamp `_procedencia.json`'s `descargado_utc` when every series came from the cache; the stale `--aliases src/aliases_cnsf.json` default in `consolidar_cnsf.py` / `scraper_cnsf.py`; the `--generar` flag documented in `configs/static_book_backtest.yaml` that `pipelines/31` does not accept; `tests/data/hazard_mx/cnsf/test_orquestacion_cnsf.py` hard-codes `/home/claude`; `configs/pimpa_fixture.yaml` spells `backtesting_Data` (dormant key; case-sensitive filesystems); 47 `read_text()` / 29 `write_text()` calls without `encoding` (guarded by `PYTHONUTF8=1` in the driver); the two canon cells whose rounding did not match their own artifact (EEPE seed sd "0.02" is 0.01; FIX 1W coverage ".88" is 0.87).

## Related
Reads with: [[WORKFLOW]] (§4 reproducibility) · [[DECISIONS]] (`GEN-30`, `GEN-37`, `GEN-38`, `CCR-SIM-02/03`) · [[ngfs_application_flavors]] (the run matrix the driver encodes) · [[CCR_MOC]] · [[MKT_MOC]] · [[HAZ_MOC]]. Home: [[_INDEX]]
#arm/int #type/pipeline
