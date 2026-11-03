# Replication check: GGR (2006) Tables 1-5, 7 and 8; Figures 1 and 4 (vol_common)

Cells show ours / paper. ✓ within 10%, ~ between 10% and 25%, ✗ outside 25%.

## Specification and limitations

Entry scale: `rms`. RMS measures deviations about zero; std demeans the spread.
The baseline retains RMS based on the printed trigger checks (REVIEW_NOTES section 21);
demeaned std remains an explicit interpretation of section 2.2.
Short weights: `value`. `value` tracks the shorted stock's liability
under section 2.3 equations (2)-(3); `position` is the superseded inverse-weight rule.
Monthly aggregation: `books`. `books` compounds long and short books
separately and subtracts, preserving Table 1B = Table 7 long minus short.
`daily_difference` is a legacy sensitivity and does not preserve that identity.
Liquidity universe: `vol_common`; traded_common requires
a CIZ trade-price flag, no recorded zero volume, and a finite return on every formation day.
This conservative observable-trade screen is not a recovered historical CRSP vintage.
Idle cash policy: `opened`; opened keeps idle months at zero
but excludes never-opened cohorts from employed capital. Zero retains all inactive
cohorts; exclude drops idle days/months. Committed capital keeps unused cash at zero.
Committed capital scales both daily books by the active fraction of selected pairs;
the employed-capital denominator uses pairs open that day. This timing convention
remains an interpretation of the paper's 'open during the trading period'.
Additional screens: same issuer excluded=True;
constant path excluded=True; maximum stale share=0.95.
These exclusions are disclosed conventions, not explicit paper instructions. The volume
baseline admits missing volume and quote prices, preserving historical Nasdaq coverage;
the stricter traded_common universe remains available as a sensitivity.
Trading paths continue formation normalization.
SIC fallback: `formation_end`. The paper baseline uses
dated formation-end codes only; unknowns map to Industrials. The legacy fallback
can use future classifications and is excluded from the paper baseline.
SIC group boundaries remain interpretations, not recovered S&P classifications.
Delayed entry: `execute`. Execute preserves the signal-day direction
and exits the next day if a crossing occurred on the entry day. Cancel is legacy behavior.
period_cash and selected_cash outputs audit fixed-dollar payoff/period denominators;
they are explicit alternatives, not substitutes chosen to improve target fit.

Factor results are proxy robustness checks: French ST_Rev is not the paper's
unavailable custom reversal series, and rebuilt Ibbotson inputs have not been
validated against its proprietary vintage. Significant proxy-factor alpha does not
establish the original regression or a causal mispricing mechanism.

The score reports weighted points and actual cell counts separately.
A better score does not override the paper's rules or accounting identities.

## Summary

- Figure 1: reproduced
- Table 1: Cells: 88; ✓ 50 (within 10%), ~ 16 (within 25%), ✗ 22.
- Table 2 Panel A: Cells: 24; ✓ 17 (within 10%), ~ 7 (within 25%), ✗ 0.
- Table 2 Panel B: Cells: 40; ✓ 24 (within 10%), ~ 6 (within 25%), ✗ 10.
- Table 3: Cells: 139; ✓ 49 (within 10%), ~ 35 (within 25%), ✗ 55.
- Table 7: Cells: 32; ✓ 22 (within 10%), ~ 7 (within 25%), ✗ 3.
- Table 4: Cells: 36; ✓ 8 (within 10%), ~ 3 (within 25%), ✗ 25.
- Table 5 Panel A: Cells: 20; ✓ 5 (within 10%), ~ 8 (within 25%), ✗ 7.
- Table 5 Panel B: Cells: 35; ✓ 24 (within 10%), ~ 4 (within 25%), ✗ 7.
- Table 8: Cells: 72; ✓ 11 (within 10%), ~ 9 (within 25%), ✗ 52.
- Figure 4: Cells: 6; ✓ 0 (within 10%), ~ 2 (within 25%), ✗ 4.
- Score: 258.5 weighted points across 492 compared cells (✓ = 1, ~ = ½, ✗ = 0); history in SCORE_LOG.md.
- Tables 1-3 alone: 172.0 of 291, the cell set of SCORE_LOG.md rows 1-13.
- Tables 1-3 and 7 alone: 197.5 of 323, the cell set of SCORE_LOG.md row 14.

## Figure 1 (Kennecott vs Uniroyal, trading Aug 1963 - Jan 1964, no wait)

| check | ours | paper | match |
|---|---|---|---|
| pair formed (rank) | 4 | top 5 | ✓ |
| trades (open day, close day) | [(8, 35), (46, 56), (76, 83), (85, 99), (108, 125)] | [(7, 35), (46, 55), (74, 82), (86, 99), (108, 126)] (read off the chart) | ✓ (±3 days) |
| day-0 levels (formation end) | [1.1006, 1.106] | about 1.10 | ✓ |

Plot: `results/replication/reconciliation/baseline/figures/figure1.png`.

