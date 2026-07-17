# 2026-07-16 — Hazard jump calibration, explained (`INT-16` / `HAZ-STOCH-04`)

> First note of the summary-explanation series (`GEN-26`): per methodological decision, *what each calibrated parameter means*, *how to interpret the results obtained*, and *the theoretical/empirical justification*. This one covers the jump-channel calibration built in `calibration.impact.hazard_jump` (`INT-16`), whose outputs feed `processes.jumps` through the `DC-XWALK-4` seam.

## 1. What was calibrated, and why

The climate jump channel (`INT-10`, `DC-CCR-SIM-2`) turns climate events into shocks on the financial diffusions. It needs exactly two empirical inputs from the HAZ arm: **how often** events arrive (the intensity $\lambda$) and **how hard** each one hits (the per-event jump-mark distribution). `INT-16` estimates both from the CENAPRED discrete climate-event base 2002–2015 (`HAZ-STOCH-04` fixes the estimation window and filters). In Lévy-process terms the pair $(\lambda, \text{mark distribution})$ *is* the specification of the jump component's Lévy measure — the fits are a model specification, not curve-fitting `[ContTankov2004]`.

## 2. What each parameter means

**$\lambda$ (`intensity_per_yr`)** — expected number of jump-triggering events per year, the homogeneous-Poisson MLE $N/T$. For `mayores_100mdp`, $\lambda \approx 19.6$/yr means: on average, about 20 times a year some climate event somewhere in Mexico causes $\geq 100$ MDP of direct damage, and each of those is a candidate jump in the simulation.

**The confidence interval (`intensity_ci_low/high`)** — the *exact* (Garwood) $\chi^2$ interval, not the Wald normal approximation `[Garwood1936]`. Exactness matters for the low-count variants (e.g. ciclón tropical, $n = 144$ events), where the normal approximation misstates coverage; this is the defensible choice for the methodology chapter.

**The arrival trend (`arrivals_growth_log_yr`, `arrivals_trend_p`)** — a log-linear intensity $\lambda(t) = \exp(\text{level} + \text{growth} \cdot (t - t_0))$ fitted by Poisson MLE. `growth` is log-growth per year, so $e^{\text{growth}} - 1$ is the fractional change per year; the $p$-value is a likelihood-ratio test of growth $= 0$ — it answers "**are arrivals rising?**" directly. `IntensityTrendFit.intensity_at(years)` projects this onto the simulation grid as the 1-D trajectory intensity the built channel already accepts (`INT-13`) — the arrival trend enters the engine with **no code change**.

**Severity (`sev_median_mdp`, `sev_sigma`)** — a lognormal fitted by MLE on per-event losses `danio_mdp` (positive losses only; zero/missing damage carries no size information, drop count reported). `median` is the median event loss in millions of MXN (*current* pesos unless `deflated`); $\sigma$ is the log-scale dispersion — unit-free, so it survives any currency rescaling. $\sigma = 1.21$ means the loss distribution spans roughly an order of magnitude between its $\sim$10th and $\sim$90th percentiles; heavy right tail, the classical catastrophe-loss shape `[Klugman]`.

**The scale $K$ (`to_mark_sampler(K)`, open `OQ-INT-07` a)** — the loss$\to$mark translation. A mark for GBM is a log-return; the sampler defines mark $= -L/K$, and since dividing a lognormal by a constant shifts only its log-mean, $L/K \sim \text{Lognormal}(\ln(\text{median}/K), \sigma^2)$ — **$\sigma$ transfers exactly, $K$ alone sets the level**. $K$ has units "MDP per unit of log-return": it answers *how many pesos of national damage correspond to a 100 % log-drop of the target*. Two candidate calibration routes: **(i) loss-to-price translation** — decompose $K = V/\varphi$ with $V$ the target-portfolio value (MDP) and $\varphi$ the fraction of national damage it absorbs (insurance penetration per `DC-XWALK-2`, or sector/geography weights); then the portfolio log-return is $\ln(1 - \varphi L / V) \approx -L/K$; transparent, but *assumes* the pass-through; **(ii) market-reaction calibration** — an event study regressing observed returns (or yield changes) around CENAPRED event dates on event losses, $\hat{K} = 1/\hat{\beta}$; empirically honest — it directly measures the climate$\to$price link the thesis claims (`INT-09`) — but noisy. A rate-target $K$ has no clean accounting identity, so it essentially requires route (ii). Ratifying the route, jointly with the asset universe (`OQ-INT-04`), is the open decision.

## 3. How to read the first estimates

| Variant | $\lambda$ (/yr) | Arrival trend | $\sigma$ | Reading |
|---|---|---|---|---|
| `todos` | 175 | $-1.2\,\%$/yr ($p = .021$) | — | all discrete climate events; severity $+28.3\,\%$/yr nominal ($p < .001$) |
| `mayores_100mdp` | 19.6 | $+9.6\,\%$/yr ($p < .001$) | 1.21 | financially material events — the natural jump-triggering set |
| `ciclon_tropical` | 10.3 | $+8.5\,\%$/yr ($p < .001$) | 2.93 | peril-specific: jumps when a cyclone happens |

