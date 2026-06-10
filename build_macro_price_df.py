#!/usr/bin/env python3
"""
Pipeline to build aligned look-ahead-free macro data and price DataFrames.
Filters out unrelated factors (keeps factors with |t| >= 1.0 in historical correlation).
Outputs long panel DataFrame (parquet) and symbol-specific wide CSVs.
Marks release and signal dates for effective factors (especially PMIs on AG).
"""
import os
import re
import json
import pandas as pd
import numpy as np
import warnings
from contract_splicer import ContractSplicer
from alphas import BEST_HOLD_PARAMS

warnings.filterwarnings('ignore')

# Factor display name map for cleaner column naming
FACTOR_DISPLAY_NAMES = {
    'PPI_全部工业品(全国:当期同比增长率:月)': 'PPI_All_Industry_YoY',
    'PPIRM_燃料及动力类(全国:当期同比增长率:月)': 'PPIRM_Fuel_Power_YoY',
    '制造业采购经理指数PMI_购进价格': 'PMI_Input_Price',
    '制造业采购经理指数PMI_当月': 'Manufacturing_PMI',
    '制造业采购经理指数PMI_原材料库存': 'PMI_Raw_Material_Inventory',
    '制造业采购经理指数PMI_新订单': 'PMI_New_Orders',
    '非制造业PMI_建筑业_新订单_全国_当期值_月': 'Non_Mfg_PMI_Constr_New_Orders',
    'PMI_生产经营活动预期_全国_当期值_月': 'PMI_Business_Expectation',
    '非制造业PMI_建筑业_业务活动预期_全国_当期值_月': 'Non_Mfg_PMI_Constr_Expectation',
    'PPI_皮革、毛皮、羽毛及其制品 and 制鞋业(全国:当期同比增长率:月)': 'PPI_Leather_Footwear_YoY',
    'PPI_通信设备、计算机及其他电子设备制造业工业品出厂价格指数PPI_(上年=100)_当月': 'PPI_Telecom_Electronics_YoY',
    'PPI_电气机械及器材制造业(全国:当期同比增长率:月)': 'PPI_Electrical_Machinery_YoY',
    'GDP增长贡献率_第二产业_累计同比_季': 'GDP_Contribution_2nd_Industry_YoY',
    '社会融资规模_当月值': 'Social_Financing_Monthly',
    '社会融资规模存量_同比增速_月末数': 'Social_Financing_Stock_YoY',
    '国内生产总值GDP_累计同比': 'GDP_Cumulative_YoY',
}

