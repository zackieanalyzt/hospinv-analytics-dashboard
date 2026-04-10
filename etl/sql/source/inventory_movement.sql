SELECT
    CONCAT(c.R_S_NUMBER, '-', c.RECORD_NUMBER) AS source_txn_id,
    CAST(c.R_S_DATE AS DATE) AS txn_date,
    c.OPERATE_DATE AS txn_ts,
    c.WORKING_CODE AS source_item_code,
    COALESCE(c.STOCK_ID, c.DEPT_ID) AS source_warehouse_code,
    CASE c.R_S_STATUS
        WHEN 'R' THEN 'receive'
        WHEN 'S' THEN 'issue'
        ELSE 'other'
    END AS movement_type,
    c.R_S_NUMBER AS ref_doc_no,
    CASE c.R_S_STATUS
        WHEN 'R' THEN 'GR'
        WHEN 'S' THEN 'ISSUANCE'
        ELSE 'OTHER'
    END AS ref_doc_type,
    c.LOT_NO AS lot_no,
    CAST(c.EXPIRED_DATE AS DATE) AS expiry_date,
    c.ACTIVE_QTY AS qty,
    c.COST AS unit_cost,
    c.VALUE AS line_value,
    c.VENDOR_CODE AS source_vendor_code,
    c.OPERATE_DATE AS source_updated_ts
FROM card c
WHERE c.R_S_STATUS IN ('R', 'S')
  AND c.CANCEL_FLAG IS NULL;
