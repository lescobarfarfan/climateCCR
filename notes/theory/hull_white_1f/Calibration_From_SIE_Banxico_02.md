# Calibrating Hull–White from Banxico SIE Data — Expanded Recipe

## Detailed Formulas, Data-to-Symbol Map, and the "Tenor from Bucket" Question

This document expands the previous *Calibration_From_SIE_Banxico* note in two ways. Section 1 walks through every step of the end-to-end recipe, giving the relevant formulas, naming the variables explicitly, and mapping each symbol to a column in your CSV (or to a specific SIE series). Section 2 addresses head-on the question of how to obtain a "3-year tenor", "5-year tenor" and so on from the bucket-labelled data — a question whose honest answer reframes how the calibration should work.

A small but important note on conventions, used throughout:

- Mexican money-market instruments (Cetes, F-TIIE compounded tenors) are quoted on **Actual/360**, simple-interest.
- Mexican Bonos M pay **fixed coupons every 182 days** on **Actual/360**, with each coupon equal to $c \cdot 182/360$ per 100 face value, where $c$ is the annual coupon rate (your `Cupon`/100). Mexican market practice rounds the period to exactly 182 days regardless of calendar, so this is not an approximation — it is the contractual rule.
- All Hull–White formulas are written in **continuous compounding** on **Actual/365** (treating $T$ in years as `Plazo`/365). Conversions between conventions appear where needed.

---

## Part 1 — Step-by-Step Recipe with Explicit Formulas and Variable Mapping

### Step 1 — Pick the Valuation Date and Pull the Snapshot

For a chosen valuation date $t_0$ (e.g., 27 February 2026), assemble the following snapshot from SIE.

**From your Bonos M CSV (CF300, Bonos block):**

For each of the six on-the-run buckets $\text{Serie} \in \{$`Bonos_0_3`, `Bonos_3_5`, `Bonos_5_7`, `Bonos_7_10`, `Bonos_10_20`, `Bonos_20_30`$\}$, take the row where `Date = t₀` and read off:

| Symbol | Column in your CSV | Meaning | Units |
|:---|:---|:---|:---|
| $T_i$ | `Plazo` (then divided by 365) | Residual maturity of the on-the-run benchmark in bucket $i$ | years |
| $c_i$ | `Cupon` (then divided by 100) | Annual coupon rate of the on-the-run benchmark | decimal |
| $P_i^{\text{mkt}}$ | `Valor` | Observed dirty price per 100 face value | currency per 100 face |

**From SIE table CF300 (Cetes block) and the F-TIIE family (CF370 / CA766):**

| Symbol | SIE source | Meaning |
|:---|:---|:---|
| $r_{\text{ON}}$ | F-TIIE de Fondeo a un día (CA684) | Overnight risk-free rate, annualised, Actual/360 |
| $r^{\text{F}}_{28}$, $r^{\text{F}}_{91}$, $r^{\text{F}}_{182}$ | TIIE de Fondeo compuestas por adelantado, 28/91/182d (CA766) | Term-compounded F-TIIE, annualised, Actual/360 |
| $r^{\text{Cetes}}_{364}$ | `Cetes 364 días — Tasa Rendimiento` (CF300) | YTM of on-the-run 1-year Cetes, Actual/360 |
| $\text{Plazo}_{364}$ | `Cetes 364 días — Plazo` (CF300) | Days to maturity of the on-the-run 1-year Cetes |

**Caveats specific to this step.**

- The valuation date must exist for all series you intend to use. If a Bonos bucket is missing on $t_0$, pick the most recent available date for that bucket, **not** the closest forward date — using a forward date introduces look-ahead bias.
- The published F-TIIE compounded tenors are forward-looking term rates as of $t_0$, exactly what you want.
- All rates at this stage are still in their native quoting conventions; the conversions happen in Step 2.

### Step 2 — Convert Short-End Yields to a Continuously-Compounded Form

#### 2.0 The Day-Count Convention of the Internal Curve Is a Modelling Choice

The Hull–White SDE

$$
dr(t) = [\theta(t) - a\,r(t)]\,dt + \sigma\,dW(t)
$$

is written in physical time. Time $t$ is just real elapsed time, and $r(t)$ is the instantaneous short rate. The model itself does not specify a day-count convention for $t$ — that is something you impose externally. Whether you measure $t$ in years on Actual/365, Actual/360, Actual/Actual, or business-day count, the model gives the same answers, **provided every part of the calibration uses the same convention consistently**: the time grid for simulation, the discount-factor formulas, the parameters $a$ and $\sigma$, the function $\theta(t)$, and any historical estimation done from time series.

The choice of Actual/365 in the rest of this document is a convention, not a requirement. Brigo & Mercurio (2006, Chapter 1) use Actual/365 throughout their definitions, and most of the academic literature follows them, which is why this document does so as well. But you could equally well do everything on Actual/360, and the only difference would be that the numerical values of $\theta(t)$, $a$, $\sigma$, and the simulated rates would be expressed on a 360-day-year scale rather than a 365-day-year scale. The model is the same; only the units differ.

The day-count convention is **fixed by the market** only at the boundary where you read in raw rates from SIE. Cetes are quoted on simple-interest Actual/360; F-TIIE de Fondeo and its compounded tenors are also quoted on simple-interest Actual/360 (see §2.1 below); Bonos M coupon periods are an exact 182-day Actual/360. These are properties of the *instruments*, not of the model. Once raw rates are converted to a single internal convention, that internal convention is your free choice.

Section 2.1 documents what the SIE input rates actually are. Section 2.2 then gives two equivalent forms of the conversion to continuous compounding — one that lands on Actual/365, one that lands on Actual/360. Either is a valid input to the rest of the calibration, as long as you stay consistent.

#### 2.1 Why a Single Formula Works for Cetes, Overnight F-TIIE, and Compounded F-TIIE

All four short-end series — overnight F-TIIE, the 28/91/182-day F-TIIE compounded tenors, and the Cetes yields — are published in the same Mexican money-market convention: **annualised percentage points on Actual/360, in simple-interest form**.

The canonical reference for this convention is the Banxico *Technical Description of Mexican Federal Treasury Certificates*, Appendix 1, Equation (1):

$$
P \;=\; \frac{VN}{1 + r\cdot t/360},
$$

where $P$ is the Cetes price, $VN$ is the face value, $r$ is the *annual rate of return*, and $t$ is the term in days. This formula is the legal-and-market definition of the Cetes yield, and its functional form — discount factor equal to $1/(1 + r\cdot t/360)$ — is, by definition, **simple interest on Actual/360**. A worked numerical example follows in Appendix 2 of the same document: a 28-day Cetes at a 15.50% annual rate of return prices at $10/(1 + 0.1550\cdot 28/360) = 9.8808805$ pesos. There is no compounding term in the formula. Were the rate annually-compounded, the denominator would be $(1+r)^{t/360}$; were it continuously-compounded, it would be $\exp(r\cdot t/365)$. Neither is the case.

