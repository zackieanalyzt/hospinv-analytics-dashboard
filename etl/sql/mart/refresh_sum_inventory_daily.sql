DELETE FROM mart.sum_inventory_daily
WHERE summary_date >= :from_date
  AND summary_date <= :to_date;

INSERT INTO mart.sum_inventory_daily (
    summary_date,
    total_sku_count,
    active_sku_count,
    warehouse_count,
    total_qty_on_hand,
    total_stock_value,
    zero_stock_sku_count,
    negative_stock_sku_count,
    near_expiry_sku_count,
    expired_sku_count,
    dead_stock_sku_count,
    created_ts
)
SELECT
    f.snapshot_date AS summary_date,
    COUNT(DISTINCT f.dim_item_id),
    COUNT(DISTINCT CASE WHEN i.is_active THEN f.dim_item_id END),
    COUNT(DISTINCT f.dim_warehouse_id),
    COALESCE(SUM(f.qty_on_hand), 0),
    COALESCE(SUM(f.stock_value), 0),
    COUNT(DISTINCT CASE WHEN f.qty_on_hand = 0 THEN f.dim_item_id END),
    COUNT(DISTINCT CASE WHEN f.qty_on_hand < 0 THEN f.dim_item_id END),
    0,
    0,
    0,
    NOW()
FROM core.fact_stock_snapshot f
LEFT JOIN core.dim_item i ON f.dim_item_id = i.dim_item_id
WHERE f.snapshot_date >= :from_date
  AND f.snapshot_date <= :to_date
GROUP BY f.snapshot_date;
