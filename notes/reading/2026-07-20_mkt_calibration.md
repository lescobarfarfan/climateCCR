# 2026-07-20 — Reading for the Mexican market calibration (`MKT-CALIB-05/06/07`, `MKT-CURVE-05`)

Priority-ordered readings to fully own this session's decisions: the HW1F two-stage calibration on real Banxico data, the estimator-disagreement finding, the full-tenor curve strip, and the IPC GBM leg.

1. **`[BrigoMercurio2006]` — Brigo & Mercurio, *Interest Rate Models — Theory and Practice*, 2nd ed., ch. 3 (§3.3 "The Hull–White Extended Vasicek Model").**
**Why:** the architecture of `MKT-CALIB-05`/`MKT-CURVE-05` — why $a,\sigma$ come from a time series while $\theta(t)$ absorbs the entire cross-section, and why no-arbitrage is immune to the estimator disagreement. Without it, the "two-stage" split looks arbitrary.

2. **`[JamesWebber2000]` — James & Webber, *Interest Rate Modelling*, the parameter-estimation chapters (discrete-time estimation of one-factor models; ch. 17–18 in the Wiley printing — pin exact pages, §99).**
**Why:** the AR(1)/discrete-Vasicek estimator and the exact transition-density MLE implemented in `calibration/financial/hull_white.py`, plus the never-MLE-on-levels rule (`MKT-CALIB-02`). This is the estimator pair whose divergence became `MKT-CALIB-06`.

3. **`[Hausman1978]` — Hausman, *Specification Tests in Econometrics*, Econometrica 46(6), §1–2 (§99, confirm DOI).**
**Why:** the logic that turns the AR(1)-vs-MLE gap from a nuisance into a *finding*: two estimators consistent under the null model diverge only under misspecification. Backs the reading of `MKT-CALIB-06`; without it the 27% $a$ gap reads as a bug, not as evidence.

4. **`[Hull1990]` — Hull & White, *Pricing Interest-Rate-Derivative Securities*, RFS 3(4), the $\theta(t)$ derivation.**
**Why:** the exact drift formula `NelsonSiegelFit.theta` implements — $\theta(t) = \partial f/\partial t + a f + \sigma^2(1-e^{-2at})/2a$ — and the convexity adjustment in $E[r(t)]$ the fan diagnostic overlays.

5. **`[NelsonSiegel1987]` — Nelson & Siegel, *Parsimonious Modeling of Yield Curves*, J. Business 60(4).**
**Why:** the curve family of `MKT-CURVE-05` and why its betas are linear given $\tau$ — the reason the fit is a profiled `lstsq` sweep, not a nonconvex optimization. Read with `[Svensson1994]` (the flagged upgrade if the 12 bp rmse matters).

6. **`[AndersenPiterbarg2010]` — Andersen & Piterbarg, *Interest Rate Modeling*, Proposition 10.1.7.**
**Why:** the exact-transition recursion the engine's `HW1F.simulate` uses — the reason the diagnostic fan has no discretization error at a weekly grid and the MC-vs-closed-form check is a clean simulator validation.

7. **`[Glasserman2003]` — Glasserman, *Monte Carlo Methods in Financial Engineering*, ch. 1 & 3 (GBM simulation and estimation; MC standard errors).**
**Why:** the closed-form GBM MLE of `MKT-CALIB-07` (including the Itô correction from log drift back to $\mu$) and the $sd/\sqrt{n}$ yardstick that certifies the fan's 15 bp MC gap as noise.

## Related

Session decisions: [[DECISIONS]] (`MKT-CALIB-05/06/07`, `MKT-CURVE-05`, `MKT-SIE-08`). Explanation note: [[2026-07-20_hw1f_estimator_disagreement_explained]]. Prior session: [[2026-07-19_rate_leg_event_study]]. MOC: [[MKT_MOC]] · Home: [[_INDEX]]
#arm/mkt #type/reading
