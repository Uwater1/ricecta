# Alternative Data Alphas for Futures (Sorted by Significance)

This document lists the single most effective alternative macro factor for each of the 23 futures underlyings, sorted by the statistical significance of their correlation with 5-day future returns.

## Performance Summary Table

| Rank | Symbol | Best Factor | Signal Type | Spearman Corr (5d) | t-statistic | p-value | Description |
|---|---|---|---|---|---|---|---|
| 1 | **AG** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *diff* | -0.2066 | -7.48 | 1.35e-13 | 光伏玻璃下游 |
| 2 | **TF** | `制造业采购经理指数PMI_当月` | *zscore* | 0.1840 | 6.01 | 2.51e-09 | 经济景气度直接影响利率预期 |
| 3 | **Y** | `社会融资规模_当月值` | *diff* | 0.2432 | 5.98 | 4.05e-09 | 信用扩张力度影响债券供给和利率 |
| 4 | **SN** | `制造业采购经理指数PMI_进口` | *level* | 0.1645 | 5.97 | 3.02e-09 | 棉花进口景气度 |
| 5 | **CF** | `PMI_生产经营活动预期_全国_当期值_月` | *diff* | -0.1599 | -5.76 | 1.07e-08 | 企业预期 |
| 6 | **RU** | `PMI_生产经营活动预期_全国_当期值_月` | *level* | -0.1493 | -5.42 | 6.95e-08 | 企业预期 |
| 7 | **V** | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *level* | 0.1384 | 5.02 | 5.90e-07 | 建筑新订单 |
| 8 | **RB** | `非制造业PMI_建筑业_新订单_全国_当期值_月` | *level* | 0.1329 | 4.82 | 1.63e-06 | 建筑新订单 |
| 9 | **P** | `制造业采购经理指数PMI_进口` | *zscore* | -0.1483 | -4.82 | 1.68e-06 | 棉花进口景气度 |
| 10 | **SR** | `PPI_食品制造业(全国:当期同比增长率:月)` | *zscore* | -0.1461 | -4.78 | 2.00e-06 | 食品制造出厂价 |
| 11 | **JD** | `居民食品消费价格指数CPI_(上年=100)_当月` | *diff* | -0.1245 | -4.48 | 8.06e-06 | 食品通胀环境 |
| 12 | **M** | `社会融资规模_当月值` | *level* | 0.1812 | 4.47 | 9.31e-06 | 信用扩张力度影响债券供给和利率 |
| 13 | **J** | `制造业采购经理指数PMI_原材料库存` | *diff* | 0.1201 | 4.31 | 1.78e-05 | 库存周期 |
| 14 | **SA** | `非制造业PMI_建筑业_全国_当期值_月` | *diff* | -0.1193 | -4.27 | 2.09e-05 | 建筑业景气度驱动玻璃需求 |
| 15 | **NI** | `社会融资规模_当月值` | *diff* | 0.1757 | 4.25 | 2.46e-05 | 信用扩张力度影响债券供给和利率 |
| 16 | **TA** | `制造业采购经理指数PMI_新订单` | *zscore* | -0.1288 | -4.17 | 3.27e-05 | 需求端 |
| 17 | **MA** | `非制造业PMI_建筑业_全国_当期值_月` | *zscore* | -0.1267 | -4.12 | 4.08e-05 | 建筑业景气度驱动玻璃需求 |
| 18 | **SC** | `制造业采购经理指数PMI_进口` | *zscore* | -0.1211 | -3.92 | 9.51e-05 | 棉花进口景气度 |
| 19 | **AU** | `PPI_全部工业品(全国:当期同比增长率:月)` | *level* | -0.1020 | -3.69 | 2.30e-04 | 工业品通胀 |
| 20 | **AL** | `制造业采购经理指数PMI_新订单` | *zscore* | -0.1125 | -3.64 | 2.89e-04 | 需求端 |
| 21 | **I** | `制造业采购经理指数PMI_进口` | *diff* | 0.1010 | 3.61 | 3.13e-04 | 棉花进口景气度 |
| 22 | **C** | `PMI_生产经营活动预期_全国_当期值_月` | *diff* | -0.0940 | -3.36 | 8.13e-04 | 企业预期 |
| 23 | **CU** | `PPI_电气机械及器材制造业(全国:当期同比增长率:月)` | *diff* | -0.0910 | -3.24 | 1.23e-03 | 光伏玻璃下游 |

