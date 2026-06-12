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
import json
from contract_splicer import ContractSplicer

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOMINANT_DIR = os.path.join(_SCRIPT_DIR, 'data', 'dominant_contracts')

# Cache for dominant switch dates to avoid re-loading per call

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

# ---------------------------------------------------------------------------
# No-rolling helpers
# ---------------------------------------------------------------------------
_dominant_switch_cache = {}

def get_dominant_switch_dates(symbol):
    """Detect dates where the dominant contract switches for a given symbol.

    Loads the dominant contract mapping from data/dominant_contracts/dominant.parquet
    and returns the first trading day of each new dominant contract period.
    This is data-driven and works for all symbol contract-month patterns
    (monthly metals, quarterly TF, 1/5/9 grains, etc.).
    """
    if symbol in _dominant_switch_cache:
        return _dominant_switch_cache[symbol]

    dominant_path = os.path.join(DOMINANT_DIR, 'dominant.parquet')
    if not os.path.exists(dominant_path):
        raise FileNotFoundError(f"Dominant contracts file not found: {dominant_path}")

    df = pd.read_parquet(dominant_path)

    # Filter for this symbol
    if 'underlying_symbol' in df.columns:
        df_sym = df[df['underlying_symbol'] == symbol].copy()
    else:
        raise ValueError("dominant.parquet missing 'underlying_symbol' column")

    if df_sym.empty:
        _dominant_switch_cache[symbol] = []
        return []

    # Ensure DatetimeIndex
    if not isinstance(df_sym.index, pd.DatetimeIndex):
        if df_sym.index.nlevels > 1:
            df_sym = df_sym.reset_index()
            df_sym = df_sym.set_index(df_sym.columns[0])
        else:
            df_sym.index = pd.to_datetime(df_sym.index)

    df_sym = df_sym.sort_index()

    # Detect switch dates: where dominant_contract changes from previous day
    df_sym['prev_contract'] = df_sym['dominant_contract'].shift(1)
    switches = df_sym[df_sym['dominant_contract'] != df_sym['prev_contract']].dropna(subset=['prev_contract'])
    switch_dates = switches.index.tolist()

    _dominant_switch_cache[symbol] = switch_dates
    return switch_dates

def compute_norolling_signal(daily_index, signal_series, symbol):
    """Discretize a daily alpha signal at dominant contract switch dates.

    The signal is sampled only at switch dates and forward-filled between them,
    producing a no-rolling signal that only updates on contract cycle transitions.
    """
    try:
        switch_dates = get_dominant_switch_dates(symbol)
    except (FileNotFoundError, ValueError):
        return signal_series.copy()

    if not switch_dates:
        return signal_series.copy()

    # Build a series indexed by switch dates, then reindex to daily and ffill
    switch_ts = pd.DatetimeIndex([pd.Timestamp(d) for d in switch_dates])
    # Keep only switch dates that fall within the daily data range
    switch_ts = switch_ts[(switch_ts >= daily_index.min()) & (switch_ts <= daily_index.max())]

    if len(switch_ts) == 0:
        return signal_series.copy()

    # Sample signal at switch dates, reindex to full daily index, and ffill
    sig_at_switches = signal_series.reindex(switch_ts)
    norolling = sig_at_switches.reindex(daily_index).ffill()
    return norolling

# Best-performing hold strategy parameters per symbol (H, k)
# from hold_strategy_report.md optimization results
BEST_HOLD_PARAMS = {
    'C': (25, 1), 'M': (40, 3), 'Y': (15, 1), 'P': (35, 2),
    'V': (5, 1), 'J': (20, 2), 'JD': (30, 2), 'I': (5, 3),
    'CU': (20, 3), 'AL': (15, 3), 'AU': (10, 1), 'AG': (25, 3),
    'RB': (20, 1), 'RU': (15, 3), 'NI': (5, 2), 'SN': (35, 2),
    'SC': (20, 3), 'CF': (30, 1), 'SR': (25, 1), 'TA': (40, 3),
    'MA': (20, 1), 'SA': (30, 2), 'TF': (40, 3)
}

