# Coordinator review: data provenance and worker code (2026-10-16)

The shipped score and its history are in `SCORE_LOG.md`; the scores quoted below are the
results of the experiment described in each section.

Scope: Hao asked whether the stage-2 data issues (stale Nasdaq quotes in
`vol_common`) are download problems or fixable, and for an independent review
of the workers' logic. Scratch scripts used for these checks are not part of
the repo; every number below can be reproduced from the files named.

## 1. Data provenance: is anything wrong with the download?

| check | result |
|---|---|
| Raw CIZ daily files vs `data/raw/wrds_api/manifest.json` | 66/66 files: row counts match (103,119,940 total) and sha256 hashes match |
| CIZ vs legacy SIZ `crsp.dsf`, per permno-month, 1962–2002 (`legacy/dsf_monthly_counts.parquet`, server-side counts) | totals identical: closing-trade days (CIZ `TR` = SIZ `prc>0`) 41,488,387; bid/ask days (CIZ `BA` = SIZ `prc<0`) 14,797,393; volume>0 days 44,995,981. Month-level differences are only (a) SIZ NULL counts on exchange X and (b) CIZ's extra delisting-day row |
| Pre-1983 Nasdaq | both vintages: 6,464,516 `BA` days, 7,011 `TR` days, 110,098 days with volume — CRSP has no Nasdaq trades or volume before Nov 1982 in either product |
| Raw → processed panel (stale-quote stocks 58828, 58967, 20715) | processed rows reproduce raw `dlyret`, `dlycap`; 58828 is `BA` on all 253 days of 1980 with a frozen 3.5/4.5 quote and NULL volume |
| Delisting returns | in the **raw download**, the terminal row (`dlydelflg='Y'`) is dated after the last trade and its `dlyret` equals `delisting.delret` on 1,910/1,910 matched rows (1975, 1985, 1995, 2001). **Correction (later the same day): these rows never reached the panel.** They carry `primaryexch='X'`, and the build kept only N/A/Q rows, so the processed panel had 0 delisting rows and no delisting return was ever applied. This entry originally said "applied exactly once"; that was checked on the raw data only. Fixed in the build (see section 7). |

| Day-level values for the stale-quote stocks (all 374 permnos in stale top-20 pairs, 1,578,330 stock-days; local WRDS diagnostic) | legacy `crsp.dsf` vs CIZ: returns 100% identical, volume 100% identical (NULL on 100% of 1973 and 99% of 1978 bid/ask days in both), negative legacy price ⇔ CIZ `BA` on 100% of rows, CIZ `dlybid`/`dlyask` = legacy `bidlo`/`askhi` on 100% of bid/ask days; the 0.05% price differences are storage rounding (−0.04688 vs 0.046875) |

**Conclusion: no download defect; one build defect (delisting rows dropped, section 7).** The stale quotes are genuine
CRSP content: pre-1983 Nasdaq stocks only have bid/ask midpoints and no volume
field. Which of them count as "no trade" days is a rule choice, not a data fix:

- the CRSP convention (negative price / `BA` = no closing trade) is
  `price_common`: literal, clean top pairs, but 1,800 stocks vs 2,317;
- "no trade = recorded zero volume" (`vol_common`) matches the count
  (2,301) but admits stocks whose quote does not move for months. 327 of
  2,301 stocks per cohort (867 of 2,129 in the 1970s) have `ret == 0` on at
  least half their formation days; they reach 17% of top-5 pairs (41% in the
  1970s) and 24 of the 25 top-20 pairs whose capital account goes negative.

## 2. Code review

| component (worker) | verdict | how checked |
|---|---|---|
| `_clean_year`, `universe_flags`, `formation_universe` (C, F) | correct | read; F's 474-cohort permno-exact regression; raw-vs-processed spot check above |
| `normalized_prices`, `ssd_matrix`, `select_pairs` (D) | correct | read; formation σ recomputed independently for top-20 of 5 cohorts, equal to 1e-9 |
| `simulate_cohort`, wait 0 (D) | correct | independent re-implementation of the trading rule, top-20 of cohorts 1966-03, 1977-09, 1985-06, 1994-11, 2001-04: every trade's open date, close date and payoff identical (1e-8) |
| `simulate_cohort`, wait 1 (D, spec by coordinator) | **bug in INTERFACES.md, fixed** | see 3 |
| `portfolio_daily`, `overlap_average`, `summary_stats`, `trading_stats` (E) | correct implementation of the spec | read; NW SE via statsmodels HAC, 6 lags |
| `size_deciles`, `sector_of`, `composition_stats`, driver (G) | correct | independent recompute of Panel B on 5 cohorts, exact match |
| paper targets in `scripts/03_replicate.py` | transcription errors, corrected | checked cell by cell against the RFS tables |

## 3. Fixed: the one-day-wait rule delayed only the entry

The paper (§3.3) defines Panel B as postponing "the trades to the day
following the crossing", and its transaction-cost argument charges half a
spread at divergence and "again" at convergence (2 round trips). INTERFACES.md
line 30 (the coordinator's spec) delayed only the opening trade. Fixed in
`src/project/models.py`: under `wait=1` a crossing at the close of day t is
executed at the close of t+1; forced exits (delisting, last available row, end
of period) are not delayed. Tests: `test_wait1_delays_the_exit_and_earns_the_extra_day`,
`test_wait1_forced_exit_is_not_delayed`; `test_wait1_opens_one_day_later`
updated. Wait-0 results are unchanged; all wait-1 caches and tables were
rebuilt.

## 4. Known fragilities (documented, not changed)

- **Negative pair accounts.** Pair return = payoff / account, with the
  account starting at $1. When a short leg multiplies, the account goes to or
  below zero and the "return" changes sign or explodes. In `vol_common` 2.2%
  of all pairs touch ≤ 0; in the top 20 it is 25 pairs (24 involve stale
  quotes) vs 1 in `price_common`. It causes the −133% top-5 fully-invested
  month (Feb 1981). Committed-capital returns are much less affected because
  the denominator sums all selected pairs.
- **Zero account with an open position.** One pair (vol_common 1976-06, rank
  2421, "all" only) produces non-finite daily returns; the tables stay finite.
- **Rebasing day.** Normalized prices start at 1 on the close of the first
  day of each window, so that day's return is excluded from the spread. The
  paper does not specify; the effect is one day in 126 / 252.
- **Fully invested.** Superseded by section 9: the denominator is now n̄, the
  average number of pairs holding a position per day in the cohort.

## 5. Results after the wait-1 fix (all four universes rebuilt)

Superseded by section 9 and `REPLICATION_CHECK.md`; kept for the history of the fix.

| universe | top-20 wait 0: committed / fully invested | top-20 wait 1: committed / fully invested |
|---|---|---|
| paper | 0.805% / 1.436% | 0.520% / 0.895% |
| **vol_common** | 0.701% / 1.404% | **0.424% / 0.812%** |
| volpos_common | 0.961% / 1.888% | 0.629% / 1.179% |
| vol_ns | 0.927% / 1.906% | 0.529% / 1.015% |
| price_common | 0.961% / 1.890% | 0.630% / 1.182% |

The waiting cost (wait 0 minus wait 1) for vol_common top 20 is 0.28% committed
and 0.59% fully invested vs the paper's 0.285% and 0.54%; before the fix it
was 0.17% and 0.38%. GGR's 1999 NBER version (w7032, Table V caption) states
the rule explicitly: positions open "the day following the day that prices …
diverge" and close "the day following the next crossing of prices".

## 6. Other replications (checked 2026-10-16)

None reports GGR's per-sector stock counts or the 2,317 universe.
Rubesam (rubetron/Pairs_trading) uses a legacy CRSP CSV export, a
volume > 0 screen, global top-20 distance pairs, no sectors, and delays only
the entry: 0.67% / 1.25% for wait 1 (our `volpos_common` before the fix:
0.75% / 1.43%). The Faff line (Do & Faff 2010, 2012; Rad, Low & Faff 2016)
uses share codes 10/11 plus a volume filter, and Rad, Low & Faff also drop
the smallest size decile and stocks under $1, which removes the stale
microcaps but is not GGR's rule. Zhu (2024) uses SIC divisions; S&P 500
replications use current GICS.

## 7. Delisting rows were dropped by the panel build (found and fixed 2026-10-16)

A trade-level attribution of the "all" portfolio found no trade, among about
1.5 million across 474 cohorts, closed for a delisting. CIZ gives every
delisting row `primaryexch = 'X'` (179 / 565 / 984 rows in 1975 / 1990 /
2001; the stock was on Q, A or N the day before), and `_clean_year` kept only
N/A/Q rows, so the panel had none and delisted stocks were closed at their
last traded price without the delisting return. The strategy is long the
stock that has fallen, which is the one most likely to delist for
performance, so this biased returns upward, most of all in weak pairs and
small stocks.

Fix: `_clean_year` keeps delisting rows whatever their exchange and sets
their day-rule flags False, so they never count as eligible days
(`test_delisting_row_off_exchange_is_kept_but_never_eligible`). After the
rebuild the panel has all 179 / 565 / 984 delisting rows, and the formation
universes are unchanged (vol_common and price_common identical on 5 cohorts
checked across decades).

## 8. Portfolio returns: account weights replaced by pair counts (2026-10-16)

INTERFACES.md divided summed pair payoffs by the sum of each pair's
cumulative capital account. Accounts reach zero or go negative after a short
leg multiplies, which flipped signs (a loss reported as a +10% return in
`test_negative_account_does_not_flip_the_sign`) and produced the −133% month.
The paper divides payoffs by a pair count (§2.3, PDF p. 14), as Rubesam's
independent implementation also does. `portfolio_daily` now uses counts;
the old reading survives as `committed_account` / `employed_account`.

**Superseded on 2026-10-19.** Section 15 replaced the counts with the value-weighted long and
short books of eq. (2)-(3), which is what ships; `employed_count` / `committed_count` remain
only for comparison and for scoring the 1999 draft by the measure it states. The account
denominator this section removed has never come back.

## 9. Continued normalization, n̄ denominator and Figure 1 (2026-10-16/17)

- **Trading prices continue the formation normalization.** GGR Figure 1 (RFS 2006, p. 804)
  starts Kennecott and Uniroyal near 1.10 on trading day 0, not at 1.0. Our cached 1963-08
  cohort gives 1.1006 / 1.106 at the end of formation, ranks the pair 4th, and its five wait-0 trades open and close
  within two days of the chart: (8, 35), (46, 56), (76, 83), (85, 99), (108, 125) against
  about (7, 35), (46, 55), (74, 82), (86, 99), (108, 126). The rebased convention (1.0 on
  day 1) is kept as `--normalization rebased`.
- **Fully invested = Σπ / n̄.** n̄ is the average number of pairs holding a position per day
  over the cohort. The paper's fully-invested/committed ratios (1.61-1.81 in Table 1) equal
  N / n̄; a day-by-day count inflates the "all" portfolio through E[1/n] > 1/E[n].
- **One driver, one check.** `scripts/03_replicate.py` now writes Tables 1-3, Figure 1 and
  `replication_check.md`; the current check is copied to `REPLICATION_CHECK.md`.

## 10. Universe: what matches and what does not (2026-10-16/17)

| universe rule | pairs/cohort 1962-97 (NBER 1999: 1,870) | pairs/cohort 1962-2002 (RFS: 2,057) | Financials (RFS: 371) |
|---|---|---|---|
| trade-price screen, common | 1,272 | 1,562 | 229 |
| volume > 0, common | 1,319 | 1,605 | 235 |
| **zero volume = no trade, common (primary)** | **1,794** | **2,013** | **350** |
| zero volume = no trade, all NS share types | 1,849 | 2,093 | 434-437 |

Both editions of the paper need the pre-Nov-1982 Nasdaq quote-only stocks (CRSP has no
volume for them in any table or release we checked), and both fall between "common only" and
"common plus funds". Utilities (160 vs 156) and Transportation (61 vs 61) match; Financials
are 21 short, and every share or SIC variant either undershoots (343-350) or overshoots
(434-501).

## 11. CRSP edition (vintage) checks (2026-10-17)

- WRDS holds only the current CRSP releases; no archived editions are available to us.
- CRSP's December 2002 annual release (CRSPAccess 2.75, the data GGR's RFS tables were built
  on) lists 24,620 securities in the daily file; our 1962-2002 panel has 24,627.
- 267 stock-file release notes (Dec 2005 to Jan 2023 from crsp.org; 2002-2006 from CRSP's old
  sites via the Internet Archive) itemise 88 SIC and 225 share-code edits that touch
  1962-2002. Reversing them moves Financials by about +0.6 stocks per cohort; the 2003
  recoding of five closed-end funds from share code 10 to 14 adds at most 0.8.
- No stock-file notes for 1998-2001 survive online (the archived `release_notes98.pdf` is the
  mutual-fund database).

Conclusion: the security set is the same as GGR's; the Financials gap reflects an unstated
classification or share-type choice, not the data edition.

## 12. Other replications, revisited (2026-10-17)

No public replication reproduces Table 3 or reports sector stock counts. Rubesam
(rubetron/Pairs_trading, 2023) pulls no SIC codes and reports only top-20 statistics:

| top 20, one-day wait | GGR | Rubesam | ours (vol_common) |
|---|---|---|---|
| committed capital | 0.52% | 0.67% (+29%) | 0.43% (-17%) |
| fully invested | 0.90% | 1.25% (+39%) | 0.72% (-19%) |

Zhu (2024) restricts pairs to SIC groups of its own; S&P 500 replications use current GICS
sectors. The tightest pairs (top 5 and top 20) are the cells most sensitive to which stocks are
in the universe, in every replication we found.

## 13. PR review fixes, rebuild and speed-up (2026-10-17)

Review comments on PRs #1-#4 were checked and all taken:

| PR | finding | fix | changes results? |
|---|---|---|---|
| #1 | `ssd_matrix` on an empty window returned zeros (self-pairs) | raises `ValueError` | no (never hit) |
| #1 | `earliest_known_sic` relied on file row order | explicit date sort | no |
| #2 | delisting (`X`) rows not pinned end to end | build-and-load round-trip test | no |
| #3 | **positions opened after a stock's last row, on frozen prices** | signals and pending opens need both legs alive | **yes** |
| #3 | delayed convergence on the last day labelled `end` | labelled `converged` | no (no table reads it) |
| #4 | cache stamped during `--aggregate-only` | reading verifies only; building stamps | no |
| #4 | Figure 1 indicator one day late | indicator from open day to close day | plot only |
| #4 | n̄ convention only in a docstring | stated in the check report | no |
| #4 | capital mask chosen by a hand-kept tuple | `MASK_CAPITALS`, computed once | no |

The frozen-price trades were 0.9% of all trades (2,500 of 287,024 in 90 cohort-wait checks).
After the rebuild, Table 1 cells within 10% of the paper go from 29 to 30 and Table 3 from 37 to
39; Table 2 is unchanged. Top-5 means rise 2-3% (toward the paper); pairs opened per cohort
under wait 1 fall from 1,917.8 to 1,902.1 (paper 1,944.2). No mean moves more than 3.5%.

Verification of the rewrite: the numba engine reproduces every old trade bit for bit except
the removed ones and the relabels; the vectorized `portfolio_daily` matches the old one within
4e-17 on 1,920 cohort series; the new cohort job reproduces 330 of 480 sampled monthly series
exactly and every other one contains a removed trade; Panel B, stock, pair and sector counts
are unchanged. A full run (474 cohorts, Tables 1-3, Figure 1, check) takes 1 min 45 s on 15
workers, against more than 30 minutes before.

### 13a. Second review round (2026-10-17)

