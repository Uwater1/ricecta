#!/usr/bin/env python3
import sys
import os
import re
import pandas as pd
import numpy as np
import warnings

_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(_SCRIPT_DIR)

from evaluate_hold_strategy import get_dominant_switch_dates

warnings.filterwarnings('ignore')

_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.join(_SCRIPT_DIR, 'data')
DAILY_DIR = os.path.join(BASE_DIR, 'dominant_daily')
MACRO_DIR = os.path.join(BASE_DIR, 'macro_factors')
RESULTS_DIR = _SCRIPT_DIR

SYMBOLS = [
    'C', 'M', 'Y', 'P', 'V', 'J', 'JD', 'I',  # DCE
    'CU', 'AL', 'AU', 'AG', 'RB', 'RU', 'NI', 'SN', # SHFE
    'SC', # INE
    'CF', 'SR', 'TA', 'MA', 'SA', # CZCE
    'TF' # CFFEX
]

SWITCH_HORIZONS = ['H1', 'H2', 'H3']

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

def compute_switch_forward_returns(df_price, switch_dates):
    trading_dates = df_price.index
    close = df_price['close'].values.astype(np.float64)
    n = len(trading_dates)
    td_ts = trading_dates.values
    sd_ts = np.sort(np.array(switch_dates, dtype='datetime64[ns]'))

    first_switch_pos = np.searchsorted(sd_ts, td_ts, side='left')
    result = pd.DataFrame(index=trading_dates)

    close_series = df_price['close']
    result['fwd_ret_5d'] = close_series.pct_change(5).shift(-5).values
    result['fwd_ret_20d'] = close_series.pct_change(20).shift(-20).values

    for i, label in enumerate(SWITCH_HORIZONS, start=1):
        target_pos = first_switch_pos + (i - 1)
        valid = (target_pos < len(sd_ts))

        target_td_pos = np.full(n, n, dtype=np.int64)
        valid_sd = sd_ts[target_pos[valid]]
        target_td_pos[valid] = np.searchsorted(td_ts, valid_sd, side='left')

        valid &= (target_td_pos < n)
        valid &= (target_td_pos >= 0)

        days_to_switch = np.full(n, -1, dtype=np.int32)
        days_to_switch[valid] = target_td_pos[valid] - np.arange(n)[valid]
        valid &= (days_to_switch > 0)

        fwd_ret = np.full(n, np.nan)
        fwd_ret[valid] = close[target_td_pos[valid]] / close[np.arange(n)[valid]] - 1.0

        result[f'fwd_ret_{label}'] = fwd_ret

    return result

def main():
    md_path = os.path.join(_SCRIPT_DIR, 'potential_alt_alphas.md')
    symbol_to_factors = parse_markdown(md_path)
    
    all_dfs = []
    
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
        
        try:
            switch_dates = get_dominant_switch_dates(symbol)
        except Exception as e:
            print(f"Warning: could not load switch dates for {symbol}: {e}")
            continue
        
        fwd_df = compute_switch_forward_returns(df_price, switch_dates)
        
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
            
            # Drop rows where both factor value and forward returns are NaN to save space, 
            # but keep rows where at least some data is present
            df_aligned = df_aligned.dropna(subset=['factor_level', 'fwd_ret_20d'], how='all')
            
            all_dfs.append(df_aligned)
            
    if all_dfs:
        df_all = pd.concat(all_dfs)
        df_all.index.name = 'date'
        
        # Save all symbols data
        csv_path = os.path.join(RESULTS_DIR, 'raw_aligned_timeseries.csv')
        df_all.to_csv(csv_path)
        print(f"Saved all symbols raw aligned data to: {csv_path}")
        
        # Save AU only data
        df_au = df_all[df_all['symbol'] == 'AU']
        au_csv_path = os.path.join(RESULTS_DIR, 'au_raw_aligned_timeseries.csv')
        df_au.to_csv(au_csv_path)
        print(f"Saved AU-only raw aligned data to: {au_csv_path}")
    else:
        print("No raw aligned data computed.")

if __name__ == '__main__':
    main()
