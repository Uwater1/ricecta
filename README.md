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

- [research_arbitrage.py](file:///home/hallo/data/ricecta/research_arbitrage.py): Backtest simulation engine for daily basis momentum and 5-minute curve spreads.
- [download_shibor.py](file:///home/hallo/data/ricecta/download_shibor.py): Downloads daily Shanghai Interbank Offered Rate (SHIBOR) data via `rqdatac`.
- [arbitrage_metrics_by_symbol.csv](file:///home/hallo/data/ricecta/arbitrage_metrics_by_symbol.csv): CSV containing detailed metrics for all 21 commodities.
- [arbitrage.md](file:///home/hallo/data/ricecta/arbitrage.md): Comprehensive research methodology and findings.
- [figures/portfolio_equity_curves.png](file:///home/hallo/data/ricecta/figures/portfolio_equity_curves.png): Cumulative return performance curves.
