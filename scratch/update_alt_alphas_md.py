#!/usr/bin/env python3
import os
import re
import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)

MD_PATH = os.path.join(_PROJECT_DIR, 'alt_alphas.md')
RESULTS_DIR = os.path.join(_PROJECT_DIR, 'data', 'results')

EXCHANGE_MAPPING = {
    'C': 'DCE (大商所)', 'M': 'DCE (大商所)', 'Y': 'DCE (大商所)', 'P': 'DCE (大商所)',
    'V': 'DCE (大商所)', 'J': 'DCE (大商所)', 'JD': 'DCE (大商所)', 'I': 'DCE (大商所)',
    'CU': 'SHFE (上期所)', 'AL': 'SHFE (上期所)', 'AU': 'SHFE (上期所)', 'AG': 'SHFE (上期所)',
    'RB': 'SHFE (上期所)', 'RU': 'SHFE (上期所)', 'NI': 'SHFE (上期所)', 'SN': 'SHFE (上期所)',
    'SC': 'INE (能源中心)',
    'CF': 'CZCE (郑商所)', 'SR': 'CZCE (郑商所)', 'TA': 'CZCE (郑商所)', 'MA': 'CZCE (郑商所)',
    'SA': 'CZCE (郑商所)',
    'TF': 'CFFEX (中金所)'
}

# Load CSV data
df_5d = pd.read_csv(os.path.join(RESULTS_DIR, 'best_factors_5d_summary.csv'))
df_5d['abs_spearman_t'] = df_5d['spearman_t'].abs()
df_5d_sorted = df_5d.sort_values('abs_spearman_t', ascending=False)

df_20d = pd.read_csv(os.path.join(RESULTS_DIR, 'best_factors_20d_summary.csv'))
df_20d['abs_spearman_t'] = df_20d['spearman_t'].abs()
df_20d_sorted = df_20d.sort_values('abs_spearman_t', ascending=False)

df_h1 = pd.read_csv(os.path.join(RESULTS_DIR, 'best_factors_H1_summary.csv'))
df_h1['abs_spearman_t'] = df_h1['spearman_t'].abs()
df_h1_sorted = df_h1.sort_values('abs_spearman_t', ascending=False)

df_h2 = pd.read_csv(os.path.join(RESULTS_DIR, 'best_factors_H2_summary.csv'))
df_h2['abs_spearman_t'] = df_h2['spearman_t'].abs()
df_h2_sorted = df_h2.sort_values('abs_spearman_t', ascending=False)

df_h3 = pd.read_csv(os.path.join(RESULTS_DIR, 'best_factors_H3_summary.csv'))
df_h3['abs_spearman_t'] = df_h3['spearman_t'].abs()
df_h3_sorted = df_h3.sort_values('abs_spearman_t', ascending=False)

df_top3_5d = pd.read_csv(os.path.join(RESULTS_DIR, 'top3_factors_5d_summary.csv'))
df_top3_20d = pd.read_csv(os.path.join(RESULTS_DIR, 'top3_factors_20d_summary.csv'))

# Generate markdown content
md = []
md.append("# Alternative Data Alphas for Futures (Release-Date-Only Correlation)")
md.append("")
md.append("This document evaluates the effectiveness of alternative macroeconomic factors for the 23 futures underlyings, utilizing a **look-ahead free** alignment methodology and **release-date-only sampling** (only sampling the first trading day after each data release to avoid autocorrelation bias).")
md.append("")
md.append("## Methodology Update: Release-Date-Only Correlation & Soundness Checks")
md.append("Previously, macroeconomic factors were aligned to daily trading returns, leading to artificial t-statistic inflation due to autocorrelation (since monthly macro data remains static for 20+ trading days). We now only sample returns and signals on the first trading day after each release (`info_date`).")
md.append("")
md.append("To ensure statistical soundness, we also implement two checks:")
md.append("1. **Temporal Consistency (Split-sample check)**: The release-aligned data is split into first and second halves. The Spearman correlation is calculated on both sub-periods. A factor is temporally consistent if the correlation sign does not flip between the two sub-periods.")
md.append("2. **Horizon sign-consistency**: We verify if the correlation has the same sign across different horizons (specifically `5d` vs `20d`). If the sign flips, the correlation may be spurious.")
md.append("")
md.append("## Performance Summary Table (20-Day Horizon) — PRIMARY")
md.append("")
md.append("| Rank | Symbol | Best Factor | Signal Type | Spearman Corr | t-statistic | p-value | Temp. Consistent | Horiz. Consistent |")
md.append("|---|---|---|---|---|---|---|---|---|")

