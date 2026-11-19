# Review notes, archive: notes 1-77 (2026-10-16 to 2026-11-17)

The record as it was written, note by note, with its numbers, dates and internal
cross-references unchanged. The text below is a straight cut of the one-file record that
stood in `REVIEW_NOTES.md` until round 9 (REVIEW_NOTES 92): nothing was edited, reordered
or renumbered in the move.

Live notes 78-88, the index to every note in this file, and the notes that continue from
there are in [`REVIEW_NOTES.md`](REVIEW_NOTES.md). The shipped score and its history are
in `SCORE_LOG.md`; what each claim stands at today is in `CLAIMS.md`; what remains between
this replication and the paper is in `GAPS.md`.

The record opens with its own title, as written.

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
  figure is not our data's. *Superseded by section 55*, which re-measures it on the current
  accounting with the `--long-delisting-loss` flag: 1.387% to 1.274%, the paper's size.

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

`--waste-sic utilities` restores the old map as a flag; section 55 re-measures it on the
current code (261.0 -> 259.0, the same Utilities 101-120 cells in reverse).

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


## 53. Three no-gain experiments, landed with their scripts (2026-10-28)

Three agent experiments were pushed as branches without a PR (`replication/exp-t2a`,
`replication/exp-subperiod-t4`, `replication/exp-nw-moments`), each adding a section to
`OPEN_QUESTIONS.md` and no code. They land here together, merged, with the scripts that
produce every number they quote (`scripts/experiments/`) and with the review's corrections.
None changes the engine, the tables or the score (267.5). Each script reads the shared
cohort cache or the aggregated `results/replication/tables/monthly_returns.parquet` and
writes nothing:

    python scripts/experiments/table2a_conventions.py    # Table 2 Panel A readings
    python scripts/experiments/table8_windows.py         # Table 8 subperiod windows
    python scripts/experiments/reversal_candidates.py    # Tables 4 and 8 reversal column
    python scripts/experiments/estimator_variants.py     # Tables 1 and 3 estimator readings

**Results** (details in the three `OPEN_QUESTIONS.md` sections of the same date):

- *Table 2 Panel A.* Counting per selected pair instead of per opened pair scores 20.0 against
  20.5 (score 267.0); the std rows cannot be pair-level dispersions (0.88-1.49 against the
  paper's 0.16-0.80); the trigger follows Table 2's note; "months open" must be a per-pair
  total. Composition explains about 1.5 of the 14% top-5 trigger gap, so Q7's formula question
  is closed and the rest is a formation-stage gap.
- *Table 8 window.* The shipped split is the caption's (306 + 168 months). Moving December 1988
  to Panel B or dropping the five partial months of 1963 would each gain half a point and
  contradict the caption; not adopted.
- *Reversal factor.* The paper's recipe (p. 813 and footnote 7) with Carhart's construction
  (1997, p. 61, footnote 3) is an equal-weighted spread of the top and bottom 30% of
  prior-month return across all NYSE/Amex/Nasdaq stocks, with no size sort, and the paper's
  next sentence fixes the sign as losers minus winners. Built from CRSP it correlates 0.82 with
  ST_Rev, has a pre-1989 standard deviation of 3.0% against the 7.23% Table 8 prints and scores
  12.5 of the 84 regression cells against ST_Rev's 13.5. No long-short candidate reaches the
  printed 7.23%, so the recipe does not identify the paper's factor either (section 51).
  ST_Rev stays the primary. **Open decision:** whether the primary should follow the recipe
  build (-1.0 point) rather than French's published series.
- *Tables 1 and 3 estimator.* The paper fixes six Newey-West lags; of the readings it leaves open,
  the df correction, the median convention and the zero-share reading flip no cell, and filling
  Table 3's empty months with zero gains half a point through one Utilities cell, which the
  paper cannot justify; not adopted.

**Corrections made in review** (the branches' text as pushed):

- Table 2 A: the shipped time-open dispersion was quoted as 0.74 / 0.51 / 0.44 / 0.31 (the
  check prints 0.71 / 0.46 / 0.37 / 0.20); the Table 2 note is on p. 809, not 808; the
  same-issuer result is section 17, not 15; the round-trip and time-open correlations with
  composition reach 0.24, not "<= 0.15"; 1963-82 was called "the paper's own mix", though the
  paper prints only a full-sample mix; agent-coordination text was removed.
- Table 8: the caption is on p. 822, not 821; the "five partial 1963 months" run dropped six
  (July-December), now five (pre_mean 0.954%, not 0.953%); the 101-120 and "all" gaps are
  negative.
- Reversal: the 2 x 3 formula was written ½(SH+BL) - ½(SL+BH), a size-by-return interaction;
  the factor is ½(SL+BL) - ½(SH+BH). A "loose universe" rebuild correlating 0.14 with ST_Rev
  used that wrong formula and is withdrawn. The equal-weighted 2 x 3 sort's pre-1989 loadings,
  0.43-0.56 *of* the paper's, were described as landing on the paper's 0.44 / 0.33 / 0.29 /
  0.45. Carhart's recipe was described as value weighted and 2 x 3; it is equal weighted with a
  single 30/70 sort.
- Estimator: the bench's baseline was 100.0 of 131, not the check's 105.5, because it compared
  the committed-capital means with the paper's fully invested means; the one-lag row read
  -3.5 where its own script gives -10.5; "the median cannot move" was wrong (it moves, by less
  than a band). The lag sweep is dropped: the paper fixes six lags.

## 54. Two readings the paper's text requires: book compounding and the mixed-pairs decile row (2026-11-02): 267.5 -> 261.0

Origin: a teammate's rule audit (public PR #8) bundled about a dozen convention changes. Two of them
are required by the paper's own text and tables; this section adopts those two, measures both, and
records what was measured of the rest. Both lower the score; they are adopted because the paper
requires them, not for fit.

**1. Compound each book, then subtract (Tables 1 and 3).** §2.3, p. 805: "The daily returns on the
long and short positions are calculated as value-weighted returns ... and the daily returns are
compounded to obtain monthly returns. This has the simple interpretation of a buy-and-hold
strategy." The tables pin the order: Table 7's long minus short book means (p. 821) equal Table 1
Panel B (p. 807) in all four portfolios, 0.01245 - 0.00501 = 0.00744 against 0.00745 and exactly
0.00895 / 0.00795 / 0.00715. That holds only if each book is compounded to a monthly return before
the two are differenced. Section 33 measured this reading and kept the daily difference because it
scored three points more on Tables 1-3; this section reverses that choice.
`evaluation.portfolio_monthly` compounds the long and the short book separately (committed capital
scales each book's day by n_t / N first); the driver uses it for Tables 1 and 3, and the Table 6
and Table 9B claim scripts use it too, so every portfolio series in the repository follows one
accounting. Table 7's books were already compounded separately and do not move. CACHE_FORMAT 6, and
the cache stamp records `monthly_aggregation: books`, so a format-5 cache is refused.

**2. "Average decile difference for mixed pairs" averages the mixed pairs (Table 2 Panel B).** §3.2,
p. 809: "About two-thirds of the pairs combine stocks from different size deciles (i.e., 'size mixed
pairs'), and the stocks in mixed pairs differ on average by a single decile." Section 34 found that
the scored key carried the all-pairs mean under the mixed-pairs name. It now carries the mean over
mixed pairs (1.67 / 1.74 / 2.17 / 2.64 against 0.97 / 0.97 / 0.97 / 0.98); the all-pairs mean is
`avg_decile_diff_all_pairs`. A mean over mixed pairs cannot be below 1, so the printed row is a
reported gap, and the second half of claim 10 is recorded as not replicated (`CLAIMS.md`).

**Measured on a full 474-cohort rebuild** (private cache; the shared cache is untouched):

| | Table 1 | 2A | 2B | 3 | 7 | 4 | 5A | 8 | Fig. 4 | total |
|---|---|---|---|---|---|---|---|---|---|---|
| before (row 16) | 54.0 | 20.5 | 29.0 | 83.5 | 26.5 | 24.0 | 9.5 | 19.5 | 1.0 | 267.5 |
| after (row 17) | 55.5 | 20.5 | 28.5 | 80.0 | 26.5 | 21.5 | 10.0 | 17.5 | 1.0 | 261.0 |

Table 1 Panel B means move toward the paper (0.691 / 0.879 / 0.749 / 0.603% -> 0.723 / 0.891 /
0.764 / 0.629%, paper 0.745 / 0.895 / 0.795 / 0.715%) and the top-5 worst month improves (-15.3% ->
-13.6%, paper -12.6%); Table 3's sector means, already at or above the paper's, rise further. The
decile row costs 0.5 (top 5 from ~ to ✗).

**Checks.**

- *Data and cache.* Before the change, a from-scratch rebuild of `personal/main` on the current shared
  panel reproduced the committed check line for line (only the Figure 1 file path differs), so the
  data and SIC mapping are the ones behind 267.5.
- *An independent implementation.* The same two changes in the teammate's code (PR #8 at 5d137c3,
  `--specification legacy --monthly-aggregation books --start 1963-07`) give identical marks on all
  484 cells both checks mark. Its `legacy` profile alone reproduces our 267.5 except the decile row.
- *Controls.* Table 6's control rebuilds the true-pair series from the trade logs with the new
  accounting and matches the cache exactly (maximum difference 0; the vectorised layer to 1.3e-15).
  Table 9B's no-recall control matches all 474 cohorts.
- *The paper's identity.* With book compounding, Table 1 Panel B equals Table 7 long minus short in
  every portfolio (gap below 0.00001; `claims/TABLE7_REGRESSIONS.md`).

**The rest of PR #8, measured one change at a time on top of these two fixes (261.0), not adopted:**

| change | score change | why not adopted |
|---|---|---|
| drop the 95% stale-quote screen | -17.5 | our disclosed convention (section 18); the paper is silent |
| value short weights | -11.5 | our disclosed reading of eq. (3) (section 29, with its objections) |
| allow same-issuer pairs | -9.5 | our disclosed convention (section 18) |
| formation-end SIC only | -1.0 | a separate decision; the paper is silent |
| next-day entry without the crossing check | -1.0 | a separate decision; the paper's wording supports it (p. 808) |
| zero return for a whole idle month | 0.0 | a separate decision |
| all six together | -25.0 | |
| strict trade-flag universe (`traded_common`) | | 1,799 stocks and 1,561 pairs per cohort against the paper's 2,317 and 2,057 (pp. 807, 812); it drops all pre-November-1982 Nasdaq stocks |
| sigma as the demeaned standard deviation | -6.0 | the paper's only direct measurement of sigma, Table 2A's trigger (p. 809), is closer under RMS in three columns and tied in the fourth (section 21) |
| warm-up cohorts from 1963-02 | | contradicts p. 806: "with the exception of the first 12 months, which are needed to estimate pairs" |

**Table 6's design: the random position opens and closes with its true trade.** The caption
(p. 819) opens "a position in a random pair when the stocks in the true pair diverge by two
historical standard deviations and closes the position after the next crossing of prices", and
§3.6 (p. 818) takes "the set of historical dates on which the various pairs open" and reads "the
difference between the actual and the simulated pairs returns" as "the portion of our pairs return
that is not due to reversion". The only crossing the sentence defines is the true pair's, and the
A/B difference isolates stock selection only if both sides hold their positions over the same
dates. So each random position now opens and closes with the true trade it replaces (earlier only
if a drawn stock delists or its data end); the drawn stocks keep their true legs' long and short
roles. The previous primary closed on the drawn stocks' own next crossing, a reading with no
sentence behind it. Three designs were measured on this build's accounting (no wait, fully
invested, top 5 / top 20 / 101-120 / all 120):

| design | random means | random SDs | Table 6 cells ✓ / ~ / ✗ |
|---|---|---|---|
| (a) open and close with the true trade (primary) | -0.20 / -0.31 / -0.31 / -0.34% | 4.12 / 2.13 / 2.15 / 1.01% | 8 / 10 / 30 |
| (b) close on the drawn stocks' own crossing (`--close own`) | -0.16 / -0.23 / -0.23 / -0.24% | 3.49 / 1.84 / 1.92 / 0.85% | 1 / 18 / 29 |
| (c) the drawn stocks on their own 2-sigma rule (scratch only) | -0.11 / -0.15 / -0.18 / -0.17% | 4.79 / 3.88 / 3.98 / 3.12% | 9 / 6 / 33 |
| paper | -0.14 / -0.11 / -0.11 / -0.11% | 5.52 / 2.30 / 2.26 / 1.20% | |

(a) was chosen on the text; it also scores best (13.0 of 48 against 10.0 and 12.0). (c) contradicts
the caption's open and does not diversify like the paper's random pairs: their SD falls from 5.5%
to 1.2% between 5 and 120 pairs, (a)'s from 4.1% to 1.0%, (c)'s only from 4.8% to 3.1%. The
decile stays the previous calendar month (§3.6, "previous month's performance"): ranking on the
trailing month that ends on the open day made random pairs earn +0.09 to +0.16% a month on PR #8's
other conventions, the reversal profit, against the paper's "slightly negative". In every design
true minus random is positive with t > 2 in all 16 series. The sign of the random-pair mean is set
by the short-weight convention, not by the bootstrap: under PR #8's value weights the random means
are near zero, under this repository's position weights they are negative, as in the paper.

**Claim 4 is no longer counted.** "Pairs trading profits from temporary mispricing of close
substitutes" (p. 797) is the abstract's interpretation, used nowhere else in the paper (its body
speaks of the "Law of One Price"). `CLAIMS.md` lists it under "Not tested" and counts 24 claims:
19 replicate (5 with the paper's numbers, 14 in substance), 4 partly, 1 not as stated.

**Legacy SIZ, for the data question.** A run of the shipped code on CRSP's legacy SIZ daily file
(final December 2024 release; `data/raw/wrds_api/legacy/dsf/`) scores 249.5 with the usual share
codes 10/11/12 and 263.5 with REITs (code 18) added. The two releases agree on 56.6 million matched
rows except the share code of corporate REITs, which CIZ classes as ordinary common stock; the data
are not closer to the paper in either format.

**One Table 6 output directory holds one run.** `--mode run` resumes by skipping the cohorts
already written, so a second run with another `--close`, seed or replication count into the same
`--out-root` would have mixed the two runs without a word. The directory now records the three
in `run_params.json`; a run or report that does not match it is refused, as are older outputs
without it, and `--mode report` renders only the primary `--close true` design that
`t6_template.md` describes. The committed report came from a fresh directory and is unchanged.

## 55. Footnote 4's delisting check and the 495x map as flags; one Newey-West estimator (2026-11-02): 261.0 -> 261.0

Two opt-in flags of `scripts/03_replicate.py` and one estimator fix. Neither flag is on by default,
and each is stamped in `cache_meta.json` only when on, so a default cache's stamp is unchanged and
the shipped check is untouched by them. All numbers are a full 474-cohort build of this
repository's defaults (`vol_common`), which reproduces the committed check at 261.0 before the
change; each flag was built into its own cache (`--cache-root`).

**1. `--long-delisting-loss`: footnote 4 (RFS p. 804).** The paper's robustness check assumes
every delisted long position loses 100% and reports the top-20 no-wait fully invested mean falling
from 1.436% to 1.32% and its standard deviation rising from 1.69% to 1.9%. With the flag, an open
position whose long leg has a terminal (`dlydelflg == 'Y'`) row books -1.0 on that leg that day,
including when the row has no return; a delisting short leg keeps its actual return, and prices
that drive the rule are unchanged (`models.simulate_cohort`, `long_delisting_loss`).

| top 20, no wait | plain | footnote 4 | change |
|---|---|---|---|
| fully invested mean, ours | 1.387% | 1.274% | -11.2 bp |
| fully invested mean, paper | 1.436% | 1.32% | -11.6 bp |
| standard deviation, ours | 1.67% | 1.87% | +0.20 |
| standard deviation, paper | 1.69% | 1.9% | +0.21 |
| committed mean, ours | 0.807% | 0.730% | -7.8 bp |

On the current accounting the effect has the paper's size in both the mean and the dispersion.
Section 17's earlier calibration (1.333% to 1.169%, about 1.4x the paper's effect) was measured
before the book-compounding change of section 54 and is superseded. The other portfolios: top 5
-16.6 bp, 101-120 -6.3 bp, all pairs -24.2 bp (no wait); the one-day wait moves by the same
amounts to within 1 bp. The top-5 worst month falls from -13.1% to -23.9%. Scored, the assumption
gives 217.0 of 481 (Table 1: 20 of 88 within 10%), so it stays a sensitivity, as in the paper.

