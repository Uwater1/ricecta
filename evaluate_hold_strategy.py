#!/usr/bin/env python3
"""
Backtest engine for macro alpha contract holding strategy without rolling.
Implements dynamic Open Interest-based liquidity filtering and official maturity month exit rules.
"""
import os
import pandas as pd
import numpy as np
import warnings
from alphas import compute_alphas, get_dominant_switch_dates

warnings.filterwarnings('ignore')

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(_SCRIPT_DIR, 'data')
DAILY_DIR = os.path.join(BASE_DIR, 'dominant_daily')
SPOT_DIR = os.path.join(BASE_DIR, 'spot_basis')
CONTRACTS_DIR = os.path.join(BASE_DIR, 'contracts_daily')

_metadata_cache = None
_contracts_cache = {}

def load_metadata():
    global _metadata_cache
    if _metadata_cache is not None:
        return _metadata_cache.copy()
    path = os.path.join(CONTRACTS_DIR, 'metadata.parquet')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Metadata file not found: {path}")
    _metadata_cache = pd.read_parquet(path)
    return _metadata_cache.copy()

def load_symbol_contracts(symbol):
    if symbol in _contracts_cache:
        return _contracts_cache[symbol].copy()
    path = os.path.join(CONTRACTS_DIR, f"{symbol}.parquet")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Contracts file not found for {symbol}: {path}")
    df = pd.read_parquet(path)
    # Sort index [order_book_id, date]
    df = df.sort_index()
    _contracts_cache[symbol] = df
    return df.copy()

def get_nth_trading_day_before(calendar_dates, target_date, n):
    """Find the n-th trading day before the target_date in the calendar using binary search."""
    idx = calendar_dates.searchsorted(target_date)
    if idx >= n:
        return calendar_dates[idx - n]
    return target_date - pd.Timedelta(days=n)

def get_exit_limit_date(calendar_dates, symbol, de_listed_date, last_trading_days_dict):
    """Calculate the official exit limit date to avoid delivery/maturity month."""
    de_listed_date = pd.to_datetime(de_listed_date)
    
    if symbol == 'TF':
        # CFFEX TF: exit 5 trading days before de-listing date
        return get_nth_trading_day_before(calendar_dates, de_listed_date, 5)
    else:
        # Commodity Futures: exit before the delivery month starts
        # Find preceding month
        year, month = de_listed_date.year, de_listed_date.month
        if month == 1:
            prec_year, prec_month = year - 1, 12
        else:
            prec_year, prec_month = year, month - 1
            
        key = (prec_year, prec_month)
        if last_trading_days_dict and key in last_trading_days_dict:
            return last_trading_days_dict[key]
        # Fallback to calendar month end if not in trading calendar
        return pd.Timestamp(prec_year, prec_month, 1) + pd.offsets.MonthEnd(0)

