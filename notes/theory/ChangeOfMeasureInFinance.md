# Understanding Change of Measure in Finance: From Theory to Practice

## Introduction

In financial mathematics, changing the probability measure from the real-world measure \( \mathbf{P} \) to the risk-neutral measure \( \mathbf{Q} \) is a fundamental technique for derivative pricing. This document consolidates the explanation of why this change is required, what happens to a stochastic process under the change, and provides a general framework applicable to complex models such as stochastic volatility or interest rate models.

---

## Why Change the Measure? From \( \mathbf{P} \) to \( \mathbf{Q} \)

We operate in two main probability spaces:

* **The Real-World Measure \( \mathbf{P} \):** This is the actual, observable probability that governs the movement of asset prices. Under \( \mathbf{P} \), investors are risk-averse, demanding a higher expected return (the drift, \( \mu \)) for taking on more risk. Consequently, the discounted price of a risky asset is **not** a martingale; its future expected value, when discounted, is not simply its current price.

* **The Risk-Neutral Measure \( \mathbf{Q} \):** This is a mathematical construct, not an observable reality. It is an *equivalent martingale measure* (EMM). The cornerstone of modern pricing is the **Fundamental Theorem of Asset Pricing**, which states that in an arbitrage-free market, there exists at least one probability measure \( \mathbf{Q} \), equivalent to \( \mathbf{P} \), under which the discounted price of any traded asset becomes a martingale.

The crucial implication is that under \( \mathbf{Q} \), the expected return of every asset is the risk-free rate \( r \). This is the essence of risk-neutral pricing.

> "Girsanov's theorem is used to change the measure from the physical measure to the risk-neutral measure. Under the risk-neutral measure, the discounted stock price becomes a martingale, simplifying the pricing formula."

---

## What is Actually Happening to a Process?

When we change from \( \mathbf{P} \) to \( \mathbf{Q} \), we are not altering the underlying set of possible price paths. Instead, we are fundamentally **re-weighting the probabilities assigned to those paths**.

This transformation is formalized by the **Radon-Nikodym Derivative**, \( \frac{d\mathbf{Q}}{d\mathbf{P}} \). This is a random variable that defines the new measure \( \mathbf{Q} \) from the original measure \( \mathbf{P} \). In continuous-time finance, the primary tool for achieving this is the **Girsanov Theorem**.

Girsanov's theorem is the mechanism that performs the change of measure on a stochastic process. In the context of a Brownian motion, it shows how to shift the drift of the process under \( \mathbf{P} \) to achieve a driftless (martingale) process under \( \mathbf{Q} \). As a result, the only feature of a price process that remains unchanged is its **volatility (\( \sigma \))**. The change of measure effectively redefines the odds of different price paths to remove the risk premium, so all assets are priced as if they grow at the risk-free rate \( r \).

---

## A Complete Example: The Black-Scholes Model

This is the classic example that illustrates the entire process.

### 1. The Process Under the Real-World Measure \( \mathbf{P} \)

Under \( \mathbf{P} \), we model a stock price \( S_t \) as a geometric Brownian motion, driven by a \( \mathbf{P} \)-Brownian motion \( W_t^{\mathbf{P}} \):

$$ \frac{dS_t}{S_t} = \mu \, dt + \sigma \, dW_t^{\mathbf{P}} $$

Here, \( \mu \) is the expected return (drift) of the stock, which is greater than the risk-free rate \( r \).

### 2. Performing the Change of Measure (Girsanov Theorem)

Our goal is to find a new measure \( \mathbf{Q} \), equivalent to \( \mathbf{P} \), under which the discounted stock price \( \hat{S}_t = e^{-rt}S_t \) is a martingale. To do this, we define a new process \( \tilde{W}_t^{\mathbf{Q}} \) as:

$$ \tilde{W}_t^{\mathbf{Q}} = W_t^{\mathbf{P}} + \lambda t $$

Here, \( \lambda = \frac{\mu - r}{\sigma} \) is known as the **market price of risk** or the **Sharpe ratio**. This process \( \tilde{W}_t^{\mathbf{Q}} \) is a \( \mathbf{Q} \)-Brownian motion by Girsanov's theorem.

Now, we substitute this into the original SDE. Since \( dW_t^{\mathbf{P}} = d\tilde{W}_t^{\mathbf{Q}} - \lambda dt \), we get:

$$ \frac{dS_t}{S_t} = \mu \, dt + \sigma \left(d\tilde{W}_t^{\mathbf{Q}} - \lambda dt\right) $$
$$ \frac{dS_t}{S_t} = (\mu - \lambda\sigma) \, dt + \sigma \, d\tilde{W}_t^{\mathbf{Q}} $$

By substituting \( \lambda = \frac{\mu - r}{\sigma} \), the drift term simplifies dramatically:

$$ \frac{dS_t}{S_t} = r \, dt + \sigma \, d\tilde{W}_t^{\mathbf{Q}} $$

### 3. The Process Under the Risk-Neutral Measure \( \mathbf{Q} \)

This final SDE describes the exact same process under \( \mathbf{Q} \):

$$ \frac{dS_t}{S_t} = r \, dt + \sigma \, d\tilde{W}_t^{\mathbf{Q}} $$

The drift has been transformed from \( \mu \) to \( r \), and the Brownian motion is now a \( \mathbf{Q} \)-Brownian motion. The volatility \( \sigma \) remains unchanged.

### 4. What Are the Implications?

This change has profound consequences for pricing:

* **Simplified Valuation:** Any contingent claim \( V_T \) (like a European call option) can now be priced as its expected discounted payoff under \( \mathbf{Q} \), using the risk-free rate \( r \):
    $$ V_t = e^{-r(T-t)} \mathbb{E}^{\mathbf{Q}}[V_T | \mathcal{F}_t] $$
    This is the standard risk-neutral valuation formula.

* **Comparison of Measures \( \mathbf{P} \) vs. \( \mathbf{Q} \):**
    * **Under \( \mathbf{P} \) (The Real World):** The process has a drift of \( \mu \). This drift compensates investors for the risk of holding the stock. Because the discounted price is not a martingale, you cannot simply discount expected payoffs without a complex risk adjustment.
    * **Under \( \mathbf{Q} \) (The Pricing World):** The drift is \( r \), the same as a risk-free bank account. In this "risk-neutral" world, all assets are priced as if investors require no extra return for risk. The mathematical structure of a martingale makes the process far more tractable for pricing.

---

## General Framework for Changing Measure for Any Given Process

Moving beyond the Black-Scholes model to more complex models (e.g., stochastic volatility, Hull-White interest rate model) does not require a completely new set of rules. The general approach is built on a few key, mathematically rigorous steps.

### Step-by-Step Framework

#### Step 1: Start with the Real-World Dynamics (Under \( \mathbf{P} \))

Begin with a multi-factor SDE that describes the asset's behavior under the real-world measure \( \mathbf{P} \). For a general asset \( S_t \) and state variable(s) \( y_t \) (e.g., for stochastic volatility or interest rates), this could look like:

$$
\begin{aligned} 
\frac{dS_t}{S_t} &= \mu(t, S_t, y_t) \, dt + \sigma_S(t, S_t, y_t) \, dW_t^P \\ 
dy_t &= a(t, y_t) \, dt + b(t, y_t) \, dZ_t^P 
\end{aligned}
$$

where \( W_t^P \) and \( Z_t^P \) are correlated \( \mathbf{P} \)-Brownian motions.

#### Step 2: Define the Market Price of Risk Process(es) (\( \boldsymbol{\lambda}_t \))

To move to \( \mathbf{Q} \), you specify the market price of risk for each source of uncertainty. These processes, \( \lambda_t^{(i)} \), represent the excess return per unit of risk. In a multi-factor model, you'll have a vector \( \boldsymbol{\lambda}_t \).

A common choice is to assume \( \boldsymbol{\lambda}_t \) is a function of the state variables, like \( \lambda_t = \lambda(t, y_t) \). In more advanced models like the Hull-White framework, you might even use time-dependent functions to better fit market data.

#### Step 3: Construct the Radon-Nikodym Derivative (\( \frac{d\mathbf{Q}}{d\mathbf{P}} \))

This derivative formally defines the new measure \( \mathbf{Q} \) by re-weighting probabilities of future paths under \( \mathbf{P} \). It is built from the market price of risk process as an exponential martingale (stochastic exponential):

$$
\frac{d\mathbf{Q}}{d\mathbf{P}}\bigg|_{\mathcal{F}_t} = \mathcal{E}\left( -\int_0^t \boldsymbol{\lambda}_s \cdot d\mathbf{W}_s^{\mathbf{P}} \right) = \exp\left( -\frac12 \int_0^t \|\boldsymbol{\lambda}_s\|^2 ds - \int_0^t \boldsymbol{\lambda}_s \cdot d\mathbf{W}_s^{\mathbf{P}} \right)
$$

