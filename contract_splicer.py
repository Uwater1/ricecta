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

# Module-level caches to avoid repeated I/O across symbols
_metadata_cache = None
_contracts_cache = {}  # symbol -> DataFrame

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
        global _metadata_cache
        if _metadata_cache is None:
            meta_path = os.path.join(CONTRACTS_DIR, 'metadata.parquet')
            if not os.path.exists(meta_path):
                raise FileNotFoundError(f"Metadata file not found: {meta_path}")
            _metadata_cache = pd.read_parquet(meta_path)
        self._metadata = _metadata_cache[_metadata_cache['underlying_symbol'] == self.symbol].copy()
        
        # Parse dates to DatetimeIndex format
        self._metadata['listed_date'] = pd.to_datetime(self._metadata['listed_date'])
        self._metadata['de_listed_date'] = pd.to_datetime(self._metadata['de_listed_date'])
        self._metadata = self._metadata.set_index('order_book_id')

        if self.symbol not in _contracts_cache:
            contracts_path = os.path.join(CONTRACTS_DIR, f"{self.symbol}.parquet")
            if not os.path.exists(contracts_path):
                raise FileNotFoundError(f"Contracts file not found for {self.symbol}: {contracts_path}")
            df_c = pd.read_parquet(contracts_path).sort_index()
            # Compute oi_5d once at load time
            if 'oi_5d' not in df_c.columns:
                df_c['oi_5d'] = df_c.groupby(level='order_book_id')['open_interest'].transform(
                    lambda x: x.rolling(5, min_periods=1).mean()
                ).fillna(0.0)
            _contracts_cache[self.symbol] = df_c
        self._df_contracts = _contracts_cache[self.symbol]

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
        
        # Pre-calculate active valid contract lists per date
        cal_arr = self._calendar_dates.values
        n_dates = len(cal_arr)
        valid_contracts_by_date = [[] for _ in range(n_dates)]
        for cid, row in self._metadata.iterrows():
            start = row['listed_date']
            end = row['exit_limit_date']
            idx_start = self._calendar_dates.searchsorted(start)
            idx_end = self._calendar_dates.searchsorted(end)
            for j in range(idx_start, idx_end):
                valid_contracts_by_date[j].append(cid)

        # Pivot all columns for quick lookup using numpy arrays
        pivoted = {}
        for col in ['open', 'high', 'low', 'close']:
            p = self._df_contracts[col].unstack(level='order_book_id').ffill()
            pivoted[col] = p
        for col in ['volume', 'open_interest']:
            p = self._df_contracts[col].unstack(level='order_book_id').fillna(0.0)
            pivoted[col] = p
            
        oi_5d_pivoted = self._df_contracts['oi_5d'].unstack(level='order_book_id').fillna(0.0)

        # Use numpy arrays for fast assignment
        close_piv = pivoted['close']
        contract_ids = close_piv.columns.tolist()
        date_index = close_piv.index
        n_contracts = len(contract_ids)
        cid_to_idx = {c: i for i, c in enumerate(contract_ids)}

        # Pre-extract numpy arrays for each column
        np_piv = {}
        for col in ['open', 'high', 'low', 'close', 'volume', 'open_interest']:
            piv = pivoted[col]
            # Reindex to common date index and contract columns
            np_piv[col] = piv.reindex(index=date_index, columns=contract_ids).values

        np_oi5d = oi_5d_pivoted.reindex(index=date_index, columns=contract_ids).values

        # Output arrays
        out_open = np.full(n_dates, np.nan)
        out_high = np.full(n_dates, np.nan)
        out_low = np.full(n_dates, np.nan)
        out_close = np.full(n_dates, np.nan)
        out_volume = np.full(n_dates, np.nan)
        out_oi = np.full(n_dates, np.nan)
        active_contract_arr = [None] * n_dates

        # Precompute de_listed dates as dict for fast lookup
        de_listed_dict = dict(zip(self._metadata.index, pd.to_datetime(self._metadata['de_listed_date'])))
        exit_limit_dict = dict(zip(self._metadata.index, self._metadata['exit_limit_date']))

        current_contract = None
        current_exit_limit = None
        
        for i in range(n_dates):
            date = self._calendar_dates[i]
            valid_contracts = valid_contracts_by_date[i]

            if not valid_contracts:
                if current_contract is not None:
                    active_contract_arr[i] = current_contract
                    c_idx = cid_to_idx.get(current_contract)
                    if c_idx is not None:
                        out_open[i] = np_piv['open'][i, c_idx]
                        out_high[i] = np_piv['high'][i, c_idx]
                        out_low[i] = np_piv['low'][i, c_idx]
                        out_close[i] = np_piv['close'][i, c_idx]
                        out_volume[i] = np_piv['volume'][i, c_idx]
                        out_oi[i] = np_piv['open_interest'][i, c_idx]
                continue

            # Check open interest
            oi_vals = np_oi5d[i]
            vc_indices = [cid_to_idx[c] for c in valid_contracts if c in cid_to_idx]
            if not vc_indices:
                continue

            oi_sub = [(j, oi_vals[j]) for j in vc_indices if oi_vals[j] > 0]
            oi_sub.sort(key=lambda x: -x[1])
            liquid_indices = oi_sub[:3]
            if not liquid_indices:
                all_sub = [(j, oi_vals[j]) for j in vc_indices]
                all_sub.sort(key=lambda x: -x[1])
                liquid_indices = all_sub[:1]

            if not liquid_indices:
                # Check for valid prices
                valid_price = [j for j in vc_indices if not np.isnan(np_piv['close'][i, j])]
                if valid_price:
                    liquid_indices = [(valid_price[0], 1.0)]

            if not liquid_indices:
                continue

            # Sort liquid contracts by maturity
            liquid_cids = [contract_ids[j] for j, _ in liquid_indices]
            liquid_cids_sorted = sorted(liquid_cids, key=lambda c: de_listed_dict.get(c, pd.Timestamp.max))

            # Determine target contract
            target_contract = liquid_cids_sorted[min(self.k - 1, len(liquid_cids_sorted) - 1)]
            target_exit_limit = exit_limit_dict.get(target_contract)

            # Check if roll needed
            roll_needed = False
            if current_contract is None:
                roll_needed = True
            elif date >= current_exit_limit:
                roll_needed = True
            elif current_contract not in [contract_ids[j] for j, _ in liquid_indices]:
                if target_contract is not None and target_contract != current_contract:
                    roll_needed = True

            if roll_needed and target_contract is not None and target_contract != current_contract:
                t_idx = cid_to_idx.get(target_contract)
                p_new = np_piv['close'][i, t_idx] if t_idx is not None else np.nan
                if current_contract is not None:
                    c_idx = cid_to_idx.get(current_contract)
                    p_old = np_piv['close'][i, c_idx] if c_idx is not None else np.nan
                else:
                    p_old = None

                if not np.isnan(p_new) and (p_old is None or not np.isnan(p_old)):
                    if current_contract is not None and p_old is not None:
                        ratio = p_new / p_old if p_old != 0 else 1.0
                        ratio *= (1.0 - 2.0 * self.slippage)
                        # Apply ratio to all prior prices using numpy
                        out_open[:i] *= ratio
                        out_high[:i] *= ratio
                        out_low[:i] *= ratio
                        out_close[:i] *= ratio
                        self.roll_dates.append(date)

                    current_contract = target_contract
                    current_exit_limit = target_exit_limit

            # Store active contract and prices
            if current_contract is not None:
                c_idx = cid_to_idx.get(current_contract)
                if c_idx is not None:
                    active_contract_arr[i] = current_contract
                    out_open[i] = np_piv['open'][i, c_idx]
                    out_high[i] = np_piv['high'][i, c_idx]
                    out_low[i] = np_piv['low'][i, c_idx]
                    out_close[i] = np_piv['close'][i, c_idx]
                    out_volume[i] = np_piv['volume'][i, c_idx]
                    out_oi[i] = np_piv['open_interest'][i, c_idx]

        # Build output DataFrame
        adjusted_df = pd.DataFrame({
            'open': out_open, 'high': out_high, 'low': out_low,
            'close': out_close, 'volume': out_volume, 'open_interest': out_oi,
        }, index=self._calendar_dates)

        # Cleanup: ffill price series
        for col in ['open', 'high', 'low', 'close']:
            adjusted_df[col] = adjusted_df[col].ffill()
        self.contract_log = pd.Series(active_contract_arr, index=self._calendar_dates)
        
        return adjusted_df