def backtest_hold_strategy(symbol, signal_series, df_contracts, metadata, H, k, slippage=0.0005, switch_dates=None):
    """
    Runs holding strategy for a single symbol.
    H: holding period in trading days
    k: contract selection index (1 for nearest, 2 for 2nd nearest, 3 for 3rd nearest)
    switch_dates: list of dates where the dominant contract switches (entry candidates).
                  If None, falls back to data-driven detection via get_dominant_switch_dates().
    """
    # Create trading calendar from contract prices
    calendar_dates = pd.DatetimeIndex(df_contracts.index.get_level_values('date').unique()).sort_values()
    
    # Pre-compute last trading days dict once per backtest
    last_trading_days_dict = {}
    for date in calendar_dates:
        key = (date.year, date.month)
        if key not in last_trading_days_dict or date > last_trading_days_dict[key]:
            last_trading_days_dict[key] = date
            
    # Pre-calculate 5-day rolling average of open interest per contract to filter cold months
    # Group by order_book_id and compute rolling mean in-place only once
    if 'oi_5d' not in df_contracts.columns:
        df_contracts['oi_5d'] = df_contracts.groupby(level='order_book_id')['open_interest'].transform(
            lambda x: x.rolling(5, min_periods=1).mean()
        ).fillna(0.0)
    
    # Align signal series with trading calendar
    signal_series = signal_series.reindex(calendar_dates).ffill().fillna(0.0)

    # Identify entry dates: use dominant contract switch dates (data-driven)
    if switch_dates is None:
        switch_dates = get_dominant_switch_dates(symbol)

    # Map switch dates to the nearest trading day in the calendar
    calendar_set = set(calendar_dates)
    entry_dates = []
    for sd in switch_dates:
        sd = pd.Timestamp(sd)
        if sd in calendar_set:
            sig_val = signal_series.loc[sd]
            if sig_val != 0.0:
                entry_dates.append(sd)
        else:
            # Find the next available trading day on or after the switch date
            idx = calendar_dates.searchsorted(sd)
            if idx < len(calendar_dates):
                nearest_date = calendar_dates[idx]
                sig_val = signal_series.loc[nearest_date]
                if sig_val != 0.0:
                    entry_dates.append(nearest_date)
        
    # Pivot prices for fast lookup during simulation
    # We need close prices indexed by date with contracts as columns
    close_prices = df_contracts['close'].unstack(level='order_book_id').ffill()
    oi_5d_pivoted = df_contracts['oi_5d'].unstack(level='order_book_id').fillna(0.0)
    
    # Load metadata for active check
    sym_metadata = metadata[metadata['underlying_symbol'] == symbol].set_index('order_book_id')
    
    # Records of all trades
    trades = []
    # Daily returns series
    daily_returns = pd.Series(0.0, index=calendar_dates)
    # Track active trades on each day to compute equal-weighted returns
    daily_active_trades = {date: [] for date in calendar_dates}
    
    for entry_date in entry_dates:
        sig_val = signal_series.loc[entry_date]
        direction = 1.0 if sig_val > 0 else -1.0
        
        # Get active contracts on this entry date
        active_contracts = sym_metadata[
            (sym_metadata['listed_date'] <= entry_date.strftime('%Y-%m-%d')) &
            (sym_metadata['de_listed_date'] > entry_date.strftime('%Y-%m-%d'))
        ].index.tolist()
        
        if not active_contracts:
            continue
            
        # Get Open Interest for active contracts on entry date
        oi_vals = oi_5d_pivoted.loc[entry_date, active_contracts] if entry_date in oi_5d_pivoted.index else pd.Series(0.0, index=active_contracts)
        
        # Filter: Top 3 by Open Interest (relative ranking, no absolute floor)
        liquid_contracts = oi_vals[oi_vals > 0].sort_values(ascending=False).head(3)
        
        if liquid_contracts.empty:
            # Fallback to top 1 contract by OI including zero-OI if nothing else
            liquid_contracts = oi_vals.sort_values(ascending=False).head(1)
            
        if liquid_contracts.empty:
            continue
            
        # Sort liquid contracts by maturity (de_listed_date)
        liquid_contracts_metadata = sym_metadata.loc[liquid_contracts.index].sort_values('de_listed_date')
        
        # Select the k-th nearest contract, trying next ones if exit date is invalid
        chosen_contract = None
        exit_date = None
        
        start_idx = min(k - 1, len(liquid_contracts_metadata) - 1)
        
        for idx in range(start_idx, len(liquid_contracts_metadata)):
            contract = liquid_contracts_metadata.index[idx]
            de_list = liquid_contracts_metadata.loc[contract, 'de_listed_date']
            
            # Find the position of entry_date in the calendar
            try:
                entry_idx = calendar_dates.get_loc(entry_date)
                # Tentative exit date H trading days later
                exit_idx = min(entry_idx + H, len(calendar_dates) - 1)
                tentative_exit_date = calendar_dates[exit_idx]
            except Exception:
                continue
                
            # Maturity/delivery limit exit date
            limit_date = get_exit_limit_date(calendar_dates, symbol, de_list, last_trading_days_dict)
            
            # Actual exit date is the minimum of tentative exit and limit date
            actual_exit = min(tentative_exit_date, limit_date)
            
            if actual_exit > entry_date:
                chosen_contract = contract
                exit_date = actual_exit
                break
                
        if chosen_contract is None or exit_date is None:
            continue
            
        # Get price series for chosen contract
        if chosen_contract not in close_prices.columns:
            continue
            
        # Extract trade window
        trade_dates = calendar_dates[(calendar_dates > entry_date) & (calendar_dates <= exit_date)]
        if trade_dates.empty:
            continue
            
        # Record trade details
        p_entry = close_prices.loc[entry_date, chosen_contract]
        p_exit = close_prices.loc[exit_date, chosen_contract]
        
        if np.isnan(p_entry) or np.isnan(p_exit) or p_entry == 0:
            continue
            
        raw_trade_ret = direction * (p_exit / p_entry - 1.0)
        net_trade_ret = raw_trade_ret - 2.0 * slippage # 5 bp each side
        
        trades.append({
            'contract': chosen_contract,
            'entry_date': entry_date,
            'exit_date': exit_date,
            'direction': 'LONG' if direction > 0 else 'SHORT',
            'p_entry': p_entry,
            'p_exit': p_exit,
            'raw_return': raw_trade_ret,
            'net_return': net_trade_ret
        })
        
        # Reconstruct daily trade returns
        # For each day in the trade hold period, compute the return
        prev_date = entry_date
        for date in trade_dates:
            p_prev = close_prices.loc[prev_date, chosen_contract]
            p_curr = close_prices.loc[date, chosen_contract]
            
            if not np.isnan(p_prev) and not np.isnan(p_curr) and p_prev > 0:
                day_ret = direction * (p_curr / p_prev - 1.0)
            else:
                day_ret = 0.0
                
            # Deduct entry slippage on the first holding day
            if date == trade_dates[0]:
                day_ret -= slippage
            # Deduct exit slippage on the last holding day
            if date == exit_date:
                day_ret -= slippage
                
            daily_active_trades[date].append(day_ret)
            prev_date = date

    # Aggregate daily returns across overlapping trades by equal weighting them
    for date in calendar_dates:
        day_rets = daily_active_trades[date]
        if day_rets:
            daily_returns.loc[date] = np.mean(day_rets)
        else:
            daily_returns.loc[date] = 0.0
            
    # Calculate performance metrics
    metrics = calculate_metrics(daily_returns, trades)
    
    return {
        'daily_returns': daily_returns,
        'trades': trades,
        'metrics': metrics
    }

