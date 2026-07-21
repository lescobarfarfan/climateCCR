# REFERENCES — Verified bibliography

Each entry below was checked against a primary/authoritative source (or carried over verified from an
origin project) and, where applicable, carries a DOI or stable URL. Each lists the decision ID(s) it
backs. Citation keys (e.g. `[Holland1980]`) are used throughout the canon.

Entries under **§99 To confirm** are cited in the project but their exact edition/DOI/URL has not been
independently re-verified in this consolidation; do not cite them in the manuscript until checked
(tracked in `OPEN_QUESTIONS.md`). The full **climate-finance bibliography (47 entries)** travels with
the repo at `literature/refs.bib` (from the MKT-arm LaTeX writeup); §6 lists the load-bearing keys and
points there for exact DOIs rather than risk transcribing them imperfectly here.

---

## 1. Tropical-cyclone hazard (HAZ-IBTRACS)

- **`[Holland1980]`** — Holland, G. J. (1980). *An Analytic Model of the Wind and Pressure Profiles in Hurricanes.* Monthly Weather Review, 108(8), 1212–1218. DOI: 10.1175/1520-0493(1980)108<1212:AAMOTW>2.0.CO;2 — Backs `HAZ-IBTRACS-04`.
- **`[KaplanDeMaria1995]`** — Kaplan, J., & DeMaria, M. (1995). *A Simple Empirical Model for Predicting the Decay of Tropical Cyclone Winds after Landfall.* Journal of Applied Meteorology, 34(11), 2499–2512. DOI: 10.1175/1520-0450(1995)034<2499:ASEMFP>2.0.CO;2 — Backs `HAZ-IBTRACS-05` (US-derived coefficients applied as a conservative minimum on Mexican landfalls).
- **`[Knapp2010]`** — Knapp, K. R., Kruk, M. C., Levinson, D. H., Diamond, H. J., & Neumann, C. J. (2010). *The International Best Track Archive for Climate Stewardship (IBTrACS): Unifying Tropical Cyclone Data.* BAMS, 91(3), 363–376. DOI: 10.1175/2009BAMS2755.1 — Backs `HAZ-IBTRACS-01`.
- **`[IBTrACSv04r01]`** — Gahtan, J., Knapp, K. R., Schreck, C. J., Diamond, H. J., Kossin, J. P., & Kruk, M. C. (2024). *IBTrACS Project, Version 4r01.* NOAA NCEI. DOI: 10.25921/82ty-9e16 — Backs `HAZ-IBTRACS-01` (cite both the BAMS paper and the dataset DOI).

## 2. Impact functions & exposure (HAZ-CLIMADA)

- **`[Emanuel2011]`** — Emanuel, K. (2011). *Global Warming Effects on U.S. Hurricane Damage.* Weather, Climate, and Society, 3(4), 261–268. DOI: 10.1175/WCAS-D-11-00007.1 — Backs `HAZ-CLIMADA-07`.
- **`[Eberenz2021]`** — Eberenz, S., Lüthi, S., & Bresch, D. N. (2021). *Regional tropical cyclone impact functions for globally consistent risk assessments.* NHESS, 21(1), 393–415. DOI: 10.5194/nhess-21-393-2021 — Backs `HAZ-CLIMADA-01/08` (`v_thresh = 25.7 m/s`, default `v_half = 74.7 m/s`; `ImpfTropCyclone.from_emanuel_usa`).
- **`[Eberenz2020LitPop]`** — Eberenz, S., Stocker, D., Röösli, T., & Bresch, D. N. (2020). *Asset exposure data for global physical risk assessment (LitPop).* ESSD, 12(2), 817–833. DOI: 10.5194/essd-12-817-2020 — Backs `HAZ-CLIMADA-03`.

## 3. Drought indices (HAZ-DROUGHT)