## Table 1 Panel A (no wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean (fully invested) | 1.34% / 1.31% ✓ | 1.46% / 1.44% ✓ | 1.02% / 1.08% ✓ | 1.05% / 1.10% ✓ |
| nw_se | 0.15% / 0.15% ✓ | 0.13% / 0.12% ✓ | 0.08% / 0.09% ✓ | 0.10% / 0.10% ✓ |
| t_stat | 8.97 / 8.84 ✓ | 11.5 / 11.6 ✓ | 12 / 11.5 ✓ | 10.5 / 11.2 ✓ |
| median | 1.22% / 1.19% ✓ | 1.29% / 1.23% ✓ | 0.91% / 0.95% ✓ | 0.74% / 0.73% ✓ |
| std | 2.34% / 2.28% ✓ | 1.70% / 1.69% ✓ | 1.59% / 1.54% ✓ | 2.06% / 1.67% ~ |
| skew | 0.193 / 0.62 ✗ | 0.807 / 1.39 ✗ | 0.569 / 1.34 ✗ | 0.854 / 3.42 ✗ |
| kurtosis | 7.56 / 7.81 ✓ | 7.09 / 10.5 ✗ | 4.9 / 10.3 ✗ | 19.2 / 25.2 ~ |
| min | -12.99% / -10.57% ~ | -7.12% / -6.63% ✓ | -4.45% / -3.86% ~ | -15.19% / -2.72% ✗ |
| max | 11.42% / 14.72% ~ | 9.55% / 13.30% ✗ | 8.02% / 12.68% ✗ | 14.53% / 17.18% ~ |
| share_negative | 0.255 / 0.26 ✓ | 0.158 / 0.15 ✓ | 0.257 / 0.21 ~ | 0.241 / 0.17 ✗ |
| mean (committed) | 0.80% / 0.78% ✓ | 0.85% / 0.80% ✓ | 0.63% / 0.68% ✓ | 0.56% / 0.61% ✓ |

## Table 1 Panel B (one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean (fully invested) | 0.78% / 0.74% ✓ | 0.96% / 0.90% ✓ | 0.82% / 0.80% ✓ | 0.80% / 0.71% ~ |
| nw_se | 0.11% / 0.12% ✓ | 0.10% / 0.10% ✓ | 0.08% / 0.08% ✓ | 0.10% / 0.09% ✓ |
| t_stat | 6.93 / 6.26 ~ | 9.73 / 9.29 ✓ | 10.3 / 9.4 ✓ | 8.13 / 7.92 ✓ |
| median | 0.79% / 0.70% ~ | 0.88% / 0.69% ✗ | 0.78% / 0.69% ~ | 0.54% / 0.41% ✗ |
| std | 2.05% / 2.10% ✓ | 1.51% / 1.53% ✓ | 1.52% / 1.44% ✓ | 1.97% / 1.58% ~ |
| skew | -0.285 / 0.34 ✗ | 0.293 / 1.45 ✗ | 0.24 / 0.98 ✗ | 0.694 / 3.32 ✗ |
| kurtosis | 8.86 / 10.6 ~ | 7.49 / 16.1 ✗ | 4.21 / 7.78 ✗ | 19.3 / 25.7 ~ |
| min | -13.43% / -12.63% ✓ | -8.11% / -8.22% ✓ | -4.37% / -4.27% ✓ | -14.89% / -2.95% ✗ |
| max | 9.98% / 14.35% ✗ | 7.88% / 13.49% ✗ | 6.70% / 10.46% ✗ | 13.03% / 16.32% ~ |
| share_negative | 0.346 / 0.35 ✓ | 0.253 / 0.23 ~ | 0.276 / 0.28 ✓ | 0.304 / 0.32 ✓ |
| mean (committed) | 0.47% / 0.46% ✓ | 0.57% / 0.52% ✓ | 0.51% / 0.50% ✓ | 0.42% / 0.40% ✓ |

Cells: 88; ✓ 50 (within 10%), ~ 16 (within 25%), ✗ 22.

## Table 2 Panel A (one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| avg_price_deviation_trigger | 0.0408 / 0.0476 ~ | 0.0465 / 0.0528 ~ | 0.0715 / 0.0756 ✓ | 0.173 / 0.169 ✓ |
| avg_pairs_traded_per_period | 4.89 / 4.81 ✓ | 19.6 / 19.3 ✓ | 19.6 / 19.4 ✓ | 1.88e+03 / 1.94e+03 ✓ |
| avg_round_trips_per_pair | 2.27 / 2.02 ~ | 2.13 / 1.96 ✓ | 1.85 / 1.78 ✓ | 1.66 / 1.62 ✓ |
| std_round_trips_per_pair | 0.702 / 0.62 ~ | 0.47 / 0.4 ~ | 0.291 / 0.27 ✓ | 0.158 / 0.16 ✓ |
| avg_time_open_months | 3.92 / 3.75 ✓ | 3.88 / 3.76 ✓ | 4.08 / 3.98 ✓ | 4.01 / 3.97 ✓ |
| std_time_open_months | 0.708 / 0.8 ~ | 0.46 / 0.45 ✓ | 0.37 / 0.38 ✓ | 0.199 / 0.17 ~ |

