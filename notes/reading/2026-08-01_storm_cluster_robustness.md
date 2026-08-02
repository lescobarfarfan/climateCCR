# 2026-08-01 · Storm-cluster robustness — session read-log

Session decisions: `INT-28` (storm-clustered sensitivity — the `OQ-INT-11` f grain robustness), `HAZ-CENAPRED-12` (MDP/MDD triage resolution under the user rule), `HAZ-SOURCES-04` (HAZ data roots re-anchored), `GEN-31` (living-calibration direction; adopt-if-material policy for the MKT desirables).

1. **[ContTankov2004] — Cont & Tankov, *Financial Modelling with Jump Processes*, §2.5 (Poisson random measures) and ch. 3 (compound Poisson processes).** Why: the exact invariance `INT-28` leans on — merging arrival points while summing their marks preserves the compound sum $\sum_i L_i$ over any window, so $\lambda \cdot \bar{L}$ (the empirical compound rate) is grain-free by construction while higher moments and the tail are not. Without this, the "λ·E[L] invariant, tails not" claim reads as an assertion instead of aggregation algebra.

2. **[Klugman2019] — Klugman, Panjer & Willmot, *Loss Models*, 5th ed., the severity-MLE chapter (lognormal fitting) and the model-selection discussion.** Why: the clustered refit fits the same lognormal family to fewer, larger observations; the *fitted* mean $\mathrm{median} \cdot e^{\sigma^2/2}$ moves under re-graining (the Jensen wedge in `parameter_summary.csv` — +1.7% registro, +77% floor) even though the empirical mean is conserved, and the simulation draws from the fitted law. This is why the floor band deepens slightly while the CT anchor eases.

3. **[PielkeLandsea1998 ref?] — Pielke & Landsea, normalized hurricane damages (§99, still to confirm).** Why: the reporting-grain caveat behind treating state rows vs whole storms as the event unit; the same measurement-vs-physics concern motivates both the `INT-28` sensitivity and the conservative `HAZ-CENAPRED-12` exclusion of magnitudes that cannot be externally corroborated.

## Related
[[2026-08-01_storm_cluster_robustness_explained]] · [[2026-07-30_peril_typed_events]] · [[DECISIONS]] · [[OPEN_QUESTIONS]] · [[HAZ_MOC]] · [[CCR_MOC]] · Home: [[_INDEX]]
#arm/int #arm/haz #type/reading
