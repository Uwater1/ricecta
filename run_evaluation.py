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
from alphas import compute_alphas, BEST_HOLD_PARAMS
from evaluate_alpha import evaluate_alpha, calculate_dsr
from evaluate_hold_strategy import (
    backtest_hold_strategy, load_symbol_contracts, load_metadata
)

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
    'Alt_Macro_Alpha_TS',
    'Alt_Macro_Alpha_NoRoll'
]

def evaluate_norolling_hold_strategy(df_data, symbols, tc_rate=0.0):
    """Evaluate the no-rolling macro alpha using the hold strategy backtest.

    Runs a per-symbol contract hold backtest using Alt_Macro_Alpha_NoRoll
    and aggregates results into an equal-weighted portfolio.
    """
    metadata = load_metadata()
    symbol_daily_returns = {}
    all_trades = []

    for symbol in symbols:
        if symbol not in BEST_HOLD_PARAMS:
            continue
        try:
            df_contracts = load_symbol_contracts(symbol)
        except FileNotFoundError:
            print(f"  Skipping {symbol} (no contract data)")
            continue

        H, k = BEST_HOLD_PARAMS[symbol]
        try:
            sig_series = df_data['Alt_Macro_Alpha_NoRoll'].xs(symbol, level='symbol')
        except KeyError:
            continue

        res = backtest_hold_strategy(
            symbol, sig_series, df_contracts, metadata, H, k,
            slippage=tc_rate
        )

        daily_ret = res.get('daily_returns')
        if daily_ret is not None and len(daily_ret) > 0:
            symbol_daily_returns[symbol] = daily_ret
        trades = res.get('trades', [])
        all_trades.extend(trades)
        if trades:
            print(f"  {symbol}: {len(trades)} trades, Sharpe={res['metrics']['sharpe']:.2f}")

    if not symbol_daily_returns:
        return {}

    # Equal-weight portfolio across symbols
    df_returns = pd.DataFrame(symbol_daily_returns)
    port_returns = df_returns.mean(axis=1).fillna(0.0)

    T = len(port_returns)
    if T == 0:
        return {}

    ann_return = port_returns.mean() * 252
    ann_vol = port_returns.std() * np.sqrt(252)
    sharpe = ann_return / ann_vol if ann_vol > 0 else 0.0

    cum_returns = (1.0 + port_returns).cumprod()
    running_max = cum_returns.cummax()
    drawdown = (cum_returns - running_max) / running_max
    max_dd = drawdown.min()

    neg_rets = port_returns[port_returns < 0]
    downside_std = np.sqrt((neg_rets ** 2).mean()) * np.sqrt(252) if len(neg_rets) > 0 else 0.0
    sortino = ann_return / downside_std if downside_std > 0 else 0.0

    calmar = ann_return / abs(max_dd) if max_dd != 0 else 0.0
    win_rate = (port_returns > 0).sum() / T if T > 0 else 0.0

    return {
        'annualized_return': ann_return,
        'annualized_vol': ann_vol,
        'sharpe_ratio': sharpe,
        'deflated_sharpe_ratio': 0.0,  # computed later with full pool
        'calmar_ratio': calmar,
        'max_drawdown': max_dd,
        'sortino_ratio': sortino,
        'profit_factor': float('nan'),
        'win_rate': win_rate,
        'hit_rate': 0.0,
        'ic': 0.0,
        'top_quintile_return': 0.0,
        'bottom_quintile_return': 0.0,
        'capacity_sharpes': {},
        'cum_returns': cum_returns,
        'drawdown': drawdown,
        'port_net_returns': port_returns
    }

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
        if alpha == 'Alt_Macro_Alpha_NoRoll':
            # NoRoll uses hold strategy backtest, not daily cross-sectional evaluation
            norolling_metrics = evaluate_norolling_hold_strategy(df_data, SYMBOLS, tc_rate=0.0)
            raw_sharpes[alpha] = norolling_metrics.get('sharpe_ratio', 0.0)
            continue
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
        if alpha == 'Alt_Macro_Alpha_NoRoll':
            print(f"\nEvaluating alpha: {alpha} (hold strategy)...")
            norolling_metrics = evaluate_norolling_hold_strategy(df_data, SYMBOLS, tc_rate=0.0005)
            if norolling_metrics:
                results[alpha] = norolling_metrics
            continue
        print(f"\nEvaluating alpha: {alpha}...")
        col = 'Alt_Macro_Alpha' if alpha in ['Alt_Macro_Alpha_XS', 'Alt_Macro_Alpha_TS'] else alpha
        is_ts = (alpha == 'Alt_Macro_Alpha_TS')
        metrics = evaluate_alpha(df_data, col, all_sharpes=all_sharpe_list, N=len(ALPHAS), tc_rate=0.0005, demean=not is_ts)
        results[alpha] = metrics
    
    # Compute DSR for NoRoll using the full Sharpe pool
    if 'Alt_Macro_Alpha_NoRoll' in results:
        noroll_port = results['Alt_Macro_Alpha_NoRoll'].get('port_net_returns')
        if noroll_port is not None and len(noroll_port) > 2:
            results['Alt_Macro_Alpha_NoRoll']['deflated_sharpe_ratio'] = calculate_dsr(
                noroll_port, all_sharpe_list, N=len(ALPHAS)
            )
        
    # Generate markdown report
    report = "# Alpha Performance Evaluation Report\n\n"
    report += f"This report evaluates the performance of the {len(ALPHAS)} alphas across 23 Chinese commodity futures from 2016 to 2026.\n\n"
    
    report += "## Performance Metrics Summary Table\n\n"
    report += "| Alpha Name | Ann. Return | Ann. Vol | Sharpe | Deflated Sharpe (DSR) | Calmar | MaxDD | Sortino | Profit Factor | Win Rate | Hit Rate | IC (Rank) |\n"
    report += "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    
    for alpha in ALPHAS:
        m = results.get(alpha)
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
    report += "![Alpha Equity Curves](figures/alpha_equity_curves.png)\n\n"
    report += "## Drawdown Charts\n\n"
    report += "![Alpha Drawdowns](figures/alpha_drawdowns.png)\n\n"
    if cap_path:
        report += "## Capacity Decay\n\n"
        report += "![Capacity Decay](figures/alpha_capacity_decay.png)\n\n"

    report += "## Capacity-Adjusted Sharpe Decay Table\n\n"
    report += "This table shows the decay of each alpha's Sharpe ratio at different levels of Assets Under Management (AUM) in RMB.\n\n"
    report += "| Alpha Name | Sharpe at 0 | Sharpe at 10M | Sharpe at 50M | Sharpe at 100M | Sharpe at 500M |\n"
    report += "|---|---|---|---|---|---|\n"
    
    for alpha in ALPHAS:
        m = results.get(alpha)
        if not m or not m.get("capacity_sharpes"):
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
