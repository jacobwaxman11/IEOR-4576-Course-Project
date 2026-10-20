"""Worker B runner: provenance, reconciliation and data-gap checks.

One WRDS connection per phase (COMMON_RULES Duo protocol):

    .venv/bin/python report/data_review/B_checks.py discover   # phase 1: schema
    .venv/bin/python report/data_review/B_checks.py run        # phase 2: B1-B5 checks
    .venv/bin/python report/data_review/B_checks.py rerun      # phase 3: fixes only

Outputs: report/data_review/B_results/*.csv (aggregates only).
Every SQL statement is documented in B_queries.sql with a query ID (B1a, ...).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

from project.data import wrds_connection, query_to_parquet
from project.paths import ROOT

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "B_results"

PHASE_TIMEOUT = "15min"
CANDIDATE_LIBRARIES = [
    "crsp",            # annual update CIZ + legacy SIZ (msf, msedelist, msi, ...)
    "crsp_q_stock",    # quarterly update CIZ
    "crsp_q_mutualfunds",
    "crsp_q_indexes",
    "ff",              # Ken French factors on WRDS
    "taqmsec",         # legacy TAQ millisecond
    "taqm_2020", "taqm_2021", "taqm_2022", "taqm_2023", "taqm_2024", "taqm_2025",
    "taqm_2026",
]


def start_phase(name: str):
    """Connect once; the statement_timeout guard is set on the same underlying
    connection inside wrds_connection()."""
    RESULTS.mkdir(parents=True, exist_ok=True)
    db = wrds_connection(statement_timeout=PHASE_TIMEOUT)
    print(f"[{name}] connected (statement_timeout={PHASE_TIMEOUT}).")
    return db


def save(db, name: str, sql: str) -> pd.DataFrame:
    t0 = time.time()
    df = db.raw_sql(sql)
    out = RESULTS / f"{name}.csv"
    df.to_csv(out, index=False)
    print(f"[{name}] {len(df)} rows in {time.time() - t0:.1f}s -> {out.name}")
    return df


def safe(fn, label: str):
    try:
        return fn()
    except Exception as err:  # noqa: BLE001 - entitlement errors are findings
        print(f"[{label}] FAILED: {type(err).__name__}: {err}")
        return pd.DataFrame([{"library_or_table": label, "error_type": type(err).__name__,
                              "error": str(err)[:500]}])


# ---------------------------------------------------------------- phase 1
def discover() -> None:
    """Phase 1: enumerate libraries/tables and columns; no row-level data."""
    db = start_phase("discover")

    frames = []
    for lib in CANDIDATE_LIBRARIES:
        try:
            obj = db.list_tables(library=lib)
            if isinstance(obj, pd.DataFrame):
                df = obj
            else:  # wrds returns a plain list of table names
                df = pd.DataFrame({"table_name": list(obj)})
            df.insert(0, "library", lib)
        except Exception as err:  # noqa: BLE001 - entitlement errors are findings
            print(f"[list_tables({lib})] FAILED: {type(err).__name__}: {err}")
            df = pd.DataFrame([{"library": lib, "table_name": None,
                                "error_type": type(err).__name__, "error": str(err)[:500]}])
        frames.append(df)
    tables = pd.concat(frames, ignore_index=True)
    tables.to_csv(RESULTS / "discovery_tables.csv", index=False)
    print(f"discovery_tables: {len(tables)} rows")

    key_tables = [
        ("crsp", "wrds_dsfv2_query"),      # CIZ daily stocks (source of export 11771134)
        ("crsp", "wrds_msfv2_query"),      # CIZ monthly stocks (11771141)
        ("crsp", "msf"),                   # legacy monthly SIZ
        ("crsp", "msedelist"),             # legacy monthly delisting
        ("crsp", "dsedelist"),             # legacy daily delisting
        ("crsp", "msi"),                   # monthly indexes (legacy)
        ("crsp", "dsp500"),                # daily S&P 500 (legacy)
        ("crsp", "msp500"),                # monthly S&P 500 total return (legacy)
        ("crsp", "mcti"),                  # monthly treasury bill/capital index
        ("crsp", "msix"),                  # monthly size-decile indices
        ("crsp", "erdport1"),              # monthly equal-weighted decile portfolio returns
        ("crsp_q_stock", "stkdelists"),
        ("crsp_q_stock", "stkdistributions"),
        ("crsp_q_stock", "stksecurityinfohdr"),
        ("crsp_q_stock", "wrds_dailyindexret_query"),
        ("crsp_q_stock", "wrds_monthlyindexret_query"),
        ("crsp_q_stock", "dlyret"),        # probe: does this exist as a table?
        ("crsp_q_stock", "stksecdata"),
        ("crsp_q_mutualfunds", "monthly_tna_ret_nav"),
        ("crsp_q_mutualfunds", "fund_names"),
        ("ff", "factors_daily"),
        ("ff", "factors_monthly"),
    ]
    rows = []
    for lib, tab in key_tables:
        try:
            df = db.describe_table(library=lib, table=tab)
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)
        except Exception as err:  # noqa: BLE001 - entitlement errors are findings
            print(f"[describe_table({lib}.{tab})] FAILED: {type(err).__name__}: {err}")
            df = pd.DataFrame([{"column_name": None, "error_type": type(err).__name__,
                                "error": str(err)[:500]}])
        df.insert(0, "table", tab)
        df.insert(0, "library", lib)
        rows.append(df)
    desc = pd.concat(rows, ignore_index=True)
    desc.to_csv(RESULTS / "discovery_columns.csv", index=False)
    print(f"discovery_columns: {len(desc)} rows")

    # ff library: search for momentum / short-term reversal factor tables
    ff_tables = tables[tables["library"] == "ff"] if len(tables) else pd.DataFrame()
    ff_tables.to_csv(RESULTS / "discovery_ff_tables.csv", index=False)

    db.close()
    print("phase 'discover' complete.")


# ---------------------------------------------------------------- phase 2

# (query_id, sql). Every statement is also documented in B_queries.sql.
B1_QUERIES = [
    ("B1a", """SELECT COUNT(*) AS rows, COUNT(DISTINCT permno) AS permnos,
       MIN(dlycaldt) AS first_date, MAX(dlycaldt) AS last_date
       FROM crsp.wrds_dsfv2_query
       WHERE dlycaldt BETWEEN '1961-01-01'::date AND '2026-03-31'::date"""),
    ("B1b", """SELECT COUNT(*) AS rows, COUNT(DISTINCT permno) AS permnos,
       MIN(mthcaldt) AS first_date, MAX(mthcaldt) AS last_date
       FROM crsp.wrds_msfv2_query
       WHERE mthcaldt BETWEEN '1961-01-01'::date AND '2026-06-30'::date"""),
    ("B1c", """SELECT COUNT(*) AS rows, COUNT(DISTINCT permno) AS permnos,
       MIN(delistingdt) AS first_date, MAX(delistingdt) AS last_date
       FROM crsp_q_stock.stkdelists
       WHERE delistingdt BETWEEN '1961-01-01'::date AND '2026-06-29'::date
         AND delactiontype = ANY (ARRAY['GDR','GEX','GLI','LOS','MER'])"""),
    ("B1d", """SELECT COUNT(*) AS rows, COUNT(DISTINCT permno) AS permnos,
       MIN(disexdt) AS first_date, MAX(disexdt) AS last_date
       FROM crsp_q_stock.stkdistributions
       WHERE disexdt BETWEEN '1961-01-01'::date AND '2026-06-30'::date
         AND distype = ANY (ARRAY['CD','CG','CP','FRS','IN','N/A','ROC','SD','SP','TSOO'])"""),
    ("B1e", """SELECT COUNT(*) AS rows, MIN(dlycaldt) AS first_date, MAX(dlycaldt) AS last_date
       FROM crsp_q_stock.wrds_dailyindexret_query
       WHERE dlycaldt BETWEEN '1961-01-01'::date AND '2026-06-30'::date"""),
    ("B1f", """SELECT COUNT(*) AS rows, MIN(mthcaldt) AS first_date, MAX(mthcaldt) AS last_date
       FROM crsp_q_stock.wrds_monthlyindexret_query
       WHERE mthcaldt BETWEEN '1961-01-01'::date AND '2026-06-30'::date"""),
    ("B1g", """SELECT COUNT(*) AS rows, MIN(caldt) AS first_date, MAX(caldt) AS last_date
       FROM crsp_q_mutualfunds.monthly_tna_ret_nav
       WHERE crsp_fundno = '008296'
         AND caldt BETWEEN '1981-06-01'::date AND '2026-06-30'::date"""),
]

B2_QUERIES = [
    ("B2a", "SELECT MAX(dlycaldt) AS last_date FROM crsp.wrds_dsfv2_query"),
    ("B2b", "SELECT MAX(dlycaldt) AS last_date FROM crsp_q_stock.wrds_dsfv2_query"),
    ("B2c", "SELECT MAX(mthcaldt) AS last_date FROM crsp.wrds_msfv2_query"),
    ("B2d", "SELECT MAX(mthcaldt) AS last_date FROM crsp_q_stock.wrds_msfv2_query"),
]

B4_QUERIES = [
    ("B4a", """SELECT COUNT(*) AS rows, MIN(date) AS first_date, MAX(date) AS last_date,
       COUNT(mktrf) AS n_mktrf, COUNT(smb) AS n_smb, COUNT(hml) AS n_hml,
       COUNT(rf) AS n_rf, COUNT(umd) AS n_umd FROM ff.factors_daily"""),
    ("B4b", """SELECT COUNT(*) AS rows, MIN(date) AS first_date, MAX(date) AS last_date,
       COUNT(mktrf) AS n_mktrf, COUNT(smb) AS n_smb, COUNT(hml) AS n_hml,
       COUNT(rf) AS n_rf, COUNT(umd) AS n_umd FROM ff.factors_monthly"""),
    ("B4c", """SELECT COUNT(umd) AS n_umd,
       MIN(date) FILTER (WHERE umd IS NOT NULL) AS first_umd,
       MAX(date) FILTER (WHERE umd IS NOT NULL) AS last_umd,
       MIN(date) FILTER (WHERE rf IS NOT NULL) AS first_rf,
       MAX(date) FILTER (WHERE rf IS NOT NULL) AS last_rf
       FROM ff.factors_monthly"""),
    ("B4d", """SELECT COUNT(umd) AS n_umd,
       MIN(date) FILTER (WHERE umd IS NOT NULL) AS first_umd,
       MAX(date) FILTER (WHERE umd IS NOT NULL) AS last_umd
       FROM ff.factors_daily"""),
]

B5_QUERIES = [
    ("B5b", """SELECT COUNT(*) AS months, MIN(caldt) AS first_date, MAX(caldt) AS last_date,
       COUNT(decret1) AS n_decret1, COUNT(decret10) AS n_decret10
       FROM crsp.msix
       WHERE caldt BETWEEN '1963-06-01'::date AND '1981-12-31'::date"""),
    ("B5c1", """SELECT COUNT(*) AS months, MIN(caldt) AS first_date, MAX(caldt) AS last_date,
       COUNT(vwretd) AS n_vwretd, COUNT(sprtrn) AS n_sprtrn, COUNT(spindx) AS n_spindx
       FROM crsp.msp500
       WHERE caldt BETWEEN '1963-06-01'::date AND '2002-12-31'::date"""),
    ("B5c2", """SELECT COUNT(*) AS months, MIN(caldt) AS first_date, MAX(caldt) AS last_date,
       COUNT(t30ret) AS n_t30ret, COUNT(t90ret) AS n_t90ret
       FROM crsp.mcti
       WHERE caldt BETWEEN '1963-06-01'::date AND '2002-12-31'::date"""),
    ("B5c3", """SELECT COUNT(*) AS months, MIN(date) AS first_date, MAX(date) AS last_date,
       COUNT(vwretd) AS n_vwretd, COUNT(sprtrn) AS n_sprtrn
       FROM crsp.msi
       WHERE date BETWEEN '1963-06-01'::date AND '2002-12-31'::date"""),
]

# B3 sample selection: deterministic, spread over the period.
B3A1_SQL = """SELECT permno, MAX(mthcap) AS max_mthcap, MIN(mthcaldt) AS first_month,
       COUNT(*) AS n_months
