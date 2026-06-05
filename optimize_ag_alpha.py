#!/usr/bin/env python3
"""
Ultra-fast parameter optimization script for Agricultural Lead-Lag Alpha.
Performs coordinate descent over N in [3, 60] to maximize portfolio Sharpe ratio.
Uses pre-pivoted vectorized calculations for sub-millisecond evaluation in the inner loop.
"""
import os
import sys
import numpy as np
import pandas as pd
from evaluate_alpha import evaluate_alpha

DATA_DIR = '/home/hallo/data/ricecta/data/dominant_daily'
ALT_DATA_DIR = '/home/hallo/data/ricecta/data_alt'
SYMBOLS = ['C', 'M', 'Y', 'P', 'CF', 'SR']

ALL_SYMBOLS = [
    'C', 'M', 'Y', 'P', 'V', 'J', 'JD', 'I',
    'CU', 'AL', 'AU', 'AG', 'RB', 'RU', 'NI', 'SN',
    'SC', 'CF', 'SR', 'TA', 'MA', 'SA', 'TF'
]

def load_data():
    dfs = {}
    for sym in ALL_SYMBOLS:
        p_path = os.path.join(DATA_DIR, f"{sym}.parquet")
        if os.path.exists(p_path):
            df = pd.read_parquet(p_path)
            df.index = pd.to_datetime(df.index)
            df['returns'] = df['close'].pct_change()
            df['symbol'] = sym
            dfs[sym] = df
            
    return dfs

