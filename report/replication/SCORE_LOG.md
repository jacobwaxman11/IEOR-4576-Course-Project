# Replication score log

This is the one place that records the replication score: the current total, how it is
counted, and every shipped change to it. Other documents point here instead of quoting the
number, so there is one thing to update.

Current shipped score: 267.5 of 481 cells

Cells outside 25% of the paper (✗): 160 = Table 1 23, Table 2 Panel A 0, Table 2 Panel B 10,
Table 3 36, Table 7 2, Table 4 32, Table 5 Panel A 8, Table 8 45, Figure 4 4. By mark: ✓ 214,
~ 107, ✗ 160. On the earlier cell sets: Tables 1-3 187.0 of 291 (rows 1-13), Tables 1-3 and 7
213.5 of 323 (row 14); the check prints both.

## How the score is counted

- A cell is one ours / paper comparison in `REPLICATION_CHECK.md`: Table 1 (88), Table 2
  Panel A (24), Table 2 Panel B (40), Table 3 (139), Table 7 (32), Table 4 (60), Table 5 Panel A
  (20), Table 8 (72) and Figure 4 (6) = 481. Figure 1 is pass or fail and is not counted;
  Figures 2 and 3 are compared through readings of their images and carry no marks. Table 7
  joined the scored set in row 14, Tables 4, 5 Panel A and 8 and Figure 4 in row 15. Rows that
  repeat a scored row (means, standard deviations, Table 4's serial correlation, Table 5's loss
  probability and minimum) are not counted twice; regression t-statistics and Table 8's factor
  standard deviations are not counted.
- ✓ (within 10% of the paper) = 1, ~ (within 25%) = ½, ✗ = 0. Score = ✓ + ½·~.
- The same rule is written in three places that must agree: the `Score:` line that
  `scripts/03_replicate.py` prints in the check summary, `scripts/replication_score.py`
  (run by `make benchmark`, writes `eval/score.json`), and `tests/test_replication_conformance.py`.
- The 1999 NBER draft is a separate target with its own cells (`EDITION_1999.md`). It is never
  added to this total.
- What the paper contains in full - all nine tables and four figures, with what each is and is not
  scored for - is indexed in `COVERAGE.md`.
- What the paper's own printed statistics imply about the reversal factor it never names, with the
  arithmetic, is `PAPER_CONSISTENCY.md`: the five-factor block pins a 2.19%/month premium at 7.23%
  monthly volatility, and its Panel A loadings need a reversal factor that Mkt-RF/SMB/HML/UMD
  already explain 95% of, against French ST_Rev's 26%. Implausible rather than contradictory, so no
  cell of the check is excluded on those grounds.

## History of shipped changes

One row per change that moved the shipped full-sample check (all 474 cohorts, `vol_common`).
The score is recomputed from the committed `REPLICATION_CHECK.md` at that commit. ✗ columns are
cells outside 25%: Table 1 / Table 2 A / Table 2 B / Table 3, from row 14 on a fifth column
for Table 7, and from row 15 four more for Table 4 / Table 5 A / Table 8 / Figure 4.

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
`OPEN_QUESTIONS.md`. Above the shipped 176.0 only one is recorded: 176.5 (round six), which rests
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

## When a PR changes the score

1. Regenerate the check (`make benchmark` from the cohort cache, or
   `python scripts/03_replicate.py --universe vol_common --workers N --force` to rebuild every
   cohort), copy `results/replication/tables/replication_check.md` to
   `report/replication/REPLICATION_CHECK.md`, and run `make conformance-full` to confirm the
   committed file is reproducible.
2. Add a row to the history table and update the current-score block above.
3. Set `full_sample.threshold` in `tests/replication_conformance.json` to the new score.
4. Name the change in the PR title as `(score A -> B)`, as in the rows above.
