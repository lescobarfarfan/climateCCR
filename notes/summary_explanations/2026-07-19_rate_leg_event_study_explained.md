# 2026-07-19 — The rate leg: event study, the null, and the scenario fallback, explained (`INT-18`)

> Summary-explanation note (`GEN-26`) for the session that closed `OQ-INT-09`: what was estimated and on which Mexican series, what every quantity in the new pipeline means ($\beta(T)$, CAR, the HW1F loading, $S_{\text{rate,eff}}$), how to read the FALLA verdict — a *bound*, not a failure — and exactly which parts of the wired rate channel are estimate vs scenario.

## 1. What was decided

Three decisions: **(i)** the loss→rate route is a MacKinlay-style event study of Mexican sovereign yields around major CENAPRED events, with the adoption criterion **pre-registered** — written into `configs/loss_to_rate_scale.yaml` *before* any estimation ran, so the data could not tempt a post-hoc spec change (`INT-18`); **(ii)** the SIE plumbing became Python (`MKT-SIE-06/07`): the full series map of the legacy R script plus FIX and the FRED controls, and daily Bonos M yields solved from CF300 dirty prices; **(iii)** the gate returned **FALLA**, so the rate channel is wired with the *blind-fixed* literature fallback — a scenario in the `INT-12` Path B sense, never presented as a Mexican estimate.

## 2. What was measured, and on what

**The subjects are all Mexican.** Eight pillars: TIIE 28 (`SF43783`), Cetes 364 (`SF45473`), and six on-the-run Bonos M buckets whose daily yields are solved from dirty price + residual maturity + coupon under the contractual conventions (182-day coupons of $c\cdot 182/360$ per 100 face; `DC-MKT-SIE-3`). Benchmark-roll days (the residual `Plazo` jumps up) are masked so no yield *change* ever compares two different bonds (`MKT-SIE-05`). The 20–30y bucket exists from 2006-10-26 with effective maturity $T \approx 28.6$y — the "as long as possible" pillar requested for the long-horizon climate discussion.

**The events.** The canonical major-event set (≥200 MDP-2025, real pesos, 2002–2015) minus events longer than 30 days (a 249-day drought has no date around which a *daily* study can localize news; 35 excluded), collapsed into **94 episodes** by merging events that start within 5 business days of each other — hurricane-season arrivals otherwise overlap event windows and double-count. An episode's date is its first `fecha_inicio` (the market learns at first impact); its loss is the member sum.

**The measurement.** For each episode × pillar: fit $\Delta y = a + b\,\Delta y^{US}$ on the $[-120,-10]$ BD pre-event window (the matched US Treasury series — DGS3MO/2/5/10/30 — absorb global rate co-movement, so what remains is the *Mexican* reaction); sum the abnormal changes over the event window ($[0,+5]$ BD in the lead spec) into $CAR_i$; regress $CAR_i = \alpha + \beta L_i$ across episodes, $L_i$ in bn MDP-2025, with heteroskedasticity-robust (HC1) errors and a pairs bootstrap as a cross-check. $\beta$ is then *decimal yield change per bn MDP of real loss*, one per pillar × window — the $\beta(T)$ term structure in `results/loss_to_rate_scale/beta_by_pillar.csv`.

## 3. The verdict, and how to read it

**The gate** (verbatim in the config header): adopt the estimate iff $\hat\beta > 0$ with one-sided HC1 $p < 0.05$ at the longest Bonos pillar with ≥30 usable episodes, window $[0,+5]$. **Result: FALLA** — the lead cell (`BonosM_20_30`, $n = 69$) gives $\hat\beta = -1.5\times10^{-5}$ per bn, $p = 0.946$, and no pillar × window cell in the principal variant is significant; the ≥1000 MDP cut and the GFC-exclusion re-run agree. The one nominally significant cell (the discontinued 5–7y bucket, $n = 13$, dead by 2007) is a textbook multiple-comparisons artifact — precisely what pre-registration exists to keep out of the result.

**This is a finding, not a failure.** The economically honest reading: over 2002–2015, Mexican sovereign yields show **no detectable per-event response** to even the largest climate disasters — consistent with FONDEN-era fiscal absorption and with Mexico's worst climate events costing only $\sim 0.1$–$0.3\,\%$ of GDP (small-island hurricane premia of 74–126 bp `[Mallucci2022]` arise at per-event damages of several % of GDP). The estimated *bound* is the thesis deliverable: at the 30Y, the one-sided 95% bound is $\approx +3\times10^{-7}$ per bn MDP — a Wilma-class event moves the 30Y by less than $\sim 0.15$ bp.

