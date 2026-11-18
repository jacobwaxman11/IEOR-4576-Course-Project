# Replicating Gatev, Goetzmann and Rouwenhorst (2006)

*"Pairs Trading: Performance of a Relative-Value Arbitrage Rule", Review of Financial Studies
19(3), 797-827.*

**The paper's thesis.** Match each stock with the stock whose normalized price path is closest over
twelve months, then trade the pair over the next six months whenever its prices diverge by two
standard deviations; the rule earns large, significant excess returns on US stocks from 1962 to 2002.
Conventional risk factors do not explain them -- "only a small portion of the excess returns of pairs
trading can be attributed to their exposures to the five risk factors" (p. 815) -- and the paper reads
them as a reward for enforcing the Law of One Price, leaving their common factor open (p. 826).

**Our finding.** Built from CRSP with the paper's stated rules, its **conclusions replicate and its
tables partly do**; this page is the campaign's final summary and links the ledgers rather than
copying them.

## The score and what it means

<!-- stamp: generated from REPLICATION_CHECK.md by scripts/docs_sync.py; do not edit by hand -->
Score: 411.0 of 865 cells (✓ 322, ~ 178, ✗ 365); how it is counted and its history are in
[`SCORE_LOG.md`](SCORE_LOG.md), and every block's marks are in the exhibit table below.

**What a cell is.** One number the paper prints about its results, compared with ours. The tables,
figures and captions print 881 table values and 12 result numbers in the text; 28 cells repeat a
number scored once where it first appears, leaving 865 distinct cells -- the fixed ceiling, pinned by
`tests/test_ceiling.py`. Each is one `ours / paper` line in [`REPLICATION_CHECK.md`](REPLICATION_CHECK.md)
with the caption that defines it. Parameters, outside estimates and the image readings of Figures 2-3
are not cells, and [`COVERAGE.md`](COVERAGE.md) gives each exclusion.

**The mark rule.** ✓ within 10% of the printed value, worth 1; ~ within 25%, worth ½; ✗ further, worth
0. The score is the sum, 322 + 178/2 = 411.0 of 865 (48%), and the weighting is pinned by
`tests/test_cell_margins.py`; no reading may tune it.

**The factor files.** The five factors are French's 2005 archives, the vintage the paper had: the
Internet Archive's captures of 30 September and 29 October 2005, committed under
`data/raw/french_vintage_2005`. They reproduce Table 8's printed factor standard deviations; today's
files do not, HML's after-1988 standard deviation being 7.8% short (REVIEW_NOTES 72). Every number here
is a 2005-archive number, and every check printed for the campaign says so in its paragraph.

