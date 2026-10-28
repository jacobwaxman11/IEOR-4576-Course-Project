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
Table 1 compounds the daily difference of the long and the short book,
while the paper's Table 1 = Table 7 identity implies compounding each book
first; that reading scores 184.0 of 291 (REVIEW_NOTES section 33).
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
- Table 1: Cells: 88; ✓ 43 (within 10%), ~ 22 (within 25%), ✗ 23.
- Table 2 Panel A: Cells: 24; ✓ 17 (within 10%), ~ 7 (within 25%), ✗ 0.
- Table 2 Panel B: Cells: 40; ✓ 28 (within 10%), ~ 2 (within 25%), ✗ 10.
- Table 3: Cells: 139; ✓ 64 (within 10%), ~ 39 (within 25%), ✗ 36.
- Table 7: Cells: 32; ✓ 23 (within 10%), ~ 7 (within 25%), ✗ 2.
- Table 4: Cells: 60; ✓ 20 (within 10%), ~ 8 (within 25%), ✗ 32.
- Table 5 Panel A: Cells: 20; ✓ 7 (within 10%), ~ 5 (within 25%), ✗ 8.
- Table 8: Cells: 72; ✓ 12 (within 10%), ~ 15 (within 25%), ✗ 45.
- Figure 4: Cells: 6; ✓ 0 (within 10%), ~ 2 (within 25%), ✗ 4.
- Score: 267.5 of 481 compared cells (✓ = 1, ~ = ½, ✗ = 0); history in SCORE_LOG.md.
- Tables 1-3 alone: 187.0 of 291, the cell set of SCORE_LOG.md rows 1-13.
- Tables 1-3 and 7 alone: 213.5 of 323, the cell set of SCORE_LOG.md row 14.

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
| mean (fully invested) | 1.26% / 1.31% ✓ | 1.38% / 1.44% ✓ | 0.96% / 1.08% ~ | 0.89% / 1.10% ~ |
| nw_se | 0.15% / 0.15% ✓ | 0.13% / 0.12% ✓ | 0.08% / 0.09% ~ | 0.08% / 0.10% ~ |
| t_stat | 8.39 / 8.84 ✓ | 11 / 11.6 ✓ | 11.6 / 11.5 ✓ | 10.5 / 11.2 ✓ |
| median | 1.09% / 1.19% ✓ | 1.21% / 1.23% ✓ | 0.87% / 0.95% ✓ | 0.62% / 0.73% ~ |
| std | 2.37% / 2.28% ✓ | 1.70% / 1.69% ✓ | 1.53% / 1.54% ✓ | 1.55% / 1.67% ✓ |
| skew | 0.119 / 0.62 ✗ | 0.809 / 1.39 ✗ | 0.8 / 1.34 ✗ | 1.99 / 3.42 ✗ |
| kurtosis | 9.38 / 7.81 ~ | 8.1 / 10.5 ~ | 6.26 / 10.3 ✗ | 11.1 / 25.2 ✗ |
| min | -14.94% / -10.57% ✗ | -8.02% / -6.63% ~ | -3.82% / -3.86% ✓ | -3.63% / -2.72% ✗ |
| max | 12.40% / 14.72% ~ | 10.23% / 13.30% ~ | 9.98% / 12.68% ~ | 10.36% / 17.18% ✗ |
| share_negative | 0.274 / 0.26 ✓ | 0.171 / 0.15 ~ | 0.241 / 0.21 ~ | 0.253 / 0.17 ✗ |
| mean (committed) | 0.74% / 0.78% ✓ | 0.80% / 0.80% ✓ | 0.59% / 0.68% ~ | 0.46% / 0.61% ✗ |

