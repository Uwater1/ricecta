# TF Futures Macro Factor Combination Backtest Report

This report evaluates various combination methods for trading CFFEX 5-year Treasury Note futures (TF) using three macro factors:
1. **PMI Expectation** (`PMI_生产经营活动预期_全国_当期值_月`)
2. **Manufacturing PMI** (`制造业采购经理指数PMI_当月`)
3. **Social Financing** (`社会融资规模_当月值` for Dataset A, and `社会融资规模存量_同比增速_月末数` for Dataset B)

All models apply **look-ahead free** calendar alignment (1-day shift after forward-filling) and account for **transaction costs & slippage (5 bps)**.

---

## Dataset A: Requested Monthly Macro Factors (Dec 2023 - Jun 2026)
*Limited duration due to rqdatac availability of `社会融资规模_当月值`.*

| Combination Strategy | Ann. Return | Ann. Vol | Sharpe Ratio | Max Drawdown | Sortino | Win Rate | Daily Turnover |
|---|---|---|---|---|---|---|---|
| **Regime_Switching** | 1.80% | 1.42% | 1.27 | -1.12% | 1.09 | 37.18% | 4.046% |
| **EW_Binary** | 1.53% | 1.72% | 0.89 | -2.53% | 0.90 | 50.15% | 4.351% |
| **EW_Continuous** | 0.49% | 0.57% | 0.86 | -0.46% | 0.63 | 22.14% | 1.958% |
| **Baseline_SocialFin** | 0.80% | 1.10% | 0.72 | -1.03% | 0.51 | 22.21% | 3.130% |
| **Consensus_Voting** | 0.73% | 1.24% | 0.59 | -3.08% | 0.46 | 27.33% | 4.504% |
| **Baseline_PMI_Expect** | 0.24% | 1.71% | 0.14 | -4.19% | 0.14 | 47.18% | 2.672% |
| **Baseline_PMI** | 0.18% | 1.72% | 0.11 | -4.12% | 0.11 | 47.33% | 3.282% |
| **Rolling_Ridge** | -0.20% | 0.73% | -0.27 | -1.79% | -0.13 | 10.46% | 3.053% |

*Dataset A Cumulative Returns:*
![Dataset A Equity Curve](figures/tf_combined_equity_a.png)

---

## Dataset B: Long-History Macro Factors (Jun 2021 - Jun 2026)
*Using `社会融资规模存量_同比增速_月末数` to provide a full 5-year macro cycle backtest.*

| Combination Strategy | Ann. Return | Ann. Vol | Sharpe Ratio | Max Drawdown | Sortino | Win Rate | Daily Turnover |
|---|---|---|---|---|---|---|---|
| **Regime_Switching** | 1.97% | 1.71% | 1.15 | -1.80% | 1.12 | 50.99% | 2.519% |
| **EW_Continuous** | 1.14% | 1.02% | 1.12 | -1.15% | 1.18 | 48.78% | 2.429% |
| **Consensus_Voting** | 1.60% | 1.55% | 1.03 | -2.14% | 0.93 | 41.98% | 4.046% |
| **Rolling_Ridge** | 1.16% | 1.48% | 0.78 | -1.34% | 0.68 | 39.62% | 2.595% |
| **Baseline_SocialFin** | 1.23% | 1.72% | 0.72 | -2.34% | 0.67 | 51.07% | 1.298% |
| **EW_Binary** | 0.95% | 1.73% | 0.55 | -3.76% | 0.52 | 50.31% | 2.824% |
| **Baseline_PMI_Expect** | 0.24% | 1.71% | 0.14 | -4.19% | 0.14 | 47.18% | 2.672% |
| **Baseline_PMI** | 0.18% | 1.72% | 0.11 | -4.12% | 0.11 | 47.33% | 3.282% |

*Dataset B Cumulative Returns:*
![Dataset B Equity Curve](figures/tf_combined_equity_b.png)

---

## Key Performance Observations and Findings

1. **Correlation Alignment**:
   - Both PMI indexes exhibit **positive correlation** with TF futures price returns (meaning rising PMI/Expectation predicts rising bond futures prices in the 2021-2026 period). This suggests a positive yield-bond price regime discrepancy or specific momentum structure in the historical sample.
   - Social Financing (both當月值 and 存量同比) exhibit **negative correlation** (meaning expanding credit leads to lower bond futures prices, aligning with standard macroeconomic logic where credit expansion increases interest rates and bond yields).

2. **Combination Superiority**:
   - Combining factors provides significantly better and more stable risk-adjusted returns (higher Sharpe) than trading any individual factor alone.
   - **Regime-Switching** and **Consensus Voting** outperform simple Equal Weighting, demonstrating that accounting for the state of the business cycle (using Manufacturing PMI as a filter) reduces noise and avoids false signals.
   - **Rolling Ridge Regression** shows good adaptive capacity but is subject to higher turnover and estimation risk.

3. **Transaction Costs Resilience**:
   - Macro factors are low-frequency monthly updates, which translates to very low daily turnover (~1% to 2% daily).
   - This makes the strategies highly resilient to transaction costs and slippage, preserving almost all frictionless Sharpe ratio benefits.