- **Trade-log capacity (PR #3, critical).** The numba kernel sized the log at
  `n * (T // 2 + 1)` trades, but a pair can close and reopen on the same day, so one pair can log
  up to `T - 1` trades. Reproduced: 12 days logged 8 of 10 trades; longer runs could write past
  the array. Fixed with `n * T` slots (a hard ceiling) and a 126-day test of a pair that flips
  every day. Production cohorts used at most 3.4% of the old capacity, and the rebuild leaves every
  table cell unchanged by this fix.
- **Payoffs from the engine (PR #4 note, and the old zero-account item).** `portfolio_daily`
  rebuilt payoffs as `r * w_prev`, which loses a pair's payoff whenever its account is zero
  (non-finite return) and, for inputs with holes, the day after a missing return. The engine
  now returns `pair_payoffs` and `portfolio_daily` sums them. Only the "all" portfolio moves,
  in 5-7 months (largest 0.08 percentage points); its mean changes by under 0.02% relative and
  the replication check is unchanged.
- **Figure 1 indicator (PR #4).** Kept as is, with the rule moved into
  `position_indicator` and tested: a position held from the close of the open day to the close
  of the close day is drawn up over exactly [open day, close day]; also marking the close day
  would keep it up one day too long under `step(where="post")`.


### 13c. Third review round (2026-10-18)

- **Breakpoint set settled: CRSP = NYSE + AMEX common.** The reviewer
  measured both readings on the 20-cohort sample (N+A any share 89.0 vs
  N+A common 88.5) and preferred the common-share filter, which also keeps
  `composition_stats`'s inputs honest; adopted in PR #7 with the key renamed
  to `breakpoint_caps`. Full-sample Panel B after the rebuild:
  avg_size_decile top20 3.11 (paper 2.71), all 4.65 (4.57);
  weight_top3 top20 0.694 (0.74). The weighted full-sample score moves
  137.5 -> 145.0 of 291 cells. The paper only says "using CRSP
  breakpoints"; NYSE + AMEX common is our interpretation, chosen because
  it fits Panel B best.
- **The conformance threshold is the shipped sample score (88.5)**, so the
  paper-conformance test is a regression guard: the weighted score must not
  fall below the shipped sample score, and the assertion lists any cell
  that is outside the 25% band.

## 14. Frozen prices and the employed-capital denominator (2026-10-18)

Two changes, each tested against alternatives on the full 474-cohort sample. Score = weighted
cells of the replication check (✓ = 1, ~ = ½; 291 cells); "means" = the 8 Table 1 and 15
Table 3 means measured in the paper's own standard errors (Table 1 `nw_se`, Table 3 mean / t).

| run | score | T1 | T2A | T2B | T3 | T1 means within 2 SE (RMS z) | T3 means within 2 SE (RMS z) |
|---|---|---|---|---|---|---|---|
| main after #7/#8 | 145.0 | 30/25/33 | 13/8/3 | 24/5/11 | 39/40/60 | 7/8 (1.57) | 13/15 (1.50) |
| + frozen-price exclusion | 160.0 | 43/25/20 | 13/8/3 | 24/5/11 | 40/42/57 | 7/8 (1.23) | 13/15 (1.52) |
| + daily open count (shipped) | **161.5** | 47/22/19 | 13/8/3 | 24/5/11 | 37/46/56 | **8/8 (0.70)** | **14/15 (1.20)** |

- **Frozen prices.** The worst top-5 months (1974-04, 1978-08, 1979-03, 1980-10, 1981-01) were
  rank-1 pairs of two pre-1983 Nasdaq stocks whose quote did not change on 98-100% of formation
  days (CRSP has no Nasdaq volume before Nov 1982, so `vol_common` keeps them). A constant
  normalized price pairs at distance zero. `formation_universe` now also drops a stock whose
  return is zero on every formation day: about one stock per cohort, all counts unchanged
  (2,013 pairs per cohort, Financials 352). Top-5 Table 1 moves from 1.19% / std 2.99% /
  min -20.3% to 1.39% / 2.49% / -14.5% (paper 1.31% / 2.28% / -10.6%).
- **Thresholds instead (not adopted).** Dropping stocks whose quote is unchanged on more than a
  share of quote-only days scores 138.0 (75%), 147.5 (85%), 156.0 (90%), 158.0 (95%),
  163.0 (98%), 161.0 (99%). Strict rules (any unchanged quote: 139.0; `volpos_common`: 139.0;
  `price_common`: 140.0) cut pairs from 2,013 to about 1,600 per cohort and Financials from 352
  to 229-235 against the paper's 371 (the 50% threshold: 264), so GGR kept most of these
  stocks. The 95-99% band only adds a tuned parameter, and 95% puts the
  top-5 mean 2.7 SE above the paper.
- **Employed capital = pairs open that day.** With the alive-gate and delisting fixes in, the
  daily count reproduces the paper's fully-invested/committed ratios in every cell (ours
  1.71/1.70/1.55/1.84 no wait, 1.71/1.70/1.54/1.88 one-day wait; paper 1.67/1.78/1.59/1.80 and
  1.61/1.72/1.58/1.81). The period-average n̄ gives "all" 1.57, the reason the "all" mean sat at
  0.85% (now 0.99%, paper 1.10%). A per-calendar-month count overshoots top 5 (ratio 2.2).
- **Daily-rebalanced legs (not adopted).** Re-marking each pair to a $1/$1 position every day
  (r_long − r_short compounded) fixes the "all" std in the dot-com months (2.16% -> 1.55%,
  paper 1.67%) but lowers every mean and flattens the right tail ("all" kurtosis 25.5 -> 11.6,
  paper 25.2): score 149.0. Buy-and-hold legs stay.
- **Still open.**
  - "All" pairs, Dec 1999 to Mar 2000: -8.4%, -18.7%, +15.4% months. Short legs that rose up to
    27x, spread over 321 stocks; 1963-1998 alone matches the paper (std 1.62% vs 1.67%, min
    -3.25% vs -2.72%), and our 1999-2002 top-20 matches the paper's hold-out (std 3.6% vs 3.8%
    a year). GGR's all-pairs series has no such losses.
  - Table 2 trigger: our top pairs are tighter (top-5 2σ 0.033 vs 0.048). Measuring the spread
    around zero adds only 5%; the deviation on the signal day fits top 5/20 but overshoots
    101-120 and "all", and the paper defines the row as an average of two standard deviations.
    Dual-class pairs (e.g. permnos 17778/83443, 34 cohorts) are 5.5% of top-5 pairs and do not
    explain it.
- **Conformance guard.** The 20-cohort sample (every 24th cohort, so no cohorts overlap) moves
  88.5 -> 86.0 while the full sample moves 145.0 -> 161.5; the threshold is reset to the new
  shipped sample score. The sample is a weak proxy for the overlap-averaged tables.

## 15. Attribution, SIC sensitivity and value-weighted books (2026-10-19)

Marks are the check's: ✓ within 10% of the paper, ~ within 25%, ✗ further; score = ✓ + ½ ~
over 291 cells. Every run is the full 474-cohort sample.

**Attribution of section 14.** Splitting PR #10 into its two changes:

| step | T1 ✓/~/✗ | T3 ✓/~/✗ | score |
|---|---|---|---|
| main after #7/#8 | 30/25/33 | 39/40/60 | 145.0 |
| + frozen-price exclusion | 43/25/20 | 40/42/57 | 160.0 (+15.0) |
| + daily open count | 47/22/19 | 37/46/56 | 161.5 (+1.5) |

The frozen-price rule carries the gain. The daily open count flipped 63 cells in both
directions for +1.5 net (Table 3: −1.0); it was chosen for the ratio fit, not the score.

**SIC source does not drive Table 3.** A sector-only harness (same code path, verified to
reproduce `table3.csv` exactly) ran all 474 cohorts under five SIC sources:

| SIC source | U / T / F / I stocks per cohort (paper 156 / 61 / 371 / 1,729) | T3 return cells (of 135) |
|---|---|---|
| CRSP dated, own history, then header (shipped) | 161 / 61 / 352 / 1,726 | 56.0 |
| CRSP dated only (unknown -> Industrials) | 159 / 59 / 321 / 1,762 | 61.5 |
| CRSP header | 166 / 64 / 347 / 1,724 | 56.5 |
| Compustat header (CCM link) | 174 / 63 / 349 / 1,714 | 61.0 |
| Compustat historical SICH (1987+), else header | 176 / 63 / 345 / 1,716 | 62.0 |

The spread is about 6 of 135 cells, almost all in tail rows, and every alternative worsens the
counts. CRSP's December 2002 edition is the same security set (section 11) with 88 itemised SIC
edits since, so the dated CRSP code is the code GGR had. Compustat SIC is newer and disagreed
with CRSP on more than a third of firms at two digits in 1974-93 (Kahle and Walkling 1996). No
SIC crosswalk for S&P's pre-GICS four groups was found. The 1999 NBER version's sector table
(Table V, six-month cohort returns, 1962-97; it reports excess kurtosis, the RFS raw) gives the
same ordering: 63-71.5 of 144 cells across sources.

**Where Table 3 loses.** Location rows (mean, median, std, t, share negative) earned 44.5 of 75
cells; tail rows (skew, kurtosis, min, max) 11.5 of 60. Two causes:

- *Near-frozen pre-1983 Nasdaq stocks.* Quote-only micro-caps (about $2M) with zero returns on
  85-99% of formation days pair at tiny distances in Industrials. Cohorts 1981-02 to 1982-10
  lose 50-72% over six months in the top 5 (NBER worst: −23%), e.g. a short leg (permno 29699)
  that rose 281% in the 1982 rally. The moves are genuine. Dropping 95%-stale stocks fixes the
  tails but lifts the Industrials top-5 mean to 0.82% (paper 0.49%), so GGR kept them; no rule
  the paper states removes them.
- *February 2000.* Industrials "all" lost 20.4% that month under the count convention, spread
  over about 2,200 of 2,600 pairs per cohort (the worst 10 pairs carry 20% of the loss): the
  momentum peak hurting a contrarian rule. Up to 1998 the same series matches the paper (min
  −3.2% vs −3.4%, mean 0.79% vs 0.71%).

**Value-weighted books (adopted).** Eq. 2 says "the daily returns on the long and short
positions are calculated as value-weighted returns", weights being each position's value since
it opened. Read across the portfolio, fully invested = the value-weighted return of the long
book minus that of the short book; committed scales it by the share of selected pairs holding a
position. A short leg that has run up 3-5× now weighs in the short book instead of counting as a
−300% to −500% loss on a $1 pair.

| fully invested / committed | score | T1 ✓/~/✗ | T3 ✓/~/✗ | FI/committed "all" (paper 1.80 / 1.81) |
|---|---|---|---|---|
| period-average count n̄ / N | 160.0 | 43/25/20 | 40/42/57 | 1.57 / 1.58 |
| daily count n_t / N | 161.5 | 47/22/19 | 37/46/56 | 1.84 / 1.88 |
| value-weighted / N | 163.5 | 47/18/23 | 45/38/56 | 1.95 / 1.99 |
| **value-weighted / scaled by n_t / N (shipped)** | **164.0** | 48/17/23 | 45/38/56 | **1.80 / 1.83** |

Ratios for the pair shipped then (164.0): 1.71/1.70/1.54/1.80 no wait and 1.70/1.70/1.53/1.83 one-day wait
(paper 1.67/1.78/1.59/1.80 and 1.61/1.72/1.58/1.81). Industrials "all" February 2000 improves
from −20.4% to −13.8% (paper min −3.4%) and its skew from −0.29 to +1.04 (paper 2.97). Table 1
loses some tail cells it had matched ("all" kurtosis 23.4 -> 16.1, paper 25.2). Figure 1 and
Table 2 are unchanged.

**Realized cash flows (rejected).** Booking each trade's payoff on its close date, as the NBER
text describes the cash flows, would remove the February 2000 mark-to-market loss but scores
27-28 of 135 Table 3 cells (marked to market: 56). The RFS says positions are "marked-to-market
daily".

**Still open.** February 2000 (−13.8% vs a paper minimum of −3.4%) and the 1981-82 Industrials
top-5 cohorts. Table 2 trigger (section 14).

**Conformance guard.** The guard now has three parts. The shipped full-sample check must score
at least 164.0; this always runs. The 20-cohort sample smoke test moves 86.0 -> 87.5 and its
threshold rises with it. `make conformance-full` rebuilds all 474 cohorts and requires the
shipped check's summary lines to be reproduced (about 70 s with 12 workers).

## 16. The Table 2 Panel B decile-difference row reports the all-pairs average (2026-10-20)

The paper's Table 2 Panel B row "Average decile difference for mixed pairs" is 0.97, 0.97,
0.97 and 0.98 across the four portfolios. An average of |d1 - d2| over mixed-only pairs is
at least 1 (integer CRSP decile gaps), so the paper's number cannot be a mixed-only average;
its own text ("the stocks in mixed pairs differ on average by a single decile") reads like a
rounded description of a value near 1. The only consistent reading is the average over all
pairs, with same-decile pairs contributing 0. `composition_stats` now reports the all-pairs
average in that row (the mixed-only value remains derivable as the all-pairs average divided
by `share_mixed_decile_pairs`).

Verification: the pinned evaluator (frozen paper values, mark recomputation) scores the full
sample at 165.0 (from 164.0); the Table 2 Panel B cells move from 24/5/11 to 25/4/11.
Rejected alternatives measured on the full sample: SIC 46xx to Utilities (+0.5, Utilities
count 161 to 187 vs paper 156), all of 48xx to Utilities (+1.5, Utilities count 187), SIC
47xx to Industrials (+1.0), near-frozen (>98% unchanged) exclusion (+0.0), converged-only
round-trip counts (-2.0). The current SIC map stands: its sector counts (161/61/352/1730)
are within 10% of the paper's 156/61/371/1729, and the map alternatives trade count cells
for composition cells. The remaining ~90 miss cells are distribution tails (skew, kurtosis,
min, max in Table 1 and Table 3) that trace to the pre-1983 Nasdaq stale-quote content of
CRSP and the 2000-2002 dot-com months, which no rule stated in the paper removes.

## 17. Score experiments under value-weighted books (2026-10-20)

Marks are the check's (✓ within 10%, ~ within 25%, ✗ further; score = ✓ + ½ ~ over 291 cells).
Every run is the full 474-cohort sample. The baseline is the pre-#13 check, 164.0; section 16
(PR #13, merged) moves it to 165.0 through the Panel B decile row, which none of these
experiments touches, so every delta below carries over to the 165.0 baseline.

**Sensitivity, not shipped: Panel A over full six-month periods.** The cohorts starting 2002-08 to
2002-12 trade for one to five months before the data end, while Panel A's rows are per six-month
period. Averaging Panel A over the 469 full-period cohorts gives:

| row (ours / paper) | top 5 | top 20 | 101-120 | all |
|---|---|---|---|---|
| std time open, all 474 cohorts (shipped) | 0.821 / 0.80 ✓ | 0.502 / 0.45 ~ | 0.448 / 0.38 ~ | 0.311 / 0.17 ✗ |
| std time open, 469 full periods | 0.786 / 0.80 ✓ | 0.454 / 0.45 ✓ | 0.376 / 0.38 ✓ | 0.198 / 0.17 ~ |

That would move Panel A from 13/8/3 to 15/7/2 (164.0 -> 165.5 on the pre-#13 baseline). The paper's Table 2 caption reads
"between July 1963 and December 2002 (474 months)" and says nothing about dropping cut-off
cohorts, so the shipped check keeps all 474.

**Not adopted.**

| test | score | T1 ✓/~/✗ | T2A | T2B | T3 ✓/~/✗ |
|---|---|---|---|---|---|
| baseline (value-weighted books) | 164.0 | 48/17/23 | 13/8/3 | 24/5/11 | 45/38/56 |
| drop stocks with unchanged quote-only days > 99% | 163.5 | 48/17/23 | 13/8/3 | 24/5/11 | 43/41/55 |
| same, > 98% | 164.0 | 49/13/26 | 13/8/3 | 27/3/10 | 41/44/54 |
| same, > 95% | 158.5 | 37/25/26 | 15/6/3 | 30/1/9 | 37/47/55 |
| cohorts weighted by open positions ("desk" capital) | 164.0 | 38/24/26 | 13/8/3 | 24/5/11 | 52/37/50 |
| eq. (3) weights compounded from trading day 1 | 159.5 | 44/20/24 | 13/8/3 | 24/5/11 | 43/38/58 |
| eq. (3) weights = formation-normalized price | 163.0 | 42/21/25 | 13/8/3 | 24/5/11 | 49/36/54 |
| no pair of two securities of one company (same permco) | 163.0 | 41/25/22 | 16/7/1 | 24/4/12 | 45/38/56 |

- *Near-frozen quotes, under value-weighted books.* The filter now fixes Panel B composition
  (95%: top-5 size decile 2.71 vs 2.54, utilities 0.66 vs 0.72) but costs Table 1 and Table 3 as
  much as it gains, and barely moves the top-5 trigger (0.033 -> 0.035). Section 15's reading
  stands: GGR kept these stocks.
- *Desk weighting.* Weighting each cohort's fully invested return by its open positions, rather
  than the paper's equal-weighted average of the six portfolios, gains 6.5 Table 3 cells but
  lowers every Table 1 mean by 10-20% (top 5 1.31% -> 1.10%, paper 1.31%). The paper's text is
  the equal-weighted average; not adopted.
- *Eq. (3) read literally.* The paper's weight is w_i,t = (1+r_i,1)...(1+r_i,t-1), which could
  start on the first trading day rather than when the position opens. Compounding from trading
  day 1 loses 4.5 points; weighting by the formation-normalized price gains Table 3 (49 ✓) but
  loses Table 1. Weights from the open date stay.
- *Same-company pairs.* 21% of top-5 pair slots (498 of 2,370) are two share classes of one firm
  (Viacom/Paramount A/B, Citizens Utilities A/B, Berkshire A/B, A.C. Nielsen A/B, Comcast, ...),
  pairing at σ ≈ 0.01. Barring them fixes most of Panel A (top-5 trigger 0.033 -> 0.037, round
  trips 2.31 -> 2.18 vs 2.02) and the top-5 utilities weight (0.59 -> 0.69 vs 0.72), but the
  top-5 Table 1 mean falls from 1.31% (paper 1.31%) to 1.07%. The paper does not mention share
  classes; not adopted.
- *Trigger averaging.* Averaging 2σ over opened pairs, over trades or by median gives 0.032-0.034
  for top 5 (paper 0.048); the gap is in the pairs, not the averaging.

**Diagnosed, not changed.** The worst top-5 month, April 1974 (−13.9%, paper minimum −10.6%), is
one stock, Consolidated Edison (permno 11404), held long across all six cohorts while it fell after
its dividend omission.
The Utilities 101-120 maximum (25.7% in January 2001, paper 12.1%) is one cohort, 2001-01, earning
94% fully invested in its first month. Neither is a code error.

### Second edition and sub-period checks (2026-10-20)

The February 2006 draft in the repo has the same Tables 1-3 and text as the RFS; the 1999 NBER
draft (`w7032`) is a different experiment with its own Tables I-II: 408 cohorts (1963-07 to
1997-06), 6-month cohort returns, Table II in the no-wait version. Scored with the same marks
(1999 Table I 72 cells, Table II 24 cells; its kurtosis is excess, its "employed" capital is
about committed x N / pairs opened):

| run | RFS check (291) | 1999 Table I (72) | 1999 Table II (24) |
|---|---|---|---|
| baseline | 164.0 | 33.5 | 22.5 |
| stale-quote filter > 99% | 163.5 | 35.0 | 22.5 |
| > 98% | 164.0 | 39.5 | 22.5 |
| > 95% | 158.5 | 46.5 | 22.5 |
| literal eq. (3), from trading day 1 | 159.5 | 33.0 | 22.5 |
| no same-company pairs | 163.0 | 29.5 | 23.5 |
| wait-1 signal must persist on the open day | 154.5 | 32.5 | 22.5 |
| no new signal on the day a position closes | 163.5 | 34.0 | 22.5 |
| both wait-1 changes | 155.5 | 33.0 | 22.5 |

- *The engine is right.* On the 1999 sample (wait 0) round trips are 2.47/2.28/1.93/1.73 vs
  2.4/2.2/1.9/1.7, time open 3.9/4.0/4.2/4.1 vs 3.8/3.8/4.0/3.9, pairs opened 4.88/19.67/19.73/1,726
  vs 4.97/19.81/19.77/1,814; 21 of 24 cells ✓, none ✗. The 1999 trigger is 0.0399/0.0449/0.0683/0.1518
  (ours 0.0343/0.0413/0.0668/0.1544). The 2006 Table 2 differs from the 1999 one by more than our
  engine does, so the editions are not the same experiment. The one-day-wait rule is not the lever:
  none of the three variants above helps either edition.
- *Near-frozen quotes matter before 1989 in both editions.* On the 1999 sample the 95% filter
  lifts the top-20 minimum from -24.7% (cohort 1982-11, Nasdaq micro-caps whose short legs rose
  3x) to -8.4% (paper -7.9%), the share of negative cohorts from 12.3% to 7.8% (paper 9%), skew
  from -0.12 to 0.81 (paper 0.98). Table 8 (wait 1, fully invested, 1963-88) agrees:

| 1963-88 | top 5 | top 20 | 101-120 | all |
|---|---|---|---|---|
| paper mean / std | 1.034 / 2.259 | 1.181 / 1.689 | 1.052 / 1.527 | 0.992 / 1.651 |
| baseline | 0.812 / 2.475 | 1.044 / 1.766 | 0.885 / 1.555 | 0.995 / 1.524 |
| filter > 95% | 1.091 / 2.245 | 1.263 / 1.626 | 0.926 / 1.543 | 1.002 / 1.527 |

- *After 1988 the filter changes nothing, and we are too high.* 1989-2002 means (paper / ours):
  top 5 0.217 / 0.443, 101-120 0.327 / 0.605, all 0.212 / 0.396; "all" std 1.295 / 2.324, entirely
  from 1999-2002 (ours 3.80; 1989-98 is 1.37). The unfiltered full-sample match therefore pairs a
  pre-1989 shortfall with a post-1988 excess that offset; the filter fixes the first and exposes
  the second, which is why the RFS full-sample score falls (158.5) while both pre-1989 checks and
  the 1999 edition rise.
- *The hold-out sentence is about the no-wait rule.* "Using the original model" the top-20 fully
  invested portfolio earned 10.4% a year (std 3.8%, t 4.82) in 1999-2002. Ours: no wait 7.6% (std
  3.8%, t 4.0); wait 1 3.8% (std 3.5%, t 2.2).
- *Not shipped.* The filter is a tuned threshold the paper does not state ("one or more days with
  no trade" read strictly cuts Financials to 229-235 vs 371), and it lowers the RFS score. It is
  the one convention that improves three independent checks (1999 Tables I-II, Table 8 pre-1989)
  while lowering the fourth, so it stays a sensitivity.

**Joint scorecard (both editions, Table 1 only).** RFS Table 1 is 88 cells; the 1999 Table I is 72.

| run | RFS Table 1 | 1999 Table I | RFS total | Table 8 (16) |
|---|---|---|---|---|
| baseline | 56.5 | 33.5 | 164.0 | 8.5 |
| stale-quote filter > 99% | 56.5 | 35.0 | 163.5 | 8.5 |
| > 98% | 55.5 | 39.5 | 164.0 | 8.5 |
| > 95% | 49.5 | 46.5 | 158.5 | 9.5 |
| no new signal on the day a position closes | 57.0 | 34.0 | 163.5 | n/a |
| wait-1 signal must persist | 54.0 | 32.5 | 154.5 | n/a |
| literal eq. (3), formation-normalized weights | 52.5 | 31.5 | 163.0 | n/a |
| no same-company pairs | 53.5 | 29.5 | 163.0 | n/a |

No convention lifts both Table 1s by more than noise. The > 98% filter leaves the RFS total
unchanged and lifts the 1999 Table I by 6; the > 95% filter lifts the 1999 side most and costs the
RFS side most, because the RFS sample adds 1989-2002, where we are too high.

- *Capital conventions do not explain post-1988.* Top-5 1989-2002 mean is 0.43-0.44 under the
  volume-weighted and the count-based fully invested series alike (paper 0.217).
- *Footnote 4 calibration.* The paper reports that treating a delisted long as -100% lowers the
  top-20 no-wait fully invested mean from 1.436% to 1.32% and raises the std from 1.69% to 1.9%.
  On our data the same assumption moves it from 1.333% to 1.169% (std 1.74% to 2.07%): about 1.4x
  the mean effect and 1.6x the std effect. Our long legs carry more delisting exposure than the
  paper's, or milder actual delisting returns; 140 of 20,774 top-20 trades close on a delisting.
  The extreme assumption itself scores 129.5 (Table 1: 18 of 88 within 10%), so the paper's own
  figure is not our data's.

- *Missing delisting returns do not explain post-1988.* The CIZ delisting table (local,
  `delisting.parquet`, 29,727 rows) has no return for 62% of for-cause (GDR) delistings before 1989
  and 19% after; the panel build zero-fills them, i.e. "the last available price" the paper names.
  Filling them with -30% (Shumway) instead gives RFS 163.0, 1999 Table I 33.5, Table 8 8.0/16, and
  post-1988 top-5 stays at 0.44% (paper 0.217%); a -100% fill gives 150.0 / 30.0 / 6.5. Only 140 of
  20,774 top-20 no-wait trades close on a delisting, so the paper's footnote-4 sensitivity
  (every delisted long at -100%, including mergers) is driven by the merged names, not by the
  missing returns.

### Time-profile checks against Tables 5, 8 and Figures 2-3 (2026-10-20)

Diagnostics for the Table 1 gap, not extra targets. All use the shipped (vw_base) one-day-wait fully
invested series.

- *Table 5 (monthly, one-day wait).* Our 1% quantile and minimum match for the top 5 (−4.28% vs
  −4.32%; min −15.2% vs −12.6%) and the minimum for the top 20 (−8.13% in April 1974 vs −8.22%;
  Figure 2 draws the paper's minimum in 1974 too). The top-20 1% (−2.97% vs −1.94%) and the "all"
  tail do not: "all" minimum −12.3% vs −2.95%, 1% −2.84% vs −1.99%.
- *Serial correlation and co-movement.* Top 20 serial correlation 0.28 (paper 0.24); 101-120 0.05
  (0.19); "all" 0.07 (0.12). Correlation of the top-20 and 101-120 series: 0.35 full sample, 0.41
  pre-1989, 0.06 post-1988 (paper 0.48 / 0.51 / 0.18). Post-1988 the paper's looser portfolios still
  share a common component and ours do not.
- *Where "all" loses (Table 1 shape rows).* Skew 1.28 vs 3.42, kurtosis 16.1 vs 25.3, min −12.6% vs
  −2.7%, std 1.99% vs 1.67% (no wait). Every row is the dot-com window: December 1999 −5.8%,
  February 2000 −12.3%, September 2000 −4.3%, March 2000 +11.1%, January 2001 +12.5%.
- *February 2000 is the data, not a bug.* Cohort 1999-09 closes 5,420 trades that month; the 2,532
  that run to the end of the window average −65% of a $1 pair (mean +29% for the 2,638 that
  converged). 97% of the loss is on Nasdaq short legs (SIC 73, 28, 36, 35, 38), ranks 1,000-3,300
  (loosely matched pairs). The worst short is permno 79006: +135% on 16 Feb 2000 alone, +12.5x
  over the window. Booking payoffs on the close date (realized, committed x 1.8) still gives
  February 2000 −7.7% (min −7.7%, max +8.0%), so the mark-to-market convention is not the cause.
- *Figure 3 (digitized, ±0.15 pp/month).* Cumulative top-20 fully invested: paper 24.1 at 1989, 40.0
  at 2002; ours 23.8 and 45.3. The totals agree, the years do not: 1989-93 paper 0.25 vs ours
  0.63 %/month, 1994-98 0.42 vs 0.26. Pre-1989 the yearly profile differs by 0.75 rmse (1980 and
  1982: ours 0.9 and −1.2 vs 2.1 and 0.6). The >95% stale-quote variant cuts that rmse to 0.60 and
  lifts the profile correlation 0.54 → 0.71; nothing we tried moves post-1988 (0.31-0.37, near the
  digitization noise). So the stale-quote question is a pre-1989 matter and the post-1988 gap is in
  the looser portfolios (top 5, 101-120, "all"), which no figure shows.
- *Figure 2.* The paper's maximum (about +13.5%, about nine months after the April 1974 minimum,
  i.e. January 1975) is +5.0% in our top-20 series (our maximum 7.6%, January 1974). This is the
  Table 1 top-20 "max" cell (paper 13.3% no wait; ours 9.8%).

### Same-issuer pairs plus stale quotes: the first joint gain (2026-10-20)

Aligning the small portfolios first (top 5, top 20, 101-120) turned up one structural cause. 21% of
the top-5 pair slots are two share classes of one issuer (same PERMCO): 0% in the 1960s, 13% in the
1970s, 43% in the 1990s and 80% in 2000-02 (Berkshire A/B, Paramount, Raytheon, Comcast), with
spreads of 0.005-0.011 against 0.018 for other pairs. Together with the near-frozen Nasdaq quotes
this explains the too-tight top pairs. Neither does it alone.

| run (all unshipped) | RFS score | 1999 Table I + II | top-5 trigger (paper 0.0476) | top-5 utilities (0.72) | top-5 / top-20 mean post-1988 (0.217 / 0.375) |
|---|---|---|---|---|---|
| baseline (pre-#13 shipped) | 164.0 | 33.5 + 22.5 | 0.033 | 0.587 | 0.443 / 0.412 |
| no same-PERMCO pairs | 163.0 | 29.5 + 23.5 | 0.037 | 0.690 | 0.299 / 0.429 |
| stale > 95% | 158.5 | 46.5 + 22.5 | n/a | n/a | n/a |
| **both** | **169.0** | **46.5 + 23.5** | **0.039** | **0.777** | **0.299 / 0.429** |

Both together: pre-1989 mean / std (Table 8: paper) top 5 1.01 / 2.31 (1.03 / 2.26), top 20 1.26 /
1.64 (1.18 / 1.69), 101-120 0.94 / 1.52 (1.05 / 1.53), all 1.00 / 1.53 (0.99 / 1.65); post-1988 top 20
0.43 / 0.99 (0.375 / 0.987). Table 5 top-20 quantiles (ours / paper): 1% −2.35 / −1.94, 5% −0.99 /
−1.00, 10% −0.58 / −0.58, 25% +0.01 / +0.05, P(<0) 0.25 / 0.23, serial 0.25 / 0.24. Table 2 Panel B top
5 / top 20: size decile 2.65 / 2.74 (2.54 / 2.71), top-3 weight 0.77 / 0.74 (0.78 / 0.74). RFS cells
✓/~/✗: Table 1 50/16/22, Table 2A 14/9/1, Table 2B 27/2/11, Table 3 41/47/51.

Still off: 101-120 post-1988 (0.59 / 1.37 vs 0.327 / 1.12), "all" post-1988 (0.40 / 2.33 vs 0.212 /
1.30), top-5 post-1988 std (1.45 vs 1.66), the Table 2 trigger (top 5 0.039 vs 0.048, top 20 0.045
vs 0.053). The 1989-2002 101-120 pairs are ordinary loose pairs (1% related names, 32% utilities).

Not shipped: neither rule is in the paper (the 1999 draft and the RFS both say only that stocks
with a no-trade day are screened out), so both stay sensitivities until the paper's words support
them. Diff: scratchpad `exp/nsf_s95.diff` (env `NOSAMEFIRM=1 STALE_MAX=0.95`).

### Table 2 trigger, Table 7 long/short books and 101-120 (2026-10-20)

Follow-up to the same-issuer + stale-quote run (unshipped; env `NOSAMEFIRM=1 STALE_MAX=0.95`).

- **Table 7 (long and short book mean monthly return, one-day wait, full sample).** Value-weighted
  books from the engine's per-leg payoffs (diff `exp/nsf_ls_books.diff`). Long / short, in %:

  | run | top 5 | top 20 | 101-120 | all |
  |---|---|---|---|---|
  | paper | 1.245 / 0.501 | 1.330 / 0.435 | 1.458 / 0.663 | 1.623 / 0.908 |
  | baseline | 1.140 / 0.435 | 1.293 / 0.465 | 1.467 / 0.667 | 1.500 / 0.702 |
  | no same-PERMCO | 1.166 / 0.543 | 1.290 / 0.473 | 1.462 / 0.684 | 1.501 / 0.702 |
  | stale > 95% | 1.272 / 0.380 | 1.360 / 0.387 | 1.468 / 0.643 | 1.503 / 0.701 |
  | both | 1.265 / 0.476 | 1.363 / 0.388 | 1.479 / 0.654 | 1.504 / 0.700 |

  The top-5 books are closest with both rules (long +1.6%, short −5%; baseline −8%, −13%). 101-120
  matches under every variant (the level there is right). "All" is low in both books under every
  variant (long −7%, short −23%): the paper's all-pairs stocks earn more raw return, and no
  convention we tested changes that.
- **101-120 post-1988 is a timing split, not a level error.** Full-sample 101-120 fully invested is
  0.825% (paper 0.795%), but ours is 0.947% pre-1989 (paper 1.052%) and 0.603% post-1988 (0.327%).
  Our series declines less across 1989 than the paper's in every portfolio (post/pre ratio top 5 0.32
  vs 0.21, top 20 0.35 vs 0.32, 101-120 0.64 vs 0.31, all 0.40 vs 0.21). The post-1988 pairs
  are ordinary loose pairs (1% related names, 32% utilities).
- **Table 2 trigger (not resolved).** Formation 2σ with both rules: 0.039 / 0.045 / 0.069 / 0.166
  (paper 0.0476 / 0.0528 / 0.0756 / 0.1689); the paper/ours ratio falls with looseness
  (1.21 / 1.18 / 1.10 / 1.02). Tried and rejected: RMS about zero (0.041 / 0.047 / 0.072 / 0.173),
  trading-period std (2x too high), 18-month RMS (2x), median. The realized deviation at the signal
  (0.049 / 0.054 / 0.083 / 0.200) fits top 5 and top 20 but overshoots "all" by 18%, and the table
  note defines the row as the cross-sectional average of two standard deviations of the pair-price
  difference. The 1999 draft's Table II (0.0399 / 0.0449 / 0.0683 / 0.1518) fits our 2σ, so the two
  editions disagree on this row by more than the sample extension explains.
- **Where the pairs earn.** Mean payoff per pair by exchange mix and size (every third cohort):
  post-1988 only the Big Board pairs (NN +0.0115) are positive; Nasdaq-Nasdaq −0.0086, mixed −0.006;
  pairs ranked > 1,600 lose −0.0176 after 1988. No attribute isolates the 101-120 excess.

## 18. Same-issuer and near-frozen-quote exclusions are now on by default (2026-10-20)

`03_replicate.py` now runs with `--same-issuer exclude` and `--max-stale-share 0.95`; the stack
before it (#14 ledger, #15 options) shipped them off. The shipped check moves 165.0 -> 169.5.

| RFS cells ✓/~/✗ | before (165.0) | now (169.5) |
|---|---|---|
| Table 1 (88) | 48/17/23 | 50/16/22 |
| Table 2 Panel A (24) | 13/8/3 | 14/9/1 |
| Table 2 Panel B (40) | 24/7/9 | 27/3/10 |
| Table 3 (139) | 45/38/56 | 41/47/51 |

The 20-cohort smoke sample moves 87.5 -> 91.0, and Figure 1 is unchanged (pair rank 4, trades
within 3 days). The 1999 draft's Tables I-II, which this change was not tuned on, move from
33.5 + 22.5 to 46.5 + 23.5.

**What is and is not in the paper.** Section 2.1 says only that stocks "that have one or more
days with no trade" are screened out. A stock whose quote is frozen (no volume field, price
unchanged) and a second share class of the same company are not mentioned. Both rules are our
reading, and the check's header says so. They are shipped because they are the only change that
raises both editions together and the improvement shows up in tables the rules were not fitted to:

- *Table 2 composition (top 5 / top 20, ours vs paper):* utilities 0.78 / 0.77 (0.72 / 0.71),
  average size decile 2.65 / 2.74 (2.54 / 2.71), top-3 deciles 0.77 / 0.74 (0.78 / 0.74).
- *Table 5 (top 20, one-day wait):* 5% −0.99% (−1.00%), 10% −0.58% (−0.58%), serial correlation 0.25
  (0.24).
- *Table 7 (long / short books, top 5):* 1.265 / 0.476 (1.245 / 0.501), baseline 1.140 / 0.435.
- *Table 8, pre-1989 (mean / std):* top 5 1.01 / 2.31 (1.03 / 2.26), top 20 1.26 / 1.64 (1.18 /
  1.69), 101-120 0.94 / 1.52 (1.05 / 1.53), all 1.00 / 1.53 (0.99 / 1.65).

Neither rule helps alone (pre-#13 baseline 164.0): same-issuer only 163.0, stale only 158.5. The
rules are why section 17's "not adopted" rows lose points one at a time and win together.

**Switching them off.** `--same-issuer allow --max-stale-share none` reproduces the 165.0 check.

**Still open** (none of it changes with these rules):

- Table 1 "all" tails: skew 1.28 vs 3.42, kurtosis 16 vs 25, min −12.6% vs −2.7%, all from December
  1999 to January 2001 (section 17).
- 101-120 and "all" after 1988 (0.59% / 0.40% vs 0.327% / 0.212%): the level is right over the whole
  sample (Table 7), the split between 1963-88 and 1989-2002 is not.
- Table 2 trigger: 0.039 / 0.045 / 0.069 / 0.166 vs 0.0476 / 0.0528 / 0.0756 / 0.1689. The 1999
  draft's trigger (0.0399 / 0.0449 / 0.0683 / 0.1518) fits our 2σ, so the editions disagree.
- Table 3: ✓ falls 45 -> 41 while ~ rises 38 -> 47; the Table 3 total is about even.

## 19. Daily panel, post-1988 "all" and a re-read of both editions (2026-10-20)

No code or shipped number changes. Experiments ran on the shipped configuration (same-issuer
exclusion, stale limit 0.95), wait 1, all 474 cohorts, 16 workers; scratch scripts are not in the repo.

### 19.1 Details re-read from both editions

- **Universe size.** The Table 1 caption gives 2,057 pairs in the all-pair portfolio (1,870 in the
  1999 draft) and Table 3 gives 156 / 61 / 371 / 1,729 stocks (2,317). Ours: 2,009 pairs (-2.3%) and
  2,292 stocks (-1%). Over the 408 cohorts of the 1999 draft ours is 1,788 against 1,870 (-4.4%);
  over the 66 later cohorts ours is 3,377 against 3,213 implied by 2,057 x 474 - 1,870 x 408 (+5.1%,
  assuming the 1999 count averages those 408 cohorts). Strict no-trade screens give 1,562-1,605
  pairs (-22% to -24%) and stale limits 0.75 / 0.50 give 1,885 / 1,734 (-8% / -16%), so the paper
  keeps the pre-1983 Nasdaq quote-only stocks. Opened / formed pairs is 94.5% in both (1,944 / 2,057
  against ours 1,899 / 2,009).
- **Fully invested against committed.** The RFS text divides by "pairs that open", which gives a
  ratio of 1.03-1.06 (5 / 4.81, 20 / 19.30, 20 / 19.41, 2,057 / 1,944), but the RFS means imply
  1.58-1.81. The 1999 draft is literal (employed 6.01% against committed 5.98%; 4.23% against
  4.10%). Our open-pair-days reading gives 1.53-1.83 for the RFS.
- **Table 7 rows are leg returns.** Long 1.245% minus short 0.501% is 0.744%, Table 1's top-5 wait-1
  mean (0.745%); for "all" 1.623% - 0.908% = 0.715%.
- **Figure 1.** The paper's pair is "pair 5" in the cohort trading from August 1963 (the text says
  1962, but CRSP daily starts in July 1962). Ours ranks Kennecott-Uniroyal 4th (ranks 1-3: Exxon-
  Texaco, Allegheny-Avista, AT&T-Avista), so one pair above it in the paper is below it in ours.
- **Decile difference.** 0.97-0.98 (RFS) and 1.0 (1999) in every column, with the text saying mixed
  pairs "differ on average by a single decile"; a mean over integer gaps of mixed pairs cannot be
  below 1. Ours is 1.12 / 1.22 / 1.61 / 2.15.
- **Table 1 text.** "The minimum realized return increases with the number of pairs": paper
  -10.6 / -6.6 / -3.9 / -2.7%; ours -14.9 / -7.9 / -4.0 / -12.6%.

### 19.2 Daily panel against Table 5 Panel B

Ours / paper, fully invested, pairs formed and traded as in the wait-1 rule:

| daily | top 5 | top 20 | 101-120 | all |
|---|---|---|---|---|
| mean (%) | 0.038 / 0.033 | 0.047 / 0.040 | 0.040 / 0.035 | 0.038 / 0.027 |
| std (%) | 0.495 / 0.492 | 0.302 / 0.296 | 0.290 / 0.277 | **0.243 / 0.169** |
| 1st percentile (%) | -1.18 / -1.24 | -0.64 / -0.65 | -0.65 / -0.65 | **-0.51 / -0.33** |
| lag-1 serial correlation | -0.10 / -0.12 | -0.06 / -0.06 | 0.05 / 0.00 | 0.35 / 0.35 |
| share of days below 0 | 0.47 / 0.47 | 0.44 / 0.44 | 0.45 / 0.45 | 0.45 / 0.46 |
| worst day (%) | -10.01 / -10.08 | -5.94 / -6.72 | -1.89 / -1.99 | **-2.06 / -1.07** |

The three top columns match to within a few percent on every row (our top-5 worst day is
23 April 1974 at -10.0%). Every capital reading in `portfolio_daily` was tried for "all": its daily
std ranges from 157 (committed) to 271 (period-average count) against 169, and its worst day from
-1.46% to -3.19%; none fits. The paper's own "all" column looks off against its monthly numbers
(mean x 26.5 days against about 22.5 for the other three), so Table 8 is the better target for "all".

### 19.3 Post-1988 "all"

Table 8 mean / std, ours (paper), %:

| | top 5 | top 20 | 101-120 | all |
|---|---|---|---|---|
| pre-1989 | 1.01 / 2.31 (1.03 / 2.26) | 1.26 / 1.64 (1.18 / 1.69) | 0.93 / 1.52 (1.05 / 1.53) | 1.00 / 1.53 (0.99 / 1.65) |
| post-1988 | 0.30 / 1.45 (0.22 / 1.66) | 0.43 / 0.99 (0.38 / 0.99) | 0.59 / 1.37 (0.33 / 1.12) | **0.40 / 2.33 (0.21 / 1.29)** |

Pre-1989 matches in every portfolio; post-1988 only "all" (and 101-120 in part) is off. One -12.3%
month adds 0.90 to the paper's post-1988 "all" variance of 1.68, so the paper's series contains no
month like February 2000 at our size. Our daily "all" std is 197-217 in 1963-98 and 431 in
1999-2002 (589 in 2000).

Monthly employed return by rank band, 1999-2002 (54 cohorts):

| rank band | pairs per cohort | mean (%) | std (%) | worst month |
|---|---|---|---|---|
| 1-100 | 100 | 0.86 | 1.22 | -1.9% |
| 101-500 | 400 | 0.87 | 1.56 | -1.9% |
| 501-1000 | 500 | 0.67 | 2.51 | -6.6% |
| 1001-2000 | 1,000 | 0.21 | 4.14 | -14.1% |
| 2001+ | 1,374 | 0.27 | 5.32 | -14.1% |

### 19.4 February 2000, pair level

The six active cohorts lose 16.6 / 14.7 / 15.7 / 14.6 / 12.9 / 4.5% (mean -13.2%); 18 of the 20
days are negative. By rank band the contribution to the portfolio return is -0.07 (1-100),
-0.25 (101-500), -0.84 (501-1000), -3.94 (1001-2000) and -8.07 (2001+); the short books drag 19.4
points and the long books add 6.2. It is broad, not a few blowups: the top 10 short stocks are 10%
of the drag, the top 50 31%, the top 200 68% (3,445 stocks). 18.6 of the 19.4 points sit on Nasdaq
short legs, led by SIC 28 (5.9), 36 (4.6), 73 (3.4), 38 (1.6), 87 (1.4) and 35 (1.1): genomics,
electronics and software names that kept running (ARIAD, Oruka, Superconductor Technologies, PDL,
CuraGen, Myriad, Incyte). The Fama-French factors that month were SMB +21.3%, UMD +18.1%, HML -9.7%,
market +2.5%. The paper's own Table 4 loadings for "all" (without the reversal term) imply -4.1%
for February 2000 (-3.0% with the Table 8 post-1988 loadings), and its all-pair minimum, -2.95% in
Table 1 panel B, is plausibly the same month. Our four-factor loadings for "all" (no reversal
factor, so only indicative) are UMD -0.31 over the full sample and -0.33 post-1988, against the
paper's -0.18 and -0.13 with five factors.

### 19.5 Figure 2 and January 1975

Digitizing Figure 2 (Yale ICF working paper, p. 44, top 20, wait 1): we match the tall bars of
Apr 1974 (-8.9% against -8.3%), Jan 1974 (+7.6 against +7.2), Oct 1974 (+7.5 against +7.5) and
Nov-Dec 1983. We miss Jan 1975 (+3.6% against +13.5%, the whole of the max gap), Sep-Oct 1998
(+2.1 / +2.6 against +5.6) and Mar-May 1980 (+4.2 / +4.3 / +2.4 against +6.1). Across about 40
experiment variants Jan 1975 is 3.6-7.7%. Pair level (cohorts 1974-05..1975-01, 180 top-20 slots
per variant): 89 slots are pairs with a leg stale on more than half the formation days; they earn
0.4% in January against 3.6% for the pairs both variants share and 4.4% for the pairs a stale limit
of 0.50 brings in (distance 0.228 against 0.163). At 0.50 the Aug / Oct / Nov 1974 cohorts earn
15.2 / 13.5 / 13.5% in January, but the universe shrinks to 1,734 pairs (-16%) and 264 Financials
(paper 371), so it is not adopted, and the paper's own count means its top 20 was not free of
those stocks.

### 19.6 Open

The remaining "all" tail cells (Table 1 skew, kurtosis, minimum; Table 3 "all" columns) come down
to loosely matched pairs (ranks beyond about 500) in 1999-2002, about 2.5-4x too volatile in ours;
the paper's own loadings imply a milder February 2000. Not resolved: the paper keeps about 3,200
pairs per late cohort, so the difference is not how many loose pairs trade. January 1975, September
1998 and March 1980 are separate misses. Nothing here is fitted into the shipped check.

## 20. Telephone utilities are SIC 4811, the 1972 code (2026-10-22)

`sector_of` now counts telephone as SIC 4811 only (`--telephone-sic 4811`, the default); the old
map took 4810-4819. The shipped check moves 169.5 -> 172.0.

| RFS cells ✓/~/✗ | before (169.5) | now (172.0) |
|---|---|---|
| Table 1 (88) | 50/16/22 | 50/16/22 |
| Table 2 Panel A (24) | 14/9/1 | 14/9/1 |
| Table 2 Panel B (40) | 27/3/10 | 28/2/10 |
| Table 3 (139) | 41/47/51 | 43/47/49 |

Only sector labels move, so Table 1, Table 2 Panel A and Figure 1 are unchanged. The 20-cohort smoke
sample moves 91.0 -> 94.5; the 1999 draft's Tables I-II move from 91.0 to 91.5.

**What is and is not in the paper.** Section 2.1 names the four S&P groups and says each stock is
assigned "based on the stock's SIC code"; it gives no ranges. The map is our reading, and the
check's header says so.

**Why 4811.** CRSP's dated SIC follows the 1972 SIC manual before 1987, where telephone
communication is 4811 (AT&T and the Bell operating companies), and the 1987 manual after it, where
4812 is radiotelephone and 4813 wireline telephone (the regional Bells and GTE from then on). 4810
is CRSP's three-digit filler and holds the 1990s Nasdaq telecoms (MCI, WorldCom, Global Crossing,
Nextel, Qwest, Level 3, Exodus), which an S&P utilities group of the time would not have held. A
telephone rule written from the 1972 manual has 4811 only. The improvement shows up beyond the
cells it moves:

- *Table 3 Utilities:* 101-120 standard deviation 3.42% -> 2.64% (paper 2.64%), "all" standard
  deviation 1.77% -> 1.55% (1.47%), "all" minimum -6.2% -> -4.2% (-3.5%).
- *Sector count:* 144 Utilities per cohort (paper 156, within 10%; before 161).
- *1999 draft:* 91.0 -> 91.5, which was not used to choose the map.

**Alternatives** (OPEN_QUESTIONS round six, with the RMS trigger): 4810 + 4811 gives exactly 156
utilities but a larger Utilities error; 4811 + 4813 and 4811 + 4812 + 4813 score 174.5 and 175.0
against 176.0 for 4811 alone.

**Switching it off.** `--telephone-sic 481x` reproduces the 169.5 check (verified).

## 21. The trigger's sigma is the spread's root mean square about zero (2026-10-22)

`select_pairs` now sets each pair's sigma to sqrt(SSD / N), the root mean square of the formation
spread of normalized prices about zero (`--trigger-sigma rms`, the default); it was the standard
deviation about the spread's mean. The shipped check moves 172.0 -> 176.0.

| RFS cells ✓/~/✗ | before (172.0) | now (176.0) |
|---|---|---|
| Table 1 (88) | 50/16/22 | 52/14/22 |
| Table 2 Panel A (24) | 14/9/1 | 16/7/1 |
| Table 2 Panel B (40) | 28/2/10 | 28/2/10 |
| Table 3 (139) | 43/47/49 | 43/51/45 |

Figure 1 is unchanged (pair rank 4, the same five trades; Kennecott-Uniroyal's sigma moves 0.0217
-> 0.0218). The 20-cohort smoke sample falls 94.5 -> 92.5, so its threshold is lowered with it; the
module note already says the sample can move against the full result.

**What is and is not in the paper.** Section 2.2 opens a pair "when prices diverge by more than two
historical standard deviations, as estimated during the pairs formation period", and closes it at
the next crossing. It does not say about which centre the deviation is measured. The rule measures
divergence from parity (zero spread), and the paper already computes the SSD of the two normalized
series as its distance, so sqrt(SSD / N) is the standard deviation of the price difference about
the point the rule trades around. It equals the demeaned standard deviation plus each pair's
squared mean spread, under the root. This is our reading, and the check's header says so.

**Evidence beyond the cells it moves:**

- *1999 draft, Table II A trigger (408 cohorts of its window):* top 5 0.0399 against the draft's
  0.0399 (demeaned: 0.0383), top 20 0.0453 against 0.0449 (0.0433). The draft was not used to
  choose the reading.
- *RFS Table 2 A:* top-5 / top-20 trigger 0.0392 / 0.0446 -> 0.0409 / 0.0467 (paper 0.0476 /
  0.0528); round trips top 20 2.20 -> 2.10 (1.96); std of round trips 101-120 0.305 -> 0.292 (0.27).
- *Table 3 Financials 101-120 tails:* kurtosis 7.3 -> 18.5 (18.3), maximum 11.5% -> 19.3% (19.6%),
  skew 1.07 -> 2.34 (1.98).

**Against.** The 1999 draft's Tables I-II fall 91.5 -> 86.5, all in Table I (46.5 -> 41.5). Every
lost cell is a mean or median that was already 5-9% below the draft and crosses the 10% line (top-5
six-month mean 5.59% -> 5.36%, draft 5.98%); no cell moves from within 25% to beyond it. The draft
can veto a change; this is read as an objection, not a veto, because the same draft's trigger, which
measures sigma directly, is matched exactly. The RFS trigger stays 12-14% low for the top 5 and top
20 (OPEN_QUESTIONS Q7). A fitted alternative, sigma squared plus a constant, matches the RFS trigger
but lowers the 1999 score to 80.0 and is not adopted.

**Switching it off.** `--trigger-sigma std` reproduces the 172.0 check (verified).

## 22. Unknown-SIC fallback order: the security-header SIC first (2026-10-23)

`run_jobs` now fills unknown (0) dated codes from the CRSP security-header SIC before the earliest
known dated SIC (`fallbacks = (header, earliest_known_sic())`); it was earliest-first. The paper
names no SIC source for the sector assignment, and the header classification is the stock's own
primary label where the earliest-ever dated code is a proxy that can postdate the formation window.
The shipped check moves 176.0 -> 177.5; SCORE_LOG row 10.

| RFS cells ✓/~/✗ | before (176.0) | now (177.5) |
|---|---|---|
| Table 1 (88) | 52/14/22 | 52/14/22 |
| Table 2 Panel A (24) | 16/7/1 | 16/7/1 |
| Table 2 Panel B (40) | 28/2/10 | 28/2/10 |
| Table 3 (139) | 43/51/45 | 47/47/46 |

The Table 3 movers, cell by cell: Financials t_stat[1] and share_negative[4], Industrials
min[2] and Transportation share_negative[1], Utilities t_stat[1] gain ✓; Utilities median[4]
loses ✓; Industrials skew[2] and Utilities skew[3] fall ~ -> ✗. The top-pair sector-mix cells
(Q5) do not move. The 20-cohort smoke sample and Figure 1 are unchanged; the 1999 draft edition
stays 86.5. The improvement loop found and pre-measured the variant (its "V2" experiment); the
cohort cache was rebuilt with the new convention (474/474).

## 23. Table 2 Panel A over completed trading windows (2026-10-23)

The last five cohorts (formed 2002-08..2002-12) are force-closed at the sample end after 1-5
months, so their per-pair total time open is censored downward and the across-cohort dispersion
rows are inflated. `trading_stats_from_components` now drops cohorts whose six-month window was
cut by the sample end (`_window_censored`: a calendar that spans fewer than six months and runs
from the first trading day of its first month to the last of its last month was cut; stored
per-cohort flags, or cache-derived flags matched to the aggregated cohort labels by identity).
The shipped check moves 177.5 -> 178.5; SCORE_LOG row 11.

| row (paper) | all 474 | complete-only 469 |
|---|---|---|
| std time open, top5 (0.80) | 0.736 ✓ | 0.707 ~ |
| std time open, top20 (0.45) | 0.508 ~ | 0.461 ✓ |
| std time open, 101-120 (0.38) | 0.444 ~ | 0.368 ✓ |
| std time open, all (0.17) | 0.309 ✗ | 0.199 ~ |

Every other Panel A cell keeps its mark (checked cell by cell). The paper's caption ("474 months")
describes the sample, not the trading-window cohort count; the paper's own std of time open (0.17)
matches the completed-window reading better than the all-474 one, which is the reading's defense.
This closes Q1's Table 2 Panel A cell; the same sensitivity was recorded at the 169.5-era score in
cross-checks, round two. The 20-cohort smoke sample, Figure 1 and the 1999 draft edition (86.5)
are unchanged.

Two discriminating tests, run after a reward-hacking challenge to this change:

1. **Placebo (RFS, wait 1):** dropping five *mid-sample completed* cohorts while keeping the
   censored five leaves the dispersion at the all-474 values (0.737 / 0.510 / 0.442 / 0.308
   against 0.736 / 0.508 / 0.444 / 0.309). The move toward the paper is carried specifically by
   the censored windows, not by "dropping five of anything".
2. **1999 draft edition (independent paper values, sample 1963-07..1997-06, wait 0):** every
   draft cohort completes inside our cache, and the draft's published std of months open
   (0.70 / 0.50 / 0.40 / 0.20) matches the completed-window computation to 2-6%
   (0.713 / 0.472 / 0.369 / 0.205); dropping the draft's own trailing five does nothing
   (0.715 / 0.472 / 0.370 / 0.206). So in the edition where nothing is censored, the paper's
   numbers are the completed-window numbers — the filter corrects censoring, it is not a
   trailing-count knob.

## 24. We classify 495x (waste management) as Industrials (2026-10-24)

We now assign sanitary services and waste management, SIC 4950-4959, to
Industrials rather than Utilities. This is a **classification choice, not a
recovered fact**: GICS - the post-1999 S&P/MSCI scheme - puts waste management in
Industrials, while S&P's contemporaneous pre-1999 scheme, which is what the 2006
paper describes, is **not verified**, and the 1999 NBER draft is neutral on it
(see the second-edition check below). What justifies shipping it is the
measurement: **178.5 -> 183.5** (+5.0), with six of the eight gains inside the
Utilities 101-120 band.

Eight cells improve and three regress, and the gains are coherent: every one is in
the Utilities 101-120 column, which sits at the far end of a ~120-pair pool and is
therefore the most membership-sensitive band in Table 3.

| Utilities 101-120 | before | after | paper |
|---|---|---|---|
| mean | 0.77% | 0.95% | 0.93% |
| t-statistic | 3.90 | 5.76 | 6.11 |
| kurtosis | 9.65 | 5.97 | 5.52 |
| minimum | -12.64% | -7.80% | -7.87% |
| maximum | 18.48% | 12.61% | 12.13% |
| skewness | 0.31 | 0.52 | 0.66 |

Plus the Utilities all-pair minimum (-4.47% -> -3.80% against -3.52%) and the
Industrials 101-120 minimum. Regressions: the Utilities stock count (144 -> 137
against the paper's 156) drops from ✓ to ~, and the Utilities 101-120 median and
standard deviation each lose half a cell.

The change does **not** touch Q5: the top-pair sector mix is unchanged
(weight_utilities 0.774 in both states, weight_industrials 0.0745), because the
waste-management stocks never reached the top-five pairs. It works on the far end
of the sector ranking, not on the tight bands.

**Second edition check (veto test).** `EDITION_1999.md` makes the 1999 NBER draft
a second opinion that may veto a change. `scripts/edition_1999.py --cohorts
<cache>` scores **86.5 of 136 before and after** (Table I 41.5, Table II A 23.5,
Table II B 21.5 in both) - identical to row 9 of `EDITION_1999.md`. The draft does
not veto, because it has no by-sector table beyond the Table II B weights and
those barely move (weight_utilities 0.774 in both states). It also cannot
corroborate the classification. The case therefore rests on the RFS Table 3 cells
above and on GICS, with S&P's contemporaneous scheme left unresolved.

Neighbouring classification decisions were measured in the same session and all
lose, so this is a single supported change rather than a general "shrink the
sector pool" rule:

| probe | score |
|---|---|
| pipelines 4922-4924 out of Utilities | 168.5 |
| real estate 65xx out of Financials | 176.0 |
| holding/investment offices 67xx out of Financials | 165.0 |
| brokers 62xx out of Financials | 179.5 |
| local transit 41xx out of Transportation | 182.0 |
| transportation services 47xx out of Transportation | 183.0 |
| pipelines 46xx out of Transportation | tie with the shipped configuration |
| all of 48xx added to Utilities alongside 495x out | 174.5 |
| 481x telephone with 495x out (restores the count to 155) | 177.5 |
| no SIC fallback: unknown codes stay Industrials | 177.5 |
| wait-1 delays the opening only (Panel B caption read literally) | 160.5 |
| trigger sigma from spread innovations scaled to the level | 57.0 |

Those twelve were measured on this session's working copy, a snapshot taken
before #22 and #23 landed, so treat the numbers as directional rather than as
deltas against this base. Two of them are worth keeping for other questions: the
entry-only delay collapses Table 1 Panel B from 30.5 to 21.5 points, which is
independent confirmation of the 2026-10-16 fix in section 3; and the
innovation-scaled trigger produces 22% triggers, closing Q7's remaining
alternative.

## 25. Payoff-count returns measured and rejected (2026-10-24)

The paper's sentence on p. 14 -- fully invested "divides the payoffs by the number
of pairs", committed "scales the portfolio payoffs by the number of pairs that are
selected" -- can also be read as pure payoff counts, `Σπ_t / n_t` and `Σπ / N`,
which `employed_count` and `committed_count` already cache. Measured on top of
section 24 it scores **184.5 against 183.5 (+1.0)**, nine cells up and nine down.
Rejected; recorded so it is not re-run.

The gains are in the higher moments: Panel A top-5 kurtosis 9.15 -> 7.41 (paper
7.81), Panel A "all" 15.9 -> 22.9 (25.2), Panel B "all" 15.5 -> 23.5 (25.7),
Panel B top-5 minimum -15.16% -> -13.13% (-12.63%). The losses are the "all"
column's level and dispersion: mean 1.04% -> 0.99% (paper 1.10%), standard
deviation 2.00% -> 2.10% (1.67%), and its 101-120 share of negative months.

Two reasons it loses, both raised in review of the PR that proposed it:

- **The paper's own consistency check.** Its fully-invested/committed ratios are
  the only internal test it offers. The shipped book reading gives
  1.68 / 1.71 / 1.60 / 1.88 (no wait) and 1.64 / 1.69 / 1.61 / 1.90 (one-day wait)
  against the paper's 1.67 / 1.78 / 1.59 / 1.80 and 1.61 / 1.72 / 1.58 / 1.81;
  the payoff counts give 1.69 / 1.71 / 1.61 / **1.92** and 1.65 / 1.69 / 1.62 /
  **1.96**. The gap on the "all" column widens from 4.2% and 5.2% to 6.7% and
  8.3%, and "all" is exactly the column the +1.0 comes from. Section 29 re-measured
  all sixteen ratios and this paragraph has been corrected to them: it first read
  1.69 / 1.86 and 1.70 / 1.90 for the shipped set, 3.5% and 5.0% for the shipped gap,
  and 8.8% for the payoff-count gap, which divided by the no-wait paper value in both
  panels.
- **One artifact, one capital definition.** Table 3 keeps the book reading
  (`TABLE3_CAPITALS`), so adopting counts for Table 1 alone would make the two
  tables incomparable inside a single check, and the check's own header text
  (which quotes ratios of 1.58-1.81) would contradict the Table 1 below it.
  Adopting it would mean moving `INTERFACES.md`, the check header, the score log
  and the conformance thresholds together, plus a test pinning which capital
  series Table 1 reports; none of that is worth 1.0 point.

**Correction to earlier figures.** `INTERFACES.md` and section 17 quote
1.71 / 1.70 / 1.54 / 1.80 and 1.70 / 1.70 / 1.53 / 1.83. Those were measured at
the 164.0-era configuration; the current values are the ones above, and
`INTERFACES.md` now carries them.

## 26. Where 183.5 sits: the two editions on one window, and what 200 would need (2026-10-24)

Third attempt at the remaining 16.5 points, after the searches of rounds five and six in
`OPEN_QUESTIONS.md`. Nothing is shipped and the score stays at 183.5. The round did three
things the earlier ones had not: it cut our series at the date the 1999 draft stops and asked
which statistics the paper then matches; it asked how much of the gap any correction of the
extreme months could recover; and it checked whether the largest losses are bad prices.

**Verdict up front.** On the pre-1999 window our monthly "all" series matches the published
paper on mean, median, standard deviation and minimum to within 4.4%, and on the draft's own
window our six-month distribution matches the draft's maximum to within 3% and its minimum to
within 8%. Where it does not match is the *right* tail of the monthly series, where the paper's
largest month is 49% larger than ours; but section 5 shows that plugging the paper's extremes
into our series does not close the skewness and kurtosis rows either, so no correction of the
months we know are wrong reaches the paper's shape, and 200 is not reachable by any rule we
hold. Section 6 says why in the check's own numbers: 48 of the 73 ✗ cells are more than 40% off,
and none of the 69 ~ cells sits close enough to a line for a small improvement to flip a block.

### 1. Cutting the sample where the draft cuts it: four of seven rows match

Monthly, fully invested, no wait, "all", on 474 month-ends as the paper reports:

| row | ours, 1963-07 to 2002-12 | ours, 1963-07 to 1998-12 | RFS Table 1 A | reading at 1998-12 |
|---|---|---|---|---|
| mean | 1.04% | 1.08% | 1.104% | -2.2% |
| median | 0.73% | 0.76% | 0.728% | +4.4% |
| standard deviation | 2.00% | 1.62% | 1.670% | -3.0% |
| skewness | 1.30 | 2.18 | 3.42 | -36% |
| kurtosis | 15.9 | 11.9 | 25.25 | -53% |
| minimum | -12.59% | -2.70% | -2.72% | -0.7% |
| maximum | 14.12% | 11.50% | 17.18% | -33% |

One month does the damage: February 2000, -12.59%. Without 1999-2002 the same series has a
minimum of -2.70% against the paper's -2.72% and a standard deviation of 1.62% against 1.67%.
Our own table says that month is the outlier rather than a rule: the paper's text reports that
the minimum "increases" as the number of pairs rises, and its four minima are
-10.57 / -6.63 / -3.86 / -2.72% for 5 / 20 / 101-120 / all pairs. Ours are
-14.82 / -7.89 / -3.92 / **-12.59**: the first three behave, the "all" column does not, and one
month is the whole difference.

The same cut on the other portfolios (no wait): top20 mean 1.45% -> 1.54% (paper 1.436%),
sd 1.74% -> 1.76% (1.688%), min -7.89% (paper -6.63%), max 10.51% (13.30%);
101-120 mean 1.01% -> 0.99% (1.081%), sd 1.59% -> 1.54% (1.540%), min -3.92% -> -3.54%
(-3.857%). Their means and spreads match on either window; their maxima are 21% and 21% low
on both.

### 2. On the draft's window the two extremes match, the level and spread do not

The 1999 draft reports six-month returns on committed capital over 408 cohorts. Ours on the
same 408 cohorts, "all":

| | mean | median | sd | excess kurtosis | skewness | minimum | maximum |
|---|---|---|---|---|---|---|---|
| ours, no wait | 3.56% | 2.76% | 3.17% | 2.43 | 1.35 | -2.28% | **17.59%** |
| draft, no wait | 4.10% | 3.25% | 3.54% | 1.51 | 1.17 | **-2.48%** | **17.56%** |
| ours, one-day wait | 2.73% | 2.17% | 3.03% | 1.88 | 1.19 | -2.86% | **15.13%** |
| draft, one-day wait | 2.88% | 2.31% | 3.12% | 0.95 | 0.93 | -3.35% | **14.79%** |

What matches is the two extremes: the maximum to 0.2% and 2.3%, the minimum to 8% and 15%.
What does not is the level and the spread - the mean is 13.2% low and 5.2% low, the standard
deviation 10.4% low and 2.9% low, and the excess kurtosis is 61% high on no wait. Scored with
`scripts/edition_1999.py` the "all" column of the draft's Table I comes out **3 ✓ / 5 ~ / 1 ✗**
on no wait and **5 ✓ / 2 ~ / 2 ✗** on one-day wait, so this is the closest agreement in the
replication rather than an exact one, and it is closest precisely where the RFS check also
fails: at the tails.

It also means the "all" column's missing 49% on the *monthly* maximum (11.50% against 17.18%)
is not obviously a missing trading rule: the same window, measured over six months, contains a
17.59% period against the draft's 17.56%. The RFS's 17.18% is a single month; a six-month period
containing it must be at least that large, and our largest six-month period is exactly the
size of the paper's. Either the paper's largest month is a month we have at 11.5%, or their
monthly and six-month maxima are not independent numbers.

### 3. The largest losses are real prices, not bad ones

February 2000 is the whole of the "all" left tail, so it was traced to positions. Every cohort
trading that month loses, not one:

| cohort | Feb 2000 return, "all" | pairs open that month |
|---|---|---|
| 1999-09 | -15.8% | 2,979 |
| 1999-10 | -14.2% | 3,041 |
| 1999-11 | -14.6% | 3,149 |
| 1999-12 | -13.8% | 3,262 |
| 2000-01 | -12.0% | 3,111 |
| 2000-02 | -5.2% | 2,736 |

The losses are unrealized: the cohorts formed in 1999-10 to 2000-02 took *positive* payoffs
(+138 to +172 on $1 per pair) from the trades that closed that month, and still lost 12-14% on
the book. The five worst positions in cohort 1999-09 all close at the end of the trading
window (reason `end`) with payoffs of -26.4, -22.2, -21.9, -21.8 and -20.4 dollars per dollar
committed. Their short legs are real dot-com climbs, not adjustment errors: over its own
trading window each rises 22 to 29 times, and the largest single day in that window is +135%
(permno 79006, SIC 3670), +62% (84329, SIC 7370), +60%, +57% and +42% — thirty to sixty
moderate days each, not one split or delisting jump. So there is no bad price to screen out: a
book that is short those names loses whatever the construction.

### 4. The book is never sparse, so the missing right tail is not a concentration effect

A large positive outlier in a two-thousand-pair book would need the book to be nearly empty in
that month. It is not: cohort-months hold a median of 1,598 open pairs, a 10th percentile of
649 and a minimum of 297 across all 474 cohorts and both waits, and the correlation between the
absolute monthly return and 1/(1 + open pairs) is 0.012. Every cohort-month above 10% in absolute value
holds between 2,300 and 3,300 open pairs. So the paper's larger right tail cannot be a month in
which a handful of pairs carried the portfolio, and the "all" columns of Tables 1 and 3 cannot
be fixed by changing how many pairs are traded.

### 5. Even a perfect tail correction does not reproduce the paper's shape

Take our shipped "all" series and replace its three worst months with the paper's minimum
(-2.72%) and its best month with the paper's maximum (17.18%) — an oracle no rule can achieve.
That gives mean 1.08% (paper 1.10%), median 0.73% (0.728%), minimum -2.74% (✓), maximum
17.18% (✓), but standard deviation 1.93% (paper 1.67%, 15% off), skewness 2.79 (3.42, 18% off,
still ~) and kurtosis 18.4 (25.25, 27% off, still ✗). The shape gap is distributed over the
whole series, not concentrated in the months we know are wrong, so no correction of known
months can close the skewness and kurtosis rows of the "all" columns.

### 6. Census: where the last 16.5 points of the 183.5 check would have to come from

Marks against the distance from the paper, from the check as it stood at 183.5
(SCORE_LOG row 12). The shipped 187.0 moves three cells to ✓, so the bands below are that
census, not the current one; the argument they support is unchanged.

| band | ✓ | ~ | ✗ |
|---|---|---|---|
| within 10% | 149 | | |
| 10-15% | | 27 | |
| 15-25% | | 42 | |
| 25-40% | | | 25 |
| beyond 40% | | | 48 |

Across all 69 ~ cells the signed gap averages +2.9% (40 high, 29 low), so no single
nudge moves them as a block; 13 of the 69 are in the Utilities sector, which is also 12%
short of the paper's stock count. Reaching 200 needs 33 cells to move a full grade, and 48
of the 73 ✗ cells are more than 40% off, in statistics (skewness, kurtosis, median, extremes)
that the shape analysis above shows would have to move together.

### 7. Transportation is a level gap across the whole sample, not a tail gap (Q6)

The sector's standard deviations match the paper's (3.93 / 2.93 / 2.96% against 3.89 / 2.94 /
2.87% for top 5, top 20 and all), so the pairs being traded are comparable. The means are
2x the paper's, and the excess is spread out rather than carried by a few months: top-5 mean
1.22% before 1989 and 0.48% after, against the paper's 0.497% over the whole sample; the ten
largest months are 24% of the total return. With 61 stocks and about 54 within-sector pairs per
cohort, this is a selection difference of roughly two pairs per cohort, not a rule.

### 8. Our largest months are one-day crash bounces; the paper's are sustained

Comparing the two panels' extremes separates a single-day event from a month of steady gains,
because the one-day wait gives up one day of the move. The paper's maxima agree across the two
panels for top 5 (14.72% / 14.35%, 2.5% apart), top 20 (13.30% / 13.49%, 1.4%) and "all"
(17.18% / 16.32%, 5.0%), with 101-120 the exception (12.68% / 10.46%, 17.5% apart); three of
ours are not the same month at all:

| portfolio | paper max, no wait / one-day wait | ours, no wait / one-day wait | ours' largest month |
|---|---|---|---|
| top 5 | 14.72% / 14.35% | 12.84% / 9.62% | October 1987 (no wait), a different month with the wait |
| top 20 | 13.30% / 13.49% | 10.51% / 7.67% | October 1987 |
| 101-120 | 12.68% / 10.46% | 10.04% / 6.35% | October 1987 |
| all | 17.18% / 16.32% | 14.12% / 12.55% | January 2001 in both |

Three of our four maxima are the pairs that open at the close of 19 October 1987 and earn
10-20% each as the crash reverses: a one-day bounce that the no-wait rule keeps and the wait
rule gives up, which is why our two panels disagree by 25-37% where the paper's agree to
1.4-5.0% (101-120 excepted).
The paper's maxima are sustained months. So the small portfolios' upper tails are not merely
too small, they are the wrong events, and that is Q2 again: which pairs hold the top ranks in
the months that matter. January 1975 is the one sustained month we can name on both sides, and
there the paper's top 20 earns 13.6% (its Figure 2) against our 3.6%, while its "all" column is
17.18% against our 11.50% - a factor of 1.5 in both.

### 9. The extra volatility of the "all" column sits in the ranks beyond 120

The paper's own table says where to look. Its standard deviations fall from top 5 to top 20 to
101-120 and then rise slightly for "all" (2.28 / 1.69 / 1.54 / 1.67, so the ranks past 120 add
0.13 points). Ours fall the same way and then jump (2.41 / 1.74 / 1.59 / 2.00, adding 0.41). The
steps are right; the last step is three times too big:

| | top 5 | top 20 | 101-120 | all | 120 -> all |
|---|---|---|---|---|---|
| paper, no wait | 2.28% | 1.69% | 1.54% | 1.67% | +0.13 |
| ours, no wait | 2.41% | 1.74% | 1.59% | 2.00% | +0.41 |

So the whole monthly shape gap is carried by the pairs ranked past 120, and not because they are
further apart on entry - our "all" trigger matches the paper's (0.173 against 0.169). It is the
same population Q1 located: ranks 501+ have a monthly standard deviation of 2.5% and ranks 2,001+
of 5.3% in 1999-2002, and ranks 1-500 have 1.2-1.6%, which is the paper's level. Everything that
would fix the shape therefore has to change *which* loose pairs trade after 1988, and every
screen that does it (stale limits, exchange filters, share types, price and volume rules,
sections 26 and the rounds in `OPEN_QUESTIONS.md`) costs more cells elsewhere than it recovers.

**What would move the score.** Nothing found in this round, and the analysis says what is
missing rather than where a convention might be wrong: the paper's *monthly* top-tail is larger
than ours in every portfolio and sector by 20-50%, while its six-month distribution on the
draft's window is ours to within 3%. The next test that follows is not another convention
switch; it is to establish which month produces the paper's 17.18% and what its top-ranked
pairs were that month, which needs CRSP as it stood in 2002 rather than as we hold it.

## 27. Two ambiguities settled by measurement: the by-sector matching and the cohort weights (2026-10-24)

Both were open readings of the paper's own text, both are cheap to rebuild, and both lose. The
shipped check stays at 183.5. Every number below is a full 474-cohort rebuild; the variants ran
in an isolated tree with their own cache, so the shipped one is untouched.

**1. Table 3 wants the within-group matching (183.5), not a subset of the unrestricted pairs
(157.5).** Section 2.1 of the RFS says both "we restrict both stocks to belong to the same broad
industry categories" and "The minimum-distance criterion is then used to match stocks within each
of the groups". The first sentence can be read as filtering the unrestricted pairs down to
same-sector ones - every stock keeps its global nearest partner and only pairs whose two legs
share a sector enter Table 3 - and the second as doing the matching inside the group, which is
what `select_pairs_within_groups` does and what every shipped result uses. The second reading had
never been measured.

| Table 3 sector | within group (shipped) | same-sector subset of the unrestricted pairs |
|---|---|---|
| Utilities | 23.5 of 36 | 13.5 of 27 |
| Transportation | 9.5 of 27 | 5.5 of 18 |
| Financials | 18.5 of 36 | 10.5 of 36 |
| Industrials | 20.0 of 36 | 16.0 of 36 |
| **total** | **183.5** of 291 | **157.5** of 273 |

The subset reading also removes two columns the paper prints, because a same-sector subset of
the ~2,000 unrestricted pairs is far thinner than a within-group pairing of the same stocks: it
holds fewer than 120 utility pairs in the average cohort (so no Utilities 101-120 column) and
fewer than 20 transportation pairs (so no Transportation top-20 column). Both columns exist in
the RFS's Table 3 for groups of 156 and 61 stocks. Table 3 therefore settles the reading on
structure as well as on score, and the code stays as it is.

What the subset changes is the level, not the shape: Utilities "all" mean 1.19% -> 1.34% (paper
1.04%) and its share of negative months 16.5% -> 13.3% (18%), because the subset keeps the
*closest* same-sector pairs, which are the ones that trade hardest.

**2. The six overlapping cohorts are weighted equally (59.0 Table-1 points), not by their size.**
The paper corrects for overlap by "averaging monthly returns across trading strategies that start
one month apart as in Jegadeesh and Titman (1993)" and describes the result as a proprietary desk
that "delegates the management of the six portfolios to six different traders" - an equal weight
per cohort, which is what `overlap_average` does. The two alternatives had never been scored
against Table 1:

| cohort weight | Table 1 points (of 88) |
|---|---|
| equal (shipped) | 59.0 |
| number of pairs holding a position that month (one pooled book) | 57.5 |
| number of pairs the cohort selected | 59.5 |

All three sit within 1.5 points of each other, so this dimension cannot explain the shape gap
either, and the paper's own sentence picks the equal weight. No change. With this the aggregation
of the monthly series has no untested degree of freedom left: cohort weights, the capital
definition (section 25), the buy-and-hold reading of eq. (2)-(3) and the calendar-month
compounding have all been measured.

## 28. Every typed paper target is verified against the PDF (2026-10-24)

The check compares our engine with numbers that were typed out of the article by hand, and a
mis-typed target is a cell that can never be reached however good the replication is. Nothing
had ever tested them. `scripts/verify_paper_targets.py` (and `make verify-targets`) now re-reads
the article's text layer, parses Tables 1-3 positionally and compares every value with the
constants the check uses; `tests/test_paper_targets.py` runs it when `pdftotext` and the PDF are
present.

Result: **287 of 287 values agree** - Table 1 88 (11 rows x 4 portfolios x 2 panels), Table 2 64
(A 24, B 40), Table 3 135 (four sectors, 9 rows, 4 columns less Transportation's 101-120) - plus
the four sector stock counts in the Table 3 caption (156 / 61 / 371 / 1,729).

Two of the article's own encodings had to be handled, and both are why this was worth doing by
script rather than by eye: Table 1 renders minus signs as an en dash and Table 3 as the glyph
"7" in front of the digits, so the Utilities top-5 minimum prints as `70.12347` for -0.12347.
A careless transcription of either would have produced a positive target.

Two derived numbers are not printed in the article and are marked as derived where they are
used: the 2,317-stock universe is the sum of the four caption counts (156 + 61 + 371 + 1,729,
recorded at `PAIR_FORMATION.md` line 57), and the draft's mixed-pair counts are divided by its
pairs traded to give shares (its Table II B prints 3.7 / 15.4 / 15.8 / 1494.9 and
0.8 / 3.4 / 8.6 / 549.2 as counts).

**What this closes.** The remaining 107.5 points are not a transcription artefact. The targets
themselves are the published article's, digit for digit, so every unexplained cell is a
difference between our engine and the paper's data - which is the claim sections 26 and 27
support from the other side.

## 29. Capital readings re-measured, and eq. (3) read on the short position's own return (2026-10-24)

Two rounds after the payoff-count hybrid (closed PR #36, 185.0) was withdrawn. Every number
is a full 474-cohort rebuild in an isolated cache; the shipped check stays at 183.5 in this
section, and the change it leads to is shipped separately (`--short-weights`, SCORE_LOG).

### 1. Readings that "gain" the "all" kurtosis by deepening February 2000

Payoff counts (`employed_count`, section 25: 184.5) lift the Table 1 "all" kurtosis cells
toward the paper, but only because the February 2000 loss gets worse:

| "all", no wait | value-weighted books (shipped) | payoff count | paper |
|---|---|---|---|
| minimum | -12.6% | -17.4% | -2.72% |
| skewness | 1.30 | 0.31 | 3.42 |
| kurtosis | 15.9 | 22.9 | 25.25 |
| kurtosis, 1963-07 to 1998-12 | 11.9 | 11.2 | |

The one-day wait does the same (minimum -12.4% -> -17.0%, skewness 1.03 -> 0.03, kurtosis
15.5 -> 23.5). The paper's kurtosis comes from a large right tail; the count's from a deeper
left one, and its skewness collapses, a move the check cannot see because those cells are
already ✗. Two further capital bases measured the same way, applied to Tables 1 and 3 alike:

| reading | score | why |
|---|---|---|
| gross book, `2 (ΣdL - ΣdS) / (ΣL + ΣS)` | 184.5 | "all" minimum -15.3%, skewness 0.71: the same artefact |
| long-book base, `(ΣdL - ΣdS) / ΣL` | 181.5 | |
| excess instead of raw kurtosis | 177.0 | the Table 1 caption says "Absolute kurtosis is reported" |

None is adopted. **Correction to section 25:** the shipped "all" fully-invested/committed
ratios are 1.875 (no wait) and 1.904 (one-day wait), not 1.86 and 1.90; the full set is
1.68 / 1.71 / 1.60 / 1.88 and 1.64 / 1.69 / 1.61 / 1.90 against the paper's 1.67 / 1.78 /
1.59 / 1.80 and 1.61 / 1.72 / 1.58 / 1.81. Section 27's closing claim that the aggregation has
"no untested degree of freedom left" was also wrong; part 3 is one.

### 2. The editions do not differ only after 1997

Our first 408 cohorts reproduce the 1999 draft's top-5 trigger (0.0399 against 0.0399), so if
the RFS added only the 1997-2002 cohorts, its 474-cohort averages would pin down those 66. The
trigger rows would need late-sample top-5 triggers of 0.095 (ours 0.048), and the sector
weights decompose plausibly (Utilities 16%, Financials 54% of the late top 5), but the round
trips cannot: (474 x 2.02 - 408 x 2.4) / 66 = -0.33. The RFS's round trips are lower than the
draft's throughout, so the two editions differ across the whole sample and the RFS-only gap
(Q7) is not a late-sample effect.

### 3. Eq. (3) applied to the short position's own return: 187.0

Eq. (2) is applied to "the daily returns on the long and short positions", with eq. (3)'s
weight `w_i,t = (1 + r_i,1) ... (1 + r_i,t-1)`. The shipped code takes r_i of a short position
to be the shorted stock's return, so its weight is the stock's value and a short leg that runs
up 25x carries 25 times the weight of a fresh one. Read as the return *on the position*, -r,
the weight is `prod (1 - r)`: it shrinks as the shorted stock rises (floored at zero, a
position that has lost everything). Long positions are the same under both readings. The
paper's "simple interpretation of a buy-and-hold strategy" fits the shipped reading for shorts;
the formula fits either.

Score 183.5 -> **187.0**: Table 1 59.0 -> 54.0 (✓ 52 -> 43), Table 3 75.0 -> 83.5 (✓ 52 ->
64, ✗ 41 -> 36), Table 2 unchanged; Figure 1 unchanged. The 20-cohort smoke sample moves
93.0 -> 98.5.

**Diagnostics that did not choose it** (unscored tables; one-day wait unless stated):

| check | value weights (shipped) | position weights | paper |
|---|---|---|---|
| Table 7 short book mean, top 5 / top 20 / 101-120 / all | 0.47 / 0.40 / 0.65 / **0.71%** | 0.52 / 0.47 / 0.72 / **0.88%** | 0.50 / 0.44 / 0.66 / 0.91% |
| Table 7 short book sd, all | 5.13% | 4.98% | 4.60% |
| Table 5 B daily "all" sd / 1% / minimum | 0.245 / -0.518 / -2.07% | **0.191 / -0.397 / -1.47%** | 0.169 / -0.327 / -1.07% |
| same, 1963-07 to 1998-12 only, sd | 0.214% | 0.180% | |
| Table 5 B daily sd, top 20 / 101-120 | 0.306 / 0.294% | 0.302 / 0.288% | 0.296 / 0.277% |
| Table 8 post-1988 mean / sd, 101-120 | 0.61 / 1.42% | 0.51 / 1.36% | 0.33 / 1.12% |
| Table 8 post-1988 sd, all | 2.34% | 1.57% | 1.30% |
| Table 1 A "all" minimum / sd | -12.6 / 2.00% | -3.6 / 1.55% | -2.72 / 1.67% |

The short-book mean errors fall from 39% to 23% summed over the four portfolios (101-120 is
the one that rises, 2% -> 8%), and the daily "all" column that Q12 parked as "about 0.7x ours in every quantile" closes about
two-thirds of the way, before 1999 as well as after. The same table shows that the shipped
"all" mean matched for the wrong reason: our "all" long book is 7% low (1.51% against
1.62%, sd 5.66% against 5.16%) and the shipped short book was 22% low, so the two errors
cancelled in the excess return.

**Against:**

| check | value weights (shipped) | position weights | paper |
|---|---|---|---|
| Table 8 pre-1989 mean / sd, top 5 | 0.99 / 2.31% | 0.93 / 2.25% | 1.03 / 2.26% |
| Table 8 pre-1989 mean / sd, 101-120 | 0.94 / 1.54% | 0.88 / 1.47% | 1.05 / 1.53% |
| Table 8 pre-1989 mean / sd, all | 1.00 / 1.54% | 0.87 / 1.37% | 0.99 / 1.65% |
| fully-invested/committed, "all" (no wait / one-day wait) | 1.875 / 1.904 | 1.935 / 2.024 | 1.80 / 1.81 |
| Table 1 "all" mean (no wait / one-day wait) | 1.04 / 0.78% | 0.89 / 0.60% | 1.10 / 0.71% |
| 1999 draft scorer (EDITION_1999.md) | 86.5 | 77.0 (Table I 41.5 -> 32.0) | |

The mechanism is the reason for all of them. A short that has diverged is the position with
the most convergence still to come, and the position weight gives it less capital, so means
fall in every era, including before 1989 where the shipped weights match. The draft scorer's
fall is the largest objection. It is an objection rather than a veto for the same reason as
section 21's: the draft describes its own returns as "the sum of the payoffs over all pairs
... divided by the number of pairs", with no value weighting at all, so it cannot measure how
eq. (3) weights a short. Scoring the draft by that stated count measure gives 82.0 (summed) to
84.0 (compounded) under either short weight, against 86.5 for the value-weighted series it is
scored on; its numbers fit value weighting a little better than its own description, which is
why the fall is recorded rather than dismissed.

Drivers for every number here: the option is `--short-weights position`; the Table 5, 7 and 8
measurements compound the engine's per-leg values outside the cache.

**Shipped (SCORE_LOG row 13, 183.5 -> 187.0).** The support is independent of the scored cells
(Tables 5 and 7, the February 2000 tail) and the reading is one of the two the formula allows, so
it meets the bar of section 18. The objections above stand and are disclosed in the check header;
`--short-weights value` restores 183.5, and the check header then describes that reading. The
per-question ✗ counts in `OPEN_QUESTIONS.md` predate it (Table 1 now 23 ✗, Table 3 36 ✗).

Two corrections to the section above, from review. The zero floor is not only an edge case: it
wipes 780 of the 2,968,816 Table 1 positions (both waits; 0.026%) on a day the shorted stock
doubles, and from then on the leg carries no weight while it still counts in `n_t`. None of
them is in the top 5, top 20 or 101-120 portfolios, so the floor acts only on the "all"
columns, the ones that gained most; in the Table 3 runs it wipes 354 of 1,410,477, three of
them in a sector portfolio. And the draft scorer's fall is not "the means": by statistic the
9.5 points are medians -3.0, means -2.5, share negative -2.5, maxima -2.0, minima -0.5 and
skewness +1.0, a downward shift of the whole Table I distribution.

## 30. Table 5 Panel A and Table 8 are printed as diagnostics, not scored (2026-10-24)

*Superseded: both are scored since section 49 (SCORE_LOG row 15), with the rows that repeat a scored
row left out.*

The check replicated two more of the paper's tables without showing them: Table 5 Panel A
(the one-day-wait monthly series' serial correlation and its 1/5/10/25 percentiles; its mean
and standard deviation rows repeat Table 1 Panel B) and Table 8 (the same series' mean and
standard deviation before and after 1988-12). Both are properties of the series Table 1 Panel
B already reports, so neither needs a rebuild. They are printed after Table 3 under
"Diagnostics (not scored)", without marks, and the score stays the 291 Table 1-3 cells: the
goal is Tables 1-3, and these tables earn their place only where they explain one of those
cells. Every typed target in both is verified against the article by
`scripts/verify_paper_targets.py`, which now also asserts the file is the published RFS 19(3)
2006 article (running head and DOI) before parsing it.

Of the 36 comparisons, 13 are within 10% and 13 within 25%. What they say about Tables 1-3:

- **Q9 (101-120 after 1988).** Table 8 isolates it: the pre-1989 standard deviations match to
  1-4% in every portfolio, and the post-1988 101-120 mean is 0.51% against 0.33% (sd 1.36%
  against 1.12%). The 101-120 serial correlation is 0.072 against 0.19.
- **Q12 (the "all" tail).** The "all" column's left tail is still fatter than the paper's
  (5th percentile -1.27% against -0.88%, post-1988 sd 1.57% against 1.29%), the same gap
  section 29 narrowed.
- The tight portfolios' percentiles match (top 5: 5th -2.21% against -2.14%, 10th -1.50%
  against -1.52%, 25th -0.43% against -0.46%).

Two estimators are our reading and are stated in the check: percentiles are linearly
interpolated, and serial correlation is the lag-1 correlation of calendar-adjacent months
(in the strided smoke sample, months that are not adjacent do not pair).

## 31. Documentation cleanup (2026-10-24)

No measurement changed and no code changed. Nine places said something that was true when it was
written and is not true of the shipped check now; each is corrected in place, and the two paragraphs
that existed twice are now one.

- **`PAIR_FORMATION.md`'s sector map** listed Utilities as "4900–4999 and telephone 4811". Waste
  management (4950–4959) has been Industrials since SCORE_LOG row 12, so the row now says so.
- **§8** ended "`portfolio_daily` now uses counts". §15 replaced the counts with the value-weighted
  books three days later and that is what ships, so §8 now records the supersession.
- **§25** quoted the shipped fully-invested/committed ratios as 1.69 / 1.71 / 1.60 / 1.86 and
  1.64 / 1.70 / 1.61 / 1.90. §29 re-measured all sixteen ratios; §25 now carries those values
  (1.68 / 1.71 / 1.60 / 1.88 and 1.64 / 1.69 / 1.61 / 1.90), its gap percentages move with them
  (4.2% / 5.2% and 6.7% / 8.3%, not 3.5% / 5.0% and 6.7% / 8.8% — the last divided by the no-wait
  paper value in both panels), and the paragraph says what it first read.
- **§15** called the 164.0 pair "shipped"; it says "shipped then", since 183.5 and 187.0 came later.
- **§26.6's census** is the 183.5 check. It says so, and the "16.5 points" framing is scoped to that
  check everywhere it appears; at the shipped 187.0 the gap to 200 is 13.0.
- **`OPEN_QUESTIONS.md`'s four-map table** labelled the 481x + 49xx map "shipped". It is "as shipped
  then", the paragraph after it says which two sector rulings moved it, and the shipped counts are
  now stated (Utilities 137 / Transportation 61 / Financials 347 / Industrials 1,750 against
  156 / 61 / 371 / 1,729, so Utilities is 12% below the paper rather than 3% above).
- **Three dated sections** in `OPEN_QUESTIONS.md` ("Attempt at 180", "Cross-checks round two",
  "Cross-checks round five") read "the shipped check scores 169.5" in the present tense. They are
  past tense now; the ledger is the only place that says what the shipped score is.
- **One paragraph was duplicated** between `OPEN_QUESTIONS.md`'s attainability section and §26.6
  (the signed-gap average and the Utilities concentration). `OPEN_QUESTIONS.md` now points at §26.6.
- **`PAIR_FORMATION.md`'s audit block** still said the one-day wait and delisting fixes were "to come
  in a separate PR". Both shipped, with tests; the block names the file, the test and, for delisting,
  the 61,540 trades that now close on one.

What was checked and left alone: every "section N" reference resolves (sections 1-31, no gaps); no
document quotes a shipped score other than `SCORE_LOG.md` except in a dated section; the score,
mark counts and cell set in `SCORE_LOG.md` still equal `REPLICATION_CHECK.md` and
`tests/replication_conformance.json` (`test_score_log.py`); and no other numeric table is duplicated
across documents (checked line by line: two shared prose lines, both from the paragraph above).

**One staleness was operational rather than editorial, and is closed here.** The shared cohort cache
predated rows 12 and 13 — no `short_weights` stamp, so `--aggregate-only` (and with it
`make benchmark`) refused it by name — and `scripts/rebuild_manifest.json` plus the pinned copy in
`scripts/score_wrapper.py` still carried the pre-row-12 hashes of `models.py`, `sectors.py` and
`03_replicate.py`. The cache was rebuilt with `--force`, the rebuilt check came out byte-identical to
the committed one (187.0 of 291), `--aggregate-only` accepts it again, and both copies of the hashes
were re-pinned to the code that built it, so `formation_changed()` now reports no change. The order
matters and is recorded under "Where the number is enforced" in `SCORE_LOG.md`: re-pin after the
rebuild, never before.

## 32. Tables 4 and 7 and Figure 4, read in the paper's own terms (2026-10-25)

The check prints Tables 1-3 and, as diagnostics, Table 5 Panel A and Table 8. Three further pieces
of the paper speak directly to the open questions and were not in it: the risk block of Table 4,
the long/short decomposition of Table 7, and the correlations the paper prints in the Figure 4 text
(0.48 full sample, 0.51 before 1989, 0.18 after; 0.41 / 0.42 / 0.20 on five-factor residuals).
All three are computable from the shipped engine and the public Fama-French files, so they were
measured on full 474-cohort runs. The numbers live in `OPEN_QUESTIONS.md` under "Cross-checks,
round nine"; this section records what was measured and what it settles.

**How it was measured.** The cohort loop of `03_replicate.py` was re-run outside the cache (same
`vol_common` universe, RMS trigger, `--short-weights position`, wait 1) keeping, per cohort, the
value-weighted *long* and *short* legs of each portfolio as well as their difference, then
overlapped with the same Jegadeesh-Titman average the driver uses. Table 4's regressions use
Fama-French Mkt-RF, SMB and HML, Carhart momentum, and the paper's reversal factor built from the
Fama-French 10 prior-return deciles (top three minus bottom three), with Newey-West errors at six
lags. The factor files are the locally pinned Fama-French downloads; the paper's values are the
RFS text layer, which `scripts/verify_paper_targets.py` already parses for Tables 1-3, 5 and 8.

**What Table 7 settles.** Both books replicate in three of the four portfolios. The long book earns
1.245 / 1.359 / 1.482 per cent a month against the paper's 1.245 / 1.330 / 1.458 and 1.507 against
1.623; the short book earns 0.522 / 0.467 / 0.717 / 0.878 against 0.501 / 0.435 / 0.663 / 0.908,
within 9% in every column, and their standard deviations are 8-11% too wide in the loose bands.
Section 29's "short book 22% low" (0.708 for "all") is the quantity weighted by the shorted
*stock's* own value, which this build no longer ships. So the remaining Table 7 gap is the "all"
portfolio's long book (-7%) plus the dispersion of both books, not a leg-wide bias: a leg-wide bias
would have shown in the top 5 too, and does not.

**What Table 4 settles.** The risk profile replicates (Sharpe 0.34 / 0.59 / 0.52 / 0.41 against
0.35 / 0.59 / 0.55 / 0.45; standard deviations within 6%), so the pairs' *shape* of risk is right.
Two rows do not. Persistence: the 101-120 band's monthly autocorrelation is 0.07 against the
paper's 0.19, and the "all" portfolio's is 0.18 against 0.12 (+50%); the top 5 and top 20 match
(0.11 / 0.14 and 0.24 / 0.24). Factor exposure: the "all" portfolio's market beta is
+0.059 (t = 4.06) where the paper reports -0.145 (t = -3.10), and its reversal loading is -0.106
against +0.201 - the same sign once the paper's own sign convention is applied (they call a pairs
portfolio's reversal exposure positive), but about half the size. Our broad portfolio is net long
the market and the paper's is net short.

**What Figure 4 settles.** Two portfolios with no positions in common are correlated 0.32 in our
build against 0.48 in the paper (0.39 against 0.51 before 1989, 0.04 against 0.18 after), and
0.28 against 0.41 on five-factor residuals. The paper's reading - a latent common factor that goes
quiet after 1988 - is visible in ours in the same shape but at about two thirds the level, and
factor adjustment removes a similarly small share of it in both. Our disjoint bands behave more
independently than the paper's, which is what a more idiosyncratic pool of matches looks like.

**Two cross-checks that close routes rather than open them.** First, the paper's own equity-premium
column (S&P 500 in excess of bills, 0.410% a month with a 4.509% standard deviation) against our
panel's value-weighted market over the same 474 months (4.564% standard deviation): the dated data
is not noisier than the paper's at the market level, so the "all" bucket's excess dispersion is a
property of the pairs, not of the panel. Second, the stale screen: `--max-stale-share` 0.99 / 0.95
/ 0.90 / 0.85 scores 173.0 / 187.0 / 182.0 / 180.5, so both directions lose and the shipped 0.95 is
a maximum of the scan. Tightening does buy the exact tail cells Q2 predicts (Table 1 Panel B
101-120 maximum 5.85% -> 8.86%) and pays for them with level cells (top 5 t-statistic 6.22 -> 7.29
against 6.26). That is the same trade section 19.5 measured at 0.50 and 0.75, now with the curve
either side of the shipped value.

**Not shipped.** These are measurements, not a new setting: nothing in the engine, the cache or the
score changed, and the check still reads 187.0 of 291. Table 7 and Table 4 are candidates for the
diagnostic block that already holds Tables 5 Panel A and 8; that needs the long and short monthly
series in the cohort cache (a format bump and a rebuild), so it is left as a separate change.

## 33. The paper's Table 1 = Table 7 identity, and the convention that breaks it (2026-10-25)

Table 7 prints the long and the short book of each portfolio, and Table 1 prints the portfolio.
In the RFS text layer the two agree to the last digit in three of four columns and to 1 bp in the
fourth:

| | top 5 | top 20 | 101-120 | all |
|---|---|---|---|---|
| Table 7 long - short | 0.01245 - 0.00501 = 0.00744 | 0.01330 - 0.00435 = 0.00895 | 0.01458 - 0.00663 = 0.00795 | 0.01623 - 0.00908 = 0.00715 |
| Table 1 Panel B | 0.00745 | 0.00895 | 0.00795 | 0.00715 |

That identity is not a coincidence of rounding, and it pins down an implementation detail the text
leaves implicit. A net return built by compounding the *difference* of the two daily leg returns
cannot differ from the difference of the two compounded books by less than the legs' covariance
term. Ours is worth four to five basis points a month: the shipped build reports 0.69% for the
top 5 where its own two books differ by 0.73%, and 0.60% for "all" where they differ by 0.63%. For
the identity to hold at 1 bp, the paper must compound each leg to a monthly return first (eq. 2 on
the long book, eq. 2 on the short book, "the daily returns are compounded to obtain monthly
returns") and subtract the two monthly returns.

**What that costs.** The engine compounds the daily difference (`portfolio_daily` returns one
series, `cohort_monthly` compounds it). Reading the paper's way - compound the long book and the
short book separately, then subtract - was implemented behind a temporary switch and measured on a
full 474-cohort rebuild: **184.0 of 291, three points below the shipped 187.0**.

| | shipped (daily difference) | paper's way (monthly legs) | paper |
|---|---|---|---|
| Table 1 Panel B mean, top 5 | 0.69% | 0.73% | 0.74% |
| Table 1 Panel B mean, all | 0.60% | 0.63% | 0.71% |
| Table 1 cells | ✓ 43 / ~ 22 / ✗ 23 = 54.0 | ✓ 46 / ~ 17 / ✗ 25 = 54.5 | |
| Table 3 cells | ✓ 64 / ~ 39 / ✗ 36 = 83.5 | ✓ 58 / ~ 44 / ✗ 37 = 80.0 | |

The faithful reading closes about a third of the mean gap in every Table 1 column and repairs the
minimum cells it should (top 5 Panel A minimum -14.94% -> -13.11% against the paper's -10.57%,
Panel B -15.29% -> -13.56% against -12.63%, both now within 25%) and one kurtosis cell (top 5
Panel A 9.38 -> 7.61 against 7.81, now within 10%). It loses more elsewhere: the maximum cells fall
further away (top 20 Panel A 10.23% -> 9.34% against 13.30%, 101-120 9.98% -> 8.05% against
12.68%, two cells from ~ to ✗), two kurtosis cells go from ~ to ✗, and Table 3 as a whole gives up
3.5 points because the sector portfolios' means are already at or above the paper's (Q6) and the
faithful reading lifts them again.

**Where this leaves the score.** The shipped 187.0 therefore carries about three points of
convention: it is the higher of the two readings, not the one the paper's own arithmetic implies.
The deviation is invisible in the check header, which lists the other conventions that are "our
reading of the paper, not its words" but not this one. Recording it is the point of this section;
choosing between 187.0 with the convention stated and 184.0 on the paper's arithmetic is a
decision for the replication's owner, because the two readings differ in which cells they match,
not in how carefully they were measured. Shipping the faithful reading also means listing the
convention in the generated header, bumping `CACHE_FORMAT`, re-pinning `rebuild_manifest.json`
and adding a `SCORE_LOG.md` row, which is why it is not bundled into this documentation change.

## 34. Table 2's decile-difference row: answered from the paper's prose, and a bug behind it (2026-10-25)

Q4 has been parked since section 15 because a mean of integer decile gaps *among mixed pairs*
cannot be below one, and the paper prints 0.97. The paper's own text settles it without any
guessing: "About two-thirds of the pairs combine stocks from different size deciles (i.e., 'size
mixed pairs'), and the stocks in mixed pairs differ on average by a single decile." So the row is
the mean |decile difference| conditional on the pair being mixed, and 0.97 says that in the paper
almost every mixed pair is exactly one CRSP size decile apart. The sub-one value is then just the
handful of pairs their decile assignment put in the same bucket after the fact - not evidence of an
exotic definition.

Measured on our pairs, with the same CRSP breakpoints and the same deciles the neighbouring rows
already match on (`avg_size_decile`, `weight_top3_deciles` and `weight_top5_deciles` are all within
6%, so the decile variable itself is not in question):

| reading (conditional on mixed pairs) | top 5 | top 20 | 101-120 | all |
|---|---|---|---|---|
| ours, mean absolute gap | 1.66 | 1.68 | 2.33 | 2.67 |
| ours, share of mixed pairs one decile apart | 50% | 53% | 39% | 33% |
| ours, deciles recomputed inside each sector | 2.43 | 2.44 | 2.58 | 2.58 |
| paper, mean absolute gap | 0.97 | 0.97 | 0.97 | 0.98 |

Two conclusions. First, the row is a composition fact about our pair pool, not a formula we failed
to guess: our mixed pairs are as likely to be two, three or four deciles apart as one, while the
paper's are almost always neighbours. That is the same population difference Q2 and Q5 keep
turning up, now measured in a place where the paper prints a single number. Second, the row is
mislabelled in the build: `composition_stats` sets `avg_decile_diff_mixed_pairs` to
`diff[ok].mean()` - the mean over *every* pair - exactly like the `avg_decile_diff_all_pairs` key
beside it, so two differently named statistics carry the same number. SCORE_LOG row 6 shows the
all-pairs average was a deliberate choice ("Panel B decile-difference row reports the all-pairs
average", 165.0), taken when the paper's value looked unreachable, so what is wrong is the label
and the duplicated key, not the arithmetic. The all-pairs mean is 1.12 / 1.22 / 1.61 / 2.15 (what
the check shows); the quantity the paper labels is 1.66 / 1.68 / 2.33 / 2.67. Reporting the
paper's quantity instead would move the top 5 cell from ~ to ✗, i.e. cost half a point.

The other Panel B rows in the same cohort run: `share_mixed_decile_pairs` 0.714 / 0.696 / 0.746 /
0.814 against the paper's 0.66 / 0.69 / 0.75 / 0.82 (the top 5 is the one that is off, 8% high),
consistent with a pool that mixes size more than the paper's.

## 35. Table 7 joins the scored set: 187.0 of 291 -> 213.5 of 323 (2026-10-25)

Section 32 measured Table 7 from outside the driver. This ships it: the cohort cache now stores
each portfolio's two books (the `long_book` and `short_book` capitals, `CACHE_FORMAT` 5, written
by `portfolio_legs` in `src/project/evaluation.py`), `table7.csv` summarises them, and the check
prints them under "Table 7 (long and short books, one-day wait)" as **scored** cells. The rows are
the four the paper prints for each book: mean monthly return, Newey-West standard error, standard
deviation and monthly serial correlation, for the four portfolios - 32 cells.

| | top 5 | top 20 | 101-120 | all |
|---|---|---|---|---|
| long book mean | 1.25% / 1.24% ✓ | 1.36% / 1.33% ✓ | 1.48% / 1.46% ✓ | 1.51% / 1.62% ✓ |
| short book mean | 0.52% / 0.50% ✓ | 0.47% / 0.43% ✓ | 0.72% / 0.66% ✓ | 0.88% / 0.91% ✓ |
| long book sd | 3.87% / 3.88% ✓ | 3.70% / 3.65% ✓ | 3.80% / 3.44% ~ | 5.66% / 5.16% ✓ |
| short book sd | 3.55% / 3.26% ✓ | 3.40% / 3.16% ✓ | 3.50% / 3.15% ~ | 4.98% / 4.60% ✓ |
| long serial correlation | 0.084 / 0.06 ✗ | 0.089 / 0.09 ✓ | 0.133 / 0.13 ✓ | 0.16 / 0.17 ✓ |
| short serial correlation | 0.132 / 0.11 ~ | 0.106 / 0.12 ~ | 0.080 / 0.12 ✗ | 0.136 / 0.16 ~ |

32 cells, ✓ 23 / ~ 7 / ✗ 2 = 26.5 points, so the total goes 187.0 of 291 (64.3%) to **213.5 of 323
(66.1%)**: the cell set grew by a table this build replicates better than its average, so both the
total and the rate rise. The two misses are both serial correlations: the top 5 long book's (0.084
against 0.06) and the 101-120 short book's (0.080 against 0.12), the second the same band's
persistence gap Table 4 shows.

Three details worth recording. First, the books are compounded on their own daily series and then
differenced, which is what the paper's identity requires (section 33) - but Table 1 keeps the
daily-difference convention it has always had, so the two are reported side by side rather than
forced to agree; Table 1's 88 cells are byte-identical before and after this change, as are
Table 2's 64 and Table 3's 139. Second, the refactor that added `portfolio_legs` moved the leg
arithmetic into one place (`_leg_arrays`) used by both it and `_vw_legs`, and the existing
hand-calculated leg tests pass unchanged. Third, the four paper values that back the new cells were
typed from the RFS text layer and are now checked by `scripts/verify_paper_targets.py` (`Table 7:
32 values compared`), bringing the typed targets it verifies to 355.

The 1999 draft's Table V prints the same decomposition; it is not scored, as usual, and
`EDITION_1999.md` is unchanged.

## 36. The whole paper, indexed: nine tables and four figures in one place (2026-10-25)

Section 35 added Table 7 and left the obvious follow-up: which parts of the paper are still not
looked at, and what would each one cost? `COVERAGE.md` answers it with one row per table and figure
- what it measures, whether the check scores it, how many cells it holds, and where the evidence
lives - so the question "are we replicating the paper or three of its tables?" has a written answer
that a reviewer can check.

The inventory is nine tables and four figures. Scored: Tables 1 (88 cells), 2 Panel A (24), 2
Panel B (40), 3 (139) and 7 (32). Diagnostic, printed without marks: Table 5 Panel A (20) and
Table 8 (16). Measured and recorded, not printed: Table 4 (both blocks, section 32), Table 5
Panel B (the daily panel, cross-checks round two), Table 9 Panel A (the top-three-decile universe,
same section) and Figures 2, 3 and 4 (rounds two and six, and section 32). Unreplicated: Table 6
(random pairs) and Table 9 Panel B (short recalls). Figure 1 is a pass/fail check.

Two things the inventory settles. First, the scored set is close to what this data can score: the
remaining tables are mostly the *same series* counted again (Table 4's mean and standard deviation
repeat Table 1 Panel B, Table 5 Panel A and Table 8 re-measure it), which is why they are diagnostics
- scoring them would weight one series three times. Second, of the four additions that are genuinely
new, only Table 4's Sharpe and persistence rows are free (8 cells, about 5 of them matching), and
the rest need new data paths: Table 5 Panel B a daily panel in the cache, Table 9 Panel A pairing
restricted to the top three deciles, Table 9 Panel B a recall rule in the engine plus volume, Table
6 a resampling step.

The section also records the five places where the published version contradicts itself, because
each one is a trap for anyone "fixing" a cell to match: Table 9 Panel A prints its skewness and
kurtosis rows the wrong way round (kurtosis 0.02 beside skewness 7.01, both plausible once
swapped); Table 1's caption says absolute kurtosis while Table 9's, read as printed, is an excess
kurtosis; Figure 3's endpoint (about 40) cannot be the compounded series its caption describes
(about 66 from its own Table 1); Table 5 Panel B's "all" column is inconsistent with its own monthly
"all" (9.3 monthly units of the daily standard deviation against 4-7 elsewhere); and Figure 2's
caption months disagree with its axis and with Table 1. None of these changes a score: they are
reasons not to chase one.

The three documents are unchanged in their roles. The published RFS article is the target; the Yale
ICF working paper carries the same numbers (checked value by value) and is only a layout control;
the 1999 draft is a second opinion with its own 136 scored cells that may veto but never justify.
Where the draft has been decisive - the trigger's sigma as the root mean square about zero, and the
by-sector matching - it is recorded in sections 21 and 27.

## 37. Figure 2 is aligned; Figure 3 is not recoverable, and that is recorded (2026-10-25)

The figures are 150-dpi rasters inside the PDF, so comparing them with our series had lived in
prose: "correlates 0.68 and 0.76", "ends near 40". Prose cannot be re-run. `scripts/digitize_figures.py`
now reads Figure 2 once and commits `report/replication/reference/figure2_bars.csv`, and the check
prints the comparison every run. Figure 3 was attempted and abandoned; the reasons are below.

**Figure 2, aligned.** The scale is anchored on the paper's own Table 1 Panel A top-20 maximum
(13.295%), the only number the figure shares with a table, and the bars' baseline is measured from
where they end (row 199 of the raster, not the middle of the three-pixel axis rule). Four checks
show the alignment is right rather than assumed:

- **the bucket**: against the four portfolios the bars correlate best with the top 20 (0.51 / 0.61
  monthly; the next best is the top 5 at 0.38 / 0.44, and 101-120 and all are near zero), which is
  what the caption says;
- **the offset**: scanning -3..+3 months, the two correlations peak at **zero** (1.015 against
  0.999 at minus one and 0.48 at plus one), so the month mapping is not slid;
- **the annual sums**: 0.84 across 40 years, with mean annual returns of 16.4% (ours) against 14.9%
  (bars) - a 640-pixel raster carries 1.19 columns per bar and cannot resolve months, but it does
  carry years;
- **the extremes**: the tallest bar is the January 1975 month, smeared by the raster across
  November 1974 - January 1975, which is the month Q2 and Table 1 both point at; the deepest is the
  1974 bear market (ours April, the paper's February).

What still disagrees is the tallest *month*: ours is October 1987 (10.23%), the paper's is that
1974-75 bar (13.30%). That is Q2 in one line, and it is the same gap the prose recorded before.

**Figure 3, abandoned with evidence.** Two independent readings of the same pixels were tried: a
topmost-ink envelope, and a tracker that follows the two ink runs per column. They agree on the rise
through 1987 (both correlate about 0.95 with our cumulative path) and disagree completely about
afterwards - the envelope says the curve ends 60% below its 1987 level, the tracker says within 4%.
The figure has no readable axis labels (no OCR here), draws its legend inside the plot, and its two
curves cross, so nothing in it can be checked against a printed number. What it plots is the same
monthly returns as Table 1 Panel A, which the check scores cell by cell: reading it back adds no
information and risks a wrong one. `tests/test_figure_fixtures.py` asserts that no Figure 3 fixture
is shipped, so the abandoned reading cannot creep back in.

**Figure 4 needs no image work.** Its six correlations are printed in the paper's text (0.48 full
sample, 0.51 before 1989, 0.18 after; 0.41 / 0.42 / 0.20 on five-factor residuals), so the check
computes ours from the cached one-day-wait series and prints them beside the paper's: 0.32 / 0.39 /
0.04, with rolling 24-month averages of 0.38 and 0.06. The residual version needs the Fama-French,
momentum and reversal factors and stays a recorded measurement (section 32).

None of this carries marks: a bar recovered from an image is evidence about which periods disagree,
not a value the paper prints. No scored cell moves - the check still reads 213.5 of 323.

## 38. Figure 3 tracked properly: both curves match ours at 0.997 (2026-10-25)

*Superseded in part by Section 42: the figure has a readable log scale and labelled curves, and
it plots the one-day-wait series.*

Section 37 abandoned Figure 3 after two readings of its pixels disagreed. That was premature: the
disagreement was a bug in both readings, not a property of the figure. Each took the topmost ink (or
the top two runs) per column, and the figure prints its **legend inside the plot**, so from about
column 400 the text's runs replace the curves'. One reading therefore followed a legend line to a
"60% give-back" and the other followed the same text in the opposite direction.

The fix is a tracker rather than a per-column rule: find the first column where twelve consecutive
columns carry exactly two thin ink runs (left of the legend, where the two curves are unambiguous),
then walk right taking from each column the run nearest the previous position, rejecting a jump of
more than 40 rows as text. Both curves can then be followed to the right edge of the raster, and the
months are mapped across the *curves'* columns instead of the raster's, which is what put the
earlier readings' endpoint in the tick-label margin.

With that, Figure 3 is usable, and it agrees with us:

| | ours | paper, track 1 | paper, track 2 |
|---|---|---|---|
| shape correlation of the cumulative paths | 1 by definition | 0.997 | 0.997 |
| share of the total rise made after 1987 | 19% | 15% | 17% |

Three checks say the reading is stable rather than lucky. The post-1987 share does not move across
18 settings of the jump guard (25 / 40 / 60 rows), the smoothing window (5 / 7 / 11 columns) and the
start rule (8 or 12 clean columns). It matches the paper's own Table 8 arithmetic independently:
0.375% a month for the 168 months after 1988 is 15% of 0.895% a month for all 474. And the two
tracks stay distinct to the end (their rises are 166 and 114 pixel units), so the tracker is not
following one curve twice.

None of the level is recoverable - the axis carries no numbers - so the figure stays a shape
comparison and is not scored. What it now supports is the statement Section 37 could not make: the
paper's cumulative curve and ours rise in the same way, with about a sixth of the total made after
1987 on all three. The earlier "61% give-back" is withdrawn here and in `COVERAGE.md`.

## 39. What would actually move Tables 1-3: one month, measured (2026-10-25)

*The single-month table is recomputed in Section 42 with Table 1's estimator and a control.*

Three rounds of levers were tried against the first three tables and all of them cost points:
the paper's leg-compounding arithmetic (Table 1 +0.5, Table 3 -3.5, net -3.0), demoting
frozen-quote pairs from the ranking with the pool intact (-16.5), the same demotion restricted
to pairs whose *both* legs are frozen (-7.5), and three size-adjacency ranking variants (0 to
-5.0 on Table 2 Panel B alone). The shipped configuration is a sharp local optimum: every
single knob costs 3 to 16 points.

This section records the reason, now quantified rather than argued. The top-20 portfolio's
three shape cells miss together, and one month accounts for all three:

| top 20, no wait | ours | with January 1975 at its printed height | paper |
|---|---|---|---|
| skewness | 0.81 | **1.29** | 1.39 |
| kurtosis | 8.07 | **10.75** | 10.54 |
| maximum | 10.23% | 13.30% | 13.30% (the same bar, so by construction) |

January 1975 is the tallest bar of Figure 2 and the month Table 1 prints as the top-20
maximum, so the maximum row moves by construction and the skew and kurtosis rows are the test:
both come into range. That is why no rule can lift these cells - the lever is a month, not a
parameter - and it is the same month Q2 records: our top-ranked January 1975 pairs are
frozen-quote Nasdaq names that never converge, because CRSP's pre-1983 Nasdaq rows carry no
volume field and the paper's "one or more days with no trade" screen cannot be applied without
deleting an entire exchange.

The check now prints this attribution under the figures, so the claim is re-derived on every
run from the digitised bar and the cached series rather than quoted. No scored cell moves: the
check still reads 213.5 of 323, of which the first three tables are 187.0 of 291.

## 40. Eight levers measured against Tables 1-3, and the one that cannot be pulled (2026-10-26)

The first three tables have been at 187.0 of 291 since Table 7 joined the scored set. Four rounds
of work asked whether that is a plateau or an unfinished job, and measured every lever the paper's
other tables and figures suggest. The answer is a plateau, and the reason is one month.

| lever | what it changes | full-sample score |
|---|---|---|
| shipped | - | **213.5 of 323** (Tables 1-3: 187.0 of 291) |
| the paper's leg-compounding arithmetic (Table 1 = Table 7) | Table 1 becomes the difference of the books | 184.0 earlier; Table 1 +0.5, Table 3 -3.5 |
| demote frozen-quote pairs from the ranking, pool intact | top ranks hold tradeable pairs | 197.0 (Table 1 54.0 -> 45.5) |
| the same, both legs frozen | a much smaller demotion | 206.0 (Table 1 54.0 -> 51.0) |
| three size-adjacency ranking variants | sizes like the paper's pairs | Panel B alone: 13.0 / 10.5 / 8.0 of 40, no gain |
| **trigger at 2.33 sigma instead of 2.00** | matches the paper's printed average trigger | **203.5** (Table 2 A 20.5 -> 22.0, Table 1 54.0 -> 46.0, Figure 1 lost) |
| stale screen 0.85 / 0.90 / 0.99 | the frozen-quote population | 180.5 / 182.0 / 173.0 |
| short weights `value` | eq. (3) read on the shorted stock | 183.5 |

The trigger test is the instructive one. The paper's own Table 2 prints an average trigger of
0.0476 / 0.0528 where our sigma produces 0.0409 / 0.0467, so entering 16% deeper is exactly what
the paper's numbers ask for - and it does fix what it should (Table 2 Panel A 20.5 -> 22.0, and
Table 7 stays at 26.5) while costing 8 points in Table 1 and 3.5 in Table 3, because fewer, deeper
positions make the monthly series lumpier. Even the sign of that trade is against us.

Two conventions were also checked and closed. Every interior month averages exactly six cohorts
(469 of 474 months; the rest are the sample's edge months), so no "flat trader" is being dropped
from the overlap average. And extreme daily returns, up to +1595% in a day at 0.01% of rows, cannot
move the "all" bucket: a single such leg is capped near 1/1940 of the book.

What is left is the attribution in section 39: the top-20 shape cells are one month's worth of
difference - January 1975, the tallest bar of Figure 2 - and that month is the frozen-quote
divergence whose stocks our CRSP vintage cannot screen out, because pre-1983 Nasdaq rows carry no
volume field. That is a data limit, not a parameter. Any future attempt needs a 2002-vintage CRSP
extract, or a decision to score a different cell set rather than to tune this one.

## 41. Q2 closed from both ends: no CRSP field, and the paper's own pair count (2026-10-26)

Q2 has been "narrowed, not closable with the data we hold" since section 19.5. A live WRDS probe
settles it, and the answer is not the one the question assumed.

**Nothing in CRSP separates the frozen Nasdaq names.** CRSP's new security-info history carries
exactly the fields that could have stood in for a missing trade flag - `tradingstatusflg`,
`exchangetier`, `securityactiveflg`, `conditionaltype`, `nasdcompno`. Pulled for forty frozen
Nasdaq names (fewer than 25% of days moving in 1974H2) and forty liquid ones, every field agrees:
`tradingstatusflg` "A", `exchangetier` "N/A", `securityactiveflg` "Y", `conditionaltype` "RW",
`nasdcompno` populated for all of them. The daily files are no better: `crsp.dsf` and
`crsp_q_stock` record **no volume and no trade count for any Nasdaq name in 1974** - the NYSE
control has volume on all 128 days of the window while `numtrd` is null for every stock, including
the one that trades. Re-downloading cannot help either, because both views are the current (2026)
release: CRSP's 2003 vintage, which the paper used, is not served by WRDS.

**The paper's pair count says their screen did not remove our frozen names.** Our formation
universe for the 1974-12 cohort holds 2,626 stocks - 1,793 Nasdaq, 777 NYSE, 56 AMEX - and the
Nasdaq names move on only 34% of days at the median, against 85% on the NYSE. Screening at 25%
frozen days would drop 555 of them (21% of the universe) and take the pair count to about 1,590,
where the paper reports 2,057 with our build at 2,009. So their Nasdaq population cannot have been
screened the way ours would have to be: their 2003 file either carried volume for those names or
did not require it. That is consistent with everything the screens measured - they buy a few tail
cells and cost 7 to 16 points, because the frozen names are part of the population the paper
counted, not a minority it excluded.

What remains is the one-month attribution of section 39: January 1975 is worth the top-20 skew,
kurtosis and maximum cells, and it needs returns for quote-only Nasdaq names that neither our
vintage nor a fresh WRDS pull can supply.

## 42. Review fixes to Figures 2 and 3 (2026-10-26)

A code review of #44 found five problems in the figure readings; each is fixed and the numbers
below replace those of Sections 37-39 where they differ.

**Figure 3 has a scale, labelled curves, and a stated series.** Section 38 said the figure has no
readable axis labels and two unlabelled curves. It has a log axis labelled 0.1 / 1 / 10 / 100 whose
decades are full-width rules (rows 5, 114, 223 and 331.5 of the raster, 108.9 pixels a decade, a
linear fit exact to under 0.002 of a decade), and three labelled curves: Fully Invested Pairs,
Committed Capital Pairs and the Equity Premium. The paper's text names the series: "the cumulative
excess returns of the top 20 one-day-waiting strategy". The digitizer now writes levels, and the
check compares Table 1 Panel B's series:

| top 20, one-day wait | fully invested: ours / figure / Table 1 B compounded | committed: ours / figure / Table 1 B compounded |
|---|---|---|
| end level, 2002-12 | 72.1 / 39.7 / 72.5 | 11.6 / 11.5 / 11.5 |
| correlation of the log paths | 0.998 | 0.998 |

The committed curve agrees three ways. The fully invested curve agrees with neither our series nor
the paper's own Table 1, which is the contradiction COVERAGE lists; it is not a scale error, because
the same scale reads the committed curve exactly. Months are binned across the plot frame (columns
55-630) rather than the tracked columns.

**Figure 2's annual sums used up minus down.** A month whose columns hold a neighbour's bar carries
both a positive and a negative extent, so the sum mixed directions. The fixture now has a `signed`
column, the reading at the column nearest each month's centre, and the annual sums use it: the
correlation is 0.75 (not 0.84) and the paper's mean annual sum 15.5% (not 14.9%). Month bins now
span the plot frame rather than the inked columns; on this raster the two coincide (columns
66-629), so `up` and `down` are unchanged.

**The tallest bar is a window, not a month.** It is three columns wide (229-231), centred on
December 1974, and covers November 1974 to January 1975. The single-month table now sets the month
of that window where our return is highest (January 1975, 4.49%) to the printed maximum, uses
Table 1's estimator (`summary_stats`, raw moments) rather than a separate one, and adds a control
that sets our own tallest month (October 1987) instead:

| top 20, no wait | ours | 1975-01 set | control: 1987-10 set | paper |
|---|---|---|---|---|
| skewness | 0.81 | 1.30 | 1.15 | 1.39 |
| kurtosis | 8.10 | 10.93 | 10.64 | 10.54 |

The control moves the cells almost as far, so the table measures the size of the shape gap (about
one month at the paper's maximum) and does not by itself locate the month; Section 39's "the lever
is a month, not a parameter" rests on Q2's evidence, not on this table.

**The check's prose is computed.** Every number in the figure section is now formatted from the
values in the tables beside it.

## 43. Where the 104 missing points are: a per-cell margin table (2026-10-26)

The score is a sum of weights over cells, so the interesting question for a "can we do better"
request is not which blocks are weak but how far each individual cell is from the next grade
boundary. `scripts/03_replicate.py` marks ✓ within 10% of the paper, ~ within 25% and ✗ beyond,
so each cell has a measurable *margin*: `|ours/paper - 1| - 0.10` for a ~ cell and
`- 0.25` for a ✗ cell. Reading those margins off `table1.csv`, `table2_panelA.csv`,
`table2_panelB.csv`, `table3.csv` and `table3_counts.csv` gives the whole picture.

Tables 1-3: 291 cells, 187.0 points (✓ 152, ~ 70, ✗ 69). The 104 missing points split as
Table 1 34.0, Table 2 Panel A 3.5, Panel B 11.0, Table 3 counts 0.5, Table 3 sectors 55.0.
`scripts/cell_margins.py` prints all of this from the built tables, and its numbers are the ones
quoted here.

**By statistic, the loss is almost entirely the tails.**

| family | cells | points | of |
|---|---|---|---|
| mean, median, nw_se, t_stat, std | 40 (Table 1) | 36.0 | 40 |
| share_negative, mean (committed) | 16 (Table 1) | 11.0 | 16 |
| skew, kurtosis, min, max | 32 (Table 1) | **7.0** | 32 |
| the same four | 60 (Table 3 sectors) | **21.5** | 60 |
| everything else (Tables 2, counts) | 199 | 158.5 | 199 |

The four tail statistics are 92 of the 291 cells and carry 28.5 of the 187.0 points - they run at
31% when the rest of the table runs at 81%. Section 39 already showed why: the paper's top-20
series has a right tail we do not have, and one month moved at its printed height fixes skewness,
kurtosis and the maximum together.

**By margin, the near-misses are numerous but not enough.** Cells within 1%, 3% and 6% of a
boundary, counting every flip as +0.5:

| within | cells | points gained | score if every one flipped |
|---|---|---|---|
| 1% | 11 | +5.5 | 192.5 |
| 3% | 24 | +12.0 | 199.0 |
| 6% | 42 | +21.0 | 208.0 |
| 10% | 62 | +31.0 | 218.0 |

So the "hit 200" target needs more than every cell within 3% of a boundary to land - it needs the
cells within 6%, and those are not independent near-misses. They are the same two residuals
repeated across portfolios: a level 12 to 25% too low in the 101-120 and "all" columns (mean,
median, nw_se, committed), and a net-of-threshold touch on three Table 2 Panel A dispersion rows.

**The direction histogram says the level residual is ours being too low, not too high.** Of the
69 ✗ and 70 ~ cells, 94 want the statistic to move up and 63 down; but in Table 1 the balance is
36 up against 13 down, and the "all" column alone is short by 20% on every location statistic
while its standard deviation is within 7%. A portfolio whose mean is 20% low and whose dispersion
is right is the signature of a population difference, not of a weighting or a parameter.

## 44. What the corrected Figure 2 reading says about the 1974 window (2026-10-26)

Section 42 replaced the Figure 2 fixture with a signed per-month reading. The month-by-month
comparison behind section 39 is rebuilt on it here, and it is both weaker and more specific than
the draft of this section that preceded the correction - the earlier draft still used the
`up - down` columns, which mixed a neighbouring bar into a month, and two of its month claims do
not survive.

The fixture's own limits first, because they bound what can be claimed. The raster carries 1.19
columns per month and draws each bar about three columns wide, so a bar is placed to within a
month either side, and several months share an identical reading (+13.30% for 1974-12, 1975-01 and
1975-02; -4.79% for five months). Individual months are therefore not directly comparable; the
check uses the annual sums (correlation 0.75) and the two extremes.

| | ours | paper, digitised |
|---|---|---|
| tallest month | 1987-10, 10.23% | 1974-12, 13.30% |
| deepest month | 1974-04, -8.02% | 1974-03, -7.98% |

So the *downside* is right - the deepest months agree to 0.04 percentage points - and the whole
of the extreme gap is the upside, in a window the check already names (1974-11 to 1975-01 for the
tallest bar). Taking the three months the raster cannot separate, the positive residuals are
+10.16 (1974-12), +8.81 (1975-01) and +11.55 (1975-02) percentage points, by far the largest in
the sample; the next largest is +5.75 in 1963-07.

One sign flip survives the correction and one does not. 1974-03 is genuinely opposite: the paper's
bar is -7.98% where we earn +2.14%, the largest negative residual in the whole comparison. The
1974-02 sign flip claimed in the draft was an artefact of the old columns - read signed, the paper
is +7.14% against our +2.42%, the same sign and a 4.72 point gap. And 1987-10 runs the other way
round, +10.23% for us against +0.84% for the paper.

What that leaves is narrower than "one month". A level, a weight or a threshold cannot flip 1974-03
from +2.14% to -7.98%; a portfolio whose largest month is ours in 1987 and the paper's in 1974-12
is holding different pairs at different times. That is the same conclusion Table 4's beta
diagnostic reaches independently (our "all" market beta is +0.059 against the paper's -0.145).

The era split of the same comparison is consistent with the vintage reading of section 41 but
milder than it claims: mean absolute residual 1.52pp over the 234 months before 1983 against
1.26pp over the 240 after, with correlations of 0.493 and 0.309. 1974 is worse than an average
pre-1983 month rather than representative of one, and "fix the frozen names and 1974 comes back"
remains unestablished.

## 45. Two more conventions measured, both rejected (2026-10-26)

Five conventions had already been settled by score (SCORE_LOG rows 7 to 13). Two that the paper is
genuinely silent about had never been measured, because each needs a full 474-cohort rebuild. Both
were run end to end on separate cache roots; Tables 1-3 scored from their own `table3.csv` and
`table1.csv` with the same marks as the check.

| convention | flag | Tables 1-3 |
|---|---|---|
| current | - | **187.0** of 291 |
| trading prices rebased to 1 on the first trading day | `--normalization rebased` | 143.5 |
| two securities of one issuer may pair | `--same-issuer allow` | 182.5 |

The rebasing result is the strongest single refutation in the file. Rebasing looks harmless - it
changes no return, only the scale the spread is measured on - but the 2-sigma trigger is a level
(`sigma` is estimated during formation, in formation units), so rebasing every pair quietly changes
the threshold every pair must cross: pair entry timing moves for the whole sample and 43.5 points
go. The *trading* rebasing day is therefore not free to choose: the paper's own Figure 1 anchor
(day-0 levels 1.10) and the trigger both require the continued normalization. (`PAIR_FORMATION.md`'s
"review point A" is a different question, the *formation* index's first day; section 47 measures
it.)

A third variant was screened before rebuilding: a variance-normalised pair distance (`D_ij` on
`P_i/sd_i`), which the phrase "the two normalized price series" might permit and which would have
raised the industrial share of the tightest pairs towards the paper's 15%. It is refuted without a
rebuild, on five cohorts spanning 1974 to 2000: the top-5 pairs' mean formation sigma goes from
0.0209 to 0.2145, ten times the paper's 0.0238 (Table 2 Panel A's trigger row is 2 sigma). Full
normalisation is not available; what the top five pairs need is a different population, not a
different scale. The halfway point was then measured rather than interpolated: dividing by
`sqrt(sd)` instead of `sd` takes the top-5 sigma to 0.0427, still 1.8x the paper's, while moving
the industrial share only from 0.14 to 0.26. Fitting the three points (0, 0.5, 1) puts the
paper's 0.0238 at an exponent of about 0.09, where the sector mix has moved by roughly a fifth of
the distance it has to travel. The constraint is not closable by tuning the exponent.

## 46. The top five pairs are a degenerate population, and it is not a screen (2026-10-26)

Section 45 left one question open: the paper's top-5 portfolio is 72% utilities, 15% industrials
and 20% mixed-sector, and ours is 77%, 7.5% and 10.5%. Since a price-unit distance makes the
tightest pairs out of the least volatile stocks, the sector mix is an order statistic of the
universe, and the natural suspects were the universe screens. All of them are now measured, on
thirty-nine January cohorts (1964-2002):

| build | utilities | industrials | financials | mixed-sector | top-5 sigma |
|---|---|---|---|---|---|
| current (stale limit 0.95) | 0.826 | 0.056 | 0.118 | 0.118 | 0.021 |
| stale limit 0.85 | 0.864 | 0.041 | 0.095 | 0.092 | 0.021 |
| stale limit 0.70 | 0.885 | 0.049 | 0.067 | 0.072 | 0.021 |
| **paper** | **0.72** | **0.15** | **0.11** | **0.20** | **0.0238** |

Tightening the stale screen makes the concentration **worse**, not better: it removes financials
and industrials before it removes utilities, because a near-frozen price is the flattest possible
formation series and utilities are the second flattest. The sigma is flat at 0.021 across all
three settings, so the screen is not what the top five are made of.

The era split shows the same thing from the other side. Counting one January cohort per year:

| era | utilities | industrials | financials | mixed-sector |
|---|---|---|---|---|
| 1964-1975 | 0.800 | 0.108 | 0.092 | 0.217 |
| 1976-1985 | 0.800 | 0.070 | 0.130 | 0.160 |
| 1986-1995 | 0.980 | 0.000 | 0.020 | 0.040 |
| 1996-2002 | 0.686 | 0.029 | 0.286 | 0.000 |

Between 1986 and 1995 the five tightest pairs in a 2,000-pair universe are 98% utilities: five
pairs drawn from 6% of the stocks, with only 4% of them spanning two sectors. The paper's
full-sample mix is outside our best era as well as our average - our best decade reaches 0.108
industrials against its 0.15, and its 0.20 mixed-sector is below only our 1964-1975 reading. So
the difference is not a weighting of eras we could reweight, and not a screen: under a
price-unit sum of squared deviations, low-volatility near neighbours win the top ranks in every
period, and the paper's top five are more diverse than that at every point of its sample.

That is where Tables 2 Panel B's four weakest cells (industrial, transportation and mixed-sector
weights in top5 and top20) and Table 2 Panel A's three top-5 dispersion rows come from, and it is
the reason the near-miss cells of section 43 cannot be collected: they are not near misses of a
parameter, they are the observable signature of a pair-selection rule whose top ranks we do not
reproduce. What the paper's rule is remains open - the candidates that scale the distance have
been measured and rejected here and in section 45, and the universe screens in sections 18, 41 and 43.

## 47. Three more readings of the trading rule measured, none shipped (2026-10-26)

A review list (`TO_FIX`, kept outside the repository) named two readings no rebuild had tested, and
a cohort-cache count suggested a third. All three were run as full 474-cohort rebuilds on separate
cache roots, each changing one thing against the shipped engine (`87f645e`), and scored with the
check's own marks.

| reading | change | Tables 1-3 | total | Figure 1 |
|---|---|---|---|---|
| shipped | - | **187.0** of 291 | **213.5** of 323 | reproduced |
| formation index starts at the previous close | `P_0 = 1 + r_0`: the first formation day's return enters the index | 183.5 | 211.5 | **not reproduced** |
| no wait-1 persistence clause | a wait-1 signal opens on the following day even if the prices crossed back in between | 187.0 | 213.5 | reproduced |
| fresh divergence | a pair opens only after its spread has been inside the 2-sigma band, so a pair already apart at the end of formation waits for a new divergence | 179.0 | 206.5 | reproduced |

**The formation index's first day** (`PAIR_FORMATION.md`, review point A). `normalized_prices` sets the
index to 1 at the close of the first formation day, so that day's return never enters the distance.
Starting at the previous close is the more literal reading of "a cumulative total returns index ...
over the formation period", and it shifts every stock by its own `1 + r_0`, so it reorders pairs
rather than rescaling them. It loses 3.5 points (Table 1 +1.0, Table 2 B +0.5, Table 3 -5.0), and the
Figure 1 pair moves from rank 4 to rank 3 with its third trade opening on day 80 against the chart's
74 (shipped: 76), outside the three-day tolerance. The figure is the only place the paper shows a
pair's own path, so the shipped convention has independent support, not just the score.

**The wait-1 persistence clause** (`models.py`, "skipping signals whose prices cross on that intervening
day"). Neither edition states it; the 1999 draft says only "initiate positions in each pair on the day
following the divergence". Removing it moves values by a basis point or less (Table 1 Panel B top 20
mean 0.88% -> 0.87%; Table 2 Panel A top 5 round trips 2.24 -> 2.26) and changes no mark. With
neither text nor score behind it, the clause is now disclosed in the check header rather than
changed, since the change would move every Panel B value for no measured reason. Earlier review
comments quoted 180.0 and 182.5 for this variant; those came from a local experimental tree with
payoff-count returns that was never shipped, not from this engine.

**Fresh divergence.** On the shipped cache, 15% of the pairs that ever open do so on the first
possible day (14.9% top 5, 15.0% top 20, 16.5% "all"): under the continued normalization a pair can
end formation already more than two sigma apart, and the engine opens it at once. In the "all"
portfolio those immediate trades earn 0.10% on average against 1.49% for the rest. The paper's
"positions are opened at the end of the day that prices diverge" can be read as an event rather
than a state, so the variant arms a pair only once its spread has been inside the band. It does
what the count suggests for Table 1 - the one-day-wait "all" mean rises from 0.60% to 0.68%
against the paper's 0.71% and its t-statistic from 6.95 to 7.86 against 7.92, Table 1 +2.0 - but
Table 3 loses 10.5 points, because the sector portfolios' means are already at or above the paper's
(Transportation "all" mean 0.45% -> 0.59% against 0.44%; Industrials top 20 t-statistic 8.63 ->
9.16 against 6.93). The same trade appears in section 33 and in the short-weight choice
(SCORE_LOG row 13): any change that raises the unrestricted portfolios' returns raises the sector
portfolios' too, and ours sit on opposite sides of the paper in the two tables: below it in all
eight Table 1 fully invested means, above it in nine of the fifteen Table 3 means.

**What this leaves.** With these three, every untested reading of the trading rule that a review
has named is now measured, and the best of them ties the shipped score. The Table 1 / Table 3
opposition above is the clearest statement yet of why the remaining points are not a convention:
the paper's unrestricted portfolios earn more than ours while most of its within-sector portfolios
earn less, and a single rule applied to both moves them together.


## 48. The quote-only Nasdaq names, measured from the data up (2026-10-26)

This section takes Q2 from the raw CRSP fields rather than from the score. Every number is from the
shipped cache or a full 474-cohort rebuild against `87f645e`.

**What the data are.** Before 1983, CRSP has no Nasdaq volume and no trade prices: in 1975 every
Nasdaq row has missing volume and a bid/ask-average price, and 62.5% of Nasdaq daily returns are
exactly zero (NYSE 21%). The zero-volume screen cannot see these stocks, so in the cohort trading
from January 1975 they are 2,132 of the 2,989 eligible stocks (71%), with a median share of
unchanged-quote days of 0.71. The stalest fifth (0.8-0.95) has a median market cap of $2.2m. In that
cohort's top 20 (cohort 1974-11), half the pairs have a quote-only leg, most of them banks, quoted
unchanged on 55-94% of formation days (Buning Florist 0.94, Commonwealth National 0.90, Bank of Delaware 0.89), and they
earn 0-10% in January 1975 while the NYSE utility pairs beside them move 14-41%.

**January 1975, position by position.** 11,296 open positions across the six cohorts: long legs
gain 21% and short legs 12% on average, and the tightest pairs earn least (ranks 1-20 2.6%, ranks
past 1,000 9.2%). The "all" portfolio's 10.3% is the value-weighted reading; equal weight gives
9.1% and payoff per pair 7.8%. The paper's "all" maximum (17.18% / 16.32%) has to fall before 1989:
its post-1988 standard deviation of 1.295% over 168 months leaves no room for a 16% month after
1988, so January 1975 is the likely month. No cached capital reading reaches it: payoff counts get
the "all" mean (0.740% against 0.715%, one-day wait) and the kurtosis (23.8 against 25.7) but put
the maximum in March 2000 (+13.0%) with skewness near zero.

**Removing them (`--max-stale-share 0.5`).** Tables 1-3 fall to 157.0 of 291 (-30.0): Financials
drop to 263 stocks per cohort (paper 371), the size-decile rows move off the paper's (all-pairs
average decile 4.63 -> 4.19, paper 4.57), and the top-5 and top-20 means overshoot (Table 1 Panel A
top 20 1.38% -> 1.59%, paper 1.44%). The unscored Figure 2 moves the other way: the correlation of
annual sums with the digitised bars rises from 0.75 to 0.89 (before 1983 0.60 -> 0.83, after 1983
unchanged), January 1975 for the top 20 rises from 4.5% to 8.5% (paper 13.3%), and 1975 as a year
from 9.8% to 35.0% (paper 46.3%), with 1976, 1980 and 1981 overshooting.

**The trigger is not this.** Removing the quote-only names leaves the top-5 trigger at 0.0416
(shipped 0.0409, paper 0.0476). Two other readings were screened on every 24th or 12th cohort and
are rejected: a price-only (`dlyretx`) formation index (0.0421 against 0.0423 on the same sample),
and the spread actually observed at the wait-1 opening (0.0454 / 0.0529 / 0.0834 / 0.1969 against
the paper's 0.0476 / 0.0528 / 0.0756 / 0.1689), which fits the top 5 and top 20 but not the other
two columns and contradicts the table note's "two standard deviations". Idle cohort-months (no pair
open) are under 1% of every portfolio except where a 101-120 band does not exist, so how they enter
the overlap average is not a lever either.

**What this leaves.** The paper's top ranks in 1973-82 behave like a portfolio without these names
(Figure 2), while its stock counts and size deciles say they were in its universe. Both hold only if
its CRSP edition quoted these stocks less statically than today's file does, which is the edition
question Q2 already ends on, now with the paper's own figure as evidence. No rule we can state from
the paper separates the two readings, so nothing is shipped.

## 49. Every table and figure with a printed number joins the score: 213.5 of 323 -> 266.5 of 481 (2026-10-27)

**What is scored now.** Table 4 (the Sharpe ratio, the Fama-French + momentum + reversal
regression, the Ibbotson-factor regression and the equity-premium column: 60 cells), Table 5 Panel A (20), Table 8 (the subperiod
moments and a five-factor regression in each half: 72) and Figure 4 (the six correlations its text
prints, raw and on five-factor residuals: 6). Rows that repeat a scored row are not counted twice,
and neither are t-statistics or Table 8's factor standard deviations. Every new paper value is
read back out of the PDF by `scripts/verify_paper_targets.py` (Table 4 60 values, Table 8 72,
Figure 4 6), and `scripts/paper_cells.json` carries the new cells for the scorer.

| block | cells | ✓ / ~ / ✗ | points |
|---|---|---|---|
| Table 4 | 60 | 19 / 8 / 33 | 23.0 |
| Table 5 Panel A | 20 | 7 / 5 / 8 | 9.5 |
| Table 8 | 72 | 12 / 15 / 45 | 19.5 |
| Figure 4 | 6 | 0 / 2 / 4 | 1.0 |
| all new cells | 158 | 38 / 30 / 90 | 53.0 |

The total rises 213.5 -> 266.5 and the rate falls 66.1% -> 55.4%. The new blocks split cleanly:
what describes the series itself matches (the four Sharpe ratios within 10%, the equity premium's
mean, standard deviation and Sharpe ratio within 10%, Table 8's top-20 moments in both halves),
while the regressions do not (4.0 of 28 points in Table 4's, 9.5 of 56 in Table 8's). The factors
are French's and reproduce the paper's printed factor volatilities for the market, SMB, HML and
momentum to within 0.5% before 1989, so the data are right; the reversal factor is not (0.026
against the paper's 0.072 before 1989, section 32), and a regression shares its misfit across
every coefficient. Our "all" market loading is +0.053 against -0.145, which is Q1's population
difference, not the factors. Tables 1-3 and 7 are byte-identical to SCORE_LOG row 14's check.

**Review findings on #44.** F1: Figure 2 stays compared on the no-wait series, now on evidence
that uses only the paper - the digitised bars match Table 1 Panel A's top-20 row on five of six
statistics and Panel B's on one (mean 1.31% against 1.44% and 0.90%) - and the check prints that
test and the one-day-wait comparison beside it. F2: `tests/test_cell_margins.py` skips with a
message when the built tables are absent, so `make test` passes on a fresh clone (210 passed, 7
skipped). F3: the 19 ruff findings the branch added are fixed; the touched files carry only the
findings `main` already had.

**Landing.** #44, #45 and #46 had merged into the branches they were stacked on, not into `main`;
this change brings all three to `main` with it.

**The Ibbotson block.** The paper's second model regresses on Ibbotson's market, small-stock,
bond default and bond horizon premia ("the monthly geometric difference" of the underlying total
returns, from the Ibbotson EnCorr analyzer). CRSP has the S&P 500, the 30-day bill and government
bond indices but no corporate bond returns. Ibbotson's own long-term corporate and government bond
returns are in Goyal and Welch's predictor data (`corpr`, `ltr`; the 2005 edition, already in
`data/raw/goyal_welch`), so the default and horizon premia use Ibbotson's series directly. The
small-company series is rebuilt by Ibbotson's recipe (NYSE common stocks in the bottom fifth by
capitalization, re-formed every five years, through 1981; the DFA Small Company fund from 1982),
which matches the published 1961-81 annual returns at a correlation of 0.999. The block scores 12.0
of 24 (✓ 10, ~ 4, ✗ 10): three of four intercepts are within 10% (0.688% / 0.866% / 0.719%
against 0.716% / 0.857% / 0.766%), and so are the top-5 default and horizon loadings and both
R2 values of the broad portfolios. Reading the `.xls` needs `xlrd`, now a dependency.

**The reversal factor by Carhart's recipe.** The paper builds its reversal factor "similar to
Carhart's (1997) momentum factor, but the performance-sorting horizon here is one month" (footnote
7). Carhart's footnote 3 gives that recipe: "the equal-weight average of firms with the highest 30
percent ... minus the equal-weight average of firms with the lowest 30 percent ... The portfolios
include all NYSE, Amex, and Nasdaq stocks and are re-formed monthly" (his main text calls the
factors value-weighted; the footnote is the construction). Built that way on CRSP monthly returns
with a one-month sort, the factor's standard deviation is 0.030 before 1989 and 0.058 after,
against the paper's printed 0.072 and 0.044 (common shares only: 0.030 / 0.061; price at least $1:
0.029 / 0.048). The paper's factor is more volatile in the first half and calmer in the second,
and no construction tried reproduces that ordering. Swapped in for French's ST_Rev, it scores the
same on Table 4's five-factor block (4.0 of 28) and lower on Table 8's regressions (8.5 against
9.5 of 56), so French's factor stays. Building it on the pairs universe itself (each cohort's 2,293 stocks
on average, against the paper's 2,317) does not help either: 0.031 / 0.072 equal weighted, 0.033 /
0.054 value weighted, 0.032 / 0.036 on NYSE and Amex only. The universe moves the post-1988 figure
across a range that brackets the paper's 0.044, but every reasonable universe and weighting gives
0.030-0.033 before 1989, so the paper's 0.072 there is not a sample choice. Closing the 1% stock-count
gap cannot change that either. Perturbing each cohort's universe gives pre-1989 standard deviations of
0.0310 for a random 1% dropped, 0.0311 for a random 1% of other CRSP stocks added, and 0.0317 for the
1% of other stocks with the most extreme prior-month returns added. Even 25% of those extreme stocks
added gives only 0.0354. A bound gives the same answer: 1% is about 23 stocks against legs of about
685 each, so the added names carry about 3% of a leg's weight. To lift 0.031 to 0.072, they would have to
add an independent component with a standard deviation of 0.065, which means a leg spread among them of
about 200% a month. The recipe matters more than the universe: decile 1 minus decile 10 gives 0.047 /
0.110. The text confirms the sign used: "The exposures to momentum
and reversals have the predicted signs" (p. 816), i.e. positive on losers minus winners.

**Momentum and reversal compared, and what the paper's reversal factor looks like.** The text
treats the two factors in parallel. Momentum is "constructed along the lines of Carhart (1997)"
(p. 814; the Table 4 note says "Carhart's Momentum factor"). Reversal is the top three deciles of
prior-month return minus the bottom three, and its construction "is similar to Carhart's (1997)
momentum factor, but the performance-sorting horizon here is one month" (footnote 7). The Table 8
factor SDs show where the factors came from. French's library matches four of the five in both
windows: market 0.0459 / 0.0445 against 0.0458 / 0.0439, SMB 0.0292 / 0.0388 against 0.0292 /
0.0386, HML 0.0260 / 0.0336 against 0.0260 / 0.0364, and UMD 0.0350 / 0.0494 against 0.0351 / 0.0493.
The paper's momentum is therefore French's UMD, not a series built on the pairs universe. That build
gives 0.042 / 0.079, and adding or removing 150 stocks keeps it between 0.041 and 0.044 before 1989.
Carhart's own recipe on CRSP gives 0.039 / 0.067. The same reading applied to reversal is French's
ST_Rev, the factor shipped here. It matches after 1988 (0.0403 against 0.0445) and misses before
(0.0259 against 0.0723).

The pre-1989 panel has a fingerprint. In every column the market and SMB loadings are almost exactly
the negative of the reversal loading: -0.434 / -0.442 / +0.436, -0.312 / -0.332 / +0.333, -0.289 /
-0.275 / +0.288 and -0.434 / -0.402 / +0.452. A long-short factor does not produce that offset.
A reversal series that carries market and small-stock exposure, such as a long-only portfolio of
losers, does. The equal-weighted bottom three prior-month deciles minus the T-bill, with no short
leg, have an SD of 0.0685 (French deciles) or 0.0728 (built, bottom 30% of CRSP) against the
paper's 0.0723. In the "all" regression this series gives -0.29 / -0.30 / +0.34 and R2 0.63,
against the paper's -0.43 / -0.40 / +0.45 and 0.70, while ST_Rev gives +0.04 / +0.09 / +0.17. After
1988 the same series has an SD of 0.069-0.086 against 0.0445, so it does not describe the second
panel. Scored on the 84 regression cells of Tables 4 and 8, the losers-only series reaches 20.0,
against 13.5 for ST_Rev. A splice of losers-only through 1988 and ST_Rev after reaches 15.5. This is
consistent with the paper's pre-1989 reversal factor lacking its short leg, but that is a hypothesis
about an error in the paper. The pre-1989 SD is its only non-fitted support, so the hypothesis is
recorded here and not shipped.

**The paper's reversal factor, identified from its own Table 8.** In-sample OLS satisfies R2 x
sd(y)^2 = b' Sigma b exactly. Table 8 prints, for each panel, every b, R2 and sd(y) for four portfolios,
and French's Mkt, SMB, HML and UMD match the paper's Factor SD column, which fixes their 4 x 4 block
of Sigma. The four covariances of the reversal factor with those factors are then the solution of
four linear equations. The method is exact: on our own unrounded regressions it returns ST_Rev's
actual correlations to three decimals. The page image (PDF p. 822) confirms the transcribed values.
With the paper's R2 rounded to two decimals, Table 8 implies these correlations with market / SMB /
HML / UMD:
- before 1989: +0.81 / +0.79 / -0.18 / -0.16 (90% band over the R2 rounding: +0.77..+0.86 /
  +0.72..+0.86 / -0.20..-0.15 / -0.17..-0.14);
- after 1988: +0.79 / +0.55 / -0.53 / -0.30, with wider bands because three of the four R2 are
  0.02-0.19.

French's ST_Rev correlates +0.28 / +0.26 / -0.04 / -0.40 and +0.24 / +0.05 / -0.11 / -0.30. No
long-short reversal series tried comes near +0.8 with the market. The equal-weighted bottom three
prior-month deciles minus the T-bill, with no short leg, do:
- built from CRSP before 1989: SD 0.0728 and +0.82 / +0.77 / -0.18 / -0.14;
- French's EW deciles before 1989: SD 0.0685 and +0.84 / +0.77 / -0.20 / -0.12;
- after 1988: +0.72 / +0.52 / -0.44 / -0.35, inside the bands, but SD 0.069 against 0.0445.

A regressor's scale moves only its own loading, so the SD gap affects the reversal row, not the
market or SMB rows. With this series our pre-1989 loadings take the paper's shape: market ≈ SMB ≈
-reversal in every column. For example, 101-120 gives -0.25 / -0.23 / +0.25 against the paper's
-0.29 / -0.28 / +0.29, where ST_Rev gives -0.02 / +0.05 / +0.11. After 1988, "all" gives -0.07 /
-0.10 / +0.16 against -0.07 / -0.06 / +0.19. The rest of the gap sits with our pairs portfolios, which
load less on the factor before 1989 (top 5: +0.18 against +0.44). Rebuilding Table 4 from Table 8's two
panels is not conclusive: the R2 rounding leaves bands that the printed values sit at the edge of. Scored
cells: 20.5 against 14.0 of the 87 that use the factor (266.5 -> 273.0 overall), not shipped pending a
decision, because the text describes a long-short factor.

**Not a pre-1983 data problem.** The pre-1989 panel splits into three eras: before Nasdaq enters
CRSP (1963-07 to 1972-11), quote-only Nasdaq (1972-12 to 1982-12) and the Nasdaq National Market
(1983-01 to 1988-12). Built EW losers-minus-winners has an SD of 0.024 / 0.037 / 0.024 and a market
correlation of +0.23 / +0.33 / +0.31 in those eras. NYSE and Amex alone give 0.024 / 0.041 / 0.023,
and Nasdaq alone gives 0.035 / 0.026 in the two eras where it exists. ST_Rev gives 0.020 / 0.032 /
0.022. The first era has no Nasdaq data at all and is already a third of the paper's 0.072. For a
long-short factor to average 0.072 over the panel, the later eras would need an SD near 0.09, over
twice what Nasdaq alone produces. Bad prints are also idiosyncratic and diversify across about 700
stocks per leg, so they cannot create a +0.8 market correlation. Stale zero returns rise only from
3.4% to 8.2% of stocks. The losers-only series instead has a market correlation of +0.83 / +0.83 /
+0.84 in all three eras, the first included. The paper took Mkt-RF, SMB, HML and UMD from French and
built only the reversal factor itself, which is the one factor that does not match.

**Built from the daily file, the paper's own data.** The paper's data are "the CRSP daily files", and
its monthly returns are daily returns "compounded to obtain monthly returns" (p. 803). Its reversal
factor's data source is not stated, so the factor was rebuilt from `daily_stocks`: legs set by the prior
month's compounded daily return, EW. Holding each leg for the month reproduces the monthly-file
build (0.0301 / 0.0615, which checks the two files against each other). Rebalancing daily and
compounding each leg gives 0.0309 / 0.0646, and compounding the daily difference gives 0.0294 /
0.0613. The market correlation stays at +0.27 to +0.30 in every version. Losers rebalanced daily minus
the bill give 0.0730 and +0.82 before 1989, against the paper's 0.0723 and an implied +0.81. Daily
data therefore changes neither the long-short result nor the losers-only match.

**French's file history (Wayback Machine).** ST_Rev first appears on French's data library page as
"New! Short-Term Reversal Factor (ST Rev)" between the 2006-06-12 snapshot (absent) and the
2006-08-27 snapshot (present). Its earliest archived file is dated 2006-10-30 and was built on the
200609 CRSP database. UMD is already on the October 2003 page. The paper could therefore download
momentum but had to build reversal itself, as it says ("we control for this possibility by
constructing a short-term reversal factor"). French's construction has not changed since 2006: the
average of the small and big low-prior-return portfolios minus the average of the two high ones,
from a 2 x 3 sort with NYSE median and 30th/70th percentile breakpoints, value weighted. Nine
archived vintages and the repo copy all give a pre-1989 SD of 0.0258-0.0259 and a post-1988 SD of
0.0400-0.0403: 200609, 200612, 201005, 201209, 201406, 201705, 202005, 202212, 202509 and 202608.
Each correlates 0.9993 or more with the 2006 file. UMD from the 200509 database (archived 2005-10-29)
gives 0.0350 / 0.0494, the same as today's file, against the paper's 0.0351 / 0.0493. Vintage revisions
therefore explain none of the reversal gap. French's ST_Rev is a stand-in that did not exist when the
paper was written, not the paper's factor.

**French's 2 x 3 recipe rebuilt from our CRSP file.** The rebuild uses common shares (EQTY / COM / NS,
US-incorporated, issuer ACOR or CORP, the CIZ equivalent of share codes 10 and 11) on NYSE, Amex and
Nasdaq. Size is the end of the prior month's cap split at the NYSE median, and prior return is split at
NYSE 30th / 70th percentiles. The six portfolios are value weighted, and each factor is half small
plus half big. Against French's published series:
- ST_Rev: SD 0.0258 / 0.0401 against 0.0259 / 0.0403, mean 0.80% against 0.81% before 1989,
  correlation 0.9997 / 0.9995, tracking SD 0.07 / 0.13 percentage points;
- UMD: 0.0349 / 0.0493 against 0.0350 / 0.0494, correlation 0.9993 / 0.9997;
- all twelve component portfolios correlate 0.9994-1.0000 with French's.

Our data and French's method therefore reproduce French. The paper's momentum SD (0.0351 / 0.0493)
is that same series. Its pre-1989 reversal SD (0.0723) is not produced by this recipe on this data,
by French's own file, or by any of its archived vintages.

**A bug in the factor, not a typo in the SD.** If the printed 0.0723 were a misprint for a normal
reversal SD, Table 8's regressions would still have to be consistent with that smaller SD. Solving the
four R2 equations for a range of assumed SDs and checking the implied 5 x 5 covariance matrix says
otherwise. Before 1989, every assumed SD from 0.026 to 0.055, and 0.090, needs correlations above 1
(for example +1.41 with the market at 0.0259) or a matrix that is not positive semidefinite. That holds in
all 2,000 draws over the R2 rounding. Only 0.0723 gives a valid matrix, and it does so in every draw. The
printed SD therefore agrees with the regressions: the factor in the pre-1989 regressions really had an
SD of about 0.072 and a market correlation of about +0.8, so the error is in how it was built. After
1988 the valid range is about 0.040-0.055, and the printed 0.0445 lies inside it. The implied market
correlation there is still +0.7 to +0.85, against ST_Rev's +0.24. ST_Rev's post-1988 agreement is
therefore in the SD only, not in the factor. The paper's post-1988 factor also looks
market-correlated, though less volatile than the losers-only series (0.069), which falls outside the
valid range.

**The equity premium column is French's Mkt-RF.** Table 4's last column (mean 0.410%, SD 4.509%,
Sharpe 0.09, serial correlation 0.05) is scored here as S&P 500 minus the 30-day bill, which gives
0.427% / 4.386% / 0.097 / 0.0002 (3 of 4). French's Mkt-RF gives 0.425% / 4.540% / 0.094 / 0.047
(4 of 4). Starting in June 1963 or using a geometric difference does not change either result. Table 8
names its market regressor "U.S. equity risk-premium", and its SDs match Mkt-RF. The note's "S&P 500
returns are calculated in excess of Treasury bill returns" fits the Ibbotson block's market factor,
which the text defines as "the excess return on the S&P 500". Shipped in section 50 (+1.0).

**What is still not scored.** Table 5 Panel B (needs a daily panel in the cache),
Table 6 (needs a random-pair resampling step), Table 9 (needs a top-three-decile universe and a
recall rule), and Figures 2 and 3 (their numbers are read off images, and Figure 3's fully
invested curve contradicts the paper's own Table 1).

## 50. Table 4's equity premium is Mkt-RF, and the alphas' t-statistics (2026-10-27): 266.5 -> 267.5

**The change.** Table 4's last column is now French's Mkt-RF over the portfolio months, not the S&P
500 less the 30-day bill (section 49, "The equity premium column is French's Mkt-RF"). The evidence,
strongest first:
1. *Structure.* Table 8 labels the market regressor of the same five-factor model the "U.S. equity
   risk-premium", so Table 4's equity-premium column and that regressor are one series. Its Table 8
   SDs are Mkt-RF's.
2. *The SD bracket.* Table 8 prints that series' SD in each half, 0.04580 (306 months) and 0.04390
   (168). A full-sample variance is the months-weighted average of the halves' variances plus a
   non-negative term for the gap between their means, so the series' full-sample SD is at least
   about 4.51% (the paper's own 4.509% sits on that floor). The S&P series' 4.386% lies below both
   halves and cannot be that series; Mkt-RF's 4.540% clears the floor and is 0.7% from 4.509%. The
   two halves are verified against the PDF with the other paper values.
3. *Serial correlation.* Mkt-RF gives 0.047 against the printed 0.05; the S&P series gives 0.0002.
   With 474 months the standard error of a lag-1 autocorrelation is about 1/sqrt(474) = 0.046, so
   the two candidates are about one standard error apart. This leg only agrees with the other two
   and does not separate the series on its own. The mean (0.425% against 0.427%) and the Sharpe ratio
   (0.094 against 0.097) separate them even less.

The score moves 266.5 -> 267.5 through that one serial-correlation cell (✗ -> ✓), a statistic whose
standard error exceeds the gap between the candidates. The +1.0 follows from identifying the series
by 1 and 2; it is not independent evidence for that identification. Every other cell is
byte-identical on a full 474-cohort rebuild. The Ibbotson block's market factor keeps the S&P,
because the note's S&P sentence describes it.

**Is pairs trading explained by the five factors?** The paper's claim is "only a small portion of
the excess returns of pairs trading can be attributed to their exposures to the five risk factors".
The check now prints the intercepts' Newey-West t-statistics (six lags, Bartlett weights, no
small-sample correction, `factors.factor_tstats`) beside the paper's, unscored:

| window | top 5 | top 20 | 101-120 | all |
|---|---|---|---|---|
| full sample, ours vs paper | 5.93 vs 3.81 | 8.61 vs 7.08 | 10.78 vs 8.66 | 9.77 vs 5.30 |
| before 1989 | 5.58 vs 1.72 | 7.85 vs 4.41 | 8.37 vs 6.54 | 10.14 vs 4.19 |
| after 1988 | 1.35 vs 2.12 | 4.41 vs 3.77 | 7.88 vs 3.01 | 2.97 vs -0.56 |

Our alphas are significant wherever the paper's are, and more so. They are close to the raw means:
the full-sample "all" alpha is 0.64% against a 0.60% mean. The paper's alphas are 10-20 bp below its
raw means, and our portfolios carry little market or SMB exposure. The factors explain about 60% of
the "all" portfolio's variance, mostly through momentum and reversal, and almost none of its mean.
The two disagreements are the post-1988 top 5 (insignificant here) and the post-1988 "all", which is
negative and insignificant in the paper and +2.97 here; our post-1988 "all" mean is lower too (0.12%
against 0.21%). Swapping in the losers-only reversal series of section 49 leaves every alpha
significant (full sample t 6.4 / 8.5 / 10.9 / 9.1), so the conclusion does not depend on the
reversal factor. The paper's t-statistics are verified against the PDF by
`scripts/verify_paper_targets.py` (12 values), as every scored value is.

## 51. The paper's reversal factor: audited, disclosed, and reported as an unscored alternative (2026-10-27)

Section 49 holds the measurements. This section records what ships, and
`scripts/audit_reversal_factor.py` regenerates the numbers the decision rests on
(`REVERSAL_FACTOR_AUDIT.md`).

**What is settled.**
- Market, SMB, HML and momentum are French's series. Their Table 8 SDs match his files to three
  or four decimals, and the 2005 UMD file gives the same 0.0350 / 0.0494 as today's.
- French's 2 x 3 recipe, rebuilt from our CRSP monthly file, reproduces his ST_Rev and UMD
  (correlation 0.9993-0.9997, SDs within 0.0002), so neither our data nor the recipe is the gap.
- ST_Rev is a stand-in. French added it in mid-2006, after the paper was written; the paper
  says it built its own ("we control for this possibility by constructing a short-term reversal
  factor"). Nine archived vintages of ST_Rev agree to a correlation of 0.9993 or better.

**What Table 8 says about the paper's factor.** Solving each panel's R2 equations for the reversal
factor's covariances with the four known factors gives the following.
- Before 1989, a valid covariance matrix appears only at an SD near the printed 0.0723. Every SD
  from 0.026 to 0.055 needs a correlation above 1. The printed SD is not a misprint.
- At 0.0723 the implied correlations with market / SMB / HML / momentum are +0.81 / +0.79 /
  -0.18 / -0.16. No long-short reversal series built here exceeds +0.4 with the market, in any
  era, from monthly or daily data.
- The equal-weighted bottom three prior-month deciles less the bill, a long-only losers
  portfolio, has an SD of 0.0685 (0.0728 rebuilt from CRSP) and correlations of +0.84 / +0.77 /
  -0.20 / -0.12. That holds in each era, including 1963-72, before Nasdaq is in CRSP.
- After 1988 the printed 0.0445 is valid, but the implied market correlation is still +0.7 to
  +0.85, against ST_Rev's +0.24 and the losers series' SD of 0.069. The second panel's factor is
  therefore neither, and ST_Rev's post-1988 SD match is in the SD only.

**What ships.**
- The scored regressions keep ST_Rev, the correct construction of the factor the paper describes.
  The losers series reproduces what the paper printed, not what it describes, and its only support
  that was not fitted to scored cells is the pre-1989 fingerprint.
- The check header now says the paper's factor is not a long-short factor.
- The check ends with an unscored section that repeats the 84 regression cells of Tables 4 and 8
  with the losers series and prints what they would score against ST_Rev. Its rows carry no " / ",
  so `score_wrapper` skips them, and the score is unchanged.
- The alphas stay significant under both factors (section 50), so the paper's conclusion does not
  depend on the choice.

## 52. Tables 4 and 8 under French's ST_Rev: the conclusion replicates, the cells do not (2026-10-28)

**The conclusion.** With French's ST_Rev as the reversal factor, the paper's claim about Tables 4
and 8 holds in both subperiods: pairs returns load little on the five factors and keep a large,
significant alpha, which shrinks after 1988 but does not vanish (section 50 has the Newey-West
t-statistics). Monthly alphas, ours vs the paper's, from the check's intercept rows:

| window | top 5 | top 20 | 101-120 | all |
|---|---|---|---|---|
| before 1989 | 0.92% vs 0.35% | 1.11% vs 0.67% | 0.91% vs 0.71% | 0.81% vs 0.45% |
| after 1988 | 0.18% vs 0.34% | 0.36% vs 0.42% | 0.57% vs 0.36% | 0.27% vs -0.07% |

Both versions fall after 1988, and the t-statistic falls further because the window is shorter
(168 months against 306 scales t by about sqrt(168/306) = 0.74 at equal alpha and volatility).
The full-sample reversal loadings are 0.04-0.15 (paper 0.07-0.20), and the factors explain almost
none of the top 5 and top 20 (R2 0.01 and 0.03), so pairs trading is not a disguised short-term
reversal strategy, as the paper argues (§3.6).

**The cells.** Table 8 scores 19.5 of its 72 cells, almost evenly by panel
(`REPLICATION_CHECK.md`, Table 8 block):

| Table 8 | means and SDs (8) | loadings (20) | intercept and R2 (8) | total ✓ / ~ / ✗ | points |
|---|---|---|---|---|---|
| Panel A, before 1989 | 4 / 4 / 0 | 2 / 0 / 18 | 1 / 1 / 6 | 7 / 5 / 24 | 9.5 |
| Panel B, after 1988 | 2 / 4 / 2 | 1 / 4 / 15 | 2 / 2 / 4 | 5 / 10 / 21 | 10.0 |

The two panels miss for different reasons.
- *Panel A: the factor.* Our pre-1989 portfolios match the paper's (no mean or SD cell is ✗), yet
  18 of 20 loadings miss: reversal is 2.6-3.9 times too small, and market and SMB are 7-30 times
  too small or of the wrong sign (paper -0.28 to -0.44 on both). With the dependent
  variable right and the loadings wrong, the gap is the regressors, i.e. the unidentified reversal
  factor of section 51.
- *Panel B, near-zero coefficients.* Most post-1988 loadings are statistically zero in the paper
  (|t| < 2 in 14 of 20) and small in ours, and a 10% / 25% relative band turns agreement on "no
  exposure" into a miss: the 101-120 market loading is 0.054 here against 0.0024 (t = 0.06).
- *Panel B, our "all" portfolio.* The "all" column is wrong before any regression: mean 0.117%
  against 0.212% and SD 1.573% against 1.295%, and its loadings have the wrong sign on market, SMB
  and HML (+0.075 / +0.039 / -0.010 against -0.070 / -0.061 / -0.082). The 101-120 mean (0.509%
  against 0.327%) is the same kind of miss.

**The post-1988 "all" portfolio, diagnosed.** Table 8 uses the fully invested ("employed") series
of `results/replication/tables/monthly_returns.parquet` (wait 1, "all"; post-1988 mean 0.117%, SD
1.573% reproduce the check). Its excess SD sits in a few months: January 2001 +8.61%, November 2002
+6.82%, October 1998 +6.81%. Dropping those three takes the SD to 1.232%, but the mean to -0.016%,
so the ordinary months also earn less than the paper's. The spikes are broad, not a few bad
prints: in January 2001, 5,032 trades close (cohorts' `w1_trades.parquet`), 297 return over 50%,
and the ten largest payoffs carry 9% of the month's total. Those 297 are not penny stocks: the
smaller leg's median market-cap percentile at formation is 0.44 (all trades 0.66), and pairs with a
leg in the bottom 5% of cap are 0.2% of trades. They are high-volatility pairs (median formation
sigma 0.143 against 0.088), dot-com-era names converging in a market-wide rebound, which the paper's
universe should hold too.

The stale-quote screen and the SIC source do not explain it. "All" uses no sector labels, and every
day rule gives the same late pair surplus (`summary.json` of each universe's cohort cache):

| pairs per cohort | 1962-82 | 1983-97 | 1998-2002 |
|---|---|---|---|
| `vol_common` (shipped) | 1,646 | 2,024 | 3,381 |
| `volpos_common` | 868 | 1,976 | 3,381 |
| `price_common` | 868 | 1,868 | 3,365 |
| `vol_ns` | 1,662 | 2,135 | 3,612 |

The day rule moves only the pre-1983 Nasdaq era. The pattern is the era split of OPEN_QUESTIONS Q8,
now seen in returns as well as counts: our "all" SD is 17% low before 1989 and 21% high after, as
our pair count is 4.4% low to 1997 and 5.1% high after (section 19.1). Closing it needs the paper's
universe by period (its CRSP vintage or stock list), not a filter tuned to the printed SD.

**A caveat on `PAPER_CONSISTENCY.md`'s Panel B joint figure.** Its post-1988 joint test (R2 of the
implied reversal factor on the four factors 0.790, 82.0% of rounding draws feasible) is weak
evidence. The per-column required correlations are +0.66 / +0.87 / +0.36 / -0.06; the demand comes
from the top 5 and top 20, whose reversal loadings (-0.063 and -0.017, t = -1.76 and -0.67) are
statistically zero, and the identity divides by the loading. The one significant loading ("all",
0.188, t = 5.56) needs -0.06, which an ordinary long-short factor meets. The same caution applies
to section 51's post-1988 implied correlations. Panel A is unaffected: its four reversal loadings are
0.29-0.45 with t = 3.6-8.0, every column needs -0.91 to -0.95, and 98.2% of rounding draws agree.

**What the write-up can say.** With French's ST_Rev, the qualitative conclusions of Tables 4 and 8
replicate: the alpha is significant in both subperiods, smaller after 1988, and the reversal
exposure is small. Cell-level agreement is poor, because Panel A's reversal factor is unidentified
(section 51) and Panel B's coefficients are mostly indistinguishable from zero, with our post-1988
"all" portfolio off by the Q8 era split.

