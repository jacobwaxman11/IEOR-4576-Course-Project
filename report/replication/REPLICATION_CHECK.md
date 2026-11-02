# Replication check: GGR (2006) Figures 1 and 4, Tables 1-4, 5 Panel A, 7 and 8 (vol_common)

Cells show ours / paper. ✓ within 10% of the paper, ~ within 25%, ✗ further.

Conventions that are our reading of the paper, not its words: fully invested
returns are eq. (2) across the portfolio, the value-weighted return of the long
positions minus that of the short positions, each position weighted by eq. (3)
applied to its own return (a long by its value, a short by prod(1 - r), which
shrinks as the shorted stock rises), and committed returns scale it by the
share of selected pairs holding a position (fully-invested/committed ratios
1.61-2.02 against the paper's 1.58-1.81, the "all" column furthest off);
trading prices continue the
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
and REVIEW_NOTES section 21 gives the evidence. The one-day wait skips a
signal whose prices cross back on the intervening day; the paper states no
such condition, and dropping it changes no mark (REVIEW_NOTES section 47).
Tables 1 and 3 compound the long and the short book to monthly returns
and then subtract, as the paper's own Table 1 = Table 7 identity requires
(pp. 807 and 821; REVIEW_NOTES sections 33 and 54).
The short-position weight is also our reading: weighting a short by the
shorted stock's value instead (--short-weights value) gives SCORE_LOG.md row
12. The weight is floored at zero; 780 of the 2,968,816 Table 1 positions
carry zero weight after their shorted stock doubles in a day, none of them in
the top 5, top 20 or 101-120 portfolios, so the floor acts on the "all"
columns. REVIEW_NOTES section 29 gives the evidence and the objections (Table
8 before 1989 and the 1999 draft).

The paper's five-factor block rests on a reversal factor it does not name: its
printed statistics pin a 2.19%/month premium at 7.23% monthly volatility, and the
Table 8 Panel A loadings need a reversal factor whose variance Mkt-RF/SMB/HML/UMD
already explain 95% of, where French ST_Rev is 26% explained. That is implausible
rather than contradictory -- PAPER_CONSISTENCY.md reports the arithmetic, the
joint test and its rounding sensitivity, and `scripts/paper_consistency.py`
reproduces them -- so a ✗ in those rows is a gap here as much as in the source.

The score total, its history and how it is counted live in SCORE_LOG.md. The
open gaps are in OPEN_QUESTIONS.md; the 1999 NBER draft is scored separately
in EDITION_1999.md.

## Summary

- Figure 1: reproduced
- Table 1: Cells: 88; ✓ 47 (within 10%), ~ 17 (within 25%), ✗ 24.
- Table 2 Panel A: Cells: 24; ✓ 17 (within 10%), ~ 7 (within 25%), ✗ 0.
- Table 2 Panel B: Cells: 40; ✓ 28 (within 10%), ~ 1 (within 25%), ✗ 11.
- Table 3: Cells: 139; ✓ 58 (within 10%), ~ 44 (within 25%), ✗ 37.
- Table 7: Cells: 32; ✓ 23 (within 10%), ~ 7 (within 25%), ✗ 2.
- Table 4: Cells: 60; ✓ 16 (within 10%), ~ 11 (within 25%), ✗ 33.
- Table 5 Panel A: Cells: 20; ✓ 7 (within 10%), ~ 6 (within 25%), ✗ 7.
- Table 8: Cells: 72; ✓ 11 (within 10%), ~ 13 (within 25%), ✗ 48.
- Figure 4: Cells: 6; ✓ 0 (within 10%), ~ 2 (within 25%), ✗ 4.
- Score: 261.0 of 481 compared cells (✓ = 1, ~ = ½, ✗ = 0); history in SCORE_LOG.md.
- Tables 1-3 alone: 184.5 of 291, the cell set of SCORE_LOG.md rows 1-13.
- Tables 1-3 and 7 alone: 211.0 of 323, the cell set of SCORE_LOG.md row 14.

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
| mean (fully invested) | 1.27% / 1.31% ✓ | 1.39% / 1.44% ✓ | 0.97% / 1.08% ~ | 0.91% / 1.10% ~ |
| nw_se | 0.15% / 0.15% ✓ | 0.12% / 0.12% ✓ | 0.08% / 0.09% ~ | 0.09% / 0.10% ~ |
| t_stat | 8.58 / 8.84 ✓ | 11.2 / 11.6 ✓ | 11.8 / 11.5 ✓ | 10.5 / 11.2 ✓ |
| median | 1.12% / 1.19% ✓ | 1.23% / 1.23% ✓ | 0.89% / 0.95% ✓ | 0.65% / 0.73% ~ |
| std | 2.31% / 2.28% ✓ | 1.67% / 1.69% ✓ | 1.52% / 1.54% ✓ | 1.59% / 1.67% ✓ |
| skew | 0.165 / 0.62 ✗ | 0.791 / 1.39 ✗ | 0.635 / 1.34 ✗ | 2.16 / 3.42 ✗ |
| kurtosis | 7.61 / 7.81 ✓ | 7.23 / 10.5 ✗ | 5.12 / 10.3 ✗ | 12.8 / 25.2 ✗ |
| min | -13.11% / -10.57% ~ | -7.25% / -6.63% ✓ | -4.05% / -3.86% ✓ | -3.62% / -2.72% ✗ |
| max | 11.04% / 14.72% ~ | 9.34% / 13.30% ✗ | 8.05% / 12.68% ✗ | 12.04% / 17.18% ✗ |
| share_negative | 0.266 / 0.26 ✓ | 0.173 / 0.15 ~ | 0.238 / 0.21 ~ | 0.253 / 0.17 ✗ |
| mean (committed) | 0.75% / 0.78% ✓ | 0.81% / 0.80% ✓ | 0.60% / 0.68% ~ | 0.47% / 0.61% ~ |

## Table 1 Panel B (one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean (fully invested) | 0.72% / 0.74% ✓ | 0.89% / 0.90% ✓ | 0.76% / 0.80% ✓ | 0.63% / 0.71% ~ |
| nw_se | 0.11% / 0.12% ✓ | 0.10% / 0.10% ✓ | 0.08% / 0.08% ✓ | 0.09% / 0.09% ✓ |
| t_stat | 6.45 / 6.26 ✓ | 9.28 / 9.29 ✓ | 9.85 / 9.4 ✓ | 7 / 7.92 ~ |
| median | 0.70% / 0.70% ✓ | 0.81% / 0.69% ~ | 0.70% / 0.69% ✓ | 0.38% / 0.41% ✓ |
| std | 2.02% / 2.10% ✓ | 1.47% / 1.53% ✓ | 1.45% / 1.44% ✓ | 1.55% / 1.58% ✓ |
| skew | -0.329 / 0.34 ✗ | 0.261 / 1.45 ✗ | 0.241 / 0.98 ✗ | 1.96 / 3.32 ✗ |
| kurtosis | 9.07 / 10.6 ~ | 7.72 / 16.1 ✗ | 4.23 / 7.78 ✗ | 12.3 / 25.7 ✗ |
| min | -13.56% / -12.63% ✓ | -8.21% / -8.22% ✓ | -4.38% / -4.27% ✓ | -3.98% / -2.95% ✗ |
| max | 9.72% / 14.35% ✗ | 7.57% / 13.49% ✗ | 6.59% / 10.46% ✗ | 11.93% / 16.32% ✗ |
| share_negative | 0.359 / 0.35 ✓ | 0.272 / 0.23 ~ | 0.283 / 0.28 ✓ | 0.338 / 0.32 ✓ |
| mean (committed) | 0.43% / 0.46% ✓ | 0.52% / 0.52% ✓ | 0.47% / 0.50% ✓ | 0.31% / 0.40% ~ |

Cells: 88; ✓ 47 (within 10%), ~ 17 (within 25%), ✗ 24.

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
| avg_decile_diff_mixed_pairs | 1.67 / 0.97 ✗ | 1.74 / 0.97 ✗ | 2.17 / 0.97 ✗ | 2.64 / 0.98 ✗ |
| weight_utilities | 0.774 / 0.72 ✓ | 0.769 / 0.71 ✓ | 0.299 / 0.32 ✓ | 0.0827 / 0.08 ✓ |
| weight_transportation | 0.0118 / 0.02 ✗ | 0.0105 / 0.02 ✗ | 0.0185 / 0.02 ✓ | 0.0298 / 0.03 ✓ |
| weight_financials | 0.14 / 0.11 ✗ | 0.139 / 0.13 ✓ | 0.264 / 0.26 ✓ | 0.149 / 0.16 ✓ |
| weight_industrials | 0.0745 / 0.15 ✗ | 0.0819 / 0.14 ✗ | 0.419 / 0.4 ✓ | 0.739 / 0.73 ✓ |
| share_mixed_sector_pairs | 0.105 / 0.2 ✗ | 0.13 / 0.22 ✗ | 0.403 / 0.44 ✓ | 0.297 / 0.33 ✓ |

Cells: 40; ✓ 28 (within 10%), ~ 1 (within 25%), ✗ 11.

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
| mean | 0.98% / 0.91% ✓ | 1.16% / 1.08% ✓ | 0.89% / 0.93% ✓ | 1.10% / 1.04% ✓ |
| t_stat | 8.01 / 7.37 ✓ | 10.3 / 10.3 ✓ | 5.36 / 6.11 ~ | 11 / 10.5 ✓ |
| median | 0.91% / 0.83% ✓ | 1.03% / 0.94% ~ | 0.79% / 0.66% ~ | 1.03% / 0.97% ✓ |
| std | 2.07% / 2.15% ✓ | 1.66% / 1.65% ✓ | 2.27% / 2.64% ~ | 1.49% / 1.47% ✓ |
| skew | -0.459 / 0.44 ✗ | 0.494 / 0.76 ✗ | 0.534 / 0.66 ~ | 0.889 / 1.39 ✗ |
| kurtosis | 10 / 13.7 ✗ | 9.95 / 12.4 ~ | 6.53 / 5.52 ~ | 8.92 / 12.7 ✗ |
| min | -13.56% / -12.35% ✓ | -8.18% / -8.75% ✓ | -7.58% / -7.87% ✓ | -3.95% / -3.52% ~ |
| max | 9.72% / 16.56% ✗ | 10.65% / 12.73% ~ | 13.34% / 12.13% ✓ | 10.98% / 12.88% ~ |
| share_negative | 0.308 / 0.28 ~ | 0.184 / 0.19 ✓ | 0.328 / 0.35 ✓ | 0.169 / 0.18 ✓ |

## Table 3: Transportation (fully invested, one-day wait)

| statistic | top5 | top20 | all |
|---|---|---|---|
| mean | 0.89% / 0.50% ✗ | 0.59% / 0.58% ✓ | 0.49% / 0.44% ~ |
| t_stat | 5.26 / 2.98 ✗ | 4.71 / 4.26 ~ | 3.98 / 3.07 ✗ |
| median | 0.93% / 0.59% ✗ | 0.42% / 0.55% ~ | 0.38% / 0.34% ~ |
| std | 3.87% / 3.89% ✓ | 2.79% / 2.94% ✓ | 2.78% / 2.87% ✓ |
| skew | 0.0303 / -0.5 ✗ | 0.11 / -0.11 ✗ | 0.47 / 0.53 ~ |
| kurtosis | 3.13 / 4.98 ✗ | 3.87 / 5 ~ | 3.9 / 5.89 ✗ |
| min | -9.54% / -19.57% ✗ | -9.89% / -12.47% ~ | -6.39% / -12.53% ✗ |
| max | 12.60% / 10.96% ~ | 10.90% / 11.10% ✓ | 10.87% / 13.56% ~ |
| share_negative | 0.397 / 0.44 ✓ | 0.424 / 0.42 ✓ | 0.428 / 0.44 ✓ |

## Table 3: Financials (fully invested, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 0.67% / 0.68% ✓ | 0.80% / 0.78% ✓ | 1.03% / 0.85% ~ | 0.71% / 0.73% ✓ |
| t_stat | 4.97 / 4.79 ✓ | 8.27 / 7.6 ✓ | 7.76 / 7.12 ✓ | 6.95 / 7.62 ✓ |
| median | 0.68% / 0.56% ~ | 0.69% / 0.61% ~ | 0.97% / 0.66% ✗ | 0.64% / 0.51% ✗ |
| std | 2.79% / 2.60% ✓ | 1.83% / 1.79% ✓ | 2.15% / 2.36% ✓ | 1.84% / 1.81% ✓ |
| skew | 0.254 / 0.81 ✗ | 0.23 / 0.61 ✗ | 2.4 / 1.98 ~ | 0.851 / 2.64 ✗ |
| kurtosis | 7.79 / 6.37 ~ | 4.8 / 6.48 ✗ | 18.9 / 18.3 ✓ | 7.39 / 21.2 ✗ |
| min | -14.10% / -8.20% ✗ | -7.31% / -7.81% ✓ | -3.73% / -10.05% ✗ | -5.21% / -4.45% ~ |
| max | 17.08% / 14.93% ~ | 7.74% / 10.64% ✗ | 19.07% / 19.58% ✓ | 11.80% / 17.21% ✗ |
| share_negative | 0.397 / 0.4 ✓ | 0.316 / 0.33 ✓ | 0.264 / 0.32 ~ | 0.325 / 0.34 ✓ |

## Table 3: Industrials (fully invested, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 0.60% / 0.49% ~ | 0.71% / 0.61% ~ | 0.76% / 0.66% ~ | 0.59% / 0.71% ~ |
| t_stat | 5.08 / 4.11 ~ | 8.86 / 6.93 ✗ | 8.6 / 6.8 ✗ | 5.85 / 7.52 ~ |
| median | 0.60% / 0.29% ✗ | 0.65% / 0.55% ~ | 0.66% / 0.55% ~ | 0.34% / 0.40% ~ |
| std | 2.35% / 2.36% ✓ | 1.66% / 1.60% ✓ | 1.80% / 1.82% ✓ | 1.71% / 1.67% ✓ |
| skew | 0.00531 / 0.4 ✗ | 0.831 / 0.43 ✗ | 0.815 / 0.94 ~ | 1.89 / 2.97 ✗ |
| kurtosis | 4.75 / 4.94 ✓ | 7.62 / 4.75 ✗ | 6.34 / 7.65 ~ | 12.2 / 20.9 ✗ |
| min | -9.71% / -10.02% ✓ | -3.85% / -4.79% ~ | -5.22% / -5.41% ✓ | -4.75% / -3.43% ✗ |
| max | 10.07% / 10.55% ✓ | 10.71% / 8.02% ✗ | 10.66% / 11.62% ✓ | 12.54% / 16.07% ~ |
| share_negative | 0.371 / 0.42 ~ | 0.333 / 0.36 ✓ | 0.331 / 0.35 ✓ | 0.39 / 0.34 ~ |

Cells: 139; ✓ 58 (within 10%), ~ 44 (within 25%), ✗ 37.

## Table 7 (long and short books, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| long: mean monthly return | 1.25% / 1.24% ✓ | 1.36% / 1.33% ✓ | 1.48% / 1.46% ✓ | 1.51% / 1.62% ✓ |
| long: standard error (Newey-West) | 0.19% / 0.18% ✓ | 0.18% / 0.18% ✓ | 0.19% / 0.17% ~ | 0.27% / 0.25% ✓ |
| long: standard deviation | 3.87% / 3.88% ✓ | 3.70% / 3.65% ✓ | 3.80% / 3.44% ~ | 5.66% / 5.16% ✓ |
| long: monthly serial correlation | 0.0837 / 0.06 ✗ | 0.0889 / 0.09 ✓ | 0.133 / 0.13 ✓ | 0.16 / 0.17 ✓ |
| short: mean monthly return | 0.52% / 0.50% ✓ | 0.47% / 0.43% ✓ | 0.72% / 0.66% ✓ | 0.88% / 0.91% ✓ |
| short: standard error (Newey-West) | 0.20% / 0.18% ~ | 0.19% / 0.17% ✓ | 0.17% / 0.17% ✓ | 0.24% / 0.23% ✓ |
| short: standard deviation | 3.55% / 3.26% ✓ | 3.40% / 3.16% ✓ | 3.50% / 3.15% ~ | 4.98% / 4.60% ✓ |
| short: monthly serial correlation | 0.132 / 0.11 ~ | 0.106 / 0.12 ~ | 0.0799 / 0.12 ✗ | 0.136 / 0.16 ~ |

Cells: 32; ✓ 23 (within 10%), ~ 7 (within 25%), ✗ 2.

## Tables 4, 5 Panel A and 8 and Figure 4: conventions

Tables 4, 5 Panel A and 8 and Figure 4 describe the one-day-wait series of Table 1
Panel B; rows that repeat a scored row (means, standard deviations, Table 4's serial
correlation, Table 5's loss probability and minimum) are left out. Percentiles are
linearly interpolated (pandas' default) and serial correlation is the lag-1
correlation of calendar-adjacent months; the paper states neither estimator. The
regressions are OLS on French's market, SMB, HML, momentum and short-term reversal
factors, and on Ibbotson's market, small-stock, default and horizon premia (Ibbotson's
bond returns from Goyal and Welch's data, the small-stock series rebuilt from CRSP by
its recipe; coefficients and R2 are scored, the paper's Newey-West t-statistics and factor
standard deviations are not; the intercepts' t-statistics, six lags, are printed beside
the paper's). Table 4's equity-premium column is French's Mkt-RF, the regressions' market
factor, which Table 8 names the "U.S. equity risk-premium" (REVIEW_NOTES section 50).
French's reversal factor is losers minus winners, the sign
of the paper's printed loadings. The paper built its own reversal factor (French's
dates from 2006), and Table 8 identifies it as no long-short factor: its regressions
need a standard deviation near 0.072 before 1989, against ST_Rev's 0.026, and a +0.8
correlation with the market. Its loadings are therefore not expected to match; the
regressions with the series it resembles, prior-month losers less the bill, are
reported unscored at the end (REVIEW_NOTES section 51). Marks are ratios, so they read
harshly where the paper's value is near zero (a 25th percentile of +0.054%, an SMB
loading of 0.001).

## Table 4 (systematic risk, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| sharpe | 0.358 / 0.35 ✓ | 0.605 / 0.59 ✓ | 0.525 / 0.55 ✓ | 0.407 / 0.45 ✓ |
| intercept | 0.739% / 0.545% ✗ | 0.886% / 0.764% ~ | 0.824% / 0.714% ~ | 0.660% / 0.512% ✗ |
| market | -0.0176 / -0.0666 ✗ | 0.0071 / -0.0316 ✗ | 0.0155 / -0.077 ✗ | 0.0647 / -0.145 ✗ |
| smb | 0.0144 / -0.0423 ✗ | 0.0189 / 0.00111 ✗ | 0.0519 / -0.0233 ✗ | 0.0799 / -0.0708 ✗ |
| hml | 0.00022 / 0.0574 ✗ | 0.0277 / 0.0451 ✗ | 0.0148 / -0.0172 ✗ | 0.0227 / -0.054 ✗ |
| momentum | -0.0382 / -0.028 ✗ | -0.0433 / -0.0482 ~ | -0.139 / -0.103 ✗ | -0.195 / -0.181 ✓ |
| reversal | 0.0373 / 0.102 ✗ | 0.0398 / 0.0724 ✗ | 0.0683 / 0.0946 ✗ | 0.148 / 0.201 ✗ |
| r2 | 0.013 / 0.05 ✗ | 0.0355 / 0.09 ✗ | 0.243 / 0.18 ✗ | 0.598 / 0.54 ~ |
| ibbotson_intercept | 0.719% / 0.716% ✓ | 0.875% / 0.857% ✓ | 0.730% / 0.766% ✓ | 0.561% / 0.651% ~ |
| ibbotson_market | -0.0296 / -0.00182 ✗ | -0.009 / 0.0138 ✗ | 0.0234 / 0.0164 ✗ | 0.097 / 0.0647 ✗ |
| ibbotson_small_premium | 0.00723 / 0.0412 ✗ | 0.0186 / 0.0523 ✗ | 0.0482 / 0.0365 ✗ | 0.0761 / 0.0761 ✓ |
| ibbotson_default_premium | 0.156 / 0.146 ✓ | 0.121 / 0.16 ~ | 0.156 / 0.168 ✓ | 0.242 / 0.306 ~ |
| ibbotson_horizon_premium | 0.0779 / 0.08 ✓ | 0.0795 / 0.0682 ~ | 0.0491 / 0.0403 ~ | 0.00918 / 0.0342 ✗ |
| ibbotson_r2 | 0.0106 / 0.02 ✗ | 0.0199 / 0.05 ✗ | 0.0474 / 0.04 ~ | 0.178 / 0.15 ~ |
| alpha t-statistic, full sample (Newey-West, 6 lags; unscored) | 6.19 vs 3.81 | 8.71 vs 7.08 | 11.04 vs 8.66 | 10.04 vs 5.30 |

| statistic | French's Mkt-RF (ours / paper) |
|---|---|
| equity premium: mean | 0.425% / 0.410% ✓ |
| equity premium: std | 4.540% / 4.509% ✓ |
| equity premium: sharpe | 0.0936 / 0.09 ✓ |
| equity premium: serial_correlation | 0.0465 / 0.05 ✓ |

Cells: 60; ✓ 16 (within 10%), ~ 11 (within 25%), ✗ 33.

## Table 5 Panel A (monthly value at risk)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| serial_correlation | 0.128 / 0.14 ✓ | 0.244 / 0.24 ✓ | 0.0778 / 0.19 ✗ | 0.177 / 0.12 ✗ |
| var_1 | -3.588% / -4.320% ~ | -2.238% / -1.943% ~ | -2.749% / -2.236% ~ | -2.170% / -1.994% ✓ |
| var_5 | -2.141% / -2.142% ✓ | -1.098% / -1.002% ✓ | -1.449% / -1.293% ~ | -1.190% / -0.877% ✗ |
| var_10 | -1.497% / -1.516% ✓ | -0.614% / -0.577% ✓ | -0.988% / -0.756% ✗ | -0.808% / -0.614% ✗ |
| var_25 | -0.403% / -0.460% ~ | -0.048% / 0.054% ✗ | -0.127% / -0.145% ~ | -0.268% / -0.146% ✗ |

Cells: 20; ✓ 7 (within 10%), ~ 6 (within 25%), ✗ 7.

## Table 8 (subperiod analysis)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| pre_mean | 0.963% / 1.034% ✓ | 1.172% / 1.181% ✓ | 0.895% / 1.052% ~ | 0.896% / 0.992% ✓ |
| pre_std | 2.222% / 2.259% ✓ | 1.612% / 1.689% ✓ | 1.482% / 1.527% ✓ | 1.436% / 1.651% ~ |
| post_mean | 0.286% / 0.217% ✗ | 0.381% / 0.375% ✓ | 0.526% / 0.327% ✗ | 0.143% / 0.212% ✗ |
| post_std | 1.493% / 1.660% ~ | 1.001% / 0.987% ✓ | 1.375% / 1.121% ~ | 1.622% / 1.295% ✗ |
| pre_intercept | 0.950% / 0.353% ✗ | 1.118% / 0.670% ✗ | 0.924% / 0.710% ✗ | 0.819% / 0.446% ✗ |
| pre_market | -0.0559 / -0.434 ✗ | -0.00385 / -0.312 ✗ | -0.00337 / -0.289 ✗ | 0.0537 / -0.434 ✗ |
| pre_smb | -0.045 / -0.442 ✗ | -0.00453 / -0.332 ✗ | 0.0542 / -0.275 ✗ | 0.102 / -0.402 ✗ |
| pre_hml | 0.0174 / 0.0357 ✗ | 0.0418 / 0.0316 ✗ | -0.00816 / -0.0684 ✗ | 0.0301 / -0.0698 ✗ |
| pre_momentum | -0.0673 / 0.0129 ✗ | -0.0668 / -0.0163 ✗ | -0.175 / -0.0769 ✗ | -0.178 / -0.158 ~ |
| pre_reversal | 0.113 / 0.436 ✗ | 0.108 / 0.333 ✗ | 0.114 / 0.288 ✗ | 0.179 / 0.452 ✗ |
| pre_r2 | 0.0511 / 0.19 ✗ | 0.0768 / 0.23 ✗ | 0.302 / 0.26 ~ | 0.585 / 0.7 ~ |
| post_intercept | 0.207% / 0.337% ✗ | 0.368% / 0.417% ~ | 0.587% / 0.363% ✗ | 0.308% / -0.065% ✗ |
| post_market | 0.105 / 0.0734 ✗ | 0.0426 / 0.048 ~ | 0.0565 / 0.00241 ✗ | 0.0716 / -0.0696 ✗ |
| post_smb | 0.0625 / -0.004 ✗ | 0.00453 / 0.0289 ✗ | 0.0381 / 0.0233 ✗ | 0.0396 / -0.0606 ✗ |
| post_hml | 0.0384 / 0.0344 ~ | 0.00424 / 0.0141 ✗ | 0.0365 / 0.0183 ✗ | -0.00873 / -0.082 ✗ |
| post_momentum | 0.0138 / -0.00424 ✗ | -0.00435 / -0.0227 ✗ | -0.0948 / -0.0884 ✓ | -0.198 / -0.127 ✗ |
| post_reversal | -0.0265 / -0.0626 ✗ | -0.0215 / -0.0173 ~ | 0.0289 / 0.024 ~ | 0.117 / 0.188 ✗ |
| post_r2 | 0.102 / 0.02 ✗ | 0.0347 / 0.04 ~ | 0.196 / 0.19 ✓ | 0.663 / 0.64 ✓ |
| alpha t-statistic, before 1989 (Newey-West, 6 lags; unscored) | 5.80 vs 1.72 | 7.93 vs 4.41 | 8.58 vs 6.54 | 10.27 vs 4.19 |
| alpha t-statistic, after 1988 (Newey-West, 6 lags; unscored) | 1.58 vs 2.12 | 4.50 vs 3.77 | 8.04 vs 3.01 | 3.26 vs -0.56 |

Cells: 72; ✓ 11 (within 10%), ~ 13 (within 25%), ✗ 48.

## Figure 4 (top 20 against 101-120, correlations printed in the text)

| statistic | raw | five-factor residuals |
|---|---|---|
| correlation, full sample | 0.326 / 0.48 ✗ | 0.276 / 0.41 ✗ |
| correlation, before 1989 | 0.392 / 0.51 ~ | 0.327 / 0.42 ~ |
| correlation, after 1988 | 0.0541 / 0.18 ✗ | 0.1 / 0.2 ✗ |

Cells: 6; ✓ 0 (within 10%), ~ 2 (within 25%), ✗ 4.

## Reversal factor: the paper's own, as Table 8 implies it (unscored)

The scored regressions above use French's ST_Rev, the long-short factor the paper
describes. The paper built its own reversal factor, and its Table 8 regressions are
consistent only with a factor whose standard deviation is near the printed 0.072
before 1989 and whose correlation with the market is about +0.8: the profile of a
long-only portfolio of prior-month losers, not of a long-short factor (REVIEW_NOTES
section 51, `scripts/audit_reversal_factor.py`). The rows below repeat the regressions
with that series, French's equal-weighted bottom three prior-month deciles less the
T-bill, in place of ST_Rev. They are not scored.

| Table 4, full sample: ours vs paper | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| intercept | 0.79% vs 0.55% ✗ | 0.89% vs 0.76% ~ | 0.82% vs 0.71% ~ | 0.63% vs 0.51% ~ |
| market | 0.0258 vs -0.0666 ✗ | -0.0229 vs -0.0316 ✗ | -0.0623 vs -0.077 ~ | -0.135 vs -0.145 ✓ |
| smb | 0.0552 vs -0.0423 ✗ | -0.0122 vs 0.00111 ✗ | -0.0274 vs -0.0233 ~ | -0.122 vs -0.0708 ✗ |
| hml | 0.00777 vs 0.0574 ✗ | 0.0197 vs 0.0451 ✗ | -0.00446 vs -0.0172 ✗ | -0.0257 vs -0.054 ✗ |
| momentum | -0.0589 vs -0.028 ✗ | -0.0437 vs -0.0482 ✓ | -0.132 vs -0.103 ✗ | -0.172 vs -0.181 ✓ |
| reversal | -0.0365 vs 0.102 ✗ | 0.0342 vs 0.0724 ✗ | 0.0839 vs 0.0946 ~ | 0.212 vs 0.201 ✓ |
| r2 | 0.012 vs 0.05 ✗ | 0.0323 vs 0.09 ✗ | 0.243 vs 0.18 ✗ | 0.623 vs 0.54 ~ |

| Table 8, before 1989: ours vs paper | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| intercept | 0.96% vs 0.35% ✗ | 1.11% vs 0.67% ✗ | 0.90% vs 0.71% ✗ | 0.80% vs 0.45% ✗ |
| market | -0.23 vs -0.434 ✗ | -0.202 vs -0.312 ✗ | -0.244 vs -0.289 ~ | -0.286 vs -0.434 ✗ |
| smb | -0.252 vs -0.442 ✗ | -0.239 vs -0.332 ✗ | -0.23 vs -0.275 ~ | -0.3 vs -0.402 ✗ |
| hml | -0.0249 vs 0.0357 ✗ | -0.00539 vs 0.0316 ✗ | -0.0647 vs -0.0684 ✓ | -0.0506 vs -0.0698 ✗ |
| momentum | -0.0735 vs 0.0129 ✗ | -0.0683 vs -0.0163 ✗ | -0.172 vs -0.0769 ✗ | -0.179 vs -0.158 ~ |
| reversal | 0.186 vs 0.436 ✗ | 0.209 vs 0.333 ✗ | 0.252 vs 0.288 ~ | 0.359 vs 0.452 ~ |
| r2 | 0.0548 vs 0.19 ✗ | 0.0941 vs 0.23 ✗ | 0.34 vs 0.26 ✗ | 0.654 vs 0.7 ✓ |

| Table 8, after 1988: ours vs paper | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| intercept | 0.26% vs 0.34% ~ | 0.36% vs 0.42% ~ | 0.56% vs 0.36% ✗ | 0.22% vs -0.07% ✗ |
| market | 0.177 vs 0.0734 ✗ | 0.0419 vs 0.048 ~ | 0.0106 vs 0.00241 ✗ | -0.0752 vs -0.0696 ✓ |
| smb | 0.13 vs -0.004 ✗ | 0.00595 vs 0.0289 ✗ | -0.00607 vs 0.0233 ✗ | -0.104 vs -0.0606 ✗ |
| hml | 0.0508 vs 0.0344 ✗ | 0.0053 vs 0.0141 ✗ | 0.0278 vs 0.0183 ✗ | -0.0377 vs -0.082 ✗ |
| momentum | -0.0127 vs -0.00424 ✗ | -0.000549 vs -0.0227 ✗ | -0.0797 vs -0.0884 ✓ | -0.153 vs -0.127 ~ |
| reversal | -0.0767 vs -0.0626 ~ | -0.00274 vs -0.0173 ✗ | 0.0511 vs 0.024 ✗ | 0.167 vs 0.188 ~ |
| r2 | 0.123 vs 0.02 ✗ | 0.0283 vs 0.04 ✗ | 0.203 vs 0.19 ✓ | 0.692 vs 0.64 ✓ |

With this series the 84 regression cells would score 19.0, against 10.5 with ST_Rev, and the total 269.5 instead of 261.0.

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
| correlation of the positive bars | 0.52 | 0.50 | 1 by definition (392 months) |
| correlation of the negative bars | 0.60 | 0.53 | 1 by definition (82 months) |
| **correlation of the annual sums** | **0.76** | 0.76 | 1 by definition (40 years) |
| mean annual sum | 16.43% | 10.56% | 15.49% |
| best month offset, -3..+3 | +0 months | - | the alignment that maximises the two correlations |
| bars above 3.4% matched within 15% in the same month | 10 of 52 | - | - |
| tallest month | 1974-01 (9.34%) | 1974-01 (7.57%) | 1974-12 (13.30%) |
| deepest month | 1974-04 (-7.25%) | 1974-04 (-8.21%) | 1974-03 (-7.98%) |

| Figure 3, cumulative top 20, one-day wait | fully invested, ours | paper's figure | paper's Table 1 B mean, compounded | committed, ours | paper's figure | paper's Table 1 B mean, compounded |
|---|---|---|---|---|---|---|
| end level, 2002-12 | 76.4 | 39.7 | 72.5 | 12.0 | 11.5 | 11.5 |
| level at 1987-12 | 38.1 | 20.9 | - | 8.0 | 7.5 | - |
| peak (month) | 76.9 (2001-12) | 40.4 (2001-04) | - | 12.0 (2001-12) | 11.6 (2002-11) | - |
| share of the log rise made after 1987 | 17% | 18% | - | 17% | 18% | - |
| correlation of the log paths | 0.998 | 1 by definition | - | 0.998 | 1 by definition | - |

The curves are read from 1964-07, where the tracker first separates them; ours and the compounded
means start at the paper's level in that month. The compounded means ignore volatility drag, which
is under a basis point a month at these standard deviations. The S&P 500, the figure's third curve,
is not read.

| Table 1 Panel A, top 20: one month at the printed maximum | ours | 1975-01 set | control: 1974-01 set | paper |
|---|---|---|---|---|
| skewness | 0.79 | 1.31 | 1.21 | 1.39 |
| kurtosis | 7.23 | 10.47 | 10.33 | 10.54 |
| maximum | 9.34% | 13.30% | 13.30% | 13.30% |

Figure 2's tallest bar covers 1974-11 to 1975-01; the raster cannot split it further, so the
month set is the one of those where our return is highest (1975-01, 5.15%). Raising it to the printed
maximum moves skewness from 0.79 to 1.31 and kurtosis from 7.23 to 10.47 (paper
1.39 and 10.54); the control moves them to 1.21 and 10.33. The table measures the
size of the top-20 shape gap - about one month at the paper's maximum - and the window says where
the paper puts that month; it does not by itself show which month ours is missing.

Not scored: a value recovered from a 640-pixel image is evidence about which periods disagree, not a
value the paper prints.
