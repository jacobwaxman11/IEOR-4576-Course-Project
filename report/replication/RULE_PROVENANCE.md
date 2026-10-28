# Rule provenance: what the final paper says, what the engine does

Compiled 2026-10-26 against `replication/round-nine-evidence` (`708fa9ed`). Corrected the
same day: rows 5, 13, 16 (split into 16 and 16b), 17 and 18, the tally, and the
references to "R" nodes, which belonged to an untracked local file rather than to the
repository's `OPEN_QUESTIONS.md`.

Purpose: every cell in `REPLICATION_CHECK.md` rests on an operational rule. This
document quotes the final paper for each rule, quotes the 1999 NBER draft where the
final paper is contradictory or silent, and records what the engine does. It is a
review of the *wording*, not of the score: the tables were already checked against
each other, but the prose never was.

Two uses. First, it is the answer to "why does the engine do that?" for anyone who
joins later, in the paper's own words instead of ours. Second, it stops a settled
rule from being re-litigated: re-check a `MATCH` row before proposing a change to it,
and if a shipped convention moves, the row that describes it has to move with it.
Row numbers are stable, so `REVIEW_NOTES` and PR reviews can cite "row 19" without
retyping a quote.

Sources, all on disk:

| file | role here |
|---|---|
| `pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf` (RFS 19(3), p. 801-824) | **the target**. Page numbers below are this edition's |
| `Pairs_Trading_RV_Arbitrage_Rule.pdf` (Yale ICF 08-03, Feb 2006) | same paper, checked wherever it was the easier grep; no wording difference found |
| `report/replication/reference/NBER_w7032_1999_draft.pdf` | tiebreaker only, per `EDITION_1999.md`: it may veto a reading, it cannot justify one |
| `src/project/*.py`, `scripts/03_replicate.py`, `configs/config.yaml` | the engine as shipped |

Verdict classes:

- **MATCH** - the engine implements the paper's words.
- **CONTRADICTORY** - the paper says two different things; the engine follows one, named below.
- **DEVIATION** - the engine departs from the paper's words deliberately; marked *disclosed* if the
  check header (`scripts/03_replicate.py`, conventions paragraph) already says so, *undisclosed* if not.
- **SILENT** - neither edition says anything; the engine's choice is an inference and must be
  defended by measurement alone.

## The table

### Sample, pairing, and portfolios

