#!/usr/bin/env python3
import os
import re
import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)

# Load files
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

# Parse old descriptions
symbol_desc = {}
if os.path.exists(MD_PATH):
    with open(MD_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.search(r'\|\s*\d+\s*\|\s*\*\*([^*]+)\*\*\s*\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|\s*([^|]+)\s*\|', line)
            if m:
                sym = m.group(1).strip()
                desc = m.group(2).strip()
                symbol_desc[sym] = desc

# Load CSV data
df_5 = pd.read_csv(os.path.join(RESULTS_DIR, 'best_factors_summary.csv'))
df_5['abs_spearman_t'] = df_5['spearman_t'].abs()
df_5_sorted = df_5.sort_values('abs_spearman_t', ascending=False)

df_20 = pd.read_csv(os.path.join(RESULTS_DIR, 'best_factors_f20_summary.csv'))
df_20['abs_spearman_t'] = df_20['spearman_t'].abs()
df_20_sorted = df_20.sort_values('abs_spearman_t', ascending=False)

df_30 = pd.read_csv(os.path.join(RESULTS_DIR, 'best_factors_f30_summary.csv'))
df_30['abs_spearman_t'] = df_30['spearman_t'].abs()
df_30_sorted = df_30.sort_values('abs_spearman_t', ascending=False)

df_40 = pd.read_csv(os.path.join(RESULTS_DIR, 'best_factors_f40_summary.csv'))
df_40['abs_spearman_t'] = df_40['spearman_t'].abs()
df_40_sorted = df_40.sort_values('abs_spearman_t', ascending=False)

df_top3_f5 = pd.read_csv(os.path.join(RESULTS_DIR, 'top3_factors_f5_summary.csv'))
df_top3_f20 = pd.read_csv(os.path.join(RESULTS_DIR, 'top3_factors_f20_summary.csv'))

# Generate markdown content
md = []
md.append("# Alternative Data Alphas for Futures (Look-Ahead Free)")
md.append("")
md.append("This document evaluates the effectiveness of alternative macroeconomic factors for the 23 futures underlyings, utilizing a **look-ahead free** alignment methodology (shifting release times by 1 calendar day to prevent intraday look-ahead bias).")
md.append("")
md.append("## Methodology Update: Look-Ahead Prevention")
md.append("Previously, macroeconomic factors (such as Social Financing or Money Supply) released by the PBOC or NBS on day $T$ were aligned to trading day $T$. However, many of these indicators are published after market close (e.g. 5:00 PM). Trading them at the 3:00 PM close of day $T$ introduced look-ahead bias. We now shift all macro daily series by 1 calendar day (`.shift(1)`), ensuring they are only traded on day $T+1$ when they are guaranteed to be public.")
md.append("")
md.append("## Performance Summary Table (20-Day Horizon) — PRIMARY")
md.append("")
md.append("This configuration is active in the Alpha Library (`alphas.py`).")
md.append("")
md.append("| Rank | Symbol | Best Factor | Signal Type | Spearman Corr (20d) | t-statistic | p-value | Description |")
md.append("|---|---|---|---|---|---|---|---|")

rank = 1
for idx, row in df_20_sorted.iterrows():
    sym = row['symbol']
    desc = symbol_desc.get(sym, 'Macro connection')
    md.append(f"| {rank} | **{sym}** | `{row['factor']}` | *{row['representation']}* | {row['spearman_corr']:.4f} | {row['spearman_t']:.2f} | {row['spearman_p']:.2e} | {desc} |")
    rank += 1

md.append("")
md.append("## Performance Summary Table (5-Day Horizon)")
md.append("")
md.append("| Rank | Symbol | Best Factor | Signal Type | Spearman Corr (5d) | t-statistic | p-value | Description |")
md.append("|---|---|---|---|---|---|---|---|")

rank = 1
for idx, row in df_5_sorted.iterrows():
    sym = row['symbol']
    desc = symbol_desc.get(sym, 'Macro connection')
    md.append(f"| {rank} | **{sym}** | `{row['factor']}` | *{row['representation']}* | {row['spearman_corr']:.4f} | {row['spearman_t']:.2f} | {row['spearman_p']:.2e} | {desc} |")
    rank += 1

md.append("")
md.append("## Long-Term Macroeconomic Effects (30-Day and 40-Day Horizons)")
md.append("Macroeconomic forces are structural and influence pricing over longer term horizons. Extending the correlation test to 30d and 40d reveals significantly larger correlations and t-statistics across almost all symbols.")
md.append("")
md.append("### 30-Day Horizon Best Factors")
md.append("")
md.append("| Rank | Symbol | Best Factor | Signal Type | Spearman Corr (30d) | t-statistic |")
md.append("|---|---|---|---|---|---|")
rank = 1
for idx, row in df_30_sorted.iterrows():
    md.append(f"| {rank} | **{row['symbol']}** | `{row['factor']}` | *{row['representation']}* | {row['spearman_corr']:.4f} | {row['spearman_t']:.2f} |")
    rank += 1

md.append("")
md.append("### 40-Day Horizon Best Factors")
md.append("")
md.append("| Rank | Symbol | Best Factor | Signal Type | Spearman Corr (40d) | t-statistic |")
md.append("|---|---|---|---|---|---|")
rank = 1
for idx, row in df_40_sorted.iterrows():
    md.append(f"| {rank} | **{row['symbol']}** | `{row['factor']}` | *{row['representation']}* | {row['spearman_corr']:.4f} | {row['spearman_t']:.2f} |")
    rank += 1

md.append("")
md.append("## Top 3 Alternative Alphas per Symbol (20-Day Horizon)")
md.append("To allow multiple factor testing at the 20-day horizon, the top 3 alternative factor configurations for each symbol ranked by absolute Spearman t-statistic are listed below. The files are saved in `data/results/top3_factors_f20_summary.csv`.")
md.append("")
md.append("| Symbol | Rank | Alternative Factor | Representation | Spearman Corr | t-statistic |")
md.append("|---|---|---|---|---|---|")
for sym in sorted(df_top3_f20['symbol'].unique()):
    df_sym = df_top3_f20[df_top3_f20['symbol'] == sym].sort_values('abs_spearman_t', ascending=False)
    sub_rank = 1
    for idx, row in df_sym.iterrows():
        md.append(f"| **{sym}** | {sub_rank} | `{row['factor']}` | *{row['representation']}* | {row['spearman_corr']:.4f} | {row['spearman_t']:.2f} |")
        sub_rank += 1

md.append("")
md.append("## Top 3 Alternative Alphas per Symbol (5-Day Horizon)")
md.append("The 5-day horizon alternative configurations for reference. Saved in `data/results/top3_factors_f5_summary.csv`.")
md.append("")
md.append("| Symbol | Rank | Alternative Factor | Representation | Spearman Corr | t-statistic |")
md.append("|---|---|---|---|---|---|")
for sym in sorted(df_top3_f5['symbol'].unique()):
    df_sym = df_top3_f5[df_top3_f5['symbol'] == sym].sort_values('abs_spearman_t', ascending=False)
    sub_rank = 1
    for idx, row in df_sym.iterrows():
        md.append(f"| **{sym}** | {sub_rank} | `{row['factor']}` | *{row['representation']}* | {row['spearman_corr']:.4f} | {row['spearman_t']:.2f} |")
        sub_rank += 1

md.append("")
md.append("## Commodity Specific Details (Sorted by Significance for 20-Day Horizon)")
md.append("")

rank = 1
for idx, row in df_20_sorted.iterrows():
    sym = row['symbol']
    exchange = EXCHANGE_MAPPING.get(sym, 'DCE')
    desc = symbol_desc.get(sym, 'Macro connection')
    sign_str = "Positive (Long when factor increases)" if row['spearman_corr'] >= 0 else "Negative (Short when factor increases)"
    
    md.append(f"### {rank}. 品种: {sym} ({exchange})")
    md.append("")
    md.append(f"* **Selected Factor**: `{row['factor']}`")
    md.append(f"* **Signal Representation**: `{row['representation']}`")
    md.append(f"* **Description**: {desc}")
    md.append(f"* **Effectiveness Metrics (20-day horizon)**:")
    md.append(f"  * Spearman Correlation: `{row['spearman_corr']:.4f}`")
    md.append(f"  * t-statistic: `{row['spearman_t']:.2f}`")
    md.append(f"  * p-value: `{row['spearman_p']:.2e}`")
    md.append(f"  * Correlation Sign: `{sign_str}`")
    md.append("")
    md.append("---")
    md.append("")
    rank += 1

# Write to file
with open(MD_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(md))

print(f"Successfully generated look-ahead free {MD_PATH}")
