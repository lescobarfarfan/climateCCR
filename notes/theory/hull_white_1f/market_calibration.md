# Hull-White Model: Calibration and Stress Testing for Market Risk

## 1. Calibration of Hull-White Model Parameters

Calibration involves estimating the parameters $a$ (mean reversion speed), $\sigma$ (volatility), and the function $\theta(t)$ (which ensures the model fits the current term structure). Below we detail common methods for each.

### 1.1 Estimating Mean Reversion Speed ($a$)

#### 1.1.1 Linear Regression on Historical Short Rates

The discrete-time version of the Hull-White SDE (under the assumption of constant $\theta$) can be approximated as:

$$r_{t+\Delta t} - r_t = a(\mu - r_t)\Delta t + \sigma \sqrt{\Delta t}\,\epsilon_t$$

where $\mu$ is the long-term mean (if constant). Rearranging:

$$r_{t+\Delta t} = a\mu\Delta t + (1 - a\Delta t) r_t + \sigma \sqrt{\Delta t}\,\epsilon_t$$

This is an AR(1) process. Regressing $r_{t+\Delta t}$ on $r_t$ gives:

$$r_{t+\Delta t} = \alpha + \beta r_t + \eta_t$$

Then:

- $a = (1 - \beta)/\Delta t$
- $\mu = \alpha/(1 - \beta)$

**Reference**: James, J., & Webber, N. (2000). *Interest Rate Modelling*. Wiley.

#### 1.1.2 Maximum Likelihood Estimation (MLE)

For the Vasicek model (constant $\theta$), the exact conditional distribution of $r_{t+\Delta t}$ given $r_t$ is normal with:

$$\mathbb{E}[r_{t+\Delta t} | r_t] = r_t e^{-a\Delta t} + \mu(1 - e^{-a\Delta t})$$
$$\text{Var}[r_{t+\Delta t} | r_t] = \frac{\sigma^2}{2a}(1 - e^{-2a\Delta t})$$

The log-likelihood for a time series $\{r_{t_i}\}$ is:

$$\mathcal{L} = -\frac{n}{2}\ln(2\pi) - \frac{1}{2}\sum_{i=1}^{n-1}\left[\ln(\sigma_i^2) + \frac{(r_{t_{i+1}} - \mu_i)^2}{\sigma_i^2}\right]$$

where $\mu_i$ and $\sigma_i^2$ are the conditional moments above. Maximizing this yields estimates for $a$, $\mu$, $\sigma$.

**Reference**: Brigo, D., & Mercurio, F. (2006). *Interest Rate Models – Theory and Practice*. Springer.

### 1.2 Estimating Volatility ($\sigma$)

#### 1.2.1 Historical Volatility

If we have historical short rate changes $\Delta r_t = r_{t+\Delta t} - r_t$, the volatility can be estimated as:

$$\hat{\sigma} = \sqrt{\frac{1}{(n-1)\Delta t}\sum_{t=1}^{n-1}(\Delta r_t - \overline{\Delta r})^2}$$

This assumes homoskedasticity and zero drift over short intervals.

#### 1.2.2 GARCH Models

For time-varying volatility, a GARCH(1,1) model can be fitted to the residuals:

$$\sigma_t^2 = \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2$$

The unconditional volatility is $\sigma = \sqrt{\omega/(1-\alpha-\beta)}$.

**Reference**: Bollerslev, T. (1986). "Generalized autoregressive conditional heteroskedasticity". *Journal of Econometrics*.

### 1.3 Calibrating $\theta(t)$ to the Initial Term Structure

The function $\theta(t)$ is chosen so that the model reproduces the observed market bond prices $P^M(0,T)$ for all $T$. In the Hull-White model, bond prices are given by:

$$P(0,T) = A(0,T)e^{-B(0,T)r_0}$$

with $B(0,T) = \frac{1 - e^{-aT}}{a}$ and $A(0,T)$ expressed in terms of $\theta$. Alternatively, one can use the relationship between $\theta(t)$ and the instantaneous forward rate $f(0,t)$:

$$\theta(t) = \frac{\partial f(0,t)}{\partial T} + a f(0,t) + \frac{\sigma^2}{2a}(1 - e^{-2at})$$

Thus, to calibrate $\theta(t)$:

1. Obtain the market instantaneous forward curve $f(0,t)$ from observed bond prices or swap rates.
2. Compute the derivative $\frac{\partial f(0,t)}{\partial T}$ numerically (e.g., finite differences).
3. Plug into the formula to get $\theta(t)$ at discrete tenors, then interpolate.

If only discrete bond prices are available, one can solve for $\theta(t)$ by inverting the bond pricing formula. A common approach is to assume $\theta(t)$ is piecewise constant and solve recursively.