FROM crsp.wrds_msfv2_query
GROUP BY permno
HAVING MIN(mthcaldt) < '1975-01-01'::date
ORDER BY MAX(mthcap) DESC NULLS LAST
LIMIT 10"""

B3A2_SQL = """SELECT permno, dlstdt, dlstcd, dlret, dlretx FROM (
    SELECT permno, dlstdt, dlstcd, dlret, dlretx,
           row_number() OVER (ORDER BY dlstdt, permno) AS rn
    FROM crsp.msedelist
    WHERE dlstdt BETWEEN '1963-01-01'::date AND '2002-12-31'::date
      AND dlstcd BETWEEN 500 AND 599) t
WHERE mod(rn, 40) = 1
ORDER BY rn
LIMIT 10"""


def _arr(values):
    return "ANY(ARRAY[" + ",".join(str(int(v)) for v in values) + "]::int[])"


def run(gaps_only: bool = False) -> None:
    """Phase 2: all B1-B5 checks on one connection; aggregates to B_results,
    the small row-level B3 samples to data/raw/wrds_api/ (git-ignored).
    gaps_only=True skips the already-completed B1/B2/B4/B5 aggregates (fix-up run)."""
    db = start_phase("rerun" if gaps_only else "run")

    if not gaps_only:
        for qid, sql in B1_QUERIES + B2_QUERIES + B4_QUERIES + B5_QUERIES:
            save(db, qid, sql)

    # ---- B3: 20 PERMNOs (10 large long-lived + 10 performance delistings)
    try:
        large = save(db, "B3a1", B3A1_SQL)  # aggregate stats per permno - fine for B_results
        large_permnos = large["permno"].tolist()
        delist = query_to_parquet(db, B3A2_SQL, "B_b3a2_delisted_sample")  # event rows -> wrds_api
        delist_permnos = delist["permno"].tolist()
    except Exception as err:  # noqa: BLE001 - record and continue with the remaining checks
        print(f"B3 sample selection FAILED: {type(err).__name__}: {err}")
        large_permnos, delist_permnos = [], []
    all_permnos = large_permnos + delist_permnos
    print(f"B3 sample: large={large_permnos}")
    print(f"B3 sample: delisted={delist_permnos}")

    # B3b: monthly compounded returns per PERMNO-year, CIZ daily vs legacy msf.
    # The CIZ query table can repeat a date when distributions share it, so
    # deduplicate to one row per permno-day (MAX dlyret) before compounding.
    b3b1_sql = f"""WITH d AS (
        SELECT permno, dlycaldt, MAX(dlyret) AS dlyret
        FROM crsp.wrds_dsfv2_query
        WHERE permno = {_arr(all_permnos)}
          AND dlycaldt BETWEEN '1963-01-01'::date AND '2002-12-31'::date
        GROUP BY permno, dlycaldt)
    SELECT permno, EXTRACT(YEAR FROM dlycaldt)::int AS yr,
           COUNT(*) AS n_days,
           SUM(CASE WHEN dlyret IS NULL THEN 1 ELSE 0 END) AS missing_days,
           CASE WHEN SUM(CASE WHEN dlyret IS NULL OR dlyret <= -1 THEN 1 ELSE 0 END) = 0
                THEN EXP(SUM(CASE WHEN dlyret IS NULL OR dlyret <= -1 THEN NULL
                                  ELSE LN(1 + dlyret) END)) - 1 END AS ciz_yr_ret
    FROM d
    GROUP BY permno, EXTRACT(YEAR FROM dlycaldt)::int
    ORDER BY permno, yr"""
    b3b2_sql = f"""SELECT permno, EXTRACT(YEAR FROM date)::int AS yr,
           COUNT(*) AS n_months,
           SUM(CASE WHEN ret IS NULL THEN 1 ELSE 0 END) AS missing_months,
           CASE WHEN SUM(CASE WHEN ret IS NULL OR ret <= -1 THEN 1 ELSE 0 END) = 0
                THEN EXP(SUM(CASE WHEN ret IS NULL OR ret <= -1 THEN NULL
                                  ELSE LN(1 + ret) END)) - 1 END AS siz_yr_ret
    FROM crsp.msf
    WHERE permno = {_arr(all_permnos)}
      AND date BETWEEN '1963-01-31'::date AND '2002-12-31'::date
    GROUP BY permno, EXTRACT(YEAR FROM date)::int
    ORDER BY permno, yr"""
    b3b1 = b3b2 = None
    try:
        b3b1 = query_to_parquet(db, b3b1_sql, "B_b3b1_ciz_yearly")
        b3b2 = query_to_parquet(db, b3b2_sql, "B_b3b2_siz_yearly")
    except Exception as err:  # noqa: BLE001
        print(f"B3b FAILED: {type(err).__name__}: {err}")

    # B3c: delisting handling - legacy dlret vs CIZ delret, and the final-day dlyret.
    b3c1_sql = f"""SELECT permno, dlstdt, dlstcd, dlret, dlretx
       FROM crsp.msedelist
       WHERE permno = {_arr(delist_permnos)}
         AND dlstdt BETWEEN '1963-01-01'::date AND '2002-12-31'::date
       ORDER BY permno, dlstdt"""
    b3c1_sql_d = b3c1_sql.replace("crsp.msedelist", "crsp.dsedelist")
    b3c2_sql = f"""SELECT permno, delistingdt, delactiontype, delstatustype, delreasontype,
       delret, delretmisstype
       FROM crsp_q_stock.stkdelists
       WHERE permno = {_arr(delist_permnos)}
         AND delistingdt BETWEEN '1963-01-01'::date AND '2002-12-31'::date
       ORDER BY permno, delistingdt"""
    b3c3_sql = f"""SELECT s.permno, s.delistingdt, s.delret, d.dlycaldt, d.dlyret, d.dlydelflg
       FROM crsp_q_stock.stkdelists s
       JOIN crsp.wrds_dsfv2_query d
         ON d.permno = s.permno
        AND d.dlycaldt BETWEEN s.delistingdt - 10 AND s.delistingdt + 5
       WHERE s.permno = {_arr(delist_permnos)}
         AND s.delistingdt BETWEEN '1963-01-01'::date AND '2002-12-31'::date
       ORDER BY s.permno, d.dlycaldt"""
    try:
        query_to_parquet(db, b3c1_sql, "B_b3c1_msedelist")
        query_to_parquet(db, b3c1_sql_d, "B_b3c1_dsedelist")
        query_to_parquet(db, b3c2_sql, "B_b3c2_stkdelists")
        query_to_parquet(db, b3c3_sql, "B_b3c3_final_day")
    except Exception as err:  # noqa: BLE001
        print(f"B3c FAILED: {type(err).__name__}: {err}")

    # ---- B5d: probe likely SBBI/Ibbotson libraries (errors are findings)
    rows = []
    for lib in ["sbbi", "ibbotson"]:
        try:
            t = db.list_tables(library=lib)
            rows.append({"library": lib, "error_type": None,
                         "error": f"accessible: {len(list(t))} tables"})
        except Exception as err:  # noqa: BLE001
            rows.append({"library": lib, "error_type": type(err).__name__,
                         "error": str(err)[:300]})
    pd.DataFrame(rows).to_csv(RESULTS / "B5d_entitlements.csv", index=False)
    print("B5d entitlement probes saved.")

    # ---- B5a: TAQ availability 2020-2025 (metadata + LIMIT 1 only)
    from contextlib import redirect_stdout
    from io import StringIO
    taq_rows = []
    for year in range(2020, 2026):
        lib = f"taqm_{year}"
        for tab in [f"complete_nbbo_{year}", f"ctm_{year}", f"cqm_{year}", f"mastm_{year}"]:
            buf = StringIO()
            exists = False
            try:
                with redirect_stdout(buf):
                    df = db.describe_table(library=lib, table=tab)
                exists = True
                ncols = len(df)
            except Exception as err:  # noqa: BLE001
                ncols, errmsg = 0, f"{type(err).__name__}: {str(err)[:200]}"
            if exists:
                try:
                    db.raw_sql(f"SELECT 1 AS ok FROM {lib}.{tab} LIMIT 1")
                    limit1 = "ok"
                except Exception as err:  # noqa: BLE001
                    limit1 = f"{type(err).__name__}: {str(err)[:120]}"
            else:
                limit1 = "n/a"
            taq_rows.append({"library": lib, "table": tab, "exists": exists,
                             "n_columns": ncols, "limit1": limit1,
                             "describe_stdout": buf.getvalue()[:200]})
            print(f"taq {lib}.{tab}: exists={exists} limit1={limit1}")
    pd.DataFrame(taq_rows).to_csv(RESULTS / "B5a_taq_availability.csv", index=False)

    db.close()
    print("phase 'run' complete.")


def rerun() -> None:
    """Phase 3 fix-up: only the statements phase 2 did not reach (B3 + B5a/B5d)."""
    run(gaps_only=True)


# ---------------------------------------------------------------- phase 3
# ---------------------------------------------------------------- reconciliation (offline)


def reconcile() -> None:
    """Offline: compare B_results CSVs against data/metadata manifests."""
    import json

    manifest = {m["file"]: m for m in json.load(open(ROOT / "data/metadata/crsp_manifest.json"))}

    def get(qid):
        p = RESULTS / f"{qid}.csv"
        return pd.read_csv(p).iloc[0].to_dict() if p.exists() else None

    rows = []
    def add(export, qid, manifest_rows, manifest_permnos, manifest_first, manifest_last,
            manifest_file):
        s = get(qid)
        if s is None:
            rows.append({"export": export, "query_id": qid, "status": "UNVERIFIED"})
            return
        mrows = manifest[manifest_file].get("rows")
        mperm = manifest[manifest_file].get("unique_permnos")
        mfirst = manifest[manifest_file].get("first_date")
        mlast = manifest[manifest_file].get("last_date")
        diffs = []
        if mrows is not None and int(s["rows"]) != int(mrows):
            diffs.append(f"rows {int(s['rows']):,} vs {int(mrows):,}")
        if mperm is not None and int(s["permnos"]) != int(mperm):
            diffs.append(f"permnos {int(s['permnos']):,} vs {int(mperm):,}")
        for col, mval in (("first_date", mfirst), ("last_date", mlast)):
            if mval and str(s[col])[:10] != mval:
                diffs.append(f"{col} {str(s[col])[:10]} vs {mval}")
        rows.append({"export": export, "query_id": qid,
                     "manifest": f"rows={mrows}, permnos={mperm}, {mfirst}..{mlast}",
                     "server": f"rows={int(s['rows']):,}, permnos={s.get('permnos')}, "
                               f"{str(s['first_date'])[:10]}..{str(s['last_date'])[:10]}",
                     "difference": "; ".join(diffs) if diffs else "none",
                     "status": "PASS" if not diffs else "WARN"})

    add("daily stocks", "B1a", 102_464_776, 40_427, "1961-01-03", "2026-03-31",
        "data/raw/crsp/daily_stocks_1961_2026q1.csv.gz")
    add("monthly stocks", "B1b", 5_003_530, 41_016, "1961-01-31", "2026-06-30",
        "data/raw/crsp/monthly_stocks_1961_2026q2.csv.gz")
    add("delisting", "B1c", 29_727, None, "1961-01-20", "2026-06-29",
        "data/raw/crsp/delisting_1961_2026q2.csv.gz")
    add("distributions", "B1d", 1_023_403, None, "1961-01-03", "2026-06-30",
        "data/raw/crsp/distributions_1961_2026q2.csv.gz")
    add("daily indexes", "B1e", 16_481, None, "1961-01-03", "2026-06-30",
        "data/raw/crsp/daily_indexes_1961_2026q2.csv.gz")
    add("monthly indexes", "B1f", 786, None, "1961-01-31", "2026-06-30",
        "data/raw/crsp/monthly_indexes_1961_2026q2.csv.gz")
    add("dfscx monthly", "B1g", 535, None, "1981-12-31", "2026-06-30",
        "data/raw/crsp/dfscx_monthly_1981_2026q2.csv")

    rec = pd.DataFrame(rows)
    rec.to_csv(RESULTS / "reconciliation.csv", index=False)
    print(rec.to_string(index=False))

    # B3 comparison: per-PERMNO-year absolute differences (per-PERMNO-year tables
    # live in data/raw/wrds_api/; only summaries and difference counts go here)
    try:
        from project.paths import WRDS_API_DIR
        b3b1 = pd.read_parquet(WRDS_API_DIR / "B_b3b1_ciz_yearly.parquet")
        b3b2 = pd.read_parquet(WRDS_API_DIR / "B_b3b2_siz_yearly.parquet")
        m = b3b1.merge(b3b2, on=["permno", "yr"], how="inner")
        m = m.dropna(subset=["ciz_yr_ret", "siz_yr_ret"])
        m["abs_diff"] = (m["ciz_yr_ret"] - m["siz_yr_ret"]).abs()
        m["abs_diff_bp"] = m["abs_diff"] * 1e4
        summary = pd.DataFrame([{
            "n_permno_years": len(m),
            "mean_abs_diff": m["abs_diff"].mean(),
            "mean_abs_diff_bp": m["abs_diff_bp"].mean(),
            "median_abs_diff_bp": m["abs_diff_bp"].median(),
            "n_over_1bp": int((m["abs_diff_bp"] > 1).sum()),
            "n_over_10bp": int((m["abs_diff_bp"] > 10).sum()),
            "max_abs_diff_bp": m["abs_diff_bp"].max(),
            "n_missing_ciz": int(m["ciz_yr_ret"].isna().sum()),
        }])
        summary.to_csv(RESULTS / "B3_summary.csv", index=False)
        worst = m.sort_values("abs_diff_bp", ascending=False).head(40)
        worst[["permno", "yr", "abs_diff_bp", "n_days", "n_months", "missing_days"]].to_csv(
            RESULTS / "B3_worst_cases.csv", index=False)
        print(summary.to_string(index=False))
    except Exception as err:  # noqa: BLE001
        print(f"B3 comparison failed: {err}")


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else ""
    if phase == "discover":
        discover()
    elif phase == "run":
        run()
    elif phase == "rerun":
        rerun()
    elif phase == "rerun":
        rerun()
    elif phase == "reconcile":
        reconcile()
    else:
        raise SystemExit(__doc__)