**2. `--waste-sic utilities`: section 24's map as a flag.** SIC 4950-4959 back in Utilities moves
261.0 to 259.0, all in Table 3: the Utilities stock count improves (137 to 144 against 156, ~ to
✓) and Utilities 101-120 loses the cells section 24 gained (mean 0.89% to 0.72% against 0.93%;
t, skew, kurtosis, minimum and maximum each lose a mark; standard deviation gains one), with small
moves in Utilities "all". The top-pair sector weights do not move (weight_utilities 0.774), as
section 24 found. The default stays Industrials.

**3. Table 1's Newey-West standard error has no small-sample factor.** `evaluation.summary_stats`
used statsmodels' HAC with `use_correction=True` (an n/(n-1) factor) while `factors.factor_tstats`
(Tables 4 and 8) uses none; the paper states none. Both now use none, and a test pins the two to
one estimator. Five printed t-statistics move by 0.01 (Table 1 Panel B and the four Table 3
sectors), no mark changes, and the score stays 261.0; `REPLICATION_CHECK.md` is regenerated.

**Not added: a second fully invested row.** A row dividing the period's summed fixed-dollar
payoffs by the pairs that opened was considered and dropped: `mean_employed_literal` in
`table1.csv` already reports payoffs over the pairs that open (compounded daily). It gives
0.856% for the top 20 against 0.807% committed and 1.387% fully invested, a ratio of 1.06
against the paper's 1.8, so the literal denominator cannot produce the paper's fully invested
numbers and the employed-capital reading the shipped headline uses is consistent with them.

## 56. Public sync: #12's flags, #13's importers and input checks, #14's tables (2026-11-03): 261.0 -> 261.0

The public team repository merged three PRs after the two readings of section 54: #12 (section
55), #13 (data importers and input checks, split out of public #8) and #14 (output tables
regenerated after #12). This branch brings in what is consistent with the code here and leaves
out what only the proposed public #8 baseline uses.

**Synced.** Section 55's `--long-delisting-loss` and `--waste-sic` flags and the single
Newey-West estimator; the CIZ web-export and legacy SIZ importers (`import_ui`, `legacy_import`,
`issuer_header`, `vintage_audit`, their scripts and query records), which read existing
downloads and write new local panels only; `GGR_PROCESSED_DIR` / `GGR_ISSUER_HEADER` input
overrides; Table 9B's input checks (a missing volume year, conflicting security-day volumes and
an observed volume without a finite positive `dlycumfacshr` now raise instead of reading as no
recall or no split; none of the 50.2 million observed-volume rows of 1961-2002 fails them); and
Table 7's cache check (`specification.validate_cache_identity`).

**Not synced.** `evidence_validation`, `reconciliation`, `validation` and `replication_report`,
and the profile helpers of `specification` (`PROFILES`, `resolve_profile`, `stamp_experiment`,
`validate_paper_cache`, `validate_book_cache`, `validate_claim_cache`). Nothing here calls them;
they expect public #8's cache format 7, its stock-value short weights and output files this
driver does not write, and their docstrings describe that baseline as the default. They belong
with #8 if it is adopted. `TOOLING_SPLIT.md` is a note on the public PR split and is not copied.

**Verified.** A full 474-cohort default rebuild from this branch reproduces
`REPLICATION_CHECK.md` byte for byte (261.0 of 481) and every committed output table; Figure
1's JSON differs only in its stored image path. The rebuild manifest and
`score_wrapper.PINNED_MANIFEST` are re-pinned to this code. The Newey-West change also moves the
standard errors and t-statistics in the Table 6, 7, 9A and 9B claim reports by about 0.1%
(sqrt(474/473) - 1 on the full sample). Those reports are regenerated from the rebuilt cache
(`TABLE9A.md`, which is maintained by hand, and claim 1 of `CLAIMS.md` take the new values; Table
1 Panel B's t is now 6.45 / 9.29 / 9.86 / 7.01). Every ✓ / ~ / ✗ mark in the eight claim files is
unchanged, and so is every verdict.

**Fixed: Table 9B could not run.** #13's input check made `table9b_recalls.py` call
`project.recalls.adjusted_volume` without importing it, so every cohort failed with a `NameError`
(public `main` has the same bug). The unit tests did not reach that line: the missing-file test
raises before it. The import is added, and `test_volume_is_read_and_split_adjusted` reads a small
synthetic year file through `VolumeSource`, so the path is now tested; it fails without the import.

**Fixed: another data vintage could reuse the default cohorts.** #13's `GGR_PROCESSED_DIR` points
the driver at another processed panel (a legacy SIZ import, say), but nothing stamped that into
the cohort cache: `processed_source_identity` was never called, so a run on another vintage into
an existing cache resumed from the default panel's cohorts and reported them as its own. The
stamp now carries `processed_source` (the panel's `source.json` hash and return convention) when
the variable is set, and `verify_cache` / `stamp_cache` refuse a mismatch. Default caches carry
no such key, so their stamp and contents are unchanged (a full rebuild is identical file for
file). The CIZ daily import now writes its provenance as `source.json` inside the panel, where
the legacy import already wrote it and the stamp reads it, instead of `../ui_import_manifest.json`,
which nothing read.

## 57. The late sample as one exchange's file: formation profile fits, returns and count do not (2026-11-15): 261.0 -> 261.0

`OPEN_QUESTIONS` ("Post-1983 test of Q5", item 4) derived the late sample the published edition
implies, given that our first 408 cohorts reproduce the 1999 draft's Table II: top-20 Utilities
near 0%, Financials about 70%, mixed-sector about half, top-5 trigger about 0.10, and read it as
impossible for any universe like ours. One reading had been listed as untried: that the
1997-2002 extension was built on a different population, for instance one exchange's CRSP file.
It is measured here on the 66 cohorts formed 1997-07 to 2002-12, with the shipped engine and
settings, the formation universe restricted after the shipped screens to Nasdaq only or to NYSE
and AMEX only (`scripts/experiments/late_exchange_universe.py`; 48 s per variant on one worker).
The table is in `REPLICATION_MAP.md` section 4. In short:

- **Nasdaq only reproduces the implied formation profile.** Trigger 0.077 / 0.086 / 0.123 /
  0.318 against the implied 0.095 / 0.102 / 0.121 / 0.275 (the combined universe: 0.048 / 0.055 /
  0.079 / 0.241); Utilities 4% of the top 5 and top 20 against the implied 16% / 3% (combined
  46% / 41%); Financials 82% / 79% against 54% / 69%. The published edition's trigger row, which
  no screen on the combined universe moved more than 3%, is matched at the 101-120 rank to 2% by
  removing the NYSE and AMEX names from the late sample.
- **It does not reproduce the returns or the count.** The Nasdaq-only top 20 earns 1.65% a
  month with a 2.93% standard deviation over the 66 months (one-day wait) and 2.92% / 3.34% over
  1999-2002 without the wait, against Table 8's post-1988 0.375% / 0.99% and section 1.2's
  hold-out 10.4% a year (0.87% a month) with a 3.8% annual standard deviation; the combined
  universe gives 0.34% / 1.19% and 0.53% / 1.26%, and NYSE + AMEX 0.31% / 1.27% and
  0.45% / 1.32%. February 2000 for "all" deepens from -3.4% to -5.5% (paper's minimum -2.95%;
  NYSE + AMEX -3.0%). Pairs per cohort are 1,792 against the implied 3,213 (combined 3,377).
- **NYSE + AMEX only is the combined universe on every formation row** (the tight late pairs are
  NYSE REITs and utilities in both), and its returns are within 0.05% a month of the combined.

So the published edition's three late-sample pins want three different populations: the
formation profile a Nasdaq-dominated one, the returns a combined or NYSE one, the pair count
the combined one. No single screen satisfies them, and the conclusion of `OPEN_QUESTIONS` stands
with the formation side now matched rather than inferred: the published Table 2 differs from
the 1999 draft by more than the sample extension, class B of `REPLICATION_MAP.md` is an edition
difference, and the late-period return cells (class E) are not a universe choice, since the one
universe that fits the published trigger makes them worse. Nothing is shipped; the check stays at
261.0.

The same section of `REPLICATION_MAP.md` records the era bracket itself (ours against the draft
on the first 408 cohorts, ours against the implied values on the last 66) and section 2 the
census of the 481 cells by cause that the map is built on; the census tally reproduces 261.0.

## 58. The four claims that fall short, measured under the readings the paper leaves open (2026-11-15): 261.0 -> 261.0

`CLAIMS.md` leaves one claim not replicated as stated (16) and three partly replicated (9, 20, 24).
None fails on a sign; three fail on the size of a t-statistic and one on the size of a robustness
effect. Each is measured here under the readings the paper does not fix, so the write-up can say
how far each one is from the line rather than only which side of it we land. Nothing is shipped;
the scored check is unchanged. `scripts/experiments/claim_sensitivity.py` writes
`claims/CLAIM_SENSITIVITY.md` and `claims/claim_sensitivity.csv` from the shipped cache; the recall
rows come from `scripts/claims/table9b_recalls.py --sd-multiple 2.0` and `3.0`, a new option that
keeps its report under the run's own `--out-root` so the committed `TABLE9B.md` (the paper's one
standard deviation) is untouched.

**Claim 16, the long book's alpha is insignificant for the top 5 and top 20** (Table 7). The top 5
holds under every reading: 25-40 bp with t 0.9-1.7 against the paper's 10 bp (t 0.47). The top 20
is on the line: 36 bp, t 2.17 on the paper's reading (ST_Rev, full sample, six lags) against 24 bp
(t 1.27); insignificant in 10 of the 24 readings, none of them on the full sample (0 of 6, |t| 2.15-3.13); among them the window the 1999 draft's data reached
(to 1998-12: t 1.87), the pre-1989 half (1.76) and the post-1988 half (1.26); all ten are window redefinitions, 6 of them post-1988. The losers-only
reversal series moves it the wrong way (t 2.73), because it absorbs part of the short book's
alpha instead. The asymmetry itself replicates in every reading: the short book carries 60-66% of
the pair alpha for the top 5 and top 20 (paper 81% and 68%) and 23-43% for the two broad
portfolios, where the paper's long book is the larger (its 101-120 long alpha is 29 bp, t 2.85;
ours 51 bp, t 5.0). The verdict stays "not as stated": one t-statistic of 2.17 against 1.27, and
the claim's second half (the long book's smaller share) holds.

**Claim 24, risk-adjusted returns persist after 1988** (Table 8 Panel B). The top 20 is robust:
36-37 bp with t 2.8-4.5 against 42 bp (t 3.77). The top 5 is 21 bp, t 1.58 on the paper's reading
against 34 bp (t 2.12); the losers-only series lifts it to 26 bp, t 2.00 and 1.98 at zero and six
lags, and the window to 1998-12 lowers it to 1.1-1.6. Two of twelve readings cross 1.96. The
20 after the top 100 (18 bp, t 2.29) and all pairs (-10 bp, t -0.94) have the paper's signs
(36 bp, t 3.01; -7 bp, t -0.56).

**Claim 9, net profits of 113-225 bp per six months are significant** (section 3.3). Our six-month
gross is 442 / 547 / 467 / 383 bp against the paper's 455 / 549 / 487 / 437. Net of the paper's 324 bp
and read against the six-lag Newey-West error, t is 1.75 / 3.87 / 3.08 / 1.10 against the ledger's
reading of the paper's 1.8 / 3.9 / 3.2 / 2.1: three of four match to the first decimal, and the
all-pairs t is the one short, because that portfolio's gross is 54 bp below the paper's. At our own
measured round-trip cost (297 bp, the top-20 drop from no wait to one-day wait over six months) the
all-pairs t is 1.61; on the window to 1998-12 it is 1.72 at the paper's cost and 2.21 at ours. Four
of twelve readings cross 1.96, all with zero lags or the pre-1999 window.

**Claim 20 (b), short recalls cost 4-13 bp a month** (Table 9 Panel B). The threshold is the one
definitional lever the text leaves: "more than one standard deviation" above the 18-month average.
At one, two and three standard deviations the rule flags about 8%, 3% and 2% of a stock's days and
ends 69%, 48% and 36% of the recall-run trades on a recall. The change against our Table 1 Panel B,
primary reading (re-entry only on a new episode), in bp of the monthly mean, paper's decline in
brackets:

| threshold | fully invested (paper 12.6 / 4.1 / 13.0 / 13.0) | committed capital (paper 15.9 / 17.3 / 20.7 / 19.4) |
|---|---|---|
| 1 sd (shipped) | -10.1 / -21.2 / -17.9 / -51.6 | +7.8 / +12.7 / +15.2 / -4.4 |
| 2 sd | -10.6 / -13.3 / -11.8 / -26.0 | +4.2 / +11.1 / +12.6 / +3.2 |
| 3 sd | -5.6 / -6.6 / -8.6 / -13.0 | +3.1 / +8.8 / +9.0 / +4.9 |
| 3 sd, no re-entry | -5.8 / -7.0 / -9.0 / -5.5 | +11.8 / +18.5 / +16.6 / +10.8 |

A rarer recall shrinks the fully-invested rise but never turns it into the paper's decline, in any
reading; on committed capital the decline has the paper's sign at every threshold and its size at
three standard deviations without re-entry (four of four within a factor of two). So the half of
the claim that does not replicate is not the threshold: it is the property `TABLE9B.md` section 0
names, that our fully-invested measure re-bases a re-opened book, and the committed row, which
cannot, replicates the paper's effect. Verdict unchanged: (a) replicated, (b) replicated on
committed capital and not on fully invested capital, at every threshold.

**What this leaves for the claims.** Nineteen of twenty-four replicate as before. Of the five that
do not, one is paper-side (10), three are a single t-statistic within one standard error of the
paper's side of 1.96 (9, 16, 24) and one is a measure-definition question on which the paper's own
two rows disagree with each other in our hands (20 b). No step in `REPLICATION_MAP.md` section 7
reaches them, and none of them touches a chain of the paper's argument.

Both this section and 57 record the row-17 base (261.0 to 261.0); PR #64 moves the total to 262.0 with two Table 1 committed-capital marks and leaves every measurement here unchanged. After #64 merged, REPLICATION_MAP.md section 2 is regenerated to the row-18 base (262.0, class F 167/52/12 at 193.0); every measurement here is unchanged by that.
## 59. PR #64 review follow-up: the note, the wording, and the committed-capital switch (2026-11-15): 262.0 -> 262.0

The review of #64 approved the reading and asked for two documentation fixes and one design
decision. No scored cell moves: the check, `REPLICATION_CHECK.md`, the score and the full-sample
threshold (262.0) are untouched, and this section is the record.

The follow-up is documentation only in the literal sense: `src/project/evaluation.py`
carries no change in this commit. `scripts/rebuild_manifest.json` pins its sha256
(`66530f87b8b4bb697e482eef12bafca1124e8876ae3e2ba567889f44745a72c4`) and
`tests/test_score_wrapper.py` enforces the pin, so even a docstring or comment edit
invalidates it until the manifest is re-pinned and the affected tables rebuilt. The
decision record therefore lives here, in the note, rather than beside the code it
describes.

**The conformance note counted four marks, the check moved two.** `tests/replication_conformance.json`
`full_sample.note` said the change moved "four Table 1 committed cells (Panel A 101-120 and all,
Panel B top5 and all)". The regenerated check moves exactly two marks, both ~ -> ✓: Panel A 101-120
(0.62% against 0.68%) and Panel B all. Panel A "all" and Panel B top5 were already ✓ since row 17's
book compounding and kept their marks. The note now states the two marks and defers to SCORE_LOG
row 18, which had it right.

**"Tables 3-8 and Figure 4 unchanged by construction" conflated scored cells with the series.**
`TABLE3_CAPITALS` includes `"committed"`, so Table 3's committed columns do change values under the
literal reading; they are simply unscored, because the check's Table 3 sections compare the
fully-invested columns only, which is why no Table 3 line appears in the `REPLICATION_CHECK.md`
diff. The PR text now says "all scored cells outside Table 1 unchanged; Table 3's unscored
committed columns move within band", which is the accurate sentence, and the conformance note
carries the same qualification.

