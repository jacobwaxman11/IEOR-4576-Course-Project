Source specification: `baseline`; cache settings: `{"delayed_entry": "execute", "exclude_constant": true, "exclude_same_issuer": true, "format": 7, "idle_policy": "opened", "issuer_source": "c02881d64d10bc6f1170ec8e1ca893f799244c48bed7b610f7e6230bc0721d7e", "max_stale_share": 0.95, "monthly_aggregation": "books", "normalization": "continued", "short_weights": "value", "sic_fallback": "formation_end", "telephone_sic": "4811", "trigger_sigma": "rms", "universe": "vol_common"}`.

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
say the random pair is re-ordered by price at the open. This run uses
`--close true`: the true trade’s close date, capped by earlier delisting or data-end exits. Accounting, portfolio
construction and monthly compounding use the shipped engine's conventions
(paper eqq. 2-3, the pipeline's --short-weights value, separately compounded books, then
the overlap average across cohorts).

Choices where the paper is silent, and the reading used:

| decision | reading | why |
|---|---|---|
| universe for the draw | the cohort's formation universe | the true pairs are formed there |
| decile population | that universe's cross-section of mthret in the prior month | "same decile of previous month's performance" |
| prior month | calendar month before the opening date (for a first-month open, the last filing month before trading) | "previous month" |
| open date and size | the true pair's opening day; each drawn stock keeps its true leg's long/short role ($1 each) | "the set of historical dates on which the pairs open"; "we replace the actual stocks" |
| close | the true trade’s close date, capped by earlier delisting or data-end exits (`--close true`) | "after the next crossing of prices" |
| accounting | buy-and-hold $1 legs, eq. (2) payoff, shorted-security value weights, with zero idle cash returns | the pipeline's conventions |
| portfolios | ranks 1-5, 1-20, 101-120, 1-120 of each cohort's ranking | Table 6's columns; "All 120" is the top 120 pairs |
| replications | 200, fixed seed | the paper's count; reproducible |
| drawn legs with no price after the open | no position | the engine cannot trade a stock with no row |

474 cohorts, 200 replications, 474 strategy months, 218295 opening events, 12 events with no prior-month decile, 431944 with no price after the open.

## 3. Control run: the same code with the effect switched off

The control prices the cached trade log with this script's accounting (each leg
substituted by itself) and compares it with the shipped monthly series.

| check | result |
|---|---|
| cohort-waits compared | 948 |
| cells compared | 7584 |
| max abs diff, rebuilt vs shipped monthly returns | 0.000e+00 |
| max abs diff, vectorised layer vs project layer | 1.332e-15 |
| max abs diff, trade payoff vs cached payoff | 1.066e-14 |

## 4. Our Table 6 next to the paper's

Cells are ours / paper, a tick within 10% of the paper, ~ within 25%, x further
(the same rule as REPLICATION_CHECK.md; these marks are not counted in the
replication score). "Ours" averages each statistic over replications.

| Panel | Block | Statistic | Top 5 | Top 20 | Top 100-120 | All 120 |
|---|---|---|---|---|---|---|
| A. No waiting | Fully invested | mean | 0.00012 / -0.00137 ✗ | -0.00000 / -0.00111 ✗ | 0.00026 / -0.00105 ✗ | 0.00018 / -0.00113 ✗ |
| A. No waiting | Fully invested | std | 0.04131 / 0.05521 ✗ | 0.02052 / 0.02295 ~ | 0.02070 / 0.02264 ✓ | 0.00858 / 0.01200 ✗ |
| A. No waiting | Fully invested | median | -0.00003 / -0.00192 ✗ | 0.00005 / -0.00153 ✗ | 0.00015 / -0.00156 ✗ | 0.00015 / -0.00162 ✗ |
| A. No waiting | Committed capital | mean | 0.00004 / -0.00083 ✗ | -0.00004 / -0.00077 ✗ | 0.00004 / -0.00089 ✗ | 0.00004 / -0.00091 ✗ |
| A. No waiting | Committed capital | std | 0.02374 / 0.02635 ✓ | 0.01200 / 0.01358 ~ | 0.01268 / 0.01443 ~ | 0.00525 / 0.00760 ✗ |
| A. No waiting | Committed capital | median | 0.00006 / -0.00123 ✗ | -0.00009 / -0.00100 ✗ | 0.00000 / -0.00123 ✗ | -0.00000 / -0.00122 ✗ |
| B. Wait one day | Fully invested | mean | 0.00010 / -0.00177 ✗ | 0.00011 / -0.00004 ✗ | 0.00030 / -0.00154 ✗ | 0.00015 / -0.00156 ✗ |
| B. Wait one day | Fully invested | std | 0.04114 / 0.05966 ✗ | 0.02062 / 0.05310 ✗ | 0.02049 / 0.02404 ~ | 0.00852 / 0.01213 ✗ |
| B. Wait one day | Fully invested | median | 0.00010 / -0.00241 ✗ | 0.00015 / -0.00172 ✗ | 0.00013 / -0.00206 ✗ | 0.00007 / -0.00201 ✗ |
| B. Wait one day | Committed capital | mean | 0.00007 / -0.00103 ✗ | 0.00002 / -0.00094 ✗ | 0.00008 / -0.00112 ✗ | 0.00003 / -0.00112 ✗ |
| B. Wait one day | Committed capital | std | 0.02364 / 0.02811 ~ | 0.01202 / 0.01363 ~ | 0.01257 / 0.01449 ~ | 0.00519 / 0.00761 ✗ |
| B. Wait one day | Committed capital | median | -0.00003 / -0.00152 ✗ | 0.00002 / -0.00118 ✗ | 0.00000 / -0.00148 ✗ | -0.00001 / -0.00139 ✗ |

