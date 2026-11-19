# Code audit, round 9: `src/project/` and the core scripts

Scope: the 18 modules under `src/project/` (3,962 LOC) and `scripts/01_get_data.py`,
`02_build_dataset.py`, `03_replicate.py`, `04_extend.py`, `replication_score.py`. Base
`personal/main` = 2f92de8. Nothing here changes a result: the shipped check is 411.0 of 865
before and after, byte for byte (section 9).

## 1. Summary

- **One duplicate helper removed**, one folded into its twin: `scripts/03_replicate.py`
  carried a private copy of `project.table7.monthly_autocorr` and a private copy of the
  overlap average that `project.table7.strategy_series` already performs. Both now have one
  home in `project.table7`; the driver keeps a five-line wrapper for the second because its
  only difference is which weights to pass. Net **-11 lines** (24 added, 35 deleted), and one
  fewer place to change the overlap average.
- **No dead code found.** All 120 top-level symbols are reachable from something: 30 run on
  the 411.0 path itself, 88 are reachable from the build or CLI path that produces the cache
  the check reads, and 2 are reachable only from tests (kept, section 6).
- **No flag is removable.** Every one of the driver's 39 flags is named either by a report
  page that names it as the way to reproduce a recorded reading, or by a call site inside
  another script, or both (section 7).

## 2. Method

1. **Inventory.** Every top-level `def`/`class` in the 18 modules was extracted with `ast`
   (120 symbols: 1 class, 119 functions) with its line span.
2. **Call sites.** An AST index over all 18 modules, every file under `scripts/` and `tests/`,
   and `conftest.py` recorded, for each name, the file, line and enclosing function of each
   load. Attribute access is indexed too, so `rep._strategy_series(...)` in
   `scripts/experiments/` is a call site of the driver's function. This is stricter than a
   `rg` on the bare name, which also matches a same-named symbol in another module.
3. **Runtime evidence for the shipped path.** The conformance run was repeated under a
   `sys.setprofile` hook that records every `src/project` function entered
   (`.private/audit/trace_run.py`). 30 symbols execute on the 411.0 path; that set is
   evidence, not inference, and is what the LIVE verdict below means.
4. **Doc references.** Each symbol's name was counted in `report/**/*.md` and `README.md`, so
   a keep verdict can name the page that documents it.
5. **Verdicts.** LIVE = executed in the traced 411.0 run. LIVE-PROD = not executed there but
   reachable from the code that builds the cohort cache or the import/CLI scripts the make
   targets run. TEST-ONLY = referenced only from `tests/`. DEAD = no call site anywhere; none
   was found.

The classification table in section 4 is generated from that evidence, not written by hand.

## 3. What the classification says

The three build-time engines (`models.simulate_cohort`, `features.select_pairs`,
`evaluation.portfolio_monthly` and their helpers) do not run on the 411.0 path, because that
path aggregates a prebuilt cache (`--aggregate-only`, "0 to build"). They are not removable:
the cache the check reads is their output, and `scripts/rebuild_manifest.json` pins their
hashes as the cache's generation. The same is true of `data.formation_universe`,
`data.load_daily` and the sector map: live for `--force`, dead for `--aggregate-only`.

That split is why the only deletions here are duplicates. A reporting-time duplicate can be
folded away with the byte-identity of the check as proof; a formation-time duplicate cannot be
touched this round at all, because changing it would invalidate the cached cohorts and the
round forbids a rebuild.

## 4. Classification table

Verdict, call site and doc mentions for every top-level symbol in scope. `-` means the symbol
is named in no report page; the code is then its only documentation.

