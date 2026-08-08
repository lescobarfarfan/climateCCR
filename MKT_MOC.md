# MKT_MOC — Market / rate & scenarios (the calibration & simulation engine)

> Map of content for the **MKT arm**: Hull–White/Vasicek calibration to Banxico data, the SIE yield
> curve, NGFS scenario translation, Monte-Carlo VaR/ES, the physical-risk dashboard, the credit
> overlay, and weather derivatives. Hub note. Home: [[_INDEX]].

**Role in the machine (`INT-11`):** the **stochastic engine** — Hull–White is one risk-factor model
(GBM another) whose calibrated parameters feed the [[CCR_MOC|CCR]] simulation in `'direct_input'`
form; it also supplies the scenario shocks (fixed level or trajectory) that climate assumptions ride
in on (`INT-12`).

## Decisions → [[DECISIONS]]
- Scope: `MKT-SCOPE-01/02` (Mexico as benchmark; EM comparators).
- Hull–White: `MKT-IR-01..03` · change of measure: `MKT-MEAS-01/02` (Q vs P, λ).
- SIE data: `MKT-SIE-01..05` (CF300/CA684/CA766; simple-interest Act/360; build from stripped zeros).
- Curve: `MKT-CURVE-01..04` (364-day Cetes 1Y pillar; strip from dirty price; NS/Svensson).
- Calibration: `MKT-CALIB-01..04` (F-TIIE overnight proxy; AR(1)/MLE; exclude COVID; weak `a`).
- Stress: `MKT-STRESS-01..03` (shock set; recalibrate θ; CNBV/Basel anchors).
- NGFS: `MKT-NGFS-01..08` (rate as a **shock not a level**; two anchors + the ST-grain adaptation; ST-first connector shipped 2026-08-02 with the WEO-anchored baseline delta, the HWTP/SWUC+DAPS set, and the first transition results — `INT-29/30`; the sector-grain equity/corporate leg wired 2026-08-03 with the sign-flipping full-leg deltas and the wrong-way PD reading — `MKT-NGFS-08`/`INT-31`).
- Monte Carlo: `MKT-MC-01` · credit overlay: `MKT-CREDIT-01` · dashboard: `MKT-PHYS-01..03` · weather deriv: `MKT-WD-01`.

## Data contracts → [[DATA_CONTRACTS]]
- `DC-MKT-SIE-1..4` SIE inputs & conventions · `DC-MKT-CURVE-1` produced curve objects.
- `DC-MKT-PHYS-1..3` dashboard schema · `DC-MKT-NGFS-1/2` (umbrella + the realized ST connector) / `DC-MKT-SSP-1` scenario contracts.
- `DC-MKT-CREDIT-1..5` bond-portfolio requirements + sector crosswalk.

## Open questions → [[OPEN_QUESTIONS]]
- `OQ-MKT-01` compounding check · `OQ-MKT-02` λ estimation · `OQ-MKT-03` long-end densification.
- `OQ-MKT-04` NGFS vintage splice (deferred to the LT join) · `OQ-MKT-13` NGFS extensions (trajectory flavor, LT join, equity leg) · `OQ-MKT-06` stripping scope.
- `OQ-MKT-07` weather-deriv scope · `OQ-MKT-08` R1–R4 bands · `OQ-MKT-09` municipal hazard source.
- `OQ-MKT-10` `industria`↔GICS/SCIAN · `OQ-MKT-11` credit overlay in scope? · (`OQ-MKT-05` closed 2026-08-02 → `MKT-NGFS-05`; `OQ-MKT-12` closed 2026-08-02 → `MKT-CALIB-08`/`MKT-CURVE-06`.)

## Notes (under `notes/`)
- Theory — Hull–White (`notes/theory/hull_white_1f/`): [[Hull_White_Comprehensive]], [[HWModel_Theory]],
  [[Hull-White-1F-calibration]], [[Hull‑White_theta_Intuition]], [[market_calibration]],
  [[Calibration_From_SIE_Banxico_01]], [[Calibration_From_SIE_Banxico_02]], [[all_info]].
- Theory — rates / curve / measure (`notes/theory/`): [[Vasicek_Calibracion_Mex]], [[ChangeOfMeasureInFinance]],
  [[instrumentos_deuda_mexico]], [[mexican_yield_curve_methodology]].
- Theory — Monte Carlo (`notes/theory/`): [[monte_carlo_risk_management_framework]], [[monte_carlo_climate_risk_applications]].
- Theory — scenarios / credit (`notes/theory/`): [[ngfs_short_term_scenarios_summary]], [[how_to_use_NGFS_PolicyRate]],
  [[climate_exposed_countries]], [[climate_risk_data_requirements_bonds]], [[climate_risk_credit_methodology_references]],
  [[referencias_weather_derivatives]].
