# Fidelity fixes and full-sample validation

The implementation is more explicit and internally consistent, but it **does not reproduce the paper numerically**. The new liquidity screen improves the top-5 tail and worsens average-return fit. No rule was selected to maximize the target-match score.

This follows the accounting audit at commit `846a777`. All mean-return comparisons below report percentages per month. The new experiment has 474 reporting months (July 1963–December 2002), 9,944 daily observations, and 479 cohorts, including five warmup cohorts. The attached February 2006 working-paper PDF is the textual source. Its Table 1 targets agree with those already used in the project; the absent published-article PDF is not silently substituted for a verified source.

## Paper-to-code corrections

| Issue | Correction and paper basis | Validation |
|---|---|---|
| Positive quotes and missing volume admitted as evidence of trading | `traded_common` requires a CRSP CIZ transaction-price flag, a finite return, and no recorded zero volume on every formation day. Section 2.1 excludes stocks with any non-trading day. Missing volume alone is not treated as proof of a non-trade. | Fixture distinguishes an actual unchanged transaction price from a quote, zero volume, and missing return; full liquidity-only run isolates the screen. |
| Delayed orders could be cancelled after the signal | Execute at the following close using the original direction. A crossing on the entry day schedules the next-day exit. Section 3.1 describes delayed opening and liquidation without a persistence condition. | Hand-calculated crossing fixture, trade cash-flow reconciliation, execution-only full run. The unstated crossing-on-entry case remains an interpretation. |
| Idle cohorts were dropped from the desk average | Retain zero returns for selected but inactive cohorts. Section 2.3 footnote 6 gives idle cash zero interest, and the staggered strategy averages the cohort portfolios. Empty rank selections remain unavailable rather than fabricated zero returns. | Two-cohort fixture yields 5%, not 10%, when one earns 10% and one is idle; hashes verify selections and trades do not change. |
| Startup had only one cohort in July 1963 | Build February–June cohorts before reporting begins. Section 2.3 describes six staggered portfolios; Table 1 specifies the reporting sample. This is an explicit startup convention, not proof of the authors' initialization. | Exact 474-month reporting calendar and separate warmup-only control. |
| Denominator alternatives compounded dollar changes as returns | Export `period_cash` and `selected_cash`, summing fixed-dollar payoffs before division. Section 2.3 distinguishes selected pairs from pairs that open during a period. | Hand-calculated total equals the trade payoff. These remain sensitivities; the value-weighted book baseline retains the Table 1/7 identity. |
| Figure 3 was rescaled to the paper | Compound from $1 before the first reporting month with no paper anchor, in both the plot and comparison report. | Rebuilt and visually inspected curve; digitized references are approximate, not scored as printed targets. |
| Supporting experiments could reuse old conventions or stale prose | Cache format 7 records liquidity, execution and idle-cash rules. Table 6 uses the same zero-idle books; Tables 6/7 report only the paper months while retaining warmup cohorts. Generated bootstrap verdicts now derive from current checks. | Full-sample controls and separate output paths; no stale numerical success paragraph. |
| Missing volume files could masquerade as no recalls | Raise a specific missing-input error for Table 9B. | Missing-year fixture; actual input availability is disclosed below. |
| Monthly duplicate handling silently chose a row | Import only the bootstrap return fields, collapse identical rows, and reject conflicting security-month returns. Keep this file separate from the richer monthly factor input. | Source hash unchanged and conflicting-return fixture fails before publication. |

