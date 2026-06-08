# Alternative Data Alphas for Futures (Contract-Switch Horizons)

This document evaluates the effectiveness of alternative macroeconomic factors for the 23 futures underlyings, utilizing a **look-ahead free** alignment methodology (shifting release times by 1 calendar day to prevent intraday look-ahead bias).

## Methodology: Mixed Horizons

Forward return horizons combine **fixed calendar windows** (short-term) with **data-driven contract-switch horizons** (medium to long-term):

- **5-Day**: Fixed 5-trading-day forward return (short-term price reaction / momentum)
- **20-Day**: Fixed 20-trading-day forward return (medium-term price adjustment)
- **H1 (1st Switch)**: Forward return to the next dominant contract switch date
- **H2 (2nd Switch)**: Forward return to the 2nd next dominant contract switch date
- **H3 (3rd Switch)**: Forward return to the 3rd next dominant contract switch date

Contract-switch horizons adapt automatically to each symbol's contract cycle:

| Symbol Group | Median H1 | Median H2 | Median H3 |
|---|---|---|---|
| SHFE metals | ~25d | ~45d | ~69d |
| SHFE precious | ~93d | ~196d | ~274d |
| SHFE black | ~85d | ~172d | ~262d |
| DCE | ~79d | ~165d | ~271d |
| CZCE | ~78d | ~163d | ~276d |
| INE | ~15d | ~35d | ~55d |
| CFFEX | ~58d | ~120d | ~183d |

## Look-Ahead Prevention

Macroeconomic factors released by the PBOC or NBS on day $T$ are shifted by 1 calendar day (`.shift(1)`), ensuring they are only traded on day $T+1$ when guaranteed to be public.

## Performance Summary Table (20-Day Horizon) — PRIMARY

| Rank | Symbol | Best Factor | Signal Type | Spearman Corr | t-statistic | p-value |
|---|---|---|---|---|---|---|
| 1 | **AG** | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | -0.2795 | -14.56 | 3.52e-46 |
| 2 | **AU** | `制造业采购经理指数PMI_购进价格` | *level* | -0.2566 | -13.24 | 1.01e-38 |
| 3 | **RU** | `PPI_橡胶和塑料制品业(全国:当期同比增长率:月)` | *level* | -0.2542 | -13.15 | 3.09e-38 |
| 4 | **TF** | `居民消费价格指数CPI_当月同比(上年同月=100)` | *zscore* | 0.2632 | 12.95 | 4.95e-37 |
| 5 | **SN** | `PPI_计算机、通信和其他电子设备制造业(全国:当期同比增长率:月)` | *diff* | 0.2456 | 12.62 | 2.05e-35 |
| 6 | **V** | `非制造业PMI_建筑业_业务活动预期_全国_当期值_月` | *level* | 0.2585 | 12.46 | 1.87e-34 |
| 7 | **SR** | `制造业采购经理指数PMI_购进价格` | *diff* | 0.2363 | 12.13 | 6.18e-33 |
| 8 | **RB** | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *level* | 0.2460 | 11.82 | 2.80e-31 |
| 9 | **P** | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | 0.2206 | 11.31 | 5.66e-29 |
| 10 | **AL** | `PPIRM_燃料及动力类(全国:当期同比增长率:月)` | *level* | -0.2027 | -10.36 | 1.22e-24 |
| 11 | **JD** | `制造业采购经理指数PMI_购进价格` | *diff* | 0.1946 | 9.89 | 1.15e-22 |
| 12 | **C** | `CPI_翘尾因素_当月` | *diff* | -0.2276 | -9.09 | 3.01e-19 |
| 13 | **NI** | `制造业采购经理指数PMI_购进价格` | *zscore* | -0.1871 | -9.01 | 4.40e-19 |
| 14 | **J** | `非制造业PMI_建筑业_业务活动预期_全国_当期值_月` | *level* | 0.1876 | 8.89 | 1.22e-18 |
| 15 | **CU** | `PPI_通用设备制造业(全国:当期同比增长率:月)` | *level* | -0.1721 | -8.74 | 4.10e-18 |
| 16 | **CF** | `PPI_纺织业(全国:当期同比增长率:月)` | *level* | -0.1703 | -8.64 | 9.45e-18 |
| 17 | **SC** | `PPI_煤炭开采和洗选业(全国:当期同比增长率:月)` | *zscore* | 0.1953 | 8.22 | 4.01e-16 |
| 18 | **Y** | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | -0.1462 | -7.39 | 1.94e-13 |
| 19 | **SA** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *zscore* | 0.2764 | 7.29 | 9.29e-13 |
| 20 | **I** | `非制造业PMI_建筑业_全国_当期值_月` | *level* | -0.1538 | -7.25 | 5.94e-13 |
| 21 | **M** | `PPI_农副食品加工业(全国:当期同比增长率:月)` | *zscore* | -0.1193 | -5.70 | 1.34e-08 |
| 22 | **TA** | `PMI_生产经营活动预期_全国_当期值_月` | *level* | 0.1203 | 5.65 | 1.82e-08 |
| 23 | **MA** | `PPI_化学纤维制造业(全国:当期同比增长率:月)` | *zscore* | 0.0977 | 4.66 | 3.35e-06 |

## Performance Summary Table (5-Day Horizon)