## Table 1 Panel B (one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean (fully invested) | 0.69% / 0.74% ✓ | 0.88% / 0.90% ✓ | 0.75% / 0.80% ✓ | 0.60% / 0.71% ~ |
| nw_se | 0.11% / 0.12% ✓ | 0.10% / 0.10% ✓ | 0.08% / 0.08% ✓ | 0.09% / 0.09% ✓ |
| t_stat | 6.22 / 6.26 ✓ | 9.15 / 9.29 ✓ | 9.77 / 9.4 ✓ | 6.95 / 7.92 ~ |
| median | 0.67% / 0.70% ✓ | 0.80% / 0.69% ~ | 0.68% / 0.69% ✓ | 0.37% / 0.41% ✓ |
| std | 2.04% / 2.10% ✓ | 1.48% / 1.53% ✓ | 1.44% / 1.44% ✓ | 1.49% / 1.58% ✓ |
| skew | -0.58 / 0.34 ✗ | 0.113 / 1.45 ✗ | 0.214 / 0.98 ✗ | 1.66 / 3.32 ✗ |
| kurtosis | 11.6 / 10.6 ✓ | 8.8 / 16.1 ✗ | 3.99 / 7.78 ✗ | 9.93 / 25.7 ✗ |
| min | -15.29% / -12.63% ~ | -9.07% / -8.22% ~ | -4.11% / -4.27% ✓ | -4.02% / -2.95% ✗ |
| max | 9.34% / 14.35% ✗ | 7.40% / 13.49% ✗ | 5.85% / 10.46% ✗ | 10.29% / 16.32% ✗ |
| share_negative | 0.363 / 0.35 ✓ | 0.274 / 0.23 ~ | 0.281 / 0.28 ✓ | 0.338 / 0.32 ✓ |
| mean (committed) | 0.42% / 0.46% ~ | 0.51% / 0.52% ✓ | 0.46% / 0.50% ✓ | 0.30% / 0.40% ~ |

Cells: 88; ✓ 43 (within 10%), ~ 22 (within 25%), ✗ 23.

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
| mean | 0.94% / 0.91% ✓ | 1.15% / 1.08% ✓ | 0.86% / 0.93% ✓ | 1.10% / 1.04% ✓ |
| t_stat | 7.82 / 7.37 ✓ | 10.3 / 10.3 ✓ | 5.33 / 6.11 ~ | 11.1 / 10.5 ✓ |
| median | 0.89% / 0.83% ✓ | 1.02% / 0.94% ✓ | 0.75% / 0.66% ~ | 1.02% / 0.97% ✓ |
| std | 2.08% / 2.15% ✓ | 1.65% / 1.65% ✓ | 2.25% / 2.64% ~ | 1.46% / 1.47% ✓ |
| skew | -0.676 / 0.44 ✗ | 0.41 / 0.76 ✗ | 0.458 / 0.66 ✗ | 0.722 / 1.39 ✗ |
| kurtosis | 12 / 13.7 ~ | 10.4 / 12.4 ~ | 5.75 / 5.52 ✓ | 7.63 / 12.7 ✗ |
| min | -15.29% / -12.35% ~ | -9.03% / -8.75% ✓ | -7.52% / -7.87% ✓ | -3.69% / -3.52% ✓ |
| max | 9.34% / 16.56% ✗ | 10.69% / 12.73% ~ | 11.88% / 12.13% ✓ | 9.61% / 12.88% ✗ |
| share_negative | 0.31 / 0.28 ~ | 0.192 / 0.19 ✓ | 0.338 / 0.35 ✓ | 0.169 / 0.18 ✓ |

## Table 3: Transportation (fully invested, one-day wait)

