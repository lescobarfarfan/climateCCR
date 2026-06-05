# Climate-Narrative-Aware Counterparty Risk Analysis

**MSc Quantitative Finance thesis project — University of Zurich & ETH Zurich**

> **Package name:** `climateCCR`. The existing **PIMPA**
> engine becomes the `risk` subpackage; the existing **randomized-signature** code becomes the
> `signatures` subpackage.

This document is the canonical map of the project: research questions, theoretical framework,
package architecture, an inventory of the **code that already exists**, the data sources, and the
engineering conventions that guarantee reproducibility. It is meant to be read first by any
collaborator (human or AI) before touching code, and kept in sync with the repository.

---

## 1. Aim and research questions

The project develops a mathematically and financially grounded framework to incorporate
**climate-change-related narratives and scenario information** into a standard financial
**risk-analysis pipeline**, with primary focus on **counterparty credit risk (CCR)** arising from
the management of bonds, derivatives, and swaps.

- **RQ1 — Detection / distillation.** Do techniques from **rough path theory** (the signature
  transform, randomized signatures) combined with **machine learning** (time-series
  classification, regression) help to *identify and distill* the impact of climate-related events
  on (a) individual equity prices and/or (b) macro-financial risk factors that drive the broader
  market (interest rates, equity indices, FX rates)?

- **RQ2 — Modelling / propagation.** *If* such effects are found, can we **calibrate a model of the
  materialization of these events** and inject their occurrence into a risk analysis via **Monte
  Carlo simulation** of an asset's (or portfolio's) risk factors, observing the resulting change in
  CCR metrics?

- **Fallback.** *If* clean effects are **not** found, derive a **robust, justifiable rule** for
  perturbing the parameters of standard risk-factor models — e.g. shifting the **drift** of a
  geometric Brownian motion, or the term structure / mean-reversion of a **Hull–White one-factor**
  model — under climate scenarios, and measure the **sensitivity** of the portfolio's risk metrics.

**Market scope.** Preferred application: the **Mexican market** (BMV). Because the local equity
universe is small, the data layer is source-agnostic so broader markets can be swapped in without
changing the pipeline. **All calibration uses publicly available data; the final sensitivity
analysis relies on controlled random simulation.**

---

## 2. Theoretical and methodological framework

Exact citations live in §9 and in the PDFs attached to the project knowledge base, which are
authoritative over any inline mention here.

- **Rough path theory & signatures.** The signature transform as a faithful, hierarchical feature
  map of a path; log-signatures; the universal-nonlinearity property that makes linear functionals
  on signatures expressive. Feature backbone for RQ1.
- **Reservoir computing & randomized signatures.** Randomized signatures as a finite-dimensional,
  training-free reservoir approximating the signature's expressive power at low cost. The project
  already prototypes the method of **Compagnoni et al. (2023),** *On the Effectiveness of
  Randomized Signatures as Reservoir for Learning Rough Dynamics* (attached).
- **Stochastic modelling of risk factors.** Brownian motion, geometric Brownian motion (with a
  term-structure of volatility), and the Hull–White one-factor short-rate model — **all already
  implemented** (see §4.1). Extensible to jump / stochastic-volatility dynamics for event modelling.
- **Counterparty credit risk.** Exposure simulation over netting sets with variation-margin
  collateral and a margin period of risk (MPOR); Expected Exposure (EE) and Potential Exposure (PE)
  profiles — **already implemented.** Expected Positive Exposure (EPE), Effective EPE, and Credit
  Valuation Adjustment (CVA) are natural, currently-missing extensions.
- **Climate scenarios.** Transition vs. physical risk; the NGFS scenario framework and the
  IIASA-hosted scenario database; IPCC / SSP–RCP pathways; Copernicus C3S observational data.

---

## 3. Architecture and import strategy

### 3.1 The import problem, solved

