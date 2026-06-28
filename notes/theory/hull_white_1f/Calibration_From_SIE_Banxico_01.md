# Calibrating Hull–White from Banxico SIE Data (CF300 Bonos M + F-TIIE)

## A Practical, Bias-Aware Calibration Recipe Using Official Sources

This document supersedes the earlier, Investing.com-based calibration guide for the Mexican curve. With access to the Banxico SIE *Vector de precios de títulos gubernamentales (on the run)* — table **CF300** — and to the **TIIE de Fondeo** family of series (table CF370 and the TIIE de Fondeo index), the calibration story changes substantially. Most of the corrections that earlier had to be approximated (yield-to-zero stripping, day-count conversions, benchmark-roll noise) are either solved outright by Banxico or become very mild.

This document covers four things, in order:

1. What CF300 actually contains and how to read its columns;
2. How the dirty-price quoting (which you confirmed) drives the strip directly;
3. The use of F-TIIE for the short end, and what to do about the 1-year tenor;
4. How to pick the historical window for estimating $a$ and $\sigma$, and how to handle outlier regimes such as the COVID period.

---

## 1. What CF300 Actually Contains

Per the SIE documentation page for CF300 — *"Vector de precios de títulos gubernamentales (on the run)"* — the table publishes a **price-and-rate vector** for the on-the-run Mexican government bond universe. The series cover Cetes, Bondes, Bondes D, Bondes F, Bondes G, **Bonos** (the M-bonos in your file), Bonos MS, Udibonos, BPAs, BPATs, BPA182 and BPAG28. Each instrument category, and within it each tenor bucket, exposes the same four series:

| Series suffix | Meaning |
|:---|:---|
| Plazo | Days to maturity of the on-the-run benchmark, in calendar days |
| Precio Limpio | Clean price, per 100 face value (Bonos and most coupon instruments) |
| Precio Sucio | Dirty price (clean + accrued), per 100 face value |
| Cupón Vigente / Tasa Rendimiento | Current coupon (for fixed-coupon bonds) or YTM/discount rate (for Cetes) |

For the Bonos M family — the "on the run" classes you listed (`Bonos_0_3`, `Bonos_3_5`, `Bonos_5_7`, `Bonos_7_10`, `Bonos_10_20`, `Bonos_20_30`) — each bucket reports one set of four series. Your CSV has consolidated those into `(Date, Serie, Plazo, Cupon, Valor)` where `Valor` is the **dirty price** and `Cupon` is the current coupon. That is exactly enough to price each on-the-run bond exactly, on each trading day, without any third-party assumption.

**One important consequence of the "on-the-run" labelling.** Each bucket's `Plazo` is *not constant over time*. As the benchmark gets older and is eventually replaced, `Plazo` drifts and then jumps. For example, `Bonos_7_10` is the on-the-run benchmark with original tenor in the 7- to 10-year range; on any single date it has whatever residual `Plazo` the current benchmark has. Across dates, that residual varies, and the bucket label is just a coarse maturity bracket. You will *not* find a clean "10-year Bono M" series with a constant 10-year residual maturity. This is fine for daily calibration (which only needs a snapshot) but matters for time-series analysis (more on this in Section 5).

### 1.1 Why CF300 is a much better starting point than yields scraped from a data vendor

The earlier document treated public yield series as a pragmatic substitute for a properly bootstrapped curve. With CF300 you have the actual ingredients of the bootstrap:

- **An actual market price** of each on-the-run bond, dirty and clean.
- **An actual coupon** (so you do not need to assume the bond trades at par).
- **The actual residual maturity** in days (so you do not need to approximate).

The strip becomes deterministic rather than approximate, and the par-bond shortcut you would otherwise need can be dropped.

### 1.2 What CF300 does *not* give you

CF300 does not give you a continuous zero-coupon curve. It gives you, on each date, six observed **dirty prices** of six benchmark coupon bonds with known coupons and known days-to-maturity. The zero curve still has to be **stripped** out of those six observations, jointly with the short-end information from F-TIIE. The strip is the subject of Sections 3 and 4.

