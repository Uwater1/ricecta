# Alternative Data Alphas for Futures (Look-Ahead Free)

This document evaluates the effectiveness of alternative macroeconomic factors for the 23 futures underlyings, utilizing a **look-ahead free** alignment methodology (shifting release times by 1 calendar day to prevent intraday look-ahead bias).

## Methodology Update: Look-Ahead Prevention
Previously, macroeconomic factors (such as Social Financing or Money Supply) released by the PBOC or NBS on day $T$ were aligned to trading day $T$. However, many of these indicators are published after market close (e.g. 5:00 PM). Trading them at the 3:00 PM close of day $T$ introduced look-ahead bias. We now shift all macro daily series by 1 calendar day (`.shift(1)`), ensuring they are only traded on day $T+1$ when they are guaranteed to be public.

## Performance Summary Table (5-Day Horizon)

| Rank | Symbol | Best Factor | Signal Type | Spearman Corr (5d) | t-statistic | p-value | Description |
|---|---|---|---|---|---|---|---|
| 1 | **AG** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *diff* | -0.2110 | -7.65 | 4.04e-14 | 光伏玻璃下游 |
| 2 | **TF** | `社会融资规模_当月值` | *level* | -0.2449 | -6.13 | 1.65e-09 | 经济景气度直接影响利率预期 |
| 3 | **SN** | `制造业采购经理指数PMI_进口` | *level* | 0.1667 | 6.06 | 1.83e-09 | 棉花进口景气度 |
| 4 | **CF** | `PMI_生产经营活动预期_全国_当期值_月` | *diff* | -0.1592 | -5.73 | 1.25e-08 | 企业预期 |
| 5 | **Y** | `社会融资规模_当月值` | *diff* | 0.2337 | 5.72 | 1.69e-08 | 信用扩张力度影响债券供给和利率 |
| 6 | **RU** | `PMI_生产经营活动预期_全国_当期值_月` | *level* | -0.1457 | -5.29 | 1.45e-07 | 企业预期 |
| 7 | **V** | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *level* | 0.1375 | 4.98 | 7.07e-07 | 建筑新订单 |
| 8 | **RB** | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *level* | 0.1320 | 4.78 | 1.92e-06 | 建筑新订单 |
| 9 | **SR** | `PPI_食品制造业(全国:当期同比增长率:月)` | *zscore* | -0.1406 | -4.59 | 4.91e-06 | 食品制造出厂价 |
| 10 | **P** | `制造业采购经理指数PMI_进口` | *zscore* | -0.1411 | -4.58 | 5.27e-06 | 棉花进口景气度 |
| 11 | **SA** | `非制造业PMI_建筑业_全国_当期值_月` | *diff* | -0.1260 | -4.51 | 6.95e-06 | 建筑业景气度驱动玻璃需求 |
| 12 | **JD** | `居民食品消费价格指数CPI_(上年=100)_当月` | *diff* | -0.1247 | -4.49 | 7.89e-06 | 食品通胀环境 |
| 13 | **M** | `社会融资规模_当月值` | *level* | 0.1642 | 4.04 | 6.13e-05 | 信用扩张力度影响债券供给和利率 |
| 14 | **AU** | `社会融资规模_当月值` | *zscore* | -0.2145 | -4.03 | 6.84e-05 | 工业品通胀 |
| 15 | **J** | `制造业采购经理指数PMI_原材料库存` | *diff* | 0.1097 | 3.93 | 8.97e-05 | 库存周期 |
| 16 | **SC** | `制造业采购经理指数PMI_进口` | *zscore* | -0.1211 | -3.92 | 9.45e-05 | 棉花进口景气度 |
| 17 | **MA** | `非制造业PMI_建筑业_全国_当期值_月` | *zscore* | -0.1205 | -3.91 | 9.69e-05 | 建筑业景气度驱动玻璃需求 |
| 18 | **TA** | `制造业采购经理指数PMI_新订单` | *zscore* | -0.1198 | -3.88 | 1.13e-04 | 需求端 |
| 19 | **AL** | `制造业采购经理指数PMI_新订单` | *zscore* | -0.1139 | -3.68 | 2.42e-04 | 需求端 |
| 20 | **I** | `制造业采购经理指数PMI_进口` | *diff* | 0.0989 | 3.54 | 4.16e-04 | 棉花进口景气度 |
| 21 | **CU** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *diff* | -0.0944 | -3.36 | 8.06e-04 | 光伏玻璃下游 |
| 22 | **C** | `PMI_生产经营活动预期_全国_当期值_月` | *diff* | -0.0931 | -3.32 | 9.20e-04 | 企业预期 |
| 23 | **NI** | `社会融资规模_当月值` | *diff* | 0.1236 | 2.96 | 3.16e-03 | 信用扩张力度影响债券供给和利率 |