Cells: 24; ✓ 17 (within 10%), ~ 7 (within 25%), ✗ 0.

## Table 2 Panel B (composition)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| avg_size_decile | 2.67 / 2.54 ✓ | 2.74 / 2.71 ✓ | 3.15 / 3.41 ✓ | 4.63 / 4.57 ✓ |
| weight_top3_deciles | 0.763 / 0.78 ✓ | 0.736 / 0.74 ✓ | 0.638 / 0.58 ~ | 0.406 / 0.4 ✓ |
| weight_top5_deciles | 0.917 / 0.91 ✓ | 0.922 / 0.91 ✓ | 0.841 / 0.79 ✓ | 0.626 / 0.62 ✓ |
| share_mixed_decile_pairs | 0.662 / 0.66 ✓ | 0.691 / 0.69 ✓ | 0.734 / 0.75 ✓ | 0.812 / 0.82 ✓ |
| avg_decile_diff_mixed_pairs | 1.66 / 0.97 ✗ | 1.74 / 0.97 ✗ | 2.17 / 0.97 ✗ | 2.64 / 0.98 ✗ |
| weight_utilities | 0.768 / 0.72 ✓ | 0.766 / 0.71 ✓ | 0.296 / 0.32 ✓ | 0.0818 / 0.08 ✓ |
| weight_transportation | 0.0118 / 0.02 ✗ | 0.0103 / 0.02 ✗ | 0.0178 / 0.02 ~ | 0.0289 / 0.03 ✓ |
| weight_financials | 0.122 / 0.11 ~ | 0.125 / 0.13 ✓ | 0.242 / 0.26 ✓ | 0.138 / 0.16 ~ |
| weight_industrials | 0.0987 / 0.15 ✗ | 0.0989 / 0.14 ✗ | 0.444 / 0.4 ~ | 0.751 / 0.73 ✓ |
| share_mixed_sector_pairs | 0.114 / 0.2 ✗ | 0.136 / 0.22 ✗ | 0.413 / 0.44 ✓ | 0.289 / 0.33 ~ |

Cells: 40; ✓ 24 (within 10%), ~ 6 (within 25%), ✗ 10.

## Table 3 stocks per cohort

| sector | ours / paper |
|---|---|
| Utilities | 135 / 156 ~ |
| Transportation | 58.9 / 61 ✓ |
| Financials | 318 / 371 ~ |
| Industrials | 1.78e+03 / 1.73e+03 ✓ |

## Table 3: Utilities (fully invested, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 1.05% / 0.91% ~ | 1.24% / 1.08% ~ | 0.88% / 0.93% ✓ | 1.19% / 1.04% ~ |
| t_stat | 8.21 / 7.37 ~ | 10.6 / 10.3 ✓ | 5.37 / 6.11 ~ | 11.3 / 10.5 ✓ |
| median | 0.96% / 0.83% ~ | 1.10% / 0.94% ~ | 0.87% / 0.66% ✗ | 1.07% / 0.97% ~ |
| std | 2.11% / 2.15% ✓ | 1.72% / 1.65% ✓ | 2.49% / 2.64% ✓ | 1.58% / 1.47% ✓ |
| skew | -0.377 / 0.44 ✗ | 0.577 / 0.76 ~ | 0.681 / 0.66 ✓ | 0.908 / 1.39 ✗ |
| kurtosis | 9.85 / 13.7 ✗ | 9.88 / 12.4 ~ | 7.15 / 5.52 ✗ | 8.86 / 12.7 ✗ |
| min | -13.43% / -12.35% ✓ | -8.08% / -8.75% ✓ | -7.90% / -7.87% ✓ | -4.07% / -3.52% ~ |
| max | 9.98% / 16.56% ✗ | 11.01% / 12.73% ~ | 15.53% / 12.13% ✗ | 11.76% / 12.88% ✓ |
| share_negative | 0.295 / 0.28 ✓ | 0.181 / 0.19 ✓ | 0.345 / 0.35 ✓ | 0.169 / 0.18 ✓ |

## Table 3: Transportation (fully invested, one-day wait)

| statistic | top5 | top20 | all |
|---|---|---|---|
| mean | 0.88% / 0.50% ✗ | 0.77% / 0.58% ✗ | 0.78% / 0.44% ✗ |
| t_stat | 5.17 / 2.98 ✗ | 6.04 / 4.26 ✗ | 5.85 / 3.07 ✗ |
| median | 0.91% / 0.59% ✗ | 0.69% / 0.55% ✗ | 0.61% / 0.34% ✗ |
| std | 3.95% / 3.89% ✓ | 2.95% / 2.94% ✓ | 3.02% / 2.87% ✓ |
| skew | -0.0436 / -0.5 ✗ | 0.0366 / -0.11 ✗ | 0.466 / 0.53 ~ |
| kurtosis | 3.4 / 4.98 ✗ | 4.1 / 5 ~ | 4.07 / 5.89 ✗ |
| min | -10.28% / -19.57% ✗ | -11.78% / -12.47% ✓ | -8.04% / -12.53% ✗ |
| max | 13.98% / 10.96% ✗ | 10.63% / 11.10% ✓ | 12.67% / 13.56% ✓ |
| share_negative | 0.397 / 0.44 ✓ | 0.367 / 0.42 ~ | 0.371 / 0.44 ~ |

