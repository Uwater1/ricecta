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

## Alpha Evaluation System (Daily)
Framework ready for Step 2 (non-price-volume alphas).

### Structure
- **Data Downloader:** [download_daily_data.py](file:///home/hallo/data/ricecta/download_daily_data.py) — fetches pre-adjusted dominant daily contracts (no roll gaps).
- **Alpha Library:** [alphas.py](file:///home/hallo/data/ricecta/alphas.py) — calculates signals.
- **Metrics Evaluator:** [evaluate_alpha.py](file:///home/hallo/data/ricecta/evaluate_alpha.py) — calculates DSR (multiple testing), Sortino, Turnover-Adjusted Calmar, Capacity-Adjusted Sharpe Decay (market impact).
- **Runner:** [run_evaluation.py](file:///home/hallo/data/ricecta/run_evaluation.py) — runs full pipeline and exports [alpha_evaluation_report.md](file:///data/ricecta/alpha_evaluation_report.md).

### Run Command
```bash
rtk venv/bin/python run_evaluation.py
# Evaluate specific alpha (1-8 or name)
rtk venv/bin/python run_evaluation.py 8
```

## Recent Alpha Updates
- **Agricultural Lead-Lag Alpha (`ForeignAg_LeadLag`):** Added daily exchange rates (USDCNY and MYRCNY) to denominate foreign commodity close prices in CNY before calculating lead-lag returns. Changed to cubed difference $(R^{CN}_t(N) - R^{US\_CNY}_{t-1\_aligned}(N))^3$ to suppress noise and highlight anomalies. Shifted foreign return by 1 day on foreign calendar before alignment. No lookahead.
- **Optimal N parameters ($N \in [3,60]$):** `C`: 3, `M`: 3, `Y`: 5, `P`: 55, `CF`: 4, `SR`: 50.
- **Vectorized Evaluation Speedup:** Vectorized weights, IC Spearman correlation, and quintiles in [evaluate_alpha.py](file:///home/hallo/data/ricecta/evaluate_alpha.py). Execution time down from 30+s to ~2s.
- **Evaluation CLI args:** Added argument parser in [run_evaluation.py](file:///home/hallo/data/ricecta/run_evaluation.py) to run specific alpha.
- **Alternative Macro Data Testing Pipeline:** Created `download_macro_factors.py` and `test_alt_alphas.py` to parse, download, and screen 83 candidate macro factors using Spearman correlation against future returns. Documented in `alt_alphas.md`, sorted by significance.
- **Alpha Library Integration (`Alt_Macro_Alpha`):** Added `Alt_Macro_Alpha` into `alphas.py`, dynamically computing the optimal representation (level, diff, or z-score) of the best macro factor signed by its correlation per symbol.
- **Flexible Evaluation Framework & 20-Day Switch:** Updated `evaluate_alpha.py` to support time-series weighting via a `demean` parameter. Modified `run_evaluation.py` to evaluate both cross-sectional (`Alt_Macro_Alpha_XS`) and time-series (`Alt_Macro_Alpha_TS`) portfolios. Switched configuration to target the optimal 20-day horizon correlation. Alt_Macro_Alpha_TS achieves a Sharpe ratio of 0.90 (up from 0.81) and Alt_Macro_Alpha_XS achieves 0.62 (up from 0.25). Included 20-day horizon summary and top 3 tables in `alt_alphas.md`.

## TF Futures Macro Factor Combination Research
- **Macro Factor Data Availability**: `社会融资规模_当月值` from rqdatac starts in December 2023, limiting joint factor testing to Dec 2023 - Jun 2026. Use `社会融资规模存量_同比增速_月末数` to provide a full 10-year macro cycle backtest (from 2016 onwards).
- **10-Year Backtest (Jun 2016 - Jun 2026)**: Modified [test_tf_combined.py](file:///home/hallo/data/ricecta/test_tf_combined.py) to support 10-year backtests using `start_date` parameter in evaluations and handling missing data (NaNs) in signals gracefully.
- **Lookahead Bias Resolution**: Replaced static sign selection with **1008-day rolling Pearson correlation sign orientation** (lookahead-free). Shifted Ridge regression training target by 20 days (ends at `idx - 20` to avoid predicting using future data).
- **Correlation Regimes**: Over 10 years, PMI correlations undergo complete sign reversal (negative in 2016-2021, positive in 2021-2026). Rolling sign handles this adaptively.
- **Strategy Performance (Lookahead-Free)**:
  - `Baseline_SocialFin`: Sharpe 0.61.
  - `Rolling_Ridge`: Sharpe 0.56 (low turnover 0.51%).
  - `EW_Continuous`: Sharpe 0.56 (up from 0.44).
  - `Consensus_Voting`: Sharpe 0.46 (up from 0.01).
- **Run Command**:
```bash
rtk venv/bin/python test_tf_combined.py
```

## Macro Alpha Contract Holding Strategy (No-Rolling)
- **Concept:** Buy specific contract (nearest, 2nd, or 3rd nearest) on monthly signal, hold 5-40 days without daily rolling. Assume 5 bp slippage per transaction.
- **Liquidity (Cold Month) Filter:** Dynamically select the top 3 contracts by 5-day rolling Open Interest on each entry date (relative ranking, no absolute OI floor).
- **Maturity Month Exit Rules:** Force-exit commodities on last trading day of month preceding delivery month. Force-exit TF 5 trading days before de-listing.
- **Data-Driven Entry Dates:** Entry trades are triggered on dominant contract switch dates detected from actual dominant contract mapping data (`data/dominant_contracts/dominant.parquet`). Adapts automatically to each symbol's contract cycle: monthly (SHFE metals CU/AL/AU/AG/RB/RU/NI/SN, INE SC), quarterly (CFFEX TF: months 3/6/9/12), or 1/5/9 (most DCE and CZCE grains).
- **Results:** Holding strategy dramatically improves performance (e.g., JD Sharpe 0.85 vs baseline 0.23; P Sharpe 0.60 vs baseline -0.15).
- **Commands to Run:**
  - Download individual contracts data:
  ```bash
  rtk venv/bin/python download_contracts_daily.py
  ```
  - Optimize holding period and contract index, compile report:
  ```bash
  rtk venv/bin/python run_hold_backtest.py
  ```