| statistic | top5 | top20 | all |
|---|---|---|---|
| mean | 0.84% / 0.50% ✗ | 0.55% / 0.58% ✓ | 0.45% / 0.44% ✓ |
| t_stat | 5.02 / 2.98 ✗ | 4.48 / 4.26 ✓ | 3.79 / 3.07 ~ |
| median | 0.87% / 0.59% ✗ | 0.37% / 0.55% ✗ | 0.34% / 0.34% ✓ |
| std | 3.86% / 3.89% ✓ | 2.76% / 2.94% ✓ | 2.73% / 2.87% ✓ |
| skew | 0.117 / -0.5 ✗ | 0.103 / -0.11 ✗ | 0.415 / 0.53 ~ |
| kurtosis | 3.09 / 4.98 ✗ | 3.63 / 5 ✗ | 3.7 / 5.89 ✗ |
| min | -9.19% / -19.57% ✗ | -9.39% / -12.47% ~ | -6.28% / -12.53% ✗ |
| max | 12.57% / 10.96% ~ | 8.88% / 11.10% ~ | 10.44% / 13.56% ~ |
| share_negative | 0.409 / 0.44 ✓ | 0.439 / 0.42 ✓ | 0.435 / 0.44 ✓ |

## Table 3: Financials (fully invested, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 0.62% / 0.68% ✓ | 0.78% / 0.78% ✓ | 1.00% / 0.85% ~ | 0.69% / 0.73% ✓ |
| t_stat | 4.61 / 4.79 ✓ | 8.05 / 7.6 ✓ | 7.67 / 7.12 ✓ | 6.84 / 7.62 ~ |
| median | 0.59% / 0.56% ✓ | 0.66% / 0.61% ✓ | 0.93% / 0.66% ✗ | 0.62% / 0.51% ~ |
| std | 2.76% / 2.60% ✓ | 1.83% / 1.79% ✓ | 2.11% / 2.36% ~ | 1.81% / 1.81% ✓ |
| skew | 0.445 / 0.81 ✗ | 0.28 / 0.61 ✗ | 2.3 / 1.98 ~ | 0.613 / 2.64 ✗ |
| kurtosis | 7.67 / 6.37 ~ | 5.21 / 6.48 ~ | 18.6 / 18.3 ✓ | 6.14 / 21.2 ✗ |
| min | -12.21% / -8.20% ✗ | -7.43% / -7.81% ✓ | -3.89% / -10.05% ✗ | -5.30% / -4.45% ~ |
| max | 17.85% / 14.93% ~ | 9.32% / 10.64% ~ | 18.76% / 19.58% ✓ | 10.38% / 17.21% ✗ |
| share_negative | 0.405 / 0.4 ✓ | 0.321 / 0.33 ✓ | 0.264 / 0.32 ~ | 0.325 / 0.34 ✓ |

## Table 3: Industrials (fully invested, one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 0.57% / 0.49% ~ | 0.69% / 0.61% ~ | 0.73% / 0.66% ✓ | 0.55% / 0.71% ~ |
| t_stat | 4.82 / 4.11 ~ | 8.63 / 6.93 ~ | 8.4 / 6.8 ~ | 5.73 / 7.52 ~ |
| median | 0.50% / 0.29% ✗ | 0.64% / 0.55% ~ | 0.64% / 0.55% ~ | 0.33% / 0.40% ~ |
| std | 2.34% / 2.36% ✓ | 1.65% / 1.60% ✓ | 1.76% / 1.82% ✓ | 1.63% / 1.67% ✓ |
| skew | 0.0808 / 0.4 ✗ | 0.778 / 0.43 ✗ | 0.663 / 0.94 ✗ | 1.57 / 2.97 ✗ |
| kurtosis | 4.96 / 4.94 ✓ | 7.48 / 4.75 ✗ | 5.44 / 7.65 ✗ | 9.9 / 20.9 ✗ |
| min | -9.76% / -10.02% ✓ | -4.48% / -4.79% ✓ | -5.01% / -5.41% ✓ | -4.70% / -3.43% ✗ |
| max | 10.75% / 10.55% ✓ | 10.00% / 8.02% ~ | 9.22% / 11.62% ~ | 10.74% / 16.07% ✗ |
| share_negative | 0.38 / 0.42 ✓ | 0.34 / 0.36 ✓ | 0.333 / 0.35 ✓ | 0.384 / 0.34 ~ |

