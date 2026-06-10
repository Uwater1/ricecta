#!/usr/bin/env python3
"""
Generates high-quality charts for commodity prices with look-ahead-free macro factor
release dates plotted directly as colored points on the price line.
Green indicates a positive factor change/surprise, Red indicates negative.
All text is strictly in English to prevent tofu character rendering issues.
"""
import os
import re
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import warnings

warnings.filterwarnings('ignore')

_POS_LIGHT = np.array(mcolors.to_rgb('#81e6d9'))
_POS_DARK = np.array(mcolors.to_rgb('#234e52'))
_NEG_LIGHT = np.array(mcolors.to_rgb('#feb2b2'))
_NEG_DARK = np.array(mcolors.to_rgb('#742a2a'))

def _magnitude_to_sizes(magnitudes):
    if len(magnitudes) == 0:
        return np.array([])
    if len(magnitudes) == 1:
        return np.array([100])
    p33 = magnitudes.quantile(0.33)
    p66 = magnitudes.quantile(0.66)
    p90 = magnitudes.quantile(0.90)
    bins = [0, p33, p66, p90, np.inf]
    labels = [50, 100, 160, 220]
    return np.array([labels[i] for i in np.digitize(magnitudes.values, bins[1:])])

def _magnitude_to_colors(magnitudes, direction='positive'):
    if len(magnitudes) == 0:
        return []
    light, dark = (_POS_LIGHT, _POS_DARK) if direction == 'positive' else (_NEG_LIGHT, _NEG_DARK)
    m_range = magnitudes.max() - magnitudes.min()
    t = np.full(len(magnitudes), 0.5) if m_range < 1e-9 else (magnitudes - magnitudes.min()) / m_range
    return [mcolors.to_hex(light * (1 - ti) + dark * ti) for ti in t]

# Exact display name map matching build_macro_price_df.py for alignment
FACTOR_DISPLAY_NAMES = {
    '非制造业PMI_建筑业_业务活动预期_全国_当期值_月': 'Non_Mfg_PMI_Constr_Expectation',
    'PPI_石油加工、炼焦及核燃料加工业(全国:当期同比增长率:月)': 'PPI_Petroleum_Coking_Nuclear_YoY',
    '社会融资规模_当月值': 'Social_Financing_Monthly',
    '制造业采购经理指数PMI_原材料库存': 'PMI_Raw_Material_Inventory',
    'PPIRM_农副产品类(全国:当期同比增长率:月)': 'PPIRM_Agri_Products_YoY',
    'PPI_皮革、毛皮、羽毛及其制品和制鞋业(全国:当期同比增长率:月)': 'PPI_Leather_Footwear_YoY',
    '国内生产总值GDP(现价)_全国_当期同比增长率_季': 'Nominal_GDP_YoY',
    '国内生产总值GDP_累计同比': 'GDP_Cumulative_YoY',
    'PPI_电气机械及器材制造业(全国:当期同比增长率:月)': 'PPI_Electrical_Machinery_YoY',
    '制造业采购经理指数PMI_购进价格': 'PMI_Input_Price',
    '制造业采购经理指数PMI_进口': 'PMI_Import',
    '居民鲜果消费价格指数CPI_(上年=100)_当月': 'CPI_Fresh_Fruit_YoY',
    'PPIRM_燃料及动力类(全国:当期同比增长率:月)': 'PPIRM_Fuel_Power_YoY',
    'PMI_生产经营活动预期_全国_当期值_月': 'PMI_Business_Expectation',
    'PPI_通信设备、计算机及其他电子设备制造业工业品出厂价格指数PPI_(上年=100)_当月': 'PPI_Telecom_Electronics_YoY',
    '制造业采购经理指数PMI_新出口订单': 'PMI_New_Export_Orders',
    'PPI_全部工业品(全国:当期同比增长率:月)': 'PPI_All_Industry_YoY',
}

def get_clean_name(factor_name):
    display = FACTOR_DISPLAY_NAMES.get(factor_name, factor_name)
    # Remove Chinese characters
    display = re.sub(r'[\u4e00-\u9fff]', '', display)
    # Replace non-alphanumeric characters with underscore
    clean = re.sub(r'[\\/*?:"<>|(),：\s-]', '_', display).strip('_')
    # Replace contiguous underscores
    clean = re.sub(r'_{2,}', '_', clean)
    if not clean:
        clean = "Macro_Factor"
    return clean

