#!/usr/bin/env python3
"""Test supplementary data APIs: NOAA weather, CFETS, customs stats, SMM, GNews, SGE, freight."""
import os, json, warnings, time, signal, io, csv
warnings.filterwarnings('ignore')

import pandas as pd
import requests

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
# SECTION 1: NOAA CDO API (weather - direct HTTP, no key for datasets list)
# ============================================================
print('=' * 80)
print('1. NOAA CDO API (weather)')
print('=' * 80)

def noaa_datasets():
    r = requests.get('https://www.ncei.noaa.gov/cdo-web/api/v2/datasets?limit=5', timeout=15)
    return pd.DataFrame(r.json().get('results', []))

def noaa_stations(loc='FIPS:CN'):
    r = requests.get(
        'https://www.ncei.noaa.gov/cdo-web/api/v2/stations',
        params={'locationid': loc, 'limit': 5},
        headers={'token': 'YOUR_TOKEN_HERE'},
        timeout=15
    )
    data = r.json()
    return pd.DataFrame(data.get('results', []))

def noaa_fetch_station_data(station_id='GHCND:CHM00057006'):
    r = requests.get(
        'https://www.ncei.noaa.gov/cdo-web/api/v2/data',
        params={'datasetid': 'GHCND', 'stationid': station_id, 'startdate': '20240101', 'enddate': '20240131', 'limit': 10},
        headers={'token': 'YOUR_TOKEN_HERE'},
        timeout=15
    )
    data = r.json()
    return pd.DataFrame(data.get('results', []))

t('NOAA datasets list (no key)', noaa_datasets)
t('NOAA stations FIPS:CN (token required)', noaa_stations)
t('NOAA station data CHM00057006 Beijing Jan 2024 (token required)', noaa_fetch_station_data)

# ============================================================
# SECTION 2: CFETS FX / Rates (via akshare + direct CSV)
# ============================================================
print()
print('=' * 80)
print('2. CFETS FX/Rates (via akshare + direct URL)')
print('=' * 80)

def cffets_fixing_usd_cny():
    url = 'https://www.chinamoney.com.cn/ags/ms/cm-u-bk-ccy/CcsrHisNew?startDate=20240101&endDate=20240603&currency=USD/CNY&pageNum=1'
    try:
        r = requests.get(url, timeout=15)
        d = r.json()
        records = d.get('records', [])
        return pd.DataFrame(records)
    except Exception as e:
        return str(e)

def cffets_fx_spot():
    url = 'https://www.chinamoney.com.cn/ags/ms/cm-u-bk-fx/FxHisNew?startDate=20240101&endDate=20240603&pageNum=1'
    try:
        r = requests.get(url, timeout=15)
        d = r.json()
        records = d.get('records', [])
        return pd.DataFrame(records)
    except Exception as e:
        return str(e)

def cffets_shibor_daily():
    url = 'https://www.shibor.org/cn/shiborhome/rbvn/detail.asp?date=2024-01-02'
    try:
        r = requests.get(url, timeout=15)
        tables = pd.read_html(io.StringIO(r.text))
        return tables[0] if tables else 'no table'
    except Exception as e:
        return str(e)

t('CFETS USD/CNY fixing direct', cffets_fixing_usd_cny)
t('CFETS FX spot direct', cffets_fx_spot)
t('CFETS Shibor daily direct', cffets_shibor_daily)

# ============================================================
# SECTION 3: Customs Statistics (GACC) - HTML parse via pandas
# ============================================================
print()
print('=' * 80)
print('3. China Customs (GACC) statistics')
print('=' * 80)

def gacc_trade_summary():
    url = 'http://english.customs.gov.cn/Statistics/Statistics?ColumnId=1'
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        tables = pd.read_html(io.StringIO(r.text))
        return tables[0] if tables else 'no table found'
    except Exception as e:
        return str(e)

def gacc_port_import_export():
    url = 'http://english.customs.gov.cn/Statistics/Statistics?ColumnId=2'
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        tables = pd.read_html(io.StringIO(r.text))
        return tables[0] if tables else 'no table found'
    except Exception as e:
        return str(e)

t('GACC trade summary (HTML)', gacc_trade_summary)
t('GACC port trade (HTML)', gacc_port_import_export)

# ============================================================
# SECTION 4: Google News RSS (free, no key - news sentiment proxy)
# ============================================================
print()
print('=' * 80)
print('4. Google News RSS (sentiment proxy)')
print('=' * 80)

