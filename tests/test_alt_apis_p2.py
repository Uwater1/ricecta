#!/usr/bin/env python3
"""Part 2: Macro, Energy, Shipping, Spot, News, FX, QDII, YFinance, Baostock."""
import os, json, warnings, time, signal
warnings.filterwarnings('ignore')
import pandas as pd
import akshare as ak
import yfinance as yf

OUT = '/data/ricecta/data_samples_alt'
os.makedirs(OUT, exist_ok=True)
results = {}

class TimeoutError(Exception): pass
def _to(signum, frame): raise TimeoutError()

def t(name, fn, *args, **kwargs):
    signal.signal(signal.SIGALRM, _to)
    signal.alarm(20)
    try:
        t0 = time.time(); df = fn(*args, **kwargs); dt = time.time()-t0; signal.alarm(0)
    except TimeoutError:
        signal.alarm(0); results[name]=['TIMEOUT','>20s',None,None]; print('  [TIMEOUT] '+name); return
    except Exception as e:
        signal.alarm(0); results[name]=['FAIL',str(e)[:300],None,None]; print('  [FAIL] '+name+': '+str(e)[:140]); return
    if isinstance(df, pd.DataFrame): shape=list(df.shape); sample=df.head(3).to_dict(orient='records') if len(df) else []
    elif isinstance(df, pd.Series): shape=[len(df)]; sample=df.head(3).to_dict()
    elif isinstance(df, dict): shape=[len(df)]; sample={k: (v.head(2).to_dict(orient='records') if isinstance(v,pd.DataFrame) else str(v)[:200]) for k,v in list(df.items())[:3]}
    elif isinstance(df, list): shape=[len(df)]; sample=df[:3]
    else: shape='scalar'; sample=str(df)[:300]
    results[name]=['OK','',sample,shape]
    print('  [OK]   '+name+': shape='+str(shape)+' ('+str(round(dt,1))+'s)')

def save():
    with open(os.path.join(OUT,'alt_api_test_results_p2.json'),'w',encoding='utf-8') as f:
        json.dump({k:[v[0],v[1],str(v[2]),v[3]] for k,v in results.items()}, f, ensure_ascii=False, indent=2, default=str)

# ============================================================
# SECTION 6: AkShare - Macro China (official NBS/PBOC)
# ============================================================
print('=' * 80)
print('6. AkShare - Macro China')
print('=' * 80)
t('ak.macro_china_cpi', ak.macro_china_cpi)
t('ak.macro_china_ppi', ak.macro_china_ppi)
t('ak.macro_china_pmi', ak.macro_china_pmi)
t('ak.macro_china_gdp', ak.macro_china_gdp)
t('ak.macro_china_m2_yearly', ak.macro_china_m2_yearly)
t('ak.macro_china_industrial_production_yoy', ak.macro_china_industrial_production_yoy)
t('ak.macro_china_consumer_goods_retail', ak.macro_china_consumer_goods_retail)
t('ak.macro_china_exports_yoy', ak.macro_china_exports_yoy)
t('ak.macro_china_imports_yoy', ak.macro_china_imports_yoy)
t('ak.macro_china_trade_balance', ak.macro_china_trade_balance)
t('ak.macro_china_fx_reserves_yearly', ak.macro_china_fx_reserves_yearly)
t('ak.macro_china_lpr', ak.macro_china_lpr)
t('ak.macro_china_reserve_requirement_ratio', ak.macro_china_reserve_requirement_ratio)
t('ak.macro_china_fdi', ak.macro_china_fdi)
t('ak.macro_china_new_financial_credit', ak.macro_china_new_financial_credit)
t('ak.macro_china_real_estate', ak.macro_china_real_estate)
t('ak.macro_china_society_electricity', ak.macro_china_society_electricity)
t('ak.macro_china_freight_index', ak.macro_china_freight_index)
t('ak.macro_china_supply_of_money', ak.macro_china_supply_of_money)
t('ak.macro_china_agricultural_product', ak.macro_china_agricultural_product)
t('ak.macro_china_commodity_price_index', ak.macro_china_commodity_price_index)
t('ak.macro_china_energy_index', ak.macro_china_energy_index)
t('ak.macro_china_construction_index', ak.macro_china_construction_index)
t('ak.macro_china_bdti_index', ak.macro_china_bdti_index)
t('ak.macro_china_bsi_index', ak.macro_china_bsi_index)
t('ak.macro_china_enterprise_boom_index', ak.macro_china_enterprise_boom_index)
t('ak.macro_china_swap_rate', ak.macro_china_swap_rate)
t('ak.macro_china_daily_energy', ak.macro_china_daily_energy)

# ============================================================
# SECTION 7: AkShare - US Macro (EIA, rig count, CPI, PMI...)
# ============================================================
print()
print('=' * 80)
print('7. AkShare - US Macro / Energy')
print('=' * 80)
t('ak.macro_usa_eia_crude_rate', ak.macro_usa_eia_crude_rate)
t('ak.macro_usa_api_crude_stock', ak.macro_usa_api_crude_stock)
t('ak.macro_usa_cpi_yoy', ak.macro_usa_cpi_yoy)
t('ak.macro_usa_ppi', ak.macro_usa_ppi)
t('ak.macro_usa_non_farm', ak.macro_usa_non_farm)
t('ak.macro_usa_unemployment_rate', ak.macro_usa_unemployment_rate)
t('ak.macro_usa_pmi', ak.macro_usa_pmi)
t('ak.macro_usa_ism_pmi', ak.macro_usa_ism_pmi)
t('ak.macro_usa_rig_count', ak.macro_usa_rig_count)
t('ak.macro_usa_industrial_production', ak.macro_usa_industrial_production)
t('ak.macro_usa_retail_sales', ak.macro_usa_retail_sales)
t('ak.macro_usa_trade_balance', ak.macro_usa_trade_balance)
t('ak.macro_usa_initial_jobless', ak.macro_usa_initial_jobless)
t('ak.macro_usa_building_permits', ak.macro_usa_building_permits)
t('ak.macro_usa_house_starts', ak.macro_usa_house_starts)
t('ak.macro_usa_gdp_monthly', ak.macro_usa_gdp_monthly)
t('ak.macro_usa_adp_employment', ak.macro_usa_adp_employment)
t('ak.macro_usa_cb_consumer_confidence', ak.macro_usa_cb_consumer_confidence)
t('ak.macro_usa_michigan_consumer_sentiment', ak.macro_usa_michigan_consumer_sentiment)
t('ak.macro_usa_core_pce_price', ak.macro_usa_core_pce_price)
t('ak.macro_usa_services_pmi', ak.macro_usa_services_pmi)
t('ak.macro_usa_durable_goods_orders', ak.macro_usa_durable_goods_orders)
t('ak.macro_usa_business_inventories', ak.macro_usa_business_inventories)
t('ak.macro_usa_current_account', ak.macro_usa_current_account)
t('ak.macro_usa_factory_orders', ak.macro_usa_factory_orders)

save(); print('=== Part 2a saved (OK='+str(sum(1 for v in results.values() if v[0]=='OK'))+') ===')
