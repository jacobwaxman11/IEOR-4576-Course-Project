# GGR (2006): proposed baseline and replication evidence

[PR #13](https://github.com/jacobwaxman11/IEOR-4576-Course-Project/pull/13) is merged
into main at `2f5e22c`; it preserves main’s strategy defaults. PR #8 now contains
the four baseline conventions and regenerated evidence. Tables 6, 7, 9A and 9B
have all been evaluated on the same complete baseline. See
[BASELINE_CLAIMS.md](BASELINE_CLAIMS.md) for controls and exact commands.

The project remains a **partial replication**. The new baseline combines Hao’s
paper-supported compounding/decile fixes, a volume-based universe and July 1963
start, PR #8’s corrected short accounting and execution, and Eiko’s consistent
Newey–West estimator. Eiko’s delisting and SIC flags remain optional. The full
baseline was rebuilt over **474 cohorts, 474 months and 9,944 trading dates**.

The eight Table 1 means have **4.76 bp mean absolute error**, versus **18.86 bp**
for the prior strict-reference run, **11.43 bp** for the earlier accounting-only
comparison, and **5.43 bp** for the nonconstant sensitivity. Seven of eight are
within 10% of the paper. These are different selection/execution specifications,
so the combined improvement is not attributable solely to accounting.

Monthly mean returns below are percentages. Panel A has no wait; Panel B waits
one day. Hao’s main column is the already-committed `bc528c0` output; the other
columns preserve the PR’s prior controlled experiments.

| Paper reference | Portfolio | Prior accounting corrected | PR #8 strict reference | Hao main (#9–10) | New reconciled baseline | Original paper |
|---|---|---:|---:|---:|---:|---:|
| Table 1A | Top 5 | 1.1250 | 1.8343 | 1.2730 | 1.3404 | 1.3080 |
| Table 1A | Top 20 | 1.2690 | 1.7510 | 1.3867 | 1.4556 | 1.4360 |
| Table 1A | 101–120 | 1.0282 | 1.1355 | 0.9684 | 1.0161 | 1.0810 |
| Table 1A | All | 1.0563 | 1.1038 | 0.9069 | 1.0533 | 1.1040 |
| Table 1B | Top 5 | 0.4986 | 1.0137 | 0.7234 | 0.7848 | 0.7450 |
| Table 1B | Top 20 | 0.7647 | 1.1151 | 0.8915 | 0.9598 | 0.8950 |
| Table 1B | 101–120 | 0.8001 | 0.8806 | 0.7643 | 0.8210 | 0.7950 |
| Table 1B | All | 0.7973 | 0.7529 | 0.6290 | 0.7973 | 0.7150 |

The new available-input check scores **258.5 weighted points across 492 cells**:
**210 (42.7%) within 10%**, **307 (62.4%) within 25% including those within 10%**,
and **185 outside 25%**. A “roughly 50%” statement describes a weighted diagnostic,
not half of the economic conclusions proved. Main’s 261.0/481 score is not directly
comparable: its check includes 24 Ibbotson cells unavailable here, while ours adds
35 daily Table 5B cells. The [committed check](REPLICATION_CHECK.md) and [aggregate outputs](outputs/README.md)
now match that run; the original generated output also remains local.

On the same 492-cell set, the score improves from the strict run's **219.0**
to **258.5**, but falls from the earlier nonconstant sensitivity's **263.5**.
Its within-25% matches fall from 321 to 307 despite closer headline means.
This is a defensible reconciled specification, not uniformly better numerical fit.

The all-pairs worst month remains **−14.8943% versus −2.9510%**. The top-20 long-book
alpha remains significant under the French proxy (t **2.16** versus paper **1.27**).
Top-20 returns decline from **1.2477% to 0.4355%** after 1988, versus **1.181% to
0.375%**. The accounting identity Table 1B = Table 7 long minus short holds within
**1.1e-16**, and all available primary statistics are finite. Passing an identity
does not explain the remaining tail or factor discrepancies.

Average universe coverage is **2,293 stocks and 2,009 pairs**, against the paper’s
**2,317 and 2,057**, substantially closer than the prior strict-price screen’s
1,799 and 1,561. RMS, same-issuer/static/stale exclusions and SIC boundaries are
still disclosed conventions. Stock-value short weights are retained for their
buy-and-hold accounting rationale despite their cost to Hao’s comparison score.

The previous WRDS audit and every tested specification remain available in
[WRDS_FOLLOWUP.md](WRDS_FOLLOWUP.md). Its strict-reference frozen-selection CIZ/SIZ
replay moved each of the eight means by less than **0.12 bp**. Thus an unavailable
identical old data vintage is a limitation, not an established explanation for
all discrepancies. The authors’ custom reversal factor and proprietary SBBI
vintage remain unavailable or unvalidated.

The full strict-reference re-aggregation preserves **all 26,544 monthly rows
exactly**. Eiko’s covariance change only alters SEs/t-statistics. Historical
Table 9A/9B results remain preserved. The new baseline was independently retested:
Table 9A has 19/44 cells within 10%; Table 9B has 10/44 under the rearm rule, but
employed returns increase 7.18–48.92 bp instead of reproducing the paper’s decline.

The independently rebuilt footnote-4 stress lowers the top-20 mean from
**1.4556% to 1.3427%**, versus the paper's **1.436% to 1.32%**, and raises SD
from **1.7048% to 1.9033%**, versus **1.688% to 1.90%**. Selection and trade timing
are exactly unchanged across all 474 cohorts. The waste-SIC sensitivity changes
sector results only. The full 200-replication true-close Table 6 experiment now uses the same 474-cohort
baseline: relative outperformance holds, but table levels do not replicate (2/48
within 10%, 9/48 within 25%). The matched control has zero monthly error across
948 cohort/waits and 7,584 cells. All 474 no-recall trade logs likewise match exactly.

[PR_RECONCILIATION.md](PR_RECONCILIATION.md) preserves the earlier decisions and
controlled experiments. [CLAIMS.md](CLAIMS.md) now records the same-baseline claim
results. The current check, aggregate outputs, claim reports and SCORE_LOG row 18
are consistent; the old 261.0/481 check remains separately tested in `archive/`.
Hao’s independent same-input rerun scores 243.0/481 versus main’s 261.0/481, so
closer headline means do not imply a uniformly better replication. Licensed
observations and trade-level caches remain local.

Final local validation: **402 tests passed, 9 skipped**, plus complete baseline
claim controls and hashed aggregate exports. The skips and reproduction commands
are documented in [BASELINE_CLAIMS.md](BASELINE_CLAIMS.md).