- **`[VicenteSerrano2010]`** — Vicente-Serrano, S. M., Beguería, S., & López-Moreno, J. I. (2010). *A Multiscalar Drought Index Sensitive to Global Warming: SPEI.* Journal of Climate, 23(7), 1696–1718. DOI: 10.1175/2009JCLI2909.1 — Backs `HAZ-DROUGHT-01`.
- **`[McKee1993]`** — McKee, T. B., Doesken, N. J., & Kleist, J. (1993). *The relationship of drought frequency and duration to time scales.* Proc. 8th Conf. on Applied Climatology, AMS, 179–184. (Conference paper; no DOI.) — Backs `HAZ-DROUGHT-01` (SPI).
- **`[WMO2012SPI]`** — World Meteorological Organization (2012). *Standardized Precipitation Index User Guide* (Svoboda, Hayes, Wood). WMO-No. 1090. — Backs `HAZ-DROUGHT-01`. *(Confirm WMO library URL on access — `OQ-HAZ-09`.)*

## 4. Disaster loss assessment (HAZ-CENAPRED)

- **`[CEPAL2014]`** — ECLAC/CEPAL (2014). *Handbook for Disaster Assessment* (3rd ed.; Damage and Loss Assessment, DaLA). Santiago, Chile. https://www.cepal.org/en/publications/36823-handbook-disaster-assessment — Backs `HAZ-CENAPRED-06`.

## 5. Stochastic loss modelling & catastrophe framing (HAZ-STOCH / MKT-MC)

- **`[McNeil1997]`** — McNeil, A. J. (1997). *Estimating the Tails of Loss Severity Distributions Using Extreme Value Theory.* ASTIN Bulletin, 27(1), 117–137. DOI: 10.2143/AST.27.1.563210 — Backs `HAZ-STOCH-01`.
- **`[ContTankov2004]`** — Cont, R., & Tankov, P. (2004). *Financial Modelling with Jump Processes.* Chapman & Hall/CRC. DOI: 10.1201/9780203485217 — Backs `HAZ-STOCH-02`, `INT-10`, `INT-13`, `DC-CCR-SIM-2` (compound-Poisson construction Ch. 3; simulation of jump processes Ch. 6).
- **`[Merton1976]`** — Merton, R. C. (1976). *Option Pricing when Underlying Stock Returns Are Discontinuous.* Journal of Financial Economics, 3(1–2), 125–144. DOI: 10.1016/0304-405X(76)90022-2 — Backs `INT-13`, `DC-CCR-SIM-2` (the price-channel jump-diffusion: multiplicative log-return marks, the independent-jump assumption, Gaussian/lognormal mark families).
- **`[Glasserman2003]`** — Glasserman, P. (2004). *Monte Carlo Methods in Financial Engineering.* Springer (Stochastic Modelling and Applied Probability, 53). DOI: 10.1007/978-0-387-21617-1 — Backs `MKT-MC-01`, `MKT-CALIB-07` (GBM log-return MLE; the MC-error yardstick in the `MKT-CALIB-06` diagnostics).
- **`[NGFS2024]`** — Network for Greening the Financial System (2024). *NGFS Climate Scenarios* (v5.0, incl. updated physical-risk damage function). https://www.ngfs.net/ngfs-scenarios-portal/ — Backs `HAZ-STOCH-03`, `MKT-NGFS-01/02`. *Caveat: the Phase V physical-risk damage function relied on a study later retracted; treat physical-loss estimates with care and consult NGFS notes.*
- **`[NGFS2025ST]`** — NGFS (2025). *NGFS Short-Term Climate Scenarios* (May 2025; ~50 sectors, quarterly, direct PD; models GEM-E3 / CLIMACRED / EIRIN; IMF WEO Oct-2023 baseline). https://www.ngfs.net/ngfs-scenarios-portal/ — Backs `MKT-NGFS-03`. *(Confirm exact title/URL on access.)*
- **`[NAIC2025]`** — National Association of Insurance Commissioners (2025). *Catastrophe Modeling Primer.* https://content.naic.org/ — Backs `HAZ-STOCH-03`.

## 6. Interest-rate modelling, curve & change-of-measure (MKT-IR / CURVE / MEAS / CALIB)

