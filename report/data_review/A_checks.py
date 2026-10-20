"""Worker A data review: single runner for the WRDS-connecting phases.

Usage: .venv/bin/python report/data_review/A_checks.py phase1|phase2

Phase 1 discovers the schema and code domains (queries A1-A5 in A_queries.sql).
Phase 2 runs the A-3 checks (queries A6-A14). COMMON_FILTER / EXCH_FILTER /
NOTRADE_SQL are constants fixed after phase 1; they must exist in the phase-1
domain CSVs or phase 2 aborts. All outputs are aggregates written to
report/data_review/A_results/. Each query is wrapped in try/except so one
failure is recorded and the rest still run on the same connection. Loops cache
per-chunk partials, so an aborted run can be retried cheaply.
"""

from __future__ import annotations

import sys
import traceback

import pandas as pd

from project.data import wrds_connection
from project.paths import ROOT

RESULTS = ROOT / "report" / "data_review" / "A_results"
DAILY = "crsp_q_stock.wrds_dsfv2_query"
DELISTS = "crsp_q_stock.stkdelists"
SECHDR = "crsp_q_stock.stksecurityinfohdr"
DECADES = [(f"{y}-01-01", f"{y + 10}-01-01") for y in range(1961, 2031, 10)]

FORMATION_DATES = [
    "1963-07", "1970-01", "1980-01", "1990-01",
    "2000-01", "2002-07", "2010-01", "2020-01",
]

# Fixed after phase 1 (A3-A5). Phase 2 validates these against the domains.
# A3: common share = EQTY/COM/NS (legacy SHRCD 10/11 equivalent, pre-ADR 'AD').
COMMON_FILTER = "securitytype = 'EQTY' AND securitysubtype = 'COM' AND sharetype = 'NS'"
# A4: primaryexch N=NYSE, A=NYSE American (AMEX), Q=NASDAQ; R/B are minor venues.
EXCH_FILTER = "primaryexch IN ('N', 'A', 'Q')"
# A5: dlyprcflg 'TR' = actual trade; every other code (BA midpoint, NT no trade,
# HA halted, SU suspended, MP missing, DA/DP/DM) is a day without a trade.
NOTRADE_SQL = "dlyprcflg IS DISTINCT FROM 'TR'"

db = None  # set in __main__


def save(df: pd.DataFrame, name: str) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{name}.csv"
    df.to_csv(out, index=False)
    print(f"[saved] {out.relative_to(ROOT)} ({len(df)} rows)")


def run(query: str, name: str) -> None:
    """Run one labelled query, save its aggregate; record but survive errors."""
    out = RESULTS / f"{name}.csv"
    if out.exists():
        print(f"[skip] {name} (csv exists)")
        return
    try:
        save(db.raw_sql(query), name)
    except Exception:  # noqa: BLE001
        print(f"[FAILED] {name}")
        traceback.print_exc()
        (RESULTS / f"{name}.error.txt").write_text(traceback.format_exc())


def run_chunks(chunks, prefix: str, name: str) -> None:
    """Run a labelled chunk generator (key, sql) with per-chunk partial caching."""
    out = RESULTS / f"{name}.csv"
    if out.exists():
        print(f"[skip] {name} (csv exists)")
        return
    frames = []
    for key, query in chunks:
        part = RESULTS / f"{prefix}_{key}.csv"
        if part.exists():
            frames.append(pd.read_csv(part))
            print(f"[skip] {prefix} {key} (partial exists)")
            continue
        try:
            df = db.raw_sql(query)
            df.to_csv(part, index=False)
            frames.append(df)
            print(f"[done] {prefix} {key} ({len(df)} rows)")
        except Exception:  # noqa: BLE001
            print(f"[FAILED] {prefix} {key}")
            traceback.print_exc()
            (RESULTS / f"{prefix}_{key}.error.txt").write_text(traceback.format_exc())
    if frames:
        save(pd.concat(frames, ignore_index=True), name)


