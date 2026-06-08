#!/usr/bin/env python3
"""
Framework for evaluating daily alpha signals on commodity futures.
Calculates 11 metrics including DSR, Turnover-Adjusted Calmar, and Capacity-Adjusted Sharpe Decay.
"""
import numpy as np
import pandas as pd
import scipy.stats as stats

# Contract multipliers for the 23 symbols
MULTIPLIERS = {
    'C': 10.0, 'M': 10.0, 'Y': 10.0, 'P': 10.0, 'V': 5.0, 'J': 100.0, 'JD': 10.0, 'I': 100.0,
    'CU': 5.0, 'AL': 5.0, 'AU': 1000.0, 'AG': 15.0, 'RB': 10.0, 'RU': 10.0, 'NI': 1.0, 'SN': 1.0,
    'SC': 1000.0, 'CF': 5.0, 'SR': 10.0, 'TA': 5.0, 'MA': 10.0, 'SA': 20.0, 'TF': 10000.0
}

def calculate_dsr(returns, all_sharpes, N=5):
    """
    Calculates the Deflated Sharpe Ratio (DSR) using Bailey and López de Prado's method.
    """
    T = len(returns)
    if T <= 2:
        return 0.0
        
    daily_mean = returns.mean()
    daily_std = returns.std()
    if daily_std == 0:
        return 0.0
        
    daily_sr = daily_mean / daily_std
    ann_sr = daily_sr * np.sqrt(252)
    
    # Skewness and Excess Kurtosis
    gamma3 = returns.skew()
    gamma4 = returns.kurt() # pandas kurt() returns excess kurtosis
    
    # Standard deviation of daily Sharpe Ratio estimate
    var_sr = (1.0 + 0.5 * (daily_sr ** 2) - gamma3 * daily_sr + 0.25 * gamma4 * (daily_sr ** 2)) / (T - 1)
    std_sr = np.sqrt(max(var_sr, 1e-8))
    
    # expected max Sharpe Ratio
    v_sr = np.var(all_sharpes) if len(all_sharpes) > 1 else 0.0
    
    euler = 0.5772156649
    if N > 1 and v_sr > 0:
        exp_max_sr = np.sqrt(v_sr) * ((1.0 - euler) * stats.norm.ppf(1.0 - 1.0 / N) + euler * stats.norm.ppf(1.0 - 1.0 / N * np.exp(-1)))
    else:
        exp_max_sr = 0.0
        
    # convert exp_max_sr to daily scale
    exp_max_sr_daily = exp_max_sr / np.sqrt(252)
    
    # Probabilistic Sharpe Ratio
    z = (daily_sr - exp_max_sr_daily) / std_sr
    dsr = stats.norm.cdf(z)
    
    return dsr

