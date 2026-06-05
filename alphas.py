#!/usr/bin/env python3
"""
Implementation of the 5 target alpha signals for Chinese commodity futures.
"""
import os
import numpy as np
import pandas as pd

# Kalman Filter 1D local level model implementation
def run_kalman_filter(y, Q=1e-4, R=1e-2):
    n = len(y)
    x_hat = np.zeros(n)
    P = np.zeros(n)
    
    # Find first non-NaN index
    valid_indices = np.where(~np.isnan(y))[0]
    if len(valid_indices) == 0:
        return np.full(n, np.nan)
    first_valid = valid_indices[0]
    
    x_hat[first_valid] = y[first_valid]
    P[first_valid] = 1.0
    
    x_hat[:first_valid] = np.nan
    
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

def ts_rank(s, window):
    return s.rolling(window).rank(pct=True)

def compute_alphas(data_dir, spot_dir, symbols):
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
        
        # Prepare symbol columns
        df["symbol"] = symbol
        df = df.reset_index().rename(columns={"index": "date"})
        
        all_data.append(df[["date", "symbol", "open", "high", "low", "close", "volume", "returns",
                            "HTFC_Alpha19_tsrank_mom_rev", "KalmanFilter_BOS",
                            "HTFC_Alpha1_meanclose12", "HTFC_Alpha5_skew20", "EWMA_32_64_CTA"]])
        
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
