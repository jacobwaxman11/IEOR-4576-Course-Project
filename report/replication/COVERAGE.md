# What the paper contains, and what this replication shows for each part

The target is the published article: *The Review of Financial Studies* 19(3), 2006,
doi:10.1093/rfs/hhj020 (`pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf`).
It has nine tables and four figures. This file is the index to all thirteen: what each one
measures, whether the replication shows it, where the evidence lives, and what adding it to the
scored set would cost. The score itself is in `SCORE_LOG.md`; the gaps are in `GAPS.md`;
the 1999 draft, which is a second opinion and never the target, is in `EDITION_1999.md`.
`GAPS.md` groups the scored cells by the stage of the method that produces them and by
the cause of each miss.

Status words used below:

- **scored** - printed in `REPLICATION_CHECK.md` with a mark per cell, counted in the score;
- **excluded** - printed by the paper but not scored, for one of three stated reasons: a
  **duplicate** of a scored number (scored once, where it first appears), a number **derived**
  from other printed numbers (tested in `CLAIMS.md`, not scored twice), or an **image** reading
  (Figures 2 and 3 print no numbers; their readings are shown unscored).

"Printed" counts the numbers the paper prints; where a table prints a caption count as well the
two are both listed. The totals and the arithmetic are in "How the numbers reconcile" below.

<!-- The "scored" column is generated from REPLICATION_CHECK.md by scripts/docs_sync.py. -->
| item | printed | scored | excluded, with reason | where |
|---|---|---|---|---|
| Table 1 (p. 807) | 88 | 88 | - | check, `table1.csv` |
| Table 2 Panel A (p. 809) | 24 | 24 | - | check, `table2_panelA.csv` |
| Table 2 Panel B (p. 809) | 40 | 40 | - | check, `table2_panelB.csv` |
| Table 3 (p. 812) | 135 + 4 caption counts (stocks per sector) | 139 | - | check, `table3.csv` |
| Table 4 (p. 814) | 116 | 104 (incl. 44 t-statistics, row 25) | 12 duplicate: mean and sd of the four portfolios (= Table 1 B), serial correlation (= Table 5 A) | check, `table4.csv`, `table4_equity_premium.csv` |
| Table 5 Panel A (p. 815) | 36 | 20 | 16 duplicate: mean, sd, probability of a loss, minimum (= Table 1 B) | check, `table5_var.csv` |
| Table 5 Panel B (p. 815) | 36 | 36 (row 24; the "all" column reported, not adjusted) | - | check, `table5b_daily.csv`; REVIEW_NOTES 62 |
| Table 6 (p. 819) | 48 | 48 (row 23, against our own draws) | - | check, `--table6-cache` (`make table6`); `TABLE6.md`, `TABLE6_READINGS.md`; REVIEW_NOTES 65, 69 |
| Table 7 (p. 821) | 136 | 136 (incl. 48 t-statistics, row 25) | - | check, `table7.csv`, `table7_reversal_alternative.csv`; REVIEW_NOTES 63, 67 |
| Table 8 (p. 822) | 130 | 130 (incl. 48 t-statistics, row 25, and 10 factor SDs, row 26) | - | check, `table8_subperiod.csv`, `table8_factor_sd.csv` |
| Table 9 (p. 825) | 88 | 88 | - | check, both panels; REVIEW_NOTES 60, 64 |
| Figure 1 (p. 804) | rank, five trades, day-0 levels | 3 pass/fail checks | not counted in the score | check, `figure1.json` |
| Figure 2 (p. 817) | bars only | - | image: the digitised bars are shown unscored | check, `figure2_bars.csv` |
| Figure 3 (p. 817) | curves only | - | image: the digitised levels are shown unscored | check, `figure3_curves.csv` |
| Figure 4 (p. 823; correlations in the text, pp. 822-823) | 6 correlations | 6 | - | check, `figure4.csv` |
| text and captions | 6 result numbers | 6 (row 26) | - | check, "Numbers printed in the text" |
| **total** | **881 table values + 12** | **865** | **28 duplicates**, plus the derived text numbers, parameters, outside estimates and the image readings (see "How the numbers reconcile" below) | SCORE_LOG rows 1-26 |


