## Short Answer: No, You Should NOT Use the NGFS Policy Rate Directly as an F-TIIE Equivalent

The NGFS "policy rate" is a **model-simulated central bank policy rate**, while F-TIIE is a **market-observed interbank rate**. They serve different purposes and cannot be used interchangeably for yield curve reconstruction.

---

## Understanding What NGFS Provides

### What the NGFS Scenarios Actually Produce

The NGFS (Network for Greening the Financial System) scenarios provide a **suite of macroeconomic variables** projected over long horizons (typically to 2050 or 2100). These variables are generated through a "suite-of-models" approach that combines:

1. **Integrated Assessment Models (IAMs)** – project energy system changes, emissions, and carbon prices
2. **Physical risk models** – project climate impacts like sea-level rise and extreme weather
3. **Macro-financial models (e.g., NiGEM)** – translate climate shocks into macroeconomic outcomes

The "policy rate" you see in NGFS outputs is the **central bank policy rate** (like the Federal Reserve's target rate or the ECB's main refinancing rate) **as simulated by the macro-financial model** under different climate scenarios. It is not a market rate.

### What Variables Are Actually Available

The Federal Reserve's pilot Climate Scenario Analysis (CSA) documentation explicitly lists the common NGFS variables that practitioners use:

| Variable Type | Description |
|---------------|-------------|
| Carbon prices | Projected price per ton of CO2 |
| Energy prices | Oil, gas, coal, electricity |
| Equity prices | Broad market indices |
| **Policy interest rate** | **Central bank policy rate** |
| **Long term interest rate** | **10-year government bond yields** |
| GDP growth | Real output growth |
| Inflation rate | Consumer price inflation |
| Unemployment rate | Labor market conditions |

**Important:** The NGFS scenarios **do not** provide the full yield curve or interbank rates like TIIE, LIBOR, or SOFR.

---

## The Key Difference: Policy Rate vs. Market Rate

### F-TIIE (Mexico) and Its International Counterparts

| Market | Benchmark Interbank Rate | Description |
|--------|-------------------------|-------------|
| Mexico | F-TIIE (TIIE de Fondeo) | Overnight interbank funding rate, transaction-based |
| United States | SOFR (Secured Overnight Financing Rate) | Overnight Treasury repo market rate |
| Euro Area | €STR (Euro Short-Term Rate) | Overnight unsecured interbank rate |

These are **market-observed rates** derived from actual transactions. They reflect:
- Supply and demand for liquidity
- Credit risk between banks
- Market expectations

### NGFS Policy Rate

The NGFS policy rate is a **model-simulated central bank instrument** that reflects:
- The monetary policy reaction function (e.g., Taylor rule vs. price-level targeting)
- The central bank's response to climate-induced inflation and output gaps
- Different policy assumptions within the macro model

The ECB's analysis shows that inflation and policy rate responses vary significantly depending on the assumed monetary policy rule:
- Under a Taylor rule, short-term interest rates increase more strongly
- Under price-level targeting, the response is more muted

---

## How Practitioners Actually Use NGFS Data for Yield Curves

### The Federal Reserve's Approach

In the Fed's pilot Climate Scenario Analysis (CSA), participants faced exactly the same challenge you're describing. Their solution was:

1. **Use the NGFS policy rate for the short end** – but as an input to a **term structure model**, not as a direct market rate
2. **Use the NGFS long-term interest rate** (e.g., 10-year government yield) for the long end
3. **Apply interpolation** to reconstruct the full yield curve

Table 9 from the Fed's CSA report shows that participants used both the "policy interest rate" and "long term interest rate" as inputs, then **expanded** these to derive additional variables like:
- Corporate yields
- Credit spreads
- LIBOR/SOFR/EURIBOR (using the policy rate as a reference)

### The Translation Methodology

As documented in the Fed's report:

> "Participants linked the NGFS variables to observable time series by converting NGFS variable trajectories from levels to growth rates and applying these to the observable time series."

In practice, this means:

**Step 1:** Take the NGFS policy rate projection (e.g., starting at 5% today, rising to 6.5% in 2030).