def compute_alphas(data_dir, spot_dir, symbols, alt_data_dir=None, macro_data_dir=None):
    """
    Computes alphas for all symbols.
    Returns a multi-indexed DataFrame with index [date, symbol] and alpha columns.
    """
    if alt_data_dir is None:
        alt_data_dir = os.path.join(_SCRIPT_DIR, 'data_alt')
    if macro_data_dir is None:
        macro_data_dir = os.path.join(_SCRIPT_DIR, 'data', 'macro_factors')
    # Load daily spot basis data for KalmanFilter_BOS
    spot_dfs = []
    for year in range(2016, 2027):
        path = os.path.join(spot_dir, f"spot_basis_{year}.parquet")
        if os.path.exists(path):
            spot_dfs.append(pd.read_parquet(path))
    
    if spot_dfs:
        df_spot = pd.concat(spot_dfs).sort_values("date").reset_index(drop=True)
        df_spot["date"] = pd.to_datetime(df_spot["date"], format="%Y%m%d")
        spot_by_symbol = {sym: grp.set_index("date").sort_index() for sym, grp in df_spot.groupby("symbol")}
    else:
        df_spot = pd.DataFrame()
        spot_by_symbol = {}

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

    # Best-performing macro factor configs per symbol from screening results (look-ahead free, 1d-shifted, release-date-only aligned)
    # Sign convention: +1 if spearman_corr > 0, -1 if spearman_corr < 0 (aligns with correlation direction)
    BEST_MACRO_CONFIGS = {
        'SA': {'factor': 'PPI_电气机械及器材制造业(全国:当期同比增长率:月)', 'representation': 'diff', 'sign': 1},   # Spearman=+0.4666
        'JD': {'factor': '制造业采购经理指数PMI_购进价格', 'representation': 'diff', 'sign': 1},                   # Spearman=+0.3116
        'RB': {'factor': '非制造业PMI_建筑业_新订单_全国_当期值_月', 'representation': 'level', 'sign': 1},        # Spearman=+0.2822
        'TF': {'factor': '社会融资规模_当月值', 'representation': 'diff', 'sign': -1},                             # Spearman=-0.5632
        'AG': {'factor': 'PPI_全部工业品(全国:当期同比增长率:月)', 'representation': 'level', 'sign': -1},         # Spearman=-0.2941
        'Y': {'factor': '社会融资规模_当月值', 'representation': 'zscore', 'sign': 1},                            # Spearman=+0.6735
        'RU': {'factor': 'PMI_生产经营活动预期_全国_当期值_月', 'representation': 'level', 'sign': -1},            # Spearman=-0.2366
        'P': {'factor': 'PPI_全部工业品(全国:当期同比增长率:月)', 'representation': 'level', 'sign': 1},          # Spearman=+0.2437
        'NI': {'factor': '制造业采购经理指数PMI_新订单', 'representation': 'diff', 'sign': 1},                     # Spearman=+0.2366
        'CU': {'factor': 'PPI_全部工业品(全国:当期同比增长率:月)', 'representation': 'level', 'sign': -1},         # Spearman=-0.1716
        'V': {'factor': '非制造业PMI_建筑业_业务活动预期_全国_当期值_月', 'representation': 'level', 'sign': 1},  # Spearman=+0.2645
        'AU': {'factor': '制造业采购经理指数PMI_购进价格', 'representation': 'level', 'sign': -1},                 # Spearman=-0.2398
        'C': {'factor': '居民鲜果消费价格指数CPI_(上年=100)_当月', 'representation': 'zscore', 'sign': -1},       # Spearman=-0.2648
        'SR': {'factor': '制造业采购经理指数PMI_购进价格', 'representation': 'diff', 'sign': 1},                   # Spearman=+0.2070
        'CF': {'factor': 'PPI_皮革、毛皮、羽毛及其制品和制鞋业(全国:当期同比增长率:月)', 'representation': 'diff', 'sign': -1},  # Spearman=-0.2461
        'I': {'factor': 'GDP增长贡献率_第二产业_累计同比_季', 'representation': 'zscore', 'sign': -1},            # Spearman=-0.4431
        'MA': {'factor': '制造业采购经理指数PMI_原材料库存', 'representation': 'diff', 'sign': 1},                 # Spearman=+0.2002
        'AL': {'factor': 'PPIRM_燃料及动力类(全国:当期同比增长率:月)', 'representation': 'level', 'sign': -1},     # Spearman=-0.2638
        'SN': {'factor': 'PPI_通信设备、计算机及其他电子设备制造业工业品出厂价格指数PPI_(上年=100)_当月', 'representation': 'diff', 'sign': 1},  # Spearman=+0.2670
        'M': {'factor': '社会融资规模_当月值', 'representation': 'zscore', 'sign': 1},                            # Spearman=+0.2882
        'J': {'factor': '社会融资规模_当月值', 'representation': 'zscore', 'sign': 1},                            # Spearman=+0.5265
        'TA': {'factor': 'PMI_生产经营活动预期_全国_当期值_月', 'representation': 'diff', 'sign': -1},             # Spearman=-0.1242
        'SC': {'factor': '国内生产总值GDP_累计同比', 'representation': 'level', 'sign': 1},                        # Spearman=+0.1158
    }

    # Hot-load from JSON if exists
    config_json_path = os.path.join(_SCRIPT_DIR, 'data', 'results', 'best_macro_configs.json')
    if os.path.exists(config_json_path):
        try:
            with open(config_json_path, 'r', encoding='utf-8') as f:
                loaded_configs = json.load(f)
                for sym, cfg in loaded_configs.items():
                    BEST_MACRO_CONFIGS[sym] = cfg
        except Exception as e:
            print(f"Warning: could not load best_macro_configs.json: {e}")

    all_data = []

    for symbol in symbols:
        # Load k-th nearest liquid contract price using ContractSplicer
        k = BEST_HOLD_PARAMS.get(symbol, (20, 1))[1]
        try:
            splicer = ContractSplicer(symbol, k=k)
            df = splicer.build()
        except Exception as e:
            print(f"Warning: could not splice contract prices for {symbol}: {e}")
            continue
            
        if df.empty:
            continue
            
        # Clean index: should be date
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(np.float32)
        # Calculate daily returns
        df["returns"] = df["close"].pct_change()
        # Replace inf/nan and clip to daily price limits [-10%, +10%] to prevent metric distortion from zero adjusted prices
        df["returns"] = df["returns"].replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-0.1, 0.1).astype(np.float32)
        
        # 1. HTFC_Alpha19_tsrank_mom_rev
        # TS_Rank(volume,32)* (1-TS_Rank(((close+high) -low),16)))* (1-TS_Rank(returns,32)))
        tr_vol = ts_rank(df["volume"], 32)
        tr_range = ts_rank(df["close"] + df["high"] - df["low"], 16)
        tr_ret = ts_rank(df["returns"], 32)
        df["HTFC_Alpha19_tsrank_mom_rev"] = (tr_vol * (1.0 - tr_range) * (1.0 - tr_ret)).astype(np.float32)
        
        # 2. KalmanFilter_BOS
        # Run Kalman Filter on Basis Over Spot
        if symbol in spot_by_symbol:
            df_sym_spot = spot_by_symbol[symbol]
            basis_rate = df_sym_spot["dom_basis_rate"].astype(np.float32).reindex(df.index)
        else:
            # Fallback if no spot data
            basis_rate = pd.Series(0.0, index=df.index)
            
        # Run 1D Kalman filter
        kf_state = run_kalman_filter(basis_rate.values.astype(np.float64), Q=1e-4, R=1e-2)
        residual = (basis_rate - kf_state).astype(np.float32)
        # Normalize residual as Z-score
        df["KalmanFilter_BOS"] = (residual / residual.rolling(20).std()).astype(np.float32)
        
        # 3. HTFC_Alpha1_meanclose12
        # mean(close,window=12)/close
        df["HTFC_Alpha1_meanclose12"] = (df["close"].rolling(12).mean() / df["close"]).astype(np.float32)
        
        # 4. HTFC_Alpha5_skew20
        # -1*skewness(returns,window=20)
        df["HTFC_Alpha5_skew20"] = (-1.0 * df["returns"].rolling(20).skew()).astype(np.float32)
        
        # 5. EWMA_32_64_CTA
        # (EMA(close, 32) - EMA(close, 64)) / close
        ema32 = df["close"].ewm(span=32, adjust=False).mean()
        ema64 = df["close"].ewm(span=64, adjust=False).mean()
        df["EWMA_32_64_CTA"] = ((ema32 - ema64) / df["close"]).astype(np.float32)
        
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
                        # NaN guard: check for at least 12 non-NaN observations
                        non_nan_count = df_fac['value'].notna().sum()
                        if non_nan_count >= 12:
                            if 'info_date' in df_fac.index.names:
                                df_fac = df_fac.reset_index()
                            df_fac['info_date'] = pd.to_datetime(df_fac['info_date'])
                            df_fac = df_fac.set_index('info_date').sort_index()
                            df_fac = df_fac[~df_fac.index.duplicated(keep='last')]
                            
                            all_dates = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
                            if cfg['representation'] == 'level':
                                val_daily = df_fac['value'].reindex(all_dates).ffill().shift(1)
                                s = val_daily.reindex(df.index)
                            elif cfg['representation'] == 'diff':
                                fac_diff = df_fac['value'].diff()
                                diff_daily = fac_diff.reindex(all_dates).ffill().shift(1)
                                s = diff_daily.reindex(df.index)
                            elif cfg['representation'] == 'zscore':
                                val_daily = df_fac['value'].reindex(all_dates).ffill().shift(1)
                                s_level = val_daily.reindex(df.index)
                                s = (s_level - s_level.rolling(252).mean()) / s_level.rolling(252).std()
                            else:
                                s = pd.Series(np.nan, index=df.index)
                            
                            raw_signal = s * cfg['sign']
                            # Winsorize at [1%, 99%] using rolling 252-day window (look-ahead free)
                            q_low = raw_signal.rolling(252, min_periods=12).quantile(0.01)
                            q_high = raw_signal.rolling(252, min_periods=12).quantile(0.99)
                            winsorized = raw_signal.clip(lower=q_low, upper=q_high)
                            
                            df["Alt_Macro_Alpha"] = winsorized.astype(np.float32)
                except Exception:
                    pass

        # 8. Alt_Macro_Alpha_NoRoll (discretized at contract switch dates)
        df["Alt_Macro_Alpha_NoRoll"] = compute_norolling_signal(
            df.index, df["Alt_Macro_Alpha"], symbol
        )
        
        # Prepare symbol columns
        df["symbol"] = symbol
        df = df.reset_index().rename(columns={"index": "date"})
        
        all_data.append(df[["date", "symbol", "open", "high", "low", "close", "volume", "returns",
                            "HTFC_Alpha19_tsrank_mom_rev", "KalmanFilter_BOS",
                            "HTFC_Alpha1_meanclose12", "HTFC_Alpha5_skew20", "EWMA_32_64_CTA",
                            "ForeignAg_LeadLag", "Alt_Macro_Alpha", "Alt_Macro_Alpha_NoRoll"]])
        
    if not all_data:
        return pd.DataFrame()
        
    df_merged = pd.concat(all_data).set_index(["date", "symbol"]).sort_index()
    return df_merged

if __name__ == '__main__':
    # Simple self-test
    DATA_DIR = os.path.join(_SCRIPT_DIR, 'data', 'dominant_daily')
    SPOT_DIR = os.path.join(_SCRIPT_DIR, 'data', 'spot_basis')
    SYMBOLS = ['CU', 'AU', 'CF']
    res = compute_alphas(DATA_DIR, SPOT_DIR, SYMBOLS)
    print("Computed alphas shape:", res.shape)
    print("Columns:", res.columns.tolist())
    print("Alt_Macro_Alpha_NoRoll non-NaN count:", res['Alt_Macro_Alpha_NoRoll'].notna().sum())
    print(res[['Alt_Macro_Alpha', 'Alt_Macro_Alpha_NoRoll']].tail(5))
