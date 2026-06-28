# CONSOLIDATION_PLAN — where every uploaded file lands in `climateCCR`

This resolves the four uploaded archives into the single `climateCCR` repo, following the
authoritative migration docs (`REPO_STRUCTURE.md` for the target tree, `ASSET_MAP.md` for the
origin→destination map) and reconciling them against **what is actually in the uploads**. Spanish
filenames are kept **verbatim** (`INT-07`). Commit moves separately from behaviour changes (`GEN-09`).

**Status legend:** `MOVE` (relocate ~as-is) · `MOVE+FIX` (relocate + a known minimal fix) ·
`PORT` (Spanish/standalone code adopted into the package; behaviour kept, APIs wrapped per `INT-07`) ·
`NEW` (build) · `REF` (reference doc → `notes/`/`literature/`) · `ARCHIVE` (superseded/duplicate;
keep out of the way or drop) · `DROP` (cruft; do not migrate).

---

## 0. Target tree (authoritative — from `REPO_STRUCTURE.md`)

Directory trees stay plain code blocks (`GEN-14`).

```text
climateCCR/
├── pyproject.toml · environment.yml · .pre-commit-config.yaml · .gitignore
├── CLAUDE.md                      # NEW (Claude Code; this package)
├── README.md                      # ← integrated_knowledge_base/README.md
├── REPO_STRUCTURE.md · ASSET_MAP.md · OBSIDIAN_SETUP.md
├── _INDEX.md · CCR_MOC.md · MKT_MOC.md · HAZ_MOC.md      # vault hubs (root)
├── .claude/                       # NEW (Claude Code; this package)
│   ├── settings.json · commands/ · rules/
├── context/                       # the 7-file canon
│   └── 00_README_CONTEXT.md · DECISIONS.md · DATA_CONTRACTS.md · GLOSSARY.md
│       REFERENCES.md · OPEN_QUESTIONS.md · WORKFLOW.md
├── notes/                         # tracked prose
│   ├── theory/   (+ theory/hull_white/) · sources/ · pipelines/ · plan/ · reviews/
├── literature/                    # marker folders + refs.bib
├── configs/                       # default.yaml (seed 233423, n_paths 10000)
├── data/                          # GIT-IGNORED · raw/{market,scenarios,hazard_mx} · interim · processed
├── results/                       # GIT-IGNORED · manifests · figures · logs
├── notebooks/ · pipelines/
├── tests/                         # fixtures/ · infra/ · risk_ccr/ · hazard_mx/
└── src/climateCCR/
    ├── infra/ ✅  · data/{market,scenarios,hazard_mx} · processes/{diffusions,jumps}
    ├── calibration/{financial,impact} · signatures/ · inference/ · simulation/
    ├── scenarios/ · risk/{ccr,market,loss} · viz/
```

---

## 1. `integrated_knowledge_base.zip` → repo root + `context/`

This archive **is** the consolidated canon + vault. Drop its contents straight in.

