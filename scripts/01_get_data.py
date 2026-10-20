"""Download every input the replication and extensions need.

    .venv/bin/python scripts/01_get_data.py         (everything, resumable)
    .venv/bin/python scripts/01_get_data.py --only daily_stocks --years 1961-1965

WRDS tables come through one connection (one Duo push) via
``project.data.wrds_connection`` and are streamed with server-side COPY, then
stored as Parquet under the git-ignored ``data/raw/wrds_api/``. Public files
(French library, Goyal-Welch) go to the git-ignored ``data/raw/public/``.
Existing outputs are skipped, so an interrupted run resumes where it stopped.
A manifest with row counts, date bounds, SHA-256 and the exact SQL is written to
``data/raw/wrds_api/manifest.json`` and copied to ``data/metadata/``.

Choices informed by report/data_review/ (A_FINDINGS.md, B_FINDINGS.md):
- Stock data come from the quarterly library ``crsp_q_stock``; the annual
  ``crsp`` library ends a quarter or two earlier.
- The daily/monthly WRDS views append distribution columns, which repeats a
  security-day when several distributions share an ex-date. Those columns are
  not selected (distributions are downloaded separately) and rows are
  de-duplicated with SELECT DISTINCT. Rows that still repeat a key come from
  intra-day security-info or share-history changes and are resolved in
  02_build_dataset.py.
- ``dlyret`` already holds the delisting return on the ``dlydelflg = 'Y'`` row,
  so ``stkdelists.delret`` must not be compounded on top of the daily panel.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv
import pyarrow.parquet as pq
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from project.data import wrds_connection
from project.paths import DATA_RAW, ROOT, WRDS_API_DIR

PUBLIC_DIR = DATA_RAW / "public"
MANIFEST = WRDS_API_DIR / "manifest.json"
MANIFEST_COPY = ROOT / "data" / "metadata" / "wrds_api_manifest.json"

DAILY_COLUMNS = [
    "permno",
    "permco",
    "dlycaldt",
    "secinfostartdt",
    "secinfoenddt",
    "shrstartdt",
    "shrenddt",
    "primaryexch",
    "conditionaltype",
    "tradingstatusflg",
    "securitytype",
    "securitysubtype",
    "sharetype",
    "usincflg",
    "issuertype",
    "siccd",
    "naics",
    "ticker",
    "hdrcusip",
    "dlydelflg",
    "dlyprc",
    "dlyprcflg",
    "dlycap",
    "dlyret",
    "dlyretx",
    "dlyretmissflg",
    "dlyvol",
    "dlyclose",
    "dlylow",
    "dlyhigh",
    "dlybid",
    "dlyask",
    "dlyopen",
    "dlynumtrd",
    "dlyfacprc",
    "dlycumfacpr",
    "dlycumfacshr",
    "shrout",
]
MONTHLY_COLUMNS = [
    "permno",
    "permco",
    "mthcaldt",
    "secinfostartdt",
    "secinfoenddt",
    "shrstartdt",
    "shrenddt",
    "primaryexch",
    "conditionaltype",
    "tradingstatusflg",
    "securitytype",
    "securitysubtype",
    "sharetype",
    "usincflg",
    "issuertype",
    "siccd",
    "naics",
    "ticker",
    "hdrcusip",
    "mthdelflg",
    "mthprc",
    "mthprcflg",
    "mthcap",
    "mthret",
    "mthretx",
    "mthretflg",
    "mthvol",
    "mthvolflg",
    "mthcumfacpr",
    "mthcumfacshr",
    "shrout",
]

FRENCH_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
FRENCH_FILES = [
    "F-F_Research_Data_Factors_CSV.zip",
    "F-F_Research_Data_Factors_daily_CSV.zip",
    "F-F_Momentum_Factor_CSV.zip",
    "F-F_Momentum_Factor_daily_CSV.zip",
    "F-F_ST_Reversal_Factor_CSV.zip",
    "F-F_ST_Reversal_Factor_daily_CSV.zip",
    "10_Portfolios_Prior_1_0_CSV.zip",
    "10_Portfolios_Prior_1_0_Daily_CSV.zip",
    "F-F_Research_Data_5_Factors_2x3_CSV.zip",
    "F-F_Research_Data_5_Factors_2x3_daily_CSV.zip",
    "49_Industry_Portfolios_CSV.zip",
    "49_Industry_Portfolios_daily_CSV.zip",
]


def wrds_tables(start: str) -> dict[str, tuple[str, str, tuple[str, str]]]:
    """name -> (sql, date column, (library, table) for column types); all but the daily panel."""

    def cols(c):
        return ", ".join(c)

    return {
        "monthly_stocks": (
            (
                f"SELECT DISTINCT {cols(MONTHLY_COLUMNS)} FROM crsp_q_stock.wrds_msfv2_query "
                f"WHERE mthcaldt >= '{start}'"
            ),
            "mthcaldt",
            ("crsp_q_stock", "wrds_msfv2_query"),
        ),
        "delisting": (
            f"SELECT * FROM crsp_q_stock.stkdelists WHERE delistingdt >= '{start}'",
            "delistingdt",
            ("crsp_q_stock", "stkdelists"),
        ),
        "distributions": (
            f"SELECT * FROM crsp_q_stock.stkdistributions WHERE disexdt >= '{start}'",
            "disexdt",
            ("crsp_q_stock", "stkdistributions"),
        ),
        "security_info_header": (
            "SELECT * FROM crsp_q_stock.stksecurityinfohdr",
            "securityenddt",
            ("crsp_q_stock", "stksecurityinfohdr"),
        ),
        "daily_indexes": (
            f"SELECT * FROM crsp_q_stock.wrds_dailyindexret_query WHERE dlycaldt >= '{start}'",
            "dlycaldt",
            ("crsp_q_stock", "wrds_dailyindexret_query"),
        ),
        "monthly_indexes": (
            f"SELECT * FROM crsp_q_stock.wrds_monthlyindexret_query WHERE mthcaldt >= '{start}'",
            "mthcaldt",
            ("crsp_q_stock", "wrds_monthlyindexret_query"),
        ),
        "sp500_monthly": (
            f"SELECT * FROM crsp.msp500 WHERE caldt >= '{start}'",
            "caldt",
            ("crsp", "msp500"),
        ),
        "treasuries_monthly": (
            f"SELECT * FROM crsp.mcti WHERE caldt >= '{start}'",
            "caldt",
            ("crsp", "mcti"),
        ),
        "size_deciles_monthly": (
            f"SELECT * FROM crsp.msix WHERE caldt >= '{start}'",
            "caldt",
            ("crsp", "msix"),
        ),
        "dfscx_monthly": (
            "SELECT * FROM crsp_q_mutualfunds.monthly_tna_ret_nav WHERE crsp_fundno = '008296'",
            "caldt",
            ("crsp_q_mutualfunds", "monthly_tna_ret_nav"),
        ),
        "ff_factors_daily": (
            f"SELECT * FROM ff.factors_daily WHERE date >= '{start}'",
            "date",
            ("ff", "factors_daily"),
        ),
        "ff_factors_monthly": (
            f"SELECT * FROM ff.factors_monthly WHERE date >= '{start}'",
            "date",
            ("ff", "factors_monthly"),
        ),
    }


def arrow_type(pg_type: str) -> pa.DataType:
    t = pg_type.upper()
    if "DATE" in t and "TIME" not in t:
        return pa.date32()
    if "TIMESTAMP" in t:
        return pa.timestamp("us")
    if any(k in t for k in ("DOUBLE", "FLOAT", "REAL", "NUMERIC", "DECIMAL")):
        return pa.float64()
    if any(k in t for k in ("INT", "SERIAL")):
        return pa.int64()
    if "BOOL" in t:
        return pa.bool_()
    return pa.string()


class Downloader:
    def __init__(self, timeout: str):
        print("Connecting to WRDS; approve the Duo push on your phone...", flush=True)
        self.db = wrds_connection(statement_timeout=timeout)
        self.raw = self.db.connection.connection
        self._types: dict[tuple[str, str], dict[str, pa.DataType]] = {}
        print("Connected.", flush=True)

    def types(self, library: str, table: str) -> dict[str, pa.DataType]:
        key = (library, table)
        if key not in self._types:
            desc = self.db.describe_table(library, table)
            self._types[key] = {r["name"]: arrow_type(str(r["type"])) for _, r in desc.iterrows()}
        return self._types[key]

    def copy_to_parquet(self, sql: str, out: Path, schema_src: tuple[str, str]) -> pa.Table:
        """Stream ``sql`` with server-side COPY into a typed Parquet file.

        The file appears at ``out`` only once it is complete: it is written to
        ``<out>.partial``, its row count is read back and checked, and then it is
        renamed into place. An interrupted run leaves no file at ``out`` (so a
        resumed run downloads it again) and no temporary CSV behind.
        """
        types = self.types(*schema_src)
        partial = out.with_name(out.name + ".partial")
        fd, tmp_name = tempfile.mkstemp(suffix=".csv", dir=out.parent)
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "w") as tmp, self.raw.cursor() as cur:
                cur.copy_expert(f"COPY ({sql}) TO STDOUT WITH CSV HEADER", tmp)
            with tmp_path.open() as fh:
                header = fh.readline().strip().split(",")
            table = pacsv.read_csv(
                tmp_path,
                convert_options=pacsv.ConvertOptions(
                    column_types={c: types.get(c, pa.string()) for c in header},
                    strings_can_be_null=True,
                ),
            )
            pq.write_table(table, partial, compression="zstd")
            written = pq.ParquetFile(partial).metadata.num_rows
            if written != table.num_rows:
                raise RuntimeError(f"{partial}: wrote {written} rows, expected {table.num_rows}")
            os.replace(partial, out)
        finally:
            tmp_path.unlink(missing_ok=True)
            partial.unlink(missing_ok=True)
        return table

    def close(self):
        self.db.close()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def record(manifest: dict, name: str, path: Path, table: pa.Table, date_col: str, sql: str):
    dates = table.column(date_col) if date_col in table.column_names else None
    manifest[name] = {
        "file": str(path.relative_to(ROOT)),
        "rows": table.num_rows,
        "columns": table.num_columns,
        "first_date": str(pc.min(dates)) if dates is not None else None,
        "last_date": str(pc.max(dates)) if dates is not None else None,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "sql": sql,
        "downloaded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }


def save_manifest(manifest: dict):
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    shutil.copyfile(MANIFEST, MANIFEST_COPY)


def download_public(manifest: dict, force: bool):
    sources = [(PUBLIC_DIR / "french" / f, FRENCH_URL + f) for f in FRENCH_FILES]
    gw = json.loads((ROOT / "data/metadata/goyal_welch_download.json").read_text())
    sources += [(PUBLIC_DIR / "goyal_welch" / e["name"], e["source"]) for e in gw]
    for path, url in sources:
        if path.exists() and not force:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        path.write_bytes(data)
        manifest[f"public/{path.parent.name}/{path.name}"] = {
            "file": str(path.relative_to(ROOT)),
            "url": url,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "downloaded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        }
        print(f"public  {path.relative_to(ROOT)}  {len(data):,} bytes", flush=True)


def main():
    cfg = yaml.safe_load((ROOT / "configs/config.yaml").read_text())
    start = cfg["sample"]["acquisition_start"]
    names = ["daily_stocks", *wrds_tables(start), "public"]

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--only", help=f"comma list from: {', '.join(names)}")
    ap.add_argument("--years", help="daily panel years, e.g. 1961-2026 (default: start..today)")
    ap.add_argument("--timeout", default="60min", help="server statement_timeout")
    ap.add_argument("--force", action="store_true", help="re-download existing outputs")
    args = ap.parse_args()

    only = set(args.only.split(",")) if args.only else set(names)
    unknown = only - set(names)
    if unknown:
        ap.error(f"unknown dataset(s): {', '.join(sorted(unknown))}")
    first, last = int(start[:4]), dt.date.today().year
    if args.years:
        a, _, b = args.years.partition("-")
        first, last = int(a), int(b or a)

    WRDS_API_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}

    if "public" in only:
        download_public(manifest, args.force)
        save_manifest(manifest)

    tables = {k: v for k, v in wrds_tables(start).items() if k in only}
    if not tables and "daily_stocks" not in only:
        return
    dl = Downloader(args.timeout)
    try:
        for name, (sql, date_col, src) in tables.items():
            out = WRDS_API_DIR / f"{name}.parquet"
            if out.exists() and not args.force:
                continue
            t0 = time.time()
            table = dl.copy_to_parquet(sql, out, src)
            record(manifest, name, out, table, date_col, sql)
            save_manifest(manifest)
            print(f"{name:22s} {table.num_rows:>12,} rows  {time.time() - t0:6.0f}s", flush=True)

        if "daily_stocks" in only:
            daily_dir = WRDS_API_DIR / "daily_stocks"
            daily_dir.mkdir(exist_ok=True)
            for year in range(first, last + 1):
                out = daily_dir / f"{year}.parquet"
                if out.exists() and not args.force:
                    continue
                sql = (
                    f"SELECT DISTINCT {', '.join(DAILY_COLUMNS)} "
                    "FROM crsp_q_stock.wrds_dsfv2_query "
                    f"WHERE dlycaldt BETWEEN '{year}-01-01' AND '{year}-12-31'"
                )
                t0 = time.time()
                table = dl.copy_to_parquet(sql, out, ("crsp_q_stock", "wrds_dsfv2_query"))
                if table.num_rows == 0:
                    out.unlink()
                    print(f"daily_stocks {year}: no rows (beyond latest vintage)", flush=True)
                    continue
                record(manifest, f"daily_stocks/{year}", out, table, "dlycaldt", sql)
                save_manifest(manifest)
                print(
                    f"daily_stocks {year}  {table.num_rows:>10,} rows  "
                    f"{out.stat().st_size / 1e6:7.1f} MB  {time.time() - t0:5.0f}s",
                    flush=True,
                )
    finally:
        dl.close()
    print("Done. Manifest:", MANIFEST.relative_to(ROOT))


if __name__ == "__main__":
    main()