It also does not give you exact cash-flow dates of the benchmark bonds. You know the residual maturity in days but not the precise calendar of past and future coupon dates. This is dealt with in Section 3.4.

---

## 2. Dirty Price Means the Strip is Direct (No "Clean → Dirty" Step Needed)

You confirmed that `Valor` is the **dirty (full) price**. This matters because the bond pricing identity used in stripping is most naturally written in dirty-price form:

$$
P_{\text{dirty}}(t) = \sum_{j: t_j > t} c_j \cdot P(t, t_j) + N \cdot P(t, T),
$$

where $P_{\text{dirty}}(t)$ is the dirty price observed at time $t$, $c_j$ are coupon cash flows on dates $t_j$, $N$ is the redemption (per 100 face value), $T$ is the maturity date, and $P(t, t_j)$ are the (continuously-compounded) zero-coupon discount factors. Working in dirty prices avoids the bookkeeping detour through accrued interest entirely: the right-hand side already includes the accrued portion implicitly, because every coupon between now and maturity (including the *next* one in full) is on the right-hand side, and all of them are discounted from $t$.

If you only had clean prices, you would need to add accrued interest before bootstrapping. With CF300's `Precio Sucio` you skip that step.

---

## 3. Stripping a Zero-Coupon Curve from CF300 + F-TIIE

### 3.1 The Two-Block Architecture

The natural way to assemble the curve is in two blocks:

- **Short block (overnight to 1 year).** Built from F-TIIE: the overnight rate, plus the compounded-in-arrears 28-, 91- and 182-day tenors that Banxico publishes. These are zero-coupon by construction.
- **Long block (1Y onwards).** Built by stripping the six on-the-run Bonos M dirty prices (`Bonos_0_3` through `Bonos_20_30`), using the short block to discount the early coupons of the longer bonds.

The two blocks meet at one year, and Section 4 deals with that join.

### 3.2 Short Block: F-TIIE Gives 1D, 1M, 3M and 6M Directly

The TIIE de Fondeo (F-TIIE) is the daily overnight risk-free rate for Mexican pesos, calculated by Banxico from observed wholesale repo transactions in government, IPAB and Banxico paper. As the central-bank documentation for the *Índice de TIIE de Fondeo y TIIEs de Fondeo compuestas por adelantado* (table CA766) describes, Banxico also publishes:

- An **Índice de TIIE de Fondeo** (one with business-day capitalisation, one with calendar-day capitalisation), which lets you compute the realised compound return between any two dates as a simple ratio of index values.
- **TIIE de Fondeo compuestas por adelantado** at the standard tenors of **28, 91 and 182 days**, which are forward-looking compounded-in-arrears term rates expressed in annualised form.

For Hull–White calibration, the consequence is direct:

- The **28-day** compounded F-TIIE *is* a zero-coupon yield at $T = 28/360$ years (Mexican money-market convention is Actual/360).
- The **91-day** compounded F-TIIE is the zero-coupon yield at $T = 91/360$.
- The **182-day** compounded F-TIIE is the zero-coupon yield at $T = 182/360$.
- The **overnight** F-TIIE is, after one-day capitalisation, the zero rate at $T \approx 1/360$.

After converting from the simple-interest Actual/360 quoting convention to continuous compounding on Actual/365 — same conversion as before, $z_\text{cont}(T) = -\ln(P(0,T))/T$ where $P(0,T) = 1/(1 + r\,d/360)$ — you have four clean zero pillars on the short end with no stripping required. As you note, that is essentially the entire short side of the curve done.

### 3.3 The 1-Year Gap

There is a real gap between the 182-day F-TIIE pillar and the 1-year point. The gap is small (a few months), and you have several reasonable ways to fill it. Section 4.3 lays them out.

### 3.4 Long Block: Stripping the Six Bonos M

You have six on-the-run dirty prices, and you want the zero rates at the corresponding maturities. The standard sequential bootstrap proceeds from the shortest bond outward.

For each on-the-run benchmark $i$, on a chosen valuation date, you have:

