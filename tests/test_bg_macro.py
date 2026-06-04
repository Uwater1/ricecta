#!/usr/bin/env python3
"""Test background macro + commodity data APIs NOT covered by RQData (safe version)."""
import os, json, warnings, time, signal
warnings.filterwarnings('ignore')

import pandas as pd

OUT = '/data/ricecta/data_samples_alt'
os.makedirs(OUT, exist_ok=True)

results = {}

class TimeoutError(Exception):
    pass

def _timeout_handler(signum, frame):
    raise TimeoutError('timed out')

def t(name, fn, *args, **kwargs):
    sigalrm = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(20)
    try:
        t0 = time.time()
        df = fn(*args, **kwargs)
        dt = time.time() - t0
        signal.alarm(0)
    except TimeoutError:
        signal.alarm(0)
        results[name] = ['TIMEOUT', '> 20s', None, None]
        print('[TIMEOUT] ' + name)
        return
    except Exception as e:
        signal.alarm(0)
        results[name] = ['FAIL', str(e)[:300], None, None]
        print('[FAIL] ' + name + ': ' + str(e)[:160])
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
    print('[OK]   ' + name + ': shape=' + str(shape) + ' (' + str(round(dt, 1)) + 's)')

def save(fname):
    with open(os.path.join(OUT, fname), 'w', encoding='utf-8') as f:
        json.dump({k: [v[0], v[1], str(v[2]), v[3]] for k, v in results.items()}, f, ensure_ascii=False, indent=2, default=str)

import akshare as ak

# ============================================================
# SECTION 1: China Macro
# ============================================================
print('=' * 80)
print('1. AkShare - China Macro')
print('=' * 80)
apis_macro_cn = [
    ('macro_china_cpi', ak.macro_china_cpi, []),
    ('macro_china_ppi', ak.macro_china_ppi, []),
    ('macro_china_pmi', ak.macro_china_pmi, []),
    ('macro_china_gdp', ak.macro_china_gdp, []),
    ('macro_china_m2_yearly', ak.macro_china_m2_yearly, []),
    ('macro_china_supply_of_money', ak.macro_china_supply_of_money, []),
    ('macro_china_industrial_production_yoy', ak.macro_china_industrial_production_yoy, []),
    ('macro_china_exports_yoy', ak.macro_china_exports_yoy, []),
    ('macro_china_imports_yoy', ak.macro_china_imports_yoy, []),
    ('macro_china_lpr', ak.macro_china_lpr, []),
    ('macro_china_reserve_requirement_ratio', ak.macro_china_reserve_requirement_ratio, []),
    ('macro_china_new_financial_credit', ak.macro_china_new_financial_credit, []),
    ('macro_china_real_estate', ak.macro_china_real_estate, []),
    ('macro_china_society_electricity', ak.macro_china_society_electricity, []),
    ('macro_china_freight_index', ak.macro_china_freight_index, []),
    ('macro_china_agricultural_product', ak.macro_china_agricultural_product, []),
    ('macro_china_commodity_price_index', ak.macro_china_commodity_price_index, []),
    ('macro_china_energy_index', ak.macro_china_energy_index, []),
    ('macro_china_construction_index', ak.macro_china_construction_index, []),
    ('macro_china_enterprise_boom_index', ak.macro_china_enterprise_boom_index, []),
    ('macro_china_daily_energy', ak.macro_china_daily_energy, []),
    ('macro_china_bdti_index', ak.macro_china_bdti_index, []),
    ('macro_china_bsi_index', ak.macro_china_bsi_index, []),
]
for name, fn, args in apis_macro_cn:
    t(name, fn, *args)

# swap rate is flaky; keep but handle
t('macro_china_swap_rate', ak.macro_china_swap_rate)

