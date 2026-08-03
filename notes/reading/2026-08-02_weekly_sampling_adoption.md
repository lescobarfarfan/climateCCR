# Read-log — 2026-08-02 · The weekly-sampling adoption + the Svensson rejection

Session decisions: `MKT-CALIB-08` (weekly-sampling HW1F fit adopted as headline under the `GEN-31` adopt-if-material policy), `MKT-CURVE-06` (Svensson evaluated under a pre-registered gate and rejected), the `INT-22`/`INT-23` re-base, `GEN-32` (canon unwrap). Readings in priority order.

**Why these readings are load-bearing:** the weekly-sampling fit is now the headline calibration basis — every downstream risk number (`θ(t)`, the engine's rate dynamics, `S_rate_eff_MX`, the jump configs' rate marks, the `INT-23` band) and the entire NGFS transition channel about to be built on top inherit these parameters — and the adoption is the first executed instance of the `GEN-31` living-calibration policy, the template every future recalibration will follow. These readings are what make that basis defensible rather than merely computed.

1. **`[JamesWebber2000]`** — *Interest Rate Modelling*, the short-rate estimation chapters (Vasicek/CIR parameter estimation; the discrete AR(1) regression vs the exact transition-density likelihood). **Why:** `MKT-CALIB-08` rests on the fact that these are two estimators of the *same* model that must agree on well-specified data (`MKT-CALIB-02`); without this the 26.9%→0.2% agreement collapse reads as a coincidence instead of a verdict on the daily sample.

2. **`[Hausman1978]`** (§99, confirm before citing) — *Specification Tests in Econometrics*, the core theorem pages (1251–1256): two estimators consistent under the null, divergent under misspecification, and the test built from their difference. **Why:** the formal frame that turns the AR(1)-vs-MLE gap into a specification *test* — the adoption's validity gate W1 is exactly this logic applied at two sampling frequencies.

3. **`[CKLS1992]`** (§99, confirm before citing) — *An Empirical Comparison of Alternative Models of the Short-Term Interest Rate*, the data/estimation section (their monthly T-bill convention) and the parameter tables. **Why:** situates coarser-than-daily sampling as the field's standard answer to short-rate microstructure — the adoption is the standard practice, not an ad-hoc fix; what breaks without it is the ability to defend weekly sampling against a "you threw away data" objection.

4. **`[Svensson1994]`** — *Estimating and Interpreting Forward Interest Rates*, the section introducing the second hump term (β₃, τ₂) and its motivation. **Why:** `MKT-CURVE-06` rejected this extension; the reading shows the second decay is meant to add *curvature* flexibility — read against our residual profile (the −23 bp miss at 16.3y persisting, τ₂ landing at 0.71y to chase the short end) it becomes clear the Mexican strip's misfit is long-end pillar *sparsity*, which more parameters cannot buy (`OQ-MKT-03` densification).

5. **`[BrigoMercurio2006]`** — the Hull–White section (§3.3 in the 2nd ed.), the exact fit of `θ(t)` to the initial curve. **Why:** the robustness half of the band result — the mean path re-anchors to the same market curve under *any* `(a, σ)`, which is why the headline EPE band moved only 0.04pp while `a` moved 38%; without this the near-null re-band looks like luck.

6. **`[NelsonSiegel1987]`** — the parsimony argument for the 4-parameter family. **Why:** the positive case for what *stays*: on a 10-pillar strip, 4 parameters is the right complexity class, and the `MKT-CURVE-06` rejection is Nelson–Siegel's parsimony rationale winning empirically.

## Related
Backs: [[DECISIONS]] (`MKT-CALIB-08`, `MKT-CURVE-06`, `GEN-31`/`GEN-32`) · [[OPEN_QUESTIONS]] (`OQ-MKT-03` re-scope, the `OQ-CCR-03` NGFS starting point) · explanation note: [[2026-08-02_weekly_sampling_adoption_explained]] · prior session context: [[2026-07-20_mkt_calibration]], [[2026-07-20_hw1f_estimator_disagreement_explained]]. Arm: [[MKT_MOC]] · Home: [[_INDEX]]
#arm/mkt #type/reading