Cells: 139; ✓ 64 (within 10%), ~ 39 (within 25%), ✗ 36.

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
| sharpe | 0.339 / 0.35 ✓ | 0.593 / 0.59 ✓ | 0.52 / 0.55 ✓ | 0.406 / 0.45 ✓ |
| intercept | 0.708% / 0.545% ✗ | 0.879% / 0.764% ~ | 0.813% / 0.714% ~ | 0.641% / 0.512% ✗ |
| market | -0.0226 / -0.0666 ✗ | 4.94e-06 / -0.0316 ✗ | 0.00669 / -0.077 ✗ | 0.0534 / -0.145 ✗ |
| smb | 0.0148 / -0.0423 ✗ | 0.0169 / 0.00111 ✗ | 0.0488 / -0.0233 ✗ | 0.0709 / -0.0708 ✗ |
| hml | -0.00576 / 0.0574 ✗ | 0.0203 / 0.0451 ✗ | 0.00933 / -0.0172 ✗ | 0.0128 / -0.054 ✗ |
| momentum | -0.035 / -0.028 ~ | -0.0416 / -0.0482 ~ | -0.136 / -0.103 ✗ | -0.189 / -0.181 ✓ |
| reversal | 0.0389 / 0.102 ✗ | 0.0404 / 0.0724 ✗ | 0.0682 / 0.0946 ✗ | 0.145 / 0.201 ✗ |
| r2 | 0.0122 / 0.05 ✗ | 0.0312 / 0.09 ✗ | 0.232 / 0.18 ✗ | 0.586 / 0.54 ✓ |
| ibbotson_intercept | 0.688% / 0.716% ✓ | 0.866% / 0.857% ✓ | 0.719% / 0.766% ✓ | 0.542% / 0.651% ~ |
| ibbotson_market | -0.0323 / -0.00182 ✗ | -0.0133 / 0.0138 ✗ | 0.0161 / 0.0164 ✓ | 0.087 / 0.0647 ✗ |
| ibbotson_small_premium | 0.00729 / 0.0412 ✗ | 0.0167 / 0.0523 ✗ | 0.0455 / 0.0365 ~ | 0.0685 / 0.0761 ✓ |
| ibbotson_default_premium | 0.153 / 0.146 ✓ | 0.116 / 0.16 ✗ | 0.15 / 0.168 ~ | 0.228 / 0.306 ✗ |
| ibbotson_horizon_premium | 0.0727 / 0.08 ✓ | 0.0727 / 0.0682 ✓ | 0.0454 / 0.0403 ~ | 0.00706 / 0.0342 ✗ |
| ibbotson_r2 | 0.00996 / 0.02 ✗ | 0.0161 / 0.05 ✗ | 0.0398 / 0.04 ✓ | 0.16 / 0.15 ✓ |
| alpha t-statistic, full sample (Newey-West, 6 lags; unscored) | 5.93 vs 3.81 | 8.61 vs 7.08 | 10.78 vs 8.66 | 9.77 vs 5.30 |

| statistic | French's Mkt-RF (ours / paper) |
|---|---|
| equity premium: mean | 0.425% / 0.410% ✓ |
| equity premium: std | 4.540% / 4.509% ✓ |
| equity premium: sharpe | 0.0936 / 0.09 ✓ |
| equity premium: serial_correlation | 0.0465 / 0.05 ✓ |

Cells: 60; ✓ 20 (within 10%), ~ 8 (within 25%), ✗ 32.

## Table 5 Panel A (monthly value at risk)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| serial_correlation | 0.114 / 0.14 ~ | 0.243 / 0.24 ✓ | 0.0722 / 0.19 ✗ | 0.179 / 0.12 ✗ |
| var_1 | -3.671% / -4.320% ~ | -2.238% / -1.943% ~ | -2.812% / -2.236% ✗ | -2.225% / -1.994% ~ |
| var_5 | -2.213% / -2.142% ✓ | -1.096% / -1.002% ✓ | -1.458% / -1.293% ~ | -1.265% / -0.877% ✗ |
| var_10 | -1.503% / -1.516% ✓ | -0.617% / -0.577% ✓ | -0.976% / -0.756% ✗ | -0.833% / -0.614% ✗ |
| var_25 | -0.432% / -0.460% ✓ | -0.055% / 0.054% ✗ | -0.137% / -0.145% ✓ | -0.274% / -0.146% ✗ |

