# Alpha Performance Evaluation Report

This report evaluates the performance of the 9 alphas across 23 Chinese commodity futures from 2016 to 2026.

## Performance Metrics Summary Table

| Alpha Name | Ann. Return | Ann. Vol | Sharpe | Deflated Sharpe (DSR) | Calmar | MaxDD | Sortino | Profit Factor | Win Rate | Hit Rate | IC (Rank) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **HTFC_Alpha19_tsrank_mom_rev** | -10.18% | 11.49% | -0.89 | 0.00% | -0.15 | -68.81% | -0.89 | 0.85 | 46.02% | 49.81% | 0.0167 |
| **KalmanFilter_BOS** | -10.35% | 11.69% | -0.89 | 0.00% | -0.16 | -66.59% | -0.87 | 0.86 | 47.55% | 48.44% | -0.0072 |
| **HTFC_Alpha1_meanclose12** | 0.77% | 33.63% | 0.02 | 0.67% | 0.01 | -66.79% | 0.02 | 1.00 | 48.27% | 50.17% | 0.0178 |
| **HTFC_Alpha5_skew20** | -4.32% | 8.97% | -0.48 | 0.00% | -0.09 | -45.91% | -0.47 | 0.92 | 48.79% | 49.52% | 0.0037 |
| **EWMA_32_64_CTA** | 13.37% | 35.38% | 0.38 | 8.82% | 0.18 | -74.07% | 0.38 | 1.07 | 51.54% | 49.71% | 0.0170 |
| **ForeignAg_LeadLag** | 29.94% | 29.43% | 1.02 | 70.17% | 1.19 | -25.20% | 1.08 | 1.24 | 51.97% | 49.26% | 0.0225 |
| **Alt_Macro_Alpha_XS** | 9.42% | 9.91% | 0.95 | 67.66% | 0.43 | -21.85% | 0.96 | 1.18 | 52.75% | 49.57% | 0.0168 |
| **Alt_Macro_Alpha_TS** | 11.95% | 11.26% | 1.06 | 79.05% | 0.50 | -23.91% | 1.07 | 1.20 | 53.31% | 50.21% | 0.0168 |
| **Alt_Macro_Alpha_NoRoll** | 3.00% | 2.56% | 1.17 | 87.57% | 0.51 | -5.85% | 1.23 | nan | 50.79% | 0.00% | 0.0000 |

---

## Equity Curves

![Alpha Equity Curves](figures/alpha_equity_curves.png)

## Drawdown Charts

![Alpha Drawdowns](figures/alpha_drawdowns.png)

## Capacity Decay

![Capacity Decay](figures/alpha_capacity_decay.png)

## Capacity-Adjusted Sharpe Decay Table

This table shows the decay of each alpha's Sharpe ratio at different levels of Assets Under Management (AUM) in RMB.

| Alpha Name | Sharpe at 0 | Sharpe at 10M | Sharpe at 50M | Sharpe at 100M | Sharpe at 500M |
|---|---|---|---|---|---|
| **HTFC_Alpha19_tsrank_mom_rev** | -0.89 | -5.94 | -5.93 | -5.92 | -5.92 |
| **KalmanFilter_BOS** | -0.89 | -7.90 | -7.89 | -7.89 | -7.89 |
| **HTFC_Alpha1_meanclose12** | 0.02 | -6.15 | -6.15 | -6.15 | -6.15 |
| **HTFC_Alpha5_skew20** | -0.48 | -8.69 | -8.70 | -8.70 | -8.70 |
| **EWMA_32_64_CTA** | 0.38 | -4.46 | -4.46 | -4.46 | -4.46 |
| **ForeignAg_LeadLag** | 1.02 | -1.30 | -1.38 | -1.40 | -1.42 |
| **Alt_Macro_Alpha_XS** | 0.95 | -2.22 | -2.40 | -2.44 | -2.48 |
| **Alt_Macro_Alpha_TS** | 1.06 | -1.63 | -2.34 | -2.51 | -2.70 |

## Key Findings and Interpretations