def google_news_rss_futures():
    url = 'https://news.google.com/rss/search?q=china+futures+commodity&hl=en-US&gl=US&ceid=US:en'
    r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
    import feedparser
    d = feedparser.parse(r.text)
    items = []
    for entry in d.entries[:5]:
        items.append({'title': entry.get('title', ''), 'link': entry.get('link', ''), 'published': entry.get('published', '')})
    return pd.DataFrame(items)

def google_news_rss_sc():
    url = 'https://news.google.com/rss/search?q=crude+oil+china&hl=en-US&gl=US&ceid=US:en'
    r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
    import feedparser
    d = feedparser.parse(r.text)
    items = []
    for entry in d.entries[:5]:
        items.append({'title': entry.get('title', ''), 'published': entry.get('published', '')})
    return pd.DataFrame(items)

try:
    t('Google News RSS: china futures', google_news_rss_futures)
    t('Google News RSS: crude oil china', google_news_rss_sc)
except ImportError:
    results['feedparser_check'] = ['FAIL', 'feedparser not installed', None, None]
    print('[FAIL] feedparser not installed - install with: pip install feedparser')

# ============================================================
# SECTION 5: SMM (Shanghai Metals Market) commodity data via akshare
# ============================================================
print()
print('=' * 80)
print('5. SMM / Shanghai Metals Market (via akshare)')
print('=' * 80)

def smm_price_daily(symbol='CU'):
    try:
        return ak.smm_price_daily(symbol=symbol)
    except Exception as e:
        return str(e)

def smm_spot_price_weekly(symbol='CU'):
    try:
        return ak.smm_spot_price_weekly(symbol=symbol)
    except Exception as e:
        return str(e)

t('SMM daily price CU', smm_price_daily, 'CU')
t('SMM spot weekly CU', smm_spot_price_weekly, 'CU')

# ============================================================
# SECTION 6: NBS 国家统计局 direct API (free, no key needed)
# ============================================================
print()
print('=' * 80)
print('6. NBS 国家统计局 direct API')
print('=' * 80)

def nbs_industrial_production():
    url = 'https://data.stats.gov.cn/easyquery.htm?m=getData&dbcode=hgyd&rowcode=reg&colcode=sj&wds=[]&dfwds=[{"valuecode":"A0202","wdcode":"zb"}]&k=20240101'
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        d = r.json()
        datanodes = d.get('returndata', {}).get('datanodes', [])
        rows = []
        for node in datanodes[:10]:
            rows.append({
                'code': node.get('code', ''),
                'name': node.get('name', ''),
                'data': node.get('data', {}).get('data', None),
                'hasdata': node.get('data', {}).get('hasdata', False)
            })
        return pd.DataFrame(rows)
    except Exception as e:
        return str(e)

def nbs_cpi():
    url = 'https://data.stats.gov.cn/easyquery.htm?m=getData&dbcode=hgyd&rowcode=reg&colcode=sj&wds=[]&dfwds=[{"valuecode":"A010101","wdcode":"zb"}]&k=20240101'
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        d = r.json()
        datanodes = d.get('returndata', {}).get('datanodes', [])
        rows = []
        for node in datanodes[:10]:
            rows.append({
                'code': node.get('code', ''),
                'name': node.get('name', ''),
                'data': node.get('data', {}).get('data', None),
            })
        return pd.DataFrame(rows)
    except Exception as e:
        return str(e)

def nbs_pmi():
    url = 'https://data.stats.gov.cn/easyquery.htm?m=getData&dbcode=hgyd&rowcode=reg&colcode=sj&wds=[]&dfwds=[{"valuecode":"A0701","wdcode":"zb"}]&k=20240101'
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        d = r.json()
        datanodes = d.get('returndata', {}).get('datanodes', [])
        rows = []
        for node in datanodes[:10]:
            rows.append({
                'code': node.get('code', ''),
                'name': node.get('name', ''),
                'data': node.get('data', {}).get('data', None),
            })
        return pd.DataFrame(rows)
    except Exception as e:
        return str(e)

t('NBS industrial production direct API', nbs_industrial_production)
t('NBS CPI direct API', nbs_cpi)
t('NBS PMI direct API', nbs_pmi)

# ============================================================
# SECTION 7: NOAA Global Historical Climatology Network (no token for dataset list)
# ============================================================
print()
print('=' * 80)
print('7. NOAA GHCN historical data (aggregate demo)')
print('=' * 80)

