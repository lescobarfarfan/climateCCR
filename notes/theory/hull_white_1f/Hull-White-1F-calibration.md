# Hull-White Model: Complete Session Compendium

This document consolidates all answers provided during the session, covering the Hull-White model's theoretical foundation, implementation, advanced Monte Carlo techniques, calibration to Mexican market data, stress testing, and practical considerations for simulating long-term interest rates.

---

## Table of Contents

1. [Basic Hull-White Model Implementation](#1-basic-hull-white-model-implementation)
2. [Advanced Monte Carlo Techniques](#2-advanced-monte-carlo-techniques)
3. [Summary Document: Theory, Mexican Market, and Code Scripts](#3-summary-document-theory-mexican-market-and-code-scripts)
4. [Detailed Calibration Methods](#4-detailed-calibration-methods)
5. [Clarification on $\theta(t)$ and Simulation for a Bond Portfolio](#5-clarification-on-thetat-and-simulation-for-a-bond-portfolio)
6. [Discount Factor Approximation and Real-World Measure](#6-discount-factor-approximation-and-real-world-measure)
7. [Instantaneous Forward Curve $f(0,t)$ and Calibration from TIIE](#7-instantaneous-forward-curve-f0t-and-calibration-from-tiie)
8. [Long-Term Maturities (10, 20, 30 Years) – Incorporating TIIE and Bonos M](#8-long-term-maturities-10-20-30-years--incorporating-tiie-and-bonos-m)
9. [References](#9-references)

---

## 1. Basic Hull-White Model Implementation

### 1.1 Theoretical Background

The Hull-White model (extended Vasicek) describes the evolution of short rates:

$$dr(t) = [\theta(t) - a \cdot r(t)]dt + \sigma dW(t)$$

where:
- $r(t)$: short rate at time $t$
- $a > 0$: mean reversion speed
- $\sigma > 0$: volatility
- $\theta(t)$: function chosen to fit the initial term structure
- $dW(t)$: Wiener process under the risk-neutral measure

### 1.2 Key Properties

- **Conditional moments**:  
  $\mathbb{E}[r(t)|\mathcal{F}_s] = r(s)e^{-a(t-s)} + \int_s^t e^{-a(t-u)}\theta(u)du$  
  $Var[r(t)|\mathcal{F}_s] = \frac{\sigma^2}{2a}\left(1-e^{-2a(t-s)}\right)$  
- **Bond prices**: Affine form 
  $P(t,T) = A(t,T)e^{-B(t,T)r(t)}$ with  
  $B(t,T)=\frac{1-e^{-a(T-t)}}{a}$.

### 1.3 Python Implementation (`hull_white_base.py`)

```python
import numpy as np
from typing import Callable, Optional, Tuple

class HullWhiteModel:
    """
    One-factor Hull-White interest rate model.
    dr(t) = [θ(t) - a·r(t)]dt + σ dW(t)
    """
    def __init__(self, a: float, sigma: float, r0: float = 0.05):
        self.a = a
        self.sigma = sigma
        self.r0 = r0

    def theta(self, t: float, forward_curve: Optional[Callable] = None) -> float:
        if forward_curve is None:
            return self.a * self.r0 + (self.sigma**2)/(2*self.a) * (1 - np.exp(-2*self.a*t))
        else:
            dt_small = 1e-6
            if t < dt_small:
                df_dt = (forward_curve(dt_small) - forward_curve(0)) / dt_small
            else:
                df_dt = (forward_curve(t+dt_small) - forward_curve(t-dt_small)) / (2*dt_small)
            f = forward_curve(t)
            return df_dt + self.a * f + (self.sigma**2)/(2*self.a) * (1 - np.exp(-2*self.a*t))

    def simulate_euler(self, T: float, n_steps: int, n_paths: int,
                       forward_curve: Optional[Callable] = None) -> Tuple[np.ndarray, np.ndarray]:
        dt = T / n_steps
        time = np.linspace(0, T, n_steps+1)
        rates = np.zeros((n_paths, n_steps+1))
        rates[:, 0] = self.r0
        for i in range(n_steps):
            t = time[i]
            theta_t = self.theta(t, forward_curve)
            drift = theta_t - self.a * rates[:, i]
            dW = np.random.normal(0, np.sqrt(dt), n_paths)
            rates[:, i+1] = rates[:, i] + drift * dt + self.sigma * dW
        return time, rates
```

### 1.4 References

- Hull, J., & White, A. (1990). "Pricing Interest-Rate-Derivative Securities". *The Review of Financial Studies*, 3(4), 573-592.
- Brigo, D., & Mercurio, F. (2006). *Interest Rate Models – Theory and Practice*. Springer.

---

## 2. Advanced Monte Carlo Techniques

### 2.1 Why Advanced Techniques?

Standard Euler-Maruyama Monte Carlo suffers from discretization error and sampling error. Advanced methods improve efficiency and accuracy.

### 2.2 Techniques Explained

#### 2.2.1 Antithetic Variates

Generate pairs of paths using $Z$ and $-Z$, creating negative correlation. For estimator $\hat{\theta} = \frac{1}{2}(\hat{\theta}_1+\hat{\theta}_2)$ and $Var(\hat{\theta}) = \frac{\sigma^2}{2}(1+\rho)$. With $\rho=-1$, variance is zero.

**Reference**: Hammersley & Morton (1956).

#### 2.2.2 Control Variates

Use a known expectation $\mathbb{E}[X]$ to correct estimator of $Y$:  
$Y_{\text{control}} = Y - \beta(X - \mathbb{E}[X])$
Optimal $\beta = \frac{Cov(Y,X)}{Var(X)}$.

**Reference**: Lavenberg & Welch (1981).

#### 2.2.3 Importance Sampling

Change drift to make important outcomes more likely, then reweight by likelihood ratio:  
$\frac{d\mathbb{P}}{d\mathbb{Q}} = \exp\!\left(-\int_0^T \gamma\,dW(t)-\frac12\gamma^2 T\right)$

**Reference**: Glynn & Iglehart (1989).

#### 2.2.4 Moment Matching

Adjust simulated paths so sample moments equal theoretical moments:  
$$X_i^{\text{adj}} = \mu + \frac{\sigma}{S}(X_i-\bar{X})$$

**Reference**: Barraquand (1995).

#### 2.2.5 Quasi-Monte Carlo

Use low-discrepancy sequences (e.g., Sobol) for integration error $O(\frac{\log{N}^d}{N})$.

**Reference**: Niederreiter (1992).

#### 2.2.6 Multilevel Monte Carlo

Combine simulations on multiple time grids:  
$$\mathbb{E}[P_L] = \mathbb{E}[P_0] + \sum_{\ell=1}^L \mathbb{E}[P_\ell-P_{\ell-1}]$$

**Reference**: Giles (2008).

### 2.3 Python Implementation (`hull_white_advanced_mc.py`)

```python
import numpy as np
from .hull_white_base import HullWhiteModel

class HullWhiteAdvancedMC(HullWhiteModel):
    def simulate_antithetic(self, T, n_steps, n_paths, forward_curve=None):
        dt = T / n_steps
        time = np.linspace(0, T, n_steps+1)
        n_pairs = n_paths // 2
        rates = np.zeros((2*n_pairs, n_steps+1))
        rates[:, 0] = self.r0
        for i in range(n_steps):
            t = time[i]
            theta_t = self.theta(t, forward_curve)
            drift = theta_t - self.a * rates[::2, i]
            Z = np.random.normal(0, 1, n_pairs)
            dW_plus = Z * np.sqrt(dt)
            dW_minus = -Z * np.sqrt(dt)
            rates[::2, i+1] = rates[::2, i] + drift * dt + self.sigma * dW_plus
            rates[1::2, i+1] = rates[1::2, i] + drift * dt + self.sigma * dW_minus
        return time, rates

    def simulate_control_variate(self, T, n_steps, n_paths, forward_curve=None):
        dt = T / n_steps
        time = np.linspace(0, T, n_steps+1)
        rates = np.zeros((n_paths, n_steps+1))
        rates[:, 0] = self.r0
        integral = np.zeros(n_paths)
        for i in range(n_steps):
            t = time[i]
            theta_t = self.theta(t, forward_curve)
            drift = theta_t - self.a * rates[:, i]
            dW = np.random.normal(0, np.sqrt(dt), n_paths)
            rates[:, i+1] = rates[:, i] + drift * dt + self.sigma * dW
            integral += 0.5 * (rates[:, i] + rates[:, i+1]) * dt
        # Known expectation (flat curve approx)
        a, sigma, r0 = self.a, self.sigma, self.r0
        exp_integral = (r0/a)*(1-np.exp(-a*T)) + (sigma**2/(2*a**2))*(T - (2/a)*(1-np.exp(-a*T)) + (1/(2*a))*(1-np.exp(-2*a*T)))
        y = rates[:, -1]
        cov = np.cov(integral, y)[0,1]
        var_x = np.var(integral)
        beta = cov / var_x if var_x > 0 else 0
        y_adj = y - beta * (integral - exp_integral)
        return time, y_adj
```

---

## 3. Summary Document: Theory, Mexican Market, and Code Scripts

This section summarises the comprehensive document provided earlier, covering:

- **Theoretical foundation** (repeated from Section 1)
- **Advanced Monte Carlo** (repeated from Section 2)
- **Mexican market context**: Bonos M, UDIBONOS, TIIE, CETES, corporate bonds
- **Stress testing framework**: scenario generation (parallel shift, steepening, volatility shock, mean reversion shock), portfolio valuation, regulatory reporting in CNBV format
- **Four Python scripts**:
  - `hull_white_base.py`
  - `hull_white_advanced_mc.py`
  - `mexican_market_risk.py` (calibration and stress scenario generation)
  - `examples.py` (usage examples)

Due to space, the full code of `mexican_market_risk.py` and `examples.py` is included in the previous response; they are available in the session history.

**References** (already listed in Section 9).

---

## 4. Detailed Calibration Methods

### 4.1 Estimating Mean Reversion Speed $a$

#### 4.1.1 Linear Regression (AR(1) approximation)

From discrete approximation: $r_{t+\Delta t} = \alpha + \beta r_t + \eta_t$. Then $a = (1-\beta)/\Delta t$, $\mu = \alpha/(1-\beta)$.

#### 4.1.2 Maximum Likelihood Estimation (MLE)

For Vasicek model (constant $\theta$), conditional density is normal with  
$\mathbb{E}[r_{t+\Delta t}|r_t] = r_t e^{-a\Delta t} + \mu(1-e^{-a\Delta t})$  
$Var[r_{t+\Delta t}|r_t] = \frac{\sigma^2}{2a}(1-e^{-2a\Delta t})$  
Maximize log-likelihood to get $a,\mu,\sigma$.  

**Reference**: Brigo & Mercurio (2006).

### 4.2 Estimating Volatility $\sigma$

#### 4.2.1 Historical Volatility

$$\hat{\sigma} = \sqrt{\frac{1}{(n-1)\Delta t}\sum (\Delta r_t - \overline{\Delta r})^2}$$

#### 4.2.2 GARCH Models

Fit GARCH(1,1) to residuals: $\sigma_t^2 = \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2$, then unconditional volatility $\sqrt{\omega/(1-\alpha-\beta)}$.

**Reference**: Bollerslev (1986).

### 4.3 Calibrating $\theta(t)$ to Initial Term Structure

From instantaneous forward curve $f(0,t)$:
$$\theta(t) = \frac{\partial f(0,t)}{\partial T} + a f(0,t) + \frac{\sigma^2}{2a}(1-e^{-2at})$$

Numerical implementation: compute $f(0,t)$ via bootstrapping, then finite differences.

### 4.4 Python Calibration Code (`mexican_market_risk.py` snippet)

```python
import numpy as np
from scipy.optimize import minimize

def estimate_mean_reversion_mle(rates, dt):
    n = len(rates)
    def neg_log_lik(params):
        a, mu, sigma = params
        if a <= 0 or sigma <= 0:
            return 1e10
        ll = 0
        for i in range(n-1):
            r_t = rates[i]
            r_n = rates[i+1]
            exp_a = np.exp(-a*dt)
            mean = r_t * exp_a + mu * (1 - exp_a)
            var = (sigma**2/(2*a)) * (1 - np.exp(-2*a*dt))
            if var <= 0:
                return 1e10
            ll += -0.5*np.log(2*np.pi*var) - 0.5*(r_n - mean)**2 / var
        return -ll
    init = [0.1, np.mean(rates), np.std(np.diff(rates)/np.sqrt(dt))]
    res = minimize(neg_log_lik, init, bounds=[(1e-6, None), (None, None), (1e-6, None)])
    return res.x

def calibrate_theta(a, sigma, r0, forward_curve_func, t_grid):
    dt_small = 1e-6
    theta = np.zeros_like(t_grid)
    for i, t in enumerate(t_grid):
        if t < dt_small:
            df_dt = (forward_curve_func(dt_small) - forward_curve_func(0)) / dt_small
        else:
            df_dt = (forward_curve_func(t+dt_small) - forward_curve_func(t-dt_small)) / (2*dt_small)
        f = forward_curve_func(t)
        theta[i] = df_dt + a*f + (sigma**2/(2*a))*(1 - np.exp(-2*a*t))
    return theta
```

---

## 5. Clarification on $\theta(t)$ and Simulation for a Bond Portfolio

### 5.1 What $\theta(t)$ Represents

$\theta(t)$ is **not** maturity-dependent. It is a single deterministic function of the current time $t$, calibrated to ensure the model reproduces the entire initial yield curve. From a single simulated path of $r(t)$, you can compute discount factors for **any** future date and thus price all bonds in your portfolio.

### 5.2 Why One $\theta(t)$ Works for All Maturities

The bond price $P(0,T)$ is an expectation over the same $r(t)$ process; $\theta(t)$ is chosen so that this expectation matches market prices for every $T$ simultaneously.

### 5.3 Step-by-Step for Portfolio Pricing

1. Calibrate $\theta(t)$ using the full yield curve.
2. Simulate $N$ paths of $r(t)$ from $t=0$ to the longest bond maturity.
3. For each path, compute discount factors to every cash flow date (using numerical integration).
4. Price each bond on that path by discounting its cash flows.
5. Aggregate to get portfolio value distribution.

---

## 6. Discount Factor Approximation and Real-World Measure

### 6.1 Numerical Approximation of Discount Factors

From a discrete path $r(t_i)$, the discount factor to time $T$ is $\exp\!\left(-\int_0^T r(s)ds\right)$. Approximate the integral using:

- **Trapezoidal rule** (more accurate): $\sum_{i=0}^{N-1} \frac{r(t_i)+r(t_{i+1})}{2}\Delta t_i$
- **Rectangle rule** (simpler): $\sum_{i=0}^{N-1} r(t_i)\Delta t_i$ (left) or $\sum_{i=1}^N r(t_i)\Delta t_{i-1}$ (right)

Maintain cumulative integral along the path. For coupon bonds, compute integrals to each payment date.

**Reference**: Yasuoka (2018) discusses integration techniques in interest rate simulation.

### 6.2 Simulating Under the Real-World $\mathbb{P}$ Measure

Risk-neutral SDE: $dr = [\theta(t)-a r]dt + \sigma dW^{\mathbb{Q}}$.  
Real-world SDE: $dr = [\theta(t)-a r + \lambda(t)\sigma]dt + \sigma dW^{\mathbb{P}}$, where $\lambda(t)$ is the market price of interest rate risk.

To estimate $\lambda(t)$:
- Use historical data to extract $\mathbb{P}$ drift (e.g., via MLE on a Vasicek model)
- Assume constant $\lambda$ and estimate from average excess return of a long-term bond over the short rate
- In stress testing, combine $\mathbb{P}$-measure dynamics with shocked initial curve or parameters

**References**: Yasuoka (2018), Brigo & Mercurio (2006).

---

## 7. Instantaneous Forward Curve $f(0,t)$ and Calibration from TIIE

### 7.1 Definition of $f(0,t)$

$f(0,t)$ is the instantaneous forward rate at time $0$ for maturity $t$, defined from zero-coupon bond prices:

$$f(0,t) = -\frac{\partial}{\partial T} \ln P(0,T) \Big|_{T=t}$$

It is **not** directly observable; it must be constructed from market instruments.

### 7.2 Standard Functional Forms

There is no single "standard" form. In practice, $f(0,t)$ is obtained by:
- **Bootstrapping** from discrete market rates (e.g., TIIE, swaps, bonds)
- **Interpolation** (cubic splines, Nelson-Siegel) to create a continuous curve
- **Smoothing** techniques to ensure differentiability

**References**: Hagan & West (2006), Nelson & Siegel (1987).

### 7.3 Using TIIE Data for Calibration

TIIE rates (28, 91, 182 days) are **term rates**, not instantaneous. To use them:

1. Treat TIIE as floating rates consistent with swap market conventions (Hull & White, 2014).
2. Bootstrap the zero-coupon yield curve from TIIE and other instruments.
3. From the continuous zero-coupon curve, compute $f(0,t)$ via numerical differentiation.

**Key insight**: TIIE data is essential and correct for the short end, but must be processed through bootstrapping.

### 7.4 References for Bootstrapping

| **Reference** | **Description** | **Relevance** |
|:---|:---|:---|
| Hagan, P., & West, G. (2006). "Interpolation Methods for Curve Construction". *Applied Mathematical Finance*, 13(2), 89-129. | Comprehensive overview of interpolation methods | Standard reference for bootstrapping techniques |
| Hull, J., & White, A. (2014). "Interest Rate Models: Theory and Practice". *Journal of Derivatives*. | Discusses construction of discount curves including treatment of TIIE | Cited in Mexican market context |
| Banco de México (2023). "Disposiciones de Carácter General Aplicables a las Instituciones de Crédito". | Official documentation on TIIE calculation | Primary source for Mexican market data interpretation |
| Ron, U. (2000). "A Practical Guide to Swap Curve Construction". *Bank of Canada Working Paper*. | Step-by-step guide to bootstrapping swap curves | Practical methodology applicable to TIIE swaps |
| Ametrano, F., & Bianchetti, M. (2013). "Everything You Always Wanted to Know About Multiple Interest Rate Curve Bootstrapping". *SSRN*. | Modern approach to multi-curve bootstrapping | Relevant for post-crisis environment with multiple curves |

---

## 8. Long-Term Maturities (10, 20, 30 Years) – Incorporating TIIE and Bonos M

### 8.1 Available Long-Term Data

| Maturity | Data Source | Availability |
|:---|:---|:---|
| 1-3 years | Bonos M, TIIE swaps | Daily quotes |
| 5 years | Bonos M, TIIE swaps | Daily quotes |
| 7 years | Bonos M | Daily quotes |
| 10 years | Bonos M, OECD data | Daily quotes |
| 15 years | Bonos M | Daily quotes |
| 20 years | Bonos M | Daily quotes |
| 30 years | Bonos M | Daily quotes |

### 8.2 Complete Calibration Approach

**Step 1: Short end (up to 182 days)** – Bootstrap using TIIE rates (28, 91, 182 days).

**Step 2: Medium to long end (1-30 years)** – Use Bonos M yields at standard tenors. Convert coupon-bearing yields to zero-coupon rates if necessary (requires stripping).

**Step 3: Interpolation** – Apply a robust interpolation method (cubic splines, Nelson-Siegel, monotone convex) to create a continuous curve.

**Step 4: Compute $f(0,t)$** – From the continuous zero-coupon curve, compute instantaneous forward rates and their derivatives for the Hull-White $\theta(t)$ function.

### 8.3 References for Long-Term Curve Construction

| **Reference** | **Description** | **Relevance** |
|:---|:---|:---|
| Nelson, C., & Siegel, A. (1987). "Parsimonious Modeling of Yield Curves". *Journal of Business*, 60(4), 473-489. | Parametric model for fitting yield curves | Widely used for fitting entire curve with few parameters |
| Svensson, L. (1994). "Estimating and Interpreting Forward Interest Rates". *IMF Working Paper* No. 94/114. | Extension of Nelson-Siegel | Standard at many central banks |
| Banco de México (2024). "Metodología para la determinación de la curva de rendimientos de los Bonos M". | Official methodology for Bonos M yield curve | Primary source for Mexican government bond curve construction |
| Hagan, P., & West, G. (2008). "Methods for Constructing a Yield Curve". *Wilmott Magazine*, May 2008, 70-81. | Practical comparison of interpolation methods | Good overview of pros and cons |
| Andersen, L., & Piterbarg, V. (2010). *Interest Rate Modeling*. Atlantic Financial Press. | Comprehensive treatment of curve construction | Advanced reference |

### 8.4 Practical Implementation Notes

- Download TIIE rates from Banco de México's SIE (series SF43783 for 28-day TIIE).
- Download Bonos M yields from financial data providers or public sources like Investing.com.
- Combine all data points, bootstrap the zero-coupon curve using a chosen interpolation method.
- Derive $f(0,t)$ numerically and use in $\theta(t)$ formula.
- For long-term simulation, ensure mean reversion $a$ and volatility $\sigma$ are consistent with historical data covering long-term rates.

---

## 9. References

### Original Papers
1. Hull, J., & White, A. (1990). "Pricing Interest‑Rate‑Derivative Securities". *The Review of Financial Studies*, 3(4), 573-592.
2. Hull, J., & White, A. (1994). "Numerical procedures for implementing term structure models I: Single‑factor models". *Journal of Derivatives*, 2(1), 7-16.
3. Hull, J., & White, A. (2014). "Interest Rate Models: Theory and Practice". *Journal of Derivatives*.

### Books
4. Brigo, D., & Mercurio, F. (2006). *Interest Rate Models – Theory and Practice* (2nd ed.). Springer.
5. Glasserman, P. (2004). *Monte Carlo Methods in Financial Engineering*. Springer.
6. Jorion, P. (2006). *Value at Risk: The New Benchmark for Managing Financial Risk* (3rd ed.). McGraw‑Hill.
7. Andersen, L., & Piterbarg, V. (2010). *Interest Rate Modeling*. Atlantic Financial Press.
8. James, J., & Webber, N. (2000). *Interest Rate Modelling*. Wiley.
9. Yasuoka, T. (2018). *Interest Rate Modeling for Risk Management: Market Price of Interest Rate Risk* (2nd ed.). Bentham Science Publishers.

### Advanced Monte Carlo
10. Hammersley, J. M., & Morton, K. W. (1956). "A new Monte Carlo technique: antithetic variates". *Mathematical Proceedings of the Cambridge Philosophical Society*, 52(3), 449-475.
11. Lavenberg, S. S., & Welch, P. D. (1981). "A perspective on the use of control variables to increase the efficiency of Monte Carlo simulations". *Management Science*, 27(3), 322-335.
12. Glynn, P. W., & Iglehart, D. L. (1989). "Importance sampling for stochastic simulations". *Management Science*, 35(11), 1367-1392.
13. Barraquand, J. (1995). "Numerical valuation of high dimensional multivariate European securities". *Management Science*, 41(12), 1882-1891.
14. Niederreiter, H. (1992). *Random Number Generation and Quasi‑Monte Carlo Methods*. SIAM.
15. Giles, M. B. (2008). "Multilevel Monte Carlo path simulation". *Operations Research*, 56(3), 607-617.

### Yield Curve Construction and Bootstrapping
16. Hagan, P., & West, G. (2006). "Interpolation Methods for Curve Construction". *Applied Mathematical Finance*, 13(2), 89-129.
17. Hagan, P., & West, G. (2008). "Methods for Constructing a Yield Curve". *Wilmott Magazine*, May 2008, 70-81.
18. Nelson, C., & Siegel, A. (1987). "Parsimonious Modeling of Yield Curves". *Journal of Business*, 60(4), 473-489.
19. Svensson, L. (1994). "Estimating and Interpreting Forward Interest Rates". *IMF Working Paper* No. 94/114.
20. Ron, U. (2000). "A Practical Guide to Swap Curve Construction". *Bank of Canada Working Paper* No. 2000-17.
21. Ametrano, F., & Bianchetti, M. (2013). "Everything You Always Wanted to Know About Multiple Interest Rate Curve Bootstrapping". *SSRN Electronic Journal*. DOI: 10.2139/ssrn.2219548.

### Calibration and Estimation
22. Bollerslev, T. (1986). "Generalized autoregressive conditional heteroskedasticity". *Journal of Econometrics*, 31(3), 307-327.

### Mexican Market Specific
23. Banco de México. "Sistema de Información Económica (SIE)". https://www.banxico.org.mx/SieInternet/
24. Banco de México. "Disposiciones de Carácter General Aplicables a las Instituciones de Crédito" (Circular Única de Bancas).
25. Banco de México (2024). "Metodología para la determinación de la curva de rendimientos de los Bonos M".
26. Sidaoui, J., et al. (2010). "The Mexican fixed income market: Structure and participants". *BIS Papers*, No. 53.
27. Investing.com (2026). "Mexico Government Bonds". https://www.investing.com/rates-bonds/mexico-government-bonds
28. OECD (2025). "Long-Term Government Bond Yields: 10-year: Main (Including Benchmark) for Mexico". https://data.oecd.org
29. CEIC Data (2026). "Mexico Treasury Bill and Government Securities Rates: Annual". https://www.ceicdata.com

### Risk Management and Regulatory
30. Basel Committee on Banking Supervision (2019). *Minimum capital requirements for market risk*. Bank for International Settlements.
31. CNBV. *Disposiciones de Carácter General en Materia de Administración de Riesgos*.

---