## Table 3: Financials (fully invested, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 0.82% / 0.68% ~ | 0.94% / 0.78% ~ | 1.14% / 0.85% ✗ | 0.88% / 0.73% ~ |
| t_stat | 6.26 / 4.79 ✗ | 10.1 / 7.6 ✗ | 9.28 / 7.12 ✗ | 8.92 / 7.62 ~ |
| median | 0.73% / 0.56% ✗ | 0.91% / 0.61% ✗ | 1.01% / 0.66% ✗ | 0.70% / 0.51% ✗ |
| std | 2.76% / 2.60% ✓ | 1.82% / 1.79% ✓ | 2.25% / 2.36% ✓ | 1.94% / 1.81% ✓ |
| skew | 0.245 / 0.81 ✗ | 0.229 / 0.61 ✗ | 3.04 / 1.98 ✗ | 0.812 / 2.64 ✗ |
| kurtosis | 8.06 / 6.37 ✗ | 4.86 / 6.48 ✗ | 27.9 / 18.3 ✗ | 6.48 / 21.2 ✗ |
| min | -14.89% / -8.20% ✗ | -7.14% / -7.81% ✓ | -3.38% / -10.05% ✗ | -5.46% / -4.45% ~ |
| max | 16.63% / 14.93% ~ | 8.19% / 10.64% ~ | 22.72% / 19.58% ~ | 11.44% / 17.21% ✗ |
| share_negative | 0.371 / 0.4 ✓ | 0.274 / 0.33 ~ | 0.256 / 0.32 ~ | 0.3 / 0.34 ~ |

## Table 3: Industrials (fully invested, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 0.54% / 0.49% ✓ | 0.77% / 0.61% ✗ | 0.83% / 0.66% ✗ | 0.79% / 0.71% ✓ |
| t_stat | 4.35 / 4.11 ✓ | 8.19 / 6.93 ~ | 8.84 / 6.8 ✗ | 7.27 / 7.52 ✓ |
| median | 0.55% / 0.29% ✗ | 0.70% / 0.55% ✗ | 0.73% / 0.55% ✗ | 0.55% / 0.40% ✗ |
| std | 2.40% / 2.36% ✓ | 1.68% / 1.60% ✓ | 1.86% / 1.82% ✓ | 2.18% / 1.67% ✗ |
| skew | -0.0987 / 0.4 ✗ | 0.32 / 0.43 ✗ | 0.897 / 0.94 ✓ | 0.695 / 2.97 ✗ |
| kurtosis | 5.15 / 4.94 ✓ | 5.41 / 4.75 ~ | 6.1 / 7.65 ~ | 20.6 / 20.9 ✓ |
| min | -10.90% / -10.02% ✓ | -4.84% / -4.79% ✓ | -5.10% / -5.41% ✓ | -16.84% / -3.43% ✗ |
| max | 10.21% / 10.55% ✓ | 8.74% / 8.02% ✓ | 10.29% / 11.62% ~ | 15.42% / 16.07% ✓ |
| share_negative | 0.403 / 0.42 ✓ | 0.3 / 0.36 ~ | 0.314 / 0.35 ~ | 0.329 / 0.34 ✓ |

Cells: 139; ✓ 49 (within 10%), ~ 35 (within 25%), ✗ 55.

## Table 7 (long and short books, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| long: mean monthly return | 1.25% / 1.24% ✓ | 1.36% / 1.33% ✓ | 1.48% / 1.46% ✓ | 1.51% / 1.62% ✓ |
| long: standard error (Newey-West) | 0.19% / 0.18% ✓ | 0.18% / 0.18% ✓ | 0.19% / 0.17% ~ | 0.27% / 0.25% ✓ |
| long: standard deviation | 3.84% / 3.88% ✓ | 3.70% / 3.65% ✓ | 3.79% / 3.44% ~ | 5.66% / 5.16% ✓ |
| long: monthly serial correlation | 0.09 / 0.06 ✗ | 0.0899 / 0.09 ✓ | 0.135 / 0.13 ✓ | 0.16 / 0.17 ✓ |
| short: mean monthly return | 0.47% / 0.50% ✓ | 0.40% / 0.43% ✓ | 0.66% / 0.66% ✓ | 0.71% / 0.91% ~ |
| short: standard error (Newey-West) | 0.20% / 0.18% ~ | 0.19% / 0.17% ✓ | 0.17% / 0.17% ✓ | 0.25% / 0.23% ✓ |
| short: standard deviation | 3.57% / 3.26% ✓ | 3.41% / 3.16% ✓ | 3.51% / 3.15% ~ | 5.13% / 4.60% ~ |
| short: monthly serial correlation | 0.142 / 0.11 ✗ | 0.112 / 0.12 ✓ | 0.0751 / 0.12 ✗ | 0.142 / 0.16 ~ |