## 5. Effect against our own baseline

The claim test compares our change with the paper's change, because our levels
differ from the paper's; the residual causes are not fully identified. "Ours true" is our true-pair mean rebuilt from the cached trade
log; "ours random" the bootstrap mean; the difference next to the paper's own
Table 1 minus Table 6 difference. The last column is our difference over the
paper's; Table 1 prints no column for the top 120 pairs, so that ratio is n/a.

| Panel | Capital | Portfolio | ours true | ours random | ours diff | paper true | paper random | paper diff | ours / paper |
|---|---|---|---|---|---|---|---|---|---|
| A | employed | top5 | 1.340% | 0.012% | 1.328% | 1.308% | -0.137% | 1.445% | 0.92 |
| A | employed | top20 | 1.456% | -0.000% | 1.456% | 1.436% | -0.111% | 1.547% | 0.94 |
| A | employed | 101-120 | 1.016% | 0.026% | 0.990% | 1.081% | -0.105% | 1.186% | 0.83 |
| A | employed | top120 | 1.302% | 0.018% | 1.284% | n/a | -0.113% | n/a | n/a |
| A | committed | top5 | 0.796% | 0.004% | 0.792% | 0.784% | -0.083% | 0.867% | 0.91 |
| A | committed | top20 | 0.853% | -0.004% | 0.857% | 0.805% | -0.077% | 0.882% | 0.97 |
| A | committed | 101-120 | 0.634% | 0.004% | 0.629% | 0.679% | -0.089% | 0.768% | 0.82 |
| A | committed | top120 | 0.784% | 0.004% | 0.781% | n/a | -0.091% | n/a | n/a |
| B | employed | top5 | 0.785% | 0.010% | 0.774% | 0.745% | -0.177% | 0.922% | 0.84 |
| B | employed | top20 | 0.960% | 0.011% | 0.949% | 0.895% | -0.004% | 0.899% | 1.06 |
| B | employed | 101-120 | 0.821% | 0.030% | 0.791% | 0.795% | -0.154% | 0.949% | 0.83 |
| B | employed | top120 | 0.975% | 0.015% | 0.960% | n/a | -0.156% | n/a | n/a |
| B | committed | top5 | 0.471% | 0.007% | 0.464% | 0.463% | -0.103% | 0.566% | 0.82 |
| B | committed | top20 | 0.567% | 0.002% | 0.565% | 0.520% | -0.094% | 0.614% | 0.92 |
| B | committed | 101-120 | 0.509% | 0.008% | 0.501% | 0.503% | -0.112% | 0.615% | 0.81 |
| B | committed | top120 | 0.591% | 0.003% | 0.587% | n/a | -0.112% | n/a | n/a |

Standard deviations, random against true: the paper's claim is that the random
pairs are much noisier ("poorly matched").

| Panel | Capital | Portfolio | true SD | random SD | random / true |
|---|---|---|---|---|---|
| A | employed | top5 | 2.343% | 4.131% | 1.76 |
| A | employed | top20 | 1.705% | 2.052% | 1.20 |
| A | employed | 101-120 | 1.586% | 2.070% | 1.31 |
| A | employed | top120 | 1.260% | 0.858% | 0.68 |
| A | committed | top5 | 1.500% | 2.374% | 1.58 |
| A | committed | top20 | 1.077% | 1.200% | 1.11 |
| A | committed | 101-120 | 1.081% | 1.268% | 1.17 |
| A | committed | top120 | 0.837% | 0.525% | 0.63 |
| B | employed | top5 | 2.047% | 4.114% | 2.01 |
| B | employed | top20 | 1.507% | 2.062% | 1.37 |
| B | employed | 101-120 | 1.518% | 2.049% | 1.35 |
| B | employed | top120 | 1.139% | 0.852% | 0.75 |
| B | committed | top5 | 1.330% | 2.364% | 1.78 |
| B | committed | top20 | 0.959% | 1.202% | 1.25 |
| B | committed | 101-120 | 1.033% | 1.257% | 1.22 |
| B | committed | top120 | 0.754% | 0.519% | 0.69 |

True minus random, replication by replication:

