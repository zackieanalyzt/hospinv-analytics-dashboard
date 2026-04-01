DELETE FROM mart.sum_procurement_monthly
WHERE year_month >= :from_month
  AND year_month <= :to_month;

INSERT INTO mart.sum_procurement_monthly (
    year_month,
    dim_item_id,
    dim_vendor_id,
    ordered_qty,
    ordered_value,
    received_qty,
    received_value,
    po_count,
    gr_count,
    created_ts
)
WITH po AS (
    SELECT
        TO_CHAR(po_date, 'YYYYMM')::INTEGER AS year_month,
        dim_item_id,
        dim_vendor_id,
        SUM(ordered_qty) AS ordered_qty,
        SUM(COALESCE(ordered_value, 0)) AS ordered_value,
        COUNT(DISTINCT po_no) AS po_count
    FROM core.fact_purchase_order_line
    WHERE TO_CHAR(po_date, 'YYYYMM')::INTEGER >= :from_month
      AND TO_CHAR(po_date, 'YYYYMM')::INTEGER <= :to_month
    GROUP BY TO_CHAR(po_date, 'YYYYMM')::INTEGER, dim_item_id, dim_vendor_id
),
gr AS (
    SELECT
        TO_CHAR(gr_date, 'YYYYMM')::INTEGER AS year_month,
        dim_item_id,
        dim_vendor_id,
        SUM(received_qty) AS received_qty,
        SUM(COALESCE(received_value, 0)) AS received_value,
        COUNT(DISTINCT gr_no) AS gr_count
    FROM core.fact_goods_receipt_line
    WHERE TO_CHAR(gr_date, 'YYYYMM')::INTEGER >= :from_month
      AND TO_CHAR(gr_date, 'YYYYMM')::INTEGER <= :to_month
    GROUP BY TO_CHAR(gr_date, 'YYYYMM')::INTEGER, dim_item_id, dim_vendor_id
)
SELECT
    COALESCE(po.year_month, gr.year_month) AS year_month,
    COALESCE(po.dim_item_id, gr.dim_item_id) AS dim_item_id,
    COALESCE(po.dim_vendor_id, gr.dim_vendor_id) AS dim_vendor_id,
    COALESCE(po.ordered_qty, 0),
    COALESCE(po.ordered_value, 0),
    COALESCE(gr.received_qty, 0),
    COALESCE(gr.received_value, 0),
    COALESCE(po.po_count, 0),
    COALESCE(gr.gr_count, 0),
    NOW()
FROM po
FULL OUTER JOIN gr
    ON po.year_month = gr.year_month
   AND po.dim_item_id = gr.dim_item_id
   AND COALESCE(po.dim_vendor_id, -1) = COALESCE(gr.dim_vendor_id, -1);
