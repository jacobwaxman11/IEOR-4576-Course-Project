# Table 6, reading by reading: why our random pairs lose more than the paper's

Contract J investigation. Table 6 (pp. 818-819) is the one scored table that misses by a
wide margin, and it misses in a pattern. This file measures the four conventions the paper
does not pin down, one at a time, on all 48 cells, and reports which reading the text
supports and what each does to the score. Nothing here ships: the scored check is
unchanged (SCORE_LOG row 23 / #71 keeps its 337.0 of 673).

## What the paper says

The text (p. 818): "The starting point of the bootstrap is the set of historical dates on
which the various pairs open. In each bootstrap we replace the actual stocks with two
random securities with similar prior one-month returns as the stocks in the actual pair.
Similarity is defined as coming from the same decile of previous month's performance."

The caption (pp. 818-819): "Bootstrap of random pairs traded according to the rule that
opens a position in a random pair when the stocks in the true pair diverge by two
historical standard deviations and closes the position after the next crossing of prices.
The random stocks are selected within the same last-month performance decile on the day the
position is opened. The top panel gives summary statistics of the monthly excess returns on
value-weighted portfolios of n pairs of stocks where the position is opened immediately.
The last column is a portfolio of all 120 top pairs. ... The statistics are computed over
200 replications of the bootstrapped sample."

## The pattern to explain

From the scored block (ours / paper, PR #71):

| block | top 5 | top 20 | 101-120 | top 120 |
|---|---|---|---|---|
| A, fully invested, mean | -0.0020 / -0.00137 | -0.0031 / -0.00111 | -0.0031 / -0.00105 | -0.0034 / -0.00113 |
| A, committed, mean | -0.0003 / -0.00083 | -0.0001 / -0.00077 | 0.0000 / -0.00089 | 0.0000 / -0.00091 |
| A, fully invested, sd | 0.041 / 0.055 | 0.021 / 0.023 | 0.021 / 0.023 | 0.010 / 0.012 |
| B, fully invested, mean | -0.0020 / -0.00177 | -0.0029 / -0.00004 | -0.0030 / -0.00154 | -0.0034 / -0.00156 |
| B, committed, mean | -0.0002 / -0.00103 | 0.0000 / -0.00094 | 0.0000 / -0.00112 | 0.0000 / -0.00112 |

(a) Our fully-invested random losses are 2-3 times the paper's while the standard deviations
match within 10% in most columns. (b) The paper's committed means are 0.6-0.85 of its
fully-invested means in every column, while ours are near zero.

## How the readings were measured

Each reading is a switch on `scripts/claims/table6_random_pairs.py` whose default is the
shipped behaviour, so every earlier run and `--mode control` stay byte-identical (control:
`max_diff_shipped` 0.0, 948 cohort-waits, 5,688 cells, re-run after the change). The runs
are 50-replication screens over all 474 cohorts, then a 200-replication confirmation of the
reading that moves cells; every count below is over the 48 cells of Table 6, scored with the
check's own rule (within 10% = check, within 25% = tilde), against
`scripts/claims/table6_paper.json`.

The regenerated control log (claims/logs/TABLE6_control.log) prints `max_diff_vector_layer`
0.173, where the log committed on 2026-11-02 printed 1.3e-15. That log predates SCORE_LOG row
18, which made the shipped committed series the literal payoffs, while
`t6_engine.book_months`, the vectorised cross-check, still builds committed as the book scaled
by `n_open / N`, which is reading 1's book-share. The gap is committed-only (employed agrees to
4e-16 on 1999-09) and no scored number uses the vector layer. The same comparison confirms
reading 1 independently: book-share computed through `monthly_series` with an empty trade log
and through the vector layer agree to 2-4e-16 on four cohort-waits (1999-09 both waits, 1975-01
and 1963-07, coordinator check).

    python scripts/claims/table6_random_pairs.py --mode run --reps 50 --workers 8 \
      --cache-root <R>/vol_common --out-root <scratch>/<name> [--pool panel] \
      [--prior-month trading] [--committed-capital book-share]

## The four readings, and what each scores

| reading | option (default first) | 50 reps | 200 reps | the paper's words | verdict |
|---|---|---|---|---|---|
| shipped control | all defaults | 11.0 (8 / 6 / 34) | 11.0 (8 / 6 / 34) | - | baseline |
| committed capital | `--committed-capital literal\|book-share` | 12.5 (8 / 9 / 31) | 13.0 (8 / 10 / 30), <scratch>/book200 | "value-weighted portfolios of n pairs" (caption, p. 819) | supported: book-share reproduces the paper's committed/fully-invested ratio; +2.0 points |
| random-stock universe | `--pool formation\|panel` | 16.5 (14 / 5 / 29) | 15.5 (12 / 7 / 29) | "two random securities" (text, p. 818); "within the same last-month performance decile" (caption) | partly supported: committed means then match the paper, but fully-invested means move further away; +4.5 points |
| which last month | `--prior-month calendar\|trading` | 11.0 (7 / 8 / 33) | not run | "previous month's performance" (text) against "on the day the position is opened" (caption) | contradicted by measurement: no gain, and columns 2-4 drift further |
| statistics over replications | `--stats replication\|pooled` | unchanged in every configuration | - | "computed over 200 replications" (caption) | neutral: means identical, sd differ by at most 2.2%, medians by at most 0.07 bp; no cell moves (one tilde becomes check in the trading-prior run) |

### 1. Committed capital: the caption's value-weighted book, not the literal payoffs

Committed / fully-invested ratio of the mean, by column (A / B):

| column | paper | ours, literal (shipped) | ours, book-share | our Table 1 Panel B |
|---|---|---|---|---|
| top 5 | 0.606 / 0.582 | 0.161 / 0.089 | 0.759 / 0.742 | 0.625 |
| top 20 | 0.694 / 23.500 | 0.039 / -0.009 | 0.687 / 0.688 | 0.629 |
| 101-120 | 0.848 / 0.727 | 0.000 / -0.008 | 0.752 / 0.743 | 0.658 |
| top 120 | 0.805 / 0.718 | -0.007 / -0.014 | 0.705 / 0.699 | 0.603 |

The paper's own Table 1 has the same ratio (0.62 / 0.58 / 0.63 / 0.56 committed divided by
fully invested), and so do our Table 1 cells, which are scored and match. Table 6 is the one
table where our committed series collapses, and the reason is arithmetic rather than
economic: since SCORE_LOG row 18 the committed series is the literal sum of the daily
payoffs over the pairs *selected*, so a bootstrap replication that draws a stock with no data
after the open (which happens often) dilutes the mean by the withdrawn pairs, and the sign
can flip. The value-weighted book scaled by the share of pairs holding a position -- the
caption's "value-weighted portfolios of n pairs" -- restores 0.69-0.76 at every
column. It adds 2.0 points (8 / 10 / 30 at 200 replications, <scratch>/book200; the 50-replication screen gave 8 / 9 / 31), all of them in the
committed cells, and leaves the fully-invested cells untouched.

