# Table 6: returns to random pairs sorted on prior one-month return

Claim: Gatev, Goetzmann and Rouwenhorst (2006), section 3.6 and Table 6
(article p. 818, text p. 819). Bootstrap of the pairs rule on random pairs;
48 cells: two panels (A no waiting, B wait one day), fully invested and
committed capital, mean / standard deviation / median, four portfolios
(top 5, top 20, top 100-120, all 120 top pairs), 200 replications.

## 1. What the paper says

> The starting point of the bootstrap is the set of historical dates on which
> the various pairs open. In each bootstrap we replace the actual stocks with
> two random securities with similar prior one-month returns as the stocks in
> the actual pair. Similarity is defined as coming from the same decile of
> previous month's performance. ... We bootstrapped the entire set of trading
> dates 200 times. The results are summarized in Table 6. On average we find
> that the returns on the bootstrapped pairs are well below the true pairs
> returns. In fact, the excess returns to the simulated pairs are slightly
> negative, and the standard deviations of the returns are large relative to
> the true pairs, which is a reflection of the fact that the simulated pairs
> are poorly matched.

Table 6 caption: "Bootstrap of random pairs traded according to the rule that
opens a position in a random pair when the stocks in the true pair diverge by
two historical standard deviations and closes the position after the next
crossing of prices. The random stocks are selected within the same last-month
performance decile on the day the position is opened. The top panel gives
summary statistics of the monthly excess returns on value-weighted portfolios
of n pairs of stocks where the position is opened immediately. The last column
is a portfolio of all 120 top pairs. The bottom panel summarizes the
performance with one day waiting before the position is opened. The statistics
are computed over 200 replications of the bootstrapped sample."

## 2. Method

For every opening in the shipped cohort cache (w0_trades.parquet for Panel A,
w1_trades.parquet for Panel B) each leg is replaced by a stock drawn uniformly
from the cohort's formation universe inside the decile of the previous calendar
month's CRSP return (mthret) that the leg occupies, excluding the two true legs
and the other drawn stock; the draw is mapped from the month's return-sorted
position to the return-matrix column. The random pair is opened at the true
pair's opening day, $1 each, with each drawn stock kept in its true leg's role
(the true long leg's replacement is bought, the true short leg's replacement
sold short); the paper replaces "the actual stocks" of the pair and does not
say the random pair is re-ordered by price at the open. It is closed on its
own next price crossing, or early on a delisting, a leg's last available row
or the end of the trading period. Accounting, portfolio
construction and monthly compounding use the shipped engine's conventions
(paper eqq. 2-3, the pipeline's --short-weights position, cohort_monthly, then
the overlap average across cohorts).

Choices where the paper is silent, and the reading used:

| decision | reading | why |
|---|---|---|
| universe for the draw | the cohort's formation universe | the true pairs are formed there |
| decile population | that universe's cross-section of mthret in the prior month | "same decile of previous month's performance" |
| prior month | calendar month before the opening date (for a first-month open, the last filing month before trading) | "previous month" |
| open date and size | the true pair's opening day; each drawn stock keeps its true leg's long/short role ($1 each) | "the set of historical dates on which the pairs open"; "we replace the actual stocks" |
| close | the random pair's own next crossing; forced exits on delisting, last row, period end | "after the next crossing of prices" |
| accounting | buy-and-hold $1 legs, eq. (2) payoff, eq. (3) short weight floored at zero | the pipeline's conventions |
| portfolios | ranks 1-5, 1-20, 101-120, 1-120 of each cohort's ranking | Table 6's columns; "All 120" is the top 120 pairs |
| replications | 200, fixed seed | the paper's count; reproducible |
| drawn legs with no price after the open | no position | the engine cannot trade a stock with no row |

474 cohorts, 200 replications, 474 strategy months, 217851 opening events, 12 events with no prior-month decile, 431050 with no price after the open.

## 3. Control run: the same code with the effect switched off

The control prices the cached trade log with this script's accounting (each leg
substituted by itself) and compares it with the shipped monthly series.

