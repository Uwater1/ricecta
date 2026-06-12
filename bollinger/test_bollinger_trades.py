import os
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

import sys
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(_SCRIPT_DIR))

from contract_splicer import ContractSplicer

symbol = 'RB'
k = 1
splicer = ContractSplicer(symbol, k=k)
df_daily = splicer.build()
contract_log = splicer.contract_log

# Load daily raw prices
df_raw_daily = pd.read_parquet(f"data/contracts_daily/{symbol}.parquet")

# Precompute daily adjustment factors
factors = {}
for date in df_daily.index:
    cid = contract_log.loc[date]
    p_adj = df_daily.loc[date, 'close']
    try:
        p_raw = df_raw_daily.loc[(cid, date), 'close']
        factor = p_adj / p_raw if p_raw > 0 else 1.0
    except KeyError:
        factor = 1.0
    factors[date] = factor
factors_series = pd.Series(factors)

# Load daily ATR for leverage
df_daily['TR'] = np.maximum(
    df_daily['high'] - df_daily['low'],
    np.maximum(
        np.abs(df_daily['high'] - df_daily['close'].shift(1)),
        np.abs(df_daily['low'] - df_daily['close'].shift(1))
    )
).fillna(0.0)
df_daily['ATR'] = df_daily['TR'].rolling(20, min_periods=1).mean()
# Lev_ATR = 0.005 * Close / ATR
df_daily['Lev_ATR'] = np.where(df_daily['ATR'] > 0, 0.005 * df_daily['close'] / df_daily['ATR'], 1.0)
lev_atr_series = df_daily['Lev_ATR']

# Multiplier
df_meta = pd.read_parquet("data/contracts_daily/metadata.parquet")
multiplier = df_meta[df_meta['underlying_symbol'] == symbol]['contract_multiplier'].iloc[0]

# Load 5-minute data and concatenate
unique_contracts = contract_log.dropna().unique()
dfs = []
for cid in unique_contracts:
    path = f"data/futures_5minute/{symbol}/{cid}.parquet"
    if not os.path.exists(path):
        continue
    df_c = pd.read_parquet(path)
    active_dates = contract_log[contract_log == cid].index
    df_c_active = df_c[df_c['trading_date'].isin(active_dates)]
    dfs.append(df_c_active)

if not dfs:
    print("No 5-minute data found!")
    exit(1)

df_all = pd.concat(dfs).sort_index()

# Resample to 15m
df_15m = df_all.resample('15Min', closed='right', label='right').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum',
    'open_interest': 'last',
    'trading_date': 'last'
}).dropna(subset=['trading_date'])

# Apply adjustment factors
df_15m['factor'] = df_15m['trading_date'].map(factors_series).fillna(1.0)
for col in ['open', 'high', 'low', 'close']:
    df_15m[col] = df_15m[col] * df_15m['factor']

# Apply daily Lev_ATR to 15m index
df_15m['Lev_ATR'] = df_15m['trading_date'].map(lev_atr_series).ffill().fillna(1.0)

# Compute indicators
df_15m['MA'] = df_15m['close'].rolling(300).mean()
df_15m['Std'] = df_15m['close'].rolling(300).std()
df_15m['Upper'] = df_15m['MA'] + 1.5 * df_15m['Std']
df_15m['Lower'] = df_15m['MA'] - 1.5 * df_15m['Std']
df_15m['OI_short'] = df_15m['open_interest'].rolling(150).mean()
df_15m['OI_long'] = df_15m['open_interest'].rolling(300).mean()
df_15m['OI_pct'] = df_15m['OI_short'] / df_15m['OI_long']

# Drop rows before indicators are ready
df_15m = df_15m.dropna(subset=['MA', 'Std', 'OI_pct'])

# Simulation loop
pos = 0
entry_idx = None
direction = 0
multiplier_oi = 1.0
tp_line = np.nan
lev_entry = 0.0

trades = []
times = df_15m.index
close = df_15m['close'].values
open_val = df_15m['open'].values
high = df_15m['high'].values
low = df_15m['low'].values
ma = df_15m['MA'].values
upper = df_15m['Upper'].values
lower = df_15m['Lower'].values
oi_pct = df_15m['OI_pct'].values
lev_atr = df_15m['Lev_ATR'].values
trading_date = df_15m['trading_date'].values
factor_arr = df_15m['factor'].values

def get_vwap(idx):
    t_idx = times[idx]
    target_time = t_idx + pd.Timedelta(minutes=5)
    f_t = factor_arr[idx]
    if target_time in df_all.index:
        row = df_all.loc[target_time]
        vol = row['volume']
        turn = row['total_turnover']
        if vol > 0 and turn > 0:
            p_raw = turn / (vol * multiplier)
        else:
            p_raw = row['close']
        return p_raw * f_t
    return close[idx]

print("Starting simulation over", len(df_15m), "bars...")
for t in range(1, len(df_15m)):
    if pos == 0:
        # Check Long Entry
        if close[t] > upper[t] and close[t-1] <= upper[t-1]:
            pos = 1
            entry_idx = t
            direction = 1
            multiplier_oi = 1.0 if oi_pct[t] > 1.0 else 0.5
            tp_line = ma[t] + 8.0 * df_15m['Std'].values[t]
            lev_entry = lev_atr[t]
        # Check Short Entry
        elif close[t] < lower[t] and close[t-1] >= lower[t-1]:
            pos = -1
            entry_idx = t
            direction = -1
            multiplier_oi = 1.0 if oi_pct[t] > 1.0 else 0.5
            tp_line = ma[t] - 8.0 * df_15m['Std'].values[t]
            lev_entry = lev_atr[t]
    elif pos == 1:
        # Check Exit for Long
        if close[t] < ma[t] or close[t] > tp_line:
            p_entry = get_vwap(entry_idx)
            p_exit = get_vwap(t)
            trades.append({
                'entry_time': times[entry_idx],
                'exit_time': times[t],
                'entry_date': trading_date[entry_idx],
                'exit_date': trading_date[t],
                'direction': 'LONG',
                'p_entry': p_entry,
                'p_exit': p_exit,
                'multiplier': multiplier_oi,
                'lev_atr': lev_entry,
                'raw_return': (p_exit / p_entry - 1.0)
            })
            pos = 0
    elif pos == -1:
        # Check Exit for Short
        if close[t] > ma[t] or close[t] < tp_line:
            p_entry = get_vwap(entry_idx)
            p_exit = get_vwap(t)
            trades.append({
                'entry_time': times[entry_idx],
                'exit_time': times[t],
                'entry_date': trading_date[entry_idx],
                'exit_date': trading_date[t],
                'direction': 'SHORT',
                'p_entry': p_entry,
                'p_exit': p_exit,
                'multiplier': multiplier_oi,
                'lev_atr': lev_entry,
                'raw_return': -1.0 * (p_exit / p_entry - 1.0)
            })
            pos = 0

print("Total trades generated:", len(trades))
if trades:
    df_trades = pd.DataFrame(trades)
    print("Average raw trade return:", df_trades['raw_return'].mean() * 100, "%")
    print("Win rate:", (df_trades['raw_return'] > 0).mean() * 100, "%")
    print(df_trades.head(10))
