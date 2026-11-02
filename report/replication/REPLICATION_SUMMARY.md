# GGR (2006): proposed baseline and replication evidence

Review split: [PR #13](https://github.com/jacobwaxman11/IEOR-4576-Course-Project/pull/13)
preserves main’s checked baseline and separates the import/cache tooling. PR #8
contains the proposed baseline below. These results are a labeled alternative
until its remaining report alignment and same-baseline claim checks are reviewed.

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
35 daily Table 5B cells. The complete generated check is local at
`results/replication/reconciliation/baseline/tables/replication_check.md`.

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
Table 9A/9B results remain tied to those selections. In particular, the prior
recall experiment increased employed returns instead of producing the paper’s
4–13 bp decline; it is not relabeled as a successful new-baseline experiment.

The independently rebuilt footnote-4 stress lowers the top-20 mean from
**1.4556% to 1.3427%**, versus the paper's **1.436% to 1.32%**, and raises SD
from **1.7048% to 1.9033%**, versus **1.688% to 1.90%**. Selection and trade timing
are exactly unchanged across all 474 cohorts. The waste-SIC sensitivity changes
sector results only. The full 200-replication true-close Table 6 experiment retains
strict-reference selections: relative outperformance holds, but table levels do
not replicate (0/48 within 10%, 9/48 within 25%). Validation: 383 tests passed,
14 skipped; full historical builds and independent isolation controls also passed.

[PR_RECONCILIATION.md](PR_RECONCILIATION.md) records each decision, robustness
results, controls and exact commands. [CLAIMS.md](CLAIMS.md) retains the numbered
claim-by-claim ledger. New outputs and restricted observations remain local.
The archived main check and its artifacts are labeled historical. Cell-margin
tests now compare against the same run’s generated check and pass on the full
baseline outputs. Remaining integration work is to align the review artifacts
with the adopted default and rerun Tables 6, 9A and 9B on that same default.
Hao’s independent same-input rerun scores 243.0/481 versus main’s 261.0/481;
that deterioration is reported alongside the closer Table 1 means. For submission,
keep main’s checked results as the established team baseline and label PR #8’s
numbers as this separately evaluated alternative.