| Origin | Destination | Status |
|---|---|---|
| `context/` (7 canon files) | `context/` | MOVE (authoritative; these supersede every origin `recommended_files/` set) |
| `README.md` | `README.md` (repo root) | MOVE (replaces the CCR scaffold's old 20 KB README) |
| `REPO_STRUCTURE.md`, `ASSET_MAP.md`, `OBSIDIAN_SETUP.md` | repo root | MOVE |
| `_INDEX.md`, `CCR_MOC.md`, `MKT_MOC.md`, `HAZ_MOC.md` | repo root (vault hubs) | MOVE |
| `.gitignore` | merge with the scaffold's `.gitignore` | MOVE+FIX (keep the union; both track `notes/`, ignore `data/`,`results/`) |

---

## 2. `climateCCR.zip` → the spine (carry the scaffold; reorganize notes)

The scaffold is pre-integration but the **`infra` layer is built and tested** — it carries over
unchanged. Only the `notes/` need reorganizing into the `notes/{plan,reviews}` subfolders.

### Scaffold & package (carry over as-is)

| Origin | Destination | Status |
|---|---|---|
| `pyproject.toml`, `environment.yml`, `.pre-commit-config.yaml`, `configs/default.yaml` | same paths | MOVE (update the `description` to the integrated objective; keep `name = "climateCCR"`, `INT-02`) |
| `.gitignore` | merge with the canon's `.gitignore` | MOVE+FIX |
| `src/climateCCR/infra/` (config, logging_utils, manifest, paths, reproducibility) | `src/climateCCR/infra/` | MOVE (✅ built & tested) |
| `src/climateCCR/{data,processes,calibration,simulation,signatures,inference,risk,viz}/__init__.py` | same | MOVE (placeholders → fill per arm) — **add** `scenarios/`, and the sub-packages `data/{market,scenarios,hazard_mx}`, `processes/{diffusions,jumps}`, `calibration/{financial,impact}`, `risk/{ccr,market,loss}` |
| `pipelines/00_smoke_test.py` | `pipelines/` | MOVE |
| `tests/test_infra.py` | `tests/infra/test_infra.py` | MOVE |
| `data/{raw,interim,processed}/.gitkeep`, `notebooks/.gitkeep` | same | MOVE |

### Notes reorg (per `ASSET_MAP.md` §1)

| Origin | Destination | Status |
|---|---|---|
| `notes/PROJECT_PLAN.md` | `notes/plan/PROJECT_PLAN.md` | MOVE (REF) |
| `notes/phases/PHASE_0.md` | `notes/plan/PHASE_0.md` | MOVE (REF) |
| `notes/CODE_REVIEW.md` | `notes/reviews/CODE_REVIEW.md` | MOVE (REF) — C1–C5 signature-fix checklist |

### Do not migrate

| Origin | Status |
|---|---|
| `README.md` (old 20 KB CCR scaffold map) | ARCHIVE (folded into the integrated `README.md` + `context/00_README_CONTEXT.md`) |
| `src/climateCCR.egg-info/`, `.pytest_cache/`, `__pycache__/` | DROP (regenerated on install/run) |
| `results/manifests/*.json`, `results/logs/*.log` | DROP from git (`results/` is ignored; keep locally if useful) |
| `.vscode/settings.json` | optional — you're Neovim-first; drop or keep for occasional VS Code use |
| `.git/` | DROP (re-init the consolidated repo fresh, or keep this one as the base — your choice) |

---

## 3. `financial_instruments.zip` → MKT arm

### Theory notes → `notes/theory/` (and `notes/theory/hull_white/`)

| Origin | Destination | Status |
|---|---|---|
| `hull_white_1f/` ×8 (`Hull_White_Comprehensive.md`, `HWModel_Theory.md`, `Hull-White-1F-calibration.md`, `Hull‑White_theta_Intuition.md`, `Calibration_From_SIE_Banxico_01.md`, `Calibration_From_SIE_Banxico_02.md`, `market_calibration.md`, `all_info.md`) | `notes/theory/hull_white/` | REF |
| `vasicek/Vasicek_Calibracion_Mex.md` | `notes/theory/` | REF |
| `general_notes/ChangeOfMeasureInFinance.md` | `notes/theory/` | REF |
| `general_notes/instrumentos_deuda_mexico.md` | `notes/theory/` | REF |
| `general_notes/mexican_yield_curve_methodology.md` | `notes/theory/` | REF |
| `general_notes/monte_carlo_risk_management_framework.md`, `monte_carlo_climate_risk_applications.md` | `notes/theory/` | REF |
| `general_notes/ngfs_short_term_scenarios_summary.md`, `how_to_use_NGFS_PolicyRate.md` | `notes/theory/` | REF |
| `general_notes/climate_risk_credit_methodology_references.md`, `climate_risk_data_requirements_bonds.md`, `climate_exposed_countries.md` | `notes/theory/` | REF |
| `general_notes/referencias_weather_derivatives.md` | `notes/theory/` | REF |

### Sources / pipelines / literature

| Origin | Destination | Status |
|---|---|---|
| `general_notes/mexican_data_sources.md` | `notes/sources/` | REF |
| `general_notes/dashboard_riesgo_excel.md` | `notes/pipelines/` | REF (`DC-MKT-PHYS-*`) |
| `technical_analysis/climate_integrated_investment_analysis.md` | `literature/` | REF (thesis-writeup draft) |
| `technical_analysis/climate_investment_analysis.tex` | `literature/` | REF |
| `technical_analysis/climate_investment_refs.bib` | `literature/refs.bib` | MOVE (authoritative 47-entry BibTeX) |
| `src/Actualiza_FTIIE.R` | `pipelines/` (or `src/climateCCR/data/market/`) | PORT (F-TIIE refresh; keep R or reimplement) |

### Do not migrate

| Origin | Status |
|---|---|
| `recommended_files/` (`00_PROJECT_CONTEXT`, `01_DECISIONS`, `02_DATA_CONTRACTS`, `03_GLOSSARY`, `04_OPEN_QUESTIONS`) | ARCHIVE — already merged into `context/*`, re-namespaced `MKT-*` |

> **MKT caveat (`ASSET_MAP`):** the Investing.com curve guide is **superseded** by the SIE/CF300
> approach (`MKT-SIE-01`). Migrate the SIE methodology, not the Investing.com one.

### To build (`NEW`)

`calibration/financial/` (HW/Vasicek/GBM estimators + curve strip → must emit `'direct_input'`
objects, `DC-CCR-CAL-1`) · `risk/market/` (VaR/ES, stress shocks) · `scenarios/` (NGFS Δr → θ*).

---

## 4. `Climate-Nature-Risks_Calibration.zip` → HAZ arm

### Pipeline code → `src/climateCCR/data/hazard_mx/<source>/` (all `PORT`; they already run)

| Origin (`src/`) | Destination |
|---|---|
| `scraper_cnsf.py`, `consolidar_cnsf.py`, `procesar_autos_cnsf.py`, `limpieza_cnsf.py`, `procesar_captura_extensos.py`, `extraccion_catalogos_cnsf.R`, `explorar_mdb_cnsf.sh` | `data/hazard_mx/cnsf/` |
| `catalogos_autos_cnsf.json` | `data/hazard_mx/cnsf/config/` |
| `descarga_ibtracs.py`, `procesar_ibtracs.py` | `data/hazard_mx/ibtracs/` |
| `procesar_cenapred.py` | `data/hazard_mx/cenapred/` |
| `scraper_sequia.py`, `indices_sequia.py`, `config_sequia.py`, `validacion_sequia.py` | `data/hazard_mx/sequia/` |

> **`limpieza_cnsf.clasificar_entidad`** is the **shared** entity cleaner — also used by CENAPRED
> (`DC-CONV-5`). Keep it importable by both `cnsf/` and `cenapred/`.

### Notes → `notes/`

| Origin (`notas/`) | Destination | Status |
|---|---|---|
| `referencias_riesgo_catastrofico.md` | `notes/theory/` | REF (**master** catastrophe-risk doc) |
| `diseno_calibracion_funciones_impacto_mexico.md` | `notes/theory/` | REF (CLIMADA subnational design) |
| `cenapred.md`, `ibtracs.md` | `notes/sources/` | REF (provenance) |
| `urls_cenapres_impactos_socio.txt` | `notes/sources/` | REF (CENAPRED source URLs) |
| `README_scraper_cnsf.md`, `README_sequia.md`, `DISENO_pipeline_autos_CNSF.md`, `Guia_MDB_Automoviles_CNSF.md` | `notes/pipelines/` | REF |
| `requirements_sequia.txt` | `notes/pipelines/` (or fold into `pyproject` extras) | REF |

### Tests & fixtures → `tests/`

| Origin (`scraps/`) | Destination | Status |
|---|---|---|
| `test_consolidar_cnsf.py`, `test_procesar_autos_cnsf.py`, `test_scraper_cnsf.py`, `test_orquestacion_cnsf.py` | `tests/hazard_mx/cnsf/` | MOVE |
| `catalogo_fenomenos_test.xlsx` | `tests/fixtures/` | MOVE |
| `plantillas/captura_extenso_PLANTILLA.csv` | `data/hazard_mx/cenapred/plantillas/` (template for `procesar_captura_extensos.py`) | MOVE |

### Do not migrate

| Origin | Status |
|---|---|
| `recommended_files/` (HAZ origin canon) | ARCHIVE — already merged into `context/*` as `HAZ-*` |
| `README.md` (128-byte stub) | ARCHIVE |
| `reporte_estructura.json` (89 KB auto-generated inventory) | DROP |
| `.Rhistory` | DROP |
| `scraps/prompt_scrapper_era5_conagua.txt` | DROP (or `notes/scraps/` if you want the prompt history) |
| `src/__pycache__/` | DROP |

### To build (`NEW`)

`calibration/impact/` (CLIMADA subnational impf: `v_half`, LitPop, PyMC partial pooling) ·
`risk/loss/` (compound-Poisson/Cox + parametric pricing; tail from CENAPRED).

---

## 5. Gaps — referenced in `ASSET_MAP.md` but **absent from this upload**

Confirm where these live before the HAZ port; the pipelines are incomplete without them:

| Missing file | Role | Why it matters |
|---|---|---|
| `campo_viento.py` (~267 ln) | Holland (Vmax-anchored) wind field + K&D decay + `celdas_ge34/64/96kt` | The wind-field attribution (`HAZ-IBTRACS-02/04/05`) — preferred over the buffer route |
| `descarga_cenapred.py` (~346 ln) | CENAPRED downloader (`sync/verificar/descargar`, `_procedencia.json`) | Feeds `procesar_cenapred.py` (`HAZ-CENAPRED-01`) |
| `agregacion_sequia.py` (~119 ln) | Drought state-aggregation step | Middle of the drought chain (`descargar→calcular→agregar→validar`) |
| `aliases_cnsf.json` | CNSF alias map (`--aliases`) | Omitting it lets processing proceed **incorrectly without warning** (`HAZ-SCRAPER-CNSF-06`) |
| `explorar_xlsx_cnsf.py` (~201 ln) | xlsx exploration helper | Listed in `ASSET_MAP`; optional |

These are likely on your machine (NOAA/CNSF downloads ran locally — sandbox was blocked). When you
set up the repo in Claude Code, the `/warmstart` recap should flag these; place them in the
`data/hazard_mx/{ibtracs,cenapred,sequia,cnsf}/` homes above.

---

## 6. Cross-arm wiring to build (`NEW`)

| Wire | Where | Contract |
|---|---|---|
| Banxico FX (MKT) → CNSF `MONEDA` normalization | `data.market` → `data.hazard_mx.cnsf` | `DC-XWALK-5` (closes `OQ-HAZ-03`) |
| CENAPRED `nombre_evento` → IBTrACS `SID` | crosswalk util → `calibration/impact` | `DC-XWALK-1` (the `v_half` calibration input) |
| HAZ `λ` + jump-mark → `processes.jumps` → `simulation` | the climate jump channel | `DC-CCR-SIM-2` / `DC-XWALK-4` (`INT-10`) |

---

## 7. Migration order (from `ASSET_MAP.md` §5 — each step = small, reviewable commits)

1. **Scaffold** — carry the CCR scaffold + `infra`; green `infra` tests.
2. **Canon + vault** — drop `context/` + the root docs/hubs in; commit. (Every later decision now has a home.)
3. **PIMPA** — `MOVE+FIX` behaviour-unchanged; lock the EE/PE regression fixture. *(separate commits)*
4. **HAZ pipelines** — `PORT` the mature scripts under `data/hazard_mx/`; wire the shared entity cleaner; locate the §5 gaps.
5. **Signatures** — `MOVE+FIX` per `CODE_REVIEW`; seed the reservoir; fix the solver contract.
6. **Calibration** — build `calibration/financial` (emit `'direct_input'`) then `calibration/impact` (CLIMADA).
7. **Risk extensions** — EPE/CVA in `risk/ccr`; VaR/ES in `risk/market`; loss models in `risk/loss`.
8. **Scenarios & cross-arm wire** — NGFS Δr→θ*; then specify the HAZ→financial-risk wire (`OQ-INT-07`).

---

## 8. Obsidian vault wiring

The vault hubs go at the **repo root** (`_INDEX.md`, `*_MOC.md`, `OBSIDIAN_SETUP.md`); open Obsidian
on the repo root. The MOCs already link to your theory notes **by filename** (e.g.
`[[Hull_White_Comprehensive]]`, `[[referencias_riesgo_catastrofico]]`,
`[[diseno_calibracion_funciones_impacto_mexico]]`). Until imported they appear as hollow nodes; when
you drop each note into `notes/{theory,sources,pipelines,...}/` **keeping the filename above**, the
matching MOC link lights up automatically (`OBSIDIAN_SETUP.md` §4). After the move, run `/link-check`
(see the guide) to confirm no broken links and full MOC coverage.

---

## Related
Reads with: [[REPO_STRUCTURE]] (target tree) · [[ASSET_MAP]] (origin→destination) · [[OBSIDIAN_SETUP]] (vault) · [[WORKFLOW]] (commit discipline). Home: [[_INDEX]]
#type/workflow #arm/int
