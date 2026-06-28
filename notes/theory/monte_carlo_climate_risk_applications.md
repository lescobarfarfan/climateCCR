# Monte Carlo Simulation and Quantitative Finance Methods for Climate Risk Assessment

## Applications of Traditional Risk Management Frameworks to Climate-Related Financial Risks

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Climate Change Valuation Adjustment (CCVA)](#2-climate-change-valuation-adjustment-ccva)
3. [Climate-Adjusted Merton Models](#3-climate-adjusted-merton-models)
4. [Monte Carlo for Climate Value-at-Risk](#4-monte-carlo-for-climate-value-at-risk)
5. [NGFS Scenarios with Monte Carlo Credit Models](#5-ngfs-scenarios-with-monte-carlo-credit-models)
6. [Physical Risk Simulation Frameworks](#6-physical-risk-simulation-frameworks)
7. [Climate-Adjusted CDS and Credit Spreads](#7-climate-adjusted-cds-and-credit-spreads)
8. [Implementation Challenges](#8-implementation-challenges)
9. [Key References](#9-key-references)

---

## 1. Introduction

### 1.1 The Convergence of Climate Risk and Quantitative Finance

The integration of climate risk into traditional quantitative finance frameworks represents one of the most significant methodological developments in risk management. Financial institutions are adapting established Monte Carlo simulation techniques, structural credit models, and counterparty risk frameworks to capture the unique characteristics of climate-related financial risks.

### 1.2 Types of Climate Risk

| Risk Type | Description | Time Horizon | Primary Transmission Channels |
|-----------|-------------|--------------|-------------------------------|
| **Transition Risk** | Financial risks from adjustment to low-carbon economy | Short to medium term | Carbon pricing, policy changes, technology shifts, market sentiment |
| **Physical Risk (Acute)** | Risks from extreme weather events | Immediate to short term | Asset damage, business interruption, supply chain disruption |
| **Physical Risk (Chronic)** | Risks from long-term climate shifts | Medium to long term | Sea level rise, temperature changes, resource scarcity |
| **Liability Risk** | Legal risks from climate-related litigation | Variable | Litigation costs, regulatory penalties |

### 1.3 Framework Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│              CLIMATE-ADJUSTED RISK MANAGEMENT FRAMEWORK                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐   │
│  │  NGFS/IPCC       │ →  │  Macro-Financial │ →  │  Firm-Level      │   │
│  │  Climate         │    │  Transmission    │    │  Impact          │   │
│  │  Scenarios       │    │  Channels        │    │  Assessment      │   │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘   │
│           ↓                       ↓                       ↓              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐   │
│  │  Carbon Price    │    │  GDP, Inflation  │    │  Revenue/Cost    │   │
│  │  Pathways        │    │  Interest Rates  │    │  Shocks          │   │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘   │
│                                    ↓                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    QUANTITATIVE MODELS                             │  │
│  │  • Climate-Adjusted Merton (PD)    • Climate VaR/CVaR             │  │
│  │  • CCVA for Derivatives            • Monte Carlo Credit Simulation │  │
│  │  • Physical Risk Jump Models       • Stochastic Carbon Pricing     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    OUTPUT METRICS                                  │  │
│  │  • Climate-Adjusted PD/LGD         • Portfolio Expected Loss      │  │
│  │  • CCVA/Climate-Adjusted XVA       • Climate Value-at-Risk        │  │
│  │  • Capital Add-ons                 • Stranded Asset Exposure      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Climate Change Valuation Adjustment (CCVA)

### 2.1 Conceptual Framework

Climate Change Valuation Adjustment (CCVA) extends the traditional CVA framework to incorporate the impact of climate-related events on counterparty credit risk over the life of derivative contracts.

**Definition:**
```
CCVA = CVA_climate_adjusted - CVA_baseline
```

Where CVA_climate_adjusted incorporates climate scenario-driven changes in:
- Counterparty default probabilities
- Expected exposures (potentially via climate-affected interest rates, FX, etc.)
- Recovery rates (potentially affected by stranded assets)

### 2.2 Kenyon & Berrahoui Framework (2021)

Kenyon and Berrahoui introduced the first comprehensive framework for pricing climate risk into derivatives via CCVA.

**Key Methodology:**
1. **CDS Curve Extension:** Most CDS trading occurs at 5-10 year tenors. Climate impacts extend beyond this horizon, requiring extrapolation.
2. **Integrated Assessment Models (IAMs):** Used to translate climate scenarios into economic impact scenarios that affect counterparty creditworthiness.
3. **Hazard Rate Adjustment:** Climate scenarios modify the hazard rate (default intensity) beyond the observable CDS curve.

**Extrapolation Approach:**
```
λ(t) = λ_market(t)                     for t ≤ T_market
λ(t) = λ_market(T_market) × f(climate_scenario, t)   for t > T_market
```

Where f(climate_scenario, t) represents the climate-induced adjustment to the baseline hazard rate.

**Key Findings:**
| Scenario | Instrument | CVA Impact |
|----------|------------|------------|
| Climate disruption at 70 years | 20-year IRS | +23% CVA |
| Climate disruption at 20-40 years | Long-dated swaps | Up to +100% CVA |
| Adverse transition scenario | Oil & Gas counterparties | >50% CVA increase |

**Important Insight:** While CVA rises under climate stress, FVA may decrease because higher probability of counterparty default means less time paying funding costs.

### 2.3 Forvis Mazars CCVA Framework (2023)

**Three-Block Approach:**

**Block 1: Climate Scenario Selection**
- Use NGFS scenarios (Orderly, Disorderly, Hot House World)
- Define transition risk pathways (carbon prices, technology shifts)
- Specify physical risk parameters (temperature pathways, extreme events)

**Block 2: Financial Impact Assessment**
- Sector-specific revenue/cost projections under each scenario
- Carbon cost pass-through modeling
- Stranded asset identification

**Block 3: Credit Risk Translation**
- Vasicek single-factor model with climate-adjusted systematic factor
- Probability of default adjustment via "Climate Credit Quality Index"

**Systemic Factor Model:**
```
X_t = ρ × Y_t + √(1-ρ²) × ε_t
```

Where:
- X_t = firm-specific credit driver
- Y_t = systemic factor (calibrated to GDP, now climate-adjusted)
- ρ = correlation to systemic factor
- ε_t = idiosyncratic factor

**Key Results:**
- Oil & Gas sector showed the most significant CCVA impact
- In 8 of 16 Swap × Oil & Gas Counterparty pairs, CVA increased by over 50% under adverse scenarios
- CCVA is highly sensitive to both sector and scenario selection

### 2.4 Implications for XVA Desks

**Practical Considerations:**
1. **Model Integration:** CCVA should be integrated with existing CVA/DVA/FVA frameworks
2. **Hedging:** Climate-adjusted CVA sensitivities create new hedging requirements
3. **Capital:** Potential for climate-specific capital add-ons for long-dated derivatives
4. **Disclosure:** TCFD alignment requires climate scenario analysis for derivative portfolios

---

## 3. Climate-Adjusted Merton Models

### 3.1 Traditional Merton Model Review

The Merton (1974) structural credit model treats equity as a call option on firm assets:

```
E = V × N(d₁) - D × e^(-rT) × N(d₂)

d₁ = [ln(V/D) + (r + σ²_V/2)T] / (σ_V × √T)
d₂ = d₁ - σ_V × √T

PD = N(-d₂)
```

Where:
- E = Equity value
- V = Firm asset value
- D = Debt face value (default point)
- σ_V = Asset volatility
- PD = Probability of default

### 3.2 BIS Climate-Extended Merton Framework

The Bank for International Settlements (BIS Working Paper 1274) proposes extending the Merton model with an additional climate risk factor.

**Two-Factor Model:**
```
dV_t / V_t = μ dt + σ_S dB_t + σ_C dC_t + J_climate dN_t
```

Where:
- B_t = Systematic (market) Brownian motion
- C_t = Climate factor (correlated with physical/transition risks)
- J_climate = Climate jump size
- N_t = Poisson process for acute climate events

**Physical Risk as Jump Process:**
Physical risk is modeled as a binary event with externally defined probability and a jump in market value of assets:

```
V_after_event = V_before_event × (1 - Loss_severity)
```

**Conditional PD with Climate Factor:**
```
PD(climate) = N([-ln(V₀/D) - (μ - σ²/2)T + β_climate × Climate_shock] / (σ × √T))
```

### 3.3 Bell and Vuuren (2022) Implementation

**Key Approach:**
- Physical risk leads to an increase in the volatility of the firm's asset value
- Transition risk is assumed to be already anticipated and priced into stock values
- Uses stochastic simulation to generate climate risk-adjusted future value of company assets

**Integration with Moody's CEDF Model:**
Climate-adjusted asset values and volatilities are fed as inputs to calculate climate risk-adjusted default rates over horizons ranging from 1 to 30 years.

### 3.4 Carbon Tax Stress Testing via Merton Model

**Reinders et al. Methodology:**

**Step 1:** Calculate scenario-based NPV of carbon tax payments
```
NPV_carbon = Σ_t [Emissions_t × Carbon_Price_t × (1-Pass_through_t)] / (1+r)^t
```

**Step 2:** Compute asset devaluation shock
```
ΔV = -NPV_carbon / V₀
```

**Step 3:** Derive climate-adjusted PD using Merton model
```
PD_climate = N([-ln((V₀ + ΔV)/D) - (μ - σ²/2)T] / (σ × √T))
```

**Empirical Results (STOXX Europe 600):**

| Carbon Tax Scenario | Asset Devaluation >30% | PD Below Investment Grade |
|---------------------|------------------------|---------------------------|
| €50/tCO₂ | ~5% of firms | ~10% of firms |
| €100/tCO₂ | ~8% of firms | ~16% of firms |

**Most Affected Sectors:**
- Asset devaluation shocks of 15-36%
- New PDs of 5-34%
- Capital ratio decrease of 1.2-1.6 percentage points

### 3.5 Ge, Liu & Wei (2024) - Chinese Banking Application

**Framework:**
- Applied Merton model to assess climate transition risk exposure of Chinese banks
- Used three NGFS scenarios over 30-year horizon
- Focused on carbon price impacts on corporate costs and operating profits

**Key Findings:**
- Rise in carbon prices increases corporate costs and reduces operating profits
- This increases probability of corporate default
- Ultimately raises the overall level of banks' credit risk exposure
- Utilities and energy sectors most affected
- Large state-owned banks have higher exposure due to loans in carbon-intensive sectors

---

## 4. Monte Carlo for Climate Value-at-Risk

### 4.1 Climate VaR Conceptual Framework

Climate Value-at-Risk extends traditional VaR to incorporate climate-specific risk factors:

```
Climate_VaR_α = -inf{x : P(ΔPortfolio_climate ≤ x) ≥ α}
```

Where ΔPortfolio_climate reflects losses under climate-stressed scenarios.

### 4.2 Desnos, Le Guenedal, Morais & Roncalli (2023)

**"From Climate Stress Testing to Climate Value-at-Risk: A Stochastic Approach"**

**Key Innovation:** Rather than using a single or limited set of scenarios, this framework uses a probabilistic approach to generate thousands of simulated pathways via Monte Carlo simulation.

**Methodology Components:**

**1. Stochastic Carbon Tax Model:**
```
τ_t = τ₀ × exp(μ_τ × t + σ_τ × W_t)
```

Where τ_t is the carbon price at time t, with drift and volatility calibrated to scenario ranges.

**2. Input-Output Analysis for Indirect Emissions:**
Uses the Leontief input-output model to capture supply chain emissions:
```
x = (I - A)^(-1) × y
```

Where A is the technical coefficients matrix capturing inter-industry linkages.

**3. Pass-Through Mechanism:**
Models how carbon costs are passed through to consumers vs. absorbed by firms:
```
Cost_absorbed = (1 - pass_through_rate) × Carbon_cost
Margin_impact = Cost_absorbed / Revenue
```

**4. Monte Carlo Simulation:**
- Generate N paths of carbon prices, GDP growth, inflation
- For each path, calculate firm-level financial impacts
- Aggregate to portfolio level
- Compute empirical distribution of portfolio value changes
- Extract Climate VaR at desired confidence level

**Key Applications:**
- Inflation risk at sector and country level
- Growth risks by industry
- Earnings risks for specific firms
- Portfolio-level climate VaR and CVaR

### 4.3 Physical Climate Risk VaR (arXiv 2024)

**Extended Vasicek Model with Climate Jumps:**

**Firm Value Process:**
```
dV_t / V_t = μ dt + σ dW_t + J dN_t
```

Where:
- J = Jump size (negative, representing acute physical risk events)
- N_t = Compound Poisson process with intensity λ_climate

**Calibration:**
- Regional vulnerability clusters based on geographic exposure
- Asset intensity clusters based on sector characteristics
- Jump intensity calibrated to historical extreme weather frequency
- Jump size calibrated to observed damage functions

**VaR Add-on Calculation:**
```
VaR_add_on = VaR_climate_stressed - VaR_baseline
```

**Results for MSCI Indexes:**

| Time Horizon | VaR 95% Add-on | VaR 99% Add-on |
|--------------|----------------|----------------|
| 1 year | Small but positive | Small but positive |
| 5 years | Significant | More significant |
| 10 years | Material | Highly material |
| 20 years | Very material | Very material |

**Key Finding:** Investing in ESG-aligned assets (MSCI World ESG Leaders, MSCI Climate Paris Aligned) does not necessarily offer protection against the financial impacts of physical climate risk, as these indexes exhibit similar asset intensity and regional vulnerability profiles.

### 4.4 Battiston et al. (Nature Communications, 2024)

**Asset-Level Physical Risk Methodology:**

**Step 1:** Geolocalize productive assets (plants, facilities)

**Step 2:** Assess exposure to chronic and acute impacts across IPCC scenarios

**Step 3:** Translate asset-level shocks into economic and financial losses

**Key Findings:**
- Investor losses underestimated by up to 70% when neglecting asset-level information
- Investor losses underestimated by up to 82% when neglecting tail acute risks
- Application to Mexico showed significant physical risk exposures for major firms

---

## 5. NGFS Scenarios with Monte Carlo Credit Models

### 5.1 NGFS Scenario Framework

The Network for Greening the Financial System (NGFS) provides standardized climate scenarios:

| Scenario Category | Key Characteristics | Physical Risk | Transition Risk |
|-------------------|---------------------|---------------|-----------------|
| **Orderly** (Net Zero 2050) | Early, gradual policy action | Low | Low-Medium |
| **Disorderly** (Delayed Transition) | Late, abrupt policy action | Medium | High |
| **Hot House World** (Current Policies) | Limited policy action | High | Low |
| **Too Little, Too Late** | Fragmented response | High | Medium |

### 5.2 Z-Risk Engine Monte Carlo Framework

**Forest & Aguais (2023) - Frontiers in Climate**

**Industry Region Monte Carlo (IRMC) Model:**

**Step 1:** Monte Carlo simulation of industry and region systematic factor Zs
```
Z_industry,region ~ N(μ_climate_adjusted, Σ)
```

**Step 2:** Transform systematic factors to credit indicators

**Step 3:** Apply multi-factor credit model to benchmark portfolio

**Step 4:** Generate portfolio credit-loss distribution

**Key Insight:**
> "Higher credit risks generally arise from unexpected economic shocks to cashflows and asset values. Systematic shocks that impact many firms like those observed during the last three economic recessions clearly produce higher volatility and systematic deviations from average economic trends."

**Comparison with NGFS Approach:**
- NGFS focuses on changes to long-run economic growth trends
- Z-Risk Engine emphasizes the role of volatility and unexpected shocks
- Monte Carlo approach captures the full distribution of outcomes, not just point estimates

### 5.3 Climate Beta and CRISK (NY Fed)

**Acharya, Berner, Engle - Climate Stress Testing**

**Climate Beta Estimation:**
```
R_bank,t = α + β_market × R_market,t + β_climate × R_stranded,t + ε_t
```

Where R_stranded,t = return on stranded asset portfolio (fossil fuel stocks)

**Dynamic Conditional Beta (DCB) Model:**
- Incorporates time-varying volatility
- Captures regime changes in climate risk exposure
- Estimates done using DCC-GARCH framework

**Climate-Adjusted SRISK (CRISK):**
```
CRISK_it = k × DEBT_it - (1-k) × EQUITY_it × (1 - LRMES_climate,it)
```

Where LRMES_climate = Long-Run Marginal Expected Shortfall including climate factor

**Key Findings:**
- Climate beta varies significantly over time
- Substantial rise in climate betas and CRISKs during 2020 oil price collapse
- Banks with higher exposure to fossil fuel industry have higher climate betas
- U.S., U.K., Canada, Japan, and France banks all show material climate exposures

---

## 6. Physical Risk Simulation Frameworks

### 6.1 Acute Physical Risk as Jump Process

**Model Specification:**
```
dV_t = μV_t dt + σV_t dW_t - L × V_t × dN_t
```

Where:
- L = Loss given event (damage severity)
- N_t = Poisson process with climate-scenario-dependent intensity

**Intensity Calibration:**
- Historical extreme weather frequency by region
- Climate model projections for future frequency under RCP scenarios
- Asset-level vulnerability assessments

### 6.2 Chronic Physical Risk Integration

**Productivity Impact Model:**
```
Productivity_t = Productivity_0 × (1 - f(ΔTemperature_t))
```

Where f() is a damage function (often quadratic in temperature deviation)

**Revenue Adjustment:**
```
Revenue_climate = Revenue_baseline × Productivity_t × (1 + Price_elasticity × ΔPrice)
```

### 6.3 Insurance-Linked Integration

**Expected Annual Damage:**
```
EAD = Σ_hazards Σ_assets [Exposure × Vulnerability × Probability]
```

Where:
- Exposure = Asset value at risk
- Vulnerability = Damage function (% loss given event)
- Probability = Annual exceedance probability

---

## 7. Climate-Adjusted CDS and Credit Spreads

### 7.1 Climate Transition Risk Factor

**Ugolini, Reboredo & Ojea Ferreiro (2023) - Bank of Canada**

**Climate Transition Risk (CTR) Factor Construction:**
- Based on vulnerability of firm's value to transition to low-carbon economy
- Incorporates carbon intensity, sector exposure, technology position

**CDS Spread Model:**
```
CDS_spread_it = α + β_1 × Traditional_factors_it + β_2 × CTR_factor_t × Vulnerability_i + ε_it
```

**Key Findings:**
- CTR factor shifts the term structure of CDS spreads of more vulnerable firms
- Less vulnerable firms show no significant response to CTR factor
- Different climate transition policies have asymmetric economic impacts on credit risk
- More vulnerable firms show significant repricing; less vulnerable firms show negligible effects

### 7.2 Distance-to-Default and Carbon Emissions

**Gianfrate & Peri (2019) - Journal of Cleaner Production**

**Hypothesis:** Companies with high carbon footprint are perceived by the market as more likely to default.

**Model:**
```
DD_it = α + β_1 × ln(Emissions_it) + β_2 × Carbon_intensity_it + Controls + ε_it
```

Where DD = Distance-to-Default (Merton-based measure)

**Key Findings:**
- Significant and negative relation between distance-to-default and CO2 emissions
- Significant and negative relation between distance-to-default and carbon intensity
- After Paris Agreement, high emitting companies significantly shortened their distance to default compared to low emitters
- Supports view that financial markets are increasingly pricing climate change exposure

### 7.3 Carbon Default Swap Concept

**Blasberg, Kiesel & Taschini (2023)**

Proposed a "Carbon Default Swap" instrument to disentangle exposure to carbon risk through CDS-like contracts, allowing for:
- Direct hedging of carbon transition risk
- Market-based pricing of climate credit risk
- Separation of carbon risk from other credit factors

---

## 8. Implementation Challenges

### 8.1 Data Challenges

| Challenge | Description | Potential Solutions |
|-----------|-------------|---------------------|
| **Emissions Data** | Scope 3 emissions often estimated, not measured | Third-party data providers, estimation models |
| **Asset-Level Geolocation** | Physical assets not always geolocated | Satellite data, corporate disclosure requirements |
| **Long Time Horizons** | Climate impacts extend beyond typical risk horizons | Scenario analysis, long-dated extrapolation |
| **Historical Data Scarcity** | Climate events are relatively rare in financial data | Physical climate models, synthetic data generation |

### 8.2 Model Uncertainty

**Sources of Uncertainty:**
1. **Climate Model Uncertainty:** Different climate models produce different projections
2. **Economic Model Uncertainty:** Transmission from climate to economic variables is complex
3. **Financial Model Uncertainty:** Mapping economic impacts to credit risk involves assumptions
4. **Parameter Uncertainty:** Calibration data is limited for climate-specific parameters

**Mitigation Approaches:**
- Multi-model ensembles
- Sensitivity analysis across scenarios
- Conservative parameter choices for risk management
- Regular model validation and backtesting where possible

### 8.3 Computational Considerations

**Nested Simulation Challenge:**
- Climate scenarios × Time steps × Monte Carlo paths × Counterparties × Instruments
- Can easily reach billions of calculations

**Solutions:**
- GPU acceleration
- Regression-based exposure approximation
- Scenario reduction techniques
- American Monte Carlo for early exercise features

### 8.4 Regulatory Landscape

**Current Requirements:**
- ECB/SSM climate stress testing exercises
- Bank of England climate scenario analysis
- TCFD disclosure recommendations
- Basel Committee guidance on climate-related financial risks

**Emerging Trends:**
- Integration of climate risk into Pillar 1 capital requirements
- Standardization of climate scenario methodologies
- Enhanced disclosure requirements for climate-related credit risk

---

## 9. Key References

### Climate-Adjusted CVA/XVA

1. **Kenyon, C. & Berrahoui, M. (2021).** "Climate Change Valuation Adjustment (CCVA)." *Risk.net*. [Link](https://www.risk.net/our-take/7861531/derivatives-pricing-starts-feeling-the-heat-of-climate-change)

2. **Forvis Mazars (2023).** "Climate Change Valuation Adjustment: Introducing a Climate Change Scenario Extrapolation to Long-dated CDS Curve." *Technical Paper*. [Link](https://financialservices.forvismazars.com/wp-content/uploads/2023/02/Climate-change-valuation-adjustment-introducing-a-climate-change-scenario-extrapolation-to-long-dated-CDS-curve.pdf)

### Climate-Adjusted Merton Models

3. **Bank for International Settlements (2024).** "Climate Risks in Banks' Credit Risk Models." *BIS Working Paper No. 1274*. [Link](https://www.bis.org/publ/work1274.pdf)

4. **Bell, A. & van Vuuren, D. (2022).** "Climate Risk in a Merton Framework." *Working Paper*.

5. **Ge, Z., Liu, Q. & Wei, Z. (2024).** "Assessment of Bank Risk Exposure Considering Climate Transition Risks." *Finance Research Letters*. [Link](https://www.sciencedirect.com/science/article/abs/pii/S1544612324009334)

6. **Reinders, H.J., et al. (2020).** "A Finance Approach to Climate Stress Testing." *DNB Working Paper*.

7. **Dunz, N., et al. (2023).** "The Impact of Transitory Climate Risk on Firm Valuation and Financial Institutions: A Stress Test Approach." *Schmalenbach Journal of Business Research*. [Link](https://link.springer.com/article/10.1007/s41471-023-00166-y)

### Monte Carlo Climate VaR

8. **Desnos, B., Le Guenedal, T., Morais, P. & Roncalli, T. (2023).** "From Climate Stress Testing to Climate Value-at-Risk: A Stochastic Approach." *SSRN Working Paper*. [Link](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4497124)

9. **Bressan, G., et al. (2024).** "Climate Physical Risk Assessment in Asset Management." *arXiv:2504.19307*. [Link](https://arxiv.org/abs/2504.19307)

10. **Battiston, S., et al. (2024).** "Asset-Level Assessment of Climate Physical Risk Matters for Adaptation Finance." *Nature Communications*. [Link](https://www.nature.com/articles/s41467-024-48820-1)

### NGFS Scenarios and Credit Models

11. **Forest, L.R. & Aguais, S. (2023).** "Climate-Change Scenarios Require Volatility Effects to Imply Substantial Credit Losses." *Frontiers in Climate*. [Link](https://www.frontiersin.org/journals/climate/articles/10.3389/fclim.2023.1127479/full)

12. **Acharya, V., Berner, R. & Engle, R. (2023).** "Climate Stress Testing." *NY Fed Staff Report No. 1059*. [Link](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr1059.pdf)

13. **NGFS (2024).** "Guide to Climate Scenario Analysis for Central Banks and Supervisors." *NGFS Technical Document*. [Link](https://www.ngfs.net/system/files/2025-11/Guide%20to%20climate%20scenario%20analysis%20for%20central%20banks%20and%20supervisors%20–%20Update_0.pdf)

14. **Jung, H., Engle, R. & Berner, R. (2021).** "Climate Stress Testing." *OFR Working Paper*. [Link](https://www.financialresearch.gov/conferences/files/2022-09-09-climate-stress-testing.pdf)

### Climate-Adjusted Credit Spreads

15. **Ugolini, A., Reboredo, J.C. & Ojea Ferreiro, J. (2023).** "Is Climate Transition Risk Priced into Corporate Credit Risk? Evidence from Credit Default Swaps." *Bank of Canada Staff Working Paper 23-38*. [Link](https://ideas.repec.org/p/bca/bocawp/23-38.html)

16. **Gianfrate, G. & Peri, M. (2019).** "The Green Advantage: Exploring the Convenience of Issuing Green Bonds." *Journal of Cleaner Production*, 219, 127-135. [Link](https://www.sciencedirect.com/science/article/abs/pii/S0959652620316814)

17. **Blasberg, A., Kiesel, R. & Taschini, L. (2023).** "Carbon Default Swap – Disentangling the Exposure to Carbon Risk Through CDS." *LSE Research Online*.

### Regulatory and Framework Documents

18. **Basel Committee on Banking Supervision (2022).** "Climate-Related Financial Risks: Measurement Methodologies." *BCBS Publication d518*. [Link](https://www.bis.org/bcbs/publ/d518.pdf)

19. **European Central Bank (2022).** "Climate Risk Stress Test." *ECB Report*.

20. **Task Force on Climate-Related Financial Disclosures (2017).** "Recommendations of the Task Force on Climate-Related Financial Disclosures." *TCFD Report*.

### General Climate Finance

21. **Bolton, P. & Kacperczyk, M. (2021).** "Do Investors Care About Carbon Risk?" *Journal of Financial Economics*, 142(2), 517-549.

22. **Battiston, S., et al. (2017).** "A Climate Stress-Test of the Financial System." *Nature Climate Change*, 7, 283-288.

23. **Dietz, S., et al. (2016).** "'Climate Value at Risk' of Global Financial Assets." *Nature Climate Change*, 6, 676-679.

24. **Carney, M. (2015).** "Breaking the Tragedy of the Horizon – Climate Change and Financial Stability." *Speech at Lloyd's of London*.

### Monte Carlo Methods (Foundational)

25. **Glasserman, P. (2004).** *Monte Carlo Methods in Financial Engineering*. Springer.

26. **Longstaff, F.A. & Schwartz, E.S. (2001).** "Valuing American Options by Simulation: A Simple Least-Squares Approach." *Review of Financial Studies*, 14(1), 113-147.

27. **Gregory, J. (2020).** *The xVA Challenge: Counterparty Credit Risk, Funding, Collateral, Capital and Initial Margin*, 4th ed. Wiley.

---

## Appendix: Summary Table of Methods

| Method | Climate Risk Type | Key Innovation | Primary Application |
|--------|-------------------|----------------|---------------------|
| CCVA | Transition | CDS curve extrapolation with IAMs | Derivatives pricing |
| Climate-Adjusted Merton | Transition + Physical | Two-factor model with climate jump | Corporate PD estimation |
| Climate VaR | Transition + Physical | Monte Carlo with stochastic carbon price | Portfolio risk measurement |
| CRISK | Transition | Dynamic climate beta estimation | Bank systemic risk |
| Physical Risk Jump Model | Physical (Acute) | Poisson jumps for extreme events | Asset-level risk assessment |
| Climate CDS Factor | Transition | CTR factor in credit spreads | Market risk pricing |

---

*Document prepared: January 2026*
*Based on academic literature, central bank publications, and practitioner research*
