#!/usr/bin/env python3
"""
Parses potential_alt_alphas.md, downloads macro factors from Ricequant rqdatac,
and saves them to data/macro_factors/ in Parquet format.
"""
import os
import re
import time
import warnings
import pandas as pd
import rqdatac

warnings.filterwarnings('ignore')

# Initialize rqdatac
rqdatac.init()

BASE_DIR = '/home/hallo/data/ricecta/data'
MACRO_DIR = os.path.join(BASE_DIR, 'macro_factors')
os.makedirs(MACRO_DIR, exist_ok=True)

START_DATE = '20210101'
END_DATE = '20260603'

# Mapping discrepancies between markdown factor names and rqdatac names
DISCREPANCIES = {
    'PPI_通信设备、计算机及其他电子设备制造业工业品出厂价格指数PPI_(上年=100)_当月': '通信设备、计算机及其他电子设备制造业工业品出厂价格指数PPI_(上年=100)_当月',
    '居民饮料消费价格指数CPI_(上年=100)_当月': '居民饮料消费价格指数CPI_(上年=100)',
    '居民干豆类及豆制品消费价格指数CPI_(上年=100)_当月': '居民干豆类及豆制品消费价格指数CPI_(上年=100)',
    'PPI_交通运输设备制造业(全国:当期同比增长率:月)': 'PPI_铁路、船舶、航空航天和其他运输设备制造业(全国:当期同比增长率:月)',
    '居民油脂消费价格指数CPI_(上年=100)_当月': '居民油脂消费价格指数CPI_(上年=100)',
    '居民糖类消费价格指数CPI_(上年=100)_当月': '居民糖类消费价格指数CPI_(上年=100)'
}

def parse_markdown(filepath):
    """
    Parses potential_alt_alphas.md and returns:
    1. A dictionary mapping symbol to list of raw factor names.
    2. A dictionary mapping raw factor names to cleaned factor names.
    """
    symbol_to_factors = {}
    current_symbol = None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        # Detect symbol sections like '### 品种:玉米 (C)' or '### 品种:5年期国债 (TF)'
        m_sym = re.search(r'### 品种:[^(]+\(([^)]+)\)', line)
        if m_sym:
            current_symbol = m_sym.group(1).strip()
            symbol_to_factors[current_symbol] = []
            continue
            
        if current_symbol and line.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9', '0')):
            # Match factors in backticks
            m_fac = re.search(r'\x60([^\x60]+)\x60', line)
            if m_fac:
                factor_name = m_fac.group(1).strip()
                symbol_to_factors[current_symbol].append(factor_name)
                
    return symbol_to_factors

def download_factors():
    md_path = '/home/hallo/data/ricecta/potential_alt_alphas.md'
    print(f"Parsing {md_path}...")
    symbol_to_factors = parse_markdown(md_path)
    
    # Get all unique factors
    all_raw_factors = set()
    for factors in symbol_to_factors.values():
        all_raw_factors.update(factors)
        
    print(f"Total unique factors in markdown: {len(all_raw_factors)}")
    
    # Download each factor
    for idx, raw_factor in enumerate(sorted(all_raw_factors)):
        cleaned_factor = DISCREPANCIES.get(raw_factor, raw_factor)
        filename = re.sub(r'[\\/*?:"<>|]', '_', raw_factor) + ".parquet"
        filepath = os.path.join(MACRO_DIR, filename)
        
        if os.path.exists(filepath):
            print(f"[{idx+1}/{len(all_raw_factors)}] Cached: {raw_factor}")
            continue
            
        print(f"[{idx+1}/{len(all_raw_factors)}] Downloading: {cleaned_factor} ...")
        try:
            df = rqdatac.econ.get_factors(
                cleaned_factor,
                start_date=START_DATE,
                end_date=END_DATE
            )
            if df is not None and not df.empty:
                # Convert float64 to float32 to save space
                if 'value' in df.columns:
                    df['value'] = df['value'].astype('float32')
                df.to_parquet(filepath, compression='zstd')
                print(f"  Saved {df.shape[0]} rows to {filename}")
            else:
                print(f"  [WARNING] No data returned for: {cleaned_factor}")
            time.sleep(0.1)
        except Exception as e:
            print(f"  [ERROR] Failed to download {cleaned_factor}: {e}")

if __name__ == '__main__':
    download_factors()
    print("=== Macro Factors Download Completed ===")