- A dirty price $P_i^{\text{mkt}}$ (your `Valor`).
- A current coupon rate $c_i$ (your `Cupon`, divided by 100).
- A residual maturity $T_i = \text{Plazo}_i / 365$ years.

Bonos M pay **semi-annual** coupons, so the cash flows on the bond are $c_i/2 \cdot 100$ on each future coupon date plus $100$ at maturity. The complication is that you do not have the exact calendar of past and future coupon dates — only $T_i$. The standard practical workaround is to assume the bond's coupon dates fall on a regular semi-annual schedule ending at the residual maturity:

$$
t^{(i)}_k = T_i - (n_i - k)\cdot 0.5, \quad k = 1, 2, \ldots, n_i,
$$

with $n_i = \lceil 2 T_i \rceil$ and the constraint that $t^{(i)}_k > 0$ (any coupon date that falls before today is dropped — it is in the past). This is an approximation: the real benchmark has specific issue and maturity dates, and the semi-annual schedule may be offset by up to about three months from your inferred grid. The error this introduces is small (a fraction of a basis point on the zero rate, for an internal consistency check), and is itself dwarfed by the residual liquidity and benchmark-noise terms.

The bootstrap recursion then asserts that the model price equals the observed dirty price:

$$
P_i^{\text{mkt}} = \frac{c_i}{2}\cdot 100 \cdot \sum_{k=1}^{n_i - 1} P\bigl(0, t^{(i)}_k\bigr) + \left(1 + \frac{c_i}{2}\right)\cdot 100 \cdot P\bigl(0, T_i\bigr).
$$

Solve for $P(0, T_i)$ given the previously-determined discount factors at all earlier coupon dates:

$$
P(0, T_i) = \frac{P_i^{\text{mkt}}/100 - (c_i/2)\sum_{k=1}^{n_i - 1} P(0, t^{(i)}_k)}{1 + c_i/2}.
$$

Earlier coupon dates that fall inside the short block (less than one year) are discounted using the F-TIIE-derived short curve. Coupon dates that fall between two already-stripped Bonos M pillars are interpolated on the working zero curve as you build it outward.

The output is a sequence of six zero rates $z(T_i)$ at the six on-the-run residual maturities, plus the four short-block points and the overnight rate — eleven zero pillars in total, which is plenty for a smooth curve fit.

### 3.5 Sanity Checks That Are Now Possible

With CF300 you can verify the strip in a way that the Investing.com data did not allow:

- **Reprice the inputs.** After fitting, plug each on-the-run bond back through its pricing formula at the stripped curve and compare to `Valor`. The residual on each pillar should be zero up to numerical-integration error.
- **Cross-check coupons against par yields.** For each Bono M, compute the YTM implied by `(Valor, Cupon, Plazo)`. This should sit near the par yield implied by your stripped curve. A persistent gap suggests the coupon-date approximation is the dominant error.
- **Compare the short end to F-TIIE compounded tenors.** If you fit a curve that joins the short block and the long block, the model rate at $T = 28/360$ should match the published 28-day compounded F-TIIE up to interpolation noise.

---

## 4. From the Stripped Pillars to f(0, t) and θ(t)

### 4.1 Interpolation Choice (Same Story as Before, but Easier)

The eleven pillars now span overnight to the longest residual maturity in the `Bonos_20_30` bucket (typically around 25–30 years). On a grid this rich, both Nelson–Siegel/Svensson and monotone-convex methods (Hagan & West, 2006) work well. Banxico itself uses a methodology consistent with these families for its public Bonos M curve. For a Hull–White input, what matters is that the interpolant is **continuous and at least once differentiable** — otherwise the $\partial f/\partial T$ term in the $\theta(t)$ formula will be ill-defined or noisy.

### 4.2 Computing f(0, t) and θ(t)

The mechanics are identical to what was described in the previous document: under continuous compounding,

$$
f(0, T) = z(T) + T\cdot\frac{\partial z(T)}{\partial T},
$$

and then

$$
\theta(t) = \frac{\partial f(0,t)}{\partial T} + a\,f(0,t) + \frac{\sigma^2}{2a}\bigl(1 - e^{-2at}\bigr).
$$

