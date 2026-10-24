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
evidence, and SCORE_LOG.md the score without them. Telephone utilities are
SIC 4811, the 1972 telephone code that CRSP carries before 1987 (4810 and the
1987 codes 4812-4819 are Industrials); the paper gives no SIC ranges, and
REVIEW_NOTES section 20 gives the evidence. Waste management (SIC
4950-4959) is Industrials, following GICS; S&P's contemporaneous scheme is
unverified and the 1999 draft is neutral on it, so this is a classification
choice worth five cells in the Utilities 101-120 band (REVIEW_NOTES section
24). The trigger's sigma is the
formation spread's root mean square about zero, sqrt(SSD/N), not its standard
deviation about its mean; the paper says "historical standard deviations",
and REVIEW_NOTES section 21 gives the evidence.

The score total, its history and how it is counted live in SCORE_LOG.md. The
open gaps are in OPEN_QUESTIONS.md; the 1999 NBER draft is scored separately
in EDITION_1999.md.

## Summary

- Figure 1: reproduced
- Table 1: Cells: 88; ✓ 52 (within 10%), ~ 14 (within 25%), ✗ 22.
- Table 2 Panel A: Cells: 24; ✓ 17 (within 10%), ~ 7 (within 25%), ✗ 0.
- Table 2 Panel B: Cells: 40; ✓ 28 (within 10%), ~ 2 (within 25%), ✗ 10.
- Table 3: Cells: 139; ✓ 52 (within 10%), ~ 46 (within 25%), ✗ 41.
- Score: 183.5 of 291 compared cells (✓ = 1, ~ = ½, ✗ = 0); history in SCORE_LOG.md.

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
| mean (fully invested) | 1.30% / 1.31% ✓ | 1.45% / 1.44% ✓ | 1.01% / 1.08% ✓ | 1.04% / 1.10% ✓ |
| nw_se | 0.15% / 0.15% ✓ | 0.13% / 0.12% ✓ | 0.08% / 0.09% ✓ | 0.10% / 0.10% ✓ |
| t_stat | 8.53 / 8.84 ✓ | 11.2 / 11.6 ✓ | 12 / 11.5 ✓ | 10.7 / 11.2 ✓ |
| median | 1.13% / 1.19% ✓ | 1.27% / 1.23% ✓ | 0.91% / 0.95% ✓ | 0.73% / 0.73% ✓ |
| std | 2.41% / 2.28% ✓ | 1.74% / 1.69% ✓ | 1.59% / 1.54% ✓ | 2.00% / 1.67% ~ |
| skew | 0.185 / 0.62 ✗ | 0.847 / 1.39 ✗ | 0.735 / 1.34 ✗ | 1.3 / 3.42 ✗ |
| kurtosis | 9.15 / 7.81 ~ | 7.92 / 10.5 ~ | 5.85 / 10.3 ✗ | 15.9 / 25.2 ✗ |
| min | -14.82% / -10.57% ✗ | -7.89% / -6.63% ~ | -3.92% / -3.86% ✓ | -12.59% / -2.72% ✗ |
| max | 12.84% / 14.72% ~ | 10.51% / 13.30% ~ | 10.04% / 12.68% ~ | 14.12% / 17.18% ~ |
| share_negative | 0.259 / 0.26 ✓ | 0.165 / 0.15 ✓ | 0.249 / 0.21 ~ | 0.241 / 0.17 ✗ |
| mean (committed) | 0.77% / 0.78% ✓ | 0.85% / 0.80% ✓ | 0.63% / 0.68% ✓ | 0.56% / 0.61% ✓ |

## Table 1 Panel B (one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean (fully invested) | 0.74% / 0.74% ✓ | 0.95% / 0.90% ✓ | 0.82% / 0.80% ✓ | 0.78% / 0.71% ✓ |
| nw_se | 0.11% / 0.12% ✓ | 0.10% / 0.10% ✓ | 0.08% / 0.08% ✓ | 0.09% / 0.09% ✓ |
| t_stat | 6.53 / 6.26 ✓ | 9.6 / 9.29 ✓ | 10.4 / 9.4 ~ | 8.37 / 7.92 ✓ |
| median | 0.70% / 0.70% ✓ | 0.88% / 0.69% ✗ | 0.76% / 0.69% ~ | 0.53% / 0.41% ✗ |
| std | 2.08% / 2.10% ✓ | 1.52% / 1.53% ✓ | 1.50% / 1.44% ✓ | 1.89% / 1.58% ~ |
| skew | -0.502 / 0.34 ✗ | 0.181 / 1.45 ✗ | 0.236 / 0.98 ✗ | 1.03 / 3.32 ✗ |
| kurtosis | 11 / 10.6 ✓ | 8.44 / 16.1 ✗ | 4.06 / 7.78 ✗ | 15.5 / 25.7 ✗ |
| min | -15.16% / -12.63% ~ | -8.95% / -8.22% ✓ | -4.11% / -4.27% ✓ | -12.38% / -2.95% ✗ |
| max | 9.62% / 14.35% ✗ | 7.67% / 13.49% ✗ | 6.35% / 10.46% ✗ | 12.55% / 16.32% ~ |
| share_negative | 0.35 / 0.35 ✓ | 0.251 / 0.23 ✓ | 0.278 / 0.28 ✓ | 0.306 / 0.32 ✓ |
| mean (committed) | 0.45% / 0.46% ✓ | 0.56% / 0.52% ✓ | 0.51% / 0.50% ✓ | 0.41% / 0.40% ✓ |

