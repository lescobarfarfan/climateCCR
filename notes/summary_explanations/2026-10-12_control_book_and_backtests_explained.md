# The control book and the backtesting layer, explained (2026-10-12)

Two things every financial-risk analysis carries that the results chain did not until today: a **comparison portfolio** against which the climate impact can be read, and a **backtest** of the modelled impacts against realised data. This note explains what was built, how each figure is read, what the numbers mean, and what they do and do not establish. Companion read-log with the references: [[2026-10-12_control_book_and_backtests]]; the proposal guide gained the matching method blocks, [[proposal_guide]] §2.8–2.9. Decisions `INT-39` (control book) and `INT-40` (backtests) are to be logged by `/digest`; the canon-ready lines sit at the end of the read-log.

Every table below regenerates from a committed config with a run manifest (`GEN-06`); the figures are referenced by their path under `results/` (git-ignored, present in the local vault).

## 1. The control book: what it is and why it was built that way

**The question.** The Mexican climate book (`INT-21`) is 26 BMV equities chosen for climate exposure plus a few diversifiers, and every headline number (book EPE −9.00 % under the physical jump) is a property of that one book. Without a second portfolio the heterogeneity of the impact — is the −9 % a feature of exposed sectors or of the engine? — cannot be read.

**The design.** The physical-risk literature answers this with control groups: hurricane-neighbourhood firms versus unaffected firms (Dessaint and Matray 2017), establishments in the landfall region versus the rest (`[Kruttli2025]`), drought-sorted food stocks (Hong, Li and Xu 2019), heat-exposed firms versus not (Pankratz, Bauer and Derwall 2023). The portfolio analogue is a **matched control book**: the same 30 netting sets, the same trade rules (one TIIE swap per issuer, an ATM call plus a 95 % put per listed name, cebures per issuer, the same VM pattern), with issuers drawn from sectors of low direct physical exposure — five banks, the exchange operator, three telecoms, a broadcaster, two consumer-staples names, a pharma, four retailers, a conglomerate, an auto-parts maker — plus five flagged fillers needed for 26-name parity (a chemicals group, a toll-road operator, two industrial-park FIBRAs, the tequila maker) and four debt-only issuers (two development banks, two captive auto-finance arms). Three candidates without a Yahoo listing (Alfa, GMXT, Sitios) were replaced by Actinver, Financiera Independencia and Fibra Monterrey. The universe is disjoint from the climate book: a shared name contributes the same shift to both and dilutes the difference. The index-replica alternative (Andersson, Bolton and Samama 2016; Jondeau, Mojon and Pereira da Silva 2021: start from the benchmark, drop the exposed names, re-spread weights) was kept as an option, not built, because it overlaps the climate book by construction and answers a tracking-error question rather than an impact-heterogeneity one.

**The anchor.** The control book's sector sensitivities $\gamma_i$ are composed by the same rule as the climate book's (`INT-24/25/26`: asset footprint × sector-peril tier × per-capita CENAPRED damage, with fourteen new sector rows in the S matrix and the population-share national proxy for every name), but normalised with the **Mexican book's** constant instead of its own. On the Mexican scale the control book's aggregate sensitivity is $\sum_i w_i\gamma_i = 0.241$ (range 0.061 for the exchange to 0.491 for the toll-road operator; banks 0.127, retail 0.462). Had each book been renormalised to 1, the two would have had the same expected equity impact by construction and only the cross-section could differ — the wrong design for the question asked. The user ruling of 2026-10-12 fixed the absolute anchor.

**The readout** (`pipelines/26`, `results/book_comparison/`):

| | Mexican climate book | Control book | Difference | MC yardstick |
|---|---|---|---|---|
| Baseline book EPE (MXN) | 255,735 | 235,199 | | |
| BOOK EPE shift, headline / CT anchor / floor | −9.00 / −5.51 / −4.99 % | −3.50 / −1.92 / −1.68 % | −5.50 / −3.58 / −3.31 pp | 0.028 / 0.015 / 0.019 pp |
| Rate channel only | −0.03 % | −0.005 % | | |
| Equity (sector) component, residual | −8.97 / −5.48 / −4.96 pp | −3.49 / −1.92 / −1.67 pp | | |
| $\sum w\gamma$ | 1.00 | 0.241 | | |