#### Step 4: Apply Girsanov's Theorem to Transform the Dynamics

Girsanov's theorem is the engine that changes the measure. It defines a new \( \mathbf{Q} \)-Brownian motion \( \mathbf{W}_t^{\mathbf{Q}} \) in terms of the old \( \mathbf{P} \)-Brownian motion and the market price of risk:

$$
d\mathbf{W}_t^{\mathbf{Q}} = d\mathbf{W}_t^{\mathbf{P}} + \boldsymbol{\lambda}_t \, dt
$$

By substituting \( d\mathbf{W}_t^{\mathbf{P}} = d\mathbf{W}_t^{\mathbf{Q}} - \boldsymbol{\lambda}_t dt \) into the \( \mathbf{P} \)-SDE, you obtain the dynamics under \( \mathbf{Q} \):

$$
\begin{aligned} 
\frac{dS_t}{S_t} &= \big(\mu(t, S_t, y_t) - \sigma_S(t, S_t, y_t) \cdot \boldsymbol{\lambda}_t \big) dt + \sigma_S(t, S_t, y_t) \, dW_t^{\mathbf{Q}} \\ 
dy_t &= \big(a(t, y_t) - b(t, y_t) \cdot \boldsymbol{\lambda}_t \big) dt + b(t, y_t) \, dZ_t^{\mathbf{Q}} 
\end{aligned}
$$

#### Step 5: Verify the Martingale Condition

For the new measure \( \mathbf{Q} \) to be valid (i.e., an Equivalent Local Martingale Measure, or ELMM), the Radon-Nikodym derivative must be a true martingale, not just a local martingale. This condition, often requiring checking criteria like Novikov's condition, is crucial and can be non-trivial to verify in models like Heston.

### Two Powerful, General Techniques

#### 1. The Change of Numeraire (Geman, El Karoui, Rochet, 1995)

The 1995 paper by Geman, El Karoui, and Rochet revolutionized the field by showing that changing the **numeraire** (the unit of account) is equivalent to changing the probability measure. The core idea is: for any strictly positive price process \( N_t \) (the new numeraire), there exists an equivalent measure \( \mathbf{Q}^N \) under which all asset prices, when expressed relative to \( N_t \), are martingales. This allows you to pick the most convenient numeraire for a pricing problem. For example, when pricing interest rate derivatives, the **forward measure** (using a zero-coupon bond as numeraire) or the **swap measure** (using an annuity as numeraire) can dramatically simplify calculations.

#### 2. The Esscher Transform (Gerber & Shiu, 1994)

In markets that are **incomplete** (where not all risks can be hedged), there are infinitely many possible risk-neutral measures \( \mathbf{Q} \). The **Esscher transform** provides a principled way to select one. It is a widely used technique in actuarial science and for pricing options in markets driven by **Lévy processes**.

---

## Bibliography

The following references are drawn from the academic literature and standard textbooks:

1.  **Geman, H., El Karoui, N., & Rochet, J. C. (1995).** Changes of numeraire, changes of probability measure and option pricing. *Journal of Applied Probability*, 32(2), 443–458.

2.  **Gerber, H. U., & Shiu, E. S. W. (1994).** Option pricing by Esscher transforms. *Transactions of the Society of Actuaries*, 46, 99–191.

3.  **Hagan, P. S., & Lesniewski, A. (2022).** *Girsanov, Numeraires, and All That*. Working paper. Available at SSRN.

4.  **Brigo, D., & Mercurio, F. (2006).** *Interest Rate Models - Theory and Practice: With Smile, Inflation and Credit* (2nd ed.). Springer Finance.

5.  **Berninger, C., & Pfeiffer, F. (2021).** The Gauss2++ Model: A comparison of different measure change techniques for consistent valuation. *Risk Magazine*, March 2021.

6.  **Wong, B., & Heyde, C. C. (2006).** On changes of measure in stochastic volatility models. *Journal of Applied Probability*, 43(2), 518–535.

7.  **Desmettre, S., Gouriéroux, C., & Le Fol, G. (2021).** Change of drift in one-dimensional diffusions. *Journal of Financial Econometrics*, 19(3), 463–491.

8.  **Björk, T. (2019).** *Arbitrage Theory in Continuous Time* (4th ed.). Oxford University Press.

9.  **Karatzas, I., & Shreve, S. E. (1998).** *Methods of Mathematical Finance*. Springer.

## Related
[[MKT_MOC]] · Home: [[_INDEX]]

#arm/mkt #type/theory