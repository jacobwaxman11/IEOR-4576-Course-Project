# CRSP raw downloads

Run `git lfs pull` from the repository root to obtain the LFS objects. Six exports
are stored intact. The daily-stock gzip archive is stored as three consecutive
binary parts because its 4,418,976,684 bytes exceed GitHub's individual-account
LFS per-file limit. Each part is smaller than 2 GB. The parts are not standalone
gzip files; concatenate them before reading the archive.

From the repository root:

```sh
cat data/raw/crsp/daily_stocks_1961_2026q1.csv.gz.part-001 \
    data/raw/crsp/daily_stocks_1961_2026q1.csv.gz.part-002 \
    data/raw/crsp/daily_stocks_1961_2026q1.csv.gz.part-003 \
    > data/raw/crsp/daily_stocks_1961_2026q1.csv.gz
shasum -a 256 data/raw/crsp/daily_stocks_1961_2026q1.csv.gz
gzip -t data/raw/crsp/daily_stocks_1961_2026q1.csv.gz
```

Expected SHA-256:

```text
345fcf6bb2473ded89377e18aa8b15ecf79dd3942d71fdeb8e3bdd7d3faab057
```

The assembled file is ignored by Git to avoid storing a duplicate object.
Allow approximately 4.42 GB of additional disk space for reassembly. Part checksums
and the exact original size are in `data/metadata/daily_stocks_storage_parts.json`.
Raw source bytes have not been cleaned, recompressed or otherwise changed.

These data are sourced from WRDS/CRSP and remain subject to vendor licenses.
The repository does not grant a separate license to use or redistribute them.
