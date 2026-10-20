# Coordinator review: data provenance and worker code (2026-10-16)

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

