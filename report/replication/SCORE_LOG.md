# Replication score log

This is the one place that records the replication score: the current total, how it is
counted, and every shipped change to it. Other documents point here instead of quoting the
number, so there is one thing to update.

Current shipped score: 411.0 of 865 cells

Cells outside 25% of the paper (✗): 365 = Table 1 24, Table 2 Panel A 0, Table 2 Panel B 11,
Table 3 37, Table 7 82, Table 4 54, Table 5 Panel A 7, Table 8 84, Figure 4 4, Table 9 A 12,
Table 9 B 17, Table 6 30, Table 5 Panel B 2, printed text 1.
By mark: ✓ 322, ~ 178, ✗ 365. On the earlier cell sets: Tables 1-3 185.5 of 291 (rows 1-13), Tables 1-3 and 7
212.0 of 323 (row 14); the check prints both.

## How the score is counted

- A cell is one ours / paper comparison in `REPLICATION_CHECK.md`: Table 1 (88), Table 2
  Panel A (24), Table 2 Panel B (40), Table 3 (139), Table 7 (136), Table 4 (104), Table 5 Panel A
  (20), Table 5 Panel B (36), Table 8 (130), Figure 4 (6), Table 9 Panel A (44), Table 9 Panel B (44),
  Table 6 (48) and the numbers printed in the text (6) = 865, the paper's distinct printed results
  (`COVERAGE.md`, "How the numbers reconcile: the ceiling"). Figure 1 is pass or fail and is not counted;
  Figures 2 and 3 are compared through readings of their images and carry no marks. Table 7
  joined the scored set in row 14 and its regression block in row 21, Tables 4, 5 Panel A and 8 and Figure 4 in row 15,
  Table 9 Panel A in row 19, Table 9 Panel B in row 22, Table 6 in row 23, Table 5 Panel B in
  row 24, the printed regression t-statistics in row 25, Table 8's factor standard deviations and the
  numbers printed in the text in row 26. Rows that repeat a scored row (means, standard deviations, Table 4's serial correlation,
  Table 5 Panel A's loss probability and minimum, which re-measure Table 1 Panel B) are not counted
  twice; Table 5 Panel B's nine rows are all functions of the daily series, so none of them repeats
  a monthly row. Since row 26 every distinct number the paper prints about its results is scored;
  what is left out (duplicates, derived text arithmetic, parameters, other papers' numbers, the
  images of Figures 2 and 3) is listed with its reason in `COVERAGE.md`.
- ✓ (within 10% of the paper) = 1, ~ (within 25%) = ½, ✗ = 0. Score = ✓ + ½·~.
- The same rule is written in three places that must agree: the `Score:` line that
  `scripts/03_replicate.py` prints in the check summary, `scripts/replication_score.py`
  (run by `make benchmark`, writes `eval/score.json`), and `tests/test_replication_conformance.py`.
- The 1999 NBER draft is a separate target with its own cells (`EDITION_1999.md`). It is never
  added to this total.
- What the paper contains in full - all nine tables and four figures, with what each is and is not
  scored for - is indexed in `COVERAGE.md`.
- What the paper's own printed statistics imply about the reversal factor it never names, with the
  arithmetic, is `GAPS.md` (section 11): the five-factor block pins a 2.19%/month premium at 7.23%
  monthly volatility, and its Panel A loadings need a reversal factor that Mkt-RF/SMB/HML/UMD
  already explain 95% of, against French ST_Rev's 26%. Implausible rather than contradictory, so no
  cell of the check is excluded on those grounds.

## History of shipped changes

One row per change that moved the shipped full-sample check (all 474 cohorts, `vol_common`).
The score is recomputed from the committed `REPLICATION_CHECK.md` at that commit. ✗ columns are
cells outside 25%: Table 1 / Table 2 A / Table 2 B / Table 3, from row 14 on a fifth column
for Table 7, from row 15 four more for Table 4 / Table 5 A / Table 8 / Figure 4, then one per
added block at the end: Table 9 A from row 19, Table 9 B from row 22, Table 6 from row 23,
Table 5 B from row 24 and the printed text numbers from row 26.

| # | Date | PR | Score | ✓ / ~ / ✗ | ✗ by table | What moved it |
|---|---|---|---|---|---|---|
| 1 | 2026-10-17 | #4 | 135.5 | 94 / 83 / 114 | 34 / 3 / 17 / 60 | first full-sample check |
| 2 | 2026-10-17 | #4 | 137.5 | 97 / 81 / 113 | 33 / 3 / 17 / 60 | review fixes: one job per cohort, payoffs from the engine |
| 3 | 2026-10-18 | #7, #8 | 145.0 | 106 / 78 / 107 | 33 / 3 / 11 / 60 | Panel B size deciles from CRSP breakpoints (NYSE + AMEX common) |
| 4 | 2026-10-18 | #10 | 161.5 | 121 / 81 / 89 | 19 / 3 / 11 / 56 | frozen-price stocks dropped; fully invested return on the pairs open that day |
| 5 | 2026-10-19 | #12 | 164.0 | 130 / 68 / 93 | 23 / 3 / 11 / 56 | value-weighted long and short books |
| 6 | 2026-10-20 | #13 | 165.0 | 130 / 70 / 91 | 23 / 3 / 9 / 56 | Panel B decile-difference row reports the all-pairs average |
| 7 | 2026-10-20 | #15, #16 | 169.5 | 132 / 75 / 84 | 22 / 1 / 10 / 51 | same-issuer and near-frozen-quote exclusions on by default |
| 8 | 2026-10-22 | #25 | 172.0 | 135 / 74 / 82 | 22 / 1 / 10 / 49 | telephone utilities are SIC 4811 only (the 1972 code) |
| 9 | 2026-10-22 | #26 | 176.0 | 139 / 74 / 78 | 22 / 1 / 10 / 45 | trigger sigma is the formation spread's RMS about zero, sqrt(SSD/N) |
| 10 | 2026-10-23 | #29 | 177.5 | 143 / 69 / 79 | 22 / 1 / 10 / 46 | unknown-SIC fallback order reversed: the CRSP security-header SIC is primary, the earliest known dated SIC fills the rest (Table 3 sector mix) |
| 11 | 2026-10-23 | #30 | 178.5 | 144 / 69 / 78 | 22 / 0 / 10 / 46 | Table 2 Panel A averages only cohorts whose six-month trading window completes inside the sample (the last five 2002 cohorts are force-closed and censor time open); Panel A dispersion rows |
| 12 | 2026-10-24 | #32 | 183.5 | 149 / 69 / 73 | 22 / 0 / 10 / 41 | waste management (SIC 4950-4959) moved from Utilities to Industrials, as GICS classifies it: the Utilities 101-120 band gains five cells (REVIEW_NOTES 24) |
| 13 | 2026-10-24 | #38, #39 | 187.0 | 152 / 70 / 69 | 23 / 0 / 10 / 36 | eq. (3) weights a short position by its own compounded return, prod(1 - r), not by the shorted stock's value: Table 3 +8.5, Table 1 -5.0 (REVIEW_NOTES 29) |
| 14 | 2026-10-25 | #43 | 213.5 | 175 / 77 / 71 | 23 / 0 / 10 / 36 / 2 | Table 7 (long and short books) joins the scored set: 32 new cells, ✓ 23 / ~ 7 / ✗ 2, so the total rises 187.0 -> 213.5 and the rate 64.3% -> 66.1%. The cohort cache also stores each portfolio's two books (CACHE_FORMAT 5); the accumulation refactor leaves Tables 1-3 byte-identical (REVIEW_NOTES 35) |
| 15 | 2026-10-27 | #47 | 266.5 | 213 / 107 / 161 | 23 / 0 / 10 / 36 / 2 / 33 / 8 / 45 / 4 | every table and figure the paper prints a number for, and that the cached series can reproduce, joins the scored set: Table 4 (Sharpe ratios, the five-factor regression, the Ibbotson-factor regression, the equity-premium column; 60 cells, 23.0), Table 5 Panel A (20, 9.5), Table 8 (subperiod moments and regressions; 72, 19.5) and Figure 4's six printed correlations (6, 1.0). The total rises 213.5 -> 266.5 and the rate falls 66.1% -> 55.4%: the 158 new cells score 33.5%, mostly because the paper's reversal factor cannot be rebuilt and the five-factor regressions inherit it; the Ibbotson regression, which has no reversal factor, scores 12.0 of 24 (REVIEW_NOTES 49). Tables 1-3 and 7 are byte-identical |
| 16 | 2026-10-27 | #48 | 267.5 | 214 / 107 / 160 | 23 / 0 / 10 / 36 / 2 / 32 / 8 / 45 / 4 | Table 4's equity-premium column is French's Mkt-RF, the regressions' market factor, which Table 8 names the "U.S. equity risk-premium" and whose SDs it prints, instead of the S&P 500 less the 30-day bill: the serial-correlation cell moves 0.0002 -> 0.0465 against 0.05 (✗ -> ✓), the other three stay ✓ (REVIEW_NOTES 50). The intercepts' Newey-West t-statistics are printed beside the paper's, unscored. Every other cell is byte-identical |
| 17 | 2026-11-02 | #61 | 261.0 | 207 / 108 / 166 | 24 / 0 / 11 / 37 / 2 / 33 / 7 / 48 / 4 | two readings the paper's own text requires: Tables 1 and 3 compound the long and the short book to monthly returns before subtracting (§2.3, p. 805; Table 1 Panel B equals Table 7 long minus short, pp. 807 and 821), and Table 2 Panel B's "average decile difference for mixed pairs" averages the mixed pairs only (§3.2 and Table 2, p. 809). Table 1 +1.5, Table 5 Panel A +0.5, Table 2 Panel B -0.5, Table 3 -3.5, Table 4 -2.5, Table 8 -2.0. CACHE_FORMAT 6. An independent implementation (public PR #8 at 5d137c3, `--specification legacy --monthly-aggregation books`) gives identical marks on every cell (REVIEW_NOTES 54) |
| 18 | 2026-11-03 | #64 | 262.0 | 209 / 106 / 166 | 24 / 0 / 11 / 37 / 2 / 33 / 7 / 48 / 4 | committed capital is the paper's literal reading: "scales the portfolio payoffs by the number of pairs that are selected for trading" (section 2.3, PDF p. 14), sum of daily payoffs over the selected pairs, on the engine path; results without a trade log keep the historical hybrid. Quarantined to the eight Table 1 committed cells: Panel A 101-120 and Panel B all move ~ to ✓ (261.0 -> 262.0) |

| 19 | 2026-11-15 | #66 | 289.0 | 231 / 116 / 178 | 24 / 0 / 11 / 37 / 2 / 33 / 7 / 48 / 4 / 12 | Table 9 Panel A (p. 825, top three size deciles, one-day wait) joins the scored set: 44 cells from a second cohort cache built with --size-deciles-top 3 (make table9a), scored as printed including the transposed skewness/kurtosis rows (COVERAGE.md item 1): 22 / 10 / 12, +27.0 (262.0 -> 289.0 of 525); under the swapped reading the block would score 22 / 11 / 11 = 27.5 (REVIEW_NOTES 60). The sample smoke test is unchanged: its scorer covers Tables 1-3, 7 and the 43 factor-free row-15 cells only and its run never executes the check step. |
| 20 | 2026-11-15 | #67 | 297.5 | 237 / 121 / 167 | 24 / 0 / 11 / 37 / 2 / 27 / 7 / 43 / 4 / 12 | the five-factor block is scored on the reversal factor the paper's own Table 8 arithmetic implies rather than on French ST_Rev: the equal-weighted bottom three prior-month deciles less the T-bill (sd 0.0685 before 1989 against the printed 0.0723; correlations +0.84 market and +0.77 SMB against the implied +0.81 and +0.79), not a long-short factor no construction brings near the printed sd. On the row-19 base the 52 class-C cells move 7.0 -> 13.0 and the paper-side pre-1989 regressions (class A) 4.0 -> 6.5, so the total rises 289.0 -> 297.5 of 525 (ST_Rev stays printed unscored and --reversal-factor st_rev reproduces row 19's block); this hypothesises that the paper's factor lacks its short leg (REVIEW_NOTES section 61) |
| 21 | 2026-11-16 | this PR | 308.0 | 245 / 126 / 210 | 24 / 0 / 11 / 37 / 45 / 27 / 7 / 43 / 4 / 12 | Table 7's regression block (intercept, five loadings, R2 for the long and the short book of each portfolio; 56 cells) joins the scored set: each book less French's RF on the driver's frame (`--reversal-factor`, six Newey-West lags), coefficients and R2 scored, t-statistics unscored as in Tables 4 and 8. Under the default losers-only series the block scores 8 / 5 / 43 = 10.5, so the total rises 297.5 -> 308.0 of 581; French's ST_Rev reading of the same 56 cells is printed unscored (10 / 9 / 37 = 14.5) and `--reversal-factor st_rev` restores it. The 525 existing marks are byte-identical (REVIEW_NOTES section 63) |
| 22 | 2026-11-16 | #69 | 326.0 | 255 / 142 / 228 | 24 / 0 / 11 / 37 / 45 / 27 / 7 / 43 / 4 / 12 / 18 | Table 9 Panel B (p. 825: short recalls on high volume, the one-day wait) joins the scored set: 44 cells from the recall cache `scripts/claims/table9b_recalls.py` writes (`make table9b`), scored as printed, 10 / 16 / 18, +18.0, so the total rises 297.5 -> 315.5 of 569. The section reads the claim script's primary reading -- a recalled short ends the pair, it is re-entered only on a new episode, threshold one standard deviation over the cohort's 18 months, flag on day t and close at the close of t+1 -- and its note records that 69% of closes are recalls at this threshold and that the fully-invested row's direction is a property of our measure under that re-entry (REVIEW_NOTES 58 and 64). The sample smoke test does not move: its scorer covers Tables 1-3, 7 and the 43 factor-free row-15 cells and never runs the check step; `REPLICATION_FULL=1` needs the recall cache at data/processed/replication/vol_common_recalls |
| 23 | 2026-11-16 | #71 | 337.0 | 263 / 148 / 262 | 24 / 0 / 11 / 37 / 45 / 27 / 7 / 43 / 4 / 12 / 18 / 34 | Table 6 (p. 818, returns to random pairs) joins the scored set: 48 cells from the bootstrap `scripts/claims/table6_random_pairs.py` already ran for CLAIMS claim 3, now read by the check through `--table6-cache` (default `data/processed/replication/vol_common_t6`, `make table6` rebuilds it; one `.npz` per cohort beside `run_params.json`). The block scores 8 / 6 / 34 = 11.0, so the total rises 326.0 -> 337.0 of 673 (the row-21 base 308.0 plus row 22's Table 9 Panel B, 18.0). The cells average our own random draws against our own true-pair series, not the paper's, so they are the least comparable in the check (REVIEW_NOTES section 65); the shared cache changed with row 18's #64 rebuild, so the regenerated TABLE6.md/TABLE6.csv differ from the committed ones. Every earlier cell is byte-identical |
| 24 | 2026-11-16 | #72 | 367.0 | 289 / 156 / 264 | 24 / 0 / 11 / 37 / 45 / 27 / 7 / 43 / 4 / 12 / 18 / 34 / 2 | Table 5 Panel B (daily value at risk, p. 816) joins the scored set: the cache now stores each cohort's daily fully-invested return for the one-day-wait portfolios (CACHE_FORMAT 7, `daily.parquet`), `aggregate` adds the daily overlap average of that series, and the 36 cells (nine statistics x four portfolios) score 26 / 8 / 2 = +30.0, so the total rises 337.0 -> 367.0 of 709. Percentiles are linearly interpolated and serial correlation is the lag-1 autocorrelation of consecutive trading days, neither of which the paper states; the paper prints the 101-120 serial correlation as a rounded "0.00", so that cell is marked on the two decimals it prints. The three named columns match on every row; the "all" column is the loosest (its daily standard deviation 1.13 times the paper's, its minimum 1.38 times) and is reported, not adjusted (COVERAGE.md item 4; REVIEW_NOTES 62). Every other cell of the check is byte-identical, the daily rows being additional output; the shared cache must be rebuilt to format 7 and the manifest re-pinned at merge, which the coordinator does |
| 25 | 2026-11-16 | #74 | 393.0 | 304 / 178 / 367 | 24 / 0 / 11 / 37 / 82 / 54 / 7 / 82 / 4 / 12 / 18 / 34 / 2 | the 140 Newey-West t-statistics the paper prints for its regression coefficients join the scored set (Table 4 44: 24 five-factor + 20 Ibbotson; Table 7 48; Table 8 48), typed as PAPER_TABLE4_T and PAPER_TABLE8_T and re-read from the PDF by verify_paper_targets, six lags as the paper states. They score 15 / 22 / 103 = 26.0, so the total rises 367.0 -> 393.0 of 849; every existing mark is unchanged, and the t-statistics raise the ✗ counts of Tables 7, 4 and 8 in place rather than adding columns. The unscored alpha-t rows are replaced by the scored rows; the ST_Rev alternative blocks keep their t rows unscored. The row-14 subset line now counts Table 7's 32 performance cells only (212.0 of 323; it had counted the whole of Table 7 since #68) (REVIEW_NOTES section 67) |
| 26 | 2026-11-17 | #76 | 406.0 | 316 / 180 / 369 | 24 / 0 / 11 / 37 / 82 / 54 / 7 / 83 / 4 / 12 / 18 / 34 / 2 / 1 | the last printed numbers join the scored set: Table 8's "Factor sd" column (10 cells: the sample standard deviation of the driver's scored factor frame over the two panels' own months; 9 / 0 / 1, the reversal's after-1988 cell the hypothesis of row 20), the captions' pairs per cohort (1, ✓), section 1.2's hold-out sentence for 1999-2002 on the no-wait rule (3: 6.53% / 4.45% / t 4.25 against 10.4% / 3.8% / 4.82, so 0 / 2 / 1; the one-day-wait reading prints unscored), and footnote 4's delisting result from the new `--delist-cache` (2, both ✓). 16 cells, +13.0, so the total rises 393.0 -> 406.0 of 865 (849 -> 865), every distinct printed result of the paper; COVERAGE.md is rewritten as the full-coverage inventory, CLAIMS.md's duplicated ledger keeps one copy, and the conformance note loses its triplicated sentence (REVIEW_NOTES 68) |
| 27 | 2026-11-17 | #79 | 406.0 | 317 / 178 / 370 | 24 / 0 / 11 / 37 / 82 / 54 / 7 / 84 / 4 / 12 / 18 / 34 / 2 / 1 | the factor regressions read French's factor library as the paper had it: the 2005 archives (Wayback 2005-09-30 and 2005-10-29, built on the 200508 / 200509 CRSP databases, `data/raw/french_vintage_2005/`, `--factor-vintage 2005`). Independent evidence: they reproduce Table 8's printed factor SDs (HML after 1988 +0.1% where today's file is -7.7%; market before 1989 0.0%). Score-neutral: Table 7 -1.0, Table 4 +0.5, Table 8 +0.5 (REVIEW_NOTES section 72) |
| 28 | 2026-11-17 | #79 | 408.0 | 317 / 182 / 366 | 24 / 0 / 11 / 37 / 82 / 54 / 7 / 84 / 4 / 12 / 18 / 30 / 2 / 1 | Table 6's committed rows take the caption's reading, "value-weighted portfolios of n pairs" (p. 819): the book scaled by the share of pairs holding a position (cache `vol_common_t6_book`, 200 replications); it restores the paper's committed / fully-invested ratio (0.69-0.76 against 0.6-0.85; the literal series gives -0.01 to 0.16). Table 6 8 / 6 / 34 -> 8 / 10 / 30, +2.0 (REVIEW_NOTES section 75) |
| 29 | 2026-11-17 | #79 | 411.0 | 322 / 178 / 365 | 24 / 0 / 11 / 37 / 82 / 54 / 7 / 84 / 4 / 12 / 17 / 30 / 2 / 1 | Table 9 Panel B's recall closes the pair at the close of the flagged day itself, also under the one-day wait: the text has the "closing of the pairs position, on days with high volume" (p. 824), and a recall is forced rather than a trading decision (cache `vol_common_recalls_r1`, `--reading R1`). Table 9 B 10 / 16 / 18 -> 15 / 12 / 17, +3.0. Like every reading measured, it raises the mean against Table 1 Panel B where the paper's falls 4-13 bp, so claim 20 (b) stays unreplicated (REVIEW_NOTES section 74) |
Other merged PRs (#5, #6, #14, #18 to #21: notes, harness, ledger, tracker, the 1999 scorer; #41,
Table 5 Panel A and Table 8 as unscored diagnostics) did not change the score. #9 and #17 are the merges that landed rows 3 and 7 on `main`; #22 landed the notes. #49 (the reversal-factor audit) adds an unscored section to the check and does not change the score.

Row 7 is the first row that rests on a convention the paper does not state. Its evidence and the
score without it (165.0, row 6) are in `REVIEW_NOTES.md` section 18; the disclosure is in the
`REPLICATION_CHECK.md` header. Row 8 is another (the paper gives no SIC ranges): evidence in
section 20, disclosure in the same header; `--telephone-sic 481x` gives row 7's 169.5. Row 9
is a third (section 21; `--trigger-sigma std` gives row 8's 172.0). It lowers the 1999 draft's
score from 91.5 to 86.5, which is recorded there as an objection, not a veto. Row 13 is a fourth
(section 29; `--short-weights value` gives row 12's 183.5). Its support is outside the scored
tables (the paper's Table 7 short book and Table 5 daily "all" column); against it, it lowers
every mean, so Table 8 before 1989 and Table 1's "all" mean move away from the paper, and the
1999 draft's score falls from 86.5 to 77.0. That fall is recorded as an objection because the
draft describes its returns as payoff counts, which the short weight does not touch.

## Not shipped

Tested levers that score higher but are not shipped, each with the reason, are in
`GAPS.md` (sections 8-10) and `archive/OPEN_QUESTIONS_ROUNDS.md`. Above the shipped 176.0 only one is recorded: 176.5 (round six), which rests
on a constant fitted to the Table 2 trigger and is rejected for that reason. Dropping Nasdaq after
1985, which has no support in the paper's text, scored 174.0 before rows 8 and 9. On row 12's
183.5, payoff counts (184.5), the count/book hybrid of closed PR #36 (185.0) and a gross-book base
(184.5) reach the "all" kurtosis only by deepening February 2000 (REVIEW_NOTES 25 and 29). These
scores are what-if results, not entries in this log.

## Where the number is enforced

- `tests/replication_conformance.json`, `full_sample.threshold`: the committed
  `REPLICATION_CHECK.md` must score at least this (`test_shipped_full_sample_check_meets_its_threshold`).
  The separate top-level `threshold` there belongs to the 20-cohort smoke sample and is a
  different quantity.
- `tests/test_score_log.py`: the "Current shipped score" line above must equal the committed
  check's score and that threshold. A PR that changes the score fails until this file, the
  threshold and the check agree.
- The cohort cache, not the code, decides whether a score can be reproduced cheaply. A formation,
  engine or reporting change invalidates it: `--aggregate-only` then refuses it by name
  ("cache was built with no `short_weights` stamp, this run uses `short_weights=position`"), so
  `make benchmark` fails until `scripts/03_replicate.py --force` rebuilds it. Rows 12-13 changed
  both the sector map and the short-position weight, so the cache was rebuilt once: `--force` was
  run, `--aggregate-only` accepts it again, and the rebuilt check is byte-identical to the committed
  one at 187.0 of 291. `scripts/rebuild_manifest.json` and the copy of the pinned hashes in
  `scripts/score_wrapper.py` were re-pinned to the code that built it in the same change, so
  `score_wrapper.formation_changed()` reports no change and the fast aggregate tier works again.
  Re-pin **after** the rebuild, never before: a manifest that matches new code while the cache was
  built by old code is the one combination the pin exists to prevent.
- Row 24 changed the cache format (7): each cohort also stores `daily.parquet`, the daily
  fully-invested series Table 5 Panel B scores. The monthly rows are unchanged, so every other cell
  of the check is byte-identical; but a format-6 cache is refused by name and has to be rebuilt with
  `--force`. `scripts/rebuild_manifest.json` and the copy of the pinned hashes in
  `scripts/score_wrapper.py` are re-pinned together to the code that produced the verification
  check, and the shared cache at `data/processed/replication/vol_common` is rebuilt to format 7 at
  merge by the coordinator: until that rebuild the pin describes the contract's cache, not the
  shipped one, and the PR says so.

## When a PR changes the score

1. Regenerate the check (`make benchmark` from the cohort cache, or
   `python scripts/03_replicate.py --universe vol_common --workers N --force` to rebuild every
   cohort), copy `results/replication/tables/replication_check.md` to
   `report/replication/REPLICATION_CHECK.md`, and run `make conformance-full` to confirm the
   committed file is reproducible.
2. Add a row to the history table and update the current-score block above.
3. Set `full_sample.threshold` in `tests/replication_conformance.json` to the new score.
4. Name the change in the PR title as `(score A -> B)`, as in the rows above.
