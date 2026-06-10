# Plan: Improve plot_macro_price.py

Two changes to make charts cleaner and more informative.

## 1. Full-height vertical lines at release dates

**Current**: Small scatter markers (`s=30`) on the price line — easy to miss, no visual span.
**Target**: Semi-transparent `axvline` at each release date spanning full chart height.

- Add `axvline` for each release point **before** the price line so it renders behind
- Color by direction: green (`#319795`) for positive, red (`#e53e3e`) for negative, gray (`#718096`) for neutral
- Low alpha (0.15–0.25) so lines don't obscure the price line
- Lower zorder (2) than the price line (3) and markers (5)
- Use same direction logic already computed for scatter markers (reuse `pos_releases`, `neg_releases`, `neutral_releases`)

**Implementation** — in the loop at `plot_macro_price.py:139`, add vertical lines before scatter calls:

```python
# Vertical lines (background, full height)
for dt in pos_releases.index:
    ax.axvline(x=dt, color='#319795', alpha=0.18, linewidth=0.8, zorder=2)
for dt in neg_releases.index:
    ax.axvline(x=dt, color='#e53e3e', alpha=0.18, linewidth=0.8, zorder=2)
for dt in neutral_releases.index:
    ax.axvline(x=dt, color='#718096', alpha=0.12, linewidth=0.5, zorder=2)
```

## 2. Size and color-scaled triangles by magnitude

**Current**: All triangles same `s=30`, same flat color.
**Target**: Triangle size and color intensity scale with the absolute magnitude of the surprise/change.

### Magnitude computation

Reuse existing direction logic. Compute `magnitude` (absolute value of the signal * sign) for each release:

- For `rep == 'diff'`: `magnitude = abs(val * sign)`
- For other reps: `magnitude = abs(change * sign)` where `change` = current - previous value

### Size scaling

Use percentile-based binning across all release magnitudes within the symbol:

| Percentile | Size | Meaning |
|---|---|---|
| 0–33% | s=50 | Small surprise |
| 33–66% | s=100 | Medium surprise |
| 66–90% | s=160 | Large surprise |
| 90–100% | s=220 | Very large surprise |

### Color scaling

Map magnitude to color intensity within each direction:

- **Positive**: light teal `#81e6d9` → deep teal `#234e52`
- **Negative**: light red `#feb2b2` → deep red `#742a2a`

Use `matplotlib.colors.LinearSegmentedColormap` or manual hex interpolation based on normalized magnitude (0→1 across min→max).

### Implementation

Replace the bulk `ax.scatter()` calls with per-point scatter (or vectorized size/color arrays):

```python
# For each release, compute magnitude and map to size + color
magnitudes = ...  # Series aligned with pos_releases / neg_releases
norm_mag = (magnitudes - magnitudes.min()) / (magnitudes.max() - magnitudes.min() + 1e-9)

sizes = np.interp(norm_mag, [0, 0.33, 0.66, 0.9, 1.0], [50, 50, 100, 160, 220])
# For colors, use colormap or manual interpolation
colors = cmap_positive(norm_mag)  # or custom blend
```

Use `matplotlib.cm` colormaps:
- Positive: custom from `#81e6d9` to `#234e52` (or use `matplotlib.colors.LinearSegmentedColormap.from_list`)
- Negative: custom from `#feb2b2` to `#742a2a`

### Legend update

Add legend entries for size tiers. Show 2–3 representative legend entries:
- "Positive (Small)", "Positive (Large)", "Negative (Small)", "Negative (Large)"
Use `ax.scatter([], [])` proxy artists for legend.

## Files to modify

- `plot_macro_price.py` — lines ~120–149 (marker plotting section)

## Execution order

1. Add vertical lines (simple, high impact)
2. Add magnitude computation for each release point
3. Replace scatter calls with size/color-scaled version
4. Update legend with representative entries
5. Test by running the script and checking output PNGs
