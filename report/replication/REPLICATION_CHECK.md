# Replication check: GGR (2006) Figures 1 and 4, Tables 1-4, 5 Panels A and B, 6, 7 and 8 (vol_common)

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
evidence, and claims/CONVENTIONS_865.md prices every convention this header
names on all 865 cells: its row 9 - same issuer allowed, the near-frozen filter
off, the trigger's sigma taken about the mean instead of the RMS about zero -
gains 6.5 and is not adopted. Telephone utilities are
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
(pp. 807 and 821; REVIEW_NOTES sections 33 and 54). Table 5 Panel B is the same
overlap average at daily frequency (``DAILY_CAPITAL``), percentiles linearly
interpolated and serial correlation the lag-1 autocorrelation of consecutive
trading days, neither of which the paper states; REVIEW_NOTES section 62 gives the
marks, the daily cache's construction and the paper's own "all" daily column,
which does not agree with its monthly "all" and is reported, not adjusted.
The short-position weight is also our reading: weighting a short by the
shorted stock's value instead (--short-weights value) gives SCORE_LOG.md row
12. The weight is floored at zero; 780 of the 2,968,816 Table 1 positions
carry zero weight after their shorted stock doubles in a day, none of them in
the top 5, top 20 or 101-120 portfolios, so the floor acts on the "all"
columns. REVIEW_NOTES section 29 gives the evidence and the objections (Table
8 before 1989 and the 1999 draft).

The scored five-factor block's reversal factor is our reading, not the paper's
stated definition. The paper's own series is unidentified: its printed statistics
pin a 2.19%/month premium at 7.23% monthly volatility, a before-1989 standard
deviation of 0.0723, and Table 8 Panel A loadings that need a factor correlated
+0.81 with the market and +0.79 with SMB, which no long-short construction
reaches (REVIEW_NOTES section 51). The scored rows use the equal-weighted bottom
three prior-month deciles less the T-bill instead: standard deviation 0.0685
before 1989, correlations +0.84 with the market and +0.77 with SMB, premium
1.30%/month against the implied 2.19%. That is a hypothesis that the paper's
factor lacks its short leg, i.e. an error in the paper, not a settled reading
(REVIEW_NOTES section 61). French's ST_Rev is printed unscored below;
--reversal-factor st_rev restores SCORE_LOG.md row 18's block (262.0).

The five factors are French's 2005 archives, the vintage the paper had: the
Internet Archive's captures of 30 September and 29 October 2005
(`F-F_Research_Data_Factors.zip`, `F-F_Momentum_Factor.zip`), committed whole
under `data/raw/french_vintage_2005` with their provenance. They reproduce
Table 8's printed factor standard deviations; the files downloaded today do not,
HML's after-1988 standard deviation being 7.8% short (REVIEW_NOTES section 72).
The prior-month deciles the reversal series is built from are today's: the
earliest archived prior-1-0 file is from 2007 and matches them.

The same arithmetic is in GAPS.md and `scripts/paper_consistency.py`.

The score total, its history and how it is counted live in SCORE_LOG.md. The
open gaps are in GAPS.md; the 1999 NBER draft is scored separately
in EDITION_1999.md.

## Summary

- Figure 1: reproduced
- Table 1: Cells: 88; ✓ 49 (within 10%), ~ 15 (within 25%), ✗ 24.
- Table 2 Panel A: Cells: 24; ✓ 17 (within 10%), ~ 7 (within 25%), ✗ 0.
- Table 2 Panel B: Cells: 40; ✓ 28 (within 10%), ~ 1 (within 25%), ✗ 11.
- Table 3: Cells: 139; ✓ 58 (within 10%), ~ 44 (within 25%), ✗ 37.
- Table 7: Cells: 136; ✓ 34 (within 10%), ~ 20 (within 25%), ✗ 82.
- Table 4: Cells: 104; ✓ 28 (within 10%), ~ 22 (within 25%), ✗ 54.
- Table 5 Panel A: Cells: 20; ✓ 7 (within 10%), ~ 6 (within 25%), ✗ 7.
- Table 5 Panel B: Cells: 36; ✓ 26 (within 10%), ~ 8 (within 25%), ✗ 2.
- Table 8: Cells: 130; ✓ 27 (within 10%), ~ 19 (within 25%), ✗ 84.
- Figure 4: Cells: 6; ✓ 0 (within 10%), ~ 2 (within 25%), ✗ 4.
- Numbers printed in the text: Cells: 6; ✓ 3 (within 10%), ~ 2 (within 25%), ✗ 1.
- Table 9 Panel A: Cells: 44; ✓ 22 (within 10%), ~ 10 (within 25%), ✗ 12.
- Table 9 Panel B: Cells: 44; ✓ 15 (within 10%), ~ 12 (within 25%), ✗ 17.
- Table 6: Cells: 48; ✓ 8 (within 10%), ~ 10 (within 25%), ✗ 30.
- Score: 411.0 of 865 compared cells (✓ = 1, ~ = ½, ✗ = 0); history in SCORE_LOG.md.
- Tables 1-3 alone: 185.5 of 291, the cell set of SCORE_LOG.md rows 1-13.
- Tables 1-3 and 7 alone: 212.0 of 323, the cell set of SCORE_LOG.md row 14.

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
| mean (committed) | 0.77% / 0.78% ✓ | 0.84% / 0.80% ✓ | 0.62% / 0.68% ✓ | 0.52% / 0.61% ~ |

## Table 1 Panel B (one-day wait)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean (fully invested) | 0.72% / 0.74% ✓ | 0.89% / 0.90% ✓ | 0.76% / 0.80% ✓ | 0.63% / 0.71% ~ |
| nw_se | 0.11% / 0.12% ✓ | 0.10% / 0.10% ✓ | 0.08% / 0.08% ✓ | 0.09% / 0.09% ✓ |
| t_stat | 6.45 / 6.26 ✓ | 9.29 / 9.29 ✓ | 9.86 / 9.4 ✓ | 7.01 / 7.92 ~ |
| median | 0.70% / 0.70% ✓ | 0.81% / 0.69% ~ | 0.70% / 0.69% ✓ | 0.38% / 0.41% ✓ |
| std | 2.02% / 2.10% ✓ | 1.47% / 1.53% ✓ | 1.45% / 1.44% ✓ | 1.55% / 1.58% ✓ |
| skew | -0.329 / 0.34 ✗ | 0.261 / 1.45 ✗ | 0.241 / 0.98 ✗ | 1.96 / 3.32 ✗ |
| kurtosis | 9.07 / 10.6 ~ | 7.72 / 16.1 ✗ | 4.23 / 7.78 ✗ | 12.3 / 25.7 ✗ |
| min | -13.56% / -12.63% ✓ | -8.21% / -8.22% ✓ | -4.38% / -4.27% ✓ | -3.98% / -2.95% ✗ |
| max | 9.72% / 14.35% ✗ | 7.57% / 13.49% ✗ | 6.59% / 10.46% ✗ | 11.93% / 16.32% ✗ |
| share_negative | 0.359 / 0.35 ✓ | 0.272 / 0.23 ~ | 0.283 / 0.28 ✓ | 0.338 / 0.32 ✓ |
| mean (committed) | 0.45% / 0.46% ✓ | 0.56% / 0.52% ✓ | 0.50% / 0.50% ✓ | 0.38% / 0.40% ✓ |

