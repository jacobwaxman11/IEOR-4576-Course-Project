# Contract B: provenance, reconciliation and data gaps

Read `report/data_review/COMMON_RULES.md` first. Every rule in it is binding.

## Exclusive writes

- `report/data_review/B_FINDINGS.md`, the deliverable.
- `report/data_review/B_queries.sql`, every SQL statement, each labelled `-- B1`, `-- B2`, and so on.
- `report/data_review/B_checks.py`, the single runner script for the connecting phases.
- `report/data_review/B_results/*.csv`, aggregates only.

Edit nothing else.

## Read first (offline)

- **What should be on WRDS:** `data/metadata/crsp_manifest.json`, the expected row counts, PERMNO counts and date bounds for each of the 7 CRSP exports.
- **How each export was made:** `data/metadata/queries/*.sql` and `*.json`.
- **Validation and coverage records:** `data/metadata/*_validation.json`, `french_manifest.json`, `goyal_welch_validation.json`.
- **Ibbotson inputs:** `report/DATA_REQUIREMENTS.md` and `report/IBBOTSON_DATA_SOURCES.md`, including the Table 4 inputs and the known gaps (the pre-1982 small-stock series; the 474- vs 475-month boundary).
- **The paper's Table 4 caption:** `pdftotext -layout Pairs_Trading_RV_Arbitrage_Rule.pdf - | grep -n -A12 "Table 4"`.
- **The extensions' data needs:** `report/proposal_trading_simulation.md`. E4 needs intraday TAQ for 2020–2025 and factors to 2026.

## Tasks

### B-1. Server counts vs the manifests (reproducibility)

For each of the 7 exports, re-run the recorded query as an aggregate: `COUNT(*)`, `COUNT(DISTINCT permno)` where it applies, and `MIN`/`MAX` of the date column, with the same date window and filters. Compare with `crsp_manifest.json`.
- Mark **PASS** if the result matches exactly.
- Otherwise mark **WARN** and quantify the difference. A newer CRSP vintage can revise history.

The exports are: daily stocks, monthly stocks, delisting, distributions, daily indexes, monthly indexes, and DFSCX monthly (fund 008296).

### B-2. Is there a newer vintage?

- Find the latest date in the daily and monthly CIZ tables, in both `crsp` (annual/monthly update) and `crsp_q_stock` (quarterly).
- Report whether data past **2026-03-31** (daily) or **2026-06-30** (monthly) now exists, and in which library.

### B-3. CIZ vs legacy SIZ conventions

- Pick 20 PERMNOs: 10 large, long-lived stocks, plus 10 that were delisted for performance reasons between 1963 and 2002.
- For each, compare monthly compounded returns from the CIZ daily table with legacy `crsp.msf.ret` (SIZ, available through 2024). Do this on the server; aggregate per PERMNO-year.
- Compare the last-day delisting handling: legacy `crsp.msedelist.dlret` (or `dsedelist`) vs CIZ `stkdelists.delret`, and whether CIZ `dlyret` on the final day already includes it.
- Report the mean absolute difference and the cases that differ by more than 1 basis point.

### B-4. Factors on WRDS vs the local French files

- Compare `ff.factors_daily` and `ff.factors_monthly`, plus momentum and short-term reversal if they are present (search with `list_tables('ff')`), against the vintage recorded in `french_manifest.json`. Use coverage and end dates; the zip bytes themselves are LFS placeholders, so compare against the manifest's recorded bounds.
- Report the end date of each, and whether WRDS is a usable source for factors through 2026.

### B-5. Gaps

- **TAQ.** Find the libraries (`taqmsec`, `taqm_2020`, ...) Hao's account can access. For each year 2020–2025, report the NBBO and trade table availability (from table names and `describe_table`; an approximate row count is enough). **Do not** query TAQ row data beyond a `LIMIT 1` existence check.
- **Pre-1982 small-stock series (Ibbotson stand-in).** Check whether CRSP size-decile portfolio returns (`crsp.erdport1`, `crsp.msix` or similar; search for them) cover June 1963 to December 1981, and whether they could proxy the missing Ibbotson small-stock series. State the bias.
- **Table 4 boundary.** Confirm month coverage June 1963 to December 2002 (475 months) for the S&P 500 total return (`crsp.msi` `sprtrn` is a *price* return; look for a total-return field such as `crsp.msp500` `totret`) and T-bill (`crsp.mcti` or similar).
- **Entitlements.** List every library the account is **not** entitled to that the plan needs. A `NotSubscribedError` or permission error counts as a finding, not a failure.

## Deliverable: `B_FINDINGS.md`

1. A summary of at most 8 bullets, worst first, each with its severity.
2. **The reconciliation table:** export | manifest value | server value | difference | status.
3. The B-2 to B-5 results, each with numbers and its query ID.
4. **A recommended source per input for `scripts/01_get_data.py`.** For each input give the WRDS library and table, its columns, the date window, and whether WRDS or the French site / Goyal–Welch should be the canonical source.
5. The questions that are still open.
