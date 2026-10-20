# Replication check: GGR (2006) Figure 1 and Tables 1-3 (vol_common)

Cells show ours / paper. ✓ within 10% of the paper, ~ within 25%, ✗ further.

Conventions that are our reading of the paper, not its words: fully invested
returns are eq. (2) across the portfolio, the value-weighted return of the long
positions minus that of the short positions, and committed returns scale it by
the share of selected pairs holding a position (this reproduces the paper's own
fully-invested/committed ratios of 1.58-1.81); trading prices continue the
formation normalization (GGR Figure 1); a no-trade day is a day with recorded
zero volume, a stock whose price never moves in the formation window is
excluded, and so is a stock with no recorded volume and an unchanged price on
more than 95% of the formation days (near-frozen quotes); a stock is never
matched with another security of its own issuer (same CRSP permco, e.g. two
share classes). The paper states none of these three exclusions beyond
screening out stocks with a no-trade day; REVIEW_NOTES section 18 gives the
evidence and the score without them (165.0).

## Summary

- Figure 1: reproduced
- Table 1: Cells: 88; ✓ 50 (within 10%), ~ 16 (within 25%), ✗ 22.
- Table 2 Panel A: Cells: 24; ✓ 14 (within 10%), ~ 9 (within 25%), ✗ 1.
- Table 2 Panel B: Cells: 40; ✓ 27 (within 10%), ~ 3 (within 25%), ✗ 10.
- Table 3: Cells: 139; ✓ 41 (within 10%), ~ 47 (within 25%), ✗ 51.

## Figure 1 (Kennecott vs Uniroyal, trading Aug 1963 - Jan 1964, no wait)

| check | ours | paper | match |
|---|---|---|---|
| pair formed (rank) | 4 | top 5 | ✓ |
| trades (open day, close day) | [(8, 35), (46, 56), (76, 83), (85, 99), (108, 125)] | [(7, 35), (46, 55), (74, 82), (86, 99), (108, 126)] (read off the chart) | ✓ (±3 days) |
| day-0 levels (formation end) | [1.1006, 1.106] | about 1.10 | ✓ |

Plot: `results/replication/figures/figure1.png`.

## Table 1 Panel A (no wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean (fully invested) | 1.34% / 1.31% ✓ | 1.47% / 1.44% ✓ | 1.03% / 1.08% ✓ | 1.05% / 1.10% ✓ |
| nw_se | 0.15% / 0.15% ✓ | 0.13% / 0.12% ✓ | 0.09% / 0.09% ✓ | 0.10% / 0.10% ✓ |
| t_stat | 8.75 / 8.84 ✓ | 11.3 / 11.6 ✓ | 12 / 11.5 ✓ | 10.8 / 11.2 ✓ |
| median | 1.19% / 1.19% ✓ | 1.28% / 1.23% ✓ | 0.94% / 0.95% ✓ | 0.75% / 0.73% ✓ |
| std | 2.43% / 2.28% ✓ | 1.73% / 1.69% ✓ | 1.60% / 1.54% ✓ | 1.99% / 1.67% ~ |
| skew | 0.205 / 0.62 ✗ | 0.849 / 1.39 ✗ | 0.794 / 1.34 ✗ | 1.29 / 3.42 ✗ |
| kurtosis | 9.07 / 7.81 ~ | 7.96 / 10.5 ~ | 6.26 / 10.3 ✗ | 16.1 / 25.2 ✗ |
| min | -14.88% / -10.57% ✗ | -7.90% / -6.63% ~ | -4.00% / -3.86% ✓ | -12.62% / -2.72% ✗ |
| max | 12.50% / 14.72% ~ | 10.26% / 13.30% ~ | 10.38% / 12.68% ~ | 14.13% / 17.18% ~ |
| share_negative | 0.266 / 0.26 ✓ | 0.156 / 0.15 ✓ | 0.249 / 0.21 ~ | 0.238 / 0.17 ✗ |
| mean (committed) | 0.81% / 0.78% ✓ | 0.88% / 0.80% ✓ | 0.66% / 0.68% ✓ | 0.58% / 0.61% ✓ |