Cells: 88; ✓ 49 (within 10%), ~ 15 (within 25%), ✗ 24.

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
| t_stat | 8.02 / 7.37 ✓ | 10.3 / 10.3 ✓ | 5.37 / 6.11 ~ | 11 / 10.5 ✓ |
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
| t_stat | 5.27 / 2.98 ✗ | 4.72 / 4.26 ~ | 3.99 / 3.07 ✗ |
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
| t_stat | 4.98 / 4.79 ✓ | 8.28 / 7.6 ✓ | 7.78 / 7.12 ✓ | 6.96 / 7.62 ✓ |
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
| t_stat | 5.09 / 4.11 ~ | 8.87 / 6.93 ✗ | 8.61 / 6.8 ✗ | 5.86 / 7.52 ~ |
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
| long: intercept | 0.40% / 0.10% ✗ | 0.48% / 0.24% ✗ | 0.65% / 0.29% ✗ | 0.37% / -0.10% ✗ |
| t: long: intercept | 2.24 / 0.47 ✗ | 2.93 / 1.27 ✗ | 7.01 / 2.85 ✗ | 6.88 / -1.32 ✗ |
| long: market | 0.619 / 0.374 ✗ | 0.653 / 0.476 ✗ | 0.859 / 0.485 ✗ | 0.793 / 0.586 ✗ |
| t: long: market | 7.68 / 4.6 ✗ | 9.96 / 6.68 ✗ | 14.3 / 10.2 ✗ | 17.1 / 15 ~ |
| long: smb | 0.0635 / -0.168 ✗ | 0.059 / -0.0651 ✗ | 0.238 / 0.0112 ✗ | 0.348 / 0.222 ✗ |
| t: long: smb | 0.739 / -1.74 ✗ | 0.79 / -0.8 ✗ | 3.62 / 0.27 ✗ | 6.4 / 3.45 ✗ |
| long: hml | 0.591 / 0.484 ~ | 0.605 / 0.525 ~ | 0.523 / 0.395 ✗ | 0.162 / 0.257 ✗ |
| t: long: hml | 9.4 / 7.12 ✗ | 11.2 / 9.36 ~ | 10.1 / 9.76 ✓ | 4.5 / 7.49 ✗ |
| long: momentum | -0.0708 / -0.0543 ✗ | -0.0714 / -0.0446 ✗ | -0.202 / -0.109 ✗ | -0.144 / -0.0883 ✗ |
| t: long: momentum | -1.63 / -1.48 ✓ | -1.62 / -1.21 ✗ | -5.11 / -3.53 ✗ | -6.32 / -3.53 ✗ |
| long: reversal | -0.0937 / 0.159 ✗ | -0.0767 / 0.096 ✗ | -0.0943 / 0.173 ✗ | 0.255 / 0.392 ✗ |
| t: long: reversal | -1.37 / 1.83 ✗ | -1.33 / 1.26 ✗ | -1.91 / 4.33 ✗ | 6.62 / 10.4 ✗ |
| long: r2 | 0.351 / 0.39 ✓ | 0.449 / 0.48 ✓ | 0.796 / 0.78 ✓ | 0.967 / 0.97 ✓ |
| short: intercept | -0.40% / -0.44% ✓ | -0.42% / -0.52% ~ | -0.17% / -0.43% ✗ | -0.26% / -0.61% ✗ |
| t: short: intercept | -2.44 / -2.74 ~ | -2.89 / -3.35 ~ | -1.89 / -4.26 ✗ | -4.45 / -5.22 ~ |
| short: market | 0.588 / 0.441 ✗ | 0.671 / 0.508 ✗ | 0.918 / 0.562 ✗ | 0.926 / 0.731 ✗ |
| t: short: market | 7.65 / 6.19 ~ | 10.1 / 8.44 ~ | 19.1 / 9.74 ✗ | 23.7 / 12.1 ✗ |
| short: smb | 0.00142 / -0.125 ✗ | 0.0651 / -0.0662 ✗ | 0.258 / 0.0345 ✗ | 0.467 / 0.293 ✗ |
| t: short: smb | 0.0169 / -2 ✗ | 0.883 / -1.22 ✗ | 3.8 / 0.95 ✗ | 7.73 / 3.15 ✗ |
| short: hml | 0.586 / 0.427 ✗ | 0.586 / 0.48 ~ | 0.529 / 0.412 ✗ | 0.186 / 0.311 ✗ |
| t: short: hml | 10.1 / 6.92 ✗ | 11.1 / 9.47 ~ | 10 / 11.5 ~ | 5.21 / 8.11 ✗ |
| short: momentum | -0.00845 / -0.0262 ✗ | -0.0254 / 0.00361 ✗ | -0.0685 / -0.00589 ✗ | 0.0286 / 0.0925 ✗ |
| t: short: momentum | -0.2 / -0.65 ✗ | -0.631 / 0.1 ✗ | -2 / -0.21 ✗ | 1.43 / 2.81 ✗ |
| short: reversal | -0.0515 / 0.0566 ✗ | -0.106 / 0.0237 ✗ | -0.174 / 0.0783 ✗ | 0.0449 / 0.191 ✗ |
| t: short: reversal | -0.818 / 1.13 ✗ | -1.92 / 0.55 ✗ | -4.21 / 1.9 ✗ | 1.21 / 2.98 ✗ |
| short: r2 | 0.412 / 0.41 ✓ | 0.483 / 0.49 ✓ | 0.781 / 0.75 ✓ | 0.959 / 0.93 ✓ |

Cells: 136; ✓ 34 (within 10%), ~ 20 (within 25%), ✗ 82.