Cells: 32; ✓ 22 (within 10%), ~ 7 (within 25%), ✗ 3.

## Risk comparisons: scope

Tables 4, 5A, 7 and 8 use the same one-day-wait monthly series; Table 5B uses
daily book differences, overlap-averaged across cohorts before its statistics.
Percentiles use linear interpolation. Monthly serial correlation pairs adjacent
calendar months; daily serial correlation pairs adjacent trading observations.
Repeated monthly moments are excluded from the score. Daily Table 5B is a distinct
frequency and includes all nine rows. A zero target is printed without a relative-error mark.
Missing inputs are shown as NA, not treated as replication. Five-factor regressions
use the French reversal proxy; Ibbotson reconstruction is a separate proxy model.
Near-zero loadings make percentage-error marks unstable; inspect signs, absolute
differences and significance as well. No claim count is inferred from the score.

## Table 4 (systematic risk, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| sharpe | 0.383 / 0.35 ✓ | 0.637 / 0.59 ✓ | 0.541 / 0.55 ✓ | 0.405 / 0.45 ~ |
| intercept | 0.808% / 0.545% ✗ | 0.960% / 0.764% ✗ | 0.895% / 0.714% ✗ | 0.824% / 0.512% ✗ |
| market | -0.0205 / -0.0666 ✗ | 0.00461 / -0.0316 ✗ | 0.012 / -0.077 ✗ | 0.0665 / -0.145 ✗ |
| smb | 0.00506 / -0.0423 ✗ | 0.0166 / 0.00111 ✗ | 0.0476 / -0.0233 ✗ | -0.0205 / -0.0708 ✗ |
| hml | -0.00248 / 0.0574 ✗ | 0.0271 / 0.0451 ✗ | 0.0125 / -0.0172 ✗ | 0.0565 / -0.054 ✗ |
| momentum | -0.0436 / -0.028 ✗ | -0.0494 / -0.0482 ✓ | -0.157 / -0.103 ✗ | -0.258 / -0.181 ✗ |
| reversal | 0.04 / 0.102 ✗ | 0.0431 / 0.0724 ✗ | 0.0783 / 0.0946 ~ | 0.253 / 0.201 ✗ |
| r2 | 0.0152 / 0.05 ✗ | 0.0401 / 0.09 ✗ | 0.274 / 0.18 ✗ | 0.666 / 0.54 ~ |
| ibbotson_intercept | NA / 0.716% | NA / 0.857% | NA / 0.766% | NA / 0.651% |
| ibbotson_market | NA / -0.00182 | NA / 0.0138 | NA / 0.0164 | NA / 0.0647 |
| ibbotson_small_premium | NA / 0.0412 | NA / 0.0523 | NA / 0.0365 | NA / 0.0761 |
| ibbotson_default_premium | NA / 0.146 | NA / 0.16 | NA / 0.168 | NA / 0.306 |
| ibbotson_horizon_premium | NA / 0.08 | NA / 0.0682 | NA / 0.0403 | NA / 0.0342 |
| ibbotson_r2 | NA / 0.02 | NA / 0.05 | NA / 0.04 | NA / 0.15 |
| alpha t-statistic, full sample (Newey-West, 6 lags; unscored) | 6.79 vs 3.81 | 9.26 vs 7.08 | 11.84 vs 8.66 | 12.05 vs 5.30 |

| statistic | French's Mkt-RF (ours / paper) |
|---|---|
| equity premium: mean | 0.425% / 0.410% ✓ |
| equity premium: std | 4.540% / 4.509% ✓ |
| equity premium: sharpe | 0.0936 / 0.09 ✓ |
| equity premium: serial_correlation | 0.0465 / 0.05 ✓ |

Cells: 36; ✓ 8 (within 10%), ~ 3 (within 25%), ✗ 25.

## Table 5 Panel A (monthly value at risk)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| serial_correlation | 0.113 / 0.14 ~ | 0.244 / 0.24 ✓ | 0.0643 / 0.19 ✗ | 0.0577 / 0.12 ✗ |
| var_1 | -3.491% / -4.320% ~ | -2.290% / -1.943% ~ | -2.898% / -2.236% ✗ | -2.832% / -1.994% ✗ |
| var_5 | -2.163% / -2.142% ✓ | -1.033% / -1.002% ✓ | -1.452% / -1.293% ~ | -1.395% / -0.877% ✗ |
| var_10 | -1.480% / -1.516% ✓ | -0.584% / -0.577% ✓ | -0.971% / -0.756% ✗ | -0.707% / -0.614% ~ |
| var_25 | -0.385% / -0.460% ~ | -0.001% / 0.054% ✗ | -0.117% / -0.145% ~ | -0.174% / -0.146% ~ |

