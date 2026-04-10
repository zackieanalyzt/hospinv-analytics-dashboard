SELECT
    snapshot_date,
    source_item_code,
    source_warehouse_code,
    lot_no,
    expiry_date,
    SUM(qty_on_hand) AS qty_on_hand,
    AVG(avg_unit_cost) AS avg_unit_cost,
    SUM(stock_value) AS stock_value,
    MAX(source_updated_ts) AS source_updated_ts
FROM (
    SELECT
        CAST(c.OPERATE_DATE AS DATE) AS snapshot_date,
        c.WORKING_CODE AS source_item_code,
        COALESCE(c.STOCK_ID, c.DEPT_ID) AS source_warehouse_code,
        c.LOT_NO AS lot_no,
        CAST(c.EXPIRED_DATE AS DATE) AS expiry_date,
        c.REMAIN_QTY_LOT AS qty_on_hand,
        c.WT_AVG AS avg_unit_cost,
        c.REMAIN_VALUE_LOT AS stock_value,
        c.OPERATE_DATE AS source_updated_ts
    FROM card c
    WHERE c.R_S_STATUS IN ('R', 'S')
      AND c.CANCEL_FLAG IS NULL
      AND c.LOT_NO IS NOT NULL
      AND c.REMAIN_QTY_LOT IS NOT NULL
) AS src
GROUP BY snapshot_date, source_item_code, source_warehouse_code, lot_no, expiry_date;