def noaa_ghcn_daily_station_china(since='20240101', until='20240131'):
    url = 'https://www.ncei.noaa.gov/cdo-web/api/v2/data'
    params = {
        'datasetid': 'GHCND',
        'locationid': 'FIPS:CN',
        'startdate': since[:4] + '-' + since[4:6] + '-' + since[6:8],
        'enddate': until[:4] + '-' + until[4:6] + '-' + until[6:8],
        'limit': 10,
        'offset': 1
    }
    r = requests.get(url, params=params, headers={'token': 'YOUR_TOKEN_HERE'}, timeout=15)
    d = r.json()
    records = d.get('results', [])
    return pd.DataFrame(records)

t('NOAA GHCN FIPS:CN Jan 2024 (token required)', noaa_ghcn_daily_station_china)

# ============================================================
# SECTION 8: SHFE daily stats via direct CSV download
# ============================================================
print()
print('=' * 80)
print('8. SHFE daily CSV statistics')
print('=' * 80)

def shfe_daily_csv(date='20240315'):
    url = f'https://www.shfe.com.cn/en/services/Technology/TechnicalSpecificationResource/202509/t20250915_829022.html'
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        return r.status_code
    except Exception as e:
        return str(e)

# SHFE: try endpoint known to serve CSV
def shfe_daily_stats_products():
    url = 'https://www.shfe.com.cn/en/services/Technology/TechnicalSpecificationResource/202509/t20250915_829022.html'
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        return r.status_code
    except Exception as e:
        return str(e)

t('SHFE tech spec page HTTP status', shfe_daily_stats_products)

# Try known daily stats endpoint - fmpubl01
def shfe_trade_daily(date_str='20240315'):
    url = f'https://www.shfe.com.cn/en/data/statdata/dailydata/{date_str}1dailydata.csv'
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code == 200 and len(r.text) > 20:
            df = pd.read_csv(io.StringIO(r.text))
            return df.head(3)
        return r.status_code
    except Exception as e:
        return str(e)

try:
    t('SHFE daily CSV 20240315', shfe_trade_daily, '20240315')
except Exception as e:
    results['SHFE daily CSV'] = ['FAIL', str(e)[:300], None, None]
    print('[FAIL] SHFE daily CSV: ' + str(e)[:160])

# ============================================================
# SECTION 9: EIA open data (energy inventories - free API)
# ============================================================
print()
print('=' * 80)
print('9. EIA v2 API (energy)')
print('=' * 80)

def eia_series(series_id='PET.WCRNTUS1.W'):
    url = 'https://api.eia.gov/v2/seriesdata/'
    params = {
        'frequency': 'weekly',
        'data[0][series_id]': series_id,
        'start': '20240101',
        'length': 10
    }
    # EIA v2 needs api_key
    return 'requires EIA API key from eia.gov'

def eia_crude_inventory_free():
    url = 'https://api.eia.gov/v2/petroleum/str/series/'
    try:
        r = requests.get(url, timeout=15)
        d = r.json()
        series = d.get('response', {}).get('data', [])
        return pd.DataFrame(series[:5])
    except Exception as e:
        return str(e)

t('EIA v2 series endpoint (no key, returns meta)', eia_crude_inventory_free)

# ============================================================
# SECTION 10: Baltic Exchange indices (via akshare fallback + direct)
# ============================================================
print()
print('=' * 80)
print('10. Baltic Dry / Freight indices (direct HTTP via akshare)')
print('=' * 80)

def balti_freight_spot():
    try:
        return ak.freight_index_spot()
    except Exception as e:
        return str(e)

try:
    t('AkShare freight index (Baltic spot fallback)', balti_freight_spot)
except Exception:
    pass

def balti_bdi_em():
    try:
        return ak.spot_goods(symbol='bdi')
    except Exception as e:
        return str(e)

t('AkShare spot_goods BDI (alt)', balti_bdi_em)

# spot_goods seems already tested and failed; check
try:
    t('spot_goods crude', ak.spot_goods, 'crude')
except Exception as e:
    results['spot_goods crude'] = ['FAIL', str(e)[:300], None, None]

try:
    t('energy_hist_sge coil', ak.energy_hist_sge, symbol='螺纹钢')
except Exception as e:
    pass  # may not exist

# ============================================================
# Save results and print summary
# ============================================================
save('alt_api_test_results_complement.json')
print()
print('=== Complement test saved ===')
n_ok = sum(1 for v in results.values() if v[0] == 'OK')
n_fail = sum(1 for v in results.values() if v[0] == 'FAIL')
n_to = sum(1 for v in results.values() if v[0] == 'TIMEOUT')
print(f'OK={n_ok} FAIL={n_fail} TIMEOUT={n_to}  Total={len(results)}')