| Rank | Symbol | Best Factor | Signal Type | Spearman Corr (5d) | t-statistic | p-value |
|---|---|---|---|---|---|---|
| 1 | **AG** | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | -0.1488 | -7.55 | 6.12e-14 |
| 2 | **P** | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | 0.1358 | 6.88 | 7.52e-12 |
| 3 | **RB** | `PPIRM_黑色金属材料类(全国:当期同比增长率:月)` | *level* | 0.1349 | 6.83 | 1.05e-11 |
| 4 | **V** | `非制造业PMI_建筑业_业务活动预期_全国_当期值_月` | *level* | 0.1412 | 6.66 | 3.38e-11 |
| 5 | **TF** | `社会融资规模_当月值` | *level* | -0.2436 | -6.10 | 1.90e-09 |
| 6 | **JD** | `制造业采购经理指数PMI_购进价格` | *diff* | 0.1198 | 6.04 | 1.82e-09 |
| 7 | **AU** | `制造业采购经理指数PMI_购进价格` | *level* | -0.1187 | -5.98 | 2.57e-09 |
| 8 | **RU** | `PPI_橡胶和塑料制品业(全国:当期同比增长率:月)` | *level* | -0.1177 | -5.95 | 3.09e-09 |
| 9 | **J** | `制造业采购经理指数PMI_原材料库存` | *level* | 0.1171 | 5.90 | 4.20e-09 |
| 10 | **Y** | `社会融资规模_当月值` | *diff* | 0.2360 | 5.79 | 1.15e-08 |
| 11 | **SN** | `PPI_通信设备、计算机及其他电子设备制造业工业品出厂价格指数PPI_(上年=100)_当月` | *diff* | 0.1349 | 5.62 | 2.23e-08 |
| 12 | **AL** | `PPIRM_燃料及动力类(全国:当期同比增长率:月)` | *level* | -0.1080 | -5.45 | 5.47e-08 |
| 13 | **SR** | `制造业采购经理指数PMI_购进价格` | *diff* | 0.1036 | 5.21 | 2.04e-07 |
| 14 | **SA** | `PPIRM_建筑材料类(全国:当期同比增长率:月)` | *diff* | -0.1249 | -4.98 | 7.23e-07 |
| 15 | **CU** | `PPI_通用设备制造业(全国:当期同比增长率:月)` | *level* | -0.0977 | -4.93 | 8.87e-07 |
| 16 | **NI** | `制造业采购经理指数PMI_购进价格` | *zscore* | -0.0913 | -4.35 | 1.43e-05 |
| 17 | **SC** | `CPI-PPI_差值_当月` | *level* | -0.1058 | -4.18 | 3.14e-05 |
| 18 | **C** | `居民鲜果消费价格指数CPI_(上年=100)_当月` | *level* | -0.0829 | -4.17 | 3.12e-05 |
| 19 | **M** | `社会融资规模_当月值` | *level* | 0.1687 | 4.16 | 3.70e-05 |
| 20 | **CF** | `居民衣着消费价格指数CPI_(上年=100)_当月` | *diff* | 0.0821 | 4.12 | 3.99e-05 |
| 21 | **I** | `非制造业PMI_建筑业_全国_当期值_月` | *level* | -0.0820 | -3.84 | 1.24e-04 |
| 22 | **TA** | `制造业采购经理指数PMI_原材料库存` | *level* | 0.0649 | 3.25 | 1.15e-03 |
| 23 | **MA** | `制造业采购经理指数PMI_原材料库存` | *diff* | 0.0541 | 2.71 | 6.81e-03 |

## Long-Term Macroeconomic Effects (Contract-Switch Horizons)

Macroeconomic forces are structural and influence pricing over contract-cycle horizons. The contract-switch horizons (H1, H2, H3) capture these effects aligned to each symbol's natural dominant contract transition pattern.

### 1st Switch Horizon Best Factors

