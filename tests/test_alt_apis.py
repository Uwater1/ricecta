#!/usr/bin/env python3
"""Test additional data sources (NOT covered by RQData) for the 23 China commodity futures."""
import os, json, warnings, time, signal
warnings.filterwarnings('ignore')

import pandas as pd
import akshare as ak
import yfinance as yf

OUT = '/data/ricecta/data_samples_alt'
os.makedirs(OUT, exist_ok=True)

results = {}

class TimeoutError(Exception):
    pass

def _timeout_handler(signum, frame):
    raise TimeoutError('timed out')

def t(name, fn, *args, **kwargs):
    """Test function with a 15s timeout. Skips on timeout."""
    sigalrm = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(15)  # 15 second timeout
    try:
        t0 = time.time()
        df = fn(*args, **kwargs)
        dt = time.time() - t0
        signal.alarm(0)  # cancel timeout
    except TimeoutError:
        signal.alarm(0)
        results[name] = ['TIMEOUT', '> 15s', None, None]
        print('  [TIMEOUT] ' + name)
        return
    except Exception as e:
        signal.alarm(0)
        results[name] = ['FAIL', str(e)[:300], None, None]
        print('  [FAIL] ' + name + ': ' + str(e)[:160])
        return
    if isinstance(df, pd.DataFrame):
        sample = df.head(3).to_dict(orient='records') if len(df) else []
        shape = list(df.shape)
    elif isinstance(df, pd.Series):
        sample = df.head(3).to_dict()
        shape = [len(df)]
    elif isinstance(df, dict):
        sample = {k: (v.head(2).to_dict(orient='records') if isinstance(v, pd.DataFrame) else str(v)[:200]) for k, v in list(df.items())[:3]}
        shape = [len(df)]
    elif isinstance(df, list):
        sample = df[:3] if not df or not isinstance(df[0], dict) else [{k: str(v)[:80] for k, v in d.items()} for d in df[:3]]
        shape = [len(df)]
    else:
        sample = str(df)[:300]
        shape = 'scalar'
    results[name] = ['OK', '', sample, shape]
    print('  [OK]   ' + name + ': shape=' + str(shape) + ' (' + str(round(dt, 1)) + 's)')

def save():
    with open(os.path.join(OUT, 'alt_api_test_results.json'), 'w', encoding='utf-8') as f:
        json.dump({k: [v[0], v[1], str(v[2]), v[3]] for k, v in results.items()}, f, ensure_ascii=False, indent=2, default=str)

# ============================================================
# SECTION 1: AkShare - Foreign Commodity Futures
# ============================================================
print('=' * 80)
print('1. AkShare - Foreign Commodity Futures (cross-market)')
print('=' * 80)
t('ak.futures_foreign_commodity_subscribe_exchange_symbol', ak.futures_foreign_commodity_subscribe_exchange_symbol)
for sym in ['HG', 'CL', 'GC', 'SI', 'CT', 'C', 'W', 'S', 'BO', 'SM',
            'NG', 'XAU', 'XAG', 'XPT', 'XPD', 'OIL', 'FCPO', 'RSS3', 'NID', 'PBD']:
    t('ak.futures_foreign_hist ' + sym, ak.futures_foreign_hist, symbol=sym)
for sym in ['HG', 'CL', 'GC', 'SI', 'CT', 'C', 'W', 'S', 'BO', 'NG']:
    t('ak.futures_foreign_detail ' + sym, ak.futures_foreign_detail, symbol=sym)
for sym in ['HG', 'CL', 'GC', 'SI', 'CT', 'C', 'W', 'S', 'BO', 'NG']:
    t('ak.futures_foreign_commodity_realtime ' + sym, ak.futures_foreign_commodity_realtime, symbol=sym)