def get_nice_display_name(factor_name):
    clean = get_clean_name(factor_name)
    # Replace underscores with spaces for premium look on charts
    return clean.replace('_', ' ')

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
        
    # Strictly English names to avoid Tofu rendering in Matplotlib
    symbol_names = {
        'C': 'Corn', 'M': 'Soymeal', 'Y': 'Soyoil', 'P': 'Palm Oil',
        'V': 'PVC', 'J': 'Coke', 'JD': 'Eggs', 'I': 'Iron Ore',
        'CU': 'Copper', 'AL': 'Aluminum', 'AU': 'Gold', 'AG': 'Silver',
        'RB': 'Rebar', 'RU': 'Rubber', 'NI': 'Nickel', 'SN': 'Tin',
        'SC': 'Crude Oil', 'CF': 'Cotton', 'SR': 'Sugar', 'TA': 'PTA',
        'MA': 'Methanol', 'SA': 'Soda Ash', 'TF': '5Y Treasury Bond'
    }
    
    print("Generating price & macro overlay plots...")
    
    for symbol, cfg in best_configs.items():
        csv_path = os.path.join(aligned_dir, f"{symbol}_aligned.csv")
        if not os.path.exists(csv_path):
            print(f"Warning: {csv_path} not found.")
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
            print(f"Warning: Column {col_val} not in {symbol}_aligned.csv columns. Skipping.")
            continue
            
        # Get active slices
        df_sub = df[[ 'close', col_val, col_rel ]].dropna(subset=['close'])
        if df_sub.empty:
            continue
            
        # Setup modern dark/light style
        plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
        fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
        
        ax.plot(df_sub.index, df_sub['close'], color='#2b6cb0', linewidth=2.0,
                alpha=0.95, zorder=3)
        ax.fill_between(df_sub.index, df_sub['close'], color='#2b6cb0', alpha=0.01)

        releases = df_sub[df_sub[col_rel] == 1].copy()

        if rep == 'diff':
            releases['magnitude'] = (releases[col_val] * sign).abs()
            pos_releases = releases[releases[col_val] * sign > 0].copy()
            neg_releases = releases[releases[col_val] * sign < 0].copy()
            neutral_releases = releases[releases[col_val] == 0].copy()
        else:
            prev_vals = df_sub[col_val].shift(1)
            releases['prev_val'] = prev_vals.loc[releases.index]
            releases['change'] = (releases[col_val] - releases['prev_val']).fillna(0)
            releases['magnitude'] = (releases['change'] * sign).abs()
            pos_releases = releases[releases['change'] * sign > 0].copy()
            neg_releases = releases[releases['change'] * sign < 0].copy()
            neutral_releases = releases[releases['change'] * sign == 0].copy()

        for dt in pos_releases.index:
            ax.axvline(x=dt, color='#319795', alpha=0.18, linewidth=0.8, zorder=2)
        for dt in neg_releases.index:
            ax.axvline(x=dt, color='#e53e3e', alpha=0.18, linewidth=0.8, zorder=2)
        for dt in neutral_releases.index:
            ax.axvline(x=dt, color='#718096', alpha=0.12, linewidth=0.5, zorder=2)

        price_range = df_sub['close'].max() - df_sub['close'].min()
        y_offset = price_range * 0.05

        legend_handles = []
        legend_handles.append(plt.Line2D([0], [0], color='#2b6cb0', linewidth=2.0,
            label='Spliced Close Price'))

        if not pos_releases.empty:
            sizes = _magnitude_to_sizes(pos_releases['magnitude'])
            colors = _magnitude_to_colors(pos_releases['magnitude'], 'positive')
            ax.scatter(pos_releases.index, pos_releases['close'] + y_offset, c=colors, marker='^',
                       s=sizes, zorder=5, edgecolors='black', linewidths=0.3)
            legend_handles.append(plt.Line2D([0], [0], marker='^', color='w',
                markerfacecolor='#234e52', markersize=10, label='Positive (Large)'))
            legend_handles.append(plt.Line2D([0], [0], marker='^', color='w',
                markerfacecolor='#81e6d9', markersize=7, label='Positive (Small)'))

        if not neg_releases.empty:
            sizes = _magnitude_to_sizes(neg_releases['magnitude'])
            colors = _magnitude_to_colors(neg_releases['magnitude'], 'negative')
            ax.scatter(neg_releases.index, neg_releases['close'] - y_offset, c=colors, marker='v',
                       s=sizes, zorder=5, edgecolors='black', linewidths=0.3)
            legend_handles.append(plt.Line2D([0], [0], marker='v', color='w',
                markerfacecolor='#742a2a', markersize=10, label='Negative (Large)'))
            legend_handles.append(plt.Line2D([0], [0], marker='v', color='w',
                markerfacecolor='#feb2b2', markersize=7, label='Negative (Small)'))

        if not neutral_releases.empty:
            ax.scatter(neutral_releases.index, neutral_releases['close'] + y_offset, color='#718096',
                       marker='o', s=20, zorder=4, edgecolors='black', linewidths=0.3)
            legend_handles.append(plt.Line2D([0], [0], marker='o', color='w',
                markerfacecolor='#718096', markersize=5, label='Neutral'))

        legend_handles.append(plt.Line2D([0], [0], color='#319795', alpha=0.5,
            linewidth=2, label='Positive release line'))
        legend_handles.append(plt.Line2D([0], [0], color='#e53e3e', alpha=0.5,
            linewidth=2, label='Negative release line'))

        title_name = symbol_names.get(symbol, symbol)
        nice_factor = get_nice_display_name(factor_name)

        ax.set_title(f"{title_name} Price & {nice_factor} ({rep.upper()}) Releases\n"
                     f"(Look-ahead-free Aligned Release Points, 2016-2026)",
                     fontsize=13, fontweight='bold', pad=15, color='#2d3748')

        ax.set_xlabel("Date", fontsize=10, labelpad=8, color='#4a5568')
        ax.set_ylabel(f"Close Price ({symbol})", fontsize=10, labelpad=8, color='#4a5568')
        ax.legend(handles=legend_handles, loc='upper left', frameon=True,
                  facecolor='white', edgecolor='#e2e8f0', fontsize=8)
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.tick_params(axis='both', colors='#4a5568', labelsize=9)

        y_min = df_sub['close'].min()
        y_max = df_sub['close'].max()
        y_pad = (y_max - y_min) * 0.08
        ax.set_ylim(y_min - y_pad, y_max + y_pad)
        
        # Optimize margins
        plt.tight_layout()
        
        # Save figure
        plot_path = os.path.join(figures_dir, f"macro_price_{symbol}.png")
        plt.savefig(plot_path, dpi=300)
        plt.close()
        
    print("Succeeded in generating and saving overlay plots to the figures/ folder.")

if __name__ == '__main__':
    main()
