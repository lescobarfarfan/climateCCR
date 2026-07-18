# OPEN_QUESTIONS — Integrated open items

Only what is genuinely open. When something is resolved, move it to `DECISIONS.md` (dated) and delete
it here (or drop it to "Recently resolved" for brief traceability). IDs follow `OQ-<ARM>-NN`;
integration questions `OQ-INT-NN` come first because they gate the others.

## Table of contents
- **Integration (decide first)** — `OQ-INT-01`–`OQ-INT-08`
- **CCR arm** — `OQ-CCR-02`–`OQ-CCR-08`
- **MKT arm** — `OQ-MKT-01`–`OQ-MKT-11`
- **HAZ arm** — `OQ-HAZ-01`–`OQ-HAZ-17`
- **GEN — housekeeping** — `OQ-GEN-01`

---

## Integration — decide before drafting the methodology chapter

- `OQ-INT-01` ✅ **Largely resolved** by `INT-09`. The unifying question: *find, test, and quantify a relationship between financial asset prices / risk factors and climate events, and measure via Monte Carlo how financial risk changes once climate is incorporated.* HAZ estimates the link; the jump channel injects it; MKT+PIMPA simulate; climateCCR reads out the change. **Residual:** the precise hypothesis wording and the headline empirical claim for the manuscript (couples with `OQ-INT-02`).
- `OQ-INT-02` **Primary risk object.** The headline metric of the *change-under-climate* — CCR (EE/PE/EPE/CVA, the spine), market (VaR/ES), or loss (parametric). All three are hosted (`INT-06`); `INT-11` makes CCR the framework, but which metric leads the results chapter (and which are secondary/robustness) is still to fix.
- `OQ-INT-03` ✅ **(a)/(b) resolved provisionally** by `INT-13` (2026-07-02; the channel is built, `INT-14`/`DC-CCR-SIM-2`): homogeneous Poisson `λ`, **both targets** (HW1F rate + GBM price) with shared event times, jumps independent of the diffusion; richer options (trajectory `λ(t)`, Cox/doubly-stochastic, correlated transmission, cross-target mark dependence) are **desirable to-dos** reachable through the built interface without engine change. **Still open:** (c) is there a defensible **NGFS↔SSP** mapping (`DC-XWALK-6`), or do transition (NGFS, fixed/trajectory rate) and physical (HAZ jump) channels stay deliberately distinct? (couples `OQ-CCR-03`, `OQ-MKT-04/05`); and swapping the placeholder `λ`/marks for HAZ estimates (`OQ-INT-07`).
- `OQ-INT-04` **Asset universe(s).** Confirm the concrete portfolios the GBM/HW1F engines calibrate to: sovereign/corporate bonds (MKT), insurance lines (HAZ), equities/derivatives/netting sets (CCR). BMV equities are a known scope risk (small universe); the data layer is source-agnostic, but calibration needs concrete targets.
- `OQ-INT-05` ✅ **Resolved** (`INT-02`): the integrated project keeps the name **`climateCCR`** (distribution, repo, import package). The broad rename to `climrisk` was rejected — that name is already taken by an existing UNAM package.
- `OQ-INT-06` **Language convention at the bilingual boundary.** Public Python APIs in English; Spanish data identifiers verbatim (`INT-07`). Confirm where the boundary sits for new code (e.g. do the HAZ pipelines keep Spanish function names internally, exposing English wrappers?).
- `OQ-INT-07` **Jump-mark estimation — the loss→mark translation residual.** ✅ **Estimation layer built 2026-07-16** (`INT-16`, `HAZ-STOCH-04`): `λ` (level + trend, with exact CI and LR test) and the lognormal severity shape are estimated from the CENAPRED panel; `to_mark_sampler(K)` maps losses onto marks with `σ` transferring exactly. **Still open:** (a) **the scale `K`** — the target series / portfolio loss-absorption size turning a loss in MDP into a log-return or rate mark (couples `OQ-INT-02/04`); the implied route is loss-to-price translation — ratify vs market-reaction calibration; (b) **INPC deflation** (`GEN-13`) — the +28%/yr nominal severity trend includes ~4–5%/yr inflation (estimator takes an injectable deflator; INEGI wiring pending); (c) the empirical shape is now **measured, not assumed** (replaces the `[IPCC_AR6]`-motivated conjecture): major-event arrivals +9.6%/yr (p<.001) and unthresholded severity +28%/yr (p<.001) — trajectory `λ(t)` enters with no engine change (`INT-13`), but a severity *trend* still needs the step-aware `MarkSampler` extension (`sample` is time-blind, noted 2026-07-05); (d) **which event-set variant leads** (`HAZ-STOCH-04`) — `mayores_100mdp` (λ≈19.6/yr, σ=1.21) is the natural jump-triggering set, to confirm with `K`. Exposure-growth vs climate-signal attribution in the trends is a manuscript caveat.
- `OQ-INT-08` **Scope realism vs the ~8-month envelope.** The jump-diffusion spine is one coherent deliverable; decide which extensions (CVA, parametric pricing, weather derivatives, the credit overlay, signatures) are in-scope vs appendix vs future work. Re-baseline `notes/plan/PROJECT_PLAN.md`.

