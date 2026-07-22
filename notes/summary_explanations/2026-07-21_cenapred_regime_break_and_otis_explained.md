# 2026-07-21 — The CENAPRED regime break and the Otis-leveraged null, explained

Plain-language companion (`GEN-26`) to `HAZ-CENAPRED-10`, `HAZ-STOCH-06`, and `INT-19`. Read-log: [[2026-07-21_cenapred_extension_regime_runs]].

## What changed in the data source (the regime break)

Until 2015 CENAPRED published its internal registry: one row per event per state, ~400–550 rows a year, including hundreds of small events. From 2016 it only publishes annual reports, and the extraction (validated in `VALIDACION_2016_2024.md`) can only be as fine as those reports: cyclones and earthquakes keep one row per (event, state), but rains, drought, frost and the minor perils appear as one row per state per *year*, with generic 1-Jan–31-Dec dates. The jump calibration keeps only *dated discrete events* (`duracion_dias` < 360), so those annual rows are dropped — 83 % of the new rows, versus 8.8 % historically.

**Consequence:** the count of qualifying events falls from 19.3/yr (2002–2015) to 7.2/yr (2016–2024) for the leading `mayores_200mdp` set — but that fall is *measurement*, not climate. The tell is the composition: cyclone arrivals, measured the same way in both regimes, are continuous (10.3 vs 9.4/yr), while the perils that lost event grain collapse to near zero in the filtered set.

## What each new quantity means

- **Report-regime $\lambda = 7.2$/yr $[5.6, 9.2]$** — the arrival intensity of separately-identified major events under the *new* measurement standard. A floor, not the "true" rate: some real ≥200-MDP events are hidden inside annual aggregates.
- **Registry-regime $\lambda = 19.3$/yr** — the same quantity under the old, finer standard (unchanged from `HAZ-STOCH-05`).
- **The ciclón bridge $\lambda \approx 10$/yr, trend $+1.4\,\%$/yr ($p=.17$)** — the only series comparable across the full 23 years. Its flat trend is the honest cross-regime statement about arrivals.
- **The pooled $-2.9\,\%$/yr ($p=5\times10^{-4}$)** — *deliberately reported as an artifact*: fitting one trend across a measurement downgrade mechanically produces "decline". It documents why pooled fits are forbidden, nothing else.

## Why the trajectory λ(t) plan was dropped

The old plan extrapolated the 2002–2015 growth to the 2025 valuation date ($\lambda(2025)\approx 69$/yr). The extension lets us *look* at 2016–2024: observed arrivals are 7–9/yr and flat. An extrapolation refuted by nine years of out-of-sample data cannot anchor the thesis; the injection returns to homogeneous $\lambda$, with the three defensible levels (7.2 / ~10 / 19.3) as a scenario band — choosing the headline level is `OQ-HAZ-19`(a). The severity side is untouched: $\sigma$ is stable (1.21 vs 1.04) and the medians differ exactly as left-censoring near the threshold predicts.

## The event-study re-run (why the null got stronger, not weaker)

The `INT-18` gate — fixed before any estimation in 2026-07-19 and re-applied verbatim — asks: does the cumulative abnormal move of the longest Bono M yield over $[0,+5]$ business days scale with episode loss? On 2002–2024 ($n=100$ episodes, Otis included): $\beta = -5.9\times10^{-6}$ per bn MDP-2025, $p=.734$ → **FALLA**, the null stands.

The 2016–2024 subsample *looks* like a pass ($\beta = +1.24\times10^{-5}$, HC1 $p=.019$) — but two diagnostics unmask it. First, the pairs-bootstrap $p=.28$ disagrees with the analytic $p$; that gap is the classic signature of a single high-leverage observation (`[BelsleyKuhWelsch1980]`). Second, the jackknife: remove the one Otis episode (91,540 MDP-2025 — five times the next largest loss) and the slope flips to $-5.0\times10^{-5}$ ($p=.82$). With $n=31$, the "effect" is one data point.

**What Otis actually did to yields:** the 20–30y Bono yield rose $+22.9$ bp abnormal over $[0,+1]$ (9.89 % → 10.17 %), was still $+17.5$ bp at $[0,+5]$, and was back to $-1.4$ bp by $[0,+10]$ — a real but *transitory* repricing, fully reverted in two weeks (the early-November global bond rally is netted out by the DGS30 control). One event's transitory spike is evidence of market *attention*, not of a persistent loss→yield pricing channel.

## What this means for the thesis (climate contagion to financial markets)

- The **rate leg** of the contagion channel is empirically bounded near zero for Mexico over 23 years *including* the strongest possible shock — upgraded from a sample-limited null to a robust finding (fiscal absorption in the FONDEN era; transitory repricing after). The `[Anyfantaki2025]` literature scenario stays as the deliberately conservative Path-B overlay, unchanged in `configs/climate_jump_real.yaml`.
- The **estimated** contagion channel is the price/loss leg (`INT-17`): severity-driven jump risk on the insurance book, whose parameters are regime-robust.
- The arrivals-growth narrative moves from "arrivals are rising +8.4 %/yr" to "arrivals growth is not identifiable across the measurement regimes; within the consistent cyclone series it is flat" — with the `[PielkeLandsea1998]` exposure/reporting caveat now carrying data support of its own.

## Related

Explains: [[DECISIONS]] (`HAZ-CENAPRED-10`, `HAZ-STOCH-06`, `INT-19`) · read-log: [[2026-07-21_cenapred_extension_regime_runs]] · predecessors: [[2026-07-19_rate_leg_event_study_explained]] · [[2026-07-18_k_scale_deflation_explained]] · contracts: [[DATA_CONTRACTS]] (`DC-HAZ-CENAPRED-1`, `DC-XWALK-4`) · open: [[OPEN_QUESTIONS]] (`OQ-HAZ-19`). Arm MOCs: [[HAZ_MOC]] · [[MKT_MOC]] · Home: [[_INDEX]]

#arm/haz #arm/int #type/explanation
