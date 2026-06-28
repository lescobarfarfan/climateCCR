# DECISIONS — Integrated decision log

One line per decision. Format: `[ID] [date] decision — rationale. [RefKey | [eng]]`.
`[eng]` = engineering decision, no academic reference expected. `[ref?]` = reference still to confirm
(see `OPEN_QUESTIONS.md`). Superseded decisions are **edited** in place, not appended. Reference keys
resolve in `REFERENCES.md`. ID scheme in `00_README_CONTEXT.md` §3.

> Dates predating 2026-06-15 are original where the origin project recorded them; **MKT-arm dates are
> reconstructed from document vintages and are approximate** (flagged per the origin project).

## Table of contents
- `GEN-*` — Cross-cutting standards (reproducibility, provenance, version control) — **shared**
- `INT-*` — Integration decisions (cross-arm, new)
- **CCR arm** — `CCR-ARCH`, `CCR-INFRA`, `CCR-MIG`, `CCR-SIG`, `CCR-CAL`, `CCR-RISK`, `CCR-RES`, `CCR-LIT`
- **MKT arm** — `MKT-SCOPE`, `MKT-IR`, `MKT-MEAS`, `MKT-SIE`, `MKT-CURVE`, `MKT-CALIB`, `MKT-STRESS`, `MKT-NGFS`, `MKT-MC`, `MKT-CREDIT`, `MKT-PHYS`, `MKT-WD`
- **HAZ arm** — `HAZ-CLEAN-CNSF`, `HAZ-SCRAPER-CNSF`, `HAZ-IBTRACS`, `HAZ-CENAPRED`, `HAZ-CLIMADA`, `HAZ-DROUGHT`, `HAZ-SOURCES`, `HAZ-STOCH`

---

## GEN — Cross-cutting standards (shared across all arms)

These unify the HAZ-arm reproducibility rules and the CCR-arm infra/reproducibility rules into one
standard the whole project obeys.

