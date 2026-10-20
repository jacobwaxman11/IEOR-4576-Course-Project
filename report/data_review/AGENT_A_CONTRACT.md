# Contract A: Is the CRSP data fit for the GGR (2006) replication and our extensions?

Read `report/data_review/COMMON_RULES.md` first. Every rule in it is binding.

## Exclusive writes

- `report/data_review/A_FINDINGS.md`, the deliverable.
- `report/data_review/A_queries.sql`, every SQL statement you ran, each labelled `-- A1`, `-- A2`, and so on.
- `report/data_review/A_checks.py`, the single runner script for the connecting phases.
- `report/data_review/A_results/*.csv`, aggregates only.

Edit nothing else.

## Read first (offline; no WRDS needed)

- **The paper:** `pdftotext -layout Pairs_Trading_RV_Arbitrage_Rule.pdf - | less`. Read Section 2 (methodology: formation and trading, eligibility, the "no-trade day" rule, delisting treatment), Table 2 (pair composition, utilities share), Table 3 (sectors), and Section 3.3 plus Table 9 (short-selling, volume-based recalls).
- **Data requirements and acquisition:** `report/DATA_REQUIREMENTS.md`, `data/README.md`, `data/raw/crsp/README.md`.
- **What was actually downloaded:** `data/metadata/crsp_manifest.json`, `data/metadata/queries/*.sql`, `data/metadata/queries/*.json`.
- **Sample settings:** `configs/config.yaml`.
- **Extension needs (frictions, bid/ask, volume, 2003 to 2026):** `report/proposal_trading_simulation.md`.

## Tasks

### A-1. Requirements matrix (offline)

Build a table with these columns: paper or extension need → CRSP CIZ field(s) → present in the downloaded export? → notes.

It must cover:

- **Total return including delisting.** Does the CIZ daily `DlyRet` already include the delisting return on the last day, or must `stkdelists.DelRet` be added? State the double-counting risk either way.
- **The common-stock filter.** The legacy filter was SHRCD 10/11. Give its CIZ equivalent using `SecurityType`, `SecuritySubType`, `ShareType`, `USIncFlg` and `IssuerType`.
- **NYSE/AMEX/NASDAQ** via `PrimaryExch`, and how `ConditionalType` and `TradingStatusFlg` interact with it.
- **The "no trade on a day" eligibility rule.** Can `DlyPrcFlg` or `DlyVol` identify days with a bid/ask midpoint and no trade?
- **SIC** for the Table 3 sector pairs (Utilities, Transportation, Financials, Industrials).
- **Volume** for the Table 9 recall rule (volume above its 18-month mean plus one standard deviation, split-adjusted via `DlyFacPrc` or the distributions table).
- **Bid and ask prices** (`DlyBid`, `DlyAsk`) for the transaction-cost model.

### A-2. Query defects found by reading (offline)

- **The delisting export filter.** `data/metadata/queries/delisting.sql` keeps only `delactiontype IN ('GDR','GEX','GLI','LOS','MER')`. List every value that exists in the field, and decide whether any excluded value matters for the paper's delisting treatment. Confirm the list live in A-3.
- **Inconsistent cut-offs.** The daily file ends on 2026-03-31; the others end on 2026-06-30. State the consequences.
- **The start date.** The team doc says the sample starts in "1986"; the paper and config say 1963-07. Flag this.

### A-3. Live checks

Run these in one connecting script, after the schema-discovery run.

1. **Missing returns by year.** For the CIZ daily stock table (find its name with `db.list_tables('crsp')` and `'crsp_q_stock'`; the export used `crsp_q_stock.wrds_dsfv2_query`), count rows with a null `dlyret`, by year and by `dlyretmissflg`.
2. **Duplicate keys.** Count (permno, dlycaldt) pairs with more than one row, by year. The view can repeat rows when security-info or share histories change within a day.
3. **Delisting action types.** All `delactiontype` values with counts, plus `delret` null counts per type. Compare with the five types in the export filter.
4. **Eligible universe at sample formation dates:** 1963-07, 1970-01, 1980-01, 1990-01, 2000-01, 2002-07, 2010-01 and 2020-01.
   - Count stocks that pass your common-stock and exchange filter.
   - Of those, count the stocks with a price on every trading day of the prior 12 months and no no-trade day.
   - Report both counts per date. The paper does not tabulate universe size, so sanity-check against your own reasoning: a few thousand in the 1990s is expected.
5. **Bid/ask coverage.** By year, the share of common-stock rows where `dlybid` and `dlyask` are both non-null and `dlyask > dlybid`, plus the median relative spread `(ask - bid) / midpoint`.
6. **SIC mix.** At the 1990-01 formation date, the distribution of 2-digit SIC among eligible stocks, and the utilities share (SIC 49). This gives context for the paper's 71% utilities share among top pairs.
7. **Volume.** By year, the share of rows with `dlyvol` null or zero. Check for the known NASDAQ volume-reporting conventions; the paper notes these.

## Deliverable: `A_FINDINGS.md`

1. A summary of at most 8 bullets, worst first, each with its severity.
2. The requirements matrix from A-1.
3. Results from A-2 and A-3. Each check gets PASS, FAIL, WARN or UNVERIFIED, with numbers and its query ID.
4. A **recommended CIZ filter spec** for `scripts/02_build_dataset.py`, written as exact column conditions, covering: common stock, exchange, eligibility, delisting-return handling and the price sign.
5. The questions that are still open.
