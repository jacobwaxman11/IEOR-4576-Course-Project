-- Worker A: every SQL statement run against WRDS, in run order.
-- Labels are A1, A2, ...; each is executed by report/data_review/A_checks.py.
-- Phase 1 = schema discovery (run 1), Phase 2 = checks (run 2).
-- Rules: server-side aggregation only; statement_timeout set to 15min per connection.

-- ============================================================================
-- PHASE 1: SCHEMA DISCOVERY
-- ============================================================================

-- A1 (driver call, not SQL): db.list_tables('crsp') and db.list_tables('crsp_q_stock')
--     Purpose: locate the CIZ daily table used by the export
--     (crsp_q_stock.wrds_dsfv2_query) and the delisting/security-info tables.

-- A2 (driver call, not SQL): db.describe_table(...) on
--     crsp_q_stock.wrds_dsfv2_query, crsp_q_stock.stkdelists,
--     crsp_q_stock.stksecurityinfohdr. Column names/types for the checks below.

-- A3: classification-code domains (legacy SHRCD 10/11 translation).
--     stksecurityinfohdr is one row per PERMNO (~40k), cheap.
SELECT securitytype, securitysubtype, sharetype, usincflg, issuertype,
       count(*) AS n
FROM crsp_q_stock.stksecurityinfohdr
GROUP BY 1, 2, 3, 4, 5
ORDER BY n DESC;

-- A4: exchange / conditional / trading-status domains.
SELECT primaryexch, conditionaltype, tradingstatusflg, count(*) AS n
FROM crsp_q_stock.stksecurityinfohdr
GROUP BY 1, 2, 3
ORDER BY n DESC;

-- A5: daily price/return-missing flag domains (joint, one scan).
SELECT dlyprcflg, dlyretmissflg, count(*) AS n
FROM crsp_q_stock.wrds_dsfv2_query
GROUP BY 1, 2
ORDER BY n DESC;

-- A13: delisting-return overlap (added by A; informs the splicing rule in
--      A_FINDINGS.md section 2, row 1). For each delisting action type: how many
--      delistings have a matching daily row on the delisting date, and among
--      those, whether DlyRet and DelRet coexist (double-count risk) or DlyRet is
--      null/zero (DelRet fills a hole).
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
FROM crsp_q_stock.stkdelists s
LEFT JOIN crsp_q_stock.wrds_dsfv2_query d
       ON d.permno = s.permno AND d.dlycaldt = s.delistingdt
GROUP BY 1
ORDER BY 2 DESC;

-- A14: primaryexch domain on the daily table by year (verifies the header-table
--      codes of A4 hold historically, and dates the R/B venues).
SELECT extract(year from dlycaldt)::int AS year,
       primaryexch,
       count(*) AS n
FROM crsp_q_stock.wrds_dsfv2_query
GROUP BY 1, 2
ORDER BY 1, 2;

