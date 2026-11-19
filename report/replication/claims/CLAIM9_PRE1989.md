# Claim 9: the all-pairs shortfall, located but not explained (round 6C, corrected in round 7)

Claim 9 (CLAIMS.md): "This gives average net profits ranging from 113 to 225 bp over each six-month
period. Comparing these profits to the reported standard errors, we conclude that they are both
economically and statistically significant." (p. 810). The ledger's reading is the paper's own
Table 1 Panel B rows: compound the monthly mean over six months, subtract the 324 bp of costs the
paper names, and divide by six times the Newey-West standard error of the monthly mean.

## 1. The arithmetic of the shortfall

| portfolio | ours: mean | se | gross 6m | net 6m | t_net | paper net 6m / t_net |
|---|---|---|---|---|---|---|
| top 5 | 0.723% | 0.112% | 442 bp | 118 bp | 1.75 | 131 bp / 1.83 |
| top 20 | 0.891% | 0.096% | 547 bp | 223 bp | 3.87 | 225 bp / 3.90 |
| 101-120 | 0.764% | 0.078% | 467 bp | 143 bp | 3.08 | 163 bp / 3.20 |
| all | 0.629% | 0.090% | 383 bp | 59 bp | **1.10** | 113 bp / **2.09** |

Three of the four portfolios carry the claim (the top 20 and 101-120 to the basis point, the top 5
just under 1.96). The all-pairs column is the weak cell: crossing t = 1.96 needs an all-pairs mean of
**0.703%** against our 0.629%, i.e. +11.8% relative, and 72% of that gain has to come before 1989
(the pre-1989 mean is 0.896% against the paper's 0.992%, the post-1988 mean 0.143% against 0.212%;
weighted by the 306:168 months, the pre-1989 gap is 72% of the full-sample mass).

## 2. Where the pre-1989 shortfall sits

The unrestricted book was rebuilt for every cohort (`table3_sectors.py all --workers 5`, run
directory `/tmp/T/t1`), which gives the book by rank, size, exchange, frozen-quote share, SIC relation
and the cheaper leg's dollar price, and the pair population behind it.

**Population: no like-for-like count shortfall of the size first reported.** The paper prints one
number for the all-pair portfolio's size, "The average number of pairs in the all-pair portfolio is
2057", in the notes of Tables 1, 5, 8 and 9 (pp. 807, 815, 822, 825), and every one of those notes is
for the whole sample: Table 1's reads "between July 1963 and December 2002 (474 observations)", and
Table 8's gives the same 2057 over both of its panels, July 1963-December 1988 and January
1989-December 2002. The one other count on that window is the number actually traded, Table 2 Panel
A's "Average number of pairs traded per six-month period" 1944.22 (p. 809). Neither count is
era-specific: the paper prints no pre-1989 and no post-1988 pair count.

An earlier version of this page (and REVIEW_NOTES 83) set our 1963-1988 average, 1680 pairs per
cohort over 306 cohorts, against the 2057 and read an 18% pre-1989 population shortfall. That
compared a 306-cohort average with a 474-cohort one and is withdrawn (REVIEW_NOTES 85). Like for
like, from the shipped cache (`claims/CLAIM_SENSITIVITY.md`, claim 9 section):

| window | quantity | cohorts | ours | printed | gap |
|---|---|---|---|---|---|
| July 1963 - December 2002 | pairs in the portfolio | 474 | 2009 | 2057 | -2.3% |
| July 1963 - December 2002 | pairs traded per period | 474 | 1884 | 1944.22 | -3.1% |
| July 1963 - June 1997 (the 1999 draft) | pairs in the portfolio | 408 | 1788 | 1870 | -4.4% |
| July 1963 - December 1988 (Table 8 A) | pairs in the portfolio | 306 | 1680 | none printed | - |
| January 1989 - December 2002 (Table 8 B) | pairs in the portfolio | 168 | 2607 | none printed | - |

