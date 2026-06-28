# Climate-Integrated Investment and Trading Analysis
## A Comprehensive Guide with Mathematical Formulations and Data Requirements

**Author Note:** This document integrates climate-related financial risks into traditional technical and fundamental analysis frameworks, based on peer-reviewed academic research and institutional methodologies from the Basel Committee, NGFS, and leading financial institutions.

---

## Table of Contents

1. [Traditional Technical Analysis](#1-traditional-technical-analysis)
2. [Fundamental Analysis](#2-fundamental-analysis)
3. [Risk Management](#3-risk-management)
4. [Climate Risk Integration](#4-climate-risk-integration)
5. [Integrated Framework](#5-integrated-framework)
6. [Data Sources](#6-data-sources)

---

## 1. Traditional Technical Analysis

### 1.1 Moving Averages (MA)

**Purpose:** Smooth price data to identify trends and generate trading signals.

**Mathematical Formulation:**

**Simple Moving Average (SMA):**
```
SMA_n = (P_1 + P_2 + ... + P_n) / n
```
Where:
- P_i = Price at period i
- n = Number of periods

**Exponential Moving Average (EMA):**
```
EMA_t = α × P_t + (1 - α) × EMA_(t-1)
Where: α = 2 / (n + 1)
```

**Data Required:**
- Historical closing prices (daily, weekly, monthly)
- Source: Yahoo Finance (`yfinance` Python library), Google Finance
- Field: `Close` price
- Minimum periods: 200 days for long-term analysis

**Trading Signals:**
- **Golden Cross:** 50-day SMA crosses above 200-day SMA → Bullish
- **Death Cross:** 50-day SMA crosses below 200-day SMA → Bearish

---

### 1.2 Relative Strength Index (RSI)

**Purpose:** Momentum oscillator measuring overbought/oversold conditions.

**Mathematical Formulation:**
```
RSI = 100 - [100 / (1 + RS)]

Where:
RS = Average Gain / Average Loss (typically over 14 periods)

Average Gain = Sum of gains over n periods / n
Average Loss = Sum of losses over n periods / n
```

**Data Required:**
- Daily closing prices
- Source: Yahoo Finance, Google Finance
- Minimum periods: 14 days (standard), but need 14+ additional days for initial calculation

**Interpretation:**
- RSI > 70: Overbought (potential sell signal)
- RSI < 30: Oversold (potential buy signal)
- Divergence: Price makes new high while RSI doesn't → Bearish divergence

---

### 1.3 MACD (Moving Average Convergence Divergence)

**Mathematical Formulation:**
```
MACD Line = EMA_12 - EMA_26
Signal Line = EMA_9 of MACD Line
Histogram = MACD Line - Signal Line
```

**Data Required:**
- Daily closing prices
- Source: Yahoo Finance, Google Finance
- Minimum periods: 26+ days

**Trading Signals:**
- MACD crosses above Signal Line → Bullish
- MACD crosses below Signal Line → Bearish
- Histogram expansion → Increasing momentum

---

### 1.4 Bollinger Bands

**Mathematical Formulation:**
```
Middle Band = SMA_20
Upper Band = SMA_20 + (2 × σ)
Lower Band = SMA_20 - (2 × σ)

Where: σ = Standard Deviation of price over 20 periods
σ = √[Σ(P_i - SMA_20)² / 20]
```

**Data Required:**
- Daily closing prices
- Source: Yahoo Finance, Google Finance
- Minimum periods: 20 days

**Interpretation:**
- Price touching upper band → Potentially overbought
- Price touching lower band → Potentially oversold
- Band squeeze (low volatility) → Often precedes significant move

---

### 1.5 Volume Analysis

**Mathematical Formulation:**
```
Volume-Weighted Average Price (VWAP):
VWAP = Σ(Price_i × Volume_i) / Σ(Volume_i)

On-Balance Volume (OBV):
If Close_t > Close_(t-1): OBV_t = OBV_(t-1) + Volume_t
If Close_t < Close_(t-1): OBV_t = OBV_(t-1) - Volume_t
If Close_t = Close_(t-1): OBV_t = OBV_(t-1)
```

**Data Required:**
- Daily closing prices and volume
- Source: Yahoo Finance (`Volume` field), Google Finance
- Field: `Close`, `Volume`

**Trading Signals:**
- Rising price + rising volume → Strong bullish confirmation
- Rising price + falling volume → Weak move, may reverse

---

## 2. Fundamental Analysis

### 2.1 Valuation Metrics

**Purpose:** Assess intrinsic value relative to market price.

**2.1.1 Price-to-Earnings Ratio (P/E)**

**Mathematical Formulation:**
```
P/E = Market Price per Share / Earnings per Share

Where:
EPS = (Net Income - Preferred Dividends) / Weighted Average Shares Outstanding
```

**Data Required:**
- Market price: Yahoo Finance, Google Finance (`Close` price)
- Net Income: Company financial statements (10-K, 10-Q)
- Shares outstanding: Financial statements or Yahoo Finance (`sharesOutstanding`)
- Source: SEC EDGAR (for US companies), company investor relations

**Interpretation:**
- High P/E (>20): Growth expectations or overvaluation
- Low P/E (<15): Value opportunity or fundamental problems
- Compare to sector average and historical P/E

---

**2.1.2 Price-to-Book Ratio (P/B)**

**Mathematical Formulation:**
```
P/B = Market Price per Share / Book Value per Share

Where:
Book Value per Share = (Total Assets - Total Liabilities - Preferred Stock) / Shares Outstanding
```

**Data Required:**
- Market price: Yahoo Finance
- Total Assets, Total Liabilities: Balance sheet (10-K, 10-Q)
- Source: SEC EDGAR, Yahoo Finance (`bookValue`)

---

**2.1.3 Free Cash Flow (FCF)**

**Mathematical Formulation:**
```
FCF = Operating Cash Flow - Capital Expenditures

Operating Cash Flow = Net Income + Non-Cash Expenses + Changes in Working Capital
```

**Data Required:**
- Cash flow statement (10-K, 10-Q)
- Operating cash flow: Direct from statement
- CapEx: Cash flow statement under investing activities
- Source: SEC EDGAR, Yahoo Finance

**Why Important:** FCF represents actual cash available to shareholders and is harder to manipulate than earnings.

---

**2.1.4 Return on Equity (ROE)**

**Mathematical Formulation:**
```
ROE = Net Income / Shareholders' Equity

DuPont Decomposition:
ROE = (Net Income / Sales) × (Sales / Assets) × (Assets / Equity)
    = Profit Margin × Asset Turnover × Equity Multiplier
```

**Data Required:**
- Net Income: Income statement
- Shareholders' Equity: Balance sheet
- Source: Company financial statements, Yahoo Finance

---

### 2.2 Credit Analysis (for Bonds)

**2.2.1 Debt-to-Equity Ratio**

**Mathematical Formulation:**
```
D/E = Total Debt / Total Shareholders' Equity

Where:
Total Debt = Short-term Debt + Long-term Debt
```

**Data Required:**
- Balance sheet data
- Source: SEC EDGAR for US companies, company reports

---

**2.2.2 Interest Coverage Ratio**

**Mathematical Formulation:**
```
Interest Coverage = EBIT / Interest Expense

Where:
EBIT = Earnings Before Interest and Taxes
```

**Data Required:**
- Income statement
- EBIT: Operating income
- Interest expense: Financial costs section
- Source: Company financial statements

**Interpretation:**
- Ratio > 2.5: Generally healthy
- Ratio < 1.5: Potential debt servicing issues

---

**2.2.3 Credit Spread**

**Mathematical Formulation:**
```
Credit Spread = Yield_corporate - Yield_risk-free

Where:
Yield = Coupon Rate / Current Bond Price (simplified)
```

**Data Required:**
- Corporate bond yield: Bloomberg, FRED (for indices)
- Treasury yield: US Treasury website, Yahoo Finance (^TNX for 10-year)
- Source: FRED (Federal Reserve Economic Data) for aggregated data

---

### 2.3 Macroeconomic Indicators

**2.3.1 GDP Growth Rate**

**Mathematical Formulation:**
```
GDP Growth Rate = [(GDP_t - GDP_(t-1)) / GDP_(t-1)] × 100
```

**Data Required:**
- Source: FRED (Federal Reserve Economic Data), World Bank, IMF
- Frequency: Quarterly
- Variable: GDPC1 (Real GDP for US)

---

**2.3.2 Inflation Rate (CPI)**

**Mathematical Formulation:**
```
Inflation Rate = [(CPI_t - CPI_(t-1)) / CPI_(t-1)] × 100

Where:
CPI = Consumer Price Index
```

**Data Required:**
- Source: FRED, Bureau of Labor Statistics
- Variable: CPIAUCSL (US CPI)
- Frequency: Monthly

---

## 3. Risk Management

### 3.1 Value at Risk (VaR)

**Purpose:** Estimate maximum potential loss over a specific time period at a given confidence level.

**3.1.1 Historical VaR**

**Mathematical Formulation:**
```
VaR_α = -Percentile(Returns, α)

Where:
α = Confidence level (e.g., 0.05 for 95% confidence)
Returns = Historical return distribution
```

**Example:** If 95% 1-day VaR = $1 million, there is 95% confidence that losses won't exceed $1 million in one day.

**Data Required:**
- Historical daily returns (minimum 250 days recommended)
- Source: Yahoo Finance, Google Finance
- Calculate: Returns = (P_t - P_(t-1)) / P_(t-1)

---

**3.1.2 Parametric VaR (Variance-Covariance Method)**

**Mathematical Formulation:**
```
VaR_α = -μ × Δt + z_α × σ × √Δt

Where:
μ = Expected return
σ = Standard deviation of returns
z_α = Z-score for confidence level α (e.g., 1.65 for 95%, 2.33 for 99%)
Δt = Time horizon (e.g., 1 day)
```

**Data Required:**
- Historical returns to calculate μ and σ
- Source: Yahoo Finance, Google Finance
- Minimum: 250 trading days

**Assumptions:** Returns are normally distributed (often violated in practice).

---

### 3.2 Expected Shortfall (Conditional VaR)

**Mathematical Formulation:**
```
ES_α = E[Loss | Loss > VaR_α]

ES_α = -E[Return | Return < -VaR_α]
```

**Purpose:** Average loss beyond the VaR threshold, provides more information about tail risk.

**Data Required:**
- Same as VaR calculation
- Source: Yahoo Finance historical data

---

### 3.3 Position Sizing

**3.3.1 Fixed Percentage Risk Method**

**Mathematical Formulation:**
```
Position Size = (Account Equity × Risk Percentage) / (Entry Price - Stop Loss Price)

Risk Percentage typically = 1-2% of total account
```

**Example:**
- Account: $100,000
- Risk per trade: 1% = $1,000
- Entry: $50
- Stop loss: $45
- Position size = $1,000 / ($50 - $45) = 200 shares = $10,000 position

**Data Required:**
- Current account value
- Current price: Yahoo Finance
- Stop loss level: Determined by technical analysis or volatility

---

**3.3.2 Kelly Criterion**

**Mathematical Formulation:**
```
f* = (p × b - q) / b

Where:
f* = Fraction of capital to bet
p = Probability of winning
q = Probability of losing = 1 - p
b = Ratio of win to loss (average win / average loss)
```

**Data Required:**
- Historical win rate from backtesting
- Historical average win and loss sizes
- Source: Trading history, backtesting results

**Note:** In practice, use fraction of Kelly (e.g., 0.25 × f*) to reduce risk.

---

### 3.4 Portfolio Risk Metrics

**3.4.1 Portfolio Standard Deviation**

**Mathematical Formulation:**
```
σ_p = √[Σ_i Σ_j w_i × w_j × σ_i × σ_j × ρ_ij]

Where:
w_i, w_j = Weights of assets i and j
σ_i, σ_j = Standard deviations of assets i and j
ρ_ij = Correlation coefficient between assets i and j
```

**Data Required:**
- Historical returns for all assets in portfolio
- Source: Yahoo Finance for multiple tickers
- Calculate correlation matrix using historical data

---

**3.4.2 Sharpe Ratio**

**Mathematical Formulation:**
```
Sharpe Ratio = (R_p - R_f) / σ_p

Where:
R_p = Portfolio return
R_f = Risk-free rate (e.g., 3-month T-bill)
σ_p = Portfolio standard deviation
```

**Data Required:**
- Portfolio returns: Calculate from holdings
- Risk-free rate: FRED (variable: DGS3MO for 3-month Treasury)
- Portfolio volatility: From historical returns

**Interpretation:** Higher Sharpe ratio = Better risk-adjusted returns. Sharpe > 1 is good, > 2 is excellent.

---

**3.4.3 Maximum Drawdown**

**Mathematical Formulation:**
```
MDD = (Trough Value - Peak Value) / Peak Value

Where:
Peak Value = Maximum cumulative portfolio value before decline
Trough Value = Minimum cumulative portfolio value during decline
```

**Data Required:**
- Daily portfolio values
- Source: Calculate from position holdings and prices

---

### 3.5 Beta and Systematic Risk

**Mathematical Formulation:**
```
β = Cov(R_i, R_m) / Var(R_m)

Where:
R_i = Stock returns
R_m = Market returns
Cov = Covariance
Var = Variance

In regression form:
R_i = α + β × R_m + ε
```

**Data Required:**
- Stock returns: Yahoo Finance
- Market returns: S&P 500 (^GSPC), relevant market index
- Minimum: 3-5 years of monthly or daily returns
- Source: Yahoo Finance

**Interpretation:**
- β = 1: Moves with market
- β > 1: More volatile than market
- β < 1: Less volatile than market
- β < 0: Moves opposite to market (rare)

---

## 4. Climate Risk Integration

### 4.1 Climate Risk Categories

According to <cite>Campiglio et al. (2023, Journal of Economic Surveys)</cite> and the <cite>Basel Committee on Banking Supervision (2021)</cite>, climate-related financial risks are categorized into:

**Physical Risks:**
- **Acute:** Event-driven (hurricanes, floods, wildfires)
- **Chronic:** Longer-term shifts (temperature changes, sea level rise, precipitation patterns)

**Transition Risks:**
- **Policy risk:** Carbon pricing, regulations, emission standards
- **Technology risk:** Disruptive clean technologies, stranded assets
- **Market risk:** Changing consumer preferences
- **Reputation risk:** Stakeholder concerns, divestment movements

---

### 4.2 Climate Value-at-Risk (Climate VaR)

**Source:** <cite>MSCI Climate VaR Methodology (2024)</cite>, <cite>UNEP FI TCFD Pilot (2019)</cite>

**Purpose:** Quantify potential financial impact of climate change on asset values under different climate scenarios.

**Mathematical Formulation:**

```
Climate VaR = Present Value of Climate Costs / Current Market Value

Climate VaR_enterprise = PV(Climate Costs) / Enterprise Value
Climate VaR_equity = PV(Equity Climate Costs) / Market Cap
Climate VaR_debt = PV(Debt Climate Costs) / Market Value of Debt
```

**Components:**

**For Physical Risk:**
```
Expected Cost = Hazard × Exposure × Vulnerability

Where:
Hazard = Probability and intensity of climate event
Exposure = Value of assets in affected location
Vulnerability = Damage function (% loss given event)
```

**For Transition Risk:**
```
Transition Cost = Σ(Carbon Price_t × Emissions_t × Discount Factor_t)

Where t ranges over scenario timeline (e.g., 2025-2050)
```

**Data Required:**

**Physical Risk:**
- Asset locations (latitude/longitude): Company disclosures, 10-K filings
- Climate hazard data: 
  - Source: NGFS Climate Scenarios Portal, IPCC data, CLIMADA
  - Variables: Temperature, precipitation, sea level, flood maps
- Asset values: Balance sheet (Property, Plant & Equipment)
- Damage functions: Academic literature, insurance industry data

**Transition Risk:**
- Scope 1, 2, 3 emissions: 
  - Source: CDP (Carbon Disclosure Project), company sustainability reports
  - Bloomberg ESG data, Refinitiv ESG data
- Carbon price scenarios:
  - Source: NGFS scenarios, IEA World Energy Outlook
  - Variable: Carbon price paths ($/tCO2) for different scenarios
- Revenue by product/geography: 10-K filings, annual reports
- WACC (Weighted Average Cost of Capital): Calculate from financial data

**NGFS Climate Scenarios:**
- **Net Zero 2050:** Ambitious climate action, 1.5°C warming
- **Delayed Transition:** Late policy action, higher transition risk
- **Current Policies:** ~3°C warming, high physical risk
- **Divergent Net Zero:** Uncoordinated transition
- Source: https://www.ngfs.net/ngfs-scenarios-portal/

**Example Calculation (Simplified):**
```
Company X:
- Current market cap: $10 billion
- Annual Scope 1+2 emissions: 5 million tCO2
- Carbon price in 2030 (Delayed Transition scenario): $150/tCO2
- Carbon price in 2040: $250/tCO2

Transition cost (2030) = 5M tCO2 × $150 = $750M annually
PV of transition costs over 15 years (using 7% discount rate):
≈ $6.8 billion

Climate VaR = $6.8B / $10B = 68%

Interpretation: Under delayed transition, company could lose 68% of value
```

---

### 4.3 Carbon Beta

**Source:** <cite>Huij et al. (2023, SSRN)</cite>, <cite>Robeco Climate Beta Methodology (2024)</cite>, <cite>Görgen et al. (2024, ScienceDirect)</cite>

**Purpose:** Market-based measure of a stock's sensitivity to climate transition risk.

**Mathematical Formulation:**

**Step 1: Construct Climate Risk Factor**
```
Climate Risk Factor_t = R_brown,t - R_green,t

Where:
R_brown,t = Return of high-emission portfolio at time t
R_green,t = Return of low-emission portfolio at time t
```

**Step 2: Estimate Climate Beta via Regression**
```
R_i,t = α_i + β_climate,i × CRF_t + β_market,i × R_m,t + ε_i,t

Where:
R_i,t = Stock i's return at time t
CRF_t = Climate Risk Factor at time t
R_m,t = Market return at time t
β_climate,i = Climate beta (sensitivity to climate risk factor)
```

**Alternative: Fama-French + Climate Factor:**
```
R_i,t - R_f,t = α + β_MKT(R_m,t - R_f,t) + β_SMB×SMB_t + β_HML×HML_t + β_climate×CRF_t + ε_t
```

**Data Required:**

**To Construct Climate Risk Factor:**
1. Emissions data for universe of stocks:
   - Source: CDP, Bloomberg ESG, Refinitiv, S&P Trucost
   - Variables: Scope 1, 2, 3 emissions, carbon intensity (tCO2/revenue)
2. Stock returns:
   - Source: Yahoo Finance, CRSP
   - Frequency: Daily or monthly
3. Green patent data (optional enhancement):
   - Source: USPTO (US Patent Office), OECD patent database
   - Variable: Climate-related patent filings

**Portfolio Construction:**
- Rank stocks by carbon intensity
- Brown portfolio = Top 30% highest emitters
- Green portfolio = Bottom 30% lowest emitters
- Equal-weight or value-weight within portfolios

**To Estimate Climate Beta:**
- Stock returns: Yahoo Finance (minimum 3 years monthly or 1 year daily)
- Climate Risk Factor returns: Calculated as above
- Market returns: S&P 500 or relevant index

**Interpretation:**
- **β_climate > 0:** Stock underperforms when climate concerns rise (climate laggard)
- **β_climate < 0:** Stock outperforms when climate concerns rise (climate leader)
- **β_climate ≈ 0:** Stock neutral to climate risk

**Academic Finding:** <cite>Huij et al. (2023)</cite> document a small but significant carbon risk premium, with high carbon beta stocks earning lower returns during climate risk realizations.

---

### 4.4 Stranded Asset Risk

**Source:** <cite>Semieniuk et al. (2022, Nature Climate Change)</cite>, <cite>Caldecott (2017, Journal of Sustainable Finance & Investment)</cite>

**Definition:** Assets that suffer premature write-downs, devaluations, or conversion to liabilities due to climate-related factors.

**Mathematical Formulation:**

**Stranded Asset Value:**
```
Stranded Value = Book Value - Recoverable Value

Where:
Recoverable Value = min(Fair Value - Costs to Sell, Value in Use)

Value in Use = Σ[CF_t / (1 + r)^t] for t = 1 to n

Where:
CF_t = Expected cash flows in year t (adjusted for climate policy)
r = Discount rate
n = Remaining useful life (may be shortened by climate policy)
```

**Carbon Budget Constraint:**
```
If: Σ Emissions from all reserves > Carbon Budget
Then: Unburnable Carbon = Σ Emissions - Carbon Budget

% Reserves Stranded = Unburnable Carbon / Total Reserve Emissions
```

**Data Required:**

**For Fossil Fuel Companies:**
- Proven reserves: 10-K filings, company reports (barrels oil, cubic feet gas, tons coal)
- Production costs: Company disclosures, IEA cost curves
- Carbon content of reserves:
  - Coal: ~2.4 tCO2/ton
  - Oil: ~0.43 tCO2/barrel
  - Natural gas: ~0.05 tCO2/cubic meter
- Carbon budget scenarios:
  - Source: IPCC reports, NGFS scenarios
  - 2°C budget: ~900 GtCO2 remaining (IPCC AR6)
- Asset book values: Balance sheet (PP&E)

**For Other Sectors:**
- Asset locations near climate hazard zones:
  - Source: Company property disclosures, GIS data
  - Hazard maps: FEMA flood zones, NOAA storm surge, wildfire risk maps
- Asset useful life: Depreciation schedules, industry standards
- Regulatory risk: Upcoming emission standards, building codes

**Academic Finding:** <cite>Semieniuk et al. (2022)</cite> estimate >$1 trillion in potential stranded oil and gas assets globally under credible climate policy scenarios, with most ownership traced to OECD investors through pension funds.

---

### 4.5 Climate Stress Testing (CRISK)

**Source:** <cite>Jung, Engle & Berner (2021, NYU Volatility Institute)</cite>, <cite>Acharya, Engle & Berner (2023, Federal Reserve)</cite>

**Purpose:** Assess expected capital shortfall of financial institutions under climate stress scenarios.

**Mathematical Formulation:**

```
CRISK_i,t = k × DEBT_i,t - (1 - k) × EQUITY_i,t × (1 - LRMES_i,t)

Where:
k = Prudential capital ratio (e.g., 8% under Basel III)
DEBT_i,t = Book value of debt for institution i
EQUITY_i,t = Market value of equity for institution i
LRMES_i,t = Long-Run Marginal Expected Shortfall
```

**LRMES Calculation:**
```
LRMES_i,t = E_t[-R_i | Climate Crisis]

Estimated via:
LRMES_i,t = 1 - exp(-18 × MES_i,t)

Where:
MES_i,t = E[-R_i,t | R_climate,t < 5th percentile]
```

**Dynamic Climate Beta (for LRMES):**
```
R_i,t = β_market,i,t × R_market,t + β_climate,i,t × R_stranded,t + ε_i,t

Where betas are time-varying via DCC-GARCH model
```

**Data Required:**

**For Financial Institutions:**
- Market capitalization: Yahoo Finance
- Book value of debt: Balance sheet (Total Liabilities - Equity)
- Stock returns: Yahoo Finance (daily, 3+ years)
- Source: Bloomberg, CRSP for higher quality data

**Climate Risk Factor:**
- Stranded asset portfolio returns: Construct from high-carbon stocks
- Or use existing indices:
  - S&P 500 Energy Select Sector (XLE)
  - MSCI Coal Index
- Source: Yahoo Finance, Bloomberg

**Market Returns:**
- S&P 500 or relevant market index
- Source: Yahoo Finance (^GSPC)

**Interpretation:**
- CRISK > 0: Expected capital shortfall in climate crisis
- CRISK < 0: Capital surplus
- Aggregate CRISK across institutions = Systemic climate risk

**Academic Finding:** <cite>Jung et al. (2021)</cite> find that major banks' CRISK increased substantially during climate policy events and extreme weather, with Japanese and European banks showing highest exposure.

---

### 4.6 Climate-Adjusted Credit Risk

**Source:** <cite>Klusak et al. (2023, Management Science)</cite>, <cite>Capasso et al. (2025, Journal of Banking & Finance)</cite>

**Purpose:** Incorporate climate risk into probability of default (PD) and credit spreads.

**Mathematical Formulation:**

**Climate-Adjusted PD:**
```
PD_climate = PD_baseline × (1 + Climate Impact Factor)

Where:
Climate Impact Factor = f(Temperature Increase, Carbon Price, Physical Damage)

Empirical specification:
ln(PD_climate / PD_baseline) = γ_1 × ΔTemp + γ_2 × Carbon_Price + γ_3 × Physical_Loss + ε

Where:
ΔTemp = Temperature increase from baseline (°C)
Carbon_Price = Carbon price level ($/tCO2)
Physical_Loss = % GDP loss from physical climate impacts
```

**Climate-Adjusted Credit Spread:**
```
Spread_climate = Spread_baseline + Climate Risk Premium

Climate Risk Premium = β_1 × Transition_Risk + β_2 × Physical_Risk

Where risks measured via:
Transition_Risk = Carbon Intensity × Carbon Price × Duration
Physical_Risk = Asset Exposure × Hazard Probability × Damage Function
```

**Data Required:**

**For Sovereigns:**
- Baseline credit spreads: 
  - Source: Bloomberg (sovereign CDS spreads), FRED
  - Variable: 5-year CDS spreads by country
- Temperature projections:
  - Source: NGFS scenarios, IPCC data
  - Variable: Country-level temperature anomaly
- GDP climate sensitivity:
  - Source: <cite>Kotz et al. (2024, Nature)</cite>, IMF estimates
  - Variable: % GDP loss per °C warming

**For Corporates:**
- Company credit rating: S&P, Moody's, Fitch
- Bond yields: Bloomberg, FRED (for aggregate indices)
- Emissions intensity: CDP, Bloomberg ESG
- Physical asset exposure: 10-K location data, hazard maps

**Climate Scenario Data:**
- NGFS scenarios: https://www.ngfs.net/ngfs-scenarios-portal/
- Variables needed:
  - Carbon price trajectories
  - Temperature pathways
  - GDP impacts by country/sector
  - Energy price changes

**Academic Finding:** <cite>Klusak et al. (2023)</cite> find that under 2.5-3°C warming scenarios, 59 countries face climate-induced sovereign credit downgrades averaging 1.0-1.3 notches, increasing borrowing costs by $22-33 billion annually.

---

### 4.7 ESG Integration Metrics

**Source:** <cite>Eccles, Ioannou & Serafeim (2014, Management Science)</cite>, <cite>Berg, Koelbel & Rigobon (2022, Review of Finance)</cite>

**4.7.1 ESG Scores**

**Data Sources:**
- MSCI ESG Ratings (AAA to CCC)
- Sustainalytics ESG Risk Ratings
- Refinitiv ESG Scores (0-100)
- Bloomberg ESG Disclosure Scores
- S&P Global ESG Scores

**Limitations:** <cite>Berg et al. (2022)</cite> document low correlation (0.38-0.71) between rating providers due to different methodologies.

**4.7.2 Carbon Footprint Metrics**

**Mathematical Formulation:**

**Weighted Average Carbon Intensity (WACI):**
```
WACI = Σ[w_i × (Emissions_i / Revenue_i)]

Where:
w_i = Portfolio weight of company i
Emissions_i = Scope 1 + Scope 2 emissions (tCO2e)
Revenue_i = Company revenue ($)

Units: tCO2e per $M revenue
```

**Portfolio Carbon Footprint:**
```
Carbon Footprint = Σ[w_i × Emissions_i] / Portfolio Value

Units: tCO2e per $M invested
```

**Data Required:**
- Portfolio holdings and weights: Your portfolio management system
- Company emissions:
  - Source: CDP, Bloomberg ESG, Refinitiv, S&P Trucost
  - Variables: Scope 1, Scope 2, Scope 3 emissions
- Company revenue: Financial statements, Yahoo Finance

**Financed Emissions (for Banks):**
```
Financed Emissions = Σ[(Outstanding_i / Total Equity + Debt_i) × Emissions_i]

Where:
Outstanding_i = Loan/investment amount to company i
```

---

## 5. Integrated Framework

### 5.1 Three-Pillar Investment Decision Framework

**Pillar 1: Fundamental + Climate Screening (What to Buy/Sell)**

**Mathematical Integration:**
```
Fundamental Score = w_1×P/E + w_2×ROE + w_3×FCF_Yield + w_4×Debt_Ratio

Climate-Adjusted Score = Fundamental Score × (1 - Climate_VaR)

Or:
Climate-Adjusted Score = Fundamental Score - Climate_Penalty

Where:
Climate_Penalty = β_climate × Climate_Risk_Factor + Physical_Risk_Score
```

**Example:**
```
Company A:
- P/E: 15 (good, below sector average of 18)
- ROE: 18% (strong)
- Climate VaR: 35% (high climate risk)
- Carbon Beta: +0.8 (climate laggard)

Company B:
- P/E: 17 (acceptable)
- ROE: 16% (good)
- Climate VaR: 8% (low climate risk)
- Carbon Beta: -0.3 (climate leader)

Traditional analysis favors A (better valuation)
Climate-adjusted analysis favors B (lower climate-adjusted risk)
```

---

**Pillar 2: Technical Analysis (When to Buy/Sell)**

**Integration with Climate Events:**

```
Buy Signal Strength = Technical_Signal × (1 - Climate_Event_Risk)

Where:
Technical_Signal = f(MA_crossover, RSI, MACD, Volume)
Climate_Event_Risk = P(Extreme Weather Event in next 30 days) × Asset Exposure
```

**Example Climate-Adjusted Entry:**
```
Stock shows golden cross (50-day MA crosses above 200-day MA) → Bullish technical signal

But:
- Company has coastal manufacturing facilities
- Hurricane season approaching (next 3 months)
- NOAA forecasts above-average hurricane activity
- Climate VaR shows 15% value at risk from acute physical events

Decision: Wait for hurricane season to pass or reduce position size by 30%
```

---

**Pillar 3: Climate-Integrated Risk Management (How Much to Buy)**

**Position Sizing with Climate Risk:**

```
Climate-Adjusted Position Size = Base Position Size × (1 - Climate_Adjustment_Factor)

Where:
Climate_Adjustment_Factor = w_1×(Climate_VaR/100) + w_2×|Carbon_Beta| + w_3×Stranded_Asset_Risk

Typical weights: w_1 = 0.4, w_2 = 0.3, w_3 = 0.3
```

**Portfolio-Level Climate Constraints:**

```
Minimize: σ_p² (portfolio variance)

Subject to:
1. Σw_i = 1 (fully invested)
2. w_i ≥ 0 (long-only, or adjust for shorts)
3. E[R_p] ≥ Target Return
4. WACI_portfolio ≤ WACI_benchmark × (1 - Reduction_Target)
5. Climate_VaR_portfolio ≤ Threshold
6. Σ(w_i × Stranded_Asset_Risk_i) ≤ Max_Stranded_Risk
```

**Example:**
```
Base position calculation:
- Account: $100,000
- Risk per trade: 1% = $1,000
- Entry: $50
- Technical stop loss: $45
- Base position = $1,000 / $5 = 200 shares

Climate adjustments:
- Climate VaR: 30%
- Carbon Beta: +0.6
- Stranded Asset Risk: 20% of book value in coal reserves
- Climate Adjustment Factor = 0.4×0.30 + 0.3×0.6 + 0.3×0.20 = 0.12 + 0.18 + 0.06 = 0.36

Climate-Adjusted Position = 200 × (1 - 0.36) = 200 × 0.64 = 128 shares
```

---

### 5.2 Climate Scenario Analysis in Portfolio Construction

**Source:** <cite>NGFS Guide to Climate Scenario Analysis (2024)</cite>

**Framework:**

**Step 1: Select Climate Scenarios**

Use NGFS scenarios or equivalent:
- Orderly transition (Net Zero 2050): Early policy action, 1.5°C
- Disorderly transition (Delayed Transition): Late policy action, higher transition costs
- Hot house world (Current Policies): 3°C+, high physical risk

**Step 2: Project Portfolio Impact**

```
Portfolio Value_scenario = Σ[w_i × V_i × (1 + r_i,scenario)^n]

Where:
r_i,scenario = Expected return for asset i under climate scenario
n = Time horizon (e.g., 2030, 2050)

Climate-adjusted return:
r_i,scenario = r_baseline + Δr_transition + Δr_physical

Δr_transition = -β_carbon × Carbon_Price_scenario
Δr_physical = -Physical_Damage_i,scenario
```

**Step 3: Calculate Climate VaR by Scenario**

```
Climate VaR_scenario = (Portfolio Value_baseline - Portfolio Value_scenario) / Portfolio Value_baseline
```

**Step 4: Probability-Weight Scenarios**

```
Expected Climate Impact = Σ[P_scenario × Climate VaR_scenario]

Where:
P_scenario = Subjective or market-implied probability of scenario
Σ P_scenario = 1
```

**Data Required:**

**NGFS Scenario Variables (by scenario, country, sector, year):**
- Carbon price ($/tCO2)
- GDP growth rate (%)
- Temperature increase (°C)
- Energy prices ($/MWh)
- Sectoral output changes (%)
- Source: https://data.ece.iiasa.ac.at/ngfs/

**Company-Specific:**
- Revenue by geography/sector: 10-K segment reporting
- Emissions by scope: CDP, sustainability reports
- Asset locations: 10-K, company disclosures

**Example Scenario Analysis:**
```
Portfolio of 10 stocks, current value $1M

Scenario 1: Net Zero 2050 (P = 30%)
- High carbon price by 2030: $200/tCO2
- High-carbon stocks decline 40%
- Clean energy stocks appreciate 60%
- Portfolio value: $950,000
- Climate VaR: 5%

Scenario 2: Delayed Transition (P = 40%)
- Moderate carbon price by 2030: $100/tCO2
- Abrupt policy changes cause volatility
- Portfolio value: $920,000
- Climate VaR: 8%

Scenario 3: Current Policies (P = 30%)
- Low carbon price: $30/tCO2
- High physical damages by 2040
- Portfolio value: $880,000 (physical damage to coastal assets)
- Climate VaR: 12%

Expected Climate VaR = 0.30×5% + 0.40×8% + 0.30×12% = 1.5% + 3.2% + 3.6% = 8.3%
Expected Portfolio Value = 0.30×$950k + 0.40×$920k + 0.30×$880k = $917,000
```

---

### 5.3 Climate-Adjusted CAPM

**Source:** <cite>Dietz, Gollier & Kessler (2018, Journal of Environmental Economics and Management)</cite>

**Mathematical Formulation:**

**Traditional CAPM:**
```
E[R_i] = R_f + β_i × (E[R_m] - R_f)
```

**Climate-Augmented CAPM:**
```
E[R_i] = R_f + β_market,i × MRP + β_climate,i × CRP

Where:
MRP = Market Risk Premium = E[R_m] - R_f
CRP = Climate Risk Premium
β_climate,i = Climate beta (from earlier section)
```

**Climate Risk Premium Estimation:**

Empirical approach:
```
Use historical returns of climate factor portfolio:
CRP = E[R_brown] - E[R_green]
```

Or model-based:
```
CRP = λ_climate × σ_climate

Where:
λ_climate = Market price of climate risk
σ_climate = Standard deviation of climate factor
```

**Data Required:**
- Risk-free rate: 3-month or 10-year Treasury (FRED: DGS3MO, DGS10)
- Market returns: S&P 500 or broad market index
- Climate factor returns: Brown-minus-green portfolio (construct as in Carbon Beta section)
- Stock returns: Yahoo Finance

**Academic Finding:** <cite>Huij et al. (2023)</cite> estimate CRP at approximately 2-3% annually, though this is debated.

---

## 6. Data Sources

### 6.1 Market Data

**Yahoo Finance (Free)**
- Stock prices (OHLC, Volume): Daily, weekly, monthly
- API: `yfinance` Python library
- Tickers: Individual stocks, indices, ETFs
- Example: `^GSPC` (S&P 500), `^TNX` (10-year Treasury yield)

**Google Finance (Free)**
- Stock prices and basic fundamentals
- Access via Google Sheets function: `=GOOGLEFINANCE("TICKER", "attribute")`

**FRED - Federal Reserve Economic Data (Free)**
- Macroeconomic data: GDP, inflation, interest rates, unemployment
- Website: https://fred.stlouisfed.org/
- API: `fredapi` Python library
- Key variables:
  - GDPC1: Real GDP
  - CPIAUCSL: Consumer Price Index
  - DGS10: 10-year Treasury rate
  - T10Y2Y: 10-Year minus 2-Year Treasury spread

**Alpha Vantage (Free tier available)**
- Stock prices, forex, crypto
- Technical indicators pre-calculated
- API: https://www.alphavantage.co/

---

### 6.2 Fundamental Data

**SEC EDGAR (Free for US companies)**
- Website: https://www.sec.gov/edgar
- Filings: 10-K (annual), 10-Q (quarterly), 8-K (current events)
- Financial statements: Balance sheet, income statement, cash flow
- API: `sec-edgar-downloader` Python library

**Yahoo Finance (Free, Limited)**
- Basic financials: P/E, P/B, market cap, dividend yield
- Access via: Yahoo Finance website or `yfinance` library
- Fields: `info['trailingPE']`, `info['bookValue']`, `info['freeCashflow']`

**Financial Modeling Prep (Free tier)**
- Financial statements, ratios, DCF valuations
- API: https://financialmodelingprep.com/

**SimFin (Free for basic data)**
- Financial statements for US companies
- API: https://simfin.com/

---

### 6.3 Climate & ESG Data

**NGFS Climate Scenarios (Free)**
- Climate scenarios for scenario analysis and stress testing
- Website: https://www.ngfs.net/ngfs-scenarios-portal/
- Data portal: https://data.ece.iiasa.ac.at/ngfs/
- Variables: Carbon prices, temperature, GDP impacts, energy prices
- Coverage: 180+ countries, multiple scenarios, 2020-2100

**CDP - Carbon Disclosure Project (Free, Public Data)**
- Corporate emissions data (Scope 1, 2, 3)
- Website: https://www.cdp.net/
- Some company data freely available, full dataset requires subscription
- Coverage: 18,700+ companies

**IPCC Data (Free)**
- Climate models, temperature projections, scenario data
- Website: https://www.ipcc.ch/data/
- CMIP6 climate models: https://esgf-node.llnl.gov/projects/cmip6/

**NOAA Climate Data (Free)**
- Historical climate data, weather events, climate indices
- Website: https://www.ncdc.noaa.gov/
- Billion-Dollar Weather/Climate Disasters: https://www.ncei.noaa.gov/access/billions/

**World Bank Climate Data (Free)**
- Climate projections by country
- Website: https://climateknowledgeportal.worldbank.org/
- API: Available for programmatic access

**FEMA Flood Maps (Free, US)**
- Flood hazard zones, flood insurance rate maps
- Website: https://msc.fema.gov/portal/

**NASA Earth Data (Free)**
- Satellite data, climate variables, sea level, temperature
- Website: https://earthdata.nasa.gov/

---

### 6.4 ESG Ratings & Data (Mostly Paid, Limited Free Access)

**Bloomberg ESG Data**
- ESG scores, emissions data, controversies
- Requires Bloomberg Terminal subscription (~$24,000/year)

**Refinitiv (LSEG) ESG Data**
- ESG scores (0-100), emissions, controversies
- Requires subscription

**MSCI ESG Ratings**
- ESG ratings (AAA to CCC)
- Limited free company lookups: https://www.msci.com/esg-ratings
- Full data requires subscription

**Sustainalytics**
- ESG Risk Ratings
- Some free company ratings via Morningstar
- Full data requires subscription

**S&P Global ESG Scores**
- ESG scores, carbon footprint
- Requires subscription

**Yahoo Finance ESG Scores (Free, Limited)**
- Basic ESG scores for some companies
- Access via `yfinance` library: `info['esgScores']`

**Free Alternative - Company Sustainability Reports:**
- Most large companies publish annual sustainability/ESG reports
- Find on company investor relations websites
- Disclosures include: Emissions, energy use, climate risks, diversity metrics

---

### 6.5 Academic & Research Data

**SSRN - Social Science Research Network (Free)**
- Working papers on climate finance, risk management
- Website: https://www.ssrn.com/
- Search: "climate risk", "carbon beta", "stranded assets"

**Google Scholar (Free)**
- Academic papers, citations
- Website: https://scholar.google.com/

**NBER - National Bureau of Economic Research (Free working papers)**
- Economics and finance research
- Website: https://www.nber.org/

**Research Papers from Central Banks (Free):**
- Bank for International Settlements (BIS): https://www.bis.org/
- Federal Reserve: https://www.federalreserve.gov/econres/
- European Central Bank: https://www.ecb.europa.eu/
- Bank of England: https://www.bankofengland.co.uk/

---

### 6.6 Python Libraries for Data Access

**Financial Data:**
```python
import yfinance as yf
import pandas_datareader as pdr
from fredapi import Fred
import sec_edgar_downloader as sed
```

**Climate/ESG Data:**
```python
import pandas as pd
import requests  # For API calls to NGFS, World Bank, etc.
import xarray as xr  # For NetCDF climate data
```

**Example Code Snippets:**

**Get Stock Data:**
```python
import yfinance as yf
ticker = yf.Ticker("AAPL")
hist = ticker.history(period="5y")  # 5 years of daily data
info = ticker.info  # Company fundamentals
print(info['trailingPE'], info['bookValue'])
```

**Get FRED Macro Data:**
```python
from fredapi import Fred
fred = Fred(api_key='your_api_key')
gdp = fred.get_series('GDPC1')
cpi = fred.get_series('CPIAUCSL')
```

**Calculate Returns:**
```python
import pandas as pd
prices = hist['Close']
returns = prices.pct_change().dropna()
```

**Calculate VaR:**
```python
import numpy as np
VaR_95 = np.percentile(returns, 5)  # 5th percentile for 95% VaR
print(f"95% Daily VaR: {VaR_95:.2%}")
```

---

## 7. Key Academic References

### Climate Risk - Financial Stability
- **Battiston, S., et al. (2017).** "A climate stress-test of the financial system." *Nature Climate Change*, 7(4), 283-288.
- **Campiglio, E., et al. (2023).** "Climate-related risks in financial assets." *Journal of Economic Surveys*, 37(3), 950-992.
- **Bolton, P., et al. (2020).** "The green swan: Central banking and financial stability in the age of climate change." *Bank for International Settlements*.

### Climate VaR
- **MSCI (2024).** "Climate Value-at-Risk Methodology." MSCI ESG Research.
- **UNEP FI (2019).** "Changing Course: A comprehensive investor guide to scenario-based methods for climate risk assessment."

### Carbon Beta
- **Huij, J., Laurs, D., Stork, P., & Zwinkels, R. (2023).** "Carbon beta: A market-based measure of climate risk." *SSRN Working Paper*.
- **Görgen, M., et al. (2020).** "Carbon risk." *SSRN Working Paper*.
- **Dietz, S., Gollier, C., & Kessler, L. (2018).** "The climate beta." *Journal of Environmental Economics and Management*, 87, 258-274.

### Stranded Assets
- **Semieniuk, G., et al. (2022).** "Stranded fossil-fuel assets translate to major losses for investors in advanced economies." *Nature Climate Change*, 12(6), 532-538.
- **Caldecott, B. (2017).** "Introduction to special issue: Stranded assets and the environment." *Journal of Sustainable Finance & Investment*, 7(1), 1-13.

### Climate Stress Testing
- **Jung, H., Engle, R., & Berner, R. (2021).** "Climate stress testing." *NYU Volatility Institute Working Paper*.
- **Acharya, V., Berner, R., Engle, R., et al. (2023).** "Climate stress testing." *Federal Reserve Bank of New York Staff Reports*, No. 1059.

### Climate-Adjusted Credit Risk
- **Klusak, P., et al. (2023).** "Rising temperatures, falling ratings: The effect of climate change on sovereign creditworthiness." *Management Science*, 69(12), 7468-7491.
- **Capasso, G., et al. (2025).** "Climate risks and financial stability: Evidence on the effectiveness of climate-related financial policies." *International Review of Financial Analysis*, 99.

### ESG Integration
- **Eccles, R., Ioannou, I., & Serafeim, G. (2014).** "The impact of corporate sustainability on organizational processes and performance." *Management Science*, 60(11), 2835-2857.
- **Berg, F., Koelbel, J., & Rigobon, R. (2022).** "Aggregate confusion: The divergence of ESG ratings." *Review of Finance*, 26(6), 1315-1344.

### NGFS & Regulatory Frameworks
- **NGFS (2024).** "NGFS Climate Scenarios for central banks and supervisors - Phase V." *Network for Greening the Financial System*.
- **Basel Committee on Banking Supervision (2021).** "Climate-related financial risks – measurement methodologies." *Bank for International Settlements*.

---

## 8. Practical Implementation Workflow

### Step-by-Step Implementation

**Week 1: Data Infrastructure Setup**
1. Set up Python environment with required libraries
2. Obtain API keys (FRED, Alpha Vantage, etc.)
3. Download NGFS climate scenarios
4. Create data pipeline for stock prices, fundamentals

**Week 2: Traditional Analysis Implementation**
1. Calculate technical indicators (MA, RSI, MACD)
2. Pull fundamental data (P/E, ROE, FCF)
3. Implement basic risk metrics (VaR, Sharpe ratio)
4. Backtest signals on historical data

**Week 3: Climate Data Integration**
1. Collect emissions data (CDP, company reports)
2. Download NGFS scenario data for relevant geographies
3. Map company asset locations to climate hazard zones
4. Calculate initial Climate VaR estimates

**Week 4: Climate Beta Calculation**
1. Construct brown-minus-green climate factor
2. Run regressions to estimate climate betas
3. Validate against third-party carbon beta data (if available)

**Week 5: Portfolio Construction**
1. Implement climate-adjusted screening
2. Set up position sizing with climate adjustments
3. Add portfolio-level climate constraints
4. Backtest climate-integrated strategy

**Week 6: Scenario Analysis**
1. Project portfolio under 3 NGFS scenarios
2. Calculate scenario-specific Climate VaR
3. Identify portfolio vulnerabilities
4. Develop mitigation strategies

**Ongoing: Monitoring & Rebalancing**
1. Monthly: Update climate factor, recalculate betas
2. Quarterly: Review Climate VaR, update scenarios
3. Semi-annually: Full scenario analysis refresh
4. Annually: Update emissions data, review climate strategy

---

## Conclusion

This framework integrates climate risk considerations into every stage of the investment process:

1. **Screening:** Use Climate VaR and carbon beta to identify climate-resilient companies
2. **Timing:** Adjust entry/exit based on climate events and policy developments
3. **Sizing:** Reduce exposure to high-climate-risk positions
4. **Portfolio Management:** Implement climate constraints alongside traditional diversification
5. **Scenario Analysis:** Stress test under multiple climate futures

The mathematical rigor comes from peer-reviewed research, while data requirements focus on publicly available sources accessible to individual and institutional investors.

**Critical Success Factors:**
- Combine climate metrics with traditional analysis (not replacement)
- Use multiple climate scenarios (don't assume one future)
- Regular updates as climate science and policy evolve
- Engage with companies on climate strategy and data quality
- Monitor regulatory developments (TCFD, ISSB, SEC climate disclosure rules)

**Next Steps:**
1. Start with climate beta calculation for current holdings
2. Calculate portfolio-level Climate VaR under 2-3 scenarios
3. Identify positions with highest climate risk exposure
4. Gradually integrate climate factors into buy/sell decisions
5. Track climate-adjusted performance over time

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**License:** Educational and research purposes

*Note: This framework is for informational and educational purposes. Investment decisions should consider multiple factors and consult with qualified financial advisors. Climate science and methodologies continue to evolve; regular updates to this framework are recommended.*

## Related
[[MKT_MOC]] · Home: [[_INDEX]]

#arm/mkt #type/source
