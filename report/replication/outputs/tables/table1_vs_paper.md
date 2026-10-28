# Table 1 / Table 2: replication vs. paper

Cohorts: 474 monthly cohorts, overlapping-averaged as in the paper.
Replication values are rounded to 5 decimals (paper reports 5); the
distribution rows use employed capital ('fully invested').

## Table 1 Panel A (no waiting)

| metric | top5 (ours / paper) | top20 (ours / paper) | 101-120 (ours / paper) | all (ours / paper) |
|---|---|---|---|---|
| mean | 0.01257 / 0.01308 | 0.01383 / 0.01436 | 0.00957 / 0.01081 | 0.00886 / 0.01104 |
| nw_se | 0.00150 / 0.00148 | 0.00126 / 0.00124 | 0.00082 / 0.00094 | 0.00084 / 0.00099 |
| t_stat | 8.39144 / 8.84000 | 10.97322 / 11.56000 | 11.64637 / 11.54000 | 10.54143 / 11.16000 |
| median | 0.01092 / 0.01194 | 0.01207 / 0.01235 | 0.00868 / 0.00955 | 0.00615 / 0.00728 |
| std | 0.02369 / 0.02280 | 0.01697 / 0.01688 | 0.01528 / 0.01540 | 0.01550 / 0.01670 |
| skew | 0.11855 / 0.62000 | 0.80881 / 1.39000 | 0.80042 / 1.34000 | 1.98598 / 3.42000 |
| kurtosis | 9.37904 / 7.81000 | 8.10042 / 10.54000 | 6.26492 / 10.30000 | 11.13238 / 25.25000 |
| min | -0.14937 / -0.10573 | -0.08018 / -0.06629 | -0.03819 / -0.03857 | -0.03629 / -0.02721 |
| max | 0.12401 / 0.14716 | 0.10226 / 0.13295 | 0.09979 / 0.12684 | 0.10360 / 0.17178 |
| share_negative | 0.27426 / 0.26000 | 0.17089 / 0.15000 | 0.24051 / 0.21000 | 0.25316 / 0.17000 |
| committed_mean | 0.00741 / 0.00784 | 0.00803 / 0.00805 | 0.00593 / 0.00679 | 0.00458 / 0.00614 |

## Table 1 Panel B (1-day waiting)

| metric | top5 (ours / paper) | top20 (ours / paper) | 101-120 (ours / paper) | all (ours / paper) |
|---|---|---|---|---|
| mean | 0.00691 / 0.00745 | 0.00879 / 0.00895 | 0.00749 / 0.00795 | 0.00603 / 0.00715 |
| nw_se | 0.00111 / 0.00119 | 0.00096 / 0.00096 | 0.00077 / 0.00085 | 0.00087 / 0.00090 |
| t_stat | 6.21609 / 6.26000 | 9.14610 / 9.29000 | 9.77050 / 9.40000 | 6.94983 / 7.92000 |
| median | 0.00669 / 0.00699 | 0.00798 / 0.00690 | 0.00680 / 0.00694 | 0.00372 / 0.00411 |
| std | 0.02039 / 0.02101 | 0.01481 / 0.01527 | 0.01440 / 0.01438 | 0.01485 / 0.01577 |
| skew | -0.58049 / 0.34000 | 0.11312 / 1.45000 | 0.21371 / 0.98000 | 1.65964 / 3.32000 |
| kurtosis | 11.55396 / 10.64000 | 8.79971 / 16.13000 | 3.99386 / 7.78000 | 9.92889 / 25.66000 |
| min | -0.15286 / -0.12628 | -0.09067 / -0.08218 | -0.04107 / -0.04266 | -0.04023 / -0.02951 |
| max | 0.09342 / 0.14350 | 0.07399 / 0.13490 | 0.05846 / 0.10464 | 0.10290 / 0.16325 |
| share_negative | 0.36287 / 0.35000 | 0.27426 / 0.23000 | 0.28059 / 0.28000 | 0.33755 / 0.32000 |
| committed_mean | 0.00416 / 0.00463 | 0.00514 / 0.00520 | 0.00461 / 0.00503 | 0.00298 / 0.00396 |

'Fully invested' = value-weighted return of the open long positions minus that of the open short positions (eq. 2); 'committed capital' scales it by the share of selected pairs holding a position. `mean_employed_literal` (table1.csv only) uses INTERFACES.md's literal denominator for comparison.

