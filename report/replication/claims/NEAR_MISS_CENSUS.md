# Near-miss census on the SIC-free surface, and the reading-combination audit

Contract R8-A (round 8). Everything here is measured on the shipped check: `REPLICATION_CHECK.md`
at `d2398b6`, **411.0 of 865** (322 / 178 / 365), regenerated from the shared caches into
`.private/base` and verified to print the same score line (865 cells, 411.0) before the census was
taken. The band rule is the driver's own (`scripts/03_replicate.py::_mark`):
`gap = |ours / paper - 1|`, check at `gap <= 0.10`, tilde at `gap <= 0.25`, cross beyond.

Sections: 1 the census, 2 the reading library, 3 the pre-registration, 4 the measurements,
5 the verdict. Section 3 was written to this file **before** any combination was run; sections 4
and 5 were added afterwards and nothing in 3 was edited.

## 1. Which missed cells are near their band edge

**What is excluded.** The SIC-dependent surface, which round 7 closed: every `Table 3` block (the
four sector panels and the stocks-per-cohort block) and Table 2 Panel B's four sector-weight rows
(`weight_utilities`, `weight_transportation`, `weight_financials`, `weight_industrials`). That
removes 139 + 16 = 155 cells and leaves **710 cells worth 320.0** (253 / 134 / 323), which is
411.0 minus Table 3's 80.0 and the four sector rows' 11.0.

**What is measured.** For every remaining tilde and cross cell the parsed `ours / paper` pair gives
`gap`; the edge it must cross is `0.25` for a cross (to reach a tilde) and `0.10` for a tilde (to
reach a check). `need = gap - edge` is the fraction of the paper's value by which the gap must
close, and `move_of_ours = need x |paper| / |ours|` the same move as a share of our own number.
Ranked by `need`, ascending.

**The page's own resolution.** The check prints three significant digits (two decimals for
percentages), so every printed value carries a rounding interval, and `unc` is what that rectangle
does to `need`. 29 of the 457 tilde and cross cells sit inside their own printing interval: the page
cannot say which side of the edge they are on, so they are listed but never ranked. One more cell
cannot be measured this way at all - Table 5 Panel B's 101-120 serial correlation, scored against a
printed zero on the two decimals the paper prints (REVIEW_NOTES section 62) - and it is a cross at
0.04 / 0.00, i.e. as far off as the page can express.

Census universe: **456 of 457 tilde and cross cells measured, 427 ranked, 29 at the edge, 1
printed-zero.** The full table is `.review/r8/A/census.csv` (456 rows with `gap`, `need`,
`move_of_ours`, `unc`, `at_edge`).

### Top 40 near misses

