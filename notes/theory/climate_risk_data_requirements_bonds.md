# Data Requirements for Climate Risk Assessment of Debt Instruments

## A Practical Guide for Implementing Climate-Adjusted Credit Risk Models for Bond Portfolios

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Core Data Categories](#2-core-data-categories)
3. [Corporate Bond Data Requirements](#3-corporate-bond-data-requirements)
4. [Sovereign Bond Data Requirements](#4-sovereign-bond-data-requirements)
5. [Climate Scenario Data](#5-climate-scenario-data)
6. [Physical Risk Data](#6-physical-risk-data)
7. [Transition Risk Data](#7-transition-risk-data)
8. [Data Sources and Providers](#8-data-sources-and-providers)
9. [Data Quality and Gap Analysis](#9-data-quality-and-gap-analysis)
10. [Minimum Viable Dataset](#10-minimum-viable-dataset)

---

## 1. Introduction

### 1.1 Purpose

This document outlines the fundamental data requirements for implementing climate risk assessment methodologies on debt instrument portfolios, specifically corporate and sovereign bonds. The focus is on practical, actionable data needs that support the quantitative frameworks discussed in the broader research on Monte Carlo simulation and climate risk.

### 1.2 Scope: Debt Instruments

| Instrument Type | Key Risk Drivers | Primary Climate Concerns |
|-----------------|------------------|--------------------------|
| **Corporate Bonds** | Issuer default risk, spread risk | Transition risk (carbon costs), physical risk (asset damage) |
| **Sovereign Bonds** | Country credit risk, interest rate risk | Physical risk (GDP impact), transition risk (fiscal impact) |
| **Green/Sustainability Bonds** | Same as above + use of proceeds | Greenwashing risk, project performance |

### 1.3 Methodologies Covered

The data requirements support implementation of:
- Climate-adjusted Merton models for corporate PD estimation
- Climate stress testing using NGFS scenarios
- Climate Value-at-Risk (VaR) for bond portfolios
- Physical risk assessment at issuer/country level
- Transition risk assessment via carbon pricing scenarios

---

## 2. Core Data Categories

### 2.1 Data Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLIMATE RISK DATA ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      PORTFOLIO DATA                                 │ │
│  │  • Bond holdings (ISIN, notional, maturity, coupon)                │ │
│  │  • Issuer mapping (LEI, sector, country)                           │ │
│  │  • Market prices, yields, spreads                                  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    ↓                                     │
│  ┌─────────────────────┐    ┌─────────────────────┐                     │
│  │   ISSUER DATA       │    │   SCENARIO DATA     │                     │
│  │  (Corporate/Sov)    │    │   (NGFS/Custom)     │                     │
│  │                     │    │                     │                     │
│  │ • Financials        │    │ • Carbon prices     │                     │
│  │ • Emissions         │    │ • GDP pathways      │                     │
│  │ • Asset locations   │    │ • Temperature       │                     │
│  │ • Sector exposure   │    │ • Policy shocks     │                     │
│  └─────────────────────┘    └─────────────────────┘                     │
│            ↓                          ↓                                  │
│  ┌─────────────────────┐    ┌─────────────────────┐                     │
│  │  PHYSICAL RISK      │    │  TRANSITION RISK    │                     │
│  │  DATA               │    │  DATA               │                     │
│  │                     │    │                     │                     │
│  │ • Hazard maps       │    │ • Carbon intensity  │                     │
│  │ • Damage functions  │    │ • Stranded assets   │                     │
│  │ • Event frequencies │    │ • Technology costs  │                     │
│  └─────────────────────┘    └─────────────────────┘                     │
│                                    ↓                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      OUTPUT METRICS                                 │ │
│  │  • Climate-adjusted PD/spreads    • Portfolio Climate VaR          │ │
│  │  • Scenario-conditional losses    • Stranded asset exposure        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Category Summary

| Category | Corporate Bonds | Sovereign Bonds | Update Frequency |
|----------|-----------------|-----------------|------------------|
| Portfolio Holdings | Required | Required | Daily/Monthly |
| Market Data | Required | Required | Daily |
| Financial Statements | Required | N/A | Quarterly/Annual |
| Credit Ratings | Required | Required | As updated |
| Emissions Data | Required | Required (country-level) | Annual |
| Asset Geolocation | Required | Limited applicability | Annual |
| Climate Scenarios | Required | Required | Annual (NGFS updates) |
| Hazard Data | Required | Required (country-level) | Annual |

---

## 3. Corporate Bond Data Requirements

### 3.1 Bond-Level Data

**Identification and Structure:**

| Field | Description | Example | Source |
|-------|-------------|---------|--------|
| ISIN | International Securities Identification Number | US037833AK68 | Bloomberg, Refinitiv |
| Issuer LEI | Legal Entity Identifier | 5493001A3B8B1MQ1V108 | GLEIF |
| Issuer Name | Legal name of issuing entity | Apple Inc. | Bond prospectus |
| Currency | Denomination currency | USD | Bloomberg |
| Coupon Rate | Annual coupon (%) | 2.85% | Bloomberg |
| Coupon Frequency | Payment frequency | Semi-annual | Bloomberg |
| Issue Date | Original issuance date | 2021-02-08 | Bloomberg |
| Maturity Date | Final redemption date | 2061-02-08 | Bloomberg |
| Outstanding Amount | Current face value outstanding | $2,500,000,000 | Bloomberg |
| Seniority | Debt ranking | Senior Unsecured | Bloomberg |
| Call Features | Embedded options | Make-whole call | Bond prospectus |

**Market Data:**

| Field | Description | Frequency | Source |
|-------|-------------|-----------|--------|
| Clean Price | Market price excluding accrued interest | Daily | Bloomberg, Refinitiv |
| Yield to Maturity | Implied yield | Daily | Calculated |
| Option-Adjusted Spread (OAS) | Spread over risk-free curve | Daily | Bloomberg |
| Z-Spread | Zero-volatility spread | Daily | Calculated |
| Asset Swap Spread | Spread vs. swap curve | Daily | Bloomberg |
| Duration | Modified duration | Daily | Calculated |
| Convexity | Second-order price sensitivity | Daily | Calculated |
| Bid-Ask Spread | Liquidity indicator | Daily | Bloomberg |

### 3.2 Issuer-Level Financial Data

**For Climate-Adjusted Merton Model Implementation:**

| Field | Description | Use in Model | Source |
|-------|-------------|--------------|--------|
| **Equity Market Cap** | Market value of equity | V_equity in Merton | Bloomberg |
| **Equity Volatility** | Historical/implied volatility | σ_equity → σ_assets | Bloomberg, Options data |
| **Total Debt** | Book value of all debt | Default point proxy | Financial statements |
| **Short-term Debt** | Debt due within 1 year | KMV default point | Financial statements |
| **Long-term Debt** | Debt due beyond 1 year | KMV default point | Financial statements |
| **Total Assets** | Book value of assets | Leverage calculation | Financial statements |
| **EBITDA** | Earnings before interest, taxes, depreciation | Debt service capacity | Financial statements |
| **Interest Expense** | Annual interest payments | Interest coverage | Financial statements |
| **Revenue** | Total sales/revenue | Carbon intensity denominator | Financial statements |
| **Operating Cash Flow** | Cash from operations | Liquidity assessment | Financial statements |

**Merton Model Data Flow:**

```
Equity Market Cap (E) ──┐
                        ├──→ Solve for Asset Value (V) and Asset Volatility (σ_V)
Equity Volatility (σ_E) ┘
                              │
Total Debt (D) ───────────────┤
                              │
Risk-free Rate (r) ───────────┤
                              ↓
                     Probability of Default = N(-d₂)
                              │
Climate Adjustment ───────────┤
(Carbon costs, physical shocks)│
                              ↓
                     Climate-Adjusted PD
```

### 3.3 Sector Classification

**Required Classifications:**

| Classification System | Description | Use Case |
|----------------------|-------------|----------|
| **GICS** | Global Industry Classification Standard | Sector-level carbon intensity |
| **NACE** | EU statistical classification | Regulatory alignment (EU Taxonomy) |
| **SIC/NAICS** | US industry codes | US regulatory alignment |
| **ICB** | Industry Classification Benchmark | Alternative to GICS |

**Climate-Relevant Sector Mapping:**

| Sector | GICS Code | Climate Risk Profile |
|--------|-----------|---------------------|
| Energy | 10 | High transition risk |
| Materials | 15 | High transition risk |
| Industrials | 20 | Medium transition risk |
| Utilities | 55 | High transition risk |
| Consumer Staples | 30 | Medium physical risk |
| Real Estate | 60 | High physical risk |
| Financials | 40 | Indirect exposure |

### 3.4 Credit Data

| Field | Description | Source |
|-------|-------------|--------|
| Credit Rating (S&P) | Long-term issuer rating | S&P Global |
| Credit Rating (Moody's) | Long-term issuer rating | Moody's |
| Credit Rating (Fitch) | Long-term issuer rating | Fitch |
| Rating Outlook | Positive/Stable/Negative | Rating agencies |
| CDS Spread (5Y) | 5-year credit default swap spread | Bloomberg, Markit |
| Implied PD | Market-implied probability of default | Calculated from CDS |
| Distance to Default | Merton-based DD measure | Calculated |

---

## 4. Sovereign Bond Data Requirements

### 4.1 Bond-Level Data

**Identification and Structure:**

| Field | Description | Example | Source |
|-------|-------------|---------|--------|
| ISIN | Bond identifier | US912810SV17 | Bloomberg |
| Issuing Country | ISO country code | US | Bloomberg |
| Currency | Denomination | USD | Bloomberg |
| Coupon Rate | Annual coupon | 1.875% | Bloomberg |
| Maturity Date | Redemption date | 2051-02-15 | Bloomberg |
| Outstanding Amount | Amount outstanding | $73,000,000,000 | Treasury/MoF |
| Bond Type | Nominal/Inflation-linked | Nominal | Bloomberg |

**Market Data:**

| Field | Description | Frequency | Source |
|-------|-------------|-----------|--------|
| Clean Price | Market price | Daily | Bloomberg |
| Yield to Maturity | Implied yield | Daily | Bloomberg |
| Spread to Benchmark | vs. German Bund, US Treasury | Daily | Calculated |
| Real Yield | Inflation-adjusted yield | Daily | Bloomberg |
| Duration | Interest rate sensitivity | Daily | Calculated |

### 4.2 Country-Level Economic Data

**Macroeconomic Fundamentals:**

| Field | Description | Frequency | Source |
|-------|-------------|-----------|--------|
| GDP (Nominal) | Gross Domestic Product | Quarterly | IMF, World Bank |
| GDP Growth Rate | Real GDP growth | Quarterly | IMF, National statistics |
| GDP per Capita | Income level indicator | Annual | World Bank |
| Inflation Rate | CPI or GDP deflator | Monthly | IMF, National statistics |
| Unemployment Rate | Labor market indicator | Monthly | ILO, National statistics |
| Current Account Balance | % of GDP | Quarterly | IMF |
| Government Debt/GDP | Fiscal sustainability | Annual | IMF |
| Fiscal Balance/GDP | Budget deficit/surplus | Annual | IMF |
| Foreign Exchange Reserves | External buffer | Monthly | Central banks |
| External Debt | Foreign currency debt | Quarterly | World Bank, BIS |

**Sovereign Credit Indicators:**

| Field | Description | Source |
|-------|-------------|--------|
| Sovereign Rating (S&P/Moody's/Fitch) | Country credit rating | Rating agencies |
| Sovereign CDS Spread | Market-implied credit risk | Bloomberg, Markit |
| Political Risk Score | Governance indicators | World Bank WGI |
| Corruption Index | Transparency International | TI |

### 4.3 Country-Level Climate Data

**Physical Risk Indicators:**

| Field | Description | Source |
|-------|-------------|--------|
| ND-GAIN Index | Notre Dame Climate Vulnerability | ND-GAIN |
| Climate Risk Index | Germanwatch indicator | Germanwatch |
| Exposure to Sea Level Rise | % of GDP/population in low-lying areas | World Bank |
| Agricultural Dependence | Agriculture % of GDP | World Bank |
| Water Stress Index | Water scarcity risk | WRI Aqueduct |
| Historical Disaster Losses | EM-DAT database | CRED |

**Transition Risk Indicators:**

| Field | Description | Source |
|-------|-------------|--------|
| Total GHG Emissions | Country-level emissions | UNFCCC, EDGAR |
| Emissions per Capita | Emissions intensity (population) | World Bank |
| Emissions per GDP | Carbon intensity of economy | World Bank |
| Fossil Fuel Dependence | % of energy from fossil fuels | IEA |
| Fossil Fuel Exports | % of exports from fossil fuels | UN Comtrade |
| Renewable Energy Share | % of energy from renewables | IEA, IRENA |
| NDC Target | Paris Agreement commitment | UNFCCC |
| Carbon Pricing Coverage | % of emissions under carbon pricing | World Bank |

---

## 5. Climate Scenario Data

### 5.1 NGFS Scenario Variables

**Core Macroeconomic Variables (by scenario, country, year):**

| Variable | Description | Unit | Source |
|----------|-------------|------|--------|
| GDP | Gross Domestic Product | Billion USD (2010) | NGFS |
| GDP Growth | Annual growth rate | % | NGFS |
| Population | Total population | Millions | NGFS |
| Inflation | Consumer price inflation | % | NGFS |
| Interest Rate (Policy) | Central bank policy rate | % | NGFS |
| Interest Rate (Long-term) | 10-year government bond yield | % | NGFS |
| Investment | Gross fixed capital formation | Billion USD | NGFS |
| Consumption | Private consumption | Billion USD | NGFS |
| Government Spending | Government consumption | Billion USD | NGFS |

**Energy and Emissions Variables:**

| Variable | Description | Unit | Source |
|----------|-------------|------|--------|
| Primary Energy | Total primary energy supply | EJ/year | NGFS |
| Final Energy | Energy delivered to end-users | EJ/year | NGFS |
| Electricity Generation | Total electricity output | TWh/year | NGFS |
| CO2 Emissions | Carbon dioxide emissions | GtCO2/year | NGFS |
| GHG Emissions | Total greenhouse gas emissions | GtCO2e/year | NGFS |
| Carbon Price | Shadow/explicit carbon price | USD/tCO2 | NGFS |
| Coal Consumption | Coal primary energy | EJ/year | NGFS |
| Oil Consumption | Oil primary energy | EJ/year | NGFS |
| Gas Consumption | Natural gas primary energy | EJ/year | NGFS |
| Renewable Share | Renewables in primary energy | % | NGFS |

**Sector-Level Variables:**

| Variable | Description | Sectors Covered | Source |
|----------|-------------|-----------------|--------|
| Sector Output | Production by sector | Energy, Industry, Transport, Buildings, Agriculture | NGFS |
| Sector Emissions | CO2 by sector | Same as above | NGFS |
| Sector Investment | Capital expenditure by sector | Same as above | NGFS |
| Technology Mix | Share of technologies | Power generation, Transport | NGFS |

### 5.2 NGFS Scenario Summary

| Scenario | Carbon Price 2030 | Carbon Price 2050 | Warming by 2100 | GDP Impact 2050 |
|----------|-------------------|-------------------|-----------------|-----------------|
| Net Zero 2050 | ~$130/tCO2 | ~$430/tCO2 | 1.5°C | -2% to -4% |
| Delayed Transition | ~$30/tCO2 | ~$700/tCO2 | 1.8°C | -3% to -5% |
| Below 2°C | ~$80/tCO2 | ~$250/tCO2 | 1.7°C | -1% to -3% |
| Current Policies | ~$10/tCO2 | ~$15/tCO2 | 3.0°C+ | -5% to -10% (physical) |
| NDCs | ~$25/tCO2 | ~$50/tCO2 | 2.5°C | -3% to -6% |
| Fragmented World | Variable | Variable | 2.3°C | -4% to -7% |

### 5.3 Accessing NGFS Data

**NGFS Scenario Explorer Portal:**
- URL: https://www.ngfs.net/ngfs-scenarios-portal/
- Format: CSV, Excel downloads
- Coverage: ~100 countries, 2020-2100
- Models: REMIND-MAgPIE, GCAM, MESSAGEix-GLOBIOM

**Key Data Files:**

| File | Content | Granularity |
|------|---------|-------------|
| NGFS_scenarios_v4_*.csv | Core scenario variables | Country × Year × Scenario |
| NGFS_finance_data_v4_*.csv | Financial variables | Country × Year × Scenario |
| NGFS_sector_data_v4_*.csv | Sector breakdown | Country × Sector × Year × Scenario |

---

## 6. Physical Risk Data

### 6.1 Hazard Data Requirements

**For Corporate Bonds (Asset-Level):**

| Hazard Type | Data Required | Resolution | Source |
|-------------|---------------|------------|--------|
| **Flood (Riverine)** | Return period flood depths | 30m-1km grid | WRI Aqueduct, JBA |
| **Flood (Coastal)** | Storm surge + sea level | Coastal zones | Climate Central, WRI |
| **Hurricane/Cyclone** | Wind speed, track probability | Regional | NOAA, IBTrACS |
| **Wildfire** | Fire weather index, burn probability | 1km grid | Copernicus, FIRMS |
| **Extreme Heat** | Days >35°C, wet-bulb temperature | Grid/station | CMIP6, Berkeley Earth |
| **Drought** | SPEI, soil moisture anomaly | Grid | SPEI Global, NASA |
| **Water Stress** | Baseline water stress, future projections | Basin level | WRI Aqueduct |

**For Sovereign Bonds (Country-Level):**

| Indicator | Description | Source |
|-----------|-------------|--------|
| Country Hazard Exposure | Composite physical risk score | NGFS, Moody's |
| GDP at Risk | % of GDP in hazard zones | Swiss Re, World Bank |
| Population Exposed | % of population in hazard zones | UNDRR |
| Agricultural Exposure | Crop production in risk areas | FAO, GAEZ |
| Infrastructure Exposure | Critical infrastructure in risk zones | World Bank |

### 6.2 Asset Geolocation Data

**Required for Corporate Physical Risk:**

| Field | Description | Source |
|-------|-------------|--------|
| Facility Latitude | Geographic coordinate | Corporate disclosure, Four Twenty Seven |
| Facility Longitude | Geographic coordinate | Corporate disclosure, Four Twenty Seven |
| Facility Type | Plant, warehouse, office, etc. | Corporate disclosure |
| Facility Value | Replacement cost or book value | Estimated from financials |
| Production Capacity | Output capacity (if applicable) | Corporate disclosure |
| Revenue Attribution | % of revenue from facility | Estimated |

**Data Challenge:** Asset-level geolocation is often the most difficult data to obtain. Alternatives include:
- Headquarters location (limited accuracy)
- Sector-country average exposure (less granular)
- Third-party datasets (Four Twenty Seven, Trucost, MSCI)

### 6.3 Damage Functions

**Translating Hazard to Financial Loss:**

| Hazard | Damage Function Form | Key Parameters |
|--------|---------------------|----------------|
| Flood | Depth-damage curve | % loss vs. flood depth |
| Wind | Vulnerability curve | % loss vs. wind speed |
| Heat | Productivity loss function | Labor productivity vs. temperature |
| Drought | Yield reduction function | Crop yield vs. water deficit |

**Example Flood Damage Function:**

```
Damage(depth) = 0                          if depth < 0.1m
              = 0.15 × depth               if 0.1m ≤ depth < 0.5m
              = 0.075 + 0.30 × (depth-0.5) if 0.5m ≤ depth < 1.0m
              = 0.225 + 0.50 × (depth-1.0) if 1.0m ≤ depth < 2.0m
              = 0.725 + 0.25 × (depth-2.0) if depth ≥ 2.0m
              = min(Damage, 1.0)
```

---

## 7. Transition Risk Data

### 7.1 Emissions Data

**Corporate Emissions (Scope 1, 2, 3):**

| Scope | Definition | Data Availability | Source |
|-------|------------|-------------------|--------|
| **Scope 1** | Direct emissions from owned sources | Good (large caps) | CDP, Company reports |
| **Scope 2** | Indirect from purchased energy | Good (large caps) | CDP, Company reports |
| **Scope 3** | All other indirect (value chain) | Limited, often estimated | CDP, Scope 3 estimators |

**Key Emissions Metrics:**

| Metric | Formula | Use |
|--------|---------|-----|
| Absolute Emissions | Scope 1 + 2 (+ 3) in tCO2e | Total carbon footprint |
| Carbon Intensity (Revenue) | Emissions / Revenue | Sector comparison |
| Carbon Intensity (EVIC) | Emissions / Enterprise Value | Portfolio weighting |
| Weighted Average Carbon Intensity | Σ(weight_i × intensity_i) | Portfolio metric |

**Data Sources for Corporate Emissions:**

| Source | Coverage | Cost | Data Quality |
|--------|----------|------|--------------|
| CDP | ~10,000 companies | Paid | Self-reported |
| Trucost (S&P) | ~15,000 companies | Paid | Modeled + reported |
| MSCI ESG | ~8,000 companies | Paid | Modeled + reported |
| ISS ESG | ~10,000 companies | Paid | Modeled + reported |
| Bloomberg | ~10,000 companies | Paid | Aggregated |
| Company Reports | Variable | Free | Self-reported |

### 7.2 Carbon Pricing Exposure

**Calculating Carbon Cost Impact:**

```
Annual Carbon Cost = Emissions × Carbon Price × (1 - Allowance_Coverage)

Carbon Cost as % of EBITDA = Annual Carbon Cost / EBITDA

Implied Margin Impact = Carbon Cost × (1 - Pass_Through_Rate) / Revenue
```

**Pass-Through Assumptions by Sector:**

| Sector | Estimated Pass-Through Rate | Rationale |
|--------|----------------------------|-----------|
| Utilities (Regulated) | 80-100% | Rate base recovery |
| Utilities (Merchant) | 50-80% | Competitive market |
| Oil & Gas (Upstream) | 0-20% | Price taker |
| Oil & Gas (Downstream) | 40-60% | Some pricing power |
| Materials (Cement, Steel) | 30-50% | Trade exposure limits |
| Airlines | 20-40% | Competitive, elastic demand |
| Autos | 50-70% | Can pass to consumers |

### 7.3 Stranded Asset Exposure

**For Fossil Fuel Companies:**

| Metric | Description | Source |
|--------|-------------|--------|
| Proved Reserves | Oil, gas, coal reserves | Company filings, Rystad |
| Reserve Replacement Ratio | Sustainability of production | Company filings |
| CapEx in Fossil Fuels | Investment in new fossil capacity | Company filings |
| Unburnable Carbon | Reserves inconsistent with 2°C | Carbon Tracker |
| Asset Impairment Risk | Book value at risk of write-down | Estimated |

**Stranded Asset Calculation:**

```
Stranded Asset Value = Proved_Reserves × Price × Stranding_Probability(scenario)

Where Stranding_Probability depends on:
- Carbon budget remaining under scenario
- Marginal cost of extraction
- Geographic/regulatory jurisdiction
```

### 7.4 Technology Exposure

**Green Revenue/CapEx Indicators:**

| Metric | Description | Source |
|--------|-------------|--------|
| Green Revenue Share | % revenue from green activities | MSCI, Trucost |
| Green CapEx Share | % investment in green technologies | Company filings |
| EU Taxonomy Alignment | % revenue/CapEx aligned with EU Taxonomy | EU Taxonomy Compass |
| Low-Carbon Patents | Patent portfolio in clean tech | PATSTAT, EPO |

---

## 8. Data Sources and Providers

### 8.1 Free/Open Data Sources

| Source | Data Type | URL |
|--------|-----------|-----|
| **NGFS Scenarios** | Climate scenarios | ngfs.net/ngfs-scenarios-portal |
| **EDGAR** | Country emissions | edgar.jrc.ec.europa.eu |
| **CDP Open Data** | Company emissions (limited) | cdp.net |
| **WRI Aqueduct** | Water risk | wri.org/aqueduct |
| **ND-GAIN** | Country climate vulnerability | gain.nd.edu |
| **World Bank WDI** | Country economic data | data.worldbank.org |
| **IMF Data** | Macro-financial data | imf.org/en/Data |
| **GLEIF** | Legal Entity Identifiers | gleif.org |
| **EM-DAT** | Disaster database | emdat.be |
| **Climate Central** | Sea level rise maps | climatecentral.org |
| **CMIP6** | Climate model outputs | esgf-node.llnl.gov |

### 8.2 Commercial Data Providers

| Provider | Key Datasets | Strengths |
|----------|--------------|-----------|
| **Bloomberg** | Market data, ESG, emissions | Comprehensive terminal integration |
| **Refinitiv** | Market data, ESG | Good API access |
| **MSCI ESG** | ESG ratings, climate metrics | Methodology transparency |
| **S&P Trucost** | Carbon data, physical risk | Scope 3 coverage |
| **ISS ESG** | ESG ratings, climate | Physical risk detail |
| **Moody's ESG** | Credit + climate | Integration with credit |
| **Sustainalytics** | ESG ratings, controversies | Company engagement |
| **Four Twenty Seven** | Physical risk, asset-level | Geospatial granularity |
| **Jupiter Intelligence** | Physical risk modeling | Scenario flexibility |
| **Carbon Tracker** | Stranded assets | Oil & gas focus |

### 8.3 Central Bank and Regulatory Sources

| Source | Data Type | Coverage |
|--------|-----------|----------|
| **ECB Statistical Data Warehouse** | Euro area financial data | sdw.ecb.europa.eu |
| **Federal Reserve FRED** | US economic data | fred.stlouisfed.org |
| **BIS Statistics** | International banking | bis.org/statistics |
| **ESRB Risk Dashboard** | EU systemic risk | esrb.europa.eu |

---

## 9. Data Quality and Gap Analysis

### 9.1 Common Data Challenges

| Challenge | Impact | Mitigation |
|-----------|--------|------------|
| **Scope 3 data gaps** | Underestimate transition risk | Use sector averages, EEIO models |
| **SME coverage** | No data for private/small issuers | Sector proxies, estimated models |
| **Asset geolocation** | Cannot assess physical risk accurately | HQ location, sector-country averages |
| **Historical climate losses** | Cannot calibrate damage functions | Use engineering/scientific estimates |
| **Forward-looking data** | Scenarios are uncertain | Multi-scenario analysis |
| **Data timeliness** | Emissions data 1-2 years lag | Nowcasting models |

### 9.2 Data Quality Indicators

| Quality Dimension | Assessment Criteria |
|-------------------|---------------------|
| **Completeness** | % of portfolio covered by data |
| **Accuracy** | Reported vs. estimated emissions |
| **Timeliness** | Data vintage (years old) |
| **Consistency** | Same methodology across issuers |
| **Granularity** | Asset-level vs. company vs. sector |
| **Auditability** | Third-party verification |

### 9.3 Coverage Statistics (Typical)

| Data Type | Large Cap Coverage | Mid Cap Coverage | Small Cap/Private |
|-----------|-------------------|------------------|-------------------|
| Scope 1+2 Emissions | 80-90% | 50-70% | 10-30% |
| Scope 3 Emissions | 50-60% | 20-40% | 5-15% |
| Asset Geolocation | 30-50% | 10-20% | <5% |
| Physical Risk Scores | 70-80% | 40-60% | 20-40% |
| Green Revenue | 60-70% | 30-50% | 10-20% |

---

## 10. Minimum Viable Dataset

### 10.1 Corporate Bond Portfolio - Basic Implementation

**Tier 1: Essential Data (Minimum for Any Analysis)**

| Data Element | Granularity | Source |
|--------------|-------------|--------|
| Bond holdings (ISIN, notional, maturity) | Bond-level | Internal |
| Issuer identification (LEI, name) | Issuer-level | GLEIF |
| Sector classification (GICS) | Issuer-level | Bloomberg |
| Country of domicile | Issuer-level | Bloomberg |
| Credit rating or spread | Issuer-level | Rating agencies, Bloomberg |
| Scope 1+2 emissions | Issuer-level | CDP, Trucost |
| Revenue | Issuer-level | Financial statements |
| NGFS scenario data | Country × Sector × Year | NGFS |

**Tier 2: Enhanced Data (For More Sophisticated Analysis)**

| Data Element | Granularity | Source |
|--------------|-------------|--------|
| Scope 3 emissions | Issuer-level | Trucost, CDP |
| Equity price & volatility | Issuer-level | Bloomberg (for Merton) |
| Balance sheet data | Issuer-level | Financial statements |
| CDS spreads | Issuer-level | Markit |
| Asset locations | Facility-level | Four Twenty Seven |
| Physical risk scores | Issuer-level | MSCI, Sustainalytics |
| Green revenue share | Issuer-level | MSCI, Trucost |

### 10.2 Sovereign Bond Portfolio - Basic Implementation

**Tier 1: Essential Data**

| Data Element | Granularity | Source |
|--------------|-------------|--------|
| Bond holdings (ISIN, notional, maturity) | Bond-level | Internal |
| Country identification | Country-level | ISO codes |
| Sovereign rating | Country-level | Rating agencies |
| GDP, GDP growth | Country-level | IMF |
| Country emissions (total, per capita) | Country-level | EDGAR, UNFCCC |
| NGFS scenario data | Country × Year | NGFS |
| ND-GAIN vulnerability index | Country-level | ND-GAIN |

**Tier 2: Enhanced Data**

| Data Element | Granularity | Source |
|--------------|-------------|--------|
| Sovereign CDS spreads | Country-level | Markit |
| Fossil fuel export dependence | Country-level | UN Comtrade |
| Energy mix | Country-level | IEA |
| NDC targets | Country-level | UNFCCC |
| Physical risk sub-indicators | Country-level | Various |

### 10.3 Practical Data Acquisition Roadmap

```
Phase 1: Foundation (Months 1-3)
├── Acquire portfolio holdings data
├── Map to LEI and sector classifications
├── Source basic emissions data (Scope 1+2)
├── Download NGFS scenarios
└── Calculate basic carbon intensity metrics

Phase 2: Enhancement (Months 4-6)
├── Acquire Scope 3 data where available
├── Source physical risk scores
├── Implement sector-level damage functions
├── Build scenario-conditional spread models
└── Calculate portfolio climate VaR

Phase 3: Advanced (Months 7-12)
├── Acquire asset-level geolocation data
├── Implement Merton model with climate adjustment
├── Build proprietary physical risk models
├── Integrate stranded asset analysis
└── Develop forward-looking emissions trajectories
```

---

## Appendix A: Key Data Fields Summary Table

### Corporate Bond Data Requirements

| Category | Field | Required | Source |
|----------|-------|----------|--------|
| **Identification** | ISIN | Yes | Bloomberg |
| | Issuer LEI | Yes | GLEIF |
| | GICS Sector | Yes | Bloomberg |
| | Country | Yes | Bloomberg |
| **Market** | Price | Yes | Bloomberg |
| | Yield/Spread | Yes | Bloomberg |
| | Duration | Yes | Calculated |
| **Credit** | Rating | Yes | S&P/Moody's/Fitch |
| | CDS Spread | Recommended | Markit |
| **Financial** | Revenue | Yes | Filings |
| | EBITDA | Recommended | Filings |
| | Total Debt | Recommended | Filings |
| | Equity Market Cap | Recommended | Bloomberg |
| **Emissions** | Scope 1 | Yes | CDP/Trucost |
| | Scope 2 | Yes | CDP/Trucost |
| | Scope 3 | Recommended | CDP/Trucost |
| **Physical Risk** | HQ Location | Yes | Filings |
| | Asset Locations | Recommended | Four Twenty Seven |
| | Physical Risk Score | Recommended | MSCI/Sustainalytics |
| **Transition Risk** | Carbon Intensity | Yes | Calculated |
| | Green Revenue % | Recommended | MSCI/Trucost |

### Sovereign Bond Data Requirements

| Category | Field | Required | Source |
|----------|-------|----------|--------|
| **Identification** | ISIN | Yes | Bloomberg |
| | Country ISO | Yes | ISO |
| **Market** | Price | Yes | Bloomberg |
| | Yield | Yes | Bloomberg |
| | Spread to benchmark | Yes | Calculated |
| **Credit** | Sovereign Rating | Yes | S&P/Moody's/Fitch |
| | Sovereign CDS | Recommended | Markit |
| **Macro** | GDP | Yes | IMF |
| | GDP Growth | Yes | IMF |
| | Debt/GDP | Recommended | IMF |
| **Emissions** | Total GHG | Yes | EDGAR |
| | Emissions/GDP | Yes | Calculated |
| | Emissions/Capita | Recommended | Calculated |
| **Physical Risk** | ND-GAIN Index | Yes | ND-GAIN |
| | Climate Risk Index | Recommended | Germanwatch |
| **Transition Risk** | Fossil Fuel Dependence | Yes | IEA/UN |
| | NDC Target | Recommended | UNFCCC |
| | Carbon Price Coverage | Recommended | World Bank |

---

*Document prepared: January 2026*
*Focus: Data requirements for climate risk assessment of debt instruments*