One anomaly is the paper's, not ours: B / top 20 / committed / mean is printed as -0.00004,
which makes its committed/fully-invested ratio 23.5 and breaks the pattern of every other
column (0.58-0.85). Whatever produced that cell, no reading of the bootstrap reproduces a
random-pair mean of exactly zero.

### 2. Where the random stocks come from: the text does not say "the formation universe"

The text says "two random securities" and the caption only constrains their *deciles*; the
shipped draw takes them from the cohort's formation universe (the pipeline's eligible
sample: 12 months of history, the stale-quote screen, common stocks). The alternative draws
from every common CRSP stock with data in the trading window:

| column | paper mean | ours, formation (shipped) | ours, whole panel |
|---|---|---|---|
| A, fully invested | -0.00137 / -0.00111 / -0.00105 / -0.00113 | -0.0019 / -0.0031 / -0.0031 / -0.0034 | -0.0041 / -0.0065 / -0.0067 / -0.0071 |
| A, committed | -0.00083 / -0.00077 / -0.00089 / -0.00091 | -0.0003 / -0.0001 / 0.0000 / 0.0000 | -0.0008 / -0.0003 / -0.0002 / 0.0000 |
| A, fully invested, sd | 0.0552 / 0.0230 / 0.0226 / 0.0120 | 0.0411 / 0.0216 / 0.0215 / 0.0101 | 0.0470 / 0.0251 / 0.0247 / 0.0126 |