| Rank | Symbol | Best Factor | Signal Type | Spearman Corr | t-statistic |
|---|---|---|---|---|---|
| 1 | **TF** | `贷款加权平均利率_非金融企业及其他部门_票据融资_人民币` | *level* | 0.7341 | 53.74 |
| 2 | **SN** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *level* | -0.6877 | -43.56 |
| 3 | **CU** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *level* | -0.6376 | -38.04 |
| 4 | **AG** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *diff* | -0.6228 | -36.75 |
| 5 | **RB** | `PPI_非金属矿物制品业(全国:当期同比增长率:月)` | *level* | 0.5830 | 35.63 |
| 6 | **V** | `非制造业PMI_建筑业_全国_当期值_月` | *level* | 0.6034 | 34.98 |
| 7 | **AL** | `PPI_有色金属矿采选业(全国:当期同比增长率:月)` | *level* | -0.5772 | -34.96 |
| 8 | **J** | `PPIRM_黑色金属材料类(全国:当期同比增长率:月)` | *level* | 0.5666 | 34.23 |
| 9 | **AU** | `国内生产总值GDP_累计同比` | *level* | 0.5387 | 31.83 |
| 10 | **RU** | `制造业采购经理指数PMI_新出口订单` | *level* | -0.5013 | -28.65 |
| 11 | **NI** | `国内生产总值GDP_累计同比` | *level* | 0.4893 | 27.77 |
| 12 | **CF** | `PPIRM_纺织原料类(全国:当期同比增长率:月)` | *level* | -0.4775 | -27.00 |
| 13 | **C** | `居民食品消费价格指数CPI_(上年=100)_当月` | *level* | 0.4770 | 26.94 |
| 14 | **MA** | `PPI_石油加工、炼焦及核燃料加工业(全国:当期同比增长率:月)` | *level* | -0.4643 | -26.07 |
| 15 | **Y** | `居民食品消费价格指数CPI_(上年=100)_当月` | *level* | 0.4533 | 25.26 |
| 16 | **I** | `GDP增长贡献率_第二产业_累计同比_季` | *level* | 0.4535 | 25.20 |
| 17 | **M** | `制造业采购经理指数PMI_生产` | *level* | 0.4527 | 25.13 |
| 18 | **SR** | `PPI_酒、饮料和精制茶制造业(全国:当期同比增长率:月)` | *level* | 0.4350 | 23.97 |
| 19 | **P** | `制造业采购经理指数PMI_新订单` | *level* | -0.4295 | -23.53 |
| 20 | **TA** | `PPI_纺织服装、服饰业(全国:当期同比增长率:月)` | *level* | -0.3819 | -20.55 |
| 21 | **JD** | `PPI_农副食品加工业(全国:当期同比增长率:月)` | *zscore* | -0.3925 | -20.11 |
| 22 | **SC** | `PPIRM_化工原料类(全国:当期同比增长率:月)` | *zscore* | 0.3918 | 17.27 |
| 23 | **SA** | `非制造业PMI_建筑业_业务活动预期_全国_当期值_月` | *level* | 0.3893 | 16.42 |

### 2nd Switch Horizon Best Factors

| Rank | Symbol | Best Factor | Signal Type | Spearman Corr | t-statistic |
|---|---|---|---|---|---|
| 1 | **TF** | `贷款加权平均利率_非金融企业及其他部门_票据融资_人民币` | *level* | 0.8006 | 65.91 |
| 2 | **SN** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *level* | -0.7326 | -50.02 |
| 3 | **AG** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *zscore* | -0.7349 | -46.92 |
| 4 | **CU** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *level* | -0.6867 | -43.86 |
| 5 | **AL** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *level* | -0.6856 | -43.70 |
| 6 | **MA** | `PPI_化学纤维制造业(全国:当期同比增长率:月)` | *level* | -0.6302 | -39.84 |
| 7 | **J** | `PPIRM_黑色金属材料类(全国:当期同比增长率:月)` | *level* | 0.6076 | 37.58 |
| 8 | **NI** | `国内生产总值GDP_累计同比` | *level* | 0.5630 | 33.96 |
| 9 | **RB** | `GDP增长贡献率_第二产业_累计同比_季` | *level* | -0.5472 | -31.94 |
| 10 | **V** | `非制造业PMI_建筑业_全国_当期值_月` | *level* | 0.5736 | 31.92 |
| 11 | **CF** | `PPI_纺织业(全国:当期同比增长率:月)` | *level* | -0.5281 | -30.53 |
| 12 | **I** | `GDP增长贡献率_第二产业_累计同比_季` | *level* | 0.4955 | 27.89 |
| 13 | **C** | `居民食品消费价格指数CPI_(上年=100)_当月` | *level* | 0.4760 | 26.77 |
| 14 | **RU** | `制造业采购经理指数PMI_新出口订单` | *level* | -0.4664 | -25.75 |
| 15 | **SR** | `PPI_酒、饮料和精制茶制造业(全国:当期同比增长率:月)` | *level* | 0.4565 | 25.18 |
| 16 | **P** | `居民食品消费价格指数CPI_(上年=100)_当月` | *level* | -0.4399 | -24.03 |
| 17 | **AU** | `国内生产总值GDP_累计同比` | *level* | 0.4350 | 23.95 |
| 18 | **Y** | `制造业采购经理指数PMI_新订单` | *level* | 0.4325 | 23.42 |
| 19 | **SA** | `非制造业PMI_建筑业_全国_当期值_月` | *level* | 0.5202 | 23.19 |
| 20 | **M** | `制造业采购经理指数PMI_生产` | *level* | 0.4255 | 22.96 |
| 21 | **SC** | `国内生产总值GDP_累计同比` | *level* | -0.3823 | -18.21 |
| 22 | **JD** | `PPI_食品制造业(全国:当期同比增长率:月)` | *level* | -0.3372 | -17.91 |
| 23 | **TA** | `制造业采购经理指数PMI_生产` | *level* | 0.3140 | 16.18 |

### 3rd Switch Horizon Best Factors