| file | symbol | LOC | verdict | call site / evidence | doc pages naming it |
|---|---|---:|---|---|---|
| `data.py` | `pgpass_path` | 2 | LIVE-PROD | `src/project/data.py:56` in `wrds_username` | - |
| `data.py` | `_split_pgpass` | 16 | LIVE-PROD | `src/project/data.py:59` in `wrds_username` | - |
| `data.py` | `wrds_username` | 11 | LIVE-PROD | `src/project/data.py:82` in `wrds_connection` | - |
| `data.py` | `wrds_connection` | 28 | LIVE-PROD | `scripts/01_get_data.py:238` in `__init__` | COMMON_RULES.md x4, DATA_REVIEW.md x1 |
| `data.py` | `query_to_parquet` | 8 | LIVE-PROD | `report/archive/data_review/B_checks.py:256` in `run` | COMMON_RULES.md x1 |
| `data.py` | `pin_arrow_threads` | 21 | LIVE-PROD | `scripts/03_replicate.py:3402` in `build_shard` | - |
| `data.py` | `processed_source_identity` | 14 | LIVE | traced in the 411.0 run | REVIEW_NOTES.md x1 |
| `data.py` | `universe_flags` | 8 | LIVE-PROD | `src/project/data.py:471` in `formation_universe` | METHOD.md x1, REVIEW_NOTES.md x1 |
| `data.py` | `day_rule_flags` | 9 | LIVE-PROD | `src/project/data.py:474` in `formation_universe` | - |
| `data.py` | `_universe_panel_columns` | 9 | LIVE-PROD | `src/project/data.py:236` in `formation_columns` | - |
| `data.py` | `formation_columns` | 11 | LIVE-PROD | `src/project/data.py:464` in `formation_universe` | - |
| `data.py` | `_clean_year` | 52 | LIVE-PROD | `src/project/import_ui.py:197` in `import_daily_csv` | REVIEW_NOTES.md x3, METHOD.md x1 |
| `data.py` | `_write_processed` | 11 | LIVE-PROD | `src/project/import_ui.py:198` in `import_daily_csv` | - |
| `data.py` | `build_daily_panel` | 24 | LIVE-PROD | `scripts/02_build_dataset.py:33` in `main` | METHOD.md x1 |
| `data.py` | `_as_date` | 4 | LIVE | traced in the 411.0 run | - |
| `data.py` | `_year_files` | 6 | LIVE | traced in the 411.0 run | - |
| `data.py` | `load_daily` | 41 | LIVE | traced in the 411.0 run | METHOD.md x2 |
| `data.py` | `trading_calendar` | 39 | LIVE | traced in the 411.0 run | METHOD.md x1 |
| `data.py` | `formation_universe` | 57 | LIVE-PROD | `scripts/03_replicate.py:1110` in `build_cohort` | METHOD.md x4, REVIEW_NOTES.md x3 |
| `data.py` | `issuer_map` | 18 | LIVE-PROD | `scripts/03_replicate.py:1041` in `_issuer_series` | - |
| `edition1999.py` | `mark` | 4 | LIVE-PROD | `src/project/edition1999.py:132` in `table1` | name too generic to count |
| `edition1999.py` | `_moments` | 7 | LIVE-PROD | `src/project/edition1999.py:128` in `table1` | - |
| `edition1999.py` | `cohort_names` | 2 | LIVE-PROD | `src/project/edition1999.py:178` in `score_cohort_dir` | name too generic to count |
| `edition1999.py` | `_six_month` | 3 | LIVE-PROD | `src/project/edition1999.py:126` in `table1` | - |
| `edition1999.py` | `table1` | 20 | LIVE-PROD | `src/project/edition1999.py:179` in `score_cohort_dir` | name too generic to count |
| `edition1999.py` | `table2a` | 25 | LIVE-PROD | `src/project/edition1999.py:179` in `score_cohort_dir` | name too generic to count |
| `edition1999.py` | `table2b` | 11 | LIVE-PROD | `src/project/edition1999.py:180` in `score_cohort_dir` | name too generic to count |
| `edition1999.py` | `score_cohort_dir` | 5 | LIVE-PROD | `scripts/edition_1999.py:37` in `main` | - |
| `edition1999.py` | `summarize` | 12 | LIVE-PROD | `src/project/edition1999.py:198` in `format_report` | name too generic to count |
| `edition1999.py` | `format_report` | 21 | LIVE-PROD | `scripts/edition_1999.py:39` in `main` | name too generic to count |
| `evaluation.py` | `_resolve_ranks` | 7 | LIVE-PROD | `src/project/evaluation.py:242` in `portfolio_legs` | - |
| `evaluation.py` | `_trade_days` | 12 | LIVE-PROD | `src/project/evaluation.py:144` in `_open_mask` | - |
| `evaluation.py` | `_open_mask` | 17 | LIVE-PROD | `src/project/evaluation.py:376` in `portfolio_daily` | - |
| `evaluation.py` | `_payoffs_and_accounts` | 14 | LIVE-PROD | `src/project/evaluation.py:365` in `portfolio_daily` | - |
| `evaluation.py` | `_leg_arrays` | 34 | LIVE-PROD | `src/project/evaluation.py:246` in `portfolio_legs` | REVIEW_NOTES.md x1 |
| `evaluation.py` | `portfolio_legs` | 24 | LIVE-PROD | `scripts/03_replicate.py:1196` in `build_cohort` | REVIEW_NOTES.md x2, METHOD.md x1 |
| `evaluation.py` | `_has_trade_log` | 8 | LIVE-PROD | `src/project/evaluation.py:358` in `portfolio_daily` | REVIEW_NOTES.md x3 |
| `evaluation.py` | `_vw_legs` | 23 | LIVE-PROD | `src/project/evaluation.py:368` in `portfolio_daily` | REVIEW_NOTES.md x1 |
| `evaluation.py` | `portfolio_daily` | 108 | LIVE-PROD | `src/project/evaluation.py:476` in `portfolio_monthly` | REVIEW_NOTES.md x10, METHOD.md x3 |
| `evaluation.py` | `_book_base_series` | 42 | LIVE-PROD | `src/project/evaluation.py:373` in `portfolio_daily` | - |
| `evaluation.py` | `cohort_monthly` | 13 | LIVE-PROD | `src/project/evaluation.py:476` in `portfolio_monthly` | REVIEW_NOTES.md x2, METHOD.md x1 |
| `evaluation.py` | `portfolio_monthly` | 43 | LIVE-PROD | `scripts/03_replicate.py:1194` in `build_cohort` | REVIEW_NOTES.md x3, METHOD.md x2 |
| `evaluation.py` | `overlap_average` | 22 | LIVE | traced in the 411.0 run | REVIEW_NOTES.md x3, METHOD.md x1 |
| `evaluation.py` | `weighted_overlap_average` | 37 | LIVE-PROD | `src/project/table7.py:80` in `strategy_series` | REVIEW_NOTES.md x1 |
| `evaluation.py` | `size_deciles` | 27 | LIVE-PROD | `src/project/evaluation.py:634` in `restrict_to_size_deciles` | METHOD.md x2, REVIEW_NOTES.md x1 |
| `evaluation.py` | `restrict_to_size_deciles` | 44 | LIVE-PROD | `scripts/03_replicate.py:1118` in `build_cohort` | - |
| `evaluation.py` | `composition_stats` | 84 | LIVE-PROD | `scripts/03_replicate.py:1221` in `build_cohort` | REVIEW_NOTES.md x4, METHOD.md x1 |
| `evaluation.py` | `summary_stats` | 43 | LIVE | traced in the 411.0 run | REVIEW_NOTES.md x5, METHOD.md x1 |
| `evaluation.py` | `trading_stats` | 51 | TEST-ONLY | `tests/test_evaluation.py:252` in `test_top2_portfolio_hand_calc` | METHOD.md x1, REVIEW_NOTES.md x1 |
| `evaluation.py` | `_month_edges` | 9 | LIVE-PROD | `src/project/evaluation.py:853` in `_window_censored` | - |
| `evaluation.py` | `_window_censored` | 25 | LIVE-PROD | `src/project/evaluation.py:951` in `trading_components` | REVIEW_NOTES.md x1 |
| `evaluation.py` | `_cached_censored_flags` | 48 | LIVE-PROD | `src/project/evaluation.py:929` in `_completed_components` | - |
| `evaluation.py` | `_completed_components` | 24 | LIVE | traced in the 411.0 run | - |
| `evaluation.py` | `trading_components` | 26 | LIVE-PROD | `src/project/evaluation.py:817` in `trading_stats` | METHOD.md x1, REVIEW_NOTES.md x1 |
| `evaluation.py` | `trading_stats_from_components` | 33 | LIVE | traced in the 411.0 run | REVIEW_NOTES.md x1, S7_SUPPORT.md x1 |
| `factors.py` | `_monthly_block` | 26 | LIVE | traced in the 411.0 run | - |
| `factors.py` | `_csv_member` | 4 | LIVE | traced in the 411.0 run | - |
| `factors.py` | `_french_text` | 9 | LIVE | traced in the 411.0 run | - |
| `factors.py` | `_txt_monthly_block` | 36 | LIVE | traced in the 411.0 run | REVIEW_NOTES.md x1 |
| `factors.py` | `vintage` | 3 | LIVE | traced in the 411.0 run | name too generic to count |
| `factors.py` | `set_vintage` | 6 | LIVE | traced in the 411.0 run | REVIEW_NOTES.md x1 |
| `factors.py` | `vintage_dir` | 6 | LIVE | traced in the 411.0 run | REVIEW_NOTES.md x1 |
| `factors.py` | `load_factors` | 30 | LIVE | traced in the 411.0 run | - |
| `factors.py` | `load_losers_only` | 18 | LIVE | traced in the 411.0 run | - |
| `factors.py` | `factor_regression` | 15 | LIVE | traced in the 411.0 run | REVIEW_NOTES.md x2, TABLE7_REGRESSIONS.md x1 |
| `factors.py` | `factor_tstats` | 22 | LIVE | traced in the 411.0 run | REVIEW_NOTES.md x4, OPEN_QUESTIONS_ROUNDS.md x2 |
| `factors.py` | `factor_residuals` | 6 | LIVE | traced in the 411.0 run | - |
| `factors.py` | `_month_end` | 2 | LIVE | traced in the 411.0 run | - |
| `factors.py` | `small_company_stocks` | 43 | LIVE | traced in the 411.0 run | - |
| `factors.py` | `load_ibbotson_factors` | 31 | LIVE | traced in the 411.0 run | - |
| `features.py` | `normalized_prices` | 13 | LIVE | traced in the 411.0 run | METHOD.md x2, REVIEW_NOTES.md x2 |
| `features.py` | `ssd_matrix` | 30 | TEST-ONLY | `tests/test_features.py:45` in `test_ssd_matches_brute_force` | METHOD.md x2, REVIEW_NOTES.md x2 |
| `features.py` | `_nearest_neighbours` | 49 | LIVE-PROD | `src/project/features.py:144` in `select_pairs` | - |
| `features.py` | `select_pairs` | 70 | LIVE-PROD | `src/project/features.py:229` in `select_pairs_within_groups` | METHOD.md x4, REVIEW_NOTES.md x2 |
| `features.py` | `demote_frozen_pairs` | 24 | LIVE-PROD | `scripts/03_replicate.py:1132` in `build_cohort` | - |
| `features.py` | `select_pairs_within_groups` | 24 | LIVE-PROD | `scripts/03_replicate.py:1137` in `build_cohort` | METHOD.md x2, REVIEW_NOTES.md x1 |
| `import_ui.py` | `import_volume_csv` | 90 | LIVE-PROD | `scripts/import_wrds_ui.py:35` in `main` | - |
| `import_ui.py` | `file_sha256` | 6 | LIVE-PROD | `src/project/issuer_header.py:31` in `extract_header` | - |
| `import_ui.py` | `import_daily_csv` | 86 | LIVE-PROD | `scripts/import_wrds_ui.py:29` in `main` | - |
| `import_ui.py` | `import_calendar` | 15 | LIVE-PROD | `scripts/import_wrds_ui.py:27` in `main` | - |
| `import_ui.py` | `import_monthly_csv` | 39 | LIVE-PROD | `scripts/import_wrds_ui.py:32` in `main` | - |
| `issuer_header.py` | `extract_header` | 21 | LIVE-PROD | `scripts/build_issuer_header.py:12` in `None` | - |
| `legacy_import.py` | `legacy_numeric` | 6 | LIVE-PROD | `src/project/legacy_import.py:35` in `legacy_returns` | - |
| `legacy_import.py` | `legacy_returns` | 6 | LIVE-PROD | `src/project/legacy_import.py:50` in `prepare_delistings` | - |
| `legacy_import.py` | `prepare_delistings` | 20 | LIVE-PROD | `src/project/legacy_import.py:108` in `import_legacy_csv` | - |
| `legacy_import.py` | `clean_legacy_year` | 33 | LIVE-PROD | `src/project/legacy_import.py:153` in `import_legacy_csv` | - |
| `legacy_import.py` | `import_legacy_csv` | 69 | LIVE-PROD | `scripts/import_legacy_wrds.py:19` in `main` | - |
| `models.py` | `CohortResult` | 23 | LIVE | traced in the 411.0 run | METHOD.md x3 |
| `models.py` | `_empty_result` | 12 | LIVE-PROD | `src/project/models.py:380` in `simulate_cohort` | - |
| `models.py` | `_simulate_kernel` | 183 | LIVE-PROD | `src/project/models.py:419` in `simulate_cohort` | - |
| `models.py` | `_last_valid_rows` | 6 | LIVE-PROD | `src/project/models.py:389` in `simulate_cohort` | - |
| `models.py` | `simulate_cohort` | 185 | LIVE-PROD | `scripts/03_replicate.py:1186` in `build_cohort` | REVIEW_NOTES.md x5, METHOD.md x4 |
| `plotting.py` | `position_indicator` | 13 | LIVE | traced in the 411.0 run | METHOD.md x1, REVIEW_NOTES.md x1 |
| `plotting.py` | `plot_pair_trading_period` | 33 | LIVE | traced in the 411.0 run | - |
| `recalls.py` | `adjusted_volume` | 13 | LIVE-PROD | `src/project/import_ui.py:94` in `import_volume_csv` | REVIEW_NOTES.md x1 |
| `recalls.py` | `volume_thresholds` | 16 | LIVE-PROD | `src/project/recalls.py:79` in `high_volume_days` | - |
| `recalls.py` | `high_volume_days` | 25 | LIVE-PROD | `scripts/claims/table9b_recalls.py:309` in `recall_flags` | - |
| `recalls.py` | `rolling_volume_thresholds` | 21 | LIVE-PROD | `scripts/claims/table9b_recalls.py:308` in `recall_flags` | REVIEW_NOTES.md x1 |
| `sectors.py` | `default_panel_dir` | 15 | LIVE-PROD | `src/project/sectors.py:70` in `default_cache_path` | - |
| `sectors.py` | `default_cache_path` | 11 | LIVE-PROD | `src/project/sectors.py:139` in `_cache_path_for` | - |
| `sectors.py` | `sector_of` | 20 | LIVE-PROD | `src/project/sectors.py:277` in `sectors_for` | METHOD.md x3, REVIEW_NOTES.md x2 |
| `sectors.py` | `resolve_sic` | 16 | LIVE-PROD | `src/project/sectors.py:275` in `sectors_for` | METHOD.md x1 |
| `sectors.py` | `_panel_signature` | 7 | LIVE-PROD | `src/project/sectors.py:224` in `earliest_known_sic` | - |
| `sectors.py` | `_cache_path_for` | 13 | LIVE-PROD | `src/project/sectors.py:223` in `earliest_known_sic` | - |
| `sectors.py` | `_replace_atomically` | 13 | LIVE-PROD | `src/project/sectors.py:178` in `_write_cache` | - |
| `sectors.py` | `_write_cache` | 22 | LIVE-PROD | `src/project/sectors.py:253` in `earliest_known_sic` | - |
| `sectors.py` | `_read_cache` | 18 | LIVE-PROD | `src/project/sectors.py:231` in `earliest_known_sic` | - |
| `sectors.py` | `earliest_known_sic` | 58 | LIVE-PROD | `scripts/03_replicate.py:994` in `_sic_fallbacks` | REVIEW_NOTES.md x2, METHOD.md x1 |
| `sectors.py` | `header_sic` | 7 | LIVE-PROD | `scripts/03_replicate.py:989` in `_sic_fallbacks` | METHOD.md x1 |
| `sectors.py` | `sectors_for` | 9 | LIVE-PROD | `scripts/03_replicate.py:1134` in `build_cohort` | METHOD.md x2 |
| `specification.py` | `validate_cache_identity` | 7 | LIVE-PROD | `scripts/claims/table7.py:349` in `build` | REVIEW_NOTES.md x1 |
| `table7.py` | `monthly_autocorr` | 11 | LIVE-PROD | `src/project/table7.py:143` in `performance_rows` | - |
| `table7.py` | `strategy_series` | 8 | LIVE-PROD | `src/project/table7.py:101` in `book_series` | - |
| `table7.py` | `book_series` | 18 | LIVE-PROD | `scripts/claims/recall_diagnostic.py:564` in `book_changes` | REVIEW_NOTES.md x1 |
| `table7.py` | `portfolio_series` | 13 | LIVE-PROD | `scripts/claims/table7.py:134` in `portfolio_series` | - |
| `table7.py` | `excess` | 9 | LIVE | traced in the 411.0 run | name too generic to count |
| `table7.py` | `performance_rows` | 11 | LIVE-PROD | `scripts/claims/table7.py:144` in `performance_rows` | - |
| `table7.py` | `regression_rows` | 13 | LIVE | traced in the 411.0 run | - |
| `vintage_audit.py` | `compare_year` | 22 | LIVE-PROD | `src/project/vintage_audit.py:45` in `main` | - |
| `vintage_audit.py` | `main` | 13 | LIVE-PROD | `scripts/cell_margins.py:178` in `None` | name too generic to count |

