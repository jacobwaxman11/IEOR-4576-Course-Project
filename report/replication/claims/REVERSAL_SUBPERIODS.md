# Pre-registration: a reversal factor for both Table 8 subperiods (contract Pb)

Written 2026-11-17, before any candidate series in the grid below was built or measured. The only
run that preceded it is the standard replication check on `f33a1cc` (406.0 of 865), which this file
does not touch. Nothing here may be amended after a distance is seen; any reading added later is
reported as a new candidate with its distance, not as a replacement.

## What the paper says

p. 813: "We control for this possibility by constructing a short-term reversal factor measured as
the excess return of stocks in the top three deciles of prior-month return minus the return on
stocks in the bottom three deciles." Footnote 7 (p. 813): "The construction is similar to Carhart's
(1997) momentum factor, but the performance-sorting horizon here is one month."

## Targets

Table 8's printed factor standard deviations and the correlations with the four French factors that
its four portfolios' loadings, R2 and SDs imply at that SD (`scripts/audit_reversal_factor.py`,
`implied_covariances` / `paper_system`, REVIEW_NOTES section 61):

| window | SD | market | SMB | HML | momentum |
|---|---|---|---|---|---|
| pre (1963-07 .. 1988-12) | 0.0723 | +0.81 | +0.79 | -0.18 | -0.16 |
| post (1989-01 .. 2002-12) | 0.0445 | +0.79 | +0.55 | -0.53 | -0.30 |

The four correlations depend on the factor vintage's own covariance matrix over the same window, so
they are recomputed for the 2005 vintage (`data/raw/french_vintage_2005/`, REVIEW_NOTES section 72) exactly as for today's files, and
each vintage's targets are used only with that vintage's factors. Contract Pa owns the 2005
recomputation (REVIEW_NOTES section 72); if that file appears, its targets are reported beside mine
and any difference is stated.

## Grid

Every candidate is one construction applied to the whole 1963-07 .. 2002-12 sample and then read in
the two windows separately.

- **leg** (4): `losers_only` = bottom group minus the T-bill; `losers_minus_winners` = bottom group
  minus top group; `winners_minus_losers` = top group minus bottom group; `winners_only` = top group
  minus the T-bill.
- **deciles** (3): `d3` = the paper's three (1-3 and 8-10), the only set that is a reading of the
  sentence; `d1` = 1 and 10; `d2` = 1-2 and 9-10. `d1` and `d2` are labelled sensitivities: they are
  not three deciles and could not be shipped under the text, they are measured so that the table
  shows what the decile width does to the two windows.
- **weighting** (2): equal (`ew`) and value (`vw`).
- **sort source and breakpoints** (3):
  - `french`: French's `10_Portfolios_Prior_1_0_CSV.zip`, value- and equal-weighted monthly blocks,
    NYSE breakpoints (his own file).
  - `crsp_all`: own build from `data/raw/wrds_api/monthly_stocks.parquet`, universe common shares
    (`securitytype EQTY`, `securitysubtype COM`, `sharetype NS`, `usincflg Y`, `issuertype` in
    ACOR/CORP) on NYSE, Amex and Nasdaq with a non-missing price two months back; breakpoints are
    that universe's own deciles of the sort signal.
  - `crsp_nyseamex`: the same build with the universe restricted to `primaryexch` N and A
    ("the same with NYSE/AMEX stocks only"); breakpoints are the restricted universe's own deciles.
- **signal**: the prior month's return (month t-1, no skip), from the same source as the returns.
- **portfolio return**: the equal-weighted mean of the group's month-t returns, or the mean weighted
  by month t-1 capitalization (beginning-of-month market cap), with the group's holdings formed
  from the sort signal at the end of t-1.

That is 4 legs x 3 decile sets x 2 weightings x 3 sort sources = **72 candidates**, named
`<sort>_<weighting>_<deciles>_<leg>`, e.g. `crsp_all_vw_d3_losers_minus_winners`. The scored series
today, equal-weighted French deciles 1-3 less the bill, is `french_ew_d3_losers_only`; its distance is
the benchmark every other candidate must beat.

## Metric and selection

For a window w and candidate c:

    d_w(c) = |ln(SD_w(c) / SD_w(paper))| + sum over f in {market, SMB, HML, momentum} |corr_w(c, f) - corr_w(paper, f)|
    d(c)   = d_pre(c) + d_post(c)

SD is the sample standard deviation (ddof = 1) of the candidate's monthly series over the window;
correlations are Pearson over the window against the same vintage's four factors. Selection is by
`d(c)` alone, ascending. Ties (equal to 3 decimals) are reported as ties and broken by name, not by
score. A candidate is *eligible for shipping* only if all of: (a) it is a reading of the p. 813
sentence and footnote 7 (three deciles each side, prior month, one construction for the whole
sample) - i.e. its decile set is `d3` and its leg is one the sentence can be read as; (b) `d_pre` and
`d_post` are both strictly smaller than the losers-only series' - a sum that wins in one window and
loses in the other does not qualify; (c) adding it to the standard check loses no point.

## What gets measured next

1. `scripts/experiments/reversal_subperiods.py` builds all 72 candidates, prints SD, the four
   correlations and `d_w` in each window, and `d(c)`, sorted, in both factor vintages.
2. The three nearest candidates by `d(c)` and the losers-only series are written as monthly CSVs
   under `<scratch>/series/` and pushed through the whole standard check as a scored
   `--reversal-factor` choice; the whole check's score and the regression blocks' marks are recorded.
3. Every number reported comes from a finished run whose directory is named beside it. Candidates
   that lose points, and the losers, are reported with their numbers.