-- A15: does CIZ DlyRet on the dlydelflg='Y' row already equal DelRet? (Worker B
--      B3c3: dlyret = delret on the dlydelflg='Y' row, dated differently than
--      stkdelists.delistingdt.) Population-wide by delactiontype, plus the
--      date-diff distribution between the flagged row and delistingdt.
WITH del AS (
    SELECT permno, delistingdt, delret, delactiontype
    FROM crsp_q_stock.stkdelists
),
j AS (
    SELECT del.delactiontype, del.delistingdt, del.delret,
           d.dlycaldt, d.dlyret
    FROM del
    LEFT JOIN crsp_q_stock.wrds_dsfv2_query d
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
ORDER BY 2 DESC;

-- A15b: population-wide dlydelflg domain on the daily table.
SELECT dlydelflg, count(*) AS n
FROM crsp_q_stock.wrds_dsfv2_query
GROUP BY 1
ORDER BY n DESC;

-- ============================================================================
-- PHASE 2: CHECKS (A-3 items 1-7)
-- Constants COMMON_FILTER / EXCH_FILTER / NOTRADE_SQL are fixed after A3-A5.
-- ============================================================================

-- A6: missing daily returns by year, by dlyretmissflg (A-3.1).
SELECT extract(year from dlycaldt)::int AS year,
       dlyretmissflg,
       count(*) AS n_rows,
       count(*) FILTER (WHERE dlyret IS NULL) AS n_ret_null
FROM crsp_q_stock.wrds_dsfv2_query
GROUP BY 1, 2
ORDER BY 1, 2;

-- A7: duplicate (permno, dlycaldt) keys by year (A-3.2); run once per decade
--     window [d0, d1) to stay inside the 15-minute statement guard.
WITH g AS (
    SELECT extract(year from dlycaldt)::int AS year, permno, dlycaldt,
           count(*) AS cnt
    FROM crsp_q_stock.wrds_dsfv2_query
    WHERE dlycaldt >= '{d0}' AND dlycaldt < '{d1}'
    GROUP BY 1, 2, 3
)
SELECT year,
       sum(cnt) AS total_rows,
       sum(CASE WHEN cnt > 1 THEN cnt ELSE 0 END) AS rows_in_duplicated_keys,
       sum(CASE WHEN cnt > 1 THEN 1 ELSE 0 END) AS duplicated_keys
FROM g
GROUP BY 1
ORDER BY 1;

-- A8: all delisting action types, counts and null-delret counts (A-3.3).
SELECT delactiontype,
       count(*) AS n,
       count(*) FILTER (WHERE delret IS NULL) AS n_delret_null
FROM crsp_q_stock.stkdelists
GROUP BY 1
ORDER BY n DESC;

-- A9: eligible universe at formation dates (A-3.4); one statement per date.
--     Formation date F uses the 12-month window [F-12m, F).
WITH td AS (
    SELECT count(DISTINCT dlycaldt)::int AS n_days
    FROM crsp_q_stock.wrds_dsfv2_query
    WHERE dlycaldt BETWEEN '{w0}' AND '{w1}'
),
elig AS (
    SELECT permno,
           count(*) AS n_rows,
           count(*) FILTER (WHERE dlyprc IS NOT NULL AND dlyprc > 0) AS n_prc,
           count(*) FILTER (WHERE dlyret IS NOT NULL) AS n_ret,
           count(*) FILTER (WHERE {NOTRADE_SQL}) AS n_notrade
    FROM crsp_q_stock.wrds_dsfv2_query
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
FROM elig;

-- A10: bid/ask coverage and median relative spread among common-stock rows
--      (A-3.5); run once per decade window [d0, d1).
SELECT extract(year from dlycaldt)::int AS year,
       count(*) AS n_common_rows,
       count(*) FILTER (WHERE dlybid IS NOT NULL AND dlyask IS NOT NULL) AS n_both_quotes,
       count(*) FILTER (WHERE dlybid IS NOT NULL AND dlyask IS NOT NULL
                          AND dlyask > dlybid) AS n_ask_gt_bid,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY
           (dlyask - dlybid) / ((dlyask + dlybid) / 2.0))
         FILTER (WHERE dlyask > dlybid AND dlyask + dlybid > 0) AS median_rel_spread
FROM crsp_q_stock.wrds_dsfv2_query
WHERE dlycaldt >= '{d0}' AND dlycaldt < '{d1}'
  AND {COMMON_FILTER}
GROUP BY 1
ORDER BY 1;

-- A11: 2-digit SIC mix among stocks passing the filter in the 1990-01
--      formation window 1989-01-01..1989-12-31 (A-3.6). Utilities = SIC 49.
WITH elig AS (
    SELECT DISTINCT permno
    FROM crsp_q_stock.wrds_dsfv2_query
    WHERE dlycaldt BETWEEN '1989-01-01' AND '1989-12-31'
      AND {COMMON_FILTER} AND {EXCH_FILTER}
)
SELECT (siccd / 100)::int AS sic2,
       count(DISTINCT permno) AS n_stocks
FROM crsp_q_stock.wrds_dsfv2_query d
JOIN elig USING (permno)
WHERE d.dlycaldt BETWEEN '1989-01-01' AND '1989-12-31'
  AND d.siccd IS NOT NULL
GROUP BY 1
ORDER BY 2 DESC;

-- A12: volume coverage (A-3.7). A12a: null/zero shares by year (one scan).
SELECT extract(year from dlycaldt)::int AS year,
       count(*) AS n_common_rows,
       count(*) FILTER (WHERE dlyvol IS NULL) AS n_vol_null,
       count(*) FILTER (WHERE dlyvol = 0) AS n_vol_zero
FROM crsp_q_stock.wrds_dsfv2_query
WHERE {COMMON_FILTER}
GROUP BY 1
ORDER BY 1;

-- A12b: median daily volume by exchange, sampled on day-15 cross-sections,
--       to expose NASDAQ volume-reporting conventions without a big sort.
SELECT extract(year from dlycaldt)::int AS year,
       primaryexch,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY dlyvol) AS median_vol
FROM crsp_q_stock.wrds_dsfv2_query
WHERE {COMMON_FILTER}
  AND extract(day from dlycaldt) = 15
  AND dlyvol > 0
GROUP BY 1, 2
ORDER BY 1, 2;