Two caveats on the table. The trace was taken on the **base** tree, and it records `src/project`
frames only: a driver function (none of which is in the 120) never appears as LIVE, so a
reporting helper reached only through the driver shows up as LIVE-PROD on the strength of its
call site. After 5.1 the driver's three serial-correlation calls land on
`table7.monthly_autocorr`, so that row is on the shipped path in the tree this branch leaves
behind, not just in principle. LIVE-PROD therefore means "reachable, with a named call site",
not "cold".


## 5. Removed

### 5.1 `scripts/03_replicate.py::_monthly_autocorr` (11 lines) - duplicate

- **Verdict:** duplicate of `project.table7.monthly_autocorr`, which is 11 lines with the same
  body (`dropna`, `len <= 2 -> nan`, reindex to `date_range(..., freq="ME")`, `autocorr(lag=1)`)
  and the same docstring. The two copies were line-for-line the same computation.
- **Evidence:** the surviving name is the one already on the shipped path:
  `project.table7.monthly_autocorr` is called by `table7.performance_rows` (Table 7's
  `serial_correlation` row) and was already imported by nothing in the driver. The private
  copy had 4 call sites, all in `scripts/03_replicate.py`: `write_risk_tables` (Table 4's
  equity-premium serial correlation), `write_outputs` (Table 1 Panel A "monthly serial
  correlation"), and twice in the Table 8 VaR block.
- **Change:** the 4 call sites now call `monthly_autocorr`; the private copy is deleted;
  `_daily_autocorr`'s docstring, which called the monthly one "the counterpart of
  `_monthly_autocorr`", now names `monthly_autocorr`.
- **Tests:** none covered either copy (no test mentions `monthly_autocorr`), so nothing needed
  rewriting; the differential probe in section 9 covers it instead.
- **Flags:** not flag-reachable; both copies were on the default path.

### 5.2 `scripts/03_replicate.py::_strategy_series` body (17 lines) - duplicate, folded

- **Verdict:** the body was the same computation as `project.table7.strategy_series` (build the
  per-cohort monthly series, `overlap_average`, drop months after `end_ts`). The only
  difference was that the driver's copy also chose per-cohort weights for the
  `--cohort-weights` reading.
- **Evidence:** `project.table7.strategy_series` is the shipped path for the Table 7 page
  (`book_series`, `portfolio_series`); the driver's copy was the shipped path for Table 1/2
  (`aggregate`), Table 3, and the Table 9 aggregates - 7 call sites, plus 3 in
  `scripts/experiments/{table3_sectors,claim_sensitivity}.py`, which call it as
  `rep._strategy_series` and are out of this contract's scope, so the name is kept.
- **Change:** `project.table7.strategy_series` gained `weights: dict | None = None` and now
  performs the weighted branch itself; its two existing call sites are unchanged (the
  parameter defaults to today's behaviour). The driver's `_strategy_series` is now a five-line
  wrapper that picks the weights and delegates. The `weighted_overlap_average` import left the
  driver with the body - its only use.
- **Tests:** none referenced either function; the shipped-path test
  `tests/test_replicate.py::test_aggregate_daily_overlap_average_is_the_equal_weighted_mean`
  exercises the wrapper end to end through `rep.aggregate`, and still passes.
- **Why this is not churn:** the surviving function is the more-documented one (it is a public
  name in the module the Table 7 page reads) and the driver loses its copy of the months
  construction. A rename on the live path would have been churn; removing a second
  implementation of a shipped computation is the shrink this round asks for.

### 5.3 Not removed, and why

Two `--cohort-weights` code paths become dormant when the flag is at its default but stay:
`evaluation.weighted_overlap_average` (37 lines) and `_cohort_weights_for` /
`COHORT_WEIGHTS` in the driver. Their reading is not rejected - `claims/FULLSET_RESCORE.md`
row S4b (`--cohort-weights selected`, 411.5) and `claims/NEAR_MISS_CENSUS.md` combinations
C1-C3 name the flag as their reproducing path, and `FULLSET_RESCORE.md` describes what
`_strategy_series` does under it. Deletion rule (b) therefore blocks removing them.

## 6. Kept though unreferenced by production code

| symbol | LOC | why it stays |
|---|---:|---|
| `evaluation.trading_stats` | 51 | TEST-ONLY by call sites: the driver composes `trading_components` + `trading_stats_from_components` itself. It is the documented specification of Table 2 Panel A's six rows (the paper's values for each row, and why only completed windows enter the moments), named by `METHOD.md` and listed as read-checked against the spec in `REVIEW_NOTES` section 2. Deleting it would delete that documentation, not just code. Candidate for a later round if that prose is moved first. |
| `features.ssd_matrix` | 30 | TEST-ONLY by call sites, but it is the reference implementation the fast path is checked against: `_nearest_neighbours` states it computes "the same arithmetic ... so every entry is bit-identical" and keeps the blocked form only to avoid n x n temporaries in the build. `METHOD.md` names it, and `REVIEW_NOTES` section 13 records the PR #1 fix it now guards (an empty window raising instead of returning zeros), so its tests are the regression guard for a logged bug. |
| `data.query_to_parquet` | 8 | Referenced from `report/archive/data_review/B_checks.py` (7 call sites) and mandated by `report/archive/data_review/COMMON_RULES.md` as the only way row-level samples are saved. |

`features._nearest_neighbours` is the deliberate non-consolidation in this area: it duplicates
`ssd_matrix`'s arithmetic on purpose, for memory, and says so in its docstring. Folding it into
`ssd_matrix` would hold ~130 MB of n x n temporaries per cohort and would change a pinned
formation file.



## 7. Flags audited

All 39 flags the driver accepts, with the number of report pages that name them and the number
of test files that use them. Every flag has a doc page or a call site: none is removable under
deletion rule (a)+(b). The three that no report page names are still used in code:
`--build-shard` by `run_jobs` (the child-process entry point) and by
`tests/test_replicate.py`; `--limit-cohorts` by `scripts/claims/table6_random_pairs.py`, which
passes it through; `--wait` by two test files and by every build (it selects the one-day wait).

| flag | doc pages naming it | test files |
|---|---|---|
| `--aggregate-only` | 5: FULLSET_RESCORE.md, METHOD.md, REVIEW_NOTES.md | 0 |
| `--build-shard` | 0 | 1 |
| `--cache-root` | 4: REVIEW_NOTES.md, S7_SUPPORT.md, TABLE6_READINGS.md | 1 |
| `--capital-base` | 3: FULLSET_RESCORE.md, NEAR_MISS_CENSUS.md, REVIEW_NOTES.md | 0 |
| `--cohort-weights` | 3: FULLSET_RESCORE.md, NEAR_MISS_CENSUS.md, REVIEW_NOTES.md | 0 |
| `--committed-capital` | 3: NEAR_MISS_CENSUS.md, REVIEW_NOTES.md, TABLE6_READINGS.md | 0 |
| `--delist-cache` | 4: REPLICATION_CHECK.md, REVIEW_NOTES.md, S7_SUPPORT.md | 0 |
| `--demote-frozen` | 3: FULLSET_RESCORE.md, NEAR_MISS_CENSUS.md, REVIEW_NOTES.md | 0 |
| `--demote-frozen-share` | 1: REVIEW_NOTES.md | 0 |
| `--end` | 1: METHOD.md | 1 |
| `--factor-vintage` | 4: NEAR_MISS_CENSUS.md, REVIEW_NOTES.md, S7_SUPPORT.md | 0 |
| `--force` | 4: METHOD.md, REVIEW_NOTES.md, SCORE_LOG.md | 2 |
| `--fresh-divergence` | 3: FULLSET_RESCORE.md, NEAR_MISS_CENSUS.md, REVIEW_NOTES.md | 0 |
| `--limit-cohorts` | 0 | 0 |
| `--long-delisting-loss` | 2: REPLICATION_CHECK.md, REVIEW_NOTES.md | 1 |
| `--max-stale-share` | 6: FULLSET_RESCORE.md, GAPS.md, METHOD.md | 0 |
| `--normalization` | 5: GAPS.md, METHOD.md, NEAR_MISS_CENSUS.md | 0 |
| `--out-root` | 7: RECALL_DIAGNOSTIC.md, REVIEW_NOTES.md, S7_SUPPORT.md | 2 |
| `--panel-a-cohorts` | 3: FULLSET_RESCORE.md, NEAR_MISS_CENSUS.md, REVIEW_NOTES.md | 0 |
| `--reversal-csv` | 1: REVIEW_NOTES.md | 0 |
| `--reversal-factor` | 6: GAPS.md, METHOD.md, REPLICATION_CHECK.md | 0 |
| `--same-issuer` | 5: GAPS.md, METHOD.md, NEAR_MISS_CENSUS.md | 0 |
| `--share-classes` | 5: FULLSET_RESCORE.md, GAPS.md, NEAR_MISS_CENSUS.md | 0 |
| `--share-classes-file` | 4: FULLSET_RESCORE.md, NEAR_MISS_CENSUS.md, REVIEW_NOTES.md | 0 |
| `--short-weights` | 8: GAPS.md, METHOD.md, NEAR_MISS_CENSUS.md | 1 |
| `--size-deciles-top` | 4: COVERAGE.md, REVIEW_NOTES.md, SCORE_LOG.md | 0 |
| `--start` | 2: METHOD.md, REVIEW_NOTES.md | 1 |
| `--steps` | 5: METHOD.md, README.md, REVIEW_NOTES.md | 1 |
| `--stride` | 1: RECALL_DIAGNOSTIC.md | 1 |
| `--table6-cache` | 5: COVERAGE.md, REPLICATION_CHECK.md, REVIEW_NOTES.md | 0 |
| `--table9a-cache` | 3: REPLICATION_CHECK.md, REVIEW_NOTES.md, S7_SUPPORT.md | 0 |
| `--table9b-cache` | 4: RECALL_DIAGNOSTIC.md, REPLICATION_CHECK.md, REVIEW_NOTES.md | 0 |
| `--telephone-sic` | 5: GAPS.md, METHOD.md, NEAR_MISS_CENSUS.md | 0 |
| `--trigger-mult` | 3: FULLSET_RESCORE.md, NEAR_MISS_CENSUS.md, REVIEW_NOTES.md | 0 |
| `--trigger-sigma` | 5: GAPS.md, METHOD.md, NEAR_MISS_CENSUS.md | 0 |
| `--universe` | 7: GAPS.md, METHOD.md, NEAR_MISS_CENSUS.md | 1 |
| `--wait` | 0 | 2 |
| `--waste-sic` | 3: GAPS.md, NEAR_MISS_CENSUS.md, REVIEW_NOTES.md | 1 |
| `--workers` | 12: CLAIM9_PRE1989.md, METHOD.md, NEAR_MISS_CENSUS.md | 1 |

## 8. The cache pin was already stale, and is left stale

`scripts/rebuild_manifest.json` and the copy in `scripts/score_wrapper.py` pin the hashes of the
code that produced the shipped cohort cache. Five of the ten pinned files already differ from
the pin at `personal/main` (`03_replicate.py`, `data.py`, `evaluation.py`, `features.py`,
`models.py`); this change adds `src/project/table7.py` to that set and touches nothing else that
is pinned.

It is **not** re-pinned here, deliberately. `score_wrapper.formation_changed` says why: the pin
records the code that built the cache, "it is not the code at HEAD", and "a stale pin is the
correct state ... it sends every evaluation to the rebuild tier instead of scoring a cache the
engine did not produce". Re-pinning would assert a generation this branch cannot verify, since
the five files above were already ahead of the cache when the round started. The operational
consequence is nil: `formation_changed()` already returned True at base, so this branch does not
downgrade anything that was not already downgraded. `tests/test_score_wrapper.py:91` skips with
the list of moved files, as it did at base. Whoever rebuilds the cache should re-pin both
copies together, as `SCORE_LOG.md` describes.

## 9. Verification

**Byte identity (the round's hard gate).** The pristine tree and the edited tree were each run
into the *same* out-root, so no path normalisation is involved:

```
# base tree (git show personal/main:... restored), out-root .private/r9_base_fresh
# edited tree, the same command and the same out-root, after the edits
diff -r .private/snapshot_base .private/r9_base_fresh      # -> no output
```

Every generated file matches byte for byte, `figure1.png` and `figure1.json` included, and both
runs print `Score: 411.0 of 865 compared cells`. The check also matches the committed
`report/replication/REPLICATION_CHECK.md` once the out-root string is normalised, at base and
after the change.

**The `--cohort-weights` branch is not exercised by that run** (the shipped reading is
`equal`), so the moved computation was also checked directly
(`.private/audit/equiv_probe.py`): the base body, copied verbatim, and
`project.table7.strategy_series` were compared on a two-cohort frame with an overlapping month,
at three weightings; they are equal in all three, the weightings demonstrably change the answer
(0.0175 equal vs 0.0193 and 0.0139 weighted), the driver's wrapper matches the base body with
the flag off and on, and `monthly_autocorr` reproduces the deleted private copy exactly.

**Tests.** `pytest -q`: 368 passed, 8 skipped, 0 failed - the same 8 skips as at base (5 need
`make benchmark` output, 2 need the CRSP panel, 1 is the cache pin above).

**Memory.** `free -g` showed 14 GB available; the gate run uses `--workers 1`.
