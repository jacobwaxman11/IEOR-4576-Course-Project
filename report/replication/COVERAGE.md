# What the paper contains, and what this replication shows for each part

The target is the published article: *The Review of Financial Studies* 19(3), 2006,
doi:10.1093/rfs/hhj020 (`pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf`).
It has nine tables and four figures. This file is the index to all thirteen: what each one
measures, whether the replication shows it, where the evidence lives, and what adding it to the
scored set would cost. The score itself is in `SCORE_LOG.md`; the gaps are in `OPEN_QUESTIONS.md`;
the 1999 draft, which is a second opinion and never the target, is in `EDITION_1999.md`.

Status words used below:

- **scored** - printed in `REPLICATION_CHECK.md` with a mark per cell, counted in the score;
- **diagnostic** - printed in the check without marks, because it re-measures the same series;
- **measured** - replicated and recorded in `REVIEW_NOTES.md` or `OPEN_QUESTIONS.md`, not printed
  by the check;
- **not replicated** - nothing yet.

| item | what it is | status | cells | where |
|---|---|---|---|---|
| Table 1 | excess-return distribution of the four portfolios, no wait (A) and one-day wait (B) | scored | 88 | check, `table1.csv` |
| Table 2 Panel A | trading statistics: trigger, pairs traded, round trips, months open | scored | 24 | check, `table2_panelA.csv` |
| Table 2 Panel B | composition: size deciles, sector weights, mixed pairs | scored | 40 | check, `table2_panelB.csv` |
| Table 3 | the same distribution inside each of the four sectors, plus stocks per cohort | scored | 139 | check, `table3.csv` |
| Table 4 | systematic risk: Sharpe and persistence, then Fama-French + momentum + reversal, then Ibbotson factors | scored (Sharpe, five-factor block, Ibbotson block, equity-premium column as French's Mkt-RF); the intercepts' Newey-West t-statistics printed beside the paper's, unscored; the five-factor block repeated with the reversal factor Table 8 implies, unscored | 60 | check, `table4.csv`, `table4_equity_premium.csv`, `reversal_alternative.csv`, `REVERSAL_FACTOR_AUDIT.md`; REVIEW_NOTES 32, 49, 50, 51 |
| Table 5 Panel A | monthly value at risk: 1/5/10/25 percentiles, serial correlation | scored | 20 | check, `table5_var.csv` |
| Table 5 Panel B | the same on daily returns | measured | 36 | OPEN_QUESTIONS, cross-checks round two |
| Table 6 | the same rule on *random* pairs, a null distribution | not replicated | 48 | - |
| Table 7 | the long and the short book of each portfolio, and their factor loadings | scored (books), not scored (regressions) | 32 + a 104-cell regression block | check, `table7.csv`; REVIEW_NOTES 32 |
| Table 8 | mean and standard deviation before 1989 and after 1988, and a five-factor regression in each half | scored (factor standard deviations and t-statistics not; the intercepts' t-statistics are printed beside the paper's; regressions repeated with the implied reversal factor, unscored) | 72 | check, `table8_subperiod.csv`, `reversal_alternative.csv`; REVIEW_NOTES 50, 51 |
| Table 9 | robustness: top-three-decile universe (A), short recalls on high volume (B) | measured (A), not replicated (B) | 44 + 44 | OPEN_QUESTIONS, cross-checks round two |
| Figure 1 | Kennecott and Uniroyal, trading August 1963 to January 1964 | scored pass/fail | 3 | check, `figure1.json` |
| Figure 2 | monthly excess returns of the top 20, drawn as bars | printed (read back from the image), unscored | 8 rows | check, `figure2_bars.csv` |
| Figure 3 | cumulative excess return of the top 20 (one-day wait) against the S&P 500 | printed (both pairs curves as levels), unscored | 5 rows | check, `figure3_curves.csv`; REVIEW_NOTES 42 |
| Figure 4 | rolling 24-month correlation of the top 20 and 101-120 risk-adjusted returns | scored: the six correlations its text prints, raw and on five-factor residuals | 6 | check, `figure4.csv` |

## Tables beyond 1-3 and 7, one by one

Tables 4, 5 Panel A and 8 and Figure 4 were measurements and diagnostics until SCORE_LOG row 15
(#47), which scored them. Their rows that repeat a scored row (Table 4's mean, standard deviation
and serial correlation, Table 5's loss probability and minimum, which re-measure Table 1 Panel B and
Table 5 Panel A) are left out, so no series is weighted twice.

**Table 4 (systematic risk).** Scored: 60 cells. The Sharpe ratio matches in all four portfolios
(0.34 / 0.59 / 0.52 / 0.41 against 0.35 / 0.59 / 0.55 / 0.45). The five-factor block uses French's
factors, committed under `data/raw/french` (Git LFS), and scores 4.0 of 28: the intercepts are higher
than the paper's in all four portfolios and the "all" market beta is +0.053 where the paper's is
-0.145, because the paper's reversal factor cannot be rebuilt (REVIEW_NOTES 49). The Ibbotson block,
which has no reversal factor, scores 12.0 of 24; the equity-premium column is the remaining four
cells. The serial correlation (a repeat of Table 5 Panel A's row) matches only for the top 20 (0.24
/ 0.24); the 101-120 band is 0.07 against 0.19.

**Table 5 Panel A (monthly VaR).** Scored: 20 cells, 7 within 10% and 5 within 25%. It re-measures
the Table 1 Panel B series, so its rows that repeat Table 1 (the loss probability and the minimum)
are left out.

**Table 5 Panel B (daily VaR).** Measured and close for three of the four portfolios: daily standard
deviation 0.495 / 0.302 / 0.290% against 0.492 / 0.296 / 0.277%, the 1% quantile -1.18 / -0.64 /
-0.65% against -1.24 / -0.65 / -0.65%, the other quantiles within 5%, the minima -10.0 / -5.9 /
-1.9% against -10.1 / -6.7 / -2.0%. The "all" column does not follow: our daily standard deviation
is 0.243% against the paper's 0.169%, and every quantile is about 1.4x. That is the one place where
the paper's own panels are hard to reconcile with each other (its monthly "all" standard deviation
is 1.577%, which is 9.3 monthly units of its daily 0.169%, where the other columns imply 4-7), so
the "all" daily column is as much a question about the paper as about us. Scoring the whole block
would add 36 cells at roughly two thirds of them matching - close to the current rate, but it needs
a daily panel in the cache, which the driver does not store today.

