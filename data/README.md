# Raw data and acquisition records

The repository includes all 26 acquired raw download files, represented by 28
Git LFS objects because one archive is split into three parts. Sixteen archives are from the
[Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html),
stored with Git LFS. Source attribution and original archive contents are preserved.

| Location | Included in GitHub | Coverage / purpose |
| --- | --- | --- |
| `raw/french/` | 8 ZIP archives | Current factors and comparison portfolios through August 2026 |
| `raw/french_legacy_202412/` | 8 ZIP archives | December 2024 legacy FIZ snapshots for sensitivity checks |
| `metadata/` | Manifests, validation summaries and source URLs | File sizes, SHA-256 checksums, schema and date coverage for all acquired datasets |
| `metadata/queries/` | 4 SQL exports and 3 JSON query records | Reacquisition of the seven WRDS exports with an authorized subscription |
| `raw/crsp/` | Seven exports represented by nine LFS objects | Six core CRSP archives plus DFSCX monthly returns; the daily-stock archive is split into three lossless parts |
| `raw/goyal_welch/` | Three LFS objects | Two source workbooks and their accompanying paper; original download URLs are in the manifest |

Each French vintage contains monthly and daily versions of the Fama–French
three factors, momentum, short-term reversal, and ten prior-month-return portfolios.
The factors are supplied in percent. A historical archive is not the same as the
authors' original database vintage.

## Retrieve the committed archives

Install [Git LFS](https://git-lfs.com/) once, then run from the repository root:

```sh
git lfs install
git lfs pull
```

The full LFS download is approximately 4.67 GB. Reassemble the daily-stock archive
using [the CRSP instructions](raw/crsp/README.md), which requires another 4.42 GB
of disk space. The assembled archive must match its original SHA-256 checksum.

Check the actual archive bytes against `french_manifest.json` and
`french_legacy_202412_manifest.json`. Plain Git blobs contain LFS pointers, so a
clone without LFS hydration will not contain the ZIP bytes yet.

## Reacquire data from their sources

Use the SQL/query parameters in `metadata/queries/` with your own authorized
WRDS account. Do not share credentials. WRDS query-result links expire and may
only be accessible to their original owner; the durable reproduction inputs are
the query definitions, field lists and date ranges. Updated vendor releases can
produce different observations and checksums.

The daily/monthly stock query JSON files are transcribed from saved WRDS query
pages. Raw browser captures, personal account paths and temporary download links
are not published. The associated source captures remain in the acquisition
workspace. Goyal–Welch public source URLs are recorded in
`metadata/goyal_welch_download.json`. Third-party rights and attribution remain
with the original providers; no new data license is granted by this repository.

[WRDS's download policy](https://wrds-www.wharton.upenn.edu/pages/about/data-download-and-analysis-policy/)
requires private storage and adherence to vendor licenses. Public hosting of
these files does not change those requirements or grant additional rights.
Preserve raw files unchanged and consult the provider terms before using or
redistributing them.

See the [full data inventory](../report/DATA_REQUIREMENTS.md) and
[Table 4 source investigation](../report/IBBOTSON_DATA_SOURCES.md). Exact pre-1982
SBBI small-stock data remain missing, and exact EnCorr-vintage equivalence has
not been established. Acquisition checks do not constitute a completed replication.
