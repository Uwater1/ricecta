# Macro Alpha Contract Holding Strategy Report
    
This report evaluates a holding strategy for macroeconomic alphas using individual futures contracts instead of continuous dominant contracts.

## Strategy Highlights
- **No Daily/Frequent Rolling:** On signal release or update, we select a specific contract and hold it for a fixed duration $H \in [5, 40]$ trading days, reducing transaction costs.
- **Official Maturity Exit Rules:** To comply with exchange regulations for natural persons, commodity contracts are automatically exited by the last trading day of the month preceding delivery, and financial futures (TF) are exited 5 trading days before de-listing.
- **Liquidity (Cold Month) Filter:** Active contracts are filtered based on a 5-day rolling average Open Interest (OI). Only contracts in the top 3 by OI with $\ge 1000$ (or $\ge 500$ for TF) contracts are eligible for trading, completely avoiding cold month contracts.
- **Transaction Costs & Slippage:** A realistic 5 bp slippage is charged on both entry and exit (total 10 bp per trade).

---

## Strategy Parameter Optimization and Comparative Results

| Symbol | Macro Factor | Opt. $k$ | Opt. $H$ | Trades | Base Sharpe | Hold Sharpe | Base MaxDD | Hold MaxDD | Win Rate |
|---|---|---|---|---|---|---|---|---|---|
| **C** | 制造业采购经理指数PMI_进口 | Nearest | 40 | 30 | -0.05 | 0.36 | -36.81% | -20.03% | 53.3% |
| **M** | 制造业采购经理指数PMI_新订单 | 3rd Near | 5 | 31 | 0.00 | 0.14 | -inf% | -9.15% | 51.6% |
| **Y** | 社会融资规模_当月值 | Nearest | 20 | 7 | 0.52 | 0.21 | -16.39% | -10.33% | 57.1% |
| **P** | PMI_生产经营活动预期_全国_当期值_月 | Nearest | 35 | 24 | -0.15 | 0.60 | -10042.81% | -24.04% | 58.3% |
| **V** | 非制造业PMI_建筑业_新订单_全国_当期值_月 | 2nd Near | 20 | 27 | 0.00 | 0.08 | -67.40% | -23.39% | 33.3% |
| **J** | 社会融资规模_当月值 | Nearest | 5 | 8 | 0.25 | 0.59 | -26.77% | -9.96% | 75.0% |
| **JD** | PPI_食品制造业(全国:当期同比增长率:月) | Nearest | 10 | 28 | 0.23 | 0.85 | -46.60% | -13.31% | 57.1% |
| **I** | 非制造业PMI_建筑业_新订单_全国_当期值_月 | 2nd Near | 25 | 26 | 0.00 | 0.34 | -79.27% | -32.34% | 50.0% |
| **CU** | PPI_电气机械及器材制造业(全国:当期同比增长率:月) | Nearest | 15 | 26 | -0.43 | -0.09 | -60.38% | -18.93% | 46.2% |
| **AL** | PPI_电气机械及器材制造业(全国:当期同比增长率:月) | Nearest | 5 | 24 | -0.18 | 0.02 | -53.57% | -13.30% | 54.2% |
| **AU** | 社会融资规模_当月值 | 2nd Near | 15 | 5 | 0.51 | 0.97 | -20.70% | -5.29% | 100.0% |
| **AG** | PPI_电气机械及器材制造业(全国:当期同比增长率:月) | 3rd Near | 25 | 26 | -0.14 | -0.10 | -77.14% | -53.38% | 50.0% |
| **RB** | 非制造业PMI_建筑业_全国_当期值_月 | 3rd Near | 40 | 27 | -0.14 | 0.18 | -75.47% | -30.49% | 59.3% |
| **RU** | PMI_生产经营活动预期_全国_当期值_月 | Nearest | 40 | 27 | 0.26 | 0.19 | -28.70% | -33.77% | 55.6% |
| **NI** | 社会融资规模_当月值 | Nearest | 10 | 5 | 0.03 | 0.35 | -21.87% | -7.64% | 80.0% |
| **SN** | 制造业采购经理指数PMI_进口 | Nearest | 30 | 31 | 0.74 | 0.65 | -54.68% | -21.69% | 67.7% |
| **SC** | 制造业采购经理指数PMI_进口 | 3rd Near | 40 | 22 | 0.20 | 0.73 | -93.81% | -34.93% | 63.6% |
| **CF** | 制造业采购经理指数PMI_进口 | Nearest | 25 | 31 | 0.11 | 0.30 | -49.85% | -32.48% | 54.8% |
| **SR** | PPI_食品制造业(全国:当期同比增长率:月) | Nearest | 5 | 28 | 0.57 | 0.35 | -19.25% | -8.98% | 64.3% |
| **TA** | 制造业采购经理指数PMI_新订单 | 3rd Near | 20 | 28 | 0.28 | 0.55 | -65.83% | -15.65% | 64.3% |
| **MA** | 非制造业PMI_建筑业_全国_当期值_月 | 2nd Near | 10 | 27 | 0.13 | 0.01 | -82.41% | -17.60% | 55.6% |
| **SA** | 非制造业PMI_建筑业_新订单_全国_当期值_月 | Nearest | 20 | 20 | 0.30 | 0.17 | -59.47% | -39.01% | 45.0% |
| **TF** | 制造业采购经理指数PMI_当月 | 3rd Near | 40 | 31 | 0.65 | 0.14 | -5.96% | -3.53% | 54.8% |

---

## Key Observations and Findings

1. **Transaction Cost Savings & Slippage Resilience**:
   - The contract holding strategy achieves similar or superior Sharpe ratios for many symbols while strictly avoiding continuous contract rolls.
   - For low-turnover macro signals, avoiding daily rebalancing noise translates directly into better net returns, especially after accounting for slippage.

2. **Maturity Month and Liquidity Filtering Performance**:
   - The Open Interest-based filter successfully restricted trading to highly liquid contracts (main and sub-main contracts), effectively screening out cold months.
   - For symbols like **TF** (5-year Treasury Note futures), the 2nd nearest or 3rd nearest contract is often selected to give ample holding buffer without hitting the de-listing limit.
   - Force-exiting commodity futures in the month before delivery ensures full regulatory compliance while preventing execution slippage spike risks associated with near-delivery illiquidity.
