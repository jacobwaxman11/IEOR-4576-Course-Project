# Table 1 / Table 2: replication vs. paper

Cohorts: 474 monthly cohorts, overlapping-averaged as in the paper.
Replication values are rounded to 5 decimals (paper reports 5); the
distribution rows use employed capital ('fully invested').

## Table 1 Panel A (no waiting)

| metric | top5 (ours / paper) | top20 (ours / paper) | 101-120 (ours / paper) | all (ours / paper) |
|---|---|---|---|---|
| mean | 0.01340 / 0.01308 | 0.01456 / 0.01436 | 0.01016 / 0.01081 | 0.01053 / 0.01104 |
| nw_se | 0.00149 / 0.00148 | 0.00126 / 0.00124 | 0.00085 / 0.00094 | 0.00101 / 0.00099 |
| t_stat | 8.96564 / 8.84000 | 11.51858 / 11.56000 | 11.96600 / 11.54000 | 10.47119 / 11.16000 |
| median | 0.01224 / 0.01194 | 0.01290 / 0.01235 | 0.00910 / 0.00955 | 0.00740 / 0.00728 |
| std | 0.02343 / 0.02280 | 0.01705 / 0.01688 | 0.01586 / 0.01540 | 0.02064 / 0.01670 |
| skew | 0.19349 / 0.62000 | 0.80725 / 1.39000 | 0.56909 / 1.34000 | 0.85371 / 3.42000 |
| kurtosis | 7.55981 / 7.81000 | 7.09337 / 10.54000 | 4.89647 / 10.30000 | 19.22899 / 25.25000 |
| min | -0.12994 / -0.10573 | -0.07124 / -0.06629 | -0.04455 / -0.03857 | -0.15191 / -0.02721 |
| max | 0.11419 / 0.14716 | 0.09548 / 0.13295 | 0.08024 / 0.12684 | 0.14530 / 0.17178 |
| share_negative | 0.25527 / 0.26000 | 0.15823 / 0.15000 | 0.25738 / 0.21000 | 0.24051 / 0.17000 |
| committed_mean | 0.00796 / 0.00784 | 0.00853 / 0.00805 | 0.00634 / 0.00679 | 0.00560 / 0.00614 |

## Table 1 Panel B (1-day waiting)

| metric | top5 (ours / paper) | top20 (ours / paper) | 101-120 (ours / paper) | all (ours / paper) |
|---|---|---|---|---|
| mean | 0.00785 / 0.00745 | 0.00960 / 0.00895 | 0.00821 / 0.00795 | 0.00797 / 0.00715 |
| nw_se | 0.00113 / 0.00119 | 0.00099 / 0.00096 | 0.00080 / 0.00085 | 0.00098 / 0.00090 |
| t_stat | 6.93350 / 6.26000 | 9.72884 / 9.29000 | 10.27219 / 9.40000 | 8.12679 / 7.92000 |
| median | 0.00789 / 0.00699 | 0.00883 / 0.00690 | 0.00783 / 0.00694 | 0.00541 / 0.00411 |
| std | 0.02047 / 0.02101 | 0.01507 / 0.01527 | 0.01518 / 0.01438 | 0.01969 / 0.01577 |
| skew | -0.28479 / 0.34000 | 0.29330 / 1.45000 | 0.24043 / 0.98000 | 0.69352 / 3.32000 |
| kurtosis | 8.86418 / 10.64000 | 7.49185 / 16.13000 | 4.20851 / 7.78000 | 19.28994 / 25.66000 |
| min | -0.13425 / -0.12628 | -0.08105 / -0.08218 | -0.04370 / -0.04266 | -0.14894 / -0.02951 |
| max | 0.09984 / 0.14350 | 0.07880 / 0.13490 | 0.06702 / 0.10464 | 0.13034 / 0.16325 |
| share_negative | 0.34599 / 0.35000 | 0.25316 / 0.23000 | 0.27637 / 0.28000 | 0.30380 / 0.32000 |
| committed_mean | 0.00471 / 0.00463 | 0.00567 / 0.00520 | 0.00509 / 0.00503 | 0.00416 / 0.00396 |