**Root cause (confirmed in both codebases):** neither PIMPA nor the randomized-signature code ships
`__init__.py` files or a `pyproject.toml`; PIMPA's data path is current-working-directory-relative
(`GLOBAL_DATA_PATH = 'data/'`), and the randomized-signature tests rely on `sys.path.append("..")`.
That is precisely why imports only work from one directory.

**Fix:** package everything as one installable distribution using a **`src/` layout**, installed in
**editable mode** (`pip install -e .`) into a dedicated environment. After a one-time install, every
module imports cleanly from anywhere — notebook, test, or pipeline — with no path hacks:

```python
from climateCCR.simulation import MultiRiskFactorSimulation
from climateCCR.processes import GeometricBrownianMotion, HW1F
from climateCCR.calibration import fit_gbm, fit_hull_white      # NEW (statistical calibration)
from climateCCR.risk import CCRValuationSession, Portfolio       # was PIMPA
from climateCCR.signatures import RandomisedSignature            # was pyrandsigSDE
```

### 3.2 Target repository layout

```
thesis-climateCCR/                 # git repository root
├── pyproject.toml               # declares `climateCCR`; enables editable install
├── environment.yml              # pinned conda env (or requirements.txt)
├── README.md                    # this file
├── .gitignore                   # excludes data/, results/, secrets, caches (notes/ is tracked)
├── configs/                     # YAML experiment configs (replaces global_parameters.py)
├── data/                        # gitignored; raw/interim/processed
├── results/                     # gitignored; figures, tables, run manifests, logs
├── notes/                       # TRACKED; working notes, code reviews, phase guides, the plan
├── notebooks/                   # exploration only — never the source of truth
├── pipelines/                   # thin run-scripts wiring modules end-to-end
├── tests/                       # pytest unit + integration tests
└── src/
    └── climateCCR/
        ├── __init__.py
        ├── infra/               # config · logging · seeds · run manifests (NEW)
        ├── data/                # source-agnostic retrieval, schema, caching (NEW)
        ├── processes/           # RiskFactorEvolution: BM, GBM, HW1F (FROM PIMPA)
        ├── calibration/         # statistical estimators from historical data (NEW)
        ├── simulation/          # MultiRiskFactorSimulation engine (FROM PIMPA)
        ├── signatures/          # (randomized) signatures + readout (FROM rand-sig code)
        ├── inference/           # hypothesis tests, ML, regression, backtest, CV (NEW)
        ├── risk/                # PIMPA: pricers, trades, portfolio, CCR evaluator (FROM PIMPA)
        └── viz/                 # publication-ready plotting (NEW)
```

### 3.3 Data flow (how the modules connect)

```
                         ┌─────────────────────────────────────────────┐
                         │                infra                         │
                         │   (config · logging · seeds · run manifests) │
                         └─────────────────────────────────────────────┘
                                   ▲ used by every module ▲

  data ──► calibration ──► simulation ──► risk (PIMPA) ──► viz
   │            ▲             ▲   (processes define the dynamics)
   │            │             │
   │            │   scenario-conditioned parameter perturbation
   │            │   (GBM drift shift, HW1F curve/mean-reversion shift) ◄── climate scenarios
   │            │
   └──► signatures ──► inference  (does a climate narrative move prices/macro?)
                          │
                          └──► feeds the detected effect (RQ2) OR the justified
                               perturbation rule (fallback) into calibration / simulation
```

**Path A (RQ1+RQ2):** `data → signatures → inference` detects/distills a climate-event impact;
that impact is calibrated and **injected into `simulation`**, whose paths flow through **PIMPA** to
produce shifted CCR metrics.
**Path B (fallback):** if `inference` cannot isolate a clean effect, climate scenarios map to
**justified perturbations of model parameters**, are re-simulated, and the **sensitivity** of the
CCR metrics is reported.

---

## 4. Existing code inventory and module specifications

### 4.0 What already exists (read this before re-implementing anything)

**PIMPA — a working Basel-III-style CCR exposure engine.** Clean object-oriented design with
abstract base classes. Subpackages and their key classes:

- `data_objects/` — `RiskFactor` (dataclass mapping a name to its evolution model), `SimulatedData`,
  `SimulatedHW1FCurve`.
- `market_data_objects/` — `Curve`, `Surface` (implied-vol), `CorrelationMatrix`, `MarketDataBuilder`
  (loads CSV market data, curves, surfaces, correlation/covariance).
- `scenario_generation/` — `RiskFactorEvolution` (ABC) with concrete `BrownianMotion`,
  `GeometricBrownianMotion` (constant **or** term-structure volatility), `HW1F` (simulated via the
  Andersen–Piterbarg short-rate scheme); `MultiRiskFactorSimulation` draws **correlated** Gaussian
  increments (`scipy multivariate_normal`, **seeded** by `random_state`) and dispatches per factor.
- `pricing_models/` — `PricingModel` (ABC), `InterestRateSwapPricer`, `EquityEuropeanOptionPricer`
  (Black–Scholes, sticky-strike).
- `trade_models/` — `Trade` (ABC), `InterestRateSwap`, `EquityEuropeanOption`, `Portfolio`
  (trade inventory, netting sets, variation-margin collateral agreements with thresholds + MTA).
- `evaluators/` — `CCR_Valuation_Session`: the orchestrator. Builds Basel default + close-out grids
  with a margin period of risk, calibrates models, generates scenarios, prices trades, aggregates
  MtM over netting sets, applies collateral, and computes **uncollateralised & collateralised EE**
  and **PE at quantiles** (default 99%).
- `utils/` — calendar/date utilities, notebook helpers.
- `data/` — CSV prototype dataset: market data, portfolio (counterparties / desks / positions),
  pre-calibrated model parameters, risk-factor attribute mapping, and `configuration/global_parameters.py`.

> **Important:** PIMPA performs **no statistical calibration** — it reads *pre-calibrated* parameter
> CSVs via `calibration_method='direct_input'`. The historical-data calibration module is genuinely
> new work (see §4.4). PIMPA also computes EE/PE but **not** EPE/Effective-EPE/CVA.

**Randomized-signature code (`pyrandsigSDE`).** Implements the Compagnoni et al. (2023) reservoir:

- `signatures/` — `Signature` (ABC) and `RandomisedSignature`, the reservoir recursion
  `Z_i = Z_{i-1} + Σ_k σ(A_k Z_{i-1} + b_k) dX^k_i` with random `A`, `b`, `z0`.
- `sde_solver/` — `SDESolver` (ABC) and `RandomizedSignatureSDESolver`: a **Ridge** linear readout
  on the reservoir state (reservoir computing = random reservoir + trained linear map).
- `control_process/` — `ControlProcessEvolution` (ABC), `BrownianMotion`, `GeometricBrownianMotion`.
- `utils/utilities.py` — calendar utilities **duplicated** from PIMPA.

> **Important:** this prototype has known correctness and reproducibility bugs (argument-signature
> mismatches in the solver, an unseeded reservoir, 2D/3D shape inconsistencies, a missing
> `simulate_random_increments`). These are catalogued with fixes in `notes/CODE_REVIEW.md` and must
> be resolved before the code is used for thesis results.

### 4.1 `processes` — stochastic-process definitions *(exists in PIMPA `scenario_generation`)*
Promote `RiskFactorEvolution` + BM/GBM/HW1F to a first-class layer; keep the clean ABC interface
(`mean`, `volatility`, `calibrate`, `simulate`, `get_dependencies`). The GBM `drift` and HW1F curve
inputs are the exact knobs the fallback perturbs.

### 4.2 `simulation` — Monte Carlo engine *(exists in PIMPA)*
Promote `MultiRiskFactorSimulation`. Already correlated and seeded. Add an interface for injecting a
calibrated climate-event component (Path A) or perturbed parameters (Path B).

