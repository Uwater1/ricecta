import os
import pandas as pd
import numpy as np
import sys
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(_SCRIPT_DIR))

from contract_splicer import ContractSplicer

symbol = 'RB'
k = 1
splicer = ContractSplicer(symbol, k=k)
df_daily = splicer.build()
contract_log = splicer.contract_log

print("Daily index range:", df_daily.index.min(), df_daily.index.max())
print("Unique contracts:", contract_log.dropna().unique())

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

if dfs:
    df_5m = pd.concat(dfs).sort_index()
    print("Spliced 5m shape:", df_5m.shape)
    
    # Resample to 15m
    df_15m = df_5m.resample('15Min', closed='right', label='right').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
        'open_interest': 'last',
        'trading_date': 'last'
    }).dropna(subset=['trading_date'])
    
    print("Resampled 15m shape:", df_15m.shape)
    
    # Apply factors
    df_15m['factor'] = df_15m['trading_date'].map(factors_series).fillna(1.0)
    for col in ['open', 'high', 'low', 'close']:
        df_15m[col] = df_15m[col] * df_15m['factor']
        
    print("Adjusted 15m close range:", df_15m['close'].min(), df_15m['close'].max())
else:
    print("No 5-minute data found!")