| # | table / block | row | portfolio | ours / paper | mark | need (pp of the paper) | move of ours |
|---|---|---|---|---|---|---|---|
| 1 | Table 8 | `post_std` | top5 | 1.493% / 1.660% ~ | ~ | +0.06 | +0.07% |
| 2 | Table 5 Panel B | `min` | 101-120 | -1.786% / -1.987% ~ | ~ | +0.12 | +0.13% |
| 3 | Table 8 | `post_std` | all | 1.622% / 1.295% ✗ | ✗ | +0.25 | +0.20% |
| 4 | Table 6 | `A. No waiting, fully invested: Standard deviation` | Top 5 | 0.041223 / 0.05521 ✗ | ✗ | +0.33 | +0.45% |
| 5 | Table 7 | `long: standard deviation` | 101-120 | 3.80% / 3.44% ~ | ~ | +0.47 | +0.42% |
| 6 | Table 4 | `t: momentum` | top20 | -2.19 / -2.45 ~ | ~ | +0.61 | +0.68% |
| 7 | Table 2 Panel A | `avg_round_trips_per_pair` | top5 | 2.24 / 2.02 ~ | ~ | +0.89 | +0.80% |
| 8 | Table 7 | `t: short: intercept` | top5 | -2.44 / -2.74 ~ | ~ | +0.95 | +1.07% |
| 9 | Table 9 Panel A | `std` | top20 | 1.62% / 1.46% ~ | ~ | +0.96 | +0.86% |
| 10 | Table 8 | `post_reversal` | top5 | -0.0789 / -0.0626 ✗ | ✗ | +1.04 | +0.82% |
| 11 | Table 6 | `B. Wait one day, fully invested: Median` | Top 5 | -0.0021427 / -0.00241 ~ | ~ | +1.09 | +1.23% |
| 12 | Table 7 | `short: standard deviation` | 101-120 | 3.50% / 3.15% ~ | ~ | +1.11 | +1.00% |
| 13 | Table 4 | `t: reversal` | 101-120 | 2.49 / 2.24 ~ | ~ | +1.16 | +1.04% |
| 14 | Table 9 Panel A | `min` | all | -2.98% / -2.68% ~ | ~ | +1.19 | +1.07% |
| 15 | Table 9 Panel A | `t_stat` | top20 | 8.41 / 9.48 ~ | ~ | +1.29 | +1.45% |
| 16 | Table 5 Panel B | `min` | top20 | -5.955% / -6.723% ~ | ~ | +1.42 | +1.61% |
| 17 | Table 1 Panel B | `t_stat` | all | 7.01 / 7.92 ~ | ~ | +1.49 | +1.68% |
| 18 | Table 9 Panel A | `std` | top5 | 2.12% / 1.90% ~ | ~ | +1.58 | +1.42% |
| 19 | Table 7 | `short: market` | all | 0.926 / 0.731 ✗ | ✗ | +1.68 | +1.32% |
| 20 | Table 8 | `post_reversal` | all | 0.166 / 0.188 ~ | ~ | +1.70 | +1.93% |
| 21 | Table 2 Panel A | `avg_price_deviation_trigger` | top20 | 0.0466 / 0.0528 ~ | ~ | +1.74 | +1.97% |
| 22 | Table 6 | `B. Wait one day, fully invested: Standard deviation` | Top 100-120 | 0.021202 / 0.02404 ~ | ~ | +1.81 | +2.05% |
| 23 | Numbers printed in the text | `Newey-West t-statistic` | ours / paper | 4.25 / 4.82 ~ | ~ | +1.83 | +2.07% |
| 24 | Table 9 Panel B | `median` | top5 | 0.66% / 0.59% ~ | ~ | +1.86 | +1.67% |
| 25 | Table 1 Panel B | `max` | all | 11.93% / 16.32% ✗ | ✗ | +1.90 | +2.60% |
| 26 | Table 8 | `pre_intercept` | 101-120 | 0.901% / 0.710% ✗ | ✗ | +1.90 | +1.50% |
| 27 | Table 8 | `post_intercept` | top20 | 0.367% / 0.417% ~ | ~ | +1.99 | +2.26% |
| 28 | Table 5 Panel A | `var_5` | 101-120 | -1.449% / -1.293% ~ | ~ | +2.06 | +1.84% |
| 29 | Table 4 | `t: ibbotson_default_premium` | 101-120 | 2.03 / 1.81 ~ | ~ | +2.15 | +1.92% |
| 30 | Table 6 | `A. No waiting, fully invested: Median` | Top 5 | -0.002155 / -0.00192 ~ | ~ | +2.24 | +2.00% |
| 31 | Table 8 | `pre_smb` | all | -0.292 / -0.402 ✗ | ✗ | +2.36 | +3.25% |
| 32 | Table 5 Panel A | `var_25` | top5 | -0.403% / -0.460% ~ | ~ | +2.39 | +2.73% |
| 33 | Table 5 Panel A | `var_25` | 101-120 | -0.127% / -0.145% ~ | ~ | +2.41 | +2.76% |
| 34 | Table 8 | `pre_hml` | all | -0.0505 / -0.0698 ✗ | ✗ | +2.65 | +3.66% |
| 35 | Table 4 | `t: ibbotson_small_premium` | 101-120 | 2.12 / 1.66 ✗ | ✗ | +2.71 | +2.12% |
| 36 | Table 8 | `t: pre_market` | 101-120 | -4.86 / -3.8 ✗ | ✗ | +2.89 | +2.26% |
| 37 | Table 5 Panel B | `std` | all | 0.191% / 0.169% ~ | ~ | +3.02 | +2.67% |
| 38 | Table 8 | `pre_std` | all | 1.436% / 1.651% ~ | ~ | +3.02 | +3.47% |
| 39 | Table 8 | `t: pre_hml` | 101-120 | -2.08 / -1.84 ~ | ~ | +3.04 | +2.69% |
| 40 | Table 8 | `t: pre_reversal` | top20 | 2.6 / 3.62 ✗ | ✗ | +3.18 | +4.42% |

