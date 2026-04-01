-- TODO: Replace with real invs2019 source query
SELECT
    txn_id AS source_txn_id,
    txn_date,
    txn_ts,
    item_code AS source_item_code,
    warehouse_code AS source_warehouse_code,
    movement_type,
    ref_doc_no,
    ref_doc_type,
    lot_no,
    expiry_date,
    qty,
    unit_cost,
    line_value,
    vendor_code AS source_vendor_code,
    updated_at AS source_updated_ts
FROM your_inventory_movement_table;