---

## Commodity Specific Details (Sorted by Significance)

### 1. 品种: AG (SHFE (上期所))

* **Selected Factor**: `PPI_电气机械及器材制造业(全国:当期同比增长率:月)`
* **Signal Representation**: `diff`
* **Description**: 光伏玻璃下游
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.2066`
  * t-statistic: `-7.48`
  * p-value: `1.35e-13`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 2. 品种: TF (CFFEX (中金所))

* **Selected Factor**: `制造业采购经理指数PMI_当月`
* **Signal Representation**: `zscore`
* **Description**: 经济景气度直接影响利率预期
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.1840`
  * t-statistic: `6.01`
  * p-value: `2.51e-09`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 3. 品种: Y (DCE (大商所))

* **Selected Factor**: `社会融资规模_当月值`
* **Signal Representation**: `diff`
* **Description**: 信用扩张力度影响债券供给和利率
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.2432`
  * t-statistic: `5.98`
  * p-value: `4.05e-09`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 4. 品种: SN (SHFE (上期所))

* **Selected Factor**: `制造业采购经理指数PMI_进口`
* **Signal Representation**: `level`
* **Description**: 棉花进口景气度
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.1645`
  * t-statistic: `5.97`
  * p-value: `3.02e-09`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 5. 品种: CF (CZCE (郑商所))

* **Selected Factor**: `PMI_生产经营活动预期_全国_当期值_月`
* **Signal Representation**: `diff`
* **Description**: 企业预期
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1599`
  * t-statistic: `-5.76`
  * p-value: `1.07e-08`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 6. 品种: RU (SHFE (上期所))

* **Selected Factor**: `PMI_生产经营活动预期_全国_当期值_月`
* **Signal Representation**: `level`
* **Description**: 企业预期
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1493`
  * t-statistic: `-5.42`
  * p-value: `6.95e-08`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 7. 品种: V (DCE (大商所))

* **Selected Factor**: `非制造业PMI_建筑业_新订单_全国_当期值_月`
* **Signal Representation**: `level`
* **Description**: 建筑新订单
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.1384`
  * t-statistic: `5.02`
  * p-value: `5.90e-07`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 8. 品种: RB (SHFE (上期所))

* **Selected Factor**: `非制造业PMI_建筑业_新订单_全国_当期值_月`
* **Signal Representation**: `level`
* **Description**: 建筑新订单
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.1329`
  * t-statistic: `4.82`
  * p-value: `1.63e-06`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 9. 品种: P (DCE (大商所))

* **Selected Factor**: `制造业采购经理指数PMI_进口`
* **Signal Representation**: `zscore`
* **Description**: 棉花进口景气度
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1483`
  * t-statistic: `-4.82`
  * p-value: `1.68e-06`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 10. 品种: SR (CZCE (郑商所))

* **Selected Factor**: `PPI_食品制造业(全国:当期同比增长率:月)`
* **Signal Representation**: `zscore`
* **Description**: 食品制造出厂价
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1461`
  * t-statistic: `-4.78`
  * p-value: `2.00e-06`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 11. 品种: JD (DCE (大商所))

