#!/usr/bin/env python3
"""
Download daily price and volume data for all individual contracts of the 23 target symbols
from 2016-01-01 to 2026-06-08. Saves metadata and per-symbol contract parquet files.
"""
import os
import time
import warnings
import pandas as pd
import rqdatac
import pyarrow as pa
import pyarrow.parquet as pq

warnings.filterwarnings('ignore')

# Initialize rqdatac
rqdatac.init()

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(_SCRIPT_DIR, 'data')
OUT_DIR = os.path.join(BASE_DIR, 'contracts_daily')
os.makedirs(OUT_DIR, exist_ok=True)

SYMBOLS = [
    'C', 'M', 'Y', 'P', 'V', 'J', 'JD', 'I',  # DCE
    'CU', 'AL', 'AU', 'AG', 'RB', 'RU', 'NI', 'SN', # SHFE
    'SC', # INE
    'CF', 'SR', 'TA', 'MA', 'SA', # CZCE
    'TF' # CFFEX
]

START_DATE = '20160101'
END_DATE = '20260608'

def save_optimized_parquet(df, filepath):
    """Save dataframe with float32 downcasting and zstd compression."""
    if df.empty:
        df.to_parquet(filepath, engine='pyarrow')
        return
    
    # Downcast float64 to float32
    for col in df.columns:
        if df[col].dtype == 'float64':
            df[col] = df[col].astype('float32')
            
    table = pa.Table.from_pandas(df, preserve_index=True)
    pq.write_table(
        table,
        filepath,
        compression='zstd',
        compression_level=5,
        coerce_timestamps='us'
    )

def main():
    print("=== Downloading Contract Metadata ===")
    df_inst = rqdatac.all_instruments(type='Future')
    df_targets = df_inst[
        df_inst['underlying_symbol'].isin(SYMBOLS) &
        (df_inst['de_listed_date'] >= '2016-01-01') &
        (df_inst['listed_date'] <= '2026-06-08')
    ]
    
    # Save contract metadata
    metadata_path = os.path.join(OUT_DIR, 'metadata.parquet')
    save_optimized_parquet(df_targets, metadata_path)
    print(f"Saved metadata for {len(df_targets)} contracts to {metadata_path}")
    
    # Download daily price data per symbol
    total = len(SYMBOLS)
    fields = ['open', 'high', 'low', 'close', 'volume', 'open_interest']
    
    for idx, symbol in enumerate(SYMBOLS):
        print(f"[{idx+1}/{total}] Downloading contracts for: {symbol}...")
        sym_metadata = df_targets[df_targets['underlying_symbol'] == symbol]
        contracts = sym_metadata['order_book_id'].tolist()
        
        if not contracts:
            print(f"  No contracts found for {symbol}")
            continue
            
        symbol_filepath = os.path.join(OUT_DIR, f"{symbol}.parquet")
        
        try:
            # Fetch daily data for all contracts of this symbol in a single batch
            # We fetch from 2016-01-01 to 2026-06-08
            df_price = rqdatac.get_price(
                contracts,
                start_date=START_DATE,
                end_date=END_DATE,
                frequency='1d',
                fields=fields
            )
            
            if df_price is not None and not df_price.empty:
                # Ensure the index is MultiIndex [order_book_id, date]
                # Sometimes if there's only 1 contract, rqdatac might return a simple DatetimeIndex
                if not isinstance(df_price.index, pd.MultiIndex):
                    # Reconstruct index to match [order_book_id, date]
                    df_price = pd.concat({contracts[0]: df_price}, names=['order_book_id', 'date'])
                else:
                    df_price.index.names = ['order_book_id', 'date']
                    
                save_optimized_parquet(df_price, symbol_filepath)
                print(f"  Saved {symbol} contracts daily data: {df_price.shape[0]} rows")
            else:
                print(f"  [WARNING] No price data returned for {symbol}")
                save_optimized_parquet(pd.DataFrame(), symbol_filepath)
                
            time.sleep(0.2) # Avoid aggressive requests
        except Exception as e:
            print(f"  [ERROR] Failed to download {symbol}: {e}")
            save_optimized_parquet(pd.DataFrame(), symbol_filepath)

if __name__ == '__main__':
    main()
    print("=== Contract Data Download Completed ===")