**The `committed` switch stays, and is now documented.** `_has_trade_log` makes
`capital="committed"` mean two economically different things, keyed on `len(result.trades) > 0`,
and its docstring used to justify the fallback by the unit-test fixtures. That justification is
backwards, and this section records the contract instead: every shipped number comes from a
`simulate_cohort` result, the paths that feed the check are all non-empty by construction
(`scripts/03_replicate.py`'s `tables` / `table3` / `check` steps, the `t6_engine` control rebuild and
the `table9b` reader all aggregate stored engine results, whose `trades` frame is populated whenever
a cohort selects a pair), and a cohort with no selections is numerically identical under both
readings because there are no payoffs to scale. The reasons it stays rather than becoming
unconditional:

- The literal branch and the hybrid agree on every cell of the shipped check; the switch is not a
  numeric freedom, it is an interface guard that keeps `portfolio_*` total for the lightweight
  result objects the module has always accepted (`test_evaluation`'s five hand-calculation fixtures
  build them without an engine).
- Making the literal unconditional rewrites those five fixtures, which compare the hybrid to numbers
  derived from it. That is a test-fixture change with no production effect, and it does not belong
  in a documentation follow-up.
- An explicit `capital`/flag parameter would thread a new keyword through `02`/`03`, the claim
  scripts and the cache readers for the same reason. If a lightweight replay path is ever wired to
  a scored cell, the correct fix is to pass engine results to it, not to widen this signature.

**The guard asymmetry stays too, with a reason.** `portfolio_daily` guards the literal branch with
`sel and _has_trade_log(result)`; `portfolio_monthly` guards with `_has_trade_log(result)` alone.
The difference is deliberate, not an oversight: the literal branch divides by `len(sel)`, so the
function that owns that division has to reject an empty selection, and `portfolio_monthly` delegates
to it, where an empty selection falls through to the historical hybrid and returns an empty series.
Repeating `sel` in the monthly guard would restate the same rule one frame up rather than add a
case; this section records it as deliberate.

## 60. Table 9 Panel A joins the scored set, as printed (2026-11-15): 262.0 -> 289.0

Contract B. The paper's robustness table on the top-three-size-deciles universe (p. 825,
one-day wait) was replicated but unscored (`claims/TABLE9A.md`, sections 53-55). It is a
scored section of the check now: 44 cells, 22 / 10 / 12 as printed, +27.0, and the total
moves 262.0 -> 289.0 of 525 (SCORE_LOG row 19).

**Plumbing.** `scripts/03_replicate.py` gains `--table9a-cache <dir>` (default
`data/processed/replication/vol_common_top3`, `none` leaves the section out) and a
`make table9a` target that builds the screened cache with `--size-deciles-top 3`. The
check step aggregates that cache with the same `summary_stats` the Table 1 section uses,
and stops with an error naming the build command when the cache is absent, exactly as
`--aggregate-only` does for the main cache. The screened cache this run scored is the one
sections 53-55 built (`.review/wt/claims-t9a/.private/t9a/top3`, 475 cohort directories);
the stamp accepts it because the formation flags and CACHE_FORMAT are unchanged, and a
copy lives at the default path for `REPLICATION_FULL=1`. The paper's 44 values are typed
as `PAPER_TABLE9A` and re-read from the PDF by a new `table9a` parser in
`scripts/verify_paper_targets.py` (`make verify-targets` passes).

**The transposed rows, scored as the paper prints them.** Panel A's kurtosis row reads
0.02-1.77 and its skewness row 7.01-11.67 -- the labels are swapped against Table 1's own
scale (COVERAGE.md, "Where the published version contradicts itself", item 1). The
repository's rule is that paper values are the paper's, so the scored rows compare our
skewness against the printed "Skewness" row and our kurtosis against "Kurtosis"; the
swapped reading prints on the line below each as an unscored diagnostic. Those two rows
carry eight of the block's nine misses (kurtosis 4, skewness 4, minimum 1); under the
swapped reading the block would score 22 / 11 / 11 = 27.5 instead of 22 / 10 / 12 = 27.0.
Class F takes the block's 28 moment cells (20 / 8 / 0) and class D its 16 shape cells
(2 / 2 / 12); `REPLICATION_MAP.md` is regenerated to the row-19 base.

**The sample smoke floor does not move.** The stride-24 sample scorer covers Tables 1-3,
7 and the 43 factor-free cells of SCORE_LOG row 15 only, and its run executes
`--steps tables,table3`, never the check step, so Table 9 A is outside it by construction;
the conformance note records this and that `REPLICATION_FULL=1` needs the screened cache.
## 61. The reversal factor the paper's own Table 8 implies, scored (2026-11-15): 262.0 -> 270.5

The five-factor block is now scored on the losers-only series the paper's Table 8 arithmetic
implies instead of French's ST_Rev, and ST_Rev is printed unscored beside it. The reading is that the paper's factor can be rebuilt: no long-short construction reaches the printed before-1989
standard deviation of 0.0723 (ST_Rev: 0.0259), while the equal-weighted bottom three prior-month
deciles less the T-bill give 0.0685 with correlations +0.84 (market) and +0.77 (SMB) against the
+0.81 and +0.79 that Table 8's loadings, R2 and factor SDs imply, and the 2.19%/month premium the
mean identity pins (sections 49-51, `REVERSAL_FACTOR_AUDIT.md`, `PAPER_CONSISTENCY.md`).
This is a hypothesis that the paper's factor lacks its short leg -- the split into six deciles minus bottom three, as the text says, does not fit its own table -- not a settled reading, and `--reversal-factor st_rev` restores row 18's block.

**What moved, cell by cell (52 class-C cells: Table 4's five-factor block 28, Table 8's post-1988
regressions for top 5 / top 20 / all 21, Figure 4's residual correlations 3).** Class C scores
7.0 -> 13.0 (check 2 / tilde 10 / cross 40 -> 6 / 14 / 32). Table 4: the "all" market loading and
the "all" reversal loading move cross -> check, the "all" intercept, the 101-120 market and SMB
loadings and the 101-120 reversal loading cross -> tilde, and the top-20 momentum loading tilde ->
check (4.5 points). Table 8 after 1988: the "all" market loading cross -> check, the top-5
intercept, the "all" momentum loading and the top-5 and "all" reversal loadings cross -> tilde,
while the top-5 HML loading, the top-20 reversal loading and the top-20 R2 move tilde -> cross
(1.5 points). Figure 4's three residual correlations do not move (cross, tilde, cross).

**The bigger mover outside class C is class A.** The paper-side pre-1989 regressions move with the
factor too, from 4.0 to 6.5 (2 / 4 / 33 -> 4 / 5 / 30): two cells cross -> check and one cross ->
tilde, three tilde/cross pairs swap. That is why the total moves 8.5 points rather than the 6.5 the
class-C block alone accounts for.

**Objections.** (1) The losers-only series' post-1988 standard deviation is 0.069-0.086, against
the printed 0.0445, so the fit is a before-1989 fit: the post-1988 block gains only 1.5 of the 6.0
class-C points. (2) The splice (losers-only before 1989, ST_Rev after) was measured at 15.5 on the
84 regression cells against 20.0 for pure losers-only (section 53) and is not adopted. (3) The
scored total reproduces exactly (270.5) from the shipped cache, and `--reversal-factor st_rev`
reproduces row 18 byte for byte apart from the header paragraph, so no series changed outside the
regression rows. (4) The option is aggregation-only: it is not in the cache stamp, because no cohort
is rebuilt, and the cache identity check is unaffected.

**Editions.** The 1999 draft prints no regressions, so `EDITION_1999.md` and its cells are unchanged.

The claims ledger follows the scored series (this section): claim 6's intercepts, claim 14's
R2 and tally (19/14/27 of 60), claim 15's reversal loadings, claim 16's long-book alphas
(0.38%/t 2.07 and 0.45%/t 2.73), claim 18's subperiod intercepts and claim 24's post-1988
intercepts (t 1.98 / 4.26 / 7.58 / 2.12) all quote the losers-only numbers as primary with
the ST_Rev reading in parentheses, and claim 24's verdict moves from "partly replicated" to
"replicated in substance" (the top-5 t crosses 1.96: 1.98 against 1.58 under ST_Rev).
`claims/CLAIM_SENSITIVITY.md` is regenerated with the labels swapped (losers-only now
"shipped"); its numbers are unchanged. `claims/TABLE7_REGRESSIONS.md` still prints the
ST_Rev reading of Table 7's book regressions; regenerating it under the scored series is a
follow-up for its own script, and CLAIMS.md names this file and the sensitivity tables as
the source of both readings until then.

## 62. Table 5 Panel B (daily value at risk) joins the scored set (2026-11-16): 297.5 -> 327.5; 337.0 -> 367.0 of 709 on main

Table 5 Panel B is the nine statistics of Panel A applied to the DAILY returns of the one-day-wait
fully invested portfolios, and it is now scored: 36 cells, 26 within 10%, 8 within 25% and 2 outside
(SCORE_LOG row 24). The note under Table 5 says the rows are "Monthly and daily VAR percentiles of
pairs trading strategies between July 1963 and December 2002 (474 months)" under "the rule that
opens a position in a pair on the day following the day on which the prices of the stocks in the
pair diverge by two historical standard deviations" (p. 816), and the text reads "Panel B shows that
on its worst day, the top five portfolio recorded a 10.08% loss, compared to a 6.72% loss of the top
20 portfolio. On average, only once every hundred days did these portfolios lose more than 1.24% and
0.65%, respectively" (p. 816). Panel B's row labels are "Mean excess return", "Standard deviation",
"Serial correlation", the four percentiles under "VAR", "Probability of return below 0" and
"Minimum historical observation". All 36 printed values are typed into `PAPER_TABLE5B`, added to
`scripts/paper_cells.json`, and re-read out of the PDF text layer by
`scripts/verify_paper_targets.py` ("Table 5 Panel B: 36 values compared"; `make verify-targets`).

**The measurement, and why it is a cache change.** The cohort cache stores, since format 7, each
cohort's `daily.parquet`: the daily fully-invested return of the four one-day-wait portfolios
(date, portfolio, ret), the series `portfolio_daily(result, ranks, "employed", short_weights)`
whose monthly compounding `cohort_monthly` already caches for Tables 1 and 3. `aggregate` files the
daily overlap average under `strategy[1][portfolio][DAILY_CAPITAL]`: each trading day's
equal-weighted mean over the cohorts trading that day, which is `overlap_average` unchanged applied
to daily timestamps, not a second aggregation rule. A day on which a cohort holds no position is NaN
in that cohort's series and is skipped, exactly as a NaN month is skipped in the monthly average, so
the daily series is Panel B's object one level down rather than a new strategy. `write_outputs`
writes `table5b_daily.csv`, `write_replication_check` prints it between Tables 5 A and 8, and the
section's note states the conventions below. The daily rows are additional output: Tables 1-4,
Table 5 Panel A, Tables 7, 8 and 9 A and Figure 4 are byte-identical to the row-20 check, and the
diff between the two files has five hunks only (the title line, one sentence of the header
paragraph, the summary block, the new section, and the auto-derived total in the
`reversal_alternative` paragraph, 289.0 -> 319.0 and 297.5 -> 327.5).

**Conventions the paper does not state.** (1) Percentiles are linearly interpolated, pandas'
default, the same estimator Panel A uses (section 15). (2) Serial correlation is the lag-1
autocorrelation of consecutive trading days: the series is reindexed to the exchange calendar
between its first and last day, so a gap never pairs two days that are not trading-day neighbours,
the daily counterpart of `_monthly_autocorr` (section 15). (3) The standard deviation is the sample
one (ddof=1), as in Panel A. (4) "Probability of return below 0" is the share of days with a strictly
negative return. (5) The paper prints the 101-120 serial correlation as "0.00" (p. 816), a rounded
zero, where a ratio of covariance to variance is undefined; `_cell` therefore marks a cell whose
paper value is exactly zero on whether ours prints the same value at the paper's own precision.
That is new code, not a change to `_mark` (within 10% = check, within 25% = tilde), and it fires only here: no other scored cell has a paper value of exactly zero, so no
existing mark can move.

**Marks, cell by cell.**

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean | ✓ | ✓ | ✓ | ✓ |
| standard deviation | ✓ | ✓ | ✓ | ~ |
| serial correlation | ~ | ✓ | ✗ | ✓ |
| 1% VaR | ✓ | ✓ | ✓ | ~ |
| 5% VaR | ✓ | ✓ | ✓ | ~ |
| 10% VaR | ✓ | ✓ | ✓ | ~ |
| 25% VaR | ✓ | ✓ | ✓ | ~ |
| probability of return below 0 | ✓ | ✓ | ✓ | ✓ |
| minimum | ✓ | ~ | ~ | ✗ |

Marks are 26 / 8 / 2. The top five column is check in eight of nine cells, its serial
correlation (-0.1078 against -0.12, 10.2% off) the exception; the top twenty in eight, its
worst day (-5.96% against -6.72%) the exception; 101-120 in seven. The values behind the table: mean 0.035 /
0.043 / 0.037 / 0.029% against 0.033 / 0.040 / 0.035 / 0.027%; standard deviation 0.496 / 0.302 /
0.288 / 0.191% against 0.492 / 0.296 / 0.277 / 0.169%; 1% quantile -1.21 / -0.67 / -0.67 / -0.40%
against -1.24 / -0.65 / -0.65 / -0.33%; 5% -0.70 / -0.41 / -0.40 / -0.25% against -0.71 / -0.40 /
-0.40 / -0.20%; 10% -0.51 / -0.30 / -0.30 / -0.18% against -0.50 / -0.29 / -0.29 / -0.15%; 25%
-0.24 / -0.13 / -0.14 / -0.08% against -0.24 / -0.13 / -0.13 / -0.07%; probability below zero 0.47 /
0.44 / 0.45 / 0.45 against 0.47 / 0.44 / 0.45 / 0.46; worst day -10.02 / -5.96 / -1.79 / -1.47%
against -10.08 / -6.72 / -1.99 / -1.07%. The two ✗ are the 101-120 serial correlation, 0.04 against
a printed zero, and the "all" worst day, 1.38 times the paper's.

**The "all" column.** The three named columns agree on every row; the "all" column is where the
block loses its marks, and the disagreement is inside the paper. COVERAGE.md item 4 records that
the paper's monthly "all" standard deviation (1.577%) is 9.3 of its own daily units where the other
three columns imply 4-7, so a daily "all" column consistent with the paper's monthly "all" would
have a standard deviation near 0.104%, and ours (0.191%) sits between the two: the paper's daily
"all" is narrower than its own monthly "all" admits. Its worst day, -1.07%, is narrower than the
101-120 portfolio's -1.99% although the "all" column has a lower standard deviation than 101-120
(0.169 against 0.277%), which no population of pairs produces. The column is reported, not
adjusted, exactly as section 29 reported its predecessor (0.243%, 1.44 times, under the
value-weighted short).

**Objections and what is left.** (1) The block rests on the cache, not on the driver alone: a
format-6 cache is refused by name, so `make benchmark` and `REPLICATION_FULL=1` need a rebuild with
`--force`. The shared cache at `data/processed/replication/vol_common` is rebuilt at merge by the
coordinator; until then `scripts/rebuild_manifest.json` and `PINNED_MANIFEST` in
`scripts/score_wrapper.py` are re-pinned together to the code that produced this check, and the PR
says the shared rebuild is pending (section 31 for why a stale pin is worse than none).
(2) The stride-24 conformance sample does not score the block: the sample scorer reads table1,
table2_panelA/B, table3, table7, table4's Sharpe row, table5_var, table8's moments and figure4 only,
and a daily average over about 1.7 cohorts a trading day is far noisier than the full sample's (in
the smoke cache the block scored 6 / 1 / 29), so it is excluded from the sample with this note and
the sample threshold stays 110.0 while `full_sample.threshold` moves to 327.5 (367.0 after the rebase). (3) The daily series
averages the cohorts trading each day (about 36 in the full sample), so the block inherits whatever
population Table 1 Panel B measures: it adds no formation or trading rule and no parameter was
tuned. (4) The 1999 draft prints no daily panel, so `EDITION_1999.md` is unchanged. (5) The
SCORE_LOG row is 24 per the round-2 addendum; rows 21-23 (Table 7's regression block, Table 9 B,
Table 6) landed first through #68, #69 and #71.

**Reproduce.**

    python scripts/03_replicate.py --universe vol_common --workers 16 --force \
      --cache-root data/processed/replication/vol_common --out-root <worktree>/.private/out \
      --steps tables,table3,figure1,check
    python scripts/03_replicate.py --universe vol_common --aggregate-only --workers 1 \
      --cache-root data/processed/replication/vol_common --table9a-cache data/processed/replication/vol_common_top3 \
      --table9b-cache data/processed/replication/vol_common_recalls \
      --table6-cache data/processed/replication/vol_common_t6 \
      --out-root results/replication --steps tables,table3,figure1,check
    python scripts/replication_score.py    # 367.0 of 709
    python scripts/verify_paper_targets.py # Table 5 Panel B: 36 values compared