## Table 2 Panel A (1-day waiting)

| statistic | top5 (ours / paper) | top20 (ours / paper) | 101-120 (ours / paper) | all (ours / paper) |
|---|---|---|---|---|
| avg_price_deviation_trigger | 0.04088 / 0.04758 | 0.04657 / 0.05284 | 0.07150 / 0.07560 | 0.17259 / 0.16888 |
| avg_pairs_traded_per_period | 4.89552 / 4.81000 | 19.65245 / 19.30000 | 19.59062 / 19.41000 | 1881.02132 / 1944.22000 |
| avg_round_trips_per_pair | 2.24179 / 2.02000 | 2.11392 / 1.96000 | 1.84427 / 1.78000 | 1.65953 / 1.62000 |
| std_round_trips_per_pair | 0.68641 / 0.62000 | 0.45772 / 0.40000 | 0.28694 / 0.27000 | 0.15586 / 0.16000 |
| avg_time_open_months | 3.92576 / 3.75000 | 3.88474 / 3.76000 | 4.08022 / 3.98000 | 4.01278 / 3.97000 |
| std_time_open_months | 0.70690 / 0.80000 | 0.46135 / 0.45000 | 0.36842 / 0.38000 | 0.19914 / 0.17000 |

## Table 2 Panel B (composition; wait-independent)

Size deciles use CRSP breakpoints (NYSE + AMEX common securities, per
the paper's 'using CRSP breakpoints')
on the last trading day of the formation window, 1 = largest. The
`_allpanel` rows (table2_panelB.csv only) use breakpoints from every
panel row on that date. The paper's 'average decile difference for
mixed pairs' (0.97) is below 1, the least a mean of integer gaps
between mixed pairs can be, so its row here is the average over all
pairs, same-decile pairs counting 0 (SCORE_LOG.md row 6); the mean
over mixed pairs only is `avg_decile_diff_mixed_only`
(table2_panelB.csv only), 1.67 for the top 5 (REVIEW_NOTES section 34).

| statistic | top5 (ours / paper) | top20 (ours / paper) | 101-120 (ours / paper) | all (ours / paper) |
|---|---|---|---|---|
| avg_size_decile | 2.64873 / 2.54000 | 2.73592 / 2.71000 | 3.14974 / 3.41000 | 4.63218 / 4.57000 |
| weight_top3_deciles | 0.76814 / 0.78000 | 0.73766 / 0.74000 | 0.63850 / 0.58000 | 0.40625 / 0.40000 |
| weight_top5_deciles | 0.92046 / 0.91000 | 0.92278 / 0.91000 | 0.84056 / 0.79000 | 0.62595 / 0.62000 |
| share_mixed_decile_pairs | 0.66371 / 0.66000 | 0.69230 / 0.69000 | 0.73418 / 0.75000 | 0.81234 / 0.82000 |
| avg_decile_diff_mixed_pairs | 1.11603 / 0.97000 | 1.21867 / 0.97000 | 1.61129 / 0.97000 | 2.14583 / 0.98000 |
| weight_utilities | 0.77363 / 0.72000 | 0.76893 / 0.71000 | 0.29931 / 0.32000 | 0.08268 / 0.08000 |
| weight_transportation | 0.01181 / 0.02000 | 0.01055 / 0.02000 | 0.01846 / 0.02000 | 0.02976 / 0.03000 |
| weight_financials | 0.14008 / 0.11000 | 0.13861 / 0.13000 | 0.26361 / 0.26000 | 0.14877 / 0.16000 |
| weight_industrials | 0.07447 / 0.15000 | 0.08191 / 0.14000 | 0.41862 / 0.40000 | 0.73879 / 0.73000 |
| share_mixed_sector_pairs | 0.10464 / 0.20000 | 0.13006 / 0.22000 | 0.40285 / 0.44000 | 0.29702 / 0.33000 |

## Universe summary

| statistic | ours / paper |
|---|---|
| mean_stocks_per_cohort | 2293.08 / 2317.00 (2,317 (Table 3 caption)) |
| mean_pairs_per_cohort | 2008.93 / 2057.00 (2,057 (Table 9 note)) |
| mean_pairs_opened_wait1 | 1884.01 / 1944.22 (1,944.22 (Table 2 Panel A, all)) |
