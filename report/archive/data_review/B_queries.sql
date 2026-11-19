-- Worker B: every SQL statement, labelled with query IDs (B1a ... B5d).
-- Executed only through report/data_review/B_checks.py (one connection per phase,
-- statement_timeout = 15min, server-side aggregation only).
-- Row-level B3 samples (20 PERMNOs) are written to git-ignored data/raw/wrds_api/.
-- Phase 1 discovery used db.list_tables / db.describe_table, not SQL.

-- ============================================================ B1: server counts vs crsp_manifest.json

-- B1a daily stocks (manifest: 102,464,776 rows; 40,427 permnos; 1961-01-03..2026-03-31;
-- manifest query 11771134 on crsp.wrds_dsfv2_query)
SELECT COUNT(*) AS rows, COUNT(DISTINCT permno) AS permnos,
       MIN(dlycaldt) AS first_date, MAX(dlycaldt) AS last_date
FROM crsp.wrds_dsfv2_query
WHERE dlycaldt BETWEEN '1961-01-01'::date AND '2026-03-31'::date;

-- B1b monthly stocks (manifest: 5,003,530 rows; 41,016 permnos; 1961-01-31..2026-06-30)
SELECT COUNT(*) AS rows, COUNT(DISTINCT permno) AS permnos,
       MIN(mthcaldt) AS first_date, MAX(mthcaldt) AS last_date
FROM crsp.wrds_msfv2_query
WHERE mthcaldt BETWEEN '1961-01-01'::date AND '2026-06-30'::date;

-- B1c delisting (manifest: 29,727 rows; 1961-01-20..2026-06-29; query 11771161)
SELECT COUNT(*) AS rows, COUNT(DISTINCT permno) AS permnos,
       MIN(delistingdt) AS first_date, MAX(delistingdt) AS last_date
FROM crsp_q_stock.stkdelists
WHERE delistingdt BETWEEN '1961-01-01'::date AND '2026-06-29'::date
  AND delactiontype = ANY (ARRAY['GDR','GEX','GLI','LOS','MER']);

-- B1d distributions (manifest: 1,023,403 rows; 1961-01-03..2026-06-30; query 11771165)
SELECT COUNT(*) AS rows, COUNT(DISTINCT permno) AS permnos,
       MIN(disexdt) AS first_date, MAX(disexdt) AS last_date
FROM crsp_q_stock.stkdistributions
WHERE disexdt BETWEEN '1961-01-01'::date AND '2026-06-30'::date
  AND distype = ANY (ARRAY['CD','CG','CP','FRS','IN','N/A','ROC','SD','SP','TSOO']);

-- B1e daily indexes (manifest: 16,481 rows; 1961-01-03..2026-06-30; query 11771207)
SELECT COUNT(*) AS rows, MIN(dlycaldt) AS first_date, MAX(dlycaldt) AS last_date
FROM crsp_q_stock.wrds_dailyindexret_query
WHERE dlycaldt BETWEEN '1961-01-01'::date AND '2026-06-30'::date;

-- B1f monthly indexes (manifest: 786 rows; 1961-01-31..2026-06-30; query 11771212)
SELECT COUNT(*) AS rows, MIN(mthcaldt) AS first_date, MAX(mthcaldt) AS last_date
FROM crsp_q_stock.wrds_monthlyindexret_query
WHERE mthcaldt BETWEEN '1961-01-01'::date AND '2026-06-30'::date;

-- B1g DFSCX monthly, fund 008296 (manifest: 535 rows; 1981-12-31..2026-06-30; query 11771343)
SELECT COUNT(*) AS rows, MIN(caldt) AS first_date, MAX(caldt) AS last_date
FROM crsp_q_mutualfunds.monthly_tna_ret_nav
WHERE crsp_fundno = '008296'
  AND caldt BETWEEN '1981-06-01'::date AND '2026-06-30'::date;

-- ============================================================ B2: is there a newer vintage?

-- B2a daily, annual-update library (crsp)
SELECT MAX(dlycaldt) AS last_date FROM crsp.wrds_dsfv2_query;

-- B2b daily, quarterly-update library (crsp_q_stock)
SELECT MAX(dlycaldt) AS last_date FROM crsp_q_stock.wrds_dsfv2_query;

-- B2c monthly, annual-update library (crsp)
SELECT MAX(mthcaldt) AS last_date FROM crsp.wrds_msfv2_query;

-- B2d monthly, quarterly-update library (crsp_q_stock)
SELECT MAX(mthcaldt) AS last_date FROM crsp_q_stock.wrds_msfv2_query;

-- ============================================================ B3: CIZ vs legacy SIZ conventions
-- Sample: 10 large long-lived PERMNOs + 10 performance-delisted 1963-2002 (dlstcd 500-599).
-- B3a1 and B3a2 selections, B3b per-PERMNO-year tables and B3c event rows are saved to
-- data/raw/wrds_api/; only summaries and difference counts go to B_results/.