**`mayores_100mdp` is an exceedance-defined process, not a peril.** By the Poisson thinning theorem `[ContTankov2004]`, thinning all events (rate $\lambda_{\text{all}}$, severity df $F$) by $L > u$ yields another Poisson process with $\lambda_u = \lambda_{\text{all}} \cdot (1 - F(u))$ and severity $L \mid L > u$. The numbers check out: $19.6 \approx 175 \times 11\,\%$, matching the threshold at $\sim$p89 of positive losses. So the variant reads: *"the process jumps whenever **any** climate phenomenon causes $\geq 100$ MDP of direct damage"* — the trigger is **financial materiality, not meteorology**. That is the right abstraction for the jump channel: the financial engine only sees (arrival time, loss size); the peril identity is marginalized out. The peril-specific variant (`ciclon_tropical`) stays the mechanistically clean narrative and the only one that maps onto covariate-driven Cox $\lambda(t)$ later (`OQ-HAZ-12`, IBTrACS wind panel).

**Why $\sigma = 1.21 < 2.93$:** conditioning on $L > u$ left-truncates the loss distribution, which cuts log-dispersion — the thresholded mixture is *less* dispersed than the unthresholded single peril. Caveats: one lognormal over a truncated mixture of perils is a pragmatic approximation (QQ-check it; POT-GPD above the threshold is the natural refinement), and the threshold is **fixed in nominal pesos**, so its real bar declines over 2002–2015 — part of the $+9.6\,\%$/yr is inflation/exposure pushing losses over a fixed bar.

**Two views of one drift:** total-event arrivals fell slightly ($-1.2\,\%$/yr, plausibly reporting), but severity grew $+28\,\%$/yr — so ever more events cross the fixed 100 MDP bar, which *is* the major-event arrival growth: $\lambda_u(t) = \lambda_{\text{all}}(t) \cdot (1 - F_t(u))$ grows when $F_t$ drifts right. Frequency growth of major events and severity growth of all events are the same underlying drift, split by the threshold.

## 4. Arrival trend vs severity trend in the simulation

Over a step $(t, t + dt]$ the jump flow is $N \sim \text{Poisson}(\lambda(t)\,dt)$ events with marks $Y(t)$. The two trends act on different moments:

- **Arrival trend** ($\lambda(t)$ rising): later steps carry *more jumps of the same size*. Raises the probability a path holds $\geq 1$ shock in a given window (what drives PE/PFE there); aggregate jump variance $\lambda(t) \cdot E[Y^2]$ grows **linearly** in $\lambda$. Already supported: pass `intensity_at(grid_years)` as the 1-D trajectory intensity.
- **Severity trend** (median drifting up $\propto e^{g t}$): the *same number* of jumps, each one *bigger* later. Deepens the conditional tail; through $E[Y^2] \propto e^{2gt}$ it compounds **exponentially** in long-horizon tail metrics. A 10-year PE99 is far more sensitive to severity growth than to equal nominal arrival growth.

**Why the severity trend cannot enter yet ("`sample` is time-blind"):** the sampler interface is `MarkSampler.sample(rng, n)` — it receives only *how many* marks to draw, never *when* the events occur; `ClimateJumpProcess.generate` draws all marks for the run in one flat call and scatters them onto (path, step) cells afterwards. A stationary severity is representable; a drifting one is not. The step-aware extension (pass per-event times into `sample`, let `LognormalMark` compute $\text{median}(t)$) is a localized interface change — the `OQ-INT-07` (c) to-do. Until then the fitted median is a 2002–2015 *window average*: conservative at the far end of a projected horizon.

## 5. Nominal vs real (the deflation caveat)

All fitted amounts are **current MXN** (`GEN-13`). The $+28\,\%$/yr nominal severity trend therefore includes inflation; the $\sim$4–5 points usually quoted for the window is the historical average INPC inflation 2002–2015 ($\approx 4.2\,\%$/yr, mostly inside Banxico's $3\,\% \pm 1$ pp band; peak $\approx 6.5\,\%$ in 2008) — a **ballpark, not computed from repo data** `[INEGI_INPC]`. The precise correction is mechanical once the deflator is wired: `fit_severity(deflator=...)` already restates every loss to the latest year's pesos; what is pending is feeding the actual INEGI INPC series through `pipelines/03` and re-emitting the table with `deflated=True`. Deflation touches severity (median, $\sigma$, trend) and — through the real value of the fixed nominal threshold — the thresholded variant's arrival trend; it never touches unthresholded $\lambda$ (counts are unit-free). Most of the trend survives deflation; the residual splits into exposure growth vs climate signal, which stays a manuscript caveat to argue against the attribution literature `[IPCC_AR6]`.

## 6. Justification summary (references)

- `[ContTankov2004]` — compound-Poisson construction, thinning, and the Lévy-measure reading of $(\lambda, \text{marks})$ (Ch. 3; simulation Ch. 6).
- `[Merton1976]` — the independent-jump assumption and the lognormal/multiplicative mark family on the price channel.
- `[Garwood1936]` (§99) — the exact Poisson CI implemented in `estimate_intensity`.
- `[Klugman]` (§99) — the actuarial frequency/severity split and the deflate-before-fitting discipline.
- `[IPCC_AR6]` (§99) — physical plausibility of the measured frequency/severity trends for Mexico's perils.
- `[INEGI_INPC]` (§99) — the INPC series behind the deflation step (`GEN-13`) and the 4–5 %/yr ballpark.

## Related

Explains: [[DECISIONS]] (`INT-16`, `HAZ-STOCH-04`) · gates it feeds: [[OPEN_QUESTIONS]] (`OQ-INT-07` a–d, `OQ-HAZ-12`) · contract: [[DATA_CONTRACTS]] (`DC-XWALK-4`, `DC-CCR-SIM-2`) · companion read-log: [[2026-07-16_hazard_jump_calibration]] · keys: [[REFERENCES]]. Arm MOCs: [[HAZ_MOC]] · [[CCR_MOC]] · Home: [[_INDEX]]

#arm/haz #arm/int #type/explanation