The same convention extends to F-TIIE de Fondeo and to its compounded tenors. F-TIIE de Fondeo is the volume-weighted median of rates paid in observed one-day repo transactions, and those underlying repo rates are themselves quoted in the standard Mexican money-market convention. The TIIE Index daily-step formula

$$
\text{Index}_D \;=\; \text{Index}_{D-1}\cdot\left(1 + \frac{TF_{D-1}}{36000}\right)
$$

confirms the convention preservation: this is a simple-interest growth factor for one day at rate $TF$ on Actual/360, expressed in percent (hence the $36000$). If $TF$ were already annually-compounded, the daily growth factor would be $(1 + TF/100)^{1/360}$, not $(1 + TF/36000)$.

For the F-TIIE compounded tenors, the convention is preserved through the formula in the Banxico *TIIE de Fondeo compuestas por adelantado* methodology:

$$
r^F_T \;=\; \left[\left(\frac{\text{Index}_D}{\text{Index}_{D-28}}\right)^{T/28} - 1\right] \cdot \frac{36000}{T},
$$

which rearranges to

$$
1 + r^F_T \cdot \frac{T}{36000} \;=\; \left(\frac{\text{Index}_D}{\text{Index}_{D-28}}\right)^{T/28}.
$$

The right-hand side is the projected compound growth factor over $T$ days; the left-hand side is the **simple-interest growth factor** in the standard Mexican money-market convention, with $r^F_T$ in percentage points. The discount factor is therefore

$$
P(t_0, t_0 + d) = \frac{1}{1 + (r/100)\cdot d/360},
$$

where $r$ is the published rate in **percent** and $d$ is the residual maturity in days. The same form holds for Cetes and for overnight F-TIIE (with $d = 1$).

#### 2.1.1 A Note on the Phrase "Términos Porcentuales Anuales"

The official Banxico documentation for both F-TIIE de Fondeo (overnight) and the F-TIIE compounded tenors states that the rate "se expresa en términos porcentuales anuales" — literally, "is expressed in annual percentage terms". This phrase is genuinely ambiguous: it could mean *annualised, in percent* (simple-interest) or *with annual compounding, in percent*. Either is a defensible reading of the words.

The disambiguator is the index formula in Anexo 4 of the Banxico methodology, which advances the TIIE Index from one day to the next using

$$
\text{Index}_D \;=\; \text{Index}_{D-1}\cdot \left(1 + \frac{TF_{D-1}}{36000}\right).
$$

This is the simple-interest growth factor for one day at rate $TF$ on Actual/360, in percent. If $TF$ were already annually-compounded, the daily growth factor would be $(1 + TF/100)^{1/360}$, not $(1 + TF/36000)$. The index formula therefore confirms that the published rate is **simple-interest Act/360**, and that the "términos porcentuales anuales" phrase refers to the units (year, percent), not to the compounding convention.

This same convention propagates to the compounded-by-adelantado tenors: the index ratio represents true compound growth, but when Banxico annualises that ratio for publication, it does so via the simple-interest formula $\times 36000/T$. The compounding lives inside the index ratio; the publication convention is simple interest.

#### 2.1.2 The Two Methodologies for Term TIIE Post-2025, and the 24 bp Differential

A subtlety that did not appear in the original version of this document, and that is essential for anyone pulling SIE data after 1 January 2025: there are **two different parallel methodologies** that produce term-TIIE rates at 28, 91 and 182 days. They differ in what economic quantity they represent, and in whether they include a fixed 24-basis-point adjustment.

**Methodology A — *TIIE de Fondeo Compuesta por Adelantado* (CA766 / Banxico Anexo 6).** This is the one used in §2.1 above. It is the **forward-looking compounded F-TIIE** projected to the relevant tenor:

$$
r^A_T \;=\; \left[\left(\frac{\text{Index}_D}{\text{Index}_{D-28}}\right)^{T/28} - 1\right]\cdot \frac{36000}{T}.
$$

There is **no 24 bp adjustment**. This rate represents the pure compounded funding cost over the relevant tenor, expressed as a simple-interest Act/360 percent.

**Methodology B — *TIIE a Plazo (contratos legados)* (Banxico Anexo 1, applicable from 1 January 2025).** This is the rate that **replaces the legacy TIIE 28 / TIIE 91 / TIIE 182 series** in legacy contracts that were originally written against the old quoted TIIE 28. Its formula is:

$$
r^B_n \;=\; \left[\left(1 + \frac{TF_{t-1} + A}{36000}\right)^n - 1\right]\cdot \frac{36000}{n} \;+\; \text{Diferencial de ajuste}.
$$

Here:

- $TF_{t-1}$ is the F-TIIE de Fondeo of the previous business day, in percent.
- $A$ is a one-day step adjustment that applies the day after a Banxico target-rate change (zero on all other days).
- *Diferencial de ajuste* is a fixed historical median spread of **24 basis points**, defined as the median of the daily spread between the legacy quoted TIIE 28 and the equivalent F-TIIE compound, computed over November 2017 – October 2022. This differential is held fixed for as long as the *TIIE a plazo* series continues to be published, and applies uniformly to all three tenors (28, 91, 182 days).

The 24 bp exists to ensure that legacy TIIE-28-referenced contracts continue to converge to the same economic value they would have had under the old quoted rate, which historically sat about 24 bp above the equivalent compounded F-TIIE because of credit and term-premium components in the old TIIE-28 quotation panel. It is a **legacy-contract spread adjustment** built into the rate by Banxico, not a feature of the underlying funding rate.

#### 2.1.3 Which Methodology Is the Right Input for Hull–White Calibration?

For a **government-bond risk model** (the use case of this document), the correct input is **Methodology A — TIIE de Fondeo Compuesta por Adelantado, with no 24 bp adjustment**. The 24 bp is an artefact of legacy contracts referenced to a discontinued rate; it does not represent funding-cost economics that belong in a sovereign-curve calibration. The Bonos M and Cetes that anchor your long block are not exposed to the legacy-TIIE-28 panel; they are sovereign instruments that price off the risk-free funding curve, and Methodology A is the cleanest available proxy for that curve at 28-, 91- and 182-day tenors.

For a **bank-product or floating-rate-note model** (e.g., modelling a portfolio of legacy TIIE-28-referenced loans), Methodology B is the right input — but in that case, the 24 bp is already baked into the published rate, and again you do not add it manually.

The 24 bp does not enter the conversion formula in §2.2 in either case. The conversion only depends on whether the published rate is simple-interest Act/360 in percent, which both methodologies are. What changes between Methodology A and Methodology B is **which curve you are calibrating to**, not how to convert that curve's rates to continuous compounding.

#### 2.1.4 Verifying Which Methodology Your Data File Came From

