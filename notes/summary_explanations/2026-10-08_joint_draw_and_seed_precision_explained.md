# The per-path aggregation artefact, the joint book draw and the measured Monte-Carlo precision, explained (2026-10-08)

Session decisions `CCR-SIM-03` and `GEN-38`, the correction of the `GEN-30` tail caveat, the re-base annotations on `INT-23/25/28/32/34/35`, `CCR-RISK-06/08` and `GEN-34`, and the three engine details `OQ-CCR-11/12/13`. This note explains what the morning's results freeze found, why the fix is a joint simulation of the book, how to read the re-based numbers, and what the seed study now says about the precision of every headline figure. Companion read-log: [[2026-10-08_results_freeze_joint_draw]]; the proposal structure guide written the same day is [[proposal_guide]].

## What the freeze found

The day started as housekeeping: re-run the two sensitivities that still sat on the pre-October state and add a seed study to put an actual interval on the tail levels, because the 2026-10-03 note had attributed a +10 % move of the 1y book-exposure q99 to Monte-Carlo sampling error. The seed study contradicted that reading at once. Across eleven master seeds under a fixed draw, the book-level q99 moved with a standard deviation of 0.6 %, so a +10 % move between two valid draws of the same model was a sixteen-sigma event, not noise.

The archived pre-Cholesky artifacts made the diagnosis direct. Per counterparty, the two draws were indistinguishable: identical standard deviations of the netted values, q99s within 2–3 % of each other. Across counterparties they were different worlds: the mean pairwise correlation of netted values at one year was 0.06 under the SVD colouring and 0.21 under the Cholesky colouring; two debt-only sets with identical factor sets moved together exactly in both; a payer-swap set and a debt-only set, both driven by the same curve, were uncorrelated in both; and two single-equity sets went from −0.58 to +0.96.

The cause is the engine's per-portfolio design, inherited from PIMPA. `pipelines/01` valued the book one netting agreement at a time, and each session drew its own standard normals from the master seed over its own event-driven grid and its own factor subset, then coloured them with its own sub-correlation. Each counterparty's marginal law was correct, but the realisation of the market differed from counterparty to counterparty, and the only thing linking them was which latent stream happened to land on which factor, which depends on the shape of each draw and on the ordering convention of the square root. Worse, the climate-event counts follow the grid too, so the book carried four independent event streams: the five-, seven- and ten-year swap groups and the bonds-only pair each saw their own climate history.

## Why the fix is a joint draw, and what it changes

A counterparty-credit engine's scenario set is one set of market paths for the whole book: a rate move or a hurricane on path $j$ hits every counterparty on path $j$. `CCR-SIM-03` restores that. The session is split into `prepare`, `simulate` and `value`; `prepare_book` prepares every netting set, `simulate_book` runs the ordinary draw once on the sorted union of their grids with the union of their factors and the book's 28×28 correlation, applying the climate-jump substream and the scheduled overlay once, and `slice_scenarios` hands each netting set exactly its own factors and dates, so pricing, collateral and exposure code are untouched. The joint store is an explicit argument of `simulate`, never a key in the shared parameter dictionary, so a later leg can never slice a stale store.

Three things are guaranteed in law. A subset of a joint $N(0, C)$ draw has the law $N(0, C_{\text{sub}})$, and the Mexican matrix is positive definite, so every netting set's sub-block is exactly the one it simulated before. The diffusions are exact-transition schemes, so a finer common grid (58 dates on the long horizon, the ten-year swap schedule, which already contains the shorter ones) changes no marginal. And the jump-off and jump-on legs share every diffusion normal under one draw per leg, so the climate delta remains a paired difference. Only the realisation changes, and with it every number by a re-draw: baseline book EPE moved +0.026 %, the headline band from −8.97 to −9.00 %, per-counterparty EPEs by a median 0.02 %. The dependence across counterparties became the modelled one: the payer swap and the long bonds on one curve move exactly opposite (−1.000), the ASUR and GAP sets correlate at +0.46 against a modelled 0.50, ASUR and VOLAR at +0.23 against 0.25, and the mean pairwise correlation is 0.05. The old aggregate had inflated the book tail by about 13 %. A welcome side effect is cost: the jump scenario is generated once instead of thirty times, so a cell runs in about twenty seconds instead of two minutes.

The per-counterparty draw survives as `--por-contraparte` for diagnostics and as the lock of the original PIMPA goldens; a third golden locks the joint draw on the fixture. The manifest records which mode produced a run; an older manifest without the key is per-counterparty era.

## How to read the re-base

