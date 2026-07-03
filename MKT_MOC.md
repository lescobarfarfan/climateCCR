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
- NGFS: `MKT-NGFS-01..03` (rate as a **shock not a level**; two anchors; short-term May-2025 vintage).
- Monte Carlo: `MKT-MC-01` · credit overlay: `MKT-CREDIT-01` · dashboard: `MKT-PHYS-01..03` · weather deriv: `MKT-WD-01`.

## Data contracts → [[DATA_CONTRACTS]]
- `DC-MKT-SIE-1..4` SIE inputs & conventions · `DC-MKT-CURVE-1` produced curve objects.
- `DC-MKT-PHYS-1..3` dashboard schema · `DC-MKT-NGFS-1`/`DC-MKT-SSP-1` scenario contracts.
- `DC-MKT-CREDIT-1..5` bond-portfolio requirements + sector crosswalk.

## Open questions → [[OPEN_QUESTIONS]]
- `OQ-MKT-01` compounding check · `OQ-MKT-02` λ estimation · `OQ-MKT-03` long-end densification.
- `OQ-MKT-04` NGFS vintage splice · `OQ-MKT-05` shock baseline · `OQ-MKT-06` stripping scope.
- `OQ-MKT-07` weather-deriv scope · `OQ-MKT-08` R1–R4 bands · `OQ-MKT-09` municipal hazard source.
- `OQ-MKT-10` `industria`↔GICS/SCIAN · `OQ-MKT-11` credit overlay in scope?

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

## Wires to the other arms
- Supplies **diffusion calibration** (HW/GBM) to [[CCR_MOC]] via `DC-CCR-CAL-1`.
- Its **FX series** can close the HAZ `MONEDA` gap (`DC-XWALK-5`); shares hazard-source questions with [[HAZ_MOC]].

## Related
Arms: [[CCR_MOC]] · [[HAZ_MOC]] · Canon: [[DECISIONS]] · [[DATA_CONTRACTS]] · [[OPEN_QUESTIONS]] · [[GLOSSARY]] · Home: [[_INDEX]]

#arm/mkt #type/workflow