**Why this had to be pre-registered.** With 8 pillars × 3 windows × 3 variants there are dozens of cells; some will always flash $p < .05$. Fixing one cell and one threshold before the run (OQ-CCR-05 ethos, same as the price leg's discipline) is what makes the null credible.

## 4. The wired rate channel: what each number is

Per the gate's FAIL branch, `rate_marks` in `configs/climate_jump_real.yaml` carries the **fallback fixed blind before the run**: $\beta_{\text{lit}} = 4\times10^{-6}$ decimal 10Y yield per bn MDP-2025, from the only unit-compatible verified source — an EMDE-panel estimate of *local-currency* 10Y yield responses to climate-disaster damage in % of GDP (`[Anyfantaki2025]`, Fig. 8), bridged with INEGI's Q4-2025 nominal GDP (1% of GDP = 363.1 bn MDP-2025; `[INEGI_PIB2025]`).

**The conversion.** A HW1F short-rate jump $J$ decays at the mean reversion $\alpha$, so it moves the $T$-maturity yield by only $J \cdot (1-e^{-\alpha T})/(\alpha T)$. Observing a *yield* slope $\beta_T$ therefore requires the *larger* short-rate jump $J = \beta_T\,\alpha T/(1-e^{-\alpha T})$. With the engine's $\alpha = 0.05$ and $T = 10$ (matching the source instrument), $S_{\text{rate,eff}} = 1/J_{\text{per MDP}} = 196{,}734{,}670$ MDP-2025. The seam is the same as the price leg: `to_mark_sampler(S, sign=+1)` divides the fitted lognormal severity by one constant — median mark $= 905.53/S \approx +0.046$ bp, mean $\approx +0.10$ bp per event, $\sigma = 1.211$ transfers exactly. Using the *engine's* $\alpha$ is deliberate (the injected jump reproduces the observed pillar move inside the engine's own dynamics); when the Mexican HW1F is calibrated, $S$ is re-derived with one function call because `scale.csv` stores $\beta$, $T$, $\alpha$ separately (`OQ-MKT-12`).

**Estimate vs scenario — keep the labels straight.** $\lambda = 19.29$/yr and the severity shape are *Mexican estimates* (`INT-16/17`); the price scale $K_{\text{eff}}$ is a *Mexican estimate*; the rate scale is a *literature scenario* whose magnitude is $\sim 12\times$ Mexico's own estimated upper bound at the long end. In the results chapter the rate-leg EE/PE shift is a scenario overlay; the empirical rate-leg result is the bound of §3.

## 5. Caveats carried forward

The fallback IRF peaks at years 2–5 with ≈0 impact in year 0–1, so injecting it as an immediate jump is an upper-bound convention (documented in the config); the ECB coefficients are chart-read from published figures; a flexible central bank can *ease* post-disaster (`[Klomp2020]`), opposing the credit-premium leg at the short end; and the 2002–2015 null is not final — **the 2016–2024 CENAPRED extension (Otis 2023 above all) is the strongest candidate to break it**, and the gate re-applies verbatim on the extended window (`OQ-HAZ-18`); a PASA there would replace the scenario with a Mexican estimate.

## 6. Justification summary (references)

- `[MacKinlay1997]` (§99, new) — the market-model event-study design behind §2.
- `[Anyfantaki2025]` (§10, new) — the fallback $\beta$; unit-compatible (local-currency yields on damage % GDP, climate perils only).
- `[AndersenPiterbarg2010]` — the affine yield loading $(1-e^{-\alpha T})/(\alpha T)$ inverted by `rate_scale_from_beta`.
- `[Klusak2023]` (§10, promoted) — the century-scenario sovereign repricing the per-event null does not contradict.
- `[Klomp2020]` / `[Klomp2015]` / `[CevikJalles2022]` / `[Mallucci2022]` (§10, new) — sign caveat, EM premia direction, vulnerability pricing, small-island external-validity contrast.
- `[INEGI_PIB2025]` (§10, new) — the GDP bridge (and its ~8% vintage sensitivity).

## Related

Explains: [[DECISIONS]] (`INT-18`, `MKT-SIE-06/07`) · gates it feeds: [[OPEN_QUESTIONS]] (`OQ-HAZ-18`, `OQ-MKT-12`, `OQ-INT-04`, `OQ-INT-02`) · contracts: [[DATA_CONTRACTS]] (`DC-MKT-SIE-5`, `DC-XWALK-4/5`) · companion read-log: [[2026-07-19_rate_leg_event_study]] · predecessor: [[2026-07-18_k_scale_deflation_explained]] · keys: [[REFERENCES]] §10. Arm MOCs: [[MKT_MOC]] · [[HAZ_MOC]] · Home: [[_INDEX]]

#arm/mkt #arm/int #type/explanation