- **`[Hull1990]`** — Hull, J., & White, A. (1990). *Pricing Interest-Rate-Derivative Securities.* Review of Financial Studies, 3(4), 573–592. DOI: 10.1093/rfs/3.4.573 — Backs `MKT-IR-01/02`, `MKT-MEAS-02`, `MKT-CURVE-05` (the θ(t) formula realized from the NS forwards). *(The Hull–White model.)*
- **`[Vasicek1977]`** — Vasicek, O. (1977). *An equilibrium characterization of the term structure.* Journal of Financial Economics, 5(2), 177–188. DOI: 10.1016/0304-405X(77)90016-2 — Backs the Vasicek estimation device (`MKT-IR-01`).
- **`[AndersenPiterbarg2010]`** — Andersen, L., & Piterbarg, V. (2010). *Interest Rate Modeling* (Vols. I–III). Atlantic Financial Press. — Backs `MKT-IR-01` and the HW1F simulation scheme PIMPA uses (`CCR` `processes`; Proposition 10.1.7 is the exact-discretization recursion `processes.diffusions.hw1f` implements and the jump overlay of `DC-CCR-SIM-2` reuses); also backs `CCR-SIM-01` (exact transition ⇒ grid densification is law-preserving). *(Confirm volume/page on citation.)*
- **`[BrigoMercurio2006]`** — Brigo, D., & Mercurio, F. (2006). *Interest Rate Models — Theory and Practice* (2nd ed.). Springer Finance. DOI: 10.1007/978-3-540-34604-3 — Backs `MKT-IR-01`, `MKT-CALIB-05` (the two-stage HW1F design: time-series `a`/`σ`, cross-sectional θ(t)).
- **`[NelsonSiegel1987]`** — Nelson, C. R., & Siegel, A. F. (1987). *Parsimonious Modeling of Yield Curves.* Journal of Business, 60(4), 473–489. DOI: 10.1086/296409 — Backs `MKT-CURVE-03/05`.
- **`[Svensson1994]`** — Svensson, L. E. O. (1994). *Estimating and Interpreting Forward Interest Rates: Sweden 1992–1994.* NBER Working Paper 4871. DOI: 10.3386/w4871 — Backs `MKT-CURVE-03` (the flagged upgrade path of `MKT-CURVE-05`).
- **`[JamesWebber2000]`** — James, J., & Webber, N. (2000). *Interest Rate Modelling.* Wiley. — Backs `MKT-CALIB-02/05/06` (discrete-Vasicek AR(1) estimation and its exact-MLE counterpart). *(Confirm exact edition/pages.)*
- **`[Yasuoka2018]`** — Yasuoka, T. (2018). *Interest Rate Modeling for Risk Management: Market Price of Interest Rate Risk* (2nd ed.). Bentham Science. — Backs `MKT-MEAS-01` (λ estimation). *(Confirm details — `OQ-MKT-05`.)*
- **`[BaselCommittee2019]`** — Basel Committee on Banking Supervision (2019). *Minimum capital requirements for market risk* (revised, "FRTB"). Bank for International Settlements. https://www.bis.org/bcbs/publ/d457.htm — Backs `MKT-STRESS-01/03`.
- **`[CNBV]`** — Comisión Nacional Bancaria y de Valores. *Disposiciones de carácter general … en materia de Administración Integral de Riesgos* (incl. Art. 282 stress tests). — Backs `MKT-STRESS-03`. *(Cite the specific Disposiciones edition/article in the manuscript.)*

## 7. Weather derivatives (MKT-WD)

- **`[Alaton2002]`** — Alaton, P., Djehiche, B., & Stillberger, D. (2002). *On modelling and pricing weather derivatives.* Applied Mathematical Finance, 9(1), 1–20. DOI: 10.1080/13504860210132897 — Backs `MKT-WD-01` (OU with seasonal mean; baseline model).
- **`[BenthSaltyteBenth2007]`** — Benth, F. E., & Šaltytė-Benth, J. (2007). *Modelling and Pricing in Financial Markets for Weather Derivatives.* World Scientific. — Backs `MKT-WD-01` (extensions). *(See `notes/theory/referencias_weather_derivatives.md` for the fuller WD reading list incl. Brody et al. 2002, Jewson & Brix 2005, and recent ML approaches.)*

## 8. Rough paths, signatures & CCR (CCR arm)

