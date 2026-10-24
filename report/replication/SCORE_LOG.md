# Replication score log

This is the one place that records the replication score: the current total, how it is
counted, and every shipped change to it. Other documents point here instead of quoting the
number, so there is one thing to update.

Current shipped score: 183.5 of 291 cells

Cells outside 25% of the paper (✗): 73 = Table 1 22, Table 2 Panel A 0, Table 2 Panel B 10,
Table 3 41. By mark: ✓ 149, ~ 69, ✗ 73.

## How the score is counted

- A cell is one ours / paper comparison in `REPLICATION_CHECK.md`: Table 1 (88), Table 2
  Panel A (24), Table 2 Panel B (40), Table 3 (139) = 291. Figure 1 is pass or fail and is not
  counted.
- ✓ (within 10% of the paper) = 1, ~ (within 25%) = ½, ✗ = 0. Score = ✓ + ½·~.
- The same rule is written in three places that must agree: the `Score:` line that
  `scripts/03_replicate.py` prints in the check summary, `scripts/replication_score.py`
  (run by `make benchmark`, writes `eval/score.json`), and `tests/test_replication_conformance.py`.
- The 1999 NBER draft is a separate target with its own cells, scored in the private working
  repository. It is never added to this total.

## History of shipped changes

One row per change that moved the shipped full-sample check (all 474 cohorts, `vol_common`).
The score is recomputed from the committed `REPLICATION_CHECK.md` at that commit. ✗ columns are
cells outside 25%: Table 1 / Table 2 A / Table 2 B / Table 3. PR numbers refer to the private
working repository; on this repository rows 1-7 arrived with PRs #3 and #4 and rows 8-12 with the
183.5 sync PR.

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

Other merged PRs (#5, #6, #14, #18 to #21: notes, harness, ledger, tracker, the 1999 scorer) did not
change the score. #9 and #17 are the merges that landed rows 3 and 7 on `main`; #22 landed the notes.

Row 7 is the first row that rests on a convention the paper does not state. Its evidence and the
score without it (165.0, row 6) are in `REVIEW_NOTES.md` section 18; the disclosure is in the
`REPLICATION_CHECK.md` header. Row 8 is another (the paper gives no SIC ranges): evidence in
section 20, disclosure in the same header; `--telephone-sic 481x` gives row 7's 169.5. Row 9
is a third (section 21; `--trigger-sigma std` gives row 8's 172.0). It lowers the 1999 draft's
score from 91.5 to 86.5, which is recorded there as an objection, not a veto.

## Not shipped

Tested levers that score higher but rest on a fitted constant or on no support in the paper's text
are not shipped; they are tracked in the private working repository. These are what-if results,
not entries in this log.

## Where the number is enforced

- `tests/replication_conformance.json`, `full_sample.threshold`: the committed
  `REPLICATION_CHECK.md` must score at least this (`test_shipped_full_sample_check_meets_its_threshold`).
  The separate top-level `threshold` there belongs to the 20-cohort smoke sample and is a
  different quantity.
- `tests/test_score_log.py`: the "Current shipped score" line above must equal the committed
  check's score and that threshold. A PR that changes the score fails until this file, the
  threshold and the check agree.

## When a PR changes the score

1. Regenerate the check (`make benchmark` from the cohort cache, or
   `python scripts/03_replicate.py --universe vol_common --workers N --force` to rebuild every
   cohort), copy `results/replication/tables/replication_check.md` to
   `report/replication/REPLICATION_CHECK.md`, and run `make conformance-full` to confirm the
   committed file is reproducible.
2. Add a row to the history table and update the current-score block above.
3. Set `full_sample.threshold` in `tests/replication_conformance.json` to the new score.
4. Name the change in the PR title as `(score A -> B)`, as in the rows above.
