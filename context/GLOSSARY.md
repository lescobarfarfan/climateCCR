# GLOSSARY — Integrated glossary & retrieval index

Terms, acronyms, and proper nouns. One line each. Spanish identifiers (column names, peril names,
institutions, CLI flags) are kept **verbatim** because they are literal artifacts in the data/code.
Reference keys in brackets resolve in `REFERENCES.md`. A **content-word retrieval index** for recalling
history across chats is at the end (§J).

## Categories
A. Project & architecture · B. Reproducibility & engineering · C. Stochastic models & math ·
D. Counterparty credit risk · E. Market / rate & curve (Mexico) · F. Climate & scenarios ·
G. Hazard concepts (physical) · H. Impact modelling & calibration · I. CNSF / insurance-loss conventions ·
J. Content-word retrieval index

---

## A. Project & architecture
- **climateCCR** — the integrated project's package: a climate-risk-aware financial risk pipeline (data → calibration → simulation → risk metrics) for Mexico. Keeps its original name even though scope now exceeds counterparty credit (`INT-02`).
- **CCR / MKT / HAZ arms** — counterparty-credit & narrative-detection (spine) / market-rate & scenarios / physical-hazard & insurance-loss. See `00_README_CONTEXT.md` §1.
- **PIMPA** — the pre-existing Basel-III-style CCR exposure engine; migrated in as the `climateCCR.risk.ccr` subpackage.
- **`direct_input`** — PIMPA's `calibration_method` that consumes *pre-calibrated* parameters rather than estimating them; the integration point for the new `calibration` module.
- **Path A / Path B** — the CCR-arm research routes. A: detect → calibrate → inject a climate-event effect, read shifted CCR metrics (RQ1+RQ2). B (fallback): map scenarios to justified parameter perturbations and report sensitivity.
- **RQ1 / RQ2** — Research Question 1 (detection/distillation of climate-event impact) / RQ2 (modelling/propagation into risk metrics).
- **marker** — library converting paper PDFs into structured markdown (+ JSON + figure JPEGs) for the literature workflow.

## B. Reproducibility & engineering
- **Provenance (`_procedencia.json`)** — per raw artifact: URL/dataset, sha256, bytes, date (+ version/DOI/request).
- **Run manifest** — per-run JSON (config + git commit + seed + package versions + timestamps) to `results/`, making every figure traceable.
- **Deterministic reconstructor** — script that re-derives an artifact from raw; the source of truth (never a pickle).
- **Idempotent** — re-running does not redo completed work (e.g. `descargar` skips existing raw unless `--forzar`).
- **`src/` layout / editable install** — packaging pattern (`pip install -e .`) that makes imports work from any directory.
- **ProjectPaths** — the `infra` resolver anchoring paths to the repo root (replaces CWD-relative paths).
- **DoD** — Definition of Done.
- **Claude Code** — Anthropic's agentic CLI/IDE coding tool; the project's primary working interface (`GEN-15`). Scoped to the directory it launches in; the context canon serves as its memory.
- **git worktree** — a second working-tree checkout of one repo on a separate branch; used for parallel Claude Code agents, created **outside** the Obsidian-indexed vault to avoid duplicate-note / wikilink clashes (`GEN-16`).
- **`additionalDirectories`** — the Claude Code setting (also `--add-dir` / `/add-dir`) that grants read/write access to one extra path (e.g. an external data drive) without widening filesystem scope (`GEN-15`).
- **`CLAUDE.md`** — the repo-root memory file Claude Code loads each session; points at the canon and restates load-bearing rules. (Distinct from `00_README_CONTEXT.md`, the human entry point.)