## Long-Term Macroeconomic Effects (30-Day and 40-Day Horizons)
Macroeconomic forces are structural and influence pricing over longer term horizons. Extending the correlation test to 30d and 40d reveals significantly larger correlations and t-statistics across almost all symbols.

### 30-Day Horizon Best Factors

| Rank | Symbol | Best Factor | Signal Type | Spearman Corr (30d) | t-statistic |
|---|---|---|---|---|---|
| 1 | **SN** | `制造业采购经理指数PMI_进口` | *level* | 0.3731 | 14.26 |
| 2 | **AG** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *diff* | -0.3590 | -13.49 |
| 3 | **AL** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *zscore* | -0.5677 | -13.10 |
| 4 | **JD** | `PPI_食品制造业(全国:当期同比增长率:月)` | *zscore* | -0.3562 | -12.18 |
| 5 | **SR** | `PPI_食品制造业(全国:当期同比增长率:月)` | *zscore* | -0.3491 | -11.90 |
| 6 | **TF** | `PMI_生产经营活动预期_全国_当期值_月` | *level* | 0.2936 | 10.92 |
| 7 | **P** | `PPI_食品制造业(全国:当期同比增长率:月)` | *diff* | 0.2804 | 10.33 |
| 8 | **V** | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *level* | 0.2688 | 9.92 |
| 9 | **SA** | `社会融资规模_当月值` | *zscore* | -0.4760 | -9.56 |
| 10 | **J** | `社会融资规模_当月值` | *zscore* | -0.4735 | -9.50 |
| 11 | **Y** | `PPI_食品制造业(全国:当期同比增长率:月)` | *diff* | 0.2337 | 8.50 |
| 12 | **AU** | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | -0.2230 | -8.16 |
| 13 | **SC** | `制造业采购经理指数PMI_进口` | *zscore* | -0.2442 | -7.99 |
| 14 | **M** | `制造业采购经理指数PMI_新订单` | *level* | -0.2169 | -7.88 |
| 15 | **I** | `PPI_全部工业品(全国:当期同比增长率:月)` | *zscore* | -0.2366 | -7.78 |
| 16 | **CF** | `制造业采购经理指数PMI_进口` | *level* | 0.2132 | 7.74 |
| 17 | **MA** | `制造业采购经理指数PMI_原材料库存` | *zscore* | -0.2361 | -7.71 |
| 18 | **RB** | `社会融资规模_当月值` | *zscore* | -0.3939 | -7.57 |
| 19 | **RU** | `社会融资规模_当月值` | *zscore* | -0.3868 | -7.41 |
| 20 | **CU** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *diff* | -0.2063 | -7.39 |
| 21 | **NI** | `PMI_生产经营活动预期_全国_当期值_月` | *zscore* | -0.1768 | -5.72 |
| 22 | **C** | `PPI_食品制造业(全国:当期同比增长率:月)` | *diff* | 0.1428 | 5.10 |
| 23 | **TA** | `PMI_生产经营活动预期_全国_当期值_月` | *zscore* | 0.1394 | 4.48 |

### 40-Day Horizon Best Factors

