#!/usr/bin/env python3
"""
Generates high-quality charts for commodity prices with look-ahead-free macro factor
release dates plotted directly as colored points on the price line.
Green indicates a positive factor change/surprise, Red indicates negative.
"""
import os
import re
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')

# Factor display name map for legend
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
    return FACTOR_DISPLAY_NAMES.get(factor, factor)

def get_clean_name(factor_name):
    # Replace spaces/colons/slashes with underscore
    clean = re.sub(r'[\\/*?:"<>|(),：\s]', '_', factor_name).strip('_')
    clean = re.sub(r'_{2,}', '_', clean)
    return clean

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, 'data', 'results')
    aligned_dir = os.path.join(results_dir, 'aligned_by_symbol')
    figures_dir = os.path.join(script_dir, 'figures')
    os.makedirs(figures_dir, exist_ok=True)
    
    # Load best macro factor configs
    config_path = os.path.join(results_dir, 'best_macro_configs.json')
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Missing config file: {config_path}. Run test_alt_alphas.py first.")
        
    with open(config_path, 'r', encoding='utf-8') as f:
        best_configs = json.load(f)
        
    # Standard translation of symbols to Chinese names
    symbol_names = {
        'C': 'Corn (玉米)', 'M': 'Soymeal (豆粕)', 'Y': 'Soyoil (豆油)', 'P': 'Palm Oil (棕榈油)',
        'V': 'PVC', 'J': 'Coke (焦炭)', 'JD': 'Eggs (鸡蛋)', 'I': 'Iron Ore (铁矿石)',
        'CU': 'Copper (沪铜)', 'AL': 'Aluminum (沪铝)', 'AU': 'Gold (沪金)', 'AG': 'Silver (沪银)',
        'RB': 'Rebar (螺纹钢)', 'RU': 'Rubber (天然橡胶)', 'NI': 'Nickel (沪镍)', 'SN': 'Tin (沪锡)',
        'SC': 'Crude Oil (原油)', 'CF': 'Cotton (棉花)', 'SR': 'Sugar (白糖)', 'TA': 'PTA',
        'MA': 'Methanol (甲醇)', 'SA': 'Soda Ash (纯碱)', 'TF': '5Y Treasury Bond (国债)'
    }
    
    print("Generating price & macro overlay plots...")
    
    for symbol, cfg in best_configs.items():
        csv_path = os.path.join(aligned_dir, f"{symbol}_aligned.csv")
        if not os.path.exists(csv_path):
            continue
            
        # Load aligned daily series
        df = pd.read_csv(csv_path, index_col='date')
        df.index = pd.to_datetime(df.index)
        
        factor_name = cfg['factor']
        rep = cfg['representation']
        sign = cfg['sign']
        
        clean_f_name = get_clean_name(factor_name)
        col_val = f"fac_{clean_f_name}_{rep}"
        col_rel = f"fac_{clean_f_name}_{rep}_release"
        
        if col_val not in df.columns or col_rel not in df.columns:
            continue
            
        # Get active slices
        df_sub = df[[ 'close', col_val, col_rel ]].dropna(subset=['close'])
        if df_sub.empty:
            continue
            
        # Setup modern dark/light style
        plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
        fig, ax = plt.subplots(figsize=(14, 7), dpi=200)
        
        # Plot price line with subtle area shading underneath
        ax.plot(df_sub.index, df_sub['close'], color='#4a90e2', linewidth=2.0, label='Spliced Close Price', alpha=0.9)
        ax.fill_between(df_sub.index, df_sub['close'], color='#4a90e2', alpha=0.08)
        
        # Filter for release points
        releases = df_sub[df_sub[col_rel] == 1]
        
        # Determine surprise direction (positive or negative change/level)
        # For 'diff', positive change is > 0
        # For 'zscore' or 'level', we can check if it is above or below its rolling average, or diff from previous release
        if rep == 'diff':
            pos_releases = releases[releases[col_val] * sign > 0]
            neg_releases = releases[releases[col_val] * sign < 0]
            neutral_releases = releases[releases[col_val] == 0]
        else:
            # Check difference between current release value and previous day (to represent the step change)
            prev_vals = df_sub[col_val].shift(1)
            releases_with_prev = releases.copy()
            releases_with_prev['prev_val'] = prev_vals.loc[releases.index]
            releases_with_prev['change'] = (releases_with_prev[col_val] - releases_with_prev['prev_val']).fillna(0)
            
            pos_releases = releases_with_prev[releases_with_prev['change'] * sign > 0]
            neg_releases = releases_with_prev[releases_with_prev['change'] * sign < 0]
            neutral_releases = releases_with_prev[releases_with_prev['change'] == 0]
            
        # Plot markers directly on the price line
        if not pos_releases.empty:
            ax.scatter(pos_releases.index, pos_releases['close'], color='#2ca02c', marker='^', s=100, 
                       label='Positive Macro Surprise (Long)', zorder=5, edgecolors='black', linewidths=0.5)
        if not neg_releases.empty:
            ax.scatter(neg_releases.index, neg_releases['close'], color='#d62728', marker='v', s=100, 
                       label='Negative Macro Surprise (Short)', zorder=5, edgecolors='black', linewidths=0.5)
        if not neutral_releases.empty:
            ax.scatter(neutral_releases.index, neutral_releases['close'], color='#7f7f7f', marker='o', s=60, 
                       label='Neutral Release', zorder=4, edgecolors='black', linewidths=0.5)
            
        # Format chart
        title_name = symbol_names.get(symbol, symbol)
        display_factor = get_display_name(factor_name)
        
        ax.set_title(f"{title_name} Price & {display_factor} ({rep.capitalize()}) Releases\n(Look-ahead-free Aligned Release Points, 2016-2026)", 
                     fontsize=14, fontweight='bold', pad=15, color='#2c3e50')
        
        ax.set_xlabel("Date", fontsize=11, labelpad=10)
        ax.set_ylabel(f"Close Price ({symbol})", fontsize=11, labelpad=10)
        ax.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#e2e2e2', fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # Optimize margins
        plt.tight_layout()
        
        # Save figure
        plot_path = os.path.join(figures_dir, f"macro_price_{symbol}.png")
        plt.savefig(plot_path, dpi=200)
        plt.close()
        
    print("Succeeded in generating and saving overlay plots to the figures/ folder.")

if __name__ == '__main__':
    main()