-- B3a-1 10 large, long-lived stocks (largest max monthly cap among stocks with data
-- before 1975); deterministic
SELECT permno, MAX(mthcap) AS max_mthcap, MIN(mthcaldt) AS first_month, COUNT(*) AS n_months
FROM crsp.wrds_msfv2_query
GROUP BY permno
HAVING MIN(mthcaldt) < '1975-01-01'::date
ORDER BY MAX(mthcap) DESC NULLS LAST
LIMIT 10;

-- B3a-2 10 PERMNOs delisted for performance reasons 1963-2002 (legacy dlstcd 500-599),
-- deterministic (every 40th row ordered by dlstdt, permno)
SELECT permno, dlstdt, dlstcd, dlret, dlretx FROM (
    SELECT permno, dlstdt, dlstcd, dlret, dlretx,
           row_number() OVER (ORDER BY dlstdt, permno) AS rn
    FROM crsp.msedelist
    WHERE dlstdt BETWEEN '1963-01-01'::date AND '2002-12-31'::date
      AND dlstcd BETWEEN 500 AND 599) t
WHERE rn % 40 = 1
ORDER BY rn
LIMIT 10;

-- B3b-1 monthly compounded returns per PERMNO-year from the CIZ daily table.
-- The CIZ query can repeat a date when distributions share it, so deduplicate to one
-- row per permno-day (MAX dlyret) before compounding. <ARR> = ANY(ARRAY[...]) of the
-- 20 sample PERMNOs.
WITH d AS (
    SELECT permno, dlycaldt, MAX(dlyret) AS dlyret
    FROM crsp.wrds_dsfv2_query
    WHERE permno = <ARR> AND dlycaldt BETWEEN '1963-01-01'::date AND '2002-12-31'::date
    GROUP BY permno, dlycaldt)
SELECT permno, EXTRACT(YEAR FROM dlycaldt)::int AS yr,
       COUNT(*) AS n_days,
       SUM(CASE WHEN dlyret IS NULL THEN 1 ELSE 0 END) AS missing_days,
       CASE WHEN SUM(CASE WHEN dlyret IS NULL OR dlyret <= -1 THEN 1 ELSE 0 END) = 0
            THEN EXP(SUM(LN(1 + dlyret))) - 1 END AS ciz_yr_ret
FROM d
GROUP BY permno, EXTRACT(YEAR FROM dlycaldt)::int
ORDER BY permno, yr;

-- B3b-2 same from legacy crsp.msf (SIZ, available through 2024)
SELECT permno, EXTRACT(YEAR FROM date)::int AS yr,
       COUNT(*) AS n_months,
       SUM(CASE WHEN ret IS NULL THEN 1 ELSE 0 END) AS missing_months,
       CASE WHEN SUM(CASE WHEN ret IS NULL OR ret <= -1 THEN 1 ELSE 0 END) = 0
            THEN EXP(SUM(LN(1 + ret))) - 1 END AS siz_yr_ret
FROM crsp.msf
WHERE permno = <ARR>
  AND date BETWEEN '1963-01-31'::date AND '2002-12-31'::date
GROUP BY permno, EXTRACT(YEAR FROM date)::int
ORDER BY permno, yr;

-- B3c-1 legacy delisting returns, monthly (msedelist) and daily (dsedelist)
SELECT permno, dlstdt, dlstcd, dlret, dlretx
FROM crsp.msedelist
WHERE permno = <ARR_DELIST> AND dlstdt BETWEEN '1963-01-01'::date AND '2002-12-31'::date
ORDER BY permno, dlstdt;
-- (identical statement with crsp.dsedelist, saved as B_b3c1_dsedelist)

-- B3c-2 CIZ delisting returns
SELECT permno, delistingdt, delactiontype, delstatustype, delreasontype,
       delret, delretmisstype
FROM crsp_q_stock.stkdelists
WHERE permno = <ARR_DELIST>
  AND delistingdt BETWEEN '1963-01-01'::date AND '2002-12-31'::date
ORDER BY permno, delistingdt;

-- B3c-3 does CIZ dlyret on the final trading day already include the delisting return?
-- (rows within [-10, +5] days of the delisting date; compared locally)
SELECT s.permno, s.delistingdt, s.delret, d.dlycaldt, d.dlyret, d.dlydelflg
FROM crsp_q_stock.stkdelists s
JOIN crsp.wrds_dsfv2_query d
  ON d.permno = s.permno
 AND d.dlycaldt BETWEEN s.delistingdt - 10 AND s.delistingdt + 5
