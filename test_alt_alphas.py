#!/usr/bin/env python3
"""
Initial screening pipeline: matches commodities with their candidate factors,
aligns them to avoid look-ahead bias, computes Pearson/Spearman stats
across mixed horizons (5d to 25d calendar + H1-H3 contract-switch), and outputs the results.

Horizons:
  5d-25d = fixed 5-25 trading-day forward returns (calendar horizon sweep)
  H1     = forward return to the 1st next dominant contract switch date
  H2     = forward return to the 2nd next dominant contract switch date
  H3     = forward return to the 3rd next dominant contract switch date
"""
import os
import re
import pandas as pd
import numpy as np
import numba
import scipy.stats as stats
import warnings

from evaluate_hold_strategy import get_dominant_switch_dates

warnings.filterwarnings('ignore')

FACTOR_DISPLAY_NAMES = {
    'PPI_全部工业品(全国:当期同比增长率:月)': 'PPI All Industry (YoY)',
    'PPIRM_燃料及动力类(全国:当期同比增长率:月)': 'PPIRM Fuel & Power (YoY)',
    '制造业采购经理指数PMI_购进价格': 'PMI Input Price',
    '制造业采购经理指数PMI_当月': 'Manufacturing PMI',
    '制造业采购经理指数PMI_原材料库存': 'PMI Raw Material Inventory',
    '制造业采购经理指数PMI_新订单': 'PMI New Orders',
    '非制造业PMI_建筑业_新订单_全国_当期值_月': 'Non-Mfg PMI Constr. New Orders',
    'PMI_生产经营活动预期_全国_当期值_月': 'PMI Business Expectation',
    '非制造业PMI_建筑业_业务活动预期_全国_当期值_月': 'Non-Mfg PMI Constr. Expectation',
    'PPI_皮革、毛皮、羽毛及其制品和制鞋业(全国:当期同比增长率:月)': 'PPI Leather & Footwear (YoY)',
    'PPI_通信设备、计算机及其他电子设备制造业工业品出厂价格指数PPI_(上年=100)_当月': 'PPI Telecom & Electronics (YoY)',
    'PPI_电气机械及器材制造业(全国:当期同比增长率:月)': 'PPI Electrical Machinery (YoY)',
    'GDP增长贡献率_第二产业_累计同比_季': 'GDP Contribution 2nd Industry (Cum YoY)',
    '社会融资规模_当月值': 'Social Financing (Monthly)',
    '社会融资规模存量_同比增速_月末数': 'Social Financing Stock (YoY)',
    '国内生产总值GDP_累计同比': 'GDP Cumulative YoY',
}

def get_display_name(factor):
    if factor in FACTOR_DISPLAY_NAMES:
        return FACTOR_DISPLAY_NAMES[factor]
    return factor

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_DIR = os.path.join(_SCRIPT_DIR, 'data')
DAILY_DIR = os.path.join(BASE_DIR, 'dominant_daily')
MACRO_DIR = os.path.join(BASE_DIR, 'macro_factors')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
FIGURES_DIR = os.path.join(_SCRIPT_DIR, 'figures')

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

SYMBOLS = [
    'C', 'M', 'Y', 'P', 'V', 'J', 'JD', 'I',  # DCE
    'CU', 'AL', 'AU', 'AG', 'RB', 'RU', 'NI', 'SN', # SHFE
    'SC', # INE
    'CF', 'SR', 'TA', 'MA', 'SA', # CZCE
    'TF' # CFFEX
]

SWITCH_HORIZONS = ['H1', 'H2', 'H3']  # contract-switch-based only
CALENDAR_HORIZONS = [f'{h}d' for h in range(5, 26)]
HORIZONS = CALENDAR_HORIZONS + SWITCH_HORIZONS

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
                symbol_to_factors[current_symbol].append(m_fac.group(1).strip())
    return symbol_to_factors

