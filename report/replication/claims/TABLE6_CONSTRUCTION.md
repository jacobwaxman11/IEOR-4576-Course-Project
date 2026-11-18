# Table 6's random pairs: every construction choice, and what is still open

Contract R10-D. Table 6 (pp. 818-819) is the one scored table that misses by a wide margin: 48
cells at 8 check / 10 tilde / 30 cross = 13.0, against our own 200-replication random-pair
bootstrap (`SCORE_LOG.md` row 28). `TBD.md` T21 said the remaining room was "+0.5 at most" and
called it a guess. This page makes the guess a measurement: it quotes every sentence the paper
gives about the bootstrap, lists each construction choice those sentences leave open, records
what the shipped `scripts/claims/table6_random_pairs.py` does for it and whether that reading
has been measured, and then measures the choices that were never tried, at 200 replications,
on the whole sample (474 cohorts) against the current 48-cell block.

Scored basis of every number here: the cohort cache `data/processed/replication/vol_common`,
`--committed-capital book-share` (the shipped Table 6 basis, `SCORE_LOG.md` row 28), seed
20060101, 200 replications, both waits, all 474 cohorts. The implied 865 total is
411.0 - 13.0 + block, because no other cell of the check reads a Table 6 run.

## 1. What the paper says

Section 3.6, p. 818, verbatim from the text layer (`paper_rfs.txt`; the paragraph's last word
"performance" resumes on p. 819 after Table 6):

> In particular, we conduct a bootstrap where we compare the performance of our pairs to random
> pairs. The starting point of the bootstrap is the set of historical dates on which the various
> pairs open. In each bootstrap we replace the actual stocks with two random securities with
> similar prior one-month returns as the stocks in the actual pair. Similarity is defined as
> coming from the same decile of previous month's performance.

Table 6's caption, p. 819, verbatim ("value-weighted" is hyphenated across two lines in the
text layer):

> Bootstrap of random pairs traded according to the rule that opens a position in a random pair
> when the stocks in the true pair diverge by two historical standard deviations and closes the
> position after the next crossing of prices. The random stocks are selected within the same
> last-month performance decile on the day the position is opened. The top panel gives summary
> statistics of the monthly excess returns on value-weighted portfolios of n pairs of stocks
> where the position is opened immediately. The last column is a portfolio of all 120 top pairs.
> The bottom panel summarizes the performance with one day waiting before the position is
> opened. The statistics are computed over 200 replications of the bootstrapped sample.

Same page, after the table: "We bootstrapped the entire set of trading dates 200 times."

Four passages elsewhere in the paper fix conventions that the bootstrap section itself does not
repeat, and they apply to the random pairs as much as to the true ones:

- Pairs formation, p. 803: "In each pairs formation period, we screen out all stocks from the
  CRSP daily files that have one or more days with no trade. This serves to identify relatively
  liquid stocks as well as to facilitate pairs formation."
- Trading rule and delisting, p. 804: "We open a position in a pair when prices diverge by more
  than two historical standard deviations, as estimated during the pairs formation period. We
  unwind the position at the next crossing of the prices. If prices do not cross before the end
  of the trading interval, gains or losses are calculated at the end of the last trading day of
  the trading interval. If a stock in a pair is delisted from CRSP, we close the position in that
  pair, using the delisting return, or the last available price."
- Capital basis and weighting, p. 807: "We consider two measures of excess return on a portfolio
  of pairs: the return on committed capital and the fully invested return, that is, the return
  on actual employed capital. The former scales the portfolio payoffs by the number of pairs that
  are selected for trading, the latter divides the payoffs by the number of pairs that open
  during the trading period." And, on the same page: "The daily returns on the long and short
  positions are calculated as value-weighted returns in the following way, ... w_i,t = w_i,t-1
  (1 + r_i,t-1) ... This has the simple interpretation of a buy-and-hold strategy."

## 2. The choice table