**Reference**: Hull, J., & White, A. (1990). "Pricing Interest-Rate-Derivative Securities". *The Review of Financial Studies*.

---

## 2. Generating Stress Trajectories

Stress testing aims to assess portfolio sensitivity to extreme but plausible market movements. For a 3-year horizon where interest rates are assumed to increase by 5% (e.g., from current 5% to 10%), we need to incorporate this view into the simulated paths. Several methods exist.

### 2.1 Adjusting the Initial Forward Curve

The most direct way: shock the initial yield curve used to compute $\theta(t)$. If we want rates to be higher on average over the next 3 years, we can shift the initial forward curve upward by a deterministic amount (e.g., +500bps) and recalibrate $\theta(t)$. Then the simulated paths will reflect that stressed initial curve. This is consistent with the model's no-arbitrage property – the drift $\theta(t)$ ensures that expected future rates match the forward curve.

**Procedure**:
- Start with the current market forward curve $f(0,t)$.
- Apply a parallel shift of +5% (500 bps) to obtain a stressed forward curve $f^*(0,t) = f(0,t) + 0.05$.
- Compute the stressed $\theta^*(t)$ using the formula with $f^*(0,t)$.
- Simulate paths under the stressed $\theta^*(t)$.

This will produce trajectories where the *expected* short rate at each future time is increased by approximately 5%, but individual paths will exhibit volatility around that mean.

**Note**: A parallel shift is a simple choice; more complex non-parallel shifts (e.g., steepening) can also be applied.

### 2.2 Importance Sampling for Targeted Terminal Rates

If we specifically want the *terminal* short rate $r(3)$ to have a higher mean (e.g., $r_0+0.05$), we can use importance sampling. This involves changing the drift of the Brownian motion to make paths ending near the target more likely, then reweighting.

For the Hull-White model, the distribution of $r(T)$ given $r_0$ is normal with known mean $\mu_T$ and variance $\sigma_T^2$. To shift the mean to a target $\mu_T^{\text{stress}}$, we can add a drift adjustment $\gamma$ to the Brownian motion:

$$dW^*(t) = dW(t) + \gamma(t) dt$$

The Radon-Nikodym derivative for the change of measure is:

$$\frac{d\mathbb{P}}{d\mathbb{P}^*} = \exp\left(-\int_0^T \gamma(t) dW(t) - \frac12\int_0^T \gamma(t)^2 dt\right)$$

Choosing $\gamma(t)$ constant such that $\mathbb{E}^*[r(T)] = \mu_T^{\text{stress}}$ yields:

$$\gamma = \frac{\mu_T^{\text{stress}} - \mu_T}{\sigma_T^2} \cdot \frac{2a}{1 - e^{-aT}} e^{-aT} \quad\text{(simplified)}$$

Then simulate under the stressed measure and weight paths by the likelihood ratio.

**Reference**: Glasserman, P. (2004). *Monte Carlo Methods in Financial Engineering*. Springer.

### 2.3 Parameter Shocks

Another approach: shock the model parameters themselves. For example, increasing the mean reversion level (through $\theta$) or decreasing mean reversion speed $a$ can produce paths that drift higher. However, these shocks may not be consistent with the initial curve. To maintain no-arbitrage, any parameter change should be accompanied by a recalibration of $\theta$ to the initial curve. Thus, shocking $a$ and $\sigma$ while keeping the initial curve fixed leads to a different $\theta(t)$, which might produce unexpected effects.

**Practical note**: In regulatory stress testing (e.g., CNBV, Basel), scenarios are often defined as parallel shifts or changes in the level, slope, and curvature of the yield curve. The most straightforward implementation is to apply the shift to the initial curve and recalibrate.

### 2.4 Combining Views with Scenario Probabilities

For a comprehensive stress test, you might define multiple scenarios with probabilities. For each scenario, you adjust the forward curve accordingly and simulate. Then aggregate results using scenario probabilities.

---

## 3. Implementation Steps for a 3-Year +5% Stress Test

1. **Obtain current Mexican yield curve** (e.g., Bonos M, Cetes, TIIE swap rates). Bootstrap zero-coupon rates and compute instantaneous forward rates $f(0,t)$ for $t$ up to 3 years.

2. **Apply the stress**: Define a stressed forward curve $f^*(0,t) = f(0,t) + 0.05$ (parallel shift). If you want a non-parallel shift (e.g., only long-term rates increase), adjust accordingly.

3. **Recalibrate $\theta^*(t)$** using the stressed forward curve:
   - Compute $\frac{\partial f^*(0,t)}{\partial T}$ numerically.
   - Compute $\theta^*(t) = \frac{\partial f^*(0,t)}{\partial T} + a f^*(0,t) + \frac{\sigma^2}{2a}(1 - e^{-2at})$.

