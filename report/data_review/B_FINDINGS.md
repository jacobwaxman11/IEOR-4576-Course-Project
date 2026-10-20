# Worker B findings: provenance, reconciliation and data gaps

Checked 2026-10-15 against WRDS (3 connecting phases: discovery, checks, fix-up).
Evidence: query IDs in `B_queries.sql`, executed by `B_checks.py`; result CSVs in
`B_results/`; the 20-PERMNO row-level B3 samples are in git-ignored
`data/raw/wrds_api/B_b3*.parquet`. Offline evidence is cited as repo file + line.

## Summary (worst first)

1. **MAJOR — delisting returns: three inconsistent conventions, and a double-counting
   trap.** CIZ `stkdelists.delret` equals legacy *daily* `crsp.dsedelist.dlret`, not
   legacy *monthly* `crsp.msedelist.dlret` (4 of 6 comparable cases differ, up to
   43.3 pp; mean |diff| 12.3 pp over the 10-PERMNO sample — B3c1/B3c2). Worse, CIZ
   `dlyret` on the final row (`dlydelflg='Y'`) already **equals** `delret`
   (all 10 cases, B3c3), so multiplying `stkdelists.delret` on top of the daily
   panel double counts the delisting. And 4 of 10 CIZ `delret` are missing
   (`delretmisstype` DM/DG) where legacy `msedelist.dlret` still has values.
2. **MAJOR (unverified residue) — the daily/monthly stock archives were pulled from
   the quarterly library, but B1a/B1b could only be re-run against the annual
   library.** `crsp` (annual) ends 2025-12-31 for both (B2a/B2c), so B1a/B1b show
   WARN by construction; the exact `crsp_q_stock` counts are UNVERIFIED because the
   connection budget ran out. The 653,741-row (daily) and 69,421-row (monthly)
   shortfalls are exactly consistent with the missing Jan–Jun 2026 months.
3. **MINOR — newer CRSP vintage exists: `crsp_q_stock` now has daily AND monthly
   data through 2026-06-30** (B2b/B2d), i.e. one quarter beyond the daily manifest
   (2026-03-31). Relevant only to the E1 extension; the 1963–2002 sample is unaffected.
4. **MINOR — CIZ-daily vs legacy-monthly returns differ by convention, not error:**
   per PERMNO-year |diff| mean 6.2 bp, median 2.5 bp, 240/356 > 1 bp, 59/356 > 10 bp,
   max 85 bp (B3b). Daily compounding + ex-date dividend reinvestment vs legacy
   monthly accrual. Must be documented, not tuned away.
5. **PASS — everything else reconciles exactly:** delisting, distributions, daily and
   monthly indexes, DFSCX all match `crsp_manifest.json` to the row and date (B1c–B1g).
6. **PASS/positive — WRDS French factors match the local vintage** (B4a/B4b) and TAQ
   2020–2025 is fully accessible (B5a); **no entitlement errors anywhere** (B5d).
7. **MINOR — no short-term-reversal factor on WRDS** (B4 discovery: 12 `ff` tables,
   none is ST-reversal); the French-site zip stays canonical for REV.
8. **MINOR — a usable but biased pre-1982 small-stock proxy exists** (`crsp.msix`
   smallest-decile, B5b): all 223 months Jun 1963–Dec 1981 present, but it is a
   monthly-rebalanced all-CRSP decile, not SBBI's 5-year-rebalanced NYSE portfolio.

## Reconciliation table (B1)

