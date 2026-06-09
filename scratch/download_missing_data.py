import os
import time
import pandas as pd
import rqdatac
import akshare as ak
import concurrent.futures
import pyarrow as pa
import pyarrow.parquet as pq

# Initialize rqdatac
rqdatac.init()

_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.join(_SCRIPT_DIR, 'data')
SPOT_DIR = os.path.join(BASE_DIR, 'spot_basis')
DOMINANT_DIR = os.path.join(BASE_DIR, 'dominant_contracts')

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
    if df.empty:
        df.to_parquet(filepath, engine='pyarrow')
        return
    for col in df.columns:
        if df[col].dtype == 'float64':
            df[col] = df[col].astype('float32')
    table = pa.Table.from_pandas(df, preserve_index=True)
    pq.write_table(table, filepath, compression='zstd', compression_level=5, coerce_timestamps='us')

def download_spot_basis():
    print("=== Downloading Missing Spot and Basis Data (2016-2020) ===")
    spot_symbols = [s for s in SYMBOLS if s not in ['TF', 'SC']]
    years = [2016, 2017, 2018, 2019, 2020]
    
    for year in years:
        filepath = os.path.join(SPOT_DIR, f"spot_basis_{year}.parquet")
        if os.path.exists(filepath):
            print(f"  Year {year} spot/basis already exists, skipping")
            continue
        
        start_day = f"{year}0101"
        end_day = f"{year}1231"
        print(f"  Fetching spot/basis for {year}...")
        try:
            df = ak.futures_spot_price_daily(start_day=start_day, end_day=end_day, vars_list=spot_symbols)
            if df is not None and not df.empty:
                save_optimized_parquet(df, filepath)
                print(f"    Saved spot_basis_{year}.parquet: {df.shape[0]} rows")
            else:
                print(f"    No data returned for year {year}")
        except Exception as e:
            print(f"    Error for year {year}: {e}")
        time.sleep(1.0)

def download_dominant_contracts():
    print("=== Downloading Complete Dominant Contracts Mapping ===")
    filepath = os.path.join(DOMINANT_DIR, "dominant.parquet")
    if os.path.exists(filepath):
        print("  Removing existing dominant.parquet to force full download...")
        os.remove(filepath)
        
    dfs = []
    for symbol in SYMBOLS:
        print(f"  Fetching dominant contracts for: {symbol}...")
        try:
            s = rqdatac.futures.get_dominant(symbol, start_date=START_DATE, end_date=END_DATE)
            if s is not None and not s.empty:
                df = s.to_frame(name='dominant_contract')
                df['underlying_symbol'] = symbol
                dfs.append(df)
            time.sleep(0.1)
        except Exception as e:
            print(f"    Error for {symbol}: {e}")
            
    if dfs:
        df_all = pd.concat(dfs)
        save_optimized_parquet(df_all, filepath)
        print(f"  Saved dominant contract mappings: {df_all.shape[0]} rows to {filepath}")
    else:
        print("  Failed to download dominant mappings")

if __name__ == '__main__':
    download_spot_basis()
    download_dominant_contracts()
    print("=== Finished downloading missing data ===")