def calculate_metrics(daily_returns, trades):
    """Compute standard backtest performance metrics."""
    T = len(daily_returns)
    if T == 0 or not trades:
        return {
            'ann_return': 0.0, 'ann_vol': 0.0, 'sharpe': 0.0,
            'max_dd': 0.0, 'calmar': 0.0, 'sortino': 0.0,
            'win_rate': 0.0, 'total_trades': 0
        }
        
    ann_return = daily_returns.mean() * 252
    ann_vol = daily_returns.std() * np.sqrt(252)
    sharpe = ann_return / ann_vol if ann_vol > 0 else 0.0
    
    # Max Drawdown
    cum_returns = (1.0 + daily_returns).cumprod()
    running_max = cum_returns.cummax()
    drawdown = (cum_returns - running_max) / running_max
    max_dd = drawdown.min()
    
    # Calmar
    calmar = ann_return / abs(max_dd) if max_dd != 0 else 0.0
    
    # Sortino
    neg_rets = daily_returns[daily_returns < 0]
    downside_std = np.sqrt((neg_rets ** 2).mean()) * np.sqrt(252)
    sortino = ann_return / downside_std if downside_std > 0 else 0.0
    
    # Win rate of trades
    net_rets = [t['net_return'] for t in trades]
    win_rate = sum(1 for r in net_rets if r > 0) / len(net_rets) if net_rets else 0.0
    
    return {
        'ann_return': ann_return,
        'ann_vol': ann_vol,
        'sharpe': sharpe,
        'max_dd': max_dd,
        'calmar': calmar,
        'sortino': sortino,
        'win_rate': win_rate,
        'total_trades': len(trades)
    }

def get_alpha_signals():
    """Load Alt_Macro_Alpha for all symbols."""
    print("Calculating Alt_Macro_Alpha using alphas.py...")
    # List of all symbols
    symbols = [
        'C', 'M', 'Y', 'P', 'V', 'J', 'JD', 'I',
        'CU', 'AL', 'AU', 'AG', 'RB', 'RU', 'NI', 'SN',
        'SC',
        'CF', 'SR', 'TA', 'MA', 'SA',
        'TF'
    ]
    df_alphas = compute_alphas(DAILY_DIR, SPOT_DIR, symbols)
    return df_alphas['Alt_Macro_Alpha'].unstack()