# ============================================================
# SECTION 2: US Macro (best-effort; skip if missing)
# ============================================================
print()
print('=' * 80)
print('2. AkShare - US Macro')
print('=' * 80)
apis_usa = [
    ('macro_usa_eia_crude_rate', ak.macro_usa_eia_crude_rate, []),
    ('macro_usa_api_crude_stock', ak.macro_usa_api_crude_stock, []),
    ('macro_usa_rig_count', ak.macro_usa_rig_count, []),
    ('macro_usa_pmi', ak.macro_usa_pmi, []),
    ('macro_usa_ism_pmi', ak.macro_usa_ism_pmi, []),
    ('macro_usa_cpi_yoy', ak.macro_usa_cpi_yoy, []),
    ('macro_usa_ppi', ak.macro_usa_ppi, []),
    ('macro_usa_non_farm', ak.macro_usa_non_farm, []),
    ('macro_usa_unemployment_rate', ak.macro_usa_unemployment_rate, []),
    ('macro_usa_industrial_production', ak.macro_usa_industrial_production, []),
    ('macro_usa_retail_sales', ak.macro_usa_retail_sales, []),
    ('macro_usa_trade_balance', ak.macro_usa_trade_balance, []),
    ('macro_usa_initial_jobless', ak.macro_usa_initial_jobless, []),
    ('macro_usa_cb_consumer_confidence', ak.macro_usa_cb_consumer_confidence, []),
    ('macro_usa_michigan_sentiment', getattr(ak, 'macro_usa_michigan_sentiment', lambda: (_ for _ in ()).throw(AttributeError('missing'))), []),
    ('macro_usa_core_pce_price', ak.macro_usa_core_pce_price, []),
    ('macro_usa_durable_goods_orders', ak.macro_usa_durable_goods_orders, []),
    ('macro_usa_gdp_monthly', ak.macro_usa_gdp_monthly, []),
    ('macro_usa_adp_employment', ak.macro_usa_adp_employment, []),
    ('macro_usa_business_inventories', ak.macro_usa_business_inventories, []),
    ('macro_usa_factory_orders', ak.macro_usa_factory_orders, []),
]
for name, fn, args in apis_usa:
    t(name, fn, *args)

# ============================================================
# SECTION 3: wbdata - Global Macro
# ============================================================
print()
print('=' * 80)
print('3. wbdata - World Bank')
print('=' * 80)

import wbdata

wb_calls = [
    ('WB GDP current USD', 'NY.GDP.MKTP.CD'),
    ('WB GDP per capita', 'NY.GDP.PCAP.CD'),
    ('WB Inflation CPI', 'FP.CPI.TOTL'),
    ('WB Unemployment', 'SL.UEM.TOTL.ZS'),
    ('WB CO2 emissions', 'EN.ATM.CO2E.PC'),
    ('WB Fossil fuel consumption', 'EG.USE.COMM.FO.ZS'),
    ('WB Crop prod index', 'AG.PRD.CROP.XD'),
    ('WB Agricultural land', 'AG.LND.AGRI.ZS'),
    ('WB FDI net inflows', 'BX.KLT.DINV.WD.GD.ZS'),
    ('WB Broad money', 'FM.LBL.BMNY.CN'),
    ('WB Official exchange rate', 'PA.NUS.FCRF'),
]
for label, code in wb_calls:
    name = 'wbdata ' + label
    try:
        t0 = time.time()
        df = wbdata.get_dataframe({code: label}, data_date=None, convert_date=False)
        dt = time.time() - t0
        if isinstance(df, pd.DataFrame) and len(df):
            sample = df.head(3).to_dict(orient='records')
            shape = list(df.shape)
        elif isinstance(df, pd.DataFrame):
            sample = []
            shape = [0, 0]
        else:
            sample = str(df)[:200]
            shape = 'scalar'
        results[name] = ['OK', '', sample, shape]
        print('[OK]   ' + name + ': shape=' + str(shape) + ' (' + str(round(dt, 1)) + 's)')
    except Exception as e:
        results[name] = ['FAIL', str(e)[:300], None, None]
        print('[FAIL] ' + name + ': ' + str(e)[:160])