## CCR arm

- `OQ-CCR-02` **Tidy time-series schema, final form.** Ratify the `PROPOSED` columns in `DATA_CONTRACTS.md` `DC-CONV-9`/`DC-CCR-DATA-1`; decide whether a wide convenience view is needed and how curve tenors are encoded.
- `OQ-CCR-03` **First climate-scenario connector** to ship end-to-end — NGFS, the IIASA database, IPCC-SSP, or Copernicus C3S. Only one is needed to clear the Phase-1 DoD. (Couples with `OQ-INT-03`.)
- `OQ-CCR-04` **Where EPE / CVA live** — inside the existing evaluator, or a thin new `risk/ccr/xva.py`? (← `CCR-RISK-01`)
- `OQ-CCR-05` **RQ1 design details:** climate-event labelling / narrative signal (event-window definition, scenario tags); the leakage-aware walk-forward CV split; and a **pre-registered go/no-go criterion** for Path A vs Path B (decide *before* seeing results to avoid hindsight bias). Most open-ended; gates RQ1.
- `OQ-CCR-06` ✅ **Location resolved** — the PIMPA prototype CSVs live in `tests/fixtures/pimpa/` (the regression fixture; `CCR-MIG-05`, `DC-CCR-RISK-2`). **Still open:** a second code-review pass on the IRS pricer / `Curve` / `Surface` / `CorrelationMatrix` internals before relying on them — the migration preserved behaviour but did not audit their correctness (the `Surface` interpolator was just swapped off `interp2d`, `CCR-MIG-04`).
- `OQ-CCR-07` **Where the randomized signatures fit, now that HAZ carries the empirical climate→price link (`INT-11`).** Options: (a) a **complementary detection/validation** method — use signatures to test whether a climate signal is present in price series independently of the hazard panels; (b) a **robustness probe** on the jump channel; (c) repositioned to future work. Decide before investing in fixing/extending the reservoir beyond the `CODE_REVIEW` repairs. Couples with `OQ-INT-02/08`.
- `OQ-CCR-08` **Should PIMPA's PE floor at 0?** The engine computes PE as a **raw** quantile of portfolio value, so a net-liability (short) book yields a **negative PE99** with EE=0 (observed: fixture counterparty 26). Standard CCR PFE is `quantile(max(MtM, 0)) ≥ 0`. Confirm whether this is an intended PIMPA convention or a defect to fix; affects the headline CCR metric (couples with `OQ-INT-02`). Captured as-is in the golden baseline (`CCR-MIG-05`, `DC-CCR-RISK-2`).

## MKT arm

