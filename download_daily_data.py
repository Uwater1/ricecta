#!/usr/bin/env python3
"""
Download daily pre-adjusted dominant price data for the 23 target commodity symbols.
Saves data under data/dominant_daily/ in parquet format.
"""
import os
import time
import warnings
import pandas as pd
import rqdatac

warnings.filterwarnings('ignore')

# Initialize rqdatac
rqdatac.init()

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Output directory
BASE_DIR = os.path.join(_SCRIPT_DIR, 'data')
DAILY_DIR = os.path.join(BASE_DIR, 'dominant_daily')
os.makedirs(DAILY_DIR, exist_ok=True)

# 23 underlyings
SYMBOLS = [
    'C', 'M', 'Y', 'P', 'V', 'J', 'JD', 'I',  # DCE
    'CU', 'AL', 'AU', 'AG', 'RB', 'RU', 'NI', 'SN', # SHFE
    'SC', # INE
    'CF', 'SR', 'TA', 'MA', 'SA', # CZCE
    'TF' # CFFEX
]

START_DATE = '20210101'
END_DATE = '20260603'

def download_all():
    print("=== Downloading Daily Pre-adjusted Dominant Prices ===")
    total = len(SYMBOLS)
    for idx, symbol in enumerate(SYMBOLS):
        print(f"[{idx+1}/{total}] Fetching daily data for: {symbol}...")
        filepath = os.path.join(DAILY_DIR, f"{symbol}.parquet")
        
        try:
            # Fetch daily pre-adjusted dominant contract prices
            df = rqdatac.futures.get_dominant_price(
                symbol,
                start_date=START_DATE,
                end_date=END_DATE,
                frequency='1d',
                adjust_type='pre',
                adjust_method='prev_close_spread'
            )
            
            if df is not None and not df.empty:
                # If MultiIndex (underlying_symbol, date), reset underlying_symbol to keep only date as index
                if isinstance(df.index, pd.MultiIndex):
                    df = df.reset_index(level='underlying_symbol')
                
                # Make sure dtypes are float32 to save space
                for col in df.columns:
                    if df[col].dtype == 'float64':
                        df[col] = df[col].astype('float32')
                
                df.to_parquet(filepath, compression='zstd')
                print(f"  Saved {symbol}: {df.shape[0]} rows")
            else:
                print(f"  [WARNING] No data returned for {symbol}")
                
            time.sleep(0.1) # Be gentle to API
        except Exception as e:
            print(f"  [ERROR] Failed to download {symbol}: {e}")

if __name__ == '__main__':
    download_all()
    print("=== Daily Data Download Completed ===")