Cells: 88; ✓ 52 (within 10%), ~ 14 (within 25%), ✗ 22.

## Table 2 Panel A (one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| avg_price_deviation_trigger | 0.0409 / 0.0476 ~ | 0.0466 / 0.0528 ~ | 0.0715 / 0.0756 ✓ | 0.173 / 0.169 ✓ |
| avg_pairs_traded_per_period | 4.9 / 4.81 ✓ | 19.7 / 19.3 ✓ | 19.6 / 19.4 ✓ | 1.88e+03 / 1.94e+03 ✓ |
| avg_round_trips_per_pair | 2.24 / 2.02 ~ | 2.11 / 1.96 ✓ | 1.84 / 1.78 ✓ | 1.66 / 1.62 ✓ |
| std_round_trips_per_pair | 0.686 / 0.62 ~ | 0.458 / 0.4 ~ | 0.287 / 0.27 ✓ | 0.156 / 0.16 ✓ |
| avg_time_open_months | 3.93 / 3.75 ✓ | 3.88 / 3.76 ✓ | 4.08 / 3.98 ✓ | 4.01 / 3.97 ✓ |
| std_time_open_months | 0.707 / 0.8 ~ | 0.461 / 0.45 ✓ | 0.368 / 0.38 ✓ | 0.199 / 0.17 ~ |

Cells: 24; ✓ 17 (within 10%), ~ 7 (within 25%), ✗ 0.

## Table 2 Panel B (composition)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| avg_size_decile | 2.65 / 2.54 ✓ | 2.74 / 2.71 ✓ | 3.15 / 3.41 ✓ | 4.63 / 4.57 ✓ |
| weight_top3_deciles | 0.768 / 0.78 ✓ | 0.738 / 0.74 ✓ | 0.639 / 0.58 ~ | 0.406 / 0.4 ✓ |
| weight_top5_deciles | 0.92 / 0.91 ✓ | 0.923 / 0.91 ✓ | 0.841 / 0.79 ✓ | 0.626 / 0.62 ✓ |
| share_mixed_decile_pairs | 0.664 / 0.66 ✓ | 0.692 / 0.69 ✓ | 0.734 / 0.75 ✓ | 0.812 / 0.82 ✓ |
| avg_decile_diff_mixed_pairs | 1.12 / 0.97 ~ | 1.22 / 0.97 ✗ | 1.61 / 0.97 ✗ | 2.15 / 0.98 ✗ |
| weight_utilities | 0.774 / 0.72 ✓ | 0.769 / 0.71 ✓ | 0.299 / 0.32 ✓ | 0.0827 / 0.08 ✓ |
| weight_transportation | 0.0118 / 0.02 ✗ | 0.0105 / 0.02 ✗ | 0.0185 / 0.02 ✓ | 0.0298 / 0.03 ✓ |
| weight_financials | 0.14 / 0.11 ✗ | 0.139 / 0.13 ✓ | 0.264 / 0.26 ✓ | 0.149 / 0.16 ✓ |
| weight_industrials | 0.0745 / 0.15 ✗ | 0.0819 / 0.14 ✗ | 0.419 / 0.4 ✓ | 0.739 / 0.73 ✓ |
| share_mixed_sector_pairs | 0.105 / 0.2 ✗ | 0.13 / 0.22 ✗ | 0.403 / 0.44 ✓ | 0.297 / 0.33 ✓ |

Cells: 40; ✓ 28 (within 10%), ~ 2 (within 25%), ✗ 10.

## Table 3 stocks per cohort

| sector | ours / paper |
|---|---|
| Utilities | 137 / 156 ~ |
| Transportation | 61.4 / 61 ✓ |
| Financials | 347 / 371 ✓ |
| Industrials | 1.75e+03 / 1.73e+03 ✓ |

## Table 3: Utilities (fully invested, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 1.00% / 0.91% ~ | 1.24% / 1.08% ~ | 0.95% / 0.93% ✓ | 1.19% / 1.04% ~ |
| t_stat | 8.08 / 7.37 ✓ | 10.5 / 10.3 ✓ | 5.76 / 6.11 ✓ | 11.4 / 10.5 ✓ |
| median | 0.95% / 0.83% ~ | 1.08% / 0.94% ~ | 0.85% / 0.66% ✗ | 1.08% / 0.97% ~ |
| std | 2.12% / 2.15% ✓ | 1.72% / 1.65% ✓ | 2.33% / 2.64% ~ | 1.55% / 1.47% ✓ |
| skew | -0.574 / 0.44 ✗ | 0.507 / 0.76 ✗ | 0.517 / 0.66 ~ | 0.787 / 1.39 ✗ |
| kurtosis | 11.4 / 13.7 ~ | 10.5 / 12.4 ~ | 5.97 / 5.52 ✓ | 7.66 / 12.7 ✗ |
| min | -15.16% / -12.35% ~ | -8.92% / -8.75% ✓ | -7.80% / -7.87% ✓ | -3.80% / -3.52% ✓ |
| max | 9.62% / 16.56% ✗ | 11.07% / 12.73% ~ | 12.61% / 12.13% ✓ | 10.24% / 12.88% ~ |
| share_negative | 0.304 / 0.28 ✓ | 0.181 / 0.19 ✓ | 0.324 / 0.35 ✓ | 0.165 / 0.18 ✓ |