What is different now is the quality of the input — the curve you get out of CF300 + F-TIIE is much closer to the curve a Mexican financial institution would actually use internally than the Investing.com-based curve was.

### 4.3 What to Use at the 1-Year Tenor

You are right that the 1-year point is the only awkward one. Three reasonable options, ordered by increasing rigour:

1. **Let the interpolant decide.** Fit Nelson–Siegel/Svensson or monotone-convex to the short block (overnight, 28D, 91D, 182D F-TIIE) plus the first long-block pillar (typically the `Bonos_0_3` bucket, with residual maturity often around 1.5–2 years). The interpolant produces a one-year rate by construction. This is the simplest option and is acceptable for risk-management work.
2. **Use the 1-year Cetes from CF300 (`Cetes 364 días`).** CF300 publishes the on-the-run 364-day Cetes — `Plazo`, `Tasa Rendimiento`, `Precio Limpio`/`Sucio`. Cetes are zero-coupon by construction, so the 364-day yield, after the Actual/360 → continuous conversion, is a zero rate at $T = 364/360 \approx 1.011$ years. This adds a fifth short-block pillar without needing to strip anything. **This is the option I'd recommend** — it gives you a clean, direct 1-year pillar from official data and resolves the gap fully.
3. **Build a synthetic 1-year point from a TIIE de Fondeo OIS swap quote**, if you have access to OTC market data. This is the cleanest from a multi-curve-bootstrapping standpoint but requires data that is not in SIE.

The 364-day Cetes from CF300 (option 2) closes the gap completely with an instrument that is unambiguously zero-coupon. There is then no awkward 1-year point left to construct.

---

## 5. Choosing the Historical Window for Estimating *a* and *σ*

Calibrating $\theta(t)$ uses one date's worth of data. Estimating $a$ (mean reversion) and $\sigma$ (volatility) uses a **time series** of a short-rate proxy, and that is where most of the bias risk lives. Three issues are particularly acute for the Mexican market: regime breaks, the COVID shock, and the benchmark-roll problem.

### 5.1 Which Series to Use as the Short-Rate Proxy

For Hull–White's $r(t)$ proxy, the three sensible candidates from SIE are:

- **F-TIIE (overnight)** — the truest short-rate proxy and the cleanest zero-coupon series. Has been published since 2 January 2006.
- **TIIE 28** — historically the standard reference, but Banxico has been pushing the market toward F-TIIE since 2020 and restricts new contracts referenced to TIIE 28 from 1 January 2025 onward. Still useful as a long historical series.
- **Cetes 28 días** — a market-priced zero-coupon yield, slightly noisier than F-TIIE because it is auctioned weekly and reflects supply/demand at issuance.

For most purposes I'd use **F-TIIE overnight** post-2006 as the cleanest proxy, with TIIE 28 used only for cross-checks or for samples that need to extend before 2006.

### 5.2 The Window-Length Trade-off

Hull–White's mean-reversion parameter $a$ is notoriously hard to identify from short-rate data alone — the likelihood is flat near the maximum, especially when the sample contains long persistent regimes (a common feature of EM short rates around easing/tightening cycles). Two competing pressures:

- **Longer windows** reduce sampling variance and stabilise $\hat a$ and $\hat\sigma$.
- **Longer windows** also span more regimes (Banxico cycles, COVID, the 2021–2023 tightening cycle), which violates the constant-parameter assumption underlying both MLE and the AR(1) regression.

The pragmatic compromise that most practitioners arrive at:

- **For $\sigma$:** a rolling window of **3 to 5 years** of daily observations. This is short enough that the volatility regime is roughly stable, long enough that the standard error of $\hat\sigma$ is small.
- **For $a$:** the **longest stable sample** you can defend, but excluding clearly anomalous regimes (see Section 5.3). The mean-reversion estimate is more sensitive to window length than to noise, so a 7–10 year window is often defensible if it does not straddle a true regime break.