Cells: 20; ✓ 7 (within 10%), ~ 5 (within 25%), ✗ 8.

## Table 8 (subperiod analysis)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| pre_mean | 0.930% / 1.034% ~ | 1.159% / 1.181% ✓ | 0.880% / 1.052% ~ | 0.870% / 0.992% ~ |
| pre_std | 2.254% / 2.259% ✓ | 1.625% / 1.689% ✓ | 1.469% / 1.527% ✓ | 1.365% / 1.651% ~ |
| post_mean | 0.256% / 0.217% ~ | 0.369% / 0.375% ✓ | 0.509% / 0.327% ✗ | 0.117% / 0.212% ✗ |
| post_std | 1.485% / 1.660% ~ | 0.993% / 0.987% ✓ | 1.356% / 1.121% ~ | 1.573% / 1.295% ~ |
| pre_intercept | 0.917% / 0.353% ✗ | 1.111% / 0.670% ✗ | 0.914% / 0.710% ✗ | 0.809% / 0.446% ✗ |
| pre_market | -0.0623 / -0.434 ✗ | -0.0136 / -0.312 ✗ | -0.015 / -0.289 ✗ | 0.0381 / -0.434 ✗ |
| pre_smb | -0.041 / -0.442 ✗ | -0.00435 / -0.332 ✗ | 0.0516 / -0.275 ✗ | 0.0883 / -0.402 ✗ |
| pre_hml | 0.0127 / 0.0357 ✗ | 0.032 / 0.0316 ✓ | -0.014 / -0.0684 ✗ | 0.0213 / -0.0698 ✗ |
| pre_momentum | -0.0621 / 0.0129 ✗ | -0.0628 / -0.0163 ✗ | -0.17 / -0.0769 ✗ | -0.174 / -0.158 ✓ |
| pre_reversal | 0.111 / 0.436 ✗ | 0.107 / 0.333 ✗ | 0.112 / 0.288 ✗ | 0.174 / 0.452 ✗ |
| pre_r2 | 0.0483 / 0.19 ✗ | 0.0688 / 0.23 ✗ | 0.285 / 0.26 ✓ | 0.567 / 0.7 ~ |
| post_intercept | 0.178% / 0.337% ✗ | 0.357% / 0.417% ~ | 0.570% / 0.363% ✗ | 0.269% / -0.065% ✗ |
| post_market | 0.102 / 0.0734 ✗ | 0.0404 / 0.048 ~ | 0.054 / 0.00241 ✗ | 0.0749 / -0.0696 ✗ |
| post_smb | 0.0603 / -0.004 ✗ | 0.00378 / 0.0289 ✗ | 0.0377 / 0.0233 ✗ | 0.0391 / -0.0606 ✗ |
| post_hml | 0.0306 / 0.0344 ~ | 0.00224 / 0.0141 ✗ | 0.0356 / 0.0183 ✗ | -0.01 / -0.082 ✗ |
| post_momentum | 0.0157 / -0.00424 ✗ | -0.00427 / -0.0227 ✗ | -0.0936 / -0.0884 ✓ | -0.188 / -0.127 ✗ |
| post_reversal | -0.0229 / -0.0626 ✗ | -0.0201 / -0.0173 ~ | 0.0298 / 0.024 ~ | 0.115 / 0.188 ✗ |
| post_r2 | 0.1 / 0.02 ✗ | 0.0325 / 0.04 ~ | 0.196 / 0.19 ✓ | 0.663 / 0.64 ✓ |
| alpha t-statistic, before 1989 (Newey-West, 6 lags; unscored) | 5.58 vs 1.72 | 7.85 vs 4.41 | 8.37 vs 6.54 | 10.14 vs 4.19 |
| alpha t-statistic, after 1988 (Newey-West, 6 lags; unscored) | 1.35 vs 2.12 | 4.41 vs 3.77 | 7.88 vs 3.01 | 2.97 vs -0.56 |