| export | manifest value | server value | difference | status |
|---|---|---|---|---|
| daily stocks (B1a, `crsp.wrds_dsfv2_query`) | 102,464,776 rows; 40,427 permnos; 1961-01-03..2026-03-31 | 101,811,035; 40,036; 1961-01-03..**2025-12-31** | −653,741 rows; −391 permnos; last_date −3 months | **WARN** — queried annual library; manifest came from `crsp_q_stock` (quarterly, B2b ends 2026-06-30). Quarterly counts UNVERIFIED (no connection left). |
| monthly stocks (B1b, `crsp.wrds_msfv2_query`) | 5,003,530 rows; 41,016 permnos; 1961-01-31..2026-06-30 | 4,934,109; 40,014; 1961-01-31..**2025-12-31** | −69,421 rows; −1,002 permnos; last_date −6 months | **WARN** — same annual-vs-quarterly cause (B2d: quarterly ends 2026-06-30). Quarterly counts UNVERIFIED. |
| delisting (B1c, `crsp_q_stock.stkdelists`) | 29,727 rows; 1961-01-20..2026-06-29 | identical | none | **PASS** |
| distributions (B1d, `crsp_q_stock.stkdistributions`) | 1,023,403 rows; 1961-01-03..2026-06-30 | identical | none | **PASS** |
| daily indexes (B1e, `crsp_q_stock.wrds_dailyindexret_query`) | 16,481 rows; 1961-01-03..2026-06-30 | identical | none | **PASS** |
| monthly indexes (B1f, `crsp_q_stock.wrds_monthlyindexret_query`) | 786 rows; 1961-01-31..2026-06-30 | identical | none | **PASS** |
| DFSCX monthly (B1g, `crsp_q_mutualfunds.monthly_tna_ret_nav`, fund 008296) | 535 rows; 1981-12-31..2026-06-30 | identical | none | **PASS** |

Full machine-readable version: `B_results/reconciliation.csv`.

## B-2. Newer vintage? — YES for quarterly, no for annual

- `crsp` (annual update): daily ends **2025-12-31** (B2a), monthly ends **2025-12-31** (B2c).
- `crsp_q_stock` (quarterly): daily ends **2026-06-30** (B2b), monthly ends **2026-06-30** (B2d).
- Data past 2026-03-31 (daily) exists **only in `crsp_q_stock`**; past 2026-06-30 in neither.
  Any 01_get_data refresh must read the quarterly library, not `crsp`.

## B-3. CIZ vs legacy SIZ (20 PERMNOs: 10 large long-lived + 10 performance delistings)

Sample: B3a1 (`B3a1.csv`) top cap with data before 1975: permnos 50876, 55976, 47896,
12060, 11850, 59328, 22111, 18163, 61241, 59408. B3a2 (`data/raw/wrds_api/B_b3a2_delisted_sample.parquet`)
every-40th `msedelist` row with `dlstcd` 500–599, 1963–2002: permnos 36556, 30189,
28839, 35190, 31050, 41267, 58326, 45111, 56304, 42650.

- **Compounded returns (B3b).** Per PERMNO-year, CIZ daily (deduplicated to one row
  per permno-day — the CIZ query table repeats dates when distributions share them,
  so naive compounding over rows is wrong) vs legacy `crsp.msf.ret`: 356 matched
  permno-years; mean |diff| **6.16 bp/yr**, median 2.46 bp, **240 (67%) > 1 bp**,
  59 (17%) > 10 bp, max **85.1 bp** (permno 47896, 1990). 26 permno-years excluded
  (null CIZ-year return). Worst cases: `B_results/B3_worst_cases.csv`; per-year
  tables in `data/raw/wrds_api/B_b3b1_ciz_yearly.parquet` / `B_b3b2_siz_yearly.parquet`.
- **Delisting handling (B3c).** `stkdelists.delret` = `dsedelist.dlret` in every
  comparable case; `msedelist.dlret` differs in 4/6 (28839: −0.600 vs −0.5556;
  36556: +0.7333 vs +0.3000; 56304: 0.0 vs +0.1875; 58326: −0.0270 vs −0.1000),
  mean |diff| 12.3 pp. **CIZ `dlyret` on the `dlydelflg='Y'` row already equals
  `delret`** (all 10 cases; e.g. 28839: final-day `dlyret` = −0.555556 = delret),
  so the daily panel is self-contained: applying `stkdelists.delret` again
  double counts. Legacy `msedelist` supplies a `dlret` for 4 permnos whose CIZ
  `delret` is missing (30189, 35190, 42650, 45111 — CIZ `delretmisstype` DM/DG),
  which matters for the paper's "−30% if missing" rule: under CIZ those 4 fall
  back to −30%, under legacy they use actual returns.

