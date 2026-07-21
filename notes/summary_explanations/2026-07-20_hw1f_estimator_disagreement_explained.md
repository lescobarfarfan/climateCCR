# 2026-07-20 — The Mexican HW1F calibration and the `MKT-CALIB-02` estimator disagreement, explained (`OQ-MKT-12` a/b)

> Summary-explanation note (`GEN-26`) for the session that executed the Mexican market calibration: what every fitted parameter means ($a$, $\sigma$, the stripped curve, $\theta(t)$, the IPC GBM $\mu$/$\sigma$), what the `MKT-CALIB-02` cross-check is, why it *fails* on the F-TIIE overnight sample, what that failure does and does not contaminate, and how the diagnostic figures (`pipelines/08_hw1f_diagnostics_figures.py`) demonstrate it.

## 1. What was calibrated

The MKT arm met its real data (`OQ-MKT-12` a/b): Hull–White $a$ and $\sigma$ from the F-TIIE overnight series 2006–2026 (`MKT-CALIB-01`), the MXN zero curve stripped from every SIE tenor — short block + Cetes 364 + all live Bonos M buckets — at 2026-07-17 (`MKT-CURVE-01/02`), a Nelson–Siegel fit whose analytic forwards give $\theta(t)$ (`MKT-CURVE-03`, `MKT-IR-02`), and GBM $\mu$/$\sigma$ for the S&P/BMV IPC 2001–2026. Crisis windows are excluded per `MKT-CALIB-03` — GFC 2008-09→2009-06, the post-US-election peso shock 2016-11→2017-03, COVID 2020-03→2021-06 — and every window × method × exclusion lands in `results/market_calibration/hw1f_by_window.csv` (`MKT-CALIB-04`). Everything is emitted through the `'direct_input'` seam (`DC-CCR-CAL-1`), so the engine is untouched.

## 2. What each parameter means

**$a$ (mean reversion, headline 0.122/yr).** How fast the short rate is pulled back toward its drift path; equivalently a *memory* dial: a displacement (a shock, a climate rate jump) decays at $e^{-a t}$, half-life $\ln 2/a \approx 5.7$y. In the climate channel this is literally the persistence of an injected rate mark (`DC-CCR-SIM-2`: the overlay decays through $a$).

**$\sigma$ (volatility, headline 0.0110 ≈ 110 bp/yr).** The instantaneous standard deviation of short-rate innovations. The daily change sd of the converted F-TIIE series is 6.8 bp; $6.8\sqrt{252} \approx 108$ bp — the annualization is where the number comes from, no mystery.

**The pair, not each alone.** Long-horizon dispersion is $sd(r_\infty) = \sigma/\sqrt{2a}$ and the $T$-maturity yield loading of a short-rate move is $B(T)/T = (1-e^{-aT})/(aT)$ — the first is what EE/PE/VaR consume, the second is what `rate_scale_from_beta` inverts (`INT-18`).

**The curve and $\theta(t)$.** The stripped pillars (overnight 6.58% → 9.9% at the long end) are the *cross-sectional* input: $\theta(t) = \partial f/\partial t + a f(0,t) + \sigma^2(1-e^{-2at})/2a$ makes the model reproduce today's curve exactly, whatever $a$ and $\sigma$ are (`MKT-IR-02`, `[Hull1990]`). No-arbitrage is therefore *immune* to the estimator disagreement below — that is the point of the two-stage design (`[BrigoMercurio2006]`).

**IPC GBM ($\mu$=0.110, $\sigma$=0.167, $S_0$=66,634).** Closed-form MLE on log returns with the same crisis discipline; the index is the price-leg proxy until the insurance-book swap (`OQ-INT-04`).

## 3. The `MKT-CALIB-02` check, and what its failure entails

**The check.** `MKT-CALIB-02` requires estimating $a,\sigma$ two ways — AR(1) on rate changes and exact transition-density MLE — and expects agreement "within a few percent". The logic is a specification test: for a correctly specified Gaussian OU process on an informative sample the two estimators are *the same estimator* up to $\Delta t$ handling (AR(1)-OLS is the conditional MLE at fixed spacing), so they can only diverge if the data violate the model (reference to confirm at digest: Hausman-type consistency-contrast logic, `[Hausman1978]` → §99).

**The result.** On F-TIIE 2006–2026 (crisis-excluded): AR(1) gives $a=0.096$, $\sigma=95$ bp; MLE gives $a=0.122$, $\sigma=110$ bp — a 27% gap in $a$, 16% in $\sigma$, stable across sub-windows. So the check **fails**: the F-TIIE overnight is not an OU diffusion at daily frequency, and the failure is informative, not cosmetic.

