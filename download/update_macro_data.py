#!/usr/bin/env python3
"""
Updates macro factors from Ricequant rqdatac to the current date.
Overwrites parquets only when new data rows or dates are detected.
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

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_DIR = os.path.dirname(_SCRIPT_DIR)

BASE_DIR = os.path.join(_WORKSPACE_DIR, 'data')
MACRO_DIR = os.path.join(BASE_DIR, 'macro_factors')
os.makedirs(MACRO_DIR, exist_ok=True)

START_DATE = '20160101'
# Query up to today
END_DATE = pd.Timestamp.now().strftime('%Y%m%d')

DISCREPANCIES = {
    'PPI_通信设备、计算机及其他电子设备制造业工业品出厂价格指数PPI_(上年=100)_当月': '通信设备、计算机及其他电子设备制造业工业品出厂价格指数PPI_(上年=100)_当月',
    '居民饮料消费价格指数CPI_(上年=100)_当月': '居民饮料消费价格指数CPI_(上年=100)',
    '居民干豆类及豆制品消费价格指数CPI_(上年=100)_当月': '居民干豆类及豆制品消费价格指数CPI_(上年=100)',
    'PPI_交通运输设备制造业(全国:当期同比增长率:月)': 'PPI_铁路、船舶、航空航天和其他运输设备制造业(全国:当期同比增长率:月)',
    '居民油脂消费价格指数CPI_(上年=100)_当月': '居民油脂消费价格指数CPI_(上年=100)',
    '居民糖类消费价格指数CPI_(上年=100)_当月': '居民糖类消费价格指数CPI_(上年=100)'
}

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
                factor_name = m_fac.group(1).strip()
                symbol_to_factors[current_symbol].append(factor_name)
    return symbol_to_factors

def update_factors():
    md_path = os.path.join(_WORKSPACE_DIR, 'potential_alt_alphas.md')
    print(f"Parsing potential factors from: {md_path}")
    symbol_to_factors = parse_markdown(md_path)
    
    all_raw_factors = set()
    for factors in symbol_to_factors.values():
        all_raw_factors.update(factors)
        
    print(f"Total unique factors to update: {len(all_raw_factors)}")
    updated_count = 0
    
    for idx, raw_factor in enumerate(sorted(all_raw_factors)):
        cleaned_factor = DISCREPANCIES.get(raw_factor, raw_factor)
        filename = re.sub(r'[\\/*?:"<>|]', '_', raw_factor) + ".parquet"
        filepath = os.path.join(MACRO_DIR, filename)
        
        # Load existing data to check for updates
        old_df = None
        old_max_date = None
        if os.path.exists(filepath):
            try:
                old_df = pd.read_parquet(filepath)
                if not old_df.empty:
                    if 'info_date' in old_df.index.names:
                        old_df = old_df.reset_index()
                    old_max_date = pd.to_datetime(old_df['info_date']).max()
            except Exception:
                pass
        
        print(f"[{idx+1}/{len(all_raw_factors)}] Fetching {cleaned_factor} (start={START_DATE}, end={END_DATE})...")
        try:
            new_df = rqdatac.econ.get_factors(
                cleaned_factor,
                start_date=START_DATE,
                end_date=END_DATE
            )
            if new_df is not None and not new_df.empty:
                if 'info_date' in new_df.index.names:
                    new_df = new_df.reset_index()
                new_max_date = pd.to_datetime(new_df['info_date']).max()
                
                # Check if there is new data
                is_updated = False
                if old_df is None:
                    is_updated = True
                    print(f"  New factor dataset downloaded.")
                elif len(new_df) > len(old_df) or (old_max_date is not None and new_max_date > old_max_date):
                    is_updated = True
                    print(f"  Updates found: {len(old_df)} -> {len(new_df)} rows, max date {old_max_date.date()} -> {new_max_date.date()}.")
                
                if is_updated:
                    # Convert to float32
                    if 'value' in new_df.columns:
                        new_df['value'] = new_df['value'].astype('float32')
                    # Save to parquet
                    if 'info_date' in new_df.columns:
                        new_df = new_df.set_index('info_date')
                    new_df.to_parquet(filepath, compression='zstd')
                    updated_count += 1
                else:
                    print("  No new data found.")
            else:
                print(f"  [WARNING] No data returned from API.")
            time.sleep(0.05)
        except Exception as e:
            print(f"  [ERROR] Failed to fetch: {e}")
            
    print(f"\n=== Update Completed: {updated_count}/{len(all_raw_factors)} factors updated. ===")

if __name__ == '__main__':
    update_factors()