def calculate_t_stat(r, n):
    if n <= 2 or abs(r) >= 1.0:
        return 0.0
    return r * np.sqrt((n - 2) / (1 - r**2))

@numba.njit(cache=True)
def _numba_newey_west_t(x, y, lags):
    n = x.shape[0]
    if n <= 3:
        return 0.0

    sum_x = 0.0
    sum_y = 0.0
    for i in range(n):
        sum_x += x[i]
        sum_y += y[i]
    mean_x = sum_x / n
    mean_y = sum_y / n

    s_xx = 0.0
    s_xy = 0.0
    for i in range(n):
        dx = x[i] - mean_x
        dy = y[i] - mean_y
        s_xx += dx * dx
        s_xy += dx * dy

    if s_xx < 1e-30:
        return 0.0

    beta1 = s_xy / s_xx
    beta0 = mean_y - beta1 * mean_x

    residuals = np.empty(n)
    for i in range(n):
        residuals[i] = y[i] - (beta0 + beta1 * x[i])

    inv_sxx = 1.0 / s_xx
    omega_11 = 0.0
    omega_12 = 0.0
    omega_22 = 0.0

    for t in range(n):
        xt1 = 1.0
        xt2 = x[t] - mean_x
        et = residuals[t]
        e2 = et * et
        omega_11 += e2 * xt1 * xt1
        omega_12 += e2 * xt1 * xt2
        omega_22 += e2 * xt2 * xt2

    for j in range(1, lags + 1):
        w = 1.0 - j / (lags + 1.0)
        for t in range(j, n):
            xt1 = 1.0
            xt2 = x[t] - mean_x
            xtj1 = 1.0
            xtj2 = x[t - j] - mean_x
            et = residuals[t]
            etj = residuals[t - j]
            eetj = et * etj

            c11 = xt1 * xtj1 + xtj1 * xt1
            c12 = xt1 * xtj2 + xtj1 * xt2
            c22 = xt2 * xtj2 + xtj2 * xt2

            omega_11 += w * eetj * c11
            omega_12 += w * eetj * c12
            omega_22 += w * eetj * c22

    var_b1 = inv_sxx * inv_sxx * omega_22
    std_b1 = np.sqrt(max(var_b1, 1e-12))
    if std_b1 < 1e-30:
        return 0.0
    return beta1 / std_b1


def fast_newey_west_t(x, y, lags):
    x = np.ascontiguousarray(x, dtype=np.float64)
    y = np.ascontiguousarray(y, dtype=np.float64)
    return _numba_newey_west_t(x, y, lags)

def compute_newey_west_spearman(sig, fwd, H, n_obs_min=15):
    """
    Computes Spearman rank correlation and its Newey-West adjusted t-statistic and p-value.
    sig, fwd are pandas Series with the same index and no NaNs.
    """
    n_obs = len(sig)
    if n_obs < n_obs_min:
        return np.nan, np.nan, np.nan
        
    # Rank transform the variables (Spearman is Pearson on ranks)
    sig_ranked = stats.rankdata(sig)
    fwd_ranked = stats.rankdata(fwd)
    
    # Standardize
    sig_ranked_std = (sig_ranked - np.mean(sig_ranked)) / (np.std(sig_ranked) + 1e-8)
    fwd_ranked_std = (fwd_ranked - np.mean(fwd_ranked)) / (np.std(fwd_ranked) + 1e-8)
    
    # monthly spacing is ~20 trading days. Overlap lag = max(0, ceil(H / 20) - 1)
    lags = max(0, int(np.ceil(H / 20.0)) - 1)
    
    r_spear, _ = stats.spearmanr(sig, fwd)
    
    try:
        t_stat = fast_newey_west_t(sig_ranked_std, fwd_ranked_std, lags)
        # Convert t_stat to p-val (two-tailed) using normal distribution (NW asymptotic normality)
        p_val = 2.0 * (1.0 - stats.norm.cdf(abs(t_stat)))
    except Exception:
        # Fallback to standard t-statistic
        t_stat = calculate_t_stat(r_spear, n_obs)
        p_val = 2.0 * (1.0 - stats.t.cdf(abs(t_stat), n_obs - 2))
        
    return r_spear, t_stat, p_val

