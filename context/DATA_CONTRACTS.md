# DATA_CONTRACTS — Integrated data contracts

What each module produces and consumes: name, grain, key columns, units, encoding, source of truth.
If a contract changes, **edit it here** (do not append) and log it in `DECISIONS.md`. IDs follow
`DC-<ARM>-<MODULE>-N`; cross-cutting conventions `DC-CONV-*`; joins between modules `DC-XWALK-*`.

**Status tags:** `FIRM` (decided / observed in code) · `PROPOSED` (recommended default, confirm in
`OPEN_QUESTIONS.md`) · `TBD` (genuinely unspecified).

## Table of contents
- `DC-CONV-*` — Cross-cutting conventions (shared)
- **CCR arm** — `DC-CCR-DATA`, `DC-CCR-CAL`, `DC-CCR-SIM`, `DC-CCR-SIG`, `DC-CCR-INF`, `DC-CCR-RISK`, `DC-CCR-MANIFEST`, `DC-CCR-LIT`
- **MKT arm** — `DC-MKT-SIE`, `DC-MKT-CURVE`, `DC-MKT-PHYS`, `DC-MKT-NGFS`, `DC-MKT-SSP`, `DC-MKT-CREDIT`
- **HAZ arm** — `DC-HAZ-CNSF`, `DC-HAZ-IBTRACS`, `DC-HAZ-CENAPRED`, `DC-HAZ-CLIMADA`, `DC-HAZ-DROUGHT`
- `DC-XWALK-*` — Crosswalks (joins between modules)

---

## DC-CONV — Cross-cutting conventions (shared)

- `DC-CONV-1` Repo layout: installable `src/climateCCR/…` package; pipeline scripts under the relevant `data/` sub-area; data under `data/<source>/{raw,interim,processed}` (HAZ legacy: `crudos`/`consolidados`). (See `../REPO_STRUCTURE.md`.)
- `DC-CONV-2` **Provenance (raw artifacts):** every raw artifact carries a provenance record (HAZ `_procedencia.json`) — URL/dataset, sha256, bytes, date; + version and DOI/request where applicable. `FIRM` (HAZ); `PROPOSED` project-wide.
- `DC-CONV-3` **Run manifest (experiments):** every stochastic run writes `results/manifests/<run_id>.json` — resolved config + git commit + seed + package versions + timestamps. `FIRM` (CCR `infra`).
- `DC-CONV-4` **Currency:** all amounts stored in **current MXN**; deflation (INEGI INPC) is a downstream step common to all monetary series. `FIRM`.
- `DC-CONV-5` **Canonical entity (geography):** 32 Mexican federal entities; names normalized by `limpieza_cnsf.clasificar_entidad`; unlocated/foreign excluded from the state panel. Municipal grain uses INEGI `clave_mpio` (5-digit). `FIRM`.
- `DC-CONV-6` **Canonical peril:** shared hazard taxonomy; cause/type → peril mapping in `mapa_perils_seguros_a_canonico.csv` and `mapa_canonico_a_fuentes.csv`. `FIRM` (HAZ).
- `DC-CONV-7` **Hazard ↔ impact join grain:** `estado × peril × año` (annual state panel). `FIRM`.
- `DC-CONV-8` **Encoding:** raw files may be latin1; canonical outputs are UTF-8. `.xlsx` views for Excel are disposable (not in git or the pipeline); the CSV is the source of truth. `FIRM`.
- `DC-CONV-9` **Tidy time-series schema (financial / scenario series):** one row per observation — `timestamp` (UTC), `series_id`, `field` (`close`/`adj_close`/`rate`/`fx`/`scenario_value`/…), `value` (float), `source`, `retrieved_at`. Source-agnostic; immutable raw cache in `data/raw/`. `PROPOSED` (CCR §1; confirm `OQ-CCR-02`).
- `DC-CONV-10` **Array layout:** **path-major** throughout — simulated paths are `(n_paths, n_steps, …)`; signature features `(n_paths, N, sig_level)`. `FIRM` (CCR/PIMPA).

---

## CCR arm — counterparty credit & narrative detection (the spine)