* **Selected Factor**: `居民食品消费价格指数CPI_(上年=100)_当月`
* **Signal Representation**: `diff`
* **Description**: 食品通胀环境
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1245`
  * t-statistic: `-4.48`
  * p-value: `8.06e-06`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 12. 品种: M (DCE (大商所))

* **Selected Factor**: `社会融资规模_当月值`
* **Signal Representation**: `level`
* **Description**: 信用扩张力度影响债券供给和利率
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.1812`
  * t-statistic: `4.47`
  * p-value: `9.31e-06`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 13. 品种: J (DCE (大商所))

* **Selected Factor**: `制造业采购经理指数PMI_原材料库存`
* **Signal Representation**: `diff`
* **Description**: 库存周期
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.1201`
  * t-statistic: `4.31`
  * p-value: `1.78e-05`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 14. 品种: SA (CZCE (郑商所))

* **Selected Factor**: `非制造业PMI_建筑业_全国_当期值_月`
* **Signal Representation**: `diff`
* **Description**: 建筑业景气度驱动玻璃需求
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1193`
  * t-statistic: `-4.27`
  * p-value: `2.09e-05`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 15. 品种: NI (SHFE (上期所))

* **Selected Factor**: `社会融资规模_当月值`
* **Signal Representation**: `diff`
* **Description**: 信用扩张力度影响债券供给和利率
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.1757`
  * t-statistic: `4.25`
  * p-value: `2.46e-05`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 16. 品种: TA (CZCE (郑商所))

* **Selected Factor**: `制造业采购经理指数PMI_新订单`
* **Signal Representation**: `zscore`
* **Description**: 需求端
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1288`
  * t-statistic: `-4.17`
  * p-value: `3.27e-05`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 17. 品种: MA (CZCE (郑商所))

* **Selected Factor**: `非制造业PMI_建筑业_全国_当期值_月`
* **Signal Representation**: `zscore`
* **Description**: 建筑业景气度驱动玻璃需求
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1267`
  * t-statistic: `-4.12`
  * p-value: `4.08e-05`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 18. 品种: SC (INE (能源中心))

* **Selected Factor**: `制造业采购经理指数PMI_进口`
* **Signal Representation**: `zscore`
* **Description**: 棉花进口景气度
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1211`
  * t-statistic: `-3.92`
  * p-value: `9.51e-05`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 19. 品种: AU (SHFE (上期所))

* **Selected Factor**: `PPI_全部工业品(全国:当期同比增长率:月)`
* **Signal Representation**: `level`
* **Description**: 工业品通胀
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1020`
  * t-statistic: `-3.69`
  * p-value: `2.30e-04`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 20. 品种: AL (SHFE (上期所))

* **Selected Factor**: `制造业采购经理指数PMI_新订单`
* **Signal Representation**: `zscore`
* **Description**: 需求端
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.1125`
  * t-statistic: `-3.64`
  * p-value: `2.89e-04`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 21. 品种: I (DCE (大商所))

* **Selected Factor**: `制造业采购经理指数PMI_进口`
* **Signal Representation**: `diff`
* **Description**: 棉花进口景气度
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `0.1010`
  * t-statistic: `3.61`
  * p-value: `3.13e-04`
  * Correlation Sign: `Positive (Long when factor increases)`

---

### 22. 品种: C (DCE (大商所))

* **Selected Factor**: `PMI_生产经营活动预期_全国_当期值_月`
* **Signal Representation**: `diff`
* **Description**: 企业预期
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.0940`
  * t-statistic: `-3.36`
  * p-value: `8.13e-04`
  * Correlation Sign: `Negative (Short when factor increases)`

---

### 23. 品种: CU (SHFE (上期所))

* **Selected Factor**: `PPI_电气机械及器材制造业(全国:当期同比增长率:月)`
* **Signal Representation**: `diff`
* **Description**: 光伏玻璃下游
* **Effectiveness Metrics (5-day horizon)**:
  * Spearman Correlation: `-0.0910`
  * t-statistic: `-3.24`
  * p-value: `1.23e-03`
  * Correlation Sign: `Negative (Short when factor increases)`

---

