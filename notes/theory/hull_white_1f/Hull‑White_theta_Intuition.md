# Hull‑White Model: Theta(t) Intuition, Discount Factor Calculation, and Real‑World Measure Simulation

This document provides a detailed explanation of three fundamental concepts in implementing the Hull‑White interest rate model for portfolio pricing and risk management:

1. The role and intuition behind the time‑dependent function $\theta(t)$
2. Numerical approximation of discount factors from simulated short rate paths
3. Modifying the model for simulation under the real‑world $\mathbb{P}$ measure for stress testing

Each section includes mathematical foundations, practical implementation guidance, and relevant citations to the academic literature.

---

## 1. The Intuition Behind $\theta(t)$ and Its Role in Bond Portfolio Pricing

### 1.1 What $\theta(t)$ Represents

The Hull‑White model extends the Vasicek model by introducing a time‑dependent function $\theta(t)$ in the drift term:

$$dr(t) = [\theta(t) - a \cdot r(t)]dt + \sigma dW(t)$$

**The crucial insight** is that $\theta(t)$ is **not** a set of different values for different bond maturities. Rather, it is a single deterministic function of the current time $t$ that is calibrated **once** to ensure the model reproduces the entire initial yield curve observed in the market today .

### 1.2 Why One $\theta(t)$ Serves All Bond Maturities

The short rate $r(t)$ is a single stochastic process that drives the entire term structure. From one simulated path of $r(t)$, you can compute discount factors for **any** future date, and therefore price bonds of **all** maturities. The function $\theta(t)$ is the "tuning knob" that makes the model arbitrage‑free with respect to current market prices.

Mathematically, $\theta(t)$ is chosen so that the risk‑neutral expectation matches observed zero‑coupon bond prices :

$$P^M(0,T) = \mathbb{E}^{\mathbb{Q}}\left[\exp\left(-\int_0^T r(s)ds\right)\right] \quad \text{for all } T$$

This condition must hold for **every** maturity $T$, and a single $\theta(t)$ function (together with parameters $a$ and $\sigma$) is sufficient to satisfy all these constraints simultaneously .

### 1.3 The Calibration Formula

Given the initial instantaneous forward curve $f(0,t)$, $\theta(t)$ is given by :

$$\theta(t) = \frac{\partial f(0,t)}{\partial T} + a f(0,t) + \frac{\sigma^2}{2a}(1 - e^{-2at})$$

Once calibrated, this $\theta(t)$ is used in the SDE for all future simulations, regardless of which bonds you intend to price.

**Key takeaway:** You do **not** simulate different $\theta$ processes for different bond maturities. You simulate **one** $r(t)$ process, and from it derive discount factors for all cash flow dates.

---

## 2. Numerical Approximation of Discount Factors from Simulated Paths

### 2.1 The Discount Factor Formula

From a simulated path of the short rate $r(t)$, the discount factor for a cash flow occurring at time $T$ is:

$$D(0,T) = \exp\left(-\int_0^T r(s)ds\right)$$

In discrete‑time simulation, we have values $r(t_0), r(t_1), \ldots, r(t_N)$ at times $t_0=0, t_1, \ldots, t_N=T$. The integral must be approximated numerically.

### 2.2 Numerical Integration Methods

#### Trapezoidal Rule
The trapezoidal rule approximates the integral by averaging the values at the beginning and end of each time interval :

$$\int_0^T r(s)ds \approx \sum_{i=0}^{N-1} \frac{r(t_i) + r(t_{i+1})}{2} \Delta t_i$$

where $\Delta t_i = t_{i+1} - t_i$.

**Why the trapezoidal rule is preferred:** For smooth functions, its error is $O(\Delta t^2)$, compared to $O(\Delta t)$ for the rectangle rule. In interest rate simulation, the trapezoidal rule provides better accuracy for a given time step, which is particularly important when pricing instruments sensitive to the entire path of rates .

#### Rectangle Rule (Left or Right)
A simpler but less accurate alternative:

$$\int_0^T r(s)ds \approx \sum_{i=0}^{N-1} r(t_i) \Delta t_i \quad \text{(left rectangle)}$$

$$\int_0^T r(s)ds \approx \sum_{i=1}^{N} r(t_i) \Delta t_{i-1} \quad \text{(right rectangle)}$$

### 2.3 Implementation Strategy

For each simulated path:

1. Maintain a cumulative integral $I(t_i) = \int_0^{t_i} r(s)ds$ as you progress through time steps
2. Update using the chosen quadrature rule
3. At any cash flow date $t_j$, the discount factor is $\exp(-I(t_j))$

For bonds with multiple cash flows (e.g., coupon bonds), you need discount factors to each payment date. You can either store the cumulative integral at each time step or recompute integrals when needed.

**Reference:** Yasuoka (2018) provides comprehensive coverage of numerical procedures for interest rate models, including integration techniques for discount factor calculation in Monte Carlo simulation .

---

## 3. Simulating Under the Real‑World $\mathbb{P}$ Measure

### 3.1 Risk‑Neutral vs. Real‑World Measures