| Panel | Capital | Portfolio | mean(true - random) | t (mean) | t (worst rep) | reps with a positive mean | reps with t > 2 |
|---|---|---|---|---|---|---|---|
| A | employed | top5 | 1.328% | 5.61 | 2.70 | 100% | 100.0% |
| A | employed | top20 | 1.456% | 9.42 | 7.28 | 100% | 100.0% |
| A | employed | 101-120 | 0.990% | 8.12 | 6.11 | 100% | 100.0% |
| A | employed | top120 | 1.284% | 14.82 | 12.98 | 100% | 100.0% |
| A | committed | top5 | 0.792% | 5.65 | 2.76 | 100% | 100.0% |
| A | committed | top20 | 0.857% | 9.57 | 7.41 | 100% | 100.0% |
| A | committed | 101-120 | 0.629% | 8.20 | 6.11 | 100% | 100.0% |
| A | committed | top120 | 0.781% | 14.36 | 12.71 | 100% | 100.0% |
| B | employed | top5 | 0.774% | 3.61 | 1.23 | 100% | 96.5% |
| B | employed | top20 | 0.949% | 7.11 | 4.44 | 100% | 100.0% |
| B | employed | 101-120 | 0.791% | 6.85 | 4.32 | 100% | 100.0% |
| B | employed | top120 | 0.960% | 12.68 | 10.74 | 100% | 100.0% |
| B | committed | top5 | 0.464% | 3.66 | 1.39 | 100% | 95.5% |
| B | committed | top20 | 0.565% | 7.17 | 4.69 | 100% | 100.0% |
| B | committed | 101-120 | 0.501% | 6.87 | 4.68 | 100% | 100.0% |
| B | committed | top120 | 0.587% | 12.30 | 10.38 | 100% | 100.0% |

## 6. Verdict

| criterion | met |
|---|---|
| random-pair means are negative in at least 14 of 16 series | no |
| random-pair means sit below the true pairs in all 16 series | yes |
| random-pair standard deviations exceed the true ones in all 16 series | no |
| the true-minus-random difference has t > 2 in all 16 series | yes |
| the difference is positive in all 12 comparable Table 1 series | yes |
| the difference is within 25% of the paper's everywhere it is defined | yes |

**Verdict: relative outperformance supported; table levels not replicated.**

Cells within 10% of the paper: 2 of 48 (4%). Within 25%: 19%.

Criteria not met: random-pair means are negative in at least 14 of 16 series, random-pair standard deviations exceed the true ones in all 16 series.

## 7. Limitations

- The draw is uniform inside the decile, so it ignores every other attribute
 (size, industry, volatility) that also drives the true mates apart; that is
 the paper's design, and it is why the random pairs should be poorly matched.
- Deciles are formed on the formation universe's cross-section, not on all CRSP
 stocks; the paper does not say which population it used.
- The bootstrap trades every true opening, including the second and later
 round trips of a pair, and each draw is a fresh pair (the paper does not say
 whether stocks are resampled per opening or per pair).
- Under `--close own`, because a random pair closes on its own crossing, a later opening of the same
 rank can arrive while an earlier random position is still open; the two are
 then held together in that rank's book (the true-pair rule re-opens a pair
 only after it has closed).
- A random leg with no price after the opening day produces no position.
- The caption does not explicitly identify whose crossing closes the position.
 `--close true` holds the true trade’s schedule fixed to isolate selection;
 `--close own` preserves the earlier experiment. Results from the two methods
 use separate output directories and cannot be mixed.
- The significance test is a Newey-West t of the monthly true-minus-random
 series, averaged over replications, not the paper's own (unreported) test.

## 8. How to regenerate

First build the paper-profile cohorts, including February–June 1963 warmup,
with `scripts/03_replicate.py`. The example below uses the controlled audit's
combined cache. All generated outputs stay under ignored `results/`.
Runtime depends on the machine; one worker limits peak memory.

```sh
python scripts/claims/table6_random_pairs.py --mode control \
    --cache-root data/processed/replication/fidelity/combined \
    --close true --out-root results/replication/reconciliation/table6_true
python scripts/claims/table6_random_pairs.py --mode run --reps 200 --workers 1 \
    --cache-root data/processed/replication/fidelity/combined \
    --close true --out-root results/replication/reconciliation/table6_true
python scripts/claims/table6_random_pairs.py --mode report --reps 200 \
    --cache-root data/processed/replication/fidelity/combined \
    --close true --out-root results/replication/reconciliation/table6_true \
    --report-dir results/replication/reconciliation/table6_true/report
```

The control writes `control.json` directly into the output directory. The
report checks the Table 6 targets against the attached paper PDF. Unit tests:
`python -m pytest tests/test_table6.py -q`.

## Reproduce the declared baseline experiment

```sh
python scripts/claims/table6_random_pairs.py --specification baseline --mode control --cache-root data/processed/replication/reconciliation/baseline --out-root results/replication/reconciliation/baseline_table6_v2 --close true
python scripts/claims/table6_random_pairs.py --specification baseline --mode run --cache-root data/processed/replication/reconciliation/baseline --out-root results/replication/reconciliation/baseline_table6_v2 --close true --reps 200 --workers 4
python scripts/claims/table6_random_pairs.py --specification baseline --mode report --cache-root data/processed/replication/reconciliation/baseline --out-root results/replication/reconciliation/baseline_table6_v2 --close true --reps 200
```
