# Thesis-registration proposal — structure guide (2026-10-08)

This note is scaffolding, not text: it fixes the shape of the registration proposal, lists what each section must contain, states the methods' formulas exactly as the code implements them, names the core references, and points at the vault notes to read before writing each part. The prose of the proposal is yours. Length target and skeleton come from the earlier proposal in this folder (`notes/manuscript/proposal.pdf`, ETH Zürich / UZH MScQF, December 2024): a title page, three short numbered sections, two numbered equations, two references, about three pages of text. Write in British English; cite only keys that appear in the verified sections of [[REFERENCES]] and compile against `literature/refs.bib` (`CCR-LIT-04`).

## 0. Target shape

| Section (as in the 2024 proposal) | Must contain | Length | Where the content lives |
|---|---|---|---|
| Title page | title; your name; time frame (check the dates — the 2024 page reads "December 2024 – May 2024"); supervisors | 1 page | — |
| 1 Motivation | why climate risk belongs inside counterparty-credit measurement, why Mexico, what is missing in current practice | ½ page | §1.1 below |
| 2 Goal of the thesis | the aim, the two research questions, the three hypotheses, the integrating mechanism, what is in and out of scope | ½–¾ page | §1.2 below |
| 3 Approach | the machine in one paragraph, then the six method blocks with their formulas, then data in two lines and the expected deliverables | 1½ pages, 6–8 numbered equations | §2 below |
| References | 12–20 entries, all from the verified bibliography | ½ page | §3 below |

Keep every equation that appears in the text numbered and referenced from the prose; the 2024 proposal shows the convention (`(1)`, `(2)`) and also shows the failure mode to avoid (unresolved `??` references).

## 1. Introduction — prompts

### 1.1 Motivation

- Open with the supervisory framing: climate risk is routed through *existing* risk categories by scenario analysis, not through a new capital charge — `[BCBS2022Principles]`, `[BCBS2021Measurement]`; for Mexico the regime is disclosure plus risk-management guidance (`[CNBV2025NIIF]`, `[CNBV]` — verified in [[REFERENCES]] §11 and §6 but without BibTeX entries: cite the DOF publication and the Disposiciones article verbatim).
- State the gap the thesis fills: scenario exercises translate *transition* narratives into prices, while the *physical* channel is usually a damage-function assumption; this thesis estimates it from realised Mexican losses and reads it out on a counterparty-credit book. Canon: `INT-09`, `INT-10`, `INT-29` (the retraction argument for an own-estimated physical channel, `[NGFS2025Notes]`).
- Why Mexico: the unit of analysis for all three arms (`INT-03`); the public loss record (CENAPRED 2000–2024, CNSF), the sovereign curve (Banxico SIE) and a listed-equity universe exposed to cyclones, rain, drought; your own prior work on Mexican transition scenarios `[Roncoroni2021]`.
- Why counterparty credit risk as the readout: EE / EPE is the pricing-and-capital path (IMM EAD $=\alpha\cdot\mathrm{EEPE}$, CVA integrates EE), so a climate delta on EE is a scenario delta on the metric supervisors already use — `INT-23`, `[BaselCRE]`, `[Gregory_xVA]`.
- Read first: [[README]] §"Aim, research questions, and the integrating mechanism" (lines 37–95), [[2026-09-14_hypotheses_and_scope_explained]], [[2026-07-25_headline_metric_explained]].

### 1.2 Goal of the thesis

- The aim verbatim from `INT-09`: find, test and quantify a relationship between financial asset prices / risk factors and climate events, and measure by Monte Carlo how financial risk changes once climate is incorporated.
- RQ1 (detection / estimation) and RQ2 (modelling / propagation) as stated in [[README]]; note that RQ1 is answered by the hazard estimation plus two pre-registered market nulls, and that rough-path / signature methods are future work (`CCR-SIG-05`) — the 2024 proposal's topic becomes one sentence of outlook.
- The three hypotheses of `INT-37` (wording in [[GLOSSARY]] *Hypotheses*): H1 market repricing (rejected), H2 loss transmission (supported), H3 separability of physical and transition channels (supported). A registration proposal normally states hypotheses and the planned tests, not verdicts; decide whether to present the verdicts as preliminary results or as expected outcomes.
- The integrating mechanism in one sentence: a climate-driven compound-Poisson jump superimposed on the risk-factor diffusions, with the jump-on minus jump-off difference read as the climate component (`INT-10`, `INT-13`).
- Scope: in — the jump channel, the NGFS three-flavour transition table, CVA, Effective EPE; body-text limitations — structural credit overlay, long-term NGFS join, Cox $\lambda(t)$, CLIMADA; future work — signatures, weather derivatives, parametric pricing, stochastic spreads (`INT-38`).
- Caveat when quoting numbers: [[README]], [[GLOSSARY]] and `INT-37` still carry the pre-2026-10-03 band (−8.93 / −5.44 / −4.86 %); the current state lives in `INT-23` (−8.97 / −5.54 / −4.99 %) and in §5 below.
- Read: [[2026-09-14_scope_manuscript_gate]], [[PROJECT_PLAN]] §4 (the chapter map the proposal condenses), `DECISIONS` entries `INT-09/10/11/12/37/38`.

## 2. Approach — the methods with their formulas