- **`[Compagnoni2023]`** — Compagnoni, E. M., et al. (2023). *On the Effectiveness of Randomized Signatures as a Reservoir for Learning Rough Dynamics.* (Attached PDF in the CCR project knowledge.) — Backs `CCR-SIG-01/02/03`. *(Finalize venue/year from the attached PDF.)*
- **`[Lyons1998]`** — Lyons, T. J. (1998). *Differential equations driven by rough signals.* Revista Matemática Iberoamericana, 14(2), 215–310. — Foundational rough-path theory. *(Confirm pages.)*
- **`[ChevyrevKormilitzin2016]`** — Chevyrev, I., & Kormilitzin, A. (2016). *A Primer on the Signature Method in Machine Learning.* arXiv:1603.03788. — Signature-method primer.
- **`[Gregory_xVA]`** — Gregory, J. *The xVA Challenge: Counterparty Risk, Funding, Collateral, Capital and Initial Margin.* Wiley. — CCR/xVA reference for EPE/CVA extensions (`CCR-RISK-01`). *(Confirm edition/year.)*

## 9. Climate–finance literature (MKT LaTeX writeup — full list in `literature/refs.bib`, 47 entries)

Load-bearing keys (give author/year here; **exact DOIs in `literature/refs.bib`**):
`[Battiston2017]` (climate stress-test, Nature Climate Change) · `[Bolton2020]` ("green swan", BIS) ·
`[Carney2015]` ("Tragedy of the Horizon") · `[Campiglio2023]` · `[Monasterolo2020]` ·
`[Giglio2021]` (climate finance review) · `[Kotz2024]` (macroeconomic damage) ·
`[Nordhaus2017]` (DICE) · `[TCFD2017]` · `[NGFS2024]` (also §5) · `[Semieniuk2022]` (stranded assets) ·
`[Gorgen2024]` (carbon risk factor) · `[Klusak2023]` (climate sovereign ratings; full entry §10) ·
`[Dietz2018]` (climate value-at-risk) · `[Acharya2023]` · `[Stock2025]` · plus standard asset-pricing
anchors `[Sharpe1964]`, `[Fama1995]`, `[Carhart1997]`, `[Engle2002]`.

> Treat `literature/refs.bib` as authoritative for these — it is the BibTeX the thesis writeup
> compiles against. Do not hand-transcribe their DOIs into the manuscript; cite from the `.bib`.

## 10. Disaster → sovereign-rate channel (INT-18 / OQ-INT-09)

Verified 2026-07-19 (web pass for the rate-leg fallback; per-paper caveats inline).

- **`[Anyfantaki2025]`** — Anyfantaki, S., Blix Grimaldi, M., Madeira, C., Malovaná, S., & Papadopoulos, G. (2025). *Decoding climate-related risks in sovereign bond pricing: a global perspective.* ECB Working Paper No. 3135 (= BIS WP No. 1275). https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp3135~024090a8b9.en.pdf — **Backs `INT-18`** (the fallback β: Figure 8, EMDE log-10Y local-currency yield response to EM-DAT climate-disaster damage in % of GDP; ~0.015 log-points per 1 pp-of-GDP at years 2–5). *Caveats: coefficients chart-read from published IRFs (68 % bands, ≈0 impact in year 0–1); regressor-unit reading documented in `configs/loss_to_rate_scale.yaml`.*
- **`[Klusak2023]`** — Klusak, P., Agarwala, M., Burke, M., Kraemer, M., & Mohaddes, K. (2023). *Rising Temperatures, Falling Ratings: The Effect of Climate Change on Sovereign Creditworthiness.* Management Science, 69(12), 7468–7491. DOI: 10.1287/mnsc.2023.4869 — Backs `INT-18` (scenario context: Mexico −5.55 notches under RCP 8.5 by 2100, Table D.2; ratings→spread 8–12 bp/notch, §6) — a century-scenario level shift, **not** a per-event elasticity.
- **`[Klomp2020]`** — Klomp, J. (2020). *Do natural disasters affect monetary policy? A quasi-experiment of earthquakes.* Journal of Macroeconomics, 64, 103164. DOI: 10.1016/j.jmacro.2019.103164 — Backs `INT-18` (sign caveat: flexible central banks *ease* post-disaster, so the short-end response can oppose the credit-premium leg). *Coefficient magnitudes paywalled/unverified; sample is earthquakes (geophysical).*
- **`[Klomp2015]`** — Klomp, J. (2015). *Sovereign Risk and Natural Disasters in Emerging Markets.* Emerging Markets Finance and Trade, 51(6), 1326–1341. DOI: 10.1080/1540496X.2015.1011530 — Context for `INT-18` (EM default premia rise after meteorological disasters). *Closed access: direction verified, magnitude NOT — cite no number from it.*
- **`[CevikJalles2022]`** — Cevik, S., & Jalles, J. T. (2022). *This changes everything: Climate shocks and sovereign bonds.* Energy Economics, 107, 105856. DOI: 10.1016/j.eneco.2022.105856 (working paper: IMF WP/20/79). — Context for `INT-18` (spreads price climate *vulnerability* — ND-GAIN index, Mexico in sample; **not** a damage elasticity).
- **`[Mallucci2022]`** — Mallucci, E. (2022). *Natural disasters, climate change, and sovereign risk.* Journal of International Economics, 139, 103672. DOI: 10.1016/j.jinteco.2022.103672 — Context for `INT-18` (structural hurricane-risk premium, 74–126 bp, seven Caribbean small islands — external-validity contrast for Mexico).
- **`[INEGI_PIB2025]`** — INEGI. Nominal GDP anchors for the `INT-18` bridge: annual 2024 = 33,506,847 M MXN (Comunicado 156/25, https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/pibent/PIBE2024_CP.pdf); Q4-2025 = 36,309,928 M MXN (Boletín 94/26, https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2026/pibt/pib_Pcorr2026_02.pdf). — Backs the β→per-bn-MDP conversion (1 % of GDP = 363.1 bn MDP-2025); the two vintages differ ~8 % (annual-accounts revision), noted in the config.