Cells: 72; ✓ 12 (within 10%), ~ 15 (within 25%), ✗ 45.

## Figure 4 (top 20 against 101-120, correlations printed in the text)

| statistic | raw | five-factor residuals |
|---|---|---|
| correlation, full sample | 0.32 / 0.48 ✗ | 0.276 / 0.41 ✗ |
| correlation, before 1989 | 0.386 / 0.51 ~ | 0.327 / 0.42 ~ |
| correlation, after 1988 | 0.0435 / 0.18 ✗ | 0.0912 / 0.2 ✗ |

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
| intercept | 0.76% vs 0.55% ✗ | 0.89% vs 0.76% ~ | 0.81% vs 0.71% ~ | 0.62% vs 0.51% ~ |
| market | 0.0174 vs -0.0666 ✗ | -0.0307 vs -0.0316 ✓ | -0.0706 vs -0.077 ✓ | -0.135 vs -0.145 ✓ |
| smb | 0.0522 vs -0.0423 ✗ | -0.0149 vs 0.00111 ✗ | -0.0299 vs -0.0233 ✗ | -0.12 vs -0.0708 ✗ |
| hml | 0.00102 vs 0.0574 ✗ | 0.0122 vs 0.0451 ✗ | -0.00985 vs -0.0172 ✗ | -0.0332 vs -0.054 ✗ |
| momentum | -0.0551 vs -0.028 ✗ | -0.042 vs -0.0482 ~ | -0.13 vs -0.103 ✗ | -0.168 vs -0.181 ✓ |
| reversal | -0.0331 vs 0.102 ✗ | 0.0349 vs 0.0724 ✗ | 0.0834 vs 0.0946 ~ | 0.201 vs 0.201 ✓ |
| r2 | 0.0106 vs 0.05 ✗ | 0.028 vs 0.09 ✗ | 0.232 vs 0.18 ✗ | 0.605 vs 0.54 ~ |

| Table 8, before 1989: ours vs paper | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| intercept | 0.93% vs 0.35% ✗ | 1.11% vs 0.67% ✗ | 0.89% vs 0.71% ✗ | 0.80% vs 0.45% ✗ |
| market | -0.234 vs -0.434 ✗ | -0.208 vs -0.312 ✗ | -0.252 vs -0.289 ~ | -0.286 vs -0.434 ✗ |
| smb | -0.245 vs -0.442 ✗ | -0.235 vs -0.332 ✗ | -0.229 vs -0.275 ~ | -0.295 vs -0.402 ✗ |
| hml | -0.0291 vs 0.0357 ✗ | -0.0143 vs 0.0316 ✗ | -0.0698 vs -0.0684 ✓ | -0.0558 vs -0.0698 ~ |
| momentum | -0.0682 vs 0.0129 ✗ | -0.0646 vs -0.0163 ✗ | -0.167 vs -0.0769 ✗ | -0.176 vs -0.158 ~ |
| reversal | 0.184 vs 0.436 ✗ | 0.206 vs 0.333 ✗ | 0.249 vs 0.288 ~ | 0.342 vs 0.452 ~ |
| r2 | 0.0518 vs 0.19 ✗ | 0.0847 vs 0.23 ✗ | 0.323 vs 0.26 ~ | 0.632 vs 0.7 ✓ |

