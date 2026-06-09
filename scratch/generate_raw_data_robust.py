#!/usr/bin/env python3
import sys
import os
import re
import pandas as pd
import numpy as np
import warnings

# Determine paths
_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(_SCRIPT_DIR)

from evaluate_hold_strategy import get_dominant_switch_dates

warnings.filterwarnings('ignore')

BASE_DIR = os.path.join(_SCRIPT_DIR, 'data')
DAILY_DIR = os.path.join(BASE_DIR, 'dominant_daily')
MACRO_DIR = os.path.join(BASE_DIR, 'macro_factors')
RESULTS_DIR = _SCRIPT_DIR

SWITCH_HORIZONS = ['H1', 'H2', 'H3']

def compute_switch_forward_returns(df_price, switch_dates):
    trading_dates = df_price.index
    close = df_price['close'].values.astype(np.float64)
    n = len(trading_dates)
    td_ts = trading_dates.values
    sd_ts = np.sort(np.array(switch_dates, dtype='datetime64[ns]'))

    first_switch_pos = np.searchsorted(sd_ts, td_ts, side='left')
    result = pd.DataFrame(index=trading_dates)

    # Identify indices where close price is negative or zero
    bad_start_mask = (close <= 0.0)

    # Calculate 5d forward returns
    fwd_ret_5d = np.full(n, np.nan)
    for t in range(n - 5):
        if not bad_start_mask[t] and close[t + 5] > 0.0:
            fwd_ret_5d[t] = close[t + 5] / close[t] - 1.0
            
    # Calculate 20d forward returns
    fwd_ret_20d = np.full(n, np.nan)
    for t in range(n - 20):
        if not bad_start_mask[t] and close[t + 20] > 0.0:
            fwd_ret_20d[t] = close[t + 20] / close[t] - 1.0

    result['fwd_ret_5d'] = fwd_ret_5d
    result['fwd_ret_20d'] = fwd_ret_20d

    for i, label in enumerate(SWITCH_HORIZONS, start=1):
        target_pos = first_switch_pos + (i - 1)
        fwd_ret = np.full(n, np.nan)
        
        for t in range(n):
            if bad_start_mask[t]:
                continue
            pos_idx = target_pos[t]
            if pos_idx < len(sd_ts):
                sd = sd_ts[pos_idx]
                td_idx = np.searchsorted(td_ts, sd, side='left')
                if 0 <= td_idx < n:
                    days = td_idx - t
                    if days > 0 and close[td_idx] > 0.0:
                        fwd_ret[t] = close[td_idx] / close[t] - 1.0
                        
        fwd_ret[~np.isfinite(fwd_ret)] = np.nan
        result[f'fwd_ret_{label}'] = fwd_ret

    # Clean returns that are outside [-0.9, 4.0]
    for c in ['fwd_ret_5d', 'fwd_ret_20d', 'fwd_ret_H1', 'fwd_ret_H2', 'fwd_ret_H3']:
        result.loc[(result[c] < -0.9) | (result[c] > 4.0), c] = np.nan

    return result