**Table 6 (random pairs).** Not replicated. It is the paper's null: the same opening rule applied to
random stocks drawn from the same prior-month-return decile, which is what makes "the matched pair
earns more than a random pair" a statement rather than an assumption. It needs a resampling step in
the driver and adds 48 cells whose expected score is unknown; ours would be measured against our own
draws, so it is the least comparable table in the paper.

**Table 8 (subperiods).** Scored: 72 cells, ✓ 12 / ~ 15 / ✗ 45. The 16 moment cells (mean and
standard deviation in each half) re-measure the Table 1 Panel B series split in two, 6 within 10%
and 8 within 25%; the 56 regression cells inherit the reversal-factor gap of Table 4. The paper is
internally consistent here (its pre and post figures weight back to its own full-sample "all" mean
and standard deviation, 0.715% and 1.58%). What it shows is that our post-1988 loose portfolios are
about twice as profitable and as volatile as the paper's, which is Q1 and Q9.

**Table 9 Panel A (top three size deciles).** Measured: mean 0.98 / 1.03 / 0.74 / 0.75% against
0.84 / 0.91 / 0.73 / 0.69%, the standard deviations within 15%, the maxima 9.5 / 9.5 / 7.6 / 8.6%
against 10.1 / 10.0 / 10.6 / 10.5%, the minima -14.6 / -9.6 / -4.7 / -6.9% against -10.9 / -5.6 /
-3.8 / -2.7%. About 40% of its 44 cells would match, so scoring it would pull the rate down; it is
worth keeping as evidence because it isolates the dot-com loss from small-cap noise (Q1). It needs
the pairing step restricted to the top three deciles, which the driver does not do today.

**Table 9 Panel B (short recalls).** Not replicated. It forces the pair closed when the short leg has
a high-volume day (volume above its own 18-month average plus one standard deviation), which the
engine has no rule for; the paper reports the cost as 4-13 bp a month. Adding it is an engine change
plus a volume-extended cache.

## The figures

**Figure 1** is scored pass/fail: rank 4 for Kennecott-Uniroyal in the cohort trading from August
1963, trades (8, 35), (46, 56), (76, 83), (85, 99), (108, 125) against the paper's (7, 35), (46, 55),
(74, 82), (86, 99), (108, 126) read off the chart within three days, and formation-end levels within
2% of 1.10.

