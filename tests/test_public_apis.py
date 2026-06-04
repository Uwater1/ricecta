#!/usr/bin/env python3
"""Test truly free, zero-auth, zero-package-required public APIs for alpha data."""
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
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(25)
    try:
        t0 = time.time()
        df = fn(*args, **kwargs)
        dt = time.time() - t0
        signal.alarm(0)
    except TimeoutError:
        signal.alarm(0)
        results[name] = ['TIMEOUT', '> 25s', None, None]
        print('[TIMEOUT] ', name)
        return
    except Exception as e:
        signal.alarm(0)
        results[name] = ['FAIL', str(e)[:500], None, None]
        print('[FAIL] ', name, ': ', str(e)[:200])
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
    elif isinstance(df, str):
        sample = df[:300]
        shape = 'str'
    else:
        sample = str(df)[:300]
        shape = 'scalar'
    results[name] = ['OK', '', sample, shape]
    print('[OK]   ', name, ': shape=', str(shape), ' (', str(round(dt, 1)), 's)')

def save(fname):
    with open(os.path.join(OUT, fname), 'w', encoding='utf-8') as f:
        json.dump({k: [v[0], v[1], str(v[2]), v[3]] for k, v in results.items()}, f, ensure_ascii=False, indent=2, default=str)

# ============================================================
# SECTION 1: Open-Meteo Historical Weather (zero-auth, crucial for C/M/CF/SR/TA)
# ============================================================
print('=' * 80)
print('1. Open-Meteo Historical Weather (free, no key)')
print('=' * 80)

def openmeteo_hist(lat=31.2, lon=121.5, start='2024-01-01', end='2024-01-31'):
    url = 'https://archive-api.open-meteo.com/v1/archive'
    params = {
        'latitude': lat, 'longitude': lon,
        'start_date': start, 'end_date': end,
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,ET0_fao_evapotranspiration',
        'timezone': 'Asia/Shanghai'
    }
    r = requests.get(url, params=params, timeout=20)
    d = r.json()
    daily = d.get('daily', {})
    if not daily:
        return str(d)[:200]
    return pd.DataFrame(daily)

def openmeteo_forecast(lat=39.9, lon=116.4):
    url = 'https://api.open-meteo.com/v1/forecast'
    params = {
        'latitude': lat, 'longitude': lon,
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_probability_max',
        'forecast_days': 7,
        'timezone': 'Asia/Shanghai'
    }
    r = requests.get(url, params=params, timeout=20)
    d = r.json()
    daily = d.get('daily', {})
    if not daily:
        return str(d)[:200]
    return pd.DataFrame(daily)

# Key agricultural provinces: 东北(玉米), 华北(棉花/红枣), 华南(橡胶), 山东(花生/蔬菜)
def openmeteo_multiloc():
    locs = [
        ('Daqing', 46.6, 125.0, 'corn_Heilongjiang'),
        ('Jiamusi', 46.8, 130.3, 'corn_Heilongjiang_east'),
        ('Shenyang', 41.8, 123.4, 'corn_Liaoning'),
        ('Shijiazhuang', 38.0, 114.5, 'cotton_Hebei'),
        ('Zhengzhou', 34.7, 113.6, 'cotton_Henan'),
        ('Wuhan', 30.6, 114.3, 'rubber_mid'),
        ('Haikou', 20.0, 110.3, 'rubber_Hainan'),
        ('Kunming', 25.0, 102.7, 'sugar_Yunnan'),
        ('Guangzhou', 23.1, 113.3, 'sugar_Guangxi'),
        ('Nanjing', 32.1, 118.8, 'rapeseed'),
        ('Chengdu', 30.6, 104.1, 'rapeseed_Sichuan'),
    ]
    rows = []
    for name, lat, lon, crop in locs:
        url = 'https://archive-api.open-meteo.com/v1/archive'
        params = {
            'latitude': lat, 'longitude': lon,
            'start_date': '20240101', 'end_date': '20240131',
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
            'timezone': 'Asia/Shanghai'
        }
        r = requests.get(url, params=params, timeout=15)
        d = r.json()
        daily = d.get('daily', {})
        if daily.get('time'):
            rows.append({
                'location': name, 'crop_zone': crop,
                'mean_temp': sum(daily.get('temperature_2m_max', [0])) / max(len(daily.get('temperature_2m_max', [1])), 1),
                'total_precip': sum(daily.get('precipitation_sum', [0])),
                'n_days': len(daily.get('time', []))
            })
    return pd.DataFrame(rows)

t('open-meteo Shanghai Jan 2024 hist', openmeteo_hist, 31.2, 121.5, '20240101', '20240131')
t('open-meteo Beijing forecast 7d', openmeteo_forecast, 39.9, 116.4)
t('open-meteo multi-loc crop zones Jan2024', openmeteo_multiloc)

