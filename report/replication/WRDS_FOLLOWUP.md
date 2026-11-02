# WRDS follow-up: historical data and liquidity definitions

This audit supersedes the claim that the prior `traded_common` run was the full paper specification. No numerical match is claimed. It separates verified accounting fixes, data-source changes and unresolved methodological interpretations.

## Full-sample results

The predeclared static-history exclusion is the closest of the tested new specifications for the eight Table 1 means: mean absolute error falls from **18.8552 bp** under the strict-price screen to **5.4318 bp**. It also improves on the prior accounting-corrected comparison (about **11.4327 bp**). This is a sensitivity result, not confirmation that the authors used that exclusion. The legacy-SIZ source alone does not improve fit. Broadening the share universe improves some delayed-return means while worsening the no-wait results; neither result is hidden.

Each new run has **479 cohorts, 474 reporting months (July 1963–December 2002), and 9,944 trading dates**, with finite primary statistics and Table 1B = Table 7 long minus short within 1.1e-16. The final five trading windows are sample-end censored as in the frozen reference. All means below are percent per month.

| Paper reference | Portfolio | Old accounting | Prior PR corrected | Prior strict-price | New CIZ volume | New CIZ nonconstant | Original paper |
|---|---|---:|---:|---:|---:|---:|---:|
| Table 1A | top5 | 1.1510 | 1.1250 | 1.8343 | 1.1316 | 1.3183 | 1.3080 |
| Table 1A | top20 | 1.2402 | 1.2690 | 1.7510 | 1.2735 | 1.3381 | 1.4360 |
| Table 1A | 101-120 | 0.9583 | 1.0282 | 1.1355 | 1.0261 | 1.0268 | 1.0810 |
| Table 1A | all | 0.8892 | 1.0563 | 1.1038 | 1.0509 | 1.0515 | 1.1040 |
| Table 1B | top5 | 0.5056 | 0.4986 | 1.0137 | 0.4803 | 0.6768 | 0.7450 |
| Table 1B | top20 | 0.7195 | 0.7647 | 1.1151 | 0.7634 | 0.8271 | 0.8950 |
| Table 1B | 101-120 | 0.7162 | 0.8001 | 0.8806 | 0.7997 | 0.8000 | 0.7950 |
| Table 1B | all | 0.6013 | 0.7973 | 0.7529 | 0.7928 | 0.7935 | 0.7150 |

The first two columns preserve the original comparison on identical stage-one selections. Later columns change eligibility/execution/startup conventions and are not attributed solely to accounting. The `nonconstant` sensitivity excludes histories with no recorded nonzero return (missing returns count as zero for this flag); it does **not** impose the older 95% stale-price cutoff or exclude same-issuer pairs.

| Paper reference | Portfolio | New CIZ activity | New SIZ volume | New CIZ normal shares | Original paper |
|---|---|---:|---:|---:|---:|
| Table 1A | top5 | 1.8288 | 1.1171 | 1.8360 | 1.3080 |
| Table 1A | top20 | 1.7503 | 1.2504 | 1.9886 | 1.4360 |
| Table 1A | 101-120 | 1.1576 | 1.0099 | 1.1776 | 1.0810 |
| Table 1A | all | 1.1075 | 1.0540 | 1.0694 | 1.1040 |
| Table 1B | top5 | 1.0051 | 0.4703 | 0.7173 | 0.7450 |
| Table 1B | top20 | 1.1146 | 0.7532 | 1.0708 | 0.8950 |
| Table 1B | 101-120 | 0.8998 | 0.7903 | 0.8590 | 0.7950 |
| Table 1B | all | 0.7531 | 0.7957 | 0.7961 | 0.7150 |