One paragraph describes the machine: HAZ estimates arrivals and severities from the loss record; MKT calibrates the risk-factor dynamics to Banxico and BMV data; the CCR engine simulates the book under correlated diffusions with and without the climate jump and reads out the exposure metrics (`INT-11`). Then one block per method. Notation: $a$ mean reversion, $\sigma$ volatility, $f(0,t)$ the instantaneous forward curve at the valuation date, $N_t$ the climate-event counter, $L$ a per-event loss in millions of real 2025 pesos (MDP-2025), $V_t$ the netted portfolio value of a netting set.

### 2.1 Risk-factor dynamics and calibration (`MKT-IR-01`, `MKT-CURVE-05`, `MKT-CALIB-05/08`, `MKT-CALIB-07`)

- Short rate, Hull–White one-factor under $\mathbb{Q}$: $dr_t = [\theta(t) - a\,r_t]\,dt + \sigma\,dW_t$, with $\theta(t) = \partial_t f(0,t) + a\,f(0,t) + \frac{\sigma^2}{2a}\big(1 - e^{-2at}\big)$ so that today's curve is reproduced `[Hull1990]`.
- Exact simulation step (Andersen–Piterbarg Proposition 10.1.7, as coded in `processes/diffusions/hw1f.py`): $r_t = f(0,t) + \frac{\sigma^2}{2a^2}\big(1-e^{-at}\big)^2 + x_t$, $x_{t+\Delta} = e^{-a\Delta}x_t + \sigma\sqrt{\tfrac{1-e^{-2a\Delta}}{2a}}\;Z$, $Z\sim N(0,1)$; zero-coupon bonds through $B(t,T) = \frac{1-e^{-a(T-t)}}{a}$ `[AndersenPiterbarg2010]` `[BrigoMercurio2006]`.
- The curve: Nelson–Siegel on the stripped SIE pillars, $z(t) = \beta_0 + \beta_1 h(t) + \beta_2\big(h(t) - e^{-t/\tau}\big)$, $h(t) = \frac{1-e^{-t/\tau}}{t/\tau}$, hence the analytic forward $f(0,t) = \beta_0 + (\beta_1 + \beta_2\,t/\tau)\,e^{-t/\tau}$ that $\theta(t)$ differentiates `[NelsonSiegel1987]`; short pillars convert simple Act/360 to continuous Act/365 (`MKT-SIE-04`).
- Estimation of $(a,\sigma)$: discrete Vasicek on the weekly F-TIIE overnight series, $r_{t+1} = c + \phi\,r_t + \varepsilon_t$, $a = -\ln\phi/\Delta t$, $\sigma^2 = \mathrm{Var}(\varepsilon)\,\frac{2a}{1-\phi^2}$, cross-checked by the exact transition-density MLE; crisis windows excluded (`MKT-CALIB-02/03/08`, `[JamesWebber2000]`, `[CKLS1992]`). Current values $a = 0.0758$, $\sigma = 0.0081$.
- Equity and FX: geometric Brownian motion per name, $dS_t/S_t = \mu\,dt + \sigma\,dW_t$; MLE on log returns $x_i = \ln(S_i/S_{i-1})$, $\hat\sigma^2 = \mathrm{Var}(x)/\Delta t$, $\hat\mu = \bar x/\Delta t + \hat\sigma^2/2$ `[Glasserman2003]`.
- Correlated draws: standard normals $Z$ of shape (paths, steps, factors) coloured by the Cholesky factor, $\varepsilon = Z L^{\top}$ with $LL^{\top} = C$ the sample correlation (`CCR-SIM-02`); every run records seed, commit, package and BLAS versions in a manifest (`GEN-06`, `GEN-37`).
- Read: [[Hull_White_Comprehensive]] §1–2 and §5, [[mexican_yield_curve_methodology]] §4, [[2026-07-20_mkt_calibration]], [[2026-07-20_hw1f_estimator_disagreement_explained]], [[2026-08-02_weekly_sampling_adoption_explained]], [[2026-10-03_canonical_draw_and_extenso_2024_explained]] (the draw).

### 2.2 The climate jump channel (`INT-10`, `INT-13`, `INT-14`, `DC-CCR-SIM-2`)

- Arrivals: a Poisson process $N_t$ with intensity $\lambda$ events per year (homogeneous in the headline; a deterministic trajectory $\lambda(t)$ in the robustness riders), one event stream shared by every target.
- Marks: each event carries a lognormal loss $L_i \sim \mathrm{LN}(\ln m,\,\sigma_L^2)$ mapped to a per-target jump, $Y_i = -L_i/K_{\text{eff}}$ in log-price for equities and $J_i = +L_i/S_{\text{rate,eff}}$ in the short rate.
- Price target (Merton jump-diffusion): $S_t = S_t^{\text{diff}}\exp\!\big(\sum_{i\le N_t} Y_i\big)$, equivalently $dS_t/S_t = \mu\,dt + \sigma\,dW_t + (e^{Y}-1)\,dN_t$ `[Merton1976]` `[ContTankov2004]`.
- Rate target (jump-extended Hull–White): $r_t = r_t^{\text{diff}} + \sum_{i\le N_t} J_i\,e^{-a(t-\tau_i)}$ — a mark enters the short rate at its event time $\tau_i$ and relaxes through the mean reversion, propagating to the curve through $B(t,T)$.
- Independence: jumps are independent of the diffusions and drawn from a derived sub-stream of the master seed, so the jump-off run is bit-for-bit the baseline and jump-on minus jump-off is the pure climate component (`INT-09`).
- Per-name redistribution (`INT-24/25/26`): a name's mark is scaled by $\gamma_i$ with $\sum_i w_i\gamma_i = 1$ on book notionals; with peril-typed events each event draws a label $p$ with probability $\pi_p$ and the scale becomes $c_{ip} = \gamma_i^p/\pi_p$, so that $\sum_p \pi_p c_{ip} = \gamma_i$; per-label severities are mean-matched, $m_p = m\,\exp\!\big((\sigma_L^2 - \sigma_p^2)/2\big)$, so $E[L_p] = E[L]$.
- Read: [[2026-07-02_climate_jump_channel]], [[2026-07-16_hazard_jump_calibration_explained]], [[2026-07-26_sector_marks_explained]], [[2026-07-30_peril_typed_events_explained]], [[2026-08-01_per_peril_severity_phase_c_explained]]; code `processes/jumps/climate_jump_process.py`, `processes/diffusions/{hw1f,geometric_brownian_motion}.py`.

