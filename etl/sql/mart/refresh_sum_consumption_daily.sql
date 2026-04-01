DELETE FROM mart.sum_consumption_daily
WHERE summary_date >= :from_date
  AND summary_date <= :to_date;

INSERT INTO mart.sum_consumption_daily (
    summary_date,
    dim_item_id,
    dim_warehouse_id,
    issue_qty,
    issue_value,
    avg_daily_consumption_30d,
    avg_daily_consumption_90d,
    created_ts
)
SELECT
    txn_date,
    dim_item_id,
    dim_warehouse_id,
    COALESCE(SUM(CASE WHEN movement_direction = 'out' THEN ABS(signed_qty) ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN movement_direction = 'out' THEN ABS(signed_value) ELSE 0 END), 0),
    NULL,
    NULL,
    NOW()
FROM core.fact_inventory_movement
WHERE txn_date >= :from_date
  AND txn_date <= :to_date
GROUP BY txn_date, dim_item_id, dim_warehouse_id;
