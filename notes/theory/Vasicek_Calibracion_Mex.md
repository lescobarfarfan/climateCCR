# Calibration of the Vasicek Model under the Real-World Measure ($\mathbb{P}$)
## Practical Guide for the Mexican Market using F-TIIE

This document compiles a step-by-step workflow for calibrating the Vasicek model's parameters ($\kappa$, $\theta$, $\sigma$) exclusively under the **Real-World measure** ($\mathbb{P}$), suitable for forecasting, scenario analysis, and risk management — not for pricing derivatives.

The guide is based on the academic standard *"Interest Rate Models – Theory and Practice"* by Brigo and Mercurio, with practical adaptations for the Mexican market using the F-TIIE overnight funding rate.

---

## 1. Model & Data Assumptions (Real‑World Measure)

Under $\mathbb{P}$, the Vasicek SDE is:

$$
dr_t = \kappa (\theta - r_t) dt + \sigma dW_t
$$

**Assumptions for calibration:**
- **Stationarity**: $\kappa > 0$ (mean‑reverting process).
- **Observed data**: Discrete, equally spaced observations $\{r_{t_1}, r_{t_2}, \dots, r_{t_n}\}$ with constant time step $\Delta t$ (e.g., daily, monthly).
- **Normality**: The transition density of $r_{t+\Delta t} \mid r_t$ is Gaussian (exact property of Vasicek).
- **No measurement error**: The observed rate is the true instantaneous rate (or a very close proxy).

---

## 2. Choice of Short Rate Proxy for the Mexican Market

For a Real-World Vasicek calibration in Mexico, the **Overnight TIIE Funding Rate (F-TIIE)** is the most appropriate proxy for the instantaneous short rate $r_t$.

### What is F-TIIE?
- **Full Name**: *Tasa de Interés Interbancaria de Equilibrio de Fondeo*.
- **Tenor**: Overnight (1 business day).
- **Administrator**: Banco de México (Banxico).
- **Nature**: A **secured** overnight funding rate, designed as the Mexican equivalent of SOFR or SONIA.

### Why it beats traditional TIIE (28, 91 days) for Vasicek calibration:

| Feature | Overnight F-TIIE | Traditional TIIE (28/91 days) |
| :--- | :--- | :--- |
| **Conceptual Match** | Closest proxy to "instantaneous" $r_t$ in the SDE. | Term rate (maturity >0), introduces auto-correlation bias. |
| **Sensitivity** | Reacts immediately to monetary policy changes. | Lags due to term averaging. |
| **Availability** | Published daily by Banxico since ~2021. | Historical, but reflects credit/liquidity premia. |

> **Note**: Using a 28-day rate forces you to assume it equals the overnight rate rolled over, which adds maturity mismatch noise to MLE estimation.

### Official Data Source
- **Source**: **Banco de México (Banxico)** – *Sistema de Información Económica (SIE)*.
- **Series ID**: `SF60653` (Overnight TIIE Funding Rate).
- **Access**: Official website `banxico.org.mx` -> Statistics -> Economic Information System.
- **Alternative**: **DOF (Diario Oficial de la Federación)** publishes the daily official rate.

**Important**: When downloading, select "Daily" frequency. Download the *Fondeo* (Funding) rate, not the *TIIE de Referencia* (Reference rate, usually 28 days).

---

## 3. Ordinary Least Squares (OLS) Calibration

OLS is the simplest method, based on the discretised equation.

### 3.1 Discretisation
Euler–Maruyama discretisation of the SDE:

$$
r_{t+\Delta t} - r_t = \kappa \theta \Delta t - \kappa \Delta t \, r_t + \sigma \sqrt{\Delta t} \, \varepsilon_t
$$

where $\varepsilon_t \sim \text{i.i.d. } \mathcal{N}(0,1)$.

Rewrite as a linear regression:

$$
\Delta r_t = \alpha + \beta \, r_t + \eta_t
$$

with:
- $\Delta r_t = r_{t+\Delta t} - r_t$
- $\alpha = \kappa \theta \Delta t$
- $\beta = -\kappa \Delta t$
- $\eta_t = \sigma \sqrt{\Delta t} \, \varepsilon_t \quad \Rightarrow \quad \text{Var}(\eta_t) = \sigma^2 \Delta t$

### 3.2 OLS Estimation Steps

1. **Prepare data**: Compute $\Delta r_t$ for $t = 1, \dots, n-1$.
2. **Run regression** $\Delta r_t = \alpha + \beta r_t + \eta_t$ (include intercept $\alpha$).
3. **Obtain coefficients** $\hat{\alpha}$ and $\hat{\beta}$ via:

$$
\hat{\beta} = \frac{\sum_{t=1}^{n-1} (r_t - \bar{r})(\Delta r_t - \overline{\Delta r})}{\sum_{t=1}^{n-1} (r_t - \bar{r})^2}, \qquad \hat{\alpha} = \overline{\Delta r} - \hat{\beta} \bar{r}
$$