Twelve choices. "Stated" means a quoted sentence above fixes it; "open" means no sentence does,
and then the reading has to be argued from the text or measured.

| # | choice | what the paper gives | what the shipped script does | measured? |
|---|---|---|---|---|
| 1 | population the deciles are computed over and drawn from | "two random securities" (p. 818), the sample is the paper's liquid universe (p. 803); the population of the deciles is not named | the cohort's formation universe (`vol_common`: 12 months of history, the stale-quote screen, common shares), equal-count deciles inside it | yes: `--pool panel` (every common CRSP stock with a prior-month return). Contract J measured 15.5 of 48 at 200 replications (`TABLE6_READINGS.md` section 2); re-scored this round on the shipped book-share basis it is 14.0, section 3 - the 1.5 difference is the committed series |
| 2 | decile breakpoints | open: only "the same decile of previous month's performance" (p. 819) | equal-count deciles of that month's formation universe | yes: `--decile-breaks panel` (CRSP-wide breakpoints) 13.0 (`REVIEW_NOTES` 75, 50 reps). NYSE breakpoints are not implemented and no sentence names them |
| 3 | which "last month" | both readings are printed: "previous month's performance" (p. 818) and "last-month performance decile on the day the position is opened" (p. 819) | the previous calendar month's `mthret` | yes: `--prior-month trading` (21 trading days before the open) 11.0 at 50 reps on the literal committed basis (`TABLE6_READINGS.md` section 3); re-scored this round at 200 reps, section 3 |
| 4 | leg-by-leg matching or one decile per pair | "replace the actual stocks with two random securities ... as the stocks in the actual pair" (p. 818) against the caption's singular "within the same last-month performance decile" (p. 819) | leg by leg: each drawn stock comes from its own true leg's decile (`--pair-decile own`) | no before this round: `--pair-decile long` / `short`, section 3. 13-28% of true pairs have both legs in the same decile, so the two readings differ |
| 5 | the opening trigger | stated, and given to the true pair: "opens a position in a random pair when the stocks in the true pair diverge by two historical standard deviations" (p. 819) | opens on the true trade's open day | closed by the quote; the own-trigger reading has no support |
| 6 | the closing event | stated: "closes the position after the next crossing of prices" (p. 819) | closes with the true trade it replaces (`--close true`), i.e. at the true pair's next crossing | measured as a variant: `--close own` and `--close own-rebase` (the drawn pair's own next crossing) 0.5 of 48 (`REVIEW_NOTES` 75, 50 reps) |
| 7 | a drawn leg that stops trading | stated for every pair, p. 804: "If a stock in a pair is delisted from CRSP, we close the position in that pair, using the delisting return, or the last available price" | caps the position at the earlier of the true close and a forced exit (delisting, a leg's last row); drops the position if a drawn leg has no price at the open | closed by the quote; D3 (`--complete-legs`, draw only legs with a full return record over the trade) 13.0 (`REVIEW_NOTES` 75, 50 reps). Frequency of both events, section 4 |
| 8 | capital basis | stated, p. 807 (committed = scaled by the pairs selected; fully invested = divided by the pairs that open); both panels printed | committed = the value-weighted book scaled by the share of pairs holding a position; fully invested = employed | yes: literal 11.0 against book-share 13.0 (`REVIEW_NOTES` 69, 75; 200 reps). Shipped |
| 9 | value weighting inside the portfolio | stated, eqs. (2)-(3), p. 807, with "the simple interpretation of a buy-and-hold strategy" | the engine's books: 1 dollar per leg at the open, drifting with returns, shared with Tables 1-3 | not a Table 6 choice: the accounting is the one Tables 1-3 score with, and `--mode control` reproduces the shipped true-pair rows exactly |
| 10 | how the replications are averaged | "The statistics are computed over 200 replications" (p. 819) | each replication's statistic, averaged over the 200 (`--stats replication`) | yes: `--stats pooled` leaves every cell unchanged in all four configurations (`TABLE6_READINGS.md` section 4) |
| 11 | the within-decile draw | open: "Similarity is defined as coming from the same decile" (pp. 818-819) fixes membership, not distance | uniform over the decile's stocks, excluding the two true legs and each other | yes: `--draw-near 10` (the ten nearest ranks) 12.0 (`REVIEW_NOTES` 75, 50 reps) |
| 12 | the number of pairs, the columns, the two waits, the 200 replications | stated throughout the caption and the text | all ranks 1-120 of every cohort, four portfolios, both waits, 474 cohorts | n/a, stated |

Choice 1 is the only one where the two candidate readings are both defensible from the text and
the paper's own sample argues for the shipped one: the deciles of "previous month's performance"
are deciles of the sample the study has (its liquid universe, p. 803), not of every share CRSP
carries. That is why the pool reading is recorded as a sensitivity and not shipped, even though
it scores higher than the shipped reading.

## 3. The readings measured this round, at 200 replications

Four runs, 200 replications each, all 474 cohorts, on the shipped committed basis. The control
is the shipped cache itself, re-collected by `scripts/claims/t6_score.py`: 13.0 (8 check / 10
tilde / 30 cross) and the implied 411.0, which is the check's own Table 6.

| id | reading | option | block of 48 | check / tilde / cross | implied 865 | verdict |
|---|---|---|---|---|---|---|
| -- | shipped control | all defaults | 13.0 | 8 / 10 / 30 | 411.0 | control |
| R-B | the decile month the caption names: the 21 trading days before the open | `--prior-month trading` | 13.0 | 6 / 14 / 28 | 411.0 | text-supported, score-neutral: the levels move toward the paper, three dispersion cells move out |
| R-A | the decile population is every common CRSP stock with a prior-month return | `--pool panel` | 14.0 | 13 / 2 / 33 | 412.0 | sensitivity: the dispersion rows match, every level row is a cross |
| R-C | both legs of a random pair from one decile (the long leg's) | `--pair-decile long` | 14.0 | 10 / 8 / 30 | 412.0 | sensitivity: four cells within the mark tolerance, no mechanism behind it |
| R-D | the same, from the short leg's decile | `--pair-decile short` | 12.0 | 8 / 8 / 32 | 410.0 | sensitivity: the mirror image of R-C, one point *below* the shipped run, so R-C's +1.0 is the choice of decile, not the reading |

The fully invested means, in percent per month (panel A; panel B is the same ordering):

| reading | top 5 | top 20 | 101-120 | top 120 |
|---|---|---|---|---|
| paper (Table 6, p. 819) | -0.137 | -0.111 | -0.105 | -0.113 |
| shipped | -0.2033 | -0.3107 | -0.3062 | -0.3397 |
| R-B, trading-prior month | -0.1514 | -0.2258 | -0.2452 | -0.2772 |
| R-C, one decile (long) | -0.2246 | -0.3335 | -0.3522 | -0.3840 |
| R-D, one decile (short) | -0.2305 | -0.3235 | -0.3382 | -0.3607 |
| R-A, panel deciles | -0.4125 | -0.6509 | -0.6696 | -0.7081 |

Read together they separate the two things the block is made of. Every run that widens or mixes
the draw makes the *level* worse (R-A doubles it, R-C adds 10%) and matches the *dispersion*
better; the one reading that moves the level toward the paper (R-B, the caption's own "on the day
the position is opened") does so at the cost of three standard-deviation cells that were checks.
R-D is the braces on R-C: the same reading one decile over scores 12.0, two median cells below the
shipped run, so the one-decile reading moves the block by a point in either direction depending on
which decile is picked, and its level is worse either way.

Per mark class, the shipped run and the four readings:

| mark class | shipped | R-B | R-A | R-C | R-D |
|---|---|---|---|---|---|
| mean, check / tilde / cross | 0 / 1 / 15 | 1 / 2 / 13 | 0 / 0 / 16 | 0 / 1 / 15 | 0 / 1 / 15 |
| standard deviation, check / tilde / cross | 7 / 6 / 3 | 4 / 9 / 3 | 13 / 2 / 1 | 8 / 6 / 2 | 7 / 6 / 3 |
| median, check / tilde / cross | 1 / 3 / 12 | 1 / 4 / 11 | 0 / 0 / 16 | 2 / 1 / 13 | 1 / 1 / 14 |

The 30 crosses of the shipped run are 15 mean cells, 12 median cells and 3 standard-deviation
cells. The block's marks are won and lost on dispersion; its misses are all in the levels.

Run directories (`<worktree>/.private/t6/<name>`, logs in `$Q/.review/r10/D/<name>.log`,
`.json` cell dumps in the same scratch): `pool_panel`, `pd_long`, `pd_short`,
`prior_trading`, and the shipped cache `data/processed/replication/vol_common_t6_book`.

## 4. Where the loss comes from

The gap is entirely in the levels, and it is a level gap of the *draw*, not of the accounting:
our random pairs lose 1.5-3 times what the paper's lose per month at matching dispersion (2.13%
against 2.30% on A|employed|std top20, 2.15% against 2.26% on 101-120, 1.01% against 1.20% on
the all-120 column). Three candidates were open after the caption, and each is now measured:

1. **The cross-decile tilt.** Because 72-87% of true pairs have their two legs in different
   prior-month deciles, and because the leg the rule buys is usually the lower-return one (the
   mean signed decile gap between the true legs is -0.3 to -0.9 deciles across 1963-2002, with
   the long leg in the lower decile in 48-60% of pairs), the shipped leg-by-leg draw builds
   random pairs that are long the laggard decile and short the winner decile. R-C removes the
   tilt by drawing both legs from one decile, and the level does not improve: the fully invested
   mean moves from -0.2033% to -0.2246% (top 5) and from -0.3397% to -0.3840% (all 120). The
   tilt is not the source of the loss.
2. **The drawn-leg exits.** Two details the bootstrap section leaves to the paper's delisting
   sentence (p. 804) touch 2.7% of positions: 1.68% of random positions are closed early at a
   drawn leg's delisting or last available row, and 0.99% are dropped because a drawn leg has no
   price on the opening day (summed over the 474 cohorts and both waits, from the run
   statistics). D3 (`--complete-legs`, which draws only stocks with a return on every day of the
   trade) measured 13.0 of 48 at 50 replications, the same as the shipped run's 12.5-13.0, so
   removing them from the draw does not move the level either.
3. **The decile month.** R-B, the caption's "on the day the position is opened", is the only
   reading measured here that improves the level: -0.1514% against -0.2033% on A|employed|mean
   top 5, -0.2772% against -0.3397% on the all-120 column. It does not raise the block (13.0,
   6 / 14 / 28), because the tighter 21-day ranking also shrinks the dispersion, and three
   committed standard-deviation cells that were checks (2.33 / 1.16 / 1.20 against the paper's
   2.64 / 1.36 / 1.44) become tildes.

What remains unexplained is the level of a *uniform* draw from the same universe; no construction
choice measured here, in this round or in the four earlier ones, moves it by more than a third of
the gap.

## 5. T21's real remaining room

T21 said "+0.5 at most" and flagged it as a guess. Measured on the current 48-cell block at 200
replications, the room is **+1.0 of 48** (implied 412.0 of 865), and only through readings the
text does not support:

- **R-A, the panel decile population, +1.0.** It buys 11 dispersion marks and loses 5 level marks;
  every one of the 16 mean cells and all 16 median cells are crosses, and the level gap doubles.
  The paper's deciles are deciles of its own sample, and that sample is the liquid universe it
  screens at p. 803, not every share CRSP carries. A reading that doubles the miss it is supposed
  to explain is a fit to the dispersion rows, not a replication.
- **R-C, one decile per pair, +1.0.** Four cells move inside the mark tolerance and nothing else
  does, and the level is worse. Its mirror image (R-D, the short leg's decile) scores 12.0, so the
  same reading moves the block from 12.0 to 14.0 depending on which decile is picked: the reading
  has no anchor and the +1.0 is the choice of decile. "Replace the actual stocks" (p. 818) is leg by
  leg.
- **R-B, the trading-prior month, 0.0.** The best-supported reading left on the table is
  score-neutral: it trades one mean check and one median tilde for three standard-deviation
  checks, and improves the level. It is the only one of the four that a reader of p. 819 could
  defend against the shipped calendar month, and it is worth no points.

So T21's real room is **+1.0 of 48 = +1.0 of 865 (411.0 -> 412.0), achieved only by readings whose
central quantity gets worse**, and 0.0 by text-supported readings. The same class of unsupported
convention can also lose a point (R-D, 410.0), which is the honest measure of how much of this
block's tally is construction choice: plus or minus one mark out of 48, with the level gap
untouched. The guess of +0.5 was, if anything, generous. The block is not under-determined by the paper's words: it is a level
difference between our random draws and the paper's, and the paper does not publish the draws
(GAPS.md section 2, class I).

## 6. What is left open, and what is not

Nothing text-supported is left untried. Twelve choices are listed in section 2: five are fixed by
a quoted sentence (the trigger, the closing event, the delisting close, the capital basis, the
value weighting), four are measured (the decile population, the breakpoints, the decile month,
the within-decile draw), one is measured this round (the decile matching), one is measured and
neutral (the replication average), and one is stated (the columns, waits and replication count).

Three choices are recorded as open but would not be measured again without a new sentence:

- **NYSE breakpoints** have no sentence behind them; the paper's deciles are deciles of its own
  liquid sample, and its one use of CRSP breakpoints is for *size* deciles in Table 2 (p. 809),
  not for the bootstrap.
- **Holding a random position open past a drawn leg's delisting** is refused by p. 804, which
  closes the position in that pair at the delisting return or the last available price.
- **A distance-weighted draw inside the decile** is refused by "Similarity is defined as coming
  from the same decile" (pp. 818-819): the paper defines similarity as membership, so the draw is
  uniform over the decile, which is what D2 (`--draw-near 10`) measured at 12.0 of 48 (`REVIEW_NOTES` 75).

One artefact is worth recording for whoever reads the cells next: `A|employed|mean|top5` needs a
mean of -0.00137 to be marked, a 10% band of 1.4 basis points per month on a series with a 5.5%
monthly standard deviation. The 200-replication average of a draw is stable to well under that,
but the paper's own -0.00137 is a single market path's realisation, so a level cell near zero can
move two marks on a 5% change in the draw. That is why the block's tally (13.0-14.0) is a weak
signal and the level table in section 3 is the honest reading.

## Reproducing

    Q=$(git rev-parse --show-toplevel)
    R=$Q/data/processed/replication
    OMP_NUM_THREADS=1 $Q/.venv/bin/python scripts/claims/table6_random_pairs.py --mode run \
        --cache-root $R/vol_common --out-root <worktree>/.private/t6/<name> --reps 200 \
        --workers 6 --committed-capital book-share <the option>
    $Q/.venv/bin/python scripts/claims/t6_score.py <worktree>/.private/t6/<name>

`scripts/claims/t6_score.py` re-collects the 48 cells exactly as
`scripts/03_replicate.py::table6_from_cache` does and marks them with the driver's own `_mark`,
because the driver refuses any run whose stamp is not `--close true`; the draw options measured
here (`--pool`, `--prior-month`, `--pair-decile`) all keep the primary close rule, so the only
thing standing between them and a `--table6-cache` line is that refusal. On the shipped cache the
scorer prints 13.0 (8 / 10 / 30) and the implied total 411.0, which is its own control.