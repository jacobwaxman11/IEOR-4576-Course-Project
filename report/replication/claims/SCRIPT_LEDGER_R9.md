# One-off scripts ledger (round 9, R9-B)

Scope: every file under `scripts/` other than the six that R9-A owns (`01_get_data.py`,
`02_build_dataset.py`, `03_replicate.py`, `04_extend.py`, `replication_score.py`, `wrds_setup.py`).
That is **48 files**: 19 under `scripts/claims/` (14 scripts, 4 JSON data files and the
one markdown template `t6_template.md`), 12 under `scripts/experiments/`, and 17 more
under `scripts/` (14 scripts and 3 JSON data companions). 48 before, 43 after:
**5 retired, 0 merged, 0 added**.

## Method

Each file was inventoried for what it does, the commit that added it, what it reads and writes, and
who names it today. The reference count is the number of tracked files that mention the file's stem,
searched from the worktree root with the stem on word boundaries so that `table7` does not match
`table7_paper`:

```
rg -l "(^|[^A-Za-z0-9_])STEM([^A-Za-z0-9_]|$)" -g '!data/**' -g '!.private/**' -g '!.review/**' .
```

The file itself and this ledger are excluded from every count; `R/` abbreviates `report/replication/`.
`refs` counts files, not occurrences, and `evidence` lists the first four (`+k` means k more).

## Verdicts

- **KEEP** - named by a live page, test, Makefile target or CI job, or imported by a KEEP script, or
  the documented reproducing path of a reading the shipped check or a claims page stands on.
- **MERGE** - two scripts measuring the same thing behind different flags, folded into one survivor.
  None: the Table 6 and Table 7 pipelines are already a survivor plus modules it imports, so folding
  them would move files, not remove code.
- **DELETE** - superseded, or named by nothing, and recoverable from git history at `2f92de8`.

## Ledger

### `scripts/claims/`

