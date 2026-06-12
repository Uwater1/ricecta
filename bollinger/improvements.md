# Bollinger Band CTA Strategy - Improvement Analysis

## Executive Summary

The Bollinger Band CTA strategy from the paper (2012-2021: 17.52% return, 1.72 Sharpe) underperforms significantly in out-of-sample (2022-2026: 3.16% return, 0.86 Sharpe). Deep diagnostic analysis reveals several structural issues and improvement opportunities.

**After implementing easy fixes** (ATR coefficient 3x, MA band exit, time stop):
- OOS Return: 3.16% → **5.28%** (+67%)
- OOS Vol: 3.68% → **6.24%** (closer to 10% target)
- OOS Sharpe: 0.86 → **0.85** (similar risk-adjusted)
- OOS Max DD: -3.12% → **-5.60%** (acceptable trade-off)

---

## Key Diagnostic Findings

### 1. Severe Underleverage (CRITICAL)

**Original paper behavior:**
- ATR leverage mean: **0.39x** (median 0.27x!)
- Effective leverage after mul_vol: only **1.06x**
- Target vol: 10%, Actual: **3.68%**

**Root cause:** The formula `Lev_ATR = 0.005 * Close / ATR` assumes 0.5% risk per trade. For Chinese futures where ATR ≈ 2% of price, this yields:
```
Lev_ATR = 0.005 / 0.02 = 0.25x
```

**Fix implemented:** Changed `ATR_COEFF` from 0.005 to **0.015** (3x increase).

**Result:** ATR leverage mean = 1.14x, effective = 1.60x, vol = 6.24%.

**Further tuning opportunity:** Try `ATR_COEFF = 0.020-0.025` to get closer to 10% vol target. The mul_vol mechanism will self-correct to maintain target vol.

### 2. Exit Type Imbalance

**Diagnostic (original params):**
| Exit Type | % of Trades | Win Rate | Avg Raw Return |
|-----------|-------------|----------|----------------|
| MA_CROSS  | 85.7%       | 22.8%    | **-0.829%**    |
| TP        | 14.3%       | 99.8%    | **+6.609%**    |

**Problem:** 86% of exits are losers. Strategy is classic trend-following (many small losses, few big wins) but the loss magnitude is too high.

**Fix implemented:** Changed exit from plain MA cross to MA ± 0.3σ band:
- Long exit: close < MA + 0.3*Std (exit_upper)
- Short exit: close > MA - 0.3*Std (exit_lower)

This creates a "buffer zone" around MA to reduce whipsaws. Result: MA_CROSS trades dropped from 85.7% to 76.4%, with avg loss reduced from -0.829% to -0.429%.

**Further tuning:**
- Try `MA_BAND_EXIT = 0.5-1.0` for even wider buffer
- Consider trailing stop instead of MA-based exit
- Consider Chandelier Exit (ATR-based trailing from high)

### 3. Time-Based Stop Loss

**Diagnostic:** Short-duration trades (0-48 bars ≈ 0-3 days) have avg return of **-1.5%** to **-1.6%**. These are failed breakout attempts.

| Duration | % of Trades | Avg Return |
|----------|-------------|------------|
| 0-16 bars | 5.0% | -1.564% |
| 16-48 bars | 17.4% | -1.591% |
| 48-96 bars | 20.2% | -1.150% |
| 96-240 bars | 40.9% | +0.394% |
| 240+ bars | 16.5% | **+4.020%** |

**Fix implemented:** Added `MAX_LOSS_BARS=32` and `MAX_LOSS_PCT=-0.015`:
- After 32 bars (~2 days), if loss exceeds -1.5%, exit the trade
- Captured 12.5% of trades with avg -1.9% return (cut losses earlier)

**Further tuning:**
- Try `MAX_LOSS_BARS = 24-48` for different time windows
- Try `MAX_LOSS_PCT = -0.01 to -0.02` for different loss thresholds
- Consider volatility-adjusted time stops

### 4. Long/Short Asymmetry

**Diagnostic:**
| Direction | Win Rate | Avg Raw Return | Avg Abs Return |
|-----------|----------|----------------|----------------|
| LONG      | 36.6%    | **+0.429%**    | 2.491%         |
| SHORT     | 30.6%    | **+0.013%**    | 2.299%         |