def evaluate_alpha(df_data, alpha_col, all_sharpes=None, N=5, tc_rate=0.0005, demean=True):
    """
    Evaluates a single alpha signal.
    df_data: DataFrame with MultiIndex [date, symbol] and columns [close, volume, returns, alpha_col]
    """
    df = df_data.copy()
    
    # Filter valid alpha signals
    df = df.dropna(subset=[alpha_col])
    if df.empty:
        return {}
        
    # Cast key columns to float32 for speed and memory efficiency
    for col in ["close", "volume", "returns", alpha_col]:
        if col in df.columns:
            df[col] = df[col].astype(np.float32)
            
    # Pivot weights and returns to align them
    signals = df[alpha_col].unstack()
    asset_returns = df["returns"].unstack().fillna(0.0).astype(np.float32)
    
    # Demean cross-sectionally if demean=True
    if demean:
        demeaned = signals.sub(signals.mean(axis=1), axis=0)
    else:
        demeaned = signals
    abs_sum = demeaned.abs().sum(axis=1)
    
    # Compute standardized weights: demeaned / sum(|demeaned|)
    weights = demeaned.div(abs_sum.replace(0.0, np.nan), axis=0).fillna(0.0).astype(np.float32)
    
    # Shift weights by 1 day to avoid lookahead (trade at close of t-1, hold on day t)
    weights_shifted = weights.shift(1).fillna(0.0)
    
    # Calculate daily portfolio returns
    port_returns = (weights_shifted * asset_returns).sum(axis=1)
    
    # Calculate daily turnover
    turnover = weights.diff().abs().sum(axis=1)
    # Deduct transaction cost
    port_net_returns = port_returns - turnover * tc_rate
    
    # Metrics calculations
    ann_return = port_net_returns.mean() * 252
    ann_vol = port_net_returns.std() * np.sqrt(252)
    sharpe = ann_return / ann_vol if ann_vol > 0 else 0.0
    
    # Max Drawdown
    cum_returns = (1.0 + port_net_returns).cumprod()
    running_max = cum_returns.cummax()
    drawdown = (cum_returns - running_max) / running_max
    max_dd = drawdown.min()
    
    # Turnover-Adjusted Calmar Ratio
    calmar = ann_return / abs(max_dd) if max_dd != 0 else 0.0
    
    # Sortino Ratio
    neg_returns = port_net_returns[port_net_returns < 0]
    downside_std = np.sqrt((neg_returns ** 2).mean()) * np.sqrt(252)
    sortino = ann_return / downside_std if downside_std > 0 else 0.0
    
    # Profit Factor
    pos_sum = port_net_returns[port_net_returns > 0].sum()
    neg_sum = abs(port_net_returns[port_net_returns < 0].sum())
    profit_factor = pos_sum / neg_sum if neg_sum > 0 else np.nan
    
    # Win Rate
    win_rate = (port_net_returns > 0).sum() / len(port_net_returns) if len(port_net_returns) > 0 else 0.0
    
    # Hit Rate (asset-level win rate)
    trade_mask = (weights_shifted != 0)
    total_trades = trade_mask.sum().sum()
    winning_trades = ((weights_shifted * asset_returns) > 0).sum().sum()
    hit_rate = winning_trades / total_trades if total_trades > 0 else 0.0
    
    # Information Coefficient (IC)
    # Daily rank correlation between alpha at t and asset return at t+1
    rets = asset_returns.shift(-1)
    
    sigs_ranked = signals.rank(axis=1, ascending=True)
    rets_ranked = rets.rank(axis=1, ascending=True)
    
    sigs_dm = sigs_ranked.sub(sigs_ranked.mean(axis=1), axis=0)
    rets_dm = rets_ranked.sub(rets_ranked.mean(axis=1), axis=0)
    
    numerator = (sigs_dm * rets_dm).sum(axis=1)
    denominator = np.sqrt((sigs_dm ** 2).sum(axis=1) * (rets_dm ** 2).sum(axis=1))
    
    # Only keep dates where both sigs and rets have at least 5 non-nan values
    valid_count = (signals.notna() & rets.notna()).sum(axis=1)
    daily_ics = (numerator / denominator.replace(0.0, np.nan)).where(valid_count > 5)
    mean_ic = daily_ics.mean(skipna=True)
    if np.isnan(mean_ic):
        mean_ic = 0.0
        
    # Top/Bottom Quintile Returns (completely vectorized)
    n_valid = signals.notna().sum(axis=1)
    ranks = signals.rank(axis=1, ascending=True)
    
    is_top = ranks.gt(n_valid * 0.8, axis=0) & (n_valid >= 5)
    is_bot = ranks.le(n_valid * 0.2, axis=0) & (n_valid >= 5)
    
    q_weights_top = is_top.astype(np.float32)
    q_weights_bot = is_bot.astype(np.float32)
    
    q_weights_top = q_weights_top.div(q_weights_top.sum(axis=1).replace(0.0, np.nan), axis=0).fillna(0.0)
    q_weights_bot = q_weights_bot.div(q_weights_bot.sum(axis=1).replace(0.0, np.nan), axis=0).fillna(0.0)
    
    q_ret_top = (q_weights_top.shift(1).fillna(0.0) * asset_returns).sum(axis=1)
    q_ret_bot = (q_weights_bot.shift(1).fillna(0.0) * asset_returns).sum(axis=1)
    
    top_quintile_ann = q_ret_top.mean() * 252
    bot_quintile_ann = q_ret_bot.mean() * 252
    
    # Deflated Sharpe Ratio
    if all_sharpes is None:
        all_sharpes = [sharpe]
    dsr = calculate_dsr(port_net_returns, all_sharpes, N=N)
    
    # Capacity-Adjusted Sharpe Decay
    # We estimate Sharpe Ratio at different AUM levels (0, 10M, 50M, 100M, 500M RMB)
    # Market impact cost model: impact = 0.1 * vol_20 * sqrt(trade_notional / market_volume_20)
    aums = [0, 10_000_000, 50_000_000, 100_000_000, 500_000_000]
    capacity_sharpes = {}
    
    # Pre-calculate symbol daily volatility (rolling 20-day standard deviation of returns)
    df["vol_20"] = df["returns"].unstack().rolling(20).std().stack().astype(np.float32)
    # Pre-calculate symbol daily market notional volume (volume * close * multiplier)
    df["multiplier"] = df.index.get_level_values("symbol").map(MULTIPLIERS).fillna(1.0).astype(np.float32)
    df["market_notional_volume"] = (df["volume"] * df["close"] * df["multiplier"]).astype(np.float32)
    df["market_vol_20"] = df["market_notional_volume"].unstack().rolling(20).mean().stack().astype(np.float32)
    
    # Re-align features
    vol_20 = df["vol_20"].unstack().fillna(0.0)
    market_vol_20 = df["market_vol_20"].unstack().fillna(1.0)
    
    for aum in aums:
        if aum == 0:
            capacity_sharpes[aum] = sharpe
            continue
            
        # Daily traded notional: AUM * |w_t - w_{t-1}|
        traded_notional = weights.diff().abs() * aum
        
        # Calculate impact cost per asset
        # impact = 0.1 * vol_20 * sqrt(traded_notional / market_vol_20)
        impact = 0.1 * vol_20 * np.sqrt(traded_notional / market_vol_20.clip(lower=1.0))
        # Total portfolio daily impact cost
        port_impact = (weights_shifted.abs() * impact).sum(axis=1)
        
        # Net returns after impact
        aum_net_returns = port_net_returns - port_impact
        aum_ann_return = aum_net_returns.mean() * 252
        aum_ann_vol = aum_net_returns.std() * np.sqrt(252)
        aum_sharpe = aum_ann_return / aum_ann_vol if aum_ann_vol > 0 else 0.0
        capacity_sharpes[aum] = aum_sharpe
        
    return {
        "annualized_return": ann_return,
        "annualized_vol": ann_vol,
        "sharpe_ratio": sharpe,
        "deflated_sharpe_ratio": dsr,
        "calmar_ratio": calmar,
        "max_drawdown": max_dd,
        "sortino_ratio": sortino,
        "profit_factor": profit_factor,
        "win_rate": win_rate,
        "hit_rate": hit_rate,
        "ic": mean_ic,
        "top_quintile_return": top_quintile_ann,
        "bottom_quintile_return": bot_quintile_ann,
        "capacity_sharpes": capacity_sharpes
    }

if __name__ == '__main__':
    # Verify evaluate_alpha structure
    print("Testing evaluate_alpha metrics imports...")