If you are not sure whether your file came from CA766 (Methodology A) or from the legacy CF101/CF112 series (Methodology B as of 2025-01-01), there are two quick ways to check:

- **Series ID prefix.** Series IDs starting with `SF` and listed under CA766 are Methodology A. Series IDs from the historical TIIE 28/91/182 publications (CF101/CF112) are Methodology B from 1 January 2025 onward, and were the legacy quoted rates before that date.
- **Empirical level check.** On any business day post-2025-01-01, compute the difference between the two series (Methodology B minus Methodology A) at the same tenor. The difference should be very close to 24 bp. If it is around 24 bp, your data file is Methodology B (or its predecessor series); if the two series effectively coincide, your data file is Methodology A.

For all of the calibration work in the rest of this document, **Methodology A (CA766) is assumed**. If you instead pulled Methodology B, the calibration is still valid — but you should subtract 24 bp from the input rate before treating it as a sovereign-curve pillar, to back out the underlying compounded F-TIIE rate that belongs on the risk-free curve.

#### 2.2 The Conversion Formula

The continuously-compounded zero rate at time fraction $T = d/365$ years is, in **decimal** form:

$$
z_{\text{dec}}(T) \;=\; -\frac{\ln P(t_0, t_0 + d)}{T} \;=\; \frac{365}{d}\,\ln\!\left(1 + r_{\text{dec}}\cdot\frac{d}{360}\right),
$$

with $r_{\text{dec}} = r/100$.

If you prefer to keep everything in percent (which is convenient in spreadsheets), substitute $r_{\text{dec}} = r/100$ and pull a factor of 100 through to get the equivalent **percent-to-percent** form:

$$
z_{\%}(T) \;=\; \frac{36500}{d}\,\ln\!\left(1 + r\cdot\frac{d}{36000}\right).
$$

Both forms are mathematically identical. The percent-to-percent form is the one to use directly in Excel.

#### 2.2.1 An Alternative Formula That Assumes Annually-Compounded Inputs

It is worth flagging an alternative conversion formula that produces a different answer and that one might naturally arrive at by a different reading of the SIE inputs. If the published rate $r_{360}$ were interpreted as an **annually-compounded** Actual/360 rate — i.e., the discount factor were

$$
P(t_0, t_0 + d) \;=\; (1 + r_{360})^{-d/360}
$$

— then equating to the Actual/365 continuous-compounding form $P = \exp(-r_{365,\text{cont}}\cdot d/365)$ and solving gives the tenor-independent result

$$
r_{365,\text{cont}} \;=\; \frac{365}{360}\,\ln(1 + r_{360}).
$$

This formula is **mathematically valid for annually-compounded inputs**, and it produces a clean, tenor-monotone output curve that mirrors the slope of the input. The two formulas (the simple-interest one in §2.2 and the annually-compounded one here) disagree because they assume different functional forms for how the published rate relates to the discount factor.

The right one to use is determined by what convention the input is actually quoted in, not by which result looks nicer.

#### 2.2.2 Which Convention Do the SIE Inputs Use?

For Mexican money-market series, both Cetes and the F-TIIE compounded tenors are quoted on **simple-interest Actual/360**. The evidence:

- **Cetes pricing.** The market-standard pricing identity for Cetes, used by Banxico, Indeval, and the Mexican stock exchange, is $P = \text{Face}/(1 + r_{\text{Cetes}}\cdot d/360)$. There is no Mexican Treasury convention that prices Cetes via $(1 + r)^{d/360}$.
- **F-TIIE compounded tenors.** The Banxico methodology (reproduced in §2.1 above) computes the rate as
   $$r^F_T = \left[\left(\frac{\text{Index}_D}{\text{Index}_{D-28}}\right)^{T/28} - 1\right]\cdot \frac{36000}{T}.$$
  Rearranging, the published rate satisfies $1 + r^F_T \cdot T/36000 = (\text{Index ratio})^{T/28}$. The right-hand side is a compound growth factor; the left-hand side is its **simple-interest annualisation** in percent on Actual/360. The underlying compounding lives inside the index ratio; the *publication* convention is simple interest.

So the formula in §2.2 (simple-interest input) is the one consistent with Banxico's documented methodology. The alternative formula in §2.2.1 would give an answer that is **incorrect for these specific inputs**, despite producing a curve that looks more consistent visually.

#### 2.2.3 Empirical Check You Can Run on Your Own Data

If you want to verify the convention directly, the cleanest test is: pick a date $D$ and plug the published $r^F_T$ at that date into both forms, then compare against the index ratio.

- If $1 + r^F_T \cdot T/36000$ matches $(\text{Index}_D / \text{Index}_{D-28})^{T/28}$, the convention is simple-interest Act/360, and the §2.2 formula is correct.
- If instead $(1 + r^F_T)^{T/360}$ matches that ratio, the convention is annually-compounded Act/360, and the §2.2.1 formula is correct.

The first identity is what the Banxico technical note explicitly writes, so the test should confirm simple-interest. But running it once on a single date is a useful sanity check, especially if you ever extend the workflow to a new SIE series whose convention you have not personally verified.

#### 2.2.4 Apply to the Five Short-End Pillars

Apply this to each of the five short-end pillars:

| Pillar | $d$ (days) | Input rate (in %) | Output |
|:---|:---|:---|:---|
| Overnight | 1 | $r_{\text{ON}}$ | $z(1/365)$ |
| 28-day | 28 | $r^{\text{F}}_{28}$ | $z(28/365)$ |
| 91-day | 91 | $r^{\text{F}}_{91}$ | $z(91/365)$ |
| 182-day | 182 | $r^{\text{F}}_{182}$ | $z(182/365)$ |
| 1-year (Cetes) | $\text{Plazo}_{364}$ | $r^{\text{Cetes}}_{364}$ | $z(\text{Plazo}_{364}/365)$ |

The output is a set of five $\bigl(T,\,z(T)\bigr)$ pillars on the short end, all in continuous compounding on Actual/365.

#### 2.3 Pitfall: Mixing Percentages and Decimals

The most common implementation bug is mixing the two scales. The two forms above are internally consistent; problems arise when the multiplicative factor outside the log is in one scale and the rate inside the log is in the other.

**Diagnostic for spotting the mistake.** If the formula is correctly implemented, then for any tenor $d$ where the simple growth factor $r_{\text{dec}}\cdot d/360$ is small (say below 0.05), a useful sanity check is the first-order Taylor approximation:

$$
z_{\%}(T) \;\approx\; r \cdot \frac{365}{360} \;\approx\; 1.0139\, r.
$$

So a 7.9% Actual/360 rate at a short tenor should convert to roughly $7.9 \times 1.0139 \approx 8.01\%$ in continuous-365 form. Any conversion that lands well below the input — for example halving it — almost always means the rate is being plugged into a formula that expects decimals while it is still in percent (or vice versa). The bug is silent at the overnight tenor because $\ln(1+x) \approx x$ when $x$ is tiny, and grows louder as the tenor extends.

