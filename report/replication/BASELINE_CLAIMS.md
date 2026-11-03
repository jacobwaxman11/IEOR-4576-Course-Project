# Same-baseline claim validation — November 2, 2026

All four claim reports now use the same 474-cohort baseline. PR #13 is merged at
`2f5e22c`; PR #8 contains the four baseline conventions and these regenerated reports.
The main check and aggregate outputs are regenerated; SCORE_LOG row 18 records
258.5/492. The historical 261.0/481 check remains separately pinned in `archive/`.

This resolves the report/specification integration gap. It does not resolve the
remaining economic replication gaps. Table 1 mean absolute error improves from
6.70 bp in the committed main snapshot to 4.76 bp; Hao’s same-input broad score
falls from 261.0/481 to 243.0/481. Different inputs/cell sets explain the difference
between that score and the local 258.5/492, not the remaining return discrepancies.

## Table 6: random pairs (§3.6, pp. 818–819)

Both columns below use true-pair closing dates, 200 replications and 474 reporting
months. The old strict reference has 479 cohorts including warmup; the new baseline
has 474. Selection and other profile differences mean this is not a one-rule attribution.

| Panel | Portfolio | Prior strict reference (%) | New baseline (%) | Original paper (%) |
|---|---|---:|---:|---:|
| A | top5 | 0.0024 | 0.0120 | -0.1370 |
| A | top20 | 0.0111 | -0.0001 | -0.1110 |
| A | 101-120 | 0.0099 | 0.0263 | -0.1050 |
| A | top120 | 0.0155 | 0.0184 | -0.1130 |
| B | top5 | -0.0052 | 0.0103 | -0.1770 |
| B | top20 | 0.0052 | 0.0112 | -0.0040 |
| B | 101-120 | 0.0285 | 0.0303 | -0.1540 |
| B | top120 | 0.0172 | 0.0155 | -0.1560 |

New: **2/48 within 10%, 9/48 within 25%**, versus 0/48 and 9/48 for the strict
true-close reference. All 16 mean true-minus-random returns are positive and their
mean Newey–West t-statistics exceed 2. The negative random-pair means and universally
greater random-pair volatility are not reproduced. The full control covers 948
cohort/waits and 7,584 cells: zero monthly discrepancy; vector error 1.33e-15;
trade-payoff error 1.07e-14. A separate check verifies accruing openings in all
3,792 source cohort/wait/portfolios, so the two recorded opening-mask controls agree.

## Table 9A: size screen (§3.9, p. 824)

Only the top-three-decile eligibility screen changes; every other cache setting matches.
Both samples have 474 cohorts and 474 months. An independent first-cohort check
verifies all selected legs against the formation-end breakpoints.

| Portfolio | Previous main (%) | New baseline, top three deciles (%) | Original paper (%) |
|---|---:|---:|---:|
| top5 | 0.9354 | 0.9963 | 0.8350 |
| top20 | 0.9450 | 1.0294 | 0.9140 |
| 101-120 | 0.6746 | 0.7597 | 0.7280 |
| all | 0.6767 | 0.7541 | 0.6900 |

The new run has **19/44 within 10%, 37/44 within 25%**. All four mean-return changes
have the paper’s direction; increases for the top portfolios are larger than published.

## Table 9B: recall robustness (§3.9, pp. 824–825)

The principal `rearm` rule is shown below; immediate re-entry, cohort lock and
formation-only volume thresholds are also retained in the regenerated report.

| Portfolio | Prior strict-reference recall (%) | New baseline recall (%) | Original paper recall (%) |
|---|---:|---:|---:|
| top5 | 1.1889 | 0.8565 | 0.6190 |
| top20 | 1.3837 | 1.1428 | 0.8540 |
| 101-120 | 1.1962 | 0.9654 | 0.6650 |
| all | 1.3736 | 1.2864 | 0.5850 |

New: **10/44 within 10%, 22/44 within 25%**, versus 4/44 and 14/44 under the prior
strict reference. Nevertheless, employed returns **increase 7.18 / 18.30 / 14.43 /
48.92 bp** rather than falling roughly 4–13 bp. The cost claim remains unreplicated.
All 474 no-recall trade logs match the source exactly, with zero monthly difference.
The 18-month volume threshold is retrospective and the final five windows are
censored by the sample cutoff; neither is presented as a deployable recall model.