| Diagnostic, not a paper statistic | CIZ volume | CIZ activity | SIZ volume | CIZ nonconstant | CIZ normal shares |
|---|---:|---:|---:|---:|---:|
| Panel A mean absolute error (bp) | 11.1729 | 22.8807 | 12.4417 | 5.3726 | 30.2964 |
| Panel B mean absolute error (bp) | 11.9693 | 15.5671 | 12.5468 | 5.4910 | 8.7125 |
| Weighted comparison points, 492 cells | 242.5 | 219.5 | 224.0 | 263.5 | 211.0 |
| Cells within 10% | 184 | 153 | 161 | 206 | 158 |
| Cells within 25%, including within 10% | 301 | 286 | 287 | 321 | 264 |
| Mean stocks per reporting cohort | 2300.6 | 1847.5 | 2270.8 | 2300.4 | 2386.9 |
| Mean pairs per reporting cohort | 2013.4 | 1605.0 | 1986.5 | 2013.3 | 2092.8 |

The paper reports about **2,057 pairs**. The nonconstant sensitivity changes the volume-screen mean pair count from 2,013.42 to 2,013.28, yet materially affects the top ranks. Numerical proximity is not a criterion for promoting a variant to the default.

| Table 1B minimum month (%) | Prior strict-price | CIZ volume | SIZ volume | CIZ nonconstant | Original paper |
|---|---:|---:|---:|---:|---:|
| top5 | -13.2418 | -23.4955 | -23.4856 | -13.4394 | -12.6280 |
| top20 | -8.5593 | -7.3529 | -7.3529 | -7.3529 | -8.2180 |
| 101-120 | -3.8701 | -3.8867 | -3.8812 | -3.8812 | -4.2660 |
| all | -14.8203 | -14.8298 | -15.1205 | -14.8298 | -2.9510 |

**The all-pairs tail remains unresolved**: the nonconstant run still loses 14.8298% in its worst month, versus 2.9510% in the paper. Improving eight means does not reproduce the full return distribution, the supporting experiments or the factor regressions.

## Identified problems and paper references