The whole panel fixes the level of the committed means (top 5: -0.00084 against -0.00083)
but makes the fully-invested losses worse, so the block gains 4.5 points while its central
column moves the wrong way. Read together with reading 1 this is informative: the paper's
committed series behaves like a value-weighted book on a *wider* pool, while its
fully-invested series stays close to what the eligible universe gives. That is hard to
produce with one draw.

### 3. Which "last month": the calendar reading wins on the numbers

The text says "previous month's performance", which is the shipped previous-calendar-month
`mthret`; the caption's "on the day the position is opened" invites the 21 trading days
before the open. Measured, the trading reading scores 11.0 (7 / 8 / 33) at 50 reps, the same
as the shipped 11.0 (8 / 6 / 34), and it pushes columns 2-4 further from the paper (A /
top 20 mean -0.0023 against -0.0011) while turning several committed means positive (ratios
-0.10 to -0.30). The decile assignment also loses events: stocks without a full 21-day
history drop out of the ranking. Nothing in the measurement supports moving away from the
calendar month.

### 4. Statistics over replications: the two readings agree

Averaging each replication's statistic (shipped) and taking the statistic of all 200
replications' months pooled give identical means (the mean of means is the pooled mean) and
standard deviations within 2.2% (top 5 A employed 0.041128 against 0.041234) and medians
within 0.07 bp. The 48-cell tally is unchanged in all four configurations; in the
trading-prior run one cell moves from tilde to check at the 25% boundary. The caption's
"computed over 200 replications" is therefore satisfied by either reading, and this one
cannot explain the gap.

## What this says about the gap

- Fact (b), the committed ratio, is a reporting definition and is explained: the caption's
  value-weighted book (reading 1) reproduces the paper's 0.6-0.85 at every column, and our
  Table 1 already does the same, so the shipped literal committed series is the odd one out
  in Table 6 only.
- Fact (a), our fully-invested random losses being 2-3 times the paper's, is *not* explained
  by any of the four readings. It survives the pool, the prior-month and the statistics
  reading, and the pool makes it worse. The standard deviations match, so the difference is
  in the mean: our random pairs lose steadily while the paper's lose about half as much per
  month. That points at details of the draw and the position accounting the caption does not
  fix (which securities count as "similar prior one-month returns" inside a decile, and what
  happens when a drawn leg stops trading) rather than at any of the four switches measured
  here.

## Recommendation

Ship nothing on this evidence. If the coordinator wants one of these readings, the
best-supported by the text and by the ratio evidence is the committed-capital reading
(reading 1): the caption says "value-weighted portfolios of n pairs" and that reading
restores the paper's own committed/fully-invested ratio and adds 2.0 points (12.5 was the 50-replication screen;
13.0 at 200 replications, <scratch>/book200) without touching a single fully-invested cell. The pool reading scores
higher (15.5) but is mixed in direction and rests on a sentence that does not name a pool,
so it should not ship on the score alone. The prior-month and statistics readings change
nothing worth scoring, and the prior-month reading measurably moves away from the paper.
A follow-up that could explain fact (a) would have to vary the *within-decile* draw (uniform
over the decile, as shipped, against a distance-weighted or size-weighted draw) and the
treatment of a drawn leg that stops trading; neither is a reading of a sentence in the paper.