The regression block is each book's own monthly return less the 30-day
bill (Table 7's note, p. 821) on the same five factors Table 4 uses, with
Newey-West t-statistics at six lags; coefficients, R2 and the t-statistics are
scored (SCORE_LOG row 25).


### The same block with French's ST_Rev in the reversal column (unscored)

The scored rows above use the losers-only series. These are the same 56 cells with the
other series; marked only for comparison, they do not count.

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| long: intercept | 0.30% vs 0.10% ✗ | 0.39% vs 0.24% ✗ | 0.54% vs 0.29% ✗ | 0.46% vs -0.10% ✗ |
| t: long: intercept | 1.72 vs 0.47 ✗ | 2.40 vs 1.27 ✗ | 5.38 vs 2.85 ✗ | 6.78 vs -1.32 ✗ |
| long: market | 0.514 vs 0.374 ✗ | 0.565 vs 0.476 ~ | 0.75 vs 0.485 ✗ | 1.04 vs 0.586 ✗ |
| t: long: market | 11.73 vs 4.60 ✗ | 14.02 vs 6.68 ✗ | 23.60 vs 10.23 ✗ | 51.38 vs 14.99 ✗ |
| long: smb | -0.0357 vs -0.168 ✗ | -0.0231 vs -0.0651 ✗ | 0.136 vs 0.0112 ✗ | 0.597 vs 0.222 ✗ |
| t: long: smb | -0.64 vs -1.74 ✗ | -0.46 vs -0.80 ✗ | 4.08 vs 0.27 ✗ | 14.18 vs 3.45 ✗ |
| long: hml | 0.569 vs 0.484 ~ | 0.587 vs 0.525 ~ | 0.501 vs 0.395 ✗ | 0.218 vs 0.257 ~ |
| t: long: hml | 8.80 vs 7.12 ~ | 10.62 vs 9.36 ~ | 9.21 vs 9.76 ✓ | 5.93 vs 7.49 ~ |
| long: momentum | -0.0315 vs -0.0543 ✗ | -0.0368 vs -0.0446 ~ | -0.157 vs -0.109 ✗ | -0.189 vs -0.0883 ✗ |
| t: long: momentum | -0.84 vs -1.48 ✗ | -0.99 vs -1.21 ~ | -3.96 vs -3.53 ~ | -6.67 vs -3.53 ✗ |
| long: reversal | 0.0432 vs 0.159 ✗ | 0.0444 vs 0.096 ✗ | 0.0648 vs 0.173 ✗ | 0.115 vs 0.392 ✗ |
| t: long: reversal | 0.90 vs 1.83 ✗ | 0.93 vs 1.26 ✗ | 1.72 vs 4.33 ✗ | 3.88 vs 10.44 ✗ |
| long: r2 | 0.349 vs 0.39 ~ | 0.448 vs 0.48 ✓ | 0.795 vs 0.78 ✓ | 0.96 vs 0.97 ✓ |
| short: intercept | -0.44% vs -0.44% ✓ | -0.50% vs -0.52% ✓ | -0.29% vs -0.43% ✗ | -0.20% vs -0.61% ✗ |
| t: short: intercept | -2.67 vs -2.74 ✓ | -3.45 vs -3.35 ✓ | -3.02 vs -4.26 ✗ | -3.30 vs -5.22 ✗ |
| short: market | 0.533 vs 0.441 ~ | 0.558 vs 0.508 ✓ | 0.735 vs 0.562 ✗ | 0.978 vs 0.731 ✗ |
| t: short: market | 12.93 vs 6.19 ✗ | 14.88 vs 8.44 ✗ | 22.33 vs 9.74 ✗ | 47.57 vs 12.13 ✗ |
| short: smb | -0.0515 vs -0.125 ✗ | -0.0436 vs -0.0662 ✗ | 0.0811 vs 0.0345 ✗ | 0.515 vs 0.293 ✗ |
| t: short: smb | -1.08 vs -2.00 ✗ | -0.96 vs -1.22 ~ | 2.35 vs 0.95 ✗ | 13.76 vs 3.15 ✗ |
| short: hml | 0.574 vs 0.427 ✗ | 0.562 vs 0.48 ~ | 0.489 vs 0.412 ~ | 0.197 vs 0.311 ✗ |
| t: short: hml | 9.67 vs 6.92 ✗ | 10.16 vs 9.47 ✓ | 8.30 vs 11.54 ✗ | 5.20 vs 8.11 ✗ |
| short: momentum | 0.0087 vs -0.0262 ✗ | 0.00791 vs 0.00361 ✗ | -0.0175 vs -0.00589 ✗ | 0.00661 vs 0.0925 ✗ |
| t: short: momentum | 0.24 vs -0.65 ✗ | 0.24 vs 0.10 ✗ | -0.50 vs -0.21 ✗ | 0.26 vs 2.81 ✗ |
| short: reversal | 0.00693 vs 0.0566 ✗ | 0.00594 vs 0.0237 ✗ | -0.00296 vs 0.0783 ✗ | -0.0329 vs 0.191 ✗ |
| t: short: reversal | 0.19 vs 1.13 ✗ | 0.16 vs 0.55 ✗ | -0.09 vs 1.90 ✗ | -1.17 vs 2.98 ✗ |
| short: r2 | 0.411 vs 0.41 ✓ | 0.478 vs 0.49 ✓ | 0.768 vs 0.75 ✓ | 0.959 vs 0.93 ✓ |

With French's ST_Rev these 104 regression cells score 21.5 of 104, against 17.5 with the losers-only series.

## Tables 4, 5 Panel A and 8 and Figure 4: conventions

Tables 4, 5 Panel A and 8 and Figure 4 describe the one-day-wait series of Table 1
Panel B; rows that repeat a scored row (means, standard deviations, Table 4's serial
correlation, Table 5's loss probability and minimum) are left out. Percentiles are
linearly interpolated (pandas' default) and serial correlation is the lag-1
correlation of calendar-adjacent months; the paper states neither estimator. The
regressions are OLS on French's market, SMB, HML, momentum and short-term reversal
factors, and on Ibbotson's market, small-stock, default and horizon premia (Ibbotson's
bond returns from Goyal and Welch's data, the small-stock series rebuilt from CRSP by
its recipe; coefficients, R2 and the Newey-West t-statistics at six lags are scored,
and its factor standard deviations are too (under Table 8). Table 4's equity-premium column is
French's Mkt-RF, the regressions' market
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
| intercept | 0.801% / 0.545% ✗ | 0.900% / 0.764% ~ | 0.825% / 0.714% ~ | 0.633% / 0.512% ~ |
| t: intercept | 6.75 / 3.81 ✗ | 8.72 / 7.08 ~ | 11.2 / 8.66 ✗ | 9.43 / 5.3 ✗ |
| market | 0.0315 / -0.0666 ✗ | -0.0181 / -0.0316 ✗ | -0.0591 / -0.077 ~ | -0.133 / -0.145 ✓ |
| t: market | 0.558 / -1.03 ✗ | -0.427 / -0.64 ✗ | -1.43 / -1.77 ~ | -4.37 / -3.1 ✗ |
| smb | 0.0621 / -0.0423 ✗ | -0.0061 / 0.00111 ✗ | -0.0194 / -0.0233 ~ | -0.118 / -0.0708 ✗ |
| t: smb | 1.25 / -0.71 ✗ | -0.143 / 0.02 ✗ | -0.516 / -0.5 ✓ | -3.99 / -1.66 ✗ |
| hml | 0.00558 / 0.0574 ✗ | 0.0189 / 0.0451 ✗ | -0.00562 / -0.0172 ✗ | -0.0244 / -0.054 ✗ |
| t: hml | 0.152 / 1.37 ✗ | 0.62 / 1.45 ✗ | -0.229 / -0.59 ✗ | -1.01 / -1.82 ✗ |
| momentum | -0.0624 / -0.028 ✗ | -0.046 / -0.0482 ✓ | -0.134 / -0.103 ✗ | -0.172 / -0.181 ✓ |
| t: momentum | -2.27 / -0.94 ✗ | -2.19 / -2.45 ~ | -6.35 / -5.83 ✓ | -10.6 / -8.5 ~ |
| reversal | -0.0423 / 0.102 ✗ | 0.0297 / 0.0724 ✗ | 0.0796 / 0.0946 ~ | 0.21 / 0.201 ✓ |
| t: reversal | -0.944 / 1.5 ✗ | 0.801 / 1.27 ✗ | 2.49 / 2.24 ~ | 7.46 / 4.34 ✗ |
| r2 | 0.0131 / 0.05 ✗ | 0.0326 / 0.09 ✗ | 0.242 / 0.18 ✗ | 0.623 / 0.54 ~ |
| ibbotson_intercept | 0.719% / 0.716% ✓ | 0.875% / 0.857% ✓ | 0.730% / 0.766% ✓ | 0.561% / 0.651% ~ |
| t: ibbotson_intercept | 6.31 / 6.32 ✓ | 9.12 / 9.25 ✓ | 9.82 / 9.39 ✓ | 7 / 7.77 ✓ |
| ibbotson_market | -0.0296 / -0.00182 ✗ | -0.009 / 0.0138 ✗ | 0.0234 / 0.0164 ✗ | 0.097 / 0.0647 ✗ |
| t: ibbotson_market | -1.03 / -0.07 ✗ | -0.462 / 0.74 ✗ | 1.12 / 0.9 ~ | 3.98 / 1.98 ✗ |
| ibbotson_small_premium | 0.00723 / 0.0412 ✗ | 0.0186 / 0.0523 ✗ | 0.0482 / 0.0365 ✗ | 0.0761 / 0.0761 ✓ |
| t: ibbotson_small_premium | 0.301 / 1.32 ✗ | 0.868 / 2.22 ✗ | 2.12 / 1.66 ✗ | 2.19 / 1.93 ~ |
| ibbotson_default_premium | 0.156 / 0.146 ✓ | 0.121 / 0.16 ~ | 0.156 / 0.168 ✓ | 0.242 / 0.306 ~ |
| t: ibbotson_default_premium | 1.52 / 1.11 ✗ | 1.4 / 1.38 ✓ | 2.03 / 1.81 ~ | 2.69 / 2.82 ✓ |
| ibbotson_horizon_premium | 0.0779 / 0.08 ✓ | 0.0795 / 0.0682 ~ | 0.0491 / 0.0403 ~ | 0.00918 / 0.0342 ✗ |
| t: ibbotson_horizon_premium | 1.63 / 1.55 ✓ | 2.2 / 1.64 ✗ | 1.43 / 1.04 ✗ | 0.256 / 0.77 ✗ |
| ibbotson_r2 | 0.0106 / 0.02 ✗ | 0.0199 / 0.05 ✗ | 0.0474 / 0.04 ~ | 0.178 / 0.15 ~ |

| statistic | French's Mkt-RF (ours / paper) |
|---|---|
| equity premium: mean | 0.409% / 0.410% ✓ |
| equity premium: std | 4.515% / 4.509% ✓ |
| equity premium: sharpe | 0.0905 / 0.09 ✓ |
| equity premium: serial_correlation | 0.0476 / 0.05 ✓ |

Cells: 104; ✓ 28 (within 10%), ~ 22 (within 25%), ✗ 54.

## Table 5 Panel A (monthly value at risk)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| serial_correlation | 0.128 / 0.14 ✓ | 0.244 / 0.24 ✓ | 0.0778 / 0.19 ✗ | 0.177 / 0.12 ✗ |
| var_1 | -3.588% / -4.320% ~ | -2.238% / -1.943% ~ | -2.749% / -2.236% ~ | -2.170% / -1.994% ✓ |
| var_5 | -2.141% / -2.142% ✓ | -1.098% / -1.002% ✓ | -1.449% / -1.293% ~ | -1.190% / -0.877% ✗ |
| var_10 | -1.497% / -1.516% ✓ | -0.614% / -0.577% ✓ | -0.988% / -0.756% ✗ | -0.808% / -0.614% ✗ |
| var_25 | -0.403% / -0.460% ~ | -0.048% / 0.054% ✗ | -0.127% / -0.145% ~ | -0.268% / -0.146% ✗ |

Cells: 20; ✓ 7 (within 10%), ~ 6 (within 25%), ✗ 7.

## Table 5 Panel B (daily value at risk)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 0.035% / 0.033% ✓ | 0.043% / 0.040% ✓ | 0.037% / 0.035% ✓ | 0.029% / 0.027% ✓ |
| std | 0.496% / 0.492% ✓ | 0.302% / 0.296% ✓ | 0.288% / 0.277% ✓ | 0.191% / 0.169% ~ |
| serial_correlation | -0.11 / -0.12 ~ | -0.06 / -0.06 ✓ | 0.04 / 0.00 ✗ | 0.33 / 0.35 ✓ |
| var_1 | -1.214% / -1.236% ✓ | -0.667% / -0.647% ✓ | -0.669% / -0.653% ✓ | -0.397% / -0.327% ~ |
| var_5 | -0.700% / -0.710% ✓ | -0.413% / -0.398% ✓ | -0.404% / -0.400% ✓ | -0.248% / -0.202% ~ |
| var_10 | -0.507% / -0.504% ✓ | -0.299% / -0.293% ✓ | -0.298% / -0.288% ✓ | -0.178% / -0.149% ~ |
| var_25 | -0.236% / -0.239% ✓ | -0.132% / -0.133% ✓ | -0.139% / -0.130% ✓ | -0.079% / -0.071% ~ |
| share_negative | 0.47 / 0.47 ✓ | 0.442 / 0.44 ✓ | 0.447 / 0.45 ✓ | 0.451 / 0.46 ✓ |
| min | -10.021% / -10.079% ✓ | -5.955% / -6.723% ~ | -1.786% / -1.987% ~ | -1.472% / -1.069% ✗ |

The daily series is the monthly series' own object one level down: each trading
day carries the equal-weighted mean over the cohorts trading that day of the
cohort's daily fully-invested return, the Jegadeesh-Titman overlap average at
daily frequency, and a day on which a cohort holds no position is skipped there
exactly as a NaN month is skipped in the monthly average. The cohort cache stores
that series since format 7, so the block is reproducible from the cache alone.
Every row is a function of the daily returns, so none of the nine repeats a
monthly row of Table 5 Panel A or Table 1 Panel B. Percentiles are linearly
interpolated (pandas' default, as in Panel A) and serial correlation is the lag-1
autocorrelation of consecutive trading days; the paper states neither estimator.
The paper prints the 101-120 serial correlation as 0.00, a rounded zero, where a
ratio is undefined, so that cell is marked on whether ours prints the same two
decimals. The top five, top twenty and 101-120 columns agree within a few percent
on every row. The "all" column is the loosest: its daily standard deviation is
0.191% against the paper's 0.169%, 1.13 times, and each quantile moves with it
(that gap was 1.44 times before the position-weighted short, REVIEW_NOTES 29).
That is the inconsistency COVERAGE.md item 4 records inside the paper itself,
where its monthly "all" standard deviation is 9.3 of its own daily units while
the other three columns imply 4-7; it is reported, not adjusted.

Cells: 36; ✓ 26 (within 10%), ~ 8 (within 25%), ✗ 2.

## Table 8 (subperiod analysis)

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| pre_mean | 0.963% / 1.034% ✓ | 1.172% / 1.181% ✓ | 0.895% / 1.052% ~ | 0.896% / 0.992% ✓ |
| pre_std | 2.222% / 2.259% ✓ | 1.612% / 1.689% ✓ | 1.482% / 1.527% ✓ | 1.436% / 1.651% ~ |
| post_mean | 0.286% / 0.217% ✗ | 0.381% / 0.375% ✓ | 0.526% / 0.327% ✗ | 0.143% / 0.212% ✗ |
| post_std | 1.493% / 1.660% ~ | 1.001% / 0.987% ✓ | 1.375% / 1.121% ~ | 1.622% / 1.295% ✗ |
| pre_intercept | 0.966% / 0.353% ✗ | 1.114% / 0.670% ✗ | 0.901% / 0.710% ✗ | 0.804% / 0.446% ✗ |
| t: pre_intercept | 6.33 / 1.72 ✗ | 8.48 / 4.41 ✗ | 9.27 / 6.54 ✗ | 11.5 / 4.19 ✗ |
| pre_market | -0.211 / -0.434 ✗ | -0.194 / -0.312 ✗ | -0.24 / -0.289 ~ | -0.284 / -0.434 ✗ |
| t: pre_market | -2.05 / -4.29 ✗ | -2.53 / -3.57 ✗ | -4.86 / -3.8 ✗ | -5.5 / -7.26 ~ |
| pre_smb | -0.225 / -0.442 ✗ | -0.226 / -0.332 ✗ | -0.221 / -0.275 ~ | -0.292 / -0.402 ✗ |
| t: pre_smb | -1.98 / -3.75 ✗ | -2.17 / -2.86 ~ | -3.93 / -2.86 ✗ | -4.05 / -5.76 ✗ |
| pre_hml | -0.0173 / 0.0357 ✗ | -0.00297 / 0.0316 ✗ | -0.0631 / -0.0684 ✓ | -0.0505 / -0.0698 ✗ |
| t: pre_hml | -0.36 / 0.64 ✗ | -0.0683 / 0.73 ✗ | -2.08 / -1.84 ~ | -1.92 / -1.97 ✓ |
| pre_momentum | -0.0767 / 0.0129 ✗ | -0.0696 / -0.0163 ✗ | -0.171 / -0.0769 ✗ | -0.179 / -0.158 ~ |
| t: pre_momentum | -2.14 / 0.29 ✗ | -2.46 / -0.5 ✗ | -8.13 / -2.92 ✗ | -8.61 / -5.01 ✗ |
| pre_reversal | 0.167 / 0.436 ✗ | 0.2 / 0.333 ✗ | 0.247 / 0.288 ~ | 0.355 / 0.452 ~ |
| t: pre_reversal | 1.67 / 4.44 ✗ | 2.6 / 3.62 ✗ | 6.14 / 4.05 ✗ | 6.29 / 7.98 ~ |
| pre_r2 | 0.0522 / 0.19 ✗ | 0.0917 / 0.23 ✗ | 0.338 / 0.26 ✗ | 0.654 / 0.7 ✓ |
| post_intercept | 0.271% / 0.337% ~ | 0.367% / 0.417% ~ | 0.564% / 0.363% ✗ | 0.213% / -0.065% ✗ |
| t: post_intercept | 2.08 / 2.12 ✓ | 4.46 / 3.77 ~ | 7.51 / 3.01 ✗ | 2.12 / -0.56 ✗ |
| post_market | 0.182 / 0.0734 ✗ | 0.0447 / 0.048 ✓ | 0.0163 / 0.00241 ✗ | -0.0736 / -0.0696 ✓ |
| t: post_market | 3.88 / 1.68 ✗ | 1.3 / 1.81 ✗ | 0.31 / 0.06 ✗ | -2.59 / -2.43 ✓ |
| post_smb | 0.13 / -0.004 ✗ | 0.009 / 0.0289 ✗ | 0.00279 / 0.0233 ✗ | -0.101 / -0.0606 ✗ |
| t: post_smb | 3.34 / -0.1 ✗ | 0.35 / 1.32 ✗ | 0.0586 / 0.69 ✗ | -4.29 / -2.83 ✗ |
| post_hml | 0.0476 / 0.0344 ✗ | 0.00249 / 0.0141 ✗ | 0.0257 / 0.0183 ✗ | -0.0348 / -0.082 ✗ |
| t: post_hml | 1.01 / 0.61 ✗ | 0.0769 / 0.45 ✗ | 0.829 / 0.5 ✗ | -1.09 / -2.65 ✗ |
| post_momentum | -0.0143 / -0.00424 ✗ | -0.00328 / -0.0227 ✗ | -0.0823 / -0.0884 ✓ | -0.153 / -0.127 ~ |
| t: post_momentum | -0.564 / -0.13 ✗ | -0.147 / -1.29 ✗ | -2.44 / -4.17 ✗ | -6.5 / -7.59 ~ |
| post_reversal | -0.0789 / -0.0626 ✗ | -0.00622 / -0.0173 ✗ | 0.046 / 0.024 ✗ | 0.166 / 0.188 ~ |
| t: post_reversal | -3.2 / -1.76 ✗ | -0.283 / -0.67 ✗ | 1.15 / 0.54 ✗ | 8.99 / 5.56 ✗ |
| post_r2 | 0.124 / 0.02 ✗ | 0.0291 / 0.04 ✗ | 0.202 / 0.19 ✓ | 0.69 / 0.64 ✓ |

Table 8's published "Factor sd" column: these cells measure the factor
inputs the regressions above are built from, over the same months.
The first four are French's series at the vintage the run names: at the
paper's 2005 files they reproduce the printed values (REVIEW_NOTES
sections 49 and 71), today's HML being 7.8% short after 1988; the reversal
cell is the hypothesis of section 61 (the
losers-only series), which is why its after-1988 value is the one
that misses.

| statistic | before 1989 | after 1988 |
|---|---|---|
| factor sd: market | 0.04580 / 0.04580 ✓ | 0.04407 / 0.04390 ✓ |
| factor sd: smb | 0.02920 / 0.02923 ✓ | 0.03887 / 0.03856 ✓ |
| factor sd: hml | 0.02610 / 0.02597 ✓ | 0.03644 / 0.03641 ✓ |
| factor sd: momentum | 0.03500 / 0.03506 ✓ | 0.04937 / 0.04926 ✓ |
| factor sd: reversal | 0.06852 / 0.07228 ✓ | 0.06857 / 0.04448 ✗ |

Cells: 130; ✓ 27 (within 10%), ~ 19 (within 25%), ✗ 84.

## Figure 4 (top 20 against 101-120, correlations printed in the text)

| statistic | raw | five-factor residuals |
|---|---|---|
| correlation, full sample | 0.326 / 0.48 ✗ | 0.279 / 0.41 ✗ |
| correlation, before 1989 | 0.392 / 0.51 ~ | 0.33 / 0.42 ~ |
| correlation, after 1988 | 0.0541 / 0.18 ✗ | 0.0945 / 0.2 ✗ |

Cells: 6; ✓ 0 (within 10%), ~ 2 (within 25%), ✗ 4.

## Numbers printed in the text

The paper prints three result numbers outside its tables: the all-pair
portfolio's average size in the captions of Tables 1, 5, 8 and 9 ("The
average number of pairs in the all-pair portfolio is 2057"), section 1.2's
hold-out sentence (p. 800), and footnote 4's delisting result (p. 804). Each
is scored once here.

| check | ours / paper |
|---|---|
| the average number of pairs in the all-pair portfolio | 2009 / 2057 ✓ |

Section 1.2's hold-out sentence (top 20, fully invested, 1999-2002): the
scored reading is the no-wait rule, as REVIEW_NOTES section 17 recorded
before these cells were scored; annual figures are twelve times the monthly
mean and the square root of twelve times the monthly standard deviation,
and the t-statistic is the six-lag Newey-West t of the monthly mean.

| statistic | ours / paper |
|---|---|
| annual excess return | 6.53% / 10.40% ✗ |
| annual standard deviation | 4.45% / 3.80% ~ |
| Newey-West t-statistic | 4.25 / 4.82 ~ |

One-day-wait reading, unscored: 3.7% vs 10.4%; 4.4% vs 3.8%; t 2.4 vs 4.82.

Footnote 4's delisting assumption (top 20, no wait), from the cache
--delist-cache names (make delist100 builds it with --long-delisting-loss):

| statistic | ours / paper |
|---|---|
| mean monthly return | 1.27% / 1.32% ✓ |
| standard deviation | 1.87% / 1.90% ✓ |

Cells: 6; ✓ 3 (within 10%), ~ 2 (within 25%), ✗ 1.

## Table 9 Panel A (top three size deciles, one-day wait)

Section 3.9 (p. 824): pairs formed only from stocks in the top three size
deciles. The rows are Table 1 Panel B's statistics over that screened
universe, from the cache --table9a-cache names (make table9a builds it).

The printed skewness and kurtosis rows are scored as printed: our skewness
against the row labelled Skewness, our kurtosis against Kurtosis. Those two
rows contradict Table 1's (COVERAGE.md, where the published version
contradicts itself, 1: the row labelled Kurtosis reads 0.02-1.77 and the
one labelled Skewness 7.01-11.67). The swapped reading is printed below as
an unscored diagnostic; the paper's values are the paper's.

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | 0.90% / 0.83% ✓ | 0.93% / 0.91% ✓ | 0.66% / 0.73% ✓ | 0.66% / 0.69% ✓ |
| nw_se | 0.13% / 0.11% ~ | 0.11% / 0.10% ~ | 0.08% / 0.07% ✓ | 0.06% / 0.06% ✓ |
| t_stat | 6.98 / 7.47 ✓ | 8.41 / 9.48 ~ | 8.78 / 9.66 ✓ | 10.9 / 10.8 ✓ |
| median | 0.64% / 0.80% ~ | 0.83% / 0.79% ✓ | 0.56% / 0.61% ✓ | 0.55% / 0.51% ✓ |
| std | 2.12% / 1.90% ~ | 1.62% / 1.46% ~ | 1.54% / 1.58% ✓ | 1.24% / 1.29% ✓ |
| kurtosis | 9.31 / 0.02 ✗ | 9.21 / 0.98 ✗ | 4.67 / 0.8 ✗ | 6.7 / 1.77 ✗ |
| skew | -0.218 / 7.01 ✗ | 0.141 / 8.2 ✗ | 0.382 / 6.46 ✗ | 1.12 / 11.7 ✗ |
| min | -14.41% / -10.89% ✗ | -9.63% / -5.65% ✗ | -4.65% / -3.80% ~ | -2.98% / -2.68% ~ |
| max | 9.24% / 10.14% ✓ | 9.78% / 10.00% ✓ | 7.33% / 10.64% ✗ | 7.23% / 10.48% ✗ |
| share_negative | 0.331 / 0.32 ✓ | 0.249 / 0.26 ✓ | 0.346 / 0.33 ✓ | 0.3 / 0.27 ~ |
| committed_mean | 0.54% / 0.49% ✓ | 0.52% / 0.51% ✓ | 0.39% / 0.46% ~ | 0.38% / 0.40% ✓ |

The two transposed rows, read swapped (unscored):

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| skew vs printed Kurtosis | -0.22 vs 0.02 | 0.14 vs 0.98 | 0.38 vs 0.80 | 1.12 vs 1.77 |
| kurtosis vs printed Skewness | 9.31 vs 7.01 | 9.21 vs 8.20 | 4.67 vs 6.46 | 6.70 vs 11.67 |

Cells: 44; ✓ 22 (within 10%), ~ 10 (within 25%), ✗ 12.

## Table 9 Panel B (short recalls on high volume, one-day wait)

Section 3.9 (pp. 824-825): recalls on the short positions, and the closing
of the pair, on days with high volume -- daily volume more than one
standard deviation above its average over the 18 months (both split
adjusted). High volume is the paper's proxy for divergence of opinion.
The note fixes the rule: "Panel B reports the summary statistics for the
rule that waits one day before opening and closing the position", 474
monthly observations, Newey-West six lags, absolute kurtosis.

The reading is the same-day recall close (REVIEW_NOTES section 74,
claims/TABLE9B_READINGS.md): a recalled short ends the pair at the close of
the flagged day itself, also under the one-day wait, because the text has
the closing happen "on days with high volume" and a recall is forced
rather than a trading decision the wait applies to. The pair is re-entered
only after the spread has come back inside two sigma and a *new* divergence
fires. This reading scores 21.0 of 44 against 18.0 for the next-day close
(section 58's reading, --table9b-cache data/processed/replication/
vol_common_recalls), and like every reading measured it raises the mean
against Table 1 Panel B where the paper's falls by 4-13 bp, so claim 20 (b)
stays unreplicated. The rows are Table 1 Panel B's statistics over the
per-cohort monthly series in the cache --table9b-cache names (make table9b
builds it with --reading R1), with the committed series supplying the last row.

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean (fully invested) | 0.78% / 0.62% ✗ | 1.10% / 0.85% ✗ | 0.97% / 0.66% ✗ | 1.25% / 0.58% ✗ |
| nw_se | 0.13% / 0.11% ~ | 0.12% / 0.09% ✗ | 0.10% / 0.08% ~ | 0.10% / 0.10% ✓ |
| t_stat | 5.81 / 5.39 ✓ | 9.08 / 9.07 ✓ | 9.42 / 7.81 ~ | 12.8 / 5.95 ✗ |
| median | 0.66% / 0.59% ~ | 0.97% / 0.70% ✗ | 0.95% / 0.53% ✗ | 0.99% / 0.31% ✗ |
| std | 2.26% / 2.21% ✓ | 1.76% / 1.49% ~ | 1.85% / 1.50% ~ | 1.67% / 1.55% ✓ |
| skew | 0.231 / 0.15 ✗ | 0.505 / 0.48 ✓ | 0.25 / 1.03 ✗ | 1.93 / 2.82 ✗ |
| kurtosis | 5.9 / 5.39 ✓ | 6.28 / 6 ✓ | 3.42 / 7.39 ✗ | 11.5 / 19 ✗ |
| min | -9.58% / -9.61% ✓ | -7.97% / -6.59% ~ | -4.71% / -4.41% ✓ | -3.68% / -3.46% ✓ |
| max | 11.31% / 10.50% ✓ | 8.72% / 7.26% ~ | 7.16% / 10.08% ✗ | 12.23% / 14.17% ~ |
| share_negative | 0.354 / 0.39 ✓ | 0.251 / 0.26 ✓ | 0.302 / 0.34 ~ | 0.165 / 0.37 ✗ |
| mean (committed) | 0.34% / 0.30% ~ | 0.39% / 0.35% ~ | 0.30% / 0.30% ✓ | 0.39% / 0.20% ✗ |

Cells: 44; ✓ 15 (within 10%), ~ 12 (within 25%), ✗ 17.

## Table 6 (random pairs sorted on prior one-month return)

Section 3.6 (pp. 818-819): at each true-pair opening the bootstrap
replaces the two legs with random securities drawn from the same decile
of the previous month's return, opens and closes them with the true trade
and averages each cell over the 200 replications. Our cells are our own
draws against our own true-pair series from the same cache, not the
paper's measurement, so this is the least comparable block in the check
(REVIEW_NOTES section 65). The values come from the per-cohort outputs
that --table6-cache names (make table6 runs the bootstrap).

The caption (p. 819) says 'value-weighted portfolios of n pairs', so the
committed rows are the value-weighted book scaled by the share of pairs
open (the book-share reading, REVIEW_NOTES section 75): that literal-to-
book-share choice is Table 6's own, and the literal series stays the
definition for Tables 1, 3, 7 and 9, whose captions do not say
'value-weighted portfolios'.

| statistic | Top 5 | Top 20 | Top 100-120 | All 120 |
|---|---|---|---|---|
| A. No waiting, fully invested: Mean excess return | -0.0020329 / -0.00137 ✗ | -0.0031073 / -0.00111 ✗ | -0.0030622 / -0.00105 ✗ | -0.003397 / -0.00113 ✗ |
| A. No waiting, fully invested: Standard deviation | 0.041223 / 0.05521 ✗ | 0.021253 / 0.02295 ✓ | 0.021454 / 0.02264 ✓ | 0.010102 / 0.012 ~ |
| A. No waiting, fully invested: Median | -0.002155 / -0.00192 ~ | -0.0029814 / -0.00153 ✗ | -0.0030097 / -0.00156 ✗ | -0.0031667 / -0.00162 ✗ |
| A. No waiting, committed capital: Mean excess return | -0.0015433 / -0.00083 ✗ | -0.0021337 / -0.00077 ✗ | -0.0023018 / -0.00089 ✗ | -0.0023949 / -0.00091 ✗ |
| A. No waiting, committed capital: Standard deviation | 0.02397 / 0.02635 ✓ | 0.012631 / 0.01358 ✓ | 0.013338 / 0.01443 ✓ | 0.0064668 / 0.0076 ~ |
| A. No waiting, committed capital: Median | -0.0015311 / -0.00123 ~ | -0.0020507 / -0.001 ✗ | -0.0022256 / -0.00123 ✗ | -0.0022 / -0.00122 ✗ |
| B. Wait one day, fully invested: Mean excess return | -0.0020042 / -0.00177 ~ | -0.0029029 / -4e-05 ✗ | -0.0030179 / -0.00154 ✗ | -0.0033719 / -0.00156 ✗ |
| B. Wait one day, fully invested: Standard deviation | 0.041328 / 0.05966 ✗ | 0.021457 / 0.0531 ✗ | 0.021202 / 0.02404 ~ | 0.0099892 / 0.01213 ~ |
| B. Wait one day, fully invested: Median | -0.0021427 / -0.00241 ~ | -0.0028034 / -0.00172 ✗ | -0.0030588 / -0.00206 ✗ | -0.0031578 / -0.00201 ✗ |
| B. Wait one day, committed capital: Mean excess return | -0.0014873 / -0.00103 ✗ | -0.0019959 / -0.00094 ✗ | -0.0022432 / -0.00112 ✗ | -0.0023553 / -0.00112 ✗ |
| B. Wait one day, committed capital: Standard deviation | 0.024173 / 0.02811 ~ | 0.012746 / 0.01363 ✓ | 0.01315 / 0.01449 ✓ | 0.0063626 / 0.00761 ~ |
| B. Wait one day, committed capital: Median | -0.0015539 / -0.00152 ✓ | -0.0019384 / -0.00118 ✗ | -0.0022098 / -0.00148 ✗ | -0.0021632 / -0.00139 ✗ |

Cells: 48; ✓ 8 (within 10%), ~ 10 (within 25%), ✗ 30.

## Reversal factor: French's ST_Rev, the text's long-short factor (unscored)

The scored regressions above use the losers-only series the paper's own Table 8
arithmetic implies, not the long-short factor its text describes: the printed
reversal standard deviation is 0.0723 before 1989, which ST_Rev (0.0259) cannot
be, while the equal-weighted bottom three prior-month deciles less the T-bill
give 0.0685 with the implied +0.81 market and +0.79 SMB correlations (REVIEW_NOTES
sections 51 and 61). The rows below repeat the regressions with ST_Rev in place
of the scored series. They are not scored.

| Table 4, full sample: ours vs paper | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| intercept | 0.74% vs 0.55% ✗ | 0.89% vs 0.76% ~ | 0.83% vs 0.71% ~ | 0.66% vs 0.51% ✗ |
| t: intercept | 6.27 vs 3.81 ✗ | 8.81 vs 7.08 ~ | 11.08 vs 8.66 ✗ | 10.09 vs 5.30 ✗ |
| market | -0.0184 vs -0.0666 ✗ | 0.00741 vs -0.0316 ✗ | 0.0147 vs -0.077 ✗ | 0.0656 vs -0.145 ✗ |
| t: market | -0.67 vs -1.03 ✗ | 0.40 vs -0.64 ✗ | 0.91 vs -1.77 ✗ | 4.52 vs -3.10 ✗ |
| smb | 0.0158 vs -0.0423 ✗ | 0.0206 vs 0.00111 ✗ | 0.0553 vs -0.0233 ✗ | 0.0816 vs -0.0708 ✗ |
| t: smb | 0.52 vs -0.71 ✗ | 0.93 vs 0.02 ✗ | 2.71 vs -0.50 ✗ | 4.40 vs -1.66 ✗ |
| hml | -0.00442 vs 0.0574 ✗ | 0.0252 vs 0.0451 ✗ | 0.0116 vs -0.0172 ✗ | 0.0214 vs -0.054 ✗ |
| t: hml | -0.11 vs 1.37 ✗ | 0.83 vs 1.45 ✗ | 0.49 vs -0.59 ✗ | 0.84 vs -1.82 ✗ |
| momentum | -0.0402 vs -0.028 ✗ | -0.0447 vs -0.0482 ✓ | -0.14 vs -0.103 ✗ | -0.196 vs -0.181 ✓ |
| t: momentum | -1.47 vs -0.94 ✗ | -2.28 vs -2.45 ✓ | -7.87 vs -5.83 ✗ | -12.16 vs -8.50 ✗ |
| reversal | 0.0363 vs 0.102 ✗ | 0.0385 vs 0.0724 ✗ | 0.0678 vs 0.0946 ✗ | 0.148 vs 0.201 ✗ |
| t: reversal | 0.94 vs 1.50 ✗ | 1.09 vs 1.27 ~ | 2.86 vs 2.24 ✗ | 5.48 vs 4.34 ✗ |
| r2 | 0.0135 vs 0.05 ✗ | 0.036 vs 0.09 ✗ | 0.244 vs 0.18 ✗ | 0.6 vs 0.54 ~ |

| Table 8, before 1989: ours vs paper | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| intercept | 0.95% vs 0.35% ✗ | 1.12% vs 0.67% ✗ | 0.93% vs 0.71% ✗ | 0.82% vs 0.45% ✗ |
| t: intercept | 5.79 vs 1.72 ✗ | 7.92 vs 4.41 ✗ | 8.57 vs 6.54 ✗ | 10.33 vs 4.19 ✗ |
| market | -0.0547 vs -0.434 ✗ | -0.00313 vs -0.312 ✗ | -0.00291 vs -0.289 ✗ | 0.0544 vs -0.434 ✗ |
| t: market | -1.71 vs -4.29 ✗ | -0.15 vs -3.57 ✗ | -0.14 vs -3.80 ✗ | 3.28 vs -7.26 ✗ |
| smb | -0.0423 vs -0.442 ✗ | -0.00318 vs -0.332 ✗ | 0.0555 vs -0.275 ✗ | 0.103 vs -0.402 ✗ |
| t: smb | -1.10 vs -3.75 ✗ | -0.08 vs -2.86 ✗ | 1.90 vs -2.86 ✗ | 4.07 vs -5.76 ✗ |
| hml | 0.0205 vs 0.0357 ✗ | 0.0419 vs 0.0316 ✗ | -0.00795 vs -0.0684 ✗ | 0.0288 vs -0.0698 ✗ |
| t: hml | 0.37 vs 0.64 ✗ | 0.96 vs 0.73 ✗ | -0.26 vs -1.84 ✗ | 0.86 vs -1.97 ✗ |
| momentum | -0.0691 vs 0.0129 ✗ | -0.068 vs -0.0163 ✗ | -0.175 vs -0.0769 ✗ | -0.18 vs -0.158 ~ |
| t: momentum | -1.59 vs 0.29 ✗ | -1.95 vs -0.50 ✗ | -7.11 vs -2.92 ✗ | -6.74 vs -5.01 ✗ |
| reversal | 0.11 vs 0.436 ✗ | 0.106 vs 0.333 ✗ | 0.112 vs 0.288 ✗ | 0.177 vs 0.452 ✗ |
| t: reversal | 1.55 vs 4.44 ✗ | 1.67 vs 3.62 ✗ | 2.82 vs 4.05 ✗ | 3.59 vs 7.98 ✗ |
| r2 | 0.0512 vs 0.19 ✗ | 0.0772 vs 0.23 ✗ | 0.301 vs 0.26 ~ | 0.587 vs 0.7 ~ |

| Table 8, after 1988: ours vs paper | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| intercept | 0.21% vs 0.34% ✗ | 0.37% vs 0.42% ~ | 0.59% vs 0.36% ✗ | 0.31% vs -0.07% ✗ |
| t: intercept | 1.66 vs 2.12 ~ | 4.62 vs 3.77 ~ | 7.94 vs 3.01 ✗ | 3.28 vs -0.56 ✗ |
| market | 0.108 vs 0.0734 ✗ | 0.0425 vs 0.048 ~ | 0.0571 vs 0.00241 ✗ | 0.0716 vs -0.0696 ✗ |
| t: market | 3.11 vs 1.68 ✗ | 1.97 vs 1.81 ✓ | 2.41 vs 0.06 ✗ | 3.39 vs -2.43 ✗ |
| smb | 0.0611 vs -0.004 ✗ | 0.00462 vs 0.0289 ✗ | 0.0422 vs 0.0233 ✗ | 0.0405 vs -0.0606 ✗ |
| t: smb | 1.73 vs -0.10 ✗ | 0.18 vs 1.32 ✗ | 1.61 vs 0.69 ✗ | 1.58 vs -2.83 ✗ |
| hml | 0.0357 vs 0.0344 ✓ | 0.00204 vs 0.0141 ✗ | 0.0323 vs 0.0183 ✗ | -0.0112 vs -0.082 ✗ |
| t: hml | 0.73 vs 0.61 ~ | 0.06 vs 0.45 ✗ | 1.07 vs 0.50 ✗ | -0.33 vs -2.65 ✗ |
| momentum | 0.0132 vs -0.00424 ✗ | -0.00558 vs -0.0227 ✗ | -0.0956 vs -0.0884 ✓ | -0.198 vs -0.127 ✗ |
| t: momentum | 0.54 vs -0.13 ✗ | -0.33 vs -1.29 ✗ | -3.78 vs -4.17 ✓ | -10.42 vs -7.59 ✗ |
| reversal | -0.0272 vs -0.0626 ✗ | -0.022 vs -0.0173 ✗ | 0.0282 vs 0.024 ~ | 0.118 vs 0.188 ✗ |
| t: reversal | -1.16 vs -1.76 ✗ | -1.10 vs -0.67 ✗ | 1.48 vs 0.54 ✗ | 5.25 vs 5.56 ✓ |
| r2 | 0.103 vs 0.02 ✗ | 0.0356 vs 0.04 ~ | 0.198 vs 0.19 ✓ | 0.665 vs 0.64 ✓ |

With this series the 156 regression cells would score 17.5, against 29.5 with the losers-only series, and the total 399.0 instead of 411.0.

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
| end level, 2002-12 | 76.4 | 39.7 | 72.5 | 14.4 | 11.5 | 11.5 |
| level at 1987-12 | 38.1 | 20.9 | - | 9.3 | 7.5 | - |
| peak (month) | 76.9 (2001-12) | 40.4 (2001-04) | - | 14.4 (2002-12) | 11.6 (2002-11) | - |
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