- `OQ-MKT-01` **SIE compounding convention — final empirical confirmation.** Decision is simple-interest Act/360 (`MKT-SIE-04`); run the documented check (plug published `r^F_T` into both forms vs the index ratio) once on real data and record the result.
- `OQ-MKT-02` **λ estimation for Mexico.** Method/data for the market price of interest-rate risk are not fixed (historical excess-return regression vs Yasuoka's forward-rate approach). Affects all P-measure stress output. (← `MKT-MEAS-01`)
- `OQ-MKT-03` **Long-end densification.** Only two pillars in 10–30y; decide whether to pull off-the-run Bonos M from CF300, and for which portfolios it's necessary. (← `MKT-CURVE-04`)
- `OQ-MKT-04` **NGFS scenario-vintage mix.** Short-term (May 2025) for 1–5y vs long-term (REMIND/GCAM/MESSAGE) beyond 5y — confirm the splice point and how to blend the two rate paths without a kink. (← `MKT-NGFS-03`)
- `OQ-MKT-05` **NGFS baseline for the shock.** `Δr = NGFS − baseline` needs a fixed baseline path: NGFS Current-Policies, IMF WEO, or market-implied forward? Also confirm `[Yasuoka2018]`/`[JamesWebber2000]` editions.
- `OQ-MKT-06` **Stripping scope.** Extend the Goal-Seek strip to all six Bonos buckets (full-curve) vs the `Bonos_0_3` pillar only — the workbook currently demonstrates one bucket.
- `OQ-MKT-07` **Weather derivatives — chapter or context?** Confirm whether this becomes an applied pricing/hedging chapter (temperature OU model on Mexican stations) or remains literature review. (← `MKT-WD-01`)
- `OQ-MKT-08` **R1–R4 band definitions.** The dashboard hazard risk-level thresholds (what distinguishes R1 from R4 per hazard) are unspecified — needed for reproducibility and heat-map cutoffs.
- `OQ-MKT-09` **Hazard data source for Mexican municipalities.** Which dataset populates `fenomeno × año × escenario` at `clave_mpio` grain (ATLAS Nacional de Riesgos / CMIP6 downscaled / commercial)? (Couples with the HAZ pipelines — possible reuse.)
- `OQ-MKT-10` **`industria` ↔ GICS/SCIAN crosswalk.** The dashboard's `industria` field needs a fixed mapping to GICS (carbon intensity) and/or SCIAN (Mexican classification) for the credit overlay. (← `DC-MKT-CREDIT-5`)
- `OQ-MKT-11` **Is the climate-credit overlay (Strand C) in scope, or context only?** It bridges the rate and physical strands but adds substantial data burden (emissions, geolocation, CDS). (Couples with `OQ-INT-02`.)

## HAZ arm

- `OQ-HAZ-01` **CDMX discretization artifact** in the IBTrACS wind-field panel — CDMX drops out (smaller than a 0.5° cell). Fix with a finer grid or point-based attribution for small entities. (← `HAZ-IBTRACS-10`)
- `OQ-HAZ-02` **Exact value separating SIPAC in autos** — locate the cut (sentinel/threshold) that distinguishes the SIPAC block.
- `OQ-HAZ-03` **`MONEDA` normalization (CNSF)** — requires Banxico FX; now wireable from the MKT/SIE pipeline (`DC-XWALK-5`). (← `HAZ-CLEAN-CNSF-10`)
- `OQ-HAZ-04` **Confirm the year convention in CNSF** — verify that **year of occurrence** (`OCURRIDO`), not of report, is used in each sector.
- `OQ-HAZ-05` **Exact list of agro-sector causes** — confirm against the real catalogs. (← `HAZ-CLEAN-CNSF-11`)
- `OQ-HAZ-06` **Validate IBTrACS covariates** against known events (Odile 2014 in BCS, Otis 2023 in Guerrero) — run on the author's machine. (← `HAZ-IBTRACS-07/09`)
- `OQ-HAZ-07` **Stochastic textbooks/papers to confirm:** `[Klugman]` (edition + URL), `[Baryshnikov2001]`, `[Burnecki2005]`. (see `REFERENCES.md` §99)
- `OQ-HAZ-08` **CLIMADA flood-route references:** exact **Hazus** manual edition and **`[Wagenaar2018]`** journal/DOI.
- `OQ-HAZ-09` **Access/coverage to confirm:** CONAFOR/SNIF, NASA FIRMS-MODIS, Munich Re NatCatSERVICE / Swiss Re *sigma*, Dartmouth FO / Global Flood Database; re-confirm `[WMO2012SPI]` URL on access.
- `OQ-HAZ-10` **Timestep convergence test** (1 h default) before freezing the CLIMADA hazards. (← `HAZ-CLIMADA-10`)
- `OQ-HAZ-11` **Wind-radii attribution refinement** vs the fixed buffer (future improvement). (← `HAZ-IBTRACS-07`)
- `OQ-HAZ-12` **Stochastic-model calibration — residual routes.** ✅ **Compound-Poisson route built** (`INT-16`/`HAZ-STOCH-04`, 2026-07-16: Poisson `λ` + log-linear trend, lognormal severity, from CENAPRED). **Still open:** Cox / doubly-stochastic `λ(t)` on covariates (the IBTrACS wind panel, `DC-HAZ-IBTRACS-3`; interface-ready per `INT-13`); the CNSF insured-loss route as the cross-check (`HAZ-CLIMADA-12` pattern, `HAZ-STOCH-01`); tail refinement beyond lognormal (POT-GPD on CENAPRED per-event losses). (Couples `OQ-INT-07`.)
- `OQ-HAZ-13` **Parametric-instrument pricing** — downstream HAZ deliverable.
- `OQ-HAZ-14` **Integration/testing of the remaining CNSF sectors** through the scraper pipeline.
- `OQ-HAZ-16` **Re-anchor HAZ pipeline default data roots.** The scripts' CLI defaults and module constants still name the legacy CWD-relative `datos/datos_<FUENTE>/…` (e.g. `scraper_cnsf --out-dir`, `config_sequia.DIR_*`, `procesar_cenapred.DIR_BASE`), but the data now lives at `data/hazard_mx/` (`GEN-24`). Route them through `infra.ProjectPaths`/configs (`GEN-08`); until then run pipelines with explicit `--root`/`--out-dir` flags. Couples `DC-HAZ-CNSF-1`, `DC-HAZ-DROUGHT-1`. [eng]
- `OQ-HAZ-17` **Agro magnitude-correction residuals** (`HAZ-CLEAN-CNSF-12/13`): (a) manual review of the **132 weak-signature rows** (prima ≤ 0, no confirming own history — e.g. arándano/agave "por planta" with `UNIDADES ASEGURADAS` = 0) deliberately left uncorrected in the copies (the corrector lists them on each run); (b) external confirmation of the systemic ×FIX error (CNSF fe de erratas / INAI request; insurer attribution is impossible from the files); (c) intra-year FIX refinement — the annual-average ÷FIX carries ±5–10% level uncertainty in 2022–2024 (per-row issue-date FIX would remove it; the FX series is wireable via `DC-XWALK-5`); (d) the standing triage queue: `error_probable` findings on the corrected emisión (323) beyond the corrected rows, in `results/inspeccion/` (`GEN-27`).

## GEN — housekeeping (small, quick tasks)

- `OQ-GEN-01` **Canon hard-wrap unwrap** (the residual of the `GEN-23` back-fill; the rest closed 2026-07-11 — (a) notes' backtick math → LaTeX done, notes unwrapped; (c) stray root files gone; (d) closed as accepted: the bat-mangled messages already on `origin` stand — a main-branch history rewrite + force-push is not worth the breakage): the canon (`context/`) is still hard-wrapped at ~100 chars and renders with mid-sentence line breaks in Obsidian — a `/compact-canon` candidate; decide whether the diff noise is worth it there. [eng]

---

## Recently resolved (traceability)

- ~~Whether the three arms relate~~ → framed: CCR is the spine, MKT and HAZ feed it (`INT-01`); the **research narrative** is now also resolved (`INT-09/10/11`): one machine that tests the price↔climate relationship via a HAZ-calibrated jump injected into GBM/HW1F diffusions, read out by Monte Carlo.
- ~~How the HAZ panels reach the financial engine~~ → the **climate jump channel** (`INT-10`, `DC-CCR-SIM-2`, `DC-XWALK-4`): `λ` + impact → jump-diffusion. Residual estimation detail is `OQ-INT-07`.
- ~~Path A vs Path B framing~~ → subsumed by `INT-12`: HAZ→jump = concrete Path A; fixed parameter shift = Path B; both via one injection hook. Signatures' role → `OQ-CCR-07`.
- ~~Package name should change~~ → **keep `climateCCR`** for the integrated project (`INT-02`); the broad rename to `climrisk` was rejected (name already taken by a UNAM package).
- ~~CCR risk-evaluator API name~~ → keep `CCR_Valuation_Session` verbatim, behaviour-unchanged migration (`CCR-MIG-05`, resolves `OQ-CCR-01`).
- ~~Route the MC draw through `infra` — preserve stream or re-baseline?~~ → **preserve the stream** via `infra.get_legacy_rng` (`RandomState(seed)` ≡ SciPy int-seed); baseline unchanged (`CCR-MIG-08`, resolves `OQ-CCR-09`).
- ~~Jump-channel knobs: which target, what dependence, Poisson vs Cox (`OQ-INT-03` a/b)~~ → fixed provisionally and **built** (2026-07-02): homogeneous Poisson, both targets with shared events, independent of the diffusion; trajectory `λ(t)` / Cox / correlated transmission kept as interface-ready to-dos (`INT-13/14`, `DC-CCR-SIM-2`). Residuals stay in `OQ-INT-03` (c) + `OQ-INT-07`.
- ~~Meaning of `NU` (CNSF)~~ → unlocated → `No Disponible` (`HAZ-CLEAN-CNSF-01`).
- ~~CENAPRED vs CLIMADA output structures differ~~ → they do; processor emits both A + B (`HAZ-CENAPRED-02`).
- ~~Pressure-governed Holland-profile bug~~ → anchor to Vmax (`HAZ-IBTRACS-04`).
- ~~Drought-index choice~~ → SPEI primary, SPI robustness, MSM complementary (`HAZ-DROUGHT-01`).
- ~~NGFS policy rate used as a level~~ → used as a shock source (`MKT-NGFS-01`).
- ~~1-year curve gap~~ → 364-day Cetes pillar (`MKT-CURVE-01`).
- ~~CNSF test-harness import bug (`OQ-HAZ-15`)~~ → resolved (`HAZ-SCRAPER-CNSF-09`, 2026-07-11): root-conftest `sys.path` shim + origin-sandbox portability fixes; tests pass against the real 2024 Incendio sample from `data/hazard_mx` (`GEN-24`); collection-safe without the `[haz]` extra.
- ~~Vault formatting back-fill — (a) note math, (c) stray files, (d) mangled pushed messages~~ → done/closed 2026-07-11; `OQ-GEN-01` slimmed to the canon unwrap (a `/compact-canon` task).
- ~~Jump-channel `λ`/marks are placeholders; stochastic calibration not started (`OQ-HAZ-12` original form)~~ → **first real estimates 2026-07-16** (`INT-16`, `HAZ-STOCH-04`): per-variant Poisson `λ` + trend and lognormal `σ` from CENAPRED; residuals = the loss→mark scale `K`, INPC deflation, step-aware marks (`OQ-INT-07`) and the Cox/CNSF/tail routes (`OQ-HAZ-12`).


---

## Related
Reads with: [[DECISIONS]] (resolved items move there) · [[DATA_CONTRACTS]] (the contracts they gate) · [[WORKFLOW]] (the ritual that closes them). By arm: [[CCR_MOC]] · [[MKT_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]
#arm/int #type/open #status/open
