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
rtk venv/bin/python download/download_shibor.py
```

3. Run backtest simulation:
```bash
rtk venv/bin/python research_arbitrage.py
```

## Strategy Logic Summary
- **Basis Momentum:** daily signal using $BR_t = \frac{spot\_price - dominant\_price}{spot\_price}$. Trade dominant contract daily. Shifted 1-day. Splice returns to avoid roll gaps.
- **Curve Arbitrage:** 5-minute calendar spread Z-score of $P_{near} - P_{dom}$ using rolling 20-day daily spread stats. Long entry $Z < -2.0$, short entry $Z > 2.0$. Exit when $|Z| \le 0.2$. Standard double transaction costs and slippage applied.

## Alpha Evaluation System (Daily + No-Rolling)
Framework evaluates 9 alpha signals across 23 commodity futures.

### Structure
- **Data Downloader:** [download_daily_data.py](file:///home/hallo/data/ricecta/download/download_daily_data.py) — fetches pre-adjusted dominant daily contracts (no roll gaps).
- **Alpha Library:** [alphas.py](file:///home/hallo/data/ricecta/alphas.py) — calculates 7 daily signals + 1 no-rolling discretized signal (`Alt_Macro_Alpha_NoRoll`). Also exposes `get_dominant_switch_dates()` (canonical source) and `BEST_HOLD_PARAMS` (optimized hold period H and contract index k per symbol).
- **Per-Symbol Evaluator:** [evaluate_per_symbol.py](file:///home/hallo/data/ricecta/evaluate_per_symbol.py) — evaluates each of the 23 symbols individually with its #1 ranked macro factor from `alt_alphas.md` Commodity Specific Details. Single-asset directional backtest with 5bps TC. Produces per-symbol metrics table, equity curve grid (`figures/per_symbol_equity.png`), and drawdown grid (`figures/per_symbol_drawdowns.png`).
- **Metrics Evaluator:** [evaluate_alpha.py](file:///home/hallo/data/ricecta/evaluate_alpha.py) — calculates DSR (multiple testing), Sortino, Turnover-Adjusted Calmar, Capacity-Adjusted Sharpe Decay (market impact).
- **Hold Strategy Engine:** [evaluate_hold_strategy.py](file:///home/hallo/data/ricecta/evaluate_hold_strategy.py) — per-symbol contract hold backtest with OI-based liquidity filtering and maturity exit rules. Imports `get_dominant_switch_dates` from `alphas.py`.
- **Runner:** [run_evaluation.py](file:///home/hallo/data/ricecta/run_evaluation.py) — runs full pipeline (daily alphas + no-rolling hold strategy) and exports [alpha_evaluation_report.md](file:///data/ricecta/alpha_evaluation_report.md).

### Alphas (9 total)
1. `HTFC_Alpha19_tsrank_mom_rev` — TS_Rank momentum/reversal composite
2. `KalmanFilter_BOS` — Kalman-filtered basis-over-spot residual Z-score
3. `HTFC_Alpha1_meanclose12` — 12-day mean close ratio
4. `HTFC_Alpha5_skew20` — negative 20-day return skewness
5. `EWMA_32_64_CTA` — dual EMA trend-following signal
6. `ForeignAg_LeadLag` — agricultural lead-lag with FX conversion
7. `Alt_Macro_Alpha_XS` — macro factor, cross-sectional portfolio
8. `Alt_Macro_Alpha_TS` — macro factor, time-series portfolio
9. `Alt_Macro_Alpha_NoRoll` — macro factor, contract hold strategy (no daily rolling)

### Run Command
```bash
rtk venv/bin/python run_evaluation.py
# Evaluate specific alpha (1-9 or name)
rtk venv/bin/python run_evaluation.py 9  # runs NoRoll hold strategy
# Per-symbol single-asset backtest
rtk venv/bin/python evaluate_per_symbol.py
```

## Recent Alpha Updates
- **Agricultural Lead-Lag Alpha (`ForeignAg_LeadLag`):** Added daily exchange rates (USDCNY and MYRCNY) to denominate foreign commodity close prices in CNY before calculating lead-lag returns. Changed to cubed difference $(R^{CN}_t(N) - R^{US\_CNY}_{t-1\_aligned}(N))^3$ to suppress noise and highlight anomalies. Shifted foreign return by 1 day on foreign calendar before alignment. No lookahead.
- **Optimal N parameters ($N \in [3,60]$):** `C`: 3, `M`: 3, `Y`: 5, `P`: 55, `CF`: 4, `SR`: 50.
- **Vectorized Evaluation Speedup:** Vectorized weights, IC Spearman correlation, and quintiles in [evaluate_alpha.py](file:///home/hallo/data/ricecta/evaluate_alpha.py). Execution time down from 30+s to ~2s.
- **Evaluation CLI args:** Added argument parser in [run_evaluation.py](file:///home/hallo/data/ricecta/run_evaluation.py) to run specific alpha.
- **Alternative Macro Data Testing Pipeline:** Created `download/download_macro_factors.py` and `test_alt_alphas.py` to parse, download, and screen 83 candidate macro factors using Spearman correlation against future returns. Documented in `alt_alphas.md`, sorted by significance. Raw aligned daily timeseries data (PMI factors vs forward returns) for 18 significant symbols (|t| >= 1.96) saved as [raw_aligned_timeseries.csv](file:///home/hallo/data/ricecta/raw_aligned_timeseries.csv) at workspace root.
- **Alpha Library Integration (`Alt_Macro_Alpha`):** Added `Alt_Macro_Alpha` into `alphas.py`, dynamically computing the optimal representation (level, diff, or z-score) of the best macro factor signed by its correlation per symbol.
- **Flexible Evaluation Framework & 20-Day Switch:** Updated `evaluate_alpha.py` to support time-series weighting via a `demean` parameter. Modified `run_evaluation.py` to evaluate both cross-sectional (`Alt_Macro_Alpha_XS`) and time-series (`Alt_Macro_Alpha_TS`) portfolios. Switched configuration to target the optimal 20-day horizon correlation. Included 20-day horizon summary and top 3 tables in `alt_alphas.md`.
- **Release-Date-Only Correlation & Soundness (Jun 2026):**
  - **Autocorrelation Correction:** Modified `test_alt_alphas.py` to sample signals and returns only on first trading day after each factor's `info_date` (release date), removing autocorrelation bias and t-statistic inflation.
  - **Horizon Stability Sweep ($5\text{d} \dots 25\text{d}$):** Expanded screening to run a full sweep across calendar horizons from 5 to 25 trading days.
  - **Newey-West HAC Adjustments:** Implemented simple OLS Newey-West (HAC) standard error adjustments in numpy on rank-transformed variables, producing robust t-statistics/p-values for Spearman correlation over overlapping return horizons.
  - **Horizon Sign-Consistency:** Filters out factors that do not share the same correlation sign as the 20d horizon across at least 90% of the sweep range (SCF $\ge 90\%$).
  - **Temporal Stability Check:** Release-aligned sample split into first/second halves. Checks if Spearman correlation sign is consistent across sub-periods.
  - **Visualization:** Generates a 5x5 grid subplot (`figures/horizon_stability.png`) displaying Full Sample vs Split-Half stability curves across horizons.
  - **Updated Portfolio Performance:** Selecting robust factors yields Sharpe 1.16 for `Alt_Macro_Alpha_XS`, Sharpe 1.13 for `Alt_Macro_Alpha_TS`, and Sharpe 1.26 for `Alt_Macro_Alpha_NoRoll`.
  - **Alpha Config Updates:** Updated `BEST_MACRO_CONFIGS` in [alphas.py](file:///home/hallo/data/ricecta/alphas.py) to use new robust factors.
  - **Backtest Caching Speedup:** Implemented in-memory caching of contract Parquet data and metadata in [evaluate_hold_strategy.py](file:///home/hallo/data/ricecta/evaluate_hold_strategy.py), cutting backtest execution time by over 50%.

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
- **Signal Integration:** `Alt_Macro_Alpha_NoRoll` is computed in `alphas.py` by discretizing `Alt_Macro_Alpha` at dominant contract switch dates (forward-filled between switches). `BEST_HOLD_PARAMS` in `alphas.py` stores the optimized `(H, k)` per symbol. `run_evaluation.py` evaluates the no-rolling variant (alpha index 9) using the hold strategy engine alongside the 8 daily alphas in a unified report.
- **Portfolio Performance (equal-weighted, 23 symbols, 5 bp slippage):** Sharpe 1.57, MaxDD -3.46%, Sortino 1.30, Calmar 1.03.
- **Commands to Run:**
  - Download individual contracts data:
  ```bash
  rtk venv/bin/python download/download_contracts_daily.py
  ```
  - Run unified evaluation (includes NoRoll as alpha 9):
  ```bash
  rtk venv/bin/python run_evaluation.py
  ```
  - Optimize holding period and contract index independently:
  ```bash
  rtk venv/bin/python run_hold_backtest.py
  ```

## Pre-2021 Backtest & Return Cleaning (Jun 2026)
- **Zero Close Prices and Inf Returns**: Pre-adjusted prices can drop to or below zero. Computing `pct_change()` on zero close prices creates `inf` values that pollute portfolio returns and result in `nan`/`inf` performance metrics. Always replace `inf`/`-inf` with `nan` and fill with `0.0` to sanitize returns. For multi-day forward returns, mask close prices <= 0.0, and clean returns outside `[-0.9, 4.0]` to NaN to remove division artifacts.
- **Report Markdown Image Paths**: Use relative paths (`figures/name.png`) instead of absolute container paths (`/data/ricecta/figures/name.png`) for report images, enabling markdown rendering in any host reader environment.

## Production Readiness & Contract-Specific Pricing (Jun 2026)
- **Contract Splicing (No Dominant Contract Dependency):** Implemented [contract_splicer.py](file:///home/hallo/data/ricecta/contract_splicer.py) to build ratio-adjusted continuous daily price series directly from individual contracts under `data/contracts_daily/` using top-3 rolling open interest and maturity month limits. Removed all dependency on `dominant_daily` parquets for evaluation and screening.
- **Release-Gated Screening:** Added a watermark tracking mechanism (`.last_run_state.json`) in [test_alt_alphas.py](file:///home/hallo/data/ricecta/test_alt_alphas.py) to skip re-running sweeps when no new macro factor data is released. Use `rtk python test_alt_alphas.py --force` to override.
- **Dynamic Config Loading:** [alphas.py](file:///home/hallo/data/ricecta/alphas.py) hot-loads robust factors from `data/results/best_macro_configs.json` if available, with a hardcoded dictionary fallback.
- **Signal Hardening:** Applied rolling 252-day winsorization (1% to 99%) and a minimum 12-observation NaN guard in [alphas.py](file:///home/hallo/data/ricecta/alphas.py) to protect signal generation.
- **Detailed Trade Logging:** Backtest logs now output to `data/results/trade_log_{symbol}.csv` including `hold_days`, raw return, transaction costs, and price levels.
- **Macro Data Updater:** Run `rtk python download/update_macro_data.py` to refresh all macro factor files from rqdatac up to the current date.

## Per-Symbol Alpha Evaluation (Jun 2026)
- **New Script:** [evaluate_per_symbol.py](file:///home/hallo/data/ricecta/evaluate_per_symbol.py) evaluates each symbol individually with its #1 ranked factor from `alt_alphas.md` Commodity Specific Details. Uses `ContractSplicer` for k-th nearest contract prices, constructs macro signal (level/diff/zscore with 1-day shift, winsorization), and runs single-asset directional backtest with 5bps TC.
- **Output:** Per-symbol metrics table (Sharpe, DSR, Calmar, Sortino, MaxDD, etc.), 5x5 equity curve grid (`figures/per_symbol_equity.png`), drawdown grid (`figures/per_symbol_drawdowns.png`), and [alpha_evaluation_report.md](file:///home/hallo/data/ricecta/alpha_evaluation_report.md).
- **Results (23 symbols):** 21/23 positive Sharpe. Top 3: AG (+0.96), SA (+0.74), AL (+0.70). Bottom 3: AU (-0.91), P (-0.50), M (-0.04). Mean Sharpe +0.31, Median +0.42.
- **Config Sync:** Updated `BEST_MACRO_CONFIGS` in both [alphas.py](file:///home/hallo/data/ricecta/alphas.py) and [run_hold_backtest.py](file:///home/hallo/data/ricecta/run_hold_backtest.py) to match Commodity Specific Details #1 factors (6 symbol changes: C, CF, CU, M, NI, SC).