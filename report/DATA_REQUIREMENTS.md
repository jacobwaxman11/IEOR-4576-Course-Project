# Data required for replication and the updated daily sample

Requested acquisition: January 1961 (warm-up buffer) through the latest available observations.
The paper's source sample is 1962–December 2002; its main performance sample begins July 1963.
Access and cutoff checks below were made on October 10, 2026.

| Dataset | Required fields and use | Source / observed coverage |
| --- | --- | --- |
| Daily stock panel, all historical securities | PERMNO/PERMCO; prices, price/trading flags; total and ex-distribution returns; volume; capitalization and shares | WRDS CRSP quarterly CIZ: validated from January 3, 1961 through March 31, 2026. |
| Historical identity/classification | Effective dates, ticker, CUSIP, company name, SIC, exchange, security/share type | CRSP names/history; history fields also selected in daily export |
| Corporate actions | Dividends, splits, adjustment factors, ex/payment dates and action types | CRSP distributions; daily summary amounts/factors also selected |
| Delisting events | Dates, reason, delisting return/value/last price and successor mapping | CRSP delisting records. CIZ and legacy return handling differ; avoid double counting. |
| Monthly stock panel | Returns, prices, capitalization, shares and historical identifiers | CRSP monthly CIZ: through June 30, 2026; lagged-return sorts and reversal/momentum checks |
| Benchmarks | Broad equal/value-weighted market returns and S&P 500 price returns | Daily/monthly index files downloaded through June 30, 2026. `sprtrn` is a price return. Goyal–Welch workbooks now supply a CRSP S&P 500 total-return candidate through December 2025; equality to the paper's EnCorr input remains unverified. |
| Risk factors | Market excess return, SMB, HML, momentum, risk-free return; short-term reversal and prior-month return deciles for comparison | [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html); actual file cutoffs recorded in the local manifest |
| Additional Table 4 factor inputs | Large/small-company, long-term corporate/government bond, and Treasury-bill **total returns** | Historical Ibbotson bond returns recovered through Goyal–Welch; French RF has Ibbotson provenance during the paper sample; underlying DFA small-stock fund recovered from 1982. Pre-1982 small-stock history and exact EnCorr equivalence remain unresolved. See [source investigation](IBBOTSON_DATA_SOURCES.md). |

## Vintage and extraction controls

- Include delisted firms and historical identifiers; do not start from today's ticker list.
- Select the entire CRSP database without a present-day market-cap or S&P 500 constituent filter.
- Retain signed legacy price flags and current CIZ flags; a quote-derived price is not an actual trade.
- Preserve raw archives unchanged. Write hashes, row counts, schema and observed date bounds under
  `data/metadata/`. Do not infer successful download from an export submission.
- Keep event records separate from the daily panel to avoid multiplying daily observations when
  several distributions occur on one date.
- CIZ monthly returns compound daily returns and reinvest dividends on ex-dates. Legacy monthly
  conventions differ. Contemporary data are not the authors' original 2006 database vintage.
- Download the CRSP legacy SIZ sample separately if needed to diagnose convention differences.
  Its observed endpoint is December 31, 2024; it cannot provide the 2025–2026 update.
- “Through present day” is bounded by provider releases. The daily CRSP query reports March 2026; the monthly query reports June 2026.
  FMP/Alpha Vantage updates would introduce another vendor/universe and must be labeled separately.

## What is derived rather than downloaded

Normalized cumulative total-return paths, distances/correlations/cointegration statistics,
formation-period eligibility, staggered-cohort returns, trading costs, regime features,
performance statistics, and the paper's custom reversal portfolios are computed from the inputs.
Table 4 size/default/horizon premia use geometric differences of the relevant total-return series.
Exact factor definitions and the paper's reversal-sign ambiguity need to be resolved before reporting.

Intraday TAQ access was verified with small 2020 and 2025 queries. A minute/hour extension still
requires a bounded historical universe, quote/trade cleaning, and explicit bar construction; it is
not part of the original paper's required daily download.