| Rank | Symbol | Best Factor | Signal Type | Spearman Corr | t-statistic |
|---|---|---|---|---|---|
| 1 | **TF** | `贷款加权平均利率_非金融企业及其他部门_票据融资_人民币` | *level* | 0.8537 | 79.91 |
| 2 | **AL** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *level* | -0.7394 | -50.66 |
| 3 | **SN** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *level* | -0.7075 | -46.32 |
| 4 | **CU** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *level* | -0.7068 | -46.19 |
| 5 | **MA** | `PPI_化学纤维制造业(全国:当期同比增长率:月)` | *level* | -0.6228 | -38.41 |
| 6 | **J** | `PPIRM_黑色金属材料类(全国:当期同比增长率:月)` | *level* | 0.5960 | 35.79 |
| 7 | **RB** | `PPI_非金属矿物制品业(全国:当期同比增长率:月)` | *level* | 0.5936 | 35.70 |
| 8 | **RU** | `PPIRM_化工原料类(全国:当期同比增长率:月)` | *level* | -0.5757 | -33.94 |
| 9 | **I** | `GDP增长贡献率_第二产业_累计同比_季` | *level* | 0.5755 | 33.84 |
| 10 | **NI** | `国内生产总值GDP_累计同比` | *level* | 0.5495 | 32.48 |
| 11 | **V** | `非制造业PMI_建筑业_全国_当期值_月` | *level* | 0.5683 | 30.84 |
| 12 | **C** | `居民食品消费价格指数CPI_(上年=100)_当月` | *level* | 0.5089 | 29.01 |
| 13 | **CF** | `PPI_化学纤维制造业(全国:当期同比增长率:月)` | *level* | -0.4944 | -27.41 |
| 14 | **AG** | `PPIRM_有色金属材料类(全国:当期同比增长率:月)` | *zscore* | -0.5043 | -27.22 |
| 15 | **SA** | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *level* | 0.5820 | 26.41 |
| 16 | **SR** | `PPI_酒、饮料和精制茶制造业(全国:当期同比增长率:月)` | *level* | 0.4707 | 25.71 |
| 17 | **M** | `PPI_食品制造业(全国:当期同比增长率:月)` | *level* | 0.4625 | 25.15 |
| 18 | **Y** | `居民食品消费价格指数CPI_(上年=100)_当月` | *level* | 0.4105 | 21.71 |
| 19 | **P** | `制造业采购经理指数PMI_新订单` | *level* | -0.4104 | -21.64 |
| 20 | **AU** | `国内生产总值GDP_累计同比` | *level* | 0.4022 | 21.62 |
| 21 | **SC** | `国内生产总值GDP_累计同比` | *level* | -0.4209 | -20.31 |
| 22 | **TA** | `PPI_纺织服装、服饰业(全国:当期同比增长率:月)` | *level* | -0.3317 | -16.97 |
| 23 | **JD** | `居民食品消费价格指数CPI_(上年=100)_当月` | *level* | -0.2893 | -15.05 |

## Top 3 Alternative Alphas per Symbol (20-Day Horizon)

Top 3 alternative factor configurations for each symbol ranked by absolute Spearman t-statistic.