### 2.3 Hazard estimation and the loss-to-mark scale (`INT-16`, `INT-17`, `INT-20`, `INT-22`, `HAZ-STOCH-04..07`)

- Data base: CENAPRED discrete climate events 2000–2024, losses deflated to 2025 pesos at load time, $L^{\text{real}} = L^{\text{nominal}}\,I_{2025}/I_{\text{year}}$ (INEGI INPC), trigger set $L \ge 200$ MDP-2025 (`HAZ-STOCH-04/05`).
- Intensity: $\hat\lambda = n/T$ with the exact Garwood interval $\big[\chi^2_{\alpha/2}(2n)/2T,\;\chi^2_{1-\alpha/2}(2n+2)/2T\big]$ `[Garwood1936]`; trend $\lambda(t) = \exp\!\big(a_0 + b\,(t - t_0)\big)$ by Poisson MLE on annual counts with the likelihood-ratio test of $b = 0$.
- Severity: lognormal MLE on the per-event losses, $\hat\mu = \overline{\ln L}$, $\hat\sigma_L = \mathrm{sd}(\ln L)$, median $e^{\hat\mu}$, mean $e^{\hat\mu + \hat\sigma_L^2/2}$ `[Klugman2019]`.
- Headline parameters: $\lambda = 19.2857$ per year (2002–2015 registry), with the regime band $\lambda = 10.0870$ (cyclone bridge 2002–2024) and $\lambda = 7.2222$ (report regime 2016–2024, its own severity); registry severity median 905.53 MDP-2025, $\sigma_L = 1.2106$ (`INT-20`, `HAZ-STOCH-07`).
- Loss-to-mark scale: $\text{mark} = -\beta L/K = -L/K_{\text{eff}}$ with $\beta$ the pass-through (insured payouts over CENAPRED damage on the overlap window, 0.174), $K$ the book size (annual real premium of the exposed CNSF lines, 22,964 MDP-2025), $K_{\text{eff}} = K/\beta = 131{,}932$; dividing a lognormal by a constant rescales the median and keeps $\sigma_L$ (`INT-17`).
- Rate scale: a short-rate jump $J$ decaying at $a$ moves the $T$-year yield by $J\,\bar B(T)$, $\bar B(T) = \frac{1-e^{-aT}}{aT}$, so a yield response $\beta_T$ per bn MDP inverts to $J = (\beta_T/10^3)/\bar B(T)$ and $S_{\text{rate,eff}} = 1/J$; with the literature slope `[Anyfantaki2025]` and the Mexican $a$, $S_{\text{rate,eff}} = 175{,}293{,}784$ MDP-2025 (`INT-18`, `INT-22`).
- Sector layer: $\gamma_i \propto \sum_s G[i,s]\,\sum_p S[\text{sector}_i,p]\,H[s,p]$ — asset footprint by state, sector × peril susceptibility tier, CENAPRED per-capita damage by state and peril `[Bressan2024]` `[Kruttli2025]` `[CEPAL2014]`.
- Read: [[2026-07-16_hazard_jump_calibration]], [[2026-07-18_k_scale_deflation_explained]], [[2026-07-25_lambda_band_readout_explained]], [[2026-07-21_cenapred_regime_break_and_otis_explained]], [[2026-10-03_canonical_draw_and_extenso_2024_explained]] (the 2024 refresh); theory [[referencias_riesgo_catastrofico]]; code `calibration/impact/{hazard_jump,sector_scales,rate_response}.py`.

### 2.4 The market-repricing tests — H1 (`INT-18`, `INT-19`, `INT-27`)

