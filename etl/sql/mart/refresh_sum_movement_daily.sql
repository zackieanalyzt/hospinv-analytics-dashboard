DELETE FROM mart.sum_movement_daily
WHERE summary_date >= :from_date
  AND summary_date <= :to_date;

INSERT INTO mart.sum_movement_daily (
    summary_date,
    dim_item_id,
    dim_warehouse_id,
    movement_type,
    movement_qty,
    movement_value,
    txn_count,
    created_ts
)
SELECT
    txn_date,
    dim_item_id,
    dim_warehouse_id,
    movement_type,
    COALESCE(SUM(ABS(qty)), 0),
    COALESCE(SUM(ABS(COALESCE(line_value, 0))), 0),
    COUNT(*),
    NOW()
FROM core.fact_inventory_movement
WHERE txn_date >= :from_date
  AND txn_date <= :to_date
GROUP BY txn_date, dim_item_id, dim_warehouse_id, movement_type;