| file | what it does (first commit) | refs | verdict | evidence | disposition |
|---|---|---|---|---|---|
| `scripts/claims/pdftxt.py` | The paper's own text, so a report can quote it instead of... (`9ce1549`) | 2 | KEEP | scripts/claims/table9b_recalls.py; tests/test_table9b.py | `scripts/claims/pdftxt.py` |
| `scripts/claims/recall_diagnostic.py` | Contract R6-D: what the positions a high-volume recall closes... (`47b2ab7`) | 4 | KEEP | R/REVIEW_NOTES.md; R/claims/CLAIM_SENSITIVITY.md; R/claims/RECALL_DIAGNOSTIC.md; scripts/experiments/claim_sensitivity.py | `scripts/claims/recall_diagnostic.py` |
| `scripts/claims/t6_control_json.py` | Turn a ``--mode control`` transcript into ``control.json``... (`f9d6139`) | 2 | KEEP | R/claims/TABLE6.md; scripts/claims/t6_template.md | `scripts/claims/t6_control_json.py` |
| `scripts/claims/t6_draws.py` | Alternate random draws for Table 6 (CONTRACT_M D2, D3). (`545ebb8`) | 1 | KEEP | scripts/claims/table6_random_pairs.py | `scripts/claims/t6_draws.py` |
| `scripts/claims/t6_engine.py` | Vectorised position accounting for the Table 6 random-pair... (`f9d6139`) | 4 | KEEP | R/REVIEW_NOTES.md; R/claims/TABLE6_READINGS.md; scripts/claims/table6_random_pairs.py; tests/test_table6.py | `scripts/claims/t6_engine.py` |
| `scripts/claims/t6_md.py` | Render report/replication/claims/TABLE6.md and TABLE6.csv. (`f9d6139`) | 1 | KEEP | scripts/claims/table6_report.py | `scripts/claims/t6_md.py` |
| `scripts/claims/t6_template.md` | Markdown template that `t6_md.py` fills for TABLE6.md (`f9d6139`) | 3 | KEEP | R/REVIEW_NOTES.md; scripts/claims/t6_md.py; scripts/claims/table6_random_pairs.py | `scripts/claims/t6_template.md` |
| `scripts/claims/table6_draws.py` | Re-score a Table 6 draw run with the check's marks. (`545ebb8`) | 1 | DELETE | one, and it is the retirement pointer: REVIEW_NOTES 75 now names `03_replicate.py::table6_from_cache` and this commit | git@2f92de8 |
| `scripts/claims/table6_paper.json` | Paper's printed Table 6 values (the scored targets) (`f9d6139`) | 4 | KEEP | R/REVIEW_NOTES.md; R/claims/TABLE6_READINGS.md; scripts/claims/table6_random_pairs.py; scripts/claims/table6_report.py | `scripts/claims/table6_paper.json` |
| `scripts/claims/table6_random_pairs.py` | Table 6 of Gatev, Goetzmann and Rouwenhorst (2006): returns... (`f9d6139`) | 13 | KEEP | Makefile; R/README.md; R/REVIEW_NOTES.md; R/SCORE_LOG.md +9 | `scripts/claims/table6_random_pairs.py` |
| `scripts/claims/table6_report.py` | Build the Table 6 report: check the paper targets, test the... (`f9d6139`) | 5 | KEEP | scripts/03_replicate.py; scripts/claims/t6_md.py; scripts/claims/table6_paper.json; scripts/claims/table6_random_pairs.py +1 | `scripts/claims/table6_report.py` |
| `scripts/claims/table7.py` | Table 7 of GGR (2006): the long and the short book of each... (`6e9e751`) | 17 | KEEP | R/COVERAGE.md; R/README.md; R/REVIEW_NOTES.md; R/claims/TABLE7_REGRESSIONS.md +13 | `scripts/claims/table7.py` |
| `scripts/claims/table7_paper.json` | Table 7's typed paper values (`6e9e751`) | 4 | KEEP | scripts/claims/table7.py; scripts/claims/table7_paper.py; scripts/claims/table7_report.py; tests/test_claims_table7.py | `scripts/claims/table7_paper.json` |
| `scripts/claims/table7_paper.py` | Table 7's printed values, read from the PDF and compared with... (`6e9e751`) | 4 | KEEP | scripts/claims/table7.py; scripts/claims/table7_paper.json; scripts/claims/table7_report.py; tests/test_claims_table7.py | `scripts/claims/table7_paper.py` |
| `scripts/claims/table7_report.py` | The Table 7 report and CSV, generated from the numbers... (`6e9e751`) | 1 | KEEP | scripts/claims/table7.py | `scripts/claims/table7_report.py` |
| `scripts/claims/table9a.py` | Table 9 Panel A: pairs formed only inside the top three size... (`6182dec`) | 12 | KEEP | Makefile; R/COVERAGE.md; R/REPLICATION_CHECK.md; R/REVIEW_NOTES.md +8 | `scripts/claims/table9a.py` |
| `scripts/claims/table9a_paper.json` | Table 9 Panel A's typed paper values (`6182dec`) | 3 | KEEP | R/claims/TABLE9A.md; scripts/claims/table9a.py; tests/test_table9a.py | `scripts/claims/table9a_paper.json` |
| `scripts/claims/table9b_paper.json` | Table 9 Panel B's typed paper values (`9ce1549`) | 3 | KEEP | scripts/claims/recall_diagnostic.py; scripts/claims/table9b_recalls.py; tests/test_table9b.py | `scripts/claims/table9b_paper.json` |
| `scripts/claims/table9b_recalls.py` | Table 9 Panel B: pairs trading with short recalls on... (`9ce1549`) | 10 | KEEP | Makefile; R/REVIEW_NOTES.md; R/SCORE_LOG.md; R/claims/NEAR_MISS_CENSUS.md +6 | `scripts/claims/table9b_recalls.py` |

### `scripts/experiments/`

