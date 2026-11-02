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
say the random pair is re-ordered by price at the open. It is closed when the
true trade it replaces closes, at the true pair's next price crossing (or the
end of the trading period), or earlier if a drawn stock delists or its data
end. Open and close are the true pair's signals, so the random trade differs
from the true trade only in the stocks held. Accounting, portfolio
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
| close | with the true trade it replaces (the true pair's next crossing, or period end); earlier only on a drawn stock's delisting or last row | the caption ties the open to "the stocks in the true pair" and closes "after the next crossing of prices"; the dates come from the true trades ("the set of historical dates on which the various pairs open", "the entire set of trading dates") |
| accounting | buy-and-hold $1 legs, eq. (2) payoff, eq. (3) short weight floored at zero | the pipeline's conventions |
| portfolios | ranks 1-5, 1-20, 101-120, 1-120 of each cohort's ranking | Table 6's columns; "All 120" is the top 120 pairs |
| replications | 200, fixed seed | the paper's count; reproducible |
| drawn legs with no price after the open | no position | the engine cannot trade a stock with no row |

{{META}}

## 3. Control run: the same code with the effect switched off

The control prices the cached trade log with this script's accounting (each leg
substituted by itself) and compares it with the shipped monthly series.

{{CONTROL}}

## 4. Our Table 6 next to the paper's

Cells are ours / paper, a tick within 10% of the paper, ~ within 25%, x further
(the same rule as REPLICATION_CHECK.md; these marks are not counted in the
replication score). "Ours" averages each statistic over replications.

{{TABLE6}}

## 5. Effect against our own baseline

The claim test compares our change with the paper's change, because our levels
differ from the paper's for known reasons (an era split in the stock universe,
return tails). "Ours true" is our true-pair mean rebuilt from the cached trade
log; "ours random" the bootstrap mean; the difference next to the paper's own
Table 1 minus Table 6 difference. The last column is our difference over the
paper's; Table 1 prints no column for the top 120 pairs, so that ratio is n/a.

{{EFFECT}}

Standard deviations, random against true: the paper's claim is that the random
pairs are much noisier ("poorly matched").

{{SPREAD}}

True minus random, replication by replication:

{{DIFF}}

## 6. Verdict

{{VERDICT}}

## 7. Limitations

- The draw is uniform inside the decile, so it ignores every other attribute
 (size, industry, volatility) that also drives the true mates apart; that is
 the paper's design, and it is why the random pairs should be poorly matched.
- Deciles are formed on the formation universe's cross-section, not on all CRSP
 stocks; the paper does not say which population it used.
- The bootstrap trades every true opening, including the second and later
 round trips of a pair, and each draw is a fresh pair (the paper does not say
 whether stocks are resampled per opening or per pair).
- A random leg with no price after the opening day produces no position.
- The caption does not say whose crossing closes the random position. Closing
 on the drawn stocks' own next crossing (`--close own`) is the measured
 alternative: random means -0.16 / -0.23 / -0.23 / -0.24% without the wait,
 standard deviations 3.5 / 1.8 / 1.9 / 0.8%, and the claim holds as well
 (REVIEW_NOTES section 54). A third reading, trading the drawn stocks on their
 own 2-sigma rule, contradicts the caption's open and does not diversify like
 the paper's random pairs (top-120 standard deviation 3.1% against 1.2%).
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