def get_clean_name(factor_name):
    if factor_name in FACTOR_DISPLAY_NAMES:
        return FACTOR_DISPLAY_NAMES[factor_name]
    # Fallback clean name
    clean = re.sub(r'[\\/*?:"<>|(),：\s]', '_', factor_name).strip('_')
    # Replace contiguous underscores
    clean = re.sub(r'_{2,}', '_', clean)
    return clean

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, 'data', 'results')
    output_dir = os.path.join(results_dir, 'aligned_by_symbol')
    os.makedirs(output_dir, exist_ok=True)
    
    # Load all correlation results
    corr_path = os.path.join(results_dir, 'all_correlation_results.csv')
    if not os.path.exists(corr_path):
        raise FileNotFoundError(f"Missing correlation screening results: {corr_path}. Run test_alt_alphas.py first.")
    
    df_all_corr = pd.read_csv(corr_path)
    # Target 20d horizon
    df_corr_20d = df_all_corr[df_all_corr['horizon'] == '20d'].copy()
    
    # Symbols list
    symbols = [
        'C', 'M', 'Y', 'P', 'V', 'J', 'JD', 'I',  # DCE
        'CU', 'AL', 'AU', 'AG', 'RB', 'RU', 'NI', 'SN', # SHFE
        'SC', # INE
        'CF', 'SR', 'TA', 'MA', 'SA', # CZCE
        'TF' # CFFEX
    ]
    
    macro_dir = os.path.join(script_dir, 'data', 'macro_factors')
    
    long_rows = []
    
    print("Starting alignment and filtering process...")
    
    for symbol in symbols:
        # Get k-th nearest liquid contract parameter
        k = BEST_HOLD_PARAMS.get(symbol, (20, 1))[1]
        try:
            splicer = ContractSplicer(symbol, k=k)
            df_price = splicer.build()
        except Exception as e:
            print(f"Warning: could not splice prices for {symbol}: {e}")
            continue
            
        if df_price.empty:
            continue
            
        # Clean price data index
        if not isinstance(df_price.index, pd.DatetimeIndex):
            df_price.index = pd.to_datetime(df_price.index)
        df_price = df_price.sort_index()
        
        # Clean price returns
        df_price['returns'] = df_price['close'].pct_change()
        # Clean inf/nan returns
        df_price['returns'] = df_price['returns'].replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(-0.1, 0.1)
        
        trading_dates = df_price.index
        all_dates = pd.date_range(start=trading_dates.min(), end=trading_dates.max(), freq='D')
        
        # Get related factors for this symbol from correlation results (|t| >= 1.0)
        df_sym_corr = df_corr_20d[
            (df_corr_20d['symbol'] == symbol) & 
            (df_corr_20d['spearman_t'].notna()) & 
            (df_corr_20d['spearman_t'].abs() >= 1.0)
        ].copy()
        
        if df_sym_corr.empty:
            print(f"  No related factors found for {symbol} with |t| >= 1.0. Skipping symbol.")
            continue
            
        # Sort by t-stat strength
        df_sym_corr['abs_t'] = df_sym_corr['spearman_t'].abs()
        df_sym_corr = df_sym_corr.sort_values('abs_t', ascending=False)
        
        print(f"Processing {symbol}: found {len(df_sym_corr)} related factors (|t| >= 1.0)")
        
        # We will build a wide DataFrame for this symbol
        df_sym_wide = df_price[['open', 'high', 'low', 'close', 'volume', 'returns']].copy()
        
        # Tracking lists for composite release flags
        all_effective_releases = [] # For factors with |t| >= 1.96
        pmi_ag_releases = [] # For PMIs effective on AG
        pmi_ag_signals = []
        
        for _, row in df_sym_corr.iterrows():
            factor_name = row['factor']
            rep = row['representation']
            t_stat = row['spearman_t']
            p_val = row['spearman_p']
            corr = row['spearman_corr']
            
            clean_f_name = get_clean_name(factor_name)
            col_name_val = f"fac_{clean_f_name}_{rep}"
            col_name_rel = f"fac_{clean_f_name}_{rep}_release"
            
            filename = re.sub(r'[\\/*?:"<>|]', '_', factor_name) + ".parquet"
            factor_path = os.path.join(macro_dir, filename)
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
            
            # Compute signal based on representation
            # Shift by 1 calendar day to prevent look-ahead bias
            if rep == 'level':
                val_daily = df_fac['value'].reindex(all_dates).ffill().shift(1)
                sig_series = val_daily.reindex(trading_dates)
            elif rep == 'diff':
                fac_diff = df_fac['value'].diff()
                diff_daily = fac_diff.reindex(all_dates).ffill().shift(1)
                sig_series = diff_daily.reindex(trading_dates)
            elif rep == 'zscore':
                val_daily = df_fac['value'].reindex(all_dates).ffill().shift(1)
                s_level = val_daily.reindex(trading_dates)
                sig_series = (s_level - s_level.rolling(252).mean()) / s_level.rolling(252).std()
            else:
                continue
                
            # Release flag: 1 on the first trading day strictly after info_date
            pos = np.searchsorted(trading_dates, df_fac.index, side='right')
            valid_mask = pos < len(trading_dates)
            release_dates = trading_dates[pos[valid_mask]].unique()
            
            rel_series = pd.Series(0, index=trading_dates)
            rel_series.loc[release_dates] = 1
            
            # Save into wide DataFrame
            df_sym_wide[col_name_val] = sig_series.astype(np.float32)
            df_sym_wide[col_name_rel] = rel_series.astype(np.int8)
            
            # Check if statistically effective (|t| >= 1.96)
            is_effective = abs(t_stat) >= 1.96
            if is_effective:
                all_effective_releases.append(rel_series)
                
            # User example: PMI effective on AG
            if symbol == 'AG' and 'PMI' in factor_name and is_effective:
                pmi_ag_releases.append(rel_series)
                # Compute signed signal: value * sign of correlation
                sign = 1 if corr > 0 else -1
                signed_sig = sig_series * sign
                pmi_ag_signals.append(signed_sig)
                
            # Collect for long-format panel DataFrame
            # For efficiency, only save non-NaN values
            valid_idx = sig_series.notna()
            if valid_idx.any():
                df_long_part = pd.DataFrame({
                    'symbol': symbol,
                    'factor': clean_f_name,
                    'representation': rep,
                    'close': df_price.loc[valid_idx, 'close'].values,
                    'returns': df_price.loc[valid_idx, 'returns'].values,
                    'factor_value': sig_series[valid_idx].values,
                    'release_flag': rel_series[valid_idx].values,
                    'spearman_t': t_stat,
                    'spearman_p': p_val,
                    'is_effective': int(is_effective)
                }, index=trading_dates[valid_idx])
                long_rows.append(df_long_part)
                
        # Compute and add composite flags to wide DataFrame
        if all_effective_releases:
            # Union of release dates: 1 if any effective factor was released
            effective_release_union = pd.concat(all_effective_releases, axis=1).max(axis=1)
            df_sym_wide['any_effective_release'] = effective_release_union.astype(np.int8)
        else:
            df_sym_wide['any_effective_release'] = 0
            
        # Special AG PMI markings
        if symbol == 'AG':
            if pmi_ag_releases:
                ag_pmi_rel = pd.concat(pmi_ag_releases, axis=1).max(axis=1)
                df_sym_wide['ag_effective_pmi_release'] = ag_pmi_rel.astype(np.int8)
            else:
                df_sym_wide['ag_effective_pmi_release'] = 0
                
            if pmi_ag_signals:
                # Average of the signed signals
                ag_pmi_sig = pd.concat(pmi_ag_signals, axis=1).mean(axis=1)
                # Clean up NaNs
                df_sym_wide['ag_effective_pmi_signal_composite'] = ag_pmi_sig.ffill().fillna(0.0).astype(np.float32)
            else:
                df_sym_wide['ag_effective_pmi_signal_composite'] = 0.0
                
        # Save symbol wide CSV
        wide_csv_path = os.path.join(output_dir, f"{symbol}_aligned.csv")
        df_sym_wide.to_csv(wide_csv_path)
        
        # Save special AG CSV directly in results directory
        if symbol == 'AG':
            ag_csv_path = os.path.join(results_dir, "macro_price_aligned_ag.csv")
            df_sym_wide.to_csv(ag_csv_path)
            print(f"  Saved special AG wide CSV to: {ag_csv_path}")
            
    # Combine long rows and save as parquet
    if long_rows:
        df_long_all = pd.concat(long_rows)
        df_long_all.index.name = 'date'
        df_long_all = df_long_all.reset_index()
        # Set MultiIndex [date, symbol, factor, representation]
        df_long_all = df_long_all.set_index(['date', 'symbol', 'factor', 'representation']).sort_index()
        
        parquet_path = os.path.join(results_dir, "macro_price_aligned.parquet")
        df_long_all.to_parquet(parquet_path, compression='snappy')
        print(f"Saved merged long-format panel DataFrame ({len(df_long_all)} rows) to: {parquet_path}")
    else:
        print("Warning: No long rows created.")
        
    print("Pipeline completed successfully!")

if __name__ == '__main__':
    main()
