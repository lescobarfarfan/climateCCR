# ASSET_MAP — Migration map (origin → integrated repo)

Where every existing note, script, and config from the three origin projects lands in
`climateCCR`. Use it to migrate deliberately, committing **moves separately from behaviour
changes** (`GEN-09`). Spanish filenames are kept **verbatim** (they are real artifacts).

**Status legend:** `MOVE` (relocate ~as-is) · `MOVE+FIX` (relocate + a known minimal fix) ·
`PORT` (Spanish/standalone code adopted into the package; keep behaviour, wrap APIs per `INT-07`) ·
`NEW` (does not exist yet; to build) · `REF` (reference doc; lands in `notes/` or `literature/`).

---

## 1. CCR arm — `Tesis QF` / `climateCCR` (the spine)

### Package scaffold & infra (already exists)

| Origin | Destination | Status | Notes |
|---|---|---|---|
| `pyproject.toml` (name `climateCCR`) (DONE) | `pyproject.toml` | MOVE | keep `name = "climateCCR"` (`INT-02`); py≥3.10; numpy/pandas≥2.0/scipy/sklearn/matplotlib/pyyaml/dateutil; dev: pytest/black/ruff/pre-commit/mypy; line-length 100. |
| `environment.yml` (DONE) | `environment.yml` | MOVE | conda python=3.11; `pip install -e ".[dev]"`. |
| `configs/default.yaml` (DONE) | `configs/default.yaml` | MOVE | seed 233423, n_paths 10000. |
| `.gitignore` (DONE) | `.gitignore` | MOVE | `notes/` tracked; `data/`,`results/` ignored. |
| `.pre-commit-config.yaml` (DONE) | `.pre-commit-config.yaml` | MOVE | ruff + black. |
| `src/climateCCR/infra/` (set_seed/get_rng, Config, logging, RunManifest, ProjectPaths) (DONE) | `src/climateCCR/infra/` | MOVE | ✅ built & tested; carries over as-is (name kept). |
| `src/climateCCR/{data,processes,calibration,simulation,signatures,inference,risk,viz}/__init__.py` (placeholders) (DONE) | `src/climateCCR/<same>/` | MOVE | empty subpackages → fill per arm below. |

### PIMPA engine & randomized signature (migrate in)

| Origin | Destination | Status | Notes |
|---|---|---|---|
| PIMPA engine (`CCR_Valuation_Session`, EE/PE, netting, collateral; `calibration_method='direct_input'`) | `src/climateCCR/risk/ccr/` | MOVE+FIX | `iteritems()`→`.items()` (4 sites); drop `from calendar import calendar`; behaviour-unchanged first (`CCR-MIG-01/02`). Add EPE/Effective-EPE/CVA after (`OQ-CCR-04`). |
| PIMPA `RiskFactor`/`MultiRiskFactorSimulation`/`RiskFactorEvolution` | `src/climateCCR/{processes,simulation}/` | MOVE+FIX | path-major arrays; define `simulate_random_increments` (`CODE_REVIEW` C4); add event-injection hook (`DC-CCR-SIM-1`). |
| PIMPA `global_parameters.py` (mutable dict) | `configs/*.yaml` + `infra.Config` | PORT | config-over-hard-coding (`CCR-ARCH-04`). |
| PIMPA prototype parameter CSVs | `tests/fixtures/` | MOVE | the EE/PE regression fixture (`CCR-MIG-03`, `OQ-CCR-06`). |
| Randomized-signature prototype (Compagnoni 2023) | `src/climateCCR/{signatures,inference}/` | MOVE+FIX | seed the reservoir; fix solver `z0,A,b` fixed between fit/predict (`CODE_REVIEW` C1–C5; `CCR-SIG-02/03`). |

### CCR notes & literature

| Origin | Destination | Status | Notes |
|---|---|---|---|
| `README.md` (project map) | folded into `README.md` + `context/00_README_CONTEXT.md` | REF | — |
| `PROJECT_PLAN.md`, `PHASE_0.md` | `notes/plan/` | REF | timeline + Phase-0 migration plan (`CCR-RES-02`). |
| `CODE_REVIEW.md` (PIMPA + rand-sig findings) | `notes/reviews/CODE_REVIEW.md` | REF | C1–C5 bugs; the fix checklist for the signature port. |
| `DECISIONS / DATA_CONTRACTS / GLOSSARY / OPEN_QUESTIONS` (CCR) | merged into `context/*` | REF | re-namespaced `CCR-*`. |
| Compagnoni 2023 PDF + any `marker` output | `literature/Compagnoni_2023_RandomizedSignatures/` | REF | keep full folder; `.md` to project knowledge (`CCR-LIT-02`). |

---

## 2. MKT arm — `financial_instruments` (feeds the spine)

### Theory & methodology notes → `notes/theory/`