4. **Simulate paths** under the stressed $\theta^*$ using Euler-Maruyama or exact simulation (since the Hull-White model has a closed-form transition density, you can simulate exactly without discretization error).

5. **Value the portfolio** under each simulated path to obtain the distribution of losses.

6. **Compare with baseline** (unstressed) simulation to quantify impact.

---

## 4. References

### Calibration

- Brigo, D., & Mercurio, F. (2006). *Interest Rate Models – Theory and Practice*. Springer.
- James, J., & Webber, N. (2000). *Interest Rate Modelling*. Wiley.
- Hull, J., & White, A. (1990). "Pricing Interest-Rate-Derivative Securities". *The Review of Financial Studies*.

### Stress Testing and Scenario Generation

- Basel Committee on Banking Supervision (2019). "Minimum capital requirements for market risk". Bank for International Settlements.
- Jorion, P. (2006). *Value at Risk: The New Benchmark for Managing Financial Risk*. McGraw-Hill.
- Glasserman, P. (2004). *Monte Carlo Methods in Financial Engineering*. Springer (Chapter on importance sampling).
- CNBV. "Disposiciones de Carácter General en Materia de Administración de Riesgos" (Mexican regulations).

### Mexican Market Specifics

- Banco de México. "Circular Única de Bancos".
- Sidaoui, J., et al. (2010). "The Mexican fixed income market: Structure and participants". *BIS Papers*, No. 53.

---

## 5. Python Code Snippets for Calibration

Below are example implementations of the calibration functions mentioned earlier. They are meant to be adapted.

```python
import numpy as np
from scipy.optimize import minimize
from scipy.interpolate import interp1d

def estimate_mean_reversion_mle(rates, dt):
    """
    Estimate a (mean reversion) and mu (long-term mean) for Vasicek model using MLE.
    rates: array of historical short rates
    dt: time step in years
    """
    n = len(rates)
    # We'll use the exact conditional distribution
    def neg_log_likelihood(params):
        a, mu, sigma = params
        if a <= 0 or sigma <= 0:
            return 1e10
        sum_ll = 0
        for i in range(n-1):
            r_t = rates[i]
            r_next = rates[i+1]
            # conditional mean and variance
            exp_a = np.exp(-a*dt)
            mean = r_t * exp_a + mu * (1 - exp_a)
            var = (sigma**2/(2*a)) * (1 - np.exp(-2*a*dt))
            if var <= 0:
                return 1e10
            ll = -0.5*np.log(2*np.pi*var) - 0.5*(r_next - mean)**2 / var
            sum_ll += ll
        return -sum_ll
    
    # initial guesses
    init_params = [0.1, np.mean(rates), np.std(np.diff(rates)/np.sqrt(dt))]
    result = minimize(neg_log_likelihood, init_params, bounds=[(0.001, None), (None, None), (0.001, None)])
    a, mu, sigma = result.x
    return a, mu, sigma

def estimate_volatility_garch(residuals):
    """
    Fit GARCH(1,1) to residuals and return unconditional volatility.
    """
    from arch import arch_model
    am = arch_model(residuals, vol='Garch', p=1, q=1)
    res = am.fit(update_freq=5, disp='off')
    omega = res.params['omega']
    alpha = res.params['alpha[1]']
    beta = res.params['beta[1]']
    uncond_var = omega / (1 - alpha - beta)
    return np.sqrt(uncond_var)

def calibrate_theta_to_curve(a, sigma, r0, forward_curve_func, t_grid):
    """
    Compute theta(t) on a grid using the formula:
    theta(t) = df(0,t)/dt + a * f(0,t) + sigma^2/(2a)*(1 - exp(-2a*t))
    forward_curve_func: function returning instantaneous forward rate at time t
    t_grid: array of times where theta is evaluated
    """
    dt_small = 1e-6
    theta = np.zeros_like(t_grid)
    for i, t in enumerate(t_grid):
        if t == 0:
            # limit as t->0, assume derivative from right
            f_plus = forward_curve_func(dt_small)
            f0 = forward_curve_func(0)
            df_dt = (f_plus - f0) / dt_small
        else:
            f_plus = forward_curve_func(t + dt_small)
            f_minus = forward_curve_func(t - dt_small)
            df_dt = (f_plus - f_minus) / (2*dt_small)
        f = forward_curve_func(t)
        theta[i] = df_dt + a * f + (sigma**2/(2*a)) * (1 - np.exp(-2*a*t))
    return theta
```

**Note**: For production use, consider more robust numerical differentiation and interpolation of the forward curve from discrete market data.

---

This document provides the theoretical and practical details needed to calibrate the Hull-White model and generate stressed trajectories. Use the references to deepen your understanding and adapt the code to your specific market data.

## Related
[[MKT_MOC]] · Home: [[_INDEX]]

#arm/mkt #type/theory