#### 2.4 Why the Converted Rate Need Not Be Monotone in Tenor

Even when the formula is implemented correctly, the relationship between the input simple-360 rate and the output continuous-365 rate is **not monotone in $d$**. In particular, a typical Mexican curve where the input rates $r$ are essentially flat across 28/91/182 days — say all near 7.85% — will produce converted rates that go *up slightly* at 28 days but *down slightly* at 182 days relative to the input. This is not a bug, and it is specific to the **simple-interest** input convention. The annually-compounded conversion in §2.2.1 does not produce this effect, because in that case the day-count and compounding effects do not compete tenor-by-tenor — there is only the day-count uplift, which is tenor-independent.

For the simple-interest case (which is the relevant one for Mexican SIE money-market data), the cross-over comes from two competing effects:

- **Day-count uplift.** Going from Actual/360 to Actual/365 raises the equivalent rate by a factor of $365/360 \approx 1.39\%$, regardless of tenor, because the same dollar return is being annualised over a longer year.
- **Continuous-compounding drag.** Going from simple interest to continuous compounding *lowers* the equivalent annualised rate, by an amount that grows with the tenor and with $r$. For small $r\cdot d/360$, the second-order term in the Taylor expansion gives a drag of approximately $r^2 \cdot d / (2 \cdot 360)$ in decimal form — roughly $r \cdot d/(2 \cdot 360)$ as a fraction of $r$.

Adding the two effects, the net change in the rate (as a fraction of the input $r$) is approximately

$$
\frac{z_{\text{dec}} - r_{\text{dec}}}{r_{\text{dec}}} \;\approx\; \underbrace{\frac{5}{360}}_{\approx +1.39\%} \;-\; \underbrace{\frac{r_{\text{dec}}\cdot d}{2\cdot 360}}_{\text{grows with }d}.
$$

The cross-over happens when $d$ is large enough that the second term equals the first — for $r_{\text{dec}} = 0.079$, that is $d \approx 2 \cdot 5 / r_{\text{dec}} \approx 127$ days. So at 28 days you should expect the converted rate to be slightly higher than the input; at 91 days, just barely higher; at 182 days, slightly lower; and at 364 days, lower still. This pattern is normal and well-behaved, and reflects the genuine difference between the simple-interest Act/360 quoting convention and the continuous Act/365 internal representation. Critically, the curve is still a valid input to the rest of the Hull–White calibration: the discount factors $P(t_0, t_0+d)$ that come out of either form are identical at the input tenors, and only the *labelling* of those discount factors as zero rates differs.

If the converted rates collapse much further than this — e.g., the 182-day rate ends up around 3% from a 7.9% input — that is the percentage/decimal bug from §2.3, not the convention conversion.

#### 2.5 Other Caveats

- The published F-TIIE compounded tenors are *already* term rates — do not compound them again. Just plug into the formula above.
- The overnight "1-day" pillar is conceptually a placeholder for $r(t_0)$ in the model; in practice, anchoring the curve at a 1-day tenor avoids issues with extrapolation toward zero maturity.
- All Hull–White formulas in the comprehensive reference document expect rates as **decimals**, not percentages. The output of Step 2 should therefore be carried forward as decimals in any subsequent calculation. Perform the percent-to-decimal conversion at the boundary between the spreadsheet and the model code, never in the middle of a pricing formula.

#### 2.6 Where This Conversion Framework Comes From in the Literature

The conversion framework used in §2.2 is standard, and the key identities can be traced to mainstream fixed-income textbooks:

- **Hull, *Options, Futures, and Other Derivatives* (any recent edition), Chapter 4 ("Interest Rates"), Section 4.2 ("Measuring Interest Rates").** Hull introduces the conversion formula between continuously-compounded rates $R_c$ and rates compounded $m$ times per year $R_m$: $R_c = m\,\ln(1 + R_m/m)$. The Mexican money-market case is the special case where $m$ is chosen to match the day-count convention. Hull's Chapter 6 ("Interest Rate Futures") works through an explicit conversion between an Act/360 quarterly-compounded rate and an Act/365 continuously-compounded rate using exactly the form $z = (365/d)\ln(1 + r\cdot d/360)$ that appears in §2.2 — see, for example, his Eurodollar futures conversion in the section on forward-vs-futures rates.

- **Brigo & Mercurio (2006), *Interest Rate Models — Theory and Practice* (2nd ed.), Chapter 1, "Definitions and Notation".** Brigo & Mercurio define the simply-compounded spot rate $L(t,T)$, the annually-compounded rate $Y(t,T)$, and the continuously-compounded rate $R(t,T)$ as **three different ways of expressing the same discount factor**:
$$
P(t,T) \;=\; \frac{1}{1 + L(t,T)\cdot \tau} \;=\; \frac{1}{[1 + Y(t,T)]^{\tau}} \;=\; e^{-R(t,T)\,\tau},
$$
where $\tau$ is the year-fraction in whatever day-count convention applies. Equating the first and third expressions and solving for $R$ recovers exactly the formula used in §2.2. The choice of day-count convention is what determines $\tau$ for a given calendar interval.

- **Veronesi, *Fixed Income Securities: Valuation, Risk, and Risk Management* (Wiley, 2010), Chapter 2.** A similar framework, with explicit treatment of US conventions and the consequences of moving between simple and continuous compounding.

The **non-monotonicity-in-tenor** observation in §2.4 — that even with a flat input curve, the converted rates are not monotone in $d$ because day-count uplift competes with continuous-compounding drag — is, to my knowledge, a direct algebraic consequence rather than a separately-named result in the literature. None of the standard references (Hull, Brigo & Mercurio, Veronesi, James & Webber) treat it as a stand-alone phenomenon, because in textbook presentations rates are usually carried in a single convention from the outset, and the cross-tenor comparison between conventions does not arise naturally. The Taylor expansion in §2.4 makes the effect explicit and is straightforwardly derivable from the conversion identity above; readers wanting a textbook-level reference for the underlying formula should look to Hull §4.2 or Brigo & Mercurio §1.2, but for a citation of the cross-over itself there is no obvious one to provide.

### Step 3 — Build the Stripped Long Block from Bonos M

You will solve for one zero-coupon discount factor per bucket. Order the buckets by $T_i$ ascending (in your data, this is `Bonos_0_3 → Bonos_3_5 → Bonos_5_7 → Bonos_7_10 → Bonos_10_20 → Bonos_20_30`) and process them sequentially.

For each bucket $i$, the assumed coupon schedule is:

$$
t^{(i)}_k = T_i - (n_i - k)\cdot \frac{182}{365}, \qquad k = 1, 2, \ldots, n_i,
$$

where:

- $T_i = \text{Plazo}_i / 365$ is the residual maturity in years (from `Plazo`).
- $n_i = \bigl\lceil T_i \cdot 365/182 \bigr\rceil$ is the number of remaining coupon dates, equivalently the smallest integer such that $t^{(i)}_{n_i} \geq T_i$ when working backward from maturity.
- Any $t^{(i)}_k \leq 0$ is dropped (those coupons are already in the past).

The cash flows on each remaining coupon date are $c_i\cdot 182/360 \cdot 100$ pesos per 100 face value, and the redemption is 100 plus the final coupon.

The dirty-price identity is:

$$
P_i^{\text{mkt}} \;=\; c_i\cdot\frac{182}{360}\cdot 100 \cdot \sum_{k=1}^{n_i - 1} P\bigl(t_0,\,t_0 + t^{(i)}_k\bigr) \;+\; \left(1 + c_i\cdot\frac{182}{360}\right)\cdot 100 \cdot P\bigl(t_0,\,t_0 + T_i\bigr).
$$

| Symbol | Meaning | Source |
|:---|:---|:---|
| $P_i^{\text{mkt}}$ | Observed dirty price | `Valor` for bucket $i$ |
| $c_i$ | Annual coupon rate | `Cupon`/100 for bucket $i$ |
| $T_i$ | Years to maturity | `Plazo`/365 for bucket $i$ |
| $t^{(i)}_k$ | Time to $k$-th remaining coupon | computed from $T_i$ |
| $P(t_0, t_0+t)$ | Continuously-compounded zero discount factor | what we are solving for |

Solve for the unknown long-end discount factor:

$$
P\bigl(t_0,\,t_0 + T_i\bigr) \;=\; \frac{\dfrac{P_i^{\text{mkt}}}{100} \;-\; c_i \cdot \dfrac{182}{360} \cdot \displaystyle\sum_{k=1}^{n_i - 1} P\bigl(t_0,\,t_0 + t^{(i)}_k\bigr)}{1 + c_i\cdot\dfrac{182}{360}}.
$$

This is the closed-form rearrangement that gives the unknown discount factor $P(t_0, t_0 + T_i)$ at the bond's maturity in terms of all the **earlier** discount factors $P(t_0, t_0 + t^{(i)}_k)$. The next subsection walks through how those earlier discount factors are obtained, because that is the mechanically tricky part of the bootstrap.

#### 3.1 How to Obtain the Discount Factors at the Intermediate Coupon Dates

The closed-form formula above assumes the discount factors at every earlier coupon date $t^{(i)}_k < T_i$ are already known. In practice, they are obtained from the curve you have **already built up to the point of processing bucket $i$**. There are two distinct cases for each intermediate coupon date, and they require different handling.

**Case 1 — The coupon date sits between two already-known pillars.** This is the easy case. Both endpoints of the interval are known, so the discount factor at the intermediate point is obtained by **interpolation** between them. Pick any reasonable interpolation method — linear in the continuously-compounded zero rate $z(T)$ is the simplest choice and works well for bootstrap purposes:

$$
z(t) = z(T_a) + \frac{t - T_a}{T_b - T_a}\cdot[z(T_b) - z(T_a)],
$$

where $T_a$ and $T_b$ are the two flanking pillars. Then $P(t_0, t_0 + t) = \exp(-z(t)\cdot t/365)$.

For the very first Bonos M bucket processed (typically `Bonos_0_3`), all coupons that fall before 1 year fit Case 1 — they sit between known short-block pillars (overnight, 28d, 91d, 182d, 364d Cetes). For later buckets (`Bonos_3_5` and onwards), some intermediate coupons fall between two already-stripped Bonos M pillars (e.g., a coupon at 1.5 years sits between the stripped `Bonos_0_3` pillar at $\sim 1.8$ y and the 1-year Cetes at $1.0$ y), and the same Case-1 interpolation applies.

**Case 2 — The coupon date sits between the last-known pillar and the unknown maturity $T_i$ of the bucket currently being stripped.** This is the hard case, and it is where the bootstrap deviates from a simple closed form. The right endpoint of the interval is precisely the quantity you are trying to solve for, so the discount factor at the intermediate coupon date depends on the unknown.

Two equivalent strategies handle this:

- **Strategy A — Numerical root-find.** Posit an interpolation rule that relates intermediate $z(t)$ values to the unknown $z(T_i)$. The simplest is linear-in-$z$ between the last-known pillar $T_{i-1}$ and the unknown pillar $T_i$:
$$
z(t) = z(T_{i-1}) + \frac{t - T_{i-1}}{T_i - T_{i-1}}\cdot[z(T_i) - z(T_{i-1})] \quad\text{for}\quad t \in (T_{i-1}, T_i).
$$
Substitute this expression for each Case-2 intermediate coupon date into the bond pricing identity. The result is a single equation in the single unknown $z(T_i)$, which is monotone-decreasing in $z(T_i)$ (higher rates produce lower discount factors and lower bond prices). Solve via Newton-Raphson or bisection; convergence takes 3–5 iterations.

- **Strategy B — Choose an interpolation that decouples the unknowns.** If you assume that the discount factor at any Case-2 intermediate date is *piecewise-flat in the forward rate* between $T_{i-1}$ and $T_i$ (or equivalently, that the zero rate is locally constant), then $P(t_0, t_0 + t) = P(t_0, t_0 + T_{i-1})\cdot\exp(-z(T_{i-1})\cdot(t - T_{i-1})/365)$ for $t \in (T_{i-1}, T_i)$. This makes the Case-2 discount factors known explicitly without reference to $T_i$, and the original closed-form rearrangement applies directly. This is computationally simpler but introduces a small bias because the forward rate is not actually flat between pillars; the bias is on the order of a few basis points and is well within risk-management tolerance for a sovereign-bond curve.

For most practical implementations, Strategy A is recommended for Bonos buckets where the unknown maturity is more than about 2 years beyond the last-known pillar (notably `Bonos_10_20` and `Bonos_20_30`, where the gap is large), while Strategy B is acceptable for the shorter buckets. Both produce valid pillars for the Step 6 global curve fit; the differences in the resulting $z(T_i)$ values are small.

#### 3.2 Two Levels of Interpolation Choice

There is a related point worth flagging explicitly: the interpolation method used **during** the bootstrap (in Case 1 and in Strategy A above) is a separate choice from the interpolation method used in **Step 6** (the global curve fit). They serve different purposes:

- The **bootstrap interpolation** is local. It only matters in the gaps between known pillars, and is used to compute discount factors for intermediate coupon dates of a single bond. Once that bond has been stripped, the interpolation is discarded — only the new pillar $z(T_i)$ is carried forward.
- The **global interpolation** in Step 6 is a single, smooth, differentiable function across the entire span. It is the input to the $f(0,t)$ derivation and to $\theta(t)$.

It is perfectly acceptable for the two interpolation choices to differ. Linear-in-$z$ during bootstrap (computationally trivial) and Nelson-Siegel/Svensson at Step 6 (smooth and differentiable everywhere) is a common pairing.