**Why it fails — two ingredients.** *(i) Non-Gaussian, non-calendar dynamics:* daily changes have excess kurtosis 42 (Gaussian: 0) and 34% of days move less than half a bp — the series hugs the Banxico target and moves in policy steps, and its weekend (3-day) changes do **not** carry $3\times$ the variance the calendar-time OU assigns them. The MLE weights pairs by true calendar $\Delta t$, the AR(1) weights them uniformly; on a process that lives in *trading time with jumps*, those two weightings disagree. *(ii) Weak identification of $a$:* the likelihood is nearly flat along a ridge $\sigma^2/2a \approx$ const (`MKT-CALIB-04` realized in data), so the modest weighting difference slides the estimate a long way *along the ridge* while barely changing the fit. The window evidence confirms it is the ridge, not the proxy: TIIE 28 is even steppier (kurtosis 97, 54% zero-change days) yet its 2001–2026 window — which contains the 2001–05 disinflation, a genuinely informative mean-reversion episode — agrees at 4%, while the same TIIE 28 on 2006–2026 disagrees by −22%.

## 4. What the failure does — and does not — contaminate

**Robust (the ridge direction preserves it).** Both fits imply nearly the same dispersion: $\sigma/\sqrt{2a}$ = 216 vs 223 bp (3% apart), $sd(r_{10y})$ = 200 vs 213 bp. The diagnostic figure `estimator_comparison` overlays the two model fans (mean $\pm 2\,sd(t)$, engine dynamics, same MXN curve): the two ribbons are visually indistinguishable — the AR(1) line is literally hidden under the MLE line. Anything that consumes rate *dispersion at a horizon* — EE/PE profiles, PFE, VaR — is insensitive to which estimator wins. The mean path is untouched by construction (§2, $\theta(t)$).

**Fragile ($a$ alone).** Anything that consumes the *speed* $a$ splits: a 100 bp climate rate jump keeps a half-life of 5.7y (MLE) vs 7.2y (AR(1)) — and 13.9y under the engine fixture's $a=0.05$ that `INT-18`'s $S_{\text{rate,eff}}$ conversion currently uses (`jump_decay` figure). The $S_{\text{rate,eff}}$ recompute with the Mexican $a$ (`OQ-MKT-12` c) therefore inherits a genuine estimator sensitivity: $J = \beta_T\, a T/(1-e^{-aT})$ grows with $a$, so MLE-vs-AR(1) moves the injected jump size by roughly the same ~15–25%.

**Verified in simulation.** The fan figure (`fan_ftiie_mle`) draws all 1,000 engine trajectories at low opacity with the Monte-Carlo mean on top of the model's own $E[r(t)] = f(0,t) + \frac{\sigma^2}{2a^2}(1-e^{-at})^2$: max gap 15 bp against an MC standard error of ~7 bp — the simulator reproduces its closed form, so the disagreement is a *data* property, not an implementation artifact. Same seed + config → bit-for-bit figures (`GEN-06/07`; manifest recorded).

## 5. How to work with it

The headline stays the exact MLE (it at least uses the true $\Delta t$), reported *with* the AR(1) row and the full window table per `MKT-CALIB-04` — a range, not a point. For $a$-sensitive outputs (jump persistence, $S_{\text{rate,eff}}$), run both fitted $a$ values as a cheap two-point sensitivity; the informative-window fit (TIIE 28, 2001–2026, $a \approx 0.26$) is the natural third anchor if a longer-memory dispute needs breaking. The manuscript caveat writes itself: *daily-frequency short-rate data identify $\sigma^2/2a$ sharply and $a$ poorly; risk metrics quoted at horizons are robust to this, jump-persistence statements are not.* A weekly-sampling refit is the obvious robustness extension if a referee presses (candidate for the digest's open-questions update).

## 6. Justification summary (references)

- `[BrigoMercurio2006]` — the HW1F two-stage design: time-series $(a,\sigma)$, cross-sectional $\theta(t)$.
- `[JamesWebber2000]` — AR(1)/discrete-Vasicek estimation and the never-MLE-on-levels rule behind `MKT-CALIB-02`.
- `[Hull1990]` — the $\theta(t)$ formula (§2) and the curvature adjustment in $E[r(t)]$.
- `[AndersenPiterbarg2010]` — the exact-transition simulation the engine (and the fan figure) uses.
- `[NelsonSiegel1987]` — the curve family whose analytic forwards feed $\theta(t)$.
- `[Glasserman2003]` — the GBM log-return MLE and MC-error yardstick in §4.
- To confirm at digest (`GEN-01`): `[Hausman1978]` (§99) for the specification-test logic in §3.

Reproduce: `python pipelines/07_market_calibration.py --forzar && python pipelines/08_hw1f_diagnostics_figures.py --forzar` → `results/market_calibration/`, `results/figures/hw1f_diagnostics/`.

## Related

Session read-log: [[2026-07-20_mkt_calibration]] (written at digest). Companion notes: [[2026-07-19_rate_leg_event_study_explained]] (the $S_{\text{rate,eff}}$ this calibration will re-derive) · [[2026-07-16_hazard_jump_calibration_explained]] (the jump channel the persistence panel speaks to). Canon: [[DECISIONS]] (`MKT-CALIB-01/02/03/04`, `MKT-CURVE-*`, `MKT-IR-02`) · [[OPEN_QUESTIONS]] (`OQ-MKT-12`) · [[MKT_MOC]] · Home: [[_INDEX]]
#arm/mkt #type/explanation