## B-4. Factors on WRDS vs `french_manifest.json`

- `ff.factors_daily` (B4a): 26,317 rows, 1926-07-01..**2026-08-31**, all of
  mktrf/smb/hml/rf complete; `umd` complete from 1926-11-03 (B4d). Manifest daily:
  19260701..20260831 — **exact match**. **PASS.**
- `ff.factors_monthly` (B4b): 1,202 rows, 1926-07-01..**2026-08-01**, all columns
  complete; `umd` from 1927-01 (B4c). Manifest monthly: 192607..202608 — **exact
  match**. **PASS.**
- Momentum is the `umd` **column** of both tables — no separate table. **Short-term
  reversal does not exist in `ff`** (discovery: 12 tables, none is a reversal
  factor) — the local French zip stays the only REV source. **UNVERIFIED:**
  WRDS row *values* vs zip contents (only bounds compared, per contract).
- Verdict: WRDS `ff` is a usable factor source through **August 2026** for
  MKT/SMB/HML/MOM/RF; it cannot replace the French-site ST-reversal file.

## B-5. Gaps

- **TAQ (B5a, `B5a_taq_availability.csv`).** All of `taqm_2020`…`taqm_2025` are
  accessible; per year `complete_nbbo_YYYY` (NBBO, 13 cols), `ctm_YYYY` (consolidated
  trades, 20 cols), `cqm_YYYY` (quotes, 29 cols) and `mastm_YYYY` (master, 40 cols)
  all exist and pass a `LIMIT 1` check. Approx rows (from EXPLAIN): NBBO 64.7–100.6 bn,
  trades 14.9–27.2 bn, quotes 322.8–569.8 bn per year. E4 is feasible; bar
  construction must be server-side/windowed. (Row data beyond `LIMIT 1` not queried.)
- **Pre-1982 small-stock proxy (B5b).** `crsp.msix` has all **223 months**
  Jun 1963–Dec 1981 with `decret1` (smallest-decile VW return) non-null. It can
  proxy the missing Ibbotson pre-1982 small-stock series, with stated bias: CRSP
  decile 1 rebalances monthly over all CRSP stocks; SBBI's historical portfolio is
  NYSE-only with 5-year rebalancing, so measured small-stock premia will differ
  (rebalancing and universe effects), and it is not the authors' EnCorr series.
- **Table 4 boundary (B5c).** All three series have exactly **475 months**
  1963-06-28..2002-12-31: `crsp.msp500` (B5c1 — no `totret` column exists; `vwretd`
  is the S&P-500 VW **total-return** candidate, `sprtrn` is the price return),
  `crsp.mcti` `t30ret` (B5c2, 30-day T-bill return index), and `crsp.msi` (B5c3,
  `sprtrn` price return only). The June 1963 start is present, so the 475- vs
  474-month boundary can be handled. Equality to Goyal's `CRSP_SPvw`/Ibbotson
  remains unverified (values not pulled).
- **Entitlements (B5d, `B5d_entitlements.csv`).** No `NotSubscribedError` anywhere:
  all 13 candidate libraries (crsp, crsp_q_stock, crsp_q_mutualfunds, crsp_q_indexes,
  ff, taqmsec, taqm_2020–2026) are accessible. `sbbi` and `ibbotson` schemas do not
  exist on this server (`SchemaNotFoundError`) — consistent with the earlier finding
  that SBBI is not on WRDS.

## Recommended sources for `scripts/01_get_data.py`