# ============================================================
# SECTION 2: World Bank Open Data API (direct HTTP, zero-auth, no package)
# ============================================================
print()
print('=' * 80)
print('2. World Bank Open Data API (direct HTTP)')
print('=' * 80)

def wb_api(indicator, country='CN', per_page=20):
    url = f'https://api.worldbank.org/v2/country/{country}/indicator/{indicator}'
    params = {'format': 'json', 'per_page': per_page, 'date': '2018:2024'}
    r = requests.get(url, params=params, timeout=15)
    d = r.json()
    if isinstance(d, list) and len(d) > 1 and d[1]:
        data = d[1]
        rows = [{'date': x['date'], 'value': x['value'], 'country': x['country']['value']} for x in data]
        return pd.DataFrame(rows)
    return str(d)[:200]

wb_indicators = [
    ('NV.IND.TOTL.ZS', 'Industrial production (% of value added)'),
    ('FP.CPI.TOTL.ZG', 'Inflation consumer prices annual %'),
    ('SL.UEM.TOTL.ZS', 'Unemployment total %'),
    ('NY.GDP.MKTP.KD.ZG', 'GDP growth annual %'),
    ('NE.EXP.GNFS.ZS', 'Exports goods services % GDP'),
    ('BX.KLT.DINV.WD.GD.ZS', 'FDI net inflows % GDP'),
    ('EG.USE.COMM.FO.ZS', 'Fossil fuel energy consumption %'),
    ('EN.ATM.CO2E.PC', 'CO2 emissions metric tons per capita'),
    ('AG.LND.AGRI.ZS', 'Agricultural land % land area'),
    ('NV.AGR.TOTL.ZS', 'Agriculture value added % GDP'),
]
for code, name in wb_indicators:
    t('WB ' + name[:40], wb_api, code, 'CN')

# Global GDP growth for context
t('WB GDP growth USA', wb_api, 'NY.GDP.MKTP.KD.ZG', 'US')
t('WB GDP growth World', wb_api, 'NY.GDP.MKTP.KD.ZG', '1W')

# ============================================================
# SECTION 3: IMF Data API (direct HTTP, no key, no package)
# ============================================================
print()
print('=' * 80)
print('3. IMF Data API (direct HTTP)')
print('=' * 80)

def imf_dataflow():
    url = 'https://dataservices.imf.org/fruapim?dso=Fruapim&repid=FRH&prog=dsFlowRef&dsName=IMF%20World%20Economic%20Outlook%20(WEO)'
    try:
        r = requests.get(url, timeout=15)
        return r.status_code, r.text[:200]
    except Exception as e:
        return str(e), ''

def imf_compressed():
    url = 'https://dataservices.imf.org/fruapim?dso=Fruapim&repId=COM&prog=dsCompressed'
    try:
        r = requests.get(url, timeout=15, headers={'Accept': 'application/json'})
        d = r.json()
        keys = list(d.keys())[:5] if isinstance(d, dict) else list(d)[:5]
        return {'status': r.status_code, 'keys': keys, 'len': len(d) if hasattr(d, '__len__') else 'N/A'}
    except Exception as e:
        return str(e)

def imf_weo_query(database_id='WEO', country='CN', indicator='NGDP_R'):
    url = 'https://dataservices.imf.org/fruapim?dso=Fruapim&repId=WEO&prog=dsData'
    params = {'databaseId': database_id, 'country': country, 'indicator': indicator, 'format': 'json'}
    try:
        r = requests.get(url, params=params, timeout=15)
        return r.status_code, r.text[:200]
    except Exception as e:
        return str(e)

def imf_cpor_url():
    url = 'https://dataservices.imf.org/fruapim?dso=Fruapim&repId=CPOR&prog=dsData'
    params = {'databaseId': 'CPOR', 'country': 'CN', 'format': 'json'}
    try:
        r = requests.get(url, params=params, timeout=15)
        d = r.json()
        keys = list(d.keys())[:5] if isinstance(d, dict) else list(d)[:5]
        return {'status': r.status_code, 'keys': keys}
    except Exception as e:
        return str(e)[:200]

t('IMF dataflow WEO', imf_dataflow)
t('IMF compressed list', imf_compressed)
t('IMF WEO query CN NGDP_R', imf_weo_query, 'WEO', 'CN', 'NGDP_R')
t('IMF CPOR commodity prices', imf_cpor_url)

# ============================================================
# SECTION 4: FAO STAT / FAOSTAT (direct HTTP, no key)
# ============================================================
print()
print('=' * 80)
print('4. FAOSTAT / FAO bulk data (direct HTTP)')
print('=' * 80)