## Table 7 and provenance

The report is rebuilt on all 474 baseline cohorts and months. Top-20 long-alpha
t remains **2.163 versus 1.27**; its insignificance claim fails under the French
reversal proxy. The authors’ custom reversal and proprietary SBBI vintage remain
unavailable/unvalidated. Table 1B equals long minus short within floating-point precision.

`python -m project.baseline_claims --publish` independently checks profile identity,
full samples, the isolated size setting, bootstrap control and every recall control
before publishing aggregate reports. It writes `claims/baseline_manifest.json`;
`python -m project.export_reports` writes the aggregate-output manifest. Licensed
stock observations, source downloads and trade-level caches remain local.

Final validation: **402 tests passed, 9 skipped** with the baseline table directory
explicitly selected. The skips cover published-PDF/default-path checks, unavailable
Ibbotson inputs, an opt-in rebuild and a shared-path Table 6 fixture. The full runs
and controls described above were executed separately; these are local validation
results, not GitHub CI. Numerical-library warnings remain, and the independent
validators check the reported full-sample statistics for finite values.

## Reproduce

Run from the repository root with the authorized processed inputs and issuer header.

```sh
export PYTHONPATH=src
export GGR_ISSUER_HEADER=data/interim/ciz_issuer_header.parquet
python scripts/03_replicate.py --specification baseline --start 1963-07 --end 2002-12 --workers 3 --cache-root data/processed/replication/reconciliation/baseline --out-root results/replication/reconciliation/baseline
python scripts/03_replicate.py --specification baseline --size-deciles-top 3 --start 1963-07 --end 2002-12 --workers 3 --cache-root data/processed/replication/reconciliation/baseline_top3 --out-root results/replication/reconciliation/baseline_top3
python scripts/claims/table9a.py --specification baseline --screened results/replication/reconciliation/baseline_top3 --baseline results/replication/reconciliation/baseline --screened-cache data/processed/replication/reconciliation/baseline_top3 --baseline-cache data/processed/replication/reconciliation/baseline --out-dir results/replication/reconciliation/baseline_table9a --check-cohort 1963-07 --cache-root data/processed/replication/reconciliation/baseline_top3 > results/replication/reconciliation/baseline_table9a.md
python scripts/claims/table7.py --universe vol_common --cache-root data/processed/replication/reconciliation/baseline --csv results/replication/reconciliation/baseline/table7_regressions.csv --json results/replication/reconciliation/baseline/table7_regressions.json --report results/replication/reconciliation/baseline/table7_regressions.md
python scripts/claims/table6_random_pairs.py --specification baseline --mode control --cache-root data/processed/replication/reconciliation/baseline --out-root results/replication/reconciliation/baseline_table6_v2 --close true > results/replication/reconciliation/baseline_table6_control.log
python scripts/claims/table6_random_pairs.py --specification baseline --mode run --cache-root data/processed/replication/reconciliation/baseline --out-root results/replication/reconciliation/baseline_table6_v2 --close true --reps 200 --workers 4 > results/replication/reconciliation/baseline_table6_run.log
python scripts/claims/table6_random_pairs.py --specification baseline --mode report --cache-root data/processed/replication/reconciliation/baseline --out-root results/replication/reconciliation/baseline_table6_v2 --close true --reps 200 --report-dir results/replication/reconciliation/baseline_table6_v2/report
python scripts/claims/table9b_recalls.py run --specification baseline --cache-root data/processed/replication/reconciliation/baseline --out-root results/replication/reconciliation/baseline_table9b --raw-dir data/interim/crsp/volume --report-dir results/replication/reconciliation/baseline_table9b/report --start 1963-07 --end 2002-12 --workers 2
python -m project.baseline_claims --publish
python scripts/replication_figures.py --tables results/replication/reconciliation/baseline/tables --out results/replication/reconciliation/baseline/figures
python -m project.export_reports --run results/replication/reconciliation/baseline --cache data/processed/replication/reconciliation/baseline
GGR_REPLICATION_TABLES=results/replication/reconciliation/baseline/tables python -m pytest tests/ -q
```
