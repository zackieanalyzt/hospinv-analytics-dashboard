DELETE FROM mart.sum_dead_stock_daily
WHERE summary_date >= :from_date
  AND summary_date <= :to_date;

INSERT INTO mart.sum_dead_stock_daily (
    summary_date,
    dim_item_id,
    dim_warehouse_id,
    qty_on_hand,
    stock_value,
    last_issue_date,
    days_since_last_issue,
    dead_stock_flag,
    slow_moving_flag,
    created_ts
)
SELECT
    f.snapshot_date,
    f.dim_item_id,
    f.dim_warehouse_id,
    f.qty_on_hand,
    f.stock_value,
    x.last_issue_date,
    CASE
        WHEN x.last_issue_date IS NULL THEN NULL
        ELSE (f.snapshot_date - x.last_issue_date)
    END AS days_since_last_issue,
    CASE
        WHEN x.last_issue_date IS NULL AND f.qty_on_hand > 0 THEN TRUE
        WHEN x.last_issue_date IS NOT NULL AND (f.snapshot_date - x.last_issue_date) >= 180 AND f.qty_on_hand > 0 THEN TRUE
        ELSE FALSE
    END AS dead_stock_flag,
    CASE
        WHEN x.last_issue_date IS NOT NULL AND (f.snapshot_date - x.last_issue_date) BETWEEN 90 AND 179 AND f.qty_on_hand > 0 THEN TRUE
        ELSE FALSE
    END AS slow_moving_flag,
    NOW()
FROM core.fact_stock_snapshot f
LEFT JOIN (
    SELECT
        dim_item_id,
        dim_warehouse_id,
        MAX(txn_date) AS last_issue_date
    FROM core.fact_inventory_movement
    WHERE movement_direction = 'out'
    GROUP BY dim_item_id, dim_warehouse_id
) x
    ON f.dim_item_id = x.dim_item_id
   AND f.dim_warehouse_id = x.dim_warehouse_id
WHERE f.snapshot_date >= :from_date
  AND f.snapshot_date <= :to_date;
