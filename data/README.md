# Raw data and acquisition records

The repository includes 16 untouched archives from the
[Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html),
stored with Git LFS. Source attribution and original archive contents are preserved.

| Location | Included in GitHub | Coverage / purpose |
| --- | --- | --- |
| `raw/french/` | 8 ZIP archives | Current factors and comparison portfolios through August 2026 |
| `raw/french_legacy_202412/` | 8 ZIP archives | December 2024 legacy FIZ snapshots for sensitivity checks |
| `metadata/` | Manifests, validation summaries and source URLs | File sizes, SHA-256 checksums, schema and date coverage for all acquired datasets |
| `metadata/queries/` | 4 SQL exports and 3 JSON query records | Reacquisition of the seven local WRDS exports with an authorized subscription |
| `raw/crsp/` | Local only | Six core CRSP archives plus DFSCX monthly returns; approximately 4.67 GB compressed/on disk |
| `raw/goyal_welch/` | Local only | Two source workbooks and their accompanying paper; original download URLs are in the manifest |

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

Check the actual archive bytes against `french_manifest.json` and
`french_legacy_202412_manifest.json`. Plain Git blobs contain LFS pointers, so a
clone without LFS hydration will not contain the ZIP bytes yet.

## Reacquire the local-only data

Use the SQL/query parameters in `metadata/queries/` with your own authorized
WRDS account. Do not share credentials. WRDS query-result links expire and may
only be accessible to their original owner; the durable reproduction inputs are
the query definitions, field lists and date ranges. Updated vendor releases can
produce different observations and checksums.

The daily/monthly stock query JSON files are transcribed from saved WRDS query
pages. Raw browser captures, personal account paths and temporary download links
are not published. The associated source captures remain in the acquisition
workspace. Goyal–Welch public source URLs are recorded in
`metadata/goyal_welch_download.json`; those workbooks include third-party series
whose redistribution rights have not been established.

[WRDS's download policy](https://wrds-www.wharton.upenn.edu/pages/about/data-download-and-analysis-policy/)
requires private storage and adherence to vendor licenses. The licensed raw
observations are not included in this public repository. Keep local extracts in
the ignored directories and preserve raw files unchanged.

See the [full data inventory](../report/DATA_REQUIREMENTS.md) and
[Table 4 source investigation](../report/IBBOTSON_DATA_SOURCES.md). Exact pre-1982
SBBI small-stock data remain missing, and exact EnCorr-vintage equivalence has
not been established. Acquisition checks do not constitute a completed replication.