- **Section 2.1, formation liquidity:** a closing bid–ask price does not imply that no transactions occurred. CRSP states that Nasdaq prices were always bid–ask averages before November 1, 1982 for NMS securities, and before June 15, 1992 for SmallCap securities. A price-type-only screen therefore changes historical coverage. [CRSP data descriptions](https://www.crsp.org/crsp_pdf/crsp-us-stock-indexes-databases-data-descriptions-guide-crspaccess/).
- **Section 2.1, total-return normalization:** the first formation date is the rebasing point. Its incoming return is not used; rejecting that stock solely for that missing return unnecessarily excludes it. Internal formation returns still must be present in the new `activity_common` diagnostic.
- **Section 2.2, delistings:** the new legacy SIZ import combines RET and DLRET exactly once, keeps separate terminal events absent from the daily file, and records its fallback for missing DLRET. CIZ continues to use its integrated delisting return. This is an explicit data-vintage comparison; the available legacy release is from December 2024, not the authors' original vintage.
- **Section 3.9, Table 9B:** WRDS supplied the missing daily share-adjustment factors and volume. Files with missing years, invalid factors, or conflicting observations fail validation. The no-recall control must reproduce cached trade logs and monthly returns before any recall result is reported.
- **Table 9B reporting:** removed unconditional success statements and unsupported explanations. The full 18-month volume threshold is explicitly retrospective; the 12-month formation-only threshold is reported separately. All 44 paper targets were checked against the attached working-paper PDF, printed p. 42.

## Acquired inputs

All observations remain local. Public query records contain dates, selected fields, row counts, file sizes and SHA-256 checksums.

| WRDS input | Period | Export rows | Record |
|---|---|---:|---|
| Legacy SIZ daily prices, returns, volume, historical share/exchange/SIC classifications | 1962–2002 | 57,599,940 | [query](../../data/metadata/queries/legacy_daily_1962_2002_query.json) |
| Legacy daily delisting events | 1962–2002 | 38,872 including empty outer-join rows | [query](../../data/metadata/queries/legacy_delistings_1962_2002_query.json) |
| CIZ daily volume and cumulative share-adjustment factors | 1962–2002 | 57,606,932 | [query](../../data/metadata/queries/ciz_volume_1962_2002_query.json) |

## Predeclared comparisons

1. Modern CIZ, restored volume-based screen, corrected execution and accounting.
2. Modern CIZ, observed activity (trade price **or** positive volume), with complete internal returns.
3. Legacy SIZ, the same volume-based screen and trading/accounting settings as comparison 1. Legacy common-share codes 10/11/12 are explicit and are not assumed to map perfectly to CIZ classifications.
4. Table 9B on the frozen strict-price selections: recall off; 18-month thresholds with re-entry on a new episode, immediate re-entry, and no re-entry; formation-only threshold with re-entry on a new episode.

These experiments distinguish source conventions and observable screening evidence. Parameters are not chosen by minimizing discrepancies from the paper.

Two additional liquidity sensitivities are predeclared after completing those comparisons: (5) CIZ volume-based eligibility excluding securities whose recorded formation returns are all zero, to measure the impact of completely static histories when historical volume is unavailable; (6) CIZ normal-share eligibility including closed-end funds, because Section 2.1 does not give share codes. Neither exclusion nor broadening is treated as an established paper rule, and both outcomes are reported regardless of fit.

A further source-attribution diagnostic is predeclared: hold the CIZ volume-screen pair ranks, formation-end price levels and formation standard deviations fixed, then replace only trading-period returns, terminal flags and data availability with SIZ. First require an exact CIZ control against both cached trade logs and monthly returns. This isolates trading-input effects from reselecting the universe; it is not a proposed paper specification or a claim that either source has the authors' vintage.

## Findings from the completed source audits

The strict-price result is **not** a verified implementation of the paper's “no non-trading days” rule. In the July 1963 cohort, 76 of the excluded stock rows have a missing incoming return on the rebasing day; the activity definition restores 75 eligible stocks. In July 1975 the strict screen excludes 1,750 volume-eligible stocks, including 1,741 Nasdaq stocks. In July 1985, excluded stocks include 35,966 bid–ask-priced rows with **positive recorded volume**. These diagnostics use prices/activity/missingness, not the target portfolio returns.

The legacy/CIZ comparison covers 1962, 1975, 1985, 1995, 2000 and 2002. Matched trade-price flags agree in all six years. Most matched returns agree too: the 99th percentile of absolute differences is zero through the 2000 audit year and about 0.000001 in 2002. Exceptions, share classifications and terminal-event timing remain material. For 2000, 900 matched returns differ by more than one basis point, 39,985 common-share flags disagree, and 1,916 terminal flags disagree. These differences mix source conventions, classification mapping and event timing; they cannot all be called vendor corrections.

CIZ uses integrated delisting returns. The separate SIZ importer combines RET and DLRET once, retains terminal events outside the daily file, and maps a non-trading delisting date to the next observed market date. Missing DLRET means zero incremental delisting return under the explicit last-price convention. SIZ codes 10/11/12 are not assumed to be an exact CIZ common-share mapping. Raw downloads are unchanged, and original CIZ caches were not overwritten.

## Source-return attribution on frozen selections

The CIZ control exactly reproduces **958 trade logs**, with **zero monthly return difference**. Each of the 32 portfolio/capital/delay/source series contains 474 reporting months. Switching only trading-period returns, terminal flags and data availability to SIZ changes each of the eight employed-capital means by **less than 0.12 bp**. The all-pairs one-day-wait minimum remains -14.8002% versus the paper's -2.9510%. On these fixed selections, trading-input differences do not explain the large residual.

| Paper reference | Portfolio | CIZ control (%) | SIZ trading-only (%) | Original paper (%) | SIZ minus CIZ (bp) |
|---|---|---:|---:|---:|---:|
| Table 1A | top5 | 1.1316 | 1.1317 | 1.3080 | +0.0126 |
| Table 1A | top20 | 1.2735 | 1.2723 | 1.4360 | -0.1107 |
| Table 1A | 101-120 | 1.0261 | 1.0264 | 1.0810 | +0.0363 |
| Table 1A | all | 1.0509 | 1.0505 | 1.1040 | -0.0440 |
| Table 1B | top5 | 0.4803 | 0.4804 | 0.7450 | +0.0081 |
| Table 1B | top20 | 0.7634 | 0.7628 | 0.8950 | -0.0577 |
| Table 1B | 101-120 | 0.7997 | 0.7996 | 0.7950 | -0.0134 |
| Table 1B | all | 0.7928 | 0.7927 | 0.7150 | -0.0174 |

Pair identities, ranks, formation-end normalized levels and standard deviations are deliberately frozen to CIZ. This is a controlled attribution experiment, not a full SIZ replication. Full SIZ runs separately recompute eligibility and formation quantities.

## Table 9B: executed, but the recall effect does not replicate

The newly acquired share-adjustment factors remove the input blocker. All **479 no-recall trade logs match** the frozen strict-price cache, with **zero monthly difference**. The full cohort/month/variant panel is checked for duplicate, missing and nonfinite returns before aggregation. All 44 paper targets were independently parsed from the attached PDF.

The primary recall interpretation closes a pair after high volume on its short leg, then waits for the spread to return inside the entry band before a new episode. Re-entry is not specified by the paper, so immediate re-entry and a rest-of-cohort lock are also retained. The literal formation-plus-trading volume threshold is retrospective: it uses future volumes. The formation-only threshold is a separate past-only sensitivity. At the December 2002 cutoff the last five cohort windows are shortened; their thresholds do not have a complete 18 months. Extending those thresholds into 2003 remains unvalidated.

| Portfolio | Our no-recall mean (%) | Our primary recall mean (%) | Paper no recall (%) | Paper recall (%) | Our decline (bp) | Paper decline (bp) |
|---|---:|---:|---:|---:|---:|---:|
| Top 5 | 1.0137 | 1.1889 | 0.7450 | 0.6190 | -17.52 | +12.60 |
| Top 20 | 1.1151 | 1.3837 | 0.8950 | 0.8540 | -26.86 | +4.10 |
| 101–120 | 0.8806 | 1.1962 | 0.7950 | 0.6650 | -31.55 | +13.00 |
| All | 0.7529 | 1.3736 | 0.7150 | 0.5850 | -62.08 | +13.00 |

The employed-capital effect has the opposite sign in all four portfolios. Only **4/44** primary targets are within 10%, and **14/44** within 25%. Committed-capital means fall to 0.4728%, 0.4731%, 0.3471%, and 0.3676%, versus paper values 0.304%, 0.347%, 0.296%, and 0.202%. Thus the employed-capital normalization matters materially; positive profits cannot be reported as reproducing the recall cost.

| Alternative | Top 5 mean (%) | Top 20 mean (%) | 101–120 mean (%) | All mean (%) | Targets within 10% / 25% |
|---|---:|---:|---:|---:|---|
| Immediate re-entry | 1.0640 | 1.2522 | 1.0133 | 0.9291 | 9/44; 17/44 |
| No re-entry during cohort | 0.7478 | 1.2807 | 0.9555 | 1.3074 | 5/44; 13/44 |
| Formation-only threshold | 1.1915 | 1.3820 | 1.3188 | 1.5489 | 6/44; 14/44 |
| Original paper | 0.6190 | 0.8540 | 0.6650 | 0.5850 | Reference |

The primary run recalls 1,421,723 of 1,871,083 trades (75.98%). This is simulated high-volume exposure, not an observed borrow-recall frequency. Its selection universe is frozen for attribution; it must not be combined with a different Table 1 baseline.

## Limits that remain open

- Neither available source is the authors' original CRSP vintage. Legacy SIZ is the final 2024 release, not a time capsule from 2002.
- Historical missing volume and bid–ask prices leave the formation universe uncertain. The `paper` profile name is retained for reproducibility of existing caches; it does not certify its strict-price screen. Select each audited universe explicitly.
- The period-level pair-count language and the active value-weighted book formula do not uniquely resolve idle capital, reinvestment and denominator timing. The fixed-dollar `period_cash`/`selected_cash` alternatives are reported separately, not substituted because a mean looks closer.
- All-pairs tail risk remains far from the paper, including the February 2000 loss. A passing trade-accounting identity does not explain that discrepancy.
- The custom reversal factor and proprietary SBBI vintage remain unavailable or unvalidated. French reversal is labeled a proxy. This cannot explain Table 1's unadjusted-return differences.
- Historical Table 6/9A and Figures 1–4 results in [the fidelity audit](FIDELITY_VALIDATION.md) remain tied to the strict-price universe. They were not relabeled as outcomes of the new source experiments. A separate legacy-SIZ Figure 1 check needs the 1961 formation supplement; that download was not completed while the browser host was locked.

## Exact reproduction

Run from the repository root after `pip install -e ".[dev]"`. Obtain licensed WRDS downloads using the committed query metadata and keep them in the local paths below. The existing CIZ daily/calendar inputs and public French factors are prerequisites; their acquisition is documented in [the accounting audit](ACCOUNTING_CORRECTIONS.md#data-and-provenance). Imports are deliberately atomic and refuse to replace an existing output directory.

```sh
export PYTHONPATH=src
python scripts/import_wrds_ui.py \
  --volume-csv data/raw/crsp_volume/ciz_volume_1962_2002.csv.gz \
  --volume-output data/interim/crsp/volume --first-year 1962 --last-year 2002
python scripts/import_legacy_wrds.py \
  --daily-csv data/raw/crsp_siz/legacy_daily_1962_2002.csv.gz \
  --delisting-csv data/raw/crsp_siz/legacy_delistings_1962_2002.csv.gz \
  --output data/processed/crsp_siz/daily --first-year 1962 --last-year 2002 \
  --common-codes 10 11 12

python scripts/03_replicate.py --specification paper --universe vol_common \
  --start 1963-02 --report-start 1963-07 --end 2002-12 --workers 1 \
  --cache-root data/processed/replication/overnight/volume_screen \
  --out-root results/replication/overnight/volume_screen
python scripts/03_replicate.py --specification paper --universe activity_common \
  --start 1963-02 --report-start 1963-07 --end 2002-12 --workers 1 \
  --cache-root data/processed/replication/overnight/activity_screen \
  --out-root results/replication/overnight/activity_screen
GGR_PROCESSED_DIR=data/processed/crsp_siz/daily \
  python scripts/03_replicate.py --specification paper --universe vol_common \
  --start 1963-02 --report-start 1963-07 --end 2002-12 --workers 1 \
  --cache-root data/processed/replication/overnight/siz_volume \
  --out-root results/replication/overnight/siz_volume
python scripts/03_replicate.py --specification paper --universe vol_common \
  --exclude-constant --start 1963-02 --report-start 1963-07 --end 2002-12 --workers 1 \
  --cache-root data/processed/replication/overnight/nonconstant \
  --out-root results/replication/overnight/nonconstant
python scripts/03_replicate.py --specification paper --universe vol_ns \
  --start 1963-02 --report-start 1963-07 --end 2002-12 --workers 1 \
  --cache-root data/processed/replication/overnight/normal_shares \
  --out-root results/replication/overnight/normal_shares

GGR_PROCESSED_DIR=data/processed/crsp_siz/daily \
  python scripts/03_replicate.py --specification paper --universe vol_common \
  --exclude-constant --start 1963-02 --report-start 1963-07 --end 2002-12 --workers 1 \
  --cache-root data/processed/replication/overnight/siz_nonconstant \
  --out-root results/replication/overnight/siz_nonconstant
python scripts/03_replicate.py --specification paper --universe informative_common \
  --start 1963-02 --report-start 1963-07 --end 2002-12 --workers 1 \
  --cache-root data/processed/replication/overnight/informative \
  --out-root results/replication/overnight/informative

python scripts/audit_liquidity.py \
  --output results/replication/overnight/liquidity_audit.json
python scripts/audit_liquidity.py \
  --static-reference-cache data/processed/replication/overnight/volume_screen \
  --static-screen-cache data/processed/replication/overnight/nonconstant \
  --output results/replication/overnight/static_history_audit.json
python scripts/audit_data_vintages.py \
  --siz data/processed/crsp_siz/daily \
  --output results/replication/overnight/vintage_audit.json
python scripts/replay_data_vintage.py \
  --cache data/processed/replication/overnight/volume_screen \
  --ciz data/processed/crsp/daily --siz data/processed/crsp_siz/daily \
  --output results/replication/overnight/vintage_replay

# Requires the preserved strict-price cache, generated by make validate-fidelity.
python scripts/claims/table9b_recalls.py run \
  --cache-root data/processed/replication/fidelity/combined \
  --out-root results/replication/overnight/table9b \
  --raw-dir data/interim/crsp/volume \
  --report-dir results/replication/overnight/table9b/report \
  --start 1963-02 --end 2002-12 --workers 1
# Use the `table` subcommand with the same options to validate/rebuild only the report.

python -m pytest -q
```

To validate the complete historical outputs without rebuilding:

```sh
PYTHONPATH=src python - <<'PY'
import json
from pathlib import Path
from project.fidelity import validate_outputs
for name in ('volume_screen', 'activity_screen', 'siz_volume', 'nonconstant',
             'normal_shares', 'siz_nonconstant', 'informative'):
    out = Path('results/replication/overnight') / name
    cache = Path('data/processed/replication/overnight') / name
    evidence = validate_outputs(out, cache)
    (out / 'validation.json').write_text(json.dumps(evidence, indent=2, allow_nan=False) + '\n')
    print(name, evidence['months'], evidence['cohorts_including_warmup'])
PY
```

Every specification and output directory is retained, including worse fits. Public files contain source/query metadata and authored audit findings; licensed observations and generated numerical result files remain local.

## Additional validation prompted by the static-history audit

The exclusion audit identified 12 securities across 62 cohorts (69 stock-cohort exclusions, 1975–1990), with 17,422 formation rows. All returns are recorded zeros, all prices are bid–ask observations, and none of these returns are missing. However, **3,289 rows have positive volume**; the other 14,133 have unknown volume. Consequently, these exclusions cannot all be described as proven non-trading securities.

Before inspecting their outcomes, two further checks were specified: (7) repeat the same nonconstant sensitivity with the independently imported SIZ panel; (8) use `informative_common`, removing a completely static history only if it has neither a positive-volume observation nor a transaction-price observation anywhere in formation. The second check deliberately retains static histories with observable trading evidence, whether or not doing so improves the published-target comparison. Both remain sensitivity analyses, not recovered author rules.


## Final cross-checks completed before the cutoff

The two checks specified after the static-history audit both finished before the overnight cutoff. Legacy SIZ with the same static exclusion has **6.1808 bp** average absolute error across the eight Table 1 means. The narrower CIZ `informative_common` rule retains static histories with any observed transaction price or positive volume and has **5.4384 bp** error. This is nearly unchanged from the broader CIZ exclusion (5.4318 bp), despite deliberately preserving observable activity. These are corroborating sensitivities, not evidence that either rule was used by the authors. No new default is selected by closeness to published targets.

All values in the next table are monthly percent. The CIZ nonconstant column is the earlier sensitivity, shown alongside both final checks and the paper.

| Paper reference | Portfolio | Earlier CIZ nonconstant | Final SIZ nonconstant | Final CIZ activity-preserving static filter | Original paper |
|---|---|---:|---:|---:|---:|
| Table 1A | top5 | 1.3183 | 1.3030 | 1.3181 | 1.3080 |
| Table 1A | top20 | 1.3381 | 1.3164 | 1.3380 | 1.4360 |
| Table 1A | 101-120 | 1.0268 | 1.0079 | 1.0223 | 1.0810 |
| Table 1A | all | 1.0515 | 1.0545 | 1.0518 | 1.1040 |
| Table 1B | top5 | 0.6768 | 0.6664 | 0.6769 | 0.7450 |
| Table 1B | top20 | 0.8271 | 0.8181 | 0.8271 | 0.8950 |
| Table 1B | 101-120 | 0.8000 | 0.7847 | 0.7963 | 0.7950 |
| Table 1B | all | 0.7935 | 0.7964 | 0.7938 | 0.7150 |

| Diagnostic, not a paper statistic | SIZ nonconstant | CIZ activity-preserving static filter |
|---|---:|---:|
| Panel A mean absolute error (bp) | 6.1814 | 5.4732 |
| Panel B mean absolute error (bp) | 6.1802 | 5.4037 |
| Weighted comparison points, 492 cells | 248.5 | 264.5 |
| Cells within 10% | 189 | 208 |
| Cells within 25%, including within 10% | 308 | 321 |
| Mean stocks per reporting cohort | 2270.6751 | 2300.4557 |
| Mean pairs per reporting cohort | 1986.3608 | 2013.3101 |

| Table 1B minimum month (%) | Earlier CIZ nonconstant | Final SIZ nonconstant | Final CIZ activity-preserving static filter | Original paper |
|---|---:|---:|---:|---:|
| top5 | -13.4394 | -13.4394 | -13.4394 | -12.6280 |
| top20 | -7.3529 | -7.3529 | -7.3529 | -8.2180 |
| 101-120 | -3.8812 | -3.8812 | -3.8867 | -4.2660 |
| all | -14.8298 | -15.1205 | -14.8298 | -2.9510 |

Both checks pass the complete 479-cohort / 474-month / 9,944-date validation, finite-output checks and Table 1B/Table 7 identity to 1.1e-16. The activity-preserving filter has 208/492 cells within 10% and 321/492 within 25%; 171 cells still miss by more than 25%. Its worst all-pairs month remains -14.8298%, versus -2.9510% in the paper. The narrower filter therefore supports the mean-return finding without resolving the tail discrepancy.

## Validation evidence

The full local suite passes with **364 passed, 14 skipped** on Python 3.13.9. Historical runs are separate actual executions, not inferred from unit tests. The recall report was rebuilt and revalidated from all 479 cached cohorts after adding completeness checks. New modules pass Ruff; modified existing files add no new lint findings relative to the prior commit. `git diff --check` passes. There is no repository GitHub Actions workflow.

Source SHA-256 and file-size checks passed for all three raw archives. Every one of the 82 imported yearly volume/SIZ files matches its recorded checksum. Expected NumPy/BLAS and font-cache warnings remain visible in local logs; the full output checks reject nonfinite primary statistics. These checks establish data/control integrity, not agreement with the paper.

The overnight research window ended at 07:00 America/New_York on November 2, 2026. The proposed Table 9B repeat on nonconstant selections was **not executed before the cutoff**. Its CLI now supports an explicitly validated source universe/static-history setting, but tests of that interface are not evidence of a completed experiment. All Table 9B results above are from the frozen strict-price selections; their recall returns must not be combined with the new Table 1 baselines. The 1961 SIZ supplement and exact proprietary factors also remain incomplete. No further experiments were launched after the cutoff.