def compute_switch_forward_returns(df_price, switch_dates):
    """Compute forward returns to the next 1st-3rd dominant contract switch dates.

    Also adds fixed calendar forward returns for horizons 5d to 25d.
    Returns a DataFrame with columns fwd_ret_5d..fwd_ret_25d, fwd_ret_H1..H3
    and days_H1..H3, aligned to df_price's index.
    """
    trading_dates = df_price.index
    close = df_price['close'].values.astype(np.float64)
    n = len(trading_dates)
    td_ts = trading_dates.values

    # Convert switch dates to numpy datetime64 for fast searchsorted
    sd_ts = np.sort(np.array(switch_dates, dtype='datetime64[ns]'))

    # For each trading date, find index of the first switch date >= that trading date
    # side='left' gives the first position where sd_ts[pos] >= td_ts[i]
    first_switch_pos = np.searchsorted(sd_ts, td_ts, side='left')

    result = pd.DataFrame(index=trading_dates)

    # Fixed calendar-day forward returns for horizons 5d to 25d
    close_series = df_price['close']
    for h in range(5, 26):
        fwd_ret = close_series.pct_change(h).shift(-h).replace([np.inf, -np.inf], np.nan)
        result[f'fwd_ret_{h}d'] = fwd_ret.values

    for i, label in enumerate(SWITCH_HORIZONS, start=1):
        # The target switch is the i-th switch from now (0-indexed: first_switch_pos + i - 1)
        target_pos = first_switch_pos + (i - 1)
        # Mask: target_pos must be within the switch dates array
        valid = (target_pos < len(sd_ts))

        # For valid positions, map from switch array to trading date positions
        target_td_pos = np.full(n, n, dtype=np.int64)  # default to out-of-bounds
        valid_sd = sd_ts[target_pos[valid]]
        target_td_pos[valid] = np.searchsorted(td_ts, valid_sd, side='left')

        # Valid mask: target trading date position within bounds
        valid &= (target_td_pos < n)
        valid &= (target_td_pos >= 0)

        days_to_switch = np.full(n, -1, dtype=np.int32)
        days_to_switch[valid] = target_td_pos[valid] - np.arange(n)[valid]
        # Only keep positive forward windows
        valid &= (days_to_switch > 0)

        fwd_ret = np.full(n, np.nan)
        fwd_ret[valid] = close[target_td_pos[valid]] / close[np.arange(n)[valid]] - 1.0
        fwd_ret[~np.isfinite(fwd_ret)] = np.nan  # Replace inf and -inf with nan

        result[f'fwd_ret_{label}'] = fwd_ret
        result[f'days_{label}'] = days_to_switch

    return result

