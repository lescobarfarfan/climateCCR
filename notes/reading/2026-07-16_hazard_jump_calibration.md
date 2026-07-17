# 2026-07-16 — Hazard jump calibration: $\lambda$ + severity from CENAPRED (read-log)

> Session: `calibration.impact` built and first estimates produced (`INT-16`, `HAZ-STOCH-04`) — homogeneous-Poisson $\lambda$ with exact CI and a log-linear trend, lognormal per-event severity with the explicit loss→mark seam `to_mark_sampler(K)`. Headline empirics (2002–2015, nominal MXN): major-event ($\geq 100$ MDP) arrivals rise $+9.6\,\%$/yr ($p<.001$) while unthresholded severity rises $+28\,\%$/yr ($p<.001$) — two views of one drift, split by the fixed nominal threshold.

1. **Cont & Tankov — *Financial Modelling with Jump Processes*** (`[ContTankov2004]`): the compound-Poisson construction in the early Lévy-process chapters, and the statistical estimation / calibration chapter. **Why:** the jump channel (`INT-10/13`) is a compound Poisson process, and what the $(\lambda, \text{mark})$ pair identifies — the Lévy measure — is the theoretical object the `INT-16` fits estimate; without this the parameter table reads as curve-fitting rather than a Lévy-measure specification.
2. **Klugman, Panjer & Willmot — *Loss Models: From Data to Decisions*** (`[Klugman]`, §99): the frequency-model chapters (Poisson MLE, exposure bases) and the severity chapters (lognormal MLE, and the *trending/deflating losses before fitting* discipline). **Why:** the actuarial standard behind the frequency/severity split (`HAZ-STOCH-01`) and behind two `INT-16` caveats — the pending INPC deflation (`GEN-13`) and the exposure-growth vs climate-signal attribution of the $+28\,\%$/yr severity trend.
3. **Garwood — *Fiducial limits for the Poisson distribution*, Biometrika 28** (`[Garwood1936]`, §99, new): the exact $\chi^2$ interval. **Why:** it is the CI implemented in `estimate_intensity`; knowing its (fiducial/exact) construction defends the choice over the Wald interval for low-count variants (e.g. ciclón tropical, $n=144$) in the methodology chapter.
4. **IPCC — *AR6 WG1*, Ch. 11 (extremes)** (`[IPCC_AR6]`, §99): the frequency/intensity trend assessments for the relevant perils. **Why:** the measured trends must be interpreted against the physical-attribution literature before being claimed as climate signal — the `OQ-INT-07` conjecture is now a measurement, and AR6 is the anchor for whether its direction and magnitude are physically plausible for Mexico's perils.

Open decisions these readings feed: the loss→mark scale $K$ and the leading event-set variant (`OQ-INT-07`, `OQ-INT-02/04`), and the Cox / covariate-driven $\lambda(t)$ extension (`OQ-HAZ-12`).

## Related

Backs: [[DECISIONS]] (`INT-16`, `HAZ-STOCH-04`) · gates: [[OPEN_QUESTIONS]] (`OQ-INT-07`, `OQ-HAZ-12`) · contract: [[DATA_CONTRACTS]] (`DC-XWALK-4`) · keys: [[REFERENCES]] §99 · explanation: [[2026-07-16_hazard_jump_calibration_explained]] (`GEN-26`). Arm MOCs: [[HAZ_MOC]] · [[CCR_MOC]] · Home: [[_INDEX]]

#arm/haz #arm/int #type/reading