def faostat_bulk_dates():
    url = 'http://fenixservices.fao.org/faostat/api/v1/en/dates'
    try:
        r = requests.get(url, timeout=15)
        d = r.json()
        if isinstance(d, dict):
            dates = d.get('data', [])[:5]
            return pd.DataFrame(dates) if dates else str(d)[:200]
        return str(d)[:200]
    except Exception as e:
        return str(e)

def faostat_commodities():
    url = 'http://fenixservices.fao.org/faostat/api/v1/en/items/groups'
    try:
        r = requests.get(url, timeout=15)
        d = r.json()
        if isinstance(d, dict):
            data = d.get('data', [])
            # filter for crop/agri-related
            keywords = ['Crop', 'Agricultural', 'Live', 'Meat', 'Dairy', 'Cereals', 'Oil', 'Sugar', 'Cotton']
            crops = [x for x in data if any(kw in str(x.get('label', '')) for kw in keywords)]
            return pd.DataFrame(crops[:10])
        return str(d)[:200]
    except Exception as e:
        return str(e)

def faostat_production_wheat():
    url = 'http://fenixservices.fao.org/faostat/api/v1/en/data/QC'
    params = {
        'area_codes': '150, Chin',
        'item_codes': '15',
        'element_codes': '5510',
        'year': '2022,2023',
        'format': 'json'
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        d = r.json()
        if isinstance(d, dict):
            data = d.get('data', [])
            rows = [{k: x.get(k) for k in ['area', 'year', 'item', 'value']} for x in data[:10]]
            return pd.DataFrame(rows)
        return str(d)[:200]
    except Exception as e:
        return str(e)

t('FAOSTAT dates list', faostat_bulk_dates)
t('FAOSTAT commodity groups', faostat_commodities)
t('FAOSTAT wheat production CN recent', faostat_production_wheat)

# ============================================================
# SECTION 5: UN Comtrade API (public, no key for single queries)
# ============================================================
print()
print('=' * 80)
print('5. UN Comtrade API (trade flows)')
print('=' * 80)

def comtrade_monthly(reporter='156', partner='all', commodity='10', year='2023', month='1'):
    url = 'https://comtradeapi.un.org/api/get/bulk/C/A/HS'
    params = {
        'reporterCode': reporter,
        'partnerCode': partner,
        'cmdCode': commodity,
        'period': f'{year}{month:02d}',
        'format': 'JSON'
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        d = r.json()
        if isinstance(d, dict):
            data = d.get('data', [])
            return pd.DataFrame(data[:5]) if data else str(d)[:200]
        return str(d)[:200]
    except Exception as e:
        return str(e)

# Commodity codes: 1001=wheat, 1003=barley, 1005=maize, 1201=soybean, 1507=soybean oil, 1701=sugar
# Country code 156=China, 842=USA
def comtrade_summary_single(reporter='156', commodity='1005', year='2023'):
    url = 'https://comtradeapi.un.org/api/get/bulk/C/A/HS'
    params = {
        'reporterCode': reporter,
        'partnerCode': '0',
        'cmdCode': commodity,
        'period': year,
        'format': 'JSON'
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        d = r.json()
        if isinstance(d, dict):
            data = d.get('data', [])
            rows = [{k: x.get(k) for k in ['reporterDesc', 'partnerDesc', 'cmdCode', 'period', 'primaryValue']} for x in data[:5]]
            return pd.DataFrame(rows) if rows else str(d)[:200]
        return str(d)[:200]
    except Exception as e:
        return str(e)

t('Comtrade CN maize imports 2023', comtrade_summary_single, '156', '1005', '2023')
t('Comtrade CN wheat imports 2023', comtrade_summary_single, '156', '1001', '2023')
t('Comtrade CN soybean imports 2023', comtrade_summary_single, '156', '1201', '2023')
t('Comtrade CN crude oil imports 2023', comtrade_summary_single, '156', '2709', '2023')
t('Comtrade CN copper ore imports 2023', comtrade_summary_single, '156', '2603', '2023')

# ============================================================
# SECTION 6: EIA Series Metadata (no key, direct HTTP)
# ============================================================
print()
print('=' * 80)
print('6. EIA API v2 series metadata (no key)')
print('=' * 80)

def eia_series_catalog():
    url = 'https://api.eia.gov/v2/series/'
    params = {
        'frequency': 'weekly',
        'data[0][series_id]': 'PET.WCRNTUS1.W',
        'start': '202401',
        'length': 5
    }
    headers = {'X-Params': json.dumps(params)}
    r = requests.get('https://api.eia.gov/v2/petroleum/str/series/', timeout=15)
    try:
        d = r.json()
        response = d.get('response', {})
        data = response.get('data', [])
        return pd.DataFrame(data[:5]) if data else str(d)[:300]
    except Exception as e:
        return str(e)

def eia_rss_headlines():
    url = 'https://www.eia.gov/rss/rss.xml'
    try:
        import feedparser
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        d = feedparser.parse(r.text)
        items = [{'title': e.get('title', ''), 'published': e.get('published', '')} for e in d.entries[:5]]
        return pd.DataFrame(items)
    except ImportError:
        return 'feedparser not installed'
    except Exception as e:
        return str(e)

t('EIA v2 petroleum series catalog', eia_series_catalog)
try:
    t('EIA RSS news headlines', eia_rss_headlines)
except Exception as e:
    results['EIA RSS'] = ['FAIL', str(e)[:300], None, None]
    print('[FAIL] EIA RSS: ', str(e)[:200])

# ============================================================
# SECTION 7: NOAA National Weather Service API (US only, zero-auth)
# ============================================================
print()
print('=' * 80)
print('7. NOAA NWS API (US forecasts, zero-auth)')
print('=' * 80)

def nws_gridpoint_forecast(office='OKX', grid_x=33, grid_y=34):
    url = f'https://api.weather.gov/gridpoints/{office}/{grid_x},{grid_y}/forecast'
    headers = {'User-Agent': 'FuturesDataCollector/1.0 test@example.com'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        d = r.json()
        periods = d.get('properties', {}).get('periods', [])
        rows = [{k: p.get(k) for k in ['name', 'temperature', 'temperatureUnit', 'windSpeed', 'shortForecast']} for p in periods[:6]]
        return pd.DataFrame(rows)
    except Exception as e:
        return str(e)

def nws_alerts_active():
    url = 'https://api.weather.gov/alerts/active'
    headers = {'User-Agent': 'FuturesDataCollector/1.0 test@example.com'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        d = r.json()
        features = d.get('features', [])
        rows = [{'event': f.get('properties', {}).get('event', ''),
                 'area': f.get('properties', {}).get('areaDesc', ''),
                 'severity': f.get('properties', {}).get('severity', '')} for f in features[:5]]
        return pd.DataFrame(rows)
    except Exception as e:
        return str(e)

t('NWS gridpoint forecast NY (OKX)', nws_gridpoint_forecast, 'OKX', 33, 34)
t('NWS active weather alerts', nws_alerts_active)

# ============================================================
# SECTION 8: XE.com Currency (free no-auth RSS/HTML)
# ============================================================
print()
print('=' * 80)
print('8. Open Exchange Rates RSS fallback + Frankfurter API')
print('=' * 80)

def frankfurter_api(base='USD', symbol='CNY', start='2024-01-01', end='2024-01-31'):
    url = f'https://api.frankfurter.app/{start}..{end}'
    params = {'from': base, 'to': symbol}
    try:
        r = requests.get(url, params=params, timeout=15)
        d = r.json()
        rates = d.get('rates', {})
        rows = [{'date': k, 'rate': v.get(symbol)} for k, v in list(rates.items())[:10]]
        return pd.DataFrame(rows)
    except Exception as e:
        return str(e)

t('Frankfurter USD/CNY Jan 2024', frankfurter_api, 'USD', 'CNY')
t('Frankfurter USD/CNY 2024-WTD', frankfurter_api, 'USD', 'CNY', '2024-01-01', '2024-12-31')

# ============================================================
# SECTION 9: GBIF / iNaturalist (biodiversity proxy for agri weather impact)
# ============================================================
print()
print('=' * 80)
print('9. GBIF API (biodiversity occurrence - agri proxy)')
print('=' * 80)

def gbif_china_moth_species():
    url = 'https://api.gbif.org/v1/occurrence/search'
    params = {
        'country': 'CN',
        'scientificName': 'Helicoverpa armigera',  # cotton bollworm
        'limit': 10,
        'year': '2020,2021,2022,2023'
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        d = r.json()
        results_list = d.get('results', [])
        rows = [{k: x.get(k) for k in ['scientificName', 'stateProvince', 'year', 'decimalLatitude', 'decimalLongitude']} for x in results_list[:5]]
        return pd.DataFrame(rows)
    except Exception as e:
        return str(e)

t('GBIF cotton bollworm occurrences CN', gbif_china_moth_species)

# ============================================================
# Save
# ============================================================
save('alt_api_test_results_public.json')
print()
print('=== Public API test saved ===')
n_ok = sum(1 for v in results.values() if v[0] == 'OK')
n_fail = sum(1 for v in results.values() if v[0] == 'FAIL')
n_to = sum(1 for v in results.values() if v[0] == 'TIMEOUT')
print(f'OK={n_ok} FAIL={n_fail} TIMEOUT={n_to}  Total={len(results)}')
