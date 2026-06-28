# NGFS Short-Term Scenarios: Economic Assumptions and Methodology

## Bridging Climate Timescales with Financial Planning Horizons

---

## Table of Contents

1. [The Fundamental Challenge](#1-the-fundamental-challenge)
2. [Key Economic Assumptions](#2-key-economic-assumptions)
3. [The Four Scenario Narratives](#3-the-four-scenario-narratives)
4. [Addressing the Temporal Horizon Problem](#4-addressing-the-temporal-horizon-problem)
5. [Quantitative Results Summary](#5-quantitative-results-summary)
6. [Limitations](#6-limitations)
7. [Implications for Credit Risk Research](#7-implications-for-credit-risk-research)
8. [Key References](#8-key-references)

---

## 1. The Fundamental Challenge

### The Temporal Mismatch Problem

Climate change operates on decadal-to-century timescales, while financial institutions, central banks, and supervisors typically work with 3-5 year planning horizons. The NGFS faced a core conceptual problem:

- **Long-term NGFS scenarios** (extending to 2050-2100) are useful for understanding transition pathways
- But they **don't capture** the business-cycle dynamics, sudden shocks, and financial market reactions that matter for:
  - Stress testing
  - Monetary policy analysis
  - Credit risk assessment
  - Capital planning

### The Solution: Reconceptualizing Climate Scenarios

The NGFS short-term scenarios, published in **May 2025**, address this by fundamentally reconceptualizing what a "climate scenario" means for near-term analysis. Rather than compressing long-term trends, they model:

- Discrete shocks and their propagation
- Financial market reactions and feedback loops
- Expectations-driven repricing
- Business cycle interactions with climate risks

---

## 2. Key Economic Assumptions

### 2.1 Baseline Calibration

The short-term scenarios use the **October 2023 IMF World Economic Outlook** as the anchor for baseline projections.

**Macroeconomic variables aligned to IMF projections:**
- GDP growth trajectories
- Inflation paths
- Technical progress assumptions
- Sectoral growth patterns
- Population levels
- Consumption patterns

This provides a credible, internationally recognized starting point that financial institutions can relate to their existing planning frameworks.

### 2.2 The Modeling Framework: Three Coupled Models

The scenarios are produced through an innovative coupling of three distinct models:

| Model | Type | Function | Coverage |
|-------|------|----------|----------|
| **GEM-E3** | Computable General Equilibrium (Economy-Energy-Environment) | Determines real macro variables, sectoral output, carbon prices, employment, trade | 50 sectors, 46 countries |
| **EIRIN** | Stock-Flow Consistent behavioral model | Projects inflation dynamics, monetary policy responses, financial-real economy interactions | 5 macro-regions, quarterly frequency |
| **CLIMACRED** | Climate credit risk model | Calculates scenario-contingent bond/equity valuations, probability of default by sector, cost of capital | 50 sectors, 46 countries |

### 2.3 Model Coupling Architecture

The models are coupled iteratively in a specific sequence:

```
Step 0: Scenario-contingent physical impacts and transition policies → GEM-E3 and EIRIN

Step 1: GEM-E3 calculates:
        → Carbon prices → EIRIN
        → Sectoral output trajectories → CLIMACRED

Step 2: EIRIN calculates:
        → Risk-free policy rate → CLIMACRED

Step 3: CLIMACRED calculates:
        → Scenario-adjusted sectoral cost of capital → GEM-E3

Step 4: GEM-E3 performs integrated run incorporating financial feedback effects
```

This architecture captures **financial-real economy feedback loops** that are absent in long-term IAM-based scenarios.

### 2.4 Agent Behavior Assumptions

#### Expectations Formation

Unlike long-term IAMs that often assume perfect foresight, the short-term models use **adaptive expectations**:

- Agents respond to observed shocks with persistence effects
- GDP shocks persist over time (up to a decade based on Kotz et al. 2024)
- Central banks respond via Taylor rules (calibrated to ECB's New Area-Wide Model II)
- Taylor rule responses affect credit conditions and investment decisions

#### Key Behavioral Parameters

| Parameter | Role | Variation |
|-----------|------|-----------|
| **Elasticity of substitution** | Ease of switching from fossil to clean energy | Varies by sector; high in electricity, low in cement |
| **Revenue recycling** | How carbon tax revenues are used | Rebated to households vs. green investment |
| **Pass-through rates** | Transmission of carbon costs to consumer prices | Depends on market structure |
| **Risk premium sensitivity** | Response of financing costs to climate news | Calibrated to historical episodes |

#### Combined Impact on Inflation

The interaction of elasticity and revenue recycling determines inflationary outcomes:

| | **Low Elasticity of Substitution** | **High Elasticity of Substitution** |
|---|---|---|
| **Low Revenue Rebate to Households** | Medium inflation | Low inflation |
| **High Revenue Rebate to Households** | High inflation | Medium inflation |

---

## 3. The Four Scenario Narratives

The NGFS developed four distinct narratives, each exploring different combinations of transition and physical risks over a **5-year horizon (2025-2030)**:

### 3.1 Highway to Paris (Orderly Transition)

**Narrative:** Elevated uncertainty about fossil energy supply leads governments to implement an ambitious mitigation pathway in a timely and anticipated fashion. Green public investment booms, technology advances rapidly, and financial disruption is contained.

**Key Assumptions:**
- Early, anticipated implementation of carbon pricing aligned with Net Zero 2050
- Carbon tax revenues recycled into green public investments and subsidies
- High elasticity of substitution (economy well-prepared for transition)
- Consistent preferences of consumers and investors toward green products
- Green prudential policies prevent financial turmoil

**Economic Logic:** Because policy is anticipated, firms and households adjust gradually. Innovation responds to policy signals, easing supply bottlenecks. Some initial "fossilflation" occurs but dissipates as green alternatives scale.

**Shock Sequence:**
| Year 1 | Year 2 | Year 3 |
|--------|--------|--------|
| Carbon tax (anticipated) | Carbon tax continues | Carbon tax continues |
| Green innovation boost | Boom in green public investment | Productivity gains materialize |

### 3.2 Sudden Wake-Up Call (Disorderly Transition)

**Narrative:** Policy makers initially procrastinate until an exogenous event (severe disaster, election result) triggers a sudden change in policy stance. Governments hastily implement carbon policies, setting off shock waves through the economy and financial system—a "Climate Minsky Moment."

**Key Assumptions:**
- Initial policy procrastination until an exogenous trigger
- Unanticipated, abrupt carbon pricing implementation
- Low elasticity of substitution (economy unprepared)
- Asset stranding in polluting sectors
- Sharp increase in risk premia and confidence crisis

**Economic Logic:** The "sunspot" trigger has no direct economic impact—it's purely an expectations shock that causes sudden policy change. This mirrors historical precedents like Germany's nuclear policy reversal after Fukushima.

**Shock Sequence:**
| Year 1 | Year 2 | Year 3 |
|--------|--------|--------|
| (No policy action) | Carbon tax (unanticipated) | Carbon tax continues |
| | Shock to physical risk expectations | Confidence crisis |
| | Risk premia spike | Financial turmoil from stranded assets |

### 3.3 Disasters and Policy Stagnation (Physical Risk)

**Narrative:** Severe acute physical disasters hit exposed jurisdictions. Investors price in sizeable risk premia, freezing private investment. Households increase precautionary savings, and insurance costs surge. No new climate policies are implemented.

**Key Assumptions:**
- No new climate policies implemented
- Sequence of severe, plausible extreme weather events in specific regions
- Physical capital destruction, labor productivity drops, supply chain disruptions
- Investors price in elevated physical risk premia
- Insurance costs increase sharply; households increase precautionary savings

**Economic Logic:** Physical risk is treated as **predetermined** in the short run—current emissions have already committed the climate system to certain hazards. The scenario explores tail events from the current climate distribution, not future warming.

**Regional Impacts:**
- **Africa:** GDP losses up to 12.5%
- **Asia:** GDP losses up to 6%
- **Advanced Economies:** Spillover effects through trade and financial linkages

**Shock Sequence:**
| Year 1 | Year 2 | Year 3 |
|--------|--------|--------|
| Severe hazard-specific disaster | Continued physical impacts | Recovery phase |
| Supply chain disruptions | Post-disaster fiscal spending | Elevated risk premia persist |
| Risk premia spike | Sovereign debt pressure | Insurance repricing |

### 3.4 Diverging Realities (Compound Risk)

**Narrative:** Advanced economies pursue ambitious transition policies while EMDEs/LICs experience severe disasters leading to "recovery traps." Disruption of critical mineral supply chains hampers the global transition. The realization that global transition is ineffective triggers worldwide risk premium increases.

**Key Assumptions:**
- Advanced economies pursue ambitious transition (face transition risk)
- EMDEs/LICs experience severe disasters leading to "recovery traps"
- Disruption of critical mineral supply chains (batteries, solar panels, wind equipment)
- Global realization that transition is ineffective triggers risk premium spike
- Lack of external financing prevents global coordination

**Economic Logic:** This captures the **global nature of climate risk**—even if some regions transition successfully, global failure means everyone faces elevated physical risk expectations. Supply chain dependencies create spillovers from disaster-affected regions to transitioning economies.

**Dual Shock Structure:**

*Advanced Economies:*
| Year 1 | Year 2 | Year 3 |
|--------|--------|--------|
| Carbon tax (anticipated) | Carbon tax continues | Carbon tax continues |
| Boom in green investment | Supply constraints from global south | Higher capital costs |
| | Risk premia rise | Transition slows |

*EMDEs and LICs:*
| Year 1 | Year 2 | Year 3 |
|--------|--------|--------|
| Severe disaster | Continued physical impacts | Recovery trap |
| Supply chain disruptions | Fiscal balance deteriorates | Sovereign risk premia spike |
| Migration begins | External financing dries up | Inability to transition |

---

## 4. Addressing the Temporal Horizon Problem

The NGFS uses several methodological innovations to make long-horizon climate dynamics relevant for short-term analysis:

### 4.1 Decoupling Physical Risk from Current Policy

A critical insight: **physical risk is predetermined over 3-5 years**. The climate system's inertia means that emissions reductions today won't materially change physical hazards until decades later.

**Implications:**
- Short-term physical risk scenarios don't depend on short-term policy choices
- They instead explore the **tail of the current physical risk distribution**
- This allows modeling severe but plausible near-term disasters without implying unrealistic warming trajectories
- No contradiction between "no policy change" and "severe physical impacts"

### 4.2 Expectations as a Transmission Channel

Rather than waiting for physical damages to accumulate, the scenarios model **changes in expectations** about future climate impacts:

| Trigger | Transmission | Financial Impact |
|---------|--------------|------------------|
| Realization that global transition is failing | Repricing of carbon-intensive assets | Higher cost of capital for brown sectors |
| Increased perception of physical risk | Higher risk premia demanded | Lower investment, insurance repricing |
| Policy announcement shock | Forward-looking asset revaluation | Immediate market adjustment |

This "bringing forward" of future risks through expectations is economically coherent and captures how financial markets actually respond to news.

### 4.3 Focusing on Shocks and Amplification, Not Trends

| Long-Term Scenarios Emphasize | Short-Term Scenarios Emphasize |
|------------------------------|-------------------------------|
| Gradual trends (rising temperatures) | **Discrete shocks** (policy announcements, disasters) |
| Smooth carbon price paths | **Amplification mechanisms** (contagion, fire sales) |
| Equilibrium outcomes | **Non-linearities** (threshold effects, tipping points in sentiment) |
| Single risk type per scenario | **Compound risks** (multiple simultaneous shocks) |

### 4.4 Higher Frequency Dynamics

| Feature | Long-Term Scenarios | Short-Term Scenarios |
|---------|---------------------|----------------------|
| **Time step** | 5 years | Quarterly |
| **Horizon** | 2050-2100 | 2025-2030 |
| **Balance sheet assumption** | Dynamic (unrealistic over 30 years) | Static or semi-static (realistic) |
| **Expectations** | Perfect foresight (IAMs) | Adaptive, backward-looking |
| **Financial sector** | Absent or stylized | Explicit (CLIMACRED) |
| **Monetary policy** | Exogenous or absent | Endogenous Taylor rule |
| **Sectoral granularity** | Limited | 50 sectors |
| **Country coverage** | Aggregated regions | 46 countries |

### 4.5 Scenario-Contingent Financial Variables

A major innovation is the direct output of **financial risk metrics**:

- Sector-specific probability of default (PD)
- Equity and bond valuation adjustments
- Cost of capital by sector and country
- Inflation and policy rate paths (quarterly)
- GDP impacts by sector and region

This eliminates the need for users to separately translate macro scenarios into financial impacts—a major source of inconsistency in previous exercises.

---

## 5. Quantitative Results Summary

### 5.1 Headline Impacts by Scenario

| Scenario | GDP Impact (World) | Unemployment Change | PD Change (Power Sector) | Primary Driver |
|----------|-------------------|---------------------|--------------------------|----------------|
| **Highway to Paris** | Modest negative (short-term) | +0.5-1.0 pp | Moderate increase | Transition costs offset by green investment |
| **Sudden Wake-Up Call** | -1.3% annually | +1.3 pp | >10 pp increase | Policy shock, stranded assets, confidence crisis |
| **Disasters & Stagnation** | Up to -12.5% (Africa), -6% (Asia) | Varies by region | Sharp increase in affected regions | Physical destruction, risk premia |
| **Diverging Realities** | Mixed (AEs vs. EMDEs) | Divergent | Elevated globally | Supply chain disruption, global repricing |

### 5.2 Sectoral Vulnerability

The power sector is identified as **particularly vulnerable** due to:
1. High capital intensity
2. High debt-to-capital ratio (sectoral average)
3. Long asset lives creating stranding risk
4. Direct exposure to both transition and physical risks

**Probability of Default Increases (Illustrative):**

| Sector | Highway to Paris | Sudden Wake-Up Call | Disasters & Stagnation |
|--------|------------------|---------------------|------------------------|
| Power Supply | +3-5 pp | >+10 pp | +5-8 pp (affected regions) |
| Oil & Gas | +2-4 pp | +8-12 pp | +3-5 pp |
| Transport Equipment | +1-3 pp | +5-8 pp | +2-4 pp |
| Agriculture | +1-2 pp | +2-3 pp | +6-10 pp (affected regions) |

### 5.3 Inflation and Monetary Policy Response

| Scenario | Inflation Impact | Policy Rate Response | Mechanism |
|----------|------------------|---------------------|-----------|
| Highway to Paris | Moderate increase (fossilflation) | Gradual tightening | Energy price pass-through |
| Sudden Wake-Up Call | Sharp spike then decline | Initial tightening, then easing | Supply shock followed by demand collapse |
| Disasters & Stagnation | Food/commodity price spikes | Mixed (stagflationary) | Supply disruption vs. demand destruction |
| Diverging Realities | Elevated in AEs (supply chains) | Tightening in AEs | Import price pressure, supply constraints |

---

## 6. Limitations

The NGFS is transparent about what the short-term scenarios **do not** capture:

### 6.1 Excluded Risk Factors

| Limitation | Description | Potential Impact |
|------------|-------------|------------------|
| **Tipping points** | Non-linear, irreversible climate system changes | Underestimates tail risks |
| **Chronic physical risk** | Sea level rise, gradual temperature increases | Less relevant over 5 years, but omits slow-moving risks |
| **Nature-related risks** | Biodiversity loss, ecosystem degradation | Missing feedback loops |
| **Polycrises** | Interacting crises that compound vulnerabilities | Underestimates systemic risk |
| **Country-specific responses** | Fiscal buffers, guarantees, bailouts | Overestimates stress in well-prepared countries |
| **Extreme tail risks** | Scenarios are "severe but plausible," not worst-case | Not suitable for maximum adverse analysis |

### 6.2 Modeling Limitations

- **GEM-E3** assumes perfect foresight in the power module, causing some anticipatory effects before policy implementation
- **EIRIN** does not cover Africa explicitly (regional aggregation)
- **CLIMACRED** does not model country-specific policy responses like bailouts
- **Physical risk calibration** relies on current climate distribution, not future intensification
- **Feedback loops** between financial stress and real economy are modeled but simplified

### 6.3 Data and Calibration Challenges

- Historical precedents for climate policy shocks are limited
- Non-linearities in climate-economy relationships are uncertain
- Sectoral emission data quality varies across countries
- Private company coverage limited compared to public firms

---

## 7. Implications for Credit Risk Research

### 7.1 Advantages for Bond Market Analysis

The short-term scenarios offer several advantages for credit risk research:

| Feature | Benefit for Credit Analysis |
|---------|----------------------------|
| **Direct PD outputs** | No need to separately model scenario-to-default transmission |
| **Sectoral granularity** | 50 sectors allow differentiated portfolio analysis |
| **Financial feedback** | Cost of capital effects are endogenous |
| **Realistic horizon** | Matches typical stress test and credit rating horizons (3-5 years) |
| **Compound scenarios** | Diverging Realities captures both transition and physical risks |
| **Quarterly frequency** | Allows analysis of shock propagation dynamics |

### 7.2 Integration with Structural Credit Models

The NGFS short-term scenarios can be integrated with Merton-based approaches:

**Step 1: Extract Scenario Variables**
- Sectoral output trajectories (from GEM-E3)
- Cost of capital by sector (from CLIMACRED)
- Risk-free rates (from EIRIN)
- Inflation paths (from EIRIN)

**Step 2: Translate to Firm-Level Impacts**
- Map sectoral shocks to firm cash flows
- Adjust asset values for NPV of climate costs
- Calibrate asset volatility to scenario uncertainty

**Step 3: Calculate Climate-Adjusted Credit Metrics**
- Distance-to-default under each scenario
- Scenario-contingent probability of default
- Credit spread implications

### 7.3 Considerations for Longer-Dated Instruments

For bonds with maturities beyond 5 years, researchers may need to:

1. **Bridge to long-term scenarios**: Use short-term scenarios for years 1-5, then transition to NGFS long-term paths
2. **Term structure analysis**: Model how carbon risk premia vary across maturities
3. **Add idiosyncratic factors**: Firm-level characteristics not captured in sectoral averages
4. **Consider roll-over risk**: Refinancing conditions under stressed scenarios

### 7.4 Recommended Approach for Counterfactual Analysis

For policy counterfactual studies (e.g., "What if a carbon tax were implemented?"):

1. **Select appropriate scenario pair**: Compare Highway to Paris vs. Disasters & Stagnation for policy vs. no-policy
2. **Match firm characteristics**: Align sample firms with NGFS sector definitions
3. **Apply sectoral shocks**: Use CLIMACRED PD adjustments as starting point
4. **Refine with firm-level data**: Adjust for emission intensity, geographic exposure, financial leverage
5. **Validate against market data**: Compare implied spreads with observed market pricing

---

## 8. Key References

### NGFS Official Documentation

1. **NGFS (2025).** "NGFS Short-Term Climate Scenarios: Technical Documentation V1.0." May 2025. https://www.ngfs.net/system/files/2025-07/NGFS%20Short-term%20climate%20Scenarios_Technical%20Documentation.pdf

2. **NGFS (2025).** "NGFS Short-Term Scenarios for Central Banks and Supervisors." Presentation, May 2025. https://www.ngfs.net/system/files/2025-05/NGFS%20Short-term%20scenarios_Presentation_1.pdf

3. **NGFS (2023).** "Conceptual Note on Short-Term Climate Scenarios." October 2023. https://www.ngfs.net/sites/default/files/medias/documents/conceptual-note-on-short-term-climate-scenarios.pdf

4. **NGFS (2024).** "NGFS Climate Scenarios Technical Documentation V5.0." November 2024. https://www.ngfs.net/system/files/2025-01/NGFS%20Climate%20Scenarios%20Technical%20Documentation.pdf

5. **NGFS (2025).** "Guide to Climate Scenario Analysis for Central Banks and Supervisors – Update." November 2025. https://www.ngfs.net/system/files/2025-11/Guide%20to%20climate%20scenario%20analysis%20for%20central%20banks%20and%20supervisors%20–%20Update_0.pdf

6. **NGFS Scenarios Portal.** Interactive data explorer. https://www.ngfs.net/ngfs-scenarios-portal/

### Underlying Models

7. **Battiston, S., et al. (2023).** "CLIMACRED: A Climate Credit Risk Model for Scenario-Contingent Financial Valuation." Working Paper.

8. **Capros, P., et al. (2013).** "GEM-E3 Model Documentation." JRC Technical Reports, European Commission.

9. **Monasterolo, I., & Raberto, M. (2018).** "The EIRIN Flow-of-Funds Behavioural Model of Green Fiscal Policies and Green Sovereign Bonds." *Ecological Economics*, 144, 228-243.

10. **Dunz, N., Mazzocchetti, A., Monasterolo, I., & Raberto, M. (2023).** "Macrofinancial Feedbacks from Climate Risk: Evidence from a Stock-Flow Consistent Model." Working Paper.

### Commentary and Analysis

11. **Carbon Tracker Initiative (2025).** "New NGFS Short-Term Scenarios for Central Banks & Supervisors." June 2025. https://carbontracker.org/new-ngfs-short-term-scenarios-for-central-banks-supervisors/

12. **Carbon Tracker Initiative (2025).** "NGFS Scenarios and the Damage Done." March 2025. https://carbontracker.org/ngfs-scenarios-and-the-damage-done/

13. **OMFIF (2025).** "Assessing the Immediate Climate Financial Risks in NGFS' Short-Term Scenarios." June 2025. https://www.omfif.org/2025/06/assessing-immediate-and-material-climate-related-financial-risks/

14. **SS&C Algorithmics (2025).** "How NGFS Short-Term Scenarios Impact Financial Stability." May 2025. https://www.ssctech.com/blog/how-ngfs-short-term-scenarios-impact-financial-stability

### Related Academic Literature

15. **Kotz, M., Levermann, A., & Wenz, L. (2024).** "The Economic Commitment of Climate Change." *Nature*, 628, 551-557.

16. **Battiston, S., Mandel, A., Monasterolo, I., Schütze, F., & Visentin, G. (2017).** "A Climate Stress-Test of the Financial System." *Nature Climate Change*, 7(4), 283-288.

17. **Acharya, V.V., Berner, R., Engle, R., Jung, H., Stroebel, J., Zeng, X., & Zhao, Y. (2023).** "Climate Stress Testing." Federal Reserve Bank of New York Staff Report No. 1059.

---

## Appendix: Scenario Variable Availability

### Macroeconomic Variables (from GEM-E3)

- GDP (by country, sector)
- Employment/Unemployment (by country, sector)
- Investment (by country, sector, technology)
- Trade flows (bilateral, by sector)
- Energy prices (by fuel type, country)
- Carbon prices (by country/region)
- Sectoral output (50 sectors × 46 countries)

### Financial Variables (from CLIMACRED)

- Probability of default (by sector, country)
- Bond valuations (scenario-adjusted)
- Equity valuations (scenario-adjusted)
- Cost of capital (by sector, country)
- Credit spreads (implied)

### Monetary Policy Variables (from EIRIN)

- Policy interest rates (quarterly, by macro-region)
- Inflation (quarterly, by macro-region)
- Credit growth
- Investment response to monetary conditions

### Physical Risk Variables

- Direct damage estimates (by hazard type, region)
- Supply chain disruption indices
- Critical mineral availability constraints
- Agricultural productivity shocks

---

*Document prepared: January 2026*
*Based on NGFS Short-Term Scenarios V1.0 (May 2025) and supporting documentation*

## Related
[[MKT_MOC]] · Home: [[_INDEX]]

#arm/mkt #type/theory