def plot_horizon_stability(df_results, best_factors_dict, figures_dir):
    """
    Generates a 5x5 grid of subplots for the 23 symbols.
    For each symbol, we plot the Spearman correlation (y-axis) vs Horizon (x-axis) for its best factor.
    Three lines are plotted: Full Sample, First Half, Second Half.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(5, 5, figsize=(22, 18))
    axes = axes.flatten()
    
    for i, symbol in enumerate(SYMBOLS):
        ax = axes[i]
        if symbol not in best_factors_dict:
            ax.text(0.5, 0.5, f"No factor for {symbol}", ha='center', va='center')
            continue
            
        best_cfg = best_factors_dict[symbol]
        factor = best_cfg['factor']
        rep = best_cfg['representation']
        
        # Filter df_results for this symbol, factor, representation, and calendar horizons
        df_sub = df_results[
            (df_results['symbol'] == symbol) & 
            (df_results['factor'] == factor) & 
            (df_results['representation'] == rep) & 
            (df_results['horizon'].str.endswith('d'))
        ].copy()
        
        # Parse horizon column to numeric for plotting (remove 'd')
        df_sub['h_num'] = df_sub['horizon'].str.replace('d', '').astype(int)
        df_sub = df_sub.sort_values('h_num')
        
        if df_sub.empty:
            ax.text(0.5, 0.5, "No data", ha='center', va='center')
            continue
            
        ax.plot(df_sub['h_num'], df_sub['spearman_corr'], label='Full', color='#1f77b4', linewidth=2.5)
        ax.plot(df_sub['h_num'], df_sub['spearman_first_half'], label='1st Half', color='#2ca02c', linestyle='--', linewidth=1.5, alpha=0.9)
        ax.plot(df_sub['h_num'], df_sub['spearman_second_half'], label='2nd Half', color='#ff7f0e', linestyle='--', linewidth=1.5, alpha=0.9)
        
        ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
        
        # Title of subplot: Symbol + Factor name + representation
        # Truncate factor name to fit
        short_factor = get_display_name(factor)
        if len(short_factor) > 25:
            short_factor = short_factor[:12] + '...' + short_factor[-10:]
            
        ax.set_title(f"{symbol}: {short_factor}\n({rep}, SCF={best_cfg['horizon_sign_consistency_pct']*100:.0f}%)", fontsize=9, fontweight='bold')
        # Dynamic y-axis based on actual correlation range for this symbol
        max_abs_corr = df_sub[['spearman_corr', 'spearman_first_half', 'spearman_second_half']].abs().max().max()
        ylim = max(0.8, np.ceil((max_abs_corr + 0.15) * 10) / 10)
        ax.set_ylim(-ylim, ylim)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.tick_params(axis='both', which='major', labelsize=8)
        
        if i == 0:
            ax.legend(fontsize=8, loc='upper left')
            
    # Hide empty subplots
    for j in range(len(SYMBOLS), len(axes)):
        fig.delaxes(axes[j])
        
    fig.suptitle("Alternative Macro Factor Correlation Stability across Horizons (5d to 25d)\n(Full Sample vs Split-Half for Temporal Stability Check)", fontsize=16, fontweight='bold', y=0.98)
    
    # Common labels
    fig.text(0.5, 0.02, 'Horizon (Calendar Days)', ha='center', va='center', fontsize=12, fontweight='bold')
    fig.text(0.02, 0.5, 'Spearman Correlation Coefficient', ha='center', va='center', rotation='vertical', fontsize=12, fontweight='bold')
    
    plt.tight_layout(rect=[0.03, 0.03, 0.97, 0.95])
    
    plot_path = os.path.join(figures_dir, 'horizon_stability.png')
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"Saved horizon stability grid plot to: {plot_path}")

def run_correlation_test():
    md_path = os.path.join(_SCRIPT_DIR, 'potential_alt_alphas.md')
    symbol_to_factors = parse_markdown(md_path)
    
    rows = []
    horizon_days_stats = {}  # {symbol: {H1: median_days, H2: ..., ...}}
    
    for symbol in SYMBOLS:
        price_path = os.path.join(DAILY_DIR, f"{symbol}.parquet")
        if not os.path.exists(price_path):
            continue
            
        df_price = pd.read_parquet(price_path)
        if df_price.empty:
            continue
            
        if not isinstance(df_price.index, pd.DatetimeIndex):
            df_price.index = pd.to_datetime(df_price.index)
        df_price = df_price.sort_index()
        
        # Load dominant contract switch dates (data-driven, per-symbol)
        try:
            switch_dates = get_dominant_switch_dates(symbol)
        except Exception as e:
            print(f"  Warning: could not load switch dates for {symbol}: {e}")
            continue
        
        if len(switch_dates) < 3:
            print(f"  Warning: {symbol} has fewer than 3 switch dates, skipping")
            continue
        
        # Compute forward returns
        fwd_df = compute_switch_forward_returns(df_price, switch_dates)
        df_price = pd.concat([df_price, fwd_df], axis=1)
        
        # Record median calendar days per horizon for this symbol
        sym_days = {}
        for label in SWITCH_HORIZONS:
            d = fwd_df[f'days_{label}']
            valid_days = d[d > 0]
            sym_days[label] = int(valid_days.median()) if len(valid_days) > 0 else -1
        # Also record for 5d and 20d
        sym_days['5d'] = 5
        sym_days['20d'] = 20
        horizon_days_stats[symbol] = sym_days
        
        trading_dates = df_price.index
        all_dates = pd.date_range(start=trading_dates.min(), end=trading_dates.max(), freq='D')
        
        candidate_factors = symbol_to_factors.get(symbol, [])
        for raw_factor in candidate_factors:
            filename = re.sub(r'[\\/*?:"<>|]', '_', raw_factor) + ".parquet"
            factor_path = os.path.join(MACRO_DIR, filename)
            if not os.path.exists(factor_path):
                continue
                
            df_fac = pd.read_parquet(factor_path)
            if df_fac.empty:
                continue
                
            # Clean and index by info_date
            if 'info_date' in df_fac.index.names:
                df_fac = df_fac.reset_index()
            
            df_fac['info_date'] = pd.to_datetime(df_fac['info_date'])
            df_fac = df_fac.set_index('info_date').sort_index()
            df_fac = df_fac[~df_fac.index.duplicated(keep='last')]
            
            # 1. Level signal representation (shifted by 1 day to prevent look-ahead bias)
            val_daily = df_fac['value'].reindex(all_dates).ffill().shift(1)
            s_level = val_daily.reindex(trading_dates)
            
            # 2. Diff signal representation (change at release, ffilled, shifted 1 day)
            fac_diff = df_fac['value'].diff()
            diff_daily = fac_diff.reindex(all_dates).ffill().shift(1)
            s_diff = diff_daily.reindex(trading_dates)
            
            # 3. Z-score signal representation (rolling 252-day Z-score of level)
            s_zscore = (s_level - s_level.rolling(252).mean()) / s_level.rolling(252).std()
            
            signals = {
                'level': s_level,
                'diff': s_diff,
                'zscore': s_zscore
            }
            
            # Calculate release trading dates (first trading day strictly after each release date)
            pos = np.searchsorted(trading_dates, df_fac.index, side='right')
            valid_pos = pos[pos < len(trading_dates)]
            release_trading_dates = trading_dates[valid_pos].unique()
            
            # Compute correlations for each signal representation
            for sig_name, sig_series in signals.items():
                horizon_stats = {}
                
                # Check calendar horizons sweep (5d to 25d)
                for h in range(5, 26):
                    horizon = f"{h}d"
                    fwd_col = f"fwd_ret_{horizon}"
                    
                    df_corr = pd.DataFrame({'sig': sig_series, 'fwd': df_price[fwd_col]}).reindex(release_trading_dates).dropna()
                    df_corr = df_corr[np.isfinite(df_corr['sig']) & np.isfinite(df_corr['fwd'])]
                    n_obs = len(df_corr)
                    
                    if n_obs < 15:
                        continue
                        
                    # Pearson
                    r_pears, p_pears = stats.pearsonr(df_corr['sig'], df_corr['fwd'])
                    t_pears = calculate_t_stat(r_pears, n_obs)
                    
                    # Spearman with Newey-West adjusted t-statistic
                    r_spear, t_spear_nw, p_spear_nw = compute_newey_west_spearman(df_corr['sig'], df_corr['fwd'], h)
                    
                    # Sub-period split for temporal stability
                    mid_idx = n_obs // 2
                    df_first = df_corr.iloc[:mid_idx]
                    df_second = df_corr.iloc[mid_idx:]
                    
                    r_first, _, _ = compute_newey_west_spearman(df_first['sig'], df_first['fwd'], h, n_obs_min=5)
                    r_second, _, _ = compute_newey_west_spearman(df_second['sig'], df_second['fwd'], h, n_obs_min=5)
                    
                    temporal_consistent = False
                    if not np.isnan(r_first) and not np.isnan(r_second):
                        temporal_consistent = (np.sign(r_first) == np.sign(r_second)) and (r_first != 0.0) and (r_second != 0.0)
                        
                    horizon_stats[horizon] = {
                        'n_obs': n_obs,
                        'pearson_corr': r_pears,
                        'pearson_t': t_pears,
                        'pearson_p': p_pears,
                        'spearman_corr': r_spear,
                        'spearman_t': t_spear_nw,
                        'spearman_p': p_spear_nw,
                        'spearman_first_half': r_first,
                        'spearman_second_half': r_second,
                        'temporal_consistent': temporal_consistent
                    }
                
                # Check contract-switch horizons H1, H2, H3
                for horizon in SWITCH_HORIZONS:
                    fwd_col = f"fwd_ret_{horizon}"
                    
                    df_corr = pd.DataFrame({'sig': sig_series, 'fwd': df_price[fwd_col]}).reindex(release_trading_dates).dropna()
                    df_corr = df_corr[np.isfinite(df_corr['sig']) & np.isfinite(df_corr['fwd'])]
                    n_obs = len(df_corr)
                    
                    if n_obs < 15:
                        continue
                        
                    r_pears, p_pears = stats.pearsonr(df_corr['sig'], df_corr['fwd'])
                    t_pears = calculate_t_stat(r_pears, n_obs)
                    
                    # Use NW-adjusted Spearman for switch horizons (consistent with calendar horizons)
                    switch_H_days = horizon_days_stats[symbol].get(horizon, 20)
                    r_spear, t_spear, p_spear = compute_newey_west_spearman(df_corr['sig'], df_corr['fwd'], switch_H_days)
                    
                    mid_idx = n_obs // 2
                    df_first = df_corr.iloc[:mid_idx]
                    df_second = df_corr.iloc[mid_idx:]
                    
                    r_first, _, _ = compute_newey_west_spearman(df_first['sig'], df_first['fwd'], switch_H_days, n_obs_min=5)
                    r_second, _, _ = compute_newey_west_spearman(df_second['sig'], df_second['fwd'], switch_H_days, n_obs_min=5)
                    
                    temporal_consistent = False
                    if not np.isnan(r_first) and not np.isnan(r_second):
                        temporal_consistent = (np.sign(r_first) == np.sign(r_second)) and (r_first != 0.0) and (r_second != 0.0)
                        
                    horizon_stats[horizon] = {
                        'n_obs': n_obs,
                        'pearson_corr': r_pears,
                        'pearson_t': t_pears,
                        'pearson_p': p_pears,
                        'spearman_corr': r_spear,
                        'spearman_t': t_spear,
                        'spearman_p': p_spear,
                        'spearman_first_half': r_first,
                        'spearman_second_half': r_second,
                        'temporal_consistent': temporal_consistent
                    }

                # Calculate Sweep Stability metrics across 5d-25d
                r_20d = horizon_stats.get('20d', {}).get('spearman_corr', np.nan)
                
                same_sign_count = 0
                total_sweep_count = 0
                nw_t_stats = []
                diffs = []
                prev_r = None
                
                for h in range(5, 26):
                    h_label = f"{h}d"
                    if h_label in horizon_stats:
                        r_h = horizon_stats[h_label]['spearman_corr']
                        t_h = horizon_stats[h_label]['spearman_t']
                        if not np.isnan(r_h) and not np.isnan(r_20d):
                            total_sweep_count += 1
                            if np.sign(r_h) == np.sign(r_20d) and r_h != 0.0:
                                same_sign_count += 1
                        if not np.isnan(t_h):
                            nw_t_stats.append(abs(t_h))
                        if prev_r is not None and not np.isnan(r_h):
                            diffs.append(r_h - prev_r)
                        prev_r = r_h
                
                horizon_sign_consistency_pct = (same_sign_count / total_sweep_count) if total_sweep_count > 0 else 0.0
                mean_nw_t_stat = np.mean(nw_t_stats) if len(nw_t_stats) > 0 else 0.0
                smoothness_index = np.std(diffs) if len(diffs) > 0 else 0.0
                
                horizon_consistent_sweep = (horizon_sign_consistency_pct >= 0.90)
                
                # Standard consistency metric (5d vs 20d)
                r_5d = horizon_stats.get('5d', {}).get('spearman_corr', np.nan)
                horizon_consistent_5d_20d = False
                if not np.isnan(r_5d) and not np.isnan(r_20d):
                    horizon_consistent_5d_20d = (np.sign(r_5d) == np.sign(r_20d)) and (r_5d != 0.0) and (r_20d != 0.0)

                for horizon in horizon_stats.keys():
                    h_stat = horizon_stats[horizon]
                    rows.append({
                        'symbol': symbol,
                        'factor': raw_factor,
                        'representation': sig_name,
                        'horizon': horizon,
                        'n_obs': h_stat['n_obs'],
                        'pearson_corr': h_stat['pearson_corr'],
                        'pearson_t': h_stat['pearson_t'],
                        'pearson_p': h_stat['pearson_p'],
                        'spearman_corr': h_stat['spearman_corr'],
                        'spearman_t': h_stat['spearman_t'],
                        'spearman_p': h_stat['spearman_p'],
                        'spearman_first_half': h_stat['spearman_first_half'],
                        'spearman_second_half': h_stat['spearman_second_half'],
                        'temporal_consistent': h_stat['temporal_consistent'],
                        'horizon_consistent_5d_20d': horizon_consistent_5d_20d,
                        'horizon_sign_consistency_pct': horizon_sign_consistency_pct,
                        'horizon_consistent_sweep': horizon_consistent_sweep,
                        'mean_nw_t_stat': mean_nw_t_stat,
                        'smoothness_index': smoothness_index
                    })
                    
    df_results = pd.DataFrame(rows)
    csv_path = os.path.join(RESULTS_DIR, 'initial_correlation_results.csv')
    df_results.to_csv(csv_path, index=False)
    print(f"Saved {len(df_results)} rows of correlation results to: {csv_path}")
    
    # Save full results
    full_results_path = os.path.join(RESULTS_DIR, 'all_correlation_results.csv')
    df_results.to_csv(full_results_path, index=False)
    print(f"Saved all correlation results to: {full_results_path}")
    
    if df_results.empty:
        print("No correlation results computed.")
        return df_results, horizon_days_stats

    # Print median calendar days per horizon per symbol (excluding detailed sweep)
    print("\n=== Median Calendar Days per Horizon per Symbol ===")
    for sym in SYMBOLS:
        if sym in horizon_days_stats:
            d = horizon_days_stats[sym]
            parts = []
            for label in ['5d', '20d', 'H1', 'H2', 'H3']:
                if label in d:
                    parts.append(f"{label}={d[label]:3d}d")
                else:
                    parts.append(f"{label}=  - ")
            print(f"  {sym:4s}: {'  '.join(parts)}")
    
    # Save horizon days stats
    days_df = pd.DataFrame(horizon_days_stats).T
    days_df.index.name = 'symbol'
    days_path = os.path.join(RESULTS_DIR, 'horizon_days_stats.csv')
    days_df.to_csv(days_path)
    print(f"\nSaved horizon days stats to: {days_path}")
    
    # Save best factors for standard 5d and 20d horizons (legacy/backward compatibility)
    for h in ['5d', '20d', 'H1', 'H2', 'H3']:
        df_h = df_results[df_results['horizon'] == h].copy()
        if df_h.empty:
            continue
        df_h['abs_spearman_t'] = df_h['spearman_t'].abs()
        idx_best = df_h.groupby('symbol')['abs_spearman_t'].idxmax()
        df_best = df_h.loc[idx_best].sort_values('abs_spearman_t', ascending=False)
        best_h_path = os.path.join(RESULTS_DIR, f'best_factors_{h}_summary.csv')
        df_best.to_csv(best_h_path, index=False)
        
        # Also top 3
        df_top3 = df_h.sort_values(['symbol', 'abs_spearman_t'], ascending=[True, False]).groupby('symbol').head(3)
        top3_path = os.path.join(RESULTS_DIR, f'top3_factors_{h}_summary.csv')
        df_top3.to_csv(top3_path, index=False)

    # -------------------------------------------------------------------------
    # NEW: Determine Robust Best Factor using Horizon Sweep Stability
    # -------------------------------------------------------------------------
    best_robust_factors = []
    best_factors_dict = {}
    
    df_20d = df_results[df_results['horizon'] == '20d'].copy()
    if not df_20d.empty:
        for symbol in SYMBOLS:
            df_sym = df_20d[df_20d['symbol'] == symbol].copy()
            if df_sym.empty:
                continue
                
            # Score each candidate factor
            # Priority 1: both temporal and horizon consistent
            # Priority 2: horizon consistent only
            # Priority 3: any candidate
            df_sym['priority'] = 3
            df_sym.loc[df_sym['horizon_consistent_sweep'] & df_sym['temporal_consistent'], 'priority'] = 1
            df_sym.loc[df_sym['horizon_consistent_sweep'] & ~df_sym['temporal_consistent'], 'priority'] = 2
            
            # Sort by priority first, then by mean absolute NW t-statistic across horizons
            df_sym['abs_mean_nw_t'] = df_sym['mean_nw_t_stat'].abs()
            df_sym = df_sym.sort_values(by=['priority', 'abs_mean_nw_t'], ascending=[True, False])
            
            best_row = df_sym.iloc[0]
            best_robust_factors.append(best_row)
            
            sign = 1 if best_row['spearman_corr'] > 0 else -1
            best_factors_dict[symbol] = {
                'factor': best_row['factor'],
                'representation': best_row['representation'],
                'sign': sign,
                'priority': int(best_row['priority']),
                'spearman_corr_20d': float(best_row['spearman_corr']),
                'spearman_t_20d': float(best_row['spearman_t']),
                'mean_nw_t_stat': float(best_row['mean_nw_t_stat']),
                'horizon_sign_consistency_pct': float(best_row['horizon_sign_consistency_pct']),
                'horizon_consistent_sweep': bool(best_row['horizon_consistent_sweep']),
                'temporal_consistent': bool(best_row['temporal_consistent']),
                'smoothness_index': float(best_row['smoothness_index'])
            }
            
        df_best_robust = pd.DataFrame(best_robust_factors)
        robust_summary_path = os.path.join(RESULTS_DIR, 'best_robust_factors_summary.csv')
        df_best_robust.to_csv(robust_summary_path, index=False)
        print(f"\nSaved horizon-robust best factors summary to: {robust_summary_path}")
        
        print("\n=== Horizon-Robust Best Alternative Data Factors per Symbol (Sorted by Symbol) ===")
        print(df_best_robust[['symbol', 'factor', 'representation', 'spearman_corr', 'spearman_t', 'horizon_sign_consistency_pct', 'temporal_consistent', 'mean_nw_t_stat']].to_string(index=False))

    # Generate 5x5 stability plot
    if best_factors_dict:
        plot_horizon_stability(df_results, best_factors_dict, FIGURES_DIR)
        
    return df_results, horizon_days_stats

if __name__ == '__main__':
    run_correlation_test()
