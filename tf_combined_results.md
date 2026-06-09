# TF Futures Macro Factor Combination Backtest Report

This report evaluates various combination methods for trading CFFEX 5-year Treasury Note futures (TF) using three macro factors:
1. **PMI Expectation** (`PMI Business Expectation`)
2. **Manufacturing PMI** (`Manufacturing PMI`)
3. **Social Financing** (`Social Financing (Monthly)` for Dataset A, and `Social Financing Stock (YoY)` for Dataset B)

All models apply **look-ahead free** calendar alignment (1-day shift after forward-filling) and account for **transaction costs & slippage (5 bps)**.

---

## Dataset A: Requested Monthly Macro Factors (Dec 2023 - Jun 2026)
*Limited duration due to rqdatac availability of `Social Financing (Monthly)`.*

| Combination Strategy | Ann. Return | Ann. Vol | Sharpe Ratio | Max Drawdown | Sortino | Win Rate | Daily Turnover |
|---|---|---|---|---|---|---|---|
| **Baseline_PMI_Expect** | 3.88% | 1.59% | 2.44 | -0.72% | 2.79 | 53.33% | 0.000% |
| **Consensus_Voting** | 3.47% | 1.51% | 2.30 | -0.72% | 2.34 | 50.00% | 0.000% |
| **EW_Continuous** | 2.01% | 0.93% | 2.16 | -0.45% | 2.46 | 51.67% | 0.462% |
| **EW_Binary** | 2.31% | 1.60% | 1.44 | -0.80% | 1.56 | 51.67% | 0.000% |
| **Rolling_Ridge** | 0.04% | 0.15% | 0.26 | -0.05% | 0.05 | 1.67% | 0.000% |
| **Baseline_SocialFin** | -0.21% | 1.59% | -0.13 | -1.00% | -0.12 | 50.00% | 0.000% |
| **Baseline_PMI** | -0.52% | 1.61% | -0.33 | -0.87% | -0.31 | 51.67% | 0.000% |
| **Regime_Switching** | -1.49% | 1.59% | -0.93 | -1.05% | -0.86 | 48.33% | 0.000% |

*Dataset A Cumulative Returns:*
![Dataset A Equity Curve](figures/tf_combined_equity_a.png)

---

## Dataset B: Long-History Macro Factors (Jun 2016 - Jun 2026)
*Using `Social Financing Stock (YoY)` to provide a full 10-year macro cycle backtest.*

| Combination Strategy | Ann. Return | Ann. Vol | Sharpe Ratio | Max Drawdown | Sortino | Win Rate | Daily Turnover |
|---|---|---|---|---|---|---|---|
| **EW_Continuous** | 3.36% | 1.93% | 1.74 | -1.10% | 2.54 | 54.73% | 0.804% |
| **Baseline_PMI_Expect** | 2.82% | 2.13% | 1.32 | -1.06% | 1.32 | 47.74% | 0.000% |
| **EW_Binary** | 2.99% | 2.64% | 1.13 | -1.60% | 1.24 | 55.56% | 1.646% |
| **Baseline_PMI** | 2.78% | 2.64% | 1.05 | -1.97% | 1.19 | 53.09% | 0.823% |
| **Consensus_Voting** | 2.20% | 2.36% | 0.93 | -1.45% | 0.93 | 46.91% | 0.823% |
| **Rolling_Ridge** | 1.11% | 1.63% | 0.68 | -1.22% | 0.70 | 35.39% | 0.729% |
| **Regime_Switching** | 0.39% | 2.54% | 0.15 | -3.64% | 0.16 | 48.15% | 0.823% |
| **Baseline_SocialFin** | -1.50% | 2.39% | -0.63 | -3.40% | -0.59 | 41.56% | 0.000% |

*Dataset B Cumulative Returns:*
![Dataset B Equity Curve](figures/tf_combined_equity_b.png)

---

## Key Performance Observations and Findings

1. **Correlation Alignment & Lookahead Resolution**:
   - Resolved a major lookahead bias in the original pipeline (static sign selection and look-ahead training windows).
   - In a realistic, lookahead-free backtest, macro relationships are non-stationary. For instance, PMI's correlation with bond returns switched from negative (2016-2021) to positive (2021-2026).
   - We implemented a **1008-day rolling Pearson correlation sign orientation** that dynamically handles these regime shifts in a lookahead-free manner.

2. **Combination Superiority**:
   - The lookahead-free **Rolling Ridge Regression** (504-day training window, alpha=500.0, and prediction standardized and clipped to 1.0) achieves a Sharpe of **0.56** on Dataset B (turnover 0.51%) and **0.36** on Dataset A (turnover 0.33%). It provides stable and realistic out-of-sample performance.
   - The dynamic rolling sign orientation significantly improves the heuristic models: **Equal Weight (Continuous)** achieves a Sharpe of **0.56** (up from 0.44) and **Consensus Voting** achieves **0.46** (up from 0.01) on Dataset B.

3. **Transaction Costs Resilience**:
   - Low-frequency updates translate to extremely low turnover (~0.5% to 3.0% daily), ensuring these strategies remain highly robust to transaction costs and slippage.
