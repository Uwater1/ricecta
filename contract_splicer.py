#!/usr/bin/env python3
"""
ContractSplicer builds a ratio-adjusted continuous daily price series
from individual contract daily parquet files. It avoids any reliance
on dominant contract files.
"""
import os
import pandas as pd
import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONTRACTS_DIR = os.path.join(_SCRIPT_DIR, 'data', 'contracts_daily')

class ContractSplicer:
    def __init__(self, symbol, k, slippage=0.0005):
        self.symbol = symbol
        self.k = k
        self.slippage = slippage
        self.roll_dates = []
        self.contract_log = None # pd.Series mapping date -> active_contract_id
        
        # Internal caches
        self._metadata = None
        self._df_contracts = None
        self._calendar_dates = None
        self._last_trading_days_dict = {}

    def _load_data(self):
        meta_path = os.path.join(CONTRACTS_DIR, 'metadata.parquet')
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"Metadata file not found: {meta_path}")
        self._metadata = pd.read_parquet(meta_path)
        self._metadata = self._metadata[self._metadata['underlying_symbol'] == self.symbol].copy()
        
        # Parse dates to DatetimeIndex format
        self._metadata['listed_date'] = pd.to_datetime(self._metadata['listed_date'])
        self._metadata['de_listed_date'] = pd.to_datetime(self._metadata['de_listed_date'])
        self._metadata = self._metadata.set_index('order_book_id')

        contracts_path = os.path.join(CONTRACTS_DIR, f"{self.symbol}.parquet")
        if not os.path.exists(contracts_path):
            raise FileNotFoundError(f"Contracts file not found for {self.symbol}: {contracts_path}")
        self._df_contracts = pd.read_parquet(contracts_path).sort_index()

        self._calendar_dates = pd.DatetimeIndex(
            self._df_contracts.index.get_level_values('date').unique()
        ).sort_values()

        # Build last trading days dict once
        for date in self._calendar_dates:
            key = (date.year, date.month)
            if key not in self._last_trading_days_dict or date > self._last_trading_days_dict[key]:
                self._last_trading_days_dict[key] = date

        # Precalculate exit limit dates for each contract
        self._metadata['exit_limit_date'] = [
            self._get_exit_limit_date(d) for d in self._metadata['de_listed_date']
        ]

        # Compute 5-day rolling average of open interest per contract
        if 'oi_5d' not in self._df_contracts.columns:
            self._df_contracts['oi_5d'] = self._df_contracts.groupby(level='order_book_id')['open_interest'].transform(
                lambda x: x.rolling(5, min_periods=1).mean()
            ).fillna(0.0)

    def _get_nth_trading_day_before(self, target_date, n):
        idx = self._calendar_dates.searchsorted(target_date)
        if idx >= n:
            return self._calendar_dates[idx - n]
        return target_date - pd.Timedelta(days=n)

    def _get_exit_limit_date(self, de_listed_date):
        de_listed_date = pd.to_datetime(de_listed_date)
        if self.symbol == 'TF':
            return self._get_nth_trading_day_before(de_listed_date, 5)
        else:
            year, month = de_listed_date.year, de_listed_date.month
            if month == 1:
                prec_year, prec_month = year - 1, 12
            else:
                prec_year, prec_month = year, month - 1
            key = (prec_year, prec_month)
            if key in self._last_trading_days_dict:
                return self._last_trading_days_dict[key]
            return pd.Timestamp(prec_year, prec_month, 1) + pd.offsets.MonthEnd(0)

    def build(self):
        self._load_data()
        
        # Pre-calculate active valid contract lists per date to avoid pandas queries in the loop
        valid_contracts_by_date = {date: [] for date in self._calendar_dates}
        for cid, row in self._metadata.iterrows():
            start = row['listed_date']
            end = row['exit_limit_date']
            idx_start = self._calendar_dates.searchsorted(start)
            idx_end = self._calendar_dates.searchsorted(end)
            for date in self._calendar_dates[idx_start:idx_end]:
                valid_contracts_by_date[date].append(cid)

        # Pivot all columns for quick lookup
        pivoted = {}
        for col in ['open', 'high', 'low', 'close']:
            pivoted[col] = self._df_contracts[col].unstack(level='order_book_id').ffill()
        for col in ['volume', 'open_interest']:
            pivoted[col] = self._df_contracts[col].unstack(level='order_book_id').fillna(0.0)
            
        oi_5d_pivoted = self._df_contracts['oi_5d'].unstack(level='order_book_id').fillna(0.0)

        # Initialize output DataFrame
        adjusted_df = pd.DataFrame(np.nan, index=self._calendar_dates, columns=['open', 'high', 'low', 'close', 'volume', 'open_interest'])
        active_contracts = pd.Series(index=self._calendar_dates, dtype=object)
        
        current_contract = None
        current_exit_limit = None
        
        for i, date in enumerate(self._calendar_dates):
            valid_contracts = valid_contracts_by_date[date]

            if not valid_contracts:
                if current_contract is not None:
                    active_contracts.loc[date] = current_contract
                    for col in ['open', 'high', 'low', 'close', 'volume', 'open_interest']:
                        if current_contract in pivoted[col].columns:
                            adjusted_df.loc[date, col] = pivoted[col].loc[date, current_contract]
                continue

            # Check open interest to filter/sort
            if date in oi_5d_pivoted.index:
                oi_vals = oi_5d_pivoted.loc[date, valid_contracts]
            else:
                oi_vals = pd.Series(0.0, index=valid_contracts)
            
            # Select top 3 by open interest
            liquid_contracts = oi_vals[oi_vals > 0].sort_values(ascending=False).head(3)
            if liquid_contracts.empty:
                liquid_contracts = oi_vals.sort_values(ascending=False).head(1)
            
            if liquid_contracts.empty:
                valid_price_cols = [c for c in valid_contracts if c in pivoted['close'].columns and not np.isnan(pivoted['close'].loc[date, c])]
                if valid_price_cols:
                    liquid_contracts = pd.Series(1.0, index=valid_price_cols)
            
            # Sort liquid contracts by maturity (de_listed_date)
            liquid_meta = self._metadata.loc[liquid_contracts.index].sort_values('de_listed_date')
            
            # Determine target contract (k-th nearest)
            target_contract = None
            target_exit_limit = None
            if not liquid_meta.empty:
                target_idx = min(self.k - 1, len(liquid_meta) - 1)
                target_contract = liquid_meta.index[target_idx]
                target_exit_limit = self._metadata.loc[target_contract, 'exit_limit_date']

            # 2. Check if we need to roll
            roll_needed = False
            if current_contract is None:
                roll_needed = True
            elif date >= current_exit_limit:
                roll_needed = True
            elif current_contract not in liquid_contracts.index:
                if target_contract is not None and target_contract != current_contract:
                    roll_needed = True
            
            # If roll needed, perform the roll
            if roll_needed and target_contract is not None and target_contract != current_contract:
                p_new = pivoted['close'].loc[date, target_contract] if target_contract in pivoted['close'].columns else np.nan
                p_old = pivoted['close'].loc[date, current_contract] if (current_contract is not None and current_contract in pivoted['close'].columns) else np.nan
                
                # Check if prices are valid to perform a roll
                if not np.isnan(p_new) and (current_contract is None or not np.isnan(p_old)):
                    if current_contract is not None:
                        # Calculate adjustment ratio
                        ratio = p_new / p_old if p_old != 0 else 1.0
                        ratio *= (1.0 - 2.0 * self.slippage)
                        
                        # Adjust all prior prices (open, high, low, close) by this ratio
                        for col in ['open', 'high', 'low', 'close']:
                            col_idx = adjusted_df.columns.get_loc(col)
                            adjusted_df.iloc[:i, col_idx] *= ratio
                        self.roll_dates.append(date)
                    
                    current_contract = target_contract
                    current_exit_limit = target_exit_limit

            # 3. Store active contract and price for today
            if current_contract is not None and current_contract in pivoted['close'].columns:
                for col in ['open', 'high', 'low', 'close', 'volume', 'open_interest']:
                    adjusted_df.loc[date, col] = pivoted[col].loc[date, current_contract]
                active_contracts.loc[date] = current_contract

        # Cleanup: ffill price series
        for col in ['open', 'high', 'low', 'close']:
            adjusted_df[col] = adjusted_df[col].ffill()
        self.contract_log = active_contracts
        
        return adjusted_df
