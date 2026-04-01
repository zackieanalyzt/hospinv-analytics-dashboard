DELETE FROM mart.sum_expiry_daily
WHERE summary_date >= :from_date
  AND summary_date <= :to_date;

INSERT INTO mart.sum_expiry_daily (
    summary_date,
    dim_item_id,
    dim_warehouse_id,
    lot_no,
    expiry_date,
    days_to_expiry,
    expiry_status,
    qty_on_hand,
    stock_value,
    created_ts
)
SELECT
    snapshot_date,
    dim_item_id,
    dim_warehouse_id,
    lot_no,
    expiry_date,
    days_to_expiry,
    expiry_status,
    qty_on_hand,
    stock_value,
    NOW()
FROM core.fact_stock_lot_snapshot
WHERE snapshot_date >= :from_date
  AND snapshot_date <= :to_date;