**Figure 2** is now read back by `scripts/digitize_figures.py` and printed in the check every run.
The scale is fixed by the paper's own Table 1 Panel A top-20 maximum (the tallest bar, 13.295%),
a bar about three columns wide centred on December 1974 that covers November 1974 to January 1975
at the raster's 1.19 columns per month. Against our top-20 no-wait series: correlation 0.51 of the positive bars and
0.61 of the negative ones, 11 of the 44 bars above 3.4% matched within 15% in the same month, the
deepest month in the same place (ours April 1974 at -8.02%, the paper's February 1974 at -8.16%),
and the tallest month in different places (ours October 1987 at 10.23%, the paper's
November-December 1974 at 13.30%) - which is Q2. The figure's caption says the series starts in May
1963; its own axis and Table 1 say July. It is also the no-wait series, although the body text
says "the next-day trading rule": measured on the paper's numbers alone, the digitised bars match
Table 1 Panel A's top-20 row on five of six statistics (mean 1.31% a month against Panel A's 1.44%
and Panel B's 0.90%) and Panel B's only on the minimum. The check prints that test and shows our
one-day-wait series beside the no-wait one (annual-sum correlation 0.75 for both; mean annual sum
16.4% no-wait, 10.4% one-day wait, 15.5% digitised).

**Figure 3 is read as levels.** It is a log scale labelled 0.1 / 1 / 10 / 100 with its decades drawn
as full-width rules, so the digitizer fits the scale to those four rules (108.9 pixels a decade,
exact to under 0.002 of a decade) and follows the Fully Invested and Committed Capital curves with a
continuity tracker; the two tracks end at 39.7 and 11.5, the levels the labelled curves show. The
paper's text says the figure is the top-20 **one-day-wait** strategy, so it is compared with Table 1
Panel B's series. The committed curve agrees three ways: ours ends at 11.6, the figure at 11.5, and
the paper's own Panel B committed mean compounded over the same months at 11.5. The fully invested
curve does not: ours ends at 72.1 and the compounded Panel B mean at 72.5, against 39.7 on the
figure. Both paths correlate 0.998 with ours in logs. The S&P 500 curve is not read (REVIEW_NOTES
42; the earlier "shape only" reading of Sections 37-38 is superseded).

**Figure 4's** six correlations are printed in the paper's text rather than on the chart, so no image
work is needed: the check computes ours from the cached one-day-wait series and prints them beside
the paper's (0.48 full sample, 0.51 before 1989, 0.18 after) - ours are 0.32 / 0.39 / 0.04, with
rolling 24-month averages of 0.38 and 0.06. The residual version of the comparison (0.41 / 0.42 /
0.20 in the paper) needs the Fama-French, momentum and reversal factors and stays in REVIEW_NOTES 32.

## Where the published version contradicts itself

These are worth knowing before anyone "fixes" a cell to match the paper:

1. **Table 9 Panel A prints its skewness and kurtosis rows the wrong way round.** The row labelled
   "Kurtosis" reads 0.02 / 0.98 / 0.80 / 1.77 and the row labelled "Skewness" 7.01 / 8.20 / 6.46 /
   11.67. Swapped, both are plausible (kurtosis 6.5-11.7, skewness 0.0-1.8) and agree with the sign
   of Table 1's skewness; as printed, a kurtosis of 0.02 cannot sit beside a skewness of 7.01.
2. **Table 1 says "absolute kurtosis is reported"**; Table 9's kurtosis row, read as printed, is an
   excess kurtosis. The swap above is the parsimonious explanation.
3. **Figure 3's fully invested curve is not its own Table 1's series.** It ends at 39.7, while the
   Panel B top-20 mean compounds to 72.5 over the same months (ours: 72.1). Its committed curve does
   agree with Table 1 (11.5 against 11.5; ours 11.6), so the scale reading is not the problem.
4. **Table 5 Panel B's "all" column is inconsistent with its own monthly "all"**: daily 0.169%
   against monthly 1.577% is a ratio of 9.3 monthly units, where the other three columns sit at
   4-7 and the paper's own mean ratio (26.5 monthly per daily) sits beside 22.5 for the others.
5. **Figure 2's caption months disagree with its axis and with Table 1** (May against July 1963).

## The other two documents

`Pairs_Trading_RV_Arbitrage_Rule.pdf` is the Yale ICF working paper, "this version February 2006":
same tables, same numbers (checked value by value on 2026-10-21), so it adds no target and is used
only as a layout control - `scripts/verify_paper_targets.py` rejects it by name.

`report/replication/reference/NBER_w7032_1999_draft.pdf` is the 1999 draft. It covers July 1963 to
June 1997 (408 cohorts) and is scored separately in `EDITION_1999.md` (136 cells, 72 + 24 + 40). Its
use is asymmetric: it may veto a change but never justify one. It has settled two conventions where
the published version is silent - the trigger's sigma as the root mean square of the spread about
zero (0.0399 / 0.0449 in the draft against our 0.0409 / 0.0467, where the RFS prints 0.0476 / 0.0528
and matches neither) and the by-sector matching - and it disagrees with the RFS on the top-5 sector
mix, which is why that row (Q5) is recorded as an edition difference rather than a defect.

## If the goal is a higher score

Since SCORE_LOG row 15 the scored set is every table and figure the paper prints a number for
that the cached series can reproduce: Tables 1, 2 and 3 (291 cells), Table 7 (32), Table 4
(60), Table 5 Panel A (20), Table 8 (72) and Figure 4 (6) = 481. Adding the last four raised the
total from 213.5 to 266.5 and lowered the rate from 66.1% to 55.4%, because the five-factor
regression rows inherit the paper's reversal factor, which cannot be rebuilt (REVIEW_NOTES 49).
What remains:

| candidate | cells | expected share matching | needs |
|---|---|---|---|
| Table 5 Panel B (daily VaR) | 36 | about two thirds | a daily panel in the cache |
| Table 9 Panel A (top three deciles) | 44 | about two in five | pairing restricted to the top three deciles |
| Table 6 (random pairs) | 48 | unknown, weakest comparison | a resampling step |
| Table 9 Panel B (short recalls) | 44 | unknown | a recall rule in the engine and volume in the cache |

Figures 2 and 3 stay unscored: their numbers are read off images, and Figure 3's fully invested
curve contradicts the paper's own Table 1.