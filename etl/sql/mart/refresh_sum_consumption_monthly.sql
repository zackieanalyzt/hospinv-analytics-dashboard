DELETE FROM mart.sum_consumption_monthly
WHERE year_month >= :from_month
  AND year_month <= :to_month;

INSERT INTO mart.sum_consumption_monthly (
    year_month,
    dim_item_id,
    dim_warehouse_id,
    issue_qty,
    issue_value,
    movement_days,
    created_ts
)
SELECT
    TO_CHAR(txn_date, 'YYYYMM')::INTEGER AS year_month,
    dim_item_id,
    dim_warehouse_id,
    COALESCE(SUM(CASE WHEN movement_direction = 'out' THEN ABS(signed_qty) ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN movement_direction = 'out' THEN ABS(signed_value) ELSE 0 END), 0),
    COUNT(DISTINCT txn_date),
    NOW()
FROM core.fact_inventory_movement
WHERE TO_CHAR(txn_date, 'YYYYMM')::INTEGER >= :from_month
  AND TO_CHAR(txn_date, 'YYYYMM')::INTEGER <= :to_month
GROUP BY TO_CHAR(txn_date, 'YYYYMM')::INTEGER, dim_item_id, dim_warehouse_id;
