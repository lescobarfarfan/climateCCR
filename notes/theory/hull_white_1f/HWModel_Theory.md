# Hull-White Model for Interest Rate Simulation
## Theory, Implementation, and Market Risk Applications

## Table of Contents
1. [Theoretical Foundation](#theoretical-foundation)
2. [Advanced Monte Carlo Techniques](#advanced-monte-carlo-techniques)
3. [Market Risk Application: Mexican Market](#market-risk-application-mexican-market)
4. [References](#references)
5. [Code Structure](#code-structure)

---

## Theoretical Foundation

### The Hull-White Model

The Hull-White model (also known as the extended Vasicek model) is a one-factor interest rate model that describes the evolution of the short rate process. It was introduced by John Hull and Alan White in their seminal 1990 paper.

#### Stochastic Differential Equation

The model is defined by the following stochastic differential equation (SDE):

$$dr(t) = [\theta(t) - a \cdot r(t)]dt + \sigma dW(t)$$

where:
- $r(t)$ is the short rate at time $t$
- $a > 0$ is the mean reversion speed
- $\sigma > 0$ is the volatility parameter
- $\theta(t)$ is a time-dependent function chosen to fit the initial term structure
- $dW(t)$ is a Wiener process under the risk-neutral measure

#### Key Properties

1. **Mean Reversion**: The process exhibits mean-reverting behavior around the time-dependent level $\theta(t)/a$

2. **Analytical Tractability**: The model admits closed-form solutions for bond prices and option prices

3. **Distribution**: The short rate is normally distributed with:
   
   **Conditional Mean**:
   $$\mathbb{E}[r(t) | \mathcal{F}_s] = r(s)e^{-a(t-s)} + \int_s^t e^{-a(t-u)}\theta(u)du$$
   
   **Conditional Variance**:
   $$\text{Var}[r(t) | \mathcal{F}_s] = \frac{\sigma^2}{2a}\left(1 - e^{-2a(t-s)}\right)$$

4. **Bond Prices**: The price of a zero-coupon bond maturing at time $T$ is:
   $$P(t,T) = A(t,T)e^{-B(t,T)r(t)}$$
   where:
   $$B(t,T) = \frac{1 - e^{-a(T-t)}}{a}$$
   $$A(t,T) = \frac{P(0,T)}{P(0,t)}\exp\left\{B(t,T)f(0,t) - \frac{\sigma^2}{4a}B(t,T)^2(1 - e^{-2at})\right\}$$

### The $\theta(t)$ Function

The function $\theta(t)$ is crucial for fitting the initial term structure:

$$\theta(t) = \frac{\partial f(0,t)}{\partial T} + a f(0,t) + \frac{\sigma^2}{2a}(1 - e^{-2at})$$

where $f(0,t)$ is the instantaneous forward rate at time $0$ for maturity $t$.

---

## Advanced Monte Carlo Techniques

### 1. Antithetic Variates

**Theory**: Antithetic variates is a variance reduction technique that exploits negative correlation between pairs of paths.

**Mathematical Foundation**:
For an estimator $\hat{\theta} = \frac{1}{2}(\hat{\theta}_1 + \hat{\theta}_2)$ where $\text{Cov}(\hat{\theta}_1, \hat{\theta}_2) < 0$:
$$\text{Var}(\hat{\theta}) = \frac{1}{4}[\text{Var}(\hat{\theta}_1) + \text{Var}(\hat{\theta}_2) + 2\text{Cov}(\hat{\theta}_1, \hat{\theta}_2)]$$

If $\text{Var}(\hat{\theta}_1) = \text{Var}(\hat{\theta}_2) = \sigma^2$ and $\text{Cov}(\hat{\theta}_1, \hat{\theta}_2) = \rho\sigma^2$, then:
$$\text{Var}(\hat{\theta}) = \frac{\sigma^2}{2}(1 + \rho)$$

For perfect negative correlation ($\rho = -1$), variance becomes zero.

**Reference**: Hammersley, J. M., & Morton, K. W. (1956). "A new Monte Carlo technique: antithetic variates". Mathematical Proceedings of the Cambridge Philosophical Society.

### 2. Control Variates

**Theory**: Control variates uses known expectations of related quantities to reduce variance.

**Mathematical Foundation**:
Let $Y$ be our target variable and $X$ a control variate with known mean $\mu_X$. The controlled estimator is:
$$Y_{\text{control}} = Y - \beta(X - \mu_X)$$

The optimal coefficient is:
$$\beta^* = \frac{\text{Cov}(Y,X)}{\text{Var}(X)}$$

The variance reduction factor is:
$$\frac{\text{Var}(Y_{\text{control}})}{\text{Var}(Y)} = 1 - \rho_{YX}^2$$

**Reference**: Lavenberg, S. S., & Welch, P. D. (1981). "A perspective on the use of control variables to increase the efficiency of Monte Carlo simulations". Management Science.

### 3. Importance Sampling

**Theory**: Importance sampling changes the probability measure to focus on important regions of the sample space.

**Mathematical Foundation**:
The expectation under the original measure $\mathbb{P}$ can be written as:
$$\mathbb{E}_{\mathbb{P}}[h(X)] = \mathbb{E}_{\mathbb{Q}}\left[h(X)\frac{d\mathbb{P}}{d\mathbb{Q}}\right]$$

where $\frac{d\mathbb{P}}{d\mathbb{Q}}$ is the Radon-Nikodym derivative. For Girsanov transformation:
$$\frac{d\mathbb{P}}{d\mathbb{Q}} = \exp\left(-\int_0^T \gamma(t)dW(t) - \frac{1}{2}\int_0^T \gamma(t)^2dt\right)$$

**Reference**: Glynn, P. W., & Iglehart, D. L. (1989). "Importance sampling for stochastic simulations". Management Science.

### 4. Moment Matching

**Theory**: Moment matching adjusts simulated paths to exactly match theoretical moments.

**Mathematical Foundation**:
For sample $\{X_i\}_{i=1}^n$ with sample mean $\bar{X}$ and variance $S^2$, the adjusted sample is:
$$X_i^{\text{adj}} = \mu + \frac{\sigma}{S}(X_i - \bar{X})$$

where $\mu$ and $\sigma$ are theoretical moments.

**Reference**: Barraquand, J. (1995). "Numerical valuation of high dimensional multivariate European securities". Management Science.

### 5. Quasi-Monte Carlo

**Theory**: QMC uses low-discrepancy sequences instead of pseudo-random numbers to achieve faster convergence.

**Mathematical Foundation**:
The Koksma-Hlawka inequality bounds the integration error:
$$\left|\frac{1}{N}\sum_{i=1}^N f(x_i) - \int_{[0,1]^d} f(u)du\right| \leq V(f)D_N^*(x_1,\ldots,x_N)$$

where $V(f)$ is the variation of $f$ and $D_N^*$ is the star-discrepancy. QMC achieves $D_N^* = O((\log N)^d/N)$ vs. $O(1/\sqrt{N})$ for MC.

**Reference**: Niederreiter, H. (1992). "Random Number Generation and Quasi-Monte Carlo Methods". SIAM.

### 6. Multilevel Monte Carlo

**Theory**: MLMC combines simulations at different discretization levels to achieve optimal computational complexity.

**Mathematical Foundation**:
The expectation on the finest level $L$ is expressed as a telescoping sum:
$$\mathbb{E}[P_L] = \mathbb{E}[P_0] + \sum_{l=1}^L \mathbb{E}[P_l - P_{l-1}]$$

Total computational cost is minimized by allocating samples inversely proportional to level variance:
$$M_l \propto \sqrt{V_l/C_l}$$

where $V_l = \text{Var}(P_l - P_{l-1})$ and $C_l$ is cost per sample at level $l$.

**Reference**: Giles, M. B. (2008). "Multilevel Monte Carlo path simulation". Operations Research.

---

## Market Risk Application: Mexican Market

### Context for Mexican Fixed Income

The Mexican fixed income market has specific characteristics:

1. **Government Bonds (Bonos M)**: Fixed-rate bonds denominated in MXN
2. **UDIBONOS**: Inflation-linked bonds
3. **Corporate Bonds**: Various tenors and credit qualities
4. **TIIE**: Interbank rate (Mexican equivalent of LIBOR)
5. **Sovereign Curve**: Government yield curve as benchmark

### Stress Testing Framework

#### Step 1: Model Calibration to Mexican Data

```python
def calibrate_to_mexican_data(bonos_curve, historical_rates):
    """
    Calibrate Hull-White model to Mexican market data
    
    Parameters:
    - bonos_curve: Current Bonos M yield curve
    - historical_rates: Historical TIIE or Cetes rates
    """
    # Estimate mean reversion from historical data
    a = estimate_mean_reversion(historical_rates)
    
    # Estimate volatility from historical changes
    sigma = estimate_volatility(historical_rates)
    
    # Calibrate theta to current Bonos curve
    theta_function = calibrate_theta_to_curve(bonos_curve)
    
    return a, sigma, theta_function
```

#### Step 2: Portfolio Construction

```python
class MexicanBondPortfolio:
    def __init__(self):
        self.positions = {
            'bonos_m_10yr': {'notional': 100_000_000, 'coupon': 0.08, 'maturity': 10},
            'bonos_m_5yr': {'notional': 50_000_000, 'coupon': 0.075, 'maturity': 5},
            'cetes_1yr': {'notional': 30_000_000, 'discount': 0.11, 'maturity': 1},
            'corporate_aa': {'notional': 40_000_000, 'coupon': 0.095, 'maturity': 7, 'spread': 0.015},
            'udibonos': {'notional': 25_000_000, 'real_coupon': 0.04, 'maturity': 30}
        }
```

#### Step 3: Stress Scenario Generation

```python
def generate_stress_scenarios(model, base_curve, n_scenarios=10000, horizon_days=10):
    """
    Generate stressed interest rate scenarios for Mexican market
    
    Stress types:
    1. Parallel shift: +200bps (Banxico tightening)
    2. Steepening: Short rates +100bps, long rates +300bps
    3. Flattening: Short rates +300bps, long rates +100bps
    4. Volatility shock: sigma increased by 50%
    5. Mean reversion shock: a decreased by 50%
    """
    
    scenarios = {}
    
    # Base scenario
    scenarios['base'] = simulate_paths(model, horizon_days, n_scenarios)
    
    # Parallel shift scenarios
    scenarios['tightening_200bps'] = simulate_with_shock(model, 'parallel', +0.02)
    scenarios['easing_100bps'] = simulate_with_shock(model, 'parallel', -0.01)
    
    # Curve reshaping scenarios
    scenarios['steepening'] = simulate_with_shock(model, 'steepening', 
                                                  short_shift=0.01, long_shift=0.03)
    scenarios['flattening'] = simulate_with_shock(model, 'flattening',
                                                  short_shift=0.03, long_shift=0.01)
    
    # Volatility stress (market turmoil)
    scenarios['vol_shock'] = simulate_with_parameter_shock(model, 'sigma', multiplier=1.5)
    
    # Mean reversion stress (regime change)
    scenarios['persistence'] = simulate_with_parameter_shock(model, 'a', multiplier=0.5)
    
    return scenarios
```

#### Step 4: Portfolio Valuation Under Stress

```python
def calculate_portfolio_risk(portfolio, scenarios):
    """
    Calculate P&L distribution and risk metrics for Mexican bond portfolio
    """
    
    results = {}
    
    for scenario_name, rates_paths in scenarios.items():
        # Calculate present value for each path
        pv_paths = []
        
        for path in rates_paths:
            # Discount factors from short rates
            discount_factors = calculate_discount_factors(path)
            
            # Value each bond position
            portfolio_pv = 0
            for bond in portfolio.positions:
                bond_pv = value_mexican_bond(bond, discount_factors)
                portfolio_pv += bond_pv
            
            pv_paths.append(portfolio_pv)
        
        # Calculate P&L relative to base
        pnl = np.array(pv_paths) - portfolio.base_value
        
        # Risk metrics
        results[scenario_name] = {
            'var_95': np.percentile(pnl, 5),
            'var_99': np.percentile(pnl, 1),
            'expected_shortfall': np.mean(pnl[pnl <= np.percentile(pnl, 5)]),
            'max_loss': np.min(pnl),
            'mean_pnl': np.mean(pnl),
            'std_pnl': np.std(pnl)
        }
    
    return results
```

#### Step 5: Regulatory Reporting

```python
def generate_regulatory_report(results):
    """
    Generate report in CNBV (Comisión Nacional Bancaria y de Valores) format
    """
    
    report = """
    ================================================
    RIESGO DE MERCADO - CARTERA DE RENTA FIJA
    FECHA: {date}
    INSTITUCIÓN: [NOMBRE DE LA INSTITUCIÓN]
    ================================================
    
    1. COMPOSICIÓN DE LA CARTERA
    ------------------------------------------------
    {portfolio_summary}
    
    2. RESULTADOS DE ESTRÉS
    ------------------------------------------------
    Escenario Base:
        VaR (95%): {base_var_95:,.2f} MXN
        Pérdida Esperada (99%): {base_es_99:,.2f} MXN
    
    Escenario de Tensión - Banxico +200bps:
        Impacto: {stress_impact_200:,.2f} MXN
        Pérdida Máxima: {stress_max_200:,.2f} MXN
    
    Escenario de Volatilidad:
        Impacto: {vol_impact:,.2f} MXN
        VaR Incremental: {incremental_var:,.2f} MXN
    
    3. PRUEBAS DE RESISTENCIA (CNBV Artículo 282)
    ------------------------------------------------
    Prueba 1: Incremento paralelo de 200bps en tasa
    Prueba 2: Incremento no paralelo (empinamiento)
    Prueba 3: Choque de volatilidad +50%
    
    4. RECOMENDACIONES
    ------------------------------------------------
    {recommendations}
    """
    
    return report
```

---

## References

### Original Papers

1. **Hull, J., & White, A. (1990).** "Pricing Interest-Rate-Derivative Securities". *The Review of Financial Studies*, 3(4), 573-592. [Link](https://academic.oup.com/rfs/article-abstract/3/4/573/1601187)

2. **Hull, J., & White, A. (1994).** "Numerical procedures for implementing term structure models I: Single-factor models". *Journal of Derivatives*, 2(1), 7-16.

3. **Hull, J., & White, A. (1996).** "Using Hull-White interest rate trees". *Journal of Derivatives*, 3(3), 26-36.

### Books

4. **Brigo, D., & Mercurio, F. (2006).** "Interest Rate Models: Theory and Practice" (2nd ed.). Springer Finance. ISBN: 978-3540221494.

5. **Glasserman, P. (2004).** "Monte Carlo Methods in Financial Engineering". Springer. ISBN: 978-0387004518.

6. **Andersen, L. B., & Piterbarg, V. V. (2010).** "Interest Rate Modeling". Atlantic Financial Press.

### Advanced Monte Carlo Techniques

7. **Hammersley, J. M., & Morton, K. W. (1956).** "A new Monte Carlo technique: antithetic variates". *Mathematical Proceedings of the Cambridge Philosophical Society*, 52(3), 449-475.

8. **Lavenberg, S. S., & Welch, P. D. (1981).** "A perspective on the use of control variables to increase the efficiency of Monte Carlo simulations". *Management Science*, 27(3), 322-335.

9. **Glynn, P. W., & Iglehart, D. L. (1989).** "Importance sampling for stochastic simulations". *Management Science*, 35(11), 1367-1392.

10. **Niederreiter, H. (1992).** "Random Number Generation and Quasi-Monte Carlo Methods". SIAM. ISBN: 978-0898712957.

11. **Giles, M. B. (2008).** "Multilevel Monte Carlo path simulation". *Operations Research*, 56(3), 607-617.

### Mexican Market Specific

12. **Banco de México.** "Disposiciones de Carácter General Aplicables a las Instituciones de Crédito" (Circular Única de Bancos).

13. **CNBV.** "Disposiciones de Carácter General en Materia de Administración de Riesgos". Comisión Nacional Bancaria y de Valores.

14. **Sidaoui, J., et al. (2010).** "The Mexican fixed income market: Structure and participants". *BIS Papers*, No. 53.

### Risk Management Standards

15. **BCBS (2019).** "Minimum capital requirements for market risk". Basel Committee on Banking Supervision.

16. **Jorion, P. (2006).** "Value at Risk: The New Benchmark for Managing Financial Risk" (3rd ed.). McGraw-Hill.

---

## Code Structure

The complete implementation is organized in the following Python scripts:

### Script 1: `hull_white_base.py`
Basic Hull-White model implementation with Euler-Maruyama simulation.

### Script 2: `hull_white_advanced_mc.py`
Advanced Monte Carlo techniques implementation.

### Script 3: `mexican_market_risk.py`
Mexican market-specific risk analysis application.

### Script 4: `examples.py`
Example usage and demonstration.

Each script is fully documented and includes error handling, type hints, and examples.