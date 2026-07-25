# 2026-07-25 — The headline λ and the regime band, explained

> Companion to [[2026-07-25_lambda_band_readout]] (the read-log). Decision: `INT-20`, resolving `OQ-HAZ-19`(a).

## What was decided

The headline climate-jump EE/PE run (`configs/climate_jump_real.yaml`) keeps the **registry-regime arrival intensity $\lambda = 19.2857$ events/yr**, and two new configs turn the measurement-regime uncertainty into explicit robustness scenarios instead of a prose caveat: a **report-regime floor** (`configs/climate_jump_real_floor.yaml`, $\lambda = 7.2222$) and a **cyclone-bridge anchor** (`configs/climate_jump_real_ct_anchor.yaml`, $\lambda = 9.9565$). The Mexican-$a$ recompute of the rate-leg scale $S_{\text{rate,eff}}$ was explicitly deferred to the fixture-book swap.

## What each intensity means

$\lambda$ is the expected number of jump-triggering climate events per year — events whose real damage clears the 200 MDP-2025 bar (`HAZ-STOCH-04/05`). The three values are *the same physical Mexico seen through three measurement lenses* (`HAZ-CENAPRED-10`):

- **19.2857/yr (registry, 2002–2015):** what CENAPRED's event×state registry recorded. This is the regime in which the loss→mark scale ($\beta$, $K_{\text{eff}}$, `INT-17`) and the severity marks were estimated, so the headline pairs like with like.
- **7.2222/yr (reports, 2016–2024):** what the annual *Impacto Socioeconómico* reports make countable — a floor by construction, because the post-2016 grain censors small/medium discrete events (83% of new rows are undated state-year aggregates).
- **9.9565/yr (ciclón bridge, pooled 2002–2024):** the arrival level of the only event set measured at the same grain in both regimes — an anchor for the *level*, not a cyclone-only loss model, which is why this scenario keeps the registry marks.

## Why severity travels with its own λ (regime-consistent pairing)

The compound loss rate is $\lambda\,\mathbb{E}[L]$. The 2016 break did not destroy events — it moved them out of the countable set, so measured frequency fell (19.3 → 7.2) while measured severity rose (median 905.5 → 1,274.1 MDP-2025, left-censoring near the bar). Pairing the floor $\lambda$ with registry severity would double-count the censoring: each scenario therefore uses the $(\lambda, \text{median}, \sigma)$ triple from its own fit window (`results/hazard_jump_calibration_2000_2024/parameters.csv`), and the equity/rate mark medians rescale as $\text{median}/K_{\text{eff}}$ and $\text{median}/S_{\text{rate,eff}}$ ($\sigma$ transfers exactly — dividing a lognormal by a scale moves only its median, `INT-16`).

## How to read the results

Mean EE / PE$_{99}$ shift (jump-ON − baseline, `largo` horizon, seed 233423, reproduced on `main`):

| NAID | headline $\lambda=19.29$ | CT anchor $\lambda=9.96$ | floor $\lambda=7.22$ |
|---|---|---|---|
| 23 (IRS book) | +1.11 / +1.11 | +0.57 / +0.69 | +0.48 / +0.44 |
| 24 | −0.20 / −0.38 | −0.10 / −0.15 | −0.09 / −0.16 |
| 25 | +0.06 / +0.17 | +0.03 / +0.09 | +0.03 / +0.12 |
| 26 (short book) | +0.00 / −1.00 | +0.00 / −0.09 | +0.00 / −0.07 |

Three things to see. **(1) The scaling validates the design:** the CT anchor shares the headline marks, so its EE shift scales with the bare intensity ratio ($9.96/19.29 \approx 52\%$); the floor carries its own (bigger) marks, so it scales with the compound-rate ratio ($\approx 43\%$, not the bare $37\%$). **(2) The band is roughly a factor of two**, and it is *measurement* uncertainty, not climate uncertainty — the manuscript should present it as the cost of the 2016 publication break. **(3) NAID 26's PE$_{99}$ is strongly nonlinear in $\lambda$** (−1.00 vs −0.07/−0.09): the short book's raw-quantile PE (`OQ-CCR-08`) reacts to how *often* the far tail is populated, not proportionally — worth a manuscript note when the PE convention is settled.

## The deferral (why the Mexican $a$ waits)

$S_{\text{rate,eff}}$ inverts the target yield response through the HW1F loading $B(T) = (1-e^{-aT})/aT$ **of the engine that simulates the jumps** ($a = 0.05$, the locked fixture calibration, `INT-18`). Recomputing it with the Mexican $a = 0.122$ while the engine still runs $a = 0.05$ would break that round trip — the injected jump would decay at the wrong speed relative to the scale that sized it. Direction check, pinned for the record: at $T = 10$y the loading falls from $0.787$ to $0.577$, so $S_{\text{rate,eff}}$ drops $\approx 27\%$ and the rate marks *grow* — faster mean reversion needs a bigger initial jump to move the 10-year yield the same amount. The exact recompute is one call (`rate_scale_from_beta`) and lands with the book swap (`OQ-INT-04`), when engine dynamics and inversion share the Mexican $a$.

## Justification

Compound-Poisson separation of intensity and marks: `[ContTankov2004]` ch. 3, 6. Frequency/severity as one observation process (the pairing rule): `[Klugman]` (§99). Recorded-loss series as measurement artifacts (the regime-band framing): `[PielkeLandsea1998]` (§99).

## Related

Decision: [[DECISIONS]] (`INT-20`) · read-log: [[2026-07-25_lambda_band_readout]] · predecessors: [[2026-07-21_cenapred_regime_break_and_otis_explained]] (the regime bounds) · [[2026-07-18_k_scale_deflation_explained]] (the scale $K_{\text{eff}}$) · gates: [[OPEN_QUESTIONS]] (`OQ-INT-02`, `OQ-INT-04`, `OQ-MKT-12`). Arm MOCs: [[HAZ_MOC]] · Home: [[_INDEX]]

#arm/haz #arm/int #type/explanation
