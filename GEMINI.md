Follow INSTRUCTIONS.md FOR API RULES

## Underlying Futures (23 个标的)

| 交易所 | 代码 | 品种 |
|---|---|---|
| DCE | C, M, Y, P, V, J, JD, I | 玉米, 豆粕, 豆油, 棕榈油, PVC, 焦炭, 鸡蛋, 铁矿石 |
| SHFE | CU, AL, AU, AG, RB, RU, NI, SN | 铜, 铝, 金, 银, 螺纹钢, 橡胶, 镍, 锡 |
| INE | SC | 原油 |
| CZCE | CF, SR, TA, MA, SA | 棉花, 白糖, PTA, 甲醇, 纯碱 |
| CFFEX | TF | 5年期国债 |

## Commands to Run Backtest

1. Install dependencies:
```bash
rtk uv pip install --python venv/bin/python -r requirements.txt
```

2. Download SHIBOR data:
```bash
rtk venv/bin/python download_shibor.py
```

3. Run backtest simulation:
```bash
rtk venv/bin/python research_arbitrage.py
```

## Strategy Logic Summary
- **Basis Momentum:** daily signal using $BR_t = \frac{spot\_price - dominant\_price}{spot\_price}$. Trade dominant contract daily. Shifted 1-day. Splice returns to avoid roll gaps.
- **Curve Arbitrage:** 5-minute calendar spread Z-score of $P_{near} - P_{dom}$ using rolling 20-day daily spread stats. Long entry $Z < -2.0$, short entry $Z > 2.0$. Exit when $|Z| \le 0.2$. Standard double transaction costs and slippage applied.