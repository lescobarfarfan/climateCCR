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
- Review: [[PRICING_INTERNALS_AUDIT_2026-08-12]] — the `OQ-CCR-06` second pass: three ACTIVE IRS-pricer errors fixed (missing accrual, wrong-state forwards, spliced-period fixing), goldens deliberately re-based, Surface/Curve/CorrelationMatrix behaviour locked by tests; cc-vs-simple floating convention deferred (`notes/reviews/`).
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
- Reading: [[2026-07-26_sector_marks]] — the sector-marks read-log: the Bressan asset-level template + proxy caveat, DaLA sector decomposition, exposure-share→return evidence, the supervisory sector×geography frame, and the lognormal median-scaling algebra behind `target_scales` (`INT-24`; `notes/reading/`, `GEN-21`).
- Explanation: [[2026-07-26_sector_marks_explained]] — what `γ_i` is, the G×S×D/pob layers, the Σwγ=1 redistribution anchor, the Jensen reading of the re-based EPE band (−8.74/−5.35/−4.68%) and the hotel/airport concentration, and the residual limits (`notes/summary_explanations/`, `GEN-26`).
- Reading: [[2026-07-30_peril_typed_events]] — the peril-typing read-log: marking/thinning of Poisson processes behind `c_ip = γ_i^p/π_p`, the frequency-vs-damage mix discipline, the cause-vs-mechanism attribution caveats, and the robust-triage basis of the base inspección (`INT-25`/`HAZ-CENAPRED-11`; `notes/reading/`, `GEN-21`).
- Explanation: [[2026-07-30_peril_typed_events_explained]] — what `π` and `c_ip` mean, the exact mean-preservation anchor, how to read the re-based band (−8.44/−5.12/−4.50%) and the three-generation lineage, and the five-variant + jitter robustness answers (`notes/summary_explanations/`, `GEN-26`).
- Reading: [[2026-08-01_per_peril_severity_phase_c]] — the per-peril-severity + Phase C read-log: conditional mark distributions and the mean-matching moment condition, the truncation lesson (ciclón σ 2.9→1.33), event-study design under cross-sectional dependence, and the manifest-driven env diagnosis (`INT-26`/`INT-27`/`GEN-30`; `notes/reading/`, `GEN-21`).
- Explanation: [[2026-08-01_per_peril_severity_phase_c_explained]] — what per-label σ and mean-matched medians mean, how to read the re-based band (−8.36/−5.05/−4.51%), what the Phase C FALLA does and does not say, and the canonical-env byte-identity lesson (`notes/summary_explanations/`, `GEN-26`).
- Reading: [[2026-08-01_knowledge_graph_tooling]] — tooling read-log, no analytical decisions (`GEN-29` adopts the understand-anything knowledge graph + dashboard, `.ua/` git-ignored; `notes/reading/`, `GEN-21`).
- Reading: [[2026-08-01_ua_config_tracking]] — housekeeping read-log, no analytical decisions (`GEN-29` amended: the UA scope config `.ua/.understandignore` + `config.json` git-tracked, manual-incremental update policy documented; `notes/reading/`, `GEN-21`).
- Explanation: [[2026-08-07_validation_figures_explained]] — the cross-run EPE comparison family on the CCR results: the scenario × λ-band delta matrix, the per-counterparty shift strips (own-baseline convention, the exposure-kink outlier), and the to-the-digit reproduction of the `INT-23/31` chain from stored frames (`GEN-33`; `notes/summary_explanations/`, `GEN-26`).
- Reading: [[2026-08-08_frn_book_v2_trajectory]] — the FRN/book-v2 read-log: floater discount-margin mechanics behind `BOND_FRN`, the collective-risk-model chapter behind the aggregate-loss panel, ST-path semantics behind maturity dating, and the exposure-metric semantics of the per-path artifact (`CCR-RISK-04`/`INT-32`/`MKT-NGFS-09`/`GEN-34`; `notes/reading/`, `GEN-21`).
- Explanation: [[2026-08-08_frn_book_v2_and_trajectory_explained]] — sobretasa vs discount margin, why the band re-based to −8.28/−5.00/−4.46% (FRNs damp the rate-jump channel), how to read nivel vs trajectory, and the two non-comparable aggregate-loss routes (`notes/summary_explanations/`, `GEN-26`).
- Reading: [[2026-08-09_ua_graph_repair]] — tooling read-log, no analytical decisions (`GEN-35`: the corrupted UA graph rolled back and rebuilt via the plugin's own `/understand` flow; hand-rolled merges banned, stale-inventory + batch-coverage traps codified; `notes/reading/`, `GEN-21`).

## Literature
- [[Compagnoni_2023_RandomizedSignatures]] — randomized signatures as a reservoir (`CCR-SIG-01`).
- [[Cuchiero_2022_DiscreteTimeSignatures]] — discrete-time signatures & randomness in reservoir computing (`CCR-SIG-*`).

## Wires to the other arms
- Receives the **climate jump** from [[HAZ_MOC]] (`λ` + impact) via `DC-CCR-SIM-2` / `DC-XWALK-4`.
- Receives **diffusion calibration** (HW/GBM) from [[MKT_MOC]] via `DC-CCR-CAL-1`.

## Related
Arms: [[MKT_MOC]] · [[HAZ_MOC]] · Canon: [[DECISIONS]] · [[DATA_CONTRACTS]] · [[OPEN_QUESTIONS]] · [[GLOSSARY]] · Home: [[_INDEX]]

#arm/ccr #type/workflow