## Tables beyond 1-3 and 7, one by one

Tables 4, 5 Panel A and 8 and Figure 4 were measurements and diagnostics until SCORE_LOG row 15
(#47), which scored them. Their rows that repeat a scored row (Table 4's mean, standard deviation
and serial correlation, Table 5's loss probability and minimum, which re-measure Table 1 Panel B and
Table 5 Panel A) are left out, so no series is weighted twice.

**Table 4 (systematic risk).** Scored: 104 cells since SCORE_LOG row 25 (60 at row 15, then the 44
t-statistics), ✓ 28 / ~ 22 / ✗ 54 at row 29. The Sharpe ratio is within 10% in all four portfolios
(0.358 / 0.605 / 0.525 / 0.407 against 0.35 / 0.59 / 0.55 / 0.45). The five-factor block uses
French's 2005 factor files (`data/raw/french_vintage_2005/`, SCORE_LOG row 27) with the losers-only
reversal series and scores 7.5 of its 28 coefficients and 12.0 of 52 with the t-statistics: the
intercepts are higher than the paper's in all four portfolios, because the paper's reversal factor
cannot be rebuilt (REVIEW_NOTES 49, 61), although the "all" market beta now matches (-0.133 against
-0.145). The Ibbotson block, which has no reversal factor, scores 10.5 of its 24 coefficients and
19.0 of 44 with the t-statistics; the equity-premium column is the remaining four cells, all ✓.
The serial correlation (a repeat of Table 5 Panel A's row) matches for the top 5 and the top 20
(0.13 / 0.14, 0.24 / 0.24); the 101-120 band is 0.08 against 0.19 and "all" 0.18 against 0.12.

**Table 5 Panel A (monthly VaR).** Scored: 20 cells, 7 within 10% and 6 within 25%. It re-measures
the Table 1 Panel B series, so its rows that repeat Table 1 (the loss probability and the minimum)
are left out.

**Table 5 Panel B (daily VaR).** Scored: 36 cells, 26 within 10%, 8 within 25% and 2 outside 25%
(the 101-120 daily serial correlation, which the paper prints as a rounded "0.00", and the "all"
minimum). The series is the same one-day-wait fully-invested return one level down: each trading
day's equal-weighted mean over the cohorts trading that day, Table 1 Panel B's overlap average at
daily frequency, which the cohort cache stores since format 7. The three named columns agree on
every row: daily standard deviation 0.496 / 0.302 / 0.288% against 0.492 / 0.296 / 0.277%, the 1%
quantile -1.21 / -0.67 / -0.67% against -1.24 / -0.65 / -0.65%, the worst day -10.0 / -6.0 /
-1.8% against -10.1 / -6.7 / -2.0%. The "all" column does not follow: our daily standard deviation
is 0.191% against the paper's 0.169% (1.13 times) and each quantile 1.1-1.2 times, while the
minimum is 1.38 times the paper's. That is the one place where the paper's own panels are hard to
reconcile with each other (item 4 below: its monthly "all" standard deviation is 9.3 of its own
daily units, where the other columns imply 4-7), so the column is reported, not adjusted
(REVIEW_NOTES 62).

**Table 6 (random pairs).** Scored by PR #71 (SCORE_LOG row 23). It is the paper's null: the same
opening rule applied to random stocks drawn from the same prior-month-return decile, which is what
makes "the matched pair earns more than a random pair" a statement rather than an assumption. The
48 cells come from the `vol_common_t6_book` cache and are measured against our own draws, so it is
the least comparable table in the paper. Since SCORE_LOG row 28 the committed rows read the
caption's "value-weighted portfolios of n pairs" (p. 819): 8 / 10 / 30 = 13.0 of 48 (REVIEW_NOTES
75).

