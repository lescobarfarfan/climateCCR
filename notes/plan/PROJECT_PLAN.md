# Project plan — status and remaining work (re-baselined 2026-09-14)

Re-baselined under `INT-38` (the scope and manuscript gate). The original 2026-06-28 plan (Phases 0–6 at ~15 hrs/week over ~34 weeks) is superseded in place: Phases 0–5 are closed, Phase 3 (signatures) leaves the plan (`CCR-SIG-05`), and Phase 6 (writing) gets the task table it never had. Each closed phase names the decisions that closed it; the canon (`context/`) stays the source of truth for the content, this note only maps it to the work.

## 1. Closed phases

| Phase | Closed by | Definition of done, as met |
|---|---|---|
| 0 — Foundation | `CCR-ARCH-01..05`, `CCR-INFRA-01`, `CCR-MIG-01..09` | `import climateCCR` works anywhere; PIMPA runs from the package; the EE/PE goldens are locked (`CCR-MIG-03`) |
| 1 — Data | `MKT-SIE-06/07/09`, `MKT-CALIB-07` (Yahoo), `MKT-NGFS-04` (NGFS short-term connector), `INT-21` (the Mexican book), `GEN-24`, `HAZ-SOURCES-04` | config-driven pulls of price, rate and one climate-scenario dataset, cached with provenance |
| 2 — Calibration + end-to-end | `MKT-CURVE-05/06`, `MKT-CALIB-05..08`, `INT-16/17`, `INT-20`, `INT-22` | PIMPA exposure profiles on real public data, byte-reproducible (`INT-21`, seed 233423) |
| 3 — RQ1 signatures | **removed** — RQ1 is answered by the HAZ estimation (`INT-16..20`) and two pre-registered nulls (`INT-18/19` rates, `INT-27` equities); the randomized signatures are future work (`CCR-SIG-05`) | n/a |
| 4 — RQ2 propagation | `INT-13/14` (jump channel), `INT-23..28` (headline metric, sector and peril marks, sensitivities), `INT-29..36` (NGFS three flavors, spread leg), `CCR-RISK-02..08` (bond desks, PFE floor, pricer audit, CVA, Effective-EPE) | quantified change in CCR metrics under climate, reproducible with manifests |
| 5 — Visualization | `INT-15`, `GEN-22/28/33/34` | every figure regenerates from one command plus a config and seed (`pipelines/02`, `08`, `18–20`, `23`) |

## 2. Built beyond the original plan

- Sector- and peril-differentiated jump marks with per-peril severity (`INT-24..26`) and their sensitivities (`INT-25` S-tier jitter, `INT-28` storm clustering).
- The NGFS short-term transition channel in three application flavors — nivel (headline), trayectoria, fase — with the valuation-side spread leg (`MKT-NGFS-06..09`, `INT-30..36`).
- Unilateral CVA with the exact exposure / credit / interaction decomposition (`CCR-RISK-06`) and Effective-EPE (`CCR-RISK-08`).
- The model-vs-observed validation layer and the aggregate-loss readouts (`GEN-33/34`).
- The pre-registered event studies on rates and equities (`INT-18/19`, `INT-27`) — the H1 nulls of `INT-37`.

## 3. Small-revisions backlog (all small, none blocking the manuscript)

- `OQ-INT-07` (c) — the step-aware `MarkSampler` (time-varying severity); interface-ready per `INT-13`, no engine change.
- `OQ-MKT-02` — a P-measure stress appendix hook: estimate the market price of rate risk only if a real-world stress-path appendix is written.
- `OQ-HAZ-19` (b, c) — refresh the report-regime fits when the CENAPRED 2024 extenso or a restored event grain appears (`GEN-31` living calibration).
- `OQ-MKT-04` / `OQ-MKT-13` (b) — the NGFS long-term vintage join and its splice, on the Phase VI release (`GEN-31`).
- Reference verification tail — the `REFERENCES.md` §99 entries that are not on the results chain (HAZ-pipeline sources, workflow books).

## 4. Phase 6 — writing (the only open phase)

| Chapter | Content, anchored in the canon | Weeks |
|---|---|---|
| 1 Introduction and hypotheses | the aim (`INT-09`); H1/H2/H3 and the headline claim (`INT-37`); the three-arm machine (`INT-11`) | 1 |
| 2 Literature | `REFERENCES.md` §1–13; signatures and weather derivatives as future-work pointers (`CCR-SIG-05`, `MKT-WD-01`) | 1.5 |
| 3 Data | SIE and the curve (`DC-MKT-SIE-*`); the Mexican book (`DC-CCR-RISK-4`); CENAPRED and CNSF (`DC-HAZ-*`); NGFS short-term (`DC-MKT-NGFS-2`); value-level inspection (`GEN-27`) | 1 |
| 4 Methodology | market calibration (`MKT-CALIB-*`, `MKT-CURVE-05`); hazard calibration and loss-to-mark scale (`INT-16/17/20`, `INT-24..26`); the rate-channel event study (`INT-18/19`); the jump-diffusion engine (`INT-13/14`, `DC-CCR-SIM-2`); CCR metrics (`INT-23`, `CCR-RISK-03/06/08`); the NGFS flavors (`MKT-NGFS-06..09`, `INT-33..36`) | 2.5 |
| 5 Results | H1 nulls (`INT-18/19/27`); H2 physical band and per-name effects (`INT-23`, `GEN-34`); the transition three-flavor table (`INT-35`); H3 separability and the combined cells; CVA and the wrong-way reversal (`CCR-RISK-06`); robustness (`INT-25/28`, the λ(t) riders `INT-34`, validation `GEN-33`) | 2 |
| 6 Discussion and limitations | the body-text-only items: structural credit overlay (`MKT-CREDIT-02`), the long-term join, Cox λ(t), CLIMADA impact functions; the `OQ-MKT-02` hook; the CNSF report-lag caveat (`HAZ-CLEAN-CNSF-15`); the long-end curve caveat (`MKT-CURVE-07`) | 1 |
| 7 Conclusions and future work | signatures, weather derivatives, parametric pricing, stochastic spreads (`INT-38`) | 0.5 |
| Appendices | reproducibility (`GEN-*`); the figure and table map (`results/figures/*` plus manifests); the reference-verification record | 0.5 |

Rollup: about 10 weeks of writing at the original ~15 hrs/week; every figure and table is already regenerable from a committed config, so the writing phase adds no build work.

## Related
Supersedes the 2026-06-28 plan (git history keeps it); [[PHASE_0]] is archived under `notes/plan/archive/`. Reads with: [[DECISIONS]] (`INT-38`) · [[OPEN_QUESTIONS]] · [[README]] (Status and roadmap). Arms: [[CCR_MOC]] · [[MKT_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]
#arm/int #type/plan
