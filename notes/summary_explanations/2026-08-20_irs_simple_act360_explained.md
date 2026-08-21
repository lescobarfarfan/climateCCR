# The IRS convention alignment, explained (2026-08-20)

Plain-language companion to `CCR-RISK-07` (closes `OQ-CCR-10`): what changed in the IRS pricer, what the new quantities mean, why every headline number barely moved, and why the change was worth a full re-base anyway.

## What changed, in one paragraph

The engine's interest-rate swaps used to compute their floating rate as a *continuously-compounded* forward on an Act/365 daycount — a textbook dialect — while the FRN cebures priced their floating coupons with the *simple Act/360* forward that the Mexican TIIE market (and USD SOFR, EUR Euribor) actually quotes. Two instruments on the same curve and the same index therefore implied two different forward rates, a measured internal basis of ~1.13% of IRS PV (`CCR-RISK-05` audit). The session's ruling aligned the IRS to the market convention: the floating rate is now $F=(P(t_{val},S)/P(t_{val},T)-1)/\delta_{360}$ and every cashflow accrues on Act/360, on both legs. Separately, the `payer` label was flipped to its universal market meaning — the payer *pays fixed* — after the legacy PIMPA label (payer pays floating) had already produced one vocabulary inconsistency in the canon (`INT-21`'s NAID-114 sentence).

## What each quantity means

- **The simple Act/360 forward** $F=(P/P'-1)\cdot 360/d$: the annualized rate a money-market lender earns over a $d$-day window, quoted the way TIIE-28 itself is quoted (`MKT-SIE-04`). The old continuously-compounded form $-\ln(P'/P)\cdot 365/d$ answers the same question in log-space; for the same window $F_{cc}<F_{simple}$ (since $\ln(1+x)<x$) and its Act/365 accrual is ~1.4% shorter, so the old floating legs were systematically cheap by about 1% of PV.
- **$\delta_{360}$ vs model time**: dates are still mapped to the curve's time axis in Act/365 (that is how the HW1F machinery measures time), while the *money* accrual multiplying each cashflow is now $d/360$. One window, two roles — coordinate and daycount — now handled separately, as market systems do.
- **`payer` / `receiver`**: market semantics — payer pays K, receives $F$, so its value is $\sum N\,\delta_{360}(F-K)\,DF$ and it *gains* when rates rise. The relabel changed no trade's economics: every label site (pricer sign, fixture CSV, book `direction_cycle`, tests) was swapped in one commit, and the proof is that the headline band artifact reproduced **byte-identically** under the relabeled book.

## How to interpret the re-based results

The whole stack was re-run under the new convention (canonical env, manifests pinned): book EPE baseline moved 255,217.29 → 255,278.60 MXN (**+0.024%**) and the climate band moved from −8.94/−5.44/−4.86% to **−8.93/−5.44/−4.86%** — one hundredth of a point on one leg. NGFS transitions eased ≤0.16pp (HWTP −5.73, SWUC −8.18, DAPS_NAM −20.03%), the jump-within legs (−9.20/−9.43%) still show the physical channel is transition-invariant, the trajectory flavor still looks through transient peaks, and CVA (514,270 MXN base) keeps the wrong-way offset: transition credit channels (+57k/+98k/+97k) nearly cancel the exposure channels (−49k/−75k/−131k). Interpretation: the correction is a *pricing-consistency* fix whose effect is bounded by ~1% of a desk that is a small share of book exposure, and the exposure kink $\max(V,0)$ plus 30-counterparty diversification damp it further — exactly the prediction that made the re-base safe to adopt under `GEN-31`'s adopt-if-material policy (here: adopt-for-consistency, materiality confirmed nil).

## Why this was worth doing at all

Three reasons, none of them the numbers. (1) *Audience*: every practitioner, examiner, or supervisor reads a floating leg as simple money-market daycount; a cc floating leg in a supervisory-framed CCR chapter (`INT-23` leans on Basel/IMM conventions) invites a footnote-and-defense that no longer needs writing. (2) *Internal coherence*: the IRS and FRN desks now imply the same forward for the same window off the same curve — the ~1.13% cross-desk basis is gone, and one audit test locks the identity permanently. (3) *The living package* (`GEN-31`): converging on market conventions now, while the re-base machinery was warm from `CCR-RISK-05`, was one background session; doing it after manuscript numbers freeze would have been far costlier. Justification anchors: `[BrigoMercurio2006]` §1.4 (the two compounding definitions), `[BanxicoTIIESwapConv ref?]` (the TIIE-28 market convention, §99 to confirm), `[Fabozzi2000FRN ref?]` (floater projection), `[Gregory_xVA]` (exposure aggregation).

## Related
Decisions: [[DECISIONS]] (`CCR-RISK-07`, `CCR-RISK-05`, `MKT-SIE-04`) · Read-log: [[2026-08-20_irs_convention_alignment]] · Findings: [[PRICING_INTERNALS_AUDIT_2026-08-12]] · Prior explanation: [[2026-08-12_cva_extension_explained]] · Arm: [[CCR_MOC]] · Home: [[_INDEX]]
#arm/ccr #type/explanation