## C. Stochastic models & math
- **BM / GBM** — Brownian motion / geometric Brownian motion (GBM supports constant **or** term-structure volatility here).
- **Hull–White 1F (extended Vasicek)** — one-factor short-rate model `dr = [θ(t) − a r] dt + σ dW`; affine bond prices; closed-form transition density (exact simulation possible). Simulated via the Andersen–Piterbarg scheme. `[Hull1990]` `[AndersenPiterbarg2010]`
- **Vasicek** — constant-θ special case; used here as the estimation device for `a`, `σ`. `[Vasicek1977]`
- **θ(t)** — deterministic HW drift calibrated so the model reproduces today's forward curve: `θ = ∂f/∂T + a·f + (σ²/2a)(1 − e^{−2at})`.
- **a** — mean-reversion speed (weakly identified; flat likelihood). **σ** — short-rate volatility.
- **f(0,t)** — instantaneous forward curve `= z(T) + T·∂z/∂T`; input to θ(t). **z(T)** — continuous zero-coupon (spot) curve from the strip.
- **λ(t) — market price of interest-rate risk** — links Q and P drifts (`dW^Q = dW^P − λ dt`); usually negative.
- **Q vs P measure** — risk-neutral (pricing) vs real-world (stress / economic capital).
- **Girsanov / change of measure** — drift change between Q and P via the Radon–Nikodym derivative.
- **Compound Poisson** — aggregate-loss / shock model (Poisson frequency × severity); here the carrier of climate shocks into the diffusion. `[Klugman ref?]`
- **Cox / doubly stochastic process** — Poisson with random / covariate-driven intensity `λ(t)`; lets the climate arrival rate vary with hazard covariates. `[ContTankov2004]`
- **Jump-diffusion** — a process combining a continuous diffusion (GBM/HW1F) with a jump component; the integrating object of the project — `dX = (diffusion) + (Σ marks at Poisson/Cox times)` (`INT-10`).
- **Jump mark / impact** — the size of a single climate shock's effect on the target process (a price-return jump for GBM, a rate jump for HW1F); estimated by HAZ. The empirical climate→price magnitude (`OQ-INT-07`).
- **Climate shock channel** — the wiring HAZ `λ` + impact → `processes.jumps` → `simulation`; how climate physically enters the financial dynamics (`DC-CCR-SIM-2`, `DC-XWALK-4`).
- **Fixed vs trajectory (climate assumption)** — climate enters either as a static level/parameter shift (*fixed* = old Path B) or as a time path of rates / of `λ(t)` (*trajectory*); both via the same injection hook (`INT-12`).
- **POT-GPD** — Peaks-Over-Threshold with Generalized Pareto; does not apply to aggregated CNSF data (tail via CENAPRED). `[McNeil1997]`
- **Signature transform** — a faithful, hierarchical feature map of a path (iterated integrals that linearise nonlinear functionals). **Log-signature** — its compressed free-Lie-algebra representation.
- **Randomized signature** — a finite-dimensional, training-free reservoir approximating the signature cheaply, via `Z_i = Z_{i-1} + Σ_k σ(A_k Z_{i-1} + b_k) dX^k_i` with random `A, b, z0`. `[Compagnoni2023]`
- **Reservoir computing** — a random, fixed reservoir + a trained linear readout (here, a Ridge regression on the reservoir state).
- **Variance reduction** — antithetic/control variates, importance sampling, moment matching, quasi-MC (Sobol), multilevel MC. `[Glasserman2003]`
- **Importance sampling** — drift change to target a terminal rate; paths reweighted by likelihood ratio.

## D. Counterparty credit risk
- **CCR** — counterparty credit risk. **MPOR** — margin period of risk (close-out horizon before collateral catches up).
- **EE** — expected exposure (mean positive exposure at a future grid point). **EPE** — expected positive exposure (time-average of EE). **Effective EPE** — its Basel running-max version.
- **PE / PFE** — potential (future) exposure: a high quantile of the exposure distribution (PIMPA default 99%).
- **CVA** — credit valuation adjustment; market value of counterparty default risk; the natural home for a climate-conditioned credit spread. **xVA** — the family (CVA, DVA, FVA, …).
- **VM / MTA** — variation margin / minimum transfer amount. **netting set** — trades whose mark-to-market legally offsets on default. **LGD** — loss given default.