def phase1() -> None:
    libs = {}
    for lib in ("crsp", "crsp_q_stock"):
        try:
            tables = db.list_tables(lib)
            libs[lib] = tables
            print(f"list_tables({lib}): {len(tables)} tables")
        except Exception as err:  # noqa: BLE001
            print(f"list_tables({lib}) failed: {err}")
    save(pd.DataFrame([(lib, t) for lib, ts in libs.items() for t in ts],
                      columns=["library", "table"]), "A1_tables")

    for label, table in [("A2a", DAILY), ("A2b", DELISTS), ("A2c", SECHDR)]:
        lib, tbl = table.split(".")
        try:
            save(db.describe_table(library=lib, table=tbl), label + "_describe")
        except Exception as err:  # noqa: BLE001
            print(f"describe {table} failed: {err}")

    run(f"""
        SELECT securitytype, securitysubtype, sharetype, usincflg, issuertype,
               count(*) AS n
        FROM {SECHDR}
        GROUP BY 1, 2, 3, 4, 5
        ORDER BY n DESC
    """, "A3_classification_domains")

    run(f"""
        SELECT primaryexch, conditionaltype, tradingstatusflg, count(*) AS n
        FROM {SECHDR}
        GROUP BY 1, 2, 3
        ORDER BY n DESC
    """, "A4_exchange_domains")

    run(f"""
        SELECT dlyprcflg, dlyretmissflg, count(*) AS n
        FROM {DAILY}
        GROUP BY 1, 2
        ORDER BY n DESC
    """, "A5_daily_flag_domains")


def _check_constants() -> None:
    for label in ("A3_classification_domains", "A4_exchange_domains"):
        df = pd.read_csv(RESULTS / f"{label}.csv")
        print(f"[domain] {label}:\n{df.to_string()}")
    assert "TRUE" not in (COMMON_FILTER, EXCH_FILTER), (
        "COMMON_FILTER/EXCH_FILTER not fixed after phase 1"
    )


def a7_chunks():
    for d0, d1 in DECADES:
        yield d0[:4], f"""
            WITH g AS (
                SELECT extract(year from dlycaldt)::int AS year, permno, dlycaldt,
                       count(*) AS cnt
                FROM {DAILY}
                WHERE dlycaldt >= '{d0}' AND dlycaldt < '{d1}'
                GROUP BY 1, 2, 3
            )
            SELECT year,
                   sum(cnt) AS total_rows,
                   sum(CASE WHEN cnt > 1 THEN cnt ELSE 0 END) AS rows_in_duplicated_keys,
                   sum(CASE WHEN cnt > 1 THEN 1 ELSE 0 END) AS duplicated_keys
            FROM g
            GROUP BY 1
            ORDER BY 1
        """


def a9_chunks():
    for fmt in FORMATION_DATES:
        year, month = (int(x) for x in fmt.split("-"))
        w1 = pd.Timestamp(year=year, month=month, day=1) - pd.Timedelta(days=1)
        w0 = (w1 - pd.DateOffset(months=12) + pd.Timedelta(days=1)).date()
        w1 = w1.date()
        yield fmt, f"""
            WITH td AS (
                SELECT count(DISTINCT dlycaldt)::int AS n_days
                FROM {DAILY}
                WHERE dlycaldt BETWEEN '{w0}' AND '{w1}'
            ),
            elig AS (
                SELECT permno,
                       count(*) AS n_rows,
                       count(*) FILTER (WHERE dlyprc IS NOT NULL AND dlyprc > 0) AS n_prc,
                       count(*) FILTER (WHERE dlyret IS NOT NULL) AS n_ret,
                       count(*) FILTER (WHERE {NOTRADE_SQL}) AS n_notrade,
                       count(*) FILTER (WHERE dlyprcflg = 'BA') AS n_ba_days,
                       count(*) FILTER (WHERE dlyprcflg = 'NT') AS n_nt_days
                FROM {DAILY}
                WHERE dlycaldt BETWEEN '{w0}' AND '{w1}'
                  AND {COMMON_FILTER} AND {EXCH_FILTER}
                GROUP BY permno
            )
            SELECT '{fmt}' AS formation_date,
                   (SELECT n_days FROM td) AS trading_days,
                   count(*) AS n_pass_filter,
                   count(*) FILTER (WHERE n_rows >= (SELECT n_days FROM td)) AS n_row_every_day,
                   count(*) FILTER (WHERE n_prc  >= (SELECT n_days FROM td)) AS n_posprc_every_day,
                   count(*) FILTER (WHERE n_ret  >= (SELECT n_days FROM td)) AS n_ret_every_day,
                   count(*) FILTER (WHERE n_notrade = 0 AND n_prc >= (SELECT n_days FROM td))
                       AS n_strict_liquid
            FROM elig
        """


