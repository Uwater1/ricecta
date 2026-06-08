#!/usr/bin/env python3
"""
Implementation of the 5 target alpha signals for Chinese commodity futures.
Optimized with Numba.
"""
import os
import re
import numpy as np
import pandas as pd
import numba

# Kalman Filter 1D local level model implementation
@numba.njit(cache=True)
def run_kalman_filter(y, Q=1e-4, R=1e-2):
    n = len(y)
    x_hat = np.zeros(n)
    P = np.zeros(n)
    
    # Find first non-NaN index
    first_valid = -1
    for i in range(n):
        if not np.isnan(y[i]):
            first_valid = i
            break
            
    if first_valid == -1:
        out = np.empty(n)
        out.fill(np.nan)
        return out
        
    x_hat[first_valid] = y[first_valid]
    P[first_valid] = 1.0
    
    for i in range(first_valid):
        x_hat[i] = np.nan
        
    for t in range(first_valid + 1, n):
        # Predict
        x_pred = x_hat[t-1]
        P_pred = P[t-1] + Q
        
        # Update
        if np.isnan(y[t]):
            x_hat[t] = x_pred
            P[t] = P_pred
        else:
            K = P_pred / (P_pred + R)
            x_hat[t] = x_pred + K * (y[t] - x_pred)
            P[t] = (1.0 - K) * P_pred
            
    return x_hat

@numba.njit(cache=True)
def numba_rolling_rank(v, window):
    n = len(v)
    out = np.full(n, np.nan)
    for i in range(window - 1, n):
        val = v[i]
        if np.isnan(val):
            continue
        
        valid_count = 0
        less_count = 0
        equal_count = 0
        for j in range(i - window + 1, i + 1):
            x = v[j]
            if not np.isnan(x):
                valid_count += 1
                if x < val:
                    less_count += 1
                elif x == val:
                    equal_count += 1
                    
        if valid_count >= window:
            rank = 1.0 + less_count + (equal_count - 1) * 0.5
            out[i] = rank / valid_count
    return out

def ts_rank(s, window):
    return pd.Series(numba_rolling_rank(s.values, window), index=s.index)