### How the mass is distributed

| distance to the edge | cells |
|---|---|
| under 0.5 pp | 5 |
| 0.5 to 1 pp | 4 |
| 1 to 2 pp | 18 |
| 2 to 5 pp | 39 |
| 5 pp or more | 361 |

427 ranked near misses: 27 within 2 pp of an edge, 66 within 5 pp, and 361 beyond it. A half point
of score is bought by flipping any single one of them, so the top of this list is the cheapest score
in the paper - and the census's real deliverable is the shape: a thin near-miss tail on a very long
body.

### Clusters (resolvable near misses within 5 pp, by block)

| cells | block | the clustered cells |
|---|---|---|
| 19 | Table 8 | post-1988 sd (top5, all) and reversal (top5, all), post-1988 intercept (top20), pre-1989 intercept/SMB/HML and their t-statistics |
| 8 | Table 7 | short book: sd 101-120, HML 101-120, market all, serial correlation all, `t: short: intercept` in three portfolios |
| 7 | Table 6 | fully-invested and committed sd/median/mean cells in both panels, top 5 and 101-120 |
| 7 | Table 4 | Ibbotson intercept (all), its two premium t-statistics, `t: intercept` 101-120, `t: momentum` top20 |
| 4 | Table 9 Panel A | `std` top5 / top20, `min` all, `t_stat` top20 |
| 4 | Table 9 Panel B | `max` all / 101-120, `mean` top20, `median` top5 |
| 4 | Table 1 Panel A | `max` all / top20, committed mean all, `share_negative` 101-120 |
| 3 | Table 5 Panel B | `min` 101-120 / top20, `std` all |
| 3 | Table 2 Panel A | `avg_round_trips_per_pair` top5, `avg_price_deviation_trigger` top5 / top20 |
| 3 | Table 1 Panel B | `t_stat` all, `max` all, kurtosis top5 |
| 3 | Table 5 Panel A | `var_25` top5 / 101-120, `var_5` 101-120 |
| 1 | printed text | the Newey-West t-statistic of the 1999-2002 hold-out sentence |

66 clustered cells in all. Two structural facts fall out. The Table 8 cluster is almost entirely the
post-1988 half of the subperiod block - the era where the paper's own reversal factor cannot be
rebuilt (REVIEW_NOTES sections 61 and 73) - and the Table 7 / Table 5 Panel B clusters are short-book
and tail statistics, which are exactly the cells the value-weighted book with a floored short weight
is known to distort (REVIEW_NOTES sections 29 and 62). Neither is a place where a *combination* of
already-measured readings can reach, which is what section 3 has to confront.

## 2. The library of readings that already carry a full-check score

One row per reading measured on the whole 865-cell check, with the flag that reproduces it. The
**cell set** matters: only 865-cell rows are comparable with the shipped 411.0. Scores marked (t) were
measured against the 865-cell check but with today's factor files instead of the 2005 archives
(REVIEW_NOTES section 87, `claims/FULLSET_RESCORE.md` section 6), so their deltas are not
transferable to the shipped check.

