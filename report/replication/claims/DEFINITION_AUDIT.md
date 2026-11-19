# Definition audit: does every missed cell compute the statistic the paper defines?

Contract R10-B, 2026-11-17. Base `personal/main` ab5c166, check **411.0 of 865**
(`REPLICATION_CHECK.md`: 322 ✓ / 178 ~ / 365 ✗). Worktree `.review/wt/r10-B`, scratch
`.review/r10/B/` (pre-registration in `PREREG.md`, written before anything was scored).
REVIEW_NOTES section 95.

The question is narrow and mechanical: **for every scored row that has at least one cross
outside the reversal and paper-side classes, is our estimator the one the paper's words
name?** 365 cells are cross. GAPS.md section 11 argues class C (the reversal factor, 145
crosses) and class A (the paper's own arithmetic, 55); R10-D owns Table 6's draw
construction. This page audits the rest: classes F, D, G, B, E and H, 165 crosses.

**The answer: every estimator matches the paper's words, and no definitional variant moves
the score up.** The misses in those classes are populations, not definitions. Five
conventions were re-measured on all 865 cells to show it (section 6): the alternate
percentile methods score 409.5 and 410.0, the bias-corrected moments 410.5, and the `<= 0`
boundary, the arithmetic Ibbotson market leg and the Newey-West degrees-of-freedom factor
411.0, every one of them below or level with the shipped reading's 411.0. The five
default-off options they are measured through are on `scripts/03_replicate.py`
(`--moments`, `--quantile-method`, `--sign-zero`, `--nw-correction`, `--ibbotson-market`),
all shipped off.

## 1. How the families were picked

`scripts/experiments/gaps_census.py` assigns every scored cell to one of nine classes
(GAPS.md section 2). It reads cells the way `scripts/score_wrapper.py` does, so the 865 and
the 411.0 are the check's own. A **row family** is one row name across its columns ("Table 1
Panel B kurtosis", "Table 5 Panel A var_5"); the check has **233** of them.

**77 families carry at least one cross outside classes A and C: 295 cells worth 94.0
points**, of which 293 cells are outside A and C - the other two are Figure 4's residual
correlations, which share a row with the raw ones this audit does audit. They hold every
class-F cross (23), every D (75), G (20), B (7), E (7) and H (3) cross outside A and C, and
all 30 class-I crosses (listed in section 4, not measured here: R10-D's).

Reproduce:

    cd .review/wt/r10-B && python - <<'EOF'
    import sys, collections; sys.path.insert(0, 'scripts/experiments')
    import gaps_census as g; from pathlib import Path
    cells = g.read_cells(Path('report/replication/REPLICATION_CHECK.md').read_text())
    fam = collections.defaultdict(collections.Counter)
    for s, l, c, m in cells:
        fam[(s, l)][g.classify(s, l, c) + m] += 1
    print(len(fam), sum(any(k.endswith('✗') and k[0] in 'FDGBEHI' for k in v)
                        for v in fam.values()))
    EOF

Searched before measuring, per COMMON_R10 ("has it been measured?"): `grep -n -i` over
`REVIEW_NOTES.md`, `REVIEW_NOTES_ARCHIVE.md`, `GAPS.md`, `TBD.md` and `claims/*.md` for
"kurtosis", "quantile", "percentile", "ibbotson", "serial correlation", "newey",
"bias-corrected", "population moment", "excess kurtosis". What the campaign had already
measured is cited at each family below and tabulated in section 5; nothing measured on 865
cells was redone, and the two readings measured only on the 291-cell set are re-scored here
where the definition (not the level) is the question.

## 2. The groups

Ten groups cover the 77 families, because a group shares one estimator: the same function
computes every family in it, on the series the paper names for that table. Table 6 is an
eleventh row, listed but not measured (class I, R10-D).

| group | families | cells | points | crosses outside A and C | what it is |
|---|---|---|---|---|---|
| S | 16 | 62 | 11.0 | 46 | skewness and kurtosis |
| X | 14 | 55 | 23.5 | 24 | minimum and maximum |
| N | 2 | 8 | 4.5 | 2 | "Observations with excess return < 0" |
| L | 11 | 41 | 13.5 | 19 | mean, Newey-West se, t, median, sd |
| B | 4 | 16 | 9.0 | 7 | Table 2 Panel B sector weights |
| T | 2 | 8 | 4.5 | 2 | Table 7's book serial correlation |
| I | 8 | 32 | 8.5 | 20 | Table 4's Ibbotson block |
| V | 3 | 12 | 5.5 | 5 | Table 5 Panel A's VaR percentiles |
| H | 2 | 8 | 4.5 | 2 | Table 5's serial correlation |
| E | 5 | 13 | 3.0 | 7 | Table 8's late period, Figure 4, the hold-out |
| 6 | 10 | 40 | 6.5 | 30 | Table 6 (R10-D's) |
| **total** | **77** | **295** | **94.0** | **165** | |

Groups are ordered by the statistic, not by class: a family's class (from the census) is in
its row's cell column.

## 3. The families, one row each

### Group S - Skewness and kurtosis (16 families, 62 cells, 11.0 points)

**(a)** Row labels "Skewness" and "Kurtosis" (Table 1, p. 807; Table 3, p. 812; Table 9,
p. 825). Three captions close **"Absolute kurtosis is reported."** (Table 1, p. 807; Table 7
note, p. 821; Table 9 note, p. 825). Table 3's caption omits the clause; its text reads "the
excess return distributions of the sector pairs portfolios are generally skewed right and
exhibit positive excess kurtosis relative to a normal distribution" (p. 812), which says the
sign of kurtosis - 3, not the statistic. No caption states a moment convention.

**(b)** `summary_stats` (`src/project/evaluation.py:797`): raw (population) Pearson central
moments about the sample mean, skew = mean(u^3)/m2^1.5 and kurtosis = mean(u^4)/m2^2, so a
normal variate reads 3: the absolute reading the captions ask for. The series is the
overlap-averaged monthly series (`overlap_average`, `evaluation.py:501`) for Tables 1, 3 and
9 A, and the recall cache's series for Table 9 B (`table9b_from_cache`,
`scripts/03_replicate.py:1509`).

**(c)-(d)** per family:

| family | cells | (c) what the quote leaves open or fixes | (d) verdict |
|---|---|---|---|
| Table 1 Panel A skewness | 4 (D 0/0/4) | absolute vs excess kurtosis: **fixed** by the caption, and ours is absolute; sample vs population moments: open, R2; the object: fixed by "474 observations" (p. 807) | matches; population (GAPS section 5) |
| Table 1 Panel A kurtosis | 4 (D 1/0/3) | as above | matches; the excess reading was measured at 177.0 on the 291-cell set (archive note 29) |
| Table 1 Panel B skewness | 4 (D 0/0/4) | as above | matches; population |
| Table 1 Panel B kurtosis | 4 (D 0/1/3) | as above | matches; the top-20 cell is the one-month question of the check's Figure 2 block (pp. 744-755) |
| Table 3 Utilities skewness | 4 (D 0/1/3) | as above; the sector itself is a label question (note 83) | matches; population |
| Table 3 Utilities kurtosis | 4 (D 0/2/2) | as above | matches; population |
| Table 3 Transportation skewness | 3 (D 0/1/2) | as above; three columns, "There is no '20 after 100' portfolio for the Transportation industry group" (p. 812) | matches; population |
| Table 3 Transportation kurtosis | 3 (D 0/1/2) | as above | matches; population |
| Table 3 Financials skewness | 4 (D 0/1/3) | as above | matches; population |
| Table 3 Financials kurtosis | 4 (D 1/1/2) | as above | matches; population |
| Table 3 Industrials skewness | 4 (D 0/1/3) | as above | matches; population |
| Table 3 Industrials kurtosis | 4 (D 1/1/2) | as above | matches; population |
| Table 9 Panel A kurtosis | 4 (D 0/0/4) | as above, and the printed rows contradict the caption: "Kurtosis" reads 0.02-1.77, impossible for an absolute kurtosis, beside "Skewness" 7.01-11.67 (COVERAGE.md item 1). The check scores as printed and prints the swapped reading unscored | our estimator matches the caption; the printed rows do not (paper-side) |
| Table 9 Panel A skewness | 4 (D 0/0/4) | as above | as above (paper-side) |
| Table 9 Panel B skewness | 4 (D 1/0/3) | as above, on the recall cache's series (note 74) | matches; the reading's level is the miss |
| Table 9 Panel B kurtosis | 4 (D 2/0/2) | as above | matches; the reading's level is the miss |

### Group X - Extremes: minimum and maximum (14 families, 55 cells, 23.5 points)

**(a)** Rows "Minimum" and "Maximum" (Table 1, p. 807; Table 3, p. 812; Table 9, p. 825) and
Table 5 Panel B's "Minimum historical observation" (p. 815). There is no estimator to state:
they are the extremes of the series named beside them, over "474 observations" (Table 1's
caption, p. 807; Table 9's note, p. 825) monthly, or over the trading days of the sample
daily (Table 5's caption, p. 815: "Monthly and daily VAR percentiles ... (474 months)").

**(b)** `summary_stats`' `min` / `max` of the same series as Group S; `_daily_risk_stats`
(`scripts/03_replicate.py:1664`) for Table 5 Panel B's minimum.

| family | cells | (c) what the quote leaves open or fixes | (d) verdict |
|---|---|---|---|
| Table 1 Panel A minimum | 4 (D 2/1/1) | the object is the monthly overlap-averaged series, fixed by "474 observations"; percent vs fraction is presentation | matches; population |
| Table 1 Panel A maximum | 4 (D 0/1/3) | as above | matches; population |
| Table 1 Panel B minimum | 4 (D 3/0/1) | as above | matches; population |
| Table 1 Panel B maximum | 4 (D 0/0/4) | as above | matches; population |
| Table 3 Utilities maximum | 4 (D 1/2/1) | as above, sector series | matches; population |
| Table 3 Transportation minimum | 3 (D 0/1/2) | as above | matches; population |
| Table 3 Financials minimum | 4 (D 1/1/2) | as above | matches; population |
| Table 3 Financials maximum | 4 (D 1/1/2) | as above | matches; population |
| Table 3 Industrials minimum | 4 (D 2/1/1) | as above | matches; population |
| Table 3 Industrials maximum | 4 (D 2/1/1) | as above | matches; population |
| Table 9 Panel A minimum | 4 (D 0/2/2) | the screened universe "pairs formed only from stocks in the top three size deciles" (p. 824) | matches; population |
| Table 9 Panel A maximum | 4 (D 2/0/2) | as above | matches; population |
| Table 9 Panel B maximum | 4 (D 1/2/1) | the recall universe (note 74) | matches; the reading's level |
| Table 5 Panel B minimum | 4 (D 1/2/1) | the **daily** series, "Minimum historical observation" (p. 815): the strategy's own daily return, one value a day, not a pooled cohort-day sample | matches; the daily "all" volatility is the printed inconsistency COVERAGE.md item 4 records |

### Group N - "Observations with excess return < 0" (2 families, 8 cells, 4.5 points)

**(a)** Row label **"Observations with excess return < 0"** (p. 807; Table 3, p. 812; Table 9,
p. 825); Table 5 Panel B's counterpart is "Probability of return below 0" (p. 815). The
denominator is fixed by the text: "During the full sample period of 474 months, a portfolio
of 20 pairs experienced 71 monthly periods with negative payoffs, compared to 124 months for
a portfolio of 5 pairs" (p. 806). 124/474 = 26.2% and 71/474 = 15.0% are exactly the printed
26% and 15%, so the row is the share of the 474 monthly observations of the table's own
series - not a share of cohort-months and not a count.

**(b)** `share_negative` (`evaluation.py:791`): `(x < 0).mean()` over the same series, a
strictly negative month. Ours: top 5 126 months (0.266), top 20 82 (0.173), 101-120 113
(0.238), all 120 (0.253).

| family | cells | (c) what the quote leaves open or fixes | (d) verdict |
|---|---|---|---|
| Table 1 Panel A share_negative | 4 (F 1/2/1) | "< 0" (fixed by the label) vs "<= 0": R3, no month is exactly zero; the denominator is **fixed** by the printed counts | matches, and the counts confirm the denominator; the "all" cross is population |
| Table 9 Panel B share_negative | 4 (F 2/1/1) | as above, on the recall series | matches; population |

### Group L - Location and dispersion: mean, Newey-West standard error, t, median, sd
(11 families, 41 cells, 13.5 points)

**(a)** Rows "Average excess return (fully invested)", "Standard error (Newey-West)",
"t-Statistic", "Median", "Standard deviation" (p. 807); Table 3's "Mean excess return",
"t-Statistic (Newey-West)", "Median", "Standard deviation" (p. 812); Table 9's "Mean monthly
return (fully invested)", "Standard error (Newey-West)", "t-Statistic", "Median", "Standard
deviation", "Mean excess return on committed capital" (p. 825). Estimators stated: **"The
t-statistics are computed using Newey-West standard errors with six-lag correction."**
(p. 807); "The t-statistic of the mean is computed using Newey-West standard errors with six
lags." (p. 812); "the Newey-West standard errors with six-lag correction" (p. 825).

**(b)** `summary_stats` (`evaluation.py:797`): the mean; the Newey-West (Bartlett, six lags)
HAC standard error of the constant in a constant-only regression, with no small-sample factor
(statsmodels `use_correction=False`; R6 measures the alternative); t = mean/se; the median;
the sample standard deviation (ddof = 1).

| family | cells | (c) what the quote leaves open or fixes | (d) verdict |
|---|---|---|---|
| Table 3 Transportation mean | 3 (F 1/1/1) | six lags (fixed); the Bartlett degrees-of-freedom factor (open, R6); ddof of the sd (open, 0.1% at n = 474); the sector universe is a label/edition question (note 83) | matches; population (note 83) |
| Table 3 Transportation t_stat | 3 (F 0/1/2) | as above | matches; population |
| Table 3 Transportation median | 3 (F 0/2/1) | as above | matches; population |
| Table 3 Financials median | 4 (F 0/2/2) | as above | matches; population |
| Table 3 Industrials t_stat | 4 (F 0/2/2) | as above | matches; population |
| Table 3 Industrials median | 4 (F 0/3/1) | as above | matches; population |
| Table 9 Panel B mean (fully invested) | 4 (F 0/0/4) | as above, on the recall series | matches; the recall reading's level (notes 64, 74) |
| Table 9 Panel B nw_se | 4 (F 1/2/1) | as above | matches |
| Table 9 Panel B t_stat | 4 (F 2/1/1) | as above | matches |
| Table 9 Panel B median | 4 (F 0/1/3) | as above | matches; the reading's level |
| Table 9 Panel B mean (committed) | 4 (F 1/2/1) | committed capital, the paper's own sentence: "the former scales the portfolio payoffs by the number of pairs that are selected for trading, the latter divides the payoffs by the number of pairs that open during the trading period" (p. 805) | matches |

### Group B - Table 2 Panel B's sector rows (4 families, 16 cells, 9.0 points)

**(a)** "**Average sector weights** / Utilities 0.72 ..." and "**Mixed sector pairs** 0.20"
(Table 2 Panel B, p. 809), with the text fixing what a "weight" is: "On average, 71% of the
stocks in the top 20 pairs are utility stocks" and "The percentage of mixed sector pairs
ranges from 20% for the top five pairs to 44% for pairs 101-120" (p. 809). So a sector weight
counts **legs** (each pair contributes two stocks), and a mixed pair is one whose two legs sit
in different sectors.

**(b)** `composition_stats` (`evaluation.py:639`): `weight_{sector}` = the share of the two
legs of every selected pair in that sector; `share_mixed_sector_pairs` = the share of pairs
with different sector labels; unknown SIC counts as Industrials.

| family | cells | (c) what the quote leaves open or fixes | (d) verdict |
|---|---|---|---|
| Table 2 Panel B weight_transportation | 4 (B 0/0/2, F 2/0/0) | legs vs pairs: **fixed** by "71% of the stocks"; the sector map is the edition question (GAPS section 4, note 83) | matches; the raw-legs share is right; the top-5/top-20 crosses are the edition gap |
| Table 2 Panel B weight_financials | 4 (B 1/0/1, F 2/0/0) | as above | matches; edition |
| Table 2 Panel B weight_industrials | 4 (B 0/0/2, F 2/0/0) | as above | matches; edition |
| Table 2 Panel B share_mixed_sector_pairs | 4 (B 0/0/2, F 2/0/0) | as above | matches; edition |

### Group T - Table 7's book serial correlation (2 families, 8 cells, 4.5 points)

**(a)** Row "**Monthly serial correlation**" over the long and the short book (Table 7,
p. 821), with the note's other estimators: "The t-statistics are computed using Newey-West
standard errors with six lags. Absolute kurtosis is reported", and the capital basis of the
bottom half: "The returns in the bottom half of the table are in excess of the 30-day
Treasury bill returns" (p. 821).

**(b)** `monthly_autocorr` (`src/project/table7.py:53`): the lag-1 autocorrelation of the
book's monthly overlap-averaged series, reindexed to a calendar-month grid so a gap never
pairs two non-adjacent months.

| family | cells | (c) what the quote leaves open or fixes | (d) verdict |
|---|---|---|---|
| Table 7 long: monthly serial correlation | 4 (F 3/0/1) | lag 1 (the row says "monthly serial correlation" beside a monthly series); a pooled cohort object or another lag is a different statistic, not a reading of this row; R5's support test uses Table 4's equity-premium row, which the same function computes | matches; the top-5 cross (0.084 against 0.06) is population |
| Table 7 short: monthly serial correlation | 4 (F 0/3/1) | as above | matches; the 101-120 cross (0.080 against 0.12) is population |

### Group I - Table 4's Ibbotson block (8 families, 32 cells, 8.5 points)

**(a)** Table 4's caption (p. 814): "Returns for the portfolios are in excess of the riskless
rate. **S&P 500 returns are calculated in excess of Treasury bill returns.** The Ibbotson
factors are from the Ibbotson EnCorr analyzer: The U.S. Small stock premium is the monthly
**geometric difference** between small-company stock total returns and large-company stock
total returns. U.S. bond default premium is the monthly **geometric difference** between total
return to long-term corporate bonds and long-term government bonds. The U.S. bond horizon
premium is the monthly **geometric difference** between investing in long-term government
bonds and U.S. Treasury bills. The t-statistics are in parentheses next to the coefficients."

**(b)** `load_ibbotson_factors` (`src/project/factors.py:343`): all four legs are geometric
differences, the market leg included. The small-company series is Ibbotson's recipe rebuilt
from CRSP - NYSE common stocks in the bottom two capitalisation deciles, value weighted,
re-formed five-yearly - through 1981, then the CRSP DFA Small Company fund, because WRDS does
not expose the SBBI monthly series (REVIEW_NOTES_ARCHIVE, the Ibbotson sourcing note); the
bond legs are Goyal-Welch's `corpr` and `ltr`, which are Ibbotson's own SBBI columns.
Regressions: `factor_regression` (`factors.py:245`), OLS with a constant, Newey-West t at six
lags.

| family | cells | (c) what the quote leaves open or fixes | (d) verdict |
|---|---|---|---|
| ibbotson_market | 4 (G 0/0/4) | "in excess of" (arithmetic) vs "geometric difference": the caption words this leg differently from the other three premia, so R4 measures the arithmetic leg; S&P 500 total return vs CRSP `vwretd` (the same series); the cells are ratios where the paper's value is near zero (the check's header) | the block's convention matches; R4 moves no mark |
| t: ibbotson_market | 4 (G 0/1/3) | as above | as above |
| ibbotson_small_premium | 4 (G 1/0/3) | "small-company stock total returns": SBBI's series is not on WRDS, so ours is the documented rebuild; "geometric difference" (fixed) | definition matches; the small-stock series is the data gap (archive, Ibbotson sourcing) |
| t: ibbotson_small_premium | 4 (G 0/1/3) | as above | as above |
| t: ibbotson_default_premium | 4 (G 2/1/1) | "geometric difference between total return to long-term corporate bonds and long-term government bonds" (fixed: `corpr` over `ltr`, both Ibbotson's) | matches |
| ibbotson_horizon_premium | 4 (G 1/2/1) | "geometric difference between investing in long-term government bonds and U.S. Treasury bills" (fixed: `ltr` over the 30-day bill) | matches |
| t: ibbotson_horizon_premium | 4 (G 1/0/3) | as above | matches |
| ibbotson_r2 | 4 (G 0/2/2) | OLS R2 of that regression | matches |

### Group V - Table 5 Panel A's VaR percentiles (3 families, 12 cells, 5.5 points)

**(a)** Rows "VAR / 5% / 10% / 25%" (p. 815) under the text "Table 5 reports both monthly and
daily VAR measures to summarize **the quantiles of the empirical distributions** of the
pairs' excess returns" (p. 816). The sample is "474 months" (p. 815). No method is stated; the
1% row is scored too and is carried with no cross at the base, so it is measured as well.

**(b)** `quantile` (`evaluation.py:778`): `Series.quantile(q)` - pandas' linearly interpolated
percentile - of the one-day-wait fully-invested monthly series, in
`write_outputs` (`03_replicate.py`, the Table 5 A block).

| family | cells | (c) what the quote leaves open or fixes | (d) verdict |
|---|---|---|---|
| Table 5 Panel A var_5 | 4 (D 2/1/1) | the interpolation method (open, R1); "percentile" vs "the 5th worst month" (a method choice, R1); percent vs fraction is presentation | matches; R1 shows linear is the closest of the three measured methods |
| Table 5 Panel A var_10 | 4 (D 2/0/2) | as above | as above |
| Table 5 Panel A var_25 | 4 (D 0/2/2) | as above | as above; the top-20 cell has the paper's 25th percentile positive (+0.054%) where ours is -0.048%, a population difference no method reaches |

### Group H - Table 5's serial correlation (2 families, 8 cells, 4.5 points)

**(a)** Row "Serial correlation" (Table 5 Panel A, p. 815; Panel B, p. 815). No estimator is
stated, in either panel.

**(b)** `monthly_autocorr` (`src/project/table7.py:53`) for Panel A and `_daily_autocorr`
(`03_replicate.py:1644`) for Panel B: the lag-1 autocorrelation of the same series the panel's
other rows use, on a calendar grid (months, or consecutive trading days).

| family | cells | (c) what the quote leaves open or fixes | (d) verdict |
|---|---|---|---|
| Table 5 Panel A serial_correlation | 4 (H 2/0/2) | lag 1 (the row names one number beside the series); a different lag or a pooled object is a different statistic; R5's support test: the same function reproduces Table 4's printed equity-premium serial correlation (0.0476 against 0.05), a row nothing was fitted to | matches; the 101-120 (0.078 against 0.19) and "all" (0.177 against 0.12) crosses are population |
| Table 5 Panel B serial_correlation | 4 (H 2/1/1) | daily lag 1 over consecutive trading days, the counterpart of Panel A's; the paper prints 0.00 for 101-120, a rounded zero where ours reads 0.04 | matches; the third cross is that printed zero (the check marks it on the two printed decimals) |

### Group E - Table 8's late period, Figure 4 and the hold-out (5 families, 13 cells, 3.0 points)

**(a)** "Table 8 summarizes the profitability of pairs trading when we **split the sample
period at the end of 1988**" (p. 820); the caption names the two windows: "over the two
subperiods between July 1963 and December 1988 (Panel A) and between January 1989 and December
2002 (Panel B)" (p. 822). Figure 4's text: "The full-sample correlation between the excess
returns of the top 20 and the 100-120 pairs portfolios is 0.48" and "the correlation is 0.51
over the profitable pre-1988 period but much lower (0.18) over the lower excess return
post-1988 period" (p. 822). The hold-out: "over the 1999-2002 period, the excess return of the
fully invested portfolio of the top 20 pairs averaged 10.4% per annum, with an annual standard
deviation of 3.8% and a large and significant Newey-West-adjusted t-statistic of 4.82"
(p. 800).

**(b)** `write_outputs` (`03_replicate.py`): the split is `SUBPERIOD_SPLIT = (1988, 12)` and
each half is summarised by `summary_stats`; the factor SD column is the sample standard
deviation of the factor over the same months (`write_risk_tables`,
`03_replicate.py:1908`); Figure 4 is Pearson `corr` of the two series (raw and
`factor_residuals`); the hold-out is 12 x the monthly mean, sqrt(12) x the monthly standard
deviation and the six-lag Newey-West t of the monthly mean, over 1999-01 to 2002-12.

| family | cells | (c) what the quote leaves open or fixes | (d) verdict |
|---|---|---|---|
| Table 8 post_mean | 4 (E 1/0/3) | the split (fixed: end of 1988, both panels' windows named); the object (the same overlap-averaged series); annualisation does not arise | matches; the late-period population (Q1, Q9; note 57) |
| Table 8 post_std | 4 (E 1/2/1) | as above; ddof of the sd | matches; population |
| Figure 4 correlation, full sample | 2 (raw E 0/0/1, residual C 0/0/1) | "correlation" of the two portfolios' **excess returns** (fixed: the same one-day-wait monthly series); the residual row is the check's own five-factor residuals, class C | matches; population |
| Figure 4 correlation, after 1988 | 2 (raw E 0/0/1, residual C 0/0/1) | as above | matches; population |
| Numbers printed in the text: annual excess return | 1 (E 0/0/1) | "per annum" is not defined: 12 x the monthly mean (shipped, disclosed) or a compounded annual rate; compounding the same 48 months gives 6.62% against the shipped 6.53%, both 37% short of 10.4%, so the mark is the same either way | matches; population (the 1999-2002 loose-pair population, note 57) |

### Group 6 - Table 6 (10 families, 40 cells, 6.5 points)

Not measured here. Table 6's cells are class I and its draw construction is R10-D's contract.
Its caption (p. 819) fixes the draw - "The top panel gives summary statistics of the monthly
excess returns on value-weighted portfolios of n pairs of stocks where the position is opened
immediately ... The statistics are computed over 200 replications of the bootstrapped sample" -
and our own rows come from `table6_from_cache` (`03_replicate.py:1563`); the committed rows
already read the caption's value-weighted book (note 75). The families are listed in section 4
so the audit accounts for all 77.

## 4. The 77 families and their marks, in census order

Every row of the table is one family with at least one cross outside A and C: cells, then the
marks by class (✓ / ~ / ✗ as census counts). Group letters are section 3's.

| # | family | cells | marks by class | group |
|---|---|---|---|---|
| 1 | Table 1 Panel A skew | 4 | D 0/0/4 | S |
| 2 | Table 1 Panel A kurtosis | 4 | D 1/0/3 | S |
| 3 | Table 1 Panel A min | 4 | D 2/1/1 | X |
| 4 | Table 1 Panel A max | 4 | D 0/1/3 | X |
| 5 | Table 1 Panel A share_negative | 4 | F 1/2/1 | N |
| 6 | Table 1 Panel B skew | 4 | D 0/0/4 | S |
| 7 | Table 1 Panel B kurtosis | 4 | D 0/1/3 | S |
| 8 | Table 1 Panel B min | 4 | D 3/0/1 | X |
| 9 | Table 1 Panel B max | 4 | D 0/0/4 | X |
| 10 | Table 2 Panel B weight_transportation | 4 | B 0/0/2, F 2/0/0 | B |
| 11 | Table 2 Panel B weight_financials | 4 | B 1/0/1, F 2/0/0 | B |
| 12 | Table 2 Panel B weight_industrials | 4 | B 0/0/2, F 2/0/0 | B |
| 13 | Table 2 Panel B share_mixed_sector_pairs | 4 | B 0/0/2, F 2/0/0 | B |
| 14 | Table 3 Utilities skew | 4 | D 0/1/3 | S |
| 15 | Table 3 Utilities kurtosis | 4 | D 0/2/2 | S |
| 16 | Table 3 Utilities max | 4 | D 1/2/1 | X |
| 17 | Table 3 Transportation mean | 3 | F 1/1/1 | L |
| 18 | Table 3 Transportation t_stat | 3 | F 0/1/2 | L |
| 19 | Table 3 Transportation median | 3 | F 0/2/1 | L |
| 20 | Table 3 Transportation skew | 3 | D 0/1/2 | S |
| 21 | Table 3 Transportation kurtosis | 3 | D 0/1/2 | S |
| 22 | Table 3 Transportation min | 3 | D 0/1/2 | X |
| 23 | Table 3 Financials median | 4 | F 0/2/2 | L |
| 24 | Table 3 Financials skew | 4 | D 0/1/3 | S |
| 25 | Table 3 Financials kurtosis | 4 | D 1/1/2 | S |
| 26 | Table 3 Financials min | 4 | D 1/1/2 | X |
| 27 | Table 3 Financials max | 4 | D 1/1/2 | X |
| 28 | Table 3 Industrials t_stat | 4 | F 0/2/2 | L |
| 29 | Table 3 Industrials median | 4 | F 0/3/1 | L |
| 30 | Table 3 Industrials skew | 4 | D 0/1/3 | S |
| 31 | Table 3 Industrials kurtosis | 4 | D 1/1/2 | S |
| 32 | Table 3 Industrials min | 4 | D 2/1/1 | X |
| 33 | Table 3 Industrials max | 4 | D 2/1/1 | X |
| 34 | Table 7 long: monthly serial correlation | 4 | F 3/0/1 | T |
| 35 | Table 7 short: monthly serial correlation | 4 | F 0/3/1 | T |
| 36 | Table 4 ibbotson_market | 4 | G 0/0/4 | I |
| 37 | Table 4 t: ibbotson_market | 4 | G 0/1/3 | I |
| 38 | Table 4 ibbotson_small_premium | 4 | G 1/0/3 | I |
| 39 | Table 4 t: ibbotson_small_premium | 4 | G 0/1/3 | I |
| 40 | Table 4 t: ibbotson_default_premium | 4 | G 2/1/1 | I |
| 41 | Table 4 ibbotson_horizon_premium | 4 | G 1/2/1 | I |
| 42 | Table 4 t: ibbotson_horizon_premium | 4 | G 1/0/3 | I |
| 43 | Table 4 ibbotson_r2 | 4 | G 0/2/2 | I |
| 44 | Table 5 Panel A serial_correlation | 4 | H 2/0/2 | H |
| 45 | Table 5 Panel A var_5 | 4 | D 2/1/1 | V |
| 46 | Table 5 Panel A var_10 | 4 | D 2/0/2 | V |
| 47 | Table 5 Panel A var_25 | 4 | D 0/2/2 | V |
| 48 | Table 5 Panel B serial_correlation | 4 | H 2/1/1 | H |
| 49 | Table 5 Panel B min | 4 | D 1/2/1 | X |
| 50 | Table 8 post_mean | 4 | E 1/0/3 | E |
| 51 | Table 8 post_std | 4 | E 1/2/1 | E |
| 52 | Figure 4 correlation, full sample | 2 | E 0/0/1, C 0/0/1 | E |
| 53 | Figure 4 correlation, after 1988 | 2 | E 0/0/1, C 0/0/1 | E |
| 54 | Numbers printed in the text: annual excess return | 1 | E 0/0/1 | E |
| 55 | Table 9 Panel A kurtosis | 4 | D 0/0/4 | S |
| 56 | Table 9 Panel A skew | 4 | D 0/0/4 | S |
| 57 | Table 9 Panel A min | 4 | D 0/2/2 | X |
| 58 | Table 9 Panel A max | 4 | D 2/0/2 | X |
| 59 | Table 9 Panel B mean (fully invested) | 4 | F 0/0/4 | L |
| 60 | Table 9 Panel B nw_se | 4 | F 1/2/1 | L |
| 61 | Table 9 Panel B t_stat | 4 | F 2/1/1 | L |
| 62 | Table 9 Panel B median | 4 | F 0/1/3 | L |
| 63 | Table 9 Panel B skew | 4 | D 1/0/3 | S |
| 64 | Table 9 Panel B kurtosis | 4 | D 2/0/2 | S |
| 65 | Table 9 Panel B max | 4 | D 1/2/1 | X |
| 66 | Table 9 Panel B share_negative | 4 | F 2/1/1 | N |
| 67 | Table 9 Panel B mean (committed) | 4 | F 1/2/1 | L |
| 68 | Table 6 A. No waiting, fully invested: mean | 4 | I 0/0/4 | 6 |
| 69 | Table 6 A. No waiting, fully invested: sd | 4 | I 2/1/1 | 6 |
| 70 | Table 6 A. No waiting, fully invested: median | 4 | I 0/1/3 | 6 |
| 71 | Table 6 A. No waiting, committed: mean | 4 | I 0/0/4 | 6 |
| 72 | Table 6 A. No waiting, committed: median | 4 | I 0/1/3 | 6 |
| 73 | Table 6 B. Wait one day, fully invested: mean | 4 | I 1/0/3 | 6 |
| 74 | Table 6 B. Wait one day, fully invested: sd | 4 | I 0/2/2 | 6 |
| 75 | Table 6 B. Wait one day, fully invested: median | 4 | I 0/1/3 | 6 |
| 76 | Table 6 B. Wait one day, committed: mean | 4 | I 0/0/4 | 6 |
| 77 | Table 6 B. Wait one day, committed: median | 4 | I 1/0/3 | 6 |

## 5. What was already measured, and where

The campaign's notes had answered some of these before this contract; those readings are
cited, not redone.

| question | already measured | on which cells | where |
|---|---|---|---|
| excess instead of absolute kurtosis | 177.0 against 183.5 | 291 (Tables 1-3) | REVIEW_NOTES_ARCHIVE 29 |
| payoff counts / gross book / long book as the "all" tail's cause | 184.5 / 184.5 / 181.5 | 291 | REVIEW_NOTES_ARCHIVE 29 |
| short-session weight of eq. (3), and what it does to Table 5 B and Table 8 | 187.0; daily "all" sd 0.245 -> 0.191 | 291 | REVIEW_NOTES_ARCHIVE 29 (shipped since, SCORE_LOG row 13) |
| percentile interpolation, serial-correlation lag | disclosed as our reading, **not measured** | - | REVIEW_NOTES_ARCHIVE 30; check's convention paragraphs |
| Table 5 Panel B's daily construction | disclosed, with its "all" gap | 36 | REVIEW_NOTES 62 |
| Table 9 B's recall reading | 21.0 against 18.0 for the next-day close | 44 | REVIEW_NOTES 64, 74 |
| Table 6's committed rows on the caption's value-weighted book | 11.0 -> 13.0 | 48 | REVIEW_NOTES 75 (and 65 for the block) |
| Table 2 B / Table 3 sector labels, seven readings | 411.0 / 404.5 / 411.5 / 375.0 / 405.5 / 399.5 / 401.5 | 865 | REVIEW_NOTES 83 |
| the Ibbotson block's data sources | SBBI not on WRDS; bond legs = Goyal-Welch; small leg rebuilt | 44 | REVIEW_NOTES_ARCHIVE, Ibbotson sourcing |
| the late period (Q1/Q9) | Nasdaq-only late universe | 14 + 66 cohorts | REVIEW_NOTES 57, GAPS section 4 |
| Table 8's 1988 split | shipped, disclosed | 130 | REVIEW_NOTES 50, 54 |

Not found anywhere, and measured here for the first time: the bias-corrected moments (R2), the
`<= 0` boundary (R3), the arithmetic Ibbotson market leg (R4), the Newey-West
degrees-of-freedom factor (R6), and the percentile method on the full 865 (R1).

## 6. The measured readings

Seven aggregate-only runs from this worktree over the shipped caches, each scored by the check
itself (`scripts/experiments/definition_audit.py run`, which writes one out-root and one log per
variant under `.private/<name>`). The command, once per variant, is COMMON_R10's baseline command
with `--out-root .private/<name>` and the variant's option.

**The default run is unchanged.** `.private/base2` - this branch, no option - prints the base
line (411.0 of 865, 322 / 178 / 365), and its seven table CSVs are byte-identical to
`.private/base`'s, built from ab5c166 in the same worktree before the change. The only
differing line of the check is the figure path, which carries the out-root.

| reading | option | score | cells that change mark |
|---|---|---|---|
| base | none | 411.0 (322 / 178 / 365) | - |
| R1a | `--quantile-method lower` | **409.5** (320 / 179 / 366) | 3 |
| R1b | `--quantile-method midpoint` | **410.0** (321 / 178 / 366) | 2 |
| R2 | `--moments sample` | **410.5** (321 / 179 / 365) | 1 |
| R3 | `--sign-zero nonpositive` | 411.0 | 0 |
| R4 | `--ibbotson-market excess` | 411.0 | 0 |
| R6 | `--nw-correction df` | 411.0 | 0 |

### R1. Percentile interpolation (class D, Table 5 Panels A and B)

The paper's 1% monthly quantiles are -4.320, -1.943, -2.236 and -1.994 (top 5, top 20,
101-120, all; p. 815). Ours under the shipped linear interpolation: -3.588, -2.238, -2.749,
-2.170. The top-5 miss is not an interpolation question: the printed -4.320 lies between our
second and third worst months of 474 (-5.971 and -4.389), at a rank of about 2.3/474 = 0.5%,
while our 5% quantile matches the printed -2.142 to three decimals (-2.141). The printed 1%
is a deeper left tail, not a different percentile convention.

`lower` (nearest rank) and `midpoint` (the average of the two bracketing order statistics)
both cost points, all on the 1% row, which carries no cross at the base:

| cell | base (linear) | paper | `lower` | `midpoint` | mark |
|---|---|---|---|---|---|
| var_1, 101-120 | -2.749% ~ | -2.236% | -3.067% **✗** | -2.850% **✗** | ~ -> ✗ |
| var_1, all | -2.170% ✓ | -1.994% | -2.386% **~** | -2.238% **~** | ✓ -> ~ |
| var_5, top 20 | -1.098% ✓ | -1.002% | -1.114% **~** | -1.102% ✓ | ✓ -> ~ (lower) |

Verdict: **closed**. Linear is the shipped reading, the paper states no method, and both
alternatives are worse on the printed numbers. The 25% row cannot move: there the methods
differ from linear by under 1%.
### R2. Bias-corrected moments (class D, Tables 1, 3, 9 A, 9 B)

At n = 474 the spreadsheet corrections move skewness by 0.2% and kurtosis by 0.6%, inside the
printing precision of the paper's values. One cell sits close enough to its band edge to move:
Table 9 B's top-5 kurtosis, ours 5.90 against the printed 5.39 (9.5% low, ✓), becomes 5.936
(10.1% low, ~). No other shape cell changes mark; the check falls from 411.0 to 410.5.

Verdict: **closed**. Both estimators agree with the printed values to better than the third
digit the paper prints, the caption fixes the absolute reading and both of ours are absolute,
and the corrected variant is the one that loses. Not a ship candidate and no new disclosure
needed: the raw-moment choice is in `summary_stats`' docstring and the check's conventions
paragraph.


### R3. "< 0" versus "<= 0" (class F)

No cell moves, and not one of the 474 monthly observations of any portfolio is exactly zero
(one-day wait: top 5 170 negative months and 0 zeros, top 20 129 and 0, 101-120 134 and 0, all
160 and 0). The label's strict inequality is what we compute.


### R4. The Ibbotson market leg (class G)

The caption words this leg as "calculated in excess of Treasury bill returns" and the other
three as geometric differences; we compute all four geometrically. The arithmetic leg changes
the factor by -0.128 bp a month on average (largest single month 13.3 bp), moves its standard
deviation from 4.3631% to 4.3859% a month and correlates 0.9999977 with the geometric one. The
regression cells move by at most 6.3e-4 on the market loading and 0.0096 on that loading's
t-statistic, a largest relative move of 0.96% on a loading near zero. **No cell changes mark.**

Verdict: **closed as immaterial**, but it is the one place where the paper's words point to a
different construction from ours, so it is disclosed here and available as
`--ibbotson-market excess`. It is not flipped: the shipped default is the geometric reading
all four legs share, the difference is 13 bp in one month of 474, and no printed value
identifies either leg.
### R5. The serial-correlation support test (class H)

No variant: the support is printed. Table 4's "Monthly serial correlation" row reads 0.05 for
the equity premium and ours is 0.0476, from the same function that produces the pairs rows
(0.128 against the printed 0.14 and 0.244 against 0.24 in Table 5 A; -0.110 against -0.12,
-0.060 against -0.06 and 0.330 against 0.35 in Table 5 B). The premium row is a series nothing
in this replication was fitted to, and its serial correlation, its Sharpe ratio (0.0905
against the printed 0.09), its standard deviation (4.515% against 4.509%) and its mean
(0.409% against 0.410%) all match under the shipped definitions.

Verdict: **matches, closed**. The residuals of Table 4's factor model do not arise here, so
the only cross that this reading has to explain is the level of the series itself, which is
the late-period population question (class E).


### R6. The Newey-West degrees-of-freedom factor (class F)

With statsmodels' n/(n-k) factor (k = 1 in these constant-only regressions, n = 474) every
`nw_se` rises by exactly 0.1057% and every `t_stat` falls by 0.1055%; the other rows are
untouched. **No cell changes mark.** The paper states the lag order ("six-lag correction",
p. 807) and not the factor, and its printed t-statistics move in both directions against ours
(top 5 8.84 against our 8.58, 101-120 11.54 against our 11.80), so no printed value identifies
either reading.

Verdict: **closed as immaterial**.

## 7. Verdicts

| reading | verdict | why |
|---|---|---|
| R1 percentile interpolation | closed | the paper states no method; linear is the best of the three measured and the 1% gap is a left tail, not a convention |
| R2 bias-corrected moments | closed | 0.2% / 0.6% shifts, one knife-edge cell moves the wrong way, the caption fixes absolute |
| R3 "< 0" boundary | closed (matches) | zero months are exactly zero; the label says "< 0" |
| R4 arithmetic Ibbotson market | sensitivity, disclosed, default off | the caption's wording favours it, 13 bp in one month, no mark moves |
| R5 serial-correlation estimator | closed (matches) | the printed equity-premium row confirms it, nothing was fitted to that row |
| R6 Newey-West df factor | closed | 0.11% on the standard error, no mark moves |
| Table 2 Panel B sector weights, Table 3 F rows, Table 7 books, Table 9 B moments, Table 8 late period, Figure 4, the hold-out | closed (definition matches) | the misses are populations: notes 57, 64, 74, 83 and GAPS sections 4 and 5 |
| Table 6 | not audited here | class I, R10-D's draw construction |

**Nothing ships as a scored change.** The four estimator switches and the Ibbotson switch are
committed default-off, with the defaults byte-identical to the base, so the 411.0 of 865, the
865 ceiling, the mark rule and every typed paper value are untouched.

## 8. What this page settles

1. **No scored family computes a different statistic from the one its caption names.** The
   four conventions the contract listed as suspect - absolute vs excess kurtosis, sample vs
   population moments, the percentile method, "< 0" vs "<= 0" - are settled: the first is
   fixed by the captions and we follow it (and the excess reading was already measured at
   177.0, archive note 29); the second is immaterial; the third is unstated and linear is the
   best of the three measured; the fourth is the printed label.
2. **The one place the paper's words point away from our construction is immaterial**: the
   Ibbotson market leg, 13 bp in one month, no mark.
3. **The 165 crosses outside A and C are populations, not definitions.** That is the negative
   the contract asked for: a definition audit cannot lift those classes, so the only levers
   left there are the ones GAPS.md section 7 already names (Q1, Q5, Q9 and the shape question
   of section 5).

Reproduce every number on this page with `scripts/experiments/definition_audit.py`: `run` executes
the seven configurations (about two and a half minutes each, aggregate-only over the shipped
caches) and `diff <base check> <variant check>` prints the cells whose mark changed.