Our count rises over the sample (846 pairs per cohort in 1963-72, 2405 in 1973-82, 1793 in 1983-88,
2306 in 1989-98, 3360 in 1999-2002), so a pre-1989 average below the full-sample one is what our own
era profile produces; whether the paper's profile is the same cannot be read from the counts it
prints. On the windows where a count is printed ours is 2-4% short: 2.3% on the portfolio's size and
3.1% on the pairs traded over the paper's 474 cohorts, 4.4% on the draft's 408. The draft's Table I
note reads "There are 408 observations, from 2/1963 until 12/1997"; the 408 cohorts July 1963 - June
1997 are the window `EDITION_1999.md` and `GAPS.md` section 4 score it on, and they are the only 408
months that fit the count (the draft's own February 1963 - December 1997 label would be 419), which
is why the count and not the label fixes the window.

**What the printed subperiod rows show.** Table 8 Panel A is the one exhibit the paper prints for the
pre-1989 window. Against it our all-pairs mean is 0.896% against 0.992% (-9.7%) and its standard
deviation 1.436% against 1.651% (-13.0%) (check, Table 8, pre_mean and pre_std rows): both moments are
10-13% below the paper's. After 1988 the mean is 0.143% against 0.212% (-33%) and the standard
deviation 1.622% against 1.295% (+25%). Weighted by months, 72% of the full-sample mean gap is
pre-1989 (section 1). On the 1999 draft's own window and measure (six-month committed returns, 408
cohorts) the mean is short by the same order (section 3) but the dispersion is not: the all-pairs
standard deviation is 0.0309 against the draft's 0.0312 (-1.0%).

**Composition, by era** (share of the book in the all-pairs column):

| fact | 1963-72 | 1973-82 | 1983-88 | 1989-98 | 1999-2002 |
|---|---|---|---|---|---|
| ranks 121+ | 76% | 94% | 91% | 77% | 73% |
| both NYSE | 79% | 21% | 42% | 106% | 115% |
| both Nasdaq | - | 44% | 22% | -16% | 8% |
| cheaper leg over $15 | 60% | 27% | 62% | 182% | 197% |
| cheaper leg $1-5 | 12% | 36% | 10% | -50% | -117% |
| high frozen-quote tercile | 16% | 31% | 25% | -54% | 5% |
| cross-group pairs | 16.5% | 29.6% | 24.4% | 25.4% | 30.0% |

The facts that matter for claim 9:

- **It is a deep-book gap.** Ranks 121+ carry 73-94% of the book in every era, and the top-5 and top-20
  portfolios match the paper, so whatever is missing is in the loose tail, not in the signal.
- **It is not a penny-stock effect.** Pairs whose cheaper leg is under $1 are 0-6% of the
  population and carry 0-7% of the pre-1989 book; the $1-5 bucket is 26% of the 1973-82 population,
  carries 36% of that era's book and a *negative* share after 1988. Screening it out lowers the
  pre-1989 book (section 4).
- **It is not the delisting convention, but that is the largest single lever found**: trades closed on a
  delisting are 3.1% of all trades before 1989 and carry a mean payoff 2.5 bp below the window-end
  trades; dropping the delisting return entirely lifts the all-pairs net t from 1.10 to 1.22
  (section 4).
- **It is not the frozen-quote screen**: the shipped 95% limit is a measured maximum
  (GAPS.md Q2), and stricter limits lose on the whole check.

## 3. The 1999 NBER draft as an independent second measurement

`EDITION_1999.md` scores the same engine against the 1999 draft, which reports 408 cohorts (July
1963-June 1997) and measures the books on *its* capital basis (mean on employed capital = the paper's
own words, "divides the payoffs by the number of pairs that open"). On that basis our all-pairs book is
**0.0266 per six months against the draft's 0.0297 (-10.4%)**, and on committed capital 0.0254 against
0.0288 (-11.8%); the top 20 matches (0.0376 against 0.0396, -5.1%) and the 101-120 is -12.1%. The
1999 draft therefore reproduces the same shape on a different sample and a different capital
convention: **the top 20 replicates and the deep book is ~10-12% short**. On the same 408 cohorts our
pair count is 1788 against the draft's 1870 (-4.4%) and our all-pairs standard deviation matches
(0.0309 against 0.0312). The draft's last cohort starts in June 1997 and 306 of its 408 cohorts are
pre-1989, so the shortfall is not a product of the RFS paper's 1997-2002 cohorts; the draft prints no
subperiod split, so on its own it does not place the shortfall before 1989 - Table 8 Panel A does
(section 2).

## 4. The three readings tested