---

## 99. To confirm (do not cite in the manuscript until verified)

- **`[Klugman]`** — Klugman, S. A., Panjer, H. H., & Willmot, G. E. *Loss Models: From Data to Decisions.* Wiley. — Confirm edition/year + URL. Backs `HAZ-STOCH-01`. (→ `OQ-HAZ-07`)
- **`[Baryshnikov2001]`** — Baryshnikov, Yu., Mayo, A., & Taylor, D. R. (2001). *Pricing of CAT bonds.* — Confirm full citation + URL. Backs `HAZ-STOCH-02`. (→ `OQ-HAZ-07`)
- **`[Burnecki2005]`** — Burnecki, K., et al. (2005). Compound-Poisson / catastrophe-bond modelling (likely a chapter in *Statistical Tools for Finance and Insurance*). — Confirm exact reference + URL. Backs `HAZ-STOCH-02`. (→ `OQ-HAZ-07`)
- **`[Garwood1936]`** — Garwood, F. (1936). *Fiducial limits for the Poisson distribution.* Biometrika 28(3/4). — Confirm pages + DOI. Backs `INT-16` (the exact χ² confidence interval on the arrival intensity in `calibration.impact`).
- **`[INEGI_INPC]`** — INEGI. *Índice Nacional de Precios al Consumidor (INPC).* — Deflator wired 2026-07-18 (`HAZ-STOCH-05`) via the World Bank `FP.CPI.TOTL` mirror in `configs/inpc_anual.yaml` (retrieved 2026-07-18 from https://api.worldbank.org/v2/country/MEX/indicator/FP.CPI.TOTL; ratios-only equivalence; cross-checked vs published INEGI annual inflation 2017 = 6.04 %, 2020 = 3.40 %, 2022 = 7.90 %). Still to confirm: the INEGI BIE series verbatim (API token) and the base-vintage citation for the manuscript. Backs `HAZ-STOCH-05` and the deflation step in `calibration.impact`.
- **`[PielkeLandsea1998]`** — Pielke Jr., R. A., & Landsea, C. W. (1998). *Normalized hurricane damages in the United States: 1925–95.* Weather and Forecasting 13(3), 621–631. — Confirm DOI/pages. Backs the exposure-vs-climate attribution caveat on the deflation-surviving trends (`HAZ-STOCH-05`, `OQ-INT-07` c residual): deflation removes prices; normalization also removes wealth/population growth.
- **`[AMIS2014Odile]`** — AMIS / CNSF. *Insured-loss figure for hurricane Odile (September 2014, Baja California Sur).* — Locate the official publication and the amount (order USD ~1.2 bn). Backs `HAZ-CLEAN-CNSF-14` (the MXN-units reading of SESA amounts: the foreign-currency-units reading fails this cross-check several-fold).
- **`[Hazus]`** — FEMA Hazus technical/flood manual. — Confirm exact edition. Backs the CLIMADA flood route. (→ `OQ-HAZ-08`)
- **`[Wagenaar2018]`** — Wagenaar, D., et al. (2018), flood depth–damage. — Confirm journal/DOI. Backs the CLIMADA flood route. (→ `OQ-HAZ-08`)
- **`[AndersenPiterbarg2010]` / `[JamesWebber2000]` / `[Yasuoka2018]` / `[Gregory_xVA]` / `[Compagnoni2023]` / `[Lyons1998]`** — standard texts/papers cited above with edition/venue/pages still to pin down precisely. (→ `OQ-MKT-05`, `OQ-CCR-05`)
- **`[IPCC_AR6]`** — IPCC (2021). *AR6 WG1: The Physical Science Basis* (likely Ch. 11, *Weather and Climate Extreme Events in a Changing Climate*). — Confirm report/chapter + DOI. Already cited by `MKT-PHYS-02` (SSP scenario choice) without a §-entry (gap found 2026-07-05); also motivates the frequency/severity-trend note in `OQ-INT-07` (time-varying `λ(t)` + time-aware marks).
- **`[Ousterhout2018]`** — Ousterhout, J. (2018). *A Philosophy of Software Design.* Yaknyam Press. — Confirm edition (a 2nd ed., 2021, exists) + ISBN. Backs `GEN-25` (complexity as the design enemy; deep modules over shallow abstractions).
- **`[Beck2004]`** — Beck, K., with Andres, C. (2004). *Extreme Programming Explained: Embrace Change* (2nd ed.). Addison-Wesley. — Confirm edition/ISBN. Backs `GEN-25` (YAGNI / simple design).
- **`[BanxicoFIX2024]`** — Banco de México. FIX MXN/USD representative exchange rate, annual averages (Informe Anual compilation 2024, cuadro "Tipos de cambio representativos"; also derivable from SIE series SF43718). — Confirm the exact publication/URL (or re-anchor to the SIE series). Backs `HAZ-CLEAN-CNSF-13` (the ÷FIX factors 2022 = 20.1274, 2023 = 17.7587, 2024 = 18.3049).
- **`[Leys2013]`** — Leys, C., Ley, C., Klein, O., Bernard, P., & Licata, L. (2013). *Detecting outliers: Do not use standard deviation around the mean, use absolute deviation around the median.* Journal of Experimental Social Psychology 49(4), 764–766. — Confirm DOI. Backs `GEN-27` (median/MAD robust $z$; the 0.6745 consistency constant).
- **`[Iglewicz1993]`** — Iglewicz, B., & Hoaglin, D. C. (1993). *How to Detect and Handle Outliers.* ASQC Quality Press (Basic References in Quality Control, vol. 16). — Confirm ISBN. Backs `GEN-27` (modified z-score labeling rules; detect-then-triage, never silent deletion).
- **`[MacKinlay1997]`** — MacKinlay, A. C. (1997). *Event Studies in Economics and Finance.* Journal of Economic Literature, 35(1), 13–39. — Confirm pages/stable URL on access. Backs `INT-18` (the market-model event-study design: estimation window, abnormal returns, CAR).
- **`[Hausman1978]`** — Hausman, J. A. (1978). *Specification Tests in Econometrics.* Econometrica, 46(6), 1251–1271. — Confirm DOI (likely 10.2307/1913827). Backs `MKT-CALIB-06` (the specification-test reading of the AR(1)-vs-MLE divergence: two estimators consistent under the null model, divergent under misspecification).
- **Climate-finance `.bib` (47 entries)** — verify each DOI in `literature/refs.bib` before the literature review hardens.


---

## Related
Reads with: [[DECISIONS]] (what each key backs) · [[OPEN_QUESTIONS]] (the §99 to-confirm items) · `literature/refs.bib` (the 47-entry BibTeX). Home: [[_INDEX]]
#arm/int #type/reference