**Table 8 (subperiods).** Scored: 130 cells, ✓ 27 / ~ 19 / ✗ 84 at SCORE_LOG row 29: the 72
moment and regression cells, their 48 t-statistics (row 25) and the 10 factor standard deviations
(row 26). The 16 moment cells (mean and standard deviation in each half) re-measure the Table 1
Panel B series split in two, 8 within 10% and 4 within 25%; the 56 regression cells inherit the
reversal-factor gap of Table 4; the factor SDs are the inputs themselves, and the first four,
computed from French's 2005 files, are within 1% of the printed values in both halves
(REVIEW_NOTES 72). The paper is
internally consistent here (its pre and post figures weight back to its own full-sample "all" mean
and standard deviation, 0.715% and 1.58%). What it shows is that after 1988 our 101-120 portfolio
earns 1.6 times the paper's mean (0.53% against 0.33%) and both loose portfolios are about 1.2
times as volatile (101-120 1.38% against 1.12%, "all" 1.62% against 1.30%), while our "all" earns
less (0.14% against 0.21%): Q1 and Q9.

**Table 9 Panel A (top three size deciles).** Scored (SCORE_LOG row 19): 22 / 10 / 12 of 44 as
printed, +27.0; under the swapped skewness/kurtosis reading 22 / 11 / 11 (27.5), printed as a
diagnostic below the scored rows (REVIEW_NOTES 60). Means 0.90 / 0.93 / 0.66 / 0.66% against
0.84 / 0.91 / 0.73 / 0.69%, t-statistics 7.0 / 8.4 / 8.8 / 10.9 against 7.5 / 9.5 / 9.7 / 10.8,
the maxima 9.2 / 9.8 / 7.3 / 7.2% against 10.1 / 10.0 / 10.6 / 10.5%. Scored from a second cohort
cache built with the driver's --size-deciles-top 3 (make table9a); the two rows the paper
transposes carry eight of the block's twelve misses. It stays worth quoting beside Table 1 because it isolates the dot-com loss from
small-cap noise (Q1).

**Table 9 Panel B (short recalls).** Scored since SCORE_LOG row 22 (10 / 16 / 18, +18.0); since
row 29 15 / 12 / 17 = 21.0 of 44 as printed. It forces the pair closed when the short leg has a
high-volume day (volume above its own 18 month average plus one standard deviation, both
split-adjusted); the pair re-enters only on a new divergence, and since row 29 a recall closes the
pair at the close of the flagged day itself, also under the one-day wait (`--reading R1`,
`claims/TABLE9B_READINGS.md`; REVIEW_NOTES 58, 64 and 74). At this threshold 70% of closes are
recalls, and the fully-invested row rises against Table 1 Panel B where the paper's falls, so
claim 20 (b) stays unreplicated.

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
the paper's (0.48 full sample, 0.51 before 1989, 0.18 after) - ours are 0.33 / 0.39 / 0.05
(rolling 24-month averages of 0.38 and 0.06 when REVIEW_NOTES 32 measured them). The residual
version (0.41 / 0.42 / 0.20 in the paper) is scored too since SCORE_LOG row 15, on the five-factor
residuals: ours 0.28 / 0.33 / 0.09, class C of `GAPS.md` section 2 because the residuals carry the
reversal factor.

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
zero (0.0399 / 0.0449 in the draft against our 0.0399 / 0.0453 over the draft's 408 cohorts; over
all 474 ours is 0.0409 / 0.0466, where the RFS prints 0.0476 / 0.0528 and matches neither) and the by-sector matching - and it disagrees with the RFS on the top-5 sector
mix, which is why that row (Q5) is recorded as an edition difference rather than a defect.

## How the numbers reconcile: the ceiling

The scored denominator is the paper, not a choice. The published article (RFS 19(3), 2006; printed
page = PDF page + 796) prints **893** result numbers in its tables, Figure 4's text and its text and
captions: 881 inside the tables (Table 3's 135 plus the 4 stocks-per-sector counts in its caption),
6 in Figure 4's text and 6 in the text and captions (the pairs-per-cohort count, the hold-out
sentence's three, footnote 4's two). **28** of them repeat another printed cell, so it prints **865
distinct results**, and since SCORE_LOG row 26 the check scores exactly those 865 - 853 table cells
plus Figure 4's 6 and the text's 6 - so the denominator is the paper and from row 26 on only the
numerator can move. `scripts/paper_ceiling.json` is the machine-readable record and
`tests/test_ceiling.py` pins it: to the article (a mechanical re-count of the nine tables from the
text layer, `scripts/paper_ceiling.py`, 881 values), to its own arithmetic (printed = scored +
duplicates for every block) and to the committed check (each block's `Cells: N` and the score line's
total). A PR that drops, adds or double-counts a cell fails that test.