**Byte-reproducible.** The check is generated, never edited: the command under [Reproduce](#reproduce)
writes a `replication_check.md` byte-identical to the committed [`REPLICATION_CHECK.md`](REPLICATION_CHECK.md)
apart from the one line naming its own output tree (2026-11-18, worktree `docs/r12-summary`).

**The claims.** Of the paper's 24 testable claims, 20 replicate: 5 with the paper's numbers and 15 in
substance (sign, significance, order of magnitude). 3 replicate in part (9, 10, 20) and 1 does not hold
as stated (16, the top-20 long-book alpha); claim 4, the abstract's "temporary mispricing", is the
paper's interpretation and is not counted. Each verdict cites its check rows in [`CLAIMS.md`](CLAIMS.md).

## What replicates

Exhibits marked *unscored* are compared in their own reports ([`claims/`](claims/)).

<!-- exhibit table: the "cells ✓ / ~ / ✗ (points)" column is generated from
     REPLICATION_CHECK.md by scripts/docs_sync.py; do not edit it by hand. -->
| exhibit | what it shows | cells ✓ / ~ / ✗ (points) | verdict |
|---|---|---|---|
| Figure 1 | one pair's trading period (Kennecott-Uniroyal) | pass/fail (3 checks) | reproduced: rank 4, five trades within 3 days of the chart |
| Table 1 | excess returns of the pairs portfolios | 49 / 15 / 24 of 88 (56.5) | means and t: replicated; skewness, kurtosis, extremes: missed |
| Table 2 A | trading statistics | 17 / 7 / 0 of 24 (20.5) | replicated |
| Table 2 B | size and sector composition | 28 / 1 / 11 of 40 (28.5) | size mix replicated; decile gap not |
| Table 3 | sector portfolios | 58 / 44 / 37 of 139 (80.0) | replicated in substance |
| Figure 2 | monthly top-20 returns (digitised bars) | unscored | similar path; annual sums correlate 0.76 |
| Figure 3 | cumulative top-20 return (digitised levels) | unscored | committed: replicated; fully invested: the paper's own figure and table disagree |
| Table 4 | systematic risk | 28 / 22 / 54 of 104 (39.0) | conclusion replicated; loadings missed |
| Table 5 A | monthly value at risk | 7 / 6 / 7 of 20 (10.0) | partly |
| Table 5 B | daily value at risk | 26 / 8 / 2 of 36 (30.0) | three columns replicated; the "all" column is loosest |
| Table 6 | true pairs against random pairs | 8 / 10 / 30 of 48 (13.0) | replicated in substance (against our own draws) |
| Table 7 | long and short books and their five-factor regressions | 34 / 20 / 82 of 136 (44.0) | not replicated as stated (claim 16) |
| Table 8 | subperiods split at 1988 | 27 / 19 / 84 of 130 (36.5) | means replicated; loadings missed |
| Figure 4 | common factor: top 20 against the 20 after the top 100 | 0 / 2 / 4 of 6 (1.0) | replicated in substance |
| Table 9 A | top three size deciles only | 22 / 10 / 12 of 44 (27.0) | replicated with numbers |
| Table 9 B | short recalls on high-volume days | 15 / 12 / 17 of 44 (21.0) | profits survive; the 4-13 bp cost does not replicate |
| text and captions | the six result numbers printed outside the tables | 3 / 2 / 1 of 6 (4.0) | hold-out sentence the loosest |

**The paper's final argument.** It does not identify a new factor; it argues the profits are
compensation for an unidentified common factor and leaves its nature to future research (p. 826). Each
step replicates in substance: conventional factors leave a significant alpha (Table 4); the top 20 and
the 20 after the top 100, which hold no pair in common, move together, raw and on five-factor
residuals; and the comovement fades when profits fall. Our common component is about two thirds of the
paper's strength and nearly gone after 1988. A shared component shows a common driver, not that the
driver is a priced risk, so the Law of One Price reading is the paper's, not tested here.

## Why the rest is missing: the nine classes

`GAPS.md` section 2 assigns every scored cell to one cause, by statistic family, table and column;
`scripts/experiments/gaps_census.py` recomputes the tally from the committed check.

| class | cells | ✓ / ~ / ✗ | points | rate | what it is |
|---|---|---|---|---|---|
| F | 310 | 217 / 70 / 23 | 252.0 | 0.81 | level, dispersion, composition, trading statistics, books, Sharpe, the pairs count |
| D | 160 | 46 / 39 / 75 | 65.5 | 0.41 | shape: skewness, kurtosis, minimum, maximum, percentiles |
| C | 200 | 23 / 32 / 145 | 39.0 | 0.20 | the reversal factor's rows and their t-statistics |
| A | 69 | 5 / 9 / 55 | 9.5 | 0.14 | Table 8's regressions, its 101-120 column, Table 2 B's decile row |
| G | 44 | 14 / 10 / 20 | 19.0 | 0.43 | Table 4's Ibbotson block |
| B | 12 | 3 / 2 / 7 | 4.0 | 0.33 | the two rows where the editions disagree |
| E | 14 | 2 / 5 / 7 | 4.5 | 0.32 | the late period |
| H | 8 | 4 / 1 / 3 | 4.5 | 0.56 | persistence: serial correlation |
| I | 48 | 8 / 10 / 30 | 13.0 | 0.27 | Table 6's random-pair bootstrap |
| total | 865 | 322 / 178 / 365 | 411.0 | 0.48 | |

**F, the level (310 cells, 23 crosses, 252.0).** The location and spread of every series replicate. The
23 crosses are named in `GAPS.md` section 2's row: the four Transportation cells, the median of
Financials, the t and median of Industrials, the "all" column's share of negative months, the books'
serial correlation and eleven of Table 9 B's. What would move it: nothing measured -- the one lever the
paper names, a SIC range for Transportation, moves the wrong way (note 94: 47xx pairs are 6.6% of the
top-5 payoff); what is left is the paper's own pair list (Q6, T10).

**D, the shape (160 cells, 75 crosses, 65.5).** One population question in two eras (`GAPS.md`
section 5): before 1983 our top ranks hold Nasdaq names whose quotes do not move, and January 1975 is
the whole top-20 skewness and kurtosis gap; after 1998 loosely matched pairs are 2.5-4 times too
volatile. Every parameter that moves these cells has been measured and buys tail cells with more level
cells (REVIEW_NOTES 40). What would move it: T26 and T27.

**C, the reversal factor (200 cells, 145 crosses, 39.0).** The largest block of lost points (161.0 of the
454) and the only named cause that is not a population. The paper puts the factor in a sentence and a
footnote, printing neither its series nor its construction; its printed moments pin a 2.18%/month
premium at 7.23% volatility, and no long-short construction reaches them -- winners-only 399.0 against
losers-only 406.0 on the 865-cell base at `f33a1cc`, 0 of 72 passing (REVIEW_NOTES 73, 82). The scored
rows use the reading the paper's own Table 8 arithmetic implies (REVIEW_NOTES 61): it lands on the
required factor before 1989 (span 0.949 against 0.943, cosine 0.999; note 99) and misses it after 1988
by 64% in covariance norm, outside the volatility band (note 103). Table 7's loading gap is mostly this
column's, the four smallest books landing within 0.035 at the paper's own factor beta (note 96). What
would move it: the authors' series (T25).

**A, the regression cells (69 cells, 55 crosses, 9.5).** Table 8's pre-1989 block, its post-1988 101-120
column and the decile row, with their 30 t-statistics. Note 99 retracted the paper-side reason: no
printed loading violates an OLS identity, and each panel is feasible -- Panel A's implied R2 0.943 with
the feasible `s_r` band 0.0608-0.0815 around the printed 0.07228, Panel B's joint R2 0.784 inside
0.0388-0.0566. Note 103 then tested round 11's construction lead, a losers-only portfolio more
co-moving with the four factors, against both windows, and it does not survive: 0 of 78 constructions
pass in both, the scored series ranks 7th of 78 on Panel A's target and 63rd on Panel B's, and what
binds is the post-1988 panel, where it is 64% too large in covariance norm and outside the band
(`claims/PANEL_A_RERANK.md`). What would move it: a construction that meets both windows, which none
of the 78 does -- in the end the factor itself (T25).

**G, the Ibbotson block (44 cells, 20 crosses, 19.0).** Table 4's regression on five Ibbotson series: two
are Goyal and Welch's own copy of the Ibbotson inputs and the T-bill is French's `RF`, while the
small-stock leg is a DFA fund from 1982 standing in for the index, and loadings are small numbers scored
as ratios. What would move it: the five SBBI series, worth at most the 20 crosses (T24).

**B, the editions (12 cells, 7 crosses, 4.0).** Table 2 Panel A's trigger at the top 5 and top 20 and
Panel B's top-5 and top-20 sector mix: ours matches the 1999 draft and the published edition differs
from both by more than the sample extension explains (`GAPS.md` section 4). What would move it: nothing
on this data (T32).

**E, the late period (14 cells, 7 crosses, 4.5).** Table 8's post-1988 mean and standard deviation,
Figure 4's raw correlations and the 1999-2002 hold-out sentence. The cause is the late loose-pair
population; the published extension looks like a different stock population (Q1, Q9), so what would
move it is the late-sample universe list (T27).

**H, persistence (8 cells, 3 crosses, 4.5).** Table 5's two serial-correlation rows, with E's cause --
the 101-120 band after 1988 -- and Panel B's 101-120 cell is a printed zero whose lag-1 is 0.04, which
no series reaches. What would move it: T27.

**I, the random-pair bootstrap (48 cells, 30 crosses, 13.0).** These cells compare our own 200-replication
random draw with our own true-pair series, so they measure our resampling. The twelve construction
choices the caption and text leave open are listed with their quotes in
`claims/TABLE6_CONSTRUCTION.md`: five fixed by a quoted sentence, five measured earlier and two in round
ten (note 97), and the measured room is +1.0, all through readings whose level rows cross. What would
move it: nothing on this data; the paper's draws are unpublished (T28).

## What was tried and closed

Every lever measured, its best score, and the rule that kept it out. No default changed; scores are on
the 865 cells unless the row says otherwise.

| lever family | best measured | why it was not shipped | note |
|---|---|---|---|
| S7: the universe without the share-type filter (T16) | 411.0 of 865 as one consistent universe, 139 marks moving for a net of zero; its variants span 407.5-415.0 | the check cannot tell the two universes apart, and an option that swings 7.5 points across its own readings cannot be adopted at the top of the range | 81, 86, 87 |
| Cohort weights by pairs selected (T17) | 411.5 (+0.5) | p. 805's averaging sentence fixes an equal-weighted average; weighting by pool size hands the series to the late sample | 77 |
| Table 3 label from the first formation day (T18) | 411.5 (+0.5) | the paper states no SIC timing rule: one cell inside a band, chosen by score | 83 |
| The delisted leg at its last available price (T19) | 412.0 (`all`, `nondistress`); 411.5 (`merge`) | footnote 4 names both rules in one sentence and its robustness discussion makes this the variant; no printed number separates them | 94 |
| The other Table 9 B recall readings (T20) | 21.5 of 44 (R3); R5 has the paper's sign at 17.0 of 44 | R3 needs "the 18 months" to be a rolling window; R5 needs "the short positions" to mean either leg | 74 |
| Table 6's draw construction (T21) | 14.0 of 48 (412.0), `--pool panel` or `--pair-decile long` | every +1.0 comes from readings whose 16 mean and 16 median cells all cross; the reading the caption supports scores 0.0 | 97 |
| Combinations of readings (T22) | 410.0 (C2); C1 401.5, C3 398.5 | all three lose: the components' signatures overlap, so their deltas do not add | 88 |
| The reversal constructions (T23) | 78 candidates in two rankings: 0 of 72 pass note 82's Table 7 test, and 0 of 78 pass both Table 8 windows (winners-only 399.0 against the losers-only 406.0 on the `f33a1cc` base) | no construction satisfies both windows: the printed standard deviations want one construction and the printed loadings another, and the two windows rank candidates differently (Spearman -0.385) | 73, 82, 103 |
| The eight shipped conventions, each off in turn | 410.0 / 390.5 / 406.5 / 409.0 / 406.5 / 346.0 / 390.0 / 395.0 | each is anchored to text or to a printed statistic, and a price read off the score cannot make a convention | 100 |
| Row 9: the same-issuer rule, the near-frozen filter and the RMS sigma off together | 417.5 (+6.5, a 32.5-point interaction over the 385.0 their deltas predict) | not supported jointly: the gain is all in Tables 7 and 8 (+5.5, +6.0; the class C and A cells) and the loss in the Table 2 composition cells (-2.0, -2.0) the rules were adopted for. Not adopted: the user's decision | 100 |
| The definition readings: percentile method, moments, sign boundary, Ibbotson market leg, Newey-West df | 409.5-411.0 | every family's estimator is the one its caption names and every variant loses or ties; the one textual finding moves no regression cell by more than 6.3e-4 | 95 |
| The literal no-trade screen, `--max-stale-share 0.0` | 365.0 (-46.0) | a pre-1983-only screen cannot touch a residual that is 1.089 after 1988; the counts fall 19-22% and both book residuals move the wrong way | 98 |
| T10's SIC 47xx Transportation attribution | not scored: an attribution, not a reading | 47xx is 6.6% of the top-5 book's summed payoff, so holding it out removes payoff; the paper quotes no SIC range and its printed count already matches | 94 |
| R12-A, T09's price-sign day rule: a formation day counts as traded only when CRSP flags the price (`price_common`), or a missing volume counts as no trade (`volpos_common`) | 361.5 and 365.0 of 865 (300.5 / 304.0 on the 729 main-cache cells) | closed: both rules put the printed counts 20-24% below the paper's (1,799.8 / 1,847.1 stocks against 2,317; 1,563.8 / 1,606.7 pairs against 2,057) and move one of T09's seven cells up (Financials top 5, 0.14 to 0.0861 against the printed 0.11, ✗ to ~) while pushing the other six further from the print; the last named lever for Q5 is gone | 102 |
| R12-B, the construction re-rank against both Table 8 windows | 0 of 78 constructions pass in both | closed: the shipped series ranks 7th of 78 on Panel A's target and 63rd on Panel B's (covariance norm 1.64 times the required one, `s_r` 0.0686 outside Panel B's 0.0388-0.0566 band); the windows rank candidates differently (Spearman -0.385) and the bottom-four deciles move the wrong way | 103 |

## What would move it

Four conditions need data we do not hold. Each is a purchase or a request, not an experiment.

| condition | the data it needs | where it would come from | cells at stake | what it unblocks |
|---|---|---|---|---|
| T24, Table 4's Ibbotson factors | the five SBBI series (small stock, large stock excess, long-term corporate and government, 30-day T-bill), monthly, June 1963-December 2002 | Morningstar Direct at Columbia (Uris or Manhattanville workstations) | class G's 44 cells, 20 crosses, 10.0 points at most | nothing else; realistically the small-stock premium |
| T25, the paper's reversal factor | the series, or its construction (p. 813 and footnote 7) | one request to the authors | class C's 200 cells, 145 crosses, 39.0 points (the block is worth up to 100 in principle) | the class A construction lead |
| T26, the 2002 CRSP edition | the file, or a paper statement about quote-only stocks and closed-end funds | the file, or the authors | up to 31 cells (15.5 points) on Q2's count, plus Figure 1's rank | Q2 and Q3 (T07, T08) |
| T27, the late-sample universe list | the stocks the published edition's 1997-2002 extension uses | the authors | about 40 cells across classes D, E and H, 20 points at most | Q1 and Q9 (T06, T13) |

Five are impossibilities, one line each:

- **T28, Table 6's own random draws:** the draws and seed are unpublished, so its 48 cells compare our resampling with our own true pairs.
- **T29, the paper's own arithmetic (69 cells, class A):** impossible as printed, but the identity half of that argument is retracted (note 99); a kurtosis of 0.02 beside a skewness of 7.01 and a flat decile row remain inconsistencies of description, and what the cells need is the reversal factor itself (T25), which note 103 shows no construction we can build reaches in both Table 8 windows.
- **T30, Table 9 Panel A's transposed skewness and kurtosis rows:** impossible as printed; the swap scores 27.5 against 27.0 and is an inference from internal consistency, not a printed statement.
- **T31, the self-contradictions that score no cell** (Table 1's "all" maximum, Figure 3's fully-invested curve, Figure 2's caption months): as printed they are mutually inconsistent, so there is nothing to reproduce without choosing which half of the paper to believe.
- **T32, the 1999 edition's disagreement (12 cells, class B):** impossible on this data -- ours matches the draft and the published edition differs from both.

## Reproduce

One command reproduces the 865-cell score from the built caches, in about 60 s:

    R=${GGR_SHARED_REPLICATION:-data/processed/replication}
    OMP_NUM_THREADS=2 python scripts/03_replicate.py --universe vol_common \
      --aggregate-only --workers 1 --cache-root $R/vol_common --table9a-cache $R/vol_common_top3 \
      --table9b-cache $R/vol_common_recalls_r1 --table6-cache $R/vol_common_t6_book \
      --delist-cache $R/vol_common_delist100 --out-root .private/base --steps tables,table3,figure1,check
    grep "^- Score" .private/base/tables/replication_check.md

The last line prints `- Score: 411.0 of 865 compared cells (✓ = 1, ~ = ½, ✗ = 0); history in
SCORE_LOG.md.` (Run 2026-11-18; what it wrote is the committed check apart from the figure path it
names for its own out-root.) `python` is the checkout's virtualenv -- `make` puts `.venv/bin` on the
`PATH` -- and `OMP_NUM_THREADS=2` keeps the BLAS pool small on a shared host. It needs two things:

- **The built caches.** Point `R` at the directory holding them: `data/processed/replication` in a
  full checkout, or a shared tree through `GGR_SHARED_REPLICATION` (with `GGR_SHARED_DATA_RAW` and
  `GGR_SHARED_PROCESSED` pointing at the CRSP trees). Under it, `vol_common` is the 474 cohorts,
  `vol_common_top3` Table 9 A, `vol_common_recalls_r1` Table 9 B, `vol_common_t6_book` Table 6 and
  `vol_common_delist100` footnote 4; the last four carry 138 of the 865 cells, so leave one out and
  its section is dropped.
- **The real factor files** in `data/raw/french`, `data/raw/french_vintage_2005` and
  `data/raw/goyal_welch`; a checkout whose files are Git LFS pointers makes the driver exit 1 and name
  them (note 101), and `--allow-missing-factors` is the way back to the old fallback, which silently
  writes a 544-cell check that reads like a result.

`make benchmark REPL=<cache dir>` runs the same command. Before round 12 the target named only
`--steps tables,table3,check` and none of the four side caches, so 138 of the 865 cells were absent
(REVIEW_NOTES 104).

    python scripts/01_get_data.py                            # the licensed CRSP pull (WRDS); then:
    python scripts/02_build_dataset.py                       # yearly panels
    python scripts/03_replicate.py --universe vol_common     # 474 cohorts, Tables 1-5, 7-9, Figures 1 and 4, the check
    python scripts/replication_figures.py                    # Figures 2-4 against the paper's
    make outputs                                             # regenerate report/replication/outputs/ and the stamps

Parsing the paper's numbers requires the published article at the repository root; it is not
redistributed here and the tests that need it are skipped without it.

## The pages of this folder

| page | what it is |
|---|---|
| [`REPLICATION_CHECK.md`](REPLICATION_CHECK.md) | every scored cell, ours / paper, with its mark (generated; the artifact of record) |
| [`SCORE_LOG.md`](SCORE_LOG.md) | the score, how it is counted, and every shipped change to it |
| [`CLAIMS.md`](CLAIMS.md) | the 25 claims, verdicts citing check rows, and the claims-to-cells map |
| [`COVERAGE.md`](COVERAGE.md) | all thirteen exhibits: what is printed, scored, excluded; the ceiling |
| [`METHOD.md`](METHOD.md) | the rule as implemented, with the paper's words quoted per row |
| [`GAPS.md`](GAPS.md) | the census by cause, the open questions Q1-Q12, the paper's own arithmetic |
| [`TBD.md`](TBD.md) | every undecided and unreproducible condition, T01-T32, with its audit trail and index |
| [`REVIEW_NOTES.md`](REVIEW_NOTES.md), [`REVIEW_NOTES_ARCHIVE.md`](REVIEW_NOTES_ARCHIVE.md) | the running log: the live notes and the index to the archive, then notes 1-77 verbatim, never quoted |
| [`EDITION_1999.md`](EDITION_1999.md) | the 1999 NBER draft as a separate, veto-only target |
| [`claims/`](claims/) | one report per unscored or specially-read exhibit, with run logs in `claims/logs/`: `DEFINITION_AUDIT`, `TABLE6_CONSTRUCTION`, `TABLE7_BETAS`, `LARGE_BOOK_BETA`, `CLASS_A_AUDIT`, `CONVENTIONS_865` and the exhibit reports |
| [`outputs/`](outputs/), [`reference/`](reference/) | the generated tables and figures, committed (`make outputs` regenerates), and the 1999 draft PDF with the digitised readings of Figures 2-3 |
| [`analysis/`](analysis/), [`archive/`](archive/) | machine-written records (`paper_consistency.json`, the reversal-factor and class-A audits), and the dated experiment rounds verbatim, including `archive/data_review/` |