- `DC-CCR-DATA-1` **`data` → everything · tidy time-series.** As `DC-CONV-9`. Source-agnostic ingestion: market/price (Yahoo/Google Finance, public), rates/curves, climate & transition scenarios. Immutable `data/raw/`; provenance logged. `PROPOSED`. `TBD`: optional **wide** convenience view; curve tenor encoding.
- `DC-CCR-CAL-1` **`calibration` → `risk.ccr` · the `'direct_input'` contract.** *Load-bearing internal contract.* PIMPA performs no statistical calibration; it consumes pre-calibrated parameters via `calibration_method='direct_input'`. New estimators must return objects that path accepts so the engine stays untouched: `fit_gbm(...)` → GBM `drift` + `volatility` (constant or term-structure); `fit_hull_white(...)` → HW1F `alpha`, `sigma`, `theta(t)`/initial-curve fit. Consumed by the `RiskFactor` dataclass (name → evolution model). **These same knobs are exactly what Path B perturbs.** Loader now lives at `calibration.financial.market_data_builder` (`MarketDataBuilder`), fed config by `risk.ccr.config.build_global_parameters` (`CCR-MIG-05/06`). `FIRM`.
- `DC-CCR-SIM-1` **`processes`/`simulation` · array layout.** Path-major `(n_paths, n_steps, …)`. `MultiRiskFactorSimulation` draws **correlated** Gaussian increments (`scipy multivariate_normal`, seeded by `random_state`) and dispatches per risk factor to `RiskFactorEvolution` (BM/GBM/HW1F). `simulate_random_increments` must produce standard-normal increments `(n_paths, n_steps, dim)` (prototype referenced but never defined it — `CODE_REVIEW.md` C4). **Homes landed** (`CCR-MIG-05`, 2026-06-29): diffusions in `processes.diffusions`, orchestrator + `RiskFactor`/`CorrelationMatrix`/`SimulatedData` in `simulation`. **Seeding done** (`CCR-MIG-08`, 2026-06-29): the draw is seeded through `infra.get_legacy_rng(seed) -> RandomState`; SciPy builds a `RandomState` from an int seed, so this reproduces the int-seed stream bit-for-bit and the baseline is unchanged (`OQ-CCR-09` resolved via preserve-the-stream, `GEN-07`). **Event-injection hook (to add):** inject a calibrated climate-event component (Path A / jump) or perturbed parameters (Path B) without altering the core engine. `FIRM` + extension.
- `DC-CCR-SIM-2` **`processes.jumps` → `simulation` · climate jump-injection (the integrating contract, `INT-10`).** A climate-shock component superimposed on the diffusion. **Inputs (from HAZ `calibration.impact`):** arrival **intensity** `λ(t; covariates)` (homogeneous Poisson, or Cox / doubly-stochastic with covariate-driven `λ`); a **jump-mark / impact** distribution mapping each shock to a move in the target process (price-return jump for GBM, rate jump for HW1F). **Behaviour:** for each path, draw shock times from `λ`, draw marks, and add them to the diffusive increments at the matching steps — yielding a **jump-diffusion** `dX = (diffusion) + (Σ marks at Poisson/Cox times)`. **Knobs:** which target(s) a shock hits (price / rate / both); the diffusion↔jump dependence (independent vs correlated); fixed `λ` vs trajectory `λ(t)` (`INT-12`). **Output:** path arrays in the same path-major layout, consumed unchanged by `risk.*`. `PROPOSED` (mechanism specified; the open knobs are `OQ-INT-03/07`). `[ContTankov2004]`
- `DC-CCR-SIG-1` **`signatures` → `inference` · feature contract.** Canonical reservoir/feature array `(n_paths, N, sig_level)` (matches path-major). Expose a clean `fit`/`transform` API. Reservoir parameters `z0, A, b` are **fixed between fit and inference** and **seeded** (`CODE_REVIEW.md` C1, C3). `PROPOSED`.
- `DC-CCR-INF-1` **`inference` outputs · effect vs rule.** Emit exactly one of: **(Path A)** a *calibrated effect* (parameterised climate-event impact, consumable by the simulation event-injection hook); **(Path B)** a *justified perturbation rule* (documented mapping climate scenario → parameter shift, consumable by `calibration`/`simulation`). `TBD`: event-window/labelling spec and the leakage-aware CV split (most open-ended interface, RQ1).
- `DC-CCR-RISK-1` **`risk.ccr` (PIMPA) outputs · CCR metrics.** Currently: uncollateralised & collateralised **EE** profiles and **PE at quantiles** (default 99%), over a Basel default + close-out grid with MPOR, aggregated over netting sets with variation-margin collateral (thresholds + MTA). **Extensions:** EPE (time-average of EE) and Effective EPE (Basel running-max) — cheap on existing arrays; CVA — needs counterparty hazard-rate/survival curve, LGD, discounting. Open: in the evaluator or a thin `risk/ccr/xva.py`? (→ `OQ-CCR-04`). `FIRM` (current) + extensions.
- `DC-CCR-RISK-2` **PIMPA regression fixture + golden baseline.** Prototype portfolio under `tests/fixtures/pimpa/` (`RFs_attributes`, `calibration_data`, `market_data`, `portfolio_data`; data root resolved via `infra.ProjectPaths`, parameters from `configs/pimpa_fixture.yaml`, `CCR-MIG-06`). Golden at `tests/fixtures/pimpa/baselines/ee_pe_baseline.csv` — one block per `netting_agreement_id` over the B3 default grid: `default_times`, `uncollateralized_ee`, `uncollateralized_pe_0.99`, and `collateralized_ee`/`collateralized_pe_0.99` where a VM agreement exists (NaN otherwise). Reconstructed deterministically by `tests/risk_ccr/pimpa_baseline.py` (params via `infra.load_config` + `build_global_parameters`; seed 233423, n_paths 10000, `today_date=2020-01-01`); guarded by `tests/risk_ccr/test_pimpa_regression.py`. PE is a **raw** (un-floored) quantile of portfolio value → can be negative for a net-liability book (→ `OQ-CCR-08`). `FIRM` (`CCR-MIG-03/05`, `GEN-04`).
- `DC-CCR-LIT-1` **`marker` paper pipeline · per-paper artifacts.** Per paper, `marker` emits a folder with a `.md` (parsed text, LaTeX equations, figure refs), a `.json` (layout metadata — dropped), and JPEG figures. Only the `.md` enters project knowledge; figures added to chat on demand; folders named `Author_Year_ShortTitle`; full folder kept in git under `literature/`. `FIRM`.

