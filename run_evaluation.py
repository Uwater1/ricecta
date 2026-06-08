#!/usr/bin/env python3
"""
Main evaluation pipeline runner.
Computes the 5 alphas, evaluates them on the 23 symbols, and prints/saves the summary report.
"""
import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
from alphas import compute_alphas
from evaluate_alpha import evaluate_alpha

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

FIGURES_DIR = os.path.join(_SCRIPT_DIR, 'figures')
os.makedirs(FIGURES_DIR, exist_ok=True)

# Paths
DATA_DIR = os.path.join(_SCRIPT_DIR, 'data', 'dominant_daily')
SPOT_DIR = os.path.join(_SCRIPT_DIR, 'data', 'spot_basis')

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
    'EWMA_32_64_CTA',
    'ForeignAg_LeadLag',
    'Alt_Macro_Alpha_XS',
    'Alt_Macro_Alpha_TS'
]

def run():
    global ALPHAS
    
    # Parse CLI argument for specific alpha
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.isdigit():
            idx = int(arg) - 1
            if 0 <= idx < len(ALPHAS):
                ALPHAS = [ALPHAS[idx]]
                print(f"Filtering to evaluate single alpha by index: {ALPHAS[0]}")
            else:
                print(f"[ERROR] Alpha index {arg} out of range (1-{len(ALPHAS)})")
                sys.exit(1)
        elif arg in ALPHAS:
            ALPHAS = [arg]
            print(f"Filtering to evaluate single alpha by name: {ALPHAS[0]}")
        else:
            print(f"[ERROR] Unknown alpha name/index: {arg}")
            sys.exit(1)

    print("=== Loading daily data and computing alphas ===")
    df_data = compute_alphas(DATA_DIR, SPOT_DIR, SYMBOLS)
    if df_data.empty:
        print("[ERROR] No data processed!")
        return
        
    print(f"Data shape: {df_data.shape}. Date range: {df_data.index.levels[0].min().date()} to {df_data.index.levels[0].max().date()}")
    
    # First, calculate frictionless Sharpe ratios for all alphas to serve as the multiple testing pool for DSR
    raw_sharpes = {}
    for alpha in ALPHAS:
        col = 'Alt_Macro_Alpha' if alpha in ['Alt_Macro_Alpha_XS', 'Alt_Macro_Alpha_TS'] else alpha
        is_ts = (alpha == 'Alt_Macro_Alpha_TS')
        metrics = evaluate_alpha(df_data, col, all_sharpes=None, N=len(ALPHAS), tc_rate=0.0, demean=not is_ts)
        raw_sharpes[alpha] = metrics.get("sharpe_ratio", 0.0)
        
    print("\nFrictionless Sharpe Ratios (Multiple Testing Pool):")
    for k, v in raw_sharpes.items():
        print(f"  {k}: {v:.4f}")
        
    all_sharpe_list = list(raw_sharpes.values())
    
    # Evaluate each alpha with DSR and transaction costs (5 bps)
    results = {}
    for alpha in ALPHAS:
        print(f"\nEvaluating alpha: {alpha}...")
        col = 'Alt_Macro_Alpha' if alpha in ['Alt_Macro_Alpha_XS', 'Alt_Macro_Alpha_TS'] else alpha
        is_ts = (alpha == 'Alt_Macro_Alpha_TS')
        metrics = evaluate_alpha(df_data, col, all_sharpes=all_sharpe_list, N=len(ALPHAS), tc_rate=0.0005, demean=not is_ts)
        results[alpha] = metrics
        
    # Generate markdown report
    report = "# Alpha Performance Evaluation Report\n\n"
    report += f"This report evaluates the performance of the {len(ALPHAS)} alphas across 23 Chinese commodity futures from 2021 to 2026.\n\n"
    
    report += "## Performance Metrics Summary Table\n\n"
    report += "| Alpha Name | Ann. Return | Ann. Vol | Sharpe | Deflated Sharpe (DSR) | Calmar | MaxDD | Sortino | Profit Factor | Win Rate | Hit Rate | IC (Rank) |\n"
    report += "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    
    for alpha in ALPHAS:
        m = results[alpha]
        if not m:
            continue
        report += f"| **{alpha}** | {m['annualized_return']*100:.2f}% | {m['annualized_vol']*100:.2f}% | {m['sharpe_ratio']:.2f} | {m['deflated_sharpe_ratio']*100:.2f}% | {m['calmar_ratio']:.2f} | {m['max_drawdown']*100:.2f}% | {m['sortino_ratio']:.2f} | {m['profit_factor']:.2f} | {m['win_rate']*100:.2f}% | {m['hit_rate']*100:.2f}% | {m['ic']:.4f} |\n"
        
    report += "\n---\n\n"
    
    # --- Generate Plots ---
    print("Generating plots...")

    # 1. Equity Curves
    fig, ax = plt.subplots(figsize=(14, 7))
    for alpha in ALPHAS:
        m = results.get(alpha, {})
        cum = m.get('cum_returns')
        if cum is not None and not cum.empty:
            rebased = cum / cum.iloc[0]
            ax.plot(rebased.index, rebased, label=f"{alpha} (Sharpe={m['sharpe_ratio']:.2f})")
    ax.set_title("Alpha Equity Curves (Cumulative Net Returns)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity (rebased to 1.0)")
    ax.legend(fontsize=8)
    ax.grid(True, linestyle='--', alpha=0.5)
    fig.tight_layout()
    equity_path = os.path.join(FIGURES_DIR, 'alpha_equity_curves.png')
    fig.savefig(equity_path, dpi=200)
    plt.close(fig)
    print(f"  Saved equity curves to {equity_path}")

    # 2. Drawdown Plot
    fig, ax = plt.subplots(figsize=(14, 6))
    for alpha in ALPHAS:
        m = results.get(alpha, {})
        dd = m.get('drawdown')
        if dd is not None and not dd.empty:
            ax.fill_between(dd.index, dd * 100, 0, alpha=0.3, label=f"{alpha} (MaxDD={m['max_drawdown']*100:.1f}%)")
    ax.set_title("Alpha Underwater Drawdown Charts")
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown (%)")
    ax.legend(fontsize=8)
    ax.grid(True, linestyle='--', alpha=0.5)
    fig.tight_layout()
    dd_path = os.path.join(FIGURES_DIR, 'alpha_drawdowns.png')
    fig.savefig(dd_path, dpi=200)
    plt.close(fig)
    print(f"  Saved drawdown plots to {dd_path}")

    # 3. Capacity Decay Bar Chart
    aum_labels = ['0', '10M', '50M', '100M', '500M']
    aum_keys = [0, 10_000_000, 50_000_000, 100_000_000, 500_000_000]
    valid_alphas = [a for a in ALPHAS if results.get(a, {}).get('capacity_sharpes')]
    if valid_alphas:
        x = np.arange(len(valid_alphas))
        width = 0.15
        fig, ax = plt.subplots(figsize=(14, 6))
        for i, (aum, label) in enumerate(zip(aum_keys, aum_labels)):
            vals = [results[a]['capacity_sharpes'].get(aum, 0.0) for a in valid_alphas]
            ax.bar(x + i * width, vals, width, label=f'AUM {label}')
        ax.set_xlabel('Alpha')
        ax.set_ylabel('Sharpe Ratio')
        ax.set_title('Capacity-Adjusted Sharpe Decay by AUM Level')
        ax.set_xticks(x + width * 2)
        ax.set_xticklabels(valid_alphas, rotation=30, ha='right', fontsize=8)
        ax.legend()
        ax.grid(True, axis='y', linestyle='--', alpha=0.5)
        fig.tight_layout()
        cap_path = os.path.join(FIGURES_DIR, 'alpha_capacity_decay.png')
        fig.savefig(cap_path, dpi=200)
        plt.close(fig)
        print(f"  Saved capacity decay chart to {cap_path}")
    else:
        cap_path = None

    # Embed plots into the report
    report += "## Equity Curves\n\n"
    report += f"![Alpha Equity Curves]({equity_path})\n\n"
    report += "## Drawdown Charts\n\n"
    report += f"![Alpha Drawdowns]({dd_path})\n\n"
    if cap_path:
        report += "## Capacity Decay\n\n"
        report += f"![Capacity Decay]({cap_path})\n\n"

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
