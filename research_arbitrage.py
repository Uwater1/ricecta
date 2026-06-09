#!/usr/bin/env python3
"""
Feasibility Study of Basis Momentum and Curve Arbitrage in Chinese Commodity Futures.
Processes 21 symbols, aligns 5-minute contract bars, simulates trades,
applies empirical transaction costs, and aggregates portfolio equity curves.
"""
import os
import glob
import numpy as np
import pandas as pd
import numba
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Directories
BASE_DIR = os.path.join(_SCRIPT_DIR, "data")
SPOT_DIR = os.path.join(BASE_DIR, "spot_basis")
FUTURES_DIR = os.path.join(BASE_DIR, "futures_5minute")
SHIBOR_DIR = os.path.join(BASE_DIR, "shibor")
FIGURES_DIR = os.path.join(_SCRIPT_DIR, "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

# 21 commodity symbols
SYMBOLS = [
    'C', 'M', 'Y', 'P', 'V', 'J', 'JD', 'I',  # DCE
    'CU', 'AL', 'AU', 'AG', 'RB', 'RU', 'NI', 'SN', # SHFE
    'CF', 'SR', 'TA', 'MA', 'SA' # CZCE
]

def load_shibor():
    shibor_path = os.path.join(SHIBOR_DIR, "shibor.parquet")
    if os.path.exists(shibor_path):
        df = pd.read_parquet(shibor_path)
        # Use 1-week Shibor as risk-free rate, convert from percentage to decimal per day
        if '1W' in df.columns:
            return df['1W'] / 100.0 / 252.0
    return pd.Series(0.0, index=pd.date_range("2021-01-01", "2026-06-03"))

def fix_czce_contract(contract, symbol):
    if pd.isna(contract) or not contract:
        return contract
    contract = str(contract).upper()
    if symbol in ['CF', 'SR', 'TA', 'MA', 'SA']:
        import re
        match = re.match(r"^([A-Z]+)(\d)(\d{2})$", contract)
        if match:
            sym_part = match.group(1)
            year_digit = match.group(2)
            month_part = match.group(3)
            return f"{sym_part}2{year_digit}{month_part}"
    return contract

def load_spot_data(symbol):
    dfs = []
    for year in range(2021, 2027):
        path = os.path.join(SPOT_DIR, f"spot_basis_{year}.parquet")
        if os.path.exists(path):
            df_year = pd.read_parquet(path)
            df_sym = df_year[df_year["symbol"] == symbol]
            dfs.append(df_sym)
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs).sort_values("date").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df["near_contract"] = df["near_contract"].apply(lambda x: fix_czce_contract(x, symbol))
    df["dominant_contract"] = df["dominant_contract"].apply(lambda x: fix_czce_contract(x, symbol))
    return df


def compute_metrics(returns, rf_daily=None):
    if returns.empty or returns.std() == 0:
        return {
            "annualized_return": 0.0,
            "annualized_vol": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0
        }
    
    # Cumulative return
    cum_returns = (1.0 + returns).cumprod()
    total_return = cum_returns.iloc[-1] - 1.0
    n_days = len(returns)
    ann_return = (cum_returns.iloc[-1]) ** (252.0 / n_days) - 1.0 if cum_returns.iloc[-1] > 0 else -1.0
    ann_vol = returns.std() * np.sqrt(252.0)
    
    # Sharpe Ratio
    if rf_daily is not None:
        excess_returns = returns - rf_daily.reindex(returns.index).fillna(0.0)
    else:
        excess_returns = returns
    sharpe = excess_returns.mean() / returns.std() * np.sqrt(252.0) if returns.std() > 0 else 0.0
    
    # Max Drawdown
    running_max = cum_returns.cummax()
    drawdown = (cum_returns - running_max) / running_max
    max_dd = drawdown.min()
    
    # Win Rate (daily positive returns)
    win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0.0
    
    return {
        "annualized_return": ann_return,
        "annualized_vol": ann_vol,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_dd,
        "win_rate": win_rate
    }

