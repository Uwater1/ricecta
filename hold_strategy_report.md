# Macro Alpha Contract Holding Strategy Report
    
This report evaluates a holding strategy for macroeconomic alphas using individual futures contracts instead of continuous dominant contracts.

## Strategy Highlights
- **No Daily/Frequent Rolling:** On signal release or update, we select a specific contract and hold it for a fixed duration $H \in [5, 40]$ trading days, reducing transaction costs.
- **Official Maturity Exit Rules:** To comply with exchange regulations for natural persons, commodity contracts are automatically exited by the last trading day of the month preceding delivery, and financial futures (TF) are exited 5 trading days before de-listing.
- **Liquidity (Cold Month) Filter:** Active contracts are filtered by relative Open Interest (OI) ranking. The top 3 contracts by 5-day rolling OI are selected per entry date, naturally screening out cold-month contracts regardless of absolute OI levels.
- **Data-Driven Entry Dates:** Entry trades are triggered on dominant contract switch dates detected from actual dominant contract mapping data, adapting automatically to each symbol's contract cycle (monthly for SHFE metals, quarterly for TF, 1/5/9 for most DCE/CZCE grains, etc.).
- **Transaction Costs & Slippage:** A realistic 5 bp slippage is charged on both entry and exit (total 10 bp per trade).

---

## Strategy Parameter Optimization and Comparative Results

| Symbol | Macro Factor | Opt. $k$ | Opt. $H$ | Trades | Base Sharpe | Hold Sharpe | Base MaxDD | Hold MaxDD | Win Rate |
|---|---|---|---|---|---|---|---|---|---|
| **C** | 制造业采购经理指数PMI_进口 | Nearest | 25 | 23 | -0.05 | 0.02 | -36.81% | -10.32% | 52.2% |
| **M** | 制造业采购经理指数PMI_新订单 | 3rd Near | 40 | 16 | 0.00 | -0.05 | -inf% | -25.84% | 56.2% |
| **Y** | 社会融资规模_当月值 | Nearest | 15 | 7 | 0.52 | 0.49 | -16.39% | -4.26% | 100.0% |
| **P** | PMI_生产经营活动预期_全国_当期值_月 | 2nd Near | 35 | 16 | -0.15 | 0.75 | -10042.81% | -21.91% | 62.5% |
| **V** | 非制造业PMI_建筑业_新订单_全国_当期值_月 | Nearest | 5 | 16 | 0.00 | 0.52 | -67.40% | -7.41% | 62.5% |
| **J** | 社会融资规模_当月值 | 2nd Near | 20 | 8 | 0.25 | 0.45 | -26.77% | -8.11% | 87.5% |
| **JD** | PPI_食品制造业(全国:当期同比增长率:月) | 2nd Near | 30 | 33 | 0.23 | 0.54 | -46.60% | -35.19% | 69.7% |
| **I** | 非制造业PMI_建筑业_新订单_全国_当期值_月 | 3rd Near | 5 | 14 | 0.00 | 0.27 | -79.27% | -11.63% | 57.1% |
| **CU** | PPI_电气机械及器材制造业(全国:当期同比增长率:月) | 3rd Near | 20 | 64 | -0.43 | -0.08 | -60.38% | -42.83% | 46.9% |
| **AL** | PPI_电气机械及器材制造业(全国:当期同比增长率:月) | 3rd Near | 15 | 32 | -0.09 | 0.06 | -52.08% | -33.81% | 46.9% |
| **AU** | 社会融资规模_当月值 | Nearest | 10 | 9 | 0.51 | 0.71 | -20.70% | -9.84% | 88.9% |
| **AG** | PPI_电气机械及器材制造业(全国:当期同比增长率:月) | 3rd Near | 25 | 23 | -0.14 | 0.35 | -77.14% | -45.95% | 56.5% |
| **RB** | 非制造业PMI_建筑业_全国_当期值_月 | Nearest | 20 | 16 | -0.14 | 0.69 | -75.47% | -10.85% | 62.5% |
| **RU** | PMI_生产经营活动预期_全国_当期值_月 | 3rd Near | 15 | 16 | 0.26 | 0.34 | -28.70% | -18.42% | 50.0% |
| **NI** | 社会融资规模_当月值 | 2nd Near | 5 | 15 | 0.03 | 0.31 | -21.87% | -6.11% | 60.0% |
| **SN** | 制造业采购经理指数PMI_进口 | 2nd Near | 35 | 63 | 0.74 | 0.58 | -54.68% | -53.79% | 61.9% |
| **SC** | 制造业采购经理指数PMI_进口 | 3rd Near | 20 | 65 | 0.20 | 0.54 | -93.81% | -37.86% | 56.9% |
| **CF** | 制造业采购经理指数PMI_进口 | Nearest | 30 | 16 | 0.11 | 0.69 | -49.85% | -12.60% | 75.0% |
| **SR** | PPI_食品制造业(全国:当期同比增长率:月) | Nearest | 25 | 18 | 0.57 | 0.61 | -19.25% | -11.74% | 66.7% |
| **TA** | 制造业采购经理指数PMI_新订单 | 3rd Near | 40 | 16 | 0.28 | 0.31 | -65.83% | -25.44% | 56.2% |
| **MA** | 非制造业PMI_建筑业_全国_当期值_月 | Nearest | 20 | 16 | 0.13 | 0.34 | -82.41% | -15.52% | 62.5% |
| **SA** | 非制造业PMI_建筑业_新订单_全国_当期值_月 | 2nd Near | 30 | 16 | 0.30 | 0.43 | -59.47% | -32.96% | 56.2% |
| **TF** | 制造业采购经理指数PMI_当月 | 3rd Near | 40 | 22 | 0.65 | 0.47 | -5.96% | -1.29% | 68.2% |

---

## Key Observations and Findings

1. **Transaction Cost Savings & Slippage Resilience**:
   - The contract holding strategy achieves similar or superior Sharpe ratios for many symbols while strictly avoiding continuous contract rolls.
   - For low-turnover macro signals, avoiding daily rebalancing noise translates directly into better net returns, especially after accounting for slippage.

2. **Maturity Month and Liquidity Filtering Performance**:
   - The Open Interest-based filter successfully restricted trading to highly liquid contracts (main and sub-main contracts), effectively screening out cold months.
   - For symbols like **TF** (5-year Treasury Note futures), the 2nd nearest or 3rd nearest contract is often selected to give ample holding buffer without hitting the de-listing limit.
   - Force-exiting commodity futures in the month before delivery ensures full regulatory compliance while preventing execution slippage spike risks associated with near-delivery illiquidity.