## Results (measured 2026-11-17; coordinator's summary of the finished grid)

The grid ran on all 72 candidates in both factor vintages (`scripts/experiments/reversal_subperiods.py`).
Targets, from Table 8's own arithmetic (`scripts/audit_reversal_factor.py`):

    targets, today factors:
      pre  SD 0.0723  market +0.81 smb +0.79 hml -0.18 momentum -0.16  valid matrix: True
      post SD 0.0445  market +0.79 smb +0.55 hml -0.53 momentum -0.30  valid matrix: True
    targets, 2005 factors:
      pre  SD 0.0723  market +0.81 smb +0.79 hml -0.18 momentum -0.15  valid matrix: True
      post SD 0.0445  market +0.74 smb +0.52 hml -0.41 momentum -0.30  valid matrix: True

Nearest candidates by the pre-registered distance, today's factors:

| candidate | pre SD | pre mkt | pre SMB | pre HML | pre momo | pre d | post SD | post mkt | post SMB | post HML | post momo | post d | total |
| french_ew_d3_losers_only | 0.0685 | +0.84 | +0.77 | -0.20 | -0.12 | 0.160 | 0.0686 | +0.72 | +0.52 | -0.44 | -0.35 | 0.691 | 0.851 |
| french_ew_d2_losers_only | 0.0728 | +0.83 | +0.77 | -0.19 | -0.13 | 0.079 | 0.0780 | +0.69 | +0.51 | -0.45 | -0.37 | 0.849 | 0.928 |
| crsp_nyseamex_ew_d1_winners_only | 0.0653 | +0.84 | +0.72 | -0.19 | +0.04 | 0.410 | 0.0534 | +0.72 | +0.54 | -0.32 | -0.16 | 0.602 | 1.012 |
| french_ew_d3_winners_only | 0.0575 | +0.88 | +0.73 | -0.25 | +0.01 | 0.592 | 0.0519 | +0.78 | +0.59 | -0.45 | -0.14 | 0.445 | 1.037 |
| crsp_nyseamex_ew_d2_winners_only | 0.0616 | +0.87 | +0.72 | -0.21 | +0.03 | 0.501 | 0.0468 | +0.78 | +0.46 | -0.26 | -0.19 | 0.540 | 1.041 |
| crsp_nyseamex_ew_d3_winners_only | 0.0599 | +0.88 | +0.72 | -0.21 | +0.01 | 0.525 | 0.0439 | +0.80 | +0.42 | -0.23 | -0.21 | 0.534 | 1.059 |
| crsp_all_ew_d3_losers_only | 0.0731 | +0.83 | +0.77 | -0.18 | -0.14 | 0.067 | 0.0871 | +0.65 | +0.50 | -0.45 | -0.38 | 1.019 | 1.085 |

Nearest candidates, French's 2005 factors:

| candidate | pre SD | pre mkt | pre SMB | pre HML | pre momo | pre d | post SD | post mkt | post SMB | post HML | post momo | post d | total |
| french_ew_d3_losers_only | 0.0685 | +0.85 | +0.76 | -0.20 | -0.12 | 0.165 | 0.0686 | +0.72 | +0.53 | -0.47 | -0.35 | 0.553 | 0.718 |
| crsp_nyseamex_ew_d1_winners_only | 0.0653 | +0.84 | +0.72 | -0.20 | +0.05 | 0.414 | 0.0534 | +0.73 | +0.55 | -0.37 | -0.16 | 0.399 | 0.814 |
| french_ew_d2_losers_only | 0.0728 | +0.83 | +0.77 | -0.20 | -0.13 | 0.084 | 0.0780 | +0.70 | +0.52 | -0.48 | -0.37 | 0.741 | 0.825 |
| crsp_nyseamex_ew_d2_winners_only | 0.0616 | +0.87 | +0.72 | -0.22 | +0.03 | 0.505 | 0.0468 | +0.78 | +0.47 | -0.30 | -0.19 | 0.377 | 0.882 |
| crsp_nyseamex_ew_d3_winners_only | 0.0599 | +0.88 | +0.71 | -0.22 | +0.01 | 0.530 | 0.0439 | +0.80 | +0.43 | -0.28 | -0.21 | 0.403 | 0.933 |
| crsp_nyseamex_ew_d3_losers_only | 0.0749 | +0.84 | +0.74 | -0.17 | -0.17 | 0.140 | 0.0637 | +0.70 | +0.40 | -0.25 | -0.43 | 0.808 | 0.948 |
| crsp_all_ew_d3_losers_only | 0.0731 | +0.83 | +0.76 | -0.19 | -0.14 | 0.071 | 0.0871 | +0.66 | +0.51 | -0.48 | -0.37 | 0.905 | 0.976 |

**The shipped series is the nearest construction in both vintages.** `french_ew_d3_losers_only`
(equal-weighted prior-month deciles 1-3 minus the bill) has the smallest total distance (0.851 with
today's factors, 0.718 with the 2005 ones). No candidate is closer in *both* windows, so ship rule (b)
admits none. Every construction misses the post-1988 SD (0.0445): the losers-only series stays near
0.069 after 1988, and the candidates that come closer after 1988 (the winners-only NYSE/AMEX builds,
0.044-0.053) move away before 1989.

Scored through the standard check (`--reversal-factor csv`): the losers-only series reproduces the
406.0 of 865 this page was written against, and `french_ew_d3_winners_only`, the nearest three-decile
candidate with another leg, scores 399.0. The post-1988 regression cells therefore stay out of reach of any construction the
p. 813 sentence describes (REVIEW_NOTES section 73).

