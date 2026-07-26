# 2026-07-25 — The headline metric decision, explained (`INT-23`, `CCR-RISK-03`)

> What was decided: the results chapter leads with **expected-exposure (EE) profiles and their climate shift**, summarized by one number — the change in the book's **EPE** — with the supervisory **PFE 99%** as the tail view. And the long-standing "negative PE99" question is closed: the engine keeps its raw quantile, the *reports* floor it at zero.

## The quantities, in plain language

**EE (expected exposure).** At each future grid date the engine asks, path by path: if this counterparty defaulted here, how much would we lose? Only positive portfolio value is at risk (a negative value means *we* owe *them*), so the per-date loss is $\max(V, 0)$ and EE is its average over the 10,000 simulated paths. An EE *profile* is that average traced over the reporting grid out to 2076.

**EPE (expected positive exposure).** One number per counterparty: the time-average of its EE profile, computed as a trapezoid integral over the grid in year fractions (`viz.epe_summary`). The book EPE is the sum over the 30 counterparties. It is the standard compression of a profile into a headline — Basel's IMM capital runs on a close cousin (Effective EPE, times a multiplier $\alpha$).

**PFE 99% (potential future exposure).** The tail companion: the 99th percentile of exposure at each grid date — "how bad could this get in the worst 1% of scenarios". PIMPA historically stored the *raw* 99% quantile of portfolio value, which goes negative when a netting set is a net liability (seven of the thirty Mexican counterparties). `CCR-RISK-03` resolves this: the raw quantile stays in the engine and the stored frames (it is real information — how deep in liability the set sits), and every *reported* figure floors it, $\text{PFE} = \max(\text{quantile}, 0)$, which is the supervisory definition. The floor was verified immaterial: 29 of 360 rows change, and no ordering or conclusion moves.

## How to read the results obtained

The headline: under the estimated climate jump channel, the Mexican book's EPE falls **$-11.0\%$** (headline $\lambda = 19.29$/yr), **$-6.5\%$** (ciclón-bridge anchor $\lambda = 9.96$/yr), **$-5.6\%$** (report-regime floor $\lambda = 7.22$/yr) against a baseline book EPE of $272{,}314$ MXN. Three readings matter:

1. **The sign is a story, not a typo.** Climate events *reduce* this book's counterparty exposure: the equity marks are adverse (prices drop), so the bank's long option/equity-linked positions are worth less — there is less to lose at default. The exception proves the mechanism: NAID 114 (payer-IRS-only) *gains* exposure because rate-up jumps raise a payer swap's value.
2. **The caveat is wrong-way risk.** The same climate event that shrinks the exposure also weakens the counterparty (it *is* the equity issuer). EE alone therefore understates the loss story — expected loss is $\text{PD} \times \text{EE}$-shaped and the PD side moves adversely. That joint story is CVA territory, explicitly future work (`OQ-CCR-04`); the manuscript states the caveat rather than hiding it.
3. **Mean vs tail.** The EE/EPE band scales almost linearly with the compound loss rate $\lambda\,\mathbb{E}[L]$ — stable, regime-robust. The PFE99 shift is ~2.7× larger and λ-nonlinear in the far tail (quantiles respond to how *often* the tail is populated). That instability across the regime band is precisely why the tail is the secondary view, not the headline.

## Why this is the defensible choice

Counterparty-credit practice splits the metrics by role: EE/EPE feed pricing and capital, PFE sets trading limits (`[PykhtinZhu2007]`, `[Gregory_xVA]`, `[BaselCRE]`). Climate supervision — BCBS Principles 2022 and its FAQ, the ECB Guide, EBA/GL/2025/01 — asks banks to run climate *through existing risk categories* via scenario analysis, not to invent a new metric, and explicitly tolerates proxy-grade quantification (`[BCBS2022Principles]`, `[BCBS2022FAQ]`, `[ECB2020Guide]`, `[EBA2025ESG]`). Our jump-on $-$ baseline design is exactly such a scenario delta on the existing EE metric; short-horizon VaR is the wrong horizon for decadal climate risk by the supervisor's own analysis (`[BCBS2021Transmission]`, `[BCBS2021Measurement]`), and quantile headlines fail aggregation (`[Artzner1999]`). No jurisdiction — Mexico included (disclosure mandate + guidance, no capital rule) — fixes a binding climate metric as of mid-2026, so the contribution is the internal-framework quantification itself.

## Related

Backs: [[DECISIONS]] (`INT-23`, `CCR-RISK-03`) · read-log: [[2026-07-25_headline_metric]] (`GEN-21`) · contracts: [[DATA_CONTRACTS]] (`DC-CCR-RISK-3`) · keys: [[REFERENCES]] (§11) · predecessors: [[2026-07-25_lambda_band_readout_explained]] · [[2026-07-25_mexican_book_swap_explained]]. Arm MOCs: [[CCR_MOC]] · Home: [[_INDEX]]

#arm/ccr #arm/int #type/explanation