| Rank | Symbol | Best Factor | Signal Type | Spearman Corr (40d) | t-statistic |
|---|---|---|---|---|---|
| 1 | **AL** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *zscore* | -0.6259 | -15.04 |
| 2 | **AG** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *diff* | -0.3874 | -14.68 |
| 3 | **SN** | `制造业采购经理指数PMI_进口` | *level* | 0.3552 | 13.42 |
| 4 | **SR** | `PPI_食品制造业(全国:当期同比增长率:月)` | *zscore* | -0.3736 | -12.80 |
| 5 | **JD** | `PPI_食品制造业(全国:当期同比增长率:月)` | *zscore* | -0.3728 | -12.77 |
| 6 | **SA** | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *level* | 0.3255 | 12.20 |
| 7 | **TF** | `PMI_生产经营活动预期_全国_当期值_月` | *level* | 0.3253 | 12.19 |
| 8 | **P** | `PPI_食品制造业(全国:当期同比增长率:月)` | *diff* | 0.3242 | 12.07 |
| 9 | **Y** | `PPI_食品制造业(全国:当期同比增长率:月)` | *diff* | 0.2929 | 10.79 |
| 10 | **V** | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *level* | 0.2878 | 10.65 |
| 11 | **AU** | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | -0.2707 | -9.99 |
| 12 | **CF** | `制造业采购经理指数PMI_进口` | *level* | 0.2687 | 9.86 |
| 13 | **J** | `社会融资规模_当月值` | *zscore* | -0.4843 | -9.62 |
| 14 | **C** | `制造业采购经理指数PMI_进口` | *zscore* | 0.2646 | 8.66 |
| 15 | **SC** | `制造业采购经理指数PMI_进口` | *zscore* | -0.2569 | -8.39 |
| 16 | **CU** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *level* | -0.2291 | -8.34 |
| 17 | **MA** | `制造业采购经理指数PMI_原材料库存` | *zscore* | -0.2549 | -8.32 |
| 18 | **I** | `PPI_全部工业品(全国:当期同比增长率:月)` | *zscore* | -0.2513 | -8.25 |
| 19 | **M** | `PPI_食品制造业(全国:当期同比增长率:月)` | *level* | 0.2219 | 8.08 |
| 20 | **RU** | `PMI_生产经营活动预期_全国_当期值_月` | *level* | -0.2133 | -7.74 |
| 21 | **NI** | `PMI_生产经营活动预期_全国_当期值_月` | *zscore* | -0.2259 | -7.35 |
| 22 | **RB** | `社会融资规模_当月值` | *zscore* | -0.3509 | -6.51 |
| 23 | **TA** | `PMI_生产经营活动预期_全国_当期值_月` | *zscore* | 0.1947 | 6.29 |

## Top 3 Alternative Alphas per Symbol (5-Day Horizon)
To allow multiple factor testing, the top 3 alternative factor configurations for each symbol ranked by absolute Spearman t-statistic are listed below. The full configuration files are saved in `data/results/top3_factors_f5_summary.csv`.