## Table 1 Panel B (one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean (fully invested) | 0.76% / 0.74% ✓ | 0.96% / 0.90% ✓ | 0.81% / 0.80% ✓ | 0.79% / 0.71% ~ |
| nw_se | 0.11% / 0.12% ✓ | 0.10% / 0.10% ✓ | 0.08% / 0.08% ✓ | 0.09% / 0.09% ✓ |
| t_stat | 6.68 / 6.26 ✓ | 9.69 / 9.29 ✓ | 10.4 / 9.4 ~ | 8.48 / 7.92 ✓ |
| median | 0.72% / 0.70% ✓ | 0.87% / 0.69% ✗ | 0.77% / 0.69% ~ | 0.53% / 0.41% ✗ |
| std | 2.08% / 2.10% ✓ | 1.50% / 1.53% ✓ | 1.48% / 1.44% ✓ | 1.87% / 1.58% ~ |
| skew | -0.444 / 0.34 ✗ | 0.193 / 1.45 ✗ | 0.227 / 0.98 ✗ | 1.02 / 3.32 ✗ |
| kurtosis | 10.7 / 10.6 ✓ | 8.54 / 16.1 ✗ | 4.07 / 7.78 ✗ | 15.6 / 25.7 ✗ |
| min | -14.95% / -12.63% ~ | -8.88% / -8.22% ✓ | -4.06% / -4.27% ✓ | -12.34% / -2.95% ✗ |
| max | 9.76% / 14.35% ✗ | 7.64% / 13.49% ✗ | 6.05% / 10.46% ✗ | 12.52% / 16.32% ~ |
| share_negative | 0.348 / 0.35 ✓ | 0.247 / 0.23 ✓ | 0.272 / 0.28 ✓ | 0.295 / 0.32 ✓ |
| mean (committed) | 0.47% / 0.46% ✓ | 0.59% / 0.52% ~ | 0.52% / 0.50% ✓ | 0.43% / 0.40% ✓ |

Cells: 88; ✓ 50 (within 10%), ~ 16 (within 25%), ✗ 22.

## Table 2 Panel A (one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| avg_price_deviation_trigger | 0.0392 / 0.0476 ~ | 0.0446 / 0.0528 ~ | 0.0686 / 0.0756 ✓ | 0.165 / 0.169 ✓ |
| avg_pairs_traded_per_period | 4.91 / 4.81 ✓ | 19.7 / 19.3 ✓ | 19.7 / 19.4 ✓ | 1.9e+03 / 1.94e+03 ✓ |
| avg_round_trips_per_pair | 2.32 / 2.02 ~ | 2.2 / 1.96 ~ | 1.9 / 1.78 ✓ | 1.7 / 1.62 ✓ |
| std_round_trips_per_pair | 0.732 / 0.62 ~ | 0.493 / 0.4 ~ | 0.305 / 0.27 ~ | 0.169 / 0.16 ✓ |
| avg_time_open_months | 3.97 / 3.75 ✓ | 3.94 / 3.76 ✓ | 4.12 / 3.98 ✓ | 4.05 / 3.97 ✓ |
| std_time_open_months | 0.731 / 0.8 ✓ | 0.502 / 0.45 ~ | 0.441 / 0.38 ~ | 0.312 / 0.17 ✗ |

Cells: 24; ✓ 14 (within 10%), ~ 9 (within 25%), ✗ 1.