CRSP field meanings are documented in the [official CIZ guide](https://www.crsp.org/crsp_pdf/crsp-us-stock-indexes-databases-guide-flat-file-format-2-0/). A trade-price flag is a conservative observable screen; it does not recover the historical CRSP vintage used by the authors.

## Before, after, and paper

“Prior PR” is the accounting-corrected run in the user's comparison, not the older calibrated legacy implementation.

| Paper reference | Portfolio | Prior PR (%) | New (%) | Paper (%) |
|---|---|---:|---:|---:|
| Table 1A | top5 | 1.1250 | 1.8343 | 1.3080 |
| Table 1A | top20 | 1.2690 | 1.7510 | 1.4360 |
| Table 1A | 101-120 | 1.0282 | 1.1355 | 1.0810 |
| Table 1A | all | 1.0563 | 1.1038 | 1.1040 |
| Table 1B | top5 | 0.4986 | 1.0137 | 0.7450 |
| Table 1B | top20 | 0.7647 | 1.1151 | 0.8950 |
| Table 1B | 101-120 | 0.8001 | 0.8806 | 0.7950 |
| Table 1B | all | 0.7973 | 0.7529 | 0.7150 |

The four-portfolio mean absolute error rises from **11.2624 to 22.4020 bp** without the wait and **11.6029 to 15.3083 bp** with the wait. The 492-cell weighted score falls from **239.5 to 219.0**: 156 cells within 10%, 126 additional cells within 25%, and 210 outside 25%. Better rule fidelity is not uniform improvement in the paper comparison.

| Table 1B diagnostic | Prior PR | New | Paper |
|---|---:|---:|---:|
| Top-5 minimum month (%) | -28.1946 | -13.2418 | -12.6280 |
| Top-20 minimum month (%) | -7.3436 | -8.5593 | -8.2180 |
| All-pairs minimum month (%) | -14.8561 | -14.8203 | -2.9510 |
| Top-20 skewness | 0.0149 | 0.9982 | 1.45 |

The independent trade-log reconstruction also matches the cached all-pairs monthly returns exactly. The new top-5 and top-20 minima occur in April 1974. The all-pairs minimum remains February 2000: its six cohort returns range from -4.88% to -18.90%. It is not the earlier non-trading-stock artifact. Table 1B equals Table 7 long minus short to about 1e-16 for every portfolio. Figure 1 still selects rank 4 and produces five trades within the stored timing tolerance.

## Controlled attribution

The control adds warmup cohorts to the prior PR rules. Liquidity, execution and idle variants each change one rule from that control; combined applies all three. The settings were chosen before inspecting the outcomes.

| Panel | Portfolio | Control | Liquidity only | Execution only | Idle only | Combined | Paper |
|---|---|---:|---:|---:|---:|---:|---:|
| A | top5 | 1.1227 | 1.8353 | 1.1227 | 1.1316 | 1.8343 | 1.3080 |
| A | top20 | 1.2735 | 1.7510 | 1.2735 | 1.2735 | 1.7510 | 1.4360 |
| A | 101-120 | 1.0261 | 1.1355 | 1.0261 | 1.0261 | 1.1355 | 1.0810 |
| A | all | 1.0509 | 1.1038 | 1.0509 | 1.0509 | 1.1038 | 1.1040 |
| B | top5 | 0.4992 | 1.0329 | 0.4698 | 0.5064 | 1.0137 | 0.7450 |
| B | top20 | 0.7720 | 1.1253 | 0.7634 | 0.7720 | 1.1151 | 0.8950 |
| B | 101-120 | 0.8026 | 0.8839 | 0.7997 | 0.8026 | 0.8806 | 0.7950 |
| B | all | 0.7942 | 0.7542 | 0.7928 | 0.7942 | 0.7529 | 0.7150 |

| Validation diagnostic (not reported by paper) | Control | Liquidity only | Execution only | Idle only | Combined |
|---|---:|---:|---:|---:|---:|
| Panel A mean absolute error, bp | 11.3947 | 22.4249 | 11.3947 | 11.1729 | 22.4020 |
| Panel B mean absolute error, bp | 11.3877 | 16.1591 | 12.2328 | 11.2063 | 15.3083 |
| Weighted comparison points | 240.5000 | 217.0000 | 241.0000 | 242.0000 | 219.0000 |

The formation screen drives the change: the control averages 2,300.6 eligible stocks and 2,013.4 selected pairs per cohort, versus 1,799.1 stocks and 1,561.1 pairs under the new screen. The paper reports roughly 2,057 pairs. The screen removes an observable non-trading-price issue, but does not recover the paper's universe and worsens mean-return fit.

The delayed-execution-only change lowers the top-5 one-day-wait mean from 0.4992% to 0.4698% (paper 0.7450%); it leaves every no-wait trade unchanged. Idle-cash treatment moves only the top-5 reported means at four-decimal precision. Adding warmup cohorts changes each mean by less than one basis point relative to the prior PR; it cannot explain the main mismatch.

Isolation checks verify **1,437 identical selection/trade files** for idle-only versus control and **958 identical selection/no-wait-trade files** for execution-only versus control. These checks separate a mechanical accounting change from a selection or trade-timing change.


## Supporting experiments

**Table 6:** 200 replications across 479 cohorts. The true-pair control compares 958 cohort/wait combinations and 7,664 portfolio/capital series (including the all-pairs portfolio), with maximum monthly difference 0, vectorized-versus-project difference 1.55e-15, and trade-payoff difference 1.07e-14. The accelerated aggregation also matches the original per-replication loop exactly on all 200 draws of the February 1963 cohort.

The true-minus-random mean is positive and its average Newey–West t exceeds 2 in all 16 portfolio/capital/delay series. However, **0/48 Table 6 cells are within 10% of the paper and only 7/48 within 25%**. Random means are not consistently negative, and random standard deviations do not exceed the true-pair values in every series. This supports relative outperformance in this implementation, not numerical replication of Table 6. Its fourth column is the top 120 pairs, not the all-pairs universe of Table 1.

| Table 6 panel | Portfolio | Random-pair mean (%) | Paper (%) |
|---|---|---:|---:|
| A | top5 | 0.0159 | -0.1370 |
| A | top20 | 0.0105 | -0.1110 |
| A | 101-120 | -0.0022 | -0.1050 |
| A | top120 | 0.0106 | -0.1130 |
| B | top5 | -0.0004 | -0.1770 |
| B | top20 | -0.0033 | -0.0040 |
| B | 101-120 | 0.0144 | -0.1540 |
| B | top120 | 0.0113 | -0.1560 |

**Table 9A:** the size-screened run uses the same 479 cohorts and 474 reporting months. Four independent universe checks find no selected legs outside the eligible three largest NYSE size deciles. Profits remain positive, but the top-20 effect has the opposite sign to the paper.

| Table 9A portfolio | New mean (%) | Paper mean (%) | New change from Table 1B (bp) | Paper change (bp) |
|---|---:|---:|---:|---:|
| top5 | 1.0439 | 0.8350 | +3.02 | +9.00 |
| top20 | 1.0348 | 0.9140 | -8.03 | +1.90 |
| 101-120 | 0.7244 | 0.7280 | -15.62 | -6.70 |
| all | 0.7412 | 0.6900 | -1.16 | -2.50 |

The Table 9A reporter retains both the printed skewness/kurtosis targets and its documented interpretation of the apparent swapped labels. That issue does not affect the mean comparison above.

**Figures and factor checks:** Figures 1–4 were rebuilt. Figure 3's independent $1 top-20 paths end at approximately $181.2 employed / $22.7 committed, versus $39.7 / $11.5 in the digitized paper figure. Log-path correlations of .998/.999 indicate similar shape, not matching wealth. Table 7's proxy-factor claim fails, as described below. All available Tables 4/7/8 and Figure 4 numeric cells are finite.

**Table 9B remains unexecuted:** the available UI export has daily volume but lacks `DlyCumFacShr`, required for split-adjusted volume. WRDS authentication has reached Duo and is awaiting completion. The driver now rejects missing yearly files or missing/nonpositive adjustment factors for observed volume instead of treating them as no recalls or no split. The exact missing inputs are `permno`, `dlycaldt`, `dlyvol`, and `dlycumfacshr` for 1962–2002; these observations must remain local.


## Remaining limits

- Current CIZ returns and historical SIZ/FIZ returns are not interchangeable vintages. CIZ delisting returns are already included and are not applied a second time. Original pair rankings/trade logs are unavailable for an exact cross-check.
- Strict transaction-price screening changes the universe materially. Common-share restrictions, SIC boundaries and unknown classifications remain implementation assumptions. Missing-volume records cannot be reclassified from the paper alone.
- The paper describes both value-weighted book returns and period-level pair-count denominators. Alternative fixed-dollar denominators produce materially different results; neither is selected because it looks closer.
- The Table 2 mixed-decile distance still differs; a conditional average of nonzero integer decile gaps cannot be less than one, yet the paper prints 0.97 for top 20. Both conditional and unconditional statistics remain labeled.
- French short-term reversal is a proxy for the paper's unavailable custom series. The Ibbotson/SBBI vintage is not available; local reconstruction inputs are incomplete. Missing factors cannot explain Table 1's unadjusted return differences.
- The regenerated Table 7 proxy-factor claim still fails: top-20 long alpha t=2.3351 versus paper 1.27. Positive gross returns, a passing accounting identity, or significant proxy alpha do not establish exact replication or a causal mispricing mechanism.

## Reproduction and provenance

Validation was run on November 1–2, 2026 with Python 3.13.9. The final test suite has **325 passed, 15 skipped**; the full historical runs are separate from the opt-in/full-data tests. New validation modules pass Ruff; existing modified files retain their pre-existing lint findings. The environment emits NumPy/BLAS warnings even on small finite arrays, so direct-subtraction checks independently verified 8,121 selected-pair distances/standard deviations and 80 nearest-neighbour cases in four cohorts; maximum SSD discrepancy was 5.28e-11. The accounting, finite-output, and bootstrap controls pass despite those warnings.

The daily and trading-calendar sources are unchanged from the [stage-one provenance record](ACCOUNTING_CORRECTIONS.md#data-and-provenance): daily source SHA-256 `345fcf6bb2473ded89377e18aa8b15ecf79dd3942d71fdeb8e3bdd7d3faab057`; calendar source SHA-256 `c838a658bbf81b3b2a7d31e1d08e003d99cbe58db9bace9b8a7a73d96c78a1eb`. The processed daily panel has 56,697,689 rows in 41 yearly files (1962–2002).

The monthly bootstrap input was imported from `monthly_stocks_1961_2026q2.csv.gz`, source SHA-256 `ddbdc7fe9afdbe041698f864bc049c054324de983611685a0872e2e89c56e9d7`. Of 5,003,530 source rows, 2,786,958 fall in 1962–2002; 29,296 identical return rows were removed, leaving 2,757,662 observations. Output SHA-256: `b55ef8defed6802e488deffb53a409dba961836832e427da8e4a3f7fa562a4c5`. This three-column file is **only** the bootstrap input, not the richer monthly dataset needed for factor reconstruction. Conflicting richer rows were rejected rather than arbitrarily deduplicated.

Install `pip install -e ".[dev]"` and hydrate the public factor archives with `git lfs pull`. Existing daily/index inputs can be imported with `scripts/import_wrds_ui.py`; the [stage-one audit](ACCOUNTING_CORRECTIONS.md) records those inputs. Import the monthly archive once:

```sh
python scripts/import_wrds_ui.py \
  --monthly-csv /path/to/monthly_stocks_1961_2026q2.csv.gz

# Five complete controlled runs plus independent formation and isolation checks.
python scripts/validate_fidelity.py --workers 1
# Revalidate completed outputs without rebuilding them.
python scripts/validate_fidelity.py --compare-only

python scripts/claims/table6_random_pairs.py --mode control \
  --cache-root data/processed/replication/fidelity/combined \
  --out-root results/replication/fidelity/table6
python scripts/claims/table6_random_pairs.py --mode run --reps 200 --workers 1 \
  --cache-root data/processed/replication/fidelity/combined \
  --out-root results/replication/fidelity/table6
python scripts/claims/table6_random_pairs.py --mode report --reps 200 \
  --cache-root data/processed/replication/fidelity/combined \
  --out-root results/replication/fidelity/table6 \
  --report-dir results/replication/fidelity/table6/report

python scripts/03_replicate.py --specification paper --workers 1 \
  --start 1963-02 --report-start 1963-07 --size-deciles-top 3 \
  --cache-root data/processed/replication/fidelity/top3 \
  --out-root results/replication/fidelity/top3
python scripts/claims/table9a.py \
  --screened results/replication/fidelity/top3 \
  --baseline results/replication/fidelity/combined \
  --screened-cache data/processed/replication/fidelity/top3 \
  --baseline-cache data/processed/replication/fidelity/combined \
  --out-dir results/replication/fidelity/table9a
# Repeat this independent check for 1963-07, 1980-08, 1999-09 and 2002-07.
python scripts/claims/table9a.py --check-cohort 1963-07 \
  --cache-root data/processed/replication/fidelity/top3

python scripts/claims/table7.py \
  --cache-root data/processed/replication/fidelity/combined \
  --report results/replication/fidelity/combined/table7_report.md \
  --csv results/replication/fidelity/combined/table7_regressions.csv \
  --json results/replication/fidelity/combined/table7_summary.json --quiet
python scripts/replication_figures.py \
  --tables results/replication/fidelity/combined/tables \
  --out results/replication/fidelity/combined/figures
python -m pytest -q
```

Local evidence is under `results/replication/fidelity/`: `evidence.json`, `comparison.md`, each variant's tables and run metadata, `formation_audit.json`, `table6/control.json`, `table6/sample_validation.json`, the 48-cell Table 6 report, the Table 9A comparison, and the regenerated figures. Caches are isolated by variant under `data/processed/replication/fidelity/`. The tracked Markdown is a written audit; restricted observations, generated results, and credentials remain outside Git.