| Table 8, after 1988: ours vs paper | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| intercept | 0.23% vs 0.34% ✗ | 0.35% vs 0.42% ~ | 0.54% vs 0.36% ✗ | 0.18% vs -0.07% ✗ |
| market | 0.17 vs 0.0734 ✗ | 0.0388 vs 0.048 ~ | 0.00844 vs 0.00241 ✗ | -0.0672 vs -0.0696 ✓ |
| smb | 0.124 vs -0.004 ✗ | 0.00431 vs 0.0289 ✗ | -0.00624 vs 0.0233 ✗ | -0.1 vs -0.0606 ✗ |
| hml | 0.0423 vs 0.0344 ~ | 0.00309 vs 0.0141 ✗ | 0.0269 vs 0.0183 ✗ | -0.0381 vs -0.082 ✗ |
| momentum | -0.00998 vs -0.00424 ✗ | -0.000343 vs -0.0227 ✗ | -0.0788 vs -0.0884 ~ | -0.145 vs -0.127 ~ |
| reversal | -0.0726 vs -0.0626 ~ | -0.00167 vs -0.0173 ✗ | 0.0509 vs 0.024 ✗ | 0.162 vs 0.188 ~ |
| r2 | 0.12 vs 0.02 ✗ | 0.0267 vs 0.04 ✗ | 0.202 vs 0.19 ✓ | 0.689 vs 0.64 ✓ |

With this series the 84 regression cells would score 20.0, against 13.5 with ST_Rev, and the total 274.0 instead of 267.5.

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
| correlation of the positive bars | 0.51 | 0.49 | 1 by definition (393 months) |
| correlation of the negative bars | 0.61 | 0.55 | 1 by definition (81 months) |
| **correlation of the annual sums** | **0.75** | 0.75 | 1 by definition (40 years) |
| mean annual sum | 16.39% | 10.41% | 15.49% |
| best month offset, -3..+3 | +0 months | - | the alignment that maximises the two correlations |
| bars above 3.4% matched within 15% in the same month | 12 of 52 | - | - |
| tallest month | 1987-10 (10.23%) | 1974-10 (7.40%) | 1974-12 (13.30%) |
| deepest month | 1974-04 (-8.02%) | 1974-04 (-9.07%) | 1974-03 (-7.98%) |

| Figure 3, cumulative top 20, one-day wait | fully invested, ours | paper's figure | paper's Table 1 B mean, compounded | committed, ours | paper's figure | paper's Table 1 B mean, compounded |
|---|---|---|---|---|---|---|
| end level, 2002-12 | 72.1 | 39.7 | 72.5 | 11.6 | 11.5 | 11.5 |
| level at 1987-12 | 36.7 | 20.9 | - | 7.8 | 7.5 | - |
| peak (month) | 72.4 (2001-12) | 40.4 (2001-04) | - | 11.6 (2001-12) | 11.6 (2002-11) | - |
| share of the log rise made after 1987 | 16% | 18% | - | 16% | 18% | - |
| correlation of the log paths | 0.998 | 1 by definition | - | 0.998 | 1 by definition | - |

The curves are read from 1964-07, where the tracker first separates them; ours and the compounded
means start at the paper's level in that month. The compounded means ignore volatility drag, which
is under a basis point a month at these standard deviations. The S&P 500, the figure's third curve,
is not read.

| Table 1 Panel A, top 20: one month at the printed maximum | ours | 1975-01 set | control: 1987-10 set | paper |
|---|---|---|---|---|
| skewness | 0.81 | 1.30 | 1.15 | 1.39 |
| kurtosis | 8.10 | 10.93 | 10.64 | 10.54 |
| maximum | 10.23% | 13.30% | 13.30% | 13.30% |

Figure 2's tallest bar covers 1974-11 to 1975-01; the raster cannot split it further, so the
month set is the one of those where our return is highest (1975-01, 4.49%). Raising it to the printed
maximum moves skewness from 0.81 to 1.30 and kurtosis from 8.10 to 10.93 (paper
1.39 and 10.54); the control moves them to 1.15 and 10.64. The table measures the
size of the top-20 shape gap - about one month at the paper's maximum - and the window says where
the paper puts that month; it does not by itself show which month ours is missing.

Not scored: a value recovered from a 640-pixel image is evidence about which periods disagree, not a
value the paper prints.