| check | result |
|---|---|
| cohort-waits compared | 948 |
| cells compared | 5688 |
| max abs diff, rebuilt vs shipped monthly returns | 0.000e+00 |
| max abs diff, vectorised layer vs project layer | 1.332e-15 |
| max abs diff, trade payoff vs cached payoff | 1.066e-14 |

## 4. Our Table 6 next to the paper's

Cells are ours / paper, a tick within 10% of the paper, ~ within 25%, x further
(the same rule as REPLICATION_CHECK.md; these marks are not counted in the
replication score). "Ours" averages each statistic over replications.

| Panel | Block | Statistic | Top 5 | Top 20 | Top 100-120 | All 120 |
|---|---|---|---|---|---|---|
| A. No waiting | Fully invested | mean | -0.00233 / -0.00137 ✗ | -0.00246 / -0.00111 ✗ | -0.00252 / -0.00105 ✗ | -0.00248 / -0.00113 ✗ |
| A. No waiting | Fully invested | std | 0.03477 / 0.05521 ✗ | 0.01828 / 0.02295 ~ | 0.01892 / 0.02264 ~ | 0.00833 / 0.01200 ✗ |
| A. No waiting | Fully invested | median | -0.00291 / -0.00192 ✗ | -0.00247 / -0.00153 ✗ | -0.00264 / -0.00156 ✗ | -0.00234 / -0.00162 ✗ |
| A. No waiting | Committed capital | mean | -0.00160 / -0.00083 ✗ | -0.00179 / -0.00077 ✗ | -0.00189 / -0.00089 ✗ | -0.00185 / -0.00091 ✗ |
| A. No waiting | Committed capital | std | 0.02206 / 0.02635 ~ | 0.01141 / 0.01358 ~ | 0.01193 / 0.01443 ~ | 0.00548 / 0.00760 ✗ |
| A. No waiting | Committed capital | median | -0.00182 / -0.00123 ✗ | -0.00176 / -0.00100 ✗ | -0.00192 / -0.00123 ✗ | -0.00175 / -0.00122 ✗ |
| B. Wait one day | Fully invested | mean | -0.00223 / -0.00177 ✗ | -0.00238 / -0.00004 ✗ | -0.00256 / -0.00154 ✗ | -0.00253 / -0.00156 ✗ |
| B. Wait one day | Fully invested | std | 0.03525 / 0.05966 ✗ | 0.01831 / 0.05310 ✗ | 0.01872 / 0.02404 ~ | 0.00830 / 0.01213 ✗ |
| B. Wait one day | Fully invested | median | -0.00272 / -0.00241 ~ | -0.00245 / -0.00172 ✗ | -0.00273 / -0.00206 ✗ | -0.00237 / -0.00201 ~ |
| B. Wait one day | Committed capital | mean | -0.00152 / -0.00103 ✗ | -0.00174 / -0.00094 ✗ | -0.00190 / -0.00112 ✗ | -0.00187 / -0.00112 ✗ |
| B. Wait one day | Committed capital | std | 0.02236 / 0.02811 ~ | 0.01147 / 0.01363 ~ | 0.01181 / 0.01449 ~ | 0.00546 / 0.00761 ✗ |
| B. Wait one day | Committed capital | median | -0.00184 / -0.00152 ~ | -0.00174 / -0.00118 ✗ | -0.00199 / -0.00148 ✗ | -0.00174 / -0.00139 ✗ |

## 5. Effect against our own baseline

The claim test compares our change with the paper's change, because our levels
differ from the paper's for known reasons (an era split in the stock universe,
return tails). "Ours true" is our true-pair mean rebuilt from the cached trade
log; "ours random" the bootstrap mean; the difference next to the paper's own
Table 1 minus Table 6 difference. The last column is our difference over the
paper's; Table 1 prints no column for the top 120 pairs, so that ratio is n/a.