**Rebased onto main after #71 (2026-11-16, coordinator).** The branch was written on the row-20
base (297.5 of 525) and rebased onto main at 337.0 of 673, after rows 21-23 had added Table 7's
regression block, Table 9 Panel B and Table 6. The check was regenerated from the format-7 cache
with all three side caches, not hand-merged. Against main's committed check, every one of the 673
scored marks is unchanged; the lines that differ are the title, the header note, the summary
block, the new Table 5 Panel B section, the figure path, and the auto-derived total in the
ST_Rev paragraph (328.5 instead of 337.0 becomes 358.5 instead of 367.0). The block adds 26 / 8 / 2
= +30.0, so the total is 367.0 of 709 (✓ 289, ~ 156, ✗ 264). One merge fix: main's `_cell` gained
a `sig` argument (Table 6's significant digits) in the position this branch's `_portfolio_table`
passed its format spec, so the spec is now passed by keyword (`fmt_spec=`); without it the Table 2
Panel A block raised "Format specifier missing precision".

## 63. Table 7's regression block joins the scored set on the scored reversal series (2026-11-16): 297.5 -> 308.0

Table 7 prints, for each of the four portfolios, the long and the short book; the bottom half of
each column is a five-factor regression. Its note (p. 821) fixes the estimator: "The returns in the
bottom half of the table are in excess of the 30-day Treasury bill returns. The risk adjustment
includes the Fama-French factors, as well as Momentum and the Reversal factors discussed in the
text. The t-statistics are computed using Newey-West standard errors with six lags."

The block is scored as 56 cells: intercept, market, SMB, HML, momentum, reversal and R2 for each
book of each portfolio (7 x 8). The dependent variable is each book's own monthly return less
French's RF; the factors are the driver's frame after `--reversal-factor` (losers-only by default,
section 61); the estimator is `factor_regression` / `factor_tstats` at six lags, now in
`src/project/table7.py` so the driver and `scripts/claims/table7.py` cannot compute a row
differently. Coefficients and R2 are scored; the Newey-West t-statistics are printed beside the
paper's and not scored, as in Tables 4 and 8, and the intercepts use the block's percent format.

Because the reversal column depends on the scored series, the same 56 cells are printed unscored
under French's ST_Rev below the scored block, in the form Table 4's alternative-factor section
uses ("ours vs paper mark", no " / "), so the scorer skips them. Under the default (losers-only)
the block scores 10.5 of 56; with ST_Rev it would score 14.5.

The Table 1 = Table 7 arithmetic is the control: the long intercept minus the short intercept
equals the Table 4 intercept the check prints, to the last digit, for every portfolio (row 17's
book compounding makes the covariance term zero):

| portfolio | long intercept | short intercept | long - short | Table 4 intercept | gap |
|---|---|---|---|---|---|
| top5 | +0.00380 | -0.00414 | +0.00794 | +0.00794 | +0.0e+00 |
| top20 | +0.00454 | -0.00441 | +0.00895 | +0.00895 | -9.9e-17 |
| 101-120 | +0.00629 | -0.00192 | +0.00822 | +0.00822 | -1.0e-16 |
| all | +0.00359 | -0.00275 | +0.00634 | +0.00634 | +0.0e+00 |

**What moved.** The total rises 297.5 -> 308.0 of 581 cells, ✓ 245 / ~ 126 / ✗ 210. Table 7 as a
whole reads 88 cells, ✓ 31 / ~ 12 / ✗ 45: the 32 performance cells are unchanged (23 / 7 / 2) and
the 56 new ones score 8 / 5 / 43 = 10.5. The 525 existing marks are byte-identical; the only other
lines that move are the Table 7 summary and the two score lines that count it.

**Cell-by-cell marks, losers-only reversal (scored):**

| row | top 5 | top 20 | 20 after top 100 | all |
|---|---|---|---|---|
| long: intercept | ✗ | ✗ | ✗ | ✗ |
| long: market | ✗ | ✗ | ✗ | ✗ |
| long: smb | ✗ | ✗ | ✗ | ✗ |
| long: hml | ~ | ~ | ✗ | ✗ |
| long: momentum | ✗ | ✗ | ✗ | ✗ |
| long: reversal | ✗ | ✗ | ✗ | ✗ |
| long: r2 | ~ | ✓ | ✓ | ✓ |
| short: intercept | ✓ | ~ | ✗ | ✗ |
| short: market | ✗ | ✗ | ✗ | ✗ |
| short: smb | ✗ | ✗ | ✗ | ✗ |
| short: hml | ✗ | ~ | ✗ | ✗ |
| short: momentum | ✗ | ✗ | ✗ | ✗ |
| short: reversal | ✗ | ✗ | ✗ | ✗ |
| short: r2 | ✓ | ✓ | ✓ | ✓ |

✓ 8 / ~ 5 / ✗ 43 of 56 = 10.5 points.

**Cell-by-cell marks, French's ST_Rev (unscored):**

| row | top 5 | top 20 | 20 after top 100 | all |
|---|---|---|---|---|
| long: intercept | ✗ | ✗ | ✗ | ✗ |
| long: market | ✗ | ~ | ✗ | ✗ |
| long: smb | ✗ | ✗ | ✗ | ✗ |
| long: hml | ~ | ~ | ✗ | ~ |
| long: momentum | ✗ | ~ | ✗ | ✗ |
| long: reversal | ✗ | ✗ | ✗ | ✗ |
| long: r2 | ~ | ✓ | ✓ | ✓ |
| short: intercept | ✓ | ✓ | ✗ | ✗ |
| short: market | ~ | ✓ | ✗ | ✗ |
| short: smb | ✗ | ✗ | ✗ | ✗ |
| short: hml | ✗ | ~ | ~ | ✗ |
| short: momentum | ✗ | ✗ | ✗ | ✗ |
| short: reversal | ✗ | ✗ | ✗ | ✗ |
| short: r2 | ✓ | ✓ | ✓ | ✓ |

✓ 10 / ~ 9 / ✗ 37 of 56 = 14.5 points.

**Sample smoke.** The stride-24 conformance scores Tables 1-3, the 32 Table 7 performance cells and
the 43 factor-free row-15 cells; the 56 regression cells need the Git LFS factor files and are
excluded from the sample the way row 15 excluded factor-dependent cells. The sample threshold stays
110.0.

**Docs and checks.** SCORE_LOG row 21 (the coordinator's numbering) records 297.5 -> 308.0;
`tests/replication_conformance.json` `full_sample.threshold` is 308.0; COVERAGE says Table 7's
regressions are scored; CLAIMS claim 16 points at the scored section of
`claims/TABLE7_REGRESSIONS.md`; `REPLICATION_MAP.md` class C grows 52 -> 108 cells by the 56
coefficients; `paper_cells.json` and `verify_paper_targets.py::table7` carry the 56 printed values
and parse the PDF's coefficient/t rows; `claims/TABLE7_REGRESSIONS.md` and
`claims/table7_regressions.csv` are regenerated with the losers-only series primary and ST_Rev
beside it, closing section 61's follow-up; the manifest is re-pinned to the code that ran the
aggregate-only check. `make verify-targets` parses Table 7's regression rows from the PDF text
layer and passes.

**Objections.** (1) The losers-only series is the hypothesis of section 61, not a published factor;
this section scores it because Table 8's arithmetic implies it, and the ST_Rev block above prices
the alternative (4.0 more points). (2) The block's 45 misses are concentrated in the loadings and
the intercept, not the R2 (4 of 8 R2 within 10%); they are the Table 4 story (sections 49-51), not
a new defect. (3) The aggregate-only run reads the shared `vol_common` cache and the shared
`vol_common_top3` Table 9 A cache and rebuilds no cohort.

## 64. Table 9 Panel B joins the scored set, on the claim script's primary reading (2026-11-16): 297.5 -> 315.5

Contract E. The paper's second robustness table -- short recalls on high-volume days (p. 825) --
was replicated and reported unscored in `claims/TABLE9B.md`; it is a scored section of the check
now: 44 cells, 10 / 16 / 18, +18.0, and the total moves 297.5 -> 315.5 of 569 (SCORE_LOG row 21,
marked `local` until the PR number exists). Sections 62 and 63 are the parallel round-2
contracts' numbers.

**Plumbing.** `scripts/03_replicate.py` gains `--table9b-cache <dir>` (default
`data/processed/replication/vol_common_recalls`; `none` leaves the section out; an absent cache
stops with the build command in the message) and `make table9b` runs the claim script into that
path. The section reads the cache's per-cohort `monthly.parquet`, keeps the `rearm` rows (the
script's primary reading) and aggregates them with the same `_strategy_series` overlap average
and `summary_stats` the Table 1 and Table 9 Panel A sections use, the committed series supplying
the last row, so the block cannot drift from the claim's numbers. The paper's 44 values are typed
as `PAPER_TABLE9B` and a new `table9b` parser re-reads them from the PDF text layer
(`make verify-targets`: 44 values compared, all agree). The 525 earlier cells are byte-identical:
the regenerated check differs from the committed one only in the summary lines, the new section,
and the unscored sentence that quotes the alternative reading's what-if total.

**The reading, and why the section states it.** The paper fixes the rule (one-day wait, 474
monthly observations, Newey-West six lags, absolute kurtosis) but not the recall dynamics. The
repository's primary reading, settled when the claim was reviewed: a recalled short ends the
pair; the flag fires on day t and the pair closes at the close of t+1; re-entry needs a *new*
divergence (the spread back inside two sigma, then a fresh trigger). Threshold one standard
deviation over the cohort's 18 months, both volume series split adjusted (p. 824). At this
threshold 69% of closes are recalls (TABLE9B.md section 0), and under re-entry our
fully-invested measure values the re-based open book while the closed position's accumulated
P&L leaves the series, so that row can rise while the committed row falls; the section says
both, so the fully-invested row's direction is not read as a failure of the rule rather than of
the measure. REVIEW_NOTES 58 measured the threshold at two and three standard deviations: the
verdict is the measure, not the threshold.

**Cell by cell (primary reading, ours / paper).**

| statistic | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| mean (fully invested) | 0.82% / 0.62% ✗ | 1.10% / 0.85% ✗ | 0.94% / 0.66% ✗ | 1.15% / 0.58% ✗ |
| nw_se | 0.14% / 0.11% ~ | 0.12% / 0.09% ✗ | 0.10% / 0.08% ~ | 0.10% / 0.10% ✓ |
| t_stat | 6.08 / 5.39 ~ | 9.23 / 9.07 ✓ | 9.04 / 7.81 ~ | 11.6 / 5.95 ✗ |
| median | 0.79% / 0.59% ✗ | 1.01% / 0.70% ✗ | 0.95% / 0.53% ✗ | 0.86% / 0.31% ✗ |
| std | 2.29% / 2.21% ✓ | 1.72% / 1.49% ~ | 1.84% / 1.50% ~ | 1.67% / 1.55% ✓ |
| skew | 0.274 / 0.15 ✗ | 0.551 / 0.48 ~ | 0.284 / 1.03 ✗ | 1.95 / 2.82 ✗ |
| kurtosis | 6.54 / 5.39 ~ | 5.57 / 6 ~ | 3.73 / 7.39 ✗ | 11.9 / 19 ✗ |
| min | -9.44% / -9.61% ✓ | -7.17% / -6.59% ✓ | -4.60% / -4.41% ✓ | -4.34% / -3.46% ✗ |
| max | 12.73% / 10.50% ~ | 8.81% / 7.26% ~ | 8.15% / 10.08% ~ | 12.26% / 14.17% ~ |
| share_negative | 0.348 / 0.39 ~ | 0.251 / 0.26 ✓ | 0.306 / 0.34 ~ | 0.194 / 0.37 ✗ |
| mean (committed) | 0.36% / 0.30% ~ | 0.41% / 0.35% ~ | 0.31% / 0.30% ✓ | 0.38% / 0.20% ✗ |

That is 10 ✓ / 16 ~ / 18 ✗: the precision rows and three of the four committed means are within
25%, the minima and two standard deviations match, and the level, central-tendency and tail rows
miss -- the fully-invested levels and medians high (the measure's re-entry effect), the shape
rows because our tails are as far from the paper's here as they are in Tables 1 and 3. Nothing in
the block was tuned: the reading is the claim's, fixed before this contract.

**The claim report moved on its committed-capital rows, and that is why it is regenerated here.**
`claims/TABLE9B.md` was last generated on 2026-11-03; the shared cache has since been rebuilt by
#64's committed-capital literal (SCORE_LOG row 18), and the claim's committed series is the same
series Table 1's committed row is built from. What moved, all of it on committed capital: the
primary reading's committed means (top5 0.35 -> 0.36%, top20 0.39 -> 0.41%, all 0.35 -> 0.38%;
101-120 unchanged), the two alternatives' committed means, section 5's committed-capital changes
(primary +7.8 / +12.7 / +15.2 / -4.4 -> +9.3 / +15.2 / +18.3 / -0.2 bp; no re-entry +24.7 / +30.3
/ +27.8 / +6.9 -> +26.8 / +34.0 / +31.6 / +13.4 bp), the 12-month-window variant's tally
(11 / 13 / 20 -> 10 / 14 / 20) and, with them, the committed-capital verdict (2 of 4 -> 3 of 4 on
the primary reading) and the sign-and-size tally (5 of 24 -> 7 of 24). The control run is the
invariant: with recalls off, 474 of 474 cohorts reproduce their cached `w1_trades.parquet` row for
row and the worst monthly gap is 0.00e+00 over 3,792 portfolio-months, so the deltas are the
rebuilt baseline's, not the recall simulation's. The primary block's marks are unchanged
(10 / 16 / 18), so the scored cells do not depend on which baseline generated the prose.

**Floors and the driver pin.** The stride-24 sample scorer covers Tables 1-3, 7 and the 43
factor-free row-15 cells and never runs the check step, so its `threshold` stays 110.0;
`full_sample.threshold` is 315.5 and `REPLICATION_FULL=1` needs the recall cache at the default
path. The driver's pinned hash in `scripts/rebuild_manifest.json` and `scripts/score_wrapper.py`
now names the previous `scripts/03_replicate.py`: those two files are outside this contract's
ownership, so the pin is left for the coordinator to refresh, and
`test_the_pin_matches_the_code_or_says_what_moved` skips (with that message) until it is. The
shared cache itself is untouched: the change adds a check-time reader, a typed constant, one
option and one make target.

**The cache this scored.** `.review/wt/score-E/.private/table9b-recalls` (474 cohort directories,
8 workers, 96 s of cohort building), built from the shared `vol_common` cache. Reproduce:

```
python scripts/claims/table9b_recalls.py run --workers 8 \
    --cache-root data/processed/replication/vol_common \
    --out-root data/processed/replication/vol_common_recalls
python scripts/03_replicate.py --universe vol_common --aggregate-only --workers 1 \
    --table9a-cache data/processed/replication/vol_common_top3 \
    --table9b-cache data/processed/replication/vol_common_recalls \
    --steps tables,table3,check
```

## 65. Table 6 (returns to random pairs) joins the scored set (2026-11-16): 297.5 -> 308.5

**What the paper says.** Section 3.6, p. 818: "In each bootstrap we replace the actual stocks
with two random securities with similar prior one-month returns as the stocks in the actual pair.
Similarity is defined as coming from the same decile of previous month's performance... We
bootstrapped the entire set of trading dates 200 times." The Table 6 caption (p. 819): "The
statistics are computed over 200 replications of the bootstrapped sample."

**What is scored: 48 cells.** Two panels (A no waiting, B wait one day) x two capital measures
(fully invested, committed) x three statistics (mean excess return, standard deviation, median) x
four portfolios (top 5, top 20, top 100-120, all 120), each the average over the 200 replications.
The values come from the per-cohort outputs of `scripts/claims/table6_random_pairs.py --mode run
--reps 200 --workers 8`, read through `--table6-cache` (default
`data/processed/replication/vol_common_t6`, which `make table6` rebuilds; `--table6-cache none`
leaves the section out) with the claim script's own reader, so the check and `TABLE6.md` cannot
drift apart. The scored design is the primary reading, `--close true`: each random position is
closed with the true trade it replaces (section 54).

**Marks, cell by cell (✓ 8 / ~ 6 / ✗ 34 = 11.0 of 48).** Columns are Top 5 / Top 20 /
Top 100-120 / All 120.

| row | Top 5 | Top 20 | Top 100-120 | All 120 |
|---|---|---|---|---|
| A, fully invested: mean | ✗ | ✗ | ✗ | ✗ |
| A, fully invested: std | ✗ | ✓ | ✓ | ~ |
| A, fully invested: median | ~ | ✗ | ✗ | ✗ |
| A, committed: mean | ✗ | ✗ | ✗ | ✗ |
| A, committed: std | ✓ | ✓ | ✓ | ✗ |
| A, committed: median | ✗ | ✗ | ✗ | ✗ |
| B, fully invested: mean | ~ | ✗ | ✗ | ✗ |
| B, fully invested: std | ✗ | ✗ | ~ | ~ |
| B, fully invested: median | ~ | ✗ | ✗ | ✗ |
| B, committed: mean | ✗ | ✗ | ✗ | ✗ |
| B, committed: std | ✓ | ✓ | ✓ | ✗ |
| B, committed: median | ✗ | ✗ | ✗ | ✗ |

**The comparability caveat.** The cells compare our own random draws with our own true-pair series
from the same cache, not the paper's random or true numbers: the paper's own table and its Table 1
sit on its data, ours on ours. So this is the least comparable block in the check -- the random
pairs' means are less negative than the paper's and their standard deviations less distinctive
relative to our true pairs -- and the marks are scored as printed nonetheless, because the paper
prints the numbers. The paper's Panel B fully-invested top-20 mean is -0.004% (typed -0.00004), so
that one cell reads harshly: the ratio of two near-zero means.

**The run and the cache.** `--mode control` reproduces the shipped monthly rows exactly on the #64
cache ("control summary: ... max_diff_shipped: 0.0", 5688 cells), so the engine path is the
shipped one. The bootstrap then ran 474 cohorts x 200 replications in eight subprocess shards
(398 s) into `data/processed/replication/vol_common_t6`, and `--mode report` regenerated
`claims/TABLE6.md` and `claims/TABLE6.csv`. The shared cache changed with #64 (committed capital is
the paper's literal sum of payoffs, SCORE_LOG row 18), so the regenerated values differ from the
committed ones in the 24 committed-capital cells (the fully-invested rows are unchanged): five
marks move, `A committed median top5`, `A committed std top120` and `B committed std top120` from
`~` to `✗`, `B committed median top5` from `✓` to `✗`, and `B committed std top5` from `~` to `✓`.
The committed report's 8 / 10 / 30 therefore becomes 8 / 6 / 34, and the 48 cells score 11.0
rather than the 13.0 the committed report would have given on the old cache.

**The smoke sample.** The stride-24 sample conformance neither builds nor scores Table 6: its
scorer covers Tables 1-3, 7 and the 43 factor-free row-15 cells, and its run never executes the
check step (the same exclusion-by-scope row 15's factor-dependent cells have), so the sample
threshold does not move. `REPLICATION_MAP.md` carries the 48 cells as class I.

**What the score does not say.** Scoring Table 6 does not change CLAIMS claim 3's verdict: the
random pairs still lose money in 12 of 16 series, sit below the true pairs in all 16 and their
difference still has t > 2 in all 16, which is what "replicated in substance" rests on.

## 66. Contract G score hunt (2026-11-16): SBBI unavailable, 73 borderline cells, no mark moves (326.0 of 625)

Contract G asked for mark gains that a skeptical reader cannot call reading-shopping. It found none,
and the clean negative is the deliverable: the score stays 326.0 of 625 (check 255 / tilde 142 /
cross 228) and no paper value, mark threshold or scored cell is touched.

**Lead 1, Ibbotson SBBI availability.** WRDS does not expose the Ibbotson SBBI monthly series to this
account: the authenticated entitlement probe (`report/data_review/B_results/B5d_entitlements.csv`,
2026-10) returned `SchemaNotFoundError` for both the `sbbi` and `ibbotson` libraries while all 13
other candidate libraries (`crsp`, `crsp_q_stock`, `crsp_q_mutualfunds`, `crsp_q_indexes`, `ff`,
`taqmsec`, `taqm_2020`-`taqm_2026`) were accessible, consistent with the earlier acquisition note
that SBBI is not on WRDS. Correction after review (the coordinator caught an imprecision here):
the bond legs need no re-sourcing at all - Goyal-Welch's `corpr` and `ltr` ARE Ibbotson's SBBI
bond series with documented provenance. That investigation and the download are the public
repository's work, inherited here (JaredCohen, 2026-10-10, origin/main commits 8b96686 and
61ce646: `IBBOTSON_DATA_SOURCES.md` records Goyal and Welch attributing both series to the SBBI
Yearbook, 475 clean months 1963-2002, vintages identical). What is
actually unavailable is only SBBI's own **small-company monthly series** and EnCorr's exact
extraction vintage: the documented route is Morningstar Direct's `IA SBBI US ...` series, which
needs a Uris or Manhattanville workstation or remote session that was not available, and the
public 1989 SBBI book prints its monthly exhibit as a bar chart, not a usable monthly table. The
block therefore keeps Ibbotson's true bond premia via Goyal-Welch plus the CRSP DFSCX
small-company rebuild (0.999 correlation with SBBI's published annuals), unchanged; the
re-sourcable upside is confined to the small-stock-premium loading cells.

**Lead 2, borderline audit.** Every scored cell of the committed `REPLICATION_CHECK.md` whose
displayed ours/paper ratio sits inside a 3-point window at a band edge (0.90-0.93 and 1.07-1.10 for
the 10% line, 0.75-0.78 and 1.22-1.25 for the 25% line) is listed below: 73 cells. For each, the
input that could move it is a shipped convention or an unavailable dataset, never a reading the
paper's text or printed numbers would prefer; switching any of them to move the mark would be
reading-shopping, which the contract forbids. None is defensible, so no mark moves.

| cell | ours / paper | ratio | gap | mark | input that could move it | defensible? |
|---|---|---|---|---|---|---|
| Figure 4 (top 20 against 101-120, correlations printed in the text) correlation, before 1989 [1] | 0.392 / 0.51 | 0.7686 | 23.14% | ~ | the five-factor residual frame and the 1988 split | no |
| Table 1 Panel A (no wait) mean (committed) [3] | 0.62 / 0.68 | 0.9118 | 8.82% | ✓ | the portfolio series and the shipped conventions | no |
| Table 1 Panel A (no wait) min [1] | -13.11 / -10.57 | 1.2403 | 24.03% | ~ | the portfolio series and the shipped conventions | no |
| Table 1 Panel A (no wait) min [2] | -7.25 / -6.63 | 1.0935 | 9.35% | ✓ | the portfolio series and the shipped conventions | no |
| Table 1 Panel B (one-day wait) mean (committed) [2] | 0.56 / 0.52 | 1.0769 | 7.69% | ✓ | the portfolio series and the shipped conventions | no |
| Table 1 Panel B (one-day wait) median [4] | 0.38 / 0.41 | 0.9268 | 7.32% | ✓ | the portfolio series and the shipped conventions | no |
| Table 1 Panel B (one-day wait) min [1] | -13.56 / -12.63 | 1.0736 | 7.36% | ✓ | the portfolio series and the shipped conventions | no |
| Table 1 Panel B (one-day wait) nw_se [1] | 0.11 / 0.12 | 0.9167 | 8.33% | ✓ | the portfolio series and the shipped conventions | no |
| Table 2 Panel A (one-day wait) avg_round_trips_per_pair [2] | 2.11 / 1.96 | 1.0765 | 7.65% | ✓ | the portfolio series and the shipped conventions | no |
| Table 2 Panel B (composition) avg_size_decile [3] | 3.15 / 3.41 | 0.9238 | 7.62% | ✓ | the portfolio series and the shipped conventions | no |
| Table 2 Panel B (composition) share_mixed_sector_pairs [3] | 0.403 / 0.44 | 0.9159 | 8.41% | ✓ | the portfolio series and the shipped conventions | no |
| Table 2 Panel B (composition) weight_transportation [3] | 0.0185 / 0.02 | 0.9250 | 7.50% | ✓ | the portfolio series and the shipped conventions | no |
| Table 2 Panel B (composition) weight_utilities [1] | 0.774 / 0.72 | 1.0750 | 7.50% | ✓ | the portfolio series and the shipped conventions | no |
| Table 2 Panel B (composition) weight_utilities [2] | 0.769 / 0.71 | 1.0831 | 8.31% | ✓ | the portfolio series and the shipped conventions | no |
| Table 3 Financials kurtosis [1] | 7.79 / 6.37 | 1.2229 | 22.29% | ~ | the sector series and the Table 1 conventions | no |
| Table 3 Financials std [1] | 2.79 / 2.6 | 1.0731 | 7.31% | ✓ | the sector series and the Table 1 conventions | no |
| Table 3 Financials std [3] | 2.15 / 2.36 | 0.9110 | 8.90% | ✓ | the sector series and the Table 1 conventions | no |
| Table 3 Financials t_stat [2] | 8.28 / 7.6 | 1.0895 | 8.95% | ✓ | the sector series and the Table 1 conventions | no |
| Table 3 Financials t_stat [3] | 7.78 / 7.12 | 1.0927 | 9.27% | ✓ | the sector series and the Table 1 conventions | no |
| Table 3 Financials t_stat [4] | 6.96 / 7.62 | 0.9134 | 8.66% | ✓ | the sector series and the Table 1 conventions | no |
| Table 3 Industrials max [3] | 10.66 / 11.62 | 0.9174 | 8.26% | ✓ | the sector series and the Table 1 conventions | no |
| Table 3 Industrials mean [1] | 0.6 / 0.49 | 1.2245 | 22.45% | ~ | the sector series and the Table 1 conventions | no |
| Table 3 Industrials share_negative [2] | 0.333 / 0.36 | 0.9250 | 7.50% | ✓ | the sector series and the Table 1 conventions | no |
| Table 3 Industrials t_stat [1] | 5.09 / 4.11 | 1.2384 | 23.84% | ~ | the sector series and the Table 1 conventions | no |
| Table 3 Industrials t_stat [4] | 5.86 / 7.52 | 0.7793 | 22.07% | ~ | the sector series and the Table 1 conventions | no |
| Table 3 Transportation kurtosis [2] | 3.87 / 5 | 0.7740 | 22.60% | ~ | the sector series and the Table 1 conventions | no |
| Table 3 Transportation median [2] | 0.42 / 0.55 | 0.7636 | 23.64% | ~ | the sector series and the Table 1 conventions | no |
| Table 3 Transportation share_negative [1] | 0.397 / 0.44 | 0.9023 | 9.77% | ✓ | the sector series and the Table 1 conventions | no |
| Table 3 Utilities max [3] | 13.34 / 12.13 | 1.0998 | 9.98% | ✓ | the sector series and the Table 1 conventions | no |
| Table 3 Utilities mean [1] | 0.98 / 0.91 | 1.0769 | 7.69% | ✓ | the sector series and the Table 1 conventions | no |
| Table 3 Utilities mean [2] | 1.16 / 1.08 | 1.0741 | 7.41% | ✓ | the sector series and the Table 1 conventions | no |
| Table 3 Utilities median [1] | 0.91 / 0.83 | 1.0964 | 9.64% | ✓ | the sector series and the Table 1 conventions | no |
| Table 3 Utilities median [2] | 1.03 / 0.94 | 1.0957 | 9.57% | ~ | the sector series and the Table 1 conventions | no |
| Table 3 Utilities min [1] | -13.56 / -12.35 | 1.0980 | 9.80% | ✓ | the sector series and the Table 1 conventions | no |
| Table 3 Utilities share_negative [1] | 0.308 / 0.28 | 1.1000 | 10.00% | ~ | the sector series and the Table 1 conventions | no |
| Table 3 Utilities t_stat [1] | 8.02 / 7.37 | 1.0882 | 8.82% | ✓ | the sector series and the Table 1 conventions | no |
| Table 4 (systematic risk, one-day wait) equity premium: serial_correlation [1] | 0.0465 / 0.05 | 0.9300 | 7.00% | ✓ | the pair series and the losers-only five-factor frame | no |
| Table 4 (systematic risk, one-day wait) ibbotson_default_premium [2] | 0.121 / 0.16 | 0.7562 | 24.38% | ~ | the Ibbotson SBBI inputs (unavailable; lead 1) | no |
| Table 4 (systematic risk, one-day wait) ibbotson_default_premium [3] | 0.156 / 0.168 | 0.9286 | 7.14% | ✓ | the Ibbotson SBBI inputs (unavailable; lead 1) | no |
| Table 4 (systematic risk, one-day wait) intercept [4] | 0.634 / 0.512 | 1.2383 | 23.83% | ~ | the pair series and the losers-only five-factor frame | no |
| Table 4 (systematic risk, one-day wait) momentum [2] | -0.0437 / -0.0482 | 0.9066 | 9.34% | ✓ | the pair series and the losers-only five-factor frame | no |
| Table 4 (systematic risk, one-day wait) sharpe [4] | 0.407 / 0.45 | 0.9044 | 9.56% | ✓ | the pair series and the losers-only five-factor frame | no |
| Table 5 Panel A (monthly value at risk) serial_correlation [1] | 0.128 / 0.14 | 0.9143 | 8.57% | ✓ | the portfolio series and the shipped conventions | no |
| Table 5 Panel A (monthly value at risk) var_1 [3] | -2.749 / -2.236 | 1.2294 | 22.94% | ~ | the portfolio series and the shipped conventions | no |
| Table 5 Panel A (monthly value at risk) var_1 [4] | -2.17 / -1.994 | 1.0883 | 8.83% | ✓ | the portfolio series and the shipped conventions | no |
| Table 5 Panel A (monthly value at risk) var_5 [2] | -1.098 / -1.002 | 1.0958 | 9.58% | ✓ | the portfolio series and the shipped conventions | no |
| Table 7 (long and short books, one-day wait) long: r2 [2] | 0.439 / 0.48 | 0.9146 | 8.54% | ✓ | the book series and the reversal frame | no |
| Table 7 (long and short books, one-day wait) long: standard deviation [4] | 5.66 / 5.16 | 1.0969 | 9.69% | ✓ | the book series and the reversal frame | no |
| Table 7 (long and short books, one-day wait) long: standard error (Newey-West) [4] | 0.27 / 0.25 | 1.0800 | 8.00% | ✓ | the book series and the reversal frame | no |
| Table 7 (long and short books, one-day wait) short: mean monthly return [2] | 0.47 / 0.43 | 1.0930 | 9.30% | ✓ | the book series and the reversal frame | no |
| Table 7 (long and short books, one-day wait) short: mean monthly return [3] | 0.72 / 0.66 | 1.0909 | 9.09% | ✓ | the book series and the reversal frame | no |
| Table 7 (long and short books, one-day wait) short: standard deviation [1] | 3.55 / 3.26 | 1.0890 | 8.90% | ✓ | the book series and the reversal frame | no |
| Table 7 (long and short books, one-day wait) short: standard deviation [2] | 3.4 / 3.16 | 1.0759 | 7.59% | ✓ | the book series and the reversal frame | no |
| Table 7 (long and short books, one-day wait) short: standard deviation [4] | 4.98 / 4.6 | 1.0826 | 8.26% | ✓ | the book series and the reversal frame | no |
| Table 8 (subperiod analysis) post_market [4] | -0.0752 / -0.0696 | 1.0805 | 8.05% | ✓ | the reversal frame and the 1988-12 split | no |
| Table 8 (subperiod analysis) post_momentum [3] | -0.0797 / -0.0884 | 0.9016 | 9.84% | ✓ | the reversal frame and the 1988-12 split | no |
| Table 8 (subperiod analysis) post_r2 [4] | 0.692 / 0.64 | 1.0812 | 8.12% | ✓ | the reversal frame and the 1988-12 split | no |
| Table 8 (subperiod analysis) post_reversal [1] | -0.0767 / -0.0626 | 1.2252 | 22.52% | ~ | the reversal frame and the 1988-12 split | no |
| Table 8 (subperiod analysis) post_std [3] | 1.375 / 1.121 | 1.2266 | 22.66% | ~ | the reversal frame and the 1988-12 split | no |
| Table 8 (subperiod analysis) pre_mean [4] | 0.896 / 0.992 | 0.9032 | 9.68% | ✓ | the reversal frame and the 1988-12 split | no |
| Table 9 Panel A (top three size deciles, one-day wait) max [1] | 9.24 / 10.14 | 0.9112 | 8.88% | ✓ | the portfolio series and the shipped conventions | no |
| Table 9 Panel A (top three size deciles, one-day wait) mean [1] | 0.9 / 0.83 | 1.0843 | 8.43% | ✓ | the portfolio series and the shipped conventions | no |
| Table 9 Panel A (top three size deciles, one-day wait) mean [3] | 0.66 / 0.73 | 0.9041 | 9.59% | ✓ | the portfolio series and the shipped conventions | no |
| Table 9 Panel A (top three size deciles, one-day wait) median [3] | 0.56 / 0.61 | 0.9180 | 8.20% | ✓ | the portfolio series and the shipped conventions | no |
| Table 9 Panel A (top three size deciles, one-day wait) median [4] | 0.55 / 0.51 | 1.0784 | 7.84% | ✓ | the portfolio series and the shipped conventions | no |
| Table 9 Panel A (top three size deciles, one-day wait) min [3] | -4.65 / -3.8 | 1.2237 | 22.37% | ~ | the portfolio series and the shipped conventions | no |
| Table 9 Panel A (top three size deciles, one-day wait) nw_se [2] | 0.11 / 0.1 | 1.1000 | 10.00% | ~ | the portfolio series and the shipped conventions | no |
| Table 9 Panel A (top three size deciles, one-day wait) t_stat [3] | 8.78 / 9.66 | 0.9089 | 9.11% | ✓ | the portfolio series and the shipped conventions | no |
| Table 9 Panel B (short recalls on high volume, one-day wait) kurtosis [2] | 5.57 / 6 | 0.9283 | 7.17% | ✓ | the portfolio series and the shipped conventions | no |
| Table 9 Panel B (short recalls on high volume, one-day wait) min [2] | -7.17 / -6.59 | 1.0880 | 8.80% | ✓ | the portfolio series and the shipped conventions | no |
| Table 9 Panel B (short recalls on high volume, one-day wait) nw_se [3] | 0.1 / 0.08 | 1.2500 | 25.00% | ~ | the portfolio series and the shipped conventions | no |
| Table 9 Panel B (short recalls on high volume, one-day wait) std [3] | 1.84 / 1.5 | 1.2267 | 22.67% | ~ | the portfolio series and the shipped conventions | no |
| Table 9 Panel B (short recalls on high volume, one-day wait) std [4] | 1.67 / 1.55 | 1.0774 | 7.74% | ✓ | the portfolio series and the shipped conventions | no |

**Lead 3, `OPEN_QUESTIONS.md` "Not shipped" revisited.** The highest old-base gains were re-read
against their rejection reasons:
- the fitted trigger constant `c = 1e-4` (176.5 on the round-six base) rests on a free parameter
  fitted to Table 2's trigger, which no paper text or printed number anchors: rejected as a fit, not
  on data availability, so it stays rejected;
- dropping Nasdaq after 1985 (174.0 on the row-7 base) has no support in either edition and worsens
  the sector counts and Table 2 marks: stays rejected;
- payoff counts (184.5 on row 12's 183.5) contradict the paper's "daily returns compounded" and the
  Table 1 = Table 7 identity: stays rejected;
- the closed PR #36 count/book hybrid (185.0) mixes two return definitions with no text anchor: stays;
- the gross-book base (184.5) has no anchor either: stays.
Every rejection was about defensibility, not data availability, so none may be retried under contract
G. The one data-availability lever, the true pre-1982 SBBI series, is lead 1, and the data is still
unavailable. `OPEN_QUESTIONS.md` records the borderline cells and this re-evaluation under "Not
shipped".

**What a mark gain would have needed.** The 73 cells sit within 2.2-3 points of an edge in ratio
terms, but every edge that pays the second half-point is on the far side of a 10-16 point move (1.10 to 1.00, or
1.25 to 1.10), not a rounding or convention difference. The only cells close to an edge in the paying
direction are the 54 already marked check, which the audit treats as fragile, not improvable.

**Verification.** No code, paper value, mark rule or check section changed: the committed check still
parses to 326.0 of 625 with 255 / 142 / 228, the test suite and `make verify-targets` are unaffected,
and the manifest needs no re-pin because no pinned file moved.

## 67. The printed regression t-statistics of Tables 4, 7 and 8 join the scored set (2026-11-16): 326.0 -> 352.0; 367.0 -> 393.0 of 849 on main

The paper prints Newey-West t-statistics for every regression coefficient: Table 4 in parentheses
beside each coefficient (p. 814, five-factor block and Ibbotson block), Table 7 on a t-Statistic row
under each of six coefficients for each book (p. 821), and Table 8 on a t-Statistic row under each
coefficient per panel (p. 822). Its notes fix the estimator: six Newey-West lags. The driver already
computed all of them (`factor_tstats`, no small-sample correction, the paper's statement); they were
printed beside the paper's values and not counted. Contract H scores all 140: Table 4 24 + 20,
Table 7 48, Table 8 48. The typed values are PAPER_TABLE4_T, PAPER_TABLE8_T and the existing
PAPER_TABLE7_T, and `verify_paper_targets.py` re-reads every one from the PDF text layer (Table 4 t
24 + Ibbotson t 20, Table 7 t 48, Table 8 t 48), so a typo cannot survive `make verify-targets`.
The unscored 'alpha t-statistic' rows and the Table 7 '(unscored)' t rows are gone; the ST_Rev
alternative sections print their t rows unscored beside their coefficients.

**What moved.** On main (after #71 and #72) the total rises 367.0 -> 393.0 of 849 cells (check 304 /
tilde 178 / cross 367); on the branch's first base it was 326.0 -> 352.0 of 765. The 709 existing marks
are unchanged. The 140 new cells score 15 / 22 / 103 = 26.0: Table 4
27 / 23 / 54 of 104 (the 44 t cells 8 / 9 / 27), Table 7 36 / 18 / 82 of 136
(t cells 5 / 6 / 37), Table 8 16 / 22 / 82 of 120 (t cells 2 / 7 / 39). The intercept t rows
move most: our alphas are larger and more significant than the paper's (top 5 6.66 against 3.81),
so the t block inherits the coefficient misses rather than adding a new defect. The Ibbotson t
rows are the exception: 7 check / 3 tilde / 10 cross of 20.

Cell-by-cell marks of the 140 new cells (✓ within 10%, ~ within 25%, ✗ beyond):

**Table 4, five-factor t (class C)**

| row | top 5 | top 20 | 20 after top 100 | all |
|---|---|---|---|---|
| intercept | ✗ | ~ | ✗ | ✗ |
| market | ✗ | ~ | ~ | ✗ |
| smb | ✗ | ✗ | ✗ | ✗ |
| hml | ✗ | ✗ | ✗ | ✗ |
| momentum | ✗ | ~ | ✓ | ~ |
| reversal | ✗ | ✗ | ~ | ✗ |

**Table 4, Ibbotson t (class G)**

| row | top 5 | top 20 | 20 after top 100 | all |
|---|---|---|---|---|
| ibbotson_intercept | ✓ | ✓ | ✓ | ✓ |
| ibbotson_market | ✗ | ✗ | ~ | ✗ |
| ibbotson_small_premium | ✗ | ✗ | ✗ | ~ |
| ibbotson_default_premium | ✗ | ✓ | ~ | ✓ |
| ibbotson_horizon_premium | ✓ | ✗ | ✗ | ✗ |

**Table 7, book t-statistics (class C)**

| row | top 5 | top 20 | 20 after top 100 | all |
|---|---|---|---|---|
| long: intercept | ✗ | ✗ | ✗ | ✗ |
| long: market | ✗ | ✗ | ✗ | ~ |
| long: smb | ✗ | ✗ | ✗ | ✗ |
| long: hml | ✗ | ~ | ✓ | ✗ |
| long: momentum | ✓ | ✗ | ✗ | ✗ |
| long: reversal | ✗ | ✗ | ✗ | ✗ |
| short: intercept | ✓ | ~ | ✗ | ✓ |
| short: market | ~ | ✓ | ✗ | ✗ |
| short: smb | ✗ | ✗ | ✗ | ✗ |
| short: hml | ✗ | ~ | ~ | ✗ |
| short: momentum | ✗ | ✗ | ✗ | ✗ |
| short: reversal | ✗ | ✗ | ✗ | ✗ |

**Table 8, subperiod t-statistics (class A pre, C post except 101-120)**

| row | top 5 | top 20 | 20 after top 100 | all |
|---|---|---|---|---|
| pre_intercept | ✗ | ✗ | ✗ | ✗ |
| pre_market | ✗ | ✗ | ✗ | ~ |
| pre_smb | ✗ | ~ | ✗ | ✗ |
| pre_hml | ✗ | ✗ | ~ | ✓ |
| pre_momentum | ✗ | ✗ | ✗ | ✗ |
| pre_reversal | ✗ | ✗ | ✗ | ~ |
| post_intercept | ✓ | ~ | ✗ | ✗ |
| post_market | ✗ | ✗ | ✗ | ~ |
| post_smb | ✗ | ✗ | ✗ | ✗ |
| post_hml | ✗ | ✗ | ✗ | ✗ |
| post_momentum | ✗ | ✗ | ✗ | ~ |
| post_reversal | ✗ | ✗ | ✗ | ✗ |

The sample smoke scores the same tables without factor data and does not include the t rows,
so its threshold stays 110.0. `paper_cells.json` carries the 140 values, the conformance threshold
is 393.0 and `test_score_wrapper.py` expects 849 cells; the manifest is re-pinned to the code that
produced this check.

**Census.** The t-statistics join their coefficients' classes in `REPLICATION_MAP.md`: C +90 (Tables 4
and 7, and Table 8 after 1988 except the 101-120 column; 7 / 15 / 68 = 14.5), A +30 (Table 8 before
1989 and its 101-120 column after 1988; 1 / 4 / 25 = 3.0), G +20 (Ibbotson; 7 / 3 / 10 = 8.5). The
first version of this census gave class C 37.0 points for 21 / 34; 21 + 34/2 is 38.0, which is the
value used now.

**The row-14 subset line.** Since #68 the summary line "Tables 1-3 and 7 alone" counted all of
Table 7, the regression block included (222.5 of 379), although SCORE_LOG row 14 defines that set
as Tables 1-3 and Table 7's 32 performance cells. It now counts exactly that set: 212.0 of 323. No
scored cell changes; the line is a subset tally only.

**Rebased onto main after #72 (2026-11-17, coordinator).** The code commits rebased cleanly (the
driver keeps Table 6, Table 5 Panel B and the keyword `fmt_spec=`; `paper_cells.json` keeps main's 20
sections and adds the t values to Tables 4, 7 and 8). The check was regenerated from the format-7
shared cache with the 9 A, 9 B and Table 6 side caches, not hand-merged: against main's committed
check the only lines that differ are the summary block, the t rows (unscored before, scored now) with
their section notes, and the derived ST_Rev totals.

## 68. The last printed numbers join the scored set, and the coverage inventory is full (2026-11-16): 326.0 -> 339.0; 393.0 -> 406.0 of 865 on #74

Contract I. The paper's remaining result numbers are scored now: Table 8's published "Factor sd"
column (10 cells), the captions' pairs per cohort (1), section 1.2's hold-out sentence (3) and
footnote 4's delisting result (2), 16 cells in all, 13.0 points, and the total moves 326.0 ->
339.0 of 641 (SCORE_LOG row 23 (26 at merge) on this branch; 625 -> 641 cells). The 16 marks: the 10 factor SDs 9 / 0 / 1
(the reversal's after-1988 cell is the miss), the pairs count check, the hold-out 0 / 2 / 1, and
footnote 4 both check.

**Plumbing.** `write_risk_tables` writes `table8_factor_sd.csv` (the sample standard deviation,
ddof 1, of each column of the driver's scored factor frame over the two Table 8 panels' own
months, so the reversal column follows `--reversal-factor`); `write_outputs` writes
`holdout_1999.csv` (both waits); the check step reads footnote 4 from a second cache through the
new `--delist-cache <dir>` (default `data/processed/replication/vol_common_delist100`, `none`
leaves the two cells out, an absent or unstamped cache stops with the build command) and
`make delist100` builds it with `--long-delisting-loss`. The two prose numbers are typed as
`PAPER_HOLDOUT` and `PAPER_FOOTNOTE4`, and `verify_paper_targets.py` re-reads all four sentences
from the PDF text layer (`text_numbers`: pairs, the hold-out's three, footnote 4's two; 44 Table 9
Panel B values still compare too).

**The readings.** The hold-out is scored on the no-wait rule: "Using the original model" (p. 800)
is the base rule, and REVIEW_NOTES 58 had recorded that reading before these cells existed; the
one-day-wait reading prints on the line below, unscored. Annual figures are 12 times the monthly
mean and sqrt(12) times the monthly standard deviation, and the t-statistic is the six-lag
Newey-West t of the monthly mean -- the paper prints no annualisation formula, and this is the
one its own Table 1 uses monthly. The factor SDs measure the factor inputs, not the replication:
the first four match French's series to three decimals (REVIEW_NOTES 49) and the reversal cell is
the hypothesis of section 61 (the losers-only series), which is why its after-1988 value is the
one that misses (0.06857 against 0.04448; before 1989 it is 0.06852 against 0.07228, within 10%).

**The 641.** 629 of the cells are table cells, 6 Figure 4 and 6 these printed-text numbers; the
check prints 267 check / 144 tilde / 230 cross for 339.0. The previously scored cells are
byte-identical: the regenerated check differs from the committed one only in the summary lines,
the new rows, the new section and the unscored sentence that quotes the alternative reversal
reading's what-if total.

**The inventory.** `COVERAGE.md`'s index now states printed / scored / excluded counts for every
table, figure and printed text number, with the exclusion reason (duplicate, derived, image), and
a "How the numbers reconcile" section: 893 printed result numbers = 641 scored here + 224 pending
(Table 6's 48, PR #71; Table 5 B's 36, C2; contract H's 140 t-statistics) + 28 duplicates;
881 = 853 + 28 inside the tables, and 865 is the inventory's full-coverage total once those
contracts land. The four stale detail paragraphs (Tables 5 B, 6, 8 and 9 B) were brought to their
current state.

**CLAIMS.md deduplicated.** The two copies were identical through all 25 rows except row 19:
copy A read 19 / 16 / 9 for Table 9 A, copy B 22 / 10 / 12. Copy B matches SCORE_LOG row 19, so
every row (1-3 and 5-25, no claim 4 exists) is taken from copy B; the six "How to read the
verdicts" paragraphs are taken from copy A, because the merge cut copy B's tail off at that
heading. The jammed title line was split into its heading and its lead paragraph. One ledger now.

**Conformance and census.** `full_sample.threshold` is 339.0 and its note gains row 23 (26 at merge). The
sample note's triplicated sentence ("Table 7's 56 regression cells ... excluded from the sample")
is kept once, with a sentence saying contract I's 16 cells sit outside the stride-24 sample too
(the factor files and the delist100 cache are not part of the sample run), so the sample
threshold stays 110.0. `REPLICATION_MAP.md`'s census is regenerated to the row-26 base: F grows
259 -> 300 cells (240.5 points, 80%), D 124 -> 140, E 11 -> 14, and the totals 267 / 144 / 230 =
339.0; section 6's two numbers and section 7's rows follow.

**Manifest.** `scripts/03_replicate.py` changed, so both copies of the pin
(`scripts/rebuild_manifest.json` and `score_wrapper.PINNED_MANIFEST`) are re-pinned to its final
sha256 after the last verification run, as ADDENDUM_R2 section 3 requires.

Reproduce (the shared caches are read-only):

```
python scripts/03_replicate.py --universe vol_common --aggregate-only --workers 1   --cache-root data/processed/replication/vol_common   --table9a-cache data/processed/replication/vol_common_top3   --table9b-cache data/processed/replication/vol_common_recalls   --delist-cache data/processed/replication/vol_common_delist100   --steps tables,table3,figure1,check
```

**Rebased onto contract H (PR #74), 2026-11-17, coordinator.** The branch was written on the
pre-#71 base (326.0 of 625) and is rebased onto H's 080c9e4 (393.0 of 849). The code merged with
both sides kept: `write_replication_check` takes `table6` and `delist100` (passed by keyword), the
Makefile keeps `table6` and `delist100`, `verify_paper_targets.py` runs both the Table 6 and the
text parsers, and `paper_cells.json` keeps H's 20 sections and adds the five Table 8 factor-SD rows
and the "Numbers printed in the text" section. The check was regenerated from the format-7 shared
cache with the 9 A, 9 B, Table 6 and delist100 side caches: 406.0 of 865 (✓ 316, ~ 180, ✗ 369),
and all 849 earlier marks are unchanged. The ledgers were re-applied on H's: SCORE_LOG row 26, the
census, COVERAGE, CLAIMS (one copy, with main's later claim-15 and Table 5 B edits), the
conformance note (one copy of the triplicated sentence) and the totals. One census change from the
first version: the two reversal-factor standard deviations sit in class C, the reversal-factor
class, not class F, so F gains 11 cells (11 / 0 / 0), C 2 (1 / 0 / 1) and E 3 (0 / 2 / 1).

## 69. Table 6's four open readings, measured (2026-11-16): 337.0 -> 337.0 (investigation)

Table 6's 48 cells are the widest miss in the check (8 / 6 / 34 against the paper, PR #71), and
they miss in two patterns: our fully-invested random losses are 2-3 times the paper's although
the standard deviations match, and the paper's committed means are 0.6-0.85 of its
fully-invested means in every column while ours are near zero. `claims/TABLE6_READINGS.md`
measures the four conventions the paper does not pin down, one switch each on
`scripts/claims/table6_random_pairs.py`, with the shipped behaviour as every default so
`--mode control` still reproduces the cache exactly (`max_diff_shipped` 0.0, 948 cohort-waits,
5,688 cells, re-run after the change). Nothing ships: the scored check and SCORE_LOG are
unchanged, which is why this section moves the total 337.0 -> 337.0.

**The control's vector-layer line.** The regenerated `claims/logs/TABLE6_control.log` prints
`max_diff_vector_layer` 0.173, where the log committed on 2026-11-02 printed 1.3e-15. The log
predates SCORE_LOG row 18, which made the shipped committed series the literal payoffs, while
`t6_engine.book_months` (the vectorised cross-check) still builds committed as the book scaled by
`n_open / N`, which is reading 1's book-share: the gap is committed-only (employed agrees to 4e-16
on 1999-09), and no scored number uses the vector layer. The same comparison confirms reading 1
independently: book-share computed through `monthly_series` with an empty trade log and through
the vector layer agree to 2-4e-16 on four cohort-waits (1999-09 both waits, 1975-01 and 1963-07;
coordinator check).

| reading | option | 48-cell score | the paper's words | verdict |
|---|---|---|---|---|
| shipped control | defaults | 11.0 (8 / 6 / 34) at 200 reps, `vol_common_t6` | - | baseline |
| committed capital = value-weighted book x share open | `--committed-capital book-share` | 13.0 (8 / 10 / 30) at 200, `<scratch>/book200` | "value-weighted portfolios of n pairs" (caption, p. 819) | supported: restores 0.69-0.76 at every column where the shipped literal series gives -0.01 to 0.16; +2.0 |
| random stocks from the whole panel | `--pool panel` | 15.5 (12 / 7 / 29) at 200, `<scratch>/panel200` | "two random securities" (text, p. 818) | mixed: committed means then match the paper, fully-invested means move further away; +4.5 |
| last month = 21 trading days before the open | `--prior-month trading` | 11.0 (7 / 8 / 33) at 50, `<scratch>/prior50` | "previous month's performance" (text) against "on the day the position is opened" (caption) | contradicted: no gain, and columns 2-4 drift further |
| statistics pooled over replications | `--stats pooled` | unchanged in every configuration | "computed over 200 replications" (caption) | neutral: means identical, sd within 2.2%, medians within 0.07 bp |

**The committed reading is the one the text supports.** The caption calls the portfolios
"value-weighted ... of n pairs", and the paper's committed/fully-invested ratio (0.606 / 0.694 /
0.848 / 0.805 for the fully-invested denominator, and the same 0.6-0.85 in its Table 1) is what
a value-weighted book scaled by the share of pairs open produces: 0.759 / 0.687 / 0.752 / 0.705
on our draws at 200 replications. The shipped literal series (`sum_p pi_p,t / N selected`,
SCORE_LOG row 18) collapses in Table 6 alone because a replication that draws a security with no
data after the open dilutes the mean by the withdrawn pairs and can flip its sign; the same
definition is right for Tables 1, 3 and 9 A, which is why our Table 1 ratio (0.60-0.66) matches
the paper's there. A committed-cell-only change would add 2.0 points.

**The pool reading scores higher but is not supported.** Drawing from every common CRSP stock in
the trading window fixes the committed level (-0.00084 against -0.00083 in the top five) but
doubles the fully-invested losses (-0.0041 against the paper's -0.0014, sd 0.047 against 0.055),
so it gains 4.5 points while moving the central column the wrong way. The text names no pool, so
this should not ship on the score alone.

**What is left.** Fact (a) survives all four readings: our random pairs lose steadily while the
paper's lose about half as much per month, with the same dispersion. What could explain it is not
a reading of a sentence but a detail of the draw (uniform over the decile, as shipped, against a
distance- or size-weighted draw) or of the accounting (what happens when a drawn leg stops
trading, which the current run treats as a forced exit at the last available row). Those are
recorded as the next experiment, not adopted.

**Reproduce.** Each switch is one flag on the claim script; the doc names every run directory:

    python scripts/claims/table6_random_pairs.py --mode run --reps 200 --workers 8 \
      --cache-root <R>/vol_common --out-root <scratch>/book200 --committed-capital book-share
    python scripts/claims/table6_random_pairs.py --mode control --cache-root <R>/vol_common

`--mode control` must print `max_diff_shipped: 0.0`; the 48-cell tallies are read with the
check's own `_mark` rule against `scripts/claims/table6_paper.json`.


## 70. The denominator is the paper: 865 cells, pinned by a test (2026-11-17): 406.0 -> 406.0

The scored cell set moved with almost every row of SCORE_LOG (291, 323, 481, 525, ... 849), so a
score was only comparable with the rows that shared its cell set. With rows 25 and 26 the check
scores every distinct number the paper prints about its results, and this section fixes that
set. Nothing in the check moves; the score stays 406.0 of 865.

**The count.** `scripts/paper_ceiling.py` re-counts the values of the nine tables from the
article's text layer (`pdftotext -layout`): 88 / 64 / 139 / 116 / 72 / 48 / 136 / 130 / 88 = 881.
A value is a token with a decimal point or a trailing percent sign; the stated corrections are
Table 5's quantile labels (labels, not values) and Table 3's caption, which prints the four
stocks-per-sector counts (156 / 61 / 371 / 1729, p. 812). The text layer renders the minus sign
as an en dash or "7" and puts each t-statistic in "(-1.03)" beside its coefficient; both are
values. With Figure 4's six correlations (pp. 822-823) and the six numbers of the "Numbers printed
in the text" block (the hold-out, p. 800; footnote 4, p. 804; the captions' 2057 pairs) the paper
prints 893 result numbers. 28 repeat a scored cell (Table 4's means, standard deviations and
serial correlation, 12; Table 5 Panel A's mean, standard deviation, loss probability and minimum,
16), so 865 are distinct, and the check scores exactly those.

**The rest of the text.** A sweep of every result-like number outside the tables (percentages,
decimals, basis-point and month counts) found 78, recorded in the manifest with page, quotation
and status: 12 scored, 42 duplicates of table cells, 17 derived from table cells (tested in
`CLAIMS.md`), 5 rule parameters and 2 other studies' estimates. The first hand inventory had
listed the derived numbers by section and had missed two of them, the abstract's "11%" (pp.
797-798) and the 30-55 / 20-35 bp drops (p. 808); neither changes the ceiling, since derived
numbers are not scored.

**The lock.** `tests/test_ceiling.py` fails when the manifest and the article disagree (the
re-count, skipped without `pdftotext`), when a block's printed count is not its scored plus its
duplicate cells, or when the committed check's `Cells: N` for any block, or its score line's
total, differs from the manifest. A negative control (Table 6 edited to 47 cells) fails with
"Table 6: the check scores 47 cells, the manifest 48". From here on a PR moves the numerator only.

**A page citation.** Table 5 is printed on p. 815; p. 816 is the page of the text that discusses
it (the VaR sentences). `COVERAGE.md` and `CEILING.md` give the table's page; the sections and
rows that quote those sentences keep p. 816, which is right for the quotations.

## 71. One home per fact: the replication folder restructured to seven pages (2026-11-17): 406.0 -> 406.0 (docs)

Contract L, take 2 (an earlier partial restructure worked in an ephemeral scratch session and
nothing landed). Thirteen hand-maintained pages had drifted apart: REPLICATION_SUMMARY.md and
outputs/README.md still said 261.0 of 481, CLAIMS quoted a 261.0-era check, PAPER_CONSISTENCY's
tail said 267.5 of 481, and only SCORE_LOG and the ceiling were test-guarded. The folder is now
seven pages with one home per fact, and the numbers that pages quote are generated from the
check:

- **README.md** (from REPLICATION_SUMMARY; git mv): thesis, a generated stamp line and a
  generated marks column in the exhibit table, the factor argument, the four causes, the page
  map, reproduce. The claims checklist moved out (its home is CLAIMS.md).
- **REPLICATION_CHECK.md**: unchanged in every mark (406.0 of 865); its header's two doc-name
  lines now name GAPS.md, regenerated from the rebuilt shared cache and byte-identical otherwise
  (verified by regenerating the full check from the cache before and after the edit).
- **SCORE_LOG.md**: rows 24/25/26 PR columns set to #72/#74/#76; CEILING/PAPER_CONSISTENCY/
  OPEN_QUESTIONS pointers repointed.
- **CLAIMS.md**: refreshed. Verdicts cite check rows ("check, Table 4, intercept and t rows")
  instead of copying ours/paper pairs, and a claims-to-cells map folds in the claim-to-evidence
  index that used to live in the summary page.
- **COVERAGE.md**: COVERAGE + CEILING merged (the reconciliation section and the ceiling are one
  section now); the "scored" column of its exhibit table is generated.
- **METHOD.md** (INTERFACES + PAIR_FORMATION + RULE_PROVENANCE merged): the rule row by row with
  the paper's words, then the formation detail, then the historical working interface marked
  historical where it differs (sigma, the wait, book compounding). Heading demotion skipped
  code-fenced lines, so the python comments in the API listing are untouched.
- **GAPS.md** (REPLICATION_MAP + OPEN_QUESTIONS tracker + PAPER_CONSISTENCY + the reversal
  audit's findings): the census by cause, the Q1-Q12 tracker with graph and evidence, the
  paper's own arithmetic (old PAPER_CONSISTENCY sections 1-8), and the audit's three findings.
  The dated cross-check and experiment rounds moved verbatim to archive/OPEN_QUESTIONS_ROUNDS.md.
- Machine artifacts: paper_consistency.json and the reversal-factor audit record now live in
  analysis/ (`scripts/audit_reversal_factor.py` and `scripts/paper_consistency.py` repointed).
  claims/TABLE6_control.log moved to claims/logs/; the unreferenced TABLE6_run.log and the
  duplicate report/replication/figure1.png (identical md5 to outputs/figures/figure1.png) are
  dropped.
- **outputs/** regenerated by the new `make outputs` (driver aggregate + figures +
  `scripts/docs_sync.py --outputs`): the committed tables are the current 406.0 base for the
  first time since 11-03, and the previously missing daily-VaR, factor-SD, hold-out and
  Table 7 alternative tables are in. `tests/test_docs_pages.py` pins the generated parts to
  the check (stamp, exhibit columns, scored column, outputs stamp; docs_sync is idempotent).

Infrastructure: the shared cache at data/processed/replication/vol_common had a stale
format-6 stamp at cohorts/cache_meta.json (and an orphaned wrong-level cache_meta.json, now
deleted); it was rebuilt with --force from f33a1cc code, re-stamped format 7 by the driver, and
the regenerated check is byte-identical to the committed one. scripts/03_replicate.py's doc-name
strings changed (INTERFACES/PAPER_CONSISTENCY/OPEN_QUESTIONS -> METHOD/GAPS), so
rebuild_manifest.json and score_wrapper's PINNED_MANIFEST are re-pinned together after an
aggregate-only verification run against the rebuilt cache. Rename map for older sections of
these notes and the archived rounds: REPLICATION_SUMMARY -> README, INTERFACES/PAIR_FORMATION/
RULE_PROVENANCE -> METHOD, REPLICATION_MAP/OPEN_QUESTIONS/PAPER_CONSISTENCY/REVERSAL_FACTOR_AUDIT
-> GAPS (sections) and analysis/reversal_factor_audit.md, CEILING -> COVERAGE's ceiling section.
Old names in REVIEW_NOTES sections 1-70 are historical and left as written.

## 72. The factors are French's 2005 files, the vintage the paper had (2026-11-17): 406.0 -> 406.0

Every regression in Tables 4, 7 and 8 runs on French's factors as downloaded today, and French
has revised them since the paper was written (HML in 2015, market and momentum in the annual
CRSP refreshes). The paper's own text fixes which vintage it used: the four series are "the
three factors of Fama and French (1996), augmented by two additional factors" taken from
Kenneth French's data library (section 2.5, p. 814), and Table 8 prints each factor's standard
deviation per panel (p. 822) - a measurement of the factors alone, not of the pairs. Only the
pre-publication files reproduce that column. The check now reads those files
(`data/raw/french_vintage_2005`), and `--factor-vintage current` restores today's.

**The evidence.** The Internet Archive's captures, before the RFS Advance Access of February
2006:

| file | Wayback timestamp | member date | first line |
|---|---|---|---|
| `F-F_Research_Data_Factors.zip` | 20050930202651 | 2005-09-22 | "created by CMPT_ME_BEME_RETS using the 200508 CRSP database" |
| `F-F_Momentum_Factor.zip` | 20051029233931 | 2005-10-21 | "created by CMPT_ME_PRIOR_RETS using the 200509 CRSP database" |

URL form `https://web.archive.org/web/<timestamp>id_/http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/<file>`;
both are committed whole, not as Git LFS, with url, timestamp, member date, first line and
sha256 in `data/raw/french_vintage_2005/PROVENANCE.md`
(`1b6d305a…` and `d9688cd1…`). The 2005 archives are in French's pre-2006 plain-text layout:
whitespace columns, momentum named `UMD`, a monthly block ended by an annual one;
`project.factors._txt_monthly_block` reads it.

**Table 8's "Factor sd" column (p. 822), the paper against both vintages.** The windows are the
two panels' own months (1963-07..1988-12 and 1989-01..2002-12), the check's rule:

| factor | paper pre | today pre | 2005 pre | paper post | today post | 2005 post |
|---|---|---|---|---|---|---|
| market | 0.04580 | 0.04595 (+0.3%) | 0.04580 (-0.0%) | 0.04390 | 0.04449 (+1.3%) | 0.04407 (+0.4%) |
| SMB | 0.02923 | 0.02919 (-0.1%) | 0.02920 (-0.1%) | 0.03856 | 0.03885 (+0.7%) | 0.03887 (+0.8%) |
| HML | 0.02597 | 0.02601 (+0.1%) | 0.02610 (+0.5%) | 0.03641 | 0.03359 (**-7.7%**) | 0.03644 (**+0.1%**) |
| momentum | 0.03506 | 0.03497 (-0.3%) | 0.03500 (-0.2%) | 0.04926 | 0.04941 (+0.3%) | 0.04937 (+0.2%) |

HML after 1988 is the one cell that separates the vintages: today's revised HML has a standard
deviation 7.7% below the printed one, the 2005 file 0.1% above. `tests/test_factors.py::test_2005_loader_reproduces_the_paper_factor_sd`
holds the eight values to 1%. This is independent, non-fitted evidence: the column measures the
factors, not our pairs, and it was printed in 2006.

**What the vintage does to the marks.** Nine of the 865 cells move, and the total does not:
Table 7 -1.0, Table 4 +0.5, Table 8 +0.5. Runs: `<scratch>/.private/out` (2005, the shipped one)
and `<scratch>/.private/out_current` (today's, `--factor-vintage current`).

| table | cell | today | 2005 |
|---|---|---|---|
| Table 7 | `long: r2`, top 5 | 0.341 / 0.39 ~ | 0.351 / 0.39 ✓ |
| Table 7 | `t: short: intercept`, top 5 | -2.49 / -2.74 ✓ | -2.44 / -2.74 ~ |
| Table 7 | `t: short: intercept`, all | -4.75 / -5.22 ✓ | -4.45 / -5.22 ~ |
| Table 7 | `t: short: market`, top 20 | 9.25 / 8.44 ✓ | 10.1 / 8.44 ~ |
| Table 4 | `t: market`, top 20 | -0.543 / -0.64 ~ | -0.427 / -0.64 ✗ |
| Table 4 | `t: smb`, 101-120 | -0.734 / -0.5 ✗ | -0.516 / -0.5 ✓ |
| Table 8 | `post_market`, top 20 | 0.0419 / 0.048 ~ | 0.0447 / 0.048 ✓ |
| Table 8 | `t: post_market`, all | -2.78 / -2.43 ~ | -2.59 / -2.43 ✓ |
| Table 8 | `post_reversal`, top 5 | -0.0767 / -0.0626 ~ | -0.0789 / -0.0626 ✗ |

By mark the check goes from ✓ 316 / ~ 180 / ✗ 369 to ✓ 317 / ~ 178 / ✗ 370, score 406.0 both
ways. Table 8's ten Factor-sd cells keep their marks (all ✓ but the reversal's after-1988 ✗),
their values as in the table above. The vintage is shipped because the evidence says it is the
paper's data, not because it scores: it is score-neutral, five of the nine cells improve and
four worsen, and the trade is not a marker of quality but of how noisy six-lag Newey-West
t-statistics are at these sample sizes.

**The reversal identification re-run (sections 51 and 61).** With the 2005 factors the four
known factors' covariance is the paper's, so `implied_covariances` and `paper_system`
(`scripts/audit_reversal_factor.py --factor-vintage 2005`, output in `<scratch>/audit_2005.md`)
give: before 1989, at the printed 0.0723, implied correlations **+0.81 market / +0.79 SMB /
-0.18 HML / -0.15 momentum**, a valid covariance matrix, the valid SD range 0.0608-0.0815;
after 1988, at the printed 0.0445, **+0.74 / +0.52 / -0.41 / -0.30**, also valid, the range
0.0396-0.0570. Today's factors give +0.81 / +0.79 / -0.18 / -0.16 (range 0.0609-0.0815) and
+0.79 / +0.55 / -0.53 / -0.30 (range 0.0424-0.0583). Section 51's reading survives the vintage
unchanged: the printed standard deviation is not a misprint, and the implied factor is a
long-only-like series; the after-1988 panel moves toward the losers-only series the scored block
uses (its correlation with the market is +0.72 there, against an implied +0.74, where today's
factors imply +0.79). The numbers are in `<scratch>/targets.json` for contract Pb.

**What it does not touch.** The prior-month deciles the losers-only reversal series is built
from are today's: the earliest archived `10_Portfolios_Prior_1_0` file is from 2007 and equals
today's (monthly returns correlate 0.9995, losers-only SD 0.0687 against 0.0685), so only the
`RF` the deciles are reduced by follows the vintage. French's `ST_Rev` - added to the library in
2006, after the paper - is today's file too, and stays the unscored alternative. Tables 1-3, 5,
6, 9 and Figure 1 do not read factors and are byte-identical; Figure 4's residual correlations
and the equity-premium column move in value, not in marks.

**Where it lives.** `project.factors.set_vintage` / `vintage_dir` / `--factor-vintage`
(`scripts/03_replicate.py`, default `2005`, named in the check's conventions paragraph);
`scripts/claims/table7.py` reads the vintage's directory; `scripts/audit_reversal_factor.py`
takes the same flag. Both manifest copies (`scripts/rebuild_manifest.json` and
`score_wrapper.PINNED_MANIFEST`) are re-pinned to the driver that produced the committed check
over the unchanged cohort cache.

## 73. No reversal construction matches the paper's factor in both subperiods (2026-11-17): 406.0 -> 406.0 (investigation)

The regression cells of Tables 4, 7 and 8 (318 cells) lose more than half the points still open, and
they hinge on the reversal factor the paper built and never published. Table 8's arithmetic
identifies its moments (sections 51 and 61): SD 0.0723 before 1989 and 0.0445 after, with market /
SMB / HML / momentum correlations +0.81 / +0.79 / -0.18 / -0.16 and +0.79 / +0.55 / -0.53 / -0.30
(today's factors; +0.74 / +0.52 / -0.41 / -0.30 after 1988 with the 2005 ones, section 72). The
scored losers-only series fits the first window and misses the second (SD 0.069). Contract Pb
pre-registered a 72-construction grid read from p. 813 and footnote 7 (leg x deciles x weighting x
sort universe), and a distance (log SD ratio plus the four correlation gaps, summed over the two
windows), and selected by that distance only.

**Result.** The shipped `french_ew_d3_losers_only` is the nearest construction in both vintages
(total distance 0.851 today, 0.718 with the 2005 factors); none is closer in both windows, so the
ship rule admits nothing. Every construction misses the post-1988 SD; the winners-only NYSE/AMEX builds
that come near it after 1988 (0.044-0.053) move away before 1989. Scored through the standard check
with the new opt-in `--reversal-factor csv --reversal-csv PATH`, the losers-only series reproduces
406.0 and `french_ew_d3_winners_only` gives 399.0. The post-1988 regression cells are therefore out
of reach of any reading of the paper's sentence. Details, both vintages' tables and the
pre-registration: `claims/REVERSAL_SUBPERIODS.md`; code: `scripts/experiments/reversal_subperiods.py`.

## 74. Table 9 Panel B: six recall readings, and the same-day close ships (2026-11-17): 408.0 -> 411.0

Table 9 Panel B (44 cells) scored 10 / 16 / 18 = 18.0 with the next-day close of section 58. The text
(p. 824): "we simulate recalls on the short positions, and subsequent closing of the pairs position,
on days with high volume. High-volume days are defined as days on which daily volume exceeds average
daily volume over the 18 months (both split-adjusted) by more than one standard deviation." Its
motivation: "short recalls are more common as the price declines". Contract L measured six readings,
each a finished 474-cohort run of `scripts/claims/table9b_recalls.py run --reading <id>`
(`claims/TABLE9B_READINGS.md`, regenerated from the run directories by the script's `readings`
command):

| id | reading | ✓ / ~ / ✗ | of 44 | change vs our Table 1 B, fully invested (bp) | recall share |
|---|---|---|---|---|---|
| R0 | next-day close (section 58, the previous scored reading) | 10 / 16 / 18 | 18.0 | +10.1 / +21.2 / +17.9 / +51.6 | 68.6% |
| **R1** | **the pair closes at the close of the flagged day, also under the one-day wait** | **15 / 12 / 17** | **21.0** | +5.5 / +20.6 / +20.2 / +62.0 | 70.3% |
| R2 | threshold over the 18 months ending the day before (rolling) | 11 / 15 / 18 | 18.5 | +7.7 / +20.0 / +25.6 / +63.2 | 68.9% |
| R3 | R1 and R2 together | 15 / 13 / 16 | 21.5 | +1.6 / +17.4 / +27.2 / +75.4 | 70.6% |
| R4 | flags only on days the short leg falls (sensitivity) | 12 / 10 / 22 | 17.0 | +14.1 / +20.9 / +15.7 / +34.0 | 55.3% |
| R5 | a flag on either leg (sensitivity) | 12 / 10 / 22 | 17.0 | +9.0 / +21.4 / +12.8 / +64.2 | 82.8% |

The paper's change is -12.6 / -4.1 / -13.0 / -13.0 bp (its Table 9 B minus its Table 1 B).

**What ships: R1.** The text puts the closing "on days with high volume", and a recall is forced on
the trader rather than a trading decision the caption's one-day wait applies to; R1 adds +3.0
(10 / 16 / 18 -> 15 / 12 / 17) through the driver (`--table9b-cache
data/processed/replication/vol_common_recalls_r1`, `make table9b` builds it with `--reading R1`).
R2's "most recent 18 months" is weaker than the cohort's 18-month window ("the 18 months"), so R3 does
not ship; R4 and R5 have no basis in the rule. **What does not change:** every reading *raises* the
mean against Table 1 Panel B where the paper's falls, so claim 20 (b) stays unreplicated.

**A correction to the contract's first report.** L's first table had the R1 and R5 rows swapped
(R1 13.0, R5 21.0); the runs were re-made and the table above is regenerated from the final run
directories, and the coordinator confirmed R1's 21.0 through the driver's own Table 9 B loader
(409.0 of 865 with R1 alone).

**The engine.** `simulate_cohort` gains `recall_immediate` and `recall_either` (default off: the
next-day path and every other output are byte-identical, and a staging rebuild of the shared cache
from this code matched the live cache file for file across 475 cohorts before the manifest was
re-pinned); `project.recalls` gains `rolling_volume_thresholds`.

## 75. Table 6 takes the caption's committed capital, and four draw readings (2026-11-17): 406.0 -> 408.0

Table 6's committed rows were the last block still built on the literal committed series
(`sum_p pi_p,t / N selected`, SCORE_LOG row 18). Its own caption says otherwise: "The random
pairs form value-weighted portfolios of n pairs" (p. 819), and section 69 measured that the
"book-share" reading (the value-weighted book scaled by the share of pairs holding a position)
restores the paper's committed / fully-invested ratio (0.69-0.76 against the printed 0.6-0.85,
where the literal series gives -0.01 to 0.16) and scores 13.0 rather than 11.0. Contract J
measured it; this section ships it, and then measures four readings of the *draw* that section
69 left open.

**What ships.** `--table6-cache` now defaults to `data/processed/replication/vol_common_t6_book`
(474 cohorts, seed 20060101, 200 replications, `--committed-capital book-share`), `make table6`
builds that cache, and the check's Table 6 section quotes the caption and says which series the
committed rows use. Tables 1, 3, 7 and 9 keep the literal series: their captions do not say
"value-weighted portfolios". The block moves 8 / 6 / 34 = 11.0 -> 8 / 10 / 30 = 13.0 and every
other cell of the check is byte-identical, so the total rises 406.0 -> 408.0 of 865
(`<scratch>/check.log`, Table 6 tally line).

**The control still holds.** With the four draw switches added, `--mode control` prints
`max_diff_shipped` 0.0 over 948 cohort-waits and 5,688 cells: the shipped draw is unchanged.

**The four draw readings** (50 replications, all 474 cohorts, on the book-share committed series;
`scripts/03_replicate.py::table6_from_cache` re-reads a run and marks each with the driver's
`_mark`, as the retired one-off `table6_draws.py` did; recover it from commit 2f92de8):

| id | reading | of 48 |
|---|---|---|
| D1 | the random pair closes at its own next crossing, both prices re-based to 1 at the open | 0.5 |
| D2 | the random stock is one of the 10 nearest prior-month ranks in its decile | 12.0 |
| D3 | draws only stocks with a return on every day of the true trade's holding window | 13.0 |
| D4 | decile breakpoints from every CRSP common stock with a prior-month return | 13.0 |

None beats the shipped 13.0 (8 / 10 / 30): our random pairs still lose 2-3x the paper's per month at
matching standard deviations (D4: -0.23 / -0.31 / -0.30 / -0.34% fully invested, no waiting). The
draw switches stay as opt-in options; `--mode control` still prints `max_diff_shipped` 0.0.

## 76. The rejected flag readings, re-scored on all 865 cells (2026-11-17): 411.0 -> 411.0 (investigation)

Most readings earlier rounds rejected were judged on Tables 1-3 (291 cells) or on 323 / 481 cells;
the scored set is now the whole paper, and a reading that lost on Tables 1-3 could win on the rest.
The coordinator rebuilt a full cohort cache for each reading that exists as a driver flag and scored
the whole check against the 406.0 base (side caches at their defaults):

| flag | judged before on | all 865 cells |
|---|---|---|
| `--normalization rebased` | 291 (143.5 vs 187.0) | 342.5 |
| `--same-issuer allow` | 291 (182.5 vs 187.0) | 404.5 |
| `--max-stale-share 0.90` / `0.99` | 323 | 396.0 / 389.0 |
| `--telephone-sic 481x` | 291 | 401.5 |
| `--waste-sic utilities` | 291 | 404.0 |
| `--trigger-sigma std` | 291 | 405.5 |
| `--short-weights value` | 323 (183.5) | 389.5 |
| `--universe volpos_common` / `vol_ns` / `price_common` | 291 | 359.0 / 349.5 / 357.0 |

All eleven still lose on the whole paper, so the earlier rejections stand. The readings that need code
(the 2.33-sigma trigger, fresh divergence, frozen-quote demotion, cohort weights, payoff-count returns,
Panel A over completed windows, wider share classes) are contract S of round 5.

**This integration (rows 27-29).** Round 4's three shipped changes land together: French's 2005
factors (section 72, score-neutral), Table 6's caption reading (section 75, +2.0) and Table 9 B's
same-day close (section 74, +3.0): 406.0 -> 411.0 of 865 (✓ 322, ~ 178, ✗ 365). The check was
regenerated from the shared caches with the new defaults; the round-4 code (`models.py`'s recall
options, the vintage loader, the Table 6 draw switches, the opt-in `--reversal-factor csv`) leaves every
default output byte-identical, which a staging rebuild of `vol_common` confirmed file for file before
both manifest copies were re-pinned.


## 77. The code-only readings, measured on all 865 cells (2026-11-17): 411.0 -> 411.0 (investigation)

Contracts S and R6-A. Thirteen readings that earlier rounds had rejected on Tables 1-3 (291
cells), 323 or 481 cells had never been scored against the whole paper. Each is now one flag
on `scripts/03_replicate.py` whose default leaves every output byte-identical, so the shipped
411.0 stands and every earlier number stands with it. The measurements, the per-block deltas,
the paper quotes and the verdicts are in `claims/FULLSET_RESCORE.md` (one home per fact; this
section records the conventions and the infrastructure).

The flags, all defaulting to the shipped reading:

- `--trigger-mult SIGMAS` (default 2.0). The entry and exit band in formation sigmas. The
  printed average trigger row of Table 2 Panel A is the band times the pairs' sigma, so a run
  that moves the band moves that row with it (`trading_components` takes the multiplier
  instead of the literal 2.0 it used to hardcode).
- `--fresh-divergence` (default off). A pair already outside the band on the trading period's
  first day has not diverged inside the period, so it waits until the spread returns inside the
  band before it can arm. The engine's `disarmed` state, set at day 0.
- `--demote-frozen none|one|both` and `--demote-frozen-share SHARE` (default none / 0.90). Pairs with
  a frozen-quote leg move to the end of the ranking, pool intact: every pair keeps its distance
  and its place in "all", only the top ranks are affected. A leg counts as frozen when its quote
  is unchanged on more than that share of the formation window's days, on the same day rule the
  near-frozen-quote screen uses.
- `--cohort-weights equal|positions|selected` (default equal). How the six overlapping cohorts
  are weighted into one monthly series. `selected` weights a cohort by the pairs it selected for
  that portfolio, `positions` by the pairs holding a position in each of its months (read from
  the cached one-day-wait trade log). Table 3's sector engines keep no trade log, so they take
  the unrestricted portfolio's weights, and Table 9 Panel A - which reads its own screened cache
  through `_strategy_series` - takes the main cache's weights. Both approximations favour the
  shipped reading and are stated in `weighted_overlap_average`'s docstring.
- `--capital-base book|count|gross|long` (default book). Which series the fully invested cells
  read: the value-weighted books (shipped), the payoff counts the cache already holds
  (`sum(pi)/n_t`), or one of the two book-scaling bases, `2 sum(dL-dS)/(sum L + sum S)` and
  `sum(dL-dS)/sum L`, which a build caches as extra capital columns for that run only.
- `--panel-a-cohorts complete|all` (default complete). Table 2 Panel A's cross-cohort moments
  over the cohorts whose window completes, or over every cohort with censored windows included.
- `--share-classes common|wide` and `--share-classes-file PARQUET` (default common). The
  formation universe's share filter: `NS` only, or those plus the classes the map names
  (`scripts/experiments/share_class_map.py --classes SB,AD,CE --out <path>` writes it from
  the raw daily extract; 1690 permnos today: ADR, shares of beneficial interest,
  certificates; it is derived, so it is not committed, and `--classes` splits it for the
  variant runs). The added permnos get the universe's own day rule and every screen, so
  the only thing that changes is the share filter.

Two stamp rules are new, both so that a cache can never be read under the wrong reading:
`capital_base` is stamped only for the bases that add a column to the cache (`count` selects a
series every default cache already holds, and stamping it would refuse the shared cache for no
reason); and a wide run stamps the share-class map's sha256, because two maps with the same
`share_classes=wide` stamp would otherwise share a cache.

Nothing here touched the shared caches: every build wrote `/tmp/S/<id>` (474 cohorts each) and
every re-score read them or the shipped cache with `--aggregate-only`. Baseline re-verified
before measuring: `sh /tmp/S/check.sh` prints 411.0 of 865 on the restored worktree.

