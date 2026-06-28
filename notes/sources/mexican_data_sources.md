# Data Sources for Mexican Firms and Markets
## Comprehensive Guide: Free, Registration-Required, and Paid Sources

**Last Updated:** January 2026  
**Focus:** Mexican equity markets, debt instruments, financial data, and climate/ESG information

---

## Table of Contents

1. [Publicly Available Data (Free)](#1-publicly-available-data-free)
2. [Free with Registration](#2-free-with-registration)
3. [Paid Data Services](#3-paid-data-services)
4. [Climate & ESG Data for Mexico](#4-climate--esg-data-for-mexico)
5. [Programming Libraries & APIs](#5-programming-libraries--apis)

---

## 1. Publicly Available Data (Free)

### 1.1 Bolsa Mexicana de Valores (BMV) - Mexican Stock Exchange

**Website:** https://www.bmv.com.mx/

**Available Data:**
- Daily stock prices (20-minute delay)
- Market indices (IPC, INMEX, FTSE BIVA)
- Trading volume
- Market capitalization
- Basic company information
- Listed companies directory

**Access Method:**
- Web interface (free, no registration)
- Data with 20-minute delay
- Market overview and main indicators

**Coverage:**
- ~140 listed companies (small market)
- Equities, ETFs, debt instruments (certificates of deposit)
- Derivatives (through MEXDER)

**Limitations:**
- Small market compared to US/European exchanges
- Limited historical data depth on free tier
- Real-time data requires paid subscription

**Note:** The Mexican stock market is relatively small. Many large Mexican companies trade primarily as ADRs on NYSE/NASDAQ.

---

### 1.2 Banco de México (Banxico) - Central Bank

**Website:** https://www.banxico.org.mx/

**Sistema de Información Económica (SIE):** https://www.banxico.org.mx/SieInternet/

**Available Data:**
- Exchange rates (USD/MXN, EUR/MXN, etc.)
- Interest rates (TIIE, Cetes rates, repo rates)
- Monetary aggregates (M1, M2, M3, M4)
- International reserves
- Credit statistics
- Balance of payments
- Foreign direct investment
- Banking sector statistics
- Government securities yields

**Access Method:**
- **Web interface:** Free browsing and downloads
- **API Access (SIE API):** Free with token registration
  - Token request: https://www.banxico.org.mx/SieAPIRest/service/v1/token
  - API documentation: https://www.banxico.org.mx/SieAPIRest/service/v1/?locale=en
  - Supports JSON and XML formats
  - Rate limits apply (check documentation)

**Coverage:**
- Historical data dating back to 1960s-1980s depending on series
- Daily, weekly, monthly, quarterly, annual frequencies
- Over 25,000 economic time series

**Key Series IDs (Examples):**
- SF43718: USD/MXN Exchange Rate (determination date)
- SF60653: USD/MXN Exchange Rate (settlement date)
- SF43783: 28-day TIIE (Interbank Equilibrium Interest Rate)
- SF311408: Monetary Aggregate M1
- SF311418: Monetary Aggregate M2

**Programming Access:**
- Python: `Banxico-SIE`, `sie-banxico` packages
- R: `siebanxicor` package (official from Banxico)
- Stata: `getmxdata` command
- See Section 5 for details

**Advantages:**
- Completely free, including API
- High-quality, authoritative data
- Good for macroeconomic and monetary analysis
- Essential for bond/fixed income research

---

### 1.3 INEGI - National Institute of Statistics and Geography

**Website:** https://en.www.inegi.org.mx/

**Banco de Información Económica (BIE):** https://www.inegi.org.mx/app/indicadores/

**Open Data Portal:** https://en.www.inegi.org.mx/datosabiertos/

**Available Data:**
- GDP (national accounts)
- Inflation (CPI, PPI)
- Employment statistics (ENOE - National Survey of Occupation and Employment)
- Industrial production indices
- Trade statistics (imports/exports)
- Construction activity
- Retail sales
- Manufacturing surveys
- Census data (population, housing, economic census)
- Poverty and inequality statistics
- Geographic and demographic data

**Access Method:**
- **Web interface:** Free downloads
- **API Access:** Free with token registration
  - Token request: https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify
  - API documentation: https://www.inegi.org.mx/servicios/api_indicadores.html
  - Supports JSON and XML

**Coverage:**
- Historical data typically from 1990s onward
- Monthly, quarterly, annual frequencies
- National and state-level disaggregation
- Sectoral breakdowns (NAICS classification)

**Key Indicators:**
- IGAE (Global Economic Activity Indicator - monthly GDP proxy)
- INPC (National Consumer Price Index)
- INPP (National Producer Price Index)
- Industrial production by sector
- Formal employment statistics

**Programming Access:**
- R: `inegiR` package
- Python: Various community packages
- Stata: `getmxdata` command
- See Section 5 for details

**Advantages:**
- Comprehensive economic statistics
- Free API access
- Good sectoral detail
- Geographic disaggregation

---

### 1.4 Comisión Nacional Bancaria y de Valores (CNBV) - Banking and Securities Commission

**Website:** https://www.cnbv.gob.mx/ (mostly Spanish)
**English Section:** https://www.cnbv.gob.mx/en/Paginas/default.aspx/

**Available Data:**
- Banking sector statistics
- Financial institution registries
- Supervised entities information
- Financial inclusion reports
- Regulatory information
- Some aggregate financial data

**Access Method:**
- Web downloads (PDF, Excel)
- Statistical bulletins
- Reports section

**Coverage:**
- Banks, brokerage houses, insurance companies
- Aggregate sector data
- Limited company-specific data publicly available

**Limitations:**
- Most detailed data requires formal request or is not public
- Interface primarily in Spanish
- Limited granular company data
- More regulatory focus than data dissemination

**Use Cases:**
- Banking sector analysis
- Financial system stability metrics
- Regulatory research
- Financial inclusion studies

---

### 1.5 Secretaría de Hacienda y Crédito Público (SHCP) - Ministry of Finance

**Website:** https://www.gob.mx/shcp (Spanish)

**Available Data:**
- Government budget and spending
- Public debt statistics
- Government securities auctions (Cetes, Bonos M, Udibonos)
- Tax revenue statistics
- Fiscal balance information

**Access Method:**
- Web downloads
- Statistical reports
- Budget transparency portal

**Coverage:**
- Federal government finances
- Historical fiscal data

**Use Cases:**
- Sovereign debt analysis
- Fiscal policy research
- Government bond valuation

---

### 1.6 Yahoo Finance - Mexican Stocks

**Website:** https://finance.yahoo.com/

**Available Data:**
- Daily stock prices for BMV-listed companies
- Basic fundamentals (P/E, market cap, dividend yield)
- Historical prices
- Mexican indices

**Ticker Format:**
- BMV stocks: `[TICKER].MX`
- Examples: 
  - WALMEX.MX (Walmart de México)
  - FEMSA.MX (FEMSA)
  - AMXL.MX (América Móvil)
  - CEMEX.MX (CEMEX)
  - GFNORTE.MX (Grupo Financiero Banorte)

**Access Method:**
- Web interface: Free
- API: `yfinance` Python library (free, unofficial)

**Advantages:**
- Easy to use
- Works with familiar tools
- Good for equity price data
- Free historical data

**Limitations:**
- Limited fundamental data for Mexican companies
- May have data quality issues for smaller stocks
- Better coverage for large-cap stocks

---

### 1.7 Refinitiv/LSEG (formerly Reuters) - Limited Free Data

**Website:** https://www.lseg.com/

**Available Data (Free tier):**
- Limited market data
- Some company profiles
- News (limited)

**Note:** Mostly paid service, but some basic information accessible for free.

---

## 2. Free with Registration

### 2.1 INEGI & Banxico APIs

**Already covered above - Free tokens available:**
- INEGI API Token: https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify
- Banxico API Token: https://www.banxico.org.mx/SieAPIRest/service/v1/token

**Process:**
1. Register with email
2. Receive 64-character token
3. Use token in API calls
4. Free for non-commercial and research use
5. Rate limits apply (typically generous)

---

### 2.2 Reportes Anuales de Emisoras (BMV)

**Website:** BMV Investor Relations sections

**Available Data:**
- Annual reports (20-F for foreign registrants, local format)
- Quarterly reports
- Financial statements
- Corporate governance reports

**Access Method:**
- Company websites (investor relations section)
- BMV website company listings
- Some available through BMV's information system

**Format:**
- PDF reports
- Some Excel data
- Requires manual extraction

**Coverage:**
- All publicly listed companies required to file
- Comprehensive financial statements
- Management discussion
- Risk factors
- Corporate governance

**How to Find:**
1. Go to BMV website
2. Navigate to "Emisoras" (Issuers)
3. Select company
4. Find "Información Financiera" section
5. Download reports

---

### 2.3 Economatica (Trial Available)

**Website:** https://economatica.com/

**Available Data:**
- Latin American market data
- Mexican stocks and bonds
- Financial statements
- Valuation metrics
- Analyst estimates

**Access:**
- Paid service, but offers free trials
- Academic pricing available
- Contact for pricing

**Coverage:**
- Comprehensive for Mexican listed companies
- Historical data
- Screening tools
- Excel add-in

---

### 2.4 S&P Capital IQ - Mexican Market (Institutional)

**Limited free access for academics/students through university libraries**

---

## 3. Paid Data Services

### 3.1 Bloomberg Terminal

**Cost:** ~$24,000 USD/year per user (2-user minimum typically)

**Coverage:**
- Comprehensive Mexican market data
- Real-time BMV prices
- Mexican government bonds (Cetes, Bonos M, Udibonos)
- Corporate bonds
- Detailed financials for public companies
- Mexican economic data
- News and analysis
- Excel integration

**Access:**
- Terminal interface
- Bloomberg API (additional setup)
- Excel add-in

**Advantages:**
- Most comprehensive data for Mexican markets
- Real-time data
- Professional-grade analytics
- Industry standard

**Best for:** Institutional investors, banks, large asset managers

---

### 3.2 Refinitiv Eikon/Workspace (formerly Thomson Reuters)

**Cost:** ~$20,000-30,000 USD/year per user

**Coverage:**
- Similar to Bloomberg for Mexican markets
- Real-time BMV data
- Mexican bonds and derivatives
- Company financials
- Economic data
- News

**Advantages:**
- Strong fundamental data
- Good for fixed income
- API access available

---

### 3.3 S&P Capital IQ

**Cost:** Variable, typically $10,000-40,000 USD/year depending on modules

**Coverage:**
- Mexican public and private company data
- Financial statements
- Ownership data
- Transactions and deals
- Credit ratings
- Estimates

**Advantages:**
- Strong fundamental data
- Good for credit analysis
- Excel plug-in

---

### 3.4 Economatica

**Cost:** Variable, contact for pricing. Academic discounts available.

**Coverage:**
- Focused on Latin American markets including Mexico
- BMV stocks
- Financial statements
- Market data
- Valuation ratios

**Advantages:**
- Latin America specialist
- Good value for Mexico-focused work
- Excel integration
- Screening tools

---

### 3.5 EOD Historical Data

**Website:** https://eodhistoricaldata.com/

**Cost:** Starting at $19.99/month for basic, up to $79.99/month for advanced

**Coverage:**
- Mexican Stock Exchange data
- End-of-day prices
- Historical data
- Fundamental data
- API access

**Advantages:**
- Affordable
- Good API
- Historical data
- JSON/CSV formats

---

### 3.6 Intrinio

**Website:** https://intrinio.com/

**Cost:** Starting from $50-200/month for Mexican market data

**Coverage:**
- Mexican Stock Exchange (BMV) end-of-day prices
- Company fundamentals
- API access
- Excel/Google Sheets integration

**Advantages:**
- Developer-friendly API
- Good documentation
- Affordable for small teams

---

### 3.7 FactSet

**Cost:** Enterprise pricing, typically $12,000-30,000 USD/year

**Coverage:**
- Mexican market data
- Company financials
- Ownership
- Estimates
- Fixed income

**Advantages:**
- Strong for asset managers
- Good analytics
- Excel integration

---

## 4. Climate & ESG Data for Mexico

### 4.1 CDP México (Carbon Disclosure Project)

**Website:** https://www.cdp.net/

**Available Data:**
- Corporate emissions disclosures (Scope 1, 2, 3)
- Climate risk responses
- Water security data
- Forest protection data

**Access:**
- Some data publicly available
- Full access requires registration (free for non-commercial)
- Annual reports downloadable

**Mexican Companies Coverage:**
- Major BMV-listed companies
- Large private companies
- Varies by year (typically 30-50 companies)

**Key Mexican Companies Reporting:**
- CEMEX
- América Móvil
- Grupo Bimbo
- FEMSA
- Walmart de México
- Grupo México

---

### 4.2 NGFS Climate Scenarios (for Mexico)

**Website:** https://www.ngfs.net/ngfs-scenarios-portal/

**Data Portal:** https://data.ece.iiasa.ac.at/ngfs/

**Available Data:**
- Carbon price projections for Mexico
- GDP impacts under climate scenarios
- Temperature projections
- Energy transition pathways
- Sectoral emissions

**Access:**
- Free download
- CSV, Excel formats
- Country-level data available

**Scenarios Available:**
- Net Zero 2050
- Delayed Transition
- Current Policies
- Divergent Net Zero

**Use Cases:**
- Climate stress testing
- Scenario analysis
- Climate VaR calculations
- Policy analysis

---

### 4.3 World Bank Climate Change Knowledge Portal

**Website:** https://climateknowledgeportal.worldbank.org/country/mexico

**Available Data:**
- Historical climate data for Mexico
- Climate projections
- Vulnerability assessments
- Climate finance data
- Sector-specific analysis

**Access:**
- Free downloads
- Interactive maps
- Data visualization tools

---

### 4.4 INECC - Instituto Nacional de Ecología y Cambio Climático

**Website:** https://www.gob.mx/inecc (Spanish)

**Available Data:**
- National greenhouse gas inventory
- Climate adaptation strategies
- Vulnerability studies
- State-level climate data
- Sectoral emissions

**Access:**
- Free downloads (mostly PDF reports)
- Some datasets available

**Limitations:**
- Primarily in Spanish
- Limited company-specific data
- Aggregate national/sectoral data

---

### 4.5 Company Sustainability Reports

**Source:** Individual company websites

**Mexican Companies with Good ESG Reporting:**
- **CEMEX:** Annual Integrated Report, Sustainability Report
- **FEMSA:** Integrated Annual Report
- **Grupo Bimbo:** Sustainability Report
- **Walmart de México:** Sustainability Report
- **América Móvil:** Annual Sustainability Report
- **Grupo México:** Sustainability Report
- **Banorte:** Sustainability Report

**Access:**
- Company investor relations pages
- Annual reports typically include sustainability sections
- Standalone sustainability reports

**Data Available:**
- Scope 1, 2, 3 emissions
- Energy consumption
- Water usage
- Waste management
- Social metrics
- Governance practices

---

### 4.6 ESG Rating Agencies (Paid, but some free data)

**MSCI ESG Ratings:**
- Website: https://www.msci.com/esg-ratings
- Free company lookup (limited)
- Full access requires subscription

**Sustainalytics:**
- Website: https://www.sustainalytics.com/
- Free ratings available for some large companies
- Full access paid

**S&P Global ESG Scores:**
- Requires S&P Capital IQ or CSA subscription
- Corporate Sustainability Assessment (CSA)

---

## 5. Programming Libraries & APIs

### 5.1 Python Libraries

#### For Banxico (SIE) Data:

**Banxico-SIE:**
```python
pip install Banxico-SIE

from siebanxico import SIEBanxico

# Initialize with token
banxico_token = "your_64_character_token_here"
api_client = SIEBanxico(token=banxico_token, locale="en")

# Get exchange rate series
series_ids = ["SF43718", "SF60653"]  # USD/MXN rates
import pandas as pd
df = api_client.getSeriesDataFrame(
    series_ids, 
    startDate="2020-01-01", 
    endDate="2024-12-31",
    periodicity=pd.offsets.BusinessDay(1)
)
```

**sie-banxico:**
```python
pip install sie-banxico

from api_banxico import SIEBanxico

api = SIEBanxico(
    token="your_token", 
    id_series=['SF311408', 'SF311418'],
    language='en'
)

# Get last data
data = api.get_lastdata()

# Get time series
data = api.get_timeseries_range(
    init_date='2020-01-01',
    end_date='2024-12-31'
)
```

#### For INEGI Data:

**No official Python package, but community solutions available on GitHub:**
- Search: "INEGI Python" on GitHub
- Manual API calls using `requests` library

**Example manual API call:**
```python
import requests

token = "your_inegi_token"
indicator_id = "494072"  # Example: Nominal GDP

url = f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/{indicator_id}/en/{token}/2.0/"

response = requests.get(url)
data = response.json()
```

#### For Yahoo Finance (Mexican Stocks):

**yfinance:**
```python
pip install yfinance

import yfinance as yf

# Get Mexican stock data
ticker = yf.Ticker("WALMEX.MX")
hist = ticker.history(period="5y")
info = ticker.info

# Get multiple tickers
tickers = ["WALMEX.MX", "FEMSA.MX", "AMXL.MX"]
data = yf.download(tickers, start="2020-01-01", end="2024-12-31")
```

---

### 5.2 R Libraries

#### For Banxico (SIE) Data:

**siebanxicor (Official from Banxico):**
```r
install.packages("siebanxicor")
library(siebanxicor)

# Set token
setToken("your_64_character_token")

# Get series data
series <- c("SF43718", "SF311408")
data <- getSeriesData(series, '2020-01-01', '2024-12-31')

# Get metadata
metadata <- getSeriesMetadata(series)

# Get last values
current <- getSeriesCurrentValue(series)
```

#### For INEGI Data:

**inegiR:**
```r
install.packages("inegiR")
library(inegiR)

# Set token
token <- "your_inegi_token"

# Get series
data <- inegi_series(
    series = "494072",  # Nominal GDP
    token = token
)

# GDP data
gdp <- PIB(token)

# Inflation data  
cpi <- inflacion_mensual(token)

# Exchange rate
fx <- tipo_cambio(token)
```

#### For Yahoo Finance:

**quantmod:**
```r
install.packages("quantmod")
library(quantmod)

# Get Mexican stock data
getSymbols("WALMEX.MX", from="2020-01-01", to="2024-12-31")

# Multiple symbols
symbols <- c("WALMEX.MX", "FEMSA.MX", "AMXL.MX")
getSymbols(symbols)
```

---

### 5.3 Stata

**getmxdata command:**

Download from: http://fmwww.bc.edu/repec/bocode/g/getmxdata.ado

```stata
* Install
net install getmxdata

* Get INEGI token
* https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify

* Get Banxico token
* https://www.banxico.org.mx/SieAPIRest/service/v1/token

* Use INEGI data (BIE)
getmxdata 494072 628194, bie key(your_inegi_token)

* Use Banxico data (SIE)
getmxdata SF43718 SF311408, banxico key(your_banxico_token)
```

---

## 6. Key Mexican Companies on BMV (Stock Tickers)

### Large Cap (IPC Components):

| Company | Ticker | Sector | Also Trades |
|---------|--------|--------|-------------|
| América Móvil | AMXL.MX | Telecom | AMX (NYSE) |
| Walmart de México | WALMEX.MX | Retail | - |
| FEMSA | FEMSAUBD.MX | Beverages/Retail | FMX (NYSE) |
| Grupo México | GMEXICOB.MX | Mining | - |
| Cemex | CEMEX.MX | Materials | CX (NYSE) |
| Grupo Financiero Banorte | GFNORTE.MX | Financials | - |
| Grupo Bimbo | BIMBO.MX | Food | - |
| Grupo Financiero Inbursa | GFINBUR.MX | Financials | - |
| Alfa | ALFAA.MX | Conglomerate | - |
| Grupo Aeroportuario del Sureste | ASUR.MX | Infrastructure | ASR (NYSE) |
| Grupo Aeroportuario del Pacífico | GAP.MX | Infrastructure | PAC (NYSE) |
| Grupo Aeroportuario del Centro Norte | OMA.MX | Infrastructure | OMAB (NASDAQ) |
| Televisa | TLEVISA.MX | Media | Now merged with Univision |

**Note:** Many major Mexican companies trade primarily as ADRs in US markets, where liquidity and data availability are better.

---

## 7. Practical Workflow Recommendations

### For Equity Analysis:

**Price Data:**
1. Start with Yahoo Finance (`yfinance`) - free and easy
2. Supplement with EOD Historical Data if you need better quality
3. Use Bloomberg/Refinitiv if you have institutional access

**Fundamental Data:**
1. Company annual reports (20-F or local format) from BMV/company websites
2. Yahoo Finance for basic metrics
3. Economatica or Bloomberg for comprehensive financials

**Economic Context:**
1. Banxico SIE API for monetary/financial data
2. INEGI API for real economy data
3. SHCP for fiscal data

---

### For Fixed Income/Credit Analysis:

**Bond Data:**
1. Bloomberg or Refinitiv (primary sources for Mexican bonds)
2. Banxico for government securities yields
3. Valmer (Mexican pricing service - paid) for corporate bonds

**Credit Analysis:**
1. CNBV for banking sector data
2. Company financial statements
3. Credit rating agencies (S&P, Moody's, Fitch, HR Ratings)

---

### For Climate/ESG Analysis:

**Emissions Data:**
1. CDP disclosures (free registration)
2. Company sustainability reports
3. INECC national inventory for benchmarking

**Climate Scenarios:**
1. NGFS scenarios (free)
2. IPCC data for Mexico
3. World Bank climate portal

**ESG Ratings:**
1. Free lookups from MSCI, Sustainalytics (limited)
2. Company self-disclosures
3. Paid services if available

---

## 8. Data Quality & Coverage Notes

### Challenges with Mexican Data:

1. **Small market:** ~140 companies on BMV vs thousands on NYSE/NASDAQ
2. **Liquidity:** Many stocks trade infrequently
3. **Dual listings:** Major companies often have better data via US ADRs
4. **Debt market:** Primarily OTC, limited transparency
5. **Private companies:** Very limited public data
6. **Language:** Much regulatory/company data only in Spanish
7. **Standardization:** Less standardized reporting than US/EU markets

### Data Gaps:

- **Corporate bond data:** Limited free sources, mostly paid
- **Private company data:** Generally unavailable
- **High-frequency data:** Requires paid services
- **Comprehensive credit data:** Mostly institutional
- **Detailed ESG:** Limited to large companies

### Recommendations:

1. **For large-cap BMV stocks:** Good free data available (Yahoo Finance, company reports)
2. **For economic analysis:** Excellent free data (Banxico, INEGI)
3. **For bonds/credit:** Paid services necessary (Bloomberg, Refinitiv)
4. **For ESG:** Start with company reports, supplement with CDP, use paid services for comprehensive coverage
5. **For academic research:** Focus on data-rich companies, leverage free APIs (Banxico, INEGI)

---

## 9. Legal & Compliance Notes

### Data Usage Rights:

**Banxico & INEGI:**
- Free for research and non-commercial use
- Attribution required
- Check specific terms of service for commercial use

**Yahoo Finance:**
- Unofficial API (`yfinance`) - use at own risk
- No official commercial use permissions
- Better to use official data providers for commercial applications

**Company Reports:**
- Public domain for publicly listed companies
- Can be used for analysis
- Redistribution may have restrictions

**Paid Services:**
- Usage rights per license agreement
- Typically restricted to licensed users
- Redistribution usually prohibited

### Recommended Citation Format:

**Banxico:**
```
Banco de México. (2024). Economic Information System (SIE). 
Retrieved from https://www.banxico.org.mx/SieInternet/
```

**INEGI:**
```
INEGI. (2024). [Indicator Name]. National Institute of Statistics and Geography.
Retrieved from https://www.inegi.org.mx/
```

**BMV:**
```
Bolsa Mexicana de Valores. (2024). [Company Name] Market Data.
Retrieved from https://www.bmv.com.mx/
```

---

## 10. Contact Information for Data Support

**Banxico (SIE API Support):**
- Email: Check API documentation
- Documentation: https://www.banxico.org.mx/SieAPIRest/service/v1/?locale=en

**INEGI (Developer Support):**
- Website: https://www.inegi.org.mx/app/desarrolladores/
- Email: Contact through website

**BMV (Information Products):**
- Website: https://www.bmv.com.mx/en/information-products/
- Phone: +52 55 5342 9000

**CNBV:**
- Website: https://www.cnbv.gob.mx/
- Address: Insurgentes Sur No. 1971, Col. Guadalupe Inn, C.P. 01020, Ciudad de México
- Phone: +52 55 1454 6000

---

## Summary Table: Quick Reference

| Data Type | Best Free Source | Best Paid Source | API Available |
|-----------|-----------------|------------------|---------------|
| Stock Prices | Yahoo Finance | Bloomberg | Yes (yfinance) |
| Company Financials | Company Reports | Bloomberg/S&P | Limited |
| Economic Data | Banxico, INEGI | Bloomberg | Yes (Free) |
| Bond Data | Banxico (govt bonds) | Bloomberg | Limited |
| ESG/Climate | CDP, Company Reports | Bloomberg ESG | Limited |
| Exchange Rates | Banxico | Bloomberg | Yes (Free) |
| Interest Rates | Banxico | Bloomberg | Yes (Free) |
| Credit Ratings | Company websites | Bloomberg/S&P | No |

---

**Document compiled:** January 2026  
**For updates and corrections, please verify information directly with data providers as availability and terms may change.**
