SELECT
    p.PO_NO AS po_no,
    CAST(p.PO_DATE AS DATE) AS po_date,
    pc.WORKING_CODE AS source_item_code,
    pc.VENDOR_CODE AS source_vendor_code,
    pc.QTY_ORDER AS ordered_qty,
    pc.BUY_UNIT_COST AS ordered_unit_cost,
    (pc.QTY_ORDER * pc.BUY_UNIT_COST) AS ordered_value,
    CASE 
        WHEN p.PROCESS = '3' THEN 'received_full'
        WHEN p.PROCESS = '2' THEN 'received_partial'
        WHEN p.PROCESS = '1' THEN 'approved'
        WHEN p.PROCESS = '4' OR p.OK = 'N' THEN 'cancelled'
        WHEN p.OK = 'Y' THEN 'approved'
        ELSE 'pending'
    END AS po_status,
    CAST(p.PO_DATE AS DATETIME) AS source_updated_ts
FROM ms_po p
INNER JOIN ms_po_c pc ON p.PO_NO = pc.PO_NO;