For an even cleaner implementation, **iterative bootstrap** is sometimes used: bootstrap once with linear-in-$z$, fit the global curve, then re-bootstrap using the global curve to discount intermediate coupons of all buckets, then re-fit, and iterate. This typically converges in 2–3 passes and produces pillars that are mutually consistent with the final fitted curve. For the use case in this document (Hull–White calibration for risk management, where the model itself has noise of several basis points), single-pass bootstrap with linear-in-$z$ is more than adequate.

#### 3.3 Summary of the Per-Bucket Procedure

For each Bonos M bucket $i$, processed in order of ascending residual maturity:

1. Construct the assumed coupon schedule $\{t^{(i)}_k\}$ from the bucket's `Plazo`.
2. For each intermediate coupon date $t^{(i)}_k < T_i$:
   - If $t^{(i)}_k$ sits between two known pillars (Case 1), interpolate the curve to obtain $P(t_0, t_0 + t^{(i)}_k)$.
   - If $t^{(i)}_k$ sits between the last-known pillar and the unknown $T_i$ (Case 2), apply Strategy A or Strategy B as described above.
3. Solve the bond pricing identity for the new pillar $z(T_i)$ — closed form under Strategy B, numerical root-find under Strategy A.
4. Add the new pillar to the curve and proceed to the next bucket.

The output of this step is six new pillars $\bigl(T_i,\,z(T_i)\bigr)$ where:

$$
z(T_i) = -\frac{\ln P(t_0,\,t_0 + T_i)}{T_i}.
$$

**Caveats specific to this step.**

- The 182-day convention for coupons is contractual, not a smoothing choice. Do not use 0.5 years.
- The recursion assumes the on-the-run benchmark is *currently outstanding* — i.e., $T_i > 0$. If a benchmark has been retired and a new one is not yet on-the-run, that bucket will be missing on $t_0$ and you simply skip it for that day.
- The sequential strip is sensitive to the discounting of the early coupons of long bonds. If your short block is wrong, the long-end strip absorbs the error. The sanity check in Step 5 catches this.

### Step 4 — Assemble the Pillar Table

You now have eleven pillars in continuous compounding on Actual/365:

| Index | Tenor | Source |
|:---|:---|:---|
| 1 | Overnight (1/365 ≈ 0.003 y) | F-TIIE Fondeo |
| 2 | 28/365 ≈ 0.077 y | F-TIIE 28D compounded |
| 3 | 91/365 ≈ 0.249 y | F-TIIE 91D compounded |
| 4 | 182/365 ≈ 0.499 y | F-TIIE 182D compounded |
| 5 | $\text{Plazo}_{364}/365 \approx 1.0$ y | Cetes 364d |
| 6 | $\text{Plazo}_{\text{Bonos}\_0\_3}/365$ | Stripped from `Bonos_0_3` |
| 7 | $\text{Plazo}_{\text{Bonos}\_3\_5}/365$ | Stripped from `Bonos_3_5` |
| 8 | $\text{Plazo}_{\text{Bonos}\_5\_7}/365$ | Stripped from `Bonos_5_7` |
| 9 | $\text{Plazo}_{\text{Bonos}\_7\_10}/365$ | Stripped from `Bonos_7_10` |
| 10 | $\text{Plazo}_{\text{Bonos}\_10\_20}/365$ | Stripped from `Bonos_10_20` |
| 11 | $\text{Plazo}_{\text{Bonos}\_20\_30}/365$ | Stripped from `Bonos_20_30` |

The actual numerical values of the long pillars depend on the day; each `Plazo` drifts as the benchmark ages. This is the right behaviour, and Section 2 of this document explains why you should embrace it rather than try to map it onto fixed tenors like "3y, 5y, 7y, 10y, 20y, 30y".

### Step 5 — Sanity-Check by Re-Pricing the Inputs

Plug each pillar back through its pricing formula and compare to the input.

For the short block, the model dirty price (per 100 face) at maturity $d$ days from rate $z$ is:

$$
\widehat{P} = 100 \cdot e^{-z\,d/365}, \qquad \text{which in money-market form is}\quad \widehat{P} = \frac{100}{1 + r\,d/360}.
$$

The two should agree to numerical precision (since the conversion is exact for a single zero pillar).

For the long block, plug $z(T_i)$ and the curve at all $t^{(i)}_k$ back into the full dirty-price identity from Step 3 and compare to $P_i^{\text{mkt}}$. The residual should be of order $10^{-10}$ if the strip is implemented correctly. A residual on the order of one basis point on price means there is a bug — most often, either the wrong day count on coupons (using `0.5` instead of `182/360`), or stale earlier pillars that were not updated when the curve was rebuilt.

### Step 6 — Interpolate to Get a Continuous Zero Curve

The eleven pillars are still discrete. The Hull–White $\theta(t)$ formula needs the zero curve $z(T)$ as a continuous, **once-differentiable** function, and the forward rate $f(0,T)$ as a continuous, **once-differentiable** function. The pillars-to-curve step is where the choice of interpolation matters.

Recommended choices, in order of complexity:

1. **Nelson–Siegel (4 parameters)** or **Svensson (6 parameters)** — fitted by least-squares to the eleven $z(T_i)$. Closed-form for $z(T)$, $\partial z/\partial T$, $f(0,T)$, $\partial f/\partial T$. Cannot oscillate. Recommended default for this use case.
2. **Cubic spline on $\ln P(t_0, t_0 + T)$** — exact pass through the pillars; smooth; differentiable. Can oscillate if pillars are noisy.
3. **Monotone-convex (Hagan & West, 2006)** — designed specifically to produce well-behaved forward curves. More complex to implement.

Whichever method you choose, evaluate $z(T)$ on a fine time grid $\{T_j\}$ (e.g., $T_j = j/12$ for $j = 1, \ldots, 360$ to cover monthly out to 30 years).

### Step 7 — Derive the Instantaneous Forward Curve

Under continuous compounding on Actual/365, the discount factor is $P(0,T) = e^{-z(T)\,T}$, so $\ln P(0,T) = -z(T)\,T$, and the instantaneous forward rate is:

$$
f(0,T) = -\frac{\partial \ln P(0,T)}{\partial T} = z(T) + T\cdot\frac{\partial z(T)}{\partial T}.
$$

Compute $f(0,T)$ on the same fine grid as in Step 6. With Nelson–Siegel or Svensson the derivative is closed-form. With a spline, evaluate the analytical spline derivative. Avoid finite differences applied to a noisy spline output — the noise gets amplified.

### Step 8 — Estimate $a$ and $\sigma$ from a Historical Short-Rate Series

Calibrating $\theta(t)$ uses the snapshot from Steps 1–7. The other two Hull–White parameters, $a$ (mean reversion speed) and $\sigma$ (volatility), are estimated from a time series of a short-rate proxy.

