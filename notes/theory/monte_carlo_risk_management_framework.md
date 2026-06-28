# Monte Carlo Simulation Frameworks for Quantitative Finance Risk Management

## Risk Factor Generation, Instrument Pricing, and Counterparty Credit Risk

---

## Table of Contents

1. [Introduction and Overview](#1-introduction-and-overview)
2. [Risk Factor Simulation Models](#2-risk-factor-simulation-models)
3. [Counterparty Credit Risk Framework](#3-counterparty-credit-risk-framework)
4. [XVA Valuation Adjustments](#4-xva-valuation-adjustments)
5. [American Monte Carlo Methods](#5-american-monte-carlo-methods)
6. [Variance Reduction Techniques](#6-variance-reduction-techniques)
7. [High-Performance Computing](#7-high-performance-computing)
8. [Machine Learning Integration](#8-machine-learning-integration)
9. [Implementation Considerations](#9-implementation-considerations)
10. [Key References](#10-key-references)

---

## 1. Introduction and Overview

### 1.1 The Role of Monte Carlo in Risk Management

Monte Carlo simulation has become the foundational methodology for pricing complex derivatives, measuring counterparty credit risk, and computing valuation adjustments in quantitative finance. The approach is particularly valuable when:

- Analytical solutions are unavailable (path-dependent options, exotic derivatives)
- High-dimensional problems preclude finite difference methods
- Portfolio-level aggregation with netting and collateral is required
- Regulatory stress testing demands scenario-based analysis

### 1.2 Core Framework Architecture

A comprehensive Monte Carlo risk engine typically consists of:

```
┌─────────────────────────────────────────────────────────────────┐
│                    MONTE CARLO RISK ENGINE                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ Risk Factor │ →  │ Instrument  │ →  │  Exposure   │         │
│  │ Simulation  │    │  Valuation  │    │ Aggregation │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         ↓                  ↓                  ↓                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Hybrid    │    │  American   │    │   Netting   │         │
│  │   Models    │    │ Monte Carlo │    │ & Collateral│         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────┐      │
│  │                    XVA CALCULATION                     │      │
│  │  CVA | DVA | FVA | MVA | KVA | ColVA                  │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Key Risk Measures

| Measure | Description | Calculation Horizon |
|---------|-------------|---------------------|
| **EE** (Expected Exposure) | Average positive exposure at future date | Each simulation date |
| **EPE** (Expected Positive Exposure) | Time-weighted average of EE | Trade lifetime |
| **ENE** (Expected Negative Exposure) | Average negative exposure | Trade lifetime |
| **PFE** (Potential Future Exposure) | Exposure at specified quantile (e.g., 97.5%) | Each simulation date |
| **EEPE** (Effective EPE) | Non-decreasing EPE (accounts for rollover risk) | Regulatory horizon |
| **EAD** (Exposure at Default) | Regulatory exposure measure | Regulatory formula |

---

## 2. Risk Factor Simulation Models

### 2.1 Interest Rate Models

#### Short-Rate Models

**Vasicek Model:**
```
dr_t = κ(θ - r_t)dt + σdW_t
```
- Mean-reverting process
- Can produce negative rates
- Analytically tractable for bond pricing

**Cox-Ingersoll-Ross (CIR) Model:**
```
dr_t = κ(θ - r_t)dt + σ√r_t dW_t
```
- Non-negative rates (when Feller condition satisfied)
- Mean-reverting
- Popular for CCR simulation under real-world measure

**Hull-White (Extended Vasicek):**
```
dr_t = [θ(t) - κr_t]dt + σdW_t
```
- Time-dependent mean reversion level
- Fits initial term structure exactly
- Widely used for risk-neutral pricing

**CIR++ (Shifted CIR):**
```
r_t = x_t + φ(t)
dx_t = κ(θ - x_t)dt + σ√x_t dW_t
```
- Allows negative rates while maintaining CIR dynamics
- Deterministic shift function φ(t) calibrated to market

#### Multi-Factor Models

**G2++ Model:**
```
r_t = x_t + y_t + φ(t)
dx_t = -a·x_t dt + σ dW_1
dy_t = -b·y_t dt + η dW_2
dW_1·dW_2 = ρ dt
```
- Two correlated factors with different mean reversion speeds
- Better captures term structure dynamics
- Commonly used in XVA calculations

### 2.2 Equity Models

**Geometric Brownian Motion (GBM):**
```
dS_t = μS_t dt + σS_t dW_t
```
- Standard model for equity prices
- Log-normal distribution of prices
- Simple but can produce unrealistic long-horizon values

**Heston Stochastic Volatility:**
```
dS_t = μS_t dt + √V_t S_t dW_S
dV_t = κ(θ - V_t)dt + σ_v√V_t dW_V
dW_S·dW_V = ρ dt
```
- Captures volatility smile/skew
- Mean-reverting variance process
- Correlation between spot and volatility (leverage effect)

### 2.3 FX Models

**Log-normal FX with Stochastic Rates:**
```
dX_t = (r_d - r_f)X_t dt + σ_X X_t dW_X
```
Where domestic and foreign rates follow their own processes.

### 2.4 Hybrid Multi-Factor Models

Modern XVA systems require **hybrid models** that combine multiple asset classes with proper correlation structure:

**General Hybrid Framework:**
```
dX = μ(X,t)dt + Σ(X,t)dW
```
Where:
- X = (r_d, r_f, S, V, λ, ...) is the state vector
- Σ captures correlations via Cholesky decomposition
- Individual components follow specific dynamics

**Correlation Matrix Construction:**

For N risk factors:
```
Σ = C × diag(σ₁, σ₂, ..., σₙ)
```
Where C is the Cholesky decomposition of the correlation matrix.

**Principal Component Analysis (PCA):**

For interest rate curves with many points:
1. Compute covariance matrix of historical changes
2. Extract principal components (typically 3 explain >95% of variance)
3. Simulate 3 drivers instead of full curve
4. Reconstruct full curve from principal components

### 2.5 Credit/Default Models

**Intensity-Based (Reduced Form) Models:**

Default time τ modeled via hazard rate λ_t:
```
P(τ > t) = E[exp(-∫₀ᵗ λ_s ds)]
```

**CIR++ for Default Intensity:**
```
λ_t = y_t + ψ(t)
dy_t = κ(θ - y_t)dt + σ√y_t dW
```
- Calibrated to CDS term structure
- ψ(t) ensures fit to market-implied survival probabilities

**Wrong-Way Risk Modeling:**

Correlation between exposure and default intensity:
```
λ_t = exp(a·V_t + b(t))
```
Where V_t is the exposure driver (e.g., swap value depends on rates).

---

## 3. Counterparty Credit Risk Framework

### 3.1 Credit Exposure Simulation

**Two-Step Procedure:**

**Step 1: Simulate Risk Factors**
- Use physical (real-world) measure for EPE/PFE calculations
- Use risk-neutral measure for CVA pricing
- Generate paths to all simulation dates

**Step 2: Value Instruments**
- At each simulation date and each path:
  - Reconstruct term structures from simulated factors
  - Price all instruments in the portfolio
  - Apply netting and collateral rules
  - Aggregate to counterparty level

### 3.2 Path-Dependent vs. Direct-Jump Simulation

**Path-Dependent Simulation (PDS):**
- Simulate risk factors at all intermediate time steps
- Required for path-dependent instruments
- Ensures marginal matching (correct distribution at each date)
- More computationally intensive

**Direct-Jump to Simulation Date (DJS):**
- Jump directly to each simulation date
- Faster but may introduce bias for some instruments
- Acceptable for vanilla instruments

**Key Result (Kan et al., 2009):**
PDS and DJS can produce different Monte Carlo estimators for EPE. The choice depends on instrument characteristics and accuracy requirements.

### 3.3 Netting and Collateral

**Netting Set Hierarchy:**
```
Counterparty
└── Netting Set 1 (Master Agreement)
    ├── Margin Set A (CSA 1)
    │   └── Trades...
    └── Margin Set B (CSA 2)
        └── Trades...
```

**Net Exposure Calculation:**
```
V_netting_set = max(∑ᵢ Vᵢ, 0)
```

**Collateralized Exposure:**
```
V_collateralized = max(V_net - C, threshold)
```
Where C is posted collateral and threshold is the minimum transfer amount.

**Margin Period of Risk (MPoR):**
- Time between last collateral exchange and potential closeout
- Typically 10-20 business days
- Critical for exposure calculation with margining

### 3.4 Exposure Aggregation

**Expected Exposure Profile:**
```
EE(t) = E[max(V(t), 0)]
     ≈ (1/N) ∑ⁿ max(V(t, ωₙ), 0)
```

**Potential Future Exposure:**
```
PFE(t, α) = Quantile_α[max(V(t), 0)]
```
Where α is typically 97.5% or 99%.

---

## 4. XVA Valuation Adjustments

### 4.1 Credit Valuation Adjustment (CVA)

**Definition:**
CVA is the difference between risk-free portfolio value and true portfolio value accounting for counterparty default:
```
CVA = V_risk_free - V_risky
```

**Calculation Formula:**
```
CVA = (1-R) ∫₀ᵀ EE*(t) × dPD(t)
```
Where:
- R = Recovery rate
- EE*(t) = Discounted expected exposure at time t
- PD(t) = Cumulative probability of default

**Discrete Approximation:**
```
CVA = (1-R) ∑ₖ EE*(tₖ) × [PD(tₖ) - PD(tₖ₋₁)]
```

**Monte Carlo Implementation:**
1. Simulate N risk factor paths to M simulation dates
2. Value portfolio at each (path, date) combination
3. Apply netting and collateral
4. Compute discounted expected exposure at each date
5. Integrate against default probability curve

### 4.2 Debt Valuation Adjustment (DVA)

**Own-Credit Adjustment:**
```
DVA = (1-R_own) ∫₀ᵀ ENE*(t) × dPD_own(t)
```

**Bilateral CVA:**
```
BCVA = CVA - DVA
```

### 4.3 Funding Valuation Adjustment (FVA)

**Funding Costs:**
```
FVA = ∫₀ᵀ E[V(t)⁺] × s_funding(t) dt - ∫₀ᵀ E[V(t)⁻] × s_borrowing(t) dt
```

Often decomposed into:
- **FCA** (Funding Cost Adjustment): Cost of funding positive exposures
- **FBA** (Funding Benefit Adjustment): Benefit from negative exposures

### 4.4 Margin Valuation Adjustment (MVA)

**Initial Margin Funding Cost:**
```
MVA = ∫₀ᵀ E[IM(t)] × s_funding(t) dt
```

Where IM(t) is the initial margin requirement at time t.

**SIMM-Based MVA:**
- Requires simulation of sensitivities (Greeks) along each path
- Apply ISDA SIMM formula to compute IM
- Computationally intensive due to nested calculation

### 4.5 Capital Valuation Adjustment (KVA)

**Regulatory Capital Cost:**
```
KVA = ∫₀ᵀ E[RC(t)] × r_hurdle × D(t) dt
```

Where:
- RC(t) = Regulatory capital requirement at time t
- r_hurdle = Required return on capital

### 4.6 Nested Monte Carlo for XVA

Full XVA calculation requires up to 5-6 layers of Monte Carlo:
1. **Inner Layer:** Mark-to-Market valuation
2. **IM Layer:** Initial margin calculation
3. **CVA/MVA Layer:** Counterparty risk and margin costs
4. **FVA Layer:** Funding costs (requires BSDE iteration)
5. **KVA Layer:** Economic capital computation

**Computational Challenge:**
```
Total simulations ≈ M_outer × M_fva × M_cva × M_im × M_mtm
```

This can easily reach 10⁹-10¹² valuations for a typical portfolio.

---

## 5. American Monte Carlo Methods

### 5.1 The Longstaff-Schwartz Algorithm

The Least-Squares Monte Carlo (LSM) method enables pricing of American/Bermudan options via simulation.

**Algorithm Overview:**

1. **Forward Simulation:** Generate N paths of underlying risk factors
2. **Backward Induction:** At each exercise date (from T back to 0):
   - For in-the-money paths, compute immediate exercise value
   - Regress discounted continuation values against state variables
   - Exercise if immediate value exceeds fitted continuation value
3. **Valuation:** Average discounted payoffs across paths

**Regression Step:**
```
E[V_{t+1}|X_t] ≈ ∑ᵏ βₖ φₖ(X_t)
```
Where φₖ are basis functions (e.g., polynomials, Laguerre functions).

### 5.2 Application to Exposure Calculation

**Key Insight:** LSM produces NPVs at each exercise date along each path—exactly what's needed for exposure profiles.

**Advantages for CVA:**
- Single simulation produces both option value and exposure profile
- Path-consistent exercise decisions
- Captures optionality impact on exposure

**Bermudan Swaption Example:**
```
At each exercise date:
  If exercise_decision(path) = True:
    Exposure(t, path) = 0  (option expired)
  Else:
    Exposure(t, path) = Continuation_value(t, path)
```

### 5.3 Optimized LSM for Credit Exposure

**Challenges:**
- Standard LSM optimized for pricing, not exposure estimation
- Future exposures may be inaccurate due to regression errors
- Early exercise decisions may be suboptimal for non-pricing paths

**OLSM Enhancements (Kan et al.):**
1. **Variance Reduction:** Antithetic variates, control variates
2. **Initial State Dispersion:** Start paths from multiple initial states
3. **Multiple Bucketing:** Piecewise linear regression for different regions

### 5.4 Alternative Regression Methods

**Neural Networks for Continuation Values:**
- Replace polynomial regression with neural network
- Better captures nonlinear relationships
- More robust for high-dimensional state spaces

**Gradient Boosted Trees:**
- Ensemble of decision trees
- Handles discontinuities better than polynomials
- Good for complex payoff structures

---

## 6. Variance Reduction Techniques

### 6.1 Antithetic Variates

**Method:** For each random draw Z, also use -Z.

**Application:**
```
V̂ = (1/2N) ∑ⁿ [f(Z_n) + f(-Z_n)]
```

**Effectiveness:** Works well when f is monotonic in Z.

### 6.2 Control Variates

**Method:** Use correlated variable with known expectation.

**Estimator:**
```
V̂_CV = (1/N) ∑ⁿ [f(X_n) - β(g(X_n) - E[g(X)])]
```

**Optimal β:**
```
β* = Cov(f,g) / Var(g)
```

**Common Controls:**
- Delta-gamma approximation for VaR
- European option price for American option
- Simple swap value for exotic swap

### 6.3 Importance Sampling

**Method:** Sample from alternative distribution that emphasizes important regions.

**Estimator:**
```
V̂_IS = (1/N) ∑ⁿ f(X_n) × [p(X_n) / q(X_n)]
```

Where p is original density and q is importance sampling density.

**Applications:**
- Rare event simulation (large losses, defaults)
- Tail risk estimation (VaR at extreme quantiles)
- CVA for low-default-probability counterparties

**Optimal Importance Sampling for CVA (Glasserman et al.):**
- Shift mean of common factors toward default-inducing region
- Combinatorial optimization to find optimal shifts
- Asymptotically optimal as default probability → 0

### 6.4 Stratified Sampling

**Method:** Divide probability space into strata, sample proportionally from each.

**For EPE:**
```
EPE = ∑ᵢ P(stratum_i) × E[Exposure | stratum_i]
```

### 6.5 Quasi-Monte Carlo (QMC)

**Method:** Replace pseudo-random numbers with low-discrepancy sequences.

**Common Sequences:**
- Sobol sequences
- Halton sequences
- Niederreiter sequences

**Convergence:**
- Standard MC: O(N^(-1/2))
- QMC: O(N^(-1) × (log N)^d) for smooth integrands

**Limitations:**
- Less effective in very high dimensions (d > 50)
- Requires smooth integrands
- Path construction affects performance (Brownian bridge)

---

## 7. High-Performance Computing

### 7.1 GPU Acceleration

**Why GPUs for Monte Carlo:**
- Monte Carlo is "embarrassingly parallel"
- Each path independent of others
- Thousands of GPU cores vs. tens of CPU cores

**Speedup Factors:**
- VaR estimation: 40% faster than CPU-only
- Monte Carlo simulation: Up to 70% reduction in processing time
- Full XVA calculation: 10-100x speedup reported

**CUDA Programming Model:**
```
Grid → Blocks → Threads

Each thread: Process one Monte Carlo path
Block: Group of threads sharing memory
Grid: All blocks for complete simulation
```

**Key Optimizations:**
1. Coalesced memory access
2. Shared memory for frequently used data
3. Efficient random number generation (cuRAND)
4. Minimize host-device data transfer

### 7.2 Parallel Algorithm Design

**Path-Level Parallelism:**
```
for each path p in parallel:
    for each time step t:
        simulate risk factors
        value instruments
        aggregate exposure
```

**Trade-Level Parallelism (within path):**
```
for each time step t:
    for each trade i in parallel:
        value trade given risk factors
    aggregate to netting set level
```

**Nested Monte Carlo Parallelization:**
- Outer paths on different GPU blocks
- Inner simulations within block (shared memory)
- Careful memory management critical

### 7.3 Distributed Computing

**Cluster Architecture:**
```
Master Node
├── Worker Node 1 (GPU 1)
├── Worker Node 2 (GPU 2)
├── ...
└── Worker Node N (GPU N)
```

**Load Balancing:**
- Static: Equal paths per worker
- Dynamic: Work stealing for heterogeneous hardware

### 7.4 Hardware Considerations

| Hardware | Use Case | Typical Speedup |
|----------|----------|-----------------|
| CPU (multi-core) | Small portfolios, development | Baseline |
| GPU (single) | Medium portfolios, production | 10-50x |
| GPU cluster | Large portfolios, full XVA | 100-1000x |
| FPGA | Ultra-low latency, specific algorithms | Variable |

---

## 8. Machine Learning Integration

### 8.1 Neural Networks for CVA/XVA

**Deep BSDE Solver:**
- XVA formulated as system of backward SDEs
- Neural network approximates continuation values
- Recursive application across time steps

**Architecture (Gnoatto et al., 2023):**
```
Input: Risk factor state X_t
Hidden Layers: Dense + ReLU activation
Output: Continuation value / XVA component
```

**Advantages:**
- Scales to high-dimensional problems
- Produces hedge ratios as by-product
- Single training enables multiple scenarios

### 8.2 Exposure Profile Approximation

**Deep Optimal Stopping (DOS):**
1. Train neural network to learn optimal exercise rule
2. Generate cashflow paths using learned strategy
3. Project cashflows onto risk factors via regression
4. Compute EE/PFE from projected values

**Result (Andersson & Oosterlee, 2021):**
- CVA overestimated by up to 25% when ignoring counterparty default in exercise
- Expected Shortfall overestimation >100% in some cases

### 8.3 Regression Enhancement

**Replacing LSM Polynomials:**

| Method | Pros | Cons |
|--------|------|------|
| Polynomial | Simple, fast | Limited flexibility |
| Neural Network | Flexible, nonlinear | Training time, hyperparameters |
| Gradient Boosted Trees | Robust, handles discontinuities | Less smooth |
| Gaussian Process | Uncertainty quantification | Scalability |

### 8.4 Scenario Generation

**Generative Adversarial Networks (GANs):**
- Generate synthetic market scenarios
- Capture complex distributional features
- Stress testing and tail risk analysis

**Variational Autoencoders (VAEs):**
- Learn latent market state representation
- Generate scenarios by sampling latent space
- Regime-aware simulation

---

## 9. Implementation Considerations

### 9.1 Model Calibration

**Interest Rate Models:**
- Calibrate to swaption volatility surface
- Match initial term structure exactly
- Consider real-world vs. risk-neutral parameters

**Credit Models:**
- Bootstrap survival probabilities from CDS spreads
- Calibrate hazard rate model to market
- Account for liquidity in illiquid names

### 9.2 Simulation Design

**Time Grid Selection:**
```
Typical grids:
- Daily for MPoR period (first 2 weeks)
- Weekly for first year
- Monthly for years 1-5
- Quarterly for years 5-10
- Semi-annual beyond
```

**Number of Paths:**
- VaR/PFE: 10,000-100,000 paths
- CVA pricing: 10,000-50,000 paths
- CVA risk (sensitivities): May require 100,000+ paths

### 9.3 Numerical Considerations

**Discretization Schemes:**
- Euler-Maruyama: Simple but may violate positivity
- Milstein: Higher order for multiplicative noise
- QE (Quadratic Exponential): Robust for Heston-type models

**Random Number Generation:**
- Mersenne Twister for CPU
- cuRAND for GPU
- Consider dimensionality reduction (PCA, Brownian bridge)

### 9.4 Validation and Testing

**Model Validation:**
1. Compare to analytical benchmarks where available
2. Convergence testing (increase paths, refine time grid)
3. Martingale tests for risk-neutral simulations
4. Backtesting against historical data

**Exposure Validation:**
- Compare to trade-level analytical approximations
- Stress test extreme scenarios
- Verify netting and collateral logic

---

## 10. Key References

### Foundational Papers

1. **Longstaff, F.A. & Schwartz, E.S. (2001).** "Valuing American Options by Simulation: A Simple Least-Squares Approach." *Review of Financial Studies*, 14(1), 113-147.

2. **Glasserman, P. (2004).** *Monte Carlo Methods in Financial Engineering*. Springer.

3. **Glasserman, P., Heidelberger, P., & Shahabuddin, P. (2000).** "Variance Reduction Techniques for Estimating Value-at-Risk." *Management Science*, 46(10), 1349-1364.

4. **Glasserman, P. & Li, J. (2005).** "Importance Sampling for Portfolio Credit Risk." *Management Science*, 51(11), 1643-1656.

### Counterparty Credit Risk

5. **Gregory, J. (2020).** *The xVA Challenge: Counterparty Credit Risk, Funding, Collateral, Capital and Initial Margin*, 4th ed. Wiley.

6. **Pykhtin, M. & Zhu, S. (2007).** "A Guide to Modeling Counterparty Credit Risk." *GARP Risk Review*, July/August.

7. **Kan, K.H.F., Reesor, R.M., Whitehead, T., & Davison, M. (2009).** "Optimized Least-Squares Monte Carlo for Measuring Counterparty Credit Exposure." *Fields Institute Communications*.

8. **Albanese, C., Caenazzo, S., & Crépey, S. (2017).** "Credit, Funding, Margin, and Capital Valuation Adjustments for Bilateral Portfolios." *Probability, Uncertainty and Quantitative Risk*, 2(7).

### XVA

9. **Green, A. (2016).** *XVA: Credit, Funding and Capital Valuation Adjustments*. Wiley.

10. **Abbas-Turki, L.A., Crépey, S., & Diallo, B. (2018).** "XVA Principles, Nested Monte Carlo Strategies, and GPU Optimizations." *International Journal of Theoretical and Applied Finance*, 21(6).

11. **Burgard, C. & Kjaer, M. (2013).** "Funding Strategies, Funding Costs." *Risk*, December.

### Machine Learning for XVA

12. **Gnoatto, A., Picarelli, A., & Reisinger, C. (2023).** "Deep xVA Solver: A Neural Network-Based Counterparty Credit Risk Management Framework." *SIAM Journal on Financial Mathematics*, 14(1), 314-352.

13. **Andersson, K. & Oosterlee, C.W. (2021).** "Deep Learning for CVA Computations of Large Portfolios of Financial Derivatives." *Applied Mathematics and Computation*, 409.

14. **She, J.-H. & Grecu, D. (2018).** "Neural Network for CVA: Learning Future Values." *arXiv:1811.08726*.

### GPU Computing

15. **Abbas-Turki, L.A. & Lapeyre, B. (2009).** "American Options by GPU-Acceleration of Monte-Carlo Simulations." *Finance and Stochastics*, 13(2).

16. **Bilokon, P., Kucherenko, S., & Williams, C. (2022).** "Quasi-Monte Carlo Methods for Calculating Derivatives Sensitivities on the GPU." *SSRN Working Paper*.

### VaR and Risk Measures

17. **Hong, L.J. & Liu, G. (2014).** "Monte Carlo Methods for Value-at-Risk and Conditional Value-at-Risk: A Review." *ACM Transactions on Modeling and Computer Simulation*, 24(4).

18. **Glasserman, P., Kang, W., & Shahabuddin, P. (2008).** "Fast Simulation of Multifactor Portfolio Credit Risk." *Operations Research*, 56(5), 1200-1217.

### Practitioner Resources

19. **Basel Committee on Banking Supervision (2019).** "Standardised Approach for Counterparty Credit Risk (SA-CCR)."

20. **ISDA (2018).** "SIMM Methodology."

---

## Appendix: Mathematical Notation

| Symbol | Description |
|--------|-------------|
| V(t) | Portfolio value at time t |
| EE(t) | Expected exposure at time t |
| PFE(t,α) | Potential future exposure at quantile α |
| EPE | Expected positive exposure |
| CVA | Credit valuation adjustment |
| DVA | Debt valuation adjustment |
| FVA | Funding valuation adjustment |
| MVA | Margin valuation adjustment |
| KVA | Capital valuation adjustment |
| R | Recovery rate |
| PD(t) | Cumulative probability of default by time t |
| λ(t) | Hazard rate (default intensity) |
| τ | Default time |
| D(t) | Discount factor to time t |
| N | Number of Monte Carlo paths |
| M | Number of simulation dates |

---

*Document prepared: January 2026*
*Based on academic literature and practitioner resources in quantitative finance*
