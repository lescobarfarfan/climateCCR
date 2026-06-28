# CCR_MOC — Counterparty credit & framework (the spine)

> Map of content for the **CCR arm**: the installable package, the reproducible `infra`, the PIMPA
> exposure engine + simulation structure, and the signatures/inference core. Hub note — links out to
> the canon (by ID) and to the CCR theory/plan/review notes. Home: [[_INDEX]].

**Role in the machine (`INT-11`):** the **framework** — runs calibration → simulation → risk and
reads out the climate-vs-baseline change. PIMPA provides exposure/valuation + the multi-factor
simulation structure into which the [[HAZ_MOC|HAZ]] jump and the [[MKT_MOC|MKT]] diffusions plug.

## Decisions → [[DECISIONS]]
- Architecture & packaging: `CCR-ARCH-01..05` (src-layout, editable install, `ProjectPaths`, config-over-hard-coding).
- Infra (built): `CCR-INFRA-01` (seeds, Config, logging, RunManifest, paths).
- Migration discipline: `CCR-MIG-01..03` (PIMPA in unchanged; `iteritems→items`; lock the EE/PE regression).
- Signatures: `CCR-SIG-01..03` (fix the reservoir — seed it, fix the solver contract).
- Calibration contract: `CCR-CAL-01` (estimators must emit `'direct_input'` objects).
- Risk: `CCR-RISK-01` (add EPE/Effective-EPE/CVA; CVA = climate-spread hook).
- Research design: `CCR-RES-01` (Path A/B reframed by `INT-10/12`); `CCR-RES-02` (timeline).
- Literature workflow: `CCR-LIT-01..03` (`marker` pipeline, naming).

## Data contracts → [[DATA_CONTRACTS]]
- `DC-CCR-DATA-1` tidy time-series · `DC-CCR-CAL-1` the `'direct_input'` contract (load-bearing).
- `DC-CCR-SIM-1` array layout + event-injection hook · **`DC-CCR-SIM-2` the climate jump-injection** (`INT-10`).
- `DC-CCR-SIG-1` reservoir/feature contract · `DC-CCR-INF-1` effect-vs-rule output.
- `DC-CCR-RISK-1` CCR metrics (EE/PE now; EPE/CVA next) · `DC-CCR-LIT-1` `marker` artifacts.

## Open questions → [[OPEN_QUESTIONS]]
- `OQ-CCR-01` API name · `OQ-CCR-02` tidy-schema final form · `OQ-CCR-03` first scenario connector.
- `OQ-CCR-04` where EPE/CVA live · `OQ-CCR-05` RQ1 design (labelling, CV split, go/no-go).
- `OQ-CCR-06` fixture location + second code-review pass · **`OQ-CCR-07` where signatures fit now**.

## Notes (import under `notes/`)
- Plan: [[PROJECT_PLAN]], [[PHASE_0]] — `notes/plan/`.
- Review: [[CODE_REVIEW]] — `notes/reviews/` (PIMPA + randomized-signature bugs C1–C5).

## Literature
- [[Compagnoni_2023_RandomizedSignatures]] — randomized signatures as a reservoir (`CCR-SIG-01`).

## Wires to the other arms
- Receives the **climate jump** from [[HAZ_MOC]] (`λ` + impact) via `DC-CCR-SIM-2` / `DC-XWALK-4`.
- Receives **diffusion calibration** (HW/GBM) from [[MKT_MOC]] via `DC-CCR-CAL-1`.

#arm/ccr #type/workflow
