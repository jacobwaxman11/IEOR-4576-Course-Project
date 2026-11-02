# Reconciliation of PR #8 with Hao and Eiko

November 2, 2026. PR #8 reconciles Hao’s merged **#9–10** and Eiko’s **#12**
(`f07fc8c`), which superseded her closed, unmerged #11 (`83aa60c`). The team
merged #12 into `main` at **`5499701`** while this reconciliation was running.
That updated main is integrated locally into PR #8. No teammate branch was
rewritten. **PR #8 remains open, with auto-merge off; this task merged no GitHub PR.**

The comparison starts from PR #8 at `5d137c3`. No old experiment or restricted
observation is discarded. New generated results remain local in `results/`.
The previously committed main artifacts are retained and labeled historical.

## Decisions and paper evidence

| Issue | Evidence / decision |
|---|---|
| Monthly compounding, Hao #9 | Retain separate monthly long/short compounding, then subtract. Section 2.3, RFS p. 805, and Table 7 long minus short = Table 1B (pp. 821/807) support it. Our implementation already contained this fix. |
| Mixed-decile distance, Hao #9 | Retain averaging over mixed pairs only (Table 2B / §3.2, p. 809). The paper’s 0.97 is below the minimum integer gap of one; report that discrepancy instead of changing the population to fit it. |
| Random-pair closes, Hao #10 | Add `--close true`: inherit the true trade’s opening and closing dates, capped by earlier random-leg forced exits. This holds timing fixed to isolate stock selection (§3.6 / Table 6, pp. 818–819). Keep `--close own` and its original results. The caption does not explicitly identify whose crossing it means. |
| Table 6 accounting | Keep PR #8’s stock-value short liabilities, zero idle returns, monthly book compounding, full-sample checks, and vectorized control. Importing Hao’s old inverse-weight engine would undo this correction. The helper lives in `src/project/random_pairs.py`; the compatibility script imports it. |
| Universe | Default to the volume-based universe. The strict transaction-price screen excludes historical Nasdaq coverage and badly misses the paper’s stock/pair counts (§2.1, p. 803; Tables 1/3, pp. 807/812). The strict-price reference remains available under its historical `paper` profile name. This change is supported by market-data semantics and coverage, not just mean-return fit. |
| First cohort | Default to July 1963, following §2.3, p. 806: the first 12 months are for estimation. February–June warmup remains explicit via `--start 1963-02 --report-start 1963-07`. |
| Trigger scale | Baseline retains RMS, reflecting Hao’s printed-trigger evidence in REVIEW_NOTES §21 and his one-change-at-a-time review. Demeaned standard deviation remains available. The paper’s wording alone does not uniquely settle this choice; this is an interpretation, not an accounting repair. |
| Same-issuer / static / stale screens | Baseline retains main’s disclosed same-issuer exclusion, never-moved-stock exclusion and 95% stale screen. These are conventions described in REVIEW_NOTES §18, not explicit paper instructions. The screens remain individually overridable and stamped. |
| Short weighting | Keep `short_weights=value`, even though Hao reports that it costs 11.5 points on his control. A bought-and-held short liability grows as `prod(1+r_short)`; `prod(1-r_short)` is a different inverse-return construction. Section 2.3’s buy-and-hold interpretation motivates this choice. The paper’s portfolio weighting remains imperfectly specified, so `position` remains an explicit alternative. No claim of unanimous agreement is made. |
| Idle capital | New `idle_policy=opened` retains zero idle months for a portfolio that opened, but omits an entirely never-opened cohort from employed-capital averaging (its period denominator is zero). Committed capital still earns zero on unused funds. This addresses Hao’s distinction between idle months and never-opened cohorts (§2.3 / RFS footnote 5, p. 805). Prior `zero` and `exclude` behavior is preserved. |
| Eiko #12 delisting check | `--long-delisting-loss`, off by default, sets an open delisting long leg’s terminal return to -100% (RFS footnote 4, p. 804). Short returns and signal prices are unchanged. It is a robustness test, not a replacement for actual CIZ/SIZ delisting returns. |
| Eiko #12 SIC check | `--waste-sic utilities` moves SIC 4950–4959 from Industrials to Utilities, explicitly reversing REVIEW_NOTES §24. Off by default; classified and cached separately. |
| Eiko #12 Newey–West | Use six lags without the small-sample covariance multiplier, matching the existing factor estimator. This is a consistent estimator convention; the paper does not settle the finite-sample correction uniquely. Means/volatilities are unchanged. |
| Cash denominator diagnostic | Do not import #11’s extra “paper definition” row; Eiko removed it in #12. Existing `period_cash`, `selected_cash` and `employed_literal` diagnostics remain distinct. Fixed-dollar payoffs and compounded returns are different numerators; their ratio does not isolate the denominator alone. |
| Cache safety / Table 7 | Preserve format 7 and reject optional delisting/SIC caches in strict-reference claim experiments. Table 6 stamps true-close results separately; a missing close key explicitly means historical own-crossing behavior. Table 7 accepts format-7 corrected books across disclosed universes, checks its own cache identity, and rejects old compounding/short weights. |
| Regression safeguard | Restore the exact 261.0-point historical snapshot check; replace the vacuous `score >= 0`. Also pin the reconciled full-run outputs and preserve accounting/calendar/finite-data checks. A score change can be justified and rebaselined; it is not a rule for optimizing fit. |
| Claims / documentation | Keep the numbered claims ledger with current evidence and explicit experiment scope. Mispricing is not a tested causal claim (Hao #10). No inherited “19/24 replicate” tally is applied to a different run. |

The new `baseline` profile differs from the old strict reference in several disclosed
conventions; the combined change is **not** an accounting-only attribution. Hao’s
one-at-a-time measurements and citations are retained in REVIEW_NOTES §54 and
[his PR #8 review](https://github.com/jacobwaxman11/IEOR-4576-Course-Project/pull/8).
Eiko’s original main-specification measurements remain attributed in §55.

## Validation and numerical comparison

### Full baseline and preserved reference

All 474 baseline cohorts were rebuilt. Output validation passed for all 474
reporting months and 9,944 daily dates, finite available risk/factor statistics,
and Table 1B = Table 7 to 1.1e-16. The eight baseline means have 4.76 bp average
absolute error; 7/8 are within 10%. The all-pairs worst month is still -14.8943%
versus -2.9510%. Means below are monthly percent.

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

The new check has 258.5 weighted points across 492 cells: 210 within 10%, 97 more
within 25%, and 185 outside 25%. Main’s 261.0/481 uses a different input/cell set
(24 Ibbotson cells here unavailable; 35 daily-risk cells added), so comparing those
totals as an improvement or deterioration would be misleading. The dated summary
and numbered ledger use the new build’s numbers, not inherited qualitative tallies.
The generated check was rebuilt locally; repository policy keeps generated
outputs out of new commits.

Re-aggregating the preserved strict-reference cache gives 479 cohorts, 474 months,
9,944 dates, and 26,544 monthly rows exactly equal to PR #8 at `5d137c3`. Its
score remains 219.0/492. Table 1 means and SDs are unchanged; t-statistics rise by
sqrt(474/473), about 0.10565%, due solely to Eiko’s covariance convention.

On the same 492-cell set, the broader evidence is mixed and is reported in full:

| Diagnostic | Prior strict reference | Earlier nonconstant sensitivity | New baseline | Original paper |
|---|---:|---:|---:|---|
| Table 1 eight-mean error, bp | 18.86 | 5.43 | **4.76** | 0 by definition |
| Weighted points | 219.0 | 263.5 | **258.5** | Not a paper metric |
| Cells within 10% | 156 | 206 | **210** | Not a paper metric |
| Cells within 25%, cumulative | 282 | 321 | **307** | Not a paper metric |

Thus the baseline improves on the strict run by 39.5 points and 54 close matches,
but loses **5 points and 14 within-25% matches** versus the nonconstant sensitivity.
It is not a uniform improvement. No rule was selected solely to maximize this score.

Figures 2–4 and Table 7 regressions were also rebuilt on the new baseline. The
top-20 long-alpha t-statistic is 2.16 versus 1.27 in the paper: the insignificance
claim still fails. The custom reversal factor/SBBI vintage and capital/tail
questions remain open. The earlier CIZ/SIZ replay moved eight headline means by
less than 0.12 bp on frozen strict selections, so data vintage alone is not a
verified explanation for the full discrepancy.

### Optional robustness and Table 6

**Footnote 4, p. 804:** rebuilt all 474 cohorts with only the long-delisting-loss
flag changed. All 474 pair selections and 948 trade-event logs are exactly
unchanged after excluding the deliberately stressed payoff column. The figures
below compare to the top-20 no-wait Table 1 column; that panel identification is
inferred from the footnote's cited 1.436% starting mean.

| Top 20, monthly percent | New baseline | -100% delisting-long stress | Paper baseline | Paper stress |
|---|---:|---:|---:|---:|
| Mean | 1.4556 | **1.3427** | 1.4360 | **1.3200** |
| Standard deviation | 1.7048 | **1.9033** | 1.6880 | **1.9000** |

The mean effect is **-11.29 bp versus -11.60 bp** in the paper; the volatility
effect is **+19.85 bp versus +21.20 bp**. This is evidence for replicating that
robustness effect, not a reason to replace actual delisting returns in the baseline.
The stressed run scores 231.5/492 against the *unstressed* published tables, as
expected for a different experiment.

**SIC sensitivity:** moving waste management to Utilities preserves the complete
unrestricted monthly panel, 474 unrestricted pair selections, and all 948
unrestricted trade logs exactly. Utilities' average stock count rises from
**134.67 to 141.51**, versus paper **156**, while its ranks-101–120 mean falls
from **0.8752% to 0.7901%**, versus paper **0.9256%**. The score falls from
258.5 to 256.0/492. Keep the mapping as an explicit sensitivity.

**Table 6 / §3.6, pp. 818–819:** the true-close test uses the preserved **strict
reference**, not the new baseline: 479 cohorts, 474 months, 200 replications and
all 16 portfolio/capital/delay series. The matched control covers 958 cohort-waits
and 7,664 cells: maximum monthly difference **0**, vectorized-layer error
**1.56e-15**, and cached trade-payoff error **1.07e-14**. Closing rules share the
same seed and source cache and have separate stamped output directories.

| Table 6 fully invested mean, monthly % | Prior own-crossing close | True trade's close | Original paper |
|---|---:|---:|---:|
| A, top 5 | 0.0159 | 0.0024 | -0.1370 |
| A, top 20 | 0.0105 | 0.0111 | -0.1110 |
| A, 101–120 | -0.0022 | 0.0099 | -0.1050 |
| A, all 120 | 0.0106 | 0.0155 | -0.1130 |
| B, top 5 | -0.0004 | -0.0052 | -0.1770 |
| B, top 20 | -0.0033 | 0.0052 | -0.0040 |
| B, 101–120 | 0.0144 | 0.0285 | -0.1540 |
| B, all 120 | 0.0113 | 0.0172 | -0.1560 |

The true-close variant has **0/48 cells within 10% and 9/48 within 25%**, versus
0 and 7 for own-crossing. All 16 mean true-minus-random returns are positive;
the mean Newey–West t over replications exceeds 2 in each series (one top-5
replication has t = 1.99). The paper's slightly negative random-pair means and
universally greater volatility are **not replicated**. This supports relative
outperformance on the strict selections, not a fully replicated Table 6.

**Validation:** 383 tests passed, 14 skipped. The skips cover unavailable published
PDF/default-path artifacts and proprietary inputs, plus opt-in rebuilds. The
actual full 474-cohort baseline and both sensitivities were executed separately;
the exact full-baseline regression assertions were run against the rebuilt
output. Every available full-run primary risk statistic is finite despite local
numerical-library warnings. The strict reference's monthly rows remain exact.
`python -m project.reconciliation` independently checks full samples, setting
isolation, unchanged selections/trade timing, Table 1/Table 7 identities and the
full Table 6 control, and writes aggregate evidence plus output SHA-256 hashes
to ignored `results/replication/reconciliation/validation.json`.


## Reproduction

Use the existing authorized CRSP processed panel, French archives and calendar.
Python 3.13 and `PYTHONPATH=src` were used locally. Commands below are run from the
repository root. The issuer exclusion requires a PERMNO/PERMCO map. The local web
export already contains it; no new WRDS download was necessary:

```sh
export PYTHONPATH=src
# Use your untouched downloaded monthly web export. This is its local sibling location.
python scripts/build_issuer_header.py \
  --source ../data/raw/crsp/monthly_stocks_1961_2026q2.csv.gz \
  --output data/interim/ciz_issuer_header.parquet
export GGR_ISSUER_HEADER=data/interim/ciz_issuer_header.parquet
python scripts/03_replicate.py --specification baseline --start 1963-07 --end 2002-12 \
  --workers 3 --cache-root data/processed/replication/reconciliation/baseline \
  --out-root results/replication/reconciliation/baseline
python scripts/replication_figures.py \
  --tables results/replication/reconciliation/baseline/tables \
  --out results/replication/reconciliation/baseline/figures
python scripts/claims/table7.py --universe vol_common \
  --cache-root data/processed/replication/reconciliation/baseline \
  --csv results/replication/reconciliation/baseline/table7_regressions.csv \
  --json results/replication/reconciliation/baseline/table7_regressions.json \
  --report results/replication/reconciliation/baseline/table7_regressions.md
python scripts/03_replicate.py --specification baseline --long-delisting-loss \
  --start 1963-07 --end 2002-12 --workers 2 \
  --cache-root data/processed/replication/reconciliation/delisting \
  --out-root results/replication/reconciliation/delisting
python scripts/03_replicate.py --specification baseline --waste-sic utilities \
  --start 1963-07 --end 2002-12 --workers 2 \
  --cache-root data/processed/replication/reconciliation/waste_utilities \
  --out-root results/replication/reconciliation/waste_utilities
```

`build_issuer_header.py` refuses to replace an existing output. It retains only
`SecurityHdrFlg=Y` mappings, collapses identical rows, rejects conflicts/missing
identifiers, and saves source/output SHA-256 checksums beside the local output.
The 40,373 mappings are used only for the disclosed issuer screen, never as a
historical SIC fallback. The run’s cache stamps the issuer-file checksum.
The untouched source SHA-256 is
`ddbdc7fe9afdbe041698f864bc049c054324de983611685a0872e2e89c56e9d7`;
the derived map SHA-256 is
`c02881d64d10bc6f1170ec8e1ca893f799244c48bed7b610f7e6230bc0721d7e`.
Both restricted files stay local and ignored. If using the separately acquired
API header, omit `GGR_ISSUER_HEADER`.

Preserve the strict-reference comparisons explicitly:

```sh
python scripts/03_replicate.py --specification paper --start 1963-02 --report-start 1963-07 \
  --aggregate-only --cache-root data/processed/replication/fidelity/combined \
  --out-root results/replication/reconciliation/strict_reference
python scripts/claims/table6_random_pairs.py --mode control --close true --reps 200 \
  --cache-root data/processed/replication/fidelity/combined \
  --out-root results/replication/reconciliation/table6_true
python scripts/claims/table6_random_pairs.py --mode run --close true --reps 200 --workers 3 \
  --cache-root data/processed/replication/fidelity/combined \
  --out-root results/replication/reconciliation/table6_true
python scripts/claims/table6_random_pairs.py --mode report --close true --reps 200 \
  --cache-root data/processed/replication/fidelity/combined \
  --out-root results/replication/reconciliation/table6_true \
  --report-dir results/replication/reconciliation/table6_true/report
python -m project.reconciliation
python -m pytest tests/ -q
```

The older full Table 6 own-crossing outputs remain at
`results/replication/fidelity/table6`; use `--close own` when reporting them.
Never switch the closing rule while reusing that output directory. Historical
strict-reference Table 9A/9B results remain tied to their original selections.
