# Alpha Performance Evaluation Report

This report evaluates the performance of the 8 alphas across 23 Chinese commodity futures from 2021 to 2026.

## Performance Metrics Summary Table

| Alpha Name | Ann. Return | Ann. Vol | Sharpe | Deflated Sharpe (DSR) | Calmar | MaxDD | Sortino | Profit Factor | Win Rate | Hit Rate | IC (Rank) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **HTFC_Alpha19_tsrank_mom_rev** | -1.71% | 13.09% | -0.13 | 0.82% | -0.05 | -34.30% | -0.15 | 0.97 | 45.46% | 49.65% | 0.0174 |
| **KalmanFilter_BOS** | -9.49% | 10.93% | -0.87 | 0.00% | -0.23 | -42.09% | -0.82 | 0.84 | 48.31% | 48.77% | -0.0000 |
| **HTFC_Alpha1_meanclose12** | 10.80% | 46.24% | 0.23 | 4.36% | 0.22 | -50.11% | 0.32 | 1.08 | 47.04% | 49.92% | 0.0141 |
| **HTFC_Alpha5_skew20** | -6.83% | 11.14% | -0.61 | 0.02% | -0.18 | -37.58% | -0.60 | 0.88 | 48.14% | 49.75% | 0.0070 |
| **EWMA_32_64_CTA** | -36.67% | 50.36% | -0.73 | 0.00% | -0.39 | -94.38% | -0.57 | 0.78 | 52.75% | 50.04% | 0.0207 |
| **ForeignAg_LeadLag** | 23.93% | 20.54% | 1.16 | 69.00% | 1.08 | -22.14% | 1.28 | 1.29 | 51.57% | 48.76% | 0.0226 |
| **Alt_Macro_Alpha_XS** | 1.74% | 6.84% | 0.25 | 5.72% | 0.09 | -20.20% | 0.26 | 1.04 | 50.42% | 48.75% | 0.0200 |
| **Alt_Macro_Alpha_TS** | 9.87% | 12.17% | 0.81 | 37.57% | 0.42 | -23.24% | 0.83 | 1.15 | 52.20% | 50.40% | 0.0200 |

---

## Capacity-Adjusted Sharpe Decay Table

This table shows the decay of each alpha's Sharpe ratio at different levels of Assets Under Management (AUM) in RMB.

| Alpha Name | Sharpe at 0 | Sharpe at 10M | Sharpe at 50M | Sharpe at 100M | Sharpe at 500M |
|---|---|---|---|---|---|
| **HTFC_Alpha19_tsrank_mom_rev** | -0.13 | -0.14 | -0.16 | -0.17 | -0.23 |
| **KalmanFilter_BOS** | -0.87 | -0.88 | -0.90 | -0.91 | -0.97 |
| **HTFC_Alpha1_meanclose12** | 0.23 | 0.23 | 0.22 | 0.22 | 0.20 |
| **HTFC_Alpha5_skew20** | -0.61 | -0.62 | -0.63 | -0.64 | -0.67 |
| **EWMA_32_64_CTA** | -0.73 | -0.73 | -0.73 | -0.74 | -0.75 |
| **ForeignAg_LeadLag** | 1.16 | 1.16 | 1.15 | 1.14 | 1.11 |
| **Alt_Macro_Alpha_XS** | 0.25 | 0.25 | 0.25 | 0.25 | 0.25 |
| **Alt_Macro_Alpha_TS** | 0.81 | 0.81 | 0.81 | 0.81 | 0.81 |

## Key Findings and Interpretations

