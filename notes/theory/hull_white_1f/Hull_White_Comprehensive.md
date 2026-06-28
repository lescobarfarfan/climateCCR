# Hull–White One-Factor Model: Comprehensive Reference

## Theory, Calibration, Stress Testing, and Application to the Mexican Fixed Income Market

This document consolidates all theoretical material, calibration techniques, simulation considerations, and stress-testing methodology for the Hull–White one-factor short-rate model. It also covers the practical application to the Mexican fixed income market (Bonos M, Cetes, TIIE, Udibonos, corporate bonds), including the construction of the instantaneous forward curve and treatment of long-term maturities (10, 20, 30 years). All references compiled from the source materials have been verified and integrated at the end of the document.

---

## Table of Contents

1. [Theoretical Foundation](#1-theoretical-foundation)
   - 1.1 [The Hull–White Stochastic Differential Equation](#11-the-hullwhite-stochastic-differential-equation)
   - 1.2 [Key Properties: Mean Reversion, Normality, Bond Prices](#12-key-properties-mean-reversion-normality-bond-prices)
   - 1.3 [The Function θ(t)](#13-the-function-thetat)
2. [Intuition Behind θ(t) and Use in a Bond Portfolio](#2-intuition-behind-thetat-and-use-in-a-bond-portfolio)
   - 2.1 [What θ(t) Represents](#21-what-thetat-represents)
   - 2.2 [Why a Single θ(t) Serves All Maturities](#22-why-a-single-thetat-serves-all-maturities)
   - 2.3 [The Calibration Formula for θ(t)](#23-the-calibration-formula-for-thetat)
   - 2.4 [Step-by-Step Workflow for Portfolio Pricing](#24-step-by-step-workflow-for-portfolio-pricing)
3. [Numerical Approximation of Discount Factors](#3-numerical-approximation-of-discount-factors)
   - 3.1 [The Discount Factor Formula](#31-the-discount-factor-formula)
   - 3.2 [Trapezoidal Rule](#32-trapezoidal-rule)
   - 3.3 [Rectangle Rule (Left and Right)](#33-rectangle-rule-left-and-right)
   - 3.4 [Implementation Strategy for Coupon Bonds](#34-implementation-strategy-for-coupon-bonds)
4. [Simulation Under the Real-World Measure ℙ](#4-simulation-under-the-real-world-measure-)
   - 4.1 [Risk-Neutral vs. Real-World Measures](#41-risk-neutral-vs-real-world-measures)
   - 4.2 [The Real-World SDE](#42-the-real-world-sde)
   - 4.3 [The Market Price of Interest Rate Risk λ(t)](#43-the-market-price-of-interest-rate-risk-lambdat)
   - 4.4 [Estimating λ(t)](#44-estimating-lambdat)
   - 4.5 [Numerical Procedure for ℙ-Measure Simulation](#45-numerical-procedure-for--measure-simulation)
   - 4.6 [Practical Considerations for Stress Testing](#46-practical-considerations-for-stress-testing)
5. [Calibration of Hull–White Parameters](#5-calibration-of-hullwhite-parameters)
   - 5.1 [Estimating the Mean Reversion Speed a](#51-estimating-the-mean-reversion-speed-a)
   - 5.2 [Estimating the Volatility σ](#52-estimating-the-volatility-sigma)
   - 5.3 [Calibrating θ(t) to the Initial Term Structure](#53-calibrating-thetat-to-the-initial-term-structure)
6. [Advanced Monte Carlo Techniques](#6-advanced-monte-carlo-techniques)
   - 6.1 [Antithetic Variates](#61-antithetic-variates)
   - 6.2 [Control Variates](#62-control-variates)
   - 6.3 [Importance Sampling](#63-importance-sampling)
   - 6.4 [Moment Matching](#64-moment-matching)
   - 6.5 [Quasi-Monte Carlo](#65-quasi-monte-carlo)
   - 6.6 [Multilevel Monte Carlo](#66-multilevel-monte-carlo)
7. [The Instantaneous Forward Curve f(0,t) and Calibration from TIIE](#7-the-instantaneous-forward-curve-f0t-and-calibration-from-tiie)
   - 7.1 [Definition of f(0,t)](#71-definition-of-f0t)
   - 7.2 [Standard Functional Forms and Construction](#72-standard-functional-forms-and-construction)
   - 7.3 [Using TIIE Data for Calibration](#73-using-tiie-data-for-calibration)
   - 7.4 [References for Bootstrapping](#74-references-for-bootstrapping)
8. [Long-Term Maturities (10, 20, 30 Years): Combining TIIE and Bonos M](#8-long-term-maturities-10-20-30-years-combining-tiie-and-bonos-m)
   - 8.1 [Available Long-Term Data](#81-available-long-term-data)
   - 8.2 [Complete Calibration Approach](#82-complete-calibration-approach)
   - 8.3 [References for Long-Term Curve Construction](#83-references-for-long-term-curve-construction)
   - 8.4 [Practical Implementation Notes](#84-practical-implementation-notes)
9. [Stress Testing for Market Risk: Mexican Market Application](#9-stress-testing-for-market-risk-mexican-market-application)
   - 9.1 [Market Context](#91-market-context)
   - 9.2 [Generating Stress Scenarios](#92-generating-stress-scenarios)
   - 9.3 [Adjusting the Initial Forward Curve](#93-adjusting-the-initial-forward-curve)
   - 9.4 [Importance Sampling for Targeted Terminal Rates](#94-importance-sampling-for-targeted-terminal-rates)
   - 9.5 [Parameter Shocks](#95-parameter-shocks)
   - 9.6 [Combining Views with Scenario Probabilities](#96-combining-views-with-scenario-probabilities)
   - 9.7 [Worked Example: 3-Year +5% Rate Increase](#97-worked-example-3-year-5-rate-increase)
   - 9.8 [Portfolio Valuation and Regulatory Reporting](#98-portfolio-valuation-and-regulatory-reporting)
10. [References](#10-references)

---

## 1. Theoretical Foundation

### 1.1 The Hull–White Stochastic Differential Equation

The Hull–White model (also known as the *extended Vasicek* model) is a one-factor short-rate model introduced by John Hull and Alan White in their seminal 1990 paper. It describes the evolution of the instantaneous short rate $r(t)$ under the risk-neutral measure $\mathbb{Q}$ via the stochastic differential equation:

$$
dr(t) = [\theta(t) - a\, r(t)]\,dt + \sigma\, dW(t)
$$

where:

- $r(t)$ is the short rate at time $t$,
- $a > 0$ is the speed of mean reversion,
- $\sigma > 0$ is the instantaneous volatility,
- $\theta(t)$ is a deterministic function of time chosen to fit the initial term structure of interest rates,
- $dW(t)$ is the increment of a standard Wiener process under $\mathbb{Q}$.

### 1.2 Key Properties: Mean Reversion, Normality, Bond Prices

**Mean Reversion.** The process is pulled toward the time-dependent level $\theta(t)/a$. The strength of the pull is governed by $a$: larger values produce faster reversion to the mean.

**Normality (conditional moments).** Given the filtration $\mathcal{F}_s$ at time $s < t$, the short rate $r(t)$ is normally distributed with conditional mean and variance

$$
\mathbb{E}[r(t)\mid\mathcal{F}_s] = r(s)\,e^{-a(t-s)} + \int_s^t e^{-a(t-u)}\theta(u)\,du,
$$

$$
\operatorname{Var}[r(t)\mid\mathcal{F}_s] = \frac{\sigma^2}{2a}\bigl(1 - e^{-2a(t-s)}\bigr).
$$

A consequence of normality is that the short rate may take negative values with positive probability — a known limitation of Gaussian short-rate models that, depending on the application, can be either acceptable or problematic.

**Affine bond prices.** Zero-coupon bond prices are affine in $r(t)$:

$$
P(t,T) = A(t,T)\,e^{-B(t,T)\,r(t)},
$$

with

$$
B(t,T) = \frac{1 - e^{-a(T-t)}}{a},
$$

$$
A(t,T) = \frac{P(0,T)}{P(0,t)}\exp\!\left\{ B(t,T)\,f(0,t) - \frac{\sigma^2}{4a}\,B(t,T)^2\bigl(1 - e^{-2at}\bigr) \right\}.
$$

This affine form is one of the central appeals of the model: bond prices, caps, floors, and European swaptions admit closed-form or quasi-closed-form pricing formulas, while the model retains enough flexibility to fit any initial yield curve exactly.

### 1.3 The Function θ(t)

The function $\theta(t)$ is determined so that the model reproduces the observed initial instantaneous forward curve $f(0,t)$:

$$
\theta(t) = \frac{\partial f(0,t)}{\partial T} + a\,f(0,t) + \frac{\sigma^2}{2a}\bigl(1 - e^{-2at}\bigr).
$$

This formula is derived from the no-arbitrage requirement that today's model-implied zero-coupon bond prices match observed market prices for all maturities.

---

## 2. Intuition Behind θ(t) and Use in a Bond Portfolio

### 2.1 What θ(t) Represents

A common point of confusion is whether $\theta(t)$ should be viewed as a maturity-dependent quantity (with different values for different bonds in the portfolio). It is **not**. The function $\theta(t)$ is a single deterministic function of the *current calendar time* $t$. It is calibrated **once** to the entire initial yield curve observed today, and the same function then drives the dynamics for all subsequent simulations regardless of which bond maturity one wishes to price.

### 2.2 Why a Single θ(t) Serves All Maturities

The short rate $r(t)$ is a single stochastic process that drives the entire term structure. From one simulated path of $r(t)$ one can compute discount factors for **any** future date and, therefore, price bonds of **all** maturities. The function $\theta(t)$ is the "tuning knob" that makes the model arbitrage-free with respect to current market prices.

Mathematically, $\theta(t)$ is chosen so that the risk-neutral expectation matches observed zero-coupon bond prices:

$$
P^M(0,T) = \mathbb{E}^{\mathbb{Q}}\!\left[\exp\!\left(-\int_0^T r(s)\,ds\right)\right] \quad \text{for all } T.
$$

This condition must hold for **every** maturity $T$, and a single $\theta(t)$ function (together with parameters $a$ and $\sigma$) is sufficient to satisfy all these constraints simultaneously.

### 2.3 The Calibration Formula for θ(t)

Given the initial instantaneous forward curve $f(0,t)$:

$$
\theta(t) = \frac{\partial f(0,t)}{\partial T} + a\,f(0,t) + \frac{\sigma^2}{2a}\bigl(1 - e^{-2at}\bigr).
$$

Once calibrated, this $\theta(t)$ is used in the SDE for all future simulations, regardless of which bonds are intended to be priced.

**Key takeaway.** One does **not** simulate different $\theta$ processes for different bond maturities. One simulates **one** $r(t)$ process, and from it derives discount factors for all cash-flow dates.

### 2.4 Step-by-Step Workflow for Portfolio Pricing

1. Calibrate $\theta(t)$ using the full yield curve.
2. Simulate $N$ paths of $r(t)$ from $t=0$ to the longest bond maturity in the portfolio.
3. For each path, compute discount factors to every cash-flow date (using numerical integration; see Section 3).
4. Price each bond on that path by discounting its cash flows.
5. Aggregate to obtain the portfolio value distribution.

---

## 3. Numerical Approximation of Discount Factors

### 3.1 The Discount Factor Formula

From a simulated path of the short rate, the discount factor for a cash flow occurring at time $T$ is

$$
D(0,T) = \exp\!\left(-\int_0^T r(s)\,ds\right).
$$

In discrete-time simulation we have values $r(t_0), r(t_1), \ldots, r(t_N)$ at times $t_0 = 0, t_1, \ldots, t_N = T$. The integral must therefore be approximated numerically.

### 3.2 Trapezoidal Rule

The trapezoidal rule averages values at the beginning and end of each interval:

$$
\int_0^T r(s)\,ds \approx \sum_{i=0}^{N-1} \frac{r(t_i) + r(t_{i+1})}{2}\,\Delta t_i,
$$

where $\Delta t_i = t_{i+1} - t_i$.

**Why the trapezoidal rule is preferred.** For smooth integrands its error is $O(\Delta t^2)$, compared to $O(\Delta t)$ for the rectangle rule. In interest-rate simulation, the trapezoidal rule provides better accuracy for a given time step, which is particularly important when pricing instruments sensitive to the entire path of rates.

### 3.3 Rectangle Rule (Left and Right)

A simpler but less accurate alternative:

$$
\int_0^T r(s)\,ds \approx \sum_{i=0}^{N-1} r(t_i)\,\Delta t_i \quad \text{(left rectangle)},
$$

$$
\int_0^T r(s)\,ds \approx \sum_{i=1}^{N} r(t_i)\,\Delta t_{i-1} \quad \text{(right rectangle)}.
$$

### 3.4 Implementation Strategy for Coupon Bonds

For each simulated path:

1. Maintain a cumulative integral $I(t_i) = \int_0^{t_i} r(s)\,ds$ as one progresses through time steps.
2. Update using the chosen quadrature rule.
3. At any cash-flow date $t_j$, the discount factor is $\exp(-I(t_j))$.

For bonds with multiple cash flows (coupon bonds), discount factors to every payment date are required. One can either store the cumulative integral at each time step or recompute integrals as needed.

**Reference.** Yasuoka (2018) provides comprehensive coverage of numerical procedures for interest-rate models, including integration techniques for discount-factor calculation in Monte Carlo simulation.

---

## 4. Simulation Under the Real-World Measure ℙ

### 4.1 Risk-Neutral vs. Real-World Measures

The Hull–White SDE in Section 1.1 is written under the **risk-neutral measure** $\mathbb{Q}$, used for pricing derivatives. Under $\mathbb{Q}$, all assets grow at the risk-free rate $r(t)$, and the drift contains $\theta(t)$ calibrated to today's yield curve.

For risk-management applications — particularly stress testing, scenario analysis, and economic capital — one often needs simulations under the **real-world (physical) measure** $\mathbb{P}$, which reflects actual historical dynamics of interest rates rather than the risk-neutral pricing dynamics.

### 4.2 The Real-World SDE

Under the real-world measure, the Hull–White SDE becomes

$$
dr(t) = \bigl[\theta(t) - a\,r(t) + \lambda(t)\,\sigma\bigr]\,dt + \sigma\, dW^{\mathbb{P}}(t),
$$

where $\lambda(t)$ is the **market price of interest rate risk**. This term adjusts the drift to reflect the risk premium demanded by investors.

### 4.3 The Market Price of Interest Rate Risk λ(t)

The market price of risk $\lambda(t)$ represents the excess return per unit of risk and links the two measures via the Girsanov transformation:

$$
dW^{\mathbb{Q}}(t) = dW^{\mathbb{P}}(t) - \lambda(t)\,dt.
$$

Key properties:

- $\lambda(t)$ can be time-dependent or constant.
- Empirical studies frequently find a **negative price tendency** for interest rate risk, meaning $\lambda(t)$ tends to be negative in many markets.
- For the Hull–White model, estimation of $\lambda(t)$ typically uses historical data on bond yields or forward rates.

### 4.4 Estimating λ(t)

Yasuoka (2018) presents two approaches for estimating $\lambda(t)$ in the Hull–White framework:

1. **Short-rate dynamics approach.** Analyze historical time series of short rates to extract the drift under $\mathbb{P}$.
2. **Forward-rate dynamics approach.** Work within the HJM framework and estimate $\lambda(t)$ from the historical evolution of the entire forward curve.

A common practical simplification is to assume $\lambda$ is constant. This constant can be estimated as

$$
\lambda = \frac{\mu_{\text{excess}}}{\sigma},
$$

where $\mu_{\text{excess}}$ is the historical average excess return of a long-term bond over the short rate.

### 4.5 Numerical Procedure for ℙ-Measure Simulation

1. **Calibrate $\theta(t)$** to the current yield curve using the standard risk-neutral formula. This step is unchanged, because $\theta(t)$ enforces no-arbitrage with respect to today's prices.
2. **Estimate $\lambda$** from historical data: collect historical time series of interest rates, estimate the drift under $\mathbb{P}$ (for example via maximum likelihood applied to a Vasicek model), and infer $\lambda$ from the difference between the $\mathbb{P}$ and $\mathbb{Q}$ drifts.
3. **Simulate paths** using the adjusted SDE:
   $$
   r(t+\Delta t) = r(t) + \bigl[\theta(t) - a\,r(t) + \lambda\sigma\bigr]\,\Delta t + \sigma\,\sqrt{\Delta t}\,\varepsilon.
   $$
4. **For stress testing**, combine the $\mathbb{P}$-measure simulation with shocked parameters or initial curves to create *stressed real-world* scenarios.

### 4.6 Practical Considerations for Stress Testing

For regulatory stress testing (for example under CNBV or Basel guidelines), a common approach is to:

- Use $\mathbb{P}$-measure dynamics for the central (baseline) scenario.
- Apply deterministic shocks to the initial yield curve and/or parameters for stressed scenarios.
- Recalibrate $\theta(t)$ under each stressed initial curve to maintain no-arbitrage.

This approach, detailed in Yasuoka (2018), allows the combination of historically realistic dynamics with specific stress assumptions.

---

## 5. Calibration of Hull–White Parameters

Calibration entails estimating the parameters $a$ (mean reversion speed), $\sigma$ (volatility), and the function $\theta(t)$ (which ensures the model fits the current term structure).

### 5.1 Estimating the Mean Reversion Speed a

#### Linear Regression on Historical Short Rates (AR(1) approximation)

The discrete-time Hull–White SDE (under the assumption of constant $\theta$, equivalent to a Vasicek model) can be approximated as

$$
r_{t+\Delta t} - r_t = a(\mu - r_t)\,\Delta t + \sigma\,\sqrt{\Delta t}\,\varepsilon_t,
$$

where $\mu$ is the long-term mean. Rearranging,

$$
r_{t+\Delta t} = a\mu\,\Delta t + (1 - a\,\Delta t)\,r_t + \sigma\,\sqrt{\Delta t}\,\varepsilon_t,
$$

an AR(1) process. Regressing $r_{t+\Delta t}$ on $r_t$ via

$$
r_{t+\Delta t} = \alpha + \beta r_t + \eta_t
$$

gives

$$
a = (1 - \beta)/\Delta t,\qquad \mu = \alpha/(1 - \beta).
$$

**Reference.** James & Webber (2000).

#### Maximum Likelihood Estimation (MLE)

For the Vasicek model the *exact* conditional distribution of $r_{t+\Delta t}$ given $r_t$ is normal with

$$
\mathbb{E}[r_{t+\Delta t}\mid r_t] = r_t\,e^{-a\,\Delta t} + \mu\,(1 - e^{-a\,\Delta t}),
$$

$$
\operatorname{Var}[r_{t+\Delta t}\mid r_t] = \frac{\sigma^2}{2a}\bigl(1 - e^{-2a\,\Delta t}\bigr).
$$

The log-likelihood for a time series $\{r_{t_i}\}$ is

$$
\mathcal{L} = -\frac{n}{2}\ln(2\pi) - \frac{1}{2}\sum_{i=1}^{n-1}\!\left[\ln(\sigma_i^2) + \frac{(r_{t_{i+1}} - \mu_i)^2}{\sigma_i^2}\right],
$$

where $\mu_i$ and $\sigma_i^2$ are the conditional moments above. Maximizing it yields estimates for $a$, $\mu$, $\sigma$.

**Reference.** Brigo & Mercurio (2006).

### 5.2 Estimating the Volatility σ

#### Historical Volatility

Given short-rate changes $\Delta r_t = r_{t+\Delta t} - r_t$, the volatility can be estimated as

$$
\hat{\sigma} = \sqrt{\frac{1}{(n-1)\,\Delta t}\sum_{t=1}^{n-1}\bigl(\Delta r_t - \overline{\Delta r}\bigr)^2}.
$$

This assumes homoskedasticity and approximately zero drift over short intervals.

#### GARCH Models

For time-varying volatility, fit a GARCH(1,1) to the residuals:

$$
\sigma_t^2 = \omega + \alpha\,\varepsilon_{t-1}^2 + \beta\,\sigma_{t-1}^2.
$$

The unconditional volatility is $\sigma = \sqrt{\omega/(1 - \alpha - \beta)}$.

**Reference.** Bollerslev (1986).

### 5.3 Calibrating θ(t) to the Initial Term Structure

The function $\theta(t)$ is chosen so that the model reproduces the observed market bond prices $P^M(0,T)$ for all $T$. Bond prices in the Hull–White model are given by

$$
P(0,T) = A(0,T)\,e^{-B(0,T)\,r_0}
$$

with $B(0,T) = (1 - e^{-aT})/a$. Equivalently, one can use the relationship between $\theta(t)$ and the instantaneous forward rate:

$$
\theta(t) = \frac{\partial f(0,t)}{\partial T} + a\,f(0,t) + \frac{\sigma^2}{2a}\bigl(1 - e^{-2at}\bigr).
$$

Calibration steps:

1. Obtain the market instantaneous forward curve $f(0,t)$ from observed bond prices or swap rates.
2. Compute the derivative $\partial f(0,t)/\partial T$ numerically (for example via central finite differences).
3. Plug into the formula to obtain $\theta(t)$ at discrete tenors, then interpolate.

If only discrete bond prices are available, one can solve for $\theta(t)$ by inverting the bond pricing formula. A common approach is to assume $\theta(t)$ is piecewise constant and solve recursively.

**Reference.** Hull & White (1990).

---

## 6. Advanced Monte Carlo Techniques

Standard Euler–Maruyama Monte Carlo suffers from both discretization error and sampling error. The techniques below improve efficiency, accuracy, or both.

### 6.1 Antithetic Variates

**Principle.** For each path generated using random increments $\varepsilon_i$, generate a second path with $-\varepsilon_i$. The resulting negative correlation reduces variance.

**Mathematical foundation.** If $\hat{\theta}_1$ and $\hat{\theta}_2$ are two estimators with the same variance $\sigma^2$ and correlation $\rho$, the average $\hat{\theta} = \tfrac{1}{2}(\hat{\theta}_1 + \hat{\theta}_2)$ has variance

$$
\operatorname{Var}(\hat{\theta}) = \frac{1}{4}\!\bigl[\operatorname{Var}(\hat{\theta}_1) + \operatorname{Var}(\hat{\theta}_2) + 2\,\operatorname{Cov}(\hat{\theta}_1, \hat{\theta}_2)\bigr] = \frac{\sigma^2}{2}(1 + \rho).
$$

For perfect negative correlation ($\rho = -1$) the variance becomes zero.

**Reference.** Hammersley & Morton (1956).

### 6.2 Control Variates

**Principle.** Use a known expectation $\mathbb{E}[X]$ of a related quantity to correct the estimator of $Y$:

$$
Y_{\text{control}} = Y - \beta\,(X - \mathbb{E}[X]).
$$

The optimal coefficient is

$$
\beta^{*} = \frac{\operatorname{Cov}(Y,X)}{\operatorname{Var}(X)},
$$

yielding a variance-reduction factor of $1 - \rho_{YX}^2$ where $\rho_{YX}$ is the correlation between $Y$ and $X$.

**Reference.** Lavenberg & Welch (1981).

### 6.3 Importance Sampling

**Principle.** Change the probability measure to focus simulation effort on important regions of the sample space, then reweight by the Radon–Nikodym derivative:

$$
\mathbb{E}_{\mathbb{P}}[h(X)] = \mathbb{E}_{\mathbb{Q}}\!\left[h(X)\,\frac{d\mathbb{P}}{d\mathbb{Q}}\right].
$$

For a Girsanov change of measure with drift adjustment $\gamma(t)$,

$$
\frac{d\mathbb{P}}{d\mathbb{Q}} = \exp\!\left(-\int_0^T \gamma(t)\,dW(t) - \frac{1}{2}\int_0^T \gamma(t)^2\,dt\right).
$$

**Reference.** Glynn & Iglehart (1989).

### 6.4 Moment Matching

**Principle.** Adjust simulated paths so that their sample moments exactly match theoretical moments. Given a sample $\{X_i\}_{i=1}^n$ with sample mean $\bar X$ and sample standard deviation $S$,

$$
X_i^{\text{adj}} = \mu + \frac{\sigma}{S}\,(X_i - \bar X),
$$

where $\mu$ and $\sigma$ are the target theoretical moments.

**Reference.** Barraquand (1995).

### 6.5 Quasi-Monte Carlo

**Principle.** Replace pseudo-random numbers with low-discrepancy sequences (Sobol, Halton, etc.) to obtain faster convergence. The Koksma–Hlawka inequality bounds the integration error:

$$
\left|\frac{1}{N}\sum_{i=1}^N f(x_i) - \int_{[0,1]^d} f(u)\,du\right| \leq V(f)\,D_N^{*}(x_1,\ldots,x_N),
$$

where $V(f)$ is the total variation of $f$ and $D_N^{*}$ is the star-discrepancy. QMC sequences attain $D_N^{*} = O((\log N)^d / N)$, compared with $O(1/\sqrt{N})$ for plain Monte Carlo.

**Reference.** Niederreiter (1992).

### 6.6 Multilevel Monte Carlo

**Principle.** Combine simulations at different discretization levels to achieve optimal computational complexity. Express the expectation on the finest level $L$ as a telescoping sum:

$$
\mathbb{E}[P_L] = \mathbb{E}[P_0] + \sum_{\ell=1}^L \mathbb{E}[P_\ell - P_{\ell-1}].
$$

Total cost is minimized by allocating samples inversely proportional to level variance:

$$
M_\ell \propto \sqrt{V_\ell / C_\ell},
$$

where $V_\ell = \operatorname{Var}(P_\ell - P_{\ell-1})$ and $C_\ell$ is the cost per sample at level $\ell$.

**Reference.** Giles (2008).

---

## 7. The Instantaneous Forward Curve f(0,t) and Calibration from TIIE

### 7.1 Definition of f(0,t)

The instantaneous forward rate is defined from zero-coupon bond prices via

$$
f(0,t) = -\frac{\partial}{\partial T}\ln P(0,T)\bigg|_{T=t}.
$$

It is **not** directly observable in the market; it must be constructed from market instruments.

### 7.2 Standard Functional Forms and Construction

There is no single "standard" form. In practice, $f(0,t)$ is obtained by:

- **Bootstrapping** from discrete market rates (TIIE, swaps, government and corporate bonds);
- **Interpolation** of the bootstrapped curve (cubic splines, Nelson–Siegel, Svensson, monotone convex) to produce a continuous curve;
- **Smoothing** to ensure differentiability (which is required to compute $\partial f/\partial T$ for $\theta(t)$).

**References.** Hagan & West (2006), Nelson & Siegel (1987), Svensson (1994).

### 7.3 Using TIIE Data for Calibration

TIIE rates (28, 91, and 182 days) are **term rates**, not instantaneous. To use them:

1. Treat TIIE as floating rates consistent with swap-market conventions (Hull & White, 2014).
2. Bootstrap the zero-coupon yield curve from TIIE together with other instruments (Cetes for the very short end, swaps and Bonos M for medium and long ends).
3. From the continuous zero-coupon curve, compute $f(0,t)$ via numerical differentiation.

**Key insight.** TIIE data is essential and correct for the short end of the curve, but it must be processed through a bootstrapping procedure before being used in the Hull–White calibration formula.

### 7.4 References for Bootstrapping

| Reference | Description | Relevance |
|:---|:---|:---|
| Hagan, P., & West, G. (2006). "Interpolation Methods for Curve Construction". *Applied Mathematical Finance*, 13(2), 89–129. | Comprehensive survey of interpolation methods | Standard reference for bootstrapping techniques |
| Hull, J., & White, A. (2014). "Interest Rate Models: Theory and Practice". *Journal of Derivatives*. | Discusses construction of discount curves including treatment of floating rates | Cited in Mexican market context |
| Banco de México. *Disposiciones de Carácter General Aplicables a las Instituciones de Crédito* (Circular Única de Bancos). | Official documentation including methodology for TIIE | Primary source for Mexican market data interpretation |
| Ron, U. (2000). "A Practical Guide to Swap Curve Construction". *Bank of Canada Working Paper* No. 2000-17. | Step-by-step guide to bootstrapping swap curves | Practical methodology applicable to TIIE swaps |
| Ametrano, F., & Bianchetti, M. (2013). "Everything You Always Wanted to Know About Multiple Interest Rate Curve Bootstrapping". *SSRN Electronic Journal*. DOI: 10.2139/ssrn.2219548. | Modern multi-curve bootstrapping in the post-crisis environment | Relevant for tenor-basis effects and OIS-discounting |

---

## 8. Long-Term Maturities (10, 20, 30 Years): Combining TIIE and Bonos M

### 8.1 Available Long-Term Data

| Maturity | Data Source | Availability |
|:---|:---|:---|
| 1–3 years | Bonos M, TIIE swaps | Daily quotes |
| 5 years | Bonos M, TIIE swaps | Daily quotes |
| 7 years | Bonos M | Daily quotes |
| 10 years | Bonos M, OECD data | Daily quotes |
| 15 years | Bonos M | Daily quotes |
| 20 years | Bonos M | Daily quotes |
| 30 years | Bonos M | Daily quotes |

### 8.2 Complete Calibration Approach

**Step 1 — Short end (up to ~182 days).** Bootstrap using TIIE rates at 28, 91, and 182 days, optionally complemented with Cetes auction yields.

**Step 2 — Medium to long end (1 to 30 years).** Use Bonos M yields at standard tenors. Convert coupon-bearing yields to zero-coupon rates if necessary (i.e., strip the coupons).

**Step 3 — Interpolation.** Apply a robust interpolation method (cubic splines, Nelson–Siegel, Svensson, or monotone convex) to obtain a continuous zero-coupon curve.

**Step 4 — Compute $f(0,t)$.** From the continuous zero-coupon curve, derive instantaneous forward rates and their derivatives, then plug them into the Hull–White $\theta(t)$ formula.

### 8.3 References for Long-Term Curve Construction

| Reference | Description | Relevance |
|:---|:---|:---|
| Nelson, C., & Siegel, A. (1987). "Parsimonious Modeling of Yield Curves". *Journal of Business*, 60(4), 473–489. | Parametric model fitting yield curves with few parameters | Widely used both in academia and practice |
| Svensson, L. (1994). "Estimating and Interpreting Forward Interest Rates". *IMF Working Paper* No. 94/114. | Extension of Nelson–Siegel with two additional parameters | Standard at many central banks |
| Banco de México. "Metodología para la determinación de la curva de rendimientos de los Bonos M". | Official methodology for Bonos M yield curve | Primary source for Mexican government bond curve construction |
| Hagan, P., & West, G. (2008). "Methods for Constructing a Yield Curve". *Wilmott Magazine*, May 2008, 70–81. | Practical comparison of interpolation methods | Good overview of pros and cons |
| Andersen, L., & Piterbarg, V. (2010). *Interest Rate Modeling*. Atlantic Financial Press. | Comprehensive treatment of curve construction and interest-rate modeling | Advanced reference |

### 8.4 Practical Implementation Notes

- TIIE rates can be downloaded from Banco de México's *Sistema de Información Económica* (SIE; for example, series SF43783 for 28-day TIIE).
- Bonos M yields can be obtained from financial data providers or public sources (Investing.com, OECD).
- After combining all data points, bootstrap the zero-coupon curve using a chosen interpolation method.
- Derive $f(0,t)$ numerically and plug it into the $\theta(t)$ formula.
- For long-term simulation, ensure that the mean-reversion parameter $a$ and volatility $\sigma$ are consistent with historical data covering the relevant long-term tenors.

---

## 9. Stress Testing for Market Risk: Mexican Market Application

### 9.1 Market Context

The Mexican fixed-income market has a number of specific characteristics relevant to risk modelling:

- **Government bonds.** *Bonos M* are fixed-rate, peso-denominated coupon bonds; *Cetes* are zero-coupon Treasury bills; *Udibonos* are inflation-linked bonds (denominated in UDIs).
- **Interbank rate.** TIIE (Tasa de Interés Interbancaria de Equilibrio) is the Mexican equivalent of (former) LIBOR-style benchmarks, available at 28-, 91-, and 182-day tenors.
- **Corporate bonds.** Various tenors and credit qualities, with credit spreads over the Bonos M curve.
- **Sovereign curve.** The Bonos M curve serves as the benchmark from which other Mexican fixed-income instruments are typically priced.
- **Regulators.** The Comisión Nacional Bancaria y de Valores (CNBV) and Banco de México set the regulatory framework, including stress-testing requirements.

### 9.2 Generating Stress Scenarios

Stress testing aims to assess the sensitivity of a portfolio to extreme but plausible market movements. Common stress types, aligned with CNBV and Basel guidelines, include:

- **Parallel shifts.** For example, +200 bps (Banxico tightening) or –100 bps (easing).
- **Non-parallel shifts.** Steepening (short rates +100 bps, long rates +300 bps) or flattening (short rates +300 bps, long rates +100 bps).
- **Volatility shock.** Increase $\sigma$ by, say, 50%, simulating market turmoil.
- **Mean-reversion shock.** Decrease $a$ by, say, 50%, simulating a regime change with greater rate persistence.

The next subsections describe alternative ways of incorporating such views into the simulated paths.

### 9.3 Adjusting the Initial Forward Curve

The most direct approach is to shock the initial yield curve used to compute $\theta(t)$. To produce paths whose rates are higher on average over a given horizon, shift the initial forward curve upward by a deterministic amount (for example +500 bps for a +5% scenario) and recalibrate $\theta(t)$. Simulated paths then reflect the stressed initial curve. This approach is consistent with the model's no-arbitrage property: the drift $\theta(t)$ ensures that expected future rates match the (stressed) forward curve.

**Procedure.**

1. Start with the current market forward curve $f(0,t)$.
2. Apply a parallel shift to obtain a stressed forward curve $f^{*}(0,t) = f(0,t) + \text{shift}$.
3. Compute the stressed $\theta^{*}(t)$ using the calibration formula with $f^{*}(0,t)$.
4. Simulate paths under the stressed $\theta^{*}(t)$.

This produces trajectories where the *expected* short rate at each future time is shifted by the chosen amount, while individual paths still exhibit volatility around that mean. A parallel shift is the simplest choice; non-parallel shifts (steepening, flattening, or hump shocks) can also be applied.

### 9.4 Importance Sampling for Targeted Terminal Rates

If one specifically wants the *terminal* short rate $r(T)$ to have a higher mean (for example $r_0 + 0.05$), importance sampling can be used. This involves changing the drift of the Brownian motion to make paths ending near the target more likely, then reweighting.

For the Hull–White model, the distribution of $r(T)$ given $r_0$ is normal with known mean $\mu_T$ and variance $\sigma_T^2$. To shift the mean to a target $\mu_T^{\text{stress}}$, one can add a drift adjustment $\gamma$ to the Brownian motion:

$$
dW^{*}(t) = dW(t) + \gamma(t)\,dt.
$$

The Radon–Nikodym derivative for the change of measure is

$$
\frac{d\mathbb{P}}{d\mathbb{P}^{*}} = \exp\!\left(-\int_0^T \gamma(t)\,dW(t) - \frac{1}{2}\int_0^T \gamma(t)^2\,dt\right).
$$

Choosing $\gamma(t)$ constant such that $\mathbb{E}^{*}[r(T)] = \mu_T^{\text{stress}}$ yields, in simplified form,

$$
\gamma = \frac{\mu_T^{\text{stress}} - \mu_T}{\sigma_T^2}\cdot\frac{2a}{1 - e^{-aT}}\,e^{-aT}.
$$

Paths are then simulated under the stressed measure and weighted by the likelihood ratio.

**Reference.** Glasserman (2004).

### 9.5 Parameter Shocks

Another approach is to shock the model parameters directly. For example, increasing the mean-reversion level (through $\theta$) or decreasing the mean-reversion speed $a$ can produce paths that drift higher. However, such shocks may be inconsistent with the initial curve. To maintain no-arbitrage, any parameter change should be accompanied by recalibration of $\theta$ to the (possibly shocked) initial curve. Shocking $a$ and $\sigma$ while keeping the initial curve fixed leads to a different $\theta(t)$, which may produce unexpected effects.

**Practical note.** In regulatory stress testing (CNBV, Basel), scenarios are often defined as parallel shifts or as changes in the level, slope, and curvature of the yield curve. The most straightforward implementation is to apply the shift to the initial curve and recalibrate.

### 9.6 Combining Views with Scenario Probabilities

For a comprehensive stress test, one can define multiple scenarios with associated probabilities. For each scenario, the forward curve is adjusted accordingly and paths are simulated. Results are then aggregated using the scenario probabilities, giving a probability-weighted view of portfolio risk.

### 9.7 Worked Example: 3-Year +5% Rate Increase

Suppose the goal is to simulate a scenario in which Mexican interest rates are on average 5% higher over the next three years. The simplest implementation is:

1. **Obtain the current Mexican yield curve** (Bonos M, Cetes, TIIE swap rates), bootstrap zero-coupon rates, and compute instantaneous forward rates $f(0,t)$ for $t$ up to 3 years.
2. **Apply the stress.** Define a stressed forward curve $f^{*}(0,t) = f(0,t) + 0.05$ (parallel shift). Non-parallel variations can be substituted as needed.
3. **Recalibrate $\theta^{*}(t)$** using the stressed forward curve:
   - Compute $\partial f^{*}(0,t)/\partial T$ numerically.
   - $\theta^{*}(t) = \partial f^{*}(0,t)/\partial T + a\,f^{*}(0,t) + \tfrac{\sigma^2}{2a}(1 - e^{-2at})$.
4. **Simulate paths** under the stressed $\theta^{*}$ using Euler–Maruyama or exact simulation (the Hull–White model has a closed-form transition density, so exact simulation is possible without discretization error).
5. **Value the portfolio** under each simulated path to obtain the distribution of losses.
6. **Compare with the baseline** (unstressed) simulation to quantify impact.

**Why this works.** The Hull–White model is arbitrage-free by construction; changing the initial curve and recalibrating $\theta$ produces a new arbitrage-free world where expected future rates are higher.

**Alternative.** Importance sampling targeting a higher *terminal* rate (Section 9.4) is also possible, but for regulatory stress tests the shifted-curve method is standard.

**References.** Basel Committee (2019); Jorion (2006).

### 9.8 Portfolio Valuation and Regulatory Reporting

For each simulated path one computes discount factors (Section 3) and prices each instrument in the portfolio (e.g., Bonos M, Cetes, corporate bonds, Udibonos), aggregates to a portfolio value, and computes the P&L distribution against the baseline. Common risk metrics derived from the simulated distribution include:

- Value at Risk at 95% and 99% confidence levels.
- Expected Shortfall (Conditional VaR).
- Maximum loss across paths.
- Mean and standard deviation of P&L.

Mexican regulatory reporting (under CNBV's *Disposiciones de Carácter General en Materia de Administración de Riesgos*, including the stress-test requirements often discussed in the context of *Artículo 282*) typically requires:

- A description of the portfolio composition.
- VaR and Expected Shortfall under the baseline scenario.
- Impact of pre-defined stress scenarios (parallel shifts, non-parallel shifts, volatility shocks).
- Comparison against capital and triggers, plus management recommendations.

The same framework is consistent with the Basel Committee's *Minimum capital requirements for market risk* (2019).

---

## 10. References

### Original Papers

1. Hull, J., & White, A. (1990). "Pricing Interest-Rate-Derivative Securities". *The Review of Financial Studies*, 3(4), 573–592. https://academic.oup.com/rfs/article-abstract/3/4/573/1601187
2. Hull, J., & White, A. (1994). "Numerical procedures for implementing term structure models I: Single-factor models". *Journal of Derivatives*, 2(1), 7–16.
3. Hull, J., & White, A. (1996). "Using Hull-White interest rate trees". *Journal of Derivatives*, 3(3), 26–36.
4. Hull, J., & White, A. (2014). "Interest Rate Models: Theory and Practice". *Journal of Derivatives*.

### Books

5. Brigo, D., & Mercurio, F. (2006). *Interest Rate Models – Theory and Practice* (2nd ed.). Springer Finance. ISBN: 978-3-540-22149-4.
6. Glasserman, P. (2004). *Monte Carlo Methods in Financial Engineering*. Springer. ISBN: 978-0-387-00451-8.
7. Andersen, L. B. G., & Piterbarg, V. V. (2010). *Interest Rate Modeling*. Atlantic Financial Press.
8. James, J., & Webber, N. (2000). *Interest Rate Modelling*. Wiley.
9. Yasuoka, T. (2018). *Interest Rate Modeling for Risk Management: Market Price of Interest Rate Risk* (2nd ed.). Bentham Science Publishers. ISBN: 978-1-68108-690-3 (Print); 978-1-68108-689-7 (Online). DOI: 10.2174/97816810868971180101.
   - Chapter 8: "Real-World Model in the Hull–White Model", pp. 175–194.
   - Chapter 10: "Numerical Examples", pp. 235–279.
10. Jorion, P. (2006). *Value at Risk: The New Benchmark for Managing Financial Risk* (3rd ed.). McGraw-Hill.

### Advanced Monte Carlo Techniques

11. Hammersley, J. M., & Morton, K. W. (1956). "A new Monte Carlo technique: antithetic variates". *Mathematical Proceedings of the Cambridge Philosophical Society*, 52(3), 449–475.
12. Lavenberg, S. S., & Welch, P. D. (1981). "A perspective on the use of control variables to increase the efficiency of Monte Carlo simulations". *Management Science*, 27(3), 322–335.
13. Glynn, P. W., & Iglehart, D. L. (1989). "Importance sampling for stochastic simulations". *Management Science*, 35(11), 1367–1392.
14. Barraquand, J. (1995). "Numerical valuation of high dimensional multivariate European securities". *Management Science*, 41(12), 1882–1891.
15. Niederreiter, H. (1992). *Random Number Generation and Quasi-Monte Carlo Methods*. SIAM. ISBN: 978-0-89871-295-7.
16. Giles, M. B. (2008). "Multilevel Monte Carlo path simulation". *Operations Research*, 56(3), 607–617.

### Yield Curve Construction and Bootstrapping

17. Hagan, P. S., & West, G. (2006). "Interpolation Methods for Curve Construction". *Applied Mathematical Finance*, 13(2), 89–129. DOI: 10.1080/13504860500396032.
18. Hagan, P. S., & West, G. (2008). "Methods for Constructing a Yield Curve". *Wilmott Magazine*, May 2008, 70–81.
19. Nelson, C. R., & Siegel, A. F. (1987). "Parsimonious Modeling of Yield Curves". *Journal of Business*, 60(4), 473–489.
20. Svensson, L. E. O. (1994). "Estimating and Interpreting Forward Interest Rates: Sweden 1992–1994". *IMF Working Paper* No. 94/114.
21. Ron, U. (2000). "A Practical Guide to Swap Curve Construction". *Bank of Canada Working Paper* No. 2000-17.
22. Ametrano, F. M., & Bianchetti, M. (2013). "Everything You Always Wanted to Know About Multiple Interest Rate Curve Bootstrapping But Were Afraid to Ask". *SSRN Electronic Journal*. DOI: 10.2139/ssrn.2219548.

### Calibration and Estimation

23. Bollerslev, T. (1986). "Generalized autoregressive conditional heteroskedasticity". *Journal of Econometrics*, 31(3), 307–327.

### Mexican Market

24. Banco de México. *Sistema de Información Económica (SIE)*. https://www.banxico.org.mx/SieInternet/
25. Banco de México. *Disposiciones de Carácter General Aplicables a las Instituciones de Crédito* (Circular Única de Bancos).
26. Banco de México. "Metodología para la determinación de la curva de rendimientos de los Bonos M".
27. Sidaoui, J., et al. (2010). "The Mexican fixed income market: Structure and participants". *BIS Papers*, No. 53.
28. Investing.com. "Mexico Government Bonds". https://www.investing.com/rates-bonds/mexico-government-bonds
29. OECD. "Long-Term Government Bond Yields: 10-year: Main (Including Benchmark) for Mexico". https://data.oecd.org
30. CEIC Data. "Mexico Treasury Bill and Government Securities Rates: Annual". https://www.ceicdata.com

### Risk Management and Regulatory Standards

31. Basel Committee on Banking Supervision (2019). *Minimum capital requirements for market risk*. Bank for International Settlements.
32. CNBV. *Disposiciones de Carácter General en Materia de Administración de Riesgos*. Comisión Nacional Bancaria y de Valores.

### Glossaries and Online Resources

33. Lund University Mathematical Statistics Glossary. "Hull-White model". https://www.maths.lth.se/matstat/research/mathematicalfinance/glossary/

---

*End of compendium.*

## Related
[[MKT_MOC]] · Home: [[_INDEX]]

#arm/mkt #type/theory
