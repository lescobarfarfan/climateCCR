# Hull-White Model: Theory, Implementation, and Market Risk Applications

## Table of Contents

1. [Theoretical Foundation](#theoretical-foundation)
   - [Stochastic Differential Equation](#stochastic-differential-equation)
   - [Key Properties](#key-properties)
   - [The $\theta(t)$ Function](#the-thetat-function)
2. [Advanced Monte Carlo Techniques](#advanced-monte-carlo-techniques)
   - [Antithetic Variates](#antithetic-variates)
   - [Control Variates](#control-variates)
   - [Importance Sampling](#importance-sampling)
   - [Moment Matching](#moment-matching)
   - [Quasi-Monte Carlo](#quasi-monte-carlo)
   - [Multilevel Monte Carlo](#multilevel-monte-carlo)
3. [Calibration of Hull-White Parameters](#calibration-of-hull-white-parameters)
   - [Estimating Mean Reversion Speed ($a$)](#estimating-mean-reversion-speed-a)
   - [Estimating Volatility ($\sigma$)](#estimating-volatility-sigma)
   - [Calibrating $\theta(t)$ to the Initial Term Structure](#calibrating-thetat-to-the-initial-term-structure)
4. [Stress Testing for Market Risk: Mexican Market Application](#stress-testing-for-market-risk-mexican-market-application)
   - [Market Context](#market-context)
   - [Generating Stress Scenarios](#generating-stress-scenarios)
   - [Example: 3‑Year +5% Rate Increase](#example-3year-5-rate-increase)
5. [Python Implementation](#python-implementation)
   - [Script 1: `hull_white_base.py`](#script-1-hull_white_basepy)
   - [Script 2: `hull_white_advanced_mc.py`](#script-2-hull_white_advanced_mcpy)
   - [Script 3: `mexican_market_risk.py`](#script-3-mexican_market_riskpy)
   - [Script 4: `examples.py`](#script-4-examplespy)
6. [References](#references)

---

## 1. Theoretical Foundation

### Stochastic Differential Equation

The one‑factor Hull‑White model (extended Vasicek) describes the evolution of the short rate $r(t)$ under the risk‑neutral measure:

$$
dr(t) = [\theta(t) - a\, r(t)]\,dt + \sigma\, dW(t)
$$

where  
- $a > 0$ is the speed of mean reversion,  
- $\sigma > 0$ is the instantaneous volatility,  
- $\theta(t)$ is a deterministic function chosen to fit the initial term structure,  
- $dW(t)$ is a standard Wiener process.

### Key Properties

- **Mean reversion:** The process is pulled towards the time‑dependent level $\theta(t)/a$.
- **Normality:** Conditionally on $\mathcal{F}_s$, $r(t)$ is normally distributed with

  $$
  \mathbb{E}[r(t)|\mathcal{F}_s] = r(s)e^{-a(t-s)} + \int_s^t e^{-a(t-u)}\theta(u)\,du,
  $$
  $$
  \operatorname{Var}[r(t)|\mathcal{F}_s] = \frac{\sigma^2}{2a}\left(1-e^{-2a(t-s)}\right).
  $$

- **Bond prices:** Zero‑coupon bond prices are affine in $r(t)$:

  $$
  P(t,T) = A(t,T)\,e^{-B(t,T)r(t)},
  $$
  with
  $$
  B(t,T)=\frac{1-e^{-a(T-t)}}{a},\qquad 
  A(t,T)=\frac{P(0,T)}{P(0,t)}\exp\!\left\{B(t,T)f(0,t)-\frac{\sigma^2}{4a}B(t,T)^2(1-e^{-2at})\right\}.
  $$

### The $\theta(t)$ Function

$\theta(t)$ is chosen so that the model reproduces the observed initial forward curve $f(0,t)$:

$$
\theta(t) = \frac{\partial f(0,t)}{\partial T} + a\,f(0,t) + \frac{\sigma^2}{2a}\bigl(1-e^{-2at}\bigr).
$$

---

## 2. Advanced Monte Carlo Techniques

### Antithetic Variates

**Principle:** For each path generated with random increments $\epsilon_i$, generate a second path with $-\epsilon_i$. The negative correlation reduces variance.

**Mathematical foundation:**  
If $\hat{\theta}_1,\hat{\theta}_2$ are two estimators with same variance $\sigma^2$ and correlation $\rho$, the average has variance $\frac{\sigma^2}{2}(1+\rho)$. With $\rho=-1$, variance becomes zero.

**Reference:** Hammersley & Morton (1956).

### Control Variates

**Principle:** Use a known expectation of a related quantity $X$ to correct the estimator of $Y$:

$$
Y_{\text{control}} = Y - \beta\,(X - \mathbb{E}[X]).
$$

The optimal coefficient is $\beta^* = \operatorname{Cov}(Y,X)/\operatorname{Var}(X)$, yielding variance reduction factor $1-\rho_{YX}^2$.

**Reference:** Lavenberg & Welch (1981).

### Importance Sampling

**Principle:** Change the drift to make “important” outcomes more likely, then reweight paths by the likelihood ratio (Radon‑Nikodym derivative). For a Girsanov transformation with constant drift $\gamma$:

$$
\frac{d\mathbb{P}}{d\mathbb{Q}} = \exp\!\left(-\int_0^T \gamma\,dW(t)-\frac12\gamma^2 T\right).
$$

**Reference:** Glynn & Iglehart (1989).

### Moment Matching

**Principle:** Adjust simulated paths so that their sample moments exactly match theoretical moments. For mean $\mu$ and variance $\sigma^2$:

$$
X_i^{\text{adj}} = \mu + \frac{\sigma}{S}(X_i-\bar{X}).
$$

**Reference:** Barraquand (1995).

### Quasi-Monte Carlo

**Principle:** Replace pseudo‑random numbers with low‑discrepancy sequences (e.g., Sobol). The integration error is bounded by $O((\log N)^d/N)$ compared to $O(1/\sqrt{N})$ for standard MC.

**Reference:** Niederreiter (1992).

### Multilevel Monte Carlo

**Principle:** Combine simulations on multiple time grids to reduce overall cost. Write the expectation on the finest level as a telescoping sum:

$$
\mathbb{E}[P_L] = \mathbb{E}[P_0] + \sum_{\ell=1}^L \mathbb{E}[P_\ell-P_{\ell-1}].
$$

Optimal sample allocation minimises total cost for a given variance.

**Reference:** Giles (2008).

---

## 3. Calibration of Hull-White Parameters

### Estimating Mean Reversion Speed ($a$)

#### Linear Regression (AR(1) approximation)

From the discrete‑time approximation $r_{t+\Delta t} = \alpha + \beta r_t + \eta_t$, we have $a = (1-\beta)/\Delta t$ and $\mu = \alpha/(1-\beta)$.

#### Maximum Likelihood Estimation (MLE)

For the Vasicek model (constant $\theta$), the conditional density is normal. Maximising the log‑likelihood gives estimates of $a$, $\mu$, and $\sigma$.

**Reference:** Brigo & Mercurio (2006).

### Estimating Volatility ($\sigma$)

#### Historical Volatility

$$
\hat{\sigma} = \sqrt{\frac{1}{(n-1)\Delta t}\sum_{t=1}^{n-1}(\Delta r_t - \overline{\Delta r})^2}.
$$

#### GARCH Models

Fit a GARCH(1,1) to residuals to capture time‑varying volatility; the unconditional volatility is $\sqrt{\omega/(1-\alpha-\beta)}$.

**Reference:** Bollerslev (1986).

### Calibrating $\theta(t)$ to the Initial Term Structure

1. Bootstrap the instantaneous forward curve $f(0,t)$ from market instruments.
2. Compute its derivative numerically.
3. Use the formula
   $$
   \theta(t) = \frac{\partial f(0,t)}{\partial T} + a f(0,t) + \frac{\sigma^2}{2a}\bigl(1-e^{-2at}\bigr).
   $$

**Reference:** Hull & White (1990).

---

## 4. Stress Testing for Market Risk: Mexican Market Application

### Market Context

- **Government bonds:** Bonos M (fixed rate), Cetes (zero‑coupon), Udibonos (inflation‑linked)
- **Interbank rate:** TIIE
- **Corporate bonds:** various tenors and credit spreads
- **Regulators:** CNBV, Banco de México

### Generating Stress Scenarios

Common stress types (aligned with CNBV and Basel guidelines):

- **Parallel shifts:** e.g., +200 bps (Banxico tightening)
- **Non‑parallel shifts:** steepening (short rates +100, long rates +300), flattening (short +300, long +100)
- **Volatility shock:** increase $\sigma$ by 50%
- **Mean reversion shock:** decrease $a$ by 50% (persistence)

### Example: 3‑Year +5% Rate Increase

Suppose we want to simulate a scenario where interest rates are on average 5% higher over the next three years. The simplest approach:

1. **Shift the initial forward curve** by +500 bps (parallel shift):  
   $f^*(0,t) = f(0,t) + 0.05$.
2. **Recalibrate $\theta^*(t)$** using the stressed curve.
3. **Simulate paths** under $\theta^*(t)$.
4. **Compare** portfolio values under the stressed and baseline scenarios.

**Why this works:** The Hull‑White model is arbitrage‑free by construction; changing the initial curve and recalibrating $\theta$ produces a new arbitrage‑free world where expected future rates are higher.

**Alternative – Importance Sampling:** To specifically target a higher terminal rate, one can use importance sampling with a drift adjustment. However, for regulatory stress tests, the shifted‑curve method is standard.

**Reference:** Basel Committee (2019), Jorion (2006).

---

## 5. Python Implementation

Below are four Python scripts that together implement the Hull‑White model, advanced Monte Carlo techniques, calibration routines, and a Mexican market risk example.

### Script 1: `hull_white_base.py`

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
        """
        Compute θ(t). If forward_curve is None, assume flat forward curve at r0.
        """
        if forward_curve is None:
            # flat forward curve approximation
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
        """
        Euler-Maruyama simulation.
        """
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

### Script 2: `hull_white_advanced_mc.py`

```python
import numpy as np
from scipy.stats import norm
from .hull_white_base import HullWhiteModel

class HullWhiteAdvancedMC(HullWhiteModel):
    """Extends HullWhiteModel with advanced Monte Carlo techniques."""

    def simulate_antithetic(self, T: float, n_steps: int, n_paths: int,
                            forward_curve=None):
        dt = T / n_steps
        time = np.linspace(0, T, n_steps+1)
        n_pairs = n_paths // 2
        rates = np.zeros((2*n_pairs, n_steps+1))
        rates[:, 0] = self.r0
        for i in range(n_steps):
            t = time[i]
            theta_t = self.theta(t, forward_curve)
            drift = theta_t - self.a * rates[::2, i]  # use every other path
            Z = np.random.normal(0, 1, n_pairs)
            dW_plus = Z * np.sqrt(dt)
            dW_minus = -Z * np.sqrt(dt)
            rates[::2, i+1] = rates[::2, i] + drift * dt + self.sigma * dW_plus
            rates[1::2, i+1] = rates[1::2, i] + drift * dt + self.sigma * dW_minus
        return time, rates

    def simulate_control_variate(self, T: float, n_steps: int, n_paths: int,
                                 forward_curve=None):
        # Use integrated short rate as control variate.
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
            integral += 0.5 * (rates[:, i] + rates[:, i+1]) * dt  # trapezoidal

        # Known expectation of integral under risk-neutral measure (flat curve approx)
        a, sigma, r0 = self.a, self.sigma, self.r0
        exp_integral = (r0/a)*(1-np.exp(-a*T)) + (sigma**2/(2*a**2))*(T - (2/a)*(1-np.exp(-a*T)) + (1/(2*a))*(1-np.exp(-2*a*T)))

        # Compute optimal beta
        y = rates[:, -1]
        cov = np.cov(integral, y)[0,1]
        var_x = np.var(integral)
        beta = cov / var_x if var_x > 0 else 0
        y_adj = y - beta * (integral - exp_integral)
        return time, y_adj  # returns only terminal rates for simplicity

    # Other techniques (importance sampling, QMC, MLMC) can be added similarly.
```

### Script 3: `mexican_market_risk.py`

```python
import numpy as np
from scipy.optimize import minimize
from scipy.interpolate import interp1d
from .hull_white_base import HullWhiteModel

# ----------------------------------------------------------------------
# Calibration helpers
# ----------------------------------------------------------------------
def estimate_mean_reversion_mle(rates: np.ndarray, dt: float) -> tuple:
    """
    MLE for Vasicek model (constant θ) to estimate a, μ, σ.
    rates: historical short rate series.
    dt: time step in years.
    """
    n = len(rates)
    def neg_log_lik(params):
        a, mu, sigma = params
        if a <= 0 or sigma <= 0:
            return 1e10
        sum_ll = 0.0
        for i in range(n-1):
            r_t = rates[i]
            r_n = rates[i+1]
            exp_a = np.exp(-a*dt)
            mean = r_t * exp_a + mu * (1 - exp_a)
            var = (sigma**2/(2*a)) * (1 - np.exp(-2*a*dt))
            if var <= 0:
                return 1e10
            ll = -0.5*np.log(2*np.pi*var) - 0.5*(r_n - mean)**2/var
            sum_ll += ll
        return -sum_ll
    init = [0.1, np.mean(rates), np.std(np.diff(rates)/np.sqrt(dt))]
    res = minimize(neg_log_lik, init, bounds=[(1e-6, None), (None, None), (1e-6, None)])
    return res.x

def calibrate_theta(a: float, sigma: float, r0: float,
                    forward_curve: callable, t_grid: np.ndarray) -> np.ndarray:
    """
    Compute θ(t) on t_grid using the theoretical formula.
    """
    dt_small = 1e-6
    theta = np.zeros_like(t_grid)
    for i, t in enumerate(t_grid):
        if t < dt_small:
            df = (forward_curve(dt_small) - forward_curve(0)) / dt_small
        else:
            df = (forward_curve(t+dt_small) - forward_curve(t-dt_small)) / (2*dt_small)
        f = forward_curve(t)
        theta[i] = df + a*f + (sigma**2/(2*a))*(1 - np.exp(-2*a*t))
    return theta

# ----------------------------------------------------------------------
# Stress scenario generation
# ----------------------------------------------------------------------
def stressed_forward_curve(base_curve: callable, shift_bps: float,
                           shift_type: str = 'parallel', **kwargs):
    """
    Return a stressed forward curve function.
    shift_type: 'parallel' or 'steepener' (requires short_shift, long_shift)
    """
    if shift_type == 'parallel':
        def stressed(t):
            return base_curve(t) + shift_bps / 10000.0
    elif shift_type == 'steepener':
        short_shift = kwargs.get('short_shift', 0.0) / 10000.0
        long_shift = kwargs.get('long_shift', 0.0) / 10000.0
        # linear interpolation between short and long tenors (e.g., 2y and 10y)
        short_tenor = 2.0
        long_tenor = 10.0
        def stressed(t):
            base = base_curve(t)
            if t <= short_tenor:
                return base + short_shift
            elif t >= long_tenor:
                return base + long_shift
            else:
                weight = (t - short_tenor) / (long_tenor - short_tenor)
                shift = short_shift + weight * (long_shift - short_shift)
                return base + shift
    else:
        raise ValueError(f"Unknown shift_type: {shift_type}")
    return stressed

def simulate_stress_scenario(model: HullWhiteModel,
                             base_forward_curve: callable,
                             shift_bps: float,
                             shift_type: str,
                             T: float,
                             n_steps: int,
                             n_paths: int,
                             **kwargs):
    """
    Generate stressed paths by shifting the forward curve and recalibrating θ.
    """
    stressed_fwd = stressed_forward_curve(base_forward_curve, shift_bps, shift_type, **kwargs)
    # We need to recompute θ(t) for each time step – in practice we precompute on a grid.
    time, rates = model.simulate_euler(T, n_steps, n_paths, forward_curve=stressed_fwd)
    return time, rates
```

### Script 4: `examples.py`

```python
import numpy as np
import matplotlib.pyplot as plt
from hull_white_base import HullWhiteModel
from hull_white_advanced_mc import HullWhiteAdvancedMC
from mexican_market_risk import estimate_mean_reversion_mle, calibrate_theta, simulate_stress_scenario

# Example 1: Basic simulation
model = HullWhiteModel(a=0.1, sigma=0.02, r0=0.05)
time, rates = model.simulate_euler(T=5.0, n_steps=250, n_paths=100)
plt.plot(time, rates.T, lw=0.5, alpha=0.3)
plt.xlabel('Time (years)')
plt.ylabel('Short rate')
plt.title('Hull-White paths (Euler)')
plt.show()

# Example 2: Antithetic variates
adv_model = HullWhiteAdvancedMC(a=0.1, sigma=0.02, r0=0.05)
time, rates_anti = adv_model.simulate_antithetic(T=5.0, n_steps=250, n_paths=100)
plt.plot(time, rates_anti.T, lw=0.5, alpha=0.3)
plt.title('Antithetic paths')
plt.show()

# Example 3: Calibration with synthetic data
np.random.seed(42)
true_a, true_sigma, true_r0 = 0.15, 0.015, 0.04
dt = 1/252   # daily
n_years = 5
n_obs = int(n_years / dt)
# generate Vasicek paths
r = np.zeros(n_obs)
r[0] = true_r0
for i in range(1, n_obs):
    dW = np.random.normal(0, np.sqrt(dt))
    r[i] = r[i-1] + true_a*(true_r0 - r[i-1])*dt + true_sigma*dW

a_est, mu_est, sigma_est = estimate_mean_reversion_mle(r, dt)
print(f"True a: {true_a:.4f}, Estimated a: {a_est:.4f}")
print(f"True sigma: {true_sigma:.4f}, Estimated sigma: {sigma_est:.4f}")

# Example 4: Stress test (+200bps parallel shift over 3 years)
base_fwd = lambda t: 0.05 + 0.005*t   # arbitrary increasing forward curve
model_stress = HullWhiteModel(a=0.1, sigma=0.02, r0=base_fwd(0))
time_stress, rates_stress = simulate_stress_scenario(
    model_stress, base_fwd, shift_bps=200, shift_type='parallel',
    T=3.0, n_steps=250, n_paths=500
)
# Compare with baseline (no shift)
_, rates_base = model_stress.simulate_euler(T=3.0, n_steps=250, n_paths=500, forward_curve=base_fwd)

plt.figure()
plt.plot(time_stress, rates_base.T, 'b', alpha=0.2, label='Baseline')
plt.plot(time_stress, rates_stress.T, 'r', alpha=0.2, label='+200bps')
plt.legend()
plt.title('Stress scenario vs baseline')
plt.show()
```

---

## 6. References

### Original Papers
- Hull, J., & White, A. (1990). *Pricing Interest-Rate-Derivative Securities*. The Review of Financial Studies, 3(4), 573–592.
- Hull, J., & White, A. (1994). *Numerical procedures for implementing term structure models I: Single-factor models*. Journal of Derivatives, 2(1), 7–16.

### Books
- Brigo, D., & Mercurio, F. (2006). *Interest Rate Models – Theory and Practice* (2nd ed.). Springer.
- Glasserman, P. (2004). *Monte Carlo Methods in Financial Engineering*. Springer.
- Jorion, P. (2006). *Value at Risk: The New Benchmark for Managing Financial Risk* (3rd ed.). McGraw‑Hill.

### Advanced Monte Carlo
- Hammersley, J. M., & Morton, K. W. (1956). *A new Monte Carlo technique: antithetic variates*. Mathematical Proceedings of the Cambridge Philosophical Society, 52(3), 449–475.
- Lavenberg, S. S., & Welch, P. D. (1981). *A perspective on the use of control variables to increase the efficiency of Monte Carlo simulations*. Management Science, 27(3), 322–335.
- Glynn, P. W., & Iglehart, D. L. (1989). *Importance sampling for stochastic simulations*. Management Science, 35(11), 1367–1392.
- Niederreiter, H. (1992). *Random Number Generation and Quasi-Monte Carlo Methods*. SIAM.
- Giles, M. B. (2008). *Multilevel Monte Carlo path simulation*. Operations Research, 56(3), 607–617.

### Calibration & Stress Testing
- Bollerslev, T. (1986). *Generalized autoregressive conditional heteroskedasticity*. Journal of Econometrics, 31(3), 307–327.
- Basel Committee on Banking Supervision (2019). *Minimum capital requirements for market risk*. Bank for International Settlements.
- CNBV. *Disposiciones de Carácter General en Materia de Administración de Riesgos* (Mexican regulations).
- Banco de México. *Circular Única de Bancos*.

## Related
[[MKT_MOC]] · Home: [[_INDEX]]

#arm/mkt #type/theory