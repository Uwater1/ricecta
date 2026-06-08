#!/usr/bin/env python3
"""
Download daily history for 6 foreign agricultural futures from AkShare and yfinance.
Saves data under data_alt/ in parquet format.
"""
import os
import time
import warnings
import pandas as pd
import akshare as ak
import yfinance as yf

warnings.filterwarnings('ignore')

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_DIR = _SCRIPT_DIR
DATA_ALT_DIR = os.path.join(BASE_DIR, 'data_alt')
os.makedirs(DATA_ALT_DIR, exist_ok=True)

# Mappings of domestic agricultural symbol to foreign symbol and source
MAPPINGS = {
    'C': {'symbol': 'C', 'source': 'akshare'},
    'M': {'symbol': 'SM', 'source': 'akshare'}, # Soy meal
    'Y': {'symbol': 'BO', 'source': 'akshare'}, # Soy oil
    'P': {'symbol': 'FCPO', 'source': 'akshare'}, # Palm oil
    'CF': {'symbol': 'CT', 'source': 'akshare'}, # Cotton
    'SR': {'symbol': 'SB=F', 'source': 'yfinance'} # Sugar
}

def clean_df(df, source):
    """Clean DataFrame to have standard date index, lowercase columns, and float32 types."""
    if df.empty:
        return df
        
    df = df.copy()
    
    if source == 'akshare':
        # Columns: date, open, high, low, close, volume, ...
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
    elif source == 'yfinance':
        # Index: Date (tz-aware)
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df.index.name = 'date'
        # Lowercase columns
        df.columns = [c.lower() for c in df.columns]
        
    # Ensure float32 for numeric columns
    for col in df.columns:
        if df[col].dtype in ['float64', 'float32']:
            df[col] = df[col].astype('float32')
        elif df[col].dtype in ['int64', 'int32']:
            df[col] = df[col].astype('int32')
            
    df = df.sort_index()
    # Filter 2020 onwards
    df = df[df.index >= '2016-01-01']
    return df

def download_all():
    print("=== Downloading Foreign Agricultural Futures Daily Data ===")
    for dom_symbol, info in MAPPINGS.items():
        foreign_sym = info['symbol']
        source = info['source']
        print(f"Fetching {foreign_sym} ({source}) for domestic {dom_symbol}...")
        
        filepath = os.path.join(DATA_ALT_DIR, f"{dom_symbol}.parquet")
        
        try:
            if source == 'akshare':
                df = ak.futures_foreign_hist(symbol=foreign_sym)
            elif source == 'yfinance':
                df = yf.Ticker(foreign_sym).history(start='2016-01-01', end='2026-06-05')
                
            if df is not None and not df.empty:
                df_clean = clean_df(df, source)
                df_clean.to_parquet(filepath, compression='zstd')
                print(f"  Saved {dom_symbol}: {df_clean.shape[0]} rows, index from {df_clean.index.min().date()} to {df_clean.index.max().date()}")
            else:
                print(f"  [WARNING] No data returned for {foreign_sym}")
                
            time.sleep(0.5) # Be gentle to APIs
        except Exception as e:
            print(f"  [ERROR] Failed to download {foreign_sym}: {e}")

def download_fx_rates():
    print("=== Downloading Exchange Rate Factors ===")
    import rqdatac
    rqdatac.init()
    
    try:
        print("Fetching USDCNY factor...")
        df_usd = rqdatac.econ.get_factors('USDCNY:即期汇率:日', start_date='2016-01-01', end_date='2026-06-03')
        if df_usd is not None and not df_usd.empty:
            df_usd = df_usd.reset_index().rename(columns={'info_date': 'date'}).set_index('date')
            df_usd = df_usd[~df_usd.index.duplicated(keep='last')]
            df_usd = df_usd[['value']].astype('float32')
            df_usd.to_parquet(os.path.join(DATA_ALT_DIR, "USDCNY.parquet"), compression='zstd')
            print(f"  Saved USDCNY: {df_usd.shape[0]} rows")
        else:
            print("  [WARNING] USDCNY factor returned empty")
    except Exception as e:
        print(f"  [ERROR] Failed to download USDCNY: {e}")
        
    try:
        print("Fetching MYRCNY factor...")
        df_myr = rqdatac.econ.get_factors('人民币对马来西亚林吉特中间汇率(间接标价法):当期值:日', start_date='2016-01-01', end_date='2026-06-03')
        if df_myr is not None and not df_myr.empty:
            df_myr = df_myr.reset_index().rename(columns={'info_date': 'date'}).set_index('date')
            df_myr = df_myr[~df_myr.index.duplicated(keep='last')]
            df_myr = df_myr[['value']].astype('float32')
            df_myr.to_parquet(os.path.join(DATA_ALT_DIR, "MYRCNY.parquet"), compression='zstd')
            print(f"  Saved MYRCNY: {df_myr.shape[0]} rows")
        else:
            print("  [WARNING] MYRCNY factor returned empty")
    except Exception as e:
        print(f"  [ERROR] Failed to download MYRCNY: {e}")

if __name__ == '__main__':
    download_all()
    download_fx_rates()
    print("=== Foreign Data Download Completed ===")