rank = 1
for idx, row in df_20d_sorted.iterrows():
    sym = row['symbol']
    temp_const = "Yes" if row['temporal_consistent'] else "No"
    horiz_const = "Yes" if row['horizon_consistent_5d_20d'] else "No"
    md.append(f"| {rank} | **{sym}** | `{row['factor']}` | *{row['representation']}* | {row['spearman_corr']:.4f} | {row['spearman_t']:.2f} | {row['spearman_p']:.2e} | {temp_const} | {horiz_const} |")
    rank += 1

md.append("")
md.append("## Performance Summary Table (5-Day Horizon)")
md.append("")
md.append("| Rank | Symbol | Best Factor | Signal Type | Spearman Corr | t-statistic | p-value | Temp. Consistent | Horiz. Consistent |")
md.append("|---|---|---|---|---|---|---|---|---|")

rank = 1
for idx, row in df_5d_sorted.iterrows():
    sym = row['symbol']
    temp_const = "Yes" if row['temporal_consistent'] else "No"
    horiz_const = "Yes" if row['horizon_consistent_5d_20d'] else "No"
    md.append(f"| {rank} | **{sym}** | `{row['factor']}` | *{row['representation']}* | {row['spearman_corr']:.4f} | {row['spearman_t']:.2f} | {row['spearman_p']:.2e} | {temp_const} | {horiz_const} |")
    rank += 1

md.append("")
md.append("## Long-Term Macroeconomic Effects (Contract-Switch Horizons)")
md.append("Macroeconomic forces are structural and influence pricing over longer term horizons. The contract-switch horizons (H1, H2, H3) capture these effects aligned to each symbol's natural dominant contract transition pattern.")
md.append("")
md.append("### 1st Switch Horizon Best Factors")
md.append("")
md.append("| Rank | Symbol | Best Factor | Signal Type | Spearman Corr | t-statistic | Temp. Consistent |")
md.append("|---|---|---|---|---|---|---|")
rank = 1
for idx, row in df_h1_sorted.iterrows():
    temp_const = "Yes" if row['temporal_consistent'] else "No"
    md.append(f"| {rank} | **{row['symbol']}** | `{row['factor']}` | *{row['representation']}* | {row['spearman_corr']:.4f} | {row['spearman_t']:.2f} | {temp_const} |")
    rank += 1

md.append("")
md.append("### 2nd Switch Horizon Best Factors")
md.append("")
md.append("| Rank | Symbol | Best Factor | Signal Type | Spearman Corr | t-statistic | Temp. Consistent |")
md.append("|---|---|---|---|---|---|---|")
rank = 1
for idx, row in df_h2_sorted.iterrows():
    temp_const = "Yes" if row['temporal_consistent'] else "No"
    md.append(f"| {rank} | **{row['symbol']}** | `{row['factor']}` | *{row['representation']}* | {row['spearman_corr']:.4f} | {row['spearman_t']:.2f} | {temp_const} |")
    rank += 1

md.append("")
md.append("### 3rd Switch Horizon Best Factors")
md.append("")
md.append("| Rank | Symbol | Best Factor | Signal Type | Spearman Corr | t-statistic | Temp. Consistent |")
md.append("|---|---|---|---|---|---|---|")
rank = 1
for idx, row in df_h3_sorted.iterrows():
    temp_const = "Yes" if row['temporal_consistent'] else "No"
    md.append(f"| {rank} | **{row['symbol']}** | `{row['factor']}` | *{row['representation']}* | {row['spearman_corr']:.4f} | {row['spearman_t']:.2f} | {temp_const} |")
    rank += 1