| Input | WRDS library.table (key columns) | Window | Canonical source |
|---|---|---|---|
| Daily stock panel | `crsp_q_stock.wrds_dsfv2_query` (permno, dlycaldt, dlyret, dlyretx, dlyprc, dlyvol, dlycap, shrout, dlydelflg, siccd, …) — dedupe to 1 row per (permno, dlycaldt) | 1961-01-01..2026-06-30 (quarterly is freshest) | Local LFS export (11771134) for the replication; WRDS quarterly for the 2026 refresh |
| Monthly stock panel | `crsp_q_stock.wrds_msfv2_query` (permno, mthcaldt, mthret, mthretx, mthprc, mthcap, shrout, …) | 1961-01-01..2026-06-30 | Local LFS export (11771141); WRDS quarterly for updates |
| Delisting events | `crsp_q_stock.stkdelists` (delistingdt, delret, delretmisstype, delstatustype, …) + `crsp.dsedelist` (dlret) cross-check; `crsp.msedelist` only for legacy-value imputation | 1961-01-01..2026-06-29 | Local export (11771161); never re-apply `delret` to the daily panel — final `dlydelflg='Y'` row already contains it |
| Distributions | `crsp_q_stock.stkdistributions` (disexdt, distype, disdivamt, disfacpr, disfacshr, …) | 1961-01-01..2026-06-30 | Local export (11771165) |
| Index benchmarks | `crsp_q_stock.wrds_dailyindexret_query` / `wrds_monthlyindexret_query` (vwretd, ewretd, sprtrn, …) | 1961-01-01..2026-06-30 | Local exports (11771207/11771212); `sprtrn` is a price return |
| S&P 500 **total** return (Table 4) | `crsp.msp500` (`vwretd`) | 1963-06..2002-12 (475 months, B5c1) | WRDS candidate; verify against Goyal–Welch `CRSP_SPvw` before use |
| T-bill total return (Table 4) | `crsp.mcti` (`t30ret`) | 1963-06..2002-12 (475 months, B5c2) | WRDS; cross-check vs French RF / Goyal `Rfree` |
| FF factors (MKT/SMB/HML/MOM/RF) | `ff.factors_daily`, `ff.factors_monthly` (incl. `umd`) | through 2026-08 (B4a/B4b) | French site zips stay canonical (they match WRDS bounds); WRDS acceptable fallback |
| Short-term reversal (REV) | **not on WRDS** | — | French site `F-F_ST_Reversal_Factor_{,daily_}CSV.zip` (local, validated) |
| Ibbotson bonds (Table 4) | not on WRDS | — | Goyal–Welch workbooks (local; `ltr`/`corpr` identical across vintages 1963-06..2002-12) |
| Small-stock premium pre-1982 | `crsp.msix` (`decret1`) — labeled proxy | 1963-06..1981-12 (223 months, B5b) | Proxy only; true fix is Morningstar Direct SBBI (`IA SBBI US Small Stock TR USD`) |
| DFSCX small-stock 1982+ | `crsp_q_mutualfunds.monthly_tna_ret_nav` (fund 008296) | 1981-12-31..2026-06-30 | Local export (11771343) |
| TAQ NBBO + trades (E4) | `taqm_2020..taqm_2025`: `complete_nbbo_YYYY`, `ctm_YYYY` (+ `mastm_YYYY` security master) | 2020–2025, per-day tables also present | WRDS only; aggregate/window server-side |

## Open questions

1. Exact `COUNT(*)`/`COUNT(DISTINCT permno)` on `crsp_q_stock.wrds_dsfv2_query` and
   `wrds_msfv2_query` (B1a/B1b against the quarterly library) — UNVERIFIED; the
   connection budget was exhausted. Expected to exceed the manifest by the
   Apr–Jun 2026 rows plus any vintage revisions.
2. Why `msedelist.dlret` and `dsedelist.dlret` disagree for pre-1975 delistings
   (4/10 sample cases, up to 43 pp) — which one the authors' pipeline used is unknown.
3. Semantics of `delretmisstype` DM vs DG, and whether the paper's −30% fallback
   was applied to the same set of months under the authors' 2006 vintage.
4. Numerical equality of `crsp.msp500.vwretd` and `crsp.mcti.t30ret` to the
   Ibbotson/EnCorr Table 4 series (values not compared; bounds verified only).
5. WRDS `ff` factor *values* vs the local French zips (bounds match; row values
   not compared per the no-row-data rule).
6. Whether any subscription (Morningstar Direct, Columbia library) can supply the
   true SBBI pre-1982 small-stock monthly series — unchanged from
   `report/IBBOTSON_DATA_SOURCES.md`.