![Climate book vs control book — BOOK EPE shift per band, rate-only component marked](../../results/book_comparison/book_comparison.png)

*How to read it.* Each bar is a book's BOOK EPE shift (climate minus baseline, as a percentage of its own baseline) under one λ leg, with ± 2 Monte-Carlo standard deviations from the ten-seed study of each book; the short horizontal mark is the shift the same book shows when only the rate marks are switched on. Two things are visible at once: the rate channel is negligible on both books (the `[Anyfantaki2025]` literature scenario moves the short rate by hundredths of a basis point per event), so the physical impact on exposure is the equity channel; and the control book moves by 39 % of the climate book at the headline while its sensitivity is 24 % of it — the exposure structure (option moneyness, the long-forward position on each share, the desk mix) carries part of the heterogeneity. The yardstick is $\sqrt{\mathrm{sd}_A^2+\mathrm{sd}_B^2}$ because the two books draw different paths under one seed (different correlation matrices and union grids); it is a floor, and the honest uncertainty of the statement is the λ band and the author tiers of the fourteen new S rows (`OQ-INT-13`).

![Per-counterparty EPE-shift strips, climate book vs control book, three bands](../../results/figures/results_distributions/epe_shift_distribution_books.png)

*How to read it.* The `pipelines/19` strip family with a new group: each labelled run is a horizontal strip of per-counterparty EPE shifts with the BOOK shift as a diamond. The climate book's strips are wide and left-heavy (the hotel, airport and reinsurance counterparties), the control book's are compact around a few percent — the cross-section, not only the mean, is what differs.

**What it establishes.** On an otherwise identical trade structure, the physical channel's exposure impact falls from −9.0 % to −3.5 % when the issuers are drawn from low-exposure sectors; the impact is heterogeneous and sector-driven. What it does not establish: that the control book is climate-neutral (its $\gamma$ is 0.24, not 0; banks' credit-channel exposure to climate is deliberately outside the physical mark), and the magnitude of the gap inherits the S-tier judgements.

## 2. The backtesting layer: five tiers, one question each

The sector consensus (`[BCBS2021Measurement]`, the NGFS guides) is that long-horizon climate scenarios cannot be backtested on history. What can be backtested is each component on the record it was fitted to and on the record it never saw. The anchor is the BCBS *Sound practices for backtesting counterparty credit risk models* (December 2010): many initialisation dates, several horizons, calibration data cut at each date, reliability at several percentiles, a static representative portfolio, and reasonableness rather than significance at long horizons. The statistics live in `risk/market/backtest.py` (PIT, reliability tables, Kupiec, Christoffersen, Berkowitz, KS, CRPS, log scores, Diebold–Mariano), the figures in `viz.validation` (`plot_reliability`, `plot_pit_histograms`).

### 2a. Tier A — the hazard model out of time (`pipelines/27`, `results/hazard_backtest/`)

Fit on 2002–2015 (the registry window the headline uses), score 2016–2024. Three streams: cyclones unthresholded, cyclones ≥ 200 MDP-2025 (the regime-continuous tests), and the all-perils trigger set (run only to show the 2016 publication censoring, `HAZ-CENAPRED-10`).

| Stream | $\lambda$ fit | Test total vs predicted | Severity KS $p$ | Largest test loss | Annual-loss coverage 50/80/95 | A/E mean / median |
|---|---|---|---|---|---|---|
| Cyclones, all | 10.29 /yr | 88 vs 92.6 ± 9.6 ($p$ 0.68) | 0.08 | Otis, 91,540 MDP, PIT 0.975 | 0.33 / 0.89 / 1.00 | 0.08 / 0.25 |
| Cyclones ≥ 200 MDP | 6.57 /yr | 51 vs 59.1 ± 7.7 ($p$ 0.32) | < 0.01 | Otis, PIT 0.999 | 0.22 / 0.78 / 0.89 | 0.74 / 0.49 |
| All perils ≥ 200 MDP (censored) | 19.29 /yr | 65 vs 173.6 ± 13.2 ($p$ 0.00) | 0.03 | Otis, PIT 1.000 | 0.11 / 0.22 / 0.56 | 0.67 / 0.46 |