### 4.3 `risk` (PIMPA) — valuation & CCR metrics *(exists; extend)*
Keep pricers, trades, portfolio, collateral, and the evaluator. Extensions: add **EPE / Effective
EPE** aggregation (cheap given the existing exposure arrays) and **CVA** (needs hazard-rate / default
curve + LGD + discounting). Decide whether these live in the evaluator or a thin `risk/xva.py`.

### 4.4 `calibration` — statistical estimation *(NEW — does not exist yet)*
Estimate process parameters from historical data produced by `data`, returning objects that PIMPA's
`'direct_input'` path can consume directly (so the engine is untouched). GBM drift & volatility;
HW1F `alpha`, `sigma`, and a `theta(t)` / initial-curve fit. Methods: MLE / log-likelihood, least
squares. This is the bridge that lets PIMPA run on **real public data** instead of prototype CSVs.

### 4.5 `signatures` — rough-path features *(exists; fix & extend)*
Repair the randomized-signature solver per `notes/CODE_REVIEW.md`; make the reservoir **seeded** and
reproducible; expose a clean `fit`/`transform` API producing features for `inference`.

### 4.6 `data` — retrieval, schema, caching *(NEW)*
Source-agnostic ingestion: market/price data (Yahoo/Google Finance, public); climate & transition
scenarios (NGFS, IIASA database, IPCC/SSP, Copernicus C3S); optional paid feeds behind the same
interface. Common tidy time-series schema; immutable raw cache in `data/raw/`.

### 4.7 `inference` — hypothesis testing & learning *(NEW — most open-ended)*
Methodological core of RQ1: signature-feature time-series classification (climate-event vs. baseline
windows), regression of returns/risk factors on climate-narrative signals, significance tests, and
**leakage-aware, time-respecting backtesting / cross-validation**. Outputs a calibrated effect
(→ RQ2) or a justified perturbation rule (→ fallback).

### 4.8 `infra` — configuration, logging, reproducibility *(NEW — build first)*
`set_seed` (Python/NumPy/ML backend); typed config loaded from `configs/*.yaml` (replacing the global
mutable dict); a configured logger; and a per-run **manifest** (config + git commit + seed + package
versions + timestamps) written to `results/`, so every thesis figure is traceable.

### 4.9 `viz` — publication-ready plotting *(NEW)*
Consistent, thesis-quality figures (exposure-profile/fan plots, distributions, calibration
diagnostics, test results); single style config; vector output (PDF/SVG).

---

## 5. Data sources

| Domain | Source(s) | Use |
|---|---|---|
| Equity & FX prices | Yahoo / Google Finance (public); paid feeds optional | GBM calibration, returns, event windows |
| Interest rates / curves | Public central-bank / market curve data | HW1F calibration |
| Transition scenarios | NGFS scenarios; IIASA scenario database | Scenario-conditioned perturbations & narratives |
| Climate pathways | IPCC / SSP–RCP | Physical-risk narratives |
| Observational climate | Copernicus C3S | Event identification / physical drivers |

Calibration inputs must be **publicly available**; proprietary feeds, if used, sit behind the same
interface and are clearly flagged.

---

## 6. Reproducibility & engineering conventions

- **Seeds.** Every stochastic operation routes through `infra.set_seed`. PIMPA already seeds its
  simulation (`random_state`); the randomized signature currently does **not** — this must be fixed.
- **Run manifests.** Each experiment writes a manifest (config + git commit + seed + versions +
  timestamps) to `results/`.
- **Configuration over hard-coding.** Parameters live in `configs/*.yaml`, not in module-level dicts;
  paths resolved centrally (no CWD-relative `'data/'`).
- **Version control.** Small, descriptive commits; feature branches; tags for milestones. Code is the
  source of truth; notebooks are exploratory.
- **Data hygiene.** `data/` and `results/` are gitignored (`notes/` is tracked); raw downloads immutable; large
  data tracked out-of-band (e.g. DVC).
- **Testing.** `pytest` units per module + one end-to-end integration test of
  `data → calibration → simulation → risk` on a tiny fixture (PIMPA's prototype CSVs are an ideal
  regression fixture).