| Readout | 2026-10-03 state | joint draw, 2026-10-08 |
|---|---|---|
| Baseline book EPE (MXN) | 255,670.01 | 255,735.47 |
| Band EPE shift, headline / CT anchor / floor | −8.97 / −5.54 / −4.99 % | −9.00 / −5.51 / −4.99 % |
| Effective EPE shift | −2.20 / −1.59 / −1.46 % | −2.18 / −1.56 / −1.43 % |
| Nivel transition HWTP / SWUC / DAPS_NAM | −5.72 / −8.16 / −20.01 % | −5.72 / −8.16 / −20.02 % |
| Trayectoria transition | −1.49 / −1.23 / +0.16 % | unchanged |
| Fase transition | −4.57 / −6.62 / −7.37 % | unchanged |
| Base book CVA (LGD 0.60) | 515,139 | 515,270 |
| Riders, registry / CT bridge | −9.36 / −9.03 % | −9.38 / −9.05 % |
| 1y book-exposure q99, headline | 3,433,541 → 2,999,986 (−12.6 %), an artefact | 3,041,356 → 2,727,327 (−10.3 %), a model output |

Every conclusion of `INT-37` stands: H1 was never touched, H2's band moved by hundredths of a point, H3's separability holds (jump-within deltas invariant to 0.1–0.3 pp across the flavours). The one number that changed in kind rather than in degree is the book-level per-path quantile, which the manuscript may now report.

## The seed study, read correctly now

`pipelines/24` re-runs each band configuration under ten extra master seeds with only the seed changed and reads the spread across the eleven realisations. On the joint draw the standard deviation across seeds is 0.01–0.03 pp for the book EPE shift, 0.02 pp for Effective EPE, 0.20–0.25 pp for the summed supervisory PFE99 shift, 0.4 % for the 1y book-exposure q99 level (its range over eleven seeds is 1 %) and 0.3 pp for that quantile's paired climate delta. These are the intervals Chapter 5 should print beside the levels. The `GEN-30` amendment that put a 10 % error on tail levels is withdrawn in place: that number was the aggregation artefact changing with the mixing matrix, and the measured precision of a 10,000-path quantile is about half a percent, as the quantile-estimator variance predicts.

Two readings follow for the manuscript. Means and paired deltas are precise to the second decimal of a percentage point, so the band, EEPE, CVA and the three-flavour table can be quoted as they are. Tail levels are precise to about half a percent and their climate deltas to about a third of a point, so a q99 may be quoted to three significant figures with that interval, and tail-to-tail comparisons across scenarios must respect it.

## The sensitivities on the current state

Both sensitivities were re-run twice today, first on the 2026-10-03 state and then on the joint draw; the canon carries the joint-draw values. The S-tier variants needed one fix to run at all: the adopted configs have carried per-peril severity since `INT-26`, and the two merged-label variants collapsed the labels without re-fitting the block, which the engine rightly rejects. They now re-fit mean-matched per-label severity on the merged groups, the same method pipeline 14 already applied, so the variant moves only the S matrix. On the joint draw every S-tier variant sits within 1.3 pp of its base leg with the ordering intact and the fluvial merge identical to the base at two decimals, and the storm-clustered band reads −8.45 / −4.06 / −5.13 % against −9.00 / −5.51 / −4.99, the CT anchor still the grain-sensitive leg, the book-summed PFE99 tail easing in all three bands.

## Limits to state when citing this session

The joint store lives in memory, which is 0.4 GB on the long horizon and would be about 24 GB on a daily Mexican grid; such a run would use `--por-contraparte` or a path-chunked draw that does not exist yet. Two overlay details move with the grid in the direction of the continuous-time model (HW1F jump marks decay from the end of a finer step; trajectory intensities are summed left-point per step), second-order on this book. The exploration surfaced three engine details that are not on the results chain and are logged as open questions: the close-out exposure pairs each date with the most recent default-grid collateral balance rather than its own, the option pricer picks its non-share underlying by list position, and the GBM term-structure volatility reuses the previous variance at a time exactly equal to the last surface tenor. The pre-joint state keeps its tag (`results-freeze-2026-10-08`) and its archived artifacts (`results/_archive/20261008_per_naid_draw/`).

## Related
Decisions: [[DECISIONS]] (`CCR-SIM-03`, `GEN-38`, `GEN-30`, `GEN-34`, `INT-23/25/28/32/34/35`, `CCR-RISK-06/08`) · Open: [[OPEN_QUESTIONS]] (`OQ-CCR-11/12/13`) · Read-log: [[2026-10-08_results_freeze_joint_draw]] · Guide: [[proposal_guide]] · Prior explanation: [[2026-10-03_canonical_draw_and_extenso_2024_explained]] · Arms: [[CCR_MOC]] · [[MKT_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]
#arm/int #arm/ccr #type/explanation