| Origin file(s) | Destination | Status | Notes |
|---|---|---|---|
| `Hull_White_Comprehensive.md` (753) + 7 more HW notes (`HWModel_Theory.md`, `Calibration_From_SIE_Banxico_01/02.md`, …) | `notes/theory/hull_white/` | REF | the calibration design behind `calibration/financial`. |
| `Vasicek_Calibracion_Mex.md` | `notes/theory/` | REF | estimation device for `a, σ`. |
| `ChangeOfMeasureInFinance.md` | `notes/theory/` | REF | Q↔P, λ (`MKT-MEAS-*`). |
| `instrumentos_deuda_mexico.md` (1388) | `notes/theory/` | REF | Bonos M / Cetes / Udibonos conventions. |
| `mexican_data_sources.md` (1020) | `notes/sources/` | REF | SIE series catalog → `data/market`. |
| `mexican_yield_curve_methodology.md` | `notes/theory/` | REF | stripping/interpolation (`MKT-CURVE-*`). |
| `monte_carlo_*.md` | `notes/theory/` | REF | variance reduction (`MKT-MC-01`). |
| `ngfs_*.md`, `how_to_use_NGFS_PolicyRate.md` | `notes/theory/` + `notes/sources/` | REF | shock translation (`MKT-NGFS-*`). |
| `dashboard_riesgo_excel.md` | `notes/pipelines/` | REF | dashboard schema (`DC-MKT-PHYS-*`). |
| `climate_*_bonds/countries/credit.md` | `notes/theory/` | REF | credit overlay (`MKT-CREDIT-01`). |
| `referencias_weather_derivatives.md` | `notes/theory/` | REF | WD reading list (`MKT-WD-01`). |

### Code, data & literature

| Origin | Destination | Status | Notes |
|---|---|---|---|
| HW/Vasicek/GBM calibration code; curve strip (Goal-Seek/linear-in-z) | `src/climateCCR/calibration/financial/` | NEW/PORT | must emit `'direct_input'` objects (`DC-CCR-CAL-1`); most is in notes, code to write. |
| VaR/ES + stress shocks (parallel/non-parallel/vol/mean-reversion) | `src/climateCCR/risk/market/` | NEW | recalibrate θ on every curve shock (`MKT-STRESS-01`). |
| NGFS Δr application + θ* recalibration | `src/climateCCR/scenarios/` | NEW | (`MKT-NGFS-02`). |
| `src/Actualiza_FTIIE.R` (208) | `pipelines/` or `data/market/` | PORT | F-TIIE refresh; R utility — keep or reimplement in Python. |
| Excel physical-risk dashboard | `notebooks/` + `notes/pipelines/dashboard_riesgo_excel.md` | MOVE | Excel-native deliverable; not a sim engine (`MKT-PHYS-03`). |
| `technical_analysis/climate_investment_analysis.tex` (1220), `climate_integrated_investment_analysis.md` | `literature/` (writeup) | REF | the thesis-writeup draft. |
| `technical_analysis/climate_investment_refs.bib` (47 entries) | `literature/refs.bib` | MOVE | authoritative climate-finance BibTeX (`REFERENCES.md` §6/§9). |

> **MKT caveat:** the Investing.com curve guide is **superseded** by the SIE/CF300 approach
> (`MKT-SIE-01`); migrate the SIE methodology, not the Investing.com one.

---

## 3. HAZ arm — `Climate-Nature-Risks_Calibration` (feeds the spine)

### Pipeline code → `src/climateCCR/data/hazard_mx/`

| Origin script (lines) | Destination | Status | Notes |
|---|---|---|---|
| `scraper_cnsf.py` (951) | `data/hazard_mx/cnsf/` | PORT | orchestrator `--modo sync/verificar/descargar/consolidar`. |
| `consolidar_cnsf.py` (546) | `data/hazard_mx/cnsf/` | PORT | xlsx sector consolidation; `CORRECCIONES_CANONICAS`. |
| `procesar_autos_cnsf.py` (428) | `data/hazard_mx/cnsf/` | PORT | autos `.mdb`→3 CSVs; exclude 2007. |
| `limpieza_cnsf.py` (275) | `data/hazard_mx/cnsf/` | PORT | `clasificar_entidad`, `filtrar_para_calibracion` (shared cleaner — also used by CENAPRED). |
| `explorar_xlsx_cnsf.py` (201), `procesar_captura_extensos.py` (177) | `data/hazard_mx/cnsf/` | PORT | exploration/long-capture helpers. |
| `extraccion_catalogos_cnsf.R` (189), `explorar_mdb_cnsf.sh` (153) | `data/hazard_mx/cnsf/` | PORT | catalog extraction (R) + MDB exploration (shell). |
| `aliases_cnsf.json`, `catalogos_autos_cnsf.json` | `data/hazard_mx/cnsf/config/` | MOVE | alias/catalog maps (`--aliases` must be passed — `HAZ-SCRAPER-CNSF-06`). |
| `descarga_ibtracs.py` (97), `procesar_ibtracs.py` (223) | `data/hazard_mx/ibtracs/` | PORT | v04r01 EP+NA; covariate panel. |
| `campo_viento.py` (267) | `data/hazard_mx/ibtracs/` | PORT | Holland (Vmax-anchored) + K&D decay + wind-field thresholds (`HAZ-IBTRACS-04/05`). |
| `descarga_cenapred.py` (346), `procesar_cenapred.py` (467) | `data/hazard_mx/cenapred/` | PORT | A/B/A′ + catalog outputs (`DC-HAZ-CENAPRED-2`). |
| `scraper_sequia.py` (644), `indices_sequia.py` (209), `agregacion_sequia.py` (119), `validacion_sequia.py` (99), `config_sequia.py` (115) | `data/hazard_mx/sequia/` | PORT | SPEI primary; idempotent CDS downloads (`HAZ-DROUGHT-*`). |

