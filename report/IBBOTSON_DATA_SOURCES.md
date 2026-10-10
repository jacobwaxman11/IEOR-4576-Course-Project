# Table 4 data-source investigation

Checked October 10, 2026. The core CRSP/French downloads are documented in
[DATA_REQUIREMENTS.md](DATA_REQUIREMENTS.md). This note concerns the additional
Ibbotson factor model, not whether the main pairs-trading backtest can run.

## What the paper specifies

Gatev, Goetzmann and Rouwenhorst name **Ibbotson EnCorr Analyzer** in the Table 4
caption (paper PDF page 38, printed page 37). They do not provide a download
URL, series identifiers, or the exact data vintage. The caption specifies monthly
geometric differences for small stocks versus large stocks, long-term corporate
bonds versus long-term government bonds, and long-term government bonds versus
Treasury bills. Compute these from simple decimal returns as
`(1 + return_a) / (1 + return_b) - 1`.

The caption separately describes the S&P 500 return in excess of Treasury bills;
do not assume that wording establishes a geometric market excess return.
The Table 4 caption starts in June 1963 (475 months through December 2002), while
the main performance sample starts in July 1963 (474 months). Retain the June
observation and resolve the boundary when aligning reconstructed strategy returns.

## Downloaded: historical bond returns

[Amit Goyal's research page](https://sites.google.com/view/agoyal145) links both the
original data through 2005 and updated data through 2025 for Goyal and Welch
(2008). Both untouched workbooks and their paper are saved in `data/raw/goyal_welch/`:

- `PredictorData_original_2005.xls`
- `PredictorData2025.xlsx`
- `goyal_welch_2008.pdf`

In the `Monthly` sheet, `ltr` is the long-term government-bond return and `corpr`
is the long-term corporate-bond return. Goyal and Welch explicitly attribute
both historical return series to the Ibbotson SBBI Yearbook (PDF page 5, printed
page 1459). This is strong provenance for the missing bond inputs, although it
does not prove equality to the particular EnCorr extraction used by Gatev et al.

Validation found:

- 475 observations for each bond series in June 1963–December 2002; no missing
  returns or duplicate months.
- The two workbook vintages have identical `ltr` and `corpr` values in every one
  of those months.
- Original workbook bond coverage is January 1926–December 2005; the updated
  workbook extends to December 2025.
- Goyal explicitly switches `ltr` and `corpr` to Bloomberg indices **from 2022**.
  The updated file is therefore not an uninterrupted original-SBBI series, and
  does not yet supply 2026 observations.

Hashes, file sizes and download URLs are in `data/metadata/goyal_welch_download.json`;
coverage and comparisons are in `data/metadata/goyal_welch_validation.json`.
The raw Goyal–Welch files are included using Git LFS. Their source attribution is
preserved; public hosting does not establish additional rights to the third-party series.

## Available candidates: Treasury bills and large stocks

The downloaded French monthly factors already contain `RF` for every Table 4
month. The [official French definition](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html)
identifies Ibbotson Associates as the source through May 2024 and ICE BofA from
June 2024. French values are in percent; divide by 100. Their reported precision
and equality to the authors' EnCorr series have not been verified.

The Goyal workbooks also include `CRSP_SPvw`, an S&P 500 total-return candidate,
and `CRSP_SPvwx`, its ex-dividend counterpart. Their paper describes obtaining
monthly S&P 500 returns including dividends from CRSP (PDF page 3, printed
page 1457). These are not verified as the EnCorr large-stock series. The downloaded
WRDS `sprtrn` field is a price return and must not be relabeled as a total return.

Only the bond columns agree between the two Goyal vintages: `CRSP_SPvw` differs
in 470 of the 475 Table 4 months and `Rfree` differs in all 475. Do not combine
vintages silently. In particular, Goyal's `tbl` is a three-month Treasury-bill
rate, not a monthly total-return series.

## Remaining small-stock history and routes checked

The [2020 SBBI Summary Edition](https://rpc.cfainstitute.org/sites/default/files/-/media/documents/book/rf-publication/2020/rf-sbbi-summary-edition.pdf)
(printed page 41) identifies a historical NYSE small-stock portfolio through
1981, followed by the DFA U.S. Small Company 9–10 Portfolio from January 1982,
renamed U.S. Micro Cap Portfolio in April 2001. The historical portfolio uses
five-year rebalancing; standard CRSP size-decile indices are not automatically
identical. The 1981 observations have limited precision.

[Dimensional's own history](https://www.dimensional.com/us-en/insights/the-evolution-of-small-cap-investing-four-decades-of-innovation-at-dimensional)
identifies the fund as **DFSCX**. CRSP Mutual Funds (Quarterly) is accessible in
the authenticated WRDS account, offering monthly total returns, NAV and assets.
WRDS query **11771343** successfully downloaded the fund component to
`data/raw/crsp/dfscx_monthly_1981_2026q2.csv`. The ticker lookup resolves to permanent
fund number **008296**, including earlier records without a ticker. Validation:

- 535 rows from December 1981 through June 2026; no duplicate fund-months or
  missing calendar months.
- December 1981 has the nonnumeric return code `R`; it is preserved unchanged,
  not treated as zero.
- 534 numeric monthly returns from January 1982 through June 2026.
- All 252 months from January 1982 through December 2002 are present with numeric
  returns. The remaining pre-fund segment is 223 months from June 1963 through
  December 1981 (222 if the eventual regression begins in July 1963).

The query, checksum and validation are recorded in
`data/metadata/queries/dfscx_monthly_query.json` and
`data/metadata/dfscx_monthly_validation.json`. These fund returns still require
comparison with SBBI before claiming numerical identity. The current raw stock
download begins in 1961 and does not include the December 1960 formation date
that a reconstruction of the earlier five-year-rebalanced portfolio would need.
Reconstruction would be a separate, explicitly labeled exercise; it would not
recover the authors' original file or establish exact equality by itself.

The [public 1989 SBBI book](https://rpc.cfainstitute.org/en/research/foundation/1989/rf-v1989-n3-sbbi-historical-returns)
confirms the construction (printed pages 18–19), but its month-by-month exhibit
is a bar chart (printed pages 75–76), not a usable monthly observation table.
Annual observations cannot fill a monthly regression input.

Authenticated WRDS searches for Ibbotson/SBBI and the CRSP index catalog did not
locate the complete SBBI series. This is a limited search result, not proof that
no Columbia subscription can supply it. The general company search also missed
the CRSP mutual-fund route, so vendor-specific queries are more informative.

[Columbia's library guide](https://guides.library.columbia.edu/ms/resources) lists
Morningstar Direct on Uris and Manhattanville workstations. A workstation or remote Direct session was not available during acquisition. Relevant series names
from the SBBI documentation for a later authorized export are:

- `IA SBBI US Small Stock TR USD`
- `IA SBBI US Large Stock TR USD Ext`
- `IA SBBI US LT Corp TR USD`
- `IA SBBI US LT Govt TR USD`
- `IA SBBI US 30 Day TBill TR USD`

Request monthly total returns for at least June 1963–December 2002 and the latest
available extension, retaining series metadata and source/vintage information.
Do not silently replace the legacy series with a successor index or assume that
Morningstar still updates every legacy series through the present.
