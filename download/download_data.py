#!/usr/bin/env python3
"""
Download futures minute-level data, spot basis, and treasury yields for arbitrage research.
Optimized to query all contracts for each commodity symbol in a single batch to maximize speed
and prevent rqdatac connection limit errors.
"""
import os
import time
import warnings
import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_DIR = os.path.dirname(_SCRIPT_DIR)

import akshare as ak
import rqdatac
import yfinance as yf
import concurrent.futures
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

warnings.filterwarnings('ignore')

# 1. Initialize rqdatac
rqdatac.init()

# Compression / encoding settings.
# - float64 -> float32 (halves numeric storage, ample precision for 5-min prices/volume)
# - zstd level 5 (industry standard for Parquet; extremely fast read/write, excellent ratio)
# - microsecond timestamp resolution (vs default nanosecond) saves 2 bytes per bar
PARQUET_COMPRESSION = 'zstd'
PARQUET_COMPRESSION_LEVEL = 5
PARQUET_VERSION = '2.6'


def _downcast_floats(df: pd.DataFrame) -> pd.DataFrame:
    """Downcast float64 -> float32 in-place on a copy. Non-numeric cols untouched."""
    if df.empty:
        return df
    for col in df.columns:
        if df[col].dtype == 'float64':
            df[col] = df[col].astype('float32')
    return df


