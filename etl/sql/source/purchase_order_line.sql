-- TODO: Replace with real invs2019 source query
SELECT
    po_no,
    po_date,
    item_code AS source_item_code,
    vendor_code AS source_vendor_code,
    ordered_qty,
    ordered_unit_cost,
    ordered_value,
    po_status,
    updated_at AS source_updated_ts
FROM your_purchase_order_line_table;
