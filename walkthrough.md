# Walkthrough: Alt_Macro_Alpha Production Readiness

Production-ready enhancements completed for `Alt_Macro_Alpha` and the backtest evaluation system.

---

## 1. Key Accomplishments

### Splicing Specific Contracts (No Dominant Contract Data)
- Built [contract_splicer.py](file:///home/hallo/data/ricecta/contract_splicer.py) to construct a ratio-adjusted continuous daily price series (including `open`, `high`, `low`, `close`, `volume`, `open_interest`) from individual contracts under `data/contracts_daily/` dynamically.
- Eliminated all usage of `dominant_daily` parquets for all 9 alphas.
- Optimized the daily loop inside the splicer by pre-calculating lists of valid contract IDs per date using binary search, bringing runtimes down to a few milliseconds.
- Stitched series apply backward ratio adjustments at roll dates and deduct a $2 \times 5\text{ bp}$ transaction slippage cost.

### Release-Gated Screening
- Added watermark-based gating in [test_alt_alphas.py](file:///home/hallo/data/ricecta/test_alt_alphas.py) using `data/results/.last_run_state.json`.
- The screening suite checks the maximum `info_date` of all factor parquets against watermarks and skips execution if no updates are detected.
- Added a `--force` flag to run sweeps manually.
- Writes optimal configs to `data/results/best_macro_configs.json`.

### Dynamic Config Loading & Signal Hardening
- Modified [alphas.py](file:///home/hallo/data/ricecta/alphas.py) to dynamically load configurations from `best_macro_configs.json` if available, falling back to a hardcoded dict.
- Added signal winsorization using a rolling 252-day window (look-ahead free) at the 1% and 99% quantiles to limit extreme outliers.
- Added a minimum observation guard: sets the signal to `NaN` if there are fewer than 12 non-NaN factor observations.

### Detailed Trade Logging
- Updated the contract hold engine in [evaluate_hold_strategy.py](file:///home/hallo/data/ricecta/evaluate_hold_strategy.py) to export granular trade metrics to `data/results/trade_log_{symbol}.csv` with `[entry_date, exit_date, contract, direction, p_entry, p_exit, hold_days, raw_return, net_return]`.

### Incremental Data Updater
- Added [download/update_macro_data.py](file:///home/hallo/data/ricecta/download/update_macro_data.py) to incrementally fetch macro factors up to the current date and log new row additions.

---

## 2. Validation & Performance Results

### Release Gate Verification
- First run (gate missing): proceeds and creates `.last_run_state.json`.
- Second run (no new data):
  ```
  No new macro data detected. Skipping run.
  ```

### Portfolio Performance Summary (Net of 5 bp Slippage)
Calculated using the new continuous contract-specific spliced pricing series:

| Alpha Name | Ann. Return | Ann. Vol | Sharpe | Deflated Sharpe (DSR) | Calmar | MaxDD | Sortino | Win Rate |
|---|---|---|---|---|---|---|---|---|
| **Alt_Macro_Alpha_NoRoll** | 2.87% | 2.93% | **0.98** | **69.84%** | **0.52** | **-5.56%** | **1.01** | **52.09%** |
| **Alt_Macro_Alpha_XS** | 7.05% | 7.91% | **0.89** | 59.13% | 0.41 | -17.27% | 0.91 | 52.36% |
| **Alt_Macro_Alpha_TS** | 9.70% | 13.19% | 0.74 | 39.63% | 0.51 | -19.03% | 0.78 | 51.41% |

All metrics match the generated [alpha_evaluation_report.md](file:///home/hallo/data/ricecta/alpha_evaluation_report.md).
Detailed trade logs are successfully stored under `data/results/trade_log_{symbol}.csv`.
`GEMINI.md` has been fully updated.