### HAZ notes → `notes/`

| Origin doc (lines) | Destination | Status | Notes |
|---|---|---|---|
| `referencias_riesgo_catastrofico.md` (262) | `notes/theory/` | REF | **master** catastrophe-risk theory doc (peril taxonomy, source tiers, stochastic framing). |
| `diseno_calibracion_funciones_impacto_mexico.md` (424) | `notes/theory/` | REF | CLIMADA subnational design (`HAZ-CLIMADA-*`). → `src/climateCCR/calibration/impact/`. |
| `cenapred.md`, `ibtracs.md` | `notes/sources/` | REF | per-source provenance. |
| `README_scraper_cnsf.md` (437), `README_sequia.md` (382), `DISENO_pipeline_autos_CNSF.md`, `Guia_MDB_Automoviles_CNSF.md` | `notes/pipelines/` | REF | pipeline how-to/design. |
| `00_README_CONTEXT / README / DECISIONS / DATA_CONTRACTS / GLOSSARY / REFERENCES / OPEN_QUESTIONS` (HAZ) | merged into `context/*` | REF | legacy IDs preserved, arm-prefixed `HAZ-*`. |

### HAZ new work → `src/climateCCR/`

| What | Destination | Status | Notes |
|---|---|---|---|
| CLIMADA subnational impact-function calibration (v_half, LitPop, PyMC partial pooling) | `calibration/impact/` | NEW | design exists in notes; code to build (`HAZ-CLIMADA-*`). |
| Compound-Poisson / Cox loss model + parametric pricing | `risk/loss/` | NEW | tail from CENAPRED (`HAZ-STOCH-*`, `OQ-HAZ-12/13`). |

---

## 4. Cross-cutting & integration assets

| Origin | Destination | Status | Notes |
|---|---|---|---|
| Root `END_OF_CHAT_RITUAL.md` | folded into `context/WORKFLOW.md` | REF | the ritual + reproducibility/version-control standard. |
| HAZ `_procedencia.json` convention | every `data/raw/**` artifact | MOVE | raw-data provenance (`GEN-02`, `INT-08`). |
| CCR `RunManifest` | `results/manifests/<run_id>.json` | MOVE | run provenance (`GEN-06`, `INT-08`). |
| `limpieza_cnsf.clasificar_entidad` (HAZ) | shared by CNSF **and** CENAPRED cleaners | PORT | one entity standard project-wide (`DC-CONV-5`). |
| Banxico FX (MKT/SIE) ↔ CNSF `MONEDA` | wire `data.market` → `data.hazard_mx.cnsf` | NEW | closes `OQ-HAZ-03` (`DC-XWALK-5`). |
| CENAPRED `nombre_evento` ↔ IBTrACS `SID` | crosswalk util feeding `calibration/impact` | NEW | the `v_half` calibration input (`DC-XWALK-1`). |

---

## 5. Migration order (recommended)

1. **Scaffold** — copy CCR scaffold + `infra` (keep the name `climateCCR`); green `infra` tests.
2. **Canon** — drop `context/` in; commit. (Now every later decision has a home.)
3. **PIMPA** — `MOVE+FIX` behaviour-unchanged; lock the EE/PE regression fixture. *(separate commits)*
4. **HAZ pipelines** — `PORT` the mature scripts under `data/hazard_mx/` (they already run); wire the shared entity cleaner.
5. **Signatures** — `MOVE+FIX` per `CODE_REVIEW`; seed the reservoir; fix the solver contract.
6. **Calibration** — build `calibration/financial` (emit `'direct_input'`) then `calibration/impact` (CLIMADA).
7. **Risk extensions** — EPE/CVA in `risk/ccr`; VaR/ES in `risk/market`; loss models in `risk/loss`.
8. **Scenarios & cross-arm wire** — NGFS Δr→θ*; then specify the HAZ→financial-risk wire (`OQ-INT-07`).

> Each step is a small, reviewable set of commits. Behaviour changes never share a commit with a
> move/rename (`GEN-09`). After each working chat, run the end-of-chat ritual (`context/WORKFLOW.md`).


---

## Related
Reads with: [[REPO_STRUCTURE]] (the destination tree) · [[README]] · [[WORKFLOW]] (commit discipline). By arm: [[CCR_MOC]] · [[MKT_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]
#type/workflow