def main():
    # Load best robust factors summary
    summary_path = os.path.join(BASE_DIR, 'results', 'best_robust_factors_summary.csv')
    if not os.path.exists(summary_path):
        print(f"Error: {summary_path} not found.")
        sys.exit(1)
        
    df_summary = pd.read_csv(summary_path)
    
    # Filter for significant factors: absolute Newey-West spearman_t >= 1.96
    # (standard 95% confidence level threshold)
    df_sig = df_summary[df_summary['spearman_t'].abs() >= 1.96]
    print(f"Found {len(df_sig)} symbols with statistically significant robust factors (|t| >= 1.96):")
    print(df_sig[['symbol', 'factor', 'spearman_t', 'mean_nw_t_stat']])
    
    all_dfs = []
    
    for _, row in df_sig.iterrows():
        symbol = row['symbol']
        raw_factor = row['factor']
        
        price_path = os.path.join(DAILY_DIR, f"{symbol}.parquet")
        if not os.path.exists(price_path):
            print(f"Warning: {price_path} not found, skipping.")
            continue
            
        df_price = pd.read_parquet(price_path)
        if df_price.empty:
            continue
            
        if not isinstance(df_price.index, pd.DatetimeIndex):
            df_price.index = pd.to_datetime(df_price.index)
        df_price = df_price.sort_index()
        
        try:
            switch_dates = get_dominant_switch_dates(symbol)
        except Exception as e:
            print(f"Warning: could not load switch dates for {symbol}: {e}")
            continue
        
        fwd_df = compute_switch_forward_returns(df_price, switch_dates)
        
        trading_dates = df_price.index
        all_dates = pd.date_range(start=trading_dates.min(), end=trading_dates.max(), freq='D')
        
        filename = re.sub(r'[\\/*?:"<>|]', '_', raw_factor) + ".parquet"
        factor_path = os.path.join(MACRO_DIR, filename)
        if not os.path.exists(factor_path):
            print(f"Warning: {factor_path} not found for {symbol}, skipping.")
            continue
            
        df_fac = pd.read_parquet(factor_path)
        if df_fac.empty:
            continue
            
        if 'info_date' in df_fac.index.names:
            df_fac = df_fac.reset_index()
        
        df_fac['info_date'] = pd.to_datetime(df_fac['info_date'])
        df_fac = df_fac.set_index('info_date').sort_index()
        df_fac = df_fac[~df_fac.index.duplicated(keep='last')]
        
        # Level signal representation (shifted by 1 day)
        val_daily = df_fac['value'].reindex(all_dates).ffill().shift(1)
        s_level = val_daily.reindex(trading_dates)
        
        # Diff signal representation (shifted 1 day)
        fac_diff = df_fac['value'].diff()
        diff_daily = fac_diff.reindex(all_dates).ffill().shift(1)
        s_diff = diff_daily.reindex(trading_dates)
        
        # Z-score signal representation (rolling 252-day Z-score of level)
        s_zscore = (s_level - s_level.rolling(252).mean()) / s_level.rolling(252).std()
        
        df_aligned = pd.DataFrame(index=trading_dates)
        df_aligned['symbol'] = symbol
        df_aligned['factor'] = raw_factor
        df_aligned['factor_level'] = s_level
        df_aligned['factor_diff'] = s_diff
        df_aligned['factor_zscore'] = s_zscore
        df_aligned['fwd_ret_5d'] = fwd_df['fwd_ret_5d']
        df_aligned['fwd_ret_20d'] = fwd_df['fwd_ret_20d']
        df_aligned['fwd_ret_H1'] = fwd_df['fwd_ret_H1']
        df_aligned['fwd_ret_H2'] = fwd_df['fwd_ret_H2']
        df_aligned['fwd_ret_H3'] = fwd_df['fwd_ret_H3']
        
        # Calculate release trading dates (first trading day strictly after each release date)
        pos = np.searchsorted(trading_dates, df_fac.index, side='right')
        valid_pos = pos[pos < len(trading_dates)]
        release_trading_dates = trading_dates[valid_pos].unique()
        
        # Filter to release trading dates
        df_aligned = df_aligned.reindex(release_trading_dates)
        
        # Drop rows where factor level is NaN
        df_aligned = df_aligned.dropna(subset=['factor_level'])
        
        # Drop rows where all forward returns are NaN
        fwd_cols = ['fwd_ret_5d', 'fwd_ret_20d', 'fwd_ret_H1', 'fwd_ret_H2', 'fwd_ret_H3']
        df_aligned = df_aligned.dropna(subset=fwd_cols, how='all')
        
        all_dfs.append(df_aligned)
        
    if all_dfs:
        df_all = pd.concat(all_dfs)
        df_all.index.name = 'date'
        
        # Round numeric columns to 5 decimal places
        float_cols = ['factor_level', 'factor_diff', 'factor_zscore', 
                      'fwd_ret_5d', 'fwd_ret_20d', 'fwd_ret_H1', 'fwd_ret_H2', 'fwd_ret_H3']
        df_all[float_cols] = df_all[float_cols].round(5)
        
        csv_path = os.path.join(RESULTS_DIR, 'raw_aligned_timeseries.csv')
        df_all.to_csv(csv_path)
        print(f"Successfully saved robust raw aligned data to: {csv_path}")
        print(f"Total rows: {len(df_all)}")
    else:
        print("No raw aligned data computed.")

if __name__ == '__main__':
    main()