**Problem:** Short side barely profitable. Longs outperform shorts significantly.

**Possible causes:**
- Chinese commodity futures have long-biased drift (similar to equity markets)
- Short squeeze dynamics in less liquid contracts
- Bollinger band mean-reversion bias in downtrends

**Potential fixes (NOT YET IMPLEMENTED):**
1. **Long-only mode:** Skip short signals entirely
2. **Asymmetric entry:** Require stronger confirmation for shorts (e.g., close < lower - 0.2*Std)
3. **Tighter exit for shorts:** Exit shorts at MA - 0.2*Std instead of MA
4. **Volume filter for shorts:** Only short when OI is strongly expanding

### 5. OI Filter Effectiveness

**Diagnostic:**
| Position | Win Rate | Avg Raw | Weighted Contribution |
|----------|----------|---------|----------------------|
| Full (OI_pct>1) | 32.6% | 0.267% | 344.12% |
| Half (OI_pct≤1) | 34.6% | 0.220% | 248.57% |

**Problem:** The difference between full and half position is marginal (0.047% avg return). The filter adds complexity without proportional benefit.

**Analysis:** OI expansion/contraction may not be a reliable signal on 15m timeframe. The 150/300 bar OI MA ratio is noisy.

**Potential fixes (NOT YET IMPLEMENTED):**
1. **Disable OI filter:** Set `OI_FILTER_ENABLED = False` (all trades at full size)
2. **Stronger signal:** Require OI_pct > 1.1 or OI_pct < 0.9 for clearer distinction
3. **Alternative OI metric:** Use OI change rate (delta OI) instead of ratio
4. **Volume filter instead:** Use volume expansion as confirmation

### 6. Universe Shrinkage

**Diagnostic:**
- Started with 23 symbols → dropped to 10-13 by end
- Worst contributors: AL (-14%), SR (-13.6%), RU (-11.3%), TF (-3.8%), CF (-2.4%)
- Best contributors: SA (+93.9%), M (+49.3%), V (+45.6%), SN (+38.3%), JD (+34.1%)

**Observation:** The dynamic universe selection correctly drops underperformers, but:
1. Some symbols persist too long before being dropped (12-month lookback is slow)
2. The "5 trades in 12 months" minimum is too low for reliable statistics
3. Symbols like SA dominate returns (concentration risk)

**Potential fixes (NOT YET IMPLEMENTED):**
1. **Shorter lookback:** Use 6-month instead of 12-month for Sharpe/Calmar filter
2. **Higher trade minimum:** Require 10+ trades for reliable evaluation
3. **Cap concentration:** Limit any single symbol to 15-20% of portfolio weight
4. **Sector diversification:** Ensure representation across agriculture, metals, energy, financials

### 7. Vol-Targeting Lag

**Diagnostic:**
- mul_vol mean: 2.76 (paper), 1.66 (improved)
- Range: 1.0 to 8.3 (paper), 1.0 to 3.0 (improved)
- Rolling 63-day vol: 2.0% to 9.7%

**Problem:** The 12-month realized vol lookback creates significant lag. When vol regime changes, mul_vol reacts slowly.

**Potential fixes (NOT YET IMPLEMENTED):**
1. **Shorter lookback:** Use 63-day (3-month) realized vol instead of 252-day
2. **Exponential weighting:** Use EWMA vol instead of simple std
3. **Vol forecast:** Use GARCH or simple MA forecast for forward vol
4. **Faster update:** Update mul_vol weekly instead of monthly

---

## Implemented Improvements (Configurable Parameters)

```python
# ========== CONFIGURABLE STRATEGY PARAMETERS ==========
ATR_COEFF = 0.015          # 0.005 in paper - increased 3x
BB_WIDTH = 1.5             # Bollinger Band width in std devs
TP_SIGMA = 8.0             # Take-profit at entry MA +/- 8*Std
MA_BAND_EXIT = 0.3         # Exit at MA +/- 0.3*Std (0 = paper)
MAX_LOSS_BARS = 32         # Time-based stop (0 = disabled)
MAX_LOSS_PCT = -0.015      # Time stop loss threshold
OI_FILTER_ENABLED = True   # Enable/disable OI filter
VOL_TARGET = 0.10          # Annualized vol target
MAX_LEVERAGE = 4.0         # Cap on ATR leverage
# =====================================================
```

