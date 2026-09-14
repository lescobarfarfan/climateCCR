# The hypotheses, the scope split, and three small revisions, explained (2026-09-14)

Session decisions `INT-37`, `INT-38`, `CCR-SIG-05`, `CCR-RISK-08`, `MKT-SIE-09`, `HAZ-CLEAN-CNSF-15` and the bundled closes (`CCR-ARCH-06`, `MKT-CURVE-07`, `MKT-CREDIT-02`, `MKT-PHYS-04`, `HAZ-SOURCES-05`, `CCR-LIT-04`, `GEN-36`). This note explains what the thesis now claims, what was ruled in and out of scope, and what the three computed results of the session mean. Companion read-log: [[2026-09-14_scope_manuscript_gate]]; the re-baselined plan is [[PROJECT_PLAN]].

## The hypotheses and how the results read against them

The thesis had an aim (`INT-09`) and two research questions but no stated hypothesis. `INT-37` fixes three, each tied to a result already on disk.

*H1, market repricing:* Mexican sovereign yields and BMV equity prices reprice individual climate events within the event window. This is the direct test of a price↔climate relationship, and it is **rejected** twice under gates fixed before estimation: the lead sovereign pillar shows a null loss-to-yield slope over 100 episodes including Otis (`INT-18/19`, one-sided $p = .734$), and the equity cross-section does not order itself by cyclone exposure over 63 episodes (`INT-27`, $\tau = +0.198$, $p_{boot} = .94$). Read H1 as the mechanism finding: Mexican markets do not price individual physical events at event horizon.

*H2, loss transmission:* a jump channel calibrated on realized Mexican climate losses materially changes counterparty exposure relative to a climate-free baseline. **Supported**: the book EPE falls by $8.93\,\%$ under the registry arrival intensity, with the regime-consistent legs at $-5.44$ and $-4.86\,\%$ (`INT-23`), concentrated on the climate-exposed names by construction of the sector and peril marks (`INT-24..26`). The transmission runs through realized losses (CENAPRED damage, CNSF pass-through) — the channel H1 shows the market does not anticipate.

*H3, separability:* the physical and transition channels are approximately additive on the book. **Supported**: the jump-within deltas move by at most $0.25$ pp across the nivel, trayectoria and fase transition states (`INT-31/35`), so the physical band needs no per-flavor restatement.

The headline claim follows: an empirically calibrated physical climate channel moves the book's expected positive exposure by 5–9 % under the current-climate arrival band, while market prices show no measurable per-event response. The three statements are ordered for the manuscript: H1 explains why the calibration is loss-based, H2 is the quantified result, H3 licenses reporting the two channels separately and combined.

## The scope split

`INT-38` closes the last general gap. In the body as results: everything built. In the body as text only: the structural credit overlay (its reduced form is CVA with CLIMACRED PDs, `MKT-CREDIT-02`), the NGFS long-term join, Cox $\lambda(t)$ and CLIMADA impact functions — each a limitations paragraph pointing at the seam that exists. Future work: signatures (`CCR-SIG-05` — a reservoir probe on 63 episodes would be a third pre-registered null, not a detection), weather derivatives (`MKT-WD-01` — temperature contracts cover a small slice of the risk quantified and the framework does not extend to them easily), parametric pricing and stochastic spreads. The dashboard is context (`MKT-PHYS-04`); the long-end curve sparsity cannot reach a book that matures inside 10 years (`MKT-CURVE-07`); the HAZ pipelines that feed no result are future work (`HAZ-SOURCES-05`). Two items stay deliberately open by user ruling: the step-aware mark sampler (`OQ-INT-07` c) and a P-measure appendix hook (`OQ-MKT-02`).

## Effective-EPE: what the new number means

Basel's IMM exposure is not the lifetime EPE the results chapter leads with but the *Effective EPE*: the running maximum of the EE profile, averaged over the first year, per netting set and then summed. On the Mexican book this is $2{,}571{,}793$ MXN against a lifetime EPE of $255{,}279$ MXN — ten times larger because the first-year exposure ($\approx 2.5$ M, dominated by the bond desk's positive mark-to-market) is averaged over one year rather than diluted over the 50-year tenor grid. The climate shift on EEPE is $-2.13 / -1.53 / -1.39\,\%$ (headline / CT anchor / floor) against $-8.93 / -5.44 / -4.86\,\%$ on EPE. The gap is the point: the jump channel accumulates arrivals over the exposure ramp, so a one-year capital measure sees a fraction of what the lifetime pricing measure sees. Two deviations from CRE53 are stated in the code and must be stated in the manuscript: the trapezoid average instead of the right-Riemann sum, and no truncation at maturity (every book maturity exceeds one year).

## The compounding identity: what was verified

`OQ-MKT-01` asked whether the compounded F-TIIE tenors quote simple Act/360 or annually compounded. Banxico's technical note answers by construction — the published rate is $r_T = [(I_D/I_{D-28})^{T/28}-1]\cdot 36000/T$ on the business-day index — and the data confirm it: rebuilding the index from the overnight fixings reproduces Banxico's index to $10^{-5}$ bp and the published 28-, 91- and 182-day rates to $0.003$ bp mean absolute deviation over 5,143 dates, while the annually-compounded reading misses by 31, 27 and 21 bp. Two things follow for the manuscript: the short-block conversion $z = (365/d)\ln(1 + r\,d/360)$ is Banxico's own convention, and the 91- and 182-day published rates carry no information beyond the 28-day one — they are the same trailing ratio extrapolated geometrically, which is why the calibration uses the overnight series.

## The CNSF year finding: what it means for β

The loss-to-mark scale pairs CNSF paid claims with CENAPRED damage over 2008–2015 to estimate the pass-through $\beta = 0.174$. The session found that the CNSF amounts are summed by the SESA *report* year (the workbook the row came from), because the consolidados carry no occurrence date — the word `OCURRIDO` appears only in an incurred-amount column that `HAZ-CLEAN-CNSF-06` already rules out. Damage is occurrence-dated, so the ratio carries a report-lag mismatch. It cannot be corrected from the files, and it is damped by the eight-year window; it is stated as a limitation, not adjusted. The premium volume $K$ is by emission year, which is the right grain.

## Limits to state when citing this session

H2's magnitude rides on the loss-to-mark scale and the arrival band; H1 is a null with the power the samples allow (100 rate episodes, 63 equity episodes), not a proof of absence. EEPE is computed on stored EE profiles at tenor pillars, not on a daily grid. The compounding check verifies a convention, not a model. The reference pass verified the results-chain keys; the §99 tail (HAZ-pipeline sources, workflow books, the AMIS Odile figure) remains to confirm before the literature review hardens.

## Related
Decisions: [[DECISIONS]] (`INT-37`, `INT-38`, `CCR-SIG-05`, `CCR-RISK-08`, `MKT-SIE-09`, `HAZ-CLEAN-CNSF-15`) · Read-log: [[2026-09-14_scope_manuscript_gate]] · Plan: [[PROJECT_PLAN]] · Prior explanation: [[2026-09-08_fase_matrix_spread_leg_explained]] · Arms: [[CCR_MOC]] · [[MKT_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]
#arm/int #type/explanation