| Symbol | Rank | Alternative Factor | Representation | Spearman Corr | t-statistic |
|---|---|---|---|---|---|
| **AG** | 1 | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *diff* | -0.2110 | -7.65 |
| **AG** | 2 | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *zscore* | -0.2560 | -5.20 |
| **AG** | 3 | `社会融资规模_当月值` | *zscore* | -0.2704 | -5.16 |
| **AL** | 1 | `制造业采购经理指数PMI_新订单` | *zscore* | -0.1139 | -3.68 |
| **AL** | 2 | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *level* | -0.0934 | -3.37 |
| **AL** | 3 | `制造业采购经理指数PMI_原材料库存` | *diff* | 0.0908 | 3.25 |
| **AU** | 1 | `社会融资规模_当月值` | *zscore* | -0.2145 | -4.03 |
| **AU** | 2 | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | -0.1014 | -3.67 |
| **AU** | 3 | `社会融资规模_当月值` | *diff* | -0.1480 | -3.56 |
| **C** | 1 | `PMI_生产经营活动预期_全国_当期值_月` | *diff* | -0.0931 | -3.32 |
| **C** | 2 | `制造业采购经理指数PMI_进口` | *diff* | -0.0770 | -2.75 |
| **C** | 3 | `制造业采购经理指数PMI_新订单` | *level* | -0.0573 | -2.05 |
| **CF** | 1 | `PMI_生产经营活动预期_全国_当期值_月` | *diff* | -0.1592 | -5.73 |
| **CF** | 2 | `制造业采购经理指数PMI_新订单` | *zscore* | -0.1337 | -4.33 |
| **CF** | 3 | `制造业采购经理指数PMI_原材料库存` | *zscore* | -0.1190 | -3.85 |
| **CU** | 1 | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *diff* | -0.0944 | -3.36 |
| **CU** | 2 | `PMI_生产经营活动预期_全国_当期值_月` | *level* | -0.0712 | -2.57 |
| **CU** | 3 | `制造业采购经理指数PMI_进口` | *level* | 0.0662 | 2.38 |
| **I** | 1 | `制造业采购经理指数PMI_进口` | *diff* | 0.0989 | 3.54 |
| **I** | 2 | `非制造业PMI_建筑业_全国_当期值_月` | *diff* | -0.0815 | -2.91 |
| **I** | 3 | `PPI_全部工业品(全国:当期同比增长率:月)` | *zscore* | -0.0848 | -2.75 |
| **J** | 1 | `制造业采购经理指数PMI_原材料库存` | *diff* | 0.1097 | 3.93 |
| **J** | 2 | `制造业采购经理指数PMI_原材料库存` | *zscore* | 0.1031 | 3.33 |
| **J** | 3 | `非制造业PMI_建筑业_全国_当期值_月` | *diff* | -0.0902 | -3.22 |
| **JD** | 1 | `居民食品消费价格指数CPI_(上年=100)_当月` | *diff* | -0.1247 | -4.49 |
| **JD** | 2 | `PPI_食品制造业(全国:当期同比增长率:月)` | *zscore* | -0.1209 | -3.94 |
| **JD** | 3 | `PPI_食品制造业(全国:当期同比增长率:月)` | *level* | -0.0577 | -2.08 |
| **M** | 1 | `社会融资规模_当月值` | *level* | 0.1642 | 4.04 |
| **M** | 2 | `PPI_食品制造业(全国:当期同比增长率:月)` | *level* | 0.1040 | 3.76 |
| **M** | 3 | `社会融资规模_当月值` | *diff* | 0.1282 | 3.08 |
| **MA** | 1 | `非制造业PMI_建筑业_全国_当期值_月` | *zscore* | -0.1205 | -3.91 |
| **MA** | 2 | `制造业采购经理指数PMI_新订单` | *zscore* | -0.1166 | -3.77 |
| **MA** | 3 | `非制造业PMI_建筑业_全国_当期值_月` | *diff* | -0.0997 | -3.56 |
| **NI** | 1 | `社会融资规模_当月值` | *diff* | 0.1236 | 2.96 |
| **NI** | 2 | `制造业采购经理指数PMI_原材料库存` | *zscore* | -0.0906 | -2.92 |
| **NI** | 3 | `PMI_生产经营活动预期_全国_当期值_月` | *zscore* | -0.0815 | -2.63 |
| **P** | 1 | `制造业采购经理指数PMI_进口` | *zscore* | -0.1411 | -4.58 |
| **P** | 2 | `社会融资规模_当月值` | *diff* | 0.1838 | 4.45 |
| **P** | 3 | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | 0.1142 | 4.14 |
| **RB** | 1 | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *level* | 0.1320 | 4.78 |
| **RB** | 2 | `非制造业PMI_建筑业_全国_当期值_月` | *diff* | -0.0798 | -2.85 |
| **RB** | 3 | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *zscore* | 0.0716 | 2.31 |
| **RU** | 1 | `PMI_生产经营活动预期_全国_当期值_月` | *level* | -0.1457 | -5.29 |
| **RU** | 2 | `PMI_生产经营活动预期_全国_当期值_月` | *zscore* | -0.1201 | -3.90 |
| **RU** | 3 | `制造业采购经理指数PMI_新订单` | *level* | -0.0926 | -3.33 |
| **SA** | 1 | `非制造业PMI_建筑业_全国_当期值_月` | *diff* | -0.1260 | -4.51 |
| **SA** | 2 | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *level* | 0.1020 | 3.68 |
| **SA** | 3 | `非制造业PMI_建筑业_全国_当期值_月` | *level* | 0.0776 | 2.80 |
| **SC** | 1 | `制造业采购经理指数PMI_进口` | *zscore* | -0.1211 | -3.92 |
| **SC** | 2 | `制造业采购经理指数PMI_新订单` | *zscore* | -0.0526 | -1.69 |
| **SC** | 3 | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | 0.0460 | 1.66 |
| **SN** | 1 | `制造业采购经理指数PMI_进口` | *level* | 0.1667 | 6.06 |
| **SN** | 2 | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *level* | -0.0890 | -3.21 |
| **SN** | 3 | `社会融资规模_当月值` | *zscore* | -0.1603 | -2.98 |
| **SR** | 1 | `PPI_食品制造业(全国:当期同比增长率:月)` | *zscore* | -0.1406 | -4.59 |
| **SR** | 2 | `PPI_食品制造业(全国:当期同比增长率:月)` | *diff* | -0.1069 | -3.84 |
| **SR** | 3 | `居民食品消费价格指数CPI_(上年=100)_当月` | *level* | 0.0819 | 2.96 |
| **TA** | 1 | `制造业采购经理指数PMI_新订单` | *zscore* | -0.1198 | -3.88 |
| **TA** | 2 | `社会融资规模_当月值` | *zscore* | 0.1507 | 2.80 |
| **TA** | 3 | `制造业采购经理指数PMI_新订单` | *diff* | -0.0625 | -2.23 |
| **TF** | 1 | `社会融资规模_当月值` | *level* | -0.2449 | -6.13 |
| **TF** | 2 | `制造业采购经理指数PMI_当月` | *zscore* | 0.1767 | 5.77 |
| **TF** | 3 | `社会融资规模_当月值` | *diff* | -0.2351 | -5.76 |
| **V** | 1 | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *level* | 0.1375 | 4.98 |
| **V** | 2 | `非制造业PMI_建筑业_全国_当期值_月` | *level* | 0.1298 | 4.70 |
| **V** | 3 | `社会融资规模_当月值` | *diff* | 0.1469 | 3.54 |
| **Y** | 1 | `社会融资规模_当月值` | *diff* | 0.2337 | 5.72 |
| **Y** | 2 | `社会融资规模_当月值` | *level* | 0.1883 | 4.65 |
| **Y** | 3 | `制造业采购经理指数PMI_进口` | *zscore* | -0.1250 | -4.05 |

## Commodity Specific Details (Sorted by Significance)

### 1. 品种: AG (SHFE (上期所))

* **Selected Factor**: `PPI_电气机械及器材制造业(全国:当期同比增长率:月)`
* **Signal Representation**: `diff`
* **Description**: 光伏玻璃下游
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.2110`
  * t-statistic: `-7.65`
  * p-value: `4.04e-14`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 2. 品种: TF (CFFEX (中金所))

* **Selected Factor**: `社会融资规模_当月值`
* **Signal Representation**: `level`
* **Description**: 经济景气度直接影响利率预期
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.2449`
  * t-statistic: `-6.13`
  * p-value: `1.65e-09`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 3. 品种: SN (SHFE (上期所))

* **Selected Factor**: `制造业采购经理指数PMI_进口`
* **Signal Representation**: `level`
* **Description**: 棉花进口景气度
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.1667`
  * t-statistic: `6.06`
  * p-value: `1.83e-09`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 4. 品种: CF (CZCE (郑商所))

* **Selected Factor**: `PMI_生产经营活动预期_全国_当期值_月`
* **Signal Representation**: `diff`
* **Description**: 企业预期
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1592`
  * t-statistic: `-5.73`
  * p-value: `1.25e-08`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 5. 品种: Y (DCE (大商所))

* **Selected Factor**: `社会融资规模_当月值`
* **Signal Representation**: `diff`
* **Description**: 信用扩张力度影响债券供给和利率
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.2337`
  * t-statistic: `5.72`
  * p-value: `1.69e-08`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 6. 品种: RU (SHFE (上期所))

* **Selected Factor**: `PMI_生产经营活动预期_全国_当期值_月`
* **Signal Representation**: `level`
* **Description**: 企业预期
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1457`
  * t-statistic: `-5.29`
  * p-value: `1.45e-07`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 7. 品种: V (DCE (大商所))

* **Selected Factor**: `非制造业PMI_建筑业_新订单_全国_当期值_月`
* **Signal Representation**: `level`
* **Description**: 建筑新订单
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.1375`
  * t-statistic: `4.98`
  * p-value: `7.07e-07`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 8. 品种: RB (SHFE (上期所))

* **Selected Factor**: `非制造业PMI_建筑业_新订单_全国_当期值_月`
* **Signal Representation**: `level`
* **Description**: 建筑新订单
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.1320`
  * t-statistic: `4.78`
  * p-value: `1.92e-06`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 9. 品种: SR (CZCE (郑商所))