- **Compatibility.** PIMPA uses `DataFrame.iteritems()`, removed in pandas ≥ 2.0 — pin pandas or
  migrate to `.items()` (see code review).
- **Code quality.** Formatter + linter (black/ruff) via pre-commit; type hints on public APIs.
- **Secrets.** API keys via environment variables / a gitignored `.env`.

---

## 7. Environment & installation

```bash
conda env create -f environment.yml        # or: python -m venv .venv && source .venv/bin/activate
conda activate climateCCR
pip install -e .                           # editable install — enables clean imports everywhere
pip install -e ".[dev]" && pre-commit install   # optional dev extras
```

After the editable install, `import climateCCR` works from any working directory.

---

## 8. Status & roadmap

| Module | Status | Next step |
|---|---|---|
| `risk` (PIMPA) | **Implemented** (EE/PE, collateral, netting) | Package it; add EPE/Effective-EPE + CVA |
| `processes` | **Implemented** in PIMPA | Promote to first-class layer (keep ABC interface) |
| `simulation` | **Implemented** in PIMPA | Promote; add event-injection / perturbation hooks |
| `signatures` | **Prototype with bugs** | Fix solver + seed reservoir (see code review) |
| `infra` | Not started | **Build first** — unblocks reproducibility everywhere |
| `data` | Not started | Connectors + common schema + immutable cache |
| `calibration` | **Not started** (PIMPA reads pre-calibrated CSVs) | GBM + HW1F estimators feeding `'direct_input'` |
| `inference` | Not started | Scope RQ1 methods; design leakage-safe CV |
| `viz` | Not started | Style config + core plot set |

**Build order:** `infra` → `src/` packaging + editable install (absorb PIMPA & rand-sig, add
`__init__.py`, fix the pandas/seed/solver bugs) → promote `processes`/`simulation` → `data` →
`calibration` → end-to-end smoke test on real data → `signatures`/`inference` → `viz`. A detailed,
time-boxed task plan is in `notes/PROJECT_PLAN.md`.

---

## 9. References (starter bibliography — verify details against attached PDFs)

> The attached PDFs are authoritative; finalize exact years/editions/pages from them.

- Foundational rough path theory (e.g. Lyons, *Differential equations driven by rough signals*).
- The signature method in machine learning (introductory/primer treatments, e.g. Chevyrev & Kormilitzin).
- **Compagnoni et al. (2023),** *On the Effectiveness of Randomized Signatures as Reservoir for
  Learning Rough Dynamics* — **attached; implemented in `signatures`.**
- Reservoir computing foundations (echo-state networks; universality results).
- Hull–White short-rate model and standard interest-rate references (e.g. Brigo & Mercurio);
  Andersen & Piterbarg, *Interest Rate Modeling* (the HW1F simulation scheme PIMPA uses).
- Counterparty credit risk & xVA (e.g. Gregory, *The xVA Challenge*; Brigo, Morini & Pallavicini).
- NGFS *Climate Scenarios*; the IIASA-hosted scenario database; IPCC AR6 / SSP–RCP.
- Plus the climate-and-finance papers attached to the project knowledge base.

---

## 10. Glossary

- **CCR** — counterparty credit risk.   **MPOR** — margin period of risk.
- **EE / EPE / Effective EPE** — expected exposure / expected positive exposure / its running max.
- **PE / PFE** — potential (future) exposure, a quantile of the exposure distribution.
- **CVA** — credit valuation adjustment.   **VM / MTA** — variation margin / minimum transfer amount.
- **BM / GBM / HW1F** — Brownian motion / geometric Brownian motion / Hull–White one-factor.
- **NGFS / IIASA** — Network for Greening the Financial System / Int'l Inst. for Applied Systems Analysis.
- **SSP / RCP** — Shared Socioeconomic Pathways / Representative Concentration Pathways.
- **PIMPA** — the project's existing portfolio valuation & counterparty-risk engine (now `risk`).