def backtest_basis_momentum(symbol, df_spot, shibor, tc_rate=0.0003, lookback=20):
    """
    Basis Momentum backtest.
    Trades the dominant contract daily based on the Basis Momentum signal.
    Correctly handles roll-adjusted returns (splicing) of dominant contracts.
    """
    if df_spot.empty or len(df_spot) < lookback + 5:
        return pd.Series(), {}
        
    df = df_spot.copy()
    
    # Basis Rate (dominant basis rate)
    df["basis_rate"] = df["dom_basis_rate"]
    
    # Basis Momentum signal: change in basis rate over lookback days
    df["bm_signal"] = df["basis_rate"] - df["basis_rate"].shift(lookback)
    
    # Shift signal to trade on the next day
    df["position"] = np.sign(df["bm_signal"].shift(1)).fillna(0.0)
    
    # Load daily price data for all dominant contracts of this symbol to compute splice returns
    contracts = df["dominant_contract"].unique()
    contract_prices = {}
    for c in contracts:
        path = os.path.join(FUTURES_DIR, symbol, f"{c}.parquet")
        if os.path.exists(path):
            df_c = pd.read_parquet(path)
            if not df_c.empty:
                # Group by trading_date (date) and get daily close
                df_daily_c = df_c.groupby("trading_date")["close"].last()
                contract_prices[c] = df_daily_c
                
    # Calculate daily contract-level splice returns (avoiding roll gap)
    daily_returns = []
    dates = df["date"].tolist()
    dominant_contracts = df["dominant_contract"].tolist()
    positions = df["position"].tolist()
    
    for i in range(1, len(df)):
        date_t = dates[i]
        date_prev = dates[i-1]
        active_contract = dominant_contracts[i-1] # position taken at close of i-1 is held on day i
        pos = positions[i]
        
        # We need the price of active_contract on day i and day i-1
        prices = contract_prices.get(active_contract)
        if prices is not None and date_t in prices.index and date_prev in prices.index:
            p_t = prices.loc[date_t]
            p_prev = prices.loc[date_prev]
            if p_prev > 0:
                ret = (p_t - p_prev) / p_prev
            else:
                ret = 0.0
        else:
            # Fallback to spot_basis dominant price if 5m file is missing
            p_t = df.loc[i, "dominant_contract_price"]
            p_prev = df.loc[i-1, "dominant_contract_price"]
            # But only if it's the same contract!
            if df.loc[i, "dominant_contract"] == df.loc[i-1, "dominant_contract"] and p_prev > 0:
                ret = (p_t - p_prev) / p_prev
            else:
                ret = 0.0
                
        # Deduct transaction costs on position changes
        prev_pos = positions[i-1]
        tc = 0.0
        if pos != prev_pos:
            tc = tc_rate * (1.0 if prev_pos == 0.0 or pos == 0.0 else 2.0)
            
        net_ret = pos * ret - tc
        daily_returns.append((date_t, net_ret))
        
    df_ret = pd.DataFrame(daily_returns, columns=["date", "return"]).set_index("date")["return"]
    metrics = compute_metrics(df_ret, shibor)
    return df_ret, metrics

@numba.njit(cache=True)
def _numba_intraday_curve_arb(near_close, dom_close, mean_s, std_s, entry_z, exit_z, tc_rate):
    n_bars = near_close.shape[0]
    day_pnl = 0.0
    pos = 0
    entry_spread = 0.0
    entry_notional = 0.0

    for bar_idx in range(n_bars):
        p_near = near_close[bar_idx]
        p_dom = dom_close[bar_idx]
        spread = p_near - p_dom
        if std_s == 0.0:
            continue
        z_score = (spread - mean_s) / std_s

        if bar_idx == n_bars - 1 and pos != 0:
            if pos == 1:
                trade_return = (spread - entry_spread) / entry_notional
            else:
                trade_return = -(spread - entry_spread) / entry_notional
            day_pnl += trade_return - 2.0 * tc_rate
            pos = 0
            continue

        if pos == 0:
            if z_score < -entry_z:
                pos = 1
                entry_spread = spread
                entry_notional = p_near + p_dom
                day_pnl -= 2.0 * tc_rate
            elif z_score > entry_z:
                pos = -1
                entry_spread = spread
                entry_notional = p_near + p_dom
                day_pnl -= 2.0 * tc_rate
        elif pos == 1:
            if z_score >= -exit_z:
                pos = 0
                trade_return = (spread - entry_spread) / entry_notional
                day_pnl += trade_return - 2.0 * tc_rate
        elif pos == -1:
            if z_score <= exit_z:
                pos = 0
                trade_return = -(spread - entry_spread) / entry_notional
                day_pnl += trade_return - 2.0 * tc_rate

    return day_pnl