# ============================================================
# SECTION 2: AkShare - Domestic Spot Price (100ppi)
# ============================================================
print()
print('=' * 80)
print('2. AkShare - Domestic Spot Price (100ppi via Eastmoney)')
print('=' * 80)
t('ak.futures_spot_price all (default date)', ak.futures_spot_price)
t('ak.futures_spot_price 20240315 [12 majors]', ak.futures_spot_price, date='20240315', vars_list=['CU', 'AU', 'RB', 'I', 'SC', 'CF', 'SR', 'TA', 'MA', 'SA', 'C', 'M'])
t('ak.futures_spot_price 20240315 [aluminum, nickel, etc.]', ak.futures_spot_price, date='20240315', vars_list=['AL', 'NI', 'SN', 'ZN', 'PB', 'AG', 'JD', 'JM', 'PP', 'V', 'Y', 'P'])
t('ak.futures_spot_price_previous 20240315', ak.futures_spot_price_previous, date='20240315')
t('ak.futures_spot_price_daily 20240101-20240131 [CU/AU/RB/I]', ak.futures_spot_price_daily, start_day='20240101', end_day='20240131', vars_list=['CU', 'AU', 'RB', 'I'])
t('ak.futures_spot_price_daily 20240101-20240131 [C/M/Y/SC/MA]', ak.futures_spot_price_daily, start_day='20240101', end_day='20240131', vars_list=['C', 'M', 'Y', 'SC', 'MA'])

# ============================================================
# SECTION 3: AkShare - Position Rank (DCE / GFEX)
# ============================================================
print()
print('=' * 80)
print('3. AkShare - Position Rank (DCE / GFEX)')
print('=' * 80)
# DCE direct (may fail due to DCE server 412)
t('ak.futures_dce_position_rank 20240115 [C/M/Y/P/V/J/JD/I/L/PP/A/B/JM]', ak.futures_dce_position_rank, date='20240115', vars_list=['C', 'M', 'Y', 'P', 'V', 'J', 'JD', 'I', 'L', 'PP', 'A', 'B', 'JM'])
# GFEX
t('ak.futures_gfex_position_rank 20240315 [SI/LC/GF]', ak.futures_gfex_position_rank, date='20240315', vars_list=['SI', 'LC', 'GF'])
# Exchange rank tables (DCE server 412 today; try SHFE/CZCE/CFFEX only)
t('ak.get_shfe_rank_table 20240115 [CU/AU]', ak.get_shfe_rank_table, date='20240115', vars_list=['CU', 'AU'])
t('ak.get_rank_table_czce 20240115', ak.get_rank_table_czce, date='20240115')
t('ak.get_cffex_rank_table 20240115 [TF]', ak.get_cffex_rank_table, date='20240115', vars_list=['TF'])

# ============================================================
# SECTION 4: AkShare - Inventory (Eastmoney)
# ============================================================
print()
print('=' * 80)
print('4. AkShare - Inventory (Eastmoney) per-symbol')
print('=' * 80)
for sym in ['CU', 'AU', 'AG', 'AL', 'NI', 'SN', 'ZN', 'PB', 'RB', 'WR', 'HC', 'RU',
            'C', 'M', 'Y', 'P', 'A', 'JD', 'L', 'V', 'PP', 'J', 'JM', 'I', 'B', 'BB',
            'SC', 'FU', 'BU', 'EC', 'PG', 'EB',
            'CF', 'SR', 'TA', 'MA', 'SA', 'OI', 'RM', 'RS', 'WH', 'PM']:
    t('ak.futures_inventory_em ' + sym, ak.futures_inventory_em, symbol=sym)

# ============================================================
# SECTION 5: AkShare - Warehouse Receipts
# ============================================================
print()
print('=' * 80)
print('5. AkShare - Warehouse Receipts (SHFE/DCE/CZCE/GFEX)')
print('=' * 80)
t('ak.futures_shfe_warehouse_receipt 20240315', ak.futures_shfe_warehouse_receipt, date='20240315')
t('ak.futures_warehouse_receipt_dce 20240315', ak.futures_warehouse_receipt_dce, date='20240315')
t('ak.futures_warehouse_receipt_czce 20240315', ak.futures_warehouse_receipt_czce, date='20240315')
t('ak.futures_gfex_warehouse_receipt 20240315', ak.futures_gfex_warehouse_receipt, date='20240315')
t('ak.futures_inventory_99 (a, 豆一)', ak.futures_inventory_99, symbol='a')
t('ak.futures_comex_inventory (黄金 gold)', ak.futures_comex_inventory, symbol='黄金')

save()
print('=== Part 1 saved ===')
n_ok = sum(1 for v in results.values() if v[0]=='OK')
n_fail = sum(1 for v in results.values() if v[0]=='FAIL')
n_to = sum(1 for v in results.values() if v[0]=='TIMEOUT')
print('OK=' + str(n_ok) + ' FAIL=' + str(n_fail) + ' TIMEOUT=' + str(n_to))