A good discipline: estimate $a$ and $\sigma$ on **multiple non-overlapping windows** (say 2008–2014, 2014–2019, 2019–2024) and report the dispersion. If $\hat a$ is wildly different across windows, that *is* the answer — the model is pointing at non-stationarity, and the confidence interval on any single estimate is wider than the parameter itself.

### 5.3 Handling the COVID Shock and Other Regime Breaks

The COVID period (roughly Feb 2020 through mid-2021) is genuinely problematic. Mexican rates collapsed in March–April 2020, then climbed steeply through the tightening cycle that followed. Two failure modes if you include this period naively:

- **Inflated $\hat\sigma$.** The realised daily standard deviation is dominated by a handful of large moves in March 2020 and during the most aggressive Banxico hikes. A rolling window that includes those days will report a $\sigma$ that is too high for "normal-times" simulation.
- **Distorted $\hat a$.** The mean-reversion estimator interprets persistent post-COVID drift as a slow reversion to a high mean, which biases $\hat a$ downward (the rate looks less mean-reverting than it really is, because the "mean" itself was moving).

Three defensible treatments, from least to most invasive:

1. **Robust estimators.** Use Huber-type or trimmed-likelihood estimators that downweight large outliers. This addresses the $\sigma$ problem without dating-sensitivity in the cut. Documented for short-rate models in Brigo & Mercurio (2006); the GARCH(1,1) approach mentioned in the comprehensive reference document is a milder version of the same idea.
2. **Explicit exclusion of crisis windows.** Drop the period from, say, 1 March 2020 to 30 June 2021 from the sample. State the exclusion in the model documentation. This is the simplest treatment and is regulator-friendly because it is transparent.
3. **Regime-switching estimation.** Fit two parameter sets — one for "normal" regimes, one for "crisis" — and use scenario weights to mix them in stress testing. This is the most sophisticated treatment and probably overkill for the use case in your earlier files.

For CNBV-style stress testing, **option 2 plus a sensitivity analysis under option 1** is usually enough: estimate parameters on the cleaned sample, then re-estimate with the crisis included as a robustness check, and report both.

A subtler issue: **2008–2009** (the Global Financial Crisis) and **2017** (the peso shock) are also regime-break candidates for some Mexican series. Whichever rule you adopt for COVID, apply it consistently to other crises in the sample. An estimation choice that excludes COVID but includes 2008 will look ad hoc to a regulator.

### 5.4 Rate-Change Transformation

Most practitioners do not run MLE on the level of the rate. The level series is very persistent and ill-conditioned for likelihood-based estimation. Two equivalent but better-conditioned alternatives:

- **AR(1) on rate changes.** Regress $\Delta r_t = r_t - r_{t-1}$ on $r_{t-1}$. The AR(1) slope on the *change*, not the level, gives $-a\Delta t$ directly. This is the standard discrete-Vasicek estimator (James & Webber, 2000).
- **MLE on the exact transition density.** As described in the comprehensive reference document, the conditional density of $r_{t+\Delta t}$ given $r_t$ is exactly normal with closed-form mean and variance. This is the most efficient estimator and avoids any small-$\Delta t$ approximation error.

Both will work on the same sample and should agree to within a few percent on $\hat a$ and $\hat\sigma$. If they disagree by an order of magnitude, the sample is non-stationary — usually because of a regime break that should have been excluded.

### 5.5 Dealing with Missing Observations and the Benchmark-Roll Issue

You note that some dates in CF300 do not have all tenors. There are two distinct cases:

- **Genuine non-quote days.** The market did not trade that bucket on that day. Most calibrators just drop the date — fitting a curve from five out of six bonds is fine.
- **Benchmark turnover.** When the on-the-run bond in a bucket changes, `Cupon` and `Plazo` jump; the new bond has a different coupon and a longer residual maturity than the bond it replaces. The bond price observation is fine; what is not fine is treating the difference between yesterday and today as a market move when half of it is the benchmark change.

The clean solution is to track **benchmark-changes by bucket** as a flag, and to compute changes in stripped *zero rates* rather than changes in the raw `Valor`. The stripped zero rate at a given residual maturity is invariant to the specific benchmark bond used. If you instead build your time series from `Valor` directly, you will be embedding benchmark-change noise into your $\hat\sigma$ estimate.

