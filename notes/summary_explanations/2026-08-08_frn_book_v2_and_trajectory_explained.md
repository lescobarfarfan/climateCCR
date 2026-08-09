# Book v2, the FRN leg & the trajectory flavor — explained (2026-08-08)

Plain-language companion to `CCR-RISK-04`, `INT-32`, `MKT-NGFS-09` and `GEN-34` (`GEN-26` series).

## 1. The FRN pricer's quantities and why the band moved

A floating-rate cebur pays 28-day TIIE plus a contractual **sobretasa** fixed at issuance. Two spreads coexist and must never be conflated: the sobretasa is part of the *promised cashflow* (the `coupon` column — a contract term, never shocked), while the **discount margin** is the spread the market currently demands to *discount* those cashflows (the `spread` column — the credit state, and therefore the NGFS `shock_bond_spreads` target). At issuance the two coincide and the note prices near par; a widening discount margin with the sobretasa fixed is exactly what a credit deterioration looks like, and the pricer's monotonicity tests lock both signs (`[Fabozzi2000FRN]`).

Because the index leg resets every 28 days, the floater's rate-duration is roughly one period: when simulated short rates move, the projected coupons and the discount factors move *together* and nearly cancel (the unit test bounds the FRN's rate move below 10% of an equal-maturity fixed bond's). That is why swapping 6 of 23 bonds to FRN terms damps the rate-jump channel and the adopted headline eases $-8.40\% \to -8.28\%$ (`INT-32` re-base of the `INT-23` chain, new baseline book EPE 273,377.64 MXN): the physical jump still hits equities identically, but the rate mark now finds less long-duration paper to reprice. The same mechanism shrinks the state issuers' (PEMEX/CFE, now FRN-heavy) sensitivity to the DAPS sovereign shock at nivel ($-13.35 \to -13.16\%$ at book level).

## 2. The trajectory flavor — what maturity dating means

The nivel (fixed) flavor shocks every pillar with the scenario's *peak* 2025–2030 anchor delta — a peak-severity stress-test convention (`[FedCSA2024]`, `[BoE2022CBES]`). The trajectory flavor (`MKT-NGFS-09`) instead asks: what shock prevails *when each cashflow actually lives*? Each zero pillar of tenor $T$ takes the tenor-blended anchor delta evaluated at its own maturity date $t_0+T$ on the full quarterly/annual paths, held constant beyond the scenario window. Two properties pin the implementation: flat paths reduce *exactly* to the nivel formula (the rtol $10^{-12}$ unit invariant — the reason the forward-integral alternative was rejected), and the end-clamp encodes the honest "no information beyond the window" extrapolation.

Reading the results (book v2): transitions HWTP $+0.06$ / SWUC $+2.20$ / DAPS_NAM $-0.16\%$ against nivel $-4.10$ / $-3.81$ / $-13.16\%$. The divergence is the point — DAPS's sovereign spike is front-loaded, so a 10-year cashflow discounted at the shock prevailing in 2036 sees the settled post-window level, not the 2026 peak. Nivel answers "how bad at the worst moment", trajectory answers "how bad along the path"; the ruling keeps nivel as the headline and the trajectory readout as the robustness flavor, both reproducible from committed configs (`GEN-31`). Jump-within stays $\approx -8.4$/$-8.6\%$ under every overlay — the physical and transition channels remain separable (`INT-29`).

## 3. The aggregate-loss layer — two routes, two different questions

Route 1 (engine, `DC-CCR-RISK-5`): the per-path artifact stores raw netted portfolio values per NAID at the reporting grid; `pipelines/20` aggregates book exposure $\Sigma_{\text{NAID}}\max(V,0)$ per path and date, and its quantiles are the distributional view of the same object EE averages — read the 1y headline (q99 3,379,705 $\to$ 3,070,656 MXN, $-9.1\%$ under climate) as "the 99th-percentile exposure the desk would report a year out"; by 10y the book has largely run off and both distributions collapse. Route 2 (compound Poisson, `[Klugman2019]`): annual aggregate *physical loss* $S=\sum X_i$ in MDP-2025 simulated straight from the fitted $\lambda$ and lognormal severities (q99 93,588 / 60,877 / 48,569 by λ leg; mean $=\lambda E[X]$ analytic check; leg provenance per `INT-20`). The routes answer different questions — counterparty exposure vs economy-side damage — so their levels are not comparable, and the figure set keeps them in separate panels.

## 4. Caveats worth carrying to the manuscript

The 26-name holdout grid (`GEN-34`) makes one data pathology visible: PENAVERDE's cone coverage is 42% (QUALITAS 91%, all others 96–100%) because its price history is illiquid step quotes — its GBM parameters, and any per-name conclusion on it, inherit that. The PEMEX sobretasa remains `[eng]` (no public document found), the UDI-linked series are excluded by scope, and the single-curve TIIE proxy (no TIIE/zero basis, curve-implied stub fixing) is a documented simplification of the FRN leg.

## Related
Read-log: [[2026-08-08_frn_book_v2_trajectory]] · decisions: [[DECISIONS]] (`CCR-RISK-04`, `INT-32`, `MKT-NGFS-09`, `GEN-34`) · previous: [[2026-08-03_ngfs_equity_corporate_leg_explained]] · Home: [[_INDEX]] · MOCs: [[CCR_MOC]] · [[MKT_MOC]]
#arm/ccr #arm/mkt #arm/int #type/explanation