## Local acquisition status

All six core CRSP archives are saved in `data/raw/crsp/`:

| Archive | Rows | Observed date range | Query | Validation |
| --- | ---: | --- | --- | --- |
| `daily_stocks_1961_2026q1.csv.gz` | 102,464,776 | 1961-01-03–2026-03-31 | 11771134 | Passed |
| `monthly_stocks_1961_2026q2.csv.gz` | 5,003,530 | 1961-01-31–2026-06-30 | 11771141 | Passed |
| `delisting_1961_2026q2.csv.gz` | 29,727 | 1961-01-20–2026-06-29 | 11771161 | Passed |
| `distributions_1961_2026q2.csv.gz` | 1,023,403 | 1961-01-03–2026-06-30 | 11771165 | Passed |
| `daily_indexes_1961_2026q2.csv.gz` | 16,481 | 1961-01-03–2026-06-30 | 11771207 | Passed |
| `monthly_indexes_1961_2026q2.csv.gz` | 786 | 1961-01-31–2026-06-30 | 11771212 | Passed |

The daily stock panel contains 40,427 distinct PERMNOs and 70 fields; the monthly
panel contains 41,016 distinct PERMNOs and 63 fields. Both include
historical identifier/classification and shares-effective-date fields. Separate
names and shares downloads are not needed to obtain those selected panel fields.
The event files remain separate; their header identifiers must not be mistaken
for time-varying classifications.

Eight current public French archives are validated through August 2026 in
`data/raw/french/`. Eight additional archives in `data/raw/french_legacy_202412/`
provide the December 2024 legacy FIZ version for sensitivity checks. They do not
recreate the authors' original 2006 database vintage. See the
[official legacy archive](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library_202412_archive.html).

Additional Table 4 inputs were recovered on October 10, 2026:

- `data/raw/goyal_welch/PredictorData_original_2005.xls` and `PredictorData2025.xlsx`
  contain Ibbotson-sourced historical corporate/government bond returns. Both have
  all 475 months from June 1963 through December 2002, and the bond columns agree
  exactly across those vintages. The current file changes to Bloomberg bond
  indices from 2022 and ends in December 2025.
- The French monthly `RF` source is Ibbotson through May 2024, then ICE BofA.
  The exact original EnCorr values and precision have not been compared.
- `data/raw/crsp/dfscx_monthly_1981_2026q2.csv` contains 535 rows for fund 008296:
  one nonnumeric December 1981 inception-period return (`R`) and 534 monthly
  returns from January 1982 through June 2026. The 252 returns from January 1982
  through December 2002 have no missing values. WRDS query: 11771343.

The full exact Table 4 Ibbotson panel is still incomplete. The pre-1982 historical
small-stock component remains missing; the recovered fund, bill and large-stock
inputs require comparison against the authors' EnCorr series. WRDS global search
did not locate SBBI, but a direct CRSP mutual-fund query did recover DFSCX.
See [IBBOTSON_DATA_SOURCES.md](IBBOTSON_DATA_SOURCES.md) for source definitions,
evidence and remaining gaps. Do not substitute Treasury yields or label CRSP
`sprtrn` as a total return.

The local manifests in `data/metadata/` contain hashes, counts and coverage.
SQL exports are retained where WRDS supplies them; the daily/monthly stock
parameters are transcribed as JSON from the saved WRDS output pages in
`data/metadata/queries/`. Licensed observations remain local. Only the public French archives are included in this repository; licensed observations remain local.

Validation read both full stock archives to the end, confirming gzip integrity,
WRDS row counts, observed date bounds, and no missing dates; SHA-256 checksums
are recorded. The six CRSP archives total 4,665,270,300 compressed bytes.
These are acquisition checks, not a completed analysis of missing returns,
security eligibility, or duplicate security-date keys. Those belong in the dataset
construction stage before a backtest is reported.