| Symbol | Rank | Alternative Factor | Representation | Spearman Corr | t-statistic |
|---|---|---|---|---|---|
| **AG** | 1 | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | -0.2795 | -14.56 |
| **AG** | 2 | `制造业采购经理指数PMI_购进价格` | *level* | -0.2478 | -12.75 |
| **AG** | 3 | `PPI_有色金属冶炼及压延加工业(全国:当期同比增长率:月)` | *level* | -0.2457 | -12.68 |
| **AL** | 1 | `PPIRM_燃料及动力类(全国:当期同比增长率:月)` | *level* | -0.2027 | -10.36 |
| **AL** | 2 | `PPI_交通运输设备制造业(全国:当期同比增长率:月)` | *level* | -0.1881 | -9.58 |
| **AL** | 3 | `制造业采购经理指数PMI_购进价格` | *level* | -0.1550 | -7.82 |
| **AU** | 1 | `制造业采购经理指数PMI_购进价格` | *level* | -0.2566 | -13.24 |
| **AU** | 2 | `社会融资规模存量_同比增速_月末数` | *level* | -0.2233 | -11.40 |
| **AU** | 3 | `国内生产总值GDP缩减指数` | *level* | -0.2101 | -10.71 |
| **C** | 1 | `CPI_翘尾因素_当月` | *diff* | -0.2276 | -9.09 |
| **C** | 2 | `居民鲜果消费价格指数CPI_(上年=100)_当月` | *level* | -0.1697 | -8.61 |
| **C** | 3 | `对CPI同比拉动_食品_粮食(全国:当期同比增长率:月)` | *zscore* | 0.1842 | 8.53 |
| **CF** | 1 | `PPI_纺织业(全国:当期同比增长率:月)` | *level* | -0.1703 | -8.64 |
| **CF** | 2 | `PPI_纺织服装、服饰业(全国:当期同比增长率:月)` | *level* | -0.1601 | -8.12 |
| **CF** | 3 | `PPI_皮革、毛皮、羽毛及其制品和制鞋业(全国:当期同比增长率:月)` | *level* | -0.1668 | -7.88 |
| **CU** | 1 | `PPI_通用设备制造业(全国:当期同比增长率:月)` | *level* | -0.1721 | -8.74 |
| **CU** | 2 | `国内生产总值GDP_累计同比` | *level* | -0.1608 | -8.14 |
| **CU** | 3 | `制造业采购经理指数PMI_购进价格` | *level* | -0.1466 | -7.39 |
| **I** | 1 | `非制造业PMI_建筑业_全国_当期值_月` | *level* | -0.1538 | -7.25 |
| **I** | 2 | `GDP增长贡献率_第二产业_累计同比_季` | *diff* | -0.1292 | -6.42 |
| **I** | 3 | `PPI_金属制品业(全国:当期同比增长率:月)` | *zscore* | 0.1325 | 6.35 |
| **J** | 1 | `非制造业PMI_建筑业_业务活动预期_全国_当期值_月` | *level* | 0.1876 | 8.89 |
| **J** | 2 | `PMI_生产经营活动预期_全国_当期值_月` | *level* | 0.1619 | 7.65 |
| **J** | 3 | `PMI_生产经营活动预期_全国_当期值_月` | *diff* | 0.1604 | 7.56 |
| **JD** | 1 | `制造业采购经理指数PMI_购进价格` | *diff* | 0.1946 | 9.89 |
| **JD** | 2 | `居民鲜菜消费价格指数CPI_(上年=100)_当月` | *level* | 0.1456 | 7.36 |
| **JD** | 3 | `PPI_农副食品加工业(全国:当期同比增长率:月)` | *diff* | -0.1395 | -7.02 |
| **M** | 1 | `PPI_农副食品加工业(全国:当期同比增长率:月)` | *zscore* | -0.1193 | -5.70 |
| **M** | 2 | `居民粮食消费价格指数CPI_(上年=100)_当月` | *level* | 0.1003 | 5.04 |
| **M** | 3 | `居民食品消费价格指数CPI_(上年=100)_当月` | *diff* | -0.1072 | -5.00 |
| **MA** | 1 | `PPI_化学纤维制造业(全国:当期同比增长率:月)` | *zscore* | 0.0977 | 4.66 |
| **MA** | 2 | `制造业采购经理指数PMI_原材料库存` | *zscore* | 0.0914 | 4.34 |
| **MA** | 3 | `PPI_煤炭开采和洗选业(全国:当期同比增长率:月)` | *zscore* | 0.0905 | 4.31 |
| **NI** | 1 | `制造业采购经理指数PMI_购进价格` | *zscore* | -0.1871 | -9.01 |
| **NI** | 2 | `PPI_有色金属冶炼及压延加工业(全国:当期同比增长率:月)` | *zscore* | -0.1582 | -7.60 |
| **NI** | 3 | `PPI_化学原料及化学制品制造业(全国:当期同比增长率:月)` | *diff* | -0.1468 | -7.39 |
| **P** | 1 | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | 0.2206 | 11.31 |
| **P** | 2 | `PMI_生产经营活动预期_全国_当期值_月` | *zscore* | -0.2342 | -10.56 |
| **P** | 3 | `PPI_全部工业品(全国:当期同比增长率:月)` | *zscore* | 0.2150 | 10.45 |
| **RB** | 1 | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *level* | 0.2460 | 11.82 |
| **RB** | 2 | `PPIRM_黑色金属材料类(全国:当期同比增长率:月)` | *level* | 0.2271 | 11.67 |
| **RB** | 3 | `非制造业PMI_建筑业_业务活动预期_全国_当期值_月` | *level* | 0.2424 | 11.63 |
| **RU** | 1 | `PPI_橡胶和塑料制品业(全国:当期同比增长率:月)` | *level* | -0.2542 | -13.15 |
| **RU** | 2 | `PPI_交通运输设备制造业(全国:当期同比增长率:月)` | *level* | -0.2258 | -11.60 |
| **RU** | 3 | `PPI_化学原料及化学制品制造业(全国:当期同比增长率:月)` | *level* | -0.2115 | -10.83 |
| **SA** | 1 | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *zscore* | 0.2764 | 7.29 |
| **SA** | 2 | `社会融资规模_当月值` | *zscore* | -0.3389 | -6.48 |
| **SA** | 3 | `PPI_非金属矿物制品业(全国:当期同比增长率:月)` | *diff* | -0.1409 | -5.60 |
| **SC** | 1 | `PPI_煤炭开采和洗选业(全国:当期同比增长率:月)` | *zscore* | 0.1953 | 8.22 |
| **SC** | 2 | `CPI-PPI_差值_当月` | *level* | -0.1944 | -7.74 |
| **SC** | 3 | `制造业采购经理指数PMI_购进价格` | *zscore* | -0.1759 | -7.39 |
| **SN** | 1 | `PPI_计算机、通信和其他电子设备制造业(全国:当期同比增长率:月)` | *diff* | 0.2456 | 12.62 |
| **SN** | 2 | `PPI_通信设备、计算机及其他电子设备制造业工业品出厂价格指数PPI_(上年=100)_当月` | *diff* | 0.2759 | 11.79 |
| **SN** | 3 | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *zscore* | 0.2075 | 9.29 |
| **SR** | 1 | `制造业采购经理指数PMI_购进价格` | *diff* | 0.2363 | 12.13 |
| **SR** | 2 | `PPI_食品制造业(全国:当期同比增长率:月)` | *zscore* | -0.1617 | -7.78 |
| **SR** | 3 | `PPI_食品制造业(全国:当期同比增长率:月)` | *diff* | -0.1346 | -6.76 |
| **TA** | 1 | `PMI_生产经营活动预期_全国_当期值_月` | *level* | 0.1203 | 5.65 |
| **TA** | 2 | `制造业采购经理指数PMI_原材料库存` | *level* | 0.1071 | 5.37 |
| **TA** | 3 | `PPIRM_纺织原料类(全国:当期同比增长率:月)` | *zscore* | 0.1031 | 4.92 |
| **TF** | 1 | `居民消费价格指数CPI_当月同比(上年同月=100)` | *zscore* | 0.2632 | 12.95 |
| **TF** | 2 | `国内生产总值GDP(现价)_全国_当期同比增长率_季` | *level* | -0.3257 | -10.01 |
| **TF** | 3 | `社会融资规模存量_同比增速_月末数` | *zscore* | -0.2059 | -9.93 |
| **V** | 1 | `非制造业PMI_建筑业_业务活动预期_全国_当期值_月` | *level* | 0.2585 | 12.46 |
| **V** | 2 | `非制造业PMI_建筑业_全国_当期值_月` | *zscore* | 0.2551 | 11.55 |
| **V** | 3 | `非制造业PMI_建筑业_全国_当期值_月` | *level* | 0.2403 | 11.53 |
| **Y** | 1 | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | -0.1462 | -7.39 |
| **Y** | 2 | `制造业采购经理指数PMI_购进价格` | *level* | -0.1398 | -7.04 |
| **Y** | 3 | `制造业采购经理指数PMI_原材料库存` | *diff* | 0.1240 | 6.23 |