## Table 3: Transportation (fully invested, one-day wait)

| statistic | top5 | top20 | all |
|---|---|---|---|
| mean | 0.96% / 0.50% ✗ | 0.74% / 0.58% ✗ | 0.72% / 0.44% ✗ |
| t_stat | 5.65 / 2.98 ✗ | 5.53 / 4.26 ✗ | 5.38 / 3.07 ✗ |
| median | 0.99% / 0.59% ✗ | 0.55% / 0.55% ✓ | 0.63% / 0.34% ✗ |
| std | 3.93% / 3.89% ✓ | 2.93% / 2.94% ✓ | 2.96% / 2.87% ✓ |
| skew | 0.0918 / -0.5 ✗ | 0.0873 / -0.11 ✗ | 0.419 / 0.53 ~ |
| kurtosis | 3.1 / 4.98 ✗ | 3.84 / 5 ~ | 3.88 / 5.89 ✗ |
| min | -9.02% / -19.57% ✗ | -11.13% / -12.47% ~ | -7.79% / -12.53% ✗ |
| max | 13.41% / 10.96% ~ | 9.72% / 11.10% ~ | 12.03% / 13.56% ~ |
| share_negative | 0.397 / 0.44 ✓ | 0.388 / 0.42 ✓ | 0.388 / 0.44 ~ |

## Table 3: Financials (fully invested, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 0.70% / 0.68% ✓ | 0.88% / 0.78% ~ | 1.10% / 0.85% ✗ | 0.86% / 0.73% ~ |
| t_stat | 5.16 / 4.79 ✓ | 8.91 / 7.6 ~ | 8.23 / 7.12 ~ | 8.69 / 7.62 ~ |
| median | 0.67% / 0.56% ~ | 0.77% / 0.61% ✗ | 1.00% / 0.66% ✗ | 0.74% / 0.51% ✗ |
| std | 2.76% / 2.60% ✓ | 1.85% / 1.79% ✓ | 2.18% / 2.36% ✓ | 1.91% / 1.81% ✓ |
| skew | 0.339 / 0.81 ✗ | 0.34 / 0.61 ✗ | 2.28 / 1.98 ~ | 0.736 / 2.64 ✗ |
| kurtosis | 7.39 / 6.37 ~ | 5.15 / 6.48 ~ | 18 / 18.3 ✓ | 6.26 / 21.2 ✗ |
| min | -12.85% / -8.20% ✗ | -7.28% / -7.81% ✓ | -3.74% / -10.05% ✗ | -5.70% / -4.45% ✗ |
| max | 17.28% / 14.93% ~ | 9.74% / 10.64% ✓ | 19.27% / 19.58% ✓ | 11.17% / 17.21% ✗ |
| share_negative | 0.38 / 0.4 ✓ | 0.297 / 0.33 ✓ | 0.259 / 0.32 ~ | 0.31 / 0.34 ✓ |

## Table 3: Industrials (fully invested, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 0.61% / 0.49% ~ | 0.74% / 0.61% ~ | 0.80% / 0.66% ~ | 0.78% / 0.71% ✓ |
| t_stat | 5.05 / 4.11 ~ | 8.57 / 6.93 ~ | 8.22 / 6.8 ~ | 7.52 / 7.52 ✓ |
| median | 0.58% / 0.29% ✗ | 0.66% / 0.55% ~ | 0.73% / 0.55% ✗ | 0.55% / 0.40% ✗ |
| std | 2.37% / 2.36% ✓ | 1.72% / 1.60% ✓ | 1.87% / 1.82% ✓ | 2.08% / 1.67% ~ |
| skew | 0.019 / 0.4 ✗ | 0.588 / 0.43 ✗ | 0.723 / 0.94 ~ | 1.13 / 2.97 ✗ |
| kurtosis | 5.14 / 4.94 ✓ | 6.67 / 4.75 ✗ | 5.57 / 7.65 ✗ | 16 / 20.9 ~ |
| min | -10.66% / -10.02% ✓ | -5.12% / -4.79% ✓ | -4.90% / -5.41% ✓ | -13.46% / -3.43% ✗ |
| max | 10.90% / 10.55% ✓ | 9.83% / 8.02% ~ | 9.83% / 11.62% ~ | 14.81% / 16.07% ✓ |
| share_negative | 0.369 / 0.42 ~ | 0.316 / 0.36 ~ | 0.329 / 0.35 ✓ | 0.321 / 0.34 ✓ |

Cells: 139; ✓ 52 (within 10%), ~ 46 (within 25%), ✗ 41.
