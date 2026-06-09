# Chinese Commodity Futures Arbitrage Research

This repository contains research on the feasibility of **Basis Momentum** and **Curve Arbitrage** strategies across 21 liquid Chinese commodity futures from 2021 to 2026.

## 1. Feasibility Study Results

Daily spot-basis and 5-minute contract data were used with risk-free financing rates (SHIBOR) and empirical transaction costs (2 bps low-friction, 5 bps high-friction per contract side, i.e., 8 bps/20 bps round-turn spread friction).

| Strategy & Cost Tier | Annualized Return | Annualized Vol | Sharpe Ratio | Max Drawdown | Win Rate |
|---|---|---|---|---|---|
| **Curve Arbitrage (Low Friction)** | 123.55% | 6.61% | 12.22 | -1.10% | 83.12% |
| **Curve Arbitrage (High Friction)** | 103.50% | 6.24% | 11.43 | -1.16% | 80.83% |
| **Basis Momentum (Low Friction)** | -2.59% | 7.37% | -0.57 | -19.49% | 49.39% |
| **Basis Momentum (High Friction)** | -5.79% | 7.38% | -1.02 | -31.61% | 48.09% |

### Strategy Conclusions
- **Curve Arbitrage (Calendar Spreads) -> Highly Feasible:** Running a 5-minute mean-reversion trading model on contract spreads using rolling daily Z-scores delivers exceptionally strong returns (>100% Ann. Return) and high Sharpe ratios (>11.0). Drawdown is restricted to ~1.16% due to market-neutral properties.
- **Basis Momentum -> Not Feasible:** A trend-following strategy on daily basis rates is unprofitable, indicating that Chinese commodity basis rates are mean-reverting rather than trending.

---

## 2. Project Structure

- **Core Strategy & Evaluation Scripts:**
  - [research_arbitrage.py](file:///home/hallo/data/ricecta/research_arbitrage.py): Backtest simulation engine for daily basis momentum and 5-minute curve spreads.
  - [run_evaluation.py](file:///home/hallo/data/ricecta/run_evaluation.py): Full evaluation pipeline runner for daily + hold alphas.
  - [alphas.py](file:///home/hallo/data/ricecta/alphas.py): Unified alpha calculation library.
  - [evaluate_alpha.py](file:///home/hallo/data/ricecta/evaluate_alpha.py): Performance metrics calculator.
  - [evaluate_per_symbol.py](file:///home/hallo/data/ricecta/evaluate_per_symbol.py): Per-symbol single-asset backtest for each symbol's #1 macro factor.
  - [evaluate_hold_strategy.py](file:///home/hallo/data/ricecta/evaluate_hold_strategy.py): Contract holding strategy backtest engine.
  - [run_hold_backtest.py](file:///home/hallo/data/ricecta/run_hold_backtest.py): Optimization CLI for holding parameters H and k.

- **Data Download Scripts (in `download/`):**
  - [download/download_data.py](file:///home/hallo/data/ricecta/download/download_data.py): Main downloader for futures minute bars, spot basis, yield curve, etc.
  - [download/download_daily_data.py](file:///home/hallo/data/ricecta/download/download_daily_data.py): Downloads pre-adjusted dominant contract daily prices.
  - [download/download_contracts_daily.py](file:///home/hallo/data/ricecta/download/download_contracts_daily.py): Downloads daily data for individual contracts.
  - [download/download_foreign_data.py](file:///home/hallo/data/ricecta/download/download_foreign_data.py): Downloads daily foreign agricultural futures prices and exchange rates.
  - [download/download_macro_factors.py](file:///home/hallo/data/ricecta/download/download_macro_factors.py): Parses potential factors and fetches macro data.
  - [download/download_shibor.py](file:///home/hallo/data/ricecta/download/download_shibor.py): Downloads SHIBOR financing rates.

- **Research and Results Reports:**
  - [arbitrage.md](file:///home/hallo/data/ricecta/arbitrage.md): Comprehensive arbitrage study methodology and conclusions.
  - [alpha_evaluation_report.md](file:///home/hallo/data/ricecta/alpha_evaluation_report.md): Per-symbol alpha strategy evaluation report.
  - [alt_alphas.md](file:///home/hallo/data/ricecta/alt_alphas.md): Macro alpha factor screening, horizon stability analysis, and cross-sectional portfolio results.
  - [hold_strategy_report.md](file:///home/hallo/data/ricecta/hold_strategy_report.md): Hold strategy optimization results report.
  - [arbitrage_metrics_by_symbol.csv](file:///home/hallo/data/ricecta/arbitrage_metrics_by_symbol.csv): Detailed arbitrage metrics for all 23 commodities.

