#!/usr/bin/env python3
"""Part 2b: Shipping, Energy, Spot Goods, News, FX, QDII, YFinance, Baostock."""
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
    elif isinstance(df, dict): shape=[len(df)]; sample={k: str(v)[:200] for k,v in list(df.items())[:3]}
    elif isinstance(df, list): shape=[len(df)]; sample=df[:3]
    else: shape='scalar'; sample=str(df)[:300]
    results[name]=['OK','',sample,shape]
    print('  [OK]   '+name+': shape='+str(shape)+' ('+str(round(dt,1))+'s)')

def save():
    with open(os.path.join(OUT,'alt_api_test_results_p2b.json'),'w',encoding='utf-8') as f:
        json.dump({k:[v[0],v[1],str(v[2]),v[3]] for k,v in results.items()}, f, ensure_ascii=False, indent=2, default=str)

# ============================================================
# SECTION 8: AkShare - Shipping / Freight
# ============================================================
print('=' * 80)
print('8. AkShare - Shipping / Freight (Baltic/Drewry)')
print('=' * 80)
t('ak.macro_shipping_bdi', ak.macro_shipping_bdi)
t('ak.macro_shipping_bpi', ak.macro_shipping_bpi)
t('ak.macro_shipping_bci', ak.macro_shipping_bci)
t('ak.macro_shipping_bcti', ak.macro_shipping_bcti)
t('ak.drewry_wci_index', ak.drewry_wci_index)

# ============================================================
# SECTION 9: AkShare - Energy / Carbon / COMEX Inventory
# ============================================================
print()
print('=' * 80)
print('9. AkShare - Energy / Carbon')
print('=' * 80)
t('ak.energy_oil_hist', ak.energy_oil_hist)
t('ak.energy_oil_detail', ak.energy_oil_detail)
t('ak.energy_carbon_domestic', ak.energy_carbon_domestic)
t('ak.energy_carbon_eu', ak.energy_carbon_eu)
t('ak.futures_comex_inventory', ak.futures_comex_inventory)
t('ak.futures_to_spot_shfe', ak.futures_to_spot_shfe, date='20240315')
t('ak.futures_to_spot_dce', ak.futures_to_spot_dce, date='20240315')
t('ak.futures_to_spot_czce', ak.futures_to_spot_czce, date='20240315')
t('ak.futures_stock_shfe_js', ak.futures_stock_shfe_js, date='20240315')

# ============================================================
# SECTION 10: AkShare - Spot Goods (SGE, Soozhu, etc.)
# ============================================================
print()
print('=' * 80)
print('10. AkShare - Spot Goods')
print('=' * 80)
t('ak.spot_golden_benchmark_sge', ak.spot_golden_benchmark_sge)
t('ak.spot_silver_benchmark_sge', ak.spot_silver_benchmark_sge)
t('ak.spot_hist_sge (Au99.99)', ak.spot_hist_sge, symbol='Au99.99')
t('ak.spot_symbol_table_sge', ak.spot_symbol_table_sge)
t('ak.spot_goods (BDI)', ak.spot_goods, symbol='波罗的海干散货指数')
t('ak.spot_hog_soozhu', ak.spot_hog_soozhu)
t('ak.spot_soybean_price_soozhu', ak.spot_soybean_price_soozhu)
t('ak.spot_corn_price_soozhu', ak.spot_corn_price_soozhu)
t('ak.futures_hog_cost', ak.futures_hog_cost)
t('ak.futures_hog_core', ak.futures_hog_core)
t('ak.futures_hog_supply', ak.futures_hog_supply)

# ============================================================
# SECTION 11: AkShare - News / Air Quality / Migration
# ============================================================
print()
print('=' * 80)
print('11. AkShare - News / Air Quality / Migration')
print('=' * 80)
t('ak.futures_news_shmet', ak.futures_news_shmet)
t('ak.air_quality_rank', ak.air_quality_rank)
t('ak.air_quality_hebei', ak.air_quality_hebei)
t('ak.migration_scale_baidu (Guangzhou)', ak.migration_scale_baidu, area='广州市')

