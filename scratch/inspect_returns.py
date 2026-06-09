import os
import pandas as pd
import numpy as np
import sys
sys.path.append(os.path.abspath('.'))

from alphas import compute_alphas
from evaluate_alpha import evaluate_alpha

DATA_DIR = 'data/dominant_daily'
SPOT_DIR = 'data/spot_basis'
SYMBOLS = ['C', 'M', 'Y', 'P', 'V', 'J', 'JD', 'I', 'CU', 'AL', 'AU', 'AG', 'RB', 'RU', 'NI', 'SN', 'SC', 'CF', 'SR', 'TA', 'MA', 'SA', 'TF']

df_data = compute_alphas(DATA_DIR, SPOT_DIR, SYMBOLS)

# Clean returns of infinity or NaN values and clip to [-0.1, 0.1]
df_data["returns"] = df_data["returns"].replace([np.inf, -np.inf], np.nan).fillna(0.0)
df_data["returns"] = df_data["returns"].clip(-0.1, 0.1)

for alpha in ['HTFC_Alpha1_meanclose12', 'EWMA_32_64_CTA', 'ForeignAg_LeadLag']:
    col = 'Alt_Macro_Alpha' if alpha in ['Alt_Macro_Alpha_XS', 'Alt_Macro_Alpha_TS'] else alpha
    is_ts = (alpha == 'Alt_Macro_Alpha_TS')
    metrics = evaluate_alpha(df_data, col, all_sharpes=[0.0], N=9, tc_rate=0.0005, demean=not is_ts)
    print(f"--- {alpha} ---")
    print("Sharpe:", metrics.get("sharpe_ratio"))
    print("Ann Return:", metrics.get("annualized_return"))
    print("Ann Vol:", metrics.get("annualized_vol"))
    
    # Let's inspect port_net_returns
    p_ret = metrics.get("port_net_returns")
    if p_ret is not None:
        print("Net returns stats:")
        print("Count:", len(p_ret))
        print("Nulls:", p_ret.isna().sum())
        print("Min:", p_ret.min())
        print("Max:", p_ret.max())
        print("Mean:", p_ret.mean())
        print("Max Drawdown:", metrics.get("max_drawdown"))