# ============================================================
# SECTION 4: Shipping, Spot, Alt + Energy
# ============================================================
print()
print('=' * 80)
print('4. AkShare - Shipping / Spot / Alt / Energy')
print('=' * 80)
alt_apis = [
    ('drewry_wci', ak.drewry_wci_index, []),
    ('spot_golden_benchmark_sge', ak.spot_golden_benchmark_sge, []),
    ('spot_silver_benchmark_sge', ak.spot_silver_benchmark_sge, []),
    ('spot_hist_sge Au99.99', ak.spot_hist_sge, ['Au99.99']),
    ('spot_goods bdi', ak.spot_goods, ['bdi']),
    ('spot_hog_soozhu', ak.spot_hog_soozhu, []),
    ('spot_soybean_price_soozhu', ak.spot_soybean_price_soozhu, []),
    ('spot_corn_price_soozhu', ak.spot_corn_price_soozhu, []),
    ('futures_hog_cost', ak.futures_hog_cost, []),
    ('futures_hog_core', ak.futures_hog_core, []),
    ('futures_hog_supply', ak.futures_hog_supply, []),
    ('air_quality_rank', ak.air_quality_rank, []),
    ('air_quality_hebei', ak.air_quality_hebei, []),
    ('futures_news_shmet', ak.futures_news_shmet, []),
    ('macro_bank_china_interest_rate', ak.macro_bank_china_interest_rate, []),
    ('macro_bank_usa_interest_rate', ak.macro_bank_usa_interest_rate, []),
    ('fx_spot_quote', ak.fx_spot_quote, []),
    ('fx_swap_quote', ak.fx_swap_quote, []),
    ('currency_boc_safe', ak.currency_boc_safe, []),
    ('qdii_e_comm_jsl', ak.qdii_e_comm_jsl, []),
    ('qdii_e_index_jsl', ak.qdii_e_index_jsl, []),
    ('energy_oil_hist', ak.energy_oil_hist, []),
    ('energy_oil_detail', ak.energy_oil_detail, []),
    ('energy_carbon_domestic', ak.energy_carbon_domestic, []),
    ('energy_carbon_eu', ak.energy_carbon_eu, []),
    ('futures_zh_realtime CU2405', ak.futures_zh_realtime, ['CU2405']),
    ('futures_zh_daily_sina CU2405', ak.futures_zh_daily_sina, ['CU2405']),
    ('futures_zh_minute_sina CU2405 1min', ak.futures_zh_minute_sina, ['CU2405', '1']),
    ('get_shfe_daily 20240315', ak.get_shfe_daily, ['20240315']),
    ('get_dce_daily 20240315', ak.get_dce_daily, ['20240315']),
]
for name, fn, args in alt_apis:
    t(name, fn, *args)

# ============================================================
# SECTION 5: tushare (free token fallback)
# ============================================================
print()
print('=' * 80)
print('5. tushare basic stock + macro (free / no-token endpoints)')
print('=' * 80)

import tushare as ts

# tushare Pro init - requires token, some pro APIs will fail without it
# Many basic APIs work with token-less or via `ts.pro_api()`
# Test a few that are known to need token (we still test; may FAIL)
tushare_apis = [
    ('tushare daily CU (pro_bar, no token)', lambda: ts.pro_bar(ts_code='000001.SZ', api=None), []),
    ('tushare trade_cal', lambda: ts.trade_cal(exchange='', start_date='20240101', end_date='20240110'), []),
    ('tushare daily basic (token required?)', lambda: ts.daily(trade_date='20240101', ts_code='000001.SZ'), []),
]
for name, fn, args in tushare_apis:
    t(name, fn, *args)

save('alt_api_test_results_bg.json')
print()
print('=== Background macro test saved ===')
n_ok = sum(1 for v in results.values() if v[0]=='OK')
n_fail = sum(1 for v in results.values() if v[0]=='FAIL')
n_to = sum(1 for v in results.values() if v[0]=='TIMEOUT')
print('OK=' + str(n_ok) + ' FAIL=' + str(n_fail) + ' TIMEOUT=' + str(n_to))