**Recommended proxy:** F-TIIE de Fondeo a un día (CA684) on daily frequency, post-2006.

**Sample window:** start with 2014–2019 as a "clean" baseline; report robustness against 2008–2014 and 2019–2024 separately. Exclude 1 March 2020 to 30 June 2021 (COVID) consistently across all windows.

**Estimator: AR(1) on differences (Vasicek discretisation).** Let $\{r_{t_k}\}$ be the daily F-TIIE series after exclusions, and $\Delta t = 1/252$ years (business-day count) or $\Delta t = 1/365$ (calendar-day count) — pick one and use it consistently. Regress:

$$
r_{t_{k+1}} - r_{t_k} = \alpha + \beta\,r_{t_k} + \eta_{k},
$$

and read off:

$$
\hat a = -\frac{\beta}{\Delta t}, \qquad \hat\mu = -\frac{\alpha}{\beta}, \qquad \hat\sigma = \frac{\text{s.d.}(\eta_k)}{\sqrt{\Delta t}}.
$$

The mean-reversion level $\hat\mu$ is not used directly in the Hull–White SDE (it is replaced by $\theta(t)$), but inspecting it is useful as a sanity check — for Mexico it should sit in the high single digits.

**Caveats.** $\hat a$ is notoriously noisy. Use the dispersion across windows as a confidence statement rather than reporting one number with a tight standard error. If the AR(1) and exact-MLE estimators disagree by more than a few percent, the sample is straining the constant-parameter assumption; exclude one more crisis or shorten the window.

### Step 9 — Compute $\theta(t)$ on a Fine Grid

For each grid point $t_j$ in Step 6, compute:

$$
\theta(t_j) = \underbrace{\frac{\partial f(0,t_j)}{\partial T}}_{\text{from Step 7's curve}} \;+\; \hat a \cdot f(0, t_j) \;+\; \frac{\hat\sigma^2}{2\hat a}\bigl(1 - e^{-2\hat a t_j}\bigr).
$$

This produces a discrete representation of the deterministic function $\theta(t)$ that goes into the Hull–White SDE.

**Caveat on mixing measures.** The $\hat a$ and $\hat\sigma$ from Step 8 are estimated under the **real-world** measure $\mathbb{P}$. When you plug them into the formula above and into the simulation, the model is technically a real-world model that happens to match today's risk-neutral curve. For risk-management work this is the standard approach. For derivative pricing, $\hat\sigma$ should be implied from caps/swaptions and $\hat a$ from a calibration to volatility cubes, not from historical estimation — at which point the model becomes properly risk-neutral.

### Step 10 — Verify Once More

Two final checks before simulating:

1. **Curve check.** For each Bonos M pillar $T_i$, recompute the model-implied dirty price using the calibrated curve (not just the stripped $z(T_i)$) and compare to `Valor`. The residual should be of order machine precision.
2. **Forward-rate sanity.** Plot $f(0,T)$. The shape should be smooth, without spikes. Spikes around the join between the short block and the long block usually mean the interpolation is locally too aggressive — consider switching from spline to Nelson–Siegel or Svensson.

### Step 11 — Simulate

Discrete-time simulation under the Euler scheme:

$$
r(t_{j+1}) = r(t_j) + \bigl[\theta(t_j) - \hat a\, r(t_j)\bigr]\,\Delta t + \hat\sigma\,\sqrt{\Delta t}\,\varepsilon_{j+1},\qquad \varepsilon_{j+1}\sim\mathcal{N}(0,1) \text{ iid},
$$

with $r(t_0)$ initialised to either the overnight F-TIIE on the valuation date (the cleanest proxy for the instantaneous short rate) or to $f(0,0)$ from your interpolated curve (consistent with the no-arbitrage assertion). For real-world simulation, replace $\theta(t_j)$ by $\theta(t_j) + \hat\lambda\hat\sigma$ as discussed in the comprehensive reference document.

Aggregate paths into discount factors via the trapezoidal rule, value the portfolio under each path, and proceed with the risk metrics.

---

## Part 2 — How to Get the "3-Year Tenor" from the Buckets

This question deserves a direct answer, because it points at a structural feature of the data that, once understood, simplifies rather than complicates the calibration.

### 2.1 The Honest Answer: You Don't Map Buckets to Fixed Tenors

The bucket label `Bonos_0_3` does not mean "the 3-year Mexican zero rate". It means: *the on-the-run Mexican government bond that was issued with an original maturity in the 0-to-3-year segment*. On any given day, the residual maturity of that bond is whatever `Plazo` says it is — which might be 2.0 years, or 1.4 years, or 2.7 years, depending on how long ago the benchmark was issued and when the next one will replace it.

So the right mental model is:

- **The bucket label tells you which segment of the curve the observation lives in**, not the tenor itself.
- **The actual tenor of each observation is `Plazo/365`**, and this is a property of the day, not of the bucket.

This is not a bug or an inconvenience. It is how an "on-the-run" vector works. The same is true of the US on-the-run Treasury curve, the German Bund curve, and so on.

### 2.2 What This Means for Calibration

The Hull–White calibration does not need rates at fixed canonical tenors (3y, 5y, 7y, 10y, etc.). It needs a continuous zero curve $z(T)$ defined for all $T \in [0, T_{\max}]$. The path is:

1. On valuation day $t_0$, observe the snapshot. The six Bonos M buckets each contribute one pillar at their *current* residual maturity $T_i$. These maturities will *not* be 3, 5, 7, 10, 20, 30 — they will be whatever residual maturities the on-the-run bonds happen to have on that day.
2. Strip a zero rate at each of those six current maturities (Step 3 of Part 1).
3. Combine with the five short-end pillars to get eleven pillars $\bigl(T_i,\,z(T_i)\bigr)$ at the *current observed* maturities.
4. Interpolate to get a continuous $z(T)$ (Step 6).
5. Read off any tenor you want — 3y, 5y, 10y, anything in between — from the *interpolated curve*, not from the raw data.

So if you want the "5-year zero rate today", you compute $z(5)$ by evaluating your fitted Nelson–Siegel/Svensson/spline at $T = 5$. The data point that contributed the most to that value is whichever pillar(s) sit nearest $T = 5$ — likely the stripped point from `Bonos_3_5` or `Bonos_5_7`, depending on where their `Plazo` happens to fall on that day.

### 2.3 Common Mistake: Using Buckets as Fixed-Tenor Labels

A natural mistake is to treat the `Bonos_0_3` row as "the 3-year point", `Bonos_3_5` as "the 5-year point", `Bonos_5_7` as "the 7-year point", and so on, and to feed those labels into an interpolation as if they were the tenors. This produces a curve that is mis-located by anywhere from a few months to nearly two years at each pillar, in a direction that drifts as benchmarks age. The error is largest near a benchmark roll and smallest just after one.

Always use `Plazo/365` as the tenor for each pillar. The bucket label is documentation, not data.

### 2.4 What the Buckets *Do* Tell You

The buckets are useful in two specific ways:

1. **They tell you which observation belongs to which segment of the curve.** If you are doing a time-series analysis of "the 5-year rate", the natural object to track is the stripped zero from whichever bucket has $T_i$ closest to 5 on each day, with a benchmark-roll flag when it changes.
2. **They tell you which on-the-run benchmark you are looking at.** When `Cupon` jumps in `Bonos_7_10` from one day to the next, that is a benchmark roll: the previous on-the-run 10-year bond has been replaced by a new one with a different coupon. Your data is fine, but interpreting the day-over-day change in `Valor` as a market move would be wrong.

### 2.5 Long-Maturity Coverage from Six Buckets

A reasonable concern: six pillars between roughly 1.5 years and roughly 28 years is a sparser grid than ideal. This is a real limitation, but a manageable one:

- **The short end is well-covered** by F-TIIE plus 1-year Cetes (5 pillars under 1.1 years).
- **The 1–3 year region** is anchored by the 1-year Cetes pillar plus the `Bonos_0_3` strip, typically near 1.5–2.0 years.
- **The 3–10 year region** has three pillars — adequate for any of the recommended interpolators.
- **The 10–30 year region** has only two pillars (`Bonos_10_20` and `Bonos_20_30`). This is the sparsest part of the curve.

For long-dated portfolios (e.g., heavy `Bonos_20_30` exposure), this last point matters: the calibrated forward curve at 25 years is essentially an interpolation between two pillars that are themselves drifting in residual maturity. If your portfolio has material long-end risk, consider supplementing with off-the-run Bonos M observations (also in CF300, under specific issue identifiers) to densify the 10-30 year region. The strip works the same way — observed dirty price plus known coupon plus known maturity — only the data-collection step gets larger.

### 2.6 Summary of the Bucket-to-Tenor Question

| If you want… | What you do |
|:---|:---|
| The 3-year zero rate today | Evaluate $z(3)$ on your fitted continuous curve |
| The 5-year zero rate today | Evaluate $z(5)$ on your fitted continuous curve |
| The 10-year zero rate today | Evaluate $z(10)$ on your fitted continuous curve |
| The on-the-run "around 3-year" data point | The `Bonos_0_3` row (its actual tenor is `Plazo`/365) |
| The on-the-run "around 10-year" data point | The `Bonos_7_10` row (its actual tenor is `Plazo`/365) |
| A historical time series of the 5-year rate | Track $z(5)$ from the daily fitted curve, not raw bucket values |

The structural insight is: **the data gives you on-the-run prices at drifting maturities; the calibration produces a continuous curve; the canonical tenors are read off the curve, not the data.**

---

## References

- Banco de México. *Vector de precios de títulos gubernamentales (on the run) — CF300.* https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?sector=18&accion=consultarCuadro&idCuadro=CF300&locale=es
- Banco de México. *Technical Description of Mexican Federal Treasury Certificates (CETES).* (English version of the Banxico technical note. Appendix 1, Equation (1) gives the canonical Cetes pricing formula $P = VN/(1 + r\cdot t/360)$ — the definitional source for the simple-interest Actual/360 convention used throughout the Mexican money market.) https://www.banxico.org.mx/markets/d/%7B3F4F830E-B395-158A-208F-B636D8AF2573%7D.pdf
- Banco de México. *TIIE de Fondeo a un día — CA684.* Technical note: *Determinación de la Tasa TIIE de Fondeo* (Circular 3/2012). https://www.banxico.org.mx/mercados/d/%7B3F620274-54CA-0261-E055-775AFEDB0A0F%7D.pdf
- Banco de México. *Índices de TIIE de Fondeo y TIIEs de Fondeo compuestas por adelantado — CA766.* Technical note: *Determinación del Índice de TIIE de Fondeo con composición en días hábiles bancarios, el Índice de TIIE de Fondeo con composición en días naturales y las TIIE de Fondeo compuestas por adelantado.*
- Banco de México. *Grupo de Trabajo de Tasas de Referencia en México (GTTR), 13ª Reunión, Anexo 1: Nueva metodología de las TIIE a plazo (contratos legados).* (Reference for the 24 bp diferencial de ajuste applied to legacy TIIE 28/91/182 series from 1 January 2025.) https://www.banxico.org.mx/mercados/grupo-de-trabajo-de-tasas-de-referencia-alternativ/d/%7B0889B314-E618-6770-08CE-45DA5F7E9FF0%7D.pdf
- Banco de México (2023). *Resolución que modifica las Disposiciones aplicables a las operaciones de las instituciones de crédito… en materia de la TIIE de Fondeo Compuesta por Adelantado.* Diario Oficial de la Federación, 13 de diciembre de 2023.
- BBVA Research (2010). *Mexico Fixed Income Handbook.* (Practitioner-side reference for Mexican government and corporate fixed-income conventions, including the 360-day-year coupon convention for Bonos M and the YTM-based market quotation convention.) https://www.bbvaresearch.com/wp-content/uploads/mult/100921_HandbookMexico_tcm346-233218.pdf
- Hagan, P. S., & West, G. (2006). "Interpolation Methods for Curve Construction". *Applied Mathematical Finance*, 13(2), 89–129.
- Nelson, C. R., & Siegel, A. F. (1987). "Parsimonious Modeling of Yield Curves". *Journal of Business*, 60(4), 473–489.
- Svensson, L. E. O. (1994). "Estimating and Interpreting Forward Interest Rates: Sweden 1992–1994". *IMF Working Paper* No. 94/114.
- Brigo, D., & Mercurio, F. (2006). *Interest Rate Models – Theory and Practice* (2nd ed.). Springer Finance. Chapter 1 ("Definitions and Notation") gives the canonical statement of the equivalence between simply-compounded, annually-compounded and continuously-compounded zero rates as different ways of expressing the same discount factor.
- Hull, J. C. (recent eds.). *Options, Futures, and Other Derivatives.* Pearson. Chapter 4 (Section 4.2, "Measuring Interest Rates") covers conversion between compounding conventions; Chapter 6 (Section 6.3, "Eurodollar Futures") works through an explicit Act/360-to-Act/365 conversion of the form used in §2.2.
- Veronesi, P. (2010). *Fixed Income Securities: Valuation, Risk, and Risk Management.* Wiley. Chapter 2 covers day-count conventions and rate conversions in the US-conventions setting.
- James, J., & Webber, N. (2000). *Interest Rate Modelling.* Wiley.
- Hull, J., & White, A. (1990). "Pricing Interest-Rate-Derivative Securities". *The Review of Financial Studies*, 3(4), 573–592.
- Eagle Investment Systems. *Mexican Bonos Best Practices.* (Reference for the 182-day Actual/360 coupon convention.)

---

*End of document.*