| Panel | Capital | Portfolio | ours true | ours random | ours diff | paper true | paper random | paper diff | ours / paper |
|---|---|---|---|---|---|---|---|---|---|
| A | employed | top5 | 1.257% | -0.233% | 1.490% | 1.308% | -0.137% | 1.445% | 1.03 |
| A | employed | top20 | 1.383% | -0.246% | 1.629% | 1.436% | -0.111% | 1.547% | 1.05 |
| A | employed | 101-120 | 0.957% | -0.252% | 1.209% | 1.081% | -0.105% | 1.186% | 1.02 |
| A | employed | top120 | 1.237% | -0.248% | 1.484% | n/a | -0.113% | n/a | n/a |
| A | committed | top5 | 0.741% | -0.160% | 0.901% | 0.784% | -0.083% | 0.867% | 1.04 |
| A | committed | top20 | 0.803% | -0.179% | 0.983% | 0.805% | -0.077% | 0.882% | 1.11 |
| A | committed | 101-120 | 0.593% | -0.189% | 0.782% | 0.679% | -0.089% | 0.768% | 1.02 |
| A | committed | top120 | 0.739% | -0.185% | 0.924% | n/a | -0.091% | n/a | n/a |
| B | employed | top5 | 0.691% | -0.223% | 0.914% | 0.745% | -0.177% | 0.922% | 0.99 |
| B | employed | top20 | 0.879% | -0.238% | 1.117% | 0.895% | -0.004% | 0.899% | 1.24 |
| B | employed | 101-120 | 0.749% | -0.256% | 1.004% | 0.795% | -0.154% | 0.949% | 1.06 |
| B | employed | top120 | 0.896% | -0.253% | 1.149% | n/a | -0.156% | n/a | n/a |
| B | committed | top5 | 0.416% | -0.152% | 0.568% | 0.463% | -0.103% | 0.566% | 1.00 |
| B | committed | top20 | 0.514% | -0.174% | 0.688% | 0.520% | -0.094% | 0.614% | 1.12 |
| B | committed | 101-120 | 0.461% | -0.190% | 0.650% | 0.503% | -0.112% | 0.615% | 1.06 |
| B | committed | top120 | 0.537% | -0.187% | 0.724% | n/a | -0.112% | n/a | n/a |

Standard deviations, random against true: the paper's claim is that the random
pairs are much noisier ("poorly matched").

| Panel | Capital | Portfolio | true SD | random SD | random / true |
|---|---|---|---|---|---|
| A | employed | top5 | 2.369% | 3.477% | 1.47 |
| A | employed | top20 | 1.697% | 1.828% | 1.08 |
| A | employed | 101-120 | 1.528% | 1.892% | 1.24 |
| A | employed | top120 | 1.214% | 0.833% | 0.69 |
| A | committed | top5 | 1.491% | 2.206% | 1.48 |
| A | committed | top20 | 1.063% | 1.141% | 1.07 |
| A | committed | 101-120 | 1.031% | 1.193% | 1.16 |
| A | committed | top120 | 0.802% | 0.548% | 0.68 |
| B | employed | top5 | 2.039% | 3.525% | 1.73 |
| B | employed | top20 | 1.481% | 1.831% | 1.24 |
| B | employed | 101-120 | 1.440% | 1.872% | 1.30 |
| B | employed | top120 | 1.077% | 0.830% | 0.77 |
| B | committed | top5 | 1.316% | 2.236% | 1.70 |
| B | committed | top20 | 0.938% | 1.147% | 1.22 |
| B | committed | 101-120 | 0.970% | 1.181% | 1.22 |
| B | committed | top120 | 0.710% | 0.546% | 0.77 |

True minus random, replication by replication:

| Panel | Capital | Portfolio | mean(true - random) | t (mean) | t (worst rep) | reps with a positive mean | reps with t > 2 |
|---|---|---|---|---|---|---|---|
| A | employed | top5 | 1.490% | 6.94 | 4.30 | 100% | 100.0% |
| A | employed | top20 | 1.629% | 11.03 | 8.76 | 100% | 100.0% |
| A | employed | 101-120 | 1.209% | 10.21 | 7.71 | 100% | 100.0% |
| A | employed | top120 | 1.484% | 16.64 | 15.23 | 100% | 100.0% |
| A | committed | top5 | 0.901% | 6.70 | 4.16 | 100% | 100.0% |
| A | committed | top20 | 0.983% | 11.25 | 9.31 | 100% | 100.0% |
| A | committed | 101-120 | 0.782% | 10.33 | 7.38 | 100% | 100.0% |
| A | committed | top120 | 0.924% | 16.19 | 14.69 | 100% | 100.0% |
| B | employed | top5 | 0.914% | 4.79 | 2.32 | 100% | 100.0% |
| B | employed | top20 | 1.117% | 9.01 | 5.62 | 100% | 100.0% |
| B | employed | 101-120 | 1.004% | 9.09 | 6.34 | 100% | 100.0% |
| B | employed | top120 | 1.149% | 14.83 | 12.75 | 100% | 100.0% |
| B | committed | top5 | 0.568% | 4.65 | 1.88 | 100% | 99.5% |
| B | committed | top20 | 0.688% | 9.08 | 6.06 | 100% | 100.0% |
| B | committed | 101-120 | 0.650% | 9.17 | 6.43 | 100% | 100.0% |
| B | committed | top120 | 0.724% | 14.53 | 12.57 | 100% | 100.0% |

## 6. Verdict

| criterion | met |
|---|---|
| random-pair means are negative in at least 14 of 16 series | yes |
| random-pair means sit below the true pairs in all 16 series | yes |
| random-pair standard deviations exceed the true ones in all 16 series | no |
| the true-minus-random difference has t > 2 in all 16 series | yes |
| the difference is positive in the paper's eight Table 1 columns | yes |
| the difference is within 25% of the paper's everywhere it is defined | yes |

**Verdict: replicated in substance.**

Cells within 10% of the paper: 0 of 48 (0%). Within 25%: 25%.

The standard-deviation criterion is the one that does not hold in every column: in the top-120 column the random pairs are quieter than the true pairs, while in the top-5, top-20 and top-100-120 columns they are noisier, as the paper describes. The mean, the negative random-pair level and the true-minus-random difference behave as the paper says in all sixteen series.

## 7. Limitations

- The draw is uniform inside the decile, so it ignores every other attribute
 (size, industry, volatility) that also drives the true mates apart; that is
 the paper's design, and it is why the random pairs should be poorly matched.
- Deciles are formed on the formation universe's cross-section, not on all CRSP
 stocks; the paper does not say which population it used.
- The bootstrap trades every true opening, including the second and later
 round trips of a pair, and each draw is a fresh pair (the paper does not say
 whether stocks are resampled per opening or per pair).
- Because a random pair closes on its own crossing, a later opening of the same
 rank can arrive while an earlier random position is still open; the two are
 then held together in that rank's book (the true-pair rule re-opens a pair
 only after it has closed).
- A random leg with no price after the opening day produces no position.
- The random pair closes on its own crossing; closing on the true pair's date
 is equally literal and is not computed here.
- The significance test is a Newey-West t of the monthly true-minus-random
 series, averaged over replications, not the paper's own (unreported) test.

## 8. How to regenerate

One command rebuilds everything below from a clean checkout (about 15 minutes
with eight workers); the four steps are the same one-liners:

    # 1. control: rebuilds the true series from the cached trade log
    python scripts/claims/table6_random_pairs.py --mode control --out-root scratch/t6control \
        > scratch/t6control.log 2>&1
    # 2. the control summary as JSON, read by the report
    python scripts/claims/t6_control_json.py scratch/t6control.log scratch/t6run/control.json
    # 3. the bootstrap: 200 replications over 474 cohorts, eight subprocess shards
    python scripts/claims/table6_random_pairs.py --mode run --reps 200 --workers 8 \
        --out-root scratch/t6run
    # 4. the report and its CSV (also checks the paper targets against the PDF)
    python scripts/claims/table6_random_pairs.py --mode report --reps 200 \
        --out-root scratch/t6run

The report reads the control numbers from scratch/t6run/control.json; without it
the control section says so instead of quoting a stale number. Unit tests:
``python -m pytest tests/test_table6.py -q``.
