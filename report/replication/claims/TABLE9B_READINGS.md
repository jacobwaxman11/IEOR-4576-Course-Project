# Table 9 Panel B: the recall readings of REVIEW_NOTES section 74

Every reading below is a finished 474-cohort run of
`scripts/claims/table9b_recalls.py run --reading <id>`; the run directory
is named in the last column. The cells are the paper's own statistics
marked with the replication check's rule (`_mark`): a check mark within
10% of the printed cell, a tilde within 25%, score = check marks + half
the tildes over the table's 44 cells. The shipped reading (R0) is the
control and must reproduce the shipped 10 / 16 / 18 = 18.0.

| id | reading | ✓ | ~ | ✗ | score of 44 | recall share | run |
|---|---|---|---|---|---|---|---|
| R0 | shipped reading (control): threshold over the cohort's 18 months, flag on t closes at the close of t+1, short leg only | 10 | 16 | 18 | 18.0 | 68.6% | `<scratch>/R0` |
| R1 | a flag on day t closes the pair at day t's close, under the one-day wait too | 15 | 12 | 17 | 21.0 | 70.3% | `<scratch>/R1` |
| R2 | the threshold over the 18 months ending the day before t (rolling) | 11 | 15 | 18 | 18.5 | 68.9% | `<scratch>/R2` |
| R3 | R1 and R2 together | 15 | 13 | 16 | 21.5 | 70.6% | `<scratch>/R3` |
| R4 | a flag counts only on a day the short leg's price falls (sensitivity) | 12 | 10 | 22 | 17.0 | 55.3% | `<scratch>/R4` |
| R5 | a flag on either leg (sensitivity; the rule says the short positions) | 12 | 10 | 22 | 17.0 | 82.8% | `<scratch>/R5` |

## The change against our own Table 1 Panel B (fully invested, bp)

Each row is a reading minus our own Table 1 Panel B for the same four
portfolios; the paper row is its Table 9 Panel B minus its Table 1 Panel B:

| id | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| paper | -12.6 | -4.1 | -13.0 | -13.0 |
| R0 | +10.1 | +21.2 | +17.9 | +51.6 |
| R1 | +5.5 | +20.6 | +20.2 | +62.0 |
| R2 | +7.7 | +20.0 | +25.6 | +63.2 |
| R3 | +1.6 | +17.4 | +27.2 | +75.4 |
| R4 | +14.1 | +20.9 | +15.7 | +34.0 |
| R5 | +9.0 | +21.4 | +12.8 | +64.2 |

Both rows are reading minus baseline, in bp, so a negative number is
a decline once recalls are on -- the sign the paper reports.

## Committed capital (bp), for reference

| id | top5 | top20 | 101-120 | all |
|---|---|---|---|---|
| paper | -15.9 | -17.3 | -20.7 | -19.4 |
| R0 | -9.3 | -15.2 | -18.3 | +0.2 |
| R1 | -11.0 | -17.2 | -19.5 | +1.2 |
| R2 | -9.8 | -16.0 | -16.7 | +4.3 |
| R3 | -12.3 | -18.6 | -18.4 | +5.3 |
| R4 | -1.9 | -5.4 | -8.9 | +4.5 |
| R5 | -16.2 | -25.8 | -28.0 | -6.3 |

Reproduce with `python scripts/claims/table9b_recalls.py readings --roots <root,R0>,<root,R1>,...` and `run --reading <id>`.

