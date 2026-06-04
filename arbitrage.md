# Futures Arbitrage Research: Curve & Basis Arbitrage in Chinese Markets

This document outlines the data collection results and the next steps for researching Curve (Term Structure) Arbitrage and Basis (Spot-Futures) Arbitrage in Chinese futures.

## 1. Data Collection Summary

All data has been downloaded and stored in Parquet format under the [data/](file:///home/hallo/data/ricecta/data/) directory:

- **Futures 5-Minute Data** (`data/futures_5minute/{symbol}/{contract}.parquet`): 5-minute OHLCV, open interest, and settlement prices for all actual individual tradeable contracts of the 23 target commodities active between **2021-01-01** and **2026-06-03**.
- **Domestic Spot & Basis Data** (`data/spot_basis/spot_basis_{year}.parquet`): Daily spot prices, dominant contract prices, near/dominant basis and basis rates for 21 commodity symbols.
- **China Treasury Yield Curve** (`data/yield_curve/yield_curve_cn.parquet`): Daily treasury yields from 1-month to 30-year maturities (used for bond futures basis/arbitrage research).
- **Global Reference Prices** (`data/global_crude/global_crude.parquet`): Brent and WTI daily prices for global crude market reference.
- **Dominant Contract Mapping** (`data/dominant_contracts/dominant.parquet`): Historical timeline mapping dominant contract IDs to dates.

---

## 2. Curve Arbitrage (Calendar Spread) Methodology

Curve Arbitrage exploits mispricings in the relative value of different contract maturities (e.g., M1, M2, M3) of the same commodity.

### A. Curve Construction
On any trading date $t$, the term structure curve is constructed by plotting the price (or roll yield) of all active contracts against their days-to-maturity (DTM):
$$\text{Slope}_{t} = \frac{P_{\text{far}} - P_{\text{near}}}{\text{DTM}_{\text{far}} - \text{DTM}_{\text{near}}}$$

- **Contango:** Curve is upward sloping ($P_{\text{far}} > P_{\text{near}}$).
- **Backwardation:** Curve is downward sloping ($P_{\text{near}} > P_{\text{far}}$).

### B. Arbitrage Signals & Next Steps
1. **Roll Yield Factor:** Calculate the roll yield for each symbol:
   $$\text{Roll Yield} = \ln\left(\frac{P_{\text{near}}}{P_{\text{far}}}\right) \times \frac{365}{\text{DTM}_{\text{far}} - \text{DTM}_{\text{near}}}$$
   Extreme roll yields signal potential mean-reversion of the curve shape.
2. **Spread Deviation (Z-Score):** Compute the historical z-score of the spread between two specific contracts (e.g., May vs. September contracts: $Spread = P_{\text{May}} - P_{\text{Sep}}$).
   - Enter long spread (Buy May, Sell Sep) when Z-Score is below $-2.0$.
   - Enter short spread (Sell May, Buy Sep) when Z-Score is above $+2.0$.
3. **Seasonality Analysis:** Calendar spreads in commodities (especially agriculture like Corn `C` and Meal `M`) exhibit strong seasonal patterns linked to harvest cycles. We will build historical seasonality profiles to filter arbitrage signals.

---

## 3. Basis (Spot-Futures) Arbitrage Methodology

Basis Arbitrage exploits the difference between physical spot prices and futures prices, utilizing the fact that they must converge at contract maturity.

### A. Basis Definition
$$\text{Basis}_{t} = \text{Spot Price}_{t} - \text{Futures Price}_{t}$$
$$\text{Basis Rate}_{t} = \frac{\text{Basis}_{t}}{\text{Spot Price}_{t}}$$

- **Positive Basis (Backwardation/Underpricing):** Spot price is higher than futures price.
- **Negative Basis (Contango/Overpricing):** Spot price is lower than futures price.

### B. Arbitrage Signals & Next Steps
1. **Convergence Trade:** 
   - **Cash-and-Carry (Reverse Basis):** When the futures price is significantly above the spot price ($\text{Basis Rate} < \text{Threshold}_{\text{negative}}$) plus carry costs (storage, insurance, financing), buy physical spot and sell the futures contract. Deliver the physical goods at maturity to lock in a risk-free return.
   - **Reverse Cash-and-Carry:** When futures price is significantly below spot ($\text{Basis Rate} > \text{Threshold}_{\text{positive}}$), sell physical spot (if inventory is held or shorting is possible) and buy futures.
2. **Basis Mean-Reversion:** In many Chinese commodity markets, physical delivery is restricted to institutional investors or has high transaction barriers. Therefore, most basis arbitrage is run as a **non-delivery mean-reversion trade**:
   - Long basis (Buy Spot, Sell Futures) when basis is historically wide.
   - Close position before maturity when basis converges to its historical mean, avoiding delivery costs.
3. **Treasury Bond Futures Basis (`TF`):**
   - For 5-year Treasury futures, delivery uses a basket of eligible bonds. We will calculate the **Net Basis** and **Implied Repo Rate (IRR)** for each eligible bond:
     $$\text{IRR} = \left(\frac{\text{Futures Price} \times \text{Conversion Factor} + \text{Accrued Interest at Delivery}}{\text{Spot Price of Bond} + \text{Accrued Interest Today}}\right)^{\frac{365}{\text{Days to Delivery}}} - 1$$
   - The bond with the highest IRR is the **Cheapest-to-Deliver (CTD)**. Arbitrage involves buying the CTD bond and selling the `TF` future when the IRR is significantly above the market repo rate.
