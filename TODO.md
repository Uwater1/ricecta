# 如何在期货交易市场上获得长期优势：

根据World Quant, 对于多alpha因子期货交易模型，另类数据， 例如天气数据，新闻分析，是取得优势的核心

Data Collection   ✅ DONE (2024-06-02)
    ↓
Data Cleaning & Normalization   ⏭️ NEXT
    ↓
Alpha Generation
    ↓
Signal Generation
    ↓
Risk Scaling
    ↓
Portfolio Construction
    ↓
Execution Optimization
    ↓
Live Monitoring
    ↓
Risk Management
    ↓
Performance Attribution
    ↓
Research Feedback Loop

# Underlying Futures
- DCE: `C, M, Y, P, V, J, JD, I`
- SHFE: `CU, AL, AU, AG, RB, RU, NI, SN`
- INE: `SC`
- CZCE: `CF, SR, TA, MA, SA`
- CFFEX: `TF` (5Y treasury futures; excluded IF/IC/IH stock-index per requirement)

---

## Data Collection (Step 1) (API listed)

## Next: Data Cleaning & Normalization (Step 2)

具体清单见 `AGENT.md` 末尾. 关键任务:
1. 时区/日历对齐 (夜盘跨日, 不同交易所)
2. 主力连续合约拼接 (已通过 `get_dominant_price` 完成) (Problems: 主力合约拼接无法反映现实情况，且移仓换月可能产生值得抓住的系统性alpha)
3. 复权处理 (88/888/889 三种模式)
4. 缺失值填充 (宏观 release date 滞后)
5. 币种/CNY 转换
6. 存储格式决策 (Parquet 推荐)
7. Outlier 检测 (涨跌停, tick 异常)