Cells: 20; ✓ 5 (within 10%), ~ 8 (within 25%), ✗ 7.

## Table 5 Panel B (daily value at risk)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 0.037% / 0.033% ~ | 0.045% / 0.040% ~ | 0.038% / 0.035% ✓ | 0.037% / 0.027% ✗ |
| std | 0.480% / 0.492% ✓ | 0.300% / 0.296% ✓ | 0.288% / 0.277% ✓ | 0.240% / 0.169% ✗ |
| serial_correlation | -0.102 / -0.12 ~ | -0.0553 / -0.06 ✓ | 0.0513 / 0  | 0.342 / 0.35 ✓ |
| var_1 | -1.161% / -1.236% ✓ | -0.651% / -0.647% ✓ | -0.676% / -0.653% ✓ | -0.510% / -0.327% ✗ |
| var_5 | -0.682% / -0.710% ✓ | -0.406% / -0.398% ✓ | -0.405% / -0.400% ✓ | -0.290% / -0.202% ✗ |
| var_10 | -0.485% / -0.504% ✓ | -0.295% / -0.293% ✓ | -0.300% / -0.288% ✓ | -0.208% / -0.149% ✗ |
| var_25 | -0.227% / -0.239% ✓ | -0.128% / -0.133% ✓ | -0.137% / -0.130% ✓ | -0.090% / -0.071% ✗ |
| share_negative | 46.641% / 47.000% ✓ | 43.695% / 44.000% ✓ | 44.680% / 45.000% ✓ | 44.781% / 46.000% ✓ |
| min | -10.018% / -10.079% ✓ | -5.943% / -6.723% ~ | -1.969% / -1.987% ✓ | -2.071% / -1.069% ✗ |

Cells: 35; ✓ 24 (within 10%), ~ 4 (within 25%), ✗ 7.

## Table 8 (subperiod analysis)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| pre_mean | 1.018% / 1.034% ✓ | 1.248% / 1.181% ✓ | 0.946% / 1.052% ~ | 1.018% / 0.992% ✓ |
| pre_std | 2.277% / 2.259% ✓ | 1.651% / 1.689% ✓ | 1.544% / 1.527% ✓ | 1.597% / 1.651% ✓ |
| post_mean | 0.360% / 0.217% ✗ | 0.435% / 0.375% ~ | 0.593% / 0.327% ✗ | 0.395% / 0.212% ✗ |
| post_std | 1.457% / 1.660% ~ | 1.011% / 0.987% ✓ | 1.447% / 1.121% ✗ | 2.465% / 1.295% ✗ |
| pre_intercept | 1.012% / 0.353% ✗ | 1.194% / 0.670% ✗ | 0.985% / 0.710% ✗ | 0.929% / 0.446% ✗ |
| pre_market | -0.0604 / -0.434 ✗ | -0.00818 / -0.312 ✗ | -0.00543 / -0.289 ✗ | 0.0425 / -0.434 ✗ |
| pre_smb | -0.0477 / -0.442 ✗ | -0.00718 / -0.332 ✗ | 0.0459 / -0.275 ✗ | 0.0795 / -0.402 ✗ |
| pre_hml | 0.0168 / 0.0357 ✗ | 0.04 / 0.0316 ✗ | -0.00755 / -0.0684 ✗ | 0.0345 / -0.0698 ✗ |
| pre_momentum | -0.0746 / 0.0129 ✗ | -0.07 / -0.0163 ✗ | -0.192 / -0.0769 ✗ | -0.211 / -0.158 ✗ |
| pre_reversal | 0.113 / 0.436 ✗ | 0.114 / 0.333 ✗ | 0.121 / 0.288 ✗ | 0.237 / 0.452 ✗ |
| pre_r2 | 0.0548 / 0.19 ✗ | 0.0801 / 0.23 ✗ | 0.32 / 0.26 ~ | 0.621 / 0.7 ~ |
| post_intercept | 0.288% / 0.337% ~ | 0.430% / 0.417% ✓ | 0.677% / 0.363% ✗ | 0.615% / -0.065% ✗ |
| post_market | 0.102 / 0.0734 ✗ | 0.0436 / 0.048 ✓ | 0.0522 / 0.00241 ✗ | 0.0585 / -0.0696 ✗ |
| post_smb | 0.0452 / -0.004 ✗ | 0.00391 / 0.0289 ✗ | 0.0382 / 0.0233 ✗ | -0.111 / -0.0606 ✗ |
| post_hml | 0.029 / 0.0344 ~ | 0.00704 / 0.0141 ✗ | 0.0337 / 0.0183 ✗ | 0.033 / -0.082 ✗ |
| post_momentum | 0.0107 / -0.00424 ✗ | -0.0122 / -0.0227 ✗ | -0.114 / -0.0884 ✗ | -0.291 / -0.127 ✗ |
| post_reversal | -0.0228 / -0.0626 ✗ | -0.0207 / -0.0173 ~ | 0.0413 / 0.024 ✗ | 0.255 / 0.188 ✗ |
| post_r2 | 0.0931 / 0.02 ✗ | 0.0374 / 0.04 ✓ | 0.242 / 0.19 ✗ | 0.757 / 0.64 ~ |
| alpha t-statistic, before 1989 (Newey-West, 6 lags; unscored) | 6.15 vs 1.72 | 8.32 vs 4.41 | 9.15 vs 6.54 | 11.39 vs 4.19 |
| alpha t-statistic, after 1988 (Newey-West, 6 lags; unscored) | 2.27 vs 2.12 | 5.26 vs 3.77 | 9.16 vs 3.01 | 6.39 vs -0.56 |

