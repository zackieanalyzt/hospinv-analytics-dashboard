SELECT
    snapshot_date,
    source_item_code,
    source_warehouse_code,
    SUM(qty_on_hand) AS qty_on_hand,
    AVG(avg_unit_cost) AS avg_unit_cost,
    SUM(stock_value) AS stock_value,
    MAX(source_updated_ts) AS source_updated_ts
FROM (
    SELECT
        CAST(c.OPERATE_DATE AS DATE) AS snapshot_date,
        c.WORKING_CODE AS source_item_code,
        COALESCE(c.STOCK_ID, c.DEPT_ID) AS source_warehouse_code,
        c.REMAIN_QTY AS qty_on_hand,
        c.REMAIN_COST AS avg_unit_cost,
        c.REMAIN_VALUE AS stock_value,
        c.OPERATE_DATE AS source_updated_ts
    FROM card c
    WHERE c.R_S_STATUS IN ('R', 'S')
      AND c.CANCEL_FLAG IS NULL
) AS src
GROUP BY snapshot_date, source_item_code, source_warehouse_code;
