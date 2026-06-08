#!/usr/bin/env python3
"""
Initial screening pipeline: matches commodities with their candidate factors,
aligns them to avoid look-ahead bias, computes Pearson/Spearman stats
across multiple horizons, and outputs the results.
"""
import os
import re
import pandas as pd
import numpy as np
import scipy.stats as stats
import warnings

warnings.filterwarnings('ignore')

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_DIR = os.path.join(_SCRIPT_DIR, 'data')
DAILY_DIR = os.path.join(BASE_DIR, 'dominant_daily')
MACRO_DIR = os.path.join(BASE_DIR, 'macro_factors')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

SYMBOLS = [
    'C', 'M', 'Y', 'P', 'V', 'J', 'JD', 'I',  # DCE
    'CU', 'AL', 'AU', 'AG', 'RB', 'RU', 'NI', 'SN', # SHFE
    'SC', # INE
    'CF', 'SR', 'TA', 'MA', 'SA', # CZCE
    'TF' # CFFEX
]

def parse_markdown(filepath):
    symbol_to_factors = {}
    current_symbol = None
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        m_sym = re.search(r'### 品种:[^(]+\(([^)]+)\)', line)
        if m_sym:
            current_symbol = m_sym.group(1).strip()
            symbol_to_factors[current_symbol] = []
            continue
        if current_symbol and line.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9', '0')):
            m_fac = re.search(r'\x60([^\x60]+)\x60', line)
            if m_fac:
                symbol_to_factors[current_symbol].append(m_fac.group(1).strip())
    return symbol_to_factors

def calculate_t_stat(r, n):
    if n <= 2 or abs(r) >= 1.0:
        return 0.0
    return r * np.sqrt((n - 2) / (1 - r**2))

