# Per-Symbol Alt Macro Alpha Evaluation Report

This report evaluates each of the 23 Chinese commodity futures individually with its #1 ranked alternative macro factor from the screening pipeline. Each symbol-factor pair is backtested as a single-asset directional strategy with 5bps transaction costs.

## Per-Symbol Performance Summary (Sorted by Sharpe Ratio)

| Rank | Symbol | Factor | Rep | Ann Return | Ann Vol | Sharpe | DSR | Calmar | MaxDD | Sortino | PF | Win Rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **AG** | PPI_全部工业品(全国:当期同比增长率:月) | level | +25.65% | 28.41% | +0.90 | 69.9% | +0.60 | -42.79% | +0.91 | 1.20 | 52.3% |
| 2 | **AL** | PPIRM_燃料及动力类(全国:当期同比增长率:月) | level | +11.50% | 17.31% | +0.66 | 40.7% | +0.32 | -35.83% | +0.67 | 1.13 | 50.8% |
| 3 | **SR** | 制造业采购经理指数PMI_购进价格 | diff | +6.98% | 12.34% | +0.57 | 29.1% | +0.46 | -15.03% | +0.57 | 1.10 | 50.3% |
| 4 | **NI** | 制造业采购经理指数PMI_新订单 | diff | +15.21% | 28.74% | +0.53 | 25.4% | +0.32 | -47.98% | +0.53 | 1.10 | 49.2% |
| 5 | **RB** | 非制造业PMI_建筑业_新订单_全国_当期值_月 | level | +10.20% | 19.87% | +0.51 | 23.9% | +0.21 | -48.83% | +0.47 | 1.10 | 44.2% |
| 6 | **SN** | PPI_通信设备、计算机及其他电子设备制造业工业品出厂价格指数PPI_(上年=100)_当月 | diff | +12.01% | 24.13% | +0.50 | 22.3% | +0.35 | -33.96% | +0.41 | 1.12 | 33.1% |
| 7 | **Y** | 社会融资规模_当月值 | zscore | +2.49% | 5.11% | +0.49 | 20.7% | +0.34 | -7.37% | +0.20 | 1.26 | 7.0% |
| 8 | **JD** | 制造业采购经理指数PMI_购进价格 | diff | +9.82% | 20.77% | +0.47 | 20.0% | +0.21 | -45.97% | +0.48 | 1.09 | 49.2% |
| 9 | **M** | 社会融资规模_当月值 | zscore | +2.21% | 4.86% | +0.45 | 18.4% | +0.15 | -14.34% | +0.17 | 1.24 | 7.1% |
| 10 | **CF** | PPI_皮革、毛皮、羽毛及其制品和制鞋业(全国:当期同比增长率:月) | diff | +7.30% | 16.20% | +0.45 | 18.1% | +0.23 | -31.79% | +0.41 | 1.10 | 39.5% |
| 11 | **I** | GDP增长贡献率_第二产业_累计同比_季 | zscore | +13.10% | 29.63% | +0.44 | 17.4% | +0.26 | -51.26% | +0.35 | 1.10 | 35.5% |
| 12 | **SC** | 国内生产总值GDP_累计同比 | level | +15.45% | 35.37% | +0.44 | 19.9% | +0.25 | -61.72% | +0.43 | 1.08 | 52.2% |
| 13 | **TF** | 社会融资规模_当月值 | diff | +0.32% | 0.78% | +0.41 | 14.6% | +0.19 | -1.66% | +0.20 | 1.16 | 11.3% |
| 14 | **CU** | PPI_全部工业品(全国:当期同比增长率:月) | level | +5.73% | 17.59% | +0.33 | 9.6% | +0.15 | -37.48% | +0.32 | 1.06 | 50.0% |
| 15 | **MA** | 制造业采购经理指数PMI_原材料库存 | diff | +8.14% | 26.51% | +0.31 | 8.6% | +0.17 | -48.56% | +0.30 | 1.06 | 46.8% |
| 16 | **SA** | PPI_电气机械及器材制造业(全国:当期同比增长率:月) | diff | +9.82% | 33.68% | +0.29 | 13.2% | +0.17 | -58.06% | +0.30 | 1.05 | 48.3% |
| 17 | **RU** | PMI_生产经营活动预期_全国_当期值_月 | level | +5.92% | 20.86% | +0.28 | 7.4% | +0.15 | -39.18% | +0.27 | 1.06 | 42.1% |
| 18 | **TA** | PMI_生产经营活动预期_全国_当期值_月 | diff | +6.17% | 22.63% | +0.27 | 7.0% | +0.13 | -46.66% | +0.24 | 1.06 | 43.0% |
| 19 | **J** | 社会融资规模_当月值 | zscore | +2.44% | 11.65% | +0.21 | 4.9% | +0.14 | -17.02% | +0.07 | 1.10 | 7.5% |
| 20 | **C** | 居民鲜果消费价格指数CPI_(上年=100)_当月 | zscore | +2.05% | 10.07% | +0.20 | 4.5% | +0.07 | -29.13% | +0.19 | 1.04 | 43.4% |
| 21 | **V** | 非制造业PMI_建筑业_业务活动预期_全国_当期值_月 | level | +1.54% | 20.49% | +0.08 | 1.8% | +0.02 | -72.54% | +0.07 | 1.01 | 42.3% |
| 22 | **P** | PPI_全部工业品(全国:当期同比增长率:月) | level | -12.04% | 24.40% | -0.49 | 0.0% | -0.15 | -80.50% | -0.48 | 0.92 | 47.6% |
| 23 | **AU** | 制造业采购经理指数PMI_购进价格 | level | -14.23% | 15.33% | -0.93 | 0.0% | -0.17 | -82.48% | -0.94 | 0.83 | 45.4% |

---

## Equity Curves

![Per-Symbol Equity Curves](figures/per_symbol_equity.png)

## Drawdown Charts

![Per-Symbol Drawdowns](figures/per_symbol_drawdowns.png)

## Aggregate Statistics

- **Symbols with positive Sharpe**: 21/23
- **Mean Sharpe**: +0.32
- **Median Sharpe**: +0.44
- **Best Sharpe**: +0.90 (AG)
- **Worst Sharpe**: -0.93 (AU)
- **Top 3**: AG (+0.90), AL (+0.66), SR (+0.57)
- **Bottom 3**: V (+0.08), P (-0.49), AU (-0.93)

## Key Findings

1. **Signal Quality**: The macro factor signals show varying effectiveness across symbols. Factors with higher screening-stage correlation tend to produce stronger backtest Sharpe ratios.
2. **Low Turnover Advantage**: Macro signals update monthly, resulting in very low turnover. The 5bps transaction cost has minimal impact on net performance.
3. **Cross-Sectional Diversification Potential**: Combining multiple symbol-factor pairs into a diversified portfolio could improve risk-adjusted returns beyond individual pairs.