- Rates: market model on daily yield changes against the matched US Treasury series, $\Delta y_t = \hat a + \hat b\,\Delta y^{US}_t$ estimated on $[-120,-10]$ business days before each episode; abnormal change $AR_t = \Delta y_t - \hat a - \hat b\,\Delta y^{US}_t$; $CAR_i[0,h] = \sum_{t=0}^{h} AR_t$; the cross-episode regression $CAR_i = \alpha + \beta\,L_i$ with HC1 errors and a pairs bootstrap `[MacKinlay1997]`.
- Equities: the same design on daily log returns against the IPC per name; the test statistic is Kendall's $\tau$ between the per-name mean CAR and the name's cyclone scale $c_{i,\text{ciclón}}$, with an episode-level bootstrap.
- Pre-registration: the adoption gate is written into the config before any estimation run (longest pillar with $n \ge 30$ episodes, window $[0,+5]$, one-sided $p < 0.05$; for equities $P(\tau^* \ge 0) < 0.05$); a null is a reportable result.
- Outcome to state as preliminary or expected: both gates returned null (rates $p = 0.73$ over 100 episodes including Otis; equities $\tau = +0.198$, $p_{\text{boot}} = 0.94$), so the rate channel carries a literature scenario rather than a Mexican estimate.
- Read: [[2026-07-19_rate_leg_event_study_explained]], [[2026-07-21_cenapred_regime_break_and_otis_explained]], [[2026-08-01_per_peril_severity_phase_c_explained]] (the equity edition); code `calibration/impact/{rate_response,sector_response}.py`.

### 2.5 Counterparty-credit metrics (`INT-23`, `CCR-RISK-03/06/08`)

- Exposure of a netting set at a reporting date: $E_t = \max(V_t, 0)$; expected exposure $EE(t) = E[E_t] = \frac1n\sum_{j=1}^{n}\max\big(V_t^{(j)},0\big)$ over $n = 10{,}000$ paths on the Basel reporting grid (0D … 50Y).
- Expected positive exposure: $EPE = \frac{1}{T}\int_0^T EE(t)\,dt$, the trapezoid over the grid in year fractions, summed across netting sets for the book — the headline metric; the climate delta is $EPE^{\text{on}} - EPE^{\text{off}}$ on shared diffusion paths.
- Effective EPE (IMM, Basel CRE53): $EEPE = \frac{1}{1\text{y}}\int_0^{1\text{y}}\max_{s\le t} EE(s)\,ds$, additive across netting sets; $EAD = \alpha\cdot EEPE$ `[BaselCRE]`.
- Potential future exposure: $PFE_q(t) = \max\big(Q_q(V_t), 0\big)$ with $q = 0.99$, a limit statistic rather than a capital aggregate `[Artzner1999]`; its level carries Monte-Carlo sampling error that means do not (`GEN-30`, §5).
- CVA (unilateral): $CVA = \mathrm{LGD}\sum_i \tfrac12\big(EE_{i-1}DF_{i-1} + EE_iDF_i\big)\big(S_{i-1} - S_i\big)$ with survival from annual PDs, $\lambda_y = -\ln(1 - PD_y)$; a scenario $\Delta CVA$ splits exactly into exposure, credit and interaction channels by bilinearity `[Gregory_xVA]` `[PykhtinZhu2007]`.
- Read: [[2026-07-25_headline_metric_explained]], [[2026-08-12_cva_extension_explained]], [[2026-09-14_hypotheses_and_scope_explained]] (Effective EPE); theory [[monte_carlo_risk_management_framework]] §1.3 and §4.1; code `risk/ccr/evaluators/ccr_valuation_session.py`, `viz/ccr.py`, `risk/ccr/xva.py`.

### 2.6 The transition channel in one formula (`MKT-NGFS-01/02/06..09`, `INT-29..36`)

- Scenario deltas from the NGFS short-term scenarios (2025–2030, Mexico grain) land on the current curve, never replace it: $\Delta r = r_{\text{scen}} - r_{\text{base}}$; the pillar shock is the two-anchor profile $\Delta(\tau) = \Delta_{\text{short}}$ up to the policy tenor, linear to $\Delta_{\text{long}}$ at the sovereign tenor, flat beyond, and $z'(\tau) = z(\tau) + \Delta(\tau)$; equities revalue $S_0' = S_0(1 + \Delta\%)$ and credit spreads $s' = \max(s + \Delta s, 0)$ by sector `[NGFS2025ST]` `[Battiston2025CLIMACRED]` `[FedCSA2024]`.
- Three application flavours: nivel (the signed peak, headline), trayectoria (maturity-dated deltas) and fase (deterministic scheduled marks inside the simulation through the same overlay seam); physical and transition channels are reported separately and combined, and their approximate additivity is H3.
- Read: [[2026-08-02_ngfs_transition_channel_explained]], [[ngfs_application_flavors]], [[2026-09-08_fase_matrix_spread_leg_explained]]; theory [[ngfs_short_term_scenarios_summary]]; code `calibration/financial/scenario_shock.py`, `processes/scheduled_shocks.py`.

### Data in two lines (prompts)

- Market: Banxico SIE (F-TIIE, TIIE compounded tenors, Cetes 364, Bonos M dirty prices; `DC-MKT-SIE-1`), BMV equities and the FIX rate (`DC-CCR-RISK-4`), the NGFS short-term scenario set via the IIASA explorer (`DC-MKT-NGFS-2`).
- Losses: CENAPRED *Impacto Socioeconómico* 2000–2024 at event grain (`DC-HAZ-CENAPRED-1`), CNSF SESA paid claims and premiums (`DC-HAZ-CNSF-2`), INEGI INPC and Censo 2020; a representative Mexican book of 30 netting sets (26 BMV equities, TIIE swaps, equity options, cebures; `INT-21`).

### 2.7 The counterparty book — structure and position assumptions (`INT-21`, `INT-32`, `CCR-RISK-02/04/07`, `DC-CCR-RISK-4`)

