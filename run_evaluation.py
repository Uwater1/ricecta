#!/usr/bin/env python3
"""
Main evaluation pipeline runner.
Computes the 5 alphas, evaluates them on the 23 symbols, and prints/saves the summary report.
"""
import os
import pandas as pd
import numpy as np
from alphas import compute_alphas
from evaluate_alpha import evaluate_alpha

# Paths
DATA_DIR = '/home/hallo/data/ricecta/data/dominant_daily'
SPOT_DIR = '/home/hallo/data/ricecta/data/spot_basis'

# 23 underlyings
SYMBOLS = [
    'C', 'M', 'Y', 'P', 'V', 'J', 'JD', 'I',  # DCE
    'CU', 'AL', 'AU', 'AG', 'RB', 'RU', 'NI', 'SN', # SHFE
    'SC', # INE
    'CF', 'SR', 'TA', 'MA', 'SA', # CZCE
    'TF' # CFFEX
]

ALPHAS = [
    'HTFC_Alpha19_tsrank_mom_rev',
    'KalmanFilter_BOS',
    'HTFC_Alpha1_meanclose12',
    'HTFC_Alpha5_skew20',
    'EWMA_32_64_CTA'
]

def run():
    print("=== Loading daily data and computing alphas ===")
    df_data = compute_alphas(DATA_DIR, SPOT_DIR, SYMBOLS)
    if df_data.empty:
        print("[ERROR] No data processed!")
        return
        
    print(f"Data shape: {df_data.shape}. Date range: {df_data.index.levels[0].min().date()} to {df_data.index.levels[0].max().date()}")
    
    # First, calculate frictionless Sharpe ratios for all 5 alphas to serve as the multiple testing pool for DSR
    raw_sharpes = {}
    for alpha in ALPHAS:
        # Evaluate without all_sharpes to get simple metric dict
        metrics = evaluate_alpha(df_data, alpha, all_sharpes=None, N=5, tc_rate=0.0)
        raw_sharpes[alpha] = metrics.get("sharpe_ratio", 0.0)
        
    print("\nFrictionless Sharpe Ratios (Multiple Testing Pool):")
    for k, v in raw_sharpes.items():
        print(f"  {k}: {v:.4f}")
        
    all_sharpe_list = list(raw_sharpes.values())
    
    # Evaluate each alpha with DSR and transaction costs (5 bps)
    results = {}
    for alpha in ALPHAS:
        print(f"\nEvaluating alpha: {alpha}...")
        metrics = evaluate_alpha(df_data, alpha, all_sharpes=all_sharpe_list, N=5, tc_rate=0.0005)
        results[alpha] = metrics
        
    # Generate markdown report
    report = "# Alpha Performance Evaluation Report\n\n"
    report += "This report evaluates the performance of the 5 requested alphas across 23 Chinese commodity futures from 2021 to 2026.\n\n"
    
    report += "## Performance Metrics Summary Table\n\n"
    report += "| Alpha Name | Ann. Return | Ann. Vol | Sharpe | Deflated Sharpe (DSR) | Calmar | MaxDD | Sortino | Profit Factor | Win Rate | Hit Rate | IC (Rank) |\n"
    report += "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    
    for alpha in ALPHAS:
        m = results[alpha]
        if not m:
            continue
        report += f"| **{alpha}** | {m['annualized_return']*100:.2f}% | {m['annualized_vol']*100:.2f}% | {m['sharpe_ratio']:.2f} | {m['deflated_sharpe_ratio']*100:.2f}% | {m['calmar_ratio']:.2f} | {m['max_drawdown']*100:.2f}% | {m['sortino_ratio']:.2f} | {m['profit_factor']:.2f} | {m['win_rate']*100:.2f}% | {m['hit_rate']*100:.2f}% | {m['ic']:.4f} |\n"
        
    report += "\n---\n\n"
    
    report += "## Capacity-Adjusted Sharpe Decay Table\n\n"
    report += "This table shows the decay of each alpha's Sharpe ratio at different levels of Assets Under Management (AUM) in RMB.\n\n"
    report += "| Alpha Name | Sharpe at 0 | Sharpe at 10M | Sharpe at 50M | Sharpe at 100M | Sharpe at 500M |\n"
    report += "|---|---|---|---|---|---|\n"
    
    for alpha in ALPHAS:
        m = results[alpha]
        if not m or "capacity_sharpes" not in m:
            continue
        cs = m["capacity_sharpes"]
        report += f"| **{alpha}** | {cs[0]:.2f} | {cs[10000000]:.2f} | {cs[50000000]:.2f} | {cs[100000000]:.2f} | {cs[500000000]:.2f} |\n"
        
    report += "\n## Key Findings and Interpretations\n\n"
    
    # Print the report to stdout
    print("\n" + report)
    
    # Save the report
    with open("alpha_evaluation_report.md", "w") as f:
        f.write(report)
    print("Report saved to alpha_evaluation_report.md")

if __name__ == '__main__':
    run()