def a10_chunks():
    for d0, d1 in DECADES:
        yield d0[:4], f"""
            SELECT extract(year from dlycaldt)::int AS year,
                   count(*) AS n_common_rows,
                   count(*) FILTER (WHERE dlybid IS NOT NULL AND dlyask IS NOT NULL)
                       AS n_both_quotes,
                   count(*) FILTER (WHERE dlybid IS NOT NULL AND dlyask IS NOT NULL
                                      AND dlyask > dlybid) AS n_ask_gt_bid,
                   percentile_cont(0.5) WITHIN GROUP (ORDER BY
                       (dlyask - dlybid) / ((dlyask + dlybid) / 2.0))
                     FILTER (WHERE dlyask > dlybid AND dlyask + dlybid > 0)
                       AS median_rel_spread
            FROM {DAILY}
            WHERE dlycaldt >= '{d0}' AND dlycaldt < '{d1}'
              AND {COMMON_FILTER}
            GROUP BY 1
            ORDER BY 1
        """


def phase2() -> None:
    _check_constants()

    # A6: missing returns by year x dlyretmissflg.
    run(f"""
        SELECT extract(year from dlycaldt)::int AS year,
               dlyretmissflg,
               count(*) AS n_rows,
               count(*) FILTER (WHERE dlyret IS NULL) AS n_ret_null
        FROM {DAILY}
        GROUP BY 1, 2
        ORDER BY 1, 2
    """, "A6_missing_returns_by_year")

    # A7: duplicate (permno, dlycaldt) keys by year, per decade.
    run_chunks(a7_chunks(), "A7_decade", "A7_duplicate_keys_by_year")

    # A8: delisting action types and null delret counts.
    run(f"""
        SELECT delactiontype,
               count(*) AS n,
               count(*) FILTER (WHERE delret IS NULL) AS n_delret_null
        FROM {DELISTS}
        GROUP BY 1
        ORDER BY n DESC
    """, "A8_delisting_action_types")

    # A9: eligible universe at the 8 formation dates.
    run_chunks(a9_chunks(), "A9_fmt", "A9_eligible_universe")

    # A10: bid/ask coverage by year, per decade.
    run_chunks(a10_chunks(), "A10_decade", "A10_bidask_coverage")

    # A11: SIC mix in the 1989 formation window.
    run(f"""
        WITH elig AS (
            SELECT DISTINCT permno
            FROM {DAILY}
            WHERE dlycaldt BETWEEN '1989-01-01' AND '1989-12-31'
              AND {COMMON_FILTER} AND {EXCH_FILTER}
        )
        SELECT (d.siccd / 100)::int AS sic2,
               count(DISTINCT d.permno) AS n_stocks
        FROM {DAILY} d
        JOIN elig ON elig.permno = d.permno
        WHERE d.dlycaldt BETWEEN '1989-01-01' AND '1989-12-31'
          AND d.siccd IS NOT NULL
        GROUP BY 1
        ORDER BY 2 DESC
    """, "A11_sic_mix_1989")

    # A12a: volume null/zero shares by year.
    run(f"""
        SELECT extract(year from dlycaldt)::int AS year,
               count(*) AS n_common_rows,
               count(*) FILTER (WHERE dlyvol IS NULL) AS n_vol_null,
               count(*) FILTER (WHERE dlyvol = 0) AS n_vol_zero
        FROM {DAILY}
        WHERE {COMMON_FILTER}
        GROUP BY 1
        ORDER BY 1
    """, "A12a_volume_missing_by_year")

    # A12b: median volume by exchange, day-15 cross-sections.
    run(f"""
        SELECT extract(year from dlycaldt)::int AS year,
               primaryexch,
               percentile_cont(0.5) WITHIN GROUP (ORDER BY dlyvol) AS median_vol
        FROM {DAILY}
        WHERE {COMMON_FILTER}
          AND extract(day from dlycaldt) = 15
          AND dlyvol > 0
        GROUP BY 1, 2
        ORDER BY 1, 2
    """, "A12b_median_volume_by_exchange")

    # A14: primaryexch domain by year on the daily table.
    run(f"""
        SELECT extract(year from dlycaldt)::int AS year,
               primaryexch,
               count(*) AS n
        FROM {DAILY}
        GROUP BY 1, 2
        ORDER BY 1, 2
    """, "A14_exchange_by_year")

    # A15: does DlyRet on the dlydelflg='Y' row already equal DelRet? (Worker B's
    # B3c3: dlyret = delret on the dlydelflg='Y' row, which is not dated
    # delistingdt.) Population-wide by delactiontype, plus the date-diff
    # distribution between the flagged row's dlycaldt and stkdelists.delistingdt.
    run(f"""
        WITH del AS (
            SELECT permno, delistingdt, delret, delactiontype
            FROM {DELISTS}
        ),
        j AS (
            SELECT del.delactiontype, del.delistingdt, del.delret,
                   d.dlycaldt, d.dlyret
            FROM del
            LEFT JOIN {DAILY} d
                   ON d.permno = del.permno AND d.dlydelflg = 'Y'
        )
        SELECT delactiontype,
               count(*) AS n_delistings,
               count(*) FILTER (WHERE dlycaldt IS NULL) AS n_no_delflg_row,
               count(*) FILTER (WHERE dlyret IS NOT NULL) AS n_dlyret_nn,
               count(*) FILTER (WHERE delret IS NOT NULL) AS n_delret_nn,
               count(*) FILTER (WHERE dlyret IS NOT NULL AND delret IS NOT NULL
                                  AND abs(dlyret - delret) < 1e-6) AS n_dlyret_equals_delret,
               count(*) FILTER (WHERE dlycaldt = delistingdt) AS n_delflg_row_on_delisting_dt,
               count(*) FILTER (WHERE dlycaldt < delistingdt) AS n_delflg_row_before,
               count(*) FILTER (WHERE dlycaldt > delistingdt) AS n_delflg_row_after,
               percentile_cont(0.5) WITHIN GROUP (ORDER BY dlycaldt - delistingdt)
                   AS median_date_diff_days
        FROM j
        GROUP BY 1
        ORDER BY 2 DESC
    """, "A15_delflg_delret")

    # A15b: population-wide count of dlydelflg='Y' rows in the daily table.
    run(f"""
        SELECT dlydelflg, count(*) AS n
        FROM {DAILY}
        GROUP BY 1
        ORDER BY n DESC
    """, "A15b_dlydelflg_domain")

    # A13: delisting-return overlap (double-count risk check).
    run(f"""
        SELECT s.delactiontype,
               count(*) AS n_delistings,
               count(*) FILTER (WHERE d.permno IS NOT NULL) AS n_daily_row_on_delisting_dt,
               count(*) FILTER (WHERE d.permno IS NOT NULL AND s.delret IS NOT NULL
                                  AND d.dlyret IS NOT NULL) AS n_both_rets,
               count(*) FILTER (WHERE d.permno IS NOT NULL AND s.delret IS NOT NULL
                                  AND d.dlyret IS NOT NULL AND d.dlyret = s.delret)
                   AS n_dlyret_equals_delret,
               count(*) FILTER (WHERE d.permno IS NOT NULL AND s.delret IS NOT NULL
                                  AND (d.dlyret IS NULL OR d.dlyret = 0))
                   AS n_dlyret_null_or_zero,
               count(*) FILTER (WHERE s.delistingdt > '2026-03-31') AS n_after_daily_cutoff
        FROM {DELISTS} s
        LEFT JOIN {DAILY} d
               ON d.permno = s.permno AND d.dlycaldt = s.delistingdt
        GROUP BY 1
        ORDER BY 2 DESC
    """, "A13_delret_overlap")


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else ""
    assert phase in ("phase1", "phase2"), "usage: A_checks.py phase1|phase2"
    db = wrds_connection(statement_timeout="15min")
    print("WRDS connected.")
    try:
        phase1() if phase == "phase1" else phase2()
    finally:
        try:
            db.close()
        except Exception as err:  # noqa: BLE001
            print(f"close failed: {err}")
    print(f"phase {phase} complete.")
