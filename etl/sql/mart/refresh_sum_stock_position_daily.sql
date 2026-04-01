DELETE FROM mart.sum_stock_position_daily
WHERE summary_date >= :from_date
  AND summary_date <= :to_date;

INSERT INTO mart.sum_stock_position_daily (
    summary_date,
    dim_item_id,
    dim_warehouse_id,
    qty_on_hand,
    avg_unit_cost,
    stock_value,
    stock_status,
    days_of_stock_est,
    reorder_flag,
    overstock_flag,
    created_ts
)
SELECT
    snapshot_date,
    dim_item_id,
    dim_warehouse_id,
    qty_on_hand,
    avg_unit_cost,
    stock_value,
    stock_status,
    NULL,
    FALSE,
    FALSE,
    NOW()
FROM core.fact_stock_snapshot
WHERE snapshot_date >= :from_date
  AND snapshot_date <= :to_date;
