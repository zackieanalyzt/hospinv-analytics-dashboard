-- TODO: Replace with real invs2019 source query
SELECT
    snapshot_date,
    item_code AS source_item_code,
    warehouse_code AS source_warehouse_code,
    lot_no,
    expiry_date,
    qty_on_hand,
    avg_unit_cost,
    stock_value,
    updated_at AS source_updated_ts
FROM your_stock_lot_balance_table;
