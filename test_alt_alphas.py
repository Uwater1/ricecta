#!/usr/bin/env python3
"""
Initial screening pipeline: matches commodities with their candidate factors,
aligns them to avoid look-ahead bias, computes Pearson/Spearman stats
across mixed horizons (5d, 20d fixed + H1-H3 contract-switch), and outputs the results.

Horizons:
  5d  = fixed 5-trading-day forward return (short-term momentum/reaction)
  20d = fixed 20-trading-day forward return (medium-term adjustment)
  H1  = forward return to the 1st next dominant contract switch date
  H2  = forward return to the 2nd next dominant contract switch date
  H3  = forward return to the 3rd next dominant contract switch date
"""
import os
import re
import pandas as pd
import numpy as np
import scipy.stats as stats
import warnings

from evaluate_hold_strategy import get_dominant_switch_dates

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

HORIZONS = ['5d', '20d', 'H1', 'H2', 'H3']
SWITCH_HORIZONS = ['H1', 'H2', 'H3']  # contract-switch-based only

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

def compute_switch_forward_returns(df_price, switch_dates):
    """Compute forward returns to the next 1st-3rd dominant contract switch dates.

    Also adds fixed 5-day and 20-day calendar forward returns.
    Returns a DataFrame with columns fwd_ret_5d, fwd_ret_20d, fwd_ret_H1..H3
    and days_H1..H3, aligned to df_price's index.
    """
    trading_dates = df_price.index
    close = df_price['close'].values.astype(np.float64)
    n = len(trading_dates)
    td_ts = trading_dates.values

    # Convert switch dates to numpy datetime64 for fast searchsorted
    sd_ts = np.sort(np.array(switch_dates, dtype='datetime64[ns]'))

    # For each trading date, find index of the first switch date >= that trading date
    # side='left' gives the first position where sd_ts[pos] >= td_ts[i]
    first_switch_pos = np.searchsorted(sd_ts, td_ts, side='left')

    result = pd.DataFrame(index=trading_dates)

    # Fixed calendar-day forward returns (short-term / medium-term)
    close_series = df_price['close']
    result['fwd_ret_5d'] = close_series.pct_change(5).shift(-5).values
    result['fwd_ret_20d'] = close_series.pct_change(20).shift(-20).values

    for i, label in enumerate(SWITCH_HORIZONS, start=1):
        # The target switch is the i-th switch from now (0-indexed: first_switch_pos + i - 1)
        target_pos = first_switch_pos + (i - 1)
        # Mask: target_pos must be within the switch dates array
        valid = (target_pos < len(sd_ts))

        # For valid positions, map from switch array to trading date positions
        target_td_pos = np.full(n, n, dtype=np.int64)  # default to out-of-bounds
        valid_sd = sd_ts[target_pos[valid]]
        target_td_pos[valid] = np.searchsorted(td_ts, valid_sd, side='left')

        # Valid mask: target trading date position within bounds
        valid &= (target_td_pos < n)
        valid &= (target_td_pos >= 0)

        days_to_switch = np.full(n, -1, dtype=np.int32)
        days_to_switch[valid] = target_td_pos[valid] - np.arange(n)[valid]
        # Only keep positive forward windows
        valid &= (days_to_switch > 0)

        fwd_ret = np.full(n, np.nan)
        fwd_ret[valid] = close[target_td_pos[valid]] / close[np.arange(n)[valid]] - 1.0

        result[f'fwd_ret_{label}'] = fwd_ret
        result[f'days_{label}'] = days_to_switch

    return result

def run_correlation_test():
    md_path = os.path.join(_SCRIPT_DIR, 'potential_alt_alphas.md')
    symbol_to_factors = parse_markdown(md_path)
    
    rows = []
    horizon_days_stats = {}  # {symbol: {H1: median_days, H2: ..., ...}}
    
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
        
        # Load dominant contract switch dates (data-driven, per-symbol)
        try:
            switch_dates = get_dominant_switch_dates(symbol)
        except Exception as e:
            print(f"  Warning: could not load switch dates for {symbol}: {e}")
            continue
        
        if len(switch_dates) < 3:
            print(f"  Warning: {symbol} has fewer than 3 switch dates, skipping")
            continue
        
        # Compute forward returns (5d, 20d fixed + H1-H3 contract-switch)
        fwd_df = compute_switch_forward_returns(df_price, switch_dates)
        df_price = pd.concat([df_price, fwd_df], axis=1)
        
        # Record median calendar days per horizon for this symbol
        sym_days = {}
        for label in SWITCH_HORIZONS:
            d = fwd_df[f'days_{label}']
            valid_days = d[d > 0]
            sym_days[label] = int(valid_days.median()) if len(valid_days) > 0 else -1
        horizon_days_stats[symbol] = sym_days
        
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
            
            # Compute correlations for each signal representation and contract-switch horizon
            for sig_name, sig_series in signals.items():
                for horizon in HORIZONS:
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
    
    # Print median calendar days per horizon per symbol
    print("\n=== Median Calendar Days per Horizon per Symbol ===")
    for sym in SYMBOLS:
        if sym in horizon_days_stats:
            d = horizon_days_stats[sym]
            parts = []
            for label in HORIZONS:
                if label in d:
                    parts.append(f"{label}={d[label]:3d}d")
                else:
                    parts.append(f"{label}=  - ")
            print(f"  {sym:4s}: {'  '.join(parts)}")
    
    # Save horizon days stats
    days_df = pd.DataFrame(horizon_days_stats).T
    days_df.index.name = 'symbol'
    days_path = os.path.join(RESULTS_DIR, 'horizon_days_stats.csv')
    days_df.to_csv(days_path)
    print(f"\nSaved horizon days stats to: {days_path}")
    
    if df_results.empty:
        print("No correlation results computed.")
        return df_results, horizon_days_stats
    
    # Save the full results
    full_results_path = os.path.join(RESULTS_DIR, 'all_correlation_results.csv')
    df_results.to_csv(full_results_path, index=False)
    print(f"Saved all correlation results to: {full_results_path}")
    
    # Best factor per symbol for each horizon
    for h in HORIZONS:
        df_h = df_results[df_results['horizon'] == h].copy()
        if df_h.empty:
            continue
        df_h['abs_spearman_t'] = df_h['spearman_t'].abs()
        
        # Best 1 per symbol
        idx_best = df_h.groupby('symbol')['abs_spearman_t'].idxmax()
        df_best = df_h.loc[idx_best].sort_values('abs_spearman_t', ascending=False)
        best_h_path = os.path.join(RESULTS_DIR, f'best_factors_{h}_summary.csv')
        df_best.to_csv(best_h_path, index=False)
        
        print(f"\n=== Best Alternative Data Factors per Symbol ({h}) ===")
        print(df_best[['symbol', 'factor', 'representation', 'spearman_corr', 'spearman_t']].to_string(index=False))
        
        # Top 3 per symbol
        df_top3 = df_h.sort_values(['symbol', 'abs_spearman_t'], ascending=[True, False]).groupby('symbol').head(3)
        top3_path = os.path.join(RESULTS_DIR, f'top3_factors_{h}_summary.csv')
        df_top3.to_csv(top3_path, index=False)
        print(f"\n=== Top 3 Alternative Data Factors per Symbol ({h}) ===")
        print(df_top3[['symbol', 'factor', 'representation', 'spearman_corr', 'spearman_t']].to_string(index=False))

    return df_results, horizon_days_stats

if __name__ == '__main__':
    run_correlation_test()
