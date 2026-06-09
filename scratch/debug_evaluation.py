import os
import pandas as pd
import numpy as np

# Load the data and look at the index
from alphas import compute_alphas

DATA_DIR = 'data/dominant_daily'
SPOT_DIR = 'data/spot_basis'
SYMBOLS = ['C', 'M', 'Y', 'P', 'V', 'J', 'JD', 'I', 'CU', 'AL', 'AU', 'AG', 'RB', 'RU', 'NI', 'SN', 'SC', 'CF', 'SR', 'TA', 'MA', 'SA', 'TF']

df_data = compute_alphas(DATA_DIR, SPOT_DIR, SYMBOLS)
print("Data Date range:", df_data.index.levels[0].min(), "to", df_data.index.levels[0].max())

for col in df_data.columns:
    if col.startswith("HTFC_") or col.startswith("EWMA_") or col.startswith("Kalman") or col.startswith("Foreign") or col.startswith("Alt_"):
        non_nan_total = df_data[col].notna().sum()
        non_nan_before_2021 = df_data.loc[:'2020-12-31', col].notna().sum()
        non_nan_after_2021 = df_data.loc['2021-01-01':, col].notna().sum()
        print(f"{col}: total={non_nan_total}, before 2021={non_nan_before_2021}, after 2021={non_nan_after_2021}")