# ============================================================
# SECTION 12: AkShare - Interest Rate / FX / Currency
# ============================================================
print()
print('=' * 80)
print('12. AkShare - Interest Rate / FX / Currency')
print('=' * 80)
t('ak.macro_bank_china_interest_rate', ak.macro_bank_china_interest_rate)
t('ak.macro_bank_usa_interest_rate', ak.macro_bank_usa_interest_rate)
t('ak.fx_spot_quote', ak.fx_spot_quote)
t('ak.fx_swap_quote', ak.fx_swap_quote)
t('ak.currency_boc_safe', ak.currency_boc_safe)
t('ak.currency_boc_sina (USD)', ak.currency_boc_sina, symbol='美元')
t('ak.macro_fx_sentiment', ak.macro_fx_sentiment)

# ============================================================
# SECTION 13: AkShare - QDII / ETF / Index
# ============================================================
print()
print('=' * 80)
print('13. AkShare - QDII / ETF / Global Index')
print('=' * 80)
t('ak.qdii_e_comm_jsl', ak.qdii_e_comm_jsl)
t('ak.qdii_e_index_jsl', ak.qdii_e_index_jsl)
t('ak.futures_global_hist_em (HG00Y copper)', ak.futures_global_hist_em, symbol='HG00Y')
t('ak.futures_global_hist_em (CL00Y crude)', ak.futures_global_hist_em, symbol='CL00Y')
t('ak.futures_global_hist_em (GC00Y gold)', ak.futures_global_hist_em, symbol='GC00Y')
t('ak.futures_global_spot_em', ak.futures_global_spot_em)
t('ak.futures_derivative', ak.futures_derivative)
t('ak.futures_symbol_mark', ak.futures_symbol_mark)
t('ak.futures_rule', ak.futures_rule)
t('ak.futures_fees_info', ak.futures_fees_info)
t('ak.futures_contract_detail_em (CU2403)', ak.futures_contract_detail_em, symbol='CU2403')

# ============================================================
# SECTION 14: YFinance - Global Commodities
# ============================================================
print()
print('=' * 80)
print('14. YFinance - Global Commodities (no API key)')
print('=' * 80)
yf_map = {
    'CL=F': 'WTI Crude Oil', 'BZ=F': 'Brent Crude', 'NG=F': 'Natural Gas',
    'GC=F': 'Gold', 'SI=F': 'Silver', 'HG=F': 'Copper', 'PL=F': 'Platinum',
    'ZC=F': 'Corn', 'ZW=F': 'Wheat', 'ZS=F': 'Soybean', 'ZM=F': 'Soy Meal',
    'ZL=F': 'Soy Oil', 'CT=F': 'Cotton', 'SB=F': 'Sugar', 'KC=F': 'Coffee',
    'CC=F': 'Cocoa', 'HE=F': 'Lean Hogs', 'LE=F': 'Live Cattle',
}
for sym, desc in yf_map.items():
    try:
        tk = yf.Ticker(sym)
        df = tk.history(period='6mo', interval='1d')
        if df is not None and len(df) > 0:
            results['yf '+sym] = ['OK','',df.tail(2).reset_index().to_dict(orient='records'),[len(df),len(df.columns)]]
            print('  [OK]   yf '+sym+' ('+desc+'): rows='+str(len(df))+', latest_close='+str(round(float(df.iloc[-1]['Close']),2)))
        else:
            results['yf '+sym]=['FAIL','empty',None,None]; print('  [FAIL] yf '+sym+': empty')
    except Exception as e:
        results['yf '+sym]=['FAIL',str(e)[:200],None,None]; print('  [FAIL] yf '+sym+': '+str(e)[:120])