- `GEN-01` [2026-06-15] Every analytical/design decision carries a real, checkable reference, or is explicitly marked `[eng]`. No invented citations; unconfirmed refs go to `REFERENCES.md` §99. [standard]
- `GEN-02` [2026-06-15] Raw data is version-pinned with a provenance record per artifact — URL/dataset, sha256, bytes, date, and version/DOI/request where applicable (HAZ uses `_procedencia.json`; the new repo standardises this; see `DC-CONV-2`). [eng]
- `GEN-03` [2026-06-15] Unlocated or ambiguous data is **excluded and documented**, never redistributed or imputed — no certainty, no fabricated structure. [standard]
- `GEN-04` [2026-06-15] Deterministic reconstructor scripts are the source of truth for any derived artifact; **never** a pickled object. [eng]
- `GEN-05` [2026-06-15] Pipelines are **idempotent**: re-running skips completed work (e.g. downloads skip existing files unless `--forzar`/`--force`). [eng]
- `GEN-06` [2026-06-15] Every stochastic run writes a **manifest** to `results/manifests/<run_id>.json` — resolved config + git commit + seed + package versions + timestamps. Nothing stochastic runs outside it. (from CCR `infra`.) [eng]
- `GEN-07` [2026-06-15] All randomness routes through one seeding entry point (`infra.set_seed` / `get_rng`); the seed is recorded in the manifest. (from CCR; the rand-sig reservoir must be fixed to comply — see `CCR-SIG-02`.) [eng]
- `GEN-08` [2026-06-15] Configuration over hard-coding: parameters live in `configs/*.yaml`; all paths resolve centrally via `infra.ProjectPaths` (no CWD-relative paths). [eng]
- `GEN-09` [2026-06-15] Version control throughout: small descriptive commits, feature branches, tags for milestones; **separate behaviour changes from packaging/move changes** in distinct commits. [eng]
- `GEN-10` [2026-06-15] `data/` and `results/` are git-ignored; `notes/`, `context/`, and `literature/*.md` are **tracked**. Large data tracked out-of-band (DVC or a documented external store). [eng]
- `GEN-11` [2026-06-15] Tests: `pytest` units per module + at least one end-to-end integration test on a tiny fixture (the PIMPA prototype CSVs are an ideal regression fixture). Code quality via pre-commit (black/ruff) + type hints on public APIs. [eng]
- `GEN-12` [2026-06-15] **Geophysical perils (earthquake/volcano) are out of scope** — the object is *climate* risk. (from HAZ; applies project-wide to the hazard data.) [standard]
- `GEN-13` [2026-06-15] Currency held in **current MXN** at source; deflation (INEGI INPC) is a documented downstream step common to all monetary series. [eng]
- `GEN-14` [2026-06-20] **Diagrams in the canon are authored in Mermaid** (fenced ` ```mermaid ` blocks), not hand-aligned ASCII / box-drawing art. Rationale: ASCII diagrams desync on ambiguous- or double-width glyphs (`λ`, `▶`, `◀`, `↵`) and overflow the viewport, so the structure is lost; Mermaid renders natively in Obsidian and on GitHub, in-terminal via `diagram.nvim` + `image.nvim` (renderer `mmdc`) and in-browser via `markdown-preview.nvim`, and its source stays human-readable as a fallback. **Directory/file trees stay plain code blocks** (Mermaid is not suited to them; box-drawing trees render reliably). Applied to `README.md`, `_INDEX.md`, `REPO_STRUCTURE.md` (§3 wiring; the §1 tree kept as a code block). [eng]

## INT — Integration decisions (cross-arm)

- `INT-01` [2026-06-15] **The CCR arm is the architectural spine.** The integrated repo keeps the `climateCCR` `src/`-layout, `infra` layer, and reproducibility model; MKT and HAZ plug into its `data → calibration → simulation → risk` flow rather than living as separate codebases. [eng]
- `INT-02` [2026-06-15; revised 2026-06-15] **Package name — keep `climateCCR`.** The integrated project retains the name `climateCCR` (distribution, repo, and import package), even though its scope now exceeds counterparty credit. A broad rename to `climrisk` was considered and **rejected**: that name is already taken by an existing UNAM package (https://climrisk.unam.mx/climrisk/). The PIMPA exposure engine is the `climateCCR.risk.ccr` submodule. (resolves `OQ-INT-05`.) [eng]
- `INT-03` [2026-06-15] **Mexico is the shared unit of analysis** across all three arms — the strongest unifier. The asset universe per arm is confirmable: sovereign/corporate bonds (MKT), insurance lines (HAZ), equities/derivatives/netting sets (CCR). (see `OQ-INT-04`.) [eng]
- `INT-04` [2026-06-15] **Three climate channels coexist, deliberately.** Transition/rate scenarios (NGFS — MKT), physical hazard (CLIMADA/IBTrACS/CENAPRED/drought — HAZ; SSP dashboard — MKT), and climate-narrative detection (signatures — CCR). They share the `data`/`scenarios` layer and the manifest standard; whether a defensible mapping links the NGFS and SSP taxonomies is open (`OQ-INT-03`). [eng]
- `INT-05` [2026-06-15] **`calibration` is split by domain:** `calibration/financial` (yield-curve strip, HW/Vasicek/GBM estimators — MKT + CCR) and `calibration/impact` (CLIMADA subnational impact functions — HAZ). Both obey the same provenance/manifest standard. [eng]
- `INT-06` [2026-06-15] **`risk` is split by metric family:** `risk/ccr` (EE/PE/EPE/CVA — the spine), `risk/market` (VaR/ES, stress shocks — MKT), `risk/loss` (compound-Poisson/Cox loss distributions, parametric pricing — HAZ). [eng]
- `INT-07` [2026-06-15] **Bilingual boundary, documented.** HAZ/MKT pipeline code and data identifiers are in Spanish (literal artifacts in the data); the CCR engine and the package API are in English. Public Python APIs are English; Spanish identifiers are kept verbatim where they name real data columns/CLI flags/institutions. (see `OQ-INT-06`.) [eng]
- `INT-08` [2026-06-15] **One provenance + manifest standard** replaces the two partial ones: HAZ's `_procedencia.json` (raw-data provenance) and CCR's `RunManifest` (run provenance) are both kept and treated as complementary — raw artifacts get provenance, runs get manifests (`GEN-02`, `GEN-06`). [eng]
- `INT-09` [2026-06-15] **General objective (the unifying research question).** The thesis finds, tests, and quantifies a **relationship between financial asset prices / risk factors and climate events**, and measures via Monte Carlo **how financial risk changes** once climate is incorporated. This resolves the architectural framing (`INT-01`) into one research narrative; the three arms are one machine, not three theses. (largely resolves `OQ-INT-01`.) [eng]
- `INT-10` [2026-06-15] **The integrating mechanism is a climate-driven jump process.** Climate enters the simulation as a **jump (compound-Poisson / Cox) component superimposed on the diffusion**: HAZ-estimated intensity `λ(t; covariates)` governs shock arrivals and a HAZ-estimated **impact/jump-mark** maps each shock onto a diffusion — an asset price (**GBM**) or a risk factor (**Hull–White** rate). Monte Carlo over the resulting **jump-diffusion** yields the climate-vs-baseline change in CCR/market/loss risk. (specifies `DC-CCR-SIM-2`, `DC-XWALK-4`.) `[ContTankov2004]`
- `INT-11` [2026-06-15] **Arm roles in the machine.** **HAZ = estimation engine** for the climate→price connection (intensity functions `λ` + impact/jump-mark, from the hazard/loss panels). **MKT (Hull–White) + PIMPA = the calibration & simulation engine** — HW and GBM are interchangeable risk-factor/asset models inside climateCCR's stochastic subsystem, alongside PIMPA's exposure/valuation + multi-factor simulation structure. **CCR/climateCCR = the framework** that runs calibration→simulation→risk and reads out the change. [eng]
- `INT-12` [2026-06-15] **Climate assumptions enter in two flavors:** **fixed** (a level/parameter shift — e.g. an NGFS `Δr` level, a drift/curve perturbation = the old "Path B") and **trajectory** (a path over time — e.g. an NGFS rate path, a time-varying `λ(t)` or scenario-driven impact). Both are injected through the same simulation hook (`DC-CCR-SIM-1/2`). This subsumes the earlier Path A/Path B split: **HAZ→jump channel = concrete Path A** (estimate the effect, inject it dynamically); **fixed parameter shift = Path B**. (refines `CCR-RES-01`.) [eng]

---

## CCR arm — counterparty credit & narrative detection (the spine)

### CCR-ARCH — architecture & packaging

- `CCR-ARCH-01` [2026-05-30] Adopt a `src/` layout + `pyproject.toml`, installed editable (`pip install -e .`). This is the fix for the import pain: after a one-time install every module imports from anywhere with no path hacks. [eng]
- `CCR-ARCH-02` [2026-05-30] Root cause of the import pain: neither legacy codebase shipped `__init__.py`/`pyproject.toml`; PIMPA used a CWD-relative `GLOBAL_DATA_PATH='data/'`; rand-sig tests used `sys.path.append("..")`. The editable install + `ProjectPaths` resolves all three. [eng]
- `CCR-ARCH-03` [2026-05-30] PIMPA becomes the `risk.ccr` subpackage; the randomized-signature code becomes the `signatures` subpackage. Migrated in, not rewritten. (The package keeps the name `climateCCR`; see `INT-02`.) [eng]
- `CCR-ARCH-04` [2026-05-30] Configuration over hard-coding: YAML configs replace PIMPA's mutable `global_parameters.py` dict; all paths resolve centrally via `ProjectPaths`. (now `GEN-08`.) [eng]
- `CCR-ARCH-05` [2026-05-30] `notes/` is git-TRACKED; `data/` and `results/` are git-ignored. (now `GEN-10`.) [eng]

### CCR-INFRA — reproducibility infrastructure (built)

- `CCR-INFRA-01` [2026-05-30] Build `infra` first — it unblocks reproducibility everywhere: `set_seed`/`get_rng`, typed `Config` from `configs/*.yaml`, console+file logger, `RunManifest`, `ProjectPaths`. (Scaffolded and tested: infra tests pass; smoke pipeline writes a real manifest.) [eng]

### CCR-MIG — PIMPA / rand-sig migration discipline (Phase 0)

- `CCR-MIG-01` [2026-05-30] Move PIMPA in "unchanged in behaviour" first, as a pure move + minimal fix; extend only afterwards. Keeps the migration mechanical and auditable. (now also `GEN-09`.) [eng]
- `CCR-MIG-02` [2026-05-30] Fix the pandas blocker on migration: replace `DataFrame.iteritems()` with `.items()` (4 sites; removed in pandas ≥ 2.0, crashes on modern installs); remove the stray `from calendar import calendar` imports. [eng]
- `CCR-MIG-03` [2026-05-30] Lock a PIMPA EE/PE regression test before any refactor — run `CCR_Valuation_Session` on the prototype CSVs under a fixed seed and assert the EE/PE profile matches a saved baseline. Protects every later change. [eng]

### CCR-SIG — signatures / reservoir (RQ1 core)

- `CCR-SIG-01` [2026-05-30] The randomized-signature prototype must be fixed before any thesis result depends on it — it cannot run as shipped (see `notes/reviews/CODE_REVIEW.md` C1–C5). `[Compagnoni2023]` [eng]
- `CCR-SIG-02` [2026-05-30] The reservoir must be **seeded and reproducible**: pass a seeded `np.random.Generator` into parameter generation and store the seed in the run manifest. (The prototype accepted a `seed` arg but never used it.) [eng]
- `CCR-SIG-03` [2026-05-30] Fix the solver contract: generate `z0, A, b` once, store them on the `RandomisedSignature` instance, and reuse the *same* values in both `train` and `predict` (a reservoir must be fixed between fit and inference). [eng]

### CCR-CAL — statistical calibration (new work)

- `CCR-CAL-01` [2026-05-30] `calibration` is genuinely new work: PIMPA does **no** statistical calibration — it reads pre-calibrated parameter CSVs via `calibration_method='direct_input'`. New estimators (GBM drift/vol; HW1F `alpha`, `sigma`, `theta(t)`/curve) must **emit `'direct_input'`-compatible objects** so the engine itself stays untouched. (This is the load-bearing internal contract `DC-CCR-CAL-1`.) [eng]

### CCR-RISK — CCR metrics

- `CCR-RISK-01` [2026-05-30] EPE / Effective-EPE / CVA are missing and will be added as extensions. EE/PE already exist. CVA is the clean hook for a **climate-conditioned credit spread** — the direct link to the thesis. Open: do they live in the evaluator or a thin `risk/ccr/xva.py`? (→ `OQ-CCR-04`.) [eng]

### CCR-RES — research design

- `CCR-RES-01` [2026-05-30; refined 2026-06-15] **Research paths, reframed by `INT-10/12`.** The integrating channel is the **HAZ→jump injection** (estimate `λ` + impact from hazard data → jump-diffusion → shifted risk metrics) — this is the concrete realization of the original *Path A* (detect/inject), now driven by hazard econometrics rather than (only) signatures. *Path B* survives as the **fixed parameter-perturbation** flavor (GBM drift; HW1F curve / mean-reversion) for scenarios without an estimated jump. **Where the randomized signatures fit is now open** (`OQ-CCR-07`): complementary detection/validation of the climate signal in price series, a robustness probe, or repositioned — not assumed dropped. [eng]
- `CCR-RES-02` [2026-05-30] Timeline assumption: ~15 productive hrs/week over an ~8-month (~34-week) envelope; build subtotal ~15–20 weeks + ~20% buffer on the research phases; critical path 0→1→2→3→4→5 with writing (Phase 6) in parallel. (See `notes/plan/PROJECT_PLAN.md`.) [eng]

### CCR-LIT — literature / project-knowledge workflow

- `CCR-LIT-01` [2026-05-30] Project knowledge holds text/markdown only; zip is not supported there. Keep one short markdown project map (the README) in project knowledge; do code analysis via per-chat zip uploads in a sandbox. [eng]
- `CCR-LIT-02` [2026-05-31] Academic papers run through a `marker` PDF→markdown pipeline. Upload **only the `.md`** to project knowledge; **skip the `.json`** (layout metadata, noise); add figures to chat selectively (more for empirical papers, rarely for methodology-heavy ones). Keep the full `marker` output folder in git as the canonical source. [eng]
- `CCR-LIT-03` [2026-05-31] Paper naming convention: `Author_Year_ShortTitle`. Scales cleanly to many papers. [eng]

---

## MKT arm — market / rate & scenarios (feeds the spine)

### MKT-SCOPE — country / scope selection

- `MKT-SCOPE-01` [2026-06-15] Mexico is the primary unit of analysis and benchmark market — deep, liquid bond market; large weight in JPMorgan EMBI/GBI-EM. (supersedes: open cross-country panel idea.) [eng]
- `MKT-SCOPE-02` [2026-01] Candidate EM comparators are climate-exposed sovereigns *with deep bond markets* (India, Philippines, Pakistan, Indonesia, Brazil, Vietnam, Nigeria, Bangladesh, Thailand, South Africa). Illiquid top-CRI countries (Dominica, Honduras, Myanmar) excluded as un-calibratable. [eng]

### MKT-IR — Hull–White one-factor model

- `MKT-IR-01` [2026-05-10] Model is Hull–White one-factor (extended Vasicek) under Q: `dr = [θ(t) − a r] dt + σ dW`. Vasicek (constant θ) is used only as the estimation device for `a` and `σ`. `[Hull1990]` `[BrigoMercurio2006]` `[AndersenPiterbarg2010]`
- `MKT-IR-02` [2026-05-10] A single θ(t) serves all maturities — the deterministic drift that makes the model reproduce today's forward curve: `θ(t) = ∂f/∂T + a·f + (σ²/2a)(1 − e^{−2at})`. `[Hull1990]`
- `MKT-IR-03` [2026-05-10] Theory/reference docs keep theory + verified references only; implementation code is excluded from the knowledge base and lives in the connected repo (`notes/theory/` + `src/`). [eng]

### MKT-MEAS — change of measure

- `MKT-MEAS-01` [2026-05-10] Risk-neutral Q for pricing; real-world P (drift `θ − a r + λσ`) for stress / economic-capital paths. λ (market price of interest-rate risk) is typically negative and estimated from historical bond excess returns or via Yasuoka (2018). `[Yasuoka2018]` `[ref?]`
- `MKT-MEAS-02` [2026-05-10] θ(t) is always calibrated under Q to today's curve even for P-measure simulation, preserving no-arbitrage; only the drift gets the λσ adjustment. `[Hull1990]`

### MKT-SIE — Banxico SIE data pipeline

- `MKT-SIE-01` [2026-02] Official Banco de México SIE is the authoritative source. CF300 ("Vector de precios … on the run") + the TIIE de Fondeo family **supersede** the earlier Investing.com-based curve guide — stripping, day-counts, and benchmark-roll are solved or made mild by official data. (supersedes: Investing.com calibration guide.) [eng]
- `MKT-SIE-02` [2026-02] Short-rate inputs: F-TIIE overnight (CA684); 28/91/182-day TIIE de Fondeo "compuestas por adelantado" (CA766); 364-day Cetes (CF300). Bonos M: six on-the-run buckets from CF300 (`Plazo`, `Cupon`, dirty price `Valor`). [eng]
- `MKT-SIE-03` [2026-02] Conventions are properties of the **instruments, not the model**: Cetes & F-TIIE compounded tenors are simple-interest Actual/360; Bonos M pay fixed coupons every 182 days, `c·182/360` per 100 face (182-day rule is contractual). [eng]
- `MKT-SIE-04` [2026-02] Short-end conversion to continuous Act/365 uses the **simple-interest** form (consistent with Banxico's documented Cetes/F-TIIE methodology), **not** `(365/360)·ln(1+r)` (annually-compounded — looks tenor-monotone but is wrong for these inputs). (supersedes: annually-compounded reading of SIE rates.) [eng] (→ `OQ-MKT-01`)
- `MKT-SIE-05` [2026-02] `Plazo` is **not constant** — on-the-run buckets drift in residual maturity and jump on benchmark rolls. Build time series from **stripped zero rates**, never from raw `Valor`, to avoid embedding benchmark-roll noise into σ̂. [eng]

### MKT-CURVE — yield-curve construction

- `MKT-CURVE-01` [2026-05-10] The 1-year tenor gap is closed with the **364-day Cetes** from CF300 — a clean, official, unambiguously zero-coupon pillar. (supersedes: "let the interpolant decide" and synthetic TIIE-Fondeo OIS as the primary 1Y fix.) [eng]
- `MKT-CURVE-02` [2026-02] Bonos M are stripped from **dirty price** (`Valor`) by a recursive root-find (Goal Seek / linear-in-z), discounting sub-1Y coupons off the short block. Worked check: 2008-01-23 → z(T)=7.4187% at T≈1.92y. [eng]
- `MKT-CURVE-03` [2026-02] Canonical tenors (3y/5y/10y…) are **read off the fitted continuous curve**, not off the drifting raw buckets. Interpolator: Nelson–Siegel, Svensson, or monotone-convex — never piecewise-linear zeros (garbage forward derivative). `[NelsonSiegel1987]` `[Svensson1994]`
- `MKT-CURVE-04` [2026-02] The 10–30y region has only two pillars; densify with off-the-run Bonos M (also in CF300) if a portfolio carries material long-end risk. [eng] (→ `OQ-MKT-03`)

### MKT-CALIB — calibration of a, σ, θ

- `MKT-CALIB-01` [2026-02] Short-rate proxy for estimating `a` and `σ` is **F-TIIE overnight, post-2006** (cleanest zero-coupon series). TIIE 28 is a cross-check / pre-2006 extension; Cetes 28 is noisier. Note: TIIE 28 restricted for new contracts from 2025-01-01 (24 bp legacy adjustment). [eng]
- `MKT-CALIB-02` [2026-02] Estimate `a` and `σ` via **AR(1) on rate changes** (discrete-Vasicek) or **exact-transition-density MLE** — never MLE on rate *levels* (ill-conditioned). The two should agree within a few percent; an order-of-magnitude gap signals a non-stationary sample. `[JamesWebber2000]`
- `MKT-CALIB-03` [2026-02] COVID handling: **exclude ~2020-03-01 to 2021-06-30** explicitly (regulator-friendly, transparent) plus a robust-estimator sensitivity check. Apply the same rule to 2008–09 GFC and the 2017 peso shock. (supersedes: ad-hoc / single-treatment of crisis windows.) [eng]
- `MKT-CALIB-04` [2026-02] `a` (mean reversion) is weakly identified (flat likelihood near the max) — report results across multiple estimation windows for robustness, not a single point estimate. [eng]

### MKT-STRESS — stress testing

- `MKT-STRESS-01` [2026-05-10] Standard shock set: parallel (+200/−100 bps), non-parallel (steepening/flattening), volatility (+50% σ), mean-reversion (−50% a). Any shock to `a` or `σ` must be accompanied by **recalibrating θ to the shocked curve** to preserve no-arbitrage. `[CNBV]` `[BaselCommittee2019]`
- `MKT-STRESS-02` [2026-05-10] Preferred stress mechanic is **shift-the-initial-curve-and-recalibrate-θ** (regulatory standard); importance sampling toward a target terminal rate is the documented alternative for terminal-rate targeting only. [eng]
- `MKT-STRESS-03` [2026-05-10] Regulatory anchor: CNBV *Disposiciones … en materia de Administración de Riesgos* (incl. Art. 282 stress tests) and Basel (2019) minimum capital for market risk. Report VaR 95/99%, Expected Shortfall, max loss, mean/sd of P&L. `[CNBV]` `[BaselCommittee2019]`

### MKT-NGFS — scenario integration

- `MKT-NGFS-01` [2026-06-15] Use the NGFS **policy rate as a shock source, not a direct F-TIIE replacement**: Δr = NGFS − baseline, applied to the *current* curve. (supersedes: using NGFS policy-rate levels directly.) `[NGFS2024]`
- `MKT-NGFS-02` [2026-06-15] Build the stressed curve from two anchors — NGFS policy rate (short end) and NGFS long-term/10Y govt yield (long end) — interpolate the shock across tenors, derive f(0,t), recalibrate θ\*. (Fed CSA 2024 translation methodology.) `[NGFS2024]`
- `MKT-NGFS-03` [2026-06-15] For near-term (3–5y) analysis, anchor on the **NGFS short-term scenarios (May 2025)**: direct PD outputs, ~50 sectors, quarterly, models GEM-E3 / CLIMACRED / EIRIN, IMF WEO Oct-2023 baseline. Bridge to long-term paths only beyond 5y. (supersedes: defaulting to the long-term vintage for short-horizon work; vintage-mix detail open — `OQ-MKT-04`.) `[NGFS2025ST]`

### MKT-MC — Monte Carlo

- `MKT-MC-01` [2026-06-15] Variance-reduction toolkit: antithetic variates, control variates, importance sampling, moment matching, quasi-MC (Sobol), multilevel MC. Exact simulation preferred where possible (Hull–White has a closed-form transition density → no discretization error). `[Glasserman2003]`

### MKT-CREDIT — climate-credit overlay

- `MKT-CREDIT-01` [2026-01] Climate-credit overlay uses climate-adjusted Merton / distance-to-default for PD and spreads, and Climate-VaR at the portfolio level; Battiston et al. (2024) asset-level physical-risk method is the reference for the Mexico application. `[Battiston2017]` `[Bolton2020]`

### MKT-PHYS — physical-risk dashboard

- `MKT-PHYS-01` [2026-01] Physical-risk exposure is modeled on a **tidy municipality grain**: `clave_mpio × fenómeno × escenario × año × nivel_riesgo (R1–R4) × industria`, with `saldo_expuesto` as the exposure measure and financial denominators (assets / regulatory capital / net income / VaR_95). [eng]
- `MKT-PHYS-02` [2026-01] Physical strand uses **SSP/CMIP scenarios (SSP2-4.5, SSP5-8.5)** and horizons 2030/2050/2100 — distinct from the NGFS taxonomy used in the rate strand. Hazards: Ciclón Tropical, Inundación, Sequía, Onda de Calor. `[IPCC_AR6]`
- `MKT-PHYS-03` [2026-01] Dashboard is Excel-native (tables `TblDatos`, `TblMetricas`, named catalog lists; `SUMAR.SI.CONJUNTO` + `BUSCARX`; conditional-format heat-map). Deliverable is a filterable concentration view, not a simulation engine. [eng]

### MKT-WD — weather derivatives

- `MKT-WD-01` [2026-01] Weather-derivative literature is a **supporting/context module** (temperature modelling, hedging instruments), not (yet) a core empirical chapter. Baseline reference model: Alaton et al. (2002) Ornstein–Uhlenbeck with seasonal mean; extensions through Benth & Šaltytė-Benth and ML approaches. (status to confirm — `OQ-MKT-07`.) `[Alaton2002]` `[BenthSaltyteBenth2007]`

---

## HAZ arm — physical hazard & insurance loss (feeds the spine)

### HAZ-CLEAN-CNSF — CNSF value-level cleaning (`limpieza_cnsf.py`)

- `HAZ-CLEAN-CNSF-01` [2026-06-06] `NU` = "unlocated" → collapses to `No Disponible`, not assigned to any state — same logic as not redistributing unlocated losses. [eng]
- `HAZ-CLEAN-CNSF-02` [2026-06-06] Entity typos auto-remapped: `Quitana Roo`→Quintana Roo, `Distrito Federal`→Ciudad de México, official long forms. [eng]
- `HAZ-CLEAN-CNSF-03` [2026-06-06] `Extranjero` / `No aplica (exportación)` excluded from the state panel. [eng]
- `HAZ-CLEAN-CNSF-04` [2026-06-06] Unrecognized labels → `desconocido` category, flagged for **manual review**; never blind-assigned. [eng]
- `HAZ-CLEAN-CNSF-05` [2026-06-06] Confirmed: 32 states per year after corrections; entity-count differences across years come from out-of-domain labels, not missing states. [eng]
- `HAZ-CLEAN-CNSF-06` [2026-06-05] Loss variable = `MONTO PAGADO`; frequency = `NÚMERO DE SINIESTROS`. **Not** `MONTO DEL SINIESTRO` (accounting figure, has negatives from reserves; e.g. Odile). [eng]
- `HAZ-CLEAN-CNSF-07` [2026-06-05] Empty = NA (not 0) for late-introduced columns (`MONTO DE REASEGURO`, cumulative earned → NA before 2021). [eng]
- `HAZ-CLEAN-CNSF-08` [2026-06-05] 2015/2021 breaks resolved as a change of **granularity**, not coverage. [eng]
- `HAZ-CLEAN-CNSF-09` [2026-06-05] 2021 continuity confirmed in the claims sheet (claim count 134%, paid 106% vs 2020; no negatives in paid). [eng]
- `HAZ-CLEAN-CNSF-10` [2026-06-05] `MONEDA` normalization is a separate, documented step — requires Banxico FX (deliberate gap; the integrated repo can source FX from the MKT/SIE pipeline). [eng] (→ `OQ-HAZ-03`)
- `HAZ-CLEAN-CNSF-11` [2026-06-05] Peril taxonomy: incendio degraded to `Rayo`; irrigated/rainfed split in agro via `TIPO DE CULTIVO`; in hydro `COBERTURA` is not a peril; autos has cause only from 2016+. [eng] (cause list → `OQ-HAZ-05`)

### HAZ-SCRAPER-CNSF — CNSF pipeline (`scraper_cnsf.py`, `consolidar_cnsf.py`, `procesar_autos_cnsf.py`)

- `HAZ-SCRAPER-CNSF-01` [2026-06-05] `scraper_cnsf.py` orchestrates with `--modo sync/verificar/descargar/consolidar`; `_despachar` routes `.zip`(autos)→`procesar_autos_cnsf` and `.xlsx`→`consolidar_cnsf`. [eng]
- `HAZ-SCRAPER-CNSF-02` [2026-06-05] Year regex unified to `(?<!\d)(19|20)\d{2}(?!\d)` — handles underscore-delimited filenames. [eng]
- `HAZ-SCRAPER-CNSF-03` [2026-06-05] `consolidar_cnsf.py`: duplicate-header crash fixed (selection by position + `_unicos` dedup); whitespace-only spacer columns discarded; `CORRECCIONES_CANONICAS` fixes canonical typos (`OCOURRIDO`→`OCURRIDO`). [eng]
- `HAZ-SCRAPER-CNSF-04` [2026-06-05] `procesar_autos_cnsf.py`: exclude 2007 (wide-format incompatible); keep codes and add `_desc` columns; expand Marca→`Marca_desc`+`Tipo_desc`; include Unidades Expuestas as a third CSV; configurable missing-value sentinel set. [eng]
- `HAZ-SCRAPER-CNSF-05` [2026-06-05] Autos: year taken from the `.zip` filename (not the `.mdb`, which in 2008–2009 may lack a year); catalog resolution accent/case-insensitive (`_clave_col`), so one config serves both individual and flotilla. [eng]
- `HAZ-SCRAPER-CNSF-06` [2026-06-05] Alias mappings must be passed explicitly (`--aliases`); omitting them lets processing proceed incorrectly without warning. [eng]
- `HAZ-SCRAPER-CNSF-07` [2026-06-05] Robustness reference pattern = the SIAP scraper (logging, retries with backoff, sessions, User-Agent). [eng]
- `HAZ-SCRAPER-CNSF-08` [2026-06-05] Sandbox constraint: `cnsf.gob.mx` is blocked; live downloads validated on the author's machine. [eng]

### HAZ-IBTRACS — tropical cyclone (`descarga_ibtracs.py`, `procesar_ibtracs.py`, `campo_viento.py`)

- `HAZ-IBTRACS-01` [2026-06-05] Raw `v04r01` (basins EP + NA) with provenance and checksums; real download runs on the author's machine (NOAA blocked in sandbox). `[Knapp2010]` `[IBTrACSv04r01]`
- `HAZ-IBTRACS-02` [2026-06-09] **Wind-field attribution preferred over buffer** — the buffer assigns the storm's central intensity at the nearest track point, not the locally experienced wind, overstating peripheral states (empirically demonstrated: Otis 2023). [eng]
- `HAZ-IBTRACS-03` [2026-06-09] The threshold columns `celdas_ge34/64/96kt` enable principled "affected" definitions — the real advantage of the wind field, not fewer rows. [eng]
- `HAZ-IBTRACS-04` [2026-06-09] **Holland wind profile anchored directly to Vmax** (bug fix) — the pressure-governed profile barely changed as Vmax decayed and overestimated wind inland. `[Holland1980]`
- `HAZ-IBTRACS-05` [2026-06-09] Inland decay per Kaplan & DeMaria (1995) as `--decaimiento-tierra` (R=0.9, Vb=26.7 kt, α=0.095 h⁻¹); US coefficients applied as a **conservative minimum** with best-track. `[KaplanDeMaria1995]`
- `HAZ-IBTRACS-06` [2026-06-09] `--anio-inicial` (recommended 2005) sharply reduces the number of storms processed. [eng]
- `HAZ-IBTRACS-07` [2026-06-05] When the buffer route is used: 100 km over INEGI states, reprojected to EPSG:6372 (so the km buffer is correct). The buffer value is an explicit assumption requiring a reference. `[ref?]` (→ `OQ-HAZ-06`)
- `HAZ-IBTRACS-08` [2026-06-05] Covariates for `λ(estado, año)`: `n_ciclones`, `viento_max_kt`, `pres_min_mb`, `cat_ss_max`, `ace`, `pdi`, `n_landfalls`; `ace`/`pdi` handle multi-event state-years without splitting. [eng]
- `HAZ-IBTRACS-09` [2026-06-05] Each processing assumption requires a reference (buffer, each covariate) — explicitly requested. `[ref?]`
- `HAZ-IBTRACS-10` [2026-06-09] Known issue: CDMX absent from the wind-field panel — discretization artifact (smallest entity, below a 0.5° cell). [eng] (→ `OQ-HAZ-01`)
- `HAZ-IBTRACS-11` [2026-06-05] Requires the 32-entity INEGI shapefile via `--estados` (column `NOMGEO`). [eng]

### HAZ-CENAPRED — socioeconomic impact (`descarga_cenapred.py`, `procesar_cenapred.py`)

- `HAZ-CENAPRED-01` [2026-06-12] `descarga_cenapred.py` with modes `sync/verificar/descargar`, control log and `_procedencia.json`; open event-level base 2000–2015 (CSV) + executive summaries 2016+ (PDF, with new-year discovery). [eng]
- `HAZ-CENAPRED-02` [2026-06-12] `procesar_cenapred.py` emits **two structures** because consumers need different grains: A (λ/severity panel) and B (events for CLIMADA calibration). [eng]
- `HAZ-CENAPRED-03` [2026-06-12] The real header is validated against a `CONCEPTOS` map; a missing required field **fails loudly** with a column report (no blind processing). [eng]
- `HAZ-CENAPRED-04` [2026-06-12] Entities cleaned with `limpieza_cnsf.clasificar_entidad` — same CNSF standard. [eng]
- `HAZ-CENAPRED-05` [2026-06-12] Amounts in **current MXN** (deflate separately, as with CNSF — see `GEN-13`); unmapped subtypes → `__SIN_MAPEO__` with a warning. [eng]
- `HAZ-CENAPRED-06` [2026-06-12] Damage = total at replacement cost, CEPAL/DaLA-adapted methodology — as declared by CENAPRED. `[CEPAL2014]`
- `HAZ-CENAPRED-07` [2026-06-12] Multi-state: **do not split**; panel A excludes multi-state (→ `impacto_multiestado.csv`); B keeps the event as **one** record with `estados = E1|E2|…`. [eng]
- `HAZ-CENAPRED-08` [2026-06-13] `catalogo_fenomenos_climaticos.csv`: filter `en_alcance_climatico == "si"`, **explode by state**, keep damage as the event total (`danio_mdp_evento_total`), `multi_estado` flag (`n_estados >= 2`), municipalities as raw text. [eng]
- `HAZ-CENAPRED-09` [2026-06-13] Encoding: raw files in latin1, outputs in UTF-8. To inspect in Excel, convert CSV→`.xlsx` in Python (a **disposable** view, not in git or the pipeline); the CSV is the source of truth. [eng]

### HAZ-CLIMADA — impact-function calibration (`diseno_calibracion_funciones_impacto_mexico.md`)

- `HAZ-CLIMADA-01` [2026-06-11] Goal: **subnational** (state-level) impact functions replacing CLIMADA's regional "Latin America and Caribbean" one. `[Eberenz2021]`
- `HAZ-CLIMADA-02` [2026-06-11] Perils: tropical-cyclone wind, storm surge, cyclonic rain, independent river flooding. [eng]
- `HAZ-CLIMADA-03` [2026-06-11] Two routes: insured losses (CNSF) vs total losses (CENAPRED), with **LitPop** as the spatial disaggregation base for both. `[Eberenz2020LitPop]`
- `HAZ-CLIMADA-04` [2026-06-11] Hazard generation **frozen** in the CLIMADA pipeline; centroids shared across the four hazards; annual aggregation by state = calibration unit. [eng]
- `HAZ-CLIMADA-05` [2026-06-11] Hierarchical Bayesian model with partial pooling by state in PyMC (optional Stan replication); precomputed surrogate surfaces avoid calling the forward model inside the sampler. [eng]
- `HAZ-CLIMADA-06` [2026-06-11] Cell-level multi-peril union: `f_total = 1 − (1−f_wind)(1−f_surge)(1−f_rain)` against a single total-loss likelihood — eliminates double counting. [eng]
- `HAZ-CLIMADA-07` [2026-06-11] Idealized sigmoidal TC impact function with a `v_thresh` lower bound and 100% upper bound. `[Emanuel2011]`
- `HAZ-CLIMADA-08` [2026-06-11] `v_thresh = 25.7 m/s` fixed; default `v_half = 74.7 m/s`; `ImpfTropCyclone.from_emanuel_usa` as the real constructor. `[Eberenz2021]`
- `HAZ-CLIMADA-09` [2026-06-11] Deflator = INEGI INPC (preferred over World Bank/IMF GDP deflators for domestic MXN series; see `GEN-13`). [eng]
- `HAZ-CLIMADA-10` [2026-06-11] Default timestep 1 h, subject to a formal convergence test before freezing hazards. [eng] (→ `OQ-HAZ-10`)
- `HAZ-CLIMADA-11` [2026-06-11] Urban pluvial flooding **out of scope** in phase 1. [eng]
- `HAZ-CLIMADA-12` [2026-06-11] The total-loss route is a **check** on the insured-loss route, not derived from it. [eng]

### HAZ-DROUGHT — drought (`scraper_sequia.py`, `config/indices/agregacion/validacion_sequia.py`)

- `HAZ-DROUGHT-01` [2026-06-14] Primary continuous index = **SPEI** (includes evapotranspiration, better for climate-change attribution); SPI as robustness/standard; Monitor de Sequía de México (MSM) **complementary** (validation, alignment with declaratorias), not a calibration substitute. `[VicenteSerrano2010]` `[McKee1993]` `[WMO2012SPI]`
- `HAZ-DROUGHT-02` [2026-06-14] Source = ERA5/Copernicus CDS (derived drought indices) + official SPI/SPEI products as benchmarks. [eng]
- `HAZ-DROUGHT-03` [2026-06-14] Modes: `descargar/verificar/calcular/agregar/validar/recuperar/registrar`. [eng]
- `HAZ-DROUGHT-04` [2026-06-14] **Idempotent** downloads: skip existing files unless `--forzar`; provenance = CDS request + version + DOI + sha256 + bytes + date (see `GEN-05`, `GEN-02`). [eng]
- `HAZ-DROUGHT-05` [2026-06-14] `recuperar --objetivo` lands the file with the canonical name and full provenance (vs free `--destino`, which warns if the name won't be recognized); `registrar` mode adopts an on-disk file without network. [eng]
- `HAZ-DROUGHT-06` [2026-06-14] Benchmarks are **non-critical**: if they fail, download continues and `validar` skips them. [eng]
- `HAZ-DROUGHT-07` [2026-06-14] `--shp-estados` (INEGI) for state aggregation; `--anio-inicial/--anio-final`; `--escalas-extra` adds {1, 48} to the base scale set. [eng]

### HAZ-SOURCES — external-source tiering (literature relevance)

- `HAZ-SOURCES-01` [2026-06-05] **Tier 1:** IBTrACS/HURDAT2 (cyclone), Monitor de Sequía + SPI (drought), CENAPRED (socioeconomic impact) — without these there is no attribution. `[Knapp2010]` `[VicenteSerrano2010]` `[CEPAL2014]`
- `HAZ-SOURCES-02` [2026-06-05] **Tier 2:** ERA5/Copernicus, declaratorias (datos.gob.mx), DesInventar. [eng]
- `HAZ-SOURCES-03` [2026-06-05] **Tier 3:** CONAGUA SIH, CHIRPS, CONAFOR/SNIF + FIRMS-MODIS, EM-DAT, Atlas Nacional de Riesgos. [eng]

### HAZ-STOCH — stochastic loss modelling & parametric pricing (planned)

- `HAZ-STOCH-01` [2026-06-05] CNSF data are **aggregated** → mean frequency and severity are recoverable, not the tail shape; individual POT-GPD does not apply; the tail is calibrated with CENAPRED per event. `[McNeil1997]` `[Klugman ref?]`
- `HAZ-STOCH-02` [2026-06-05] Compound-Poisson / Cox (doubly stochastic) `λ(t)` formulations sit on jump-process theory. `[ContTankov2004]` `[Baryshnikov2001 ref?]` `[Burnecki2005 ref?]`
- `HAZ-STOCH-03` [2026-06-05] Framing/vocabulary for catastrophe modelling and physical-risk scenarios. `[NAIC2025]` `[NGFS2024]`


---

## Related
Reads with: [[DATA_CONTRACTS]] (the contracts these decisions imply) · [[OPEN_QUESTIONS]] (what is still undecided) · [[REFERENCES]] (the keys cited here) · [[GLOSSARY]] (terms). By arm: [[CCR_MOC]] · [[MKT_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]
#type/decision
