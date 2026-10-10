SELECT
    crsp_q_stock.wrds_monthlyindexret_query.mthcaldt,
    crsp_q_stock.wrds_monthlyindexret_query.vwretd,
    crsp_q_stock.wrds_monthlyindexret_query.vwretx,
    crsp_q_stock.wrds_monthlyindexret_query.vwtotval,
    crsp_q_stock.wrds_monthlyindexret_query.vwusdval,
    crsp_q_stock.wrds_monthlyindexret_query.vwtotcnt,
    crsp_q_stock.wrds_monthlyindexret_query.vwusdcnt,
    crsp_q_stock.wrds_monthlyindexret_query.ewretd,
    crsp_q_stock.wrds_monthlyindexret_query.ewretx,
    crsp_q_stock.wrds_monthlyindexret_query.ewtotval,
    crsp_q_stock.wrds_monthlyindexret_query.ewusdval,
    crsp_q_stock.wrds_monthlyindexret_query.ewtotcnt,
    crsp_q_stock.wrds_monthlyindexret_query.ewusdcnt,
    crsp_q_stock.wrds_monthlyindexret_query.sprtrn,
    crsp_q_stock.wrds_monthlyindexret_query.spindx

FROM crsp_q_stock.wrds_monthlyindexret_query

WHERE crsp_q_stock.wrds_monthlyindexret_query.mthcaldt BETWEEN
    '1961-01-01'::date AND '2026-06-30'::date