The book is a hypothetical Mexican bank's derivatives and cebures portfolio, built deterministically by `pipelines/09` from `configs/mexican_book.yaml` into the PIMPA data schemas; the bank itself has no credit identity (CVA is unilateral). Valuation date 2026-07-17, settlement currency MXN, 10,000 paths, seed 233423, reporting on the Basel grid 0D … 50Y with a 14-day margin period of risk.

- **Counterparties.** 30 netting agreements: one per listed issuer (NAIDs 101–128, the 26 equities below plus BACHOCO and TERRAFINA whose shares could no longer be fetched, so those two keep only their swap and bond trades) and two debt-only issuers, PEMEX (201) and CFE (202). Every counterparty has a single `MAIN` netting set, so all of its trades net against each other on default.
- **Equity universe.** 26 BMV names weighted toward climate-exposed sectors — coastal hotels and hotel FIBRAs (HCITY, HOTEL, FIHO12, RLH, POSADAS, FINN13), the three airport groups on hurricane paths (ASUR, GAP, OMA) and Volaris, water and agro-food (AGUA, GRUMA, HERDEZ, CULTIBA), insurance (Quálitas, Peña Verde), cement and mining (CEMEX, GCC, GMEXICO, PEÑOLES), energy (VISTA) — plus IPC diversifiers (FUNO, AC, FEMSA, WALMEX, ALSEA). Each name's share is a GBM risk factor fitted on Yahoo history with the crisis windows excluded; the implied-volatility surfaces are flat at the fitted volatility (a documented proxy).
- **Trades, 103 in all.** (i) 28 TIIE interest-rate swaps, one per issuer counterparty: notional 100,000 MXN, spot-starting 2026-07-17, quarterly, tenors 5 / 7 / 10 years assigned round-robin in NAID order with near-par fixed rates 8.75 / 9.00 / 9.40 %, and the direction alternated payer / receiver in NAID order so the book is two-way in rates (14 of each; `payer` = the bank pays fixed). (ii) 52 European equity options, two per listed name on its own share and both expiring 2028-07-17: a **long at-the-money call** and a **short 95 %-strike put**, each sized to a 50,000 MXN position at the valuation spot. (iii) 23 cebures across 18 issuers, face 100,000 MXN, **all held long**: 17 fixed-coupon semi-annual bonds priced off the stripped MXN curve plus a static issuance spread, and 6 floating-rate notes paying TIIE plus a contractual sobretasa on 28-day periods; six issuers carry issuance-verified terms with provenance (OMA, FIBRA UNO, CEMEX, FEMSA/KOF, PEMEX, CFE), the rest representative terms; UDI-linked series are out of scope.
- **Position economics the results depend on.** The bank is long its counterparties' credit (it holds their bonds), long equity optionality (a long call plus a short put is a synthetic long forward on the share, so the bank's claim on a counterparty rises with its share price), and neutral in rates at book level (payer and receiver swaps alternate, so a rate-up event raises exposure on the payer-swap counterparties and lowers it on the receiver and bond-heavy ones). This is why a physical climate jump, which lowers share prices and lifts the short rate, *reduces* the bank's expected positive exposure (−9 % headline) while raising the same counterparties' default probabilities — the wrong-way reading of `INT-23` and `CCR-RISK-06`.
- **Collateral.** 16 counterparties sit under a variation-margin agreement with the fixture's thresholds and minimum transfer amounts (post 2.0 / receive 1.5, MTA 0.5 / 0.3, in the engine's USD units); 14 are uncollateralised. The reported metrics are the **uncollateralised** profiles (the climate comparison frame carries only those), so collateral enters the stored results nowhere; the collateralised profiles exist in the engine for completeness.
- **Risk factors.** 28 simulated factors — the MXN zero curve (Hull–White, weekly-calibrated), the MXN/USD rate (GBM on the Banxico FIX, required by the engine's settlement conversion) and the 26 shares (GBM) — correlated by the 28×28 sample correlation of their returns (positive definite, no repair); 26 volatility surfaces are static market data.
- **Sizing.** Notionals are small and uniform by design (100,000 MXN per swap and bond, 50,000 MXN per option leg); the engine is linear in notionals, so the portable results are the percentages, not the pesos (the institutional-scale reading of the 2026-10-03 explanation note).
- Read: [[2026-07-25_mexican_book_swap_explained]], [[2026-08-08_frn_book_v2_and_trajectory_explained]], [[2026-08-20_irs_simple_act360_explained]]; the config header of `configs/mexican_book.yaml` and the build report `data/ccr_book_mx/build_report.csv`; code `risk/ccr/trade_models/`, `risk/ccr/pricing_models/`.

## 3. Core references

Full entries are copied from [[REFERENCES]] (verified sections); the BibTeX keys in `literature/refs.bib` match the citation keys. The first tier is the minimum a reader of the proposal needs; the second tier supports individual sentences. Do not cite `[Compagnoni2023]`, `[GolubVanLoan2013]` or `[Yasuoka2018]` until they leave §99; `[CNBV2025NIIF]` and `[CNBV]` are verified but have no BibTeX entry, so they enter the bibliography by hand.

**Tier 1 — the twelve the proposal cannot do without**

- `[ContTankov2004]` — Cont, R., & Tankov, P. (2004). *Financial Modelling with Jump Processes.* Chapman & Hall/CRC. DOI: 10.1201/9780203485217. — the jump-diffusion construction (§2.2).
- `[Merton1976]` — Merton, R. C. (1976). *Option Pricing when Underlying Stock Returns Are Discontinuous.* Journal of Financial Economics, 3(1–2), 125–144. DOI: 10.1016/0304-405X(76)90022-2. — the price-channel jump-diffusion and the independence assumption (§2.2).
- `[Hull1990]` — Hull, J., & White, A. (1990). *Pricing Interest-Rate-Derivative Securities.* Review of Financial Studies, 3(4), 573–592. DOI: 10.1093/rfs/3.4.573. — the rate model and $\theta(t)$ (§2.1).
- `[BrigoMercurio2006]` — Brigo, D., & Mercurio, F. (2006). *Interest Rate Models — Theory and Practice* (2nd ed.). Springer Finance. DOI: 10.1007/978-3-540-34604-3. — the two-stage Hull–White calibration (§2.1).
- `[NelsonSiegel1987]` — Nelson, C. R., & Siegel, A. F. (1987). *Parsimonious Modeling of Yield Curves.* Journal of Business, 60(4), 473–489. DOI: 10.1086/296409. — the curve (§2.1).
- `[Glasserman2003]` — Glasserman, P. (2004). *Monte Carlo Methods in Financial Engineering.* Springer. DOI: 10.1007/978-0-387-21617-1. — simulation, GBM MLE, quantile-estimator error (§2.1, §5).
- `[Klugman2019]` — Klugman, S. A., Panjer, H. H., & Willmot, G. E. (2019). *Loss Models: From Data to Decisions* (5th ed.). Wiley. ISBN 9781119523789. — frequency–severity modelling and the lognormal severity (§2.3).
- `[MacKinlay1997]` — MacKinlay, A. C. (1997). *Event Studies in Economics and Finance.* Journal of Economic Literature, 35(1), 13–39. — the H1 tests (§2.4).
- `[PykhtinZhu2007]` — Pykhtin, M., & Zhu, S. (2007). *A Guide to Modeling Counterparty Credit Risk.* GARP Risk Review, July/August, 16–22. SSRN 1032522. — EE / PFE / CVA definitions (§2.5; the 2024 proposal cited the same work).
- `[Gregory_xVA]` — Gregory, J. (2020). *The xVA Challenge* (4th ed.). Wiley. ISBN 9781119508977. — exposure metrics and CVA (§2.5).
- `[BaselCRE]` — Basel Committee on Banking Supervision. *The Basel Framework*, CRE50 / CRE52 / CRE53. https://www.bis.org/basel_framework/chapter/CRE/50.htm. — EEPE and the IMM path (§1.1, §2.5).
- `[NGFS2025ST]` — NGFS (2025). *NGFS Short-term Climate Scenarios — Technical Documentation V1.0.* — the transition scenarios (§2.6).

**Tier 2 — sentence-level support**

- `[AndersenPiterbarg2010]` — Andersen, L., & Piterbarg, V. (2010). *Interest Rate Modeling* (Vol. II). Atlantic Financial Press. ISBN 978-0-9844221-1-1. — the exact simulation step (§2.1).
- `[Vasicek1977]` — Vasicek, O. (1977). *An equilibrium characterization of the term structure.* Journal of Financial Economics, 5(2), 177–188. DOI: 10.1016/0304-405X(77)90016-2. — the estimation device (§2.1).
- `[JamesWebber2000]` — James, J., & Webber, N. (2000). *Interest Rate Modelling.* Wiley. ISBN 978-0-471-97523-6. — AR(1) versus exact MLE (§2.1).
- `[Garwood1936]` — Garwood, F. (1936). *Fiducial Limits for the Poisson Distribution.* Biometrika, 28(3/4), 437–442. DOI: 10.1093/biomet/28.3-4.437. — the exact interval on $\lambda$ (§2.3).
- `[PielkeLandsea1998]` — Pielke Jr., R. A., & Landsea, C. W. (1998). *Normalized Hurricane Damages in the United States: 1925–95.* Weather and Forecasting, 13(3), 621–631. — exposure-versus-climate attribution and loss normalisation (§2.3).
- `[CEPAL2014]` — ECLAC/CEPAL (2014). *Handbook for Disaster Assessment* (DaLA). Santiago. — the CENAPRED damage methodology (§2.3).
- `[Anyfantaki2025]` — Anyfantaki, S., Blix Grimaldi, M., Madeira, C., Malovaná, S., & Papadopoulos, G. (2025). *Decoding climate-related risks in sovereign bond pricing: a global perspective.* ECB Working Paper 3135. — the rate-channel scenario slope (§2.3).
- `[Klusak2023]` — Klusak, P., Agarwala, M., Burke, M., Kraemer, M., & Mohaddes, K. (2023). *Rising Temperatures, Falling Ratings.* Management Science, 69(12), 7468–7491. DOI: 10.1287/mnsc.2023.4869. — sovereign-channel context (§1.1).
- `[Bressan2024]` — Bressan, G., Đuranović, A., Monasterolo, I., & Battiston, S. (2024). *Asset-level assessment of climate physical risk matters for adaptation finance.* Nature Communications, 15, 5371. DOI: 10.1038/s41467-024-48820-1. — the Mexican asset-level template and the coarse-proxy caveat (§2.3).
- `[Kruttli2025]` — Kruttli, M. S., Roth Tran, B., & Watugala, S. W. (2025). *Pricing Poseidon: Extreme Weather Uncertainty and Firm Return Dynamics.* Journal of Finance, 80(2), 783–832. DOI: 10.1111/jofi.13416. — exposure-share weighting (§2.3).
- `[Battiston2025CLIMACRED]` — Battiston, S., Mandel, A., Monasterolo, I., & Roncoroni, A. (2025). *Climate Credit Risk and Corporate Valuation.* CEPR DP20239. — the equity / spread adjustments and the epistemic split between scenario repricing and realised losses (§2.6).
- `[Roncoroni2021]` — Roncoroni, A., Battiston, S., Escobar-Farfán, L. O. L., & Martínez-Jaramillo, S. (2021). *Climate risk and financial stability in the network of banks and investment funds.* Journal of Financial Stability, 54, 100870. DOI: 10.1016/j.jfs.2021.100870. — your own Mexican precedent (§1.1).
- `[Vermeulen2021]` — Vermeulen, R., et al. (2021). *The heat is on.* Ecological Economics, 190, 107205. DOI: 10.1016/j.ecolecon.2021.107205. — the transition-scenario-to-risk-factor framework (§2.6).
- `[FedCSA2024]` — Board of Governors of the Federal Reserve System (2024). *Pilot Climate Scenario Analysis Exercise.* — deltas-on-current-conditions practice (§2.6).
- `[Dietz2016]` — Dietz, S., Bowen, A., Dixon, C., & Gradwell, P. (2016). *'Climate value at risk' of global financial assets.* Nature Climate Change, 6(7), 676–679. DOI: 10.1038/nclimate2972. — scenario-delta valuation as the readout family (§1.1).
- `[Artzner1999]` — Artzner, P., Delbaen, F., Eber, J.-M., & Heath, D. (1999). *Coherent Measures of Risk.* Mathematical Finance, 9(3), 203–228. DOI: 10.1111/1467-9965.00068. — why PFE is a limit statistic (§2.5).
- `[BCBS2022Principles]` — BCBS (2022). *Principles for the effective management and supervision of climate-related financial risks.* https://www.bis.org/bcbs/publ/d532.htm. — the supervisory framing (§1.1).
- `[BCBS2021Measurement]` — BCBS (2021). *Climate-related financial risks — measurement methodologies.* https://www.bis.org/bcbs/publ/d518.htm. — scenario analysis as the quantification route (§1.1).
- `[NGFS2025Notes]` — NGFS (2025). *2025 Explanatory notes on NGFS long-term scenarios.* — the damage-function retraction that motivates an own-estimated physical channel (§1.1).

The climate-finance survey keys of [[REFERENCES]] §9 (`[Battiston2017]`, `[Bolton2020]`, `[Carney2015]`, `[Giglio2021]`, …) are available for the Motivation paragraph; take their DOIs from `literature/refs.bib`.

## 4. Reading map

| Method block | Read-logs (what to read and why) | Explanations (what was done, what it means) | Theory notes | Code |
|---|---|---|---|---|
| 2.1 dynamics and calibration | [[2026-07-20_mkt_calibration]], [[2026-08-02_weekly_sampling_adoption]], [[2026-10-03_numerics_pin_cenapred_2024]] | [[2026-07-20_hw1f_estimator_disagreement_explained]], [[2026-08-02_weekly_sampling_adoption_explained]], [[2026-10-03_canonical_draw_and_extenso_2024_explained]] | [[Hull_White_Comprehensive]], [[HWModel_Theory]], [[Calibration_From_SIE_Banxico_02]], [[mexican_yield_curve_methodology]], [[Vasicek_Calibracion_Mex]] | `calibration/financial/{hull_white,gbm,yield_curve}.py`, `processes/diffusions/`, `simulation/multi_risk_factor_simulation.py` |
| 2.2 jump channel | [[2026-07-02_climate_jump_channel]], [[2026-07-26_sector_marks]], [[2026-07-30_peril_typed_events]], [[2026-08-01_per_peril_severity_phase_c]] | [[2026-07-16_hazard_jump_calibration_explained]], [[2026-07-26_sector_marks_explained]], [[2026-07-30_peril_typed_events_explained]], [[2026-08-01_per_peril_severity_phase_c_explained]] | [[referencias_riesgo_catastrofico]], [[monte_carlo_climate_risk_applications]] | `processes/jumps/`, `processes/diffusions/*.apply_jump_overlay` |
| 2.3 hazard estimation and scales | [[2026-07-16_hazard_jump_calibration]], [[2026-07-18_k_scale_deflation]], [[2026-07-21_cenapred_extension_regime_runs]], [[2026-07-25_lambda_band_readout]], [[2026-08-01_storm_cluster_robustness]] | [[2026-07-18_k_scale_deflation_explained]], [[2026-07-21_cenapred_regime_break_and_otis_explained]], [[2026-07-25_lambda_band_readout_explained]], [[2026-08-01_storm_cluster_robustness_explained]] | [[referencias_riesgo_catastrofico]], [[cenapred]] | `calibration/impact/{hazard_jump,sector_scales}.py`, `pipelines/03`, `04`, `10` |
| 2.4 H1 tests | [[2026-07-19_rate_leg_event_study]], [[2026-07-21_cenapred_extension_regime_runs]], [[2026-08-01_per_peril_severity_phase_c]] | [[2026-07-19_rate_leg_event_study_explained]], [[2026-07-21_cenapred_regime_break_and_otis_explained]], [[2026-08-01_per_peril_severity_phase_c_explained]] | — | `calibration/impact/{rate_response,sector_response}.py`, `pipelines/06`, `13` |
| 2.5 CCR metrics | [[2026-07-25_headline_metric]], [[2026-07-25_mexican_book_swap]], [[2026-08-12_ccr_audit_cva]], [[2026-09-14_scope_manuscript_gate]] | [[2026-07-25_headline_metric_explained]], [[2026-07-25_mexican_book_swap_explained]], [[2026-08-12_cva_extension_explained]], [[2026-09-14_hypotheses_and_scope_explained]] | [[monte_carlo_risk_management_framework]] | `risk/ccr/evaluators/`, `risk/ccr/xva.py`, `viz/ccr.py`, `pipelines/01`, `02`, `21` |
| 2.6 transition channel | [[2026-08-02_ngfs_short_term_connector]], [[2026-08-03_ngfs_equity_corporate_leg]], [[2026-08-22_scheduled_shocks_design]], [[2026-09-08_fase_matrix_spread_leg]] | [[2026-08-02_ngfs_transition_channel_explained]], [[2026-08-03_ngfs_equity_corporate_leg_explained]], [[2026-08-22_scheduled_shocks_design_explained]], [[2026-09-08_fase_matrix_spread_leg_explained]] | [[ngfs_short_term_scenarios_summary]], [[ngfs_application_flavors]] | `calibration/financial/scenario_shock.py`, `processes/scheduled_shocks.py`, `pipelines/15`, `16`, `17`, `22` |
| validation and figures | [[2026-08-07_viz_validation_layer]], [[2026-08-08_frn_book_v2_trajectory]] | [[2026-08-07_validation_figures_explained]], [[2026-08-08_frn_book_v2_and_trajectory_explained]] | — | `viz/`, `pipelines/18`, `19`, `20`, `23` |

## 5. Numbers available after the freeze (optional for a registration text)

The current state is the 2026-10-08 joint-draw re-base (`CCR-SIM-03`: the book is simulated once per leg on the union of the netting sets' grids, so every counterparty sees the same market and climate-event paths and book-level per-path aggregates are model outputs), on top of the 2026-10-03 two-stage re-base (`INT-23`); every figure below regenerates from a committed config and carries a manifest. A registration proposal usually states the expected contribution rather than results; if you quote numbers, quote them as preliminary.

| Readout | Value | Where |
|---|---|---|
| Baseline book EPE | 255,735.47 MXN | `INT-23` |
| Book EPE shift, headline / CT anchor / floor | −9.00 / −5.51 / −4.99 % | `INT-23` |
| Effective EPE shift, same legs | −2.18 / −1.56 / −1.43 % | `CCR-RISK-08` |
| Supervisory PFE99 shift (time-averaged, book), same legs | −17.20 / −10.03 / −8.89 % | `results/seed_sensitivity/seed_metrics.csv` |
| 1y book-exposure q99, baseline → climate, headline / CT anchor / floor | 3,041,356 → 2,727,327 / 2,855,976 / 2,872,875 MXN (−10.3 / −6.1 / −5.5 %) | `GEN-34` |
| Nivel transition, HWTP / SWUC / DAPS_NAM | −5.72 / −8.16 / −20.02 % | `INT-32`, `INT-35` |
| Trayectoria transition, same scenarios | −1.49 / −1.23 / +0.16 % | `MKT-NGFS-09` |
| Fase transition, same scenarios | −4.57 / −6.62 / −7.37 % | `INT-35` |
| Base book CVA (LGD 0.60) | 515,270 MXN | `CCR-RISK-06` |
| H1 gates | rates $p = 0.73$ (n = 100); equities $\tau = +0.198$, $p_{\text{boot}} = 0.94$ | `INT-19`, `INT-27` |
| Monte-Carlo spread across 11 master seeds (sd; canonical 233423 plus ten extra) | book EPE shift ± 0.01–0.03 pp; Effective EPE shift ± 0.02 pp; book PFE99 shift ± 0.20–0.25 pp; 1y book-exposure q99 level ± 0.4 % (range 1 %); its paired climate delta ± 0.3 pp | `results/seed_sensitivity/seed_intervals.csv` (pipelines/24, 2026-10-08) |

## 6. Checklist before you submit

- Length matches the 2024 proposal: three pages of text plus references; six to eight numbered equations, each referenced from the prose.
- Every citation key exists in the verified sections of [[REFERENCES]] and in `literature/refs.bib`; nothing from §99.
- Numbers, if any, come from `INT-23` / §5 and are labelled preliminary; the hypotheses are stated as tests, with the verdicts optional.
- British spelling throughout (modelling, calibrated, behaviour, analyse); institution and series names stay in Spanish where they name real data (`INT-07`).
- Title page: title, name, time frame with correct years, supervisors.

## Related
Plan: [[PROJECT_PLAN]] (Phase 6 chapter map) · Canon: [[DECISIONS]] (`INT-09/10/11/23/37/38`) · [[REFERENCES]] · [[GLOSSARY]] (*Hypotheses*) · Hypotheses explained: [[2026-09-14_hypotheses_and_scope_explained]] · Arms: [[CCR_MOC]] · [[MKT_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]
#arm/int #type/plan