## E. Market / rate & curve (Mexico)
- **Bonos M** — fixed-rate peso government bonds; coupon every 182 days, `c·182/360` per 100 face.
- **Cetes** — zero-coupon Treasury bills (Act/360 simple). **364-day Cetes** = the chosen 1Y zero pillar.
- **Udibonos** — inflation-linked (UDI-denominated) government bonds. **Bondes** — floating-rate development bonds.
- **F-TIIE / TIIE de Fondeo** — transaction-based overnight interbank funding rate (market-observed); compounded 28/91/182-day tenors exist. **TIIE 28** — legacy term rate, restricted for new contracts from 2025-01-01.
- **On-the-run / benchmark roll** — `Plazo`/`Cupon` drift then jump as the benchmark bond is replaced; a roll-date price jump is not a market move.
- **CF300 / CA684 / CA766** — SIE on-the-run gov price/rate vector / TIIE de Fondeo overnight / F-TIIE compounded tenors.
- **Stripping / bootstrap** — recover zero rates from dirty bond prices by recursive root-find (Goal Seek / linear-in-z).
- **Nelson–Siegel / Svensson / monotone-convex** — admissible (differentiable-forward) interpolators; piecewise-linear zeros disallowed.
- **Day-count (Act/360 vs Act/365)** — a property of the *instrument*, not the model.
- **VaR (95/99%)** — quantile loss. **Expected Shortfall (CVaR)** — mean loss beyond VaR.
- **CNBV** — Mexican banking/securities regulator (stress-test rules, incl. Art. 282). **Banxico** — central bank. **BMV** — Bolsa Mexicana de Valores (the small target equity universe; pipeline source-agnostic).

## F. Climate & scenarios
- **NGFS** — Network for Greening the Financial System; macro/policy-rate scenario paths (not full curves). **Short-term scenarios (May 2025)** — 3–5y, quarterly, ~50 sectors, direct PD.
- **IIASA** — hosts the NGFS scenario database. **IPCC** — AR6 pathways. **SSP / RCP** — Shared Socioeconomic Pathways / Representative Concentration Pathways (SSP2-4.5 middle, SSP5-8.5 high). **Copernicus C3S / ERA5** — observational climate / reanalysis (drought indices via `cdsapi`).
- **Policy rate vs market rate** — the NGFS policy rate is a *model-simulated* central-bank rate; used as a **shock source**, never a direct F-TIIE substitute.
- **Physical vs transition vs liability risk** — hazard damage / low-carbon-transition / litigation channels. **Acute vs chronic** — extreme events vs slow shifts.
- **R1–R4** — hazard risk bands in the dashboard (thresholds `TBD`).
- **Climate VaR / climate-adjusted Merton** — portfolio climate-loss metric / PD model with climate-shocked asset values. `[Battiston2017]` `[Bolton2020]`
- **ND-GAIN / Germanwatch CRI / EM-DAT** — sovereign climate-vulnerability indices / disaster database.
- **OU temperature model (Alaton et al. 2002)** — Ornstein–Uhlenbeck with seasonal mean; baseline for weather-derivative pricing. **Basis risk** — geographic mismatch between hedge index and exposure. `[Alaton2002]`