def run_correlation_test():
    md_path = os.path.join(_SCRIPT_DIR, 'potential_alt_alphas.md')
    symbol_to_factors = parse_markdown(md_path)
    
    rows = []
    
    for symbol in SYMBOLS:
        price_path = os.path.join(DAILY_DIR, f"{symbol}.parquet")
        if not os.path.exists(price_path):
            continue
            
        df_price = pd.read_parquet(price_path)
        if df_price.empty:
            continue
            
        if not isinstance(df_price.index, pd.DatetimeIndex):
            df_price.index = pd.to_datetime(df_price.index)
        df_price = df_price.sort_index()
        
        # Calculate daily returns and future returns
        df_price['ret'] = df_price['close'].pct_change()
        df_price['fwd_ret_1'] = df_price['ret'].shift(-1)
        df_price['fwd_ret_5'] = df_price['close'].pct_change(5).shift(-5)
        df_price['fwd_ret_20'] = df_price['close'].pct_change(20).shift(-20)
        df_price['fwd_ret_30'] = df_price['close'].pct_change(30).shift(-30)
        df_price['fwd_ret_40'] = df_price['close'].pct_change(40).shift(-40)
        
        trading_dates = df_price.index
        all_dates = pd.date_range(start=trading_dates.min(), end=trading_dates.max(), freq='D')
        
        candidate_factors = symbol_to_factors.get(symbol, [])
        for raw_factor in candidate_factors:
            filename = re.sub(r'[\\/*?:"<>|]', '_', raw_factor) + ".parquet"
            factor_path = os.path.join(MACRO_DIR, filename)
            if not os.path.exists(factor_path):
                continue
                
            df_fac = pd.read_parquet(factor_path)
            if df_fac.empty:
                continue
                
            # Clean and index by info_date
            if 'info_date' in df_fac.index.names:
                df_fac = df_fac.reset_index()
            
            df_fac['info_date'] = pd.to_datetime(df_fac['info_date'])
            df_fac = df_fac.set_index('info_date').sort_index()
            df_fac = df_fac[~df_fac.index.duplicated(keep='last')]
            
            # 1. Level signal representation (shifted by 1 day to prevent look-ahead bias)
            val_daily = df_fac['value'].reindex(all_dates).ffill().shift(1)
            s_level = val_daily.reindex(trading_dates)
            
            # 2. Diff signal representation (change at release, ffilled, shifted 1 day)
            fac_diff = df_fac['value'].diff()
            diff_daily = fac_diff.reindex(all_dates).ffill().shift(1)
            s_diff = diff_daily.reindex(trading_dates)
            
            # 3. Z-score signal representation (rolling 252-day Z-score of level)
            s_zscore = (s_level - s_level.rolling(252).mean()) / s_level.rolling(252).std()
            
            signals = {
                'level': s_level,
                'diff': s_diff,
                'zscore': s_zscore
            }
            
            # Compute correlations for each signal representation and horizon
            for sig_name, sig_series in signals.items():
                for horizon in [1, 5, 20, 30, 40]:
                    fwd_col = f"fwd_ret_{horizon}"
                    
                    # Align and drop NaNs
                    df_corr = pd.DataFrame({'sig': sig_series, 'fwd': df_price[fwd_col]}).dropna()
                    n_obs = len(df_corr)
                    if n_obs < 30:
                        continue
                        
                    # Pearson
                    r_pears, p_pears = stats.pearsonr(df_corr['sig'], df_corr['fwd'])
                    t_pears = calculate_t_stat(r_pears, n_obs)
                    
                    # Spearman
                    r_spear, p_spear = stats.spearmanr(df_corr['sig'], df_corr['fwd'])
                    t_spear = calculate_t_stat(r_spear, n_obs)
                    
                    rows.append({
                        'symbol': symbol,
                        'factor': raw_factor,
                        'representation': sig_name,
                        'horizon': horizon,
                        'n_obs': n_obs,
                        'pearson_corr': r_pears,
                        'pearson_t': t_pears,
                        'pearson_p': p_pears,
                        'spearman_corr': r_spear,
                        'spearman_t': t_spear,
                        'spearman_p': p_spear
                    })
                    
    df_results = pd.DataFrame(rows)
    csv_path = os.path.join(RESULTS_DIR, 'initial_correlation_results.csv')
    df_results.to_csv(csv_path, index=False)
    print(f"Saved {len(df_results)} rows of correlation results to: {csv_path}")
    
    # Filter for best-performing factor configuration per symbol based on absolute Spearman t-stat for fwd_ret_5
    df_f5 = df_results[df_results['horizon'] == 5].copy()
    if not df_f5.empty:
        df_f5['abs_spearman_t'] = df_f5['spearman_t'].abs()
        idx_best = df_f5.groupby('symbol')['abs_spearman_t'].idxmax()
        df_best = df_f5.loc[idx_best].sort_values('symbol')
        
        print("\n=== Best Alternative Data Factors per Symbol (fwd_ret_5) ===")
        print(df_best[['symbol', 'factor', 'representation', 'spearman_corr', 'spearman_t', 'spearman_p']].to_string(index=False))
        
        # Save a summary JSON or CSV for alphas.py to import dynamically
        best_path = os.path.join(RESULTS_DIR, 'best_factors_summary.csv')
        df_best.to_csv(best_path, index=False)
        print(f"\nSaved best factors summary to: {best_path}")

    # Top 3 factor configurations per symbol based on absolute Spearman t-stat for fwd_ret_5
    if not df_results.empty:
        # Save the full results containing all horizons for reference
        full_results_path = os.path.join(RESULTS_DIR, 'all_correlation_results.csv')
        df_results.to_csv(full_results_path, index=False)
        print(f"Saved all correlation results to: {full_results_path}")
        
        # Find top 3 factors per symbol for fwd_ret_5
        df_f5 = df_results[df_results['horizon'] == 5].copy()
        if not df_f5.empty:
            df_f5['abs_spearman_t'] = df_f5['spearman_t'].abs()
            df_top3_f5 = df_f5.sort_values(['symbol', 'abs_spearman_t'], ascending=[True, False]).groupby('symbol').head(3)
            
            top3_f5_path = os.path.join(RESULTS_DIR, 'top3_factors_f5_summary.csv')
            df_top3_f5.to_csv(top3_f5_path, index=False)
            print(f"\nSaved top 3 factors for fwd_ret_5 to: {top3_f5_path}")
            
            print("\n=== Top 3 Alternative Data Factors per Symbol (fwd_ret_5) ===")
            print(df_top3_f5[['symbol', 'factor', 'representation', 'spearman_corr', 'spearman_t']].to_string(index=False))

        # Find top 3 factors per symbol for fwd_ret_20
        df_f20 = df_results[df_results['horizon'] == 20].copy()
        if not df_f20.empty:
            df_f20['abs_spearman_t'] = df_f20['spearman_t'].abs()
            df_top3_f20 = df_f20.sort_values(['symbol', 'abs_spearman_t'], ascending=[True, False]).groupby('symbol').head(3)
            
            top3_f20_path = os.path.join(RESULTS_DIR, 'top3_factors_f20_summary.csv')
            df_top3_f20.to_csv(top3_f20_path, index=False)
            print(f"\nSaved top 3 factors for fwd_ret_20 to: {top3_f20_path}")

        # Also print best factors for long term horizons (20d, 30d and 40d) summary to assess macroecon long term effects
        for h in [20, 30, 40]:
            df_h = df_results[df_results['horizon'] == h].copy()
            if not df_h.empty:
                df_h['abs_spearman_t'] = df_h['spearman_t'].abs()
                df_best_h = df_h.sort_values(['symbol', 'abs_spearman_t'], ascending=[True, False]).groupby('symbol').head(1)
                best_h_path = os.path.join(RESULTS_DIR, f'best_factors_f{h}_summary.csv')
                df_best_h.to_csv(best_h_path, index=False)
                
                print(f"\n=== Best Alternative Data Factors per Symbol (fwd_ret_{h}) ===")
                print(df_best_h[['symbol', 'factor', 'representation', 'spearman_corr', 'spearman_t']].to_string(index=False))

if __name__ == '__main__':
    run_correlation_test()
