-- TODO: Replace with real invs2019 source query
SELECT
    gr_no,
    gr_date,
    po_no,
    item_code AS source_item_code,
    warehouse_code AS source_warehouse_code,
    vendor_code AS source_vendor_code,
    lot_no,
    expiry_date,
    received_qty,
    received_unit_cost,
    received_value,
    updated_at AS source_updated_ts
FROM your_goods_receipt_line_table;