## Top 3 Alternative Alphas per Symbol (5-Day Horizon)

| Symbol | Rank | Alternative Factor | Representation | Spearman Corr | t-statistic |
|---|---|---|---|---|---|
| **AG** | 1 | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | -0.1488 | -7.55 |
| **AG** | 2 | `PPI_有色金属冶炼及压延加工业(全国:当期同比增长率:月)` | *level* | -0.1028 | -5.19 |
| **AG** | 3 | `社会融资规模_当月值` | *zscore* | -0.2575 | -4.91 |
| **AL** | 1 | `PPIRM_燃料及动力类(全国:当期同比增长率:月)` | *level* | -0.1080 | -5.45 |
| **AL** | 2 | `PPI_交通运输设备制造业(全国:当期同比增长率:月)` | *level* | -0.0814 | -4.10 |
| **AL** | 3 | `制造业采购经理指数PMI_原材料库存` | *diff* | 0.0779 | 3.91 |
| **AU** | 1 | `制造业采购经理指数PMI_购进价格` | *level* | -0.1187 | -5.98 |
| **AU** | 2 | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | -0.1169 | -5.91 |
| **AU** | 3 | `社会融资规模存量_同比增速_月末数` | *level* | -0.1015 | -5.09 |
| **C** | 1 | `居民鲜果消费价格指数CPI_(上年=100)_当月` | *level* | -0.0829 | -4.17 |
| **C** | 2 | `对CPI同比拉动_食品_粮食(全国:当期同比增长率:月)` | *zscore* | 0.0822 | 3.77 |
| **C** | 3 | `居民鲜果消费价格指数CPI_(上年=100)_当月` | *zscore* | -0.0751 | -3.59 |
| **CF** | 1 | `居民衣着消费价格指数CPI_(上年=100)_当月` | *diff* | 0.0821 | 4.12 |
| **CF** | 2 | `居民服装消费价格指数CPI_(上年=100)_当月` | *diff* | 0.0802 | 4.02 |
| **CF** | 3 | `PPI_纺织服装、服饰业(全国:当期同比增长率:月)` | *level* | -0.0735 | -3.70 |
| **CU** | 1 | `PPI_通用设备制造业(全国:当期同比增长率:月)` | *level* | -0.0977 | -4.93 |
| **CU** | 2 | `制造业采购经理指数PMI_新订单` | *diff* | 0.0849 | 4.26 |
| **CU** | 3 | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | -0.0831 | -4.18 |
| **I** | 1 | `非制造业PMI_建筑业_全国_当期值_月` | *level* | -0.0820 | -3.84 |
| **I** | 2 | `制造业采购经理指数PMI_原材料库存` | *level* | 0.0728 | 3.65 |
| **I** | 3 | `制造业采购经理指数PMI_进口` | *diff* | 0.0710 | 3.56 |
| **J** | 1 | `制造业采购经理指数PMI_原材料库存` | *level* | 0.1171 | 5.90 |
| **J** | 2 | `PPIRM_黑色金属材料类(全国:当期同比增长率:月)` | *level* | 0.0925 | 4.66 |
| **J** | 3 | `非制造业PMI_建筑业_业务活动预期_全国_当期值_月` | *level* | 0.0981 | 4.60 |
| **JD** | 1 | `制造业采购经理指数PMI_购进价格` | *diff* | 0.1198 | 6.04 |
| **JD** | 2 | `居民粮食消费价格指数CPI_(上年=100)_当月` | *diff* | -0.0839 | -4.21 |
| **JD** | 3 | `PPI_农副食品加工业(全国:当期同比增长率:月)` | *diff* | -0.0801 | -4.01 |
| **M** | 1 | `社会融资规模_当月值` | *level* | 0.1687 | 4.16 |
| **M** | 2 | `制造业采购经理指数PMI_原材料库存` | *diff* | -0.0746 | -3.74 |
| **M** | 3 | `居民食品消费价格指数CPI_(上年=100)_当月` | *diff* | -0.0788 | -3.68 |
| **MA** | 1 | `制造业采购经理指数PMI_原材料库存` | *diff* | 0.0541 | 2.71 |
| **MA** | 2 | `制造业采购经理指数PMI_原材料库存` | *zscore* | 0.0542 | 2.58 |
| **MA** | 3 | `制造业采购经理指数PMI_购进价格` | *zscore* | -0.0527 | -2.50 |
| **NI** | 1 | `制造业采购经理指数PMI_购进价格` | *zscore* | -0.0913 | -4.35 |
| **NI** | 2 | `制造业采购经理指数PMI_生产` | *level* | 0.0709 | 3.56 |
| **NI** | 3 | `PPI_汽车制造业(全国:当期同比增长率:月)` | *zscore* | 0.0740 | 3.53 |
| **P** | 1 | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | 0.1358 | 6.88 |
| **P** | 2 | `PPI_全部工业品(全国:当期同比增长率:月)` | *zscore* | 0.1377 | 6.62 |
| **P** | 3 | `PPI_食品制造业(全国:当期同比增长率:月)` | *zscore* | 0.1363 | 6.55 |
| **RB** | 1 | `PPIRM_黑色金属材料类(全国:当期同比增长率:月)` | *level* | 0.1349 | 6.83 |
| **RB** | 2 | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *level* | 0.1364 | 6.43 |
| **RB** | 3 | `PPI_金属制品业(全国:当期同比增长率:月)` | *level* | 0.1206 | 6.10 |
| **RU** | 1 | `PPI_橡胶和塑料制品业(全国:当期同比增长率:月)` | *level* | -0.1177 | -5.95 |
| **RU** | 2 | `PPI_化学原料及化学制品制造业(全国:当期同比增长率:月)` | *level* | -0.1077 | -5.44 |
| **RU** | 3 | `PPI_交通运输设备制造业(全国:当期同比增长率:月)` | *level* | -0.1032 | -5.20 |
| **SA** | 1 | `PPIRM_建筑材料类(全国:当期同比增长率:月)` | *diff* | -0.1249 | -4.98 |
| **SA** | 2 | `PPI_非金属矿物制品业(全国:当期同比增长率:月)` | *diff* | -0.1151 | -4.58 |
| **SA** | 3 | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *zscore* | 0.1514 | 3.93 |
| **SC** | 1 | `CPI-PPI_差值_当月` | *level* | -0.1058 | -4.18 |
| **SC** | 2 | `制造业采购经理指数PMI_进口` | *zscore* | -0.0935 | -3.90 |
| **SC** | 3 | `制造业采购经理指数PMI_购进价格` | *zscore* | -0.0905 | -3.78 |
| **SN** | 1 | `PPI_通信设备、计算机及其他电子设备制造业工业品出厂价格指数PPI_(上年=100)_当月` | *diff* | 0.1349 | 5.62 |
| **SN** | 2 | `PPI_计算机、通信和其他电子设备制造业(全国:当期同比增长率:月)` | *diff* | 0.1111 | 5.58 |
| **SN** | 3 | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *zscore* | 0.0890 | 3.93 |
| **SR** | 1 | `制造业采购经理指数PMI_购进价格` | *diff* | 0.1036 | 5.21 |
| **SR** | 2 | `PPI_食品制造业(全国:当期同比增长率:月)` | *diff* | -0.0868 | -4.35 |
| **SR** | 3 | `PPI_食品制造业(全国:当期同比增长率:月)` | *zscore* | -0.0767 | -3.66 |
| **TA** | 1 | `制造业采购经理指数PMI_原材料库存` | *level* | 0.0649 | 3.25 |
| **TA** | 2 | `制造业采购经理指数PMI_新出口订单` | *diff* | -0.0617 | -3.09 |
| **TA** | 3 | `PMI_生产经营活动预期_全国_当期值_月` | *diff* | -0.0629 | -2.95 |
| **TF** | 1 | `社会融资规模_当月值` | *level* | -0.2436 | -6.10 |
| **TF** | 2 | `社会融资规模存量_同比增速_月末数` | *zscore* | -0.1211 | -5.78 |
| **TF** | 3 | `社会融资规模_当月值` | *diff* | -0.2343 | -5.75 |
| **V** | 1 | `非制造业PMI_建筑业_业务活动预期_全国_当期值_月` | *level* | 0.1412 | 6.66 |
| **V** | 2 | `非制造业PMI_建筑业_全国_当期值_月` | *level* | 0.1404 | 6.63 |
| **V** | 3 | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *level* | 0.1271 | 5.99 |
| **Y** | 1 | `社会融资规模_当月值` | *diff* | 0.2360 | 5.79 |
| **Y** | 2 | `社会融资规模_当月值` | *level* | 0.1914 | 4.74 |
| **Y** | 3 | `制造业采购经理指数PMI_原材料库存` | *diff* | 0.0841 | 4.22 |

