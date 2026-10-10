SELECT
    crsp_q_stock.stkdistributions.distype,
    crsp_q_stock.stkdistributions.permno,
    crsp_q_stock.stkdistributions.disexdt,
    id_table.primaryexch,
    id_table.nasdissuno,
    id_table.siccd,
    crsp_q_stock.stkdistributions.disseqnbr,
    crsp_q_stock.stkdistributions.disordinaryflg,
    crsp_q_stock.stkdistributions.disfreqtype,
    crsp_q_stock.stkdistributions.dispaymenttype,
    crsp_q_stock.stkdistributions.disdetailtype,
    crsp_q_stock.stkdistributions.distaxtype,
    crsp_q_stock.stkdistributions.disorigcurtype,
    crsp_q_stock.stkdistributions.disdivamt,
    crsp_q_stock.stkdistributions.disfacpr,
    crsp_q_stock.stkdistributions.disfacshr,
    crsp_q_stock.stkdistributions.disdeclaredt,
    crsp_q_stock.stkdistributions.disrecorddt,
    crsp_q_stock.stkdistributions.dispaydt,
    crsp_q_stock.stkdistributions.dispermno,
    crsp_q_stock.stkdistributions.dispermco,
    crsp_q_stock.stkdistributions.disamountsourcetype

FROM crsp_q_stock.stkdistributions
LEFT JOIN (
    SELECT
        permno,
        primaryexch,
        nasdissuno,
        siccd
    FROM crsp_q_stock.stksecurityinfohdr
) AS id_table

ON crsp_q_stock.stkdistributions.permno = id_table.permno

WHERE crsp_q_stock.stkdistributions.disexdt BETWEEN
    '1961-01-01'::date AND '2026-06-30'::date

AND ("crsp_q_stock"."stkdistributions"."distype" = ANY (ARRAY['CD','CG','CP','FRS','IN','N/A','ROC','SD','SP','TSOO']))
