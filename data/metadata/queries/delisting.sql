SELECT
    crsp_q_stock.stkdelists.delactiontype,
    crsp_q_stock.stkdelists.permno,
    crsp_q_stock.stkdelists.delistingdt,
    id_table.primaryexch,
    id_table.nasdissuno,
    id_table.siccd,
    crsp_q_stock.stkdelists.deldtprc,
    crsp_q_stock.stkdelists.deldtprcflg,
    crsp_q_stock.stkdelists.delstatustype,
    crsp_q_stock.stkdelists.delreasontype,
    crsp_q_stock.stkdelists.delpaymenttype,
    crsp_q_stock.stkdelists.delpermno,
    crsp_q_stock.stkdelists.delpermco,
    crsp_q_stock.stkdelists.delret,
    crsp_q_stock.stkdelists.delretmisstype,
    crsp_q_stock.stkdelists.delnextdt,
    crsp_q_stock.stkdelists.delnextprc,
    crsp_q_stock.stkdelists.delnextprcflg,
    crsp_q_stock.stkdelists.delamtdt,
    crsp_q_stock.stkdelists.deldivamt,
    crsp_q_stock.stkdelists.deldistype,
    crsp_q_stock.stkdelists.deldlydt

FROM crsp_q_stock.stkdelists
LEFT JOIN (
    SELECT
        permno,
        primaryexch,
        nasdissuno,
        siccd
    FROM crsp_q_stock.stksecurityinfohdr
) AS id_table

ON crsp_q_stock.stkdelists.permno = id_table.permno

WHERE crsp_q_stock.stkdelists.delistingdt BETWEEN
    '1961-01-01'::date AND '2026-06-29'::date

AND ("crsp_q_stock"."stkdelists"."delactiontype" = ANY (ARRAY['GDR','GEX','GLI','LOS','MER']))