### Blocks

| block | page | printed | scored | duplicates (scored once, where they first appear) |
|---|---|---|---|---|
| Table 1 | 807 | 88 | 88 | - |
| Table 2 Panel A | 809 | 24 | 24 | - |
| Table 2 Panel B | 809 | 40 | 40 | - |
| Table 3 | 812 | 139 (135 in the table, 4 stocks-per-sector counts in its caption) | 139 | - |
| Table 4 | 814 | 116 | 104 | 8: mean excess return, standard deviation (4 portfolios) (= Table 1 Panel B); 4: monthly serial correlation (4 portfolios) (= Table 5 Panel A) |
| Table 5 Panel A | 815 | 36 | 20 | 16: mean, standard deviation, probability of return below 0, minimum historical observation (= Table 1 Panel B) |
| Table 5 Panel B | 815 | 36 | 36 | - |
| Table 6 | 819 | 48 | 48 | - |
| Table 7 | 821 | 136 | 136 | - |
| Table 8 | 822 | 130 | 130 | - |
| Table 9 Panel A | 825 | 44 | 44 | - |
| Table 9 Panel B | 825 | 44 | 44 | - |
| Figure 4 | 822-823 | 6 | 6 | - |
| Numbers printed in the text | 800, 804, 807 | 6 | 6 | - |
| **total** | | **893** | **865** | **28** |

881 = 853 + 28; every other number the text prints outside the tables is classified below, so each
number the paper prints about its results is scored or excluded here, and nothing is left out.

### Numbers outside the tables

The manifest classifies every result-like number the text prints outside the tables (78 entries:
percentages, decimals, basis-point and month counts), each with its page, the quoted words and its
twin or its reason:

| status | entries | what it means | examples |
|---|---|---|---|
| scored | 12 | a cell of the check (Figure 4's six correlations, the six numbers of the "Numbers printed in the text" block) | hold-out 10.4% / 3.8% / t 4.82 (p. 800); footnote 4's 1.32% and 1.9% (p. 804); 2057 pairs |
| duplicate | 42 | repeats a scored table cell; not scored twice | 1.44% and t 11.56 (p. 806, Table 1 A); the VaR sentences (p. 816, Table 5); 118 -> 38 bp (p. 820, Table 8) |
| derived | 17 | arithmetic on table cells; tested in `CLAIMS.md`, not scored | the abstract's 11% (p. 797); 71 and 124 negative months (p. 806); 324 / 162 / 81 bp (p. 810); 4-13 bp (p. 824) |
| parameter | 5 | an input of the rule or the sample | 12- and 6-month periods; 474 months; 200 replications; the -100% delisting assumption |
| external | 2 | another study's estimate the paper quotes | the 37 bp CRSP effective spread (p. 810); the 4-15 bp rebate (p. 825) |

Figures 2 and 3 print no numbers (their digitised readings are shown in the check, unscored), and
Figure 1's three checks (pair rank, trades, day-0 levels) are pass or fail and not counted. The
1999 NBER draft's cells are a separate target (`EDITION_1999.md`) and are never added.

### Keeping it true

- A PR that scores a new block must add it to `scripts/paper_ceiling.json` with its printed count,
  and the re-count must still reproduce the article.
- A PR that changes how many cells a block scores must change the manifest in the same commit; the
  test compares the two.
- Run `python scripts/paper_ceiling.py` to re-count the tables from the PDF (needs `pdftotext`).

## If the goal is a higher score

Nothing the paper prints about its results is left out of the scored set: each number is scored
or excluded above. What no further work can buy is the paper's universe and its CRSP edition:
those are the causes the census in `GAPS.md` names, not missing cells. What is left to try in
that sense is that page's section 7.