md.append("")
md.append("## Top 3 Alternative Alphas per Symbol (20-Day Horizon)")
md.append("To allow multiple factor testing, the top 3 alternative factor configurations for each symbol ranked by absolute Spearman t-statistic are listed below.")
md.append("")
md.append("| Symbol | Rank | Alternative Factor | Representation | Spearman Corr | t-statistic | Temp. Consistent | Horiz. Consistent |")
md.append("|---|---|---|---|---|---|---|---|")
for sym in sorted(df_top3_20d['symbol'].unique()):
    df_sym = df_top3_20d[df_top3_20d['symbol'] == sym].sort_values('abs_spearman_t', ascending=False)
    sub_rank = 1
    for idx, row in df_sym.iterrows():
        temp_const = "Yes" if row['temporal_consistent'] else "No"
        horiz_const = "Yes" if row['horizon_consistent_5d_20d'] else "No"
        md.append(f"| **{sym}** | {sub_rank} | `{row['factor']}` | *{row['representation']}* | {row['spearman_corr']:.4f} | {row['spearman_t']:.2f} | {temp_const} | {horiz_const} |")
        sub_rank += 1

md.append("")
md.append("## Top 3 Alternative Alphas per Symbol (5-Day Horizon)")
md.append("")
md.append("| Symbol | Rank | Alternative Factor | Representation | Spearman Corr | t-statistic | Temp. Consistent | Horiz. Consistent |")
md.append("|---|---|---|---|---|---|---|---|")
for sym in sorted(df_top3_5d['symbol'].unique()):
    df_sym = df_top3_5d[df_top3_5d['symbol'] == sym].sort_values('abs_spearman_t', ascending=False)
    sub_rank = 1
    for idx, row in df_sym.iterrows():
        temp_const = "Yes" if row['temporal_consistent'] else "No"
        horiz_const = "Yes" if row['horizon_consistent_5d_20d'] else "No"
        md.append(f"| **{sym}** | {sub_rank} | `{row['factor']}` | *{row['representation']}* | {row['spearman_corr']:.4f} | {row['spearman_t']:.2f} | {temp_const} | {horiz_const} |")
        sub_rank += 1

md.append("")
md.append("## Commodity Specific Details (Sorted by Significance for 20-Day Horizon)")
md.append("")

rank = 1
for idx, row in df_20d_sorted.iterrows():
    sym = row['symbol']
    exchange = EXCHANGE_MAPPING.get(sym, 'DCE')
    sign_str = "Positive (Long when factor increases)" if row['spearman_corr'] >= 0 else "Negative (Short when factor increases)"
    temp_const = "Yes" if row['temporal_consistent'] else "No"
    horiz_const = "Yes" if row['horizon_consistent_5d_20d'] else "No"
    
    md.append(f"### {rank}. 品种: {sym} ({exchange})")
    md.append("")
    md.append(f"* **Selected Factor**: `{row['factor']}`")
    md.append(f"* **Signal Representation**: `{row['representation']}`")
    md.append(f"* **Effectiveness Metrics (20-day horizon)**:")
    md.append(f"  * Spearman Correlation: `{row['spearman_corr']:.4f}`")
    md.append(f"  * t-statistic: `{row['spearman_t']:.2f}`")
    md.append(f"  * p-value: `{row['spearman_p']:.2e}`")
    md.append(f"  * First-half Spearman: `{row['spearman_first_half']:.4f}`")
    md.append(f"  * Second-half Spearman: `{row['spearman_second_half']:.4f}`")
    md.append(f"  * Temporal Consistency: `{temp_const}`")
    md.append(f"  * 5d vs 20d Horizon Consistency: `{horiz_const}`")
    md.append(f"  * Correlation Sign: `{sign_str}`")
    md.append("")
    md.append("---")
    md.append("")
    rank += 1

# Write to file
with open(MD_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(md))

print(f"Successfully generated release-date-only aligned {MD_PATH}")