Cells: 72; ✓ 11 (within 10%), ~ 9 (within 25%), ✗ 52.

## Figure 4 (top 20 against 101-120, correlations printed in the text)

| statistic | raw | five-factor residuals |
|---|---|---|
| correlation, full sample | 0.343 / 0.48 ✗ | 0.289 / 0.41 ✗ |
| correlation, before 1989 | 0.405 / 0.51 ~ | 0.337 / 0.42 ~ |
| correlation, after 1988 | 0.104 / 0.18 ✗ | 0.133 / 0.2 ✗ |

Cells: 6; ✓ 0 (within 10%), ~ 2 (within 25%), ✗ 4.

## Reversal factor: reconstructed losers-only sensitivity (unscored)

The scored regressions use French's ST_Rev as a proxy. The paper's own
reversal-factor observations are unavailable. A prior audit inferred that
a long-only losers factor could explain some printed moments; that inference
does not recover or authenticate the original series. The alternative below
uses French's equal-weighted bottom three prior-month deciles less the T-bill.
Neither version is an exact replication of the proprietary factor regression.

| Table 4, full sample: ours vs paper | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| intercept | 0.87% vs 0.55% ✗ | 0.97% vs 0.76% ✗ | 0.90% vs 0.71% ✗ | 0.80% vs 0.51% ✗ |
| market | 0.0238 vs -0.0666 ✗ | -0.0302 vs -0.0316 ✓ | -0.0718 vs -0.077 ✓ | -0.244 vs -0.145 ✗ |
| smb | 0.0467 vs -0.0423 ✗ | -0.0194 vs 0.00111 ✗ | -0.038 vs -0.0233 ✗ | -0.336 vs -0.0708 ✗ |
| hml | 0.00518 vs 0.0574 ✗ | 0.0179 vs 0.0451 ✗ | -0.00843 vs -0.0172 ✗ | -0.0196 vs -0.054 ✗ |
| momentum | -0.0652 vs -0.028 ✗ | -0.0492 vs -0.0482 ✓ | -0.15 vs -0.103 ✗ | -0.227 vs -0.181 ✗ |
| reversal | -0.0372 vs 0.102 ✗ | 0.0392 vs 0.0724 ✗ | 0.091 vs 0.0946 ✓ | 0.332 vs 0.201 ✗ |
| r2 | 0.0138 vs 0.05 ✗ | 0.037 vs 0.09 ✗ | 0.272 vs 0.18 ✗ | 0.682 vs 0.54 ✗ |

| Table 8, before 1989: ours vs paper | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| intercept | 1.02% vs 0.35% ✗ | 1.19% vs 0.67% ✗ | 0.96% vs 0.71% ✗ | 0.95% vs 0.45% ✗ |
| market | -0.238 vs -0.434 ✗ | -0.215 vs -0.312 ✗ | -0.255 vs -0.289 ~ | -0.33 vs -0.434 ~ |
| smb | -0.259 vs -0.442 ✗ | -0.252 vs -0.332 ~ | -0.249 vs -0.275 ✓ | -0.363 vs -0.402 ✓ |
| hml | -0.0264 vs 0.0357 ✗ | -0.00938 vs 0.0316 ✗ | -0.0663 vs -0.0684 ✓ | -0.0558 vs -0.0698 ~ |
| momentum | -0.0804 vs 0.0129 ✗ | -0.0722 vs -0.0163 ✗ | -0.19 vs -0.0769 ✗ | -0.223 vs -0.158 ✗ |
| reversal | 0.19 vs 0.436 ✗ | 0.219 vs 0.333 ✗ | 0.262 vs 0.288 ✓ | 0.399 vs 0.452 ~ |
| r2 | 0.0588 vs 0.19 ✗ | 0.0972 vs 0.23 ✗ | 0.357 vs 0.26 ✗ | 0.657 vs 0.7 ✓ |