'Fully invested' = value-weighted return of the open long positions minus that of the open short positions (eq. 2); 'committed capital' scales it by the share of selected pairs holding a position. `mean_employed_literal` (table1.csv only) uses INTERFACES.md's literal denominator for comparison.

## Table 2 Panel A (1-day waiting)

| statistic | top5 (ours / paper) | top20 (ours / paper) | 101-120 (ours / paper) | all (ours / paper) |
|---|---|---|---|---|
| avg_price_deviation_trigger | 0.04083 / 0.04758 | 0.04654 / 0.05284 | 0.07149 / 0.07560 | 0.17259 / 0.16888 |
| avg_pairs_traded_per_period | 4.89126 / 4.81000 | 19.64392 / 19.30000 | 19.59488 / 19.41000 | 1881.00000 / 1944.22000 |
| avg_round_trips_per_pair | 2.27047 / 2.02000 | 2.13100 / 1.96000 | 1.84913 / 1.78000 | 1.66342 / 1.62000 |
| std_round_trips_per_pair | 0.70167 / 0.62000 | 0.47037 / 0.40000 | 0.29081 / 0.27000 | 0.15793 / 0.16000 |
| avg_time_open_months | 3.91563 / 3.75000 | 3.88134 / 3.76000 | 4.08089 / 3.98000 | 4.01268 / 3.97000 |
| std_time_open_months | 0.70758 / 0.80000 | 0.46044 / 0.45000 | 0.37033 / 0.38000 | 0.19927 / 0.17000 |

## Table 2 Panel B (composition; wait-independent)

Size deciles use CRSP breakpoints (NYSE + AMEX common securities, per
the paper's 'using CRSP breakpoints')
on the last trading day of the formation window, 1 = largest. The
`_allpanel` rows (table2_panelB.csv only) use breakpoints from every
panel row on that date. Average decile difference for mixed pairs
uses only pairs whose two stocks occupy different deciles. The
all-pairs average is reported separately in table2_panelB.csv.
The paper's target below one is unresolved under integer deciles;
the named statistic is not redefined to move it closer to the target.

| statistic | top5 (ours / paper) | top20 (ours / paper) | 101-120 (ours / paper) | all (ours / paper) |
|---|---|---|---|---|
| avg_size_decile | 2.66814 / 2.54000 | 2.74088 / 2.71000 | 3.15058 / 3.41000 | 4.63224 / 4.57000 |
| weight_top3_deciles | 0.76287 / 0.78000 | 0.73608 / 0.74000 | 0.63819 / 0.58000 | 0.40624 / 0.40000 |
| weight_top5_deciles | 0.91688 / 0.91000 | 0.92247 / 0.91000 | 0.84077 / 0.79000 | 0.62594 / 0.62000 |
| share_mixed_decile_pairs | 0.66245 / 0.66000 | 0.69072 / 0.69000 | 0.73439 / 0.75000 | 0.81232 / 0.82000 |
| avg_decile_diff_mixed_pairs | 1.66323 / 0.97000 | 1.74137 / 0.97000 | 2.16717 / 0.97000 | 2.63523 / 0.98000 |
| weight_utilities | 0.76751 / 0.72000 | 0.76593 / 0.71000 | 0.29647 / 0.32000 | 0.08180 / 0.08000 |
| weight_transportation | 0.01181 / 0.02000 | 0.01028 / 0.02000 | 0.01783 / 0.02000 | 0.02894 / 0.03000 |
| weight_financials | 0.12194 / 0.11000 | 0.12489 / 0.13000 | 0.24204 / 0.26000 | 0.13778 / 0.16000 |
| weight_industrials | 0.09873 / 0.15000 | 0.09889 / 0.14000 | 0.44367 / 0.40000 | 0.75148 / 0.73000 |
| share_mixed_sector_pairs | 0.11392 / 0.20000 | 0.13639 / 0.22000 | 0.41319 / 0.44000 | 0.28922 / 0.33000 |

## Universe summary

| statistic | ours / paper |
|---|---|
| mean_stocks_per_cohort | 2293.08 / 2317.00 (2,317 (Table 3 caption)) |
| mean_pairs_per_cohort | 2008.83 / 2057.00 (2,057 (Table 9 note)) |
| mean_pairs_opened_wait1 | 1883.99 / 1944.22 (1,944.22 (Table 2 Panel A, all)) |