| file | what it does (first commit) | refs | verdict | evidence | disposition |
|---|---|---|---|---|---|
| `scripts/experiments/claim_sensitivity.py` | Sensitivity of the five claims nearest the line (9, 10, 16... (`fb5bc24`) | 3 | KEEP | R/REVIEW_NOTES.md; R/claims/CLAIM9_PRE1989.md; R/claims/CLAIM_SENSITIVITY.md | `scripts/experiments/claim_sensitivity.py` |
| `scripts/experiments/estimator_variants.py` | Estimator readings of the Table 1 / Table 3 inference rows... (`2f27da4`) | 2 | KEEP | R/REVIEW_NOTES.md; R/archive/OPEN_QUESTIONS_ROUNDS.md | `scripts/experiments/estimator_variants.py` |
| `scripts/experiments/gaps_census.py` | The census of `GAPS.md` section 2: every scored cell of the... (`cb8d4c4`) | 2 | KEEP | R/GAPS.md; R/REVIEW_NOTES.md | `scripts/experiments/gaps_census.py` |
| `scripts/experiments/late_exchange_universe.py` | Late-sample universe as one exchange's file: build the... (`2dd5252`) | 3 | KEEP | R/GAPS.md; R/REVIEW_NOTES.md; scripts/experiments/s7_support.py | `scripts/experiments/late_exchange_universe.py` |
| `scripts/experiments/reversal_candidates.py` | Table 4 + Table 8's 84 regression cells under candidate... (`2f27da4`) | 2 | KEEP | R/REVIEW_NOTES.md; R/archive/OPEN_QUESTIONS_ROUNDS.md | `scripts/experiments/reversal_candidates.py` |
| `scripts/experiments/reversal_subperiods.py` | Contract Pb: candidate reversal factors read in both Table 8... (`545ebb8`) | 3 | KEEP | R/REVIEW_NOTES.md; R/claims/REVERSAL_SUBPERIODS.md; scripts/experiments/table7_rerank.py | `scripts/experiments/reversal_subperiods.py` |
| `scripts/experiments/s7_support.py` | Does anything outside the score support the S7 universe?... (`65457e0`) | 2 | KEEP | R/REVIEW_NOTES.md; R/claims/S7_SUPPORT.md | `scripts/experiments/s7_support.py` |
| `scripts/experiments/share_class_map.py` | The permnos a wide share filter adds to CRSP's ordinary... (`4df207f`) | 3 | KEEP | R/REVIEW_NOTES.md; R/claims/FULLSET_RESCORE.md; scripts/claims/table6_random_pairs.py | `scripts/experiments/share_class_map.py` |
| `scripts/experiments/table2a_conventions.py` | Table 2 Panel A: the counting conventions and where the... (`2f27da4`) | 2 | KEEP | R/REVIEW_NOTES.md; R/archive/OPEN_QUESTIONS_ROUNDS.md | `scripts/experiments/table2a_conventions.py` |
| `scripts/experiments/table3_sectors.py` | Why our sector portfolios earn too much at the top and too... (`b84afab`) | 4 | KEEP | R/REVIEW_NOTES.md; R/claims/CLAIM9_PRE1989.md; R/claims/NEAR_MISS_CENSUS.md; R/claims/TABLE3_SECTORS.md | `scripts/experiments/table3_sectors.py` |
| `scripts/experiments/table7_rerank.py` | Contract R6B: re-rank the 72 reversal constructions against... (`e90e716`) | 2 | KEEP | R/GAPS.md; R/REVIEW_NOTES.md | `scripts/experiments/table7_rerank.py` |
| `scripts/experiments/table8_windows.py` | Table 8's subperiod window against the caption (REVIEW_NOTES... (`2f27da4`) | 2 | KEEP | R/REVIEW_NOTES.md; R/archive/OPEN_QUESTIONS_ROUNDS.md | `scripts/experiments/table8_windows.py` |

### Other one-off scripts under `scripts/`

| file | what it does (first commit) | refs | verdict | evidence | disposition |
|---|---|---|---|---|---|
| `scripts/audit_data_vintages.py` | Compare matching SIZ and CIZ observations with aggregate... (`eaa8662`) | 0 | DELETE | zero: no tracked file names it; a 5-line wrapper over `project.vintage_audit.main` | git@2f92de8 |
| `scripts/audit_reversal_factor.py` | Audit of the paper's short-term reversal factor (REVIEW_NOTES... (`1791db8`) | 8 | KEEP | R/GAPS.md; R/REVIEW_NOTES.md; R/analysis/reversal_factor_audit.md; R/claims/REVERSAL_SUBPERIODS.md +4 | `scripts/audit_reversal_factor.py` |
| `scripts/build_issuer_header.py` | Build a local CIZ issuer mapping from the web export. (`eaa8662`) | 0 | DELETE | zero: CLI over `project.issuer_header.extract_header`, still covered by `tests/test_issuer_header.py` | git@2f92de8 |
| `scripts/cell_margins.py` | Per-cell margins for the scored tables: how far is each cell... (`87f645e`) | 2 | KEEP | R/REVIEW_NOTES.md; tests/test_cell_margins.py | `scripts/cell_margins.py` |
| `scripts/digitize_figures.py` | Digitize Figures 2 (monthly bars) and 3 (cumulative returns)... (`d2d3fed`) | 5 | KEEP | R/COVERAGE.md; R/REPLICATION_CHECK.md; R/REVIEW_NOTES.md; scripts/03_replicate.py +1 | `scripts/digitize_figures.py` |
| `scripts/docs_sync.py` | Keep the generated parts of report/replication/ equal to the... (`0f71919`) | 5 | KEEP | Makefile; R/COVERAGE.md; R/README.md; R/REVIEW_NOTES.md +1 | `scripts/docs_sync.py` |
| `scripts/edition_1999.py` | Score a cohort cache against the 1999 NBER draft's Tables I... (`03743d6`) | 5 | KEEP | Makefile; R/EDITION_1999.md; R/REVIEW_NOTES.md; R/claims/CLAIM9_PRE1989.md +1 | `scripts/edition_1999.py` |
| `scripts/import_legacy_wrds.py` | Import legacy SIZ downloads into a local daily panel. (`eaa8662`) | 0 | DELETE | zero: CLI over `project.legacy_import`, still covered by `tests/test_legacy_import.py` | git@2f92de8 |
| `scripts/import_wrds_ui.py` | Build replication inputs from WRDS web-export CSV archives. (`eaa8662`) | 0 | DELETE | zero: CLI over `project.import_ui`, still covered by `tests/test_import_ui.py` | git@2f92de8 |
| `scripts/paper_ceiling.json` | The paper's 865 printed results, block by block (`dc07305`) | 4 | KEEP | R/COVERAGE.md; R/REVIEW_NOTES.md; scripts/paper_ceiling.py; tests/test_ceiling.py | `scripts/paper_ceiling.json` |
| `scripts/paper_ceiling.py` | Re-count the values GGR (2006) print in their nine tables... (`dc07305`) | 4 | KEEP | R/COVERAGE.md; R/REVIEW_NOTES.md; scripts/paper_ceiling.json; tests/test_ceiling.py | `scripts/paper_ceiling.py` |
| `scripts/paper_cells.json` | Every paper cell, typed, as the harness scores it (`441797d`) | 5 | KEEP | R/REVIEW_NOTES.md; R/claims/TABLE9A.md; scripts/claims/table6_report.py; scripts/paper_consistency.py +1 | `scripts/paper_cells.json` |
| `scripts/paper_consistency.py` | Arithmetic checks of the paper's own printed tables against... (`d135657`) | 6 | KEEP | R/GAPS.md; R/README.md; R/REPLICATION_CHECK.md; R/REVIEW_NOTES.md +2 | `scripts/paper_consistency.py` |
| `scripts/rebuild_manifest.json` | sha256 of the scoring path (`03_replicate` + `src/project`) (`441797d`) | 5 | KEEP | R/REVIEW_NOTES.md; R/SCORE_LOG.md; R/claims/TABLE9A.md; scripts/score_wrapper.py +1 | `scripts/rebuild_manifest.json` |
| `scripts/replication_figures.py` | Figures 2, 3 and 4 of GGR (2006), ours against the paper's. (`013c88d`) | 3 | KEEP | Makefile; R/README.md; R/outputs/README.md | `scripts/replication_figures.py` |
| `scripts/score_wrapper.py` | Pinned evaluator for the GGR replication-score campaign. (`441797d`) | 5 | KEEP | R/REVIEW_NOTES.md; R/SCORE_LOG.md; R/claims/TABLE9A.md; scripts/experiments/gaps_census.py +1 | `scripts/score_wrapper.py` |
| `scripts/verify_paper_targets.py` | Verify the paper targets typed into ``03_replicate.py``... (`6bf6a64`) | 8 | KEEP | Makefile; R/COVERAGE.md; R/METHOD.md; R/REVIEW_NOTES.md +4 | `scripts/verify_paper_targets.py` |

## The five retirements: 167 lines, one convenience each

Four of them are CLI wrappers: each unpacks `argparse` and calls one function of a `src/project`
module. Three of those modules are still covered by tests, so they keep the test and lose only a
hand-typed front door; the fourth, `vintage_audit`, had no test and goes with its wrapper (below). Nothing in the repo names any of the four - not a page, not a Makefile target, not a workflow,
not a test - and the wrapper's only cost is a second, untested way to reach `import_ui`,
`issuer_header`, `legacy_import` and `vintage_audit`.

The fifth, `claims/table6_draws.py` (84 lines), is the one that could have been kept: it
re-marked a Table 6 bootstrap run against the paper. But it is a copy of what the driver already does
- `table6_from_cache` aggregates the same `.npz` cohorts through `table6_report.collect`, and `_cell`
applies the same `_mark` bands - and its only reference was the REVIEW_NOTES 75 line that introduced
it. That line now names the driver path and this commit, so the reading keeps a reproducing path
without a second implementation of the mark rule.

## Referenced only by the script that imports it

Three modules have no other referent and are KEEP because the surviving pipeline imports them:
`claims/t6_md.py` (by `table6_report.py`), `claims/t6_draws.py` (by `table6_random_pairs.py`) and
`claims/table7_report.py` (by `table7.py`). The four `*_paper.json` files hold the paper's printed
values the claim scripts compare against; each is also named by a live page or test, so they are
KEEP on their own evidence.

## The sixth retirement, on coordinator review: `src/project/vintage_audit.py`

`src/project/vintage_audit.py` (48 lines) lost its only caller with `scripts/audit_data_vintages.py`
and has no test. This ledger first flagged it and left it in place, because the contract kept R9-B out
of `src/`. The coordinator's review of PR #91 asked for it to follow its wrapper under the same
deletion rule, and it is now deleted. Evidence: before the deletion, `git grep -n vintage_audit`
over `src scripts tests report Makefile pyproject.toml` found only this ledger and REVIEW_NOTES
(sections 56 and 91), with no importer and no test. It can be recovered from commit `2f92de8`.
`import_ui`, `issuer_header` and `legacy_import` stay live: `tests/test_import_ui.py`,
`tests/test_issuer_header.py` and `tests/test_legacy_import.py` import them directly.

## Retirement candidates for a later round

Named only by `REVIEW_NOTES.md` plus, for four of them, `archive/OPEN_QUESTIONS_ROUNDS.md`, and for
two, a live page; none has a test or a Makefile target: `experiments/estimator_variants.py`,
`experiments/reversal_candidates.py`, `experiments/table2a_conventions.py` and
`experiments/table8_windows.py` (the four round-4 experiments), `experiments/s7_support.py`
(`claims/S7_SUPPORT.md`) and `experiments/table7_rerank.py` (`GAPS.md`). Retiring them means rewriting
those note lines to a git-history pointer the way REVIEW_NOTES 75 now points at `2f92de8`; that is a
decision about the prose, not about the scripts, so they are KEEP this round.

## Verification

`pytest -q`: 368 passed, 8 skipped. `scripts/03_replicate.py --aggregate-only --workers 1` over the
shipped caches: `Score: 411.0 of 865`, and `replication_check.md` byte-identical to the base run of
this round (only the `--out-root` echo differs between two different output directories).
`SCORE_LOG.md` gains no row; `data/` is untouched; no script in this ledger is on the scoring path.
