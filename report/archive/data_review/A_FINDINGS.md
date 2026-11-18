# A. Is the CRSP data fit for the GGR (2006) replication and our extensions?

Worker A data review. Evidence: query IDs `A1`–`A15b` in `A_queries.sql`, executed by
`A_checks.py`, outputs in `A_results/`; repo files cited as path/line. WRDS connections:
phase 1 (schema discovery, A1–A5), phase 2 (checks A6–A14), phase 3 (A15/A15b retry);
`~/.pgpass` never read; all results are aggregates.

## 1. Summary (worst first)

1. **RESOLVED-BLOCKER — delisting returns are already embedded in `DlyRet` (A15).** On the daily row flagged `dlydelflg='Y'`, `DlyRet` equals `stkdelists.DelRet` in 100% of testable cases (16,741/16,741 MER; 7,932/7,932 GDR; 3,115/3,115 GLI; 1,211/1,211 GEX). That row is dated **after** `delistingdt` (median +1 day; never on `delistingdt` itself). A naive build that adds `DelRet` onto the last day would double-count every delisting. Correct rule in §5.
2. **MAJOR — duplicate (permno, dlycaldt) keys exist in every year (A7).** 29,742 duplicated keys (61,194 rows) across 1961–2026, ~0.06% of keys, up to 1,712 rows in one year (1974). The CIZ view repeats rows when security-info or share histories change intra-day; `02_build_dataset.py` must deduplicate or pairs get phantom double-priced days.
3. **MAJOR — NASDAQ daily volume is NULL for ~50–56% of common-stock rows 1973–1982 (A12a).** The Table 9 recall rule (volume > 18-month split-adjusted mean + 1 s.d.) is not computable for NASDAQ names in that era; NASDAQ volume-reporting conventions (units/side-counting) remain UNVERIFIED (A12b shows anomalous NASDAQ medians, e.g. 373,600 in 1979).
4. **MAJOR — inconsistent cut-offs (offline; `data/metadata/crsp_manifest.json`).** Daily panel ends 2026-03-31; monthly/delisting/distributions/indexes end 2026-06-30. The 2003–2026 extension loses its last quarter of daily signals; Apr–Jun 2026 delisting records have no daily row; monthly-vs-daily reconciliation must exclude that quarter.
5. **MAJOR — start-date conflict (offline).** `configs/config.yaml` `replication_start: 1963-07-01` matches the paper (July 1963–December 2002, 474 months); the team doc reportedly says 1986, which would discard 274 months of the replication sample. Follow the config; fix the doc.
6. **WARN — bid/ask coverage is thin before ~1995 (A10).** Valid-quote share of common rows: 10.7% (1963), 5.5% (1970), 51.6% (1980), 67.4% (1990), 97%+ (1995+). The §3.3 cost model on actual quotes only reaches full coverage in the late 1990s; median relative spread falls from 2.6–7.7% (pre-1995) to 0.16–0.35% (2005+).
7. **WARN — 7.8% of the 1989 eligible universe has SIC 0/unknown (A11).** Sector assignment for Table 3 needs an explicit missing-SIC rule; utilities are only 3.3% of the eligible universe (252/7,742), so the paper's 71% utilities weight among top pairs is a selection effect, not a universe property.
8. **MINOR — this clone holds only Git LFS placeholders** (`data/README.md`); every claim about the local files rests on the recorded manifests, not re-derived bytes.

Missing-return context (A6): 1,906,443 of 111,626,026 daily rows (1.7%) have null `DlyRet` — 2.29% within the 1963–2002 replication window, 1.14% in 2003–2026. Missingness is fully explained by `dlyretmissflg` codes (NT no-trade 1.40M, MP missing price 0.46M, NS/RA/GP/DM/DG/DG smaller); `dlyretmissflg='NA'` marks present returns. Two rows have both flags NULL (111,626,026 vs 111,626,024 in A5) — immaterial.