def compute_alphas(data_dir, spot_dir, symbols, alt_data_dir='/home/hallo/data/ricecta/data_alt', macro_data_dir='/home/hallo/data/ricecta/data/macro_factors'):
    """
    Computes alphas for all symbols.
    Returns a multi-indexed DataFrame with index [date, symbol] and alpha columns.
    """
    # Load daily spot basis data for KalmanFilter_BOS
    spot_dfs = []
    for year in range(2021, 2027):
        path = os.path.join(spot_dir, f"spot_basis_{year}.parquet")
        if os.path.exists(path):
            spot_dfs.append(pd.read_parquet(path))
    
    if spot_dfs:
        df_spot = pd.concat(spot_dfs).sort_values("date").reset_index(drop=True)
        df_spot["date"] = pd.to_datetime(df_spot["date"], format="%Y%m%d")
    else:
        df_spot = pd.DataFrame()

    # Load exchange rates for ForeignAg_LeadLag
    usd_path = os.path.join(alt_data_dir, "USDCNY.parquet")
    myr_path = os.path.join(alt_data_dir, "MYRCNY.parquet")
    if os.path.exists(usd_path) and os.path.exists(myr_path):
        df_usd = pd.read_parquet(usd_path)
        df_myr = pd.read_parquet(myr_path)
        
        myr_cny = 100.0 / df_myr['value']
        usd_cny = df_usd['value']
        
        fx_rates = pd.DataFrame({'USDCNY': usd_cny, 'MYRCNY': myr_cny})
        fx_rates = fx_rates.asfreq('D').ffill()
    else:
        fx_rates = pd.DataFrame()

    # Best-performing macro factor configs per symbol from screening results
    BEST_MACRO_CONFIGS = {
        'AG': {'factor': 'PPI_电气机械及器材制造业(全国:当期同比增长率:月)', 'representation': 'diff', 'sign': -1},
        'AL': {'factor': '制造业采购经理指数PMI_新订单', 'representation': 'zscore', 'sign': -1},
        'AU': {'factor': 'PPI_全部工业品(全国:当期同比增长率:月)', 'representation': 'level', 'sign': -1},
        'C': {'factor': 'PMI_生产经营活动预期_全国_当期值_月', 'representation': 'diff', 'sign': -1},
        'CF': {'factor': 'PMI_生产经营活动预期_全国_当期值_月', 'representation': 'diff', 'sign': -1},
        'CU': {'factor': 'PPI_电气机械及器材制造业(全国:当期同比增长率:月)', 'representation': 'diff', 'sign': -1},
        'I': {'factor': '制造业采购经理指数PMI_进口', 'representation': 'diff', 'sign': 1},
        'J': {'factor': '制造业采购经理指数PMI_原材料库存', 'representation': 'diff', 'sign': 1},
        'JD': {'factor': '居民食品消费价格指数CPI_(上年=100)_当月', 'representation': 'diff', 'sign': -1},
        'M': {'factor': '社会融资规模_当月值', 'representation': 'level', 'sign': 1},
        'MA': {'factor': '非制造业PMI_建筑业_全国_当期值_月', 'representation': 'zscore', 'sign': -1},
        'NI': {'factor': '社会融资规模_当月值', 'representation': 'diff', 'sign': 1},
        'P': {'factor': '制造业采购经理指数PMI_进口', 'representation': 'zscore', 'sign': -1},
        'RB': {'factor': '非制造业PMI_建筑业_新订单_全国_当期值_月', 'representation': 'level', 'sign': 1},
        'RU': {'factor': 'PMI_生产经营活动预期_全国_当期值_月', 'representation': 'level', 'sign': -1},
        'SA': {'factor': '非制造业PMI_建筑业_全国_当期值_月', 'representation': 'diff', 'sign': -1},
        'SC': {'factor': '制造业采购经理指数PMI_进口', 'representation': 'zscore', 'sign': -1},
        'SN': {'factor': '制造业采购经理指数PMI_进口', 'representation': 'level', 'sign': 1},
        'SR': {'factor': 'PPI_食品制造业(全国:当期同比增长率:月)', 'representation': 'zscore', 'sign': -1},
        'TA': {'factor': '制造业采购经理指数PMI_新订单', 'representation': 'zscore', 'sign': -1},
        'TF': {'factor': '制造业采购经理指数PMI_当月', 'representation': 'zscore', 'sign': 1},
        'V': {'factor': '非制造业PMI_建筑业_新订单_全国_当期值_月', 'representation': 'level', 'sign': 1},
        'Y': {'factor': '社会融资规模_当月值', 'representation': 'diff', 'sign': 1}
    }

    all_data = []

    for symbol in symbols:
        price_path = os.path.join(data_dir, f"{symbol}.parquet")
        if not os.path.exists(price_path):
            continue
            
        df = pd.read_parquet(price_path)
        if df.empty:
            continue
            
        # Clean index: should be date
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        # Calculate daily returns
        df["returns"] = df["close"].pct_change()
        
        # 1. HTFC_Alpha19_tsrank_mom_rev
        # TS_Rank(volume,32)* (1-TS_Rank(((close+high) -low),16)))* (1-TS_Rank(returns,32)))
        tr_vol = ts_rank(df["volume"], 32)
        tr_range = ts_rank(df["close"] + df["high"] - df["low"], 16)
        tr_ret = ts_rank(df["returns"], 32)
        df["HTFC_Alpha19_tsrank_mom_rev"] = tr_vol * (1.0 - tr_range) * (1.0 - tr_ret)
        
        # 2. KalmanFilter_BOS
        # Run Kalman Filter on Basis Over Spot
        if not df_spot.empty and symbol in df_spot["symbol"].unique():
            df_sym_spot = df_spot[df_spot["symbol"] == symbol].copy()
            df_sym_spot = df_sym_spot.set_index("date").sort_index()
            # Align basis rate with the price dataframe
            basis_rate = df_sym_spot["dom_basis_rate"].reindex(df.index)
        else:
            # Fallback if no spot data
            basis_rate = pd.Series(0.0, index=df.index)
            
        # Run 1D Kalman filter
        kf_state = run_kalman_filter(basis_rate.values, Q=1e-4, R=1e-2)
        residual = basis_rate - kf_state
        # Normalize residual as Z-score
        df["KalmanFilter_BOS"] = residual / residual.rolling(20).std()
        
        # 3. HTFC_Alpha1_meanclose12
        # mean(close,window=12)/close
        df["HTFC_Alpha1_meanclose12"] = df["close"].rolling(12).mean() / df["close"]
        
        # 4. HTFC_Alpha5_skew20
        # -1*skewness(returns,window=20)
        df["HTFC_Alpha5_skew20"] = -1.0 * df["returns"].rolling(20).skew()
        
        # 5. EWMA_32_64_CTA
        # (EMA(close, 32) - EMA(close, 64)) / close
        ema32 = df["close"].ewm(span=32, adjust=False).mean()
        ema64 = df["close"].ewm(span=64, adjust=False).mean()
        df["EWMA_32_64_CTA"] = (ema32 - ema64) / df["close"]
        
        # 6. ForeignAg_LeadLag
        # Lead-lag difference of N-day changes cubed (to highlight anomalies)
        optimal_n = {'C': 3, 'M': 3, 'Y': 5, 'P': 55, 'CF': 4, 'SR': 50}
        if symbol in optimal_n:
            n_days = optimal_n[symbol]
            alt_path = os.path.join(alt_data_dir, f"{symbol}.parquet")
            if os.path.exists(alt_path) and not fx_rates.empty:
                df_alt = pd.read_parquet(alt_path)
                if not isinstance(df_alt.index, pd.DatetimeIndex):
                    df_alt.index = pd.to_datetime(df_alt.index)
                df_alt = df_alt.sort_index()
                
                # Align exchange rate to foreign calendar
                fx_col = 'MYRCNY' if symbol == 'P' else 'USDCNY'
                fx_aligned = fx_rates[fx_col].reindex(df_alt.index).ffill()
                
                # Convert foreign price to CNY
                close_cny = df_alt["close"] * fx_aligned
                
                # Compute returns on the foreign calendar, then shift by 1 day to prevent lookahead
                foreign_ret = close_cny.pct_change(n_days).shift(1).reindex(df.index).ffill()
                # Compute returns on the domestic calendar
                domestic_ret = df["close"].pct_change(n_days)
                df["ForeignAg_LeadLag"] = ((domestic_ret - foreign_ret) ** 3).astype(np.float32)
            else:
                df["ForeignAg_LeadLag"] = np.nan
        else:
            df["ForeignAg_LeadLag"] = np.nan

        # 7. Alt_Macro_Alpha
        df["Alt_Macro_Alpha"] = np.nan
        if symbol in BEST_MACRO_CONFIGS:
            cfg = BEST_MACRO_CONFIGS[symbol]
            filename = re.sub(r'[\\/*?:"<>|]', '_', cfg['factor']) + ".parquet"
            factor_path = os.path.join(macro_data_dir, filename)
            if os.path.exists(factor_path):
                try:
                    df_fac = pd.read_parquet(factor_path)
                    if not df_fac.empty:
                        if 'info_date' in df_fac.index.names:
                            df_fac = df_fac.reset_index()
                        df_fac['info_date'] = pd.to_datetime(df_fac['info_date'])
                        df_fac = df_fac.set_index('info_date').sort_index()
                        df_fac = df_fac[~df_fac.index.duplicated(keep='last')]
                        
                        all_dates = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
                        if cfg['representation'] == 'level':
                            val_daily = df_fac['value'].reindex(all_dates).ffill()
                            s = val_daily.reindex(df.index)
                        elif cfg['representation'] == 'diff':
                            fac_diff = df_fac['value'].diff()
                            diff_daily = fac_diff.reindex(all_dates).ffill()
                            s = diff_daily.reindex(df.index)
                        elif cfg['representation'] == 'zscore':
                            val_daily = df_fac['value'].reindex(all_dates).ffill()
                            s_level = val_daily.reindex(df.index)
                            s = (s_level - s_level.rolling(252).mean()) / s_level.rolling(252).std()
                        else:
                            s = pd.Series(np.nan, index=df.index)
                        
                        df["Alt_Macro_Alpha"] = (s * cfg['sign']).astype(np.float32)
                except Exception:
                    pass
            
        # Prepare symbol columns
        df["symbol"] = symbol
        df = df.reset_index().rename(columns={"index": "date"})
        
        all_data.append(df[["date", "symbol", "open", "high", "low", "close", "volume", "returns",
                            "HTFC_Alpha19_tsrank_mom_rev", "KalmanFilter_BOS",
                            "HTFC_Alpha1_meanclose12", "HTFC_Alpha5_skew20", "EWMA_32_64_CTA",
                            "ForeignAg_LeadLag", "Alt_Macro_Alpha"]])
        
    if not all_data:
        return pd.DataFrame()
        
    df_merged = pd.concat(all_data).set_index(["date", "symbol"]).sort_index()
    return df_merged

if __name__ == '__main__':
    # Simple self-test
    DATA_DIR = '/home/hallo/data/ricecta/data/dominant_daily'
    SPOT_DIR = '/home/hallo/data/ricecta/data/spot_basis'
    SYMBOLS = ['CU', 'AU', 'CF']
    res = compute_alphas(DATA_DIR, SPOT_DIR, SYMBOLS)
    print("Computed alphas shape:", res.shape)
    print(res.tail(2))