---

## Suggested Experiments

### Priority 1: Quick Wins

| Experiment | Parameter Change | Expected Impact |
|------------|-----------------|-----------------|
| Higher leverage | `ATR_COEFF = 0.020` | Vol closer to 10%, higher return |
| Wider exit band | `MA_BAND_EXIT = 0.5` | Fewer whipsaw exits |
| Disable OI filter | `OI_FILTER_ENABLED = False` | Simpler, marginal improvement |

### Priority 2: Structural Changes

| Experiment | Implementation | Expected Impact |
|------------|---------------|-----------------|
| Long-only mode | Skip short entries | Remove drag from losing shorts |
| Trailing stop | Replace MA exit with ATR trailing | Let winners run longer |
| Faster vol adj | 63-day lookback for mul_vol | Better vol targeting |

### Priority 3: Advanced Improvements

| Experiment | Implementation | Expected Impact |
|------------|---------------|-----------------|
| Regime filter | Reduce size in low-vol regimes | Better capital efficiency |
| Multi-timeframe | Daily trend + 15m entry | Higher quality signals |
| Adaptive params | Optimize BB_WIDTH, TP_SIGMA per symbol | Symbol-specific tuning |
| Position scaling | Scale in on confirmation | Better entry prices |

---

## Performance Comparison

| Metric | Paper (2012-2021) | Original OOS (2022-2026) | Improved OOS (2022-2026) |
|--------|-------------------|-------------------------|-------------------------|
| **Ann Return** | 17.52% | 3.16% | **5.28%** |
| **Ann Vol** | 10.18% | 3.68% | **6.24%** |
| **Sharpe** | 1.72 | 0.86 | **0.85** |
| **Max DD** | -8.27% | -3.12% | **-5.60%** |
| **Calmar** | 2.12 | 1.02 | **0.94** |

**Key insight:** The improved version is closer to paper behavior (vol ~6% vs target 10%). Further ATR_COEFF increase could close the gap. The lower Sharpe (0.85 vs 1.72) suggests either:
1. Post-2021 market regime is less favorable to trend-following
2. Paper had look-ahead bias or overfitting
3. Transaction costs/slippage underestimated in paper

---

## Next Steps

1. **Run parameter sweep:** Test `ATR_COEFF ∈ [0.015, 0.020, 0.025]` to find optimal leverage
2. **Backtest long-only:** Quantify impact of removing short side
3. **Implement trailing stop:** Replace MA-based exit with ATR-based trailing
4. **Shorter vol lookback:** Test 63-day vs 252-day for mul_vol
5. **Cross-validate:** Test improvements on different time periods (2018-2021 warmup)

---

## Appendix: Diagnostic Output (Improved Version)

```
--- 2. Exit Type Breakdown (All Symbols) ---
  MA_CROSS: 3167 trades (76.4%), WinRate=26.2%, AvgRaw=-0.429%, AvgBars=104.6
  TP: 462 trades (11.1%), WinRate=99.8%, AvgRaw=6.462%, AvgBars=166.5
  TIME_STOP: 517 trades (12.5%), WinRate=0.2%, AvgRaw=-1.903%, AvgBars=47.5

--- 3. Long vs Short Asymmetry ---
  LONG: 2238 trades, WinRate=32.7%, AvgRaw=0.277%, AvgBars=104.1
  SHORT: 1908 trades, WinRate=29.3%, AvgRaw=0.013%, AvgBars=104.6

--- 8. Leverage Utilization ---
  ATR Leverage: mean=1.14, median=0.80, min=0.12, max=17.41
  Effective leverage (capped * avg mul_vol): mean=1.60x
  Avg mul_vol: 1.658

--- 9. Trade Duration Distribution ---
  0-16 bars: 320 (7.7%), AvgRaw=-1.473%
  16-48 bars: 1159 (28.0%), AvgRaw=-1.487%
  48-96 bars: 878 (21.2%), AvgRaw=-0.615%
  96-240 bars: 1433 (34.6%), AvgRaw=1.177%
  240+ bars: 356 (8.6%), AvgRaw=4.750%
```