| # | reading | flag(s) | score (865 cells unless noted) | section |
|---|---|---|---|---|
| 1 | open at 2.33 sigma instead of 2.00 | `--trigger-mult 2.33` | 395.0 (t) | FULLSET 2 |
| 2 | fresh divergence: a pair outside the band at formation end waits for a new crossing | `--fresh-divergence` | 409.5 (t) | FULLSET 2 |
| 3 | frozen-quote pairs demoted, either leg / both legs | `--demote-frozen one` / `both` | 401.5 / 408.5 (t) | FULLSET 2 |
| 4 | cohort weights by pairs holding a position | `--cohort-weights positions` | 404.0 (t) | FULLSET 2 |
| 5 | cohort weights by pairs selected | `--cohort-weights selected` | 411.5 (t) | FULLSET 2 |
| 6 | fully invested on the payoff count | `--capital-base count` | 397.5 (t) | FULLSET 2 |
| 7 | fully invested on the gross book | `--capital-base gross` | 299.0 (t) | FULLSET 2 |
| 8 | fully invested on the long book | `--capital-base long` | 405.0 (t) | FULLSET 2 |
| 9 | Table 2 Panel A over every cohort, censored windows included | `--panel-a-cohorts all` | 410.0 (t) | FULLSET 2 |
| 10 | share classes: the flag's default map (SB+AD, 1,677 permnos) | `--share-classes wide` | 411.0 | REVIEW_NOTES 87 |
| 11 | share classes: shares of beneficial interest only (299) | `--share-classes wide --share-classes-file <SB>` | 407.5 | REVIEW_NOTES 87 |
| 12 | share classes: ADRs only (1,378) | `--share-classes wide --share-classes-file <AD>` | 415.0 | REVIEW_NOTES 87 |
| 13 | share classes: every type the raw files carry (2,079), all five caches rebuilt | `--share-classes wide --share-classes-file <complete>` | 411.0 | REVIEW_NOTES 87 |
| 14 | rebased normalization | `--normalization rebased` | 342.5 | REVIEW_NOTES 76 |
| 15 | same-issuer pairs allowed | `--same-issuer allow` | 404.5 | REVIEW_NOTES 76 |
| 16 | near-frozen-quote share 0.90 / 0.99 | `--max-stale-share 0.90` / `0.99` | 396.0 / 389.0 | REVIEW_NOTES 76 |
| 17 | 481x telephone SIC | `--telephone-sic 481x` | 401.5 | REVIEW_NOTES 76 |
| 18 | waste management as Utilities | `--waste-sic utilities` | 404.0 | REVIEW_NOTES 76 |
| 19 | trigger sigma as the standard deviation about the mean | `--trigger-sigma std` | 405.5 | REVIEW_NOTES 21, 76 |
| 20 | short positions weighted by the shorted stock's value | `--short-weights value` | 389.5 | REVIEW_NOTES 29, 76 |
| 21 | universe `volpos_common` / `vol_ns` / `price_common` | `--universe ...` | 359.0 / 349.5 / 357.0 | REVIEW_NOTES 76 |
| 22 | Table 3 group label from the header SIC | `table3_sectors.py --label header` | 404.5 | REVIEW_NOTES 83 |
| 23 | Table 3 label from the first formation day | `... --label formstart` | 411.5 | REVIEW_NOTES 83 |
| 24 | Table 3 label from the first trading day | `... --label tradestart` | 375.0 | REVIEW_NOTES 83 |
| 25 | Table 3 modal 18-month label | `... --label modal18` | 405.5 | REVIEW_NOTES 83 |
| 26 | Table 3, unknown-SIC stocks dropped | `... --label nosic_drop` | 399.5 | REVIEW_NOTES 83 |
| 27 | Table 3, 481x telephone as its own group | `... --label 481x` | 401.5 | REVIEW_NOTES 83 |
| 28 | delisted leg closes at its last available price, no delisting return | `--delist-last-px all` (round 6: `table3_sectors.py`) | 412.0 (REVIEW_NOTES 94; first recorded as 412.5 in the round-6 engine, which a full build does not reproduce) | REVIEW_NOTES 83, 94 |
| 29 | $5 floor on the cheaper leg | `--min-price 5` | 398.0 | REVIEW_NOTES 83 |
| 30 | both legs in one sector group | `--match same-sector` | 394.5 | REVIEW_NOTES 83 |
| 31 | today's factor files instead of the 2005 archives | `--factor-vintage today` | 411.0 (neutral: Table 7 -1.0, Table 4 +0.5, Table 8 +0.5) | REVIEW_NOTES 72 |
| 32 | recall closes at the flagged day (shipped R1) vs next day (R0) | `table9b_recalls.py --reading R1` / `R0` | block only: 21.0 / 18.0 of 44 | REVIEW_NOTES 74 |
| 33 | recall rolling threshold / R1+rolling / falls-only / either leg | `--reading R2` / `R3` / `R4` / `R5` | block only: 18.5 / 21.5 / 17.0 / 17.0 of 44 | REVIEW_NOTES 74 |
| 34 | Table 6 committed capital: book-share (shipped) vs literal | `table6_random_pairs.py --committed-capital` | block only: 13.0 / 11.0 of 48 | REVIEW_NOTES 75 |
| 35 | Table 6 draw readings D1-D4 | `--close` / `--draw-near 10` / `--complete-legs` / `--decile-breaks market` | block only: 0.5 / 12.0 / 13.0 / 13.0 of 48 | REVIEW_NOTES 75 |