**Step 2:** Calculate the **shock** relative to baseline: $\Delta r_t = r_t^{\text{NGFS}} - r_t^{\text{baseline}}$.

**Step 3:** Apply this shock to the current F-TIIE curve (not the NGFS level directly):

$$r_{\text{TIIE}}^{\text{stressed}}(t) = r_{\text{TIIE}}^{\text{current}}(t) + \Delta r_t^{\text{policy}}$$

This preserves the market's current term structure while applying the NGFS shock.

---

## Practical Workflow for Your Mexican Market Application

### Step 1: Gather NGFS Scenario Data

From the NGFS Scenario Explorer, extract for your chosen scenario (e.g., "Net Zero 2050"):
- Policy interest rate (short-term rate)
- Long-term interest rate (10-year government bond yield)
- (Optional) Inflation and GDP projections

### Step 2: Obtain Current Mexican Yield Curve

From Banco de México's SIE (Sistema de Información Económica):
- F-TIIE curve (continuously compounded zero-coupon rates)
- Bonos M yields for longer maturities

### Step 3: Calculate Shocks

For each projection year:

$$\text{Shock}_{\text{policy}}(t) = r_{\text{policy}}^{\text{NGFS}}(t) - r_{\text{policy}}^{\text{baseline}}(t)$$
$$\text{Shock}_{\text{long}}(t) = r_{\text{long}}^{\text{NGFS}}(t) - r_{\text{long}}^{\text{baseline}}(t)$$

### Step 4: Apply Shocks to Current Market Curve

Interpolate the shock across all maturities (simple linear interpolation between short and long ends):

$$\text{Shock}(T) = \text{Shock}_{\text{policy}} + \frac{T}{T_{\text{long}}} \times (\text{Shock}_{\text{long}} - \text{Shock}_{\text{policy}})$$

### Step 5: Construct Stressed Zero Curve

$$R_c^{\text{stressed}}(T) = R_c^{\text{current}}(T) + \text{Shock}(T)$$

### Step 6: Use in Hull-White Calibration

From this stressed zero curve, derive $f(0,t)$ and $\theta(t)$ as we discussed in previous sessions.

---

## Why This Approach Is Correct

1. **Preserves market structure** – The NGFS scenarios are designed for relative comparisons, not absolute rate levels
2. **Aligns with regulatory practice** – The Federal Reserve's CSA participants used identical translation methods
3. **Maintains no-arbitrage** – By constructing a full zero curve, you ensure your Hull-White calibration remains consistent

---

## References

| Source | Citation |
|--------|---------|
| **Federal Reserve CSA (2024)** | "Pilot Climate Scenario Analysis Exercise Summary of Participants Risk-Management Practices and Estimates" – Table 9, Section "Transition Risk Module" – details variable expansion and translation methodology |
| **ECB Occasional Paper No. 336 (2023)** | Darracq Pariès et al., "NGFS climate scenarios for the euro area: role of fiscal and monetary policy conduct" – discusses policy rate sensitivity to monetary policy assumptions |
| **SUERF Policy Brief (2024)** | Darracq Pariès et al., "Opening up the macroeconomic toolbox of NGFS climate scenarios for the euro area" – explains scenario construction and policy rule impacts |
| **NGFS Technical Documentation** | NGFS (2023), "NGFS Climate Scenarios Technical Documentation V4.3" – details variable definitions and model integration |

---

## Summary Table: NGFS Policy Rate vs. F-TIIE

| Feature | NGFS Policy Rate | F-TIIE (Mexico) |
|---------|------------------|-----------------|
| **What it is** | Model-simulated central bank rate | Market-observed interbank rate |
| **Source** | Macro-financial model (NiGEM, etc.) | Actual transactions reported to Banxico |
| **Term** | Typically annual projections to 2100 | Daily observations |
| **Use in modeling** | Input to derive yield curve shocks | Direct calibration input |
| **Relationship** | Policy rate → influences market rates | Market rate reflects policy + liquidity + credit |

In short: treat the NGFS policy rate as a **shock source** to apply to your current F-TIIE curve, not as a direct replacement for market rates. This is exactly how central banks and financial institutions use NGFS scenarios in practice.