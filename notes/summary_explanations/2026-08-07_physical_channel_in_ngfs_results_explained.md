# The physical channel inside the NGFS result set, explained (2026-08-07)

How the physical risk we have been calibrating all along — the HAZ climate-jump channel — sits inside the `INT-30/31` NGFS transition results, and how the wrong-way discussion resolves. This note answers the session-opening question in durable form: *where does the physical part enter this set of results?*

## 1. What the physical channel is, in one paragraph

The physical channel is the jump: CENAPRED discrete climate events give a Poisson arrival intensity ($\lambda = 19.29$/yr registry headline, with the regime band $9.96$/$7.22$, `INT-20`) and a lognormal per-event real loss ($\text{median} = 905.5$ MDP-2025, $\sigma = 1.21$, `INT-16`); each simulated event maps to marks — equities take $-L/K_{\text{eff}}$ distributed across names by the sector–peril weights $c_{ip}$ (`INT-24/25/26`), the rate curve takes $+L/S_{\text{rate,eff}}$ under the `[Anyfantaki2025]` literature scenario, because our own pre-registered event studies bound the *realized* Mexican responses at zero (`INT-18/19` rates, `INT-27` equities). Jump-on minus jump-off, run through the CCR engine, is the physical result.

## 2. Role 1 — the standalone headline result

Jump-on vs jump-off on the base book gives the thesis's central physical number: book-EPE **−8.40 % / −5.07 % / −4.53 %** (headline / CT anchor / floor, vs baseline 269,655.35 MXN). Nothing in the NGFS work altered this: the transition build shocked *initial conditions* (curve, S0, spreads), never the jump process, and the frozen-$\gamma$ invariant (`MKT-NGFS-08`) guarantees the physical-exposure composition is identical in every scenario.

## 3. Role 2 — the jump-on legs of the NGFS matrix, and separability

In the scenario matrix the physical channel is the jump-on leg run on transition-shocked books: combined cells $\approx$ **−12.0 %** under HWTP/SWUC. The load-bearing finding (`INT-31` c) is that the *jump-within* delta is **overlay-invariant to ~0.02 pp** (−8.54/−8.68 % under shocked books vs −8.40 % unshocked): equity jump marks are multiplicative in log-price, so scaling S0 rescales both legs of the difference and the physical percentage survives. Practically, the physical and transition channels are approximately **separable** on this book — which licenses separate-plus-combined reporting and means the physical conclusion does not hinge on which transition state you condition on.

## 4. Role 3 — DAPS_NAM as the physical channel's model-world mirror

The physical-embedding NGFS narrative (`DAPS_NAM`) runs **jump-off only** (`INT-29`): combining NGFS's own embedded physical repricing with our jump would double-count physical risk. That deliberate separation buys the manuscript a three-way triangulation of the *same* risk: NGFS's **anticipated** expectations repricing (−13.35 %), our **empirically calibrated realized-damage** channel (−8.40 %), and the **measured** contemporaneous market repricing around actual events ($\approx 0$, the `INT-18/19/27` nulls). Same direction, comparable order, three different epistemics — the operating argument for the `INT-29` split (scenario what cannot be estimated, estimate what can, compare where both exist, never sum them).

## 5. Role 4 — the CVA future work, and the wrong-way reading in full

The exposure headline is EE/EPE $= E[\max(V,0)]$: claim size, not expected loss. Under adverse states the bank's claims *shrink* (long calls die as S0 falls; cebures mark down as spreads widen) while counterparty PDs *jump* (CLIMACRED `pd_adjustment|Crude Oil` +15.4 pp on a 12.3 pp base under HWTP) — so the exposure-only delta moves in the reassuring direction exactly when default risk explodes, and expected loss $\approx \int EE \cdot dPD \cdot LGD$ rises while EPE falls. Two honesty notes fixed this session: (i) in the strict `[Gregory_xVA]` taxonomy this book's composition is *right-way* on the exposure side (claims fall as credit worsens — the textbook wrong-way trade would be long puts written by correlated counterparties); the canon's "wrong-way caveat" names the **readout hazard**, and the manuscript should carry that distinction as a footnote; (ii) part of the cebur EPE decline *is* the anticipatory credit loss itself — spread widening is the market pricing the higher PD, and jump-to-default still bites on face value net of the mark-down. The physical channel has the same structure (`INT-23`'s original form: one hurricane lowers the counterparty's equity and its creditworthiness together), and the pulled PD families include the DAPS scenarios — so the future CVA (`OQ-CCR-04`) can carry a physical-side PD leg under the same channel-separation caveat, where "oil & gas loses most" would appear directly instead of as a caveat sentence.

## 6. What today's figures add to this story

The `GEN-33` jump diagnostics are the physical calibration made visible: the staircase shows observed CENAPRED arrivals against the fitted per-regime Poisson bands across the 2016 publication break, the QQ pair shows the Exponential/lognormal fits the marks ride on, the marked stems put one simulated year-by-year loss record next to the observed one, and the daily jump-on/off paths show the channel landing on a book name at the grain the engine actually simulates. When the CVA chapter arrives, this note's §5 is its opening paragraph.

## Related
Explanation of: [[DECISIONS]] (`INT-29`, `INT-30`, `INT-31`, `INT-23` caveat; figures `GEN-33`) · companion: [[2026-08-07_validation_figures_explained]] · read-log: [[2026-08-07_viz_validation_layer]] · prior: [[2026-08-03_ngfs_equity_corporate_leg_explained]] · [[2026-07-25_headline_metric_explained]] · Home: [[_INDEX]] · MOCs: [[MKT_MOC]] · [[HAZ_MOC]]
#arm/int #arm/mkt #arm/haz #type/explanation
