# Cross-machine reproduction — what the measured differences mean (2026-10-20)

Plain-language companion to `GEN-39` / `GEN-40`: what was compared when the project was landed on the Linux x86-64 machine, what each class of difference means, and why the results chain is declared reproduced. Procedure, copy list and the per-family table: [[linux_landing_reproduction]]; readings: [[2026-10-20_linux_landing_reproduction]].

## The quantities introduced

**Scale-relative difference** — per column (or array), $\max_i |x_i - y_i| \,/\, \max_i |x_i|$: it asks whether the *artifact* moved, not whether a near-zero cell did. A $10^{-4}$ MXN move in a cell of an EE column that reaches $2\times10^{5}$ MXN is $10^{-9}$, not a "100 % difference"; the earlier cell-relative reading of the same files flagged shift columns near zero as large and was replaced.

**Reported precision** — the digits the canon quotes (two decimals of a percentage, integer MXN, four decimals of $\lambda$); a headline cell reproduces when both machines round to the same quoted value (`tools/headlines.yaml`, 64 cells).

**The four classes of difference actually observed.** (1) *ulp-level*: $\le 10^{-13}$ on the PIMPA goldens — the last bits of sums and products depend on the BLAS kernel, the libm and fused multiply-add choices of each CPU architecture; (2) *optimiser tolerance*: the Nelder–Mead HW1F fit stops within `xatol` $10^{-8}$ on a likelihood that is flat in $a$, so $a$ agrees to seven digits and everything downstream of it (the book's HW1F pillars, the loading $L(a)$ behind `S_rate_eff_MX`, the EE cells) inherits a $10^{-7}$–$10^{-8}$ relative difference; (3) *discrete flips*: a probability-integral transform sitting on a percentile boundary moves one count (one of 1,080 tier-C coverage cells, by one forecast of 914), and tied rows change order unless the sort is stable; (4) *stale artifacts*: files an earlier code state wrote that an idempotent pipeline never deletes (the July fixture demos, the pre-`INT-39` jitter tables, superseded figure names) — differences of vintage, not of machine.

## How to read the results

Means and paired deltas — EPE, Effective EPE, the band shifts — agree to four decimals (255,735.47 MXN; $-8.9965 / -5.5071 / -4.9897\,\%$); the seed-study spread of the headline shift is 0.026 pp, three orders of magnitude above the cross-machine noise, so every conclusion is machine-independent by a wide margin. Tail levels agree to $10^{-9}$ (1y q99 3,041,356.0014 vs 3,041,355.9992 MXN) against a 0.4 % seed sd. Fitted parameters should be quoted to the stability of their estimator, not to float precision: HW1F $a$ to seven digits, `S_rate_eff_MX` as 175.29 M MDP-2025 (the canon's nine-digit 175,293,784 was two digits beyond what the optimiser fixes). The tercile spread of the sector event study is 0.00449 log-return under the deterministic tie-break; 0.00431 was one of several orders of the tied names, while the test statistic itself ($\tau = +0.198$, $p_{\text{boot}} = .94$) is tie-free, so the pre-registered verdict stands.

## Why this is the right standard

Floating-point addition is not associative, so any two implementations that sum in a different order (threads, SIMD width, kernel blocking) legitimately differ in the last bits — `[Goldberg1991]`; the project met the same mechanism one level up when macOS 27 replaced Apple Accelerate (`GEN-37`), and the Cholesky colouring of `CCR-SIM-02` is what makes those bits stay bits instead of swapping factor streams. The Monte-Carlo frame of `GEN-38` (`[Glasserman2003]`) gives the yardstick: a difference is immaterial when it is far inside the seed-to-seed spread. The sort rule follows from the `numpy.sort` contract (`[NumPySort]`): only `kind="stable"` promises an order for ties, so any artifact whose row order or cut points can involve ties must ask for it.

## Related
Read-log: [[2026-10-20_linux_landing_reproduction]] · procedure: [[linux_landing_reproduction]] · decisions: [[DECISIONS]] (`GEN-37/38/39/40`, `CCR-SIM-02`, `INT-27`) · [[CCR_MOC]] · [[MKT_MOC]] · [[HAZ_MOC]]. Home: [[_INDEX]]
#arm/int #arm/ccr #arm/mkt #arm/haz #type/explanation