## 2. Requirements matrix (A-1)

| Paper / extension need | CRSP CIZ field(s) | Present in downloaded export? | Notes (evidence) |
| --- | --- | --- | --- |
| Total return including delisting (paper §2.2 p.11–12: close "using the delisting return, or the last available price") | `DlyRet`, `DlyRetx`, `DlyDelFlg`; `stkdelists.DelRet`, `DelistingDt` | Yes: all in daily panel (`crsp_manifest.json` columns) + delisting file | **`DlyRet` already contains the delisting return** on the `dlydelflg='Y'` row, dated `delistingdt + 1 trading day` (A15). Do **not** add `DelRet` again — double-counting is certain (100% equality). On the `delistingdt` row itself, `DlyRet` is the ordinary last-trade return (A13: equality there only 433/14,929 MER). Where `DlyRet` is NULL on the flagged row (3,187 GDR, matching A8's 3,187 null `DelRet`), apply the paper's fallback (proposal: −30% long leg; paper's robustness: −100%). |
| Common-stock filter (paper: "common stocks"; legacy `SHRCD 10/11`) | `SecurityType`, `SecuritySubType`, `ShareType`, `USIncFlg`, `IssuerType` | Yes (daily panel columns) | CIZ equivalent (A3): `securitytype='EQTY' AND securitysubtype='COM' AND sharetype='NS'` — 30,385 of 41,520 header securities. `ShareType='AD'` (ADRs, 1,385) is the SHRCD-30xx analogue and is excluded. `USIncFlg` (Y/N) and `IssuerType` (CORP/ACOR/REIT) are *not* part of the legacy 10/11 definition; keeping all of EQTY/COM/NS matches SHRCD 10/11, with US-incorporation as a documented sensitivity (3,129 NS non-US). Time-varying applicability via `SecInfoStartDt`/`SecInfoEndDt`/`SecurityHdrFlg`. |
| NYSE / AMEX / NASDAQ (legacy `EXCHCD 1,2,3`) | `PrimaryExch`, plus `ConditionalType`, `TradingStatusFlg`, `ExchangeTier` | Yes | Domains (A4 header, A14 daily by year): `N`=NYSE, `A`=NYSE American/AMEX, `Q`=NASDAQ, plus minor venues `R` (from ~2010), `B` (from ~2020), `X` (all eras, 1963: 1,439 rows) — the legacy 1/2/3 set maps to `('N','A','Q')`. `ConditionalType` is `RW` (regular way) for ~99.99%, `NW` 2 rows; `TradingStatusFlg` `A` active, `S` suspended (21 rows). Interaction: exchange alone is not a tradability filter — suspended/conditional rows still carry a `PrimaryExch`; the paper's no-trade screen (row below) supplies tradability. |
| "No trade on a day" screen (paper §2.1: drop stocks with ≥1 no-trade day in the 12-month formation window) | `DlyPrcFlg`, `DlyVol`, `DlyNumTrd`, `DlyPrc` | Yes | **Yes — `DlyPrcFlg` identifies it directly (A5).** `TR` = actual trade (92.1M rows); `BA` = bid/ask midpoint, no trade (17.6M); `NT` = no trade, no quote (1.40M); plus `HA` halted (23.6K), `SU` suspended (22.3K), `MP` missing price (413.9K), `DA`/`DP`/`DM`. A "no-trade day" (midpoint exists, no trade) = `dlyprcflg='BA'`; a strict "traded every day" screen is `dlyprcflg='TR'` on every day (used in A9). `DlyVol=0`/NULL corroborates but is redundant with the flag. |
| SIC for Table 3 sector pairs (paper §2.1: S&P groups "based on the stock's SIC code") | `SICCD` (time-varying), alternates `NAICS`, `ICBIndustry` | Yes | Mapping: Utilities = 2-digit 49; Transportation = 40–47; Financials = 60–69; Industrials = rest (paper Table 3, p.36). A11: at 1989, 7,742 eligible stocks with non-null SIC — Utilities 252 (3.3%), Transportation 133 (1.7%), Financials 1,543 (19.9%), SIC 0/unknown 602 (7.8%). SIC must be taken from the formation-window row (time-varying), not the latest. |
| Volume for the Table 9 recall rule (paper §3.9 p.29: volume > 18-month mean + 1 s.d., both split-adjusted) | `DlyVol`; split adjustment via `DlyFacPrc` or `stkdistributions.DisFacShr` | Yes (`DlyFacPrc` in daily panel; `disfacshr` in distributions file) | `DlyVol` NULL: 7.84M common rows (A12a) — concentrated 1973–1982 NASDAQ (~50–56%/yr; matches A14 NASDAQ row counts; consistent with CRSP receiving NASD volume from 1983). Zero-volume rows track no-trade days (1963: 10.7%). The recall trigger needs split-adjusted volume: `DlyVol` deflated by cumulative `DlyFacPrc` or rebuilt `disfacshr`; NASDAQ unit conventions UNVERIFIED (open question 5). |
| Bid/ask for the transaction-cost model (paper §3.3: 81 bp implied spread; extension S1/S2) | `DlyBid`, `DlyAsk`; fallback needs `DlyHigh`/`DlyLow` (Corwin–Schultz/Roll) | Yes | Coverage and quality by year in A10: valid-quote share ≥95% only from ~1995; median relative spread 2.6–7.7% pre-1995, 0.16–0.35% 2005+. Early quoted rows are likely AMEX-skewed (NYSE quotes from 1993) — UNVERIFIED (open question 6). For pre-quote years the extension falls back to high/low estimators, which the export supports. |

## 3. Query defects (A-2) and live-check results (A-3)

| Check | Query | Status | Result |
| --- | --- | --- | --- |
| A-3.1 missing returns by year × `dlyretmissflg` | A6 | **PASS** | 1.7% of 111.6M rows null `DlyRet` (2.29% in 1963–2002, 1.14% in 2003–2026); every null carries a miss flag (NT 1.40M, MP 0.46M, NS 41.5K, GP 2.5K, DM 1.8K, RA 1.5K, DG 1.4K); `NA`/`MV` rows have returns. Table spans 1925–2026 (live table exceeds the 1961+ export; export cutoff Mar 2026). |
| A-3.2 duplicate (permno, dlycaldt) keys | A7 | **FAIL** (must dedupe in build) | 29,742 duplicated keys / 61,194 rows, every year 1961–2026; ~0.06% of keys; worst year 1974 (1,712 rows). Consistent with intra-day security-info/share history changes in the CIZ view. |
| A-3.3 delisting action types + null `DelRet` | A8 | **PASS** (filter is complete) | The live domain is exactly the five filtered values: MER 14,938, GDR 11,114, GLI 3,040, GEX 1,117, LOS 3. `data/metadata/queries/delisting.sql` excludes nothing. Null `DelRet`: GDR 3,187 (28.7%), LOS 3/3, GLI 120, MER 11, GEX 5 → the −30%/last-price fallback matters mostly for GDR. |
| A-3.4 eligible universe at formation dates (12-month window, `EQTY/COM/NS` + `N/A/Q` + `dlyprcflg='TR'` every day + `dlyprc>0`) | A9 | **PASS** (sanity ✓) | n pass filter / n strict-liquid: 1963-07 2,097/622; 1970-01 2,364/1,214; 1980-01 4,964/1,132; 1990-01 6,819/1,839; 2000-01 8,302/3,873; 2002-07 6,758/3,619; 2010-01 5,018/3,483; 2020-01 4,615/3,646. 1963 count is near the paper's average group total (156+61+371+1,729 = 2,317, Table 3); 1990s ≈ 6.8K ("a few thousand" ✓). The strict screen binds hard pre-1980 (only 622 fully-traded names in 1962-63) — the paper's liquidity screen is what produces the small 1960s universes. |
| A-3.5 bid/ask coverage + median relative spread | A10 | **WARN** | Valid-quote share (`dlybid`,`dlyask` non-null, `ask>bid` ≈ 100% of quoted): 1963 10.7% (median spread 3.17%), 1970 5.5% (2.63%), 1980 51.6% (6.45%), 1990 67.4% (7.69%), 1995 97.2% (3.45%), 2000 91.4% (2.11%), 2005 96.9% (0.29%), 2010 97.7% (0.19%), 2020 99.0% (0.16%). Pre-1993 coverage is partial and its exchange composition is UNVERIFIED (open question 6). |
| A-3.6 SIC mix, 1989 window | A11 | **PASS** (with caveat) | Top 2-digit groups: 67 (8.8%), 0/unknown (7.8%), 36 (6.8%), 35 (6.5%), 73 (6.1%), 60 (5.3%)… Utilities (49) 252 = 3.25%; Transportation (40–47) 133; Financials (60–69) 1,543. Consistent with paper Table 2: utilities dominate top *pairs* despite being 3% of the universe. |
| A-3.7 volume null/zero + NASDAQ conventions | A12a/A12b | **WARN** | Null `DlyVol` 7.84M common rows (7.0%), concentrated 1973–1982 at 50–56%/yr (NASDAQ rows per A14; NASD volume reaches CRSP 1983). Zero-volume rows 6.65M (6.0%), tracking no-trade days. NASDAQ medians behave anomalously pre-1983 (1979: 373,600) — conventions UNVERIFIED. |
| Delisting-return overlap / embedding | A13, A15, A15b | **PASS** (rule established) | A13: a daily row exists on `delistingdt` for ~100% of delistings, but `DlyRet` there equals `DelRet` only 3% — the embedded row is elsewhere. A15: the `dlydelflg='Y'` row (population-wide 32,326 rows, A15b) is dated after `delistingdt` (median +1d; 0 on the date itself) and its `DlyRet` equals `DelRet` in 100% of testable cases; 16 delistings (2 MER, 11 GLI, 3 LOS) have no flagged row; 3,187 GDR have the flag but NULL `DlyRet`/`DelRet`. |

### 3.1 Delisting export filter — verdict

`data/metadata/queries/delisting.sql` keeps `delactiontype IN ('GDR','GEX','GLI','LOS','MER')`.
The live domain of `stkdelists.delactiontype` is exactly these five values (A8), so **no
delisting is excluded** and no re-download is needed. The residual exposure is null
`DelRet` (3,187 GDR + 128 others) and the 16 delistings with no `dlydelflg='Y'` daily row —
handled by the fallback rule in §5.

### 3.2 Inconsistent cut-offs — verdict

Daily 2026-03-31 vs everything else 2026-06-30 (`data/metadata/crsp_manifest.json`).
Consequences: (1) the frozen-rules extension loses Apr–Jun 2026 of daily signals and
mark-to-market; (2) 195 Apr–Jun 2026 delistings (A13 `n_after_daily_cutoff`) and any
distributions in that window have no daily row; (3) monthly returns exist for months the
daily panel lacks, so monthly/daily cross-checks must exclude 2026Q2; (4) `extension_end:
latest_available` resolves per dataset and must be pinned per file in the build.

### 3.3 Start date — verdict

`configs/config.yaml` says `replication_start: 1963-07-01` (paper: 474 months, July 1963–
December 2002). The team doc's reported "1986" start contradicts both and would drop 274
months including the entire pre-1989 high-profit regime (paper Table 8 Panel A). The data
support the config (acquisition from 1961). Action: correct the team doc; nothing to
re-download.

## 4. Recommended CIZ filter spec for `scripts/02_build_dataset.py`

Exact column conditions (all verified against live domains A3–A5, A14, A15):

```sql
-- 1. Common stock (legacy SHRCD 10/11 equivalent), using the row fields that are
--    effective on dlycaldt (SecInfoStartDt/SecInfoEndDt govern applicability):
    securitytype   = 'EQTY'
AND securitysubtype = 'COM'
AND sharetype       = 'NS'
--    USIncFlg / IssuerType are documentation-only: SHRCD 10/11 did not restrict
--    them; run USIncFlg='Y' as a sensitivity, not the base case.

-- 2. Exchange (legacy EXCHCD 1,2,3 equivalent):
    primaryexch IN ('N', 'A', 'Q')   -- N=NYSE, A=NYSE American/AMEX, Q=NASDAQ
--    R/B/X rows are minor venues the legacy filter excluded; keep excluded.

-- 3. Price sign and trade status: never use a raw sign to infer tradability.
--    DlyPrcFlg codes: TR=trade price, BA=bid/ask midpoint (no trade),
--    NT=no trade/no quote, HA=halted, SU=suspended, MP=missing, DA/DP/DM other.
--    A "no-trade day" (paper §2.1) is any day with dlyprcflg <> 'TR' (BA included).

-- 4. Formation-window eligibility (per paper §2.1, 12 months ending before the
--    trading window): for every trading day t in the window the stock has a row,
--    dlyprcflg = 'TR', and dlyprc > 0. (A9 implements exactly this.)

-- 5. Duplicate keys: deduplicate to one row per (permno, dlycaldt) after the
--    filter (A7: 29,742 duplicated keys). Keep the row with the latest
--    SecInfoStartDt, or aggregate deterministically; never sum returns.

-- 6. Delisting handling (A15: DlyRet ALREADY includes the delisting return):
--    a. The terminal observation of a delisted PERMNO is the daily row with
--       dlydelflg = 'Y', dated delistingdt + 1 trading day.
--    b. Its DlyRet IS the delisting return (100% equality with stkdelists.DelRet).
--       Use it as the closing return; do NOT multiply stkdelists.DelRet again.
--    c. If that row's DlyRet IS NULL (3,187 GDR + others; DelRet also NULL),
--       apply the paper fallback: -30% for a performance-related delisting
--       (report/proposal_trading_simulation.md), with the paper's -100% long-leg
--       extreme as robustness.
--    d. For 16 delistings with no flagged row (A15), close at the last available
--       price (paper §2.2's "or the last available price").
```

## 5. Open questions

1. **`USIncFlg`/`IssuerType` scope:** does the replication keep non-US-incorporated common shares (SHRCD 10/11 allowed them)? Base spec keeps them; sensitivity run recommended (A3).
2. **Minor venues `X`/`R`/`B`:** confirm the legacy intent — `EXCHCD 1,2,3` excluded them, and the spec keeps them out; if the team wants "all CRSP trades", the counts are in A14 (X: 1,439 rows in 1963 alone).
3. **Which exchange supplies the pre-1993 quotes** (A10 shows 10.7–67.4% coverage but not its composition) — likely AMEX-only until NYSE quotes begin; needs a per-exchange coverage query in a future run or the CRSP v2 documentation.
4. **`ConditionalType`/`TradingStatusFlg` historical domains** were verified only on the current header snapshot (A4); the daily-row historical domain (esp. pre-1970) is UNVERIFIED.
5. **NASDAQ volume-reporting conventions** (units, side-counting, the pre-1983 gap) — A12b medians are anomalous; needs the CRSP v2 volume documentation before implementing the Table 9 recall trigger.
6. **Vintage:** today's CIZ data are not the authors' 2006 database; convention differences are documented, not resolvable (report/DATA_REQUIREMENTS.md). The 2-row difference between A5 and A6 totals (null flags) is immaterial but noted.
7. **`dlyretmissflg` code semantics** (`RA`, `MV`, `DG`, `DP`, `GP`) are inferred from null-patterns (A6) and should be checked against the WRDS data dictionary when the build consumes them.
