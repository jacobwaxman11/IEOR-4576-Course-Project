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
| A. No waiting | Fully invested | mean | -0.00159 / -0.00137 ~ | -0.00227 / -0.00111 ✗ | -0.00228 / -0.00105 ✗ | -0.00244 / -0.00113 ✗ |
| A. No waiting | Fully invested | std | 0.03500 / 0.05521 ✗ | 0.01843 / 0.02295 ~ | 0.01915 / 0.02264 ~ | 0.00845 / 0.01200 ✗ |
| A. No waiting | Fully invested | median | -0.00172 / -0.00192 ~ | -0.00215 / -0.00153 ✗ | -0.00229 / -0.00156 ✗ | -0.00230 / -0.00162 ✗ |
| A. No waiting | Committed capital | mean | -0.00126 / -0.00083 ✗ | -0.00171 / -0.00077 ✗ | -0.00179 / -0.00089 ✗ | -0.00184 / -0.00091 ✗ |
| A. No waiting | Committed capital | std | 0.02222 / 0.02635 ~ | 0.01147 / 0.01358 ~ | 0.01204 / 0.01443 ~ | 0.00554 / 0.00760 ✗ |
| A. No waiting | Committed capital | median | -0.00131 / -0.00123 ✓ | -0.00163 / -0.00100 ✗ | -0.00179 / -0.00123 ✗ | -0.00174 / -0.00122 ✗ |
| B. Wait one day | Fully invested | mean | -0.00145 / -0.00177 ~ | -0.00219 / -0.00004 ✗ | -0.00232 / -0.00154 ✗ | -0.00249 / -0.00156 ✗ |
| B. Wait one day | Fully invested | std | 0.03503 / 0.05966 ✗ | 0.01851 / 0.05310 ✗ | 0.01895 / 0.02404 ~ | 0.00842 / 0.01213 ✗ |
| B. Wait one day | Fully invested | median | -0.00151 / -0.00241 ✗ | -0.00213 / -0.00172 ~ | -0.00237 / -0.00206 ~ | -0.00234 / -0.00201 ~ |
| B. Wait one day | Committed capital | mean | -0.00118 / -0.00103 ~ | -0.00166 / -0.00094 ✗ | -0.00179 / -0.00112 ✗ | -0.00186 / -0.00112 ✗ |
| B. Wait one day | Committed capital | std | 0.02244 / 0.02811 ~ | 0.01158 / 0.01363 ~ | 0.01191 / 0.01449 ~ | 0.00552 / 0.00761 ✗ |
| B. Wait one day | Committed capital | median | -0.00131 / -0.00152 ~ | -0.00160 / -0.00118 ✗ | -0.00185 / -0.00148 ✗ | -0.00173 / -0.00139 ~ |

## 5. Effect against our own baseline

The claim test compares our change with the paper's change, because our levels
differ from the paper's for known reasons (an era split in the stock universe,
return tails). "Ours true" is our true-pair mean rebuilt from the cached trade
log; "ours random" the bootstrap mean; the difference next to the paper's own
Table 1 minus Table 6 difference. The last column is our difference over the
paper's; Table 1 prints no column for the top 120 pairs, so that ratio is n/a.

| Panel | Capital | Portfolio | ours true | ours random | ours diff | paper true | paper random | paper diff | ours / paper |
|---|---|---|---|---|---|---|---|---|---|
| A | employed | top5 | 1.273% | -0.159% | 1.432% | 1.308% | -0.137% | 1.445% | 0.99 |
| A | employed | top20 | 1.387% | -0.227% | 1.614% | 1.436% | -0.111% | 1.547% | 1.04 |
| A | employed | 101-120 | 0.968% | -0.228% | 1.197% | 1.081% | -0.105% | 1.186% | 1.01 |
| A | employed | top120 | 1.238% | -0.244% | 1.483% | n/a | -0.113% | n/a | n/a |
| A | committed | top5 | 0.751% | -0.126% | 0.877% | 0.784% | -0.083% | 0.867% | 1.01 |
| A | committed | top20 | 0.807% | -0.171% | 0.979% | 0.805% | -0.077% | 0.882% | 1.11 |
| A | committed | 101-120 | 0.597% | -0.179% | 0.776% | 0.679% | -0.089% | 0.768% | 1.01 |
| A | committed | top120 | 0.740% | -0.184% | 0.924% | n/a | -0.091% | n/a | n/a |
| B | employed | top5 | 0.723% | -0.145% | 0.869% | 0.745% | -0.177% | 0.922% | 0.94 |
| B | employed | top20 | 0.891% | -0.219% | 1.111% | 0.895% | -0.004% | 0.899% | 1.24 |
| B | employed | 101-120 | 0.764% | -0.232% | 0.996% | 0.795% | -0.154% | 0.949% | 1.05 |
| B | employed | top120 | 0.902% | -0.249% | 1.151% | n/a | -0.156% | n/a | n/a |
| B | committed | top5 | 0.430% | -0.118% | 0.548% | 0.463% | -0.103% | 0.566% | 0.97 |
| B | committed | top20 | 0.521% | -0.166% | 0.687% | 0.520% | -0.094% | 0.614% | 1.12 |
| B | committed | 101-120 | 0.467% | -0.179% | 0.646% | 0.503% | -0.112% | 0.615% | 1.05 |
| B | committed | top120 | 0.540% | -0.186% | 0.726% | n/a | -0.112% | n/a | n/a |