4. **Recover Vasicek parameters**:

$$
\hat{\kappa} = -\frac{\hat{\beta}}{\Delta t}, \qquad \hat{\theta} = \frac{\hat{\alpha}}{-\hat{\beta}} = \frac{\hat{\alpha}}{\hat{\kappa} \Delta t}
$$

5. **Estimate volatility $\sigma$** from regression residuals $\hat{\eta}_t$:

$$
\hat{\sigma} = \sqrt{ \frac{1}{(n-2)\Delta t} \sum_{t=1}^{n-1} \hat{\eta}_t^2 }
$$

(Denominator $n-2$ corrects for degrees of freedom.)

### 3.3 Advantages & Caveats
- **Pros**: Extremely fast, closed‑form, no optimisation needed.
- **Cons**:  
  - Biased for small $\Delta t$ or strong mean reversion (the bias is $O(\Delta t)$).  
  - Does not use the exact transition density (only first‑moment approximation).  
  - Not efficient if data are irregularly spaced.

---

## 4. Maximum Likelihood Estimation (MLE) – Preferred for Accuracy

MLE uses the **exact conditional distribution** of $r_{t+\Delta t} \mid r_t$ from the Vasicek model.

### 4.1 Exact Transition Density
From Brigo & Mercurio (Chapter 3), conditional on $r_t$, the distribution of $r_{t+\Delta t}$ is Gaussian:

$$
r_{t+\Delta t} \mid r_t \;\sim\; \mathcal{N}\left( \mu(r_t), s^2 \right)
$$

with:

$$
\mu(r_t) = \theta + (r_t - \theta) e^{-\kappa \Delta t}
$$

$$
s^2 = \frac{\sigma^2}{2\kappa} \left(1 - e^{-2\kappa \Delta t}\right)
$$

### 4.2 Log‑Likelihood Function
For a sample $\{r_1, r_2, \dots, r_n\}$ with constant $\Delta t$:

$$
\mathcal{L}(\kappa, \theta, \sigma) = \sum_{t=1}^{n-1} \log f(r_{t+1} \mid r_t)
$$

where $f$ is the Gaussian density:

$$
\log f(r_{t+1} \mid r_t) = -\frac{1}{2}\log(2\pi s^2) - \frac{\big(r_{t+1} - \mu(r_t)\big)^2}{2s^2}
$$

Explicitly:

$$
\mathcal{L} = -\frac{n-1}{2}\log(2\pi) - \frac{n-1}{2}\log(s^2) - \frac{1}{2s^2} \sum_{t=1}^{n-1} \left( r_{t+1} - \theta - (r_t - \theta)e^{-\kappa \Delta t} \right)^2
$$

### 4.3 MLE Workflow

1. **Choose initial guesses**: Use the OLS estimates as starting values for $\kappa, \theta, \sigma$.
2. **Optimise numerically**: Maximise $\mathcal{L}$ with respect to $\kappa, \theta, \sigma$.
   - Constraints: $\kappa > 0, \sigma > 0$ (use log transforms or bound constraints).
   - Typical methods: **Nelder‑Mead** (simplex) or **BFGS** (gradient‑based).
3. **Obtain asymptotic standard errors**: From the inverse of the Fisher information matrix (Hessian of $-\mathcal{L}$ at the optimum).

### 4.4 Practical Implementation Notes
- **Closed‑form for $\theta$** given $\kappa, \sigma$: The likelihood can be concentrated, but full numerical optimisation is easier with modern software (R's `optim`, Python's `scipy.optimize.minimize`).
- **Unbiasedness**: MLE is consistent and asymptotically efficient, even for strongly mean‑reverting processes.
- **Small‑sample bias**: For very small $n$ (e.g., <100), bias in $\kappa$ can be significant; use **bootstrap** or **Jackknife** for bias correction if needed.

---

## 5. Comparison: OLS vs. MLE for Real‑World Use

| Criterion | OLS | MLE |
|-----------|-----|-----|
| **Speed** | Instant (closed form) | Requires optimisation (seconds) |
| **Bias** | $O(\Delta t)$ bias in $\kappa$ | Consistent (bias $O(1/n)$) |
| **Efficiency** | Lower | Asymptotically optimal |
| **Handling irregular $\Delta t$** | No | Yes (modify $\mu$ and $s^2$ per interval) |
| **Good for** | Quick initial guess, large $\Delta t$ (monthly+) | Final calibration, small $\Delta t$ (daily), high precision |

**Recommended workflow for real‑world use:**
1. Use **OLS** to get starting values.
2. Refine with **MLE** for final parameter estimates.
3. Report both: OLS for transparency (linear regression), MLE for inference (standard errors).

