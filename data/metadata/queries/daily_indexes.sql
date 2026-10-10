SELECT
    crsp_q_stock.wrds_dailyindexret_query.dlycaldt,
    crsp_q_stock.wrds_dailyindexret_query.vwretd,
    crsp_q_stock.wrds_dailyindexret_query.vwretx,
    crsp_q_stock.wrds_dailyindexret_query.vwtotval,
    crsp_q_stock.wrds_dailyindexret_query.vwusdval,
    crsp_q_stock.wrds_dailyindexret_query.vwtotcnt,
    crsp_q_stock.wrds_dailyindexret_query.vwusdcnt,
    crsp_q_stock.wrds_dailyindexret_query.ewretd,
    crsp_q_stock.wrds_dailyindexret_query.ewretx,
    crsp_q_stock.wrds_dailyindexret_query.ewtotval,
    crsp_q_stock.wrds_dailyindexret_query.ewusdval,
    crsp_q_stock.wrds_dailyindexret_query.ewtotcnt,
    crsp_q_stock.wrds_dailyindexret_query.ewusdcnt,
    crsp_q_stock.wrds_dailyindexret_query.sprtrn,
    crsp_q_stock.wrds_dailyindexret_query.spindx

FROM crsp_q_stock.wrds_dailyindexret_query

WHERE crsp_q_stock.wrds_dailyindexret_query.dlycaldt BETWEEN
    '1961-01-01'::date AND '2026-06-30'::date