def run_optimization(use_cubed=True):
    print("=== Loading daily data ===")
    dfs = load_data()
    
    # Pre-load foreign agricultural data for optimization
    alt_dfs = {}
    for sym in SYMBOLS:
        alt_path = os.path.join(ALT_DATA_DIR, f"{sym}.parquet")
        df_alt = pd.read_parquet(alt_path)
        df_alt.index = pd.to_datetime(df_alt.index)
        alt_dfs[sym] = df_alt.sort_index()

    # Pre-pivot asset returns for all 23 symbols
    # Pivot all returns to shape (dates, 23_symbols)
    list_rets = []
    for sym in ALL_SYMBOLS:
        if sym in dfs:
            s = dfs[sym]['returns'].copy()
            s.name = sym
            list_rets.append(s)
    asset_returns = pd.concat(list_rets, axis=1).fillna(0.0).astype(np.float32)
    dates_index = asset_returns.index

    # Pre-calculate close prices and indices for speed
    close_prices = {}
    for sym in SYMBOLS:
        close_prices[sym] = dfs[sym]['close'].copy()

    # Helper function for ultra-fast Sharpe calculation in the inner loop
    def get_portfolio_sharpe_fast(n_dict):
        signals_dict = {}
        for sym in SYMBOLS:
            close_dom = close_prices[sym]
            close_alt = alt_dfs[sym]['close']
            
            dom_ret = close_dom.pct_change(n_dict[sym])
            for_ret = close_alt.pct_change(n_dict[sym])
            # Timezone-safe alignment (shift 1 on foreign calendar, reindex, forward-fill)
            for_ret_safe = for_ret.shift(1).reindex(dates_index).ffill()
            
            diff = dom_ret - for_ret_safe
            if use_cubed:
                signals_dict[sym] = (diff ** 3).astype(np.float32)
            else:
                signals_dict[sym] = diff.astype(np.float32)
                
        # Combine signals to DataFrame
        signals = pd.DataFrame(signals_dict, index=dates_index)
        
        # Standardize weights cross-sectionally
        demeaned = signals.sub(signals.mean(axis=1), axis=0)
        abs_sum = demeaned.abs().sum(axis=1)
        weights = demeaned.div(abs_sum.replace(0.0, np.nan), axis=0).fillna(0.0).astype(np.float32)
        
        # Align weights with the full asset list (shape: dates, 23_symbols)
        weights_full = weights.reindex(columns=asset_returns.columns, fill_value=0.0)
        weights_shifted = weights_full.shift(1).fillna(0.0)
        
        # Calculate daily portfolio returns
        port_returns = (weights_shifted * asset_returns).sum(axis=1)
        
        mean_ret = port_returns.mean()
        std_ret = port_returns.std()
        if std_ret > 0:
            return (mean_ret / std_ret) * np.sqrt(252)
        else:
            return -999.0

    # Starting values (linear model results)
    current_n = {'C': 3, 'M': 55, 'Y': 4, 'P': 56, 'CF': 50, 'SR': 42}
    
    best_sharpe = get_portfolio_sharpe_fast(current_n)
    print(f"Initial Portfolio Sharpe: {best_sharpe:.4f}")
    
    N_choices = [3, 4, 5, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
    improved = True
    step = 0
    
    while improved and step < 5:
        improved = False
        for sym in SYMBOLS:
            best_val = current_n[sym]
            for N in N_choices:
                if N == current_n[sym]:
                    continue
                test_n = current_n.copy()
                test_n[sym] = N
                sh = get_portfolio_sharpe_fast(test_n)
                if sh > best_sharpe:
                    best_sharpe = sh
                    best_val = N
                    improved = True
            if current_n[sym] != best_val:
                print(f"Step {step}: Updated {sym} from {current_n[sym]} to {best_val}. Portfolio Sharpe: {best_sharpe:.4f}")
                current_n[sym] = best_val
        step += 1
        
    print("\n=== Optimization Complete ===")
    print("Optimal Ns (Cubed):", current_n)
    print(f"Final Frictionless Sharpe: {best_sharpe:.4f}")
    
    # Run a single full evaluation once to print complete metrics
    print("\nRunning full evaluation on optimized parameters...")
    merged_dfs = []
    for sym in ALL_SYMBOLS:
        df = dfs[sym].copy()
        if sym in current_n:
            N = current_n[sym]
            df_alt = alt_dfs[sym]
            dom_ret = df['close'].pct_change(N)
            for_ret = df_alt['close'].pct_change(N)
            for_ret_safe = for_ret.shift(1).reindex(df.index).ffill()
            diff = dom_ret - for_ret_safe
            if use_cubed:
                df['ForeignAg_LeadLag'] = (diff ** 3).astype(np.float32)
            else:
                df['ForeignAg_LeadLag'] = diff.astype(np.float32)
        else:
            df['ForeignAg_LeadLag'] = np.nan
        df = df.reset_index().rename(columns={'index': 'date'})
        merged_dfs.append(df[['date', 'symbol', 'close', 'volume', 'returns', 'ForeignAg_LeadLag']])
        
    df_all = pd.concat(merged_dfs).set_index(['date', 'symbol']).sort_index()
    res = evaluate_alpha(df_all, 'ForeignAg_LeadLag', tc_rate=0.0005) # with 5 bps transaction costs
    print("\nPortfolio Metrics with 5 bps Transaction Cost:")
    print(f"  Sharpe Ratio: {res.get('sharpe_ratio', 0.0):.4f}")
    print(f"  Annualized Return: {res.get('annualized_return', 0.0)*100:.2f}%")
    print(f"  Annualized Volatility: {res.get('annualized_vol', 0.0)*100:.2f}%")
    print(f"  Max Drawdown: {res.get('max_drawdown', 0.0)*100:.2f}%")
    print(f"  Calmar Ratio: {res.get('calmar_ratio', 0.0):.4f}")
    print(f"  Sortino Ratio: {res.get('sortino_ratio', 0.0):.4f}")
    print(f"  Information Coefficient (IC): {res.get('ic', 0.0):.4f}")
    print(f"  Capacity Sharpe (AUM 500M): {res.get('capacity_sharpes', {}).get(500000000, 0.0):.4f}")
    
    return current_n

if __name__ == '__main__':
    use_cubed_arg = True
    if len(sys.argv) > 1 and sys.argv[1].lower() == '--linear':
        use_cubed_arg = False
    run_optimization(use_cubed=use_cubed_arg)