## Table 2 Panel B (composition)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| avg_size_decile | 2.65 / 2.54 ✓ | 2.74 / 2.71 ✓ | 3.15 / 3.41 ✓ | 4.63 / 4.57 ✓ |
| weight_top3_deciles | 0.768 / 0.78 ✓ | 0.738 / 0.74 ✓ | 0.639 / 0.58 ~ | 0.406 / 0.4 ✓ |
| weight_top5_deciles | 0.92 / 0.91 ✓ | 0.923 / 0.91 ✓ | 0.841 / 0.79 ✓ | 0.626 / 0.62 ✓ |
| share_mixed_decile_pairs | 0.664 / 0.66 ✓ | 0.692 / 0.69 ✓ | 0.734 / 0.75 ✓ | 0.812 / 0.82 ✓ |
| avg_decile_diff_mixed_pairs | 1.12 / 0.97 ~ | 1.22 / 0.97 ✗ | 1.61 / 0.97 ✗ | 2.15 / 0.98 ✗ |
| weight_utilities | 0.777 / 0.72 ✓ | 0.772 / 0.71 ✓ | 0.304 / 0.32 ✓ | 0.0906 / 0.08 ~ |
| weight_transportation | 0.0118 / 0.02 ✗ | 0.0105 / 0.02 ✗ | 0.0184 / 0.02 ✓ | 0.0296 / 0.03 ✓ |
| weight_financials | 0.141 / 0.11 ✗ | 0.14 / 0.13 ✓ | 0.264 / 0.26 ✓ | 0.15 / 0.16 ✓ |
| weight_industrials | 0.0703 / 0.15 ✗ | 0.0777 / 0.14 ✗ | 0.413 / 0.4 ✓ | 0.73 / 0.73 ✓ |
| share_mixed_sector_pairs | 0.103 / 0.2 ✗ | 0.128 / 0.22 ✗ | 0.401 / 0.44 ✓ | 0.308 / 0.33 ✓ |

Cells: 40; ✓ 27 (within 10%), ~ 3 (within 25%), ✗ 10.

## Table 3 stocks per cohort

| sector | ours / paper |
|---|---|
| Utilities | 161 / 156 ✓ |
| Transportation | 61.1 / 61 ✓ |
| Financials | 349 / 371 ✓ |
| Industrials | 1.72e+03 / 1.73e+03 ✓ |

## Table 3: Utilities (fully invested, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 1.00% / 0.91% ~ | 1.24% / 1.08% ~ | 0.65% / 0.93% ✗ | 1.07% / 1.04% ✓ |
| t_stat | 8.11 / 7.37 ✓ | 10.5 / 10.3 ✓ | 2.98 / 6.11 ✗ | 9.01 / 10.5 ~ |
| median | 0.90% / 0.83% ✓ | 1.09% / 0.94% ~ | 0.67% / 0.66% ✓ | 1.01% / 0.97% ✓ |
| std | 2.12% / 2.15% ✓ | 1.70% / 1.65% ✓ | 3.42% / 2.64% ✗ | 1.77% / 1.47% ~ |
| skew | -0.549 / 0.44 ✗ | 0.506 / 0.76 ✗ | 1 / 0.66 ✗ | 0.522 / 1.39 ✗ |
| kurtosis | 11.1 / 13.7 ~ | 10.1 / 12.4 ~ | 13.7 / 5.52 ✗ | 7.65 / 12.7 ✗ |
| min | -14.95% / -12.35% ~ | -8.70% / -8.75% ✓ | -12.08% / -7.87% ✗ | -6.19% / -3.52% ✗ |
| max | 9.76% / 16.56% ✗ | 10.46% / 12.73% ~ | 25.66% / 12.13% ✗ | 10.19% / 12.88% ~ |
| share_negative | 0.304 / 0.28 ✓ | 0.177 / 0.19 ✓ | 0.359 / 0.35 ✓ | 0.205 / 0.18 ~ |

## Table 3: Transportation (fully invested, one-day wait)