# ============================================================
# SECTION 15: YFinance - Macro Indices
# ============================================================
print()
print('=' * 80)
print('15. YFinance - Macro Indices (DXY, VIX, yields, A-shares)')
print('=' * 80)
yf_macro = {
    'DX-Y.NYB': 'DXY Dollar Index', '^VIX': 'VIX',
    '^TNX': 'US 10Y Yield', '^FVX': 'US 5Y Yield', '^TYX': 'US 30Y Yield',
    '^GSPC': 'S&P500', '^IXIC': 'Nasdaq', '^HSI': 'Hang Seng',
    '000300.SS': 'CSI300', '000905.SS': 'CSI500', '000852.SS': 'CSI1000',
    'CNY=X': 'USD/CNY', 'EURUSD=X': 'EUR/USD',
}
for sym, desc in yf_macro.items():
    try:
        tk = yf.Ticker(sym)
        df = tk.history(period='6mo', interval='1d')
        if df is not None and len(df) > 0:
            results['yf '+sym] = ['OK','',[{'close':float(df.iloc[-1]['Close']),'date':str(df.index[-1].date())}],[len(df),len(df.columns)]]
            print('  [OK]   yf '+sym+' ('+desc+'): close='+str(round(float(df.iloc[-1]['Close']),4)))
        else:
            results['yf '+sym]=['FAIL','empty',None,None]; print('  [FAIL] yf '+sym+': empty')
    except Exception as e:
        results['yf '+sym]=['FAIL',str(e)[:200],None,None]; print('  [FAIL] yf '+sym+': '+str(e)[:120])

# ============================================================
# SECTION 16: YFinance - Long history
# ============================================================
print()
print('=' * 80)
print('16. YFinance - Long history (5Y backfill)')
print('=' * 80)
for sym in ['CL=F', 'GC=F', 'HG=F', 'ZC=F', 'CT=F', 'NG=F', 'ZS=F']:
    try:
        tk = yf.Ticker(sym)
        df = tk.history(period='5y', interval='1d')
        if df is not None and len(df) > 0:
            results['yf 5y '+sym]=['OK','',{'from':str(df.index[0].date()),'to':str(df.index[-1].date()),'rows':len(df)},[len(df),len(df.columns)]]
            print('  [OK]   yf 5y '+sym+': '+str(df.shape)+', from='+str(df.index[0].date())+', to='+str(df.index[-1].date()))
        else:
            print('  [FAIL] yf 5y '+sym+': empty')
    except Exception as e:
        results['yf 5y '+sym]=['FAIL',str(e)[:200],None,None]; print('  [FAIL] yf 5y '+sym+': '+str(e)[:120])

# ============================================================
# SECTION 17: Baostock - A-share + macro
# ============================================================
print()
print('=' * 80)
print('17. Baostock - A-share + macro')
print('=' * 80)
import baostock as bs
lg = bs.login(); print('baostock login:', lg.error_code, lg.error_msg)
for code in ['sh.000300', 'sh.000905', 'sz.399006', 'sh.000852']:
    rs = bs.query_history_k_data_plus(code, 'date,open,high,low,close,volume,amount',
                                      start_date='2024-01-01', end_date='2024-03-31', frequency='d', adjustflag='2')
    rows = []
    while (rs.error_code=='0') and rs.next(): rows.append(rs.get_row_data())
    if rows:
        results['bs.'+code]=['OK','',rows[:2],[len(rows)]]
        print('  [OK]   bs.'+code+': '+str(len(rows))+' rows')
    else:
        results['bs.'+code]=['FAIL','no data',None,None]; print('  [FAIL] bs.'+code+': no data')

t('bs.query_trade_dates', bs.query_trade_dates, start_date='2024-01-01', end_date='2024-12-31')
t('bs.query_deposit_rate_data', bs.query_deposit_rate_data, start_date='2024-01-01', end_date='2024-12-31')
t('bs.query_loan_rate_data', bs.query_loan_rate_data, start_date='2024-01-01', end_date='2024-12-31')
t('bs.query_required_reserve_ratio_data', bs.query_required_reserve_ratio_data, start_date='2024-01-01', end_date='2024-12-31', yearType='0')
t('bs.query_money_supply_data_month', bs.query_money_supply_data_month, start_date='2024-01-01', end_date='2024-12-31')
bs.logout(); print('baostock logout')

save()
print('=== Part 2b saved ===')
n_ok = sum(1 for v in results.values() if v[0]=='OK')
n_fail = sum(1 for v in results.values() if v[0]=='FAIL')
n_to = sum(1 for v in results.values() if v[0]=='TIMEOUT')
print('OK='+str(n_ok)+' FAIL='+str(n_fail)+' TIMEOUT='+str(n_to))
