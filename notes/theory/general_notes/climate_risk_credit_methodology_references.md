# Climate Risk Integration into Credit Risk Assessment: Methodologies and References

## A Comprehensive Guide for Bond Market Research

---

## Table of Contents

1. [Bottom-Up Approaches: Firm-Level Cash Flow Analysis](#1-bottom-up-approaches-firm-level-cash-flow-analysis)
2. [Structural Credit Risk Models (Merton-Based)](#2-structural-credit-risk-models-merton-based)
3. [Market-Based Approaches](#3-market-based-approaches)
4. [Complete Reference List](#4-complete-reference-list)

---

## 1. Bottom-Up Approaches: Firm-Level Cash Flow Analysis

### 1.1 Overview

Bottom-up approaches start at the individual firm level, projecting how climate scenarios affect a company's financial statements and ultimately its creditworthiness. Unlike top-down approaches that apply sector-wide adjustments, bottom-up methods capture firm-specific vulnerabilities, competitive positioning, and adaptive capacity.

### 1.2 The General Methodology Framework

The bottom-up approach typically follows a five-step process:

**Step 1: Estimate Firm-Level Carbon Footprint and Exposure**

- Collect Scope 1, 2, and (where available) Scope 3 emissions data
- Estimate carbon intensity (emissions per unit revenue or per unit output)
- Map physical asset locations for physical risk exposure
- Identify supply chain vulnerabilities

**Step 2: Define Climate Scenario Parameters**

- Select transition pathways (e.g., NGFS scenarios: Net Zero 2050, Delayed Transition, Current Policies)
- Specify carbon price trajectories (e.g., €50, €100, €200, €800 per tCO₂)
- Define physical hazard scenarios (flood depth, drought severity, temperature increases)
- Set time horizons (short-term: 1-5 years; medium-term: 5-15 years; long-term: 15-30 years)

**Step 3: Estimate Energy Demand Response**

The approach requires estimating how firms respond to carbon pricing:

- **Energy demand elasticity**: Sector-specific price elasticities determine how firms adjust energy consumption in response to cost increases
- **Energy mix**: Different fuels have different carbon intensities; firms may substitute between fuels
- **Pass-through rates**: The ability to pass increased costs to customers varies by market structure

**Step 4: Calculate Financial Impact**

The financial impact can be computed through several channels:

**Revenue Impact:**
```
ΔRevenue = f(demand elasticity, price increase, competitive position)
```

**Cost Impact:**
```
ΔCosts = (Carbon Price × Emissions) + Adaptation Costs - Energy Efficiency Savings
```

**EBITDA Impact:**
```
Stressed EBITDA = Base EBITDA - Carbon Costs - Revenue Loss + Cost Savings
```

This can be integrated into:
- **NPV Cash Flow Models**: Discount future stressed cash flows to assess asset devaluation
- **P&L Impact**: Direct cost or write-offs for stranded assets
- **Balance Sheet Effects**: Collateral devaluation, working capital changes

**Step 5: Translate to Credit Risk Parameters**

The financial impacts are then converted to standard credit risk metrics:

**Probability of Default (PD):**
- Use stressed financial ratios in credit scoring models
- Apply Merton distance-to-default methodology (detailed in Section 2)
- Migrate credit ratings based on financial deterioration

**Loss Given Default (LGD):**
- Adjust for collateral devaluation (particularly for stranded assets)
- Consider sector-specific recovery rates under climate stress

**Exposure at Default (EAD):**
- Project credit line utilization under stress
- Consider covenant breaches and acceleration clauses

### 1.3 The Italian Carbon Tax Counterfactual Example

One of the most detailed implementations is the Bank of Italy's microsimulation approach (Aiello & Angelico, 2023):

**Methodology:**
1. Estimate energy demand elasticity by firm group using administrative data
2. Compute price variations for each energy service (electricity, heating, transport) under alternative carbon taxes (€50, €100, €200, €800/tCO₂)
3. Translate price shocks to sectoral impacts based on energy mix and sensitivity
4. Simulate new EBITDA accounting for changed energy expenditure
5. Use microsimulation to identify "financially vulnerable" firms
6. Predict sectoral default rates using models trained on historical data

**Key Finding:** Even with a carbon tax of €800/tCO₂, default rates remain below historical averages, though effects are heterogeneous across sectors.

### 1.4 The Reinders et al. (2020) NPV Approach

This methodology, applied to Dutch financial institutions, uses:

1. **Scenario-based NPV of carbon tax payments**: Calculate present value of future carbon costs under each scenario
2. **Asset devaluation shock**: Deduct NPV from current asset value
3. **Merton model integration**: Feed asset devaluation into structural model to compute new PDs

**Mathematical Framework:**
```
Asset Devaluation = NPV(Carbon Costs) / Current Asset Value

New PD = Merton_PD(Asset Value - Devaluation, Asset Volatility, Liabilities)
```

### 1.5 Key Data Requirements

| Data Type | Sources | Challenges |
|-----------|---------|------------|
| Scope 1-3 Emissions | CDP, Trucost, Bloomberg, company reports | Scope 3 availability; estimation proxies needed |
| Energy Consumption | Company disclosures, sector averages | Granularity varies by firm size |
| Financial Statements | Orbis, Bloomberg, Eikon, iBACH | Timeliness; private company coverage |
| Asset Locations | Company filings, geospatial databases | Supply chain mapping incomplete |
| Carbon Prices | NGFS scenarios, market prices | Scenario uncertainty |

### 1.6 Advantages and Limitations

**Advantages:**
- Captures firm-specific heterogeneity within sectors
- Identifies winners and losers from transition
- Enables granular portfolio analysis
- Can incorporate firm-level adaptation strategies

**Limitations:**
- Data intensive (especially for private companies)
- Requires assumptions about firm behavior and competitive dynamics
- Expert judgment needed for many parameters
- Computationally demanding for large portfolios

---

## 2. Structural Credit Risk Models (Merton-Based)

### 2.1 The Classical Merton Framework

The Merton (1974) model treats a firm's equity as a call option on its assets, with the face value of debt as the strike price.

**Core Assumptions:**
- Firm assets follow geometric Brownian motion
- Single zero-coupon debt obligation with maturity T
- Default occurs when asset value falls below liabilities at maturity
- Frictionless markets; no dividends before maturity

**Asset Value Dynamics:**
```
dVt = μVt dt + σVt dWt

Where:
Vt = Asset value at time t
μ = Expected asset return (drift)
σ = Asset volatility
Wt = Standard Brownian motion
```

**Probability of Default:**
```
PD = Φ(-DD)

Where DD (Distance to Default) = [ln(V/L) + (μ - σ²/2)T] / (σ√T)

And:
V = Current asset value
L = Default threshold (typically between short-term and total liabilities)
Φ = Standard normal CDF
```

**Equity as Call Option:**
```
E = V·N(d₁) - L·e^(-rT)·N(d₂)

Where:
d₁ = [ln(V/L) + (r + σ²/2)T] / (σ√T)
d₂ = d₁ - σ√T
```

### 2.2 Climate-Adjusted Extensions

#### 2.2.1 Asset Value Channel

Climate risk can affect the drift (μ) and level of asset value:

**Transition Risk Adjustment:**
```
V_stressed = V - NPV(Carbon Costs)

Where NPV(Carbon Costs) = Σ [Carbon Price_t × Emissions_t × (1-Abatement_t)] / (1+r)^t
```

**Physical Risk Adjustment:**
```
V_stressed = V × (1 - Damage Factor)

Where Damage Factor = f(Hazard Intensity, Exposure, Vulnerability)
```

#### 2.2.2 Asset Volatility Channel

Climate policy uncertainty increases asset volatility:

**Empirical Evidence (Seltzer, Starks & Zhu, 2024):**
- Following the Paris Agreement, high-carbon firms experienced significant increases in asset volatility
- Counterfactual analysis showed volatility increases contributed more to PD changes than asset value declines
- The volatility effect remained persistent, unlike the transitory asset value effect

**Volatility Adjustment:**
```
σ_stressed = σ_base × (1 + Climate Uncertainty Premium)
```

#### 2.2.3 The BIS/Vasicek Extension for Climate Risk

BIS Working Paper 1274 (2025) proposes extending the Basel IRB framework to incorporate physical climate risk:

**Standard Vasicek Model:**
```
CV(Q) = Φ[(Φ⁻¹(PD) + √ρ·Φ⁻¹(Q)) / √(1-ρ)]

Where:
CV(Q) = Conditional default probability at quantile Q
ρ = Asset correlation
```

**Climate-Adjusted Extension:**

Introduce climate risk as an additional systematic factor:
```
Asset Return = α + β·Economic_Factor + γ·Climate_Factor + ε
```

The climate factor can manifest as:
1. **Sudden jump in asset value** (physical event)
2. **Increased systematic volatility** (climate uncertainty)
3. **Correlation with economic downturns** (compound risk)

### 2.3 The KMV/Moody's EDF Implementation

The KMV model (now Moody's Expected Default Frequency) is the most widely used commercial implementation:

**Key Modifications from Base Merton:**
- Uses market equity value and volatility (observable) to infer asset value and volatility (unobservable)
- Default threshold set between short-term liabilities and total liabilities
- Empirical mapping from distance-to-default to EDF using historical default rates

**Climate-Adjusted EDF (CAEDF) Model:**
- Moody's CAEDF calculates PD over horizons from 1-30 years
- Incorporates both physical and transition risks
- Uses NGFS scenarios and proprietary physical risk scores
- Aggregates firm-specific location data with climate hazard projections

### 2.4 Empirical Implementation Steps

**Step 1: Calibrate Base Merton Model**
```python
# Solve for asset value (V) and volatility (σ_A) from:
# 1) E = V·N(d₁) - L·e^(-rT)·N(d₂)  [Equity pricing equation]
# 2) σ_E·E = N(d₁)·σ_A·V           [Volatility relationship]
```

**Step 2: Calculate Climate-Stressed Asset Value**
- Estimate NPV of future carbon costs under scenario
- Apply physical damage factors based on asset locations
- Subtract from current asset value

**Step 3: Adjust Asset Volatility**
- Increase volatility to reflect climate policy uncertainty
- Consider regime-dependent volatility (pre/post policy announcements)

**Step 4: Compute Stressed PD**
```
DD_stressed = [ln(V_stressed/L) + (μ - σ_stressed²/2)T] / (σ_stressed√T)
PD_stressed = Φ(-DD_stressed)
```

**Step 5: Price the Bond**
```
Credit Spread ≈ -ln(1 - PD·LGD) / T

Or using risk-neutral valuation:
Risky Bond Value = Risk-Free Bond Value × (1 - PD×LGD)
```

### 2.5 Distance-to-Default and Carbon Emissions: Empirical Evidence

Multiple studies document the relationship between carbon footprint and credit risk:

**Capasso, Gianfrate & Spinelli (2020):**
- Sample: 458 global investment-grade firms (2004-2018)
- Finding: Significant negative relationship between CO₂ emissions and distance-to-default
- Implication: Higher emitters face higher default probability

**Nguyen et al. (2022):**
- Sample: 2,785 firms from 42 economies (2004-2018)
- Finding: Emissions have significant negative causal impact on distance-to-default
- Channels: ROA deterioration and cash flow volatility
- Moderators: Environmental commitments mitigate the effect; controversies exacerbate it

### 2.6 Practical Considerations

**Challenges:**
- Merton assumes lognormal asset returns; climate events may cause jumps
- Single default threshold may not capture restructuring scenarios
- Asset correlations may increase during climate stress (systemic risk)
- Long time horizons exceed typical model calibration periods

**Extensions to Address Challenges:**
- **Jump-diffusion models**: Incorporate sudden asset value changes from physical events
- **Regime-switching models**: Allow parameters to vary with climate policy state
- **Multi-factor models**: Separate economic and climate systematic risks
- **Dynamic models**: Allow balance sheet evolution over scenario horizon

---

## 3. Market-Based Approaches

### 3.1 Overview

Market-based approaches use observed market prices to infer climate risk exposure and measure its impact on credit risk. The key advantage is that market prices incorporate forward-looking information and aggregate diverse investor views.

### 3.2 CRISK: Climate Risk Capital Shortfall

Developed by Jung et al. (NY Fed Staff Report 977), CRISK adapts the SRISK systemic risk methodology to climate risk:

**Definition:**
```
CRISK = Expected capital shortfall of a bank in a climate stress scenario
```

**Methodology:**

**Step 1: Construct Climate Risk Factor**

Create a factor that captures climate transition risk:
- **Brown-Minus-Green (BMG) Factor**: Return spread between carbon-intensive and clean firms
- **Climate-Efficient Portfolio (CEP)**: Short position in sustainable funds

**Step 2: Estimate Climate Beta**

Using dynamic conditional correlation (DCC) models:
```
R_bank,t = α + β_market·R_market,t + β_climate·Climate_Factor_t + ε_t
```

Climate beta (β_climate) captures the bank's sensitivity to climate risk factor movements.

**Step 3: Calculate CRISK**

```
CRISK = max[0, k(D + E) - E(1 - LRMES_climate)]

Where:
k = Prudential capital ratio (e.g., 8%)
D = Book value of debt
E = Market value of equity
LRMES_climate = Long-run marginal expected shortfall under climate stress
```

**Step 4: Validate with Loan Portfolio Data**

The authors validate climate betas by comparing with granular Y-14 data on US banks' loan portfolios, showing that banks with higher exposure to carbon-intensive borrowers have higher climate betas.

### 3.3 Market-Implied Climate Risk Measures

#### 3.3.1 Option-Implied Tail Risk

Ilhan, Sautner & Vilkov (2021) use options data to measure climate tail risk:

**Methodology:**
- Examine out-of-the-money put options on high-carbon firms
- Measure changes in tail risk around climate policy events (e.g., Trump election, Paris Agreement)
- Find that policy shifts significantly affect downside risk pricing

#### 3.3.2 CDS-Implied Climate Risk

Zhang & Zhao (2022) examine credit default swap spreads:

**Finding:** Higher direct carbon emissions intensity correlates with higher CDS spreads, particularly for financially constrained firms.

**Mechanism:**
- Carbon-intensive firms face higher probability of stranded assets
- Transition costs create cash flow uncertainty
- Market participants price this risk into credit protection

### 3.4 Event Study Approaches

**The Paris Agreement Natural Experiment:**

Seltzer, Starks & Zhu (2024) use the Paris Agreement as an exogenous shock to climate policy expectations:

**Methodology:**
1. **Treatment Group**: High-carbon firms (top quartile emissions or carbon intensity)
2. **Control Group**: Low-carbon firms
3. **Difference-in-Differences**: Compare bond yields before and after December 2015

**Key Findings:**
- Treated firms experienced significant credit rating downgrades (0.48-0.63 notches)
- Bond yield spreads increased significantly for treated firms
- Effect amplified in states with stricter environmental enforcement

**Structural Model Decomposition:**

The authors decompose the spread changes using Merton (1974):
```
ΔSpread = f(ΔAsset_Value, ΔAsset_Volatility)
```

**Result:** Under constant volatility assumption, observed spread increases are too large to be explained by asset value changes alone. The volatility increase (uncertainty channel) is the primary driver.

### 3.5 Climate Factor Models for Bonds

#### 3.5.1 Carbon Risk Premium in Bonds

Bolton, Halem & Kacperczyk (2022) - "The Financial Cost of Carbon":

**Finding:** Small but emerging discount for corporate bonds of high-carbon firms, statistically significant for small caps.

#### 3.5.2 Term Structure of Carbon Premia

BIS Working Paper 1045 examines how carbon risk varies across bond maturities:

**Key Insight:** The term structure of carbon premia is hump-shaped:
- Short-term bonds: Limited carbon premium (transition seen as distant)
- Medium-term bonds: Highest premium (transition risks crystallizing)
- Long-term bonds: Premium declines (uncertainty about long-term policy)

### 3.6 Implementing Market-Based Climate Stress Tests

**Advantages:**
- Forward-looking (incorporates market expectations)
- Time-varying (can be updated in real-time)
- Uses publicly available data
- Captures both credit and market risk channels

**Limitations:**
- Requires liquid, traded securities
- May not capture risks not yet priced by markets
- Subject to market sentiment and noise
- Limited coverage for private debt

**Practical Steps:**

1. **Construct Climate Factor:**
   - Use BMG (Brown-Minus-Green) portfolio returns
   - Or climate news sentiment indices
   - Or carbon price changes

2. **Estimate Exposures:**
   - Run rolling regressions of bank returns on climate factor
   - Estimate time-varying climate betas using DCC or similar

3. **Define Stress Scenario:**
   - Specify climate factor shock (e.g., 2 standard deviation move)
   - Can be calibrated to specific events (carbon tax announcement)

4. **Calculate Stressed Values:**
   - Apply shock to portfolios based on estimated exposures
   - Compute capital shortfall under stress

5. **Aggregate and Report:**
   - Sum CRISK across institutions for systemic measure
   - Identify concentration of climate risk in financial system

---

## 4. Complete Reference List

### 4.1 Foundational Papers on Climate Risk and Credit

1. **Bolton, P., & Kacperczyk, M. (2021).** "Do Investors Care about Carbon Risk?" *Journal of Financial Economics*, 142(2), 517-549. Available at SSRN: https://ssrn.com/abstract=3398441

2. **Bolton, P., Halem, Z., & Kacperczyk, M. (2022).** "The Financial Cost of Carbon." SSRN/NBER Working Paper. https://ssrn.com/abstract=4094399

3. **Bolton, P., & Kacperczyk, M. (2023).** "Global Pricing of Carbon-Transition Risk." *Journal of Finance*, 78(6), 3677-3754.

4. **Capasso, G., Gianfrate, G., & Spinelli, M. (2020).** "Climate Change and Credit Risk." *Journal of Cleaner Production*, 266, 121634. https://doi.org/10.1016/j.jclepro.2020.121634

### 4.2 Bond Market Studies

5. **Seltzer, L., Starks, L., & Zhu, Q. (2024).** "Climate Regulatory Risks and Corporate Bonds." Federal Reserve Bank of New York Staff Report No. 1014. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr1014.pdf

6. **Höck, A., Bauckloh, M.T., Dumrose, M., & Klein, C. (2023).** "ESG Criteria and the Credit Risk of Corporate Bond Portfolios." *Journal of Asset Management*, 24(7). CFR Working Papers 23-03.

7. **Zerbib, O.D. (2019).** "The Effect of Pro-Environmental Preferences on Bond Prices: Evidence from Green Bonds." *Journal of Banking & Finance*, 98, 39-60.

8. **Duan, T., Li, F.W., & Wen, Q. (2021).** "Is Carbon Risk Priced in the Cross-Section of Corporate Bond Returns?" *Journal of Financial and Quantitative Analysis*.

### 4.3 Structural Credit Risk Models

9. **Merton, R.C. (1974).** "On the Pricing of Corporate Debt: The Risk Structure of Interest Rates." *Journal of Finance*, 29(2), 449-470.

10. **Vasicek, O. (2002).** "The Distribution of Loan Portfolio Value." *Risk*, 15(12), 160-162.

11. **Bell, A., & van Vuuren, G. (2022).** "Climate Risk in the Merton Model Framework." Working Paper.

12. **Reinders, H.J., Schoenmaker, D., & van Dijk, M. (2020).** "A Finance Approach to Climate Stress Testing." De Nederlandsche Bank Working Paper No. 686.

### 4.4 Distance-to-Default and Climate Risk

13. **Nguyen, Q., Diaz-Rainey, I., Kuruppuarachchi, D., McCarten, M., & Tan, E.K.M. (2022).** "In Search of Climate Distress Risk." *International Review of Financial Analysis*, 85, 102445. https://doi.org/10.1016/j.irfa.2022.102445

14. **Nguyen, Q., Diaz-Rainey, I., & Kuruppuarachchi, D. (2023).** "Climate Transition Risk in U.S. Loan Portfolios: Are All Banks the Same?" *International Review of Financial Analysis*, 85, 102433.

15. **Ge, Z., Liu, Q., & Wei, Z. (2024).** "Assessment of Bank Risk Exposure Considering Climate Transition Risks." *Finance Research Letters*, 69, 105933.

### 4.5 Market-Based Approaches

16. **Jung, H., Engle, R., & Giglio, S. (2024).** "CRISK: Measuring the Climate Risk Exposure of the Financial System." Federal Reserve Bank of New York Staff Report No. 977. https://www.newyorkfed.org/research/staff_reports/sr977

17. **Acharya, V.V., Berner, R., Engle, R., Jung, H., Stroebel, J., Zeng, X., & Zhao, Y. (2023).** "Climate Stress Testing." Federal Reserve Bank of New York Staff Report No. 1059. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr1059.pdf

18. **Ilhan, E., Sautner, Z., & Vilkov, G. (2021).** "Carbon Tail Risk." *Review of Financial Studies*, 34(3), 1540-1571.

19. **Zhang, S., & Zhao, X. (2022).** "Carbon Emissions and CDS Spreads." Working Paper.

### 4.6 Stress Testing Methodologies

20. **BIS (2025).** "Incorporating Physical Climate Risks into Banks' Credit Risk Models." BIS Working Papers No. 1274. https://www.bis.org/publ/work1274.pdf

21. **Basel Committee on Banking Supervision (2021).** "Climate-Related Risk Drivers and Their Transmission Channels." https://www.bis.org/bcbs/publ/d517.pdf

22. **Basel Committee on Banking Supervision (2021).** "Climate-Related Financial Risks – Measurement Methodologies." https://www.bis.org/bcbs/publ/d518.pdf

23. **Basel Committee on Banking Supervision (2023).** "The Effects of Climate Change-Related Risks on Banks: A Literature Review." BIS Working Paper No. 40. https://www.bis.org/bcbs/publ/wp40.pdf

24. **ECB (2022).** "2022 Climate Risk Stress Test." https://www.bankingsupervision.europa.eu/ecb/pub/pdf/ssm.climate_stress_test_report.20220708~2e3cc0999f.en.pdf

25. **Federal Reserve (2024).** "Pilot Climate Scenario Analysis Exercise: Summary of Participants' Risk-Management Practices and Estimates." https://www.federalreserve.gov/publications/2024-may-pilot-climate-scenario-analysis-transition-risk-module.htm

### 4.7 Bottom-Up and Cash Flow Approaches

26. **Aiello, F., & Angelico, C. (2023).** "Climate Change and Credit Risk: The Effect of Carbon Tax on Italian Banks' Business Loan Default Rates." *Business Economics*, 58(4). https://doi.org/10.1016/j.buseco.2022.11.003

27. **Faiella, I., Ferriani, F., Giambona, F., & Natoli, F. (2022).** "Climate Change and Credit Risk: The Italian Banks' Business Loan Portfolio." Bank of Italy Occasional Paper.

28. **Battiston, S., Mandel, A., Monasterolo, I., Schütze, F., & Visentin, G. (2017).** "A Climate Stress-Test of the Financial System." *Nature Climate Change*, 7(4), 283-288.

29. **Monasterolo, I., & de Angelis, L. (2020).** "Blind to Carbon Risk? An Analysis of Stock Market Reaction to the Paris Agreement." *Ecological Economics*, 170, 106571.

30. **Reinders, H.J., Schoenmaker, D., & van Dijk, M.A. (2023).** "Climate Risks and the Pricing of Corporate Bonds." *Journal of Financial Economics*.

### 4.8 Firm-Level Analysis

31. **Dietz, S., Bowen, A., Dixon, C., & Gradwell, P. (2016).** "'Climate Value at Risk' of Global Financial Assets." *Nature Climate Change*, 6(7), 676-679.

32. **Le Guenedal, T., & Tankov, P. (2024).** "Corporate Debt Value under Climate Transition." Working Paper.

33. **Kölbel, J.F., Leippold, M., Rillaerts, J., & Wang, Q. (2024).** "Ask BERT: How Regulatory Disclosure of Transition and Physical Climate Risks Affects the CDS Term Structure." *Journal of Financial Econometrics*.

34. **Bouchet, V., & Le Guenedal, T. (2020).** "Credit Risk Sensitivity to Carbon Price." Amundi Working Paper.

### 4.9 NGFS and Scenario Analysis

35. **NGFS (2024).** "NGFS Scenarios Portal." https://www.ngfs.net/ngfs-scenarios-portal/

36. **NGFS (2024).** "Guide to Climate Scenario Analysis for Central Banks and Supervisors." https://www.ngfs.net/en/press-release/ngfs-publishes-latest-long-term-climate-macro-financial-scenarios-climate-risks-assessment

37. **NGFS (2022).** "Physical Climate Risk Assessment: Practical Lessons for the Development of Climate Scenarios." https://www.ngfs.net/system/files/import/ngfs/media/2022/09/02/ngfs_physical_climate_risk_assessment.pdf

38. **Bank of England (2024).** "Measuring Climate-Related Financial Risks Using Scenario Analysis." *Bank of England Quarterly Bulletin*. https://www.bankofengland.co.uk/quarterly-bulletin/2024/2024/measuring-climate-related-financial-risks-using-scenario-analysis

### 4.10 Sovereign Credit Risk

39. **Klusak, P., Agarwala, M., Burke, M., Kraemer, M., & Mohaddes, K. (2023).** "Rising Temperatures, Falling Ratings: The Effect of Climate Change on Sovereign Creditworthiness." *Management Science*.

40. **IMF (2020).** "Feeling the Heat: Climate Shocks and Credit Ratings." IMF Working Paper 20/286. https://www.imf.org/-/media/Files/Publications/WP/2020/English/wpiea2020286-print-pdf.ashx

41. **ECB (2024).** "Creditworthy: Do Climate Change Risks Matter for Sovereign Ratings?" ECB Working Paper No. 3042. https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp3042~b5465ef93e.en.pdf

42. **Agarwala, M., Burke, M., Doherty-Bigara, J., Klusak, P., & Mohaddes, K. (2024).** "Climate Change and Sovereign Risk: A Regional Analysis for the Caribbean." Janeway Institute Working Papers.

### 4.11 TCFD and Disclosure Frameworks

43. **TCFD (2017).** "Recommendations of the Task Force on Climate-Related Financial Disclosures." https://www.fsb-tcfd.org/

44. **TCFD (2017).** "The Use of Scenario Analysis in Disclosure of Climate-Related Risks and Opportunities." Technical Supplement.

45. **UNEP FI (2020).** "Beyond the Horizon: New Tools and Frameworks for Transition Risk Assessments from UNEP FI's TCFD Banking Program." https://www.unepfi.org/wordpress/wp-content/uploads/2020/10/Climate-Risk-Applications-From-Disclosure-to-Action.pdf

46. **UNEP FI (2025).** "Bridging Climate and Credit Risk." https://www.unepfi.org/wordpress/wp-content/uploads/2025/07/Bridging-Climate-and-Credit-Risk.pdf

### 4.12 Physical Risk Assessment

47. **Caloia, F., & Jansen, D.J. (2021).** "Flood Risk and Financial Stability: Evidence from a Stress Test for the Netherlands." DNB Working Papers 730.

48. **Rossi, C.V. (2021).** "Assessing the Impact of Hurricane Frequency and Intensity on Mortgage Delinquency." *Journal of Risk Management in Financial Institutions*, 14(4), 426-442.

49. **Medina-Olivares, V., Calabrese, R., Crook, J., & Lindgren, F. (2023).** "Joint Models for Longitudinal and Discrete Survival Data in Credit Scoring." *European Journal of Operational Research*, 307(3), 1457-1473.

50. **Climate Stress Testing for Mortgage Default Probability (2024).** *International Review of Financial Analysis*, 95. https://doi.org/10.1016/j.irfa.2024.103429

### 4.13 Carbon Tax and Policy Simulation

51. **Carbone, S., Giuzio, M., Kapadia, S., Krämer, J., Mazzaferro, F., & Westerhoff, H. (2021).** "The Low-Carbon Transition, Climate Commitments and Firm Credit Risk." ECB Working Paper No. 2631. https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp2631~00a6e0368c.en.pdf

52. **Reply (2021).** "Integrating Climate Risk into Credit Risk Modelling." https://www.reply.com/contents/ARF-Climate-Risk-Into-Credit-Risk-Models.pdf

53. **Climate Bonds Initiative (2024).** "Assessing Climate Transition Risks Using Scenario Analysis and Stress Testing." https://www.climatebonds.net/files/documents/publications/Assessing-Climate-Transition-Risks-Using-Scenario-Analysis-and-Stress-Testing-Insights-for-the-Reserve-Bank-of-India.pdf

### 4.14 Additional Academic References

54. **Painter, M. (2020).** "An Inconvenient Cost: The Effects of Climate Change on Municipal Bonds." *Journal of Financial Economics*, 135(2), 468-482.

55. **Goldsmith-Pinkham, P., Gustafson, M.T., Lewis, R.C., & Schwert, M. (2023).** "Sea Level Rise Exposure and Municipal Bond Yields." *Review of Financial Studies*.

56. **Ehlers, T., Packer, F., & de Greiff, K. (2022).** "The Pricing of Carbon Risk in Syndicated Loans: Which Risks Are Priced and Why?" *Journal of Banking & Finance*, 136, 106180.

57. **Delis, M.D., de Greiff, K., & Ongena, S. (2019).** "Being Stranded on the Carbon Bubble? Climate Policy Risk and the Pricing of Bank Loans." Swiss Finance Institute Research Paper 18-10.

58. **Kleimeier, S., & Viehs, P.M. (2018).** "Carbon Disclosure, Emission Levels, and the Cost of Debt." SSRN Working Paper.

### 4.15 Rating Agency Methodologies

59. **Moody's (2023).** "Climate-Adjusted Expected Default Frequency (CAEDF) Model." Moody's Analytics.

60. **Moody's (2025).** "Climate Change: Impact on the Auto Industry Credit Risk Depends on a Climate Scenario." https://www.moodys.com/web/en/us/insights/physical-transition-risk/impact-on-the-auto-industry-credit-risk-depends-on-a-climate-scenario.html

61. **MSCI (2024).** "The Financial Materiality of Sustainability Risk in Credit Markets: A Decade of Evidence." https://www.msci.com/research-and-insights/paper/the-financial-materiality-of-sustainability-risk-in-credit-markets-a-decade-of-evidence

62. **IEEFA (2024).** "Climate Risks Underplayed in Recent Credit Rating Actions." https://ieefa.org/resources/climate-risks-underplayed-recent-credit-rating-actions

### 4.16 Financial Stability Board and Regulatory Documents

63. **FSB (2025).** "Assessment of Climate-Related Vulnerabilities: Analytical Framework and Toolkit." https://www.fsb.org/uploads/P160125.pdf

64. **Basel Committee on Banking Supervision (2025).** "A Framework for the Voluntary Disclosure of Climate-Related Financial Risks." https://www.bis.org/bcbs/publ/d597.pdf

65. **ECB (2024).** "Occasional Paper Series: Advancements in Stress-Testing Methodologies." https://www.ecb.europa.eu/pub/pdf/scpops/ecb.op348~6b72fbe3cf.en.pdf

### 4.17 Practitioner Guides

66. **Schmalenbach Journal (2023).** "The Impact of Transitory Climate Risk on Firm Valuation and Financial Institutions: A Stress Test Approach." https://link.springer.com/article/10.1007/s41471-023-00166-y

67. **Springer Risk Management (2025).** "Calibrating Credit Risk Parameters for Climate Stress Testing." https://link.springer.com/article/10.1057/s41283-025-00189-1

68. **Springer Risk Management (2025).** "Inclusion of Carbon Pricing into Stress Testing for the Austrian Banking Sector." https://link.springer.com/article/10.1057/s41283-025-00184-6

69. **Weber, O. (2024).** "Climate Stress Testing in the Financial Industry." *Ecological Economics*, 208, 107781.

### 4.18 ESG and Credit Risk

70. **ScienceDirect (2024).** "ESG Factors and Firms' Credit Risk." *Research in International Business and Finance*. https://doi.org/10.1016/j.ribaf.2024.100026

71. **Devalle, A., Fiandrino, S., & Cantino, V. (2017).** "The Linkage between ESG Performance and Credit Ratings: A Firm-Level Perspective Analysis." *International Journal of Business and Management*, 12(9), 1-53.

72. **Bahra, B., & Thukral, L. (2020).** "ESG in Global Corporate Bonds: The Analysis Behind the Hype." *Journal of Portfolio Management*.

73. **Henke, H.M. (2016).** "The Effect of Social Screening on Bond Mutual Fund Performance." *Journal of Banking & Finance*, 67, 69-84.

---

## Notes on Using These References

### For Academic Research:
- The Merton-based papers (9-15) provide the theoretical foundation
- The empirical studies (1-8, 13-15) offer evidence on carbon-credit risk relationships
- The stress testing papers (20-30) provide methodological guidance

### For Practitioner Implementation:
- Start with NGFS documentation (35-37) for scenario frameworks
- Use BIS papers (20-23) for regulatory alignment
- Consult Moody's and MSCI materials (59-61) for commercial model insights

### For Policy Analysis:
- The sovereign credit papers (39-42) extend the analysis beyond corporates
- The FSB and ECB documents (63-65) provide systemic risk perspectives
- The carbon tax simulations (26-27, 51) offer policy counterfactual frameworks

---

*Document prepared: January 2026*
*Compiled from academic literature, regulatory publications, and practitioner resources*

## Related
[[MKT_MOC]] · Home: [[_INDEX]]

#arm/mkt #type/theory