def backtest_curve_arbitrage(symbol, df_spot, tc_rate=0.0003, z_window=20, entry_z=2.0, exit_z=0.2):
    """
    Curve Arbitrage (Calendar Spread) backtest using 5-minute data.
    """
    if df_spot.empty:
        return pd.Series(), {}
        
    # Load 5m contract close prices
    # Only load files for contracts active in spot_basis to save memory
    all_contracts = set(df_spot["near_contract"].unique()).union(set(df_spot["dominant_contract"].unique()))
    contract_data = {}
    for c in all_contracts:
        path = os.path.join(FUTURES_DIR, symbol, f"{c}.parquet")
        if os.path.exists(path):
            try:
                df_c = pd.read_parquet(path)
                if not df_c.empty:
                    contract_data[c] = df_c[["close", "trading_date"]]
            except Exception:
                pass
                
    # Calculate daily generic close spread for rolling Z-score stats.
    # Shift by 1 day to avoid look-ahead bias (using historical data only).
    df_daily = df_spot.copy()
    df_daily["daily_spread"] = df_daily["near_contract_price"] - df_daily["dominant_contract_price"]
    df_daily["spread_mean"] = df_daily["daily_spread"].rolling(z_window).mean().shift(1)
    df_daily["spread_std"] = df_daily["daily_spread"].rolling(z_window).std().shift(1)
    
    # Store daily stats in a dictionary for quick lookup
    stats_lookup = df_daily.set_index("date")[["spread_mean", "spread_std"]].to_dict(orient="index")
    
    # We will simulate the backtest day-by-day
    daily_returns_list = []
    
    for idx, row in df_spot.iterrows():
        date_t = row["date"]
        near = row["near_contract"]
        dom = row["dominant_contract"]
        
        # Get rolling daily stats for day t
        stats = stats_lookup.get(date_t)
        if stats is None or pd.isna(stats["spread_mean"]) or pd.isna(stats["spread_std"]) or stats["spread_std"] == 0:
            daily_returns_list.append((date_t, 0.0))
            continue
            
        mean_s = stats["spread_mean"]
        std_s = stats["spread_std"]
        
        # Load 5m bars for this trading day
        df_near_5m = contract_data.get(near)
        df_dom_5m = contract_data.get(dom)
        
        if df_near_5m is None or df_dom_5m is None:
            daily_returns_list.append((date_t, 0.0))
            continue
            
        # Filter 5m data by trading_date
        near_day = df_near_5m[df_near_5m["trading_date"] == date_t]
        dom_day = df_dom_5m[df_dom_5m["trading_date"] == date_t]
        
        if near_day.empty or dom_day.empty:
            daily_returns_list.append((date_t, 0.0))
            continue
            
        aligned_index = near_day.index.intersection(dom_day.index)
        if len(aligned_index) == 0:
            daily_returns_list.append((date_t, 0.0))
            continue
            
        near_aligned = near_day.loc[aligned_index, "close"].values.astype(np.float64)
        dom_aligned = dom_day.loc[aligned_index, "close"].values.astype(np.float64)
        
        day_pnl = _numba_intraday_curve_arb(
            near_aligned, dom_aligned, float(mean_s), float(std_s),
            entry_z, exit_z, tc_rate
        )
                    
        daily_returns_list.append((date_t, day_pnl))
        
    df_ret = pd.DataFrame(daily_returns_list, columns=["date", "return"]).set_index("date")["return"]
    metrics = compute_metrics(df_ret)
    return df_ret, metrics

