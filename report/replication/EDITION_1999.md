# Second target: the 1999 NBER draft

The shipped check (`REPLICATION_CHECK.md`; total and history in `SCORE_LOG.md`) compares our engine with the published paper
(Review of Financial Studies 2006). The 1999 NBER draft of the same paper reports the same method
on 408 monthly cohorts (July 1963 to June 1997) and different numbers, so it is a second, independent
measurement of the same rules.

## Which PDF is which

| file | what it is | role |
|---|---|---|
| `Pairs_Trading_RV_Arbitrage_Rule.pdf` | Yale ICF working paper 08-03, "This Version: February 2006" (47 pages) | the paper; same tables and numbers as the RFS article |
| `pairs-trading-performance-of-a-relative-value-arbitrage-rule_final.pdf` | RFS 19(3), 2006, typeset (31 pages), doi:10.1093/rfs/hhj020 — the final published version | the paper; the target of `REPLICATION_CHECK.md`. `make verify-targets` checks this file's identity (running head and DOI) as well as every typed target, so it cannot be scored against the working paper by mistake |
| `report/replication/reference/NBER_w7032_1999_draft.pdf` | NBER Working Paper 7032, March 1999 (35 pages) | helper only: second opinion, as below |

The first two are the same paper (every table value agrees; checked 2026-10-21). Only the NBER draft
is a different edition. It is © 1999 by the authors, so it is kept in the private repository and is
not part of the public snapshot.

## Rules for using it

- The RFS paper is the target. A change is judged on the RFS check.
- The draft is a second opinion. It may **veto** a change (a rule that fits the RFS and breaks the
  draft is suspect). It cannot **justify** one.
- Marks follow the RFS check: within 10% of the paper is a match, within 25% a half match.

## What is scored (136 cells)

| table | cells | content |
|---|---|---|
| Table I | 72 | six-month returns of the no-wait and one-day-wait portfolios, committed capital (mean, median, standard deviation, kurtosis, skewness, minimum, maximum, share of negative cohorts), mean on employed capital |
| Table II A | 24 | trigger, pairs traded, round trips, months open, with their standard deviations (no wait) |
| Table II B | 40 | size deciles, share of mixed-size pairs, sector weights, mixed-sector pairs |

Paper values are typed in `src/project/edition1999.py`. The draft's counts of mixed pairs are divided
by its pairs traded to give shares.

## Results (408 cohorts)

Every row is a full 474-cohort rebuild on the 2026-10-22 CRSP pull, so the rows are comparable
one with the next; the original table (2026-10-21 cache) read 79.0 and 90.0 for the first two
rows. The 1.0 step between the caches is the cache refresh, not a rule change.

| defaults | Table I | Table II A | Table II B | total (of 136) |
|---|---|---|---|---|
| before the same-issuer and near-frozen-quote exclusions (`std` trigger, 481x telephone) | 33.5 | 22.5 | 24.0 | 80.0 |
| + both exclusions — SCORE_LOG row 7 | 46.5 | 23.5 | 21.0 | 91.0 |
| + telephone utilities are SIC 4811 — SCORE_LOG row 8 | 46.5 | 23.5 | 21.5 | 91.5 |
| + trigger sigma is the spread's RMS about zero — SCORE_LOG row 9 (shipped) | 41.5 | 23.5 | 21.5 | 86.5 |
| + waste management (SIC 495x) classified as Industrials — SCORE_LOG row 12 (no veto: the draft has no by-sector table, Table II B weights unchanged) | 41.5 | 23.5 | 21.5 | 86.5 |
| + short positions weighted by their own return, prod(1 - r) — SCORE_LOG row 13 (shipped; objection, see below) | 32.0 | 23.5 | 21.5 | 77.0 |

The exclusions raise Table I by 13 points and lower Table II B by 3. In Table II B they move the
top-5 and top-20 sector weights the right way for Utilities (top 5: 0.67 to 0.83, draft 0.81) and the
wrong way for Industrials (top 20: 0.127 to 0.081, draft 0.13) and mixed-sector pairs (top 20: 0.152
to 0.129, draft 0.172). They also push the size decile away from the draft's (top 5: 3.35 to 2.55,
draft 3.1), while that decile matches the RFS's 2.54. The two editions therefore disagree about what
the exclusions should do to the composition rows. See `OPEN_QUESTIONS.md` (Q5).

Row 9 lowers the draft score 91.5 -> 86.5, all in Table I (46.5 -> 41.5): ten cells move from
✓ to ~ and none to ✗. The draft's Table I means and medians were already 5-9% low and the RMS
trigger trades less. Against it, the draft's own Table II A trigger, which measures sigma
directly, matches ours exactly at top 5 (0.0399 against the draft's 0.0399) and near-exactly at
top 20 (0.0453 against 0.0449). REVIEW_NOTES section 21 therefore records the fall as an
objection, not a veto; SCORE_LOG row 9 carries the shipped decision.

Row 13 lowers the draft score 86.5 -> 77.0, all in Table I (41.5 -> 32.0). The short weight
shifts the whole monthly distribution down, not only the means: by statistic the 9.5 points
are medians -3.0, means -2.5, share negative -2.5, maxima -2.0 and minima -0.5, offset by
skewness +1.0, and the draft's locations were already low. It is recorded as an objection, not
a veto. The draft describes its committed return as "the sum of the payoffs over all pairs ...
divided by the number of pairs", a payoff count with no value weighting, so it cannot measure how
eq. (3) weights a short; scored by that stated measure (`committed_count`) the draft gives 82.0 to
84.0 under either short weight. Against that, its numbers fit the value-weighted series a little
better (86.5 with the stock-value short weight) than its own description, which is why the fall is
recorded. REVIEW_NOTES section 29 has the full evidence.

## Running it

    python scripts/edition_1999.py [--cohorts DIR] [--out PATH]
    make edition-1999

It reads the cohort cache that `03_replicate.py` builds (default
`data/processed/replication/vol_common/cohorts`) and writes
`results/replication/tables/edition_1999.md` with every cell. No WRDS access is needed.