* **Selected Factor**: `PPI_食品制造业(全国:当期同比增长率:月)`
* **Signal Representation**: `zscore`
* **Description**: 食品制造出厂价
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1406`
  * t-statistic: `-4.59`
  * p-value: `4.91e-06`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 10. 品种: P (DCE (大商所))

* **Selected Factor**: `制造业采购经理指数PMI_进口`
* **Signal Representation**: `zscore`
* **Description**: 棉花进口景气度
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1411`
  * t-statistic: `-4.58`
  * p-value: `5.27e-06`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 11. 品种: SA (CZCE (郑商所))

* **Selected Factor**: `非制造业PMI_建筑业_全国_当期值_月`
* **Signal Representation**: `diff`
* **Description**: 建筑业景气度驱动玻璃需求
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1260`
  * t-statistic: `-4.51`
  * p-value: `6.95e-06`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 12. 品种: JD (DCE (大商所))

* **Selected Factor**: `居民食品消费价格指数CPI_(上年=100)_当月`
* **Signal Representation**: `diff`
* **Description**: 食品通胀环境
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1247`
  * t-statistic: `-4.49`
  * p-value: `7.89e-06`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 13. 品种: M (DCE (大商所))

* **Selected Factor**: `社会融资规模_当月值`
* **Signal Representation**: `level`
* **Description**: 信用扩张力度影响债券供给和利率
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.1642`
  * t-statistic: `4.04`
  * p-value: `6.13e-05`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 14. 品种: AU (SHFE (上期所))

* **Selected Factor**: `社会融资规模_当月值`
* **Signal Representation**: `zscore`
* **Description**: 工业品通胀
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.2145`
  * t-statistic: `-4.03`
  * p-value: `6.84e-05`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 15. 品种: J (DCE (大商所))

* **Selected Factor**: `制造业采购经理指数PMI_原材料库存`
* **Signal Representation**: `diff`
* **Description**: 库存周期
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.1097`
  * t-statistic: `3.93`
  * p-value: `8.97e-05`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 16. 品种: SC (INE (能源中心))

* **Selected Factor**: `制造业采购经理指数PMI_进口`
* **Signal Representation**: `zscore`
* **Description**: 棉花进口景气度
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1211`
  * t-statistic: `-3.92`
  * p-value: `9.45e-05`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 17. 品种: MA (CZCE (郑商所))

* **Selected Factor**: `非制造业PMI_建筑业_全国_当期值_月`
* **Signal Representation**: `zscore`
* **Description**: 建筑业景气度驱动玻璃需求
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1205`
  * t-statistic: `-3.91`
  * p-value: `9.69e-05`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 18. 品种: TA (CZCE (郑商所))

* **Selected Factor**: `制造业采购经理指数PMI_新订单`
* **Signal Representation**: `zscore`
* **Description**: 需求端
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1198`
  * t-statistic: `-3.88`
  * p-value: `1.13e-04`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 19. 品种: AL (SHFE (上期所))

* **Selected Factor**: `制造业采购经理指数PMI_新订单`
* **Signal Representation**: `zscore`
* **Description**: 需求端
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1139`
  * t-statistic: `-3.68`
  * p-value: `2.42e-04`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 20. 品种: I (DCE (大商所))

* **Selected Factor**: `制造业采购经理指数PMI_进口`
* **Signal Representation**: `diff`
* **Description**: 棉花进口景气度
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.0989`
  * t-statistic: `3.54`
  * p-value: `4.16e-04`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 21. 品种: CU (SHFE (上期所))

* **Selected Factor**: `PPI_电气机械及器材制造业(全国:当期同比增长率:月)`
* **Signal Representation**: `diff`
* **Description**: 光伏玻璃下游
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.0944`
  * t-statistic: `-3.36`
  * p-value: `8.06e-04`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 22. 品种: C (DCE (大商所))

* **Selected Factor**: `PMI_生产经营活动预期_全国_当期值_月`
* **Signal Representation**: `diff`
* **Description**: 企业预期
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.0931`
  * t-statistic: `-3.32`
  * p-value: `9.20e-04`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 23. 品种: NI (SHFE (上期所))

* **Selected Factor**: `社会融资规模_当月值`
* **Signal Representation**: `diff`
* **Description**: 信用扩张力度影响债券供给和利率
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.1236`
  * t-statistic: `2.96`
  * p-value: `3.16e-03`
  * Correlation Sign: `Positive (Long when factor increases)`

---