---

## MKT arm — market / rate & scenarios (feeds the spine)

### DC-MKT-SIE — Banxico SIE interest-rate inputs

- `DC-MKT-SIE-1` **Source:** Banco de México SIE (https://www.banxico.org.mx/SieInternet/). Series:
  | Symbol | SIE source | Meaning | Quote convention |
  |--------|-----------|---------|------------------|
  | `r_ON` | CA684 — *TIIE de Fondeo a un día* | Overnight risk-free proxy | annualised, simple, Act/360 |
  | `r^F_28/91/182` | CA766 — *TIIE de Fondeo compuestas por adelantado* | Term-compounded F-TIIE | annualised, simple, Act/360 |
  | `r^Cetes_364` | CF300 — *Cetes 364 días* | On-the-run 1-year Cetes YTM → **1Y zero pillar** | YTM, simple, Act/360 |
  | Bonos M ×6 | CF300 — *Vector de precios … (on the run)*, Bonos block | Six on-the-run coupon-bond buckets | dirty price per 100 face |
- `DC-MKT-SIE-2` **Bonos M CSV schema:** rows `(Date, Serie, Plazo, Cupon, Valor)`. `Serie ∈ {Bonos_0_3, Bonos_3_5, Bonos_5_7, Bonos_7_10, Bonos_10_20, Bonos_20_30}`; `Plazo` = residual days of the on-the-run benchmark (drifts; jumps on roll); `Cupon` = annual coupon %; `Valor` = **dirty price** per 100 face. `T = Plazo/365`; `c = Cupon/100`; each coupon `= c·182/360` per 100 face.
- `DC-MKT-SIE-3` **Conventions (binding):** Cetes & F-TIIE compounded tenors simple-interest Act/360 (`P = Face/(1 + r·d/360)`); Bonos M coupon every 182 days; Hull–White internal math continuous-compounding Act/365 (`T = Plazo/365`); short-end → continuous uses the **simple-interest** conversion, **not** `(365/360)·ln(1+r)`. (see `MKT-SIE-04`.)
- `DC-MKT-SIE-4` **Quality rules:** drop a date if a needed series is a genuine non-quote (partial-curve fits fine); flag benchmark rolls per bucket; compute change-series on **stripped zero rates**, never raw `Valor`; reprice each input bond/zero from the fitted curve as a sanity check.

### DC-MKT-CURVE — produced curve objects

- `DC-MKT-CURVE-1` **Outputs (produced):** `z(T)` continuous zero curve (≈11 pillars: short block + 364d Cetes + 6 stripped Bonos, interpolated NS/Svensson/monotone-convex); `f(0,T) = z(T) + T·∂z/∂T` (must be differentiable); `a, σ` (rolling F-TIIE overnight, COVID window excluded); `θ(t)` on a fine grid via the HW formula. `FIRM`.

### DC-MKT-PHYS — physical-risk dashboard schema (Excel)

- `DC-MKT-PHYS-1` **`TblDatos` (base exposures), tidy, one row per cell:** `clave_mpio` (5-digit), `nombre_mpio`, `fenomeno ∈ {Ciclón Tropical, Inundación, Sequía, Onda de Calor}`, `escenario ∈ {SSP2-4.5, SSP5-8.5}`, `año ∈ {2030, 2050, 2100}`, `nivel_riesgo ∈ {R1,R2,R3,R4}`, `industria`, `saldo_expuesto` (currency), `activos_totales`, `capital_reg`, `utilidad_neta`.
- `DC-MKT-PHYS-2` **`TblMetricas` (denominators by industry):** `industria | activos_totales | capital_regulatorio | utilidad_neta | var_95`.
- `DC-MKT-PHYS-3` **Dashboard semantics:** filters `Filtro_Fenomeno`, `Filtro_Metrica ∈ {Valor Absoluto, % Activos, % Capital, % Utilidad}`; core formula `SUMAR.SI.CONJUNTO(TblDatos[saldo_expuesto], …)` over {fenómeno, industria, escenario, año, nivel_riesgo} ÷ metric-selected denominator via `BUSCARX` on `TblMetricas`; rows = industries, columns = (escenario × año × R1–R4); conditional-format heat-map; >10% flagged high concentration. `R1–R4` band thresholds `TBD` (→ `OQ-MKT-08`).

### DC-MKT-NGFS / DC-MKT-SSP — climate-scenario contracts

- `DC-MKT-NGFS-1` **NGFS (transition/rates).** Portal ngfs.net/ngfs-scenarios-portal (CSV/Excel). Long-term: ~100 countries 2020–2100, models REMIND-MAgPIE/GCAM/MESSAGEix-GLOBIOM. Short-term (May 2025): 3–5y, quarterly, ~50 sectors, direct PD; models GEM-E3/CLIMACRED/EIRIN; IMF WEO Oct-2023 baseline. **Variables used:** policy interest rate (short end), long-term/10Y govt yield (long end); optionally GDP, inflation. **Not provided:** full yield curve, TIIE/interbank → reconstruct via the shock method. **Usage rule:** `Δr = NGFS − baseline → apply to current curve → interpolate across tenors → recalibrate θ\*`. Families: Net Zero 2050, Below 2°C, Delayed Transition, Current Policies, NDCs, Fragmented World.
- `DC-MKT-SSP-1` **SSP/CMIP6 (physical hazards).** Scenarios SSP2-4.5 (middle) and SSP5-8.5 (high). Horizons 2030/2050/2100. Hazard typing → `nivel_riesgo` R1–R4 (band definitions `TBD`).

### DC-MKT-CREDIT — climate-credit / bond-portfolio requirements (optional overlay)

- `DC-MKT-CREDIT-1` **Sovereign bond (min viable):** `ISIN · Country ISO · Price · Yield · Spread-to-benchmark · Sovereign rating · (CDS) · GDP · GDP growth · (Debt/GDP) · Total GHG (EDGAR) · Emissions/GDP · ND-GAIN · (Germanwatch CRI) · Fossil-fuel dependence · (NDC target)`.
- `DC-MKT-CREDIT-2` **Corporate bond (min viable):** `ISIN · Issuer LEI · Currency · Coupon · Maturity · Outstanding · Clean price · YTM · OAS · Rating · (CDS 5Y) · Revenue · (EBITDA, Debt, Mkt cap) · Scope 1&2 (CDP/Trucost) · (Scope 3) · HQ location · (asset geolocation) · carbon intensity · (green-revenue %)`.
- `DC-MKT-CREDIT-3` **Physical-risk layers:** riverine/coastal flood, cyclone wind, wildfire, extreme heat (days >35°C, wet-bulb), drought (SPEI), water stress (WRI Aqueduct) — gridded for corporates, composite scores for sovereigns. Damage functions: depth-damage (flood), vulnerability curve (wind), productivity loss (heat), yield reduction (drought).
- `DC-MKT-CREDIT-4` **Output metrics:** climate-adjusted PD / spread · scenario-conditional losses · portfolio Climate-VaR · stranded-asset exposure; (rate strand) VaR 95/99%, Expected Shortfall, loss distribution vs baseline.
- `DC-MKT-CREDIT-5` **Sector crosswalk:** GICS (carbon intensity) ↔ NACE (EU Taxonomy) ↔ SIC/NAICS/SCIAN ↔ ICB. High-transition GICS: Energy(10), Materials(15), Utilities(55); high-physical: Real Estate(60), Consumer Staples(30). A Mexican-`industria` ↔ GICS/SCIAN crosswalk is `TBD` (→ `OQ-MKT-10`).

---

## HAZ arm — physical hazard & insurance loss (feeds the spine)

### DC-HAZ-CNSF — CNSF consolidation + cleaning

- `DC-HAZ-CNSF-1` **Input:** CNSF SharePoint downloads in `datos/datos_CNSF/crudos`. Sectors in `.xlsx` (agrícola, incendio, hidrometeorológicos, …); autos in `.zip` → `.mdb` (Access), subfolders `automoviles/individual/`, `automoviles/flotilla/`.
- `DC-HAZ-CNSF-2` **xlsx sector output (`consolidar_cnsf.py`):** one consolidated CSV per sector; canonical headers (typos fixed via `CORRECCIONES_CANONICAS`); spacer columns dropped; optional `--comprimir {gzip,bz2,xz}`. Loss = `MONTO PAGADO`; frequency = `NÚMERO DE SINIESTROS`; empty = NA.
- `DC-HAZ-CNSF-3` **autos output (`procesar_autos_cnsf.py`):** **three** CSVs — claims, premiums, **Unidades Expuestas**. Codes kept + `_desc` columns (catalog join); `Marca` → `Marca_desc` + `Tipo_desc`; 2007 excluded (wide format); year from `.zip` filename.
- `DC-HAZ-CNSF-4` **Config:** `catalogos_autos_cnsf.json` (incl. `Tipo de poliza` catalog); key resolution accent/case-insensitive.
- `DC-HAZ-CNSF-5` **Cleaning API (`limpieza_cnsf.py`):** `clasificar_entidad(x)→(categoría, canónico)` (estado / `extranjero` / `no_localizado` incl. `NU`→`No Disponible` / `desconocido`); `filtrar_para_calibracion(df)→(df_estados, df_no_asignado)`; `vacio_a_na(df, COLUMNAS_TARDIAS)`; `validar_variable_perdida()` (warns on negatives in `MONTO DEL SINIESTRO`); `normalizar_primera_linea_de_mar()`; `mapear_peril()`. **Guarantee:** 32 states/year after corrections.

### DC-HAZ-IBTRACS — tropical cyclone

- `DC-HAZ-IBTRACS-1` **Input:** raw `v04r01` basins EP+NA (double-header CSV) + 32-entity INEGI shapefile (`--estados`, col `NOMGEO`).
- `DC-HAZ-IBTRACS-2` **Outputs (panel `estado × año`):** buffer route `covariables_ciclon_estado_anio.csv`; wind-field route `covariables_ciclon_estado_anio_campoviento.csv` (+ `_decae` with `--decaimiento-tierra`).
- `DC-HAZ-IBTRACS-3` **Key columns (λ covariates):** `n_ciclones`, `viento_max_kt`, `pres_min_mb`, `cat_ss_max`, `ace`, `pdi`, `n_landfalls`; wind-field route also `celdas_ge34/64/96kt` (thresholds for "affected").
- `DC-HAZ-IBTRACS-4` **Parametric assumptions:** buffer 100 km (buffer route only); EPSG:6372 reprojection; K&D decay `R=0.9, Vb=26.7 kt, α=0.095 h⁻¹`; `--anio-inicial` default 2005.

### DC-HAZ-CENAPRED — socioeconomic impact

- `DC-HAZ-CENAPRED-1` **Input:** open event-level base 2000–2015 (CSV, latin1) + executive-summary PDFs 2016+; header validated against `CONCEPTOS` (loud failure on missing required field).
- `DC-HAZ-CENAPRED-2` **Outputs (four):**
  | File | Grain | Multi-state | Consumer |
  |---|---|---|---|
  | `impacto_estado_anio_peril.csv` (**A**) | (entidad, año, peril) | excluded (→ A′) | `λ(estado, año)` panel + severity; penetration vs CNSF |
  | `eventos_cenapred_climada.csv` (**B**) | individual event | kept as 1 record, `estados = E1|E2|…` | `climada.util.calibrate` (observed damage per event) |
  | `impacto_multiestado.csv` (**A′**) | multi-state event | kept, not split | national reconciliation |
  | `catalogo_fenomenos_climaticos.csv` | event × entity (exploded) | damage = event total (`danio_mdp_evento_total`), `multi_estado` flag | catalog/inspection |
- `DC-HAZ-CENAPRED-3` **Key B fields:** `evento_id`, `nombre_evento` (matchable to IBTrACS), dates, peril, estados, `danio_mdp`/`danio_mdd`, declaratoria, source, description; flag `en_alcance_climatico`; unmapped subtypes → `__SIN_MAPEO__`.

### DC-HAZ-CLIMADA — impact-function calibration

- `DC-HAZ-CLIMADA-1` **Calibration unit:** annual loss aggregated by state.
- `DC-HAZ-CLIMADA-2` **Routes:** insured (CNSF) and total (CENAPRED); shared spatial base **LitPop**.
- `DC-HAZ-CLIMADA-3` **Hazards:** TC wind, storm surge, cyclonic rain, river flood; shared centroids; frozen in the CLIMADA pipeline.
- `DC-HAZ-CLIMADA-4` **Parameter output:** versioned parameter tables + deterministic reconstructor scripts (never pickles). Precomputed surrogate surfaces per hazard.
- `DC-HAZ-CLIMADA-5` **User inputs:** DEM `.tif`, flood depth/fraction `.nc`, INEGI shapefile.

### DC-HAZ-DROUGHT — drought pipeline

- `DC-HAZ-DROUGHT-1` **Input:** ERA5/Copernicus CDS (`.nc` clipped to Mexico) in `datos/datos_sequia/crudos`; official SPI/SPEI benchmarks.
- `DC-HAZ-DROUGHT-2` **Processing:** `indices_sequia` (SPI/SPEI by scale) → `agregacion_sequia` (to state via `--shp-estados`) → `validacion_sequia` (`reporte_validacion.json` vs official product).
- `DC-HAZ-DROUGHT-3` **Canonical download targets:** `crudo_era5`, `benchmark_spi`, `benchmark_spei` (fixed canonical names so `verificar` recognizes them).
- `DC-HAZ-DROUGHT-4` **Provenance:** CDS request + version + DOI + sha256 + bytes + date.

---

## DC-XWALK — Crosswalks (joins between modules)

- `DC-XWALK-1` **CENAPRED B ↔ IBTrACS:** `nombre_evento` (e.g. "Ciclón Odile") + year → IBTrACS `NAME`/`SEASON` → `SID` → event wind footprint → modeled damage vs `danio_mdp`. This is the (per-event hazard, per-event observed damage) pair the impact-function calibration of `v_half` requires. `FIRM` (next deliverable).
- `DC-XWALK-2` **CNSF ↔ CENAPRED:** same `estado × peril × año` grain; penetration = insured paid (CNSF) ÷ total damage (CENAPRED). `FIRM`.
- `DC-XWALK-3` **Hazard ↔ impact (peril):** CNSF cause ↔ canonical peril ↔ source catalog (in `notes/theory/referencias_riesgo_catastrofico.md` §4). `FIRM`.
- `DC-XWALK-4` **HAZ → simulation · the climate jump channel (`INT-10`).** HAZ `calibration.impact` produces the **intensity** `λ(estado, año / t)` and the **impact/jump-mark** distribution; these are the inputs to `processes.jumps` (`DC-CCR-SIM-2`), which injects climate shocks into the GBM/HW1F diffusions. The `estado × peril × año` loss panels and the compound-Poisson/Cox `λ(t)` also feed `risk.loss` directly. **Mechanism specified; remaining knobs** (which target a shock hits, jump↔diffusion dependence, fixed vs trajectory `λ`) are `OQ-INT-03/07`. `FIRM` (mechanism) + `PROPOSED` (knobs).
- `DC-XWALK-5` **MKT FX ↔ HAZ `MONEDA`:** the MKT/SIE Banxico FX series can supply the FX normalization the HAZ CNSF `MONEDA` step needs (closes `HAZ-CLEAN-CNSF-10`/`OQ-HAZ-03` once wired). `PROPOSED`.
- `DC-XWALK-6` **NGFS ↔ SSP taxonomies:** the rate strand uses NGFS, the physical strand uses SSP2-4.5/SSP5-8.5; a defensible mapping (or a deliberate non-mapping) is unresolved. `TBD` (→ `OQ-INT-03`).


---

## Related
Reads with: [[DECISIONS]] (the decisions behind each contract) · [[GLOSSARY]] (column/term meanings) · [[OPEN_QUESTIONS]] (unspecified fields). By arm: [[CCR_MOC]] · [[MKT_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]
#type/contract
