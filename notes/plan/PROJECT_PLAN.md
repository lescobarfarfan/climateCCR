# Project plan — tasks & rough time estimates

*Working note for the gitignored `notes/` folder.*

**Estimating assumptions (adjust to your reality):**
- Part-time thesis effort alongside a full-time job: **~15 productive hours/week**, within an **~8-month**
  (≈34-week) envelope. Estimates below are **calendar weeks at ~15 hrs/week**.
- Estimates are **rough planning figures**, not commitments. The two research phases (3 & 4) carry
  genuine uncertainty because they depend on whether RQ1's effects are detectable — build in slack.
- Thesis **writing overlaps** the build (don't leave it to the end): keep a running methods/results
  document from Phase 0.
- "DoD" = Definition of Done.

---

## Phase 0 — Foundation: packaging, infra, PIMPA migration  ·  ~2–3 weeks
The highest-leverage phase: it removes the import pain and makes everything reproducible.

| # | Task | Est. |
|---|---|---|
| 0.1 | Create repo, `src/climateCCR` skeleton, `pyproject.toml`, `environment.yml`, `.gitignore`, pre-commit (black/ruff) | 2–3 d |
| 0.2 | `infra`: `set_seed`, YAML config loader, logger, run-manifest writer | 3–4 d |
| 0.3 | Move PIMPA into `climateCCR.risk` **unchanged in behaviour**; add `__init__.py`; fix `iteritems`→`items` and stray imports | 2–3 d |
| 0.4 | Lock a **regression test** reproducing PIMPA's EE/PE on the prototype CSVs under a fixed seed | 2 d |
| 0.5 | `pip install -e .`; confirm clean imports from a notebook and a script | 0.5 d |

**DoD:** `import climateCCR` works anywhere; PIMPA runs from the package and the regression test is green.

---

## Phase 1 — Data layer  ·  ~2–3 weeks

| # | Task | Est. |
|---|---|---|
| 1.1 | `data` interface + common tidy time-series schema; immutable `data/raw/` cache | 3 d |
| 1.2 | Market/FX price connector (Yahoo/Google Finance) for the chosen universe | 2–3 d |
| 1.3 | Rates/curve data ingestion for HW1F inputs | 2 d |
| 1.4 | Climate/scenario connectors (NGFS / IIASA database; IPCC-SSP; Copernicus C3S) — at least one working end-to-end | 3–5 d |
| 1.5 | Caching + provenance logging; small fixtures for tests | 1–2 d |

**DoD:** a config-driven pull of price, rate, and one climate-scenario dataset, cached and logged.

---

## Phase 2 — Calibration + real-data end-to-end  ·  ~2 weeks

| # | Task | Est. |
|---|---|---|
| 2.1 | `calibration.fit_gbm` (drift/vol from log-returns; MLE) → emits PIMPA `'direct_input'` objects | 2–3 d |
| 2.2 | `calibration.fit_hull_white` (`alpha`, `sigma`, curve/`theta` fit) | 3–4 d |
| 2.3 | Promote `processes` + `simulation` out of `scenario_generation` (keep ABCs) | 2 d |
| 2.4 | **End-to-end smoke test:** real data → calibrate → simulate → PIMPA EE/PE | 2–3 d |

**DoD:** PIMPA produces an exposure profile on **real public data** (no prototype CSVs), reproducibly.

---

## Phase 3 — RQ1: signatures + inference (research core)  ·  ~4–6 weeks *(high uncertainty)*

| # | Task | Est. |
|---|---|---|
| 3.1 | Move rand-sig into `climateCCR.signatures`; fix solver arg/shape bugs; **seed** the reservoir; add a fixed-seed reproducibility unit test (see code review C1–C4) | 4–5 d |
| 3.2 | Feature pipeline: path → (randomized) signature features for equities/macro series | 3–4 d |
| 3.3 | Define the climate-event labelling / narrative signal (event windows, scenario tags) | 3–5 d |
| 3.4 | `inference`: time-series classification + regression of risk factors on climate signals | 1–1.5 wk |
| 3.5 | **Leakage-aware** backtesting / walk-forward CV; significance tests | 1 wk |
| 3.6 | Decision checkpoint: are effects detectable? → choose Path A (RQ2) or fallback | 1–2 d |

**DoD:** a defensible empirical answer to RQ1 with cross-validated evidence and the go/no-go decision.

---

## Phase 4 — RQ2 / fallback: propagation & sensitivity  ·  ~3–4 weeks

| # | Task | Est. |
|---|---|---|
| 4.A | *(Path A)* Calibrate the detected effect; add an event-injection hook to `simulation`; re-run PIMPA | 1.5–2 wk |
| 4.B | *(Fallback)* Map climate scenarios to **justified** parameter perturbations (GBM drift, HW1F curve); document the rule | 1–1.5 wk |
| 4.1 | Add EPE / Effective EPE, and CVA (with optionally climate-conditioned credit spread) to `risk` | 4–6 d |
| 4.2 | Monte Carlo **sensitivity analysis**: how CCR metrics move across scenarios (fixed seeds, manifests) | 1 wk |

**DoD:** quantified change in CCR metrics under climate scenarios, fully reproducible with logged params.

---

## Phase 5 — Visualization & results consolidation  ·  ~1.5–2 weeks

| # | Task | Est. |
|---|---|---|
| 5.1 | `viz`: style config + core plots (exposure fans, distributions, calibration & test diagnostics) | 1 wk |
| 5.2 | Reproducible figure/table pipeline driving every thesis exhibit from manifests | 3–4 d |

**DoD:** every figure in the thesis regenerates from a single command + a config/seed.

---

## Phase 6 — Writing & defense prep  ·  ~4–6 weeks (overlapping from Phase 0)
Methods and literature written alongside the build; final integration, proofing, and defense slides
at the end.

---

## Rollup

| Phase | Theme | Weeks (part-time) |
|---|---|---|
| 0 | Foundation / packaging | 2–3 |
| 1 | Data | 2–3 |
| 2 | Calibration + E2E | ~2 |
| 3 | RQ1 (research core) | 4–6 |
| 4 | RQ2 / fallback | 3–4 |
| 5 | Visualization | 1.5–2 |
| 6 | Writing (overlapping) | 4–6 |
| | **Build subtotal (0–5)** | **~15–20 weeks** |

Add a ~20% contingency buffer on the research phases. Sequence the *critical path* as
**0 → 1 → 2 → 3 → 4 → 5**; writing (6) and the literature review run in parallel throughout.

**Fit to your 8 months:** the build subtotal (~15–20 weeks) plus a ~20% research-phase buffer lands
well inside ~34 weeks, leaving comfortable slack for write-up and the defense.

---

## Immediate next actions (this week)
1. Approve the `src/climateCCR` layout and confirm the package name.
2. I scaffold Phase 0.1–0.2 (`pyproject.toml`, `infra`, repo skeleton) so you can `git init` and commit.
3. Pick the **first market/universe** for the data layer (BMV subset, or a broader proxy) so calibration
   has a concrete target.

## Related
[[CCR_MOC]] · Home: [[_INDEX]]

#arm/ccr #type/plan