Each reading is built for all 474 cohorts, assembled into a complete cohort cache that replaces Table 1's
and Table 3's employed rows, and scored on the whole 865-cell check (run directories
`/tmp/T/runs/c9_*`). The score covers the blocks that read the monthly series; the regression blocks
(Tables 4, 7 and 8's factor rows) are the shipped ones and do not move.

| reading | rule | all-pairs mean pre-1989 / post-1988 / full | net t | score |
|---|---|---|---|---|
| shipped | - | 0.00896 / 0.00143 / 0.00629 | 1.10 | 411.0 |
| `last_px` | a delisted leg closes at its last available price: no delisting return enters the payoff (fn. 4, p. 804) | 0.00903 / 0.00157 / 0.00639 | 1.22 | 412.0 (REVIEW_NOTES 94; the 412.5 first recorded came from the round-6 experiment script's engine, which a full build does not reproduce) |
| `minpx5` | a pair whose cheaper leg traded below $5 at formation is not formed | 0.00758 / 0.00285 / 0.00590 | 0.66 | 398.0 |
| `samesector` | both legs in the same group, ranked jointly (the "all" column of Table 3's rule) | 0.00989 / 0.00149 / 0.00691 | 1.82 | 394.5 |

The informative reading is `samesector`: restricting both legs to one group lifts the pre-1989 all-pairs
mean to 0.00989 - the paper's 0.992% almost exactly - and the full-sample net t to 1.82, and costs 16.5
points only because the concentrated portfolios then overshoot (top 5 1.23% against the paper's pre-1989
1.03%). It contradicts the paper's own text ("In addition to 'unrestricted' pairs, we will also present
results by sector", p. 803), so it cannot ship; what it measures is that **our cross-group pairs are the
weak population**. The group split of the unrestricted book says the same thing directly: cross-group
pairs carry 16-30% of the book, against a population share of 29.7% (the paper's Table 2 B prints
33%; check, Table 2 Panel B, share_mixed_sector_pairs) - and the cross-group pairs contribute
0.00095 per month in 1963-72 and 0.00037 in 1989-98 while the within-group pairs contribute 0.00482
and 0.00109; in the top 5 they contribute *negative* amounts in every era from 1973-82 on, in the top
20 in every era from 1973-82 on but 1983-88. This is a measurement of our book only: the paper does not
print what its cross-group pairs earn, and its mixed-sector share is larger than ours, so the
weakness of our cross-group pairs does not by itself explain the gap to the paper. `last_px` is the
one reading that also gains on the whole check (+1.5, Table 1 50/14/24 against 49/15/24); it reads
footnote 4's second clause as the rule where the sentence names the delisting return first, and one
and a half cells is not support, so it does not ship either.

## 5. Verdict

**Claim 9 is partly replicated; the weak column's shortfall is located, not explained.** Net profits
are positive in all four portfolios and significant in three of them, exactly as the paper states; the
all-pairs column's net t is 1.10 against 2.09 because our all-pairs mean is 12% below the paper's
(0.629% against 0.715%). What is measured about that shortfall:

- **Where it sits.** In the deep book (ranks 121+ carry 73-94% of the all-pairs book in every era;
  the top 5 and top 20 match), 72% of it before 1989 by month weight: Table 8 Panel A's all-pairs mean
  is 9.7% low and its standard deviation 13% low. The 1999 draft's 408 cohorts (July 1963 - June 1997)
  show a mean 10-12% low on its own capital bases, with a standard deviation that matches.
- **What it is not.** It is not a pair count of the size first reported: the "18% fewer pairs" was a
  306-cohort average set against a 474-cohort one. Like for like the count is 2.3% short over the
  paper's 474 cohorts (and the pairs traded 3.1% short) and 4.4% short over the draft's 408. It is not
  the penny-stock tail, the frozen-quote screen or a rule we can defend: of the three readings built
  over all 474 cohorts, the one that moves the all-pairs net t most without contradicting the text
  (`last_px`) closes 14% of the distance to 1.96 (1.10 to 1.22) and does not ship; `samesector`
  reaches the paper's pre-1989 mean but contradicts the paper's unrestricted rule.
- **What is not known.** Whether the 4.4% more pairs the draft's window holds would carry the mean
  gap, and what the paper's cross-group pairs earn, are not measurable from what either edition
  prints.

Consequence for `CLAIMS.md`'s claim 9 row: the verdict stays **partly**; its evidence pointer carries
this page, and the row names the shortfall's location, not a cause.

## 6. Reproduction

    PY=.venv/bin/python
    $PY scripts/experiments/table3_sectors.py all --root /tmp/T/t1 --workers 5   # the deep book
    $PY /tmp/T/analyze.py                                                       # era + kind tables
    sh /tmp/T/run_c9.sh last_px                                                 # build + score one reading
    $PY scripts/edition_1999.py --cohorts $R/vol_common/cohorts --out /tmp/T/edition1999.md
    GGR_SHARED_REPLICATION=$R $PY scripts/experiments/claim_sensitivity.py    # pair counts by window

`$R` is the shared replication directory. The pair population is `/tmp/T/ana/population.csv`, the
price buckets `/tmp/T/ana/price_bucket.csv`, the delisting P&L `/tmp/T/delist_share.py`'s output.