## G. Hazard concepts (physical)
- **λ(estado, año)** — occurrence intensity/frequency to calibrate per state-year. **Severity** — per-event loss magnitude (tail via CENAPRED). **Covariate** — annual per-state variable feeding `λ` (`DC-HAZ-IBTRACS-3`).
- **IBTrACS** — International Best Track Archive for Climate Stewardship (NOAA/NCEI); cyclone tracks at 3 h. **HURDAT2** — NOAA/NHC best track (the IBTrACS input). **v04r01** — the pinned version. **SID** — unique storm identifier; `NAME`/`SEASON` resolve it. **Basins EP / NA** — East Pacific / North Atlantic (both reach Mexico).
- **ACE** — Accumulated Cyclone Energy (Σ wind² at ≥34 kt synoptic points). **PDI** — Power Dissipation Index (Σv³; most tied to damage). **Saffir-Simpson (`cat_ss_max`)** — max category in the state-year. **Vmax** — max sustained wind (the Holland profile is anchored to it). **Landfall** — coastal crossing.
- **Holland profile** — parametric radial wind-field model. `[Holland1980]` **Inland decay (Kaplan & DeMaria 1995)** — Vmax decay after landfall (`R=0.9, Vb=26.7 kt, α=0.095 h⁻¹`; here a conservative minimum). `[KaplanDeMaria1995]`
- **Buffer attribution** — assign storm to state by distance (≤100 km); applies central intensity → overstates periphery. **Wind-field attribution** — reconstruct local wind on a grid; preferred. **`celdas_ge34/64/96kt`** — count of cells exceeding thresholds; "affected" cutoffs. **EPSG:6372** — projected CRS for Mexico (correct km buffers).
- **CENAPRED** — Centro Nacional de Prevención de Desastres; *Impacto socioeconómico de los principales desastres*; total damage per event. **Monitor de Sequía de México (MSM)** — SMN-CONAGUA; biweekly D0–D4 polygons since 2014. **D0–D4** — drought-intensity scale. **SPEI/SPI** — Standardized Precipitation Evapotranspiration Index / Precipitation Index. **SIH (CONAGUA)** — station precipitation/hydrometry. **CHIRPS** — gridded satellite precipitation. **Declaratorias** — emergency/disaster declarations (CNPC–Segob), the FONDEN trigger. **DesInventar** — municipal disaster-loss inventory (UNDRR). **Atlas Nacional de Riesgos** — static hazard layers. **INEGI** — 32-entity shapefile + INPC. **SIAP** — reference scraper for robustness patterns.

## H. Impact modelling & calibration
- **CLIMADA** — climate-risk modelling platform (hazard × exposure × impact function). **Impact function (impf)** — intensity→damage-fraction relation; here subnational per state. `[Eberenz2021]`
- **`ImpfTropCyclone.from_emanuel_usa`** — the real TC impact-function constructor in CLIMADA. **`v_thresh = 25.7 m/s`** — wind threshold below which there is no damage. **`v_half`** — wind at half saturation; the parameter to calibrate (default 74.7 m/s). `[Emanuel2011]` `[Eberenz2021]`
- **LitPop** — exposure base (nightlights × population) for spatial disaggregation. `[Eberenz2020LitPop]` **Partial pooling** — per-state partial pooling in the hierarchical Bayesian model (PyMC/Stan). **Surrogate surface** — precomputed emulator of the forward model. **Multi-peril union** — `f_total = 1 − (1−f_wind)(1−f_surge)(1−f_rain)`; avoids double counting.
- **DaLA / CEPAL** — damage-and-loss assessment methodology; basis of CENAPRED total damages. `[CEPAL2014]` **INPC** — Índice Nacional de Precios al Consumidor (INEGI); the chosen deflator. **Penetration** — insured paid (CNSF) ÷ total damage (CENAPRED).
- **Parametric instrument** — cover whose payout is triggered by a measurable index (not adjusted loss). **Basis risk** — mismatch between parametric payout and actual loss.

## I. CNSF / insurance-loss conventions
- **`MONTO PAGADO`** — chosen loss variable (vs `MONTO DEL SINIESTRO`). **`MONTO DEL SINIESTRO`** — accounting figure with reserve-driven negatives; **not** used. **`NÚMERO DE SINIESTROS`** — frequency. **`OCURRIDO`** — year of occurrence (vs report); avoids smearing year-end catastrophes.
- **`NU`** — entity label = unlocated → `No Disponible`; not assigned to a state. **`vacío = NA`** — convention for late-introduced columns (not 0). **`CORRECCIONES_CANONICAS`** — dict fixing canonical-header typos (`OCOURRIDO`→`OCURRIDO`). **`__SIN_MAPEO__`** — marker for a CENAPRED subtype with no assigned peril. **Ramo** — insurance line of business (autos, agrícola, incendio, hidrometeorológicos, …).