def save_parquet(df: pd.DataFrame, path: str) -> None:
    """Write DataFrame to parquet with optimized dtype + zstd-3 compression.

    Used for ALL parquet outputs in this script (futures minute bars, spot/basis,
    yield curve, global crude, dominant contract mappings) so re-downloads and
    the in-place recompressor produce the same compact encoding.

    Empty DataFrames still write a valid (header-only) parquet so downstream
    code can use ``pd.read_parquet`` without special-casing.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if df.empty:
        pd.DataFrame().to_parquet(path, engine='pyarrow')
        return

    df = _downcast_floats(df)
    table = pa.Table.from_pandas(df, preserve_index=True)
    pq.write_table(
        table,
        path,
        compression=PARQUET_COMPRESSION,
        compression_level=PARQUET_COMPRESSION_LEVEL,
        coerce_timestamps='us',
        data_page_size=8 * 1024 * 1024,  # 8 MiB pages => better brotli ratio on minute bars
    )

# Define output directories
BASE_DIR = os.path.join(_WORKSPACE_DIR, 'data')
FUTURES_DIR = os.path.join(BASE_DIR, 'futures_5minute')
SPOT_DIR = os.path.join(BASE_DIR, 'spot_basis')
YIELD_DIR = os.path.join(BASE_DIR, 'yield_curve')
CRUDE_DIR = os.path.join(BASE_DIR, 'global_crude')
DOMINANT_DIR = os.path.join(BASE_DIR, 'dominant_contracts')

for d in [FUTURES_DIR, SPOT_DIR, YIELD_DIR, CRUDE_DIR, DOMINANT_DIR]:
    os.makedirs(d, exist_ok=True)

# 23 underlyings
SYMBOLS = [
    'C', 'M', 'Y', 'P', 'V', 'J', 'JD', 'I',  # DCE
    'CU', 'AL', 'AU', 'AG', 'RB', 'RU', 'NI', 'SN', # SHFE
    'SC', # INE
    'CF', 'SR', 'TA', 'MA', 'SA', # CZCE
    'TF' # CFFEX
]

START_DATE = '20160101'
END_DATE = '20260608'

def check_existing_contracts(contracts, symbol):
    """Filter out contracts that already have valid parquet files."""
    to_download = []
    skipped = 0
    sym_dir = os.path.join(FUTURES_DIR, symbol)
    os.makedirs(sym_dir, exist_ok=True)
    
    for contract in contracts:
        filepath = os.path.join(sym_dir, f"{contract}.parquet")
        if os.path.exists(filepath):
            try:
                # Check if parquet is readable and valid
                pd.read_parquet(filepath)
                skipped += 1
                continue
            except Exception:
                pass
        to_download.append(contract)
    return to_download, skipped

def download_futures_5minute():
    print("=== Downloading Futures 5m Data ===")
    df_inst = rqdatac.all_instruments(type='Future')
    df_targets = df_inst[
        df_inst['underlying_symbol'].isin(SYMBOLS) & 
        (df_inst['de_listed_date'] >= '2016-01-01') & 
        (df_inst['listed_date'] <= '2026-06-03')
    ]
    
    total_symbols = len(SYMBOLS)
    for sym_idx, symbol in enumerate(SYMBOLS):
        print(f"[{sym_idx+1}/{total_symbols}] Processing symbol: {symbol}")
        
        # Get all contracts active since 2021 for this symbol
        df_sym = df_targets[df_targets['underlying_symbol'] == symbol]
        contracts = df_sym['order_book_id'].tolist()
        
        if not contracts:
            print(f"  No contracts found for {symbol}")
            continue
            
        contracts_to_download, skipped = check_existing_contracts(contracts, symbol)
        print(f"  Total contracts: {len(contracts)}, Skipped: {skipped}, To download: {len(contracts_to_download)}")
        
        if not contracts_to_download:
            print(f"  All contracts for {symbol} already downloaded.")
            continue
            
        # Download in a single batch
        print(f"  Fetching batch of {len(contracts_to_download)} contracts...")
        try:
            df_batch = rqdatac.get_price(
                contracts_to_download, 
                start_date=START_DATE, 
                end_date=END_DATE, 
                frequency='5m'
            )
            
            sym_dir = os.path.join(FUTURES_DIR, symbol)
            
            if df_batch is not None and not df_batch.empty:
                # Group by contract and write to separate parquet files
                if df_batch.index.nlevels > 1:
                    grouped = df_batch.groupby(level='order_book_id')
                else:
                    # If only one contract was returned, it might not have order_book_id in index, or it could be different.
                    # Usually get_price for multiple contracts always returns MultiIndex ['order_book_id', 'datetime'].
                    grouped = [(df_batch.index.name or 'order_book_id', df_batch)]
                    
                downloaded_set = set()
                for contract, df_group in grouped:
                    # If MultiIndex, drop the contract level to make index clean (datetime)
                    if isinstance(df_group.index, pd.MultiIndex):
                        df_group = df_group.droplevel('order_book_id')
                    
                    filepath = os.path.join(sym_dir, f"{contract}.parquet")
                    save_parquet(df_group, filepath)
                    downloaded_set.add(contract)
                    print(f"    Saved {contract}: {df_group.shape[0]} rows")
 
                # Write empty parquet for requested contracts that didn't return any data
                for contract in contracts_to_download:
                    if contract not in downloaded_set:
                        filepath = os.path.join(sym_dir, f"{contract}.parquet")
                        save_parquet(pd.DataFrame(), filepath)
                        print(f"    Saved {contract}: 0 rows (empty)")
            else:
                print("    Batch returned no data.")
                # Write empty files for all contracts in this batch
                for contract in contracts_to_download:
                    filepath = os.path.join(sym_dir, f"{contract}.parquet")
                    save_parquet(pd.DataFrame(), filepath)
                    
            time.sleep(0.5) # Gentle break between symbols
        except Exception as e:
            print(f"  Error downloading batch for {symbol}: {e}")
            # Fallback to sequential download for this symbol if batch fails
            print(f"  Falling back to sequential download for {symbol}...")
            for contract in contracts_to_download:
                filepath = os.path.join(sym_dir, f"{contract}.parquet")
                row = df_sym[df_sym['order_book_id'] == contract].iloc[0]
                q_start = max(row['listed_date'], '2016-01-01').replace('-', '')
                q_end = min(row['de_listed_date'], '2026-06-03').replace('-', '')
                try:
                    df = rqdatac.get_price(contract, start_date=q_start, end_date=q_end, frequency='5m')
                    if df is not None and not df.empty:
                        save_parquet(df, filepath)
                        print(f"    Saved sequential {contract}: {df.shape[0]} rows")
                    else:
                        save_parquet(pd.DataFrame(), filepath)
                        print(f"    Saved sequential {contract}: empty")
                    time.sleep(0.1)
                except Exception as seq_e:
                    print(f"    Failed sequential {contract}: {seq_e}")

def fetch_spot_basis_year(year, spot_symbols):
    filepath = os.path.join(SPOT_DIR, f"spot_basis_{year}.parquet")
    if os.path.exists(filepath):
        return year, "skipped (exists)"
        
    start_day = f"{year}0101"
    end_day = f"{year}1231" if year < 2026 else "20260603"
    try:
        df = ak.futures_spot_price_daily(start_day=start_day, end_day=end_day, vars_list=spot_symbols)
        if df is not None and not df.empty:
            save_parquet(df, filepath)
            return year, f"success ({df.shape[0]} rows)"
        else:
            return year, "no data"
    except Exception as e:
        return year, f"error: {str(e)}"

def download_spot_basis():
    print("=== Downloading Spot and Basis Data ===")
    spot_symbols = [s for s in SYMBOLS if s not in ['TF', 'SC']]
    years = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
    
    # Run year-by-year spot/basis download in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fetch_spot_basis_year, y, spot_symbols): y for y in years}
        for future in concurrent.futures.as_completed(futures):
            year = futures[future]
            try:
                _, status = future.result()
                print(f"  Year {year} spot/basis: {status}")
            except Exception as e:
                print(f"  Exception spot/basis {year}: {e}")

def download_yield_curve():
    print("=== Downloading Yield Curve Data ===")
    filepath = os.path.join(YIELD_DIR, "yield_curve_cn.parquet")
    if os.path.exists(filepath):
        print("  yield_curve_cn.parquet already exists, skipping")
        return
        
    print("Downloading China Treasury Yield Curve...")
    try:
        df = rqdatac.get_yield_curve(start_date=START_DATE, end_date=END_DATE, country='cn')
        if df is not None and not df.empty:
            save_parquet(df, filepath)
            print(f"  Saved yield curve: {df.shape[0]} rows")
        else:
            print("  No yield curve data")
    except Exception as e:
        print(f"  Error downloading yield curve: {e}")

def download_global_crude():
    print("=== Downloading Global Crude Data ===")
    filepath = os.path.join(CRUDE_DIR, "global_crude.parquet")
    if os.path.exists(filepath):
        print("  global_crude.parquet already exists, skipping")
        return
        
    print("Downloading Brent/WTI daily from yfinance (for reference)...")
    try:
        yf_start = '2016-01-01'
        yf_end = '2026-06-04'
        df_brent = yf.Ticker('BZ=F').history(start=yf_start, end=yf_end)
        df_wti = yf.Ticker('CL=F').history(start=yf_start, end=yf_end)
        
        df_brent['symbol'] = 'BZ=F'
        df_wti['symbol'] = 'CL=F'
        
        df_combined = pd.concat([df_brent, df_wti])
        save_parquet(df_combined, filepath)
        print(f"  Saved global crude: {df_combined.shape[0]} rows")
    except Exception as e:
        print(f"  Error downloading global crude: {e}")

def download_dominant_contracts():
    print("=== Downloading Dominant Contracts Mapping ===")
    filepath = os.path.join(DOMINANT_DIR, "dominant.parquet")
    if os.path.exists(filepath):
        print("  dominant.parquet already exists, skipping")
        return
        
    print("Downloading dominant contract mappings...")
    dfs = []
    for symbol in SYMBOLS:
        try:
            s = rqdatac.futures.get_dominant(symbol, start_date=START_DATE, end_date=END_DATE)
            if s is not None and not s.empty:
                df = s.to_frame(name='dominant_contract')
                df['underlying_symbol'] = symbol
                dfs.append(df)
            time.sleep(0.05)
        except Exception as e:
            print(f"  Error getting dominant for {symbol}: {e}")
            
    if dfs:
        df_all = pd.concat(dfs)
        save_parquet(df_all, filepath)
        print(f"  Saved dominant contract mappings: {df_all.shape[0]} rows")
    else:
        print("  No dominant mappings found")

if __name__ == '__main__':
    download_futures_5minute()
    download_spot_basis()
    download_yield_curve()
    download_global_crude()
    download_dominant_contracts()
    print("=== Data Download Completed ===")
