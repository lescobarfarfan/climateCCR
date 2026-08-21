# Read-log — the IRS convention alignment (2026-08-20)

Session decision: `CCR-RISK-07` (IRS floating leg → simple Act/360, `payer` relabeled to market semantics, goldens + chain re-based; closes `OQ-CCR-10`). Readings ordered by priority.

1. **`[BrigoMercurio2006]` — Brigo & Mercurio, *Interest Rate Models*, §1.4 (simply-compounded vs continuously-compounded spot/forward rates) and §3.3 (Hull–White ZCB reconstruction).** Why: `CCR-RISK-07`'s formula $F=(P(t,S)/P(t,T)-1)/\delta_{360}$ is the textbook *simply-compounded* forward of §1.4 — the object market floating legs actually fix on — while the replaced $-\ln[P(t,T)/P(t,S)]/\delta$ is the continuously-compounded dialect; without §1.4 the change reads cosmetic instead of as a definitional alignment, and §3.3 is why both bond prices are functions of the same simulated short rate.
2. **`[BanxicoTIIESwapConv ref?]` — the TIIE-28 IRS convention document (Banxico Circular 4/2012 / MexDer swap specs / ISDA 2006 «MXN-TIIE-Banxico»; §99, to confirm).** Why: the market-convention claim behind the ruling — 28-day coupons, Act/360 both legs, simple compounding; also documents what the engine deliberately simplifies (quarterly schedule, an `INT-21` book-design call).
3. **`[Fabozzi2000FRN ref?]` — Fabozzi & Mann, *Floating-Rate Securities*, the floater-valuation chapter.** Why: the cross-desk identity the change enforces — the IRS floating leg now projects index cashflows exactly as the FRN pricer does (`CCR-RISK-04`), so one convention (`MKT-SIE-04`) prices every floating instrument off the single curve.
4. **`[Gregory_xVA]` — Gregory, *The xVA Challenge*, the credit-exposure chapter (exposure as $\mathrm{mean}(\max(V,0))$ at book scale).** Why: why a ~1.13%-of-PV floating-leg reprice moves book EPE only +0.024% and the band at the second decimal — the exposure kink and 30-NAID diversification damp a small parallel desk-level PV shift, which is what made the re-base safe to adopt.

## Related
Decisions: [[DECISIONS]] (`CCR-RISK-07`) · Findings: [[PRICING_INTERNALS_AUDIT_2026-08-12]] (the audit that quantified the wedge) · Explanation: [[2026-08-20_irs_simple_act360_explained]] · Prior read-log: [[2026-08-12_ccr_audit_cva]] · Arm: [[CCR_MOC]] · Home: [[_INDEX]]
#arm/ccr #type/reading