Standard deviations, random against true: the paper's claim is that the random
pairs are much noisier ("poorly matched").

| Panel | Capital | Portfolio | true SD | random SD | random / true |
|---|---|---|---|---|---|
| A | employed | top5 | 2.312% | 3.500% | 1.51 |
| A | employed | top20 | 1.670% | 1.843% | 1.10 |
| A | employed | 101-120 | 1.522% | 1.915% | 1.26 |
| A | employed | top120 | 1.206% | 0.845% | 0.70 |
| A | committed | top5 | 1.476% | 2.222% | 1.51 |
| A | committed | top20 | 1.053% | 1.147% | 1.09 |
| A | committed | 101-120 | 1.028% | 1.204% | 1.17 |
| A | committed | top120 | 0.796% | 0.554% | 0.70 |
| B | employed | top5 | 2.019% | 3.503% | 1.74 |
| B | employed | top20 | 1.474% | 1.851% | 1.26 |
| B | employed | 101-120 | 1.455% | 1.895% | 1.30 |
| B | employed | top120 | 1.088% | 0.842% | 0.77 |
| B | committed | top5 | 1.309% | 2.244% | 1.71 |
| B | committed | top20 | 0.936% | 1.158% | 1.24 |
| B | committed | 101-120 | 0.979% | 1.191% | 1.22 |
| B | committed | top120 | 0.715% | 0.552% | 0.77 |

True minus random, replication by replication:

| Panel | Capital | Portfolio | mean(true - random) | t (mean) | t (worst rep) | reps with a positive mean | reps with t > 2 |
|---|---|---|---|---|---|---|---|
| A | employed | top5 | 1.432% | 6.66 | 3.79 | 100% | 100.0% |
| A | employed | top20 | 1.614% | 11.04 | 8.62 | 100% | 100.0% |
| A | employed | 101-120 | 1.197% | 10.11 | 7.54 | 100% | 100.0% |
| A | employed | top120 | 1.483% | 16.83 | 15.33 | 100% | 100.0% |
| A | committed | top5 | 0.877% | 6.49 | 3.90 | 100% | 100.0% |
| A | committed | top20 | 0.979% | 11.24 | 9.28 | 100% | 100.0% |
| A | committed | 101-120 | 0.776% | 10.27 | 7.31 | 100% | 100.0% |
| A | committed | top120 | 0.924% | 16.34 | 14.91 | 100% | 100.0% |
| B | employed | top5 | 0.869% | 4.55 | 2.14 | 100% | 100.0% |
| B | employed | top20 | 1.111% | 8.94 | 5.69 | 100% | 100.0% |
| B | employed | 101-120 | 0.996% | 8.91 | 6.13 | 100% | 100.0% |
| B | employed | top120 | 1.151% | 14.84 | 12.65 | 100% | 100.0% |
| B | committed | top5 | 0.548% | 4.47 | 1.87 | 100% | 99.5% |
| B | committed | top20 | 0.687% | 9.03 | 6.14 | 100% | 100.0% |
| B | committed | 101-120 | 0.646% | 9.03 | 6.32 | 100% | 100.0% |
| B | committed | top120 | 0.726% | 14.55 | 12.51 | 100% | 100.0% |

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

Cells within 10% of the paper: 1 of 48 (2%). Within 25%: 40%.

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