## Commodity Specific Details (Sorted by Significance for 20-Day Horizon)

### 1. Symbol: AG (SHFE)

* **Selected Factor**: `PPI_全部工业品(全国:当期同比增长率:月)`
* **Signal Representation**: `level`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `-0.2795`
  * t-statistic: `-14.56`
  * p-value: `3.52e-46`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 2. Symbol: AU (SHFE)

* **Selected Factor**: `制造业采购经理指数PMI_购进价格`
* **Signal Representation**: `level`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `-0.2566`
  * t-statistic: `-13.24`
  * p-value: `1.01e-38`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 3. Symbol: RU (SHFE)

* **Selected Factor**: `PPI_橡胶和塑料制品业(全国:当期同比增长率:月)`
* **Signal Representation**: `level`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `-0.2542`
  * t-statistic: `-13.15`
  * p-value: `3.09e-38`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 4. Symbol: TF (CFFEX)

* **Selected Factor**: `居民消费价格指数CPI_当月同比(上年同月=100)`
* **Signal Representation**: `zscore`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `0.2632`
  * t-statistic: `12.95`
  * p-value: `4.95e-37`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 5. Symbol: SN (SHFE)

* **Selected Factor**: `PPI_计算机、通信和其他电子设备制造业(全国:当期同比增长率:月)`
* **Signal Representation**: `diff`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `0.2456`
  * t-statistic: `12.62`
  * p-value: `2.05e-35`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 6. Symbol: V (DCE)

