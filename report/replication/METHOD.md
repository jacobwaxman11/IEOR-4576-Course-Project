# Method: the rule as implemented, and where each convention comes from

One home for how this replication reads the paper: the rule row by row, with the
paper's own words quoted for every operational decision (section 1); the formation
stage in detail (section 2); and the historical working interface the code was built
against (section 3). What the engine does today is section 1 plus the code; sections
2-3 carry the measurements that chose the readings. Where they disagree with section
1, section 1 wins, and the disagreement is named.

Page conventions differ by part and each part says so: section 1 quotes the final RFS
article by **printed page** (`pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf`,
printed page = PDF page + 796); section 3 quotes the Yale ICF working paper by **PDF
page**; section 2 by PDF page of the working paper as well. The 1999 NBER draft
(`reference/NBER_w7032_1999_draft.pdf`) is the tiebreaker only, per `EDITION_1999.md`:
it may veto a reading, it cannot justify one.

## 1. The rule, row by row

Compiled 2026-10-26 against `replication/round-nine-evidence` (`708fa9ed`). Corrected the
same day: rows 5, 13, 16 (split into 16 and 16b), 17 and 18, the tally, and the
references to "R" nodes, which belonged to an untracked local file rather than to the
repository's gap tracker (now `GAPS.md`). Brought current on 2026-11-17 against SCORE_LOG row 29
and the engine at `49e4529`: rows 5, 13, 15, 16b, 17 and 19, the tally, the class-D numbers below,
section 2's pair and sector counts and section 3's superseded conventions; each changed row says
what it read before. The same pass re-read every page citation below against the published
edition's own text layer (`paper_rfs.txt`, printed pages 797-827): rows 1-5, 10, 12, 18, 19 and 21
carried page numbers that are not this edition's - mostly one page out, and for Table 2's text the
page of the paragraph rather than of the table - and now give the page the quoted words are printed
on. Every quote in the table was re-checked against that layer at the same time.

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
| `pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf` (RFS 19(3), pp. 797-827) | **the target**. Page numbers below are this edition's, printed page = PDF page + 796, and every quote below is read from its text layer (`paper_rfs.txt`) |
| `Pairs_Trading_RV_Arbitrage_Rule.pdf` (Yale ICF 08-03, Feb 2006) | **not a source**: the working paper, not the published article. It carries no target and supplies no quote or page number here; `scripts/verify_paper_targets.py` rejects it by name (`identify()`), and `COVERAGE.md` records that its values were checked against the article once, on 2026-10-21 |
| `report/replication/reference/NBER_w7032_1999_draft.pdf` | tiebreaker only, per `EDITION_1999.md`: it may veto a reading, it cannot justify one |
| `src/project/*.py`, `scripts/03_replicate.py`, `configs/config.yaml` | the engine as shipped |

Verdict classes:

- **MATCH** - the engine implements the paper's words.
- **CONTRADICTORY** - the paper says two different things; the engine follows one, named below.
- **DEVIATION** - the engine departs from the paper's words deliberately; marked *disclosed* if the
  check header (`scripts/03_replicate.py`, conventions paragraph) already says so, *undisclosed* if not.
- **SILENT** - neither edition says anything; the engine's choice is an inference and must be
  defended by measurement alone.

### The table

#### Sample, pairing, and portfolios