---

## J. Content-word retrieval index (use these phrases to recall history)

| To recall… | Search phrase |
|------------|---------------|
| The arm-relationship / unifying RQ | **CCR spine MKT HAZ supporting arms unifying research question** |
| The unifying narrative / general objective | **price climate relationship jump-diffusion Monte Carlo change baseline INT-09** |
| The climate jump channel | **lambda jump process compound Poisson Cox impact GBM Hull-White injection** |
| Fixed vs trajectory climate assumption | **fixed level vs trajectory climate assumption Path A Path B INT-12** |
| Where signatures fit now | **randomized signatures detection validation role under review OQ-CCR-07** |
| The package name (kept climateCCR) | **climateCCR keep name climrisk rejected UNAM INT-02** |
| The src-layout / editable-install fix | **src layout editable install import pain ProjectPaths** |
| The PIMPA → risk migration | **PIMPA risk.ccr migration unchanged behaviour iteritems** |
| The PIMPA EE/PE regression test | **PIMPA EE PE regression test fixed seed baseline** |
| The randomized-signature solver bugs | **randomized signature solver z0 A b seeded reservoir** |
| The calibration direct_input contract | **calibration direct_input GBM HW1F pre-calibrated** |
| Path A vs Path B | **Path A Path B detect inject vs justified perturbation** |
| Why NGFS rates are a shock, not a level | **NGFS policy rate shock vs F-TIIE level** |
| The 1-year pillar choice | **364-day Cetes one-year pillar decision** |
| Short-end compounding-conversion choice | **simple-interest vs annually-compounded SIE conversion** |
| Which short-rate proxy for a, σ | **F-TIIE overnight short-rate proxy post-2006** |
| Crisis-window handling in estimation | **COVID window exclusion mean reversion volatility** |
| Bonos M stripping mechanics | **dirty price Goal Seek Bonos M strip linear-in-z** |
| Stress mechanic of choice | **shift initial curve recalibrate theta no-arbitrage** |
| Real-world simulation | **market price of interest-rate risk lambda P-measure** |
| Country scope decision | **Mexico benchmark deep bond market EM comparators** |
| Physical dashboard grain | **municipality clave_mpio SSP exposure dashboard** |
| Credit overlay method | **climate-adjusted Merton Climate VaR Battiston Mexico** |
| Weather-derivative baseline | **Alaton Ornstein-Uhlenbeck temperature seasonal mean** |
| The state↔storm crosswalk | **CENAPRED nombre_evento IBTrACS SID v_half calibration crosswalk** |
| The Holland wind-profile bug | **Holland wind profile anchored Vmax bug inland overestimate** |
| The Kaplan-DeMaria decay | **Kaplan DeMaria inland decay decaimiento-tierra conservative minimum** |
| The CNSF entity-cleaning rules | **CNSF clasificar_entidad NU Extranjero 32 states desconocido** |
| Which CNSF loss variable | **MONTO PAGADO not MONTO DEL SINIESTRO negatives reservas** |
| The CENAPRED A/B/A′ structures | **CENAPRED two grains panel A events B multiestado climada** |
| The drought-index choice | **SPEI primary SPI robustness MSM complementary evapotranspiration** |
| The CDMX discretization artifact | **CDMX wind-field panel 0.5 degree cell discretization** |
| The CLIMADA calibration design | **subnational impact function v_thresh v_half LitPop PyMC partial pooling** |
| The compound-Poisson/Cox plan | **compound Poisson Cox doubly stochastic aggregated tail CENAPRED** |


---

## Related
Reads with: [[DECISIONS]] · [[DATA_CONTRACTS]] · [[REFERENCES]] · Home: [[_INDEX]]
#type/glossary