---

## 6. Practical Considerations for Time Window Selection (Mexican Market)

For the Mexican market, there is no single optimal window length. The trade-off is between **estimation accuracy (longer windows)** vs. **regime relevance (shorter windows)**.

### 6.1 The Problem: Structural Breaks in Mexico
Banxico has recently demonstrated sharp policy pivots. As of March 2026, headline inflation accelerated to **4.63%** (above the 3% target), yet Banxico cut rates to **6.75%** in a divided vote. If your data window includes the aggressive hiking cycle of 2022-2023 *and* a cutting cycle, your OLS/MLE will produce an **average** mean reversion level ($\theta$) that exists nowhere in reality.

### 6.2 Recommended Approach: The "5-Year Rolling Window with a Regime Filter"

**Step 1: Identify the Current Monetary Policy Regime**
- **Look back**: Do not exceed **5 years (approx. 1,250 daily observations)**.
- **Rationale**: 5 years is long enough for MLE to be statistically consistent but short enough to exclude extreme volatility of the COVID-19 period (2020-2021) and the peak inflation shock (2022).

**Step 2: The "Crisis Exclusion" Rule**
Manually exclude specific periods if your goal is "current market conditions":
- **Exclude**: March 2020 – December 2021 (COVID liquidity shock). Rates hit near-zero, breaking the mean-reverting assumption.
- **Consider excluding**: Specific months in 2022 where Banxico made "emergency" 75bps+ hikes.

**Step 3: The Stability Test**
Run MLE on the last 3 years and the last 5 years.
- **If $\kappa$ and $\theta$ are similar**: The market is stationary; use the 5-year window (lower standard errors).
- **If they are different**: The market is in transition. **Prefer the 3-year window**. It will have higher variance but lower bias.

### 6.3 Final Recommendation for Today (2026)
Given that Banxico is pivoting from high rates to a neutral/lower rate environment, **use the last 3 years of daily F-TIIE data** (March 2023 – March 2026). This window captures the tail end of the high-rate plateau and the current easing cycle, giving a $\theta$ relevant for the next 12 months.

---

## 7. Complete Calibration Workflow for Mexico

### Step 1: Data Cleaning
- Pull F-TIIE from Banxico SIE (Series SF60653).
- Frequency: Daily ($\Delta t = 1/252$).
- Check for missing days (Banxico publishes only business days).

### Step 2: OLS Estimation (Initial Guess)
- Regress $\Delta r_t$ on $r_t$.
- Output: Provides starting values for MLE.

### Step 3: MLE Refinement (Final Parameters)
- Optimise using the exact Gaussian transition density.
- Constraint: $\sigma$ should be relatively low for F-TIIE (overnight risk is lower than 28-day TIIE).

### Step 4: Diagnostic Check
- **QQ Plot**: Compare residuals against a normal distribution. If tails are too fat (common in Mexican markets due to sudden "Banxico surprises"), MLE standard errors might be underestimated.

### Step 5: Stationarity Check
- $\kappa > 0$ must hold. If $\hat{\kappa}$ is not significant (within 2 standard errors of zero), the series may not be mean‑reverting. A unit‑root test (e.g., ADF) is advised before Vasicek calibration.

---

## 8. Summary Table for Mexican Calibration

| Decision Variable | Recommended Setting | Justification |
| :--- | :--- | :--- |
| **Short Rate Proxy** | F-TIIE (Overnight) | Matches "instantaneous" assumption of Vasicek. |
| **Data Source** | Banxico SIE (Series SF60653) | Official, free, daily updates. |
| **Window Length** | 3 to 5 years (max) | Balances statistical power vs. regime relevance. |
| **Excluded Periods** | COVID-19 shock (2020-2021) | Non-stationary behavior breaks Vasicek assumptions. |
| **Current Bias Check** | Compare 3y vs 5y results | If 5y shows higher $\theta$ than 3y, use the 3y estimate. |

---

## 9. Example (Conceptual) – Daily Data

Suppose $\Delta t = 1/252$ (daily), and OLS gives $\hat{\kappa}=0.8$, $\hat{\theta}=0.05$, $\hat{\sigma}=0.01$.  
Plug into MLE optimisation. The optimiser might adjust to $\kappa=0.75$, $\theta=0.051$, $\sigma=0.0105$, with standard errors (e.g., $\text{se}(\kappa)=0.12$).

---

## References

1. Brigo, D., & Mercurio, F. (2006). *Interest Rate Models – Theory and Practice: With Smile, Inflation and Credit* (2nd ed.). Springer Finance.

2. Banco de México. (n.d.). *Sistema de Información Económica (SIE)*. Retrieved from https://www.banxico.org.mx

3. Vasicek, O. (1977). An equilibrium characterization of the term structure. *Journal of Financial Economics*, 5(2), 177–188.