# Replication corrections audit

> **Historical stage:** numerical results below precede the liquidity, execution, idle-cash,
> and warmup validation. See [FIDELITY_VALIDATION.md](FIDELITY_VALIDATION.md) for current
> results and remaining gaps. Earlier cache formats and commands are historical; the
> stage-one accounting experiment is retained at commit `846a777`.

This audit replaces the methodological and reporting claims attached to the run
shipped at `6644cbf4461f22b21a1a69d3e4e0a7052eefbb17`. It distinguishes correct
implementation from agreement with published estimates. A higher target-match
score is not a reason to depart from the paper's rules.

## Issues, corrections, and paper references

| Issue | Correction | Paper reference / why it matters |
|---|---|---|
| Short positions weighted by `prod(1-r_short)`, floored at zero | The paper profile weights each shorted stock by its actual accumulated stock value/liability. The inverse-weight variant is explicitly legacy. | Section 2.3, equations (2)-(3): value-weighted buy-and-hold books. A doubling stock cannot erase the short liability from portfolio weights. |
| Monthly Table 1 compounded daily long-minus-short returns while Table 7 compounded each book | One shared `portfolio_monthly` compounds each book separately and subtracts. Tables 1 and 3 and claim experiments use it. Committed capital scales each daily book by the active fraction before compounding. | Section 2.3 and Table 1B versus Table 7: long-book mean minus short-book mean must reconcile to the portfolio mean. |
| RMS trigger and extra screens presented as paper rules | Default `paper` profile uses population standard deviation of the formation spread, allows same-issuer pairs, and removes flat-path / 95%-stale exclusions. `legacy` preserves the old settings for disclosed sensitivities. | Section 2.1, section 2.2, Table 2A: the text specifies two historical standard deviations and does not specify those additional exclusions. The variance denominator is not specified; `ddof=0` remains a disclosed choice. |
| Full-panel/header SIC could introduce future information | The paper profile uses the SIC in the dated formation-end row only. Full-panel/header fallback is confined to `legacy`. | Section 2.1 and Table 3: sector assignment for formation must not use later observations. Exact S&P boundaries and unknown-code handling remain approximations. |
| "Mixed-decile distance" averaged all pairs | Condition on unequal deciles; retain the unconditional statistic under its own name. A cohort with no mixed pair has a missing conditional statistic. | Table 2B: the row describes the difference among pairs from different deciles. Correcting the label does not imply a closer numerical match. |
| Daily Table 5B not rebuildable | Retain per-cohort daily portfolio returns, average overlapping cohorts by trading date, and export all 36 daily risk statistics. | Table 5B: daily mean, standard deviation, serial correlation, four quantiles, loss probability, and minimum for all four portfolios. The zero serial-correlation target is printed but excluded from relative-error scoring. |
| "23/25 claims replicate" and "267.5 matching cells" overstatements | Replace the blanket verdict with partial replication, separate weighted points from cell counts, archive the legacy claims, and disclose factor substitutions / failed checks. | Tables 4, 6-9, Figure 4 and the conclusion: proxy-factor significance and robustness do not establish exact regression replication or causal mispricing. |
| Claim scripts could mix old selections or accounting, and Table 7 reused hard-coded old controls | Check input conventions and claim-output stamps; require new output directories for changed claim settings. Use the corrected vectorized random-pair engine and current-run Table 7 controls. Match the losers-only decomposition to its own factor regression. | Tables 6, 7 and 9: comparisons require the same return definition and internally consistent controls. |

## Independent accounting evidence

- Two fixed-share short legs move +10%/-10% and then return to their entry prices;
  the long legs are flat. Actual terminal payoff is zero. The old portfolio reports
  **-2.020202%**; corrected monthly accounting returns zero within `1e-14`.
- If one of two shorted stocks doubles and then rises another 10%, the next-day
  liability-weighted return is **-0.20 / 3 = -6.666667%**, rather than discarding
  that short's weight after the doubling.
- Separate monthly compounding reconciles the two books before and after
  overlapping-cohort averaging. A second vectorized engine agrees on employed
  and committed capital across calendar-month boundaries.
- A historical Table 6 control on July/August 1963, both waits, reproduces cached
  corrected monthly returns exactly. Maximum vectorized / trade-payoff difference
  is `4.440892098500626e-16`. This is a control check, not a new 200-draw bootstrap.

## Controlled full-period evidence

Both runs completed **474 cohorts / 474 monthly observations**, July 1963 through
December 2002, on the same processed panel. SHA-256 checks confirm **1,422 identical
files**: each cohort's selected pairs and both waits' trade logs. Thus this comparison
isolates the two accounting changes; it does not attribute the other profile changes
to accounting or compare different stock universes.

| Measure | Old accounting, same selections | Corrected accounting | Assessment |
|---|---:|---:|---|
| Mean absolute error of four Table 1A portfolio means | 17.2579 bp | 11.2624 bp | 34.7% lower |
| Mean absolute error of four Table 1B portfolio means | 15.1868 bp | 11.6029 bp | 23.6% lower |
| Largest Table 1B minus Table 7 mean discrepancy | 2.9257 bp | < 1e-11 bp | Accounting identity restored |
| Top-20 mean, one-day wait (paper 0.8950%) | 0.7195% | 0.7647% | Closer, still materially below paper |
| Broad comparison weighted points, same 492 cells | 250.5 | 239.5 | Worse; not hidden |
| Cells within 10% / additional within 25% / outside 25% | 186 / 129 / 177 | 181 / 117 / 194 | Distributional and other gaps remain |

The mean-error measure is the unweighted average absolute difference from the
published mean across **all four portfolios**, reported separately for each wait;
no portfolio or date is dropped. All mean returns (percent per month):

| Portfolio | No wait: old accounting | No wait: corrected | No wait: paper | Wait 1: old accounting | Wait 1: corrected | Wait 1: paper |
|---|---:|---:|---:|---:|---:|---:|
| Top 5 | 1.1510 | 1.1250 | 1.3080 | 0.5056 | 0.4986 | 0.7450 |
| Top 20 | 1.2402 | 1.2690 | 1.4360 | 0.7195 | 0.7647 | 0.8950 |
| 101-120 | 0.9583 | 1.0282 | 1.0810 | 0.7162 | 0.8001 | 0.7950 |
| All | 0.8892 | 1.0563 | 1.1040 | 0.6013 | 0.7973 | 0.7150 |

Daily outputs cover **9,944 trading dates**. The corrected top-20 daily 1% quantile
is -0.7385% (paper -0.6470%); the all-pairs worst month is -14.8561% (paper -2.9510%).
These are remaining risk-replication gaps, not evidence that the tails are fixed.
The corrected Table 7 proxy-factor claim still fails: the top-20 long alpha has
t=1.9995 (paper 1.27), and the top-5 short alpha has t=-1.2413, insignificant.
Figure 1 remains rank 4 with five trades within the existing date tolerance.

Validation completed on 2026-11-01 with Python 3.13.9 (Anaconda): **311 tests passed,
16 skipped**. The suite includes a real 20-cohort sample rebuild; both full-period
runs were executed separately and checked by `validate_replication.py`. Optional
PDF/data tests and the separately gated full-rebuild pytest test are skipped where
applicable. New modules pass Ruff, and `git diff --check` passes. Existing script
import-order lint findings remain; the test environment emits NumPy/BLAS warnings,
but the accounting, finite-risk-output, OLS/HAC, and reconstruction checks pass.

## Data and provenance

The historical experiment uses the existing WRDS CIZ daily-stock web export,
imported without editing its source. SHA-256:
`345fcf6bb2473ded89377e18aa8b15ecf79dd3942d71fdeb8e3bdd7d3faab057`.
The export contains 102,464,776 rows; 57,606,932 fall in 1962-2002. The importer
removes 20,537 exact duplicate analysis rows and applies the existing security/day
cleaner, yielding **56,697,689 processed rows** across 41 yearly files. Conflicting
duplicate keys fail rather than being resolved by a target-fit choice. CIZ returns
already include delisting returns; no second delisting adjustment is applied.

Trading dates come from the observed CRSP daily-index export (SHA-256
`c838a658bbf81b3b2a7d31e1d08e003d99cbe58db9bace9b8a7a73d96c78a1eb`).
The importer saves local source and yearly-panel checksums. Restricted observations
and generated output remain outside Git. Public factor archives are the existing
Git LFS files. This web-export rebuild is not asserted to be byte-identical to the
teammate's earlier API pull; the controlled comparison uses the same imported
panel on both sides.

## Reproduce the controlled comparison

Install `pip install -e ".[dev]"` and hydrate the public factor archives with
`git lfs pull`. Import the existing downloads, or build the same panel with the
licensed WRDS acquisition pipeline. The web importer refuses to overwrite existing
yearly panels.

```sh
python scripts/import_wrds_ui.py \
  --daily-csv /path/to/daily_stocks_1961_2026q1.csv.gz \
  --index-csv /path/to/daily_indexes_1961_2026q2.csv.gz

python scripts/03_replicate.py --specification paper --workers 3 \
  --cache-root data/processed/replication/paper \
  --out-root results/replication/paper

python scripts/03_replicate.py --specification paper \
  --short-weights position --monthly-aggregation daily_difference --workers 2 \
  --cache-root data/processed/replication/accounting_control \
  --out-root results/replication/accounting_control

python scripts/validate_replication.py \
  --before results/replication/accounting_control \
  --after results/replication/paper \
  --before-cache data/processed/replication/accounting_control \
  --after-cache data/processed/replication/paper \
  --output results/replication/accounting_evidence.json

python scripts/claims/table6_random_pairs.py --mode control \
  --cache-root data/processed/replication/paper --limit-cohorts 2

python scripts/claims/table7.py --cache-root data/processed/replication/paper \
  --report results/replication/paper/table7_report.md \
  --csv results/replication/paper/table7_regressions.csv \
  --json results/replication/paper/table7_summary.json --quiet
```

The accounting control changes only short weights and monthly aggregation relative
to the paper profile. It is **not** the former calibrated specification. The
validator checks every cohort's pair-selection and trade-log hashes before
attributing differences to accounting. The committed legacy `outputs/` directory
is preserved as a separate historical record.

## Limits on the conclusion

This is a partial replication. Exact original reversal and proprietary Ibbotson
observations/vintages remain unavailable or unvalidated. The current local run does
not have the API inputs required for the Ibbotson block. CIZ versus historical CRSP
return conventions, missing-volume interpretation, SIC mapping, the employed-
capital denominator, and skipping a delayed entry whose divergence already
reversed remain disclosed sensitivities. Tail and composition gaps must be reported
rather than tuned away. Table 6's full bootstrap, Table 9's two robustness runs,
and digitized Figures 2/3 need fresh validation before renewing their older claims.