Rows 32-35 are recorded because they were measured, but they are **block** scores, not full-check
scores: they cannot be added to a full-check number without re-running the check.

**What the library says before any combination is run.** Of the 31 full-check rows, exactly five sit
above 411.0: `--cohort-weights selected` 411.5 (+0.5), the two share-class variants 415.0 (+4.0,
which REVIEW_NOTES 87 records as indefensible as the paper's universe), the first-formation-day
Table 3 label 411.5 (+0.5, one cell, no textual support), and `last_px` 412.0 (+1.0 on the driver's full build, REVIEW_NOTES 94; first recorded as 412.5, expressly the
paper's robustness variant rather than its stated rule). Every other reading loses, most by more
than five points.

## 3. The combination audit: pre-registration

**Written before any combination was scored**, and not edited afterwards. Every candidate obeys:
(a) each component is textually supportable or a shipped-default neighbour whose support is in the
library; (b) the components act on different statistics, so their cell-level effects compose without
a known interaction; (c) the combination targets section 1's clusters; (d) no per-table mixing, no
threshold tuning, no component chosen for its score.

**The ship rule, fixed now.** A combination ships only if it (i) beats 411.0 on the whole 865-cell
check, (ii) has textual support for *every* component, and (iii) is reproducible from one command
line as one global reading set. Anything else is a measurement, not a proposal.

| id | combination | flag(s) | components | target |
|---|---|---|---|---|
| C1 | overlap weights by active positions + Panel A over every cohort | `--cohort-weights positions --panel-a-cohorts all` | 404.0 / 410.0 | Table 2 Panel A `avg_*`, Table 1 B `t_stat`/`max`, Table 8 dispersion |
| C2 | overlap weights by selected pairs + Panel A over every cohort | `--cohort-weights selected --panel-a-cohorts all` | 411.5 / 410.0 | the same clusters, from the two components nearest the baseline |
| C3 | overlap weights by active positions + payoff-count base | `--cohort-weights positions --capital-base count` | 404.0 / 397.5 | Table 1 A/B levels, Table 4 and Table 8 pre/post loadings, Table 5 A VaR |

**Textual support, component by component.** C1 and C3 rest on the paper's overlap-average sentence
for the weights ("averaging monthly returns across trading strategies that start one month apart as
in Jegadeesh and Titman (1993)", p. 805), which weights a month by the strategies actually held, i.e.
`positions`; C2's `selected` weights a cohort by the pairs it chose for that portfolio, the same
sentence read one step earlier. `panel-a-cohorts all` rests on Table 2 Panel A being an average over
the paper's every cohort month, censored windows included. `capital-base count` rests on eq. (2)/(3)
being a sum over the pairs selected divided by the number of pairs, the payoff count the cache
already carries.

**Prediction, recorded before measuring.** Each component is individually at or below the baseline,
the two `positions`/`count` readings lose 7.0 and 13.5 points, and the Table 2 Panel A rows the
combination aims at are 0.9 and 1.7 pp from their edges. The pre-registered expectation was that
**all three lose**, C2 by least; a combination that beat the baseline would have to be explained by an
interaction, and none of these components has a mechanism for one.

## 4. The measurements

Three aggregate-only runs over the shipped caches, one global reading set each, `--workers 1`
(`.review/r8/A/check_combos.sh`; pages in `.private/c1`, `.private/c2`, `.private/c3`; baseline in
`.private/base`). All three print the 2005-archives paragraph and 865 compared cells, so the columns
are like for like.

| id | combination | score | delta | marks moved vs shipped |
|---|---|---|---|---|
| C1 | `--cohort-weights positions --panel-a-cohorts all` | **401.5** | **-9.5** | 70 |
| C2 | `--cohort-weights selected --panel-a-cohorts all` | **410.0** | **-1.0** | 8 |
| C3 | `--cohort-weights positions --capital-base count` | **398.5** | **-12.5** | 147 |

**C1, per block** (net points against the shipped check): Table 4 -2.5, Table 1 Panel A -1.5, Table 1
Panel B -1.5, Table 3 Financials -1.5, Table 3 Industrials -1.5, Table 9 Panel A -1.5, Table 2 Panel A
-1.0, Table 3 Utilities -0.5, Table 7 -0.5, Table 5 Panel A 0.0, Table 8 +0.5, the text's numbers
+0.5, Table 3 Transportation +1.5. Sum -9.5. The moves are 33 check-to-tilde, 16 tilde-to-check, 12
tilde-to-cross, 8 cross-to-tilde, 1 cross-to-check.

**C2, per block**: Table 2 Panel A -1.0, Table 4 -0.5, Table 9 Panel A -0.5, Table 1 Panel A +0.5,
Table 3 Transportation +0.5. Sum -1.0, on 8 marks (3 tilde-to-check, 3 check-to-tilde, 2
tilde-to-cross). C2 is the near-baseline pair, and it does what the components say it should: the
`selected` weights buy their half point back in Table 2 Panel A when Panel A is read over every
cohort, so the two halves of the pair cancel almost exactly and the residual is -1.0.

**C3, per block**: Table 4 -10.0, Table 3 Financials -3.5, Table 3 Utilities -2.0, Table 3
Transportation -2.0, Table 5 Panel A -1.5, Table 9 Panel A -1.5, Table 7 -0.5, Table 1 Panel B 0.0,
the text's numbers +0.5, Table 8 +1.0, Table 1 Panel A +2.5, Table 3 Industrials +4.5. Sum -12.5,
on 147 marks.

Two findings come out of the measurement that the pre-registration did not forecast in their size:

1. **The components do not compose additively; they concentrate.** C3 moves 147 marks and costs
   12.5 points, and 10.0 of that is Table 4 alone: the payoff-count base rescales the fully-invested
   series, so every regression loading and t-statistic in Table 4 re-marks against a paper that
   reports value-weighted books. C1's damage is spread across nine blocks with the same signature.
   Neither combination has a cell-level interaction *inside* a block; the interaction is between the
   base and the block's sign.
2. **The near-miss clusters are not where combinations bite.** Section 1's clusters are Table 8
   post-1988, the Table 7 short book and the Table 5 Panel B tails; C1 and C3 both move Table 8 in
   the *right* direction (+0.5 and +1.0) and both lose far more in Table 4 and the sector blocks,
   which are not near-miss territory. The near-miss tail is a property of the paper's estimates,
   not of the levers the library contains.

## 5. The verdict

**No combination ships.** All three pre-registered combinations lose: C2 by 1.0 point (410.0), C1 by
9.5 (401.5), C3 by 12.5 (398.5). The pre-registered prediction held exactly, including that C2 would
lose by least. The ship rule was not met by any of them, so the shipped score stays **411.0 of 865**
and nothing in this contract touches `tests/replication_conformance.json`, `SCORE_LOG.md`, the
manifest or the shared caches.

**What the census is, then.** It is the "what is left" exhibit. The SIC-free surface holds 456
missed or near-missed cells, of which 27 sit within 2 pp of a band edge and 66 within 5 pp; a single
cell is worth half a point, so the entire ranked tail is worth at most about 30 points of score and
the library's best admissible single reading (`selected` 411.5) already takes the cheapest one. The
remaining 361 cells are more than 5 pp out, and they are not spread evenly: they are the paper's
regression and dispersion blocks, where the paper's own reversal factor cannot be rebuilt and the
value-weighted book's tails are known to differ.

**What would be needed to move the number.** Not a combination of readings already in the library:
their cell-level signatures overlap too much (Table 4 and Table 8 carry most of the weight, and both
are dominated by the factor frame). A real move needs either a factor frame that reproduces the
paper's implied reversal factor in both subperiods (REVIEW_NOTES 61, 73) or a book definition that
fixes Tables 5 and 7's tails without breaking Tables 1 and 4 - and the second is exactly the
interaction C3 measured at -12.5 points. That is where the next round of work should look.

**Reproduction.** From `.review/wt/r8-A`:

    Q=$(git rev-parse --show-toplevel)
    sh $Q/.review/r8/A/check_base.sh          # shipped: 411.0 of 865
    sh $Q/.review/r8/A/check_combos.sh        # C1 401.5, C2 410.0, C3 398.5

The census itself is `python $Q/.review/r8/A/census.py 40`, which re-derives `census.csv` from the
committed `REPLICATION_CHECK.md` and refuses to run silently if the scored-cell count is not the
expected 710 after the SIC exclusions.