| # | rule | the final paper's words | engine | verdict |
|---|---|---|---|---|
| 1 | formation and trading horizons | p. 802: "We form pairs over a 12-month period (formation period) and trade them in the next 6-month period (trading period). Both 12 months and 6 months are chosen arbitrarily" | `formation_months: 12`, `trading_months: 6`, `COHORT_TRADING_MONTHS = 6` | **MATCH** |
| 2 | overlapping cohorts | p. 805: "trading the pairs at the beginning of every month in the sample period, with the exception of the first 12 months ... The result is a time series of overlapping six-month trading period excess returns. We correct for the correlation induced by overlap by averaging monthly returns across trading strategies that start one month apart as in Jegadeesh and Titman (1993)" | `evaluation.py` equal-weights the cohorts whose trading window covers month *m* | **MATCH**. This is the rule that makes 474 observations out of 474 cohorts; the reproduction of 474 is itself the evidence |
| 3 | liquidity screen | p. 802: "we screen out all stocks from the CRSP daily files that have one or more days with no trade. This serves to identify relatively liquid stocks as well as to facilitate pairs formation" | no-trade day = recorded zero volume (`vol_common`); plus two exclusions the paper does not have (never-moving price; no volume and unchanged price on >95% of formation days) | **DEVIATION, disclosed** ("The paper states none of these three exclusions beyond screening out stocks with a no-trade day") |
| 4 | normalization | p. 802: "construct a cumulative total returns index for each stock over the formation period ... normalized daily 'price' space, where price includes reinvested dividends" | cumulative total-return index, dividends reinvested | **MATCH** |
| 5 | pairing | p. 802: "choose a matching partner **for each stock** by finding the security that minimizes the sum of squared deviations between the two normalized price series. Pairs are thus formed by exhaustive matching" | `select_pairs`: nearest neighbour per stock, duplicate legs allowed, ranked by distance | **MATCH**. "For each stock" settles the duplicate-leg question textually, which `PAIR_FORMATION.md` section 2 had settled only by measurement (0.875 pairs per stock against the paper's 2,057 / 2,317 = 0.888; a one-pair-per-stock rule would give at most 0.5) |
| 6 | sector-restricted pairs | p. 803: "we restrict both stocks to belong to the same broad industry categories defined by Standard and Poors: Utilities, Transportation, Financial, and Industrials. Each stock is assigned to one of these four groups, based on the stock's SIC code. The minimum-distance criterion is then used to match stocks within each of the groups" | `select_pairs_within_groups`, same four labels; SIC membership from `sectors.py` (4811 telephone -> Utilities, 495x -> Industrials) | **MATCH** on the method. The SIC ranges are ours: "the paper gives no SIC ranges" (disclosed) |
| 7 | portfolio definitions | p. 803: "the top 5 and 20 pairs with the smallest historical distance measure, in addition to the 20 pairs after the top 100 (pairs 101-120)"; Table 2 note: "the portfolio '101-120' includes the 20 pairs after the top 100" | `pair_counts: [5, 20, 100]`; 101-120 = ranks 101-120, left empty when the sector has 101-119 | **MATCH** |

### Trading rules

| # | rule | the final paper's words | engine | verdict |
|---|---|---|---|---|
| 8 | entry trigger | p. 804: "We open a position in a pair when prices diverge by more than **two historical standard deviations, as estimated during the pairs formation period**"; Table 2 note: "Average deviation to trigger opening of pair is the cross-sectional average of two standard deviations of the **pair prices difference**" | 2 x `sigma`, where `sigma` is the formation spread's **root mean square about zero**, `sqrt(SSD/N)` (`features.py`, `sigma="rms"`, the default) | **DEVIATION, disclosed** ("The trigger's sigma is the formation spread's root mean square about zero, sqrt(SSD/N), not its standard deviation about its mean"). Because `rms^2 = std^2 + mean^2` pair by pair, `rms >= std` always, so the paper's literal estimator would put the Table 2A trigger row *below* our 4.09% and *widen* the gap to the paper's 4.76%. The deviation is chosen against the paper's words and still does not close the gap - it is the closest of the readings, not a match |
| 9 | exit rule | p. 804: "We unwind the position at the next crossing of the prices. If prices do not cross before the end of the trading interval, gains or losses are calculated at the end of the last trading day of the trading interval. If a stock in a pair is delisted from CRSP, we close the position in that pair, using the delisting return, or the last available price" | trade reasons `converged` / `end` / `delisted`, with the delisting row as terminal | **MATCH** |
| 10 | position sizes | p. 804: "we open a long-short position ... payoffs by going **one dollar short** in the higher-priced stock and **one dollar long** in the lower-priced stock" | `L = np.ones(n)`, `S = np.ones(n)`; both reset to 1.0 on every reopen | **MATCH**. The long leg is the *lower*-priced stock, which is what the sign convention of the spread test already encodes |
| 11 | entry and exit timing (no wait) | p. 806: "positions are opened at the end of the day that prices diverge and closed at the end of the day of price convergence" | open at the signal close, returns accrue from the next day; close at the crossing close | **MATCH** |
| 12 | **the one-day wait** | **contradictory.** Table 1 note, p. 806: "The results in Panel B correspond to a strategy that **delays the opening** of the pairs position by one day." Body, p. 812: "the pairs are traded with a one-day delay before **opening and closing** a position to minimize the effect of the bid-ask bounce." Table 7 note, p. 821: "formed and traded according to the **'wait one day'** rule" | wait 1 opens at the close of the following day and closes at the close of the day after the crossing | **CONTRADICTORY**; the engine follows the body text and Table 7, and the 1999 draft agrees explicitly: "we initiate positions in each pair on the day following the divergence and liquidate on the day following the crossing" |
| 13 | wait-1 pending entry | **silent** in both editions. The draft states the rule without any persistence condition: "initiate positions in each pair on the day following the divergence" | "skipping signals whose prices **cross on that intervening day**" (`models.py`, wait=1 docstring) | **SILENT, undisclosed**, and **score-neutral**. Measured on the shipped engine, 2026-10-26 (full 474-cohort rebuild with the clause removed, everything else at `708fa9ed` defaults): Tables 1-3 stay at 187.0 of 291 and the total at 213.5 of 323, with no cell changing its mark. Values move by a basis point or less (Table 1 Panel B top 5 mean 0.69% both ways, top 20 0.88% -> 0.87%; Table 2 Panel A top 5 round trips 2.24 -> 2.26), and Figure 1 is unaffected (it is no-wait). The clause therefore has neither a textual nor a measured reason. Numbers quoted elsewhere for it (180.0 alone, 182.5 with 495x, against 184.5) come from a local experimental lineage with payoff-count returns that was never shipped, and do not apply to this engine |
| 14 | same-issuer pairs | **silent** | a stock is never matched with another security of the same `permco` | **DEVIATION, disclosed** |

### Return computation

| # | rule | the final paper's words | engine | verdict |
|---|---|---|---|---|
| 15 | portfolio weighting | p. 805, eq. (2)-(3): `r_P,t = sum_i w_i,t r_i,t / sum_i w_i,t`, `w_i,t = w_i,t-1 (1 + r_i,t-1)`; "The daily returns on the long and short positions are calculated as value-weighted returns in the following way ... the daily returns are compounded to obtain monthly returns. This has the simple interpretation of a **buy-and-hold strategy**" | value-weighted daily returns with compounding weights; `CACHE_FORMAT = 5` | **MATCH** at portfolio level |
| 16 | **short leg weighting** | eq. (3), `w_i,t = w_i,t-1 (1 + r_i,t-1)`, is stated for "the long and short positions" without saying whether `r` is a shorted stock's return or the short position's | `--short-weights position` (default): the short's weight compounds at the position's own return, `prod(1 - r_short)`, floored at 0; `--short-weights value` compounds at the shorted stock's return | **SILENT, reading disclosed** in the check header ("The short-position weight is also our reading ... SCORE_LOG.md row 12"). Measured both ways (REVIEW_NOTES 29, SCORE_LOG rows 12-13): `value` scores 183.5 of 291 against 187.0 (Table 1 +5.0, Table 3 -8.5). Table 7 does **not** separate them: on the full sample our long-minus-short exceeds our Table 1 Panel B mean by 3.2 / 1.2 / 1.5 / 2.6 bp under `position` and by 3.1 / 1.2 / 1.4 / 1.4 bp under `value`, against the paper's -0.1 / 0 / 0 / 0. That residual is row 16b, not this row. Table 7's short-book level leans to `position`: "all" 0.878% (`position`) and 0.708% (`value`) against the paper's 0.908% |
| 16b | **monthly aggregation of the two books** | p. 805: "the daily returns are compounded to obtain monthly returns"; Table 7 long - short = Table 1 Panel B to one basis point (top 5: 0.01245 - 0.00501 = 0.00744 against 0.00745; the other three columns agree to the last digit) | Table 1 compounds the **daily difference** of the two books (`cohort_monthly(portfolio_daily(...))`); Table 7 compounds each book separately | **DEVIATION, undisclosed in the check header** (recorded in REVIEW_NOTES 33). The paper's identity says it compounds each book and then differences. Doing that for Table 1 too scores 184.0 of 291 against 187.0 (REVIEW_NOTES 33): it closes a third of every Table 1 mean gap but costs Table 3 3.5 points. This, not the short weight, is the convention the paper's arithmetic contradicts |
| 17 | committed vs fully invested | p. 805: "The former scales the portfolio payoffs by the number of pairs that are selected for trading, the latter divides the payoffs by the number of pairs that open during the trading period" | committed divides by pairs selected; fully invested divides by pairs holding a position that day | **MATCH**, with a documented caveat: the paper's words for the fully invested measure say "open during the trading period", the engine divides by pairs *open that day*. The daily reading is confirmed by the paper's daily Table 5 Panel B (REVIEW_NOTES 19.2). The two means' ratio is close but not equal: 1.61-2.02 against the paper's 1.58-1.81, with the "all" column furthest off (disclosed in the check header) |

### Composition tables

| # | rule | the final paper's words | engine | verdict |
|---|---|---|---|---|
| 18 | size deciles | p. 806: "belong to the top three size deciles **using CRSP breakpoints**" | `size_deciles(caps, breakpoint_caps)`, integer decile 1 = largest; breakpoints from NYSE + AMEX common stocks | **SILENT on which breakpoints, settled by measurement.** "CRSP breakpoints" does not distinguish all-stock from NYSE-only; the engine states its reading ("NYSE + AMEX common securities, per the paper's 'using CRSP breakpoints'"). Every build also computes the alternative, deciles on every panel row (`*_allpanel` in `table2_panelB.csv`): `avg_size_decile` 1.88 / 1.90 / 2.21 / 3.47 and `weight_top3_deciles` 0.89 / 0.89 / 0.83 / 0.60 against the paper's 2.54 / 2.71 / 3.41 / 4.57 and 0.78 / 0.74 / 0.58 / 0.40, 14-50% off, where the NYSE + AMEX set is within 10% on seven of the eight (the eighth is 10.1%). The neighbouring rows pick the breakpoints |
| 19 | **average decile difference** | Table 2B row label p. 807: "Average decile difference for **mixed pairs**", values 0.97 / 0.97 / 0.97 / 0.98; text p. 806: "the stocks in mixed pairs differ on average by a single decile" | `avg_decile_diff_mixed_pairs` and `avg_decile_diff_all_pairs`, both computed over **all** pairs - the two rows of `results/replication/tables/table2_panelB.csv` are identical: 1.116, 1.219, 1.611, 2.146 | **BUG, and a composition gap that no decile definition closes.** The bug: one of two rows is miscomputed (the duplicate assignment). Measured against every reading, 2026-10-26 (see `DECILE_PROBE` below): integer all-pairs 1.116 / 1.219 / 1.611 / 2.146, integer mixed-only 1.671 / 1.744 / 2.168 / 2.635, continuous mixed-only 1.570 / 1.653 / 2.141 / 2.603, continuous all-pairs 1.145 / 1.250 / 1.673 / 2.181. The paper's 0.97 / 0.97 / 0.97 / 0.98 is reachable under none of them, and continuous positions also move `avg_size_decile` from 2.65 to 2.13 against the paper's 2.54, i.e. from ✓ to ✗. So the row is not a decile-definition artifact: **our pairs span more size deciles than the paper's do**, which is the same pair-selection gap that shows up in the sector weights of rows 21 and in the tail moments. Relabelling the field is correct bookkeeping, not a fix |
| 20 | share of mixed pairs | Table 2B row: "Average **weight** of pairs from different deciles" 0.66 / 0.69 / 0.75 / 0.82; text: "About two-thirds of the **pairs** combine stocks from different size deciles" | `share_mixed_decile_pairs` (a count share) | **MATCH in effect.** The label says weight, the text says count; equal-weighted pairs make the two identical, so the row is unambiguous once the portfolios are equal-weighted |
| 21 | sector weights, Table 2B | p. 807 Table 2B Panel B, Utilities 0.72 / 0.71 / 0.32 / 0.08 etc. | `sector_of` on every stock; unknown SIC = 0 = Industrials | **MATCH** on the method (see row 6 for the SIC ranges) |

### Statistics with no stated definition

| # | statistic | what the paper gives | engine | verdict |
|---|---|---|---|---|
| 22 | monthly serial correlation | only the row label, in Tables 4, 5 and 7 (e.g. Table 4: 0.14 / 0.24 / 0.19 / 0.12 for the wait-one-day portfolios) | AR(1) of the monthly excess-return series, reindexed to calendar month ends so that only calendar-adjacent months are differenced | **SILENT.** The calendar-month reading is the more literal reading of "monthly", but it is an inference. Two decimal places means the marks on these rows are partly estimator noise; the 20-cohort sample tally should not carry them |
| 23 | round trips, months open (Table 2A) | row labels only: "Standard deviation of number of round trips per pair", "Standard deviation of time open, per pair, in months" | engine counters: one round trip per open-close cycle; months open from open to close dates | **SILENT** on the counting convention (a pair that opens twice in a month, a partial month). Worth a sentence in the check, not a rebuild |

### Tally

| verdict | rows |
|---|---|
| MATCH | 12: 1, 2, 4, 5, 6, 7, 9, 10, 11, 15, 17, 21 (6 and 21 on the method; the SIC ranges are ours and disclosed) |
| MATCH in effect | 1: 20 |
| CONTRADICTORY, engine follows the body text and the draft | 1: 12 |
| DEVIATION, disclosed in the check header | 3: 3, 8, 14 |
| DEVIATION, undisclosed | 1: 16b (Table 1's daily-difference compounding) |
| SILENT | 5: 13 (undisclosed, score-neutral), 16 (reading disclosed), 18 (settled by the neighbouring rows), 22, 23 |
| BUG, plus a composition gap | 1: 19 |

## What this diff changed

1. **The one-day wait is contradictory, not silent** (row 12). The Table 1 note says
   entry only; the body and Table 7 say entry and exit; the draft resolves it in favour
   of entry *and* exit, which is what the engine already does. The repository's
   `OPEN_QUESTIONS.md` has no node for this rule (an "R7" node quoted in the first
   draft of this document lives in an untracked local file from an earlier lineage,
   not in any branch). The only genuinely silent half is the pending-entry skip clause
   (row 13): undisclosed, and measured here as score-neutral on the shipped engine.
2. **The mislabelled decile row is a labelling bug only** (row 19). An earlier review
   comment on #43 suggested that relabelling `avg_decile_diff_mixed_pairs` would move the
   cell; it would not, and the natural follow-up - "then the paper's 0.97 must need
   continuous decile positions" - is **false**, measured. Four readings were computed
   for all 474 cohorts from the cached pair selections: integer all-pairs (shipped),
   integer mixed-only, continuous mixed-only and continuous all-pairs. They give
   1.12 / 1.67 / 1.57 / 1.14 at the top 5, against the paper's 0.97; continuous
   positions also move `avg_size_decile` away from the paper (2.65 -> 2.13 against
   2.54), breaking a row that passes today. The gap is in the pairs, not the deciles.
   Relabelling is still correct bookkeeping, but it is not the fix and the decile
   definition is not either.
3. **The paper's Table 1 = Table 7 identity is about aggregation, not the short weight**
   (rows 16 and 16b). The first draft of this document read the identity as deciding
   `value` over `position`. Measured on both full builds, it does not: our two books
   overshoot our Table 1 Panel B mean by 1-3 bp under either weight, because Table 1
   compounds the daily difference of the books while the paper evidently compounds each
   book first (REVIEW_NOTES 33, 184.0 if Table 1 follows it). The short weight remains a
   disclosed reading (row 16) with a measured trade-off (Table 1 +5.0, Table 3 -8.5 for
   `value`); the aggregation is the undisclosed one (row 16b).
4. **Two rules that were settled by measurement are settled by the text** as well:
   duplicate legs are licensed by "choose a matching partner *for each stock*" (row 5;
   `PAIR_FORMATION.md` section 2 had settled it by the pair count), and the
   overlapping-cohort averaging is licensed verbatim by the Jegadeesh-Titman sentence
   (row 2).

## What stays open, and why no download fixes it

Rows 8, 13, 16, 18, 22 and 23 are genuine silences: the paper does not say which sigma
denominator, whether a wait-1 signal must survive the intervening day, which return
compounds a short position's weight, which decile breakpoints, which autocorrelation
estimator, or how a round trip is counted (row 18 is settled by the neighbouring
rows). Rows 3, 6, 14 and 16b are deviations the engine makes on purpose; 3, 6 and 14
are disclosed in the check header, 16b is not, and neither is row 13's reading.
Nothing in the paper's
bibliography bears on any of them: its 32 references are cointegration theory
(Bossaerts, Engle-Granger, Connor-Korajczyk), factor benchmarks (Fama-French,
Carhart, Jegadeesh-Titman, Lehman), short-selling and trading costs (D'Avolio,
Geczy, Jones-Lamont, Peterson-Fialkowski, Keim-Madhavan), none of which defines an
operational rule. The 1999 draft is the only useful second document, and it is
already in the repository and already scored.

The remaining large gap, the distribution shape (`OPEN_QUESTIONS` Q1 and Q2: 92 of the
291 cells are skewness, kurtosis, minimum or maximum and carry 28.5 of the 187.0
points, as measured in #44; our worst one-day-wait "all" month is -4.02% against the
paper's -2.95%),
is not a wording problem at all. No amount of prose settles which pairs sit in the
tight bands on this CRSP pull.

## DECILE_PROBE: the four readings of the decile-difference row

Measured 2026-10-26 over all 474 cached cohorts, recomputing Table 2B's decile rows
from the cached `pairs.parquet` selections plus the formation-end caps. The control
reproduces the committed `table2_panelB.csv` to four decimals, so the variants are
comparable with it.

| reading | top 5 | top 20 | 101-120 | all | marks vs 0.97 / 0.97 / 0.97 / 0.98 |
|---|---|---|---|---|---|
| A. integer deciles, all pairs (**shipped**) | 1.116 | 1.219 | 1.611 | 2.146 | 0.5 of 4 |
| B. integer deciles, mixed pairs only | 1.671 | 1.744 | 2.168 | 2.635 | 0.0 of 4 |
| C. continuous positions, mixed only | 1.570 | 1.653 | 2.141 | 2.603 | 0.0 of 4 |
| D. continuous positions, all pairs | 1.145 | 1.250 | 1.673 | 2.181 | 0.5 of 4 |
| paper | 0.97 | 0.97 | 0.97 | 0.98 | |

Supporting rows under the two decile definitions:

| row | integer | continuous | paper |
|---|---|---|---|
| `avg_size_decile` top 5 | 2.649 | 2.131 | 2.54 |
| `avg_size_decile` all | 4.632 | 4.122 | 4.57 |
| `share_mixed_decile_pairs` top 5 | 0.664 | 0.664 | 0.66 |

Bucket membership is unchanged by the continuous definition (so `weight_top3` /
`weight_top5` / `share_mixed` are identical), which is why C and D differ from B and A
only in the difference itself. Conclusion: no decile definition reproduces 0.97; the
paper's pairs are more size-adjacent than ours, the same selection gap that drives the
sector-weight misses and the tail moments.

## Reproducing the greps

    pdftotext -layout pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf /tmp/rfs.txt
    pdftotext -layout report/replication/reference/NBER_w7032_1999_draft.pdf /tmp/nber99.txt
    grep -n -i 'standard deviation' /tmp/rfs.txt
    grep -n -i 'one.day\|opening and closing' /tmp/rfs.txt
    grep -n -i 'decile' /tmp/rfs.txt
    sed -n '1245,1280p' /tmp/rfs.txt        # Table 7 long and short means and its note
    grep -n 'trigger_sigma\|sigma' scripts/03_replicate.py