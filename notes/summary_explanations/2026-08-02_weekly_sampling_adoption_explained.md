# Explained — 2026-08-02 · What the weekly-sampling adoption changes (and what it deliberately doesn't)

Decisions covered: `MKT-CALIB-08` (weekly HW1F headline), `MKT-CURVE-06` (Svensson rejected), the `INT-22`/`INT-23` re-base. Companion read-log: [[2026-08-02_weekly_sampling_adoption]].

## The parameters, in plain language

- **`a` = 0.0758 (mean reversion, was 0.1221).** Half-life $\ln 2 / a$ = **9.1 years** (was 5.7): a displacement of the Mexican short rate — including a climate rate jump — now takes ~9 years to decay halfway back. This is the *persistence* dial, and it is the one number the manuscript's persistence language must track.
- **`σ` = 0.0081 (instantaneous vol, was 0.0110).** 81 bp/yr of Brownian noise on the short rate.
- **Stationary sd $\sigma/\sqrt{2a}$ = 207 bp (was 223, −6.8%).** The long-horizon dispersion the Monte Carlo actually feels. `a` and `σ` fell *together* along the likelihood ridge, so this robust combination barely moved — that is the `MKT-CALIB-06` mechanism, not an accident.

## Why weekly is the better measurement, not a data diet

Daily F-TIIE is a policy step function: 54% zero-change days, weekend gaps that carry no calendar-$\Delta t$ variance — not the Gaussian diffusion either estimator assumes. The `MKT-CALIB-02` agreement check (AR(1) vs exact-MLE, a Hausman-style specification test — `[Hausman1978]` §99) *fails* on daily data (26.9% gap in `a`) and *passes* on weekly (0.2%, every sample: both anchors, both proxies). The weekly sample is the one on which the model we simulate is actually well-specified; coarser-than-daily sampling is the field's standard convention for exactly this reason (`[CKLS1992]` §99, monthly). The price: n = 937 weekly pairs vs 4,514 daily — wider confidence intervals, accepted as the cost of killing a bias.

## The S_rate_eff re-inversion, step by step

$S_{\text{rate,eff}}$ is the rate channel's *inverse sensitivity* — the damage (MDP-2025) that would move the short rate a full 10,000 bp; it exceeds Mexican GDP by construction and is not an exposure (the `INT-22` interpretation guard). The event-study scenario β is a *yield* response per damage; converting it to a *short-rate* jump divides by the HW1F loading $L(a) = (1-e^{-aT})/(aT)$ at $T$=10y. Slower decay (smaller `a`) → a jump survives longer → the same yield response needs a smaller short-rate jump: $L$ rises 0.577 → 0.701 (+21.4%), so $S_{\text{rate,eff,MX}}$ = **175,293,784 MDP-2025** (−10.9% vs the engine-`a`, was −26.6%) and the per-event rate-mark medians *shrink* ~17.6% (a median event now jumps the short rate +0.052 bp, was +0.063).

## Why the headline band barely moved — and why that is the point

Re-banded book-EPE deltas: **−8.40 / −5.07 / −4.53%** vs −8.36/−5.05/−4.51 (moves ≤ 0.04pp), on a baseline that moved −0.98% (272,314.21 → 269,655.35 MXN). The EE/PE machinery consumes three things: (i) $\theta(t)$, which re-anchors the mean rate path to the *same* market curve under any $(a,\sigma)$ (`[BrigoMercurio2006]` §3.3); (ii) dispersion $\sigma^2/2a$, which moved only −6.8%; (iii) the rate marks, which are 0.05-bp-scale events on a book whose climate delta is equity-mark-dominated. So the calibration *basis* improved (better-specified sample, internally consistent `a` everywhere) while the headline *story* is unmoved — the `MKT-CALIB-06` consequence map ("horizon-dispersion metrics are robust, persistence statements are not") validated end-to-end. What genuinely changed: the baseline level (−0.98%), jump persistence (5.7 → 9.1y), and the rate-mark scale (−17.6%).

## The Svensson rejection, read correctly

The pre-registered gate demanded rmse ≤ 6.0 bp (halving NS's 12.0); Svensson delivered 10.3 bp with its second hump ($\tau_2$ = 0.71y) chasing the *short* end, while the dominant miss (−23 bp at the 16.3y `BonosM_10_20` pillar) persisted. Diagnosis: the misfit is **long-end pillar sparsity** — 2 pillars beyond 10y — not missing curvature; a 6-parameter family cannot buy what more pillars would. Consequence: Nelson–Siegel's parsimony stands (`[NelsonSiegel1987]`), and `OQ-MKT-03` is now densification-only (off-the-run Bonos M via CF300).

## Standing caveats

`a` remains weakly identified (`MKT-CALIB-04`): the weekly anchor choice spreads it 0.076 (W-WED, the pre-registered primary) to 0.086 (W-FRI), and the informative TIIE-28 weekly fit sits near 0.32. The three-point `a` sensitivity (weekly-MLE / daily-MLE / daily-AR1) is the standing discipline for anything consuming `a` alone.

## Related
Explains: [[DECISIONS]] (`MKT-CALIB-08`, `MKT-CURVE-06`, `INT-22`, `INT-23`) · read-log: [[2026-08-02_weekly_sampling_adoption]] · builds on: [[2026-07-20_hw1f_estimator_disagreement_explained]], [[2026-07-25_mexican_book_swap_explained]]. Arm: [[MKT_MOC]] · Home: [[_INDEX]]
#arm/mkt #type/explanation