WHERE s.permno = <ARR_DELIST>
  AND s.delistingdt BETWEEN '1963-01-01'::date AND '2002-12-31'::date
ORDER BY s.permno, d.dlycaldt;

-- ============================================================ B4: factors on WRDS vs french_manifest.json
-- ff library (discovery) has 12 tables; there is NO standalone momentum or
-- short-term-reversal table: momentum is the `umd` column in factors_daily/monthly.

-- B4a ff.factors_daily coverage (manifest daily: 19260701..20260831)
SELECT COUNT(*) AS rows, MIN(date) AS first_date, MAX(date) AS last_date,
       COUNT(mktrf) AS n_mktrf, COUNT(smb) AS n_smb, COUNT(hml) AS n_hml,
       COUNT(rf) AS n_rf, COUNT(umd) AS n_umd
FROM ff.factors_daily;

-- B4b ff.factors_monthly coverage (manifest monthly: 192607..202608)
SELECT COUNT(*) AS rows, MIN(date) AS first_date, MAX(date) AS last_date,
       COUNT(mktrf) AS n_mktrf, COUNT(smb) AS n_smb, COUNT(hml) AS n_hml,
       COUNT(rf) AS n_rf, COUNT(umd) AS n_umd
FROM ff.factors_monthly;

-- B4c momentum (umd) and RF end dates, monthly
SELECT COUNT(umd) AS n_umd,
       MIN(date) FILTER (WHERE umd IS NOT NULL) AS first_umd,
       MAX(date) FILTER (WHERE umd IS NOT NULL) AS last_umd,
       MIN(date) FILTER (WHERE rf IS NOT NULL) AS first_rf,
       MAX(date) FILTER (WHERE rf IS NOT NULL) AS last_rf
FROM ff.factors_monthly;

-- B4d momentum (umd) end dates, daily
SELECT COUNT(umd) AS n_umd,
       MIN(date) FILTER (WHERE umd IS NOT NULL) AS first_umd,
       MAX(date) FILTER (WHERE umd IS NOT NULL) AS last_umd
FROM ff.factors_daily;

-- ============================================================ B5: gaps

-- B5a TAQ: availability for 2020-2025 from discovery table names + describe_table
-- (approx row counts from EXPLAIN) + LIMIT 1 existence checks. No row data pulled.
-- Key tables per year library taqm_<YYYY>: complete_nbbo_<YYYY> (NBBO), ctm_<YYYY>
-- (consolidated trades), cqm_<YYYY> (consolidated quotes), mastm_<YYYY> (master).
-- Also: LIMIT 1 SELECT on each; results in B5a_taq_availability.csv.

-- B5b size-decile portfolio returns covering Jun 1963 - Dec 1981 (small-stock stand-in);
-- CRSP msix decret1 is the smallest-size decile value-weighted return
SELECT COUNT(*) AS months, MIN(caldt) AS first_date, MAX(caldt) AS last_date,
       COUNT(decret1) AS n_decret1, COUNT(decret10) AS n_decret10
FROM crsp.msix
WHERE caldt BETWEEN '1963-06-01'::date AND '1981-12-31'::date;

-- B5c-1 Table 4 boundary: S&P 500 monthly, Jun 1963 - Dec 2002 (475 months expected).
-- msp500 has no `totret`; vwretd is the S&P-500 value-weighted total-return candidate,
-- sprtrn is the price return.
SELECT COUNT(*) AS months, MIN(caldt) AS first_date, MAX(caldt) AS last_date,
       COUNT(vwretd) AS n_vwretd, COUNT(sprtrn) AS n_sprtrn, COUNT(spindx) AS n_spindx
FROM crsp.msp500
WHERE caldt BETWEEN '1963-06-01'::date AND '2002-12-31'::date;

-- B5c-2 Treasury-bill monthly total returns (30-day T-bill return index t30ret)
SELECT COUNT(*) AS months, MIN(caldt) AS first_date, MAX(caldt) AS last_date,
       COUNT(t30ret) AS n_t30ret, COUNT(t90ret) AS n_t90ret
FROM crsp.mcti
WHERE caldt BETWEEN '1963-06-01'::date AND '2002-12-31'::date;

-- B5c-3 crsp.msi coverage for the same window (sprtrn = price return only)
SELECT COUNT(*) AS months, MIN(date) AS first_date, MAX(date) AS last_date,
       COUNT(vwretd) AS n_vwretd, COUNT(sprtrn) AS n_sprtrn
FROM crsp.msi
WHERE date BETWEEN '1963-06-01'::date AND '2002-12-31'::date;

-- B5d entitlements: probe list_tables('sbbi') and list_tables('ibbotson');
-- any NotSubscribedError/unknown-library error is a finding, not a failure.
-- Recorded by the runner in B5d_entitlements.csv (no SQL).