| # | rule | the final paper's words | engine | verdict |
|---|---|---|---|---|
| 1 | formation and trading horizons | p. 803: "We form pairs over a 12-month period (formation period) and trade them in the next 6-month period (trading period). Both 12 months and 6 months are chosen arbitrarily" | `formation_months: 12`, `trading_months: 6`, `COHORT_TRADING_MONTHS = 6` | **MATCH** |
| 2 | overlapping cohorts | p. 806: "trading the pairs at the beginning of every month in the sample period, with the exception of the first 12 months ... The result is a time series of overlapping six-month trading period excess returns. We correct for the correlation induced by overlap by averaging monthly returns across trading strategies that start one month apart as in Jegadeesh and Titman (1993)" | `evaluation.py` equal-weights the cohorts whose trading window covers month *m* | **MATCH**. This is the rule that makes 474 observations out of 474 cohorts; the reproduction of 474 is itself the evidence |
| 3 | liquidity screen | p. 803: "we screen out all stocks from the CRSP daily files that have one or more days with no trade. This serves to identify relatively liquid stocks as well as to facilitate pairs formation" | no-trade day = recorded zero volume (`vol_common`); plus two exclusions the paper does not have (never-moving price; no volume and unchanged price on >95% of formation days) | **DEVIATION, disclosed** ("The paper states none of these three exclusions beyond screening out stocks with a no-trade day") |
| 4 | normalization | p. 803: "construct a cumulative total returns index for each stock over the formation period ... normalized daily 'price' space, where price includes reinvested dividends" | cumulative total-return index, dividends reinvested | **MATCH** |
| 5 | pairing | p. 803: "choose a matching partner **for each stock** by finding the security that minimizes the sum of squared deviations between the two normalized price series. Pairs are thus formed by exhaustive matching" | `select_pairs`: nearest neighbour per stock, duplicate legs allowed, ranked by distance | **MATCH**. "For each stock" settles the duplicate-leg question textually, which section 2.2 of this page had settled only by measurement (0.876 pairs per stock, 2,009 from 2,293, against the paper's 2,057 / 2,317 = 0.888; a one-pair-per-stock rule would give at most 0.5) |
| 6 | sector-restricted pairs | p. 803: "we restrict both stocks to belong to the same broad industry categories defined by Standard and Poors: Utilities, Transportation, Financial, and Industrials. Each stock is assigned to one of these four groups, based on the stock's SIC code. The minimum-distance criterion is then used to match stocks within each of the groups" | `select_pairs_within_groups`, same four labels; SIC membership from `sectors.py` (4811 telephone -> Utilities, 495x -> Industrials) | **MATCH** on the method. The SIC ranges are ours: "the paper gives no SIC ranges" (disclosed) |
| 7 | portfolio definitions | p. 803: "the top 5 and 20 pairs with the smallest historical distance measure, in addition to the 20 pairs after the top 100 (pairs 101-120)"; Table 2 note: "the portfolio '101-120' includes the 20 pairs after the top 100" | `pair_counts: [5, 20, 100]`; 101-120 = ranks 101-120, left empty when the sector has 101-119 | **MATCH** |

#### Trading rules

| # | rule | the final paper's words | engine | verdict |
|---|---|---|---|---|
| 8 | entry trigger | p. 804: "We open a position in a pair when prices diverge by more than **two historical standard deviations, as estimated during the pairs formation period**"; Table 2 note: "Average deviation to trigger opening of pair is the cross-sectional average of two standard deviations of the **pair prices difference**" | 2 x `sigma`, where `sigma` is the formation spread's **root mean square about zero**, `sqrt(SSD/N)` (`features.py`, `sigma="rms"`, the default) | **DEVIATION, disclosed** ("The trigger's sigma is the formation spread's root mean square about zero, sqrt(SSD/N), not its standard deviation about its mean"). Because `rms^2 = std^2 + mean^2` pair by pair, `rms >= std` always, so the paper's literal estimator would put the Table 2A trigger row *below* our 4.09% and *widen* the gap to the paper's 4.76%. The deviation is chosen against the paper's words and still does not close the gap - it is the closest of the readings, not a match |
| 9 | exit rule | p. 804: "We unwind the position at the next crossing of the prices. If prices do not cross before the end of the trading interval, gains or losses are calculated at the end of the last trading day of the trading interval. If a stock in a pair is delisted from CRSP, we close the position in that pair, using the delisting return, or the last available price" | trade reasons `converged` / `end` / `delisted`, with the delisting row as terminal | **MATCH** |
| 10 | position sizes | pp. 804-805: "we open a long-short position ... payoffs by going **one dollar short** in the higher-priced stock and **one dollar long** in the lower-priced stock" | `L = np.ones(n)`, `S = np.ones(n)`; both reset to 1.0 on every reopen | **MATCH**. The long leg is the *lower*-priced stock, which is what the sign convention of the spread test already encodes |
| 11 | entry and exit timing (no wait) | p. 806: "positions are opened at the end of the day that prices diverge and closed at the end of the day of price convergence" | open at the signal close, returns accrue from the next day; close at the crossing close | **MATCH** |
| 12 | **the one-day wait** | **contradictory.** Table 1 note, p. 807: "The results in Panel B correspond to a strategy that **delays the opening** of the pairs position by one day." Body, p. 811: "the pairs are traded with a one-day delay before **opening and closing** a position to minimize the effect of the bid-ask bounce." Table 7 note, p. 821: "formed and traded according to the **'wait one day'** rule" | wait 1 opens at the close of the following day and closes at the close of the day after the crossing | **CONTRADICTORY**; the engine follows the body text and Table 7, and the 1999 draft agrees explicitly: "we initiate positions in each pair on the day following the divergence and liquidate on the day following the crossing" |
| 13 | wait-1 pending entry | **silent** in both editions. The draft states the rule without any persistence condition: "initiate positions in each pair on the day following the divergence" | "skipping signals whose prices **cross on that intervening day**" (`models.py`, wait=1 docstring) | **SILENT**, **disclosed** in the check header since `REVIEW_NOTES` 47 ("the paper states no such condition, and dropping it changes no mark"; this row read *undisclosed* until 2026-11-17), and **score-neutral**. Measured on the shipped engine, 2026-10-26 (full 474-cohort rebuild with the clause removed, everything else at `708fa9ed` defaults): Tables 1-3 stay at 187.0 of 291 and the total at 213.5 of 323, with no cell changing its mark. Values move by a basis point or less (Table 1 Panel B top 5 mean 0.69% both ways, top 20 0.88% -> 0.87%; Table 2 Panel A top 5 round trips 2.24 -> 2.26), and Figure 1 is unaffected (it is no-wait). The clause therefore has neither a textual nor a measured reason. Numbers quoted elsewhere for it (180.0 alone, 182.5 with 495x, against 184.5) come from a local experimental lineage with payoff-count returns that was never shipped, and do not apply to this engine |
| 14 | same-issuer pairs | **silent** | a stock is never matched with another security of the same `permco` | **DEVIATION, disclosed** |

#### Return computation

| # | rule | the final paper's words | engine | verdict |
|---|---|---|---|---|
| 15 | portfolio weighting | p. 805, eq. (2)-(3): `r_P,t = sum_i w_i,t r_i,t / sum_i w_i,t`, `w_i,t = w_i,t-1 (1 + r_i,t-1)`; "The daily returns on the long and short positions are calculated as value-weighted returns in the following way ... the daily returns are compounded to obtain monthly returns. This has the simple interpretation of a **buy-and-hold strategy**" | value-weighted daily returns with compounding weights; `CACHE_FORMAT = 7` | **MATCH** at portfolio level |
| 16 | reversal factor | **stated** as the top three prior-month deciles minus the bottom three (p. 813, footnote 7: Carhart 1997 with a one-month sort), but **silent** on the short leg the Table 8 regressions fit | "constructing a short-term reversal factor measured as the excess return of stocks in the top three deciles of prior-month return minus the return on stocks in the bottom three deciles" | the equal-weighted bottom three prior-month deciles less the T-bill (losers only), by default | **DEVIATION, disclosed**: no long-short construction reaches the printed before-1989 factor sd of 0.0723 (ST_Rev 0.0259), while the losers-only series gives 0.0685 with the +0.81/+0.79 implied market/SMB correlations. That hypothesises an error in the paper, so it is a hypothesis rather than a reading; ST_Rev is printed unscored and --reversal-factor st_rev restores row 18 (REVIEW_NOTES sections 51 and 61) |
| 16 | **short leg weighting** | eq. (3), `w_i,t = w_i,t-1 (1 + r_i,t-1)`, is stated for "the long and short positions" without saying whether `r` is a shorted stock's return or the short position's | `--short-weights position` (default): the short's weight compounds at the position's own return, `prod(1 - r_short)`, floored at 0; `--short-weights value` compounds at the shorted stock's return | **SILENT, reading disclosed** in the check header ("The short-position weight is also our reading ... SCORE_LOG.md row 12"). Measured both ways (REVIEW_NOTES 29, SCORE_LOG rows 12-13): `value` scores 183.5 of 291 against 187.0 (Table 1 +5.0, Table 3 -8.5). Table 7 does **not** separate them: on the full sample our long-minus-short exceeds our Table 1 Panel B mean by 3.2 / 1.2 / 1.5 / 2.6 bp under `position` and by 3.1 / 1.2 / 1.4 / 1.4 bp under `value`, against the paper's -0.1 / 0 / 0 / 0. That residual is row 16b, not this row. Table 7's short-book level leans to `position`: "all" 0.878% (`position`) and 0.708% (`value`) against the paper's 0.908% |
| 16b | **monthly aggregation of the two books** | p. 805: "the daily returns are compounded to obtain monthly returns"; Table 7 long - short = Table 1 Panel B to one basis point (top 5: 0.01245 - 0.00501 = 0.00744 against 0.00745; the other three columns agree to the last digit) | `portfolio_monthly` compounds **each book** to a monthly return and subtracts (`REVIEW_NOTES` 54, `CACHE_FORMAT` 6 onwards); Table 7 compounds the same two books | **MATCH**, and the check header says so ("Tables 1 and 3 compound the long and the short book to monthly returns and then subtract"). This row read **DEVIATION, undisclosed** until it was brought current on 2026-11-17; the engine had compounded the daily *difference* of the books for Tables 1 and 3 until SCORE_LOG row 17 (2026-11-02), when the paper's own order replaced it (`REVIEW_NOTES` 54; the book-first order had scored 184.0 of 291 against 187.0 when first measured, `REVIEW_NOTES` 33). The only series still built on the literal §2.3 daily difference is the *committed* capital on the engine path, which is what the paper's §2.3 sentence describes |
| 17 | committed vs fully invested | p. 805: "The former scales the portfolio payoffs by the number of pairs that are selected for trading, the latter divides the payoffs by the number of pairs that open during the trading period" | committed divides by pairs selected; fully invested divides by pairs holding a position that day | **MATCH**, with a documented caveat: the paper's words for the fully invested measure say "open during the trading period", the engine divides by pairs *open that day*. The daily reading is confirmed by the paper's daily Table 5 Panel B (REVIEW_NOTES 19.2). The two means' ratio is close but not equal: recomputed from `table1.csv` on 2026-11-17 it is 1.54-1.75 against the paper's own printed means' 1.59-1.80, five of the eight columns within 5%, with the two top-20 ratios the furthest off (-8.7% and -8.1%) and Panel B's "all" 6.3% low, rather than the "all" column alone. The check header still describes committed returns as the fully-invested return scaled by the share of selected pairs holding a position - the hybrid that SCORE_LOG row 18 replaced on the engine path with the paper's payoffs over the pairs selected (`evaluation.py`, `portfolio_monthly`) - and still quotes the older 1.61-2.02 range with the "all" column furthest off. That sentence is generated by `scripts/03_replicate.py`, outside this page; it is recorded here and not changed, because changing it regenerates the check |

#### Composition tables

| # | rule | the final paper's words | engine | verdict |
|---|---|---|---|---|
| 18 | size deciles | p. 809: "belong to the top three size deciles **using CRSP breakpoints**" | `size_deciles(caps, breakpoint_caps)`, integer decile 1 = largest; breakpoints from NYSE + AMEX common stocks | **SILENT on which breakpoints, settled by measurement.** "CRSP breakpoints" does not distinguish all-stock from NYSE-only; the engine states its reading ("NYSE + AMEX common securities, per the paper's 'using CRSP breakpoints'"). Every build also computes the alternative, deciles on every panel row (`*_allpanel` in `table2_panelB.csv`): `avg_size_decile` 1.88 / 1.90 / 2.21 / 3.47 and `weight_top3_deciles` 0.89 / 0.89 / 0.83 / 0.60 against the paper's 2.54 / 2.71 / 3.41 / 4.57 and 0.78 / 0.74 / 0.58 / 0.40, 14-50% off, where the NYSE + AMEX set is within 10% on seven of the eight (the eighth is 10.1%). The neighbouring rows pick the breakpoints |
| 19 | **average decile difference** | Table 2B row label p. 809: "Average decile difference for **mixed pairs**", values 0.97 / 0.97 / 0.97 / 0.98; text p. 809: "the stocks in mixed pairs differ on average by a single decile" | `avg_decile_diff_mixed_pairs` (the mean gap **among mixed pairs**, the paper's row) and `avg_decile_diff_all_pairs`, kept beside it in `table2_panelB.csv`; the scored row reads 1.67 / 1.74 / 2.17 / 2.64 | **FIXED, and a composition gap that no decile definition closes.** The duplicate assignment this row reported until 2026-11-17 made both fields print the all-pairs mean; it was fixed in SCORE_LOG row 17 and the scored row now carries the quantity the paper names (`REVIEW_NOTES` 54). Measured against every reading, 2026-10-26 (see `DECILE_PROBE` below): integer all-pairs 1.116 / 1.219 / 1.611 / 2.146, integer mixed-only 1.671 / 1.744 / 2.168 / 2.635, continuous mixed-only 1.570 / 1.653 / 2.141 / 2.603, continuous all-pairs 1.145 / 1.250 / 1.673 / 2.181. The paper's 0.97 / 0.97 / 0.97 / 0.98 is reachable under none of them, and continuous positions also move `avg_size_decile` from 2.65 to 2.13 against the paper's 2.54, i.e. from ✓ to ✗. So the row is not a decile-definition artifact: **our pairs span more size deciles than the paper's do**, which is the same pair-selection gap that shows up in the sector weights of rows 21 and in the tail moments. The relabelling fixes the bookkeeping and the composition gap of the row itself stays. |
| 20 | share of mixed pairs | Table 2B row, p. 809: "Average **weight** of pairs from different deciles" 0.66 / 0.69 / 0.75 / 0.82; text p. 809: "About two-thirds of the **pairs** combine stocks from different size deciles" | `share_mixed_decile_pairs` (a count share) | **MATCH in effect.** The label says weight, the text says count; equal-weighted pairs make the two identical, so the row is unambiguous once the portfolios are equal-weighted |
| 21 | sector weights, Table 2B | p. 809 Table 2B Panel B, Utilities 0.72 / 0.71 / 0.32 / 0.08 etc. | `sector_of` on every stock; unknown SIC = 0 = Industrials | **MATCH** on the method (see row 6 for the SIC ranges) |

#### Statistics with no stated definition

| # | statistic | what the paper gives | engine | verdict |
|---|---|---|---|---|
| 22 | monthly serial correlation | only the row label, in Tables 4, 5 and 7 (e.g. Table 4: 0.14 / 0.24 / 0.19 / 0.12 for the wait-one-day portfolios) | AR(1) of the monthly excess-return series, reindexed to calendar month ends so that only calendar-adjacent months are differenced | **SILENT.** The calendar-month reading is the more literal reading of "monthly", but it is an inference. Two decimal places means the marks on these rows are partly estimator noise; the 20-cohort sample tally should not carry them |
| 23 | round trips, months open (Table 2A) | row labels only: "Standard deviation of number of round trips per pair", "Standard deviation of time open, per pair, in months" | engine counters: one round trip per open-close cycle; months open from open to close dates | **SILENT** on the counting convention (a pair that opens twice in a month, a partial month). Worth a sentence in the check, not a rebuild |

#### Tally

| verdict | rows |
|---|---|
| MATCH | 14: 1, 2, 4, 5, 6, 7, 9, 10, 11, 15, 16b, 17, 19, 21 (6 and 21 on the method; the SIC ranges are ours and disclosed; 16b and 19 follow the paper's own order as of REVIEW_NOTES 54) |
| MATCH in effect | 1: 20 |
| CONTRADICTORY, engine follows the body text and the draft | 1: 12 |
| DEVIATION, disclosed in the check header | 3: 3, 8, 14 |
| SILENT | 5: 13 (disclosed since `REVIEW_NOTES` 47, score-neutral), 16 (reading disclosed), 18 (settled by the neighbouring rows), 22, 23 |
| no longer a verdict: the undisclosed 16b and the row-19 bug | 0 (both fixed; see the rows) |

#### The default-off readings of rounds 10-11

Rounds 10 and 11 added seven options to `scripts/03_replicate.py`, each a reading of a rule or a
statistic above that the paper leaves open. None is a default, none moves a mark, and every one is
a sensitivity: the default path is byte-identical to the pre-change baseline's tables and prints
411.0 of 865.

| option | what it reproduces | note | status |
|---|---|---|---|
| `--delist-last-px {off,merge,nondistress,all}` | row 9's delisting sentence (p. 804) read by CRSP delisting-code class: the chosen classes book the last available price on the terminal row instead of CRSP's delisting return. `merge` = 2xx mergers, `nondistress` = mergers plus exchange and listing moves, `all` = every class | `REVIEW_NOTES` 94 | default off; sensitivity. `merge` 411.5, `nondistress` 412.0, `all` 412.0, every mark that moves a band-edge tip; the 7 Table 2 B cells it was named for are composition statistics and cannot move |
| `--pair-decile {own,long,short}` | Table 6's draw: the caption's singular "within the same last-month performance decile" (p. 819) read as one decile per pair (the long leg's or the short leg's) against leg-by-leg matching | `REVIEW_NOTES` 97 | default off (`own`, leg by leg); sensitivity. `long` reads 14.0 of the 48 Table 6 cells and 412.0 on the whole check, `short` 12.0 and 410.0, against the shipped 13.0 and 411.0; `long`'s +1.0 is the choice of decile, not the reading |
| `--moments {raw,sample}` | the shape rows' skewness and kurtosis: raw Pearson central moments (the caption's "Absolute kurtosis is reported", p. 807) or the bias-corrected spreadsheet moments | `REVIEW_NOTES` 95 | default off (`raw`); sensitivity. `sample` 410.5 of 865, 1 cell, on a band edge |
| `--quantile-method {linear,lower,higher,nearest,midpoint,hazen,weibull,median_unbiased,normal_unbiased}` | Table 5's VaR percentiles, which the paper does not define: pandas' linear interpolation or another numpy method | `REVIEW_NOTES` 95 | default off (`linear`); sensitivity. `lower` 409.5 and `midpoint` 410.0 of 865, both on the 1% row |
| `--sign-zero {strict,nonpositive}` | the "Observations with excess return < 0" row boundary: a strictly negative month, or also a zero month | `REVIEW_NOTES` 95 | default off (`strict`, the printed label); sensitivity. 411.0, 0 cells, because no month of any portfolio's 474 is exactly zero |
| `--nw-correction {none,df}` | the Newey-West standard errors: without or with statsmodels' n/(n-k) small-sample factor, which the paper states neither way | `REVIEW_NOTES` 95 | default off (`none`); sensitivity. 411.0, 0 cells; each standard error moves 0.106% and each t 0.106% |
| `--ibbotson-market {geometric,excess}` | Table 4's Ibbotson market leg: a geometric difference like the other three premia, or the arithmetic S&P 500 minus the T-bill the caption's words describe | `REVIEW_NOTES` 95 | default off (`geometric`, the leg the other three share); sensitivity. 411.0, 0 cells; the two legs correlate 0.9999977 |

The user has not decided whether the five of `REVIEW_NOTES` 95 stay in the driver; this table
records them as they exist today.

### What this diff changed

1. **The one-day wait is contradictory, not silent** (row 12). The Table 1 note says
   entry only; the body and Table 7 say entry and exit; the draft resolves it in favour
   of entry *and* exit, which is what the engine already does. The repository's
   the gap tracker (now `GAPS.md`) has no node for this rule (an "R7" node quoted in the first
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
   Relabelling was the fix for the duplicated field (SCORE_LOG row 17, REVIEW_NOTES 54):
   `avg_decile_diff_mixed_pairs` now averages mixed pairs only and the scored row is
   4 ✗, as the composition gap predicts. The decile definition is still not the fix.
3. **The paper's Table 1 = Table 7 identity is about aggregation, not the short weight**
   (rows 16 and 16b). The first draft of this document read the identity as deciding
   `value` over `position`. Measured on both full builds, it does not: our two books
   overshoot our Table 1 Panel B mean by 1-3 bp under either weight, because Table 1
   compounds the daily difference of the books while the paper evidently compounds each
   book first (REVIEW_NOTES 33, 184.0 if Table 1 follows it). That is now the shipped
   aggregation (REVIEW_NOTES 54), so row 16b is a MATCH and the short weight is the only
   one of the two left as a disclosed reading (row 16), with a measured trade-off
   (Table 1 +5.0, Table 3 -8.5 for `value`).
4. **Two rules that were settled by measurement are settled by the text** as well:
   duplicate legs are licensed by "choose a matching partner *for each stock*" (row 5;
   section 2.2 of this page had settled it by the pair count), and the
   overlapping-cohort averaging is licensed verbatim by the Jegadeesh-Titman sentence
   (row 2).

### What stays open, and why no download fixes it

Rows 8, 13, 16, 18, 22 and 23 are genuine silences: the paper does not say which sigma
denominator, whether a wait-1 signal must survive the intervening day, which return
compounds a short position's weight, which decile breakpoints, which autocorrelation
estimator, or how a round trip is counted (row 18 is settled by the neighbouring
rows). Rows 3, 6 and 14 are deviations the engine makes on purpose and all three are
disclosed in the check header; row 16b stopped being one when the paper's own aggregation
became the shipped one (REVIEW_NOTES 54), and row 13's reading is disclosed in the check header
(`REVIEW_NOTES` 47) and score-neutral as measured.
Nothing in the paper's
bibliography bears on any of them: its 32 references are cointegration theory
(Bossaerts, Engle-Granger, Connor-Korajczyk), factor benchmarks (Fama-French,
Carhart, Jegadeesh-Titman, Lehman), short-selling and trading costs (D'Avolio,
Geczy, Jones-Lamont, Peterson-Fialkowski, Keim-Madhavan), none of which defines an
operational rule. The 1999 draft is the only useful second document, and it is
already in the repository and already scored.

The remaining large gap, the distribution shape (`GAPS.md` section 2: class D is 160 of the
865 cells and carries 65.5 points at SCORE_LOG row 29; on the 291-cell set of #44 it was 92 cells and 28.5 of
187.0 points; the check's worst one-day-wait "all" month is -3.98% against the paper's
-2.95%),
is not a wording problem at all. No amount of prose settles which pairs sit in the
tight bands on this CRSP pull.

### DECILE_PROBE: the four readings of the decile-difference row

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

### Reproducing the greps

    pdftotext -layout pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf /tmp/rfs.txt
    pdftotext -layout report/replication/reference/NBER_w7032_1999_draft.pdf /tmp/nber99.txt
    grep -n -i 'standard deviation' /tmp/rfs.txt
    grep -n -i 'one.day\|opening and closing' /tmp/rfs.txt
    grep -n -i 'decile' /tmp/rfs.txt
    sed -n '1245,1280p' /tmp/rfs.txt        # Table 7 long and short means and its note
    grep -n 'trigger_sigma\|sigma' scripts/03_replicate.py

## 2. Pair formation: normalization, distance, σ and sector mapping

Code: `src/project/features.py` (normalization, distance, pairing, σ) and
`src/project/sectors.py` (sector map). Tests: `tests/test_features.py`,
`tests/test_sectors.py`. Page numbers in this section are **PDF pages** of the
Yale ICF working paper (`Pairs_Trading_RV_Arbitrage_Rule.pdf`).

How the replication forms pairs, and where each choice comes from in Gatev,
Goetzmann & Rouwenhorst (2006), `Pairs_Trading_RV_Arbitrage_Rule.pdf`. Page
numbers are **PDF pages** (the number printed on the page is one lower).

Code: `src/project/features.py` (normalization, distance, pairing, σ) and
`src/project/sectors.py` (sector map). Tests: `tests/test_features.py`,
`tests/test_sectors.py`.

### 1. Normalized prices

**Paper.** "Next, we construct a cumulative total return index for each stock
over the formation period" (§2.1, PDF p. 11, first paragraph). The pairing
space is "normalized, cum-dividend prices, i.e. cumulative total returns with
dividends re-invested" (§1.3, PDF p. 9). Figure 1's trading-period lines are
"the normalized price paths with dividends re-invested" (§2.2, PDF p. 12).

**Implementation** (`normalized_prices`). For a window of daily CRSP total
returns `r_t` (dividends included):

    P_0 = 1,   P_t = (1 + r_1)(1 + r_2)…(1 + r_t)

The formation window (12 months) and the trading window (6 months) are each
rebased separately. A missing return counts as 0 (price unchanged); in the
eligible formation universe this is essentially never needed (0 missing
returns in the 1975-07 cohort, 1 stock in 1990-01), because eligibility
already requires a valid price on every day.

**Review point A: the rebasing day.** `P_0 = 1` is set at the *close of the
first day* of the window, so the first day's return is not in the index (1 of
252 formation days, 1 of ~126 trading days). The alternative is to start at
the previous close, so `P_0 = 1 + r_0`. The paper does not say which. Changing
it shifts every SSD slightly and requires re-running all cohorts.
*Measured 2026-10-26 (REVIEW_NOTES section 47):* starting at the previous close
scores 183.5 of 291 against 187.0 and moves the Figure 1 pair from rank 4 to
rank 3 with one trade six days off the chart, so the shipped day is kept.

### 2. Distance and pairing

**Paper.** "We then choose a matching partner for each stock by finding the
security that minimizes the sum of squared deviations between the two
normalized price series. Pairs are thus formed by exhaustive matching in
normalized daily 'price' space" (§2.1, PDF p. 11). Portfolios are "the top 5
and 20 pairs with the smallest historical distance measure, in addition to the
20 pairs after the top 100" (§2.2, PDF p. 12).

**Implementation** (`ssd_matrix`, `select_pairs`).

- `D_ij = Σ_t (P_it − P_jt)²` over the formation window, for all stocks at
  once (`a² + b² − 2ab`, float64; about 0.1 s for 4,000 stocks).
- Every stock `i` takes its nearest neighbour `j* = argmin_{j≠i} D_ij`. The
  pair set is the unique unordered `{i, j*}`, so a stock can sit in more than
  one pair (it is the nearest neighbour of several stocks), and mutual
  nearest neighbours count once.
- Pairs are ranked by `D` ascending; ties break on (permno_1, permno_2).

**Check.** This rule gives pairs ≈ 0.876 × stocks (2,009 pairs from 2,293
stocks per cohort under `vol_common`, the mean over 474 cohorts; it read 0.875, 2,013 from
2,301, when this section was written on 2026-10-16, before the same-issuer and near-frozen-quote
exclusions of `REVIEW_NOTES` 18). The paper's own numbers give
2,057 / 2,317 = 0.888 (2,057 pairs: notes to Tables 5, 8 and 9, PDF pp. 39,
42, 43; 2,317 stocks: Table 3 caption, PDF p. 37).
A rule that paired each stock only once would give ≤ 0.5 × stocks.

### 3. The 2σ trigger

**Paper.** "We open a position in a pair when prices diverge by more than two
historical standard deviations, as estimated during the pairs formation
period" (§2.2, last line of PDF p. 12 to the first line of p. 13). Table 2's
note (PDF p. 36): "Average deviation to trigger opening of pair is the
cross-sectional average of two standard deviations".

**Implementation** (`select_pairs`, column `sigma`).

    σ = sqrt(SSD / N) = sqrt(mean over the formation window of (P_1t − P_2t)²)

the root mean square of the spread about zero, computed on the same
normalized prices as the distance (`--trigger-sigma rms`, the default since
REVIEW_NOTES section 21). `--trigger-sigma std` gives the standard deviation
about the spread's mean (ddof = 0), which this section described until then;
the checks below were run with it. In trading, a pair
opens when `|P_1t − P_2t| > 2σ` with both stocks rebased to 1 at the start
of the trading window. σ was recomputed independently for the top-20 pairs of
5 cohorts (1966-03, 1977-09, 1985-06, 1994-11, 2001-04) and agrees to 1e-9.

**Review point B: ddof.** With 252 observations, ddof = 0 vs 1 changes σ by
0.2%; immaterial, but the paper does not say.

**Review point C: open gap.** On the shipped RMS trigger the four columns read
0.0409 / 0.0466 / 0.0715 / 0.173 against the paper's 0.0476 / 0.0528 / 0.0756 / 0.169
(top 5 / top 20 / 101-120 / all, the check's Table 2 A row); this paragraph read
0.041 / 0.068 / 0.165 (top 20 / 101-120 / all) when it was written on 2026-10-16, while the
trigger was still the spread's standard deviation (row 8; RMS since `REVIEW_NOTES` 21). Our
top pairs are closer than GGR's. Neither A nor B is large enough to explain the gap.
Stale-quote stocks (flat prices, tiny σ) are part of it under
`vol_common`, but the stage-1 universe without them is also low (0.0436).

### 4. Sector mapping

**Paper.** The only description is §2.1 (bottom of PDF p. 11 to the top of
p. 12): "the same broad industry categories defined by Standard & Poors:
Utilities, Transportation, Financial and Industrials. Each stock is assigned
to one of these four groups, based on the stock's SIC code. The minimum-
distance criterion is then used to match stocks within each of the groups."
There are no SIC ranges, no appendix and no cited mapping. The targets are
the Table 3 caption counts, "156 Utilities, 61 Transportation, 371
Financials, and 1729 Industrials" (PDF p. 37), and the Table 2 Panel B sector
weights (PDF p. 36).

**Map (our reading of the S&P groups)** (`sector_of`):

| Sector | SIC codes |
|---|---|
| Transportation | 4000–4799 |
| Utilities | 4900–4999 and telephone 4811, but **not** waste management (4950–4959), which has been Industrials since 2026-10-24 (`src/project/sectors.py`, SCORE_LOG row 12) |
| Financials | 6000–6999 |
| Industrials | everything else |

The telephone code was 4810–4819 until REVIEW_NOTES section 20 narrowed it to
4811, the 1972 manual's telephone code (`--telephone-sic 481x` restores the
old map). The alternatives tested in the tables below were run with 4810–4819.

**Unknown SIC (new in this PR)** (`resolve_sic`, `sectors_for`). CRSP codes
an unknown SIC as 0. On the formation-end day, about 106 stocks per cohort
have a dated SIC of 0 (276 per cohort in the 1970s, 143 in the 1980s, about 1
in the 1990s), mostly early Nasdaq listings. The same gaps are in legacy CRSP:
today's dated `siccd` equals legacy `crsp.dsenames.siccd` on 100% of 181,344
stock-cohorts checked, including every 0. For about 97 of the 106 stocks CRSP
has no earlier code either; their first code appears only later, so a strictly
point-in-time rule cannot classify them.

The old map counted them all as Industrials. They are now filled, in order,
from:

1. the stock's own earliest nonzero dated SIC in the CRSP panel
   (`earliest_known_sic`): covers 91.5% of them;
2. the CIZ security-header SIC (`header_sic`).

In effect this is **point-in-time SIC where CRSP has one, otherwise the
stock's nearest known code**: it gives exactly the same counts as "last
earlier code, else next later code". 3.7 stocks per cohort stay unknown and
remain Industrials. The fallback can use a code recorded after the formation
window; that only affects the label, never trading.

**Effect** (`vol_common` universe, 79 cohorts, every 6th of 474):

| Sector labels | Utilities | Transportation | Financials | Industrials |
|---|---:|---:|---:|---:|
| Paper (Table 3 caption) | 156 | 61 | 371 | 1,729 |
| Dated SIC only (before) | 158.5 (+1.6%) | 59.0 (−3.3%) | 318.7 (−14.1%) | 1,759.3 (+1.8%) |
| **Dated → own history → header** | **161.4 (+3.5%)** | **61.2 (+0.3%)** | **350.0 (−5.7%)** | **1,722.9 (−0.4%)** |

**Alternatives tested** (same 79 cohorts; Utilities / Transportation /
Financials / Industrials per cohort):

| SIC timing rule | U | T | F | I | worst cell |
|---|---:|---:|---:|---:|---|
| Paper | 156 | 61 | 371 | 1,729 | |
| Strict point-in-time (0 → Industrials) | 158.5 | 59.0 | 318.7 | 1,759.3 | F −14.1% |
| Point-in-time + carry earlier code forward | 158.5 | 59.4 | 321.7 | 1,755.9 | F −13.3% |
| Mid-formation dated SIC | 158.1 | 58.9 | 317.5 | 1,761.0 | F −14.4% |
| **This PR (nearest known code)** | **161.4** | **61.2** | **350.0** | **1,722.9** | F −5.7% |
| Backfilled: last code as of 2002-12 | 167.0 | 62.7 | 341.6 | 1,724.3 | F −7.9% |
| Backfilled: today's CIZ header | 165.7 | 63.6 | 340.2 | 1,726.0 | F −8.3% |
| Backfilled: legacy `hsiccd` | 165.0 | 63.7 | 343.9 | 1,722.9 | F −7.3% |
| Dropping unknown-SIC stocks | 158.5 | 59.0 | 318.7 | 1,653.2 | F −14.1% |

**Stocks per cohort by sector, before and after the 495x change (current check):**

| map | U | T | F | I | worst cell |
|---|---:|---:|---:|---:|---|
| shipped until 2026-10-24: U = 4811 + 49xx | 144 | 61.4 | 347 | 1,740 | U −7.7% |
| shipped from 2026-10-24: 495x moved to Industrials | 137 | 61.4 | 347 | 1,748 | U −12.1% |

The change moves seven Utilities stocks to Industrials and leaves Financials alone; the earlier
draft of this section read 161 / 350 / 1,723 for the pre-change row, which was the 2026-10-17
configuration before the telephone code, the header-SIC fallback and the RMS trigger. Those
older figures, and the variant rows below, are directional only:

| SIC map variant (measured 2026-10-17, before #22/#25/#26/#29) | U | T | F | I | worst cell |
|---|---:|---:|---:|---:|---|
| U = all of 48xx + 49xx | 187 | 61 | 350 | 1,697 | U +19.8% |
| U = 49xx only | 136 | 61 | 350 | 1,748 | U −13.0% |
| U excludes sanitary services 495x | 154 | 61 | 350 | 1,730 | F −5.7% |
| F excludes real estate 65xx | 161 | 61 | 333 | 1,740 | F −10.3% |

The telephone-plus-49xx Utilities group fits best. **Update 2026-10-24:** the map
now classifies waste management (495x) as Industrials, following GICS. How S&P's
contemporaneous scheme classified it is still **not verified**, and the 1999
NBER draft is neutral on it (its edition score is unchanged), so this is a
classification choice rather than a recovered fact. It was adopted because it
scores 178.5 -> 183.5, with six of the eight gains inside the Utilities 101-120
band (REVIEW_NOTES section 24); the cost is the Utilities count, now 137 against
the paper's 156. It does not move the Table 2 Panel B top-pair weights.

**Review point D: the remaining Financials gap (about 21 stocks).** No SIC
timing rule or map variant tested moves Financials past 350. About 70
non-financial stocks per cohort carry a financial code somewhere in their
CRSP record (and 44 the reverse), so a SIC difference specific to GGR's 2003
release could in principle close it, but it cannot be observed. Universe
composition is the other candidate: adding closed-end funds (legacy share
code 14, about 78 per cohort, all financial) overshoots to about 430. The
paper's single sentence does not say which SIC field was used or how
unknown codes were treated.

### 5. Not in this PR, and known issues downstream

The formation universe (which stocks are eligible), the trading engine and
the return aggregation are not in this PR. Their review, done after this PR
was opened, found three problems (two misunderstandings in the coordinator's spec,
section 3 below, one panel-build bug) that affect the downstream tables but
none of the code here:

1. **One-day wait.** Panel B and Table 3 delay both the opening and the
   closing trade by one day (2006 §3.3, PDF p. 18; 1999 NBER version, Table V
   caption). The spec delayed only the opening. **Fixed and shipped** in
   `src/project/models.py` (`exit_pending`); `test_wait1_delays_the_exit_and_earns_the_extra_day`
   and `test_wait1_forced_exit_is_not_delayed` pin it, and forced exits stay on the
   last day of the window, as PDF p. 16 has it (REVIEW_NOTES section 3).
2. **Portfolio returns.** The spec divided daily payoffs by the sum of each
   pair's cumulative capital account, which can reach zero or go negative.
   That denominator is **gone**: no reported cell uses it, and the readings survive
   only as `employed_account` / `committed_account` (REVIEW_NOTES section 8). What
   ships today is the value-weighted long and short books of eq. (2)-(3), not the
   pair counts — section 15 replaced the counts and
   section 3's portfolio-return row is the historical description; the counts
   remain in the cache for comparison and against the 1999 draft.
3. **Delisting returns.** CIZ dates each delisting row after the last trade
   with exchange code `X`; the panel build kept only N/A/Q rows, so no
   delisting return was ever applied. This biased returns upward, most in
   weak pairs and small stocks. **Fixed and shipped** in
   `src/project/data.py::_clean_year`, which keeps `dlydelflg == 'Y'` rows whatever
   their exchange and carries `dlyret`; `test_delisting_row_off_exchange_is_kept_but_never_eligible`
   and `test_offexchange_delisting_row_survives_build_and_load` pin it, and
   61,540 trades (2.1% of 2.97M) now close on a delisting (REVIEW_NOTES section 7).

Table 3 results are therefore not reported here. With either return reading,
the less-similar pairs (every sector's "all" portfolio, and Transportation,
whose ~49 pairs per cohort are mostly such pairs) earn about twice the
paper's returns; the cause is under investigation and is not the sector map
(Transportation's stock count matches: 61.4 vs 61).

## 3. The working interface (historical)

What follows is the interface the three replication workers coded against in
October 2026, kept verbatim because tests, docstrings and `REVIEW_NOTES.md`
sections still cite it. It is **historical**: where it differs from the shipped
engine, section 1's rows win and the difference is named there. The five that
matter: the spread σ is the formation spread's root mean square about zero, not
the `std(P_i − P_j)` this spec first wrote (row 8; `--trigger-sigma rms`); the
no-trade day is recorded zero volume, not `dlyprcflg == 'TR'` (row 3;
`--universe vol_common`); trading prices continue the formation normalization
rather than being rebased to 1 ("Trading-price normalization" below); the
one-day wait delays the exit too, corrected inside this spec on 2026-10-16 (row
12); and Tables 1 and 3 compound each book to a monthly return before
subtracting (row 16b), a reading this spec's portfolio-return row predates. Rows
of the conventions table that the shipped engine contradicts carry a
**superseded** note. The worker lanes and memory notes below describe an
abandoned coordination scheme, not the current workflow.

All three replication workers code against this file. The coordinator owns it; if a worker
needs a change, it must `ask` rather than edit. Paper references are to
`Pairs_Trading_RV_Arbitrage_Rule.pdf`, sections 2.1–2.3 (pp. 10–14) and Tables 1–2 (pp. 34–35).

### Target of this stage

Reproduce **Table 1**, Panels A and B, and **Table 2**, Panel A, for July 1963 to December
2002 (474 months). Anchor numbers for the top-20 portfolio are 1.436% per month fully
invested and 0.805% on committed capital with no waiting, and 0.895% / 0.520% when waiting
one day.

### Conventions (fixed; flag disagreements, do not silently change)

| Item | Rule |
|---|---|
| Universe (row level, time-varying) | `securitytype='EQTY' AND securitysubtype='COM' AND sharetype='NS' AND primaryexch IN ('N','A','Q')` |
| Trading calendar | The dates in `data/raw/wrds_api/daily_indexes.parquet` (`dlycaldt`). |
| Traded day (**superseded**: this is the stage-1 `price_common` universe ("Universe variants" below), not the shipped `vol_common`, whose no-trade day is recorded zero volume - row 3 above) | `dlyprcflg == 'TR'` and `dlyprc > 0`. |
| Daily total return | `dlyret`. On the terminal row (`dlydelflg == 'Y'`), `dlyret` already includes the delisting return, so **never add `delisting.delret`**. If `dlyret` is null on that row, use 0.0, which closes at the last available price (paper §2.2). The −30% and −100% long-leg variants are later sensitivity runs, not the base case. |
| Formation eligibility (§2.1) | The stock passes the universe filter, and on **every** calendar date in the 12-month formation window it has a row with traded day = True. One missing or non-traded day excludes it, and so does a zero return on every day of the window (a price that never moves: no evidence of trading, and a constant normalized price that pairs at distance zero). It is also excluded when more than 95% of its formation days have no recorded volume and an unchanged price (`--max-stale-share`, near-frozen quotes), and a stock is never matched with another security of the same issuer (same permco, `--same-issuer`); both are our reading, see REVIEW_NOTES section 18. |
| Cohorts | One cohort starts every month. Formation is months [m−12, m−1] and trading is months [m, m+5]. The first trading month is 1963-07 (formation 1962-07..1963-06). The last cohort starts 2002-12, and only its months up to 2002-12 are used. |
| Normalized price (**superseded** for the trading window: "Trading-price normalization" below is the shipped `--normalization continued` reading, in which trading prices continue the formation index instead of being rebased) | Cumulative total-return index `P_t = Π_{s≤t}(1+r_s)`, rebased to 1 on the first day of the window. Formation and trading are rebased separately: trading starts at 1 on the first trading-period day, as in Figure 1. |
| Distance | `D_ij = Σ_t (P_it − P_jt)²` over the formation window, using normalized formation prices. |
| Pairing | Each eligible stock i is matched with `j* = argmin_{j≠i} D_ij`. The set of pairs is the unique unordered {i, j*}. Pairs are ranked by `D`, ascending, and ties are broken by (permno_lo, permno_hi). A stock may appear in more than one pair. |
| Portfolios | top 5 = ranks 1–5; top 20 = ranks 1–20; "101–120" = ranks 101–120; "all" = every pair. |
| Spread σ (**superseded**: row 8 above is the shipped estimator, the root mean square about zero, `sqrt(SSD/N)`) | `σ_ij = std(P_i − P_j)` over the formation window (ddof=0). |
| Entry (§2.2) | The position is closed and `|P_i,t − P_j,t| > 2σ_ij` at the close of day t, using trading-normalized prices. Go $1 long the lower-priced stock and $1 short the higher-priced one. |
| Wait rule | `wait=0`: open at the close of signal day t, so returns accrue from t+1. `wait=1` (Panel B): open at the close of t+1, so returns accrue from t+2; skip if the prices crossed on t+1. `wait=0` closes at the close of the first day the sign of `P_i − P_j` differs from its sign at opening (a crossing); **`wait=1` closes at the close of the day after the crossing** (paper §3.3: "postpone the trades to the day following the crossing"; corrected 2026-10-16, the original spec delayed only the entry). Forced exits are never delayed. |
| Forced exits | At the close of the last trading-period day; or on a stock's terminal row (`dlydelflg=='Y'`), or its last available row, whichever comes first. That day's return is included, then the pair is closed and cannot reopen. |
| Re-opening | After a convergence exit, the pair may open again. |
| Missing return inside the trading period | Treat as 0.0 (price unchanged) for marking to market; count these in diagnostics. |
| Pair daily payoff | For an open position, the leg values start at $1 at opening and are bought and held: `L_t = L_{t−1}(1+r_long,t)`, `S_t = S_{t−1}(1+r_short,t)`. Pair payoff on day t is `π_t = (L_t − L_{t−1}) − (S_t − S_{t−1})`. On closing, cash `L − S` is realized; the realized cash earns 0 (paper footnote 6). |
| Portfolio return (§2.3, PDF p. 14; corrected 2026-10-16, 2026-10-19, 2026-10-24) | Each trade holds $1 long and $1 short, bought and held. Eq. 2 is read **across the portfolio**: "the daily returns on the long and short positions are calculated as value-weighted returns", each position weighted by eq. (3) applied to its own return since the trade opened: a long by its value `L`, a short by `Q = Π (1 − r_short)`, floored at 0 (780 of 2,968,816 Table 1 positions, all outside top 5 / top 20 / 101-120), which shrinks as the shorted stock rises (`--short-weights position`, default since 2026-10-24; `value` weights a short by the stock's value `S` instead). **Employed / fully invested** `R_t = Σ dL / Σ L_t−1 − Σ Q_t−1 r_short,t / Σ Q_t−1` over the positions open on day t (a day with none is skipped): the value-weighted return of the long book minus that of the short book. **Committed** scales it by the share of selected pairs holding a position, `R_t × n_t / N` (0 on a day with none). Fully-invested/committed ratios: ours 1.70/1.72/1.61/1.94 no wait and 1.66/1.71/1.62/2.02 one-day wait (stock-value short weights: 1.68/1.71/1.60/1.88 and 1.64/1.69/1.61/1.90); paper 1.67/1.78/1.59/1.80 and 1.61/1.72/1.58/1.81. The short weight is our reading; REVIEW_NOTES section 29 has the evidence and the objections. Either way a short leg that has run up 3-5× no longer counts as a −300% to −500% loss on a $1 pair. Daily returns compound to monthly. *Kept for comparison:* `employed_count` (summed payoffs `Σ_p π_p,t / n_t`, the convention of 2026-10-18), `committed_count` (`Σ_p π_p,t / N`), `employed_nbar` (period-average count `n̄`, until 2026-10-18; "all" ratio 1.57), `employed_literal`, and the superseded account readings `committed_account` / `employed_account` (dividing by `Σ_p w_p,t−1`; accounts reach zero or go negative after a short leg multiplies). |
| Monthly returns | Compound `R_t` within each calendar month for each cohort. The strategy's month-m return is the **equal-weighted average across the cohorts active in month m**: up to 6, fewer at the start of the sample (Jegadeesh–Titman 1993). |
| Statistics | Mean; Newey–West standard error with **6 lags** and t-statistic; median; standard deviation (ddof=1); skewness; excess-or-raw kurtosis (report raw Pearson kurtosis, where normal = 3, matching the paper's magnitudes); min; max; share < 0. Scored since SCORE_LOG row 15: Table 5 Panel A's first-order serial correlation (lag-1 correlation of calendar-adjacent months) and 1/5/10/25 percentiles (linear interpolation) of the one-day-wait monthly series, Table 8's mean and standard deviation of the same series before and after 1988-12 and its five-factor regressions, Table 4's Sharpe ratios and two factor regressions, and Figure 4's printed correlations. |

### Data artifacts (produced by worker C, read by D and E)

`data/processed/crsp/daily/{YYYY}.parquet` holds one file per year, 1961–2026 (git-ignored), with these columns:

| column | type | meaning |
|---|---|---|
| `permno` | int64 | |
| `date` | date32 | trading date |
| `ret` | float64 | daily total return per the rule above; NaN when unknown |
| `traded` | bool | traded day |
| `terminal` | bool | `dlydelflg=='Y'` row |
| `siccd` | int64 (nullable) | for Table 3 later |
| `exch` | string | N / A / Q |

Rows are already restricted to the universe filter and de-duplicated: there is one row per (permno, date), and a duplicate is an error.

### Python API (module ownership in brackets)

```python
# project.data  [worker C]
def build_daily_panel(years: range | None = None, force: bool = False) -> None
    """Raw -> data/processed/crsp/daily/{YYYY}.parquet, one year at a time (RAM ~21 GB free)."""
def load_daily(start: date, end: date, columns: list[str] | None = None) -> pd.DataFrame
    """Long panel for [start, end] from the processed files (pyarrow filters, only needed years)."""
def trading_calendar(start: date, end: date) -> pd.DatetimeIndex
def formation_universe(start: date, end: date) -> pd.Index
    """PERMNOs eligible per §2.1 over the formation window [start, end]."""

# project.features  [worker D]
def normalized_prices(returns: pd.DataFrame) -> pd.DataFrame
    """Wide (dates x permno) returns -> cumulative index rebased to 1 on row 0. NaN -> 0 for compounding."""
def ssd_matrix(prices: pd.DataFrame) -> np.ndarray
    """Pairwise sum of squared deviations, vectorized ((a-b)^2 = a^2 + b^2 - 2ab), float64, diag=+inf."""
def select_pairs(prices: pd.DataFrame) -> pd.DataFrame
    """Columns: rank, permno_1, permno_2 (permno_1 < permno_2), distance, sigma. Ranked ascending."""

# project.models  [worker D]
def simulate_cohort(pairs: pd.DataFrame, trade_returns: pd.DataFrame, terminal: pd.DataFrame,
                    wait: int = 0) -> CohortResult
    """trade_returns/terminal are wide (trading dates x permno). Returns per-pair daily
    returns r_p,t (dates x pair rank) plus a trade log: rank, open_date, close_date, reason in
    {'converged','end','delisted'}, long_permno, short_permno, payoff."""
@dataclass
class CohortResult:
    pair_returns: pd.DataFrame   # dates x rank, r_p,t (0 when closed)
    opened: pd.Series            # rank -> bool, opened at least once
    trades: pd.DataFrame         # trade log above
    pair_payoffs: pd.DataFrame   # dates x rank, pi_p,t
    long_payoffs: pd.DataFrame   # dates x rank, dL (0 when closed); short_payoffs likewise
    long_values: pd.DataFrame    # dates x rank, L_t-1 of an open position; short_values likewise

# project.evaluation  [worker E]
def portfolio_daily(result: CohortResult, ranks: list[int], capital: str) -> pd.Series
    """Value-weighted long book minus short book (employed); committed scales it by n_t / N."""
def cohort_monthly(daily: pd.Series) -> pd.Series            # month-end index -> compounded return
def overlap_average(cohort_months: dict[pd.Timestamp, pd.Series]) -> pd.Series
def summary_stats(monthly: pd.Series, nw_lags: int = 6) -> pd.Series   # Table 1 rows
def trading_stats(results: dict, ranks: list[int]) -> pd.Series          # Table 2 Panel A rows

PORTFOLIOS = {"top5": range(1, 6), "top20": range(1, 21), "101-120": range(101, 121), "all": None}
```

`scripts/03_replicate.py` (worker E) loops over cohorts. For each cohort it:

1. finds the formation universe;
2. builds wide formation returns and selects pairs;
3. builds wide trading returns and terminal flags;
4. runs `simulate_cohort` for wait 0 and wait 1;
5. computes committed and employed returns for each portfolio.

It writes `results/replication/tables/table1.csv`, `table2_panelA.csv`, `table2_panelB.csv` and `monthly_returns.parquet`, plus a markdown comparison to the paper numbers in `results/replication/tables/table1_vs_paper.md`. It supports `--start/--end` and `--workers N` (process pool; about 1.3 GB per worker). Table 3, Figure 1 and the replication check are steps of the same script (see "Driver steps" below).

### Shared rules for workers

- **Working directory:** the repository root. Python: `.venv/bin/python`. `project` is installed in editable mode.
- **No git commit, push or stash.** The coordinator commits, and only to the private remote.
- **No WRDS access is needed.** Everything is local. Do not call `wrds_connection()`.
- **Stay in your lane:** write only the files in your contract. If you need something from another module, code against the signature above, use a local stub in your tests, and `ask` if the signature is insufficient.
- **Memory:** about 21 GB is free (other jobs share the machine). Never load more than about 2 years of the panel at once.
- **Testing:** every function gets a pytest test in your `tests/` file. Small synthetic data with hand-checkable answers is preferred, and `ruff check` must be clean.
- **Ask, don't guess:** if the paper is ambiguous, follow this file and record the ambiguity under "Open questions" in your `*_NOTES.md`.
- **Done signal:** a single `orca orchestration send --type worker_done ... --outcome succeeded|failed --files-modified <csv>`, with a 3-sentence body: what works, test count, and open issues.

---

### Stage 2 amendments (2026-10-16). These supersede stage 1 wherever they conflict.

### Why
The stage-1 universe averaged 1,801 stocks per cohort; the paper averages 2,317 (Table 3 caption:
156 Utilities, 61 Transportation, 371 Financials, 1,729 Industrials), and its Table 9 note of
2,057 "all" pairs implies about 2,356. A local diagnostic of no-trade rules shows the gap
is the **no-trade definition**. CRSP has no volume for Nasdaq before Nov-1982 (bid/ask quotes only).
A screen that treats only *recorded zero volume* as no trade keeps those stocks and reproduces
the paper's counts. Do & Faff (2010) and Rubesam's public replication also use a volume screen.

### Universe variants (the coordinator chose these; do not invent others)

Every day-level flag below is evaluated on each panel row. A stock is eligible for a formation
window when it has a row on **every** trading-calendar date of the window, every one of those rows
passes the share filter, and every one passes the day rule.

| name | day rule (a row counts as a traded day when …) | share filter | role |
|---|---|---|---|
| `vol_common` | `prc_ok and not vol_zero` | `common` | **primary** |
| `volpos_common` | `prc_ok and vol_pos` (missing volume counts as no trade; Rubesam) | `common` | sensitivity |
| `vol_ns` | `prc_ok and not vol_zero` | `ns` (also keeps closed-end funds and ETFs) | sensitivity |
| `price_common` | `tr` (stage-1 rule) | `common` | baseline; already run, cache archived |

Definitions per raw row:
- `prc_ok` = `dlyprc` is not null and `abs(dlyprc) > 0`
- `vol_zero` = `dlyvol == 0` (null is **not** zero)
- `vol_pos` = `dlyvol > 0` (null is False)
- `tr` = `dlyprcflg == 'TR' and dlyprc > 0`
- `common` = `securitytype=='EQTY' and securitysubtype=='COM' and sharetype=='NS'`
- `ns` = `sharetype=='NS'`

Expected averages over the 474 cohorts, from `volume_rules.csv` (computed with month-end share
attributes, so row-level results may differ by a few stocks):

| variant | Util | Trans | Fin | Ind | Total |
|---|---|---|---|---|---|
| `vol_common` | 159 | 59 | 321 | 1,762 | 2,302 |
| `vol_ns` | 159 | 59 | 406 | 1,764 | 2,388 |
| `price_common` | 147 | 51 | 230 | 1,373 | 1,801 |

`volpos_common`: the 1,933 (Fin 318) quoted earlier used the NS-only share filter (it includes closed-end funds). Worker F's row-level `common` result, 149 / 52 / 234 / 1,412 = 1,847, is the correct expectation.

### Panel schema v2 (`data/processed/crsp/daily/{YYYY}.parquet`; replaces the stage-1 table)
Rows: every raw row with `primaryexch IN ('N','A','Q')`, **any share type**, plus every
delisting row (`dlydelflg=='Y'`) whatever its exchange; one row per (permno, date). A
duplicate is an error. *Corrected 2026-10-16:* CIZ dates the delisting row after the last
trade with `primaryexch = 'X'`, so the original exchange filter dropped all of them and no
delisting return was ever applied. Delisting rows have `tr`, `prc_ok` and `vol_pos` False:
they are never eligible trading days.

| column | type | meaning |
|---|---|---|
| `permno` | int64 | |
| `date` | date32 | |
| `ret` | float64 | as in stage 1 (terminal-row rule unchanged) |
| `terminal` | bool | `dlydelflg=='Y'` |
| `siccd` | int64 | 0 = unknown |
| `exch` | string | N / A / Q |
| `cap` | float64 | `dlycap` (CRSP market cap, $000s); NaN when unknown |
| `tr`, `prc_ok`, `vol_zero`, `vol_pos`, `common`, `ns` | bool | as defined above |

The stage-1 column `traded` is removed. `load_daily` is unchanged.

### API changes
```python
# project.data  [worker F]
UNIVERSES: dict[str, tuple[str, str]]   # name -> (day-rule name, share-filter name), the four variants above
def formation_universe(start, end, universe: str = "vol_common") -> pd.Index
def universe_flags(panel: pd.DataFrame, universe: str) -> pd.Series   # row-level bool, pure; used by formation_universe

# project.evaluation  [worker G]
def size_deciles(caps: pd.Series, nyse_caps: pd.Series) -> pd.Series
    """1 = largest. Breakpoints are the deciles of nyse_caps (NYSE stocks, CRSP convention)."""
def sector_of(siccd) -> str   # 'Utilities' | 'Transportation' | 'Financials' | 'Industrials'
def composition_stats(pairs_info: dict, ranks) -> pd.Series   # Table 2 Panel B rows
```

### Driver changes (`scripts/03_replicate.py`) [worker G]
- `--universe NAME` (default `vol_common`) is passed to `formation_universe`.
- Cohort cache: `data/processed/replication/{NAME}/cohorts/YYYY-MM/`.
- Outputs: `results/replication/tables/` and `results/replication/figures/` for the primary
  `vol_common` universe; other variants write to `tables/{NAME}/` and `figures/{NAME}/`.
- The stage-1 run lives at `.../price_common/` and must stay readable: `--universe price_common
  --aggregate-only` regenerates its tables from the cache without simulating anything.
- The trading period loads returns for the pair stocks from the full v2 panel, regardless of share
  filter, so a share-type change inside the trading period does not cut a stock off early.

### Sector map (Table 2 Panel B and Table 3)
| sector | SIC |
|---|---|
| Utilities | 49xx, or 4811 (telephone; `--telephone-sic 481x` gives the older 4810-4819) |
| Transportation | 40xx–47xx |
| Financials | 60xx–69xx |
| Industrials | everything else, including 0 (unknown) |


### Trading-price normalization (corrected 2026-10-16, evening)
Trading prices **continue the formation normalization**: each stock's normalized price at the
close of the last formation day is its starting level, and every trading-day return (day 1
included) compounds from there; the spread `P_1 − P_2` is measured in that same space. A pair
that ended formation more than 2σ apart can open at the close of day 1, and it converges when
the formation-normalized prices cross. Evidence: GGR Figure 1 (RFS 2006, p. 804) starts both
Kennecott and Uniroyal near 1.10 on day 0; our data give 1.1006 and 1.106 for the same pair and
reproduce its five openings. The earlier convention (rebased to 1 on the first trading day) is
kept as `--normalization rebased` and `simulate_cohort(start_levels=None)`.

### Driver steps (`scripts/03_replicate.py --steps`, 2026-10-17)
One script produces every replication output; `--steps` picks a subset of
`tables,table3,figure1,check` (default: all four).

| step | output (primary universe) |
|---|---|
| `tables` | `results/replication/tables/table1.csv`, `table2_panelA.csv`, `table2_panelB.csv`, `universe_summary.csv`, `monthly_returns.parquet`, `table1_vs_paper.md` |
| `table3` | `results/replication/tables/table3.csv`, `table3_counts.csv` |
| `figure1` | `results/replication/figures/figure1.png`, `figure1.json` |
| `check` | `results/replication/tables/replication_check.md` |

- **One job per cohort** (`build_cohort`, run by `run_jobs` in a process pool, `--workers N`):
  formation and trading data are loaded once; the job forms unrestricted pairs and
  within-sector pairs (`select_pairs_within_groups`), simulates them and caches
  `pairs.parquet`, `w{wait}_trades.parquet`, `w{wait}_opened.parquet`, `monthly.parquet` (each
  cohort's monthly returns for Tables 1 and 3) and `summary.json` (Table 2 Panel A components,
  Panel B composition, stock / pair / sector counts), written last. Aggregation reads only these
  small files.
- Sector labels come from `project.sectors.sectors_for` (dated SIC on the formation-end day,
  else the stock's earliest known SIC, else the CIZ header SIC); Table 2 Panel B uses the same
  labels.
- Figure 1 reads the cached wait-0 trades of the 1963-08 cohort for Kennecott (12706) and
  Uniroyal (14912); the indicator is up from the opening day to the closing day.
- The check compares Figure 1 (rank, trade days within ±3, formation-end levels within 2% of
  1.10) and every cell of Tables 1, 2, 3 and 7 with the paper: ✓ within 10%, ~ within 25%, ✗
  further. Table 7's cells are the long and the short book of each portfolio (mean, Newey-West
  standard error, standard deviation, serial correlation), computed by `portfolio_legs` and
  cached as the `long_book` / `short_book` capitals. Since SCORE_LOG row 15 it also scores Table 4,
  Table 5 Panel A, Table 8 and Figure 4's printed correlations (`write_risk_tables`). It states the conventions that are our reading of the paper (n̄, continued
  normalization, the zero-volume no-trade rule).
- **Cache stamp** `cache_meta.json` = `{"normalization", "format": 7, "monthly_aggregation":
  "books"}` plus every formation and engine option with its value (`exclude_same_issuer`,
  `max_stale_share` when set, `telephone_sic`, `trigger_sigma`, `short_weights`, and, only when
  they are not the default, `size_deciles_top`, `long_delisting_loss`, `waste_sic`, `trigger_mult`,
  `fresh_divergence`, `capital_base`, `demote_frozen` / `demote_frozen_share`, `share_classes` /
  `share_classes_map` and `processed_source`; `formation_options` in `scripts/03_replicate.py`).
  Format 7 adds each cohort's `daily.parquet`, the series Table 5 Panel B scores (`REVIEW_NOTES`
  62); format 6 added the book-first monthly aggregation (row 16b). This item read
  `{"normalization", "format": 5}` until it was brought current on 2026-11-17. Building stamps the cache
  first and refuses to build into a cache stamped differently unless `--force`; reading
  (`--aggregate-only`, `figure1`) only verifies and never writes the stamp.
- **Engine and evaluation are array code.** `simulate_cohort` runs its day loop in a numba
  kernel and returns `pair_payoffs` (the daily dollar payoff of each pair) next to
  `pair_returns`, plus `open_day` / `close_day` in the trade log. The trade log has `n * T`
  slots: a pair closes at most once a day, even when it closes and reopens on the same day.
  `portfolio_daily` sums `pair_payoffs` directly, so a zero or negative account no longer
  drops a pair's payoff; for inputs without payoffs it rebuilds them from returns, a missing
  return counting as no change. `portfolio_daily` and `trading_components` are numpy.
- **Figure 1 indicator** (`project.plotting.position_indicator`): a trade (open day, close day)
  is held from the close of the open day to the close of the close day, so days
  `open_day .. close_day - 1` are marked and `step(where="post")` draws the line up from the
  open day to the close day. A full
  rebuild of 474 cohorts takes under two minutes on 15 workers (about 1 GB each).