* **Selected Factor**: `非制造业PMI_建筑业_业务活动预期_全国_当期值_月`
* **Signal Representation**: `level`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `0.2585`
  * t-statistic: `12.46`
  * p-value: `1.87e-34`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 7. Symbol: SR (CZCE)

* **Selected Factor**: `制造业采购经理指数PMI_购进价格`
* **Signal Representation**: `diff`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `0.2363`
  * t-statistic: `12.13`
  * p-value: `6.18e-33`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 8. Symbol: RB (SHFE)

* **Selected Factor**: `非制造业PMI_建筑业_新订单_全国_当期值_月`
* **Signal Representation**: `level`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `0.2460`
  * t-statistic: `11.82`
  * p-value: `2.80e-31`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 9. Symbol: P (DCE)

* **Selected Factor**: `PPI_全部工业品(全国:当期同比增长率:月)`
* **Signal Representation**: `level`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `0.2206`
  * t-statistic: `11.31`
  * p-value: `5.66e-29`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 10. Symbol: AL (SHFE)

* **Selected Factor**: `PPIRM_燃料及动力类(全国:当期同比增长率:月)`
* **Signal Representation**: `level`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `-0.2027`
  * t-statistic: `-10.36`
  * p-value: `1.22e-24`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 11. Symbol: JD (DCE)

* **Selected Factor**: `制造业采购经理指数PMI_购进价格`
* **Signal Representation**: `diff`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `0.1946`
  * t-statistic: `9.89`
  * p-value: `1.15e-22`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 12. Symbol: C (DCE)

* **Selected Factor**: `CPI_翘尾因素_当月`
* **Signal Representation**: `diff`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `-0.2276`
  * t-statistic: `-9.09`
  * p-value: `3.01e-19`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 13. Symbol: NI (SHFE)

* **Selected Factor**: `制造业采购经理指数PMI_购进价格`
* **Signal Representation**: `zscore`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `-0.1871`
  * t-statistic: `-9.01`
  * p-value: `4.40e-19`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 14. Symbol: J (DCE)

* **Selected Factor**: `非制造业PMI_建筑业_业务活动预期_全国_当期值_月`
* **Signal Representation**: `level`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `0.1876`
  * t-statistic: `8.89`
  * p-value: `1.22e-18`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 15. Symbol: CU (SHFE)

* **Selected Factor**: `PPI_通用设备制造业(全国:当期同比增长率:月)`
* **Signal Representation**: `level`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `-0.1721`
  * t-statistic: `-8.74`
  * p-value: `4.10e-18`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 16. Symbol: CF (CZCE)

* **Selected Factor**: `PPI_纺织业(全国:当期同比增长率:月)`
* **Signal Representation**: `level`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `-0.1703`
  * t-statistic: `-8.64`
  * p-value: `9.45e-18`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 17. Symbol: SC (INE)

* **Selected Factor**: `PPI_煤炭开采和洗选业(全国:当期同比增长率:月)`
* **Signal Representation**: `zscore`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `0.1953`
  * t-statistic: `8.22`
  * p-value: `4.01e-16`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 18. Symbol: Y (DCE)

* **Selected Factor**: `PPI_全部工业品(全国:当期同比增长率:月)`
* **Signal Representation**: `level`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `-0.1462`
  * t-statistic: `-7.39`
  * p-value: `1.94e-13`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 19. Symbol: SA (CZCE)

* **Selected Factor**: `PPI_电气机械及器材制造业(全国:当期同比增长率:月)`
* **Signal Representation**: `zscore`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `0.2764`
  * t-statistic: `7.29`
  * p-value: `9.29e-13`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 20. Symbol: I (DCE)

* **Selected Factor**: `非制造业PMI_建筑业_全国_当期值_月`
* **Signal Representation**: `level`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `-0.1538`
  * t-statistic: `-7.25`
  * p-value: `5.94e-13`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 21. Symbol: M (DCE)

* **Selected Factor**: `PPI_农副食品加工业(全国:当期同比增长率:月)`
* **Signal Representation**: `zscore`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `-0.1193`
  * t-statistic: `-5.70`
  * p-value: `1.34e-08`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 22. Symbol: TA (CZCE)

* **Selected Factor**: `PMI_生产经营活动预期_全国_当期值_月`
* **Signal Representation**: `level`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `0.1203`
  * t-statistic: `5.65`
  * p-value: `1.82e-08`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 23. Symbol: MA (CZCE)

* **Selected Factor**: `PPI_化学纤维制造业(全国:当期同比增长率:月)`
* **Signal Representation**: `zscore`
* **Effectiveness Metrics (20-Day horizon)**:
  * Spearman Correlation: `0.0977`
  * t-statistic: `4.66`
  * p-value: `3.35e-06`
  * Correlation Sign: `Positive (Long when factor increases)`

---
