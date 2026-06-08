#!/usr/bin/env python3
import os
import pandas as pd
import rqdatac

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize rqdatac
rqdatac.init()

def download_shibor():
    print("=== Downloading SHIBOR Data ===")
    out_dir = os.path.join(_SCRIPT_DIR, "data", "shibor")
    os.makedirs(out_dir, exist_ok=True)
    
    filepath = os.path.join(out_dir, "shibor.parquet")
    
    try:
        df = rqdatac.get_interbank_offered_rate(
            start_date='20160101',
            end_date='20260608',
            source='Shibor'
        )
        if df is not None and not df.empty:
            # Save to Parquet
            df.to_parquet(filepath, engine='pyarrow', compression='zstd')
            print(f"Successfully downloaded SHIBOR data. Saved to {filepath}")
            print(df.head())
        else:
            print("Received empty DataFrame for SHIBOR.")
    except Exception as e:
        print(f"Error downloading SHIBOR: {e}")

if __name__ == '__main__':
    download_shibor()