The Hull‑White SDE presented earlier is under the **risk‑neutral measure** $\mathbb{Q}$, used for pricing derivatives. Under this measure, all assets grow at the risk‑free rate $r(t)$, and the drift contains $\theta(t)$ calibrated to fit today's yield curve.

For risk management applications—particularly stress testing and scenario analysis—you may need simulations under the **real‑world (physical) measure** $\mathbb{P}$, which reflects actual historical dynamics of interest rates .

### 3.2 The Real‑World SDE

Under the real‑world measure, the Hull‑White SDE becomes :

$$dr(t) = [\theta(t) - a\,r(t) + \lambda(t)\sigma]\,dt + \sigma\,dW^{\mathbb{P}}(t)$$

where $\lambda(t)$ is the **market price of interest rate risk**. This term adjusts the drift to account for the risk premium demanded by investors.

### 3.3 The Market Price of Risk

The market price of risk $\lambda(t)$ represents the excess return per unit of risk. It links the two measures through the Girsanov transformation:

$$dW^{\mathbb{Q}}(t) = dW^{\mathbb{P}}(t) - \lambda(t)dt$$

**Key properties** :
- $\lambda(t)$ can be time‑dependent or constant
- Empirical studies often find a **negative price tendency** for interest rate risk, meaning $\lambda(t)$ tends to be negative in many markets
- For the Hull‑White model, estimation of $\lambda(t)$ typically uses historical data on bond yields or forward rates

### 3.4 Estimating the Market Price of Risk

Yasuoka (2018) presents two approaches for estimating $\lambda(t)$ in the Hull‑White framework :

1. **Short rate dynamics approach:** Analyze historical time series of short rates to extract the drift under $\mathbb{P}$
2. **Forward rate dynamics approach:** Work within the HJM framework and estimate $\lambda(t)$ from the historical evolution of the entire forward curve

For practical implementation, a common simplification is to assume $\lambda$ is constant. This constant can be estimated as :

$$\lambda = \frac{\mu_{\text{excess}}}{\sigma}$$

where $\mu_{\text{excess}}$ is the historical average excess return of a long‑term bond over the short rate.

### 3.5 Numerical Procedure for $\mathbb{P}$‑Measure Simulation

The steps for simulating under the real‑world measure are :

1. **Calibrate $\theta(t)$** to the current yield curve using the standard risk‑neutral formula (this remains unchanged, as $\theta(t)$ ensures no‑arbitrage relative to today's prices)

2. **Estimate $\lambda$** from historical data:
   - Collect historical time series of interest rates
   - Estimate the drift under $\mathbb{P}$ (e.g., using maximum likelihood)
   - Infer $\lambda$ from the difference between $\mathbb{P}$ and $\mathbb{Q}$ drifts

3. **Simulate paths** using the adjusted SDE:
   $$r(t+\Delta t) = r(t) + [\theta(t) - a r(t) + \lambda\sigma]\Delta t + \sigma \sqrt{\Delta t}\,\epsilon$$

4. **For stress testing**, combine the $\mathbb{P}$‑measure simulation with shocked parameters or initial curves to create "stressed real‑world" scenarios 

### 3.6 Practical Considerations for Stress Testing

For regulatory stress testing (e.g., under CNBV or Basel guidelines), a common approach is to :

- Use $\mathbb{P}$‑measure dynamics for the central (baseline) scenario
- Apply deterministic shocks to the initial yield curve and/or parameters for stressed scenarios
- Recalibrate $\theta(t)$ under each stressed initial curve to maintain no‑arbitrage

This approach, detailed in Yasuoka (2018), allows you to combine historically realistic dynamics with specific stress assumptions .

---

## References

1. **Yasuoka, T. (2018).** *Interest Rate Modeling for Risk Management: Market Price of Interest Rate Risk* (2nd ed.). Bentham Science Publishers. [ISBN: 978-1-68108-689-7] 

2. **Hull, J., & White, A. (1990).** "Pricing Interest‑Rate‑Derivative Securities". *The Review of Financial Studies*, 3(4), 573–592. 

3. **Brigo, D., & Mercurio, F. (2006).** *Interest Rate Models – Theory and Practice* (2nd ed.). Springer. 

4. **Lund University Mathematical Statistics Glossary.** "Hull-White model." [Online]. Available: https://www.maths.lth.se/matstat/research/mathematicalfinance/glossary/ [Accessed: 2026]. 

5. **Yasuoka, T. (2018).** "Chapter 8: Real-World Model In The Hull{White Model". In *Interest Rate Modeling for Risk Management* (2nd ed.), pp. 175–194. Bentham Science Publishers. 

6. **Yasuoka, T. (2018).** "Chapter 10: Numerical Examples". In *Interest Rate Modeling for Risk Management* (2nd ed.), pp. 235–279. Bentham Science Publishers. 

7. **Basel Committee on Banking Supervision (2019).** *Minimum capital requirements for market risk*. Bank for International Settlements.

8. **Jorion, P. (2006).** *Value at Risk: The New Benchmark for Managing Financial Risk* (3rd ed.). McGraw‑Hill.

## Related
[[MKT_MOC]] · Home: [[_INDEX]]

#arm/mkt #type/theory