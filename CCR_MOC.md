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
- Migration discipline: `CCR-MIG-01..09` (PIMPA in unchanged; `iteritems→items`; lock the EE/PE regression; move-then-decompose; the 2026-07-11 ponytail cuts).
- Signatures: `CCR-SIG-01..04` (fix the reservoir — seed it, fix the solver contract; `scikit-learn` kept for the readout).
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
- Review: [[PONYTAIL_AUDIT_2026-07-11]] — over-engineering sweep: applied/rejected cuts + the `notebook_tools` inventory (`CCR-MIG-09`, `GEN-25`).
- Reading: [[2026-07-02_climate_jump_channel]] — the jump-channel read-log (`notes/reading/`, `GEN-21`).
- Reading: [[2026-07-05_viz_layer_horizons]] — viz layer, horizons & grid-densification read-log (`notes/reading/`, `GEN-21`).
- Reading: [[2026-07-05_vault_formatting]] — housekeeping read-log, no analytical decisions (the `GEN-23` formatting convention; `notes/reading/`, `GEN-21`).
- Reading: [[2026-07-11_ponytail_minimalism]] — ponytail-audit read-log, no analytical decisions (`GEN-25` grounding refs in §99; `notes/reading/`, `GEN-21`).
- Reading: [[2026-07-16_summary_explanations_workflow]] — workflow read-log, no analytical decisions (`GEN-26` adds the summary-explanation note series to the ritual; `notes/reading/`, `GEN-21`).
- Reading: [[2026-07-25_mexican_book_swap]] — the book-swap read-log: HW1F bond reconstruction behind the new DEBT desk, the S_rate_eff inversion, per-name GBM fits, PSD repair (`INT-21`/`INT-22`/`CCR-RISK-02`; `notes/reading/`, `GEN-21`).
- Explanation: [[2026-07-25_mexican_book_swap_explained]] — the Mexican book's calibrated quantities, the bond desk, why `S_rate_eff` is an inverse sensitivity (≈4–5× GDP by construction), and how to read the re-baselined EE/PE band (`notes/summary_explanations/`, `GEN-26`).
- Reading: [[2026-07-25_viz_mexican_book_render]] — rendering the book: exposure-profile convention behind the tenor axis, the λ·E[L] reading of the scenario band, and the bit-for-bit figure-refactor check (`INT-15`/`GEN-28`; no methodological decisions; `notes/reading/`, `GEN-21`).
- Reading: [[2026-07-25_headline_metric]] — the headline-metric read-log: the EE/PFE/CVA role split, Basel CRE definitions, the climate-supervision scenario-analysis mandate, and quantile non-coherence (`INT-23`/`CCR-RISK-03`; `notes/reading/`, `GEN-21`).
- Explanation: [[2026-07-25_headline_metric_explained]] — what EE/EPE/PFE mean, how to read the book-EPE delta band (−11.0/−6.5/−5.6%) and its sign, the wrong-way-risk caveat, and why the floor-at-reporting convention is supervisory-exact without touching the golden baselines (`notes/summary_explanations/`, `GEN-26`).

## Literature
- [[Compagnoni_2023_RandomizedSignatures]] — randomized signatures as a reservoir (`CCR-SIG-01`).
- [[Cuchiero_2022_DiscreteTimeSignatures]] — discrete-time signatures & randomness in reservoir computing (`CCR-SIG-*`).

## Wires to the other arms
- Receives the **climate jump** from [[HAZ_MOC]] (`λ` + impact) via `DC-CCR-SIM-2` / `DC-XWALK-4`.
- Receives **diffusion calibration** (HW/GBM) from [[MKT_MOC]] via `DC-CCR-CAL-1`.

## Related
Arms: [[MKT_MOC]] · [[HAZ_MOC]] · Canon: [[DECISIONS]] · [[DATA_CONTRACTS]] · [[OPEN_QUESTIONS]] · [[GLOSSARY]] · Home: [[_INDEX]]

#arm/ccr #type/workflow