| statistic | top5 | top20 | all |
|---|---|---|---|
| mean | 0.93% / 0.50% ✗ | 0.76% / 0.58% ✗ | 0.73% / 0.44% ✗ |
| t_stat | 5.86 / 2.98 ✗ | 5.8 / 4.26 ✗ | 5.62 / 3.07 ✗ |
| median | 0.97% / 0.59% ✗ | 0.62% / 0.55% ~ | 0.55% / 0.34% ✗ |
| std | 3.75% / 3.89% ✓ | 2.80% / 2.94% ✓ | 2.81% / 2.87% ✓ |
| skew | 0.0267 / -0.5 ✗ | 0.0609 / -0.11 ✗ | 0.492 / 0.53 ✓ |
| kurtosis | 3.16 / 4.98 ✗ | 3.9 / 5 ~ | 4.14 / 5.89 ✗ |
| min | -9.67% / -19.57% ✗ | -10.94% / -12.47% ~ | -7.80% / -12.53% ✗ |
| max | 12.28% / 10.96% ~ | 9.83% / 11.10% ~ | 12.51% / 13.56% ✓ |
| share_negative | 0.371 / 0.44 ~ | 0.403 / 0.42 ✓ | 0.395 / 0.44 ~ |

## Table 3: Financials (fully invested, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 0.72% / 0.68% ✓ | 0.89% / 0.78% ~ | 1.05% / 0.85% ~ | 0.85% / 0.73% ~ |
| t_stat | 5.48 / 4.79 ~ | 9.06 / 7.6 ~ | 8.69 / 7.12 ~ | 8.76 / 7.62 ~ |
| median | 0.68% / 0.56% ~ | 0.81% / 0.61% ✗ | 0.93% / 0.66% ✗ | 0.73% / 0.51% ✗ |
| std | 2.71% / 2.60% ✓ | 1.80% / 1.79% ✓ | 1.98% / 2.36% ~ | 1.85% / 1.81% ✓ |
| skew | 0.423 / 0.81 ✗ | 0.389 / 0.61 ✗ | 1.07 / 1.98 ✗ | 0.84 / 2.64 ✗ |
| kurtosis | 7.12 / 6.37 ~ | 5.15 / 6.48 ~ | 7.34 / 18.3 ✗ | 6.61 / 21.2 ✗ |
| min | -12.47% / -8.20% ✗ | -7.23% / -7.81% ✓ | -3.98% / -10.05% ✗ | -5.79% / -4.45% ✗ |
| max | 16.12% / 14.93% ✓ | 9.91% / 10.64% ✓ | 11.49% / 19.58% ✗ | 11.17% / 17.21% ✗ |
| share_negative | 0.38 / 0.4 ✓ | 0.306 / 0.33 ✓ | 0.253 / 0.32 ~ | 0.297 / 0.34 ~ |

## Table 3: Industrials (fully invested, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 0.61% / 0.49% ~ | 0.72% / 0.61% ~ | 0.84% / 0.66% ✗ | 0.79% / 0.71% ~ |
| t_stat | 5.08 / 4.11 ~ | 8.47 / 6.93 ~ | 8.5 / 6.8 ~ | 7.68 / 7.52 ✓ |
| median | 0.63% / 0.29% ✗ | 0.65% / 0.55% ~ | 0.73% / 0.55% ✗ | 0.55% / 0.40% ✗ |
| std | 2.38% / 2.36% ✓ | 1.70% / 1.60% ✓ | 1.87% / 1.82% ✓ | 2.07% / 1.67% ~ |
| skew | 0.0624 / 0.4 ✗ | 0.476 / 0.43 ~ | 0.77 / 0.94 ~ | 1.04 / 2.97 ✗ |
| kurtosis | 5.01 / 4.94 ✓ | 6.8 / 4.75 ✗ | 6.23 / 7.65 ~ | 16.4 / 20.9 ~ |
| min | -10.04% / -10.02% ✓ | -6.44% / -4.79% ✗ | -5.62% / -5.41% ✓ | -13.79% / -3.43% ✗ |
| max | 10.81% / 10.55% ✓ | 10.06% / 8.02% ✗ | 11.12% / 11.62% ✓ | 14.41% / 16.07% ~ |
| share_negative | 0.369 / 0.42 ~ | 0.314 / 0.36 ~ | 0.31 / 0.35 ~ | 0.314 / 0.34 ✓ |

Cells: 139; ✓ 41 (within 10%), ~ 47 (within 25%), ✗ 51.