- Pipelines (`notes/pipelines/`): [[dashboard_riesgo_excel]].
- Sources (`notes/sources/`): [[mexican_data_sources]].
- Writeup (`literature/`): [[climate_integrated_investment_analysis]], `refs.bib` (BibTeX).
- Reading (`notes/reading/`, `GEN-21`): [[2026-07-19_rate_leg_event_study]] — event-study design, the ECB fallback source, and the HW1F yield loading behind the rate leg (`INT-18`, `MKT-SIE-06/07`). [[2026-07-20_mkt_calibration]] — the HW1F two-stage design, the AR(1)/MLE estimator pair and the specification-test reading of their divergence, NS profiling, exact-transition simulation (`MKT-CALIB-05/06/07`, `MKT-CURVE-05`). [[2026-07-21_cenapred_extension_regime_runs]] — the extended-window event-study re-run and the leverage diagnostics behind the Otis subsample (`INT-19`). [[2026-07-25_mexican_book_swap]] — the book swap: per-name GBM fits, the FIX FX leg, and the Mexican-`a` re-inversion of the rate scale (`INT-21`/`INT-22`). [[2026-08-02_weekly_sampling_adoption]] — the weekly-sampling adoption readings: the estimator pair as a specification test, coarse-sampling conventions, and why the Svensson rejection is about pillar support (`MKT-CALIB-08`/`MKT-CURVE-06`). [[2026-08-02_ngfs_short_term_connector]] — the NGFS connector readings: the ST technical documentation, the DNB/Fed/ACPR/CBES translation precedents, the Mexican anchors, and the exposure-kink chapter behind the non-monotone transition delta (`MKT-NGFS-04..07`, `INT-29/30`). [[2026-08-03_ngfs_equity_corporate_leg]] — the equity/corporate-leg readings: the CLIMACRED variable definitions and sector annex, the Battiston et al. structural model behind them, the wrong-way-risk chapter that frames the exposure-vs-PD reading, and the Banxico Recuadro-6 pilot (`MKT-NGFS-08`, `INT-31`). [[2026-08-07_viz_validation_layer]] — the validation-layer readings: fan-chart density evaluation and the coverage backtest, actuarial GOF (QQ) for the jump channel, the P-vs-pricing measure distinction behind the two rate fans, and the EE/EPE semantics of the cross-run family (`GEN-33`).
- Explanation (`notes/summary_explanations/`, `GEN-26`): [[2026-07-19_rate_leg_event_study_explained]] — what β(T)/CAR/`S_rate_eff` mean, how to read the pre-registered null (a bound, not a failure), and which parts of the wired rate channel are estimate vs scenario. [[2026-07-20_hw1f_estimator_disagreement_explained]] — the Mexican HW1F/GBM parameters, why the `MKT-CALIB-02` AR(1)-vs-MLE check fails on F-TIIE (weakly identified `a` on a step-like series), what stays robust (σ²/2a dispersion) vs fragile (jump persistence), with the `pipelines/08` diagnostic figures. [[2026-07-21_cenapred_regime_break_and_otis_explained]] — the reconfirmed rate-channel null and the Otis anatomy (+23 bp at $[0,+1]$, reverted by $[0,+10]$): transitory repricing, not a pricing channel (`INT-19`). [[2026-07-25_mexican_book_swap_explained]] — `S_rate_eff` as the rate channel's inverse sensitivity (damage per 10,000 bp move — why 144.3M MDP-2025 is correct, not 5× GDP of exposure), the −26.6% Mexican-`a` recompute, and the `[Anyfantaki2025]` ~12×-bound scenario flag (`INT-22`). [[2026-08-02_weekly_sampling_adoption_explained]] — what `a`=0.0758/`σ`=0.0081 mean (half-life 9.1y, stationary sd 207 bp), why weekly is the better-specified sample, the +21.4% loading behind `S_rate_eff_MX` 175.3M, why the EPE band moved ≤0.04pp, and the Svensson rejection anatomy (`MKT-CALIB-08`/`MKT-CURVE-06`). [[2026-08-02_ngfs_transition_channel_explained]] — the NGFS short-term transition channel end to end: the five decisions in plain language, what the anchors/shock/readout columns mean, the three headline findings (the non-monotone transition delta via the exposure kink; the physical-band robustness; DAPS_NAM as the model-world counterpoint to the `INT-18/19` null), the literature map, and the stated limitations (`MKT-NGFS-04..07`, `INT-29/30`). [[2026-08-03_ngfs_equity_corporate_leg_explained]] — the equity/corporate leg: sector-grain S0 revaluations + excl-policy cebur spread shocks, the sign-flipping full-leg transition deltas (HWTP −3.78 / SWUC −3.65 / DAPS −13.35 %), the DAPS-vs-`INT-27` counterpoint, and the (e) resolution — the "inner-band reordering" was a label crossing, not a real swap (`OQ-MKT-13` c/d/e). [[2026-08-07_validation_figures_explained]] — the model-vs-observed figure sets end to end: the coverage findings (F-TIIE 54/47 %, equities 83–100 %), the unidentifiable ≤2022 rate refit and the conditional-cone convention, the jump diagnostics, the daily jump-path convention, and the cross-run EPE matrix/strips (`GEN-33`). [[2026-08-07_physical_channel_in_ngfs_results_explained]] — how the calibrated physical jump sits inside the NGFS result set: standalone headline, separable jump-on legs, the DAPS counterpoint triangulation, and the wrong-way/CVA reading in full (`INT-29/31`, `OQ-CCR-04`).

## Wires to the other arms
- Supplies **diffusion calibration** (HW/GBM) to [[CCR_MOC]] via `DC-CCR-CAL-1`.
- Its **FX series** can close the HAZ `MONEDA` gap (`DC-XWALK-5`); shares hazard-source questions with [[HAZ_MOC]].

## Related
Arms: [[CCR_MOC]] · [[HAZ_MOC]] · Canon: [[DECISIONS]] · [[DATA_CONTRACTS]] · [[OPEN_QUESTIONS]] · [[GLOSSARY]] · Home: [[_INDEX]]

#arm/mkt #type/workflow