def run_research():
    shibor = load_shibor()
    
    # We will test two transaction cost levels:
    # 1. Low Friction: 0.02% (2 bps)
    # 2. High Friction: 0.05% (5 bps)
    costs = {"low": 0.0002, "high": 0.0005}
    
    results = {}
    
    # Store daily return series for portfolio aggregation
    portfolio_bm_returns = {"low": [], "high": []}
    portfolio_ca_returns = {"low": [], "high": []}
    
    print("\n--- Running Backtests ---")
    for symbol in SYMBOLS:
        print(f"Processing symbol: {symbol}...")
        df_spot = load_spot_data(symbol)
        if df_spot.empty:
            print(f"  No data for {symbol}, skipping.")
            continue
            
        results[symbol] = {}
        
        # 1. Basis Momentum
        for label, tc in costs.items():
            ret, metr = backtest_basis_momentum(symbol, df_spot, shibor, tc_rate=tc, lookback=20)
            results[symbol][f"bm_{label}"] = metr
            if not ret.empty:
                portfolio_bm_returns[label].append(ret)
                
        # 2. Curve Arbitrage
        for label, tc in costs.items():
            ret, metr = backtest_curve_arbitrage(symbol, df_spot, tc_rate=tc, z_window=20)
            results[symbol][f"ca_{label}"] = metr
            if not ret.empty:
                portfolio_ca_returns[label].append(ret)
                
    # Aggregate equally weighted portfolios
    portfolio_results = {}
    
    for label in ["low", "high"]:
        # Basis Momentum Portfolio
        if portfolio_bm_returns[label]:
            bm_df = pd.concat(portfolio_bm_returns[label], axis=1).mean(axis=1).fillna(0.0)
            portfolio_results[f"bm_{label}"] = (bm_df, compute_metrics(bm_df, shibor))
            
        # Curve Arbitrage Portfolio
        if portfolio_ca_returns[label]:
            ca_df = pd.concat(portfolio_ca_returns[label], axis=1).mean(axis=1).fillna(0.0)
            portfolio_results[f"ca_{label}"] = (ca_df, compute_metrics(ca_df))
            
    # Print results summary table
    print("\n=== FEASIBILITY RESULTS SUMMARY ===")
    
    # Portfolios
    print("\nPortfolio Metrics:")
    print(f"{'Strategy & Cost':<30} | {'Return (Ann)':<12} | {'Vol (Ann)':<10} | {'Sharpe':<8} | {'MaxDD':<8} | {'WinRate':<8}")
    print("-" * 85)
    for k, (df_ret, metr) in portfolio_results.items():
        print(f"{k:<30} | {metr['annualized_return']*100:10.2f}% | {metr['annualized_vol']*100:8.2f}% | {metr['sharpe_ratio']:6.2f} | {metr['max_drawdown']*100:6.2f}% | {metr['win_rate']*100:6.2f}%")
        
    # Plot portfolio equity curves and drawdown
    fig, (ax_eq, ax_dd) = plt.subplots(2, 1, figsize=(13, 10),
        gridspec_kw={'height_ratios': [2, 1]}, sharex=True)
    for k, (df_ret, metr) in portfolio_results.items():
        cum_ret = (1.0 + df_ret).cumprod()
        ax_eq.plot(cum_ret.index, (cum_ret - 1.0) * 100.0, label=f"{k} (Sharpe: {metr['sharpe_ratio']:.2f})")
        # Drawdown
        running_max = cum_ret.cummax()
        dd = (cum_ret - running_max) / running_max * 100.0
        ax_dd.fill_between(dd.index, dd, 0, alpha=0.4, label=f"{k} (MaxDD: {metr['max_drawdown']*100:.1f}%)")

    ax_eq.set_title("Chinese Futures Arbitrage Portfolio Cumulative Returns (2021-2026)")
    ax_eq.set_ylabel("Cumulative Return (%)")
    ax_eq.legend()
    ax_eq.grid(True, linestyle="--", alpha=0.5)

    ax_dd.set_title("Underwater Drawdown")
    ax_dd.set_xlabel("Date")
    ax_dd.set_ylabel("Drawdown (%)")
    ax_dd.legend(fontsize=8)
    ax_dd.grid(True, linestyle="--", alpha=0.5)

    fig.tight_layout()
    plot_path = os.path.join(FIGURES_DIR, "portfolio_equity_curves.png")
    fig.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"\nSaved portfolio equity curves to {plot_path}")
    
    # Save individual symbol results to CSV
    rows = []
    for sym, metrics_dict in results.items():
        row = {"symbol": sym}
        for k, metr in metrics_dict.items():
            row[f"{k}_return"] = metr.get("annualized_return", 0.0)
            row[f"{k}_sharpe"] = metr.get("sharpe_ratio", 0.0)
            row[f"{k}_maxdd"] = metr.get("max_drawdown", 0.0)
        rows.append(row)
        
    df_out = pd.DataFrame(rows)
    csv_path = os.path.join(_SCRIPT_DIR, "arbitrage_metrics_by_symbol.csv")
    df_out.to_csv(csv_path, index=False)
    print(f"Saved symbol-level metrics to {csv_path}")

if __name__ == '__main__':
    run_research()