---

## 6. End-to-End Recipe (Updated)

1. **Pick a valuation date.** Pull the row from CF300 for that date for: F-TIIE overnight, 28-day TIIE-Fondeo compounded, 91-day, 182-day, 364-day Cetes (`Plazo` and `Tasa Rendimiento`), and the six Bonos M buckets (`Plazo`, `Cupon`, `Valor` as dirty price).
2. **Convert all short-end yields to continuous compounding** on Actual/365.
3. **Build the short block.** Direct conversion of overnight, 28D, 91D, 182D F-TIIE; add the 364-day Cetes pillar.
4. **Strip the long block.** Apply the dirty-price recursion of Section 3.4 to the six Bonos M, using the short block to discount sub-1Y coupons.
5. **Sanity-check.** Reprice each Bono M from the stripped curve; compare to `Valor`.
6. **Interpolate.** Fit Nelson–Siegel, Svensson, or monotone-convex to the eleven pillars to get a continuous, differentiable $z(T)$ curve.
7. **Derive $f(0,T)$** as $z(T) + T\,\partial z/\partial T$.
8. **Estimate $a$ and $\sigma$ separately** from a rolling window of F-TIIE overnight (or TIIE 28 if you need pre-2006 history), excluding the COVID window (March 2020 – June 2021) and any other clearly non-stationary period. Use AR(1) on differences or exact MLE; report multiple windows for robustness.
9. **Compute $\theta(t)$** on a fine grid via the Hull–White formula.
10. **Verify** by re-pricing both the input bond prices and the input zero rates.
11. **Simulate** under either the risk-neutral or real-world measure as required.

---

## 7. References

- Banco de México. *Sistema de Información Económica (SIE)*. https://www.banxico.org.mx/SieInternet/
- Banco de México. *Vector de precios de títulos gubernamentales (on the run) — CF300.* https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?sector=18&accion=consultarCuadro&idCuadro=CF300&locale=es
- Banco de México. *TIIE de Fondeo a un día — CA684.* https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?sector=18&accion=consultarCuadroAnalitico&idCuadro=CA684&locale=es
- Banco de México. *Índices de TIIE de Fondeo y TIIEs de Fondeo compuestas por adelantado — CA766.*
- Banco de México. *Determinación de la tasa TIIE de Fondeo* (Circular 3/2012, technical note).
- Banco de México. *Determinación del Índice de TIIE de Fondeo con composición en días naturales y en días hábiles bancarios* (technical note).
- Banco de México. *Disposiciones de Carácter General Aplicables a las Instituciones de Crédito* (Circular Única de Bancos).
- Banco de México (2024). *Comunicado de prensa — exhorto al uso de TIIE de Fondeo.*
- Hagan, P. S., & West, G. (2006). "Interpolation Methods for Curve Construction". *Applied Mathematical Finance*, 13(2), 89–129.
- Hagan, P. S., & West, G. (2008). "Methods for Constructing a Yield Curve". *Wilmott Magazine*, May 2008, 70–81.
- Nelson, C. R., & Siegel, A. F. (1987). "Parsimonious Modeling of Yield Curves". *Journal of Business*, 60(4), 473–489.
- Svensson, L. E. O. (1994). "Estimating and Interpreting Forward Interest Rates: Sweden 1992–1994". *IMF Working Paper* No. 94/114.
- Brigo, D., & Mercurio, F. (2006). *Interest Rate Models – Theory and Practice* (2nd ed.). Springer Finance.
- James, J., & Webber, N. (2000). *Interest Rate Modelling*. Wiley.
- Ametrano, F. M., & Bianchetti, M. (2013). "Everything You Always Wanted to Know About Multiple Interest Rate Curve Bootstrapping But Were Afraid to Ask". *SSRN Electronic Journal*. DOI: 10.2139/ssrn.2219548.
- Hull, J., & White, A. (1990). "Pricing Interest-Rate-Derivative Securities". *The Review of Financial Studies*, 3(4), 573–592.

---

*End of document.*
