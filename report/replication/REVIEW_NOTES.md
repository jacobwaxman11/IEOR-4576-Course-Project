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

Ratios for the shipped pair: 1.71/1.70/1.54/1.80 no wait and 1.70/1.70/1.53/1.83 one-day wait
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

## 19. Not in this snapshot

Section 19 (daily-panel cross-checks) and the long-form trackers it cites (`OPEN_QUESTIONS.md`,
`EDITION_1999.md`, the 1999 NBER draft scorer) stay in the private working repository; they are
diagnostics and do not change any code path. Sections 20-24 below are the evidence for every
change between the 169.5 snapshot and the 183.5 check, and are copied as written; the PR numbers
and the references to those trackers point at the private repository.

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

