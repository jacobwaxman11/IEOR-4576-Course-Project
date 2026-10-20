# Data review: CRSP/WRDS inputs for the GGR (2006) replication and extensions

Reviewed 2026-10-15 against live WRDS. The review had two parts:

- **Worker A** (data fit for the paper): `report/data_review/A_FINDINGS.md`.
- **Worker B** (provenance and gaps): `report/data_review/B_FINDINGS.md`.

The contracts the workers ran under, every SQL statement and the aggregate results are in `report/data_review/`. Numbers in this summary trace to a query ID there, or to the download manifest `data/metadata/wrds_api_manifest.json`, which `scripts/01_get_data.py` writes.

## Headline issues (worst first)

1. **Licensing: the repository is public and hosts raw CRSP exports.**
   - The repo is `jacobwaxman11/IEOR-4576-Course-Project`, visibility PUBLIC. The exports are in Git LFS under `data/raw/crsp/`.
   - The WRDS terms require private storage and forbid redistribution.
   - **Team decision needed:** make the repository private, or remove the CRSP files from LFS. Removal also requires purging LFS history.
   - The new API pulls are written only to git-ignored folders.
2. **Delisting returns are already in the daily return. Adding them again double counts.** (A15, B3c3)
   - In the CIZ data, `dlyret` on the row flagged `dlydelflg = 'Y'` equals `stkdelists.delret` in 100% of testable cases. That row is dated a median of one day after `delistingdt`.
   - **Rule:** never compound `delret` onto the daily panel.
   - When that row's return is null (3,187 GDR cases), apply the paper's fallback.
3. **The repo's daily panel is out of date and contained duplicate rows.**
   - The quarterly library now runs to **2026-06-30**; the repo's export ends 2026-03-31.
   - The "duplicate keys" (A7: 29,742 keys) came from the distribution columns that the WRDS view appends. Dropping those columns and selecting `DISTINCT` leaves **zero** duplicated (permno, date) keys in the new download.
   - Rows for 1961 to 2026-03 in the new download: 102,433,386. The repo manifest had 102,464,776. The difference of −31,390 matches the duplicate rows that were removed (A7) to within 62 rows, which is vintage noise.
   - This closes B's open question about the quarterly row counts (B1a).
4. **Volume before 1983.** NASDAQ daily volume is null for about 50–56% of common-stock rows from 1973 to 1982 (A12a). The Table 9 volume-recall test cannot be computed for those stocks; document the restriction.
5. **Bid/ask quotes are thin before 1993.** Coverage is 5–67% of rows before 1993 and at least 95% from 1995 (A10). A quoted-spread cost model needs the high/low estimators (Corwin–Schultz, Roll) for the early sample.
6. **Old vs new CRSP conventions** (document these; don't tune them away).
   - **Returns:** CIZ daily-compounded returns differ from legacy monthly returns by a mean of 6.2 bp per stock-year, with a maximum of 85 bp (B3b).
   - **Delisting returns:** legacy monthly `msedelist.dlret` disagrees with daily `dsedelist`/CIZ in 4 of 6 sampled cases (B3c).
7. **Start date.** The team doc says the sample starts in "1986". The paper and `configs/config.yaml` use **1963-07** (474 months). Fix the team doc.
8. **Table 4 inputs.**
   - The S&P 500 total return (`crsp.msp500.vwretd`) and the T-bill return (`crsp.mcti.t30ret`) cover all 475 months from 1963-06 to 2002-12 (B5c).
   - The pre-1982 small-stock series has only a proxy: CRSP decile 1 (`crsp.msix.decret1`). It is biased against SBBI (B5b).
   - The short-term reversal factor is **not** on WRDS, so the French-site file stays the source (B4).

## Status by dataset

| Dataset | Reconciles with repo manifest | New API pull (`data/raw/wrds_api/`) | Notes |
|---|---|---|---|
| Daily stocks | WARN: repo file stale, contains duplicate rows | 103,119,940 rows, 41,038 PERMNOs, 1961-01-03 to **2026-06-30**, 66 yearly Parquet files, 4.3 GB | 38 of 70 columns kept; zero duplicate keys |
| Monthly stocks | WARN: contains duplicate rows | 4,946,816 rows through 2026-06-30 | `DISTINCT`, without distribution columns |
| Delisting | PASS (B1c) | 29,727 rows, the same as the manifest | the 5 action types are the full domain (A8) |
| Distributions | PASS (B1d) | 1,023,403 rows, the same as the manifest | |
| Daily / monthly indexes | PASS (B1e/B1f) | 16,481 / 786 rows, the same as the manifest | `sprtrn` is a price return |
| DFSCX fund 008296 | PASS (B1g) | 535 rows, the same as the manifest | |
| S&P 500, T-bills, size deciles | PASS (B5) | 768 months each, 1961–2024 | legacy SIZ tables; they cover the replication window |
| FF factors (WRDS) | PASS: the bounds match the French manifest (B4) | 16,524 daily / 788 monthly rows | no REV factor on WRDS |
| French library (public) | PASS: the 8 repo files are byte-identical | 12 zips in `data/raw/public/french/` | adds the five-factor and 49-industry files for the extensions |
| Goyal–Welch (public) | PASS | 3 files in `data/raw/public/goyal_welch/` | bond series switch to Bloomberg from 2022 |
| TAQ 2020–2025 | Accessible (B5a) | not downloaded | 65–100 bn NBBO rows per year; build intraday bars on the server |

## Build rules for `scripts/02_build_dataset.py`

The full spec is in A_FINDINGS §4.

- **Common stock:** `securitytype = 'EQTY' AND securitysubtype = 'COM' AND sharetype = 'NS'`. This is equivalent to SHRCD 10/11.
- **Exchange:** `primaryexch IN ('N','A','Q')`.
- **No-trade day:** `dlyprcflg <> 'TR'`. A stock is eligible only if it has a `TR` row with `dlyprc > 0` on every trading day of the formation window.
- **Delisting:**
  - The `dlydelflg = 'Y'` row is the terminal return. Do not add `delret` again.
  - If that row's return is null, use the fallback: −30% for performance delistings, with −100% as a robustness check.
  - If a stock has no flagged row, close at the last available price.
- **Sector (Table 3):** use 2-digit SIC from the formation window: Utilities 49, Transportation 40–47, Financials 60–69, Industrials the rest. SIC 0 (7.8% of the universe) needs an explicit rule.

## Credentials and reproducibility

- **Setup:** each teammate runs `.venv/bin/python scripts/wrds_setup.py` once, in their own terminal. It stores the password in `~/.pgpass` (mode 600, outside the repo).
- **Connecting:** code connects only through `project.data.wrds_connection()`, which has no password argument and never falls back to an interactive prompt.
- **Downloading:** `scripts/01_get_data.py` pulls everything through one connection, so one Duo push. It takes about 20 minutes and resumes if interrupted.
- **Where data goes:**
  - CRSP data goes to the git-ignored `data/raw/wrds_api/`.
  - Public files go to `data/raw/public/`, also git-ignored.
  - Only the manifest (counts, dates, SHA-256 and SQL) is committed.

## Still open

- Which exchange supplied the pre-1993 quotes, and NASDAQ volume units (A open questions 3, 5).
- The values (not just the date bounds) of WRDS `ff` factors, `msp500.vwretd` and `mcti.t30ret`, compared with the French and Ibbotson series (B open questions 4, 5).
- The true SBBI small-stock series before 1982, which needs Morningstar Direct (see `report/IBBOTSON_DATA_SOURCES.md`).