![Cyclone arrivals 2002–2024 against the 2002–2015 intensity, extended without re-anchoring](../../results/hazard_backtest/arrival_staircase_ciclon_200.png)

*How to read it.* The observed cumulative count of ≥ 200 MDP cyclone events (black staircase) against the expectation $N(t_0) + \hat\lambda (t - t_0)$ fitted on 2002–2015 and extended over 2016–2024 with its 95 % Poisson band — the honest version of the `GEN-33` staircase, which re-anchored each regime. The staircase stays inside the band to 2024: cyclone frequency is stable across the publication break. The companion `arrival_staircase_trigger_all_perils` shows the all-perils count leaving the band in 2016 — the censoring, not the climate.

![PIT of the realised annual aggregate loss under the compound-Poisson predictive, per stream](../../results/hazard_backtest/annual_loss_pit.png)

*How to read it.* Nine PIT values per stream (one per test year): where the realised annual cyclone loss fell in the predictive distribution simulated from the fitted $\lambda$ and lognormal. A uniform histogram is a calibrated predictive; a pile on the left means the model over-predicts. The unthresholded stream piles left (A/E 0.08 on the mean): its $\sigma_L \approx 2.9$ is the sub-threshold dispersion `INT-26` already diagnosed, and the lognormal mean with that $\sigma$ is enormous; the thresholded stream is closer to uniform with A/E 0.74 — the model over-predicts cyclone losses by a quarter on the mean and by half on the median because the 2016–2024 record is thinner-tailed with a higher median (the floor fit's $\sigma_L$ 1.06 against 1.33), with Otis the one event the registry tail did not expect.

*What it establishes.* Frequency is well modelled and stable; severity carries the model risk, and the direction is conservative (the registry fit over-predicts annual cyclone loss). The headline band's uncertainty is in its severity leg.

### 2b. Tier B — the loss-to-mark seam against realised insured loss ratios (`pipelines/28`, `results/loss_ratio_backtest/`)

The mark $-\beta L/K$ is an insured loss-ratio contribution (`INT-17`), so the modelled annual mark $\beta S/K$ is an annual loss ratio of the hidro + agro CNSF book, and CNSF publishes the realised paid-over-premium every year 2008–2024 with no publication break — the one realised series the H2 channel's magnitude can be scored on. Inputs: $\beta$ 0.174, $K$ 22,964 MDP-2025, registry $\lambda$ and severity, trigger share of damage 0.964 on the $\beta$ window, attritional floor 0.33 (the in-sample minimum).

| Variant | Window | Coverage 50/80/95 | A/E mean / median | CRPS | KS $p$ |
|---|---|---|---|---|---|
| raw ($\beta S/\text{premium}_y$) | in-sample 2008–15 | 0.38 / 0.50 / 0.75 | 1.64 / 1.73 | 0.206 | 0.004 |
| raw | out-of-time 2016–24 | 0.56 / 0.78 / 0.89 | 1.50 / 1.24 | 0.149 | 0.057 |
| bridged (÷ trigger share) | out-of-time | 0.56 / 0.78 / 0.89 | 1.44 / 1.20 | 0.144 | 0.095 |
| K fixed at 2024 | out-of-time | 0.44 / 0.67 / 0.89 | 1.64 / 1.38 | 0.160 | 0.005 |
| cat-excess over the floor | out-of-time | 0.11 / 0.11 / 0.22 | 0.47 / 0.06 | 0.209 | 0.000 |

![Realised CNSF loss ratio 2008–2024 over the modelled fan, raw variant](../../results/loss_ratio_backtest/loss_ratio_fan_raw.png)

*How to read it.* The `GEN-33` fan convention on a yearly grid: nested 50/80/95 bands of $\beta S/\text{premium}_y$ (green) with the realised ratio (black) and the coverage annotation. The realised series sits in the upper half of the fan most years — the model is a cat-only loss ratio, the realised one includes attritional claims — and the two catastrophe years (2015, 2024, ratios above 1) sit inside the 95 % band. `loss_ratio_fan_bridged` is the same picture divided by the trigger share, nearly identical because the ≥ 200 MDP events carry 96 % of discrete damage.

![PIT of the realised loss ratio per variant](../../results/loss_ratio_backtest/loss_ratio_pit.png)

*How to read it.* Seventeen PIT values per variant. Raw and bridged lean right (realised above the modelled median: attritional claims), cat-excess leans left (subtracting a fixed 0.33 floor over-corrects). None of the three readings is "the" answer; the table carries all three.

*What it establishes.* The loss-to-mark scale is of the right order of magnitude — between a 1.5× under-prediction with attritional claims included and a 2× over-prediction of the cat-excess — with near-nominal out-of-time coverage on the central bands. This is the magnitude check of H2, and it passes in the only sense a scale estimated on an eight-year overlap can.

### 2c. Tier C — the risk-factor forecast distributions per BCBS 2010 (`pipelines/29`, `results/risk_factor_backtest/`)

For the 26 book equities, the IPC, the FIX and the F-TIIE short rate: non-overlapping forecasts at 1W, 1M, 3M and 1Y initialised on dates spaced by the horizon from 2008 (967, 222, 74 and 18 dates), each refit on data strictly before its date with the crisis exclusions (29,732 forecasts), PITs read against nine percentiles.

| Factor | 1W coverage 50/80/95 | 1Y coverage 50/80/95 | KS / Berkowitz |
|---|---|---|---|
| Equities pooled (26 names) | 0.66 / 0.87 / 0.95 (n 19,612) | 0.54 / 0.79 / 0.92 (n 357) | both $p$ 0.000 at every horizon |
| IPC | 0.61 / 0.87 / 0.96 | 0.39 / 0.83 / 0.94 | 0.000 / 0.003 at 1W |
| FIX (MXN/USD) | 0.46 / 0.72 / 0.87 | 0.22 / 0.50 / 0.94 | 0.006 / 0.000 at 1W |
| F-TIIE (Vasicek, weekly MLE with restart) | 0.72 / 0.85 / 0.91 | 0.29 / 0.35 / 0.65 | 0.000 / 0.000 |
| Daily VaR exceptions | 95 %: median hit rate 6.2 % · 99 %: median 2.6 %, Kupiec $p < 0.05$ for 28 of 28 names | | |

![Reliability diagram at one week: empirical share of PIT ≤ p against nominal p, one curve per factor](../../results/risk_factor_backtest/reliability_1W.png)

*How to read it.* The Basel reliability criterion drawn (¶25/¶31): a reliable forecasting system sits on the diagonal; the grey band is ± 2 binomial standard errors at the pooled count. Curves above the diagonal in the lower half and below it in the upper half are over-dispersed forecasts (too wide in the body); the equities trace exactly that S-shape at one week while meeting the diagonal near 0.01 and 0.99 — leptokurtic returns against a Gaussian cone. The one-year panel (`reliability_1Y`) is nearer the diagonal with only 18 dates per name. `pit_hist_<h>` shows the same facts as per-factor histograms (a hump at one week, flattening with the horizon).

*What it establishes.* The engine's diffusions are the standard Gaussian compromise: the body is over-dispersed at short horizons and the daily tails are fatter than Gaussian (every name rejects at VaR99); the one-factor rate cone cannot span a policy cycle at one year. None of this is new to the project (`MKT-CALIB-06`, `GEN-33`) and it is why pricing rides $\theta(t)$, scenarios enter exogenously and climate effects are read as paired differences on shared paths. It is the component-level backtest the sound-practices paper requires (¶18–20), and it should be reported as such.

### 2d. Tier D — does the jump-on density describe realised returns? (`pipelines/30`, `results/jump_density_backtest/`)

Per name and horizon, realised non-overlapping log returns are scored under the plain GBM (jump-off) and under the Merton mixture the engine simulates — the jump totals drawn by `ClimateJumpProcess` over one horizon step with the adopted peril labels, $c_{ip}$ and per-label severities — and the log-score differential is tested per name and pooled (Diebold–Mariano; the Amisano–Giacomini comparison). Two variants: `engine` (the overlay as applied, with its expected drag $E[e^{J}] - 1$) and `compensated` (the mixture re-centred so only the shape is scored).

| Horizon | Band | Variant | Pooled mean log-score diff | DM | $p$ | Names rejecting jump-on at 5 % |
|---|---|---|---|---|---|---|
| 1M (294 dates) | headline | engine | +0.009 | +0.34 | 0.73 | 6 of 26 |
| 1M | headline | compensated | +0.015 | +0.59 | 0.55 | 7 |
| 1Y (24 dates) | headline | engine | −0.242 | −3.45 | 0.001 | 8 |
| 1Y | headline | compensated | −0.035 | −0.95 | 0.34 | 10 |
| 1Y | CT anchor / floor | engine | −0.07 / −0.06 | −1.49 / −1.44 | 0.14 / 0.15 | 5 / 5 |

![Diebold–Mariano statistic per name against the name's γ, one-year horizon, engine and compensated variants](../../results/jump_density_backtest/dm_vs_gamma_1Y.png)

*How to read it.* Each point is a name; below the dashed line at −1.96 the jump-on density scores significantly worse than the jump-off one. In the engine panel the high-$\gamma$ names (the airports and hotels, $\gamma \approx 4$) sit lowest: their overlay carries an expected log drag of ≈ −70 to −110 % per year that realised prices never showed. In the compensated panel the cloud rises toward zero: once the location is matched, the fat left tail alone is not rejected pooled at one year. At one month (`dm_vs_gamma_1M`) nothing is distinguishable: a month of jump mass is small against a month of volatility.

*What it establishes.* Exactly what the plan said it would: the jump channel is a loss-transmission overlay on exposure (`INT-17`, `INT-37`), not a forecast of BMV prices. Realised prices rejecting the headline overlay's drag is the pre-registered H1 null (`INT-18/19`, `INT-27`) stated in density form, and it should be written up that way — as the reason the physical channel is estimated from losses, not inferred from prices.

### 2e. Tier E — the exposure model on a static representative portfolio (`pipelines/31`, `results/static_book_backtest/`)

The sound-practices paper's own test (¶33–34, ¶41): re-strike the book at past dates, re-calibrate strictly on pre-date data, simulate, and compare with what happened. Three initialisation dates (2016-07-15, 2019-07-15, 2022-07-15); the dated market calibration (every window ending at the date; the TIIE-28 2001-start weekly MLE as the rate cell, the only one identified at all three dates — $a$ 0.56 / 0.48 / 0.49, long-run level 5.7 / 6.2 / 6.5 %, $\sigma$ 1.6 %) and the dated book (18 / 25 / 26 of the 26 names survive the min-data rule; option strikes ATM at the dated spot, swap rates and fixed-bond coupons off the dated curve, maturities shifted by one offset, FRN sobretasas kept); the three λ legs simulated jump-off and jump-on to a 0D … 3Y grid; then the **same book repriced on the realised path** (closes, FIX, F-TIIE as the short-rate state) through the engine's joint-scenario seam with one path, and the realised netted MtM per counterparty scored against the 10,000 forecast paths. 540 observations per leg and band.

| Leg / band | Mean PIT | KS $p$ | Coverage 50/80/95 | Realised exposure / forecast EE |
|---|---|---|---|---|
| Baseline (jump-off) | 0.470 | 0.002 | 0.47 / 0.76 / 0.92 | 0.971 |
| Climate, headline | 0.548 | 0.000 | 0.46 / 0.76 / 0.92 | 1.026 |
| Climate, CT anchor | 0.515 | 0.166 | 0.49 / 0.75 / 0.93 | 1.003 |
| Climate, floor | 0.511 | 0.240 | 0.49 / 0.75 / 0.93 | 1.000 |

By horizon (baseline → climate headline): 1W 0.47 → 0.49, 1M 0.48 → 0.52, 3M 0.47 → 0.55, 1Y 0.46 → 0.60, 2Y 0.46 → 0.64, 3Y 0.49 → 0.49 mean PIT; realised exposure over forecast EE 1.00 / 1.00 / 0.99 / 0.96 / 0.90 / 1.00 on the baseline. By date (baseline): 2016 PIT 0.47 and A/E 0.94; 2019 PIT 0.40 and A/E 0.95; 2022 PIT 0.54 and A/E 1.02.

![Reliability of the baseline forecast paths against realised netted MtM, by horizon](../../results/static_book_backtest/reliability_baseline.png)

*How to read it.* One curve per horizon pooled over the 30 counterparties and the three dates. The short horizons hug the diagonal; the one- and two-year curves bow (central coverage 0.32–0.38 at nominal 0.50 with the 95 % band at 0.77–0.89): realised MtM at those horizons concentrates in the forecast tails — the 2019 book's realised values sat low (post-COVID rate collapse) and the 2022 book's high (the hiking cycle), the two dates on either side of the forecast. With 90 observations per horizon, dependent across counterparties, this is the ¶38 regime: reasonableness, not significance. `reliability_climate` is the same figure for the headline jump-on leg, shifted right at 1Y–2Y (the overlay lowers the forecast, realised values move up the distribution); `pit_hist_{baseline,climate}` show the histograms per horizon.

*What it establishes.* The dated books neither over- nor under-state realised exposure (0.97 on the baseline, 1.00–1.03 with climate), the short-horizon distributions are reliable, and the mild CT/floor overlays are at least as consistent with realised MtM as the baseline. The caveats the pipeline records: the rate side is model-mapped (the pricers rebuild the curve from the realised short rate through $B(t,T)$, so the 0D pin is within 248 MXN rather than exact), options price on the flat fitted-$\sigma$ surface, the bond rows are representative re-strikes, and a 2016 book has eight fewer names.

## 3. What this session does *not* establish

The control book's neutrality (it is a lower-exposure book, $\gamma$ 0.24, with author-set sector tiers awaiting references); any statement about the equity *prices* of exposed names (tier D says the opposite, and that is the point); significance at the two-to-three-year exposure horizons (tier E); and anything about the transition channel, which runs on the Mexican book only by the user ruling. The three nulls of the project (rates, equities, now densities) and the two magnitude checks that pass (loss ratios, exposure) are one consistent story: transmission through realised losses, not anticipatory repricing.

## 4. New references used (verify before citing — `GEN-01`, `REFERENCES.md` §99)

- BCBS (2010). *Sound practices for backtesting counterparty credit risk models.* December 2010 (consultative bcbs171, final bcbs185; ISBN 92-9197-858-2 online). https://www.bis.org/publ/bcbs185.htm — `[BCBS2010Backtesting]`.
- Kupiec, P. H. (1995). *Techniques for Verifying the Accuracy of Risk Measurement Models.* Journal of Derivatives, 3(2), 73–84 — `[Kupiec1995]`.
- Christoffersen, P. F. (1998). *Evaluating Interval Forecasts.* International Economic Review, 39(4), 841–862 — `[Christoffersen1998]`.
- Berkowitz, J. (2001). *Testing Density Forecasts, with Applications to Risk Management.* Journal of Business & Economic Statistics, 19(4), 465–474 — `[Berkowitz2001]`.
- Diebold, F. X., Gunther, T. A., & Tay, A. S. (1998). *Evaluating Density Forecasts with Applications to Financial Risk Management.* International Economic Review, 39(4), 863–883 (pages to confirm) — `[DieboldGuntherTay1998]`.
- Diebold, F. X., & Mariano, R. S. (1995). *Comparing Predictive Accuracy.* Journal of Business & Economic Statistics, 13(3), 253–263 (to confirm) — `[DieboldMariano1995]`.
- Gneiting, T., & Raftery, A. E. (2007). *Strictly Proper Scoring Rules, Prediction, and Estimation.* JASA, 102(477), 359–378. DOI 10.1198/016214506000001437 — `[GneitingRaftery2007]`.
- Amisano, G., & Giacomini, R. (2007). *Comparing Density Forecasts via Weighted Likelihood Ratio Tests.* JBES, 25(2), 177–190 — `[AmisanoGiacomini2007]`.
- Czado, C., Gneiting, T., & Held, L. (2009). *Predictive Model Assessment for Count Data.* Biometrics, 65(4), 1254–1261 (to confirm) — `[CzadoGneitingHeld2009]`.
- Acerbi, C., & Székely, B. (2014). *Backtesting Expected Shortfall.* MSCI, December 2014 — `[AcerbiSzekely2014]`.
- Ruiz, I. *Backtesting counterparty risk: how good is your model?* Journal of Credit Risk (year to confirm) — `[Ruiz2014]`; Anfuso, F., Karyampas, D., & Nawroth, A. *Credit exposure models backtesting for Basel III.* Risk.net technical paper — `[Anfuso2017]`.
- Dessaint, O., & Matray, A. (2017). *Do managers overreact to salient risks? Evidence from hurricane strikes.* Journal of Financial Economics, 126(1), 97–121. DOI 10.1016/j.jfineco.2017.07.002 — `[DessaintMatray2017]`.
- Hong, H., Li, F. W., & Xu, J. (2019). *Climate risks and market efficiency.* Journal of Econometrics, 208(1), 265–281 — `[HongLiXu2019]`.
- Pankratz, N., Bauer, R., & Derwall, J. (2023). *Climate Change, Firm Performance, and Investor Surprises.* Management Science, 69(12), 7352–7398 — `[Pankratz2023]`; Addoum, J. M., Ng, D. T., & Ortiz-Bobea, A. (2020). *Temperature Shocks and Establishment Sales.* Review of Financial Studies. DOI 10.1093/rfs/hhz126 — `[Addoum2020]`.
- Engle, R. F., Giglio, S., Kelly, B., Lee, H., & Stroebel, J. (2020). *Hedging Climate Change News.* Review of Financial Studies, 33(3), 1184–1216. DOI 10.1093/rfs/hhz072 — `[Engle2020]`; Alekseev, G., Giglio, S., Maingi, Q., Selgrad, J., & Stroebel, J. (2022). *A Quantity-Based Approach to Constructing Climate Risk Hedge Portfolios.* NBER WP 30703 — `[Alekseev2022]`.
- Bua, G., Kapp, D., Ramella, F., & Rognone, L. (2022). *Transition versus physical climate risk pricing in European financial markets: a text-based approach.* ECB Working Paper 2677 — `[Bua2022]`.
- Andersson, M., Bolton, P., & Samama, F. (2016). *Hedging Climate Risk.* Financial Analysts Journal, 72(3), 13–32 — `[AnderssonBoltonSamama2016]`; Jondeau, E., Mojon, B., & Pereira da Silva, L. A. (2021). *Building benchmarks portfolios with decreasing carbon footprints.* BIS Working Paper 985 — `[Jondeau2021]`.

## Related
Read-log: [[2026-10-12_control_book_and_backtests]] · manuscript: [[proposal_guide]] (§2.8–2.9) · prior: [[2026-08-07_validation_figures_explained]] (the fan-coverage layer this extends) · [[2026-10-08_joint_draw_and_seed_precision_explained]] (the seed yardstick) · [[2026-07-26_sector_marks_explained]] (the γ composition the control book reuses) · [[2026-09-14_hypotheses_and_scope_explained]] (H1/H2/H3) · Home: [[_INDEX]] · MOCs: [[CCR_MOC]] · [[MKT_MOC]] · [[HAZ_MOC]]
#arm/ccr #arm/mkt #arm/haz #arm/int #type/explanation