| Table 8, after 1988: ours vs paper | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| intercept | 0.35% vs 0.34% ✓ | 0.42% vs 0.42% ✓ | 0.64% vs 0.36% ✗ | 0.48% vs -0.07% ✗ |
| market | 0.178 vs 0.0734 ✗ | 0.04 vs 0.048 ~ | 0.000443 vs 0.00241 ✗ | -0.186 vs -0.0696 ✗ |
| smb | 0.116 vs -0.004 ✗ | 0.0026 vs 0.0289 ✗ | -0.0124 vs 0.0233 ✗ | -0.356 vs -0.0606 ✗ |
| hml | 0.0419 vs 0.0344 ~ | 0.00761 vs 0.0141 ✗ | 0.0235 vs 0.0183 ✗ | -0.0185 vs -0.082 ✗ |
| momentum | -0.0185 vs -0.00424 ✗ | -0.00725 vs -0.0227 ✗ | -0.0983 vs -0.0884 ~ | -0.226 vs -0.127 ✗ |
| reversal | -0.0808 vs -0.0626 ✗ | 0.000363 vs -0.0173 ✗ | 0.059 vs 0.024 ✗ | 0.289 vs 0.188 ✗ |
| r2 | 0.119 vs 0.02 ✗ | 0.0315 vs 0.04 ~ | 0.246 vs 0.19 ✗ | 0.737 vs 0.64 ~ |

With this series the 84 regression cells would score 16.0, against 8.0 with ST_Rev, and the total 266.5 instead of 258.5.

## Figures 2 and 3 (read back from the paper's images, not scored)

Figures 2 and 3 are 150-dpi rasters inside the PDF. `scripts/digitize_figures.py` reads them once and
writes `report/replication/reference/`; the numbers below are those readings against the cached
top-20 series. Figure 2's scale is fixed so its tallest bar equals Table 1 Panel A's top-20
maximum (13.295%), and the month offset scan below peaks at +0. The raster carries 1.19 columns per month
and draws each bar about three columns wide, so a bar is placed to within a month either side and
the annual sums (one signed reading per month) are the finest comparison it supports. Figure 3
is a log scale whose decades are drawn as rules, so its curves are read as levels.

Which series Figure 2 plots: the text says "the next-day trading rule", but the bars themselves
match the paper's own no-wait top-20 row (Table 1 Panel A) on 5 of 6 statistics and the one-day-wait row
(Panel B) on 1: their mean is 1.31% a month against Panel A's 1.44% and Panel B's 0.90%.
That test uses only the paper's numbers, so the comparison below is on our no-wait series, with the
one-day-wait series beside it for reference.

| Figure 2, monthly bars | ours, no wait | ours, one-day wait | paper, digitised |
|---|---|---|---|
| correlation of the positive bars | 0.52 | 0.50 | 1 by definition (399 months) |
| correlation of the negative bars | 0.58 | 0.51 | 1 by definition (75 months) |
| **correlation of the annual sums** | **0.75** | 0.75 | 1 by definition (40 years) |
| mean annual sum | 17.25% | 11.37% | 15.49% |
| best month offset, -3..+3 | +0 months | - | the alignment that maximises the two correlations |
| bars above 3.4% matched within 15% in the same month | 10 of 52 | - | - |
| tallest month | 1974-01 (9.55%) | 1974-01 (7.88%) | 1974-12 (13.30%) |
| deepest month | 1974-04 (-7.12%) | 1974-04 (-8.11%) | 1974-03 (-7.98%) |

| Figure 3, cumulative top 20, one-day wait | fully invested, ours | paper's figure | paper's Table 1 B mean, compounded | committed, ours | paper's figure | paper's Table 1 B mean, compounded |
|---|---|---|---|---|---|---|
| end level, 2002-12 | 87.8 | 39.7 | 68.3 | 14.3 | 11.5 | 11.7 |
| level at 1987-12 | 39.7 | 20.9 | - | 8.9 | 7.5 | - |
| peak (month) | 87.8 (2002-12) | 40.4 (2001-04) | - | 14.3 (2002-12) | 11.6 (2002-11) | - |
| share of the log rise made after 1987 | 18% | 18% | - | 18% | 18% | - |
| correlation of the log paths | 0.998 | 1 by definition | - | 0.997 | 1 by definition | - |

Paper curves are readable from 1964-07. Our curve and the constant-mean
illustration start independently from $1 before July 1963; neither is scaled to the paper.
The constant-mean illustration omits volatility drag and is not the paper's realized path.
Log-path correlation uses common months. The S&P 500 curve is not digitized.

| Table 1 Panel A, top 20: one month at the printed maximum | ours | 1975-01 set | control: 1974-01 set | paper |
|---|---|---|---|---|
| skewness | 0.81 | 1.28 | 1.18 | 1.39 |
| kurtosis | 7.09 | 9.99 | 9.83 | 10.54 |
| maximum | 9.55% | 13.30% | 13.30% | 13.30% |

Figure 2's tallest bar covers 1974-11 to 1975-01; the raster cannot split it further, so the
month set is the one of those where our return is highest (1975-01, 5.03%). Raising it to the printed
maximum moves skewness from 0.81 to 1.28 and kurtosis from 7.09 to 9.99 (paper
1.39 and 10.54); the control moves them to 1.18 and 9.83. The table measures the
size of the top-20 shape gap - about one month at the paper's maximum - and the window says where
the paper puts that month; it does not by itself show which month ours is missing.

Not scored: a value recovered from a 640-pixel image is evidence about which periods disagree, not a
value the paper prints.
