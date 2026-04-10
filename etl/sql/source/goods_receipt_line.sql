SELECT
    i.INVOICE_NO AS gr_no,
    CAST(i.INVOICE_DATE AS DATE) AS gr_date,
    i.PO_NO AS po_no,
    ic.WORKING_CODE AS source_item_code,
    COALESCE(ic.DEPT_ID, i.DEPT_ID) AS source_warehouse_code,
    i.VENDOR_CODE AS source_vendor_code,
    ic.LOT_NO AS lot_no,
    CAST(ic.EXPIRED_DATE AS DATE) AS expiry_date,
    ic.QTY_ORDER AS received_qty,
    ic.BUY_UNIT_COST AS received_unit_cost,
    (ic.QTY_ORDER * ic.BUY_UNIT_COST) AS received_value,
    NOW() AS source_updated_ts
FROM ms_ivo i
INNER JOIN ms_ivo_c ic ON i.INVOICE_NO = ic.INVOICE_NO
WHERE i.RCV_FLAG = 'Y';
