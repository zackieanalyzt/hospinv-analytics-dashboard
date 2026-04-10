"""
SQL queries for various reports and dashboards
"""

# ========== DASHBOARD OVERVIEW QUERIES ==========

QUERY_DASHBOARD_SUMMARY = """
SELECT 
    (SELECT COUNT(*) FROM core.dim_item) as total_items,
    (SELECT COUNT(DISTINCT warehouse_id) FROM core.dim_warehouse) as total_warehouses,
    (SELECT COUNT(DISTINCT vendor_id) FROM core.dim_vendor) as total_vendors,
    (SELECT COALESCE(SUM(quantity), 0) FROM mart.fact_stock_balance) as total_stock_qty
"""

QUERY_INVENTORY_LEVEL = """
SELECT 
    COALESCE(di.item_code, 'Unknown') as item_code,
    COALESCE(di.item_name, 'Unknown') as item_name,
    COALESCE(dw.warehouse_name, 'Unknown') as warehouse,
    COALESCE(fsb.quantity, 0) as quantity,
    COALESCE(fsb.last_updated, NOW()) as last_updated
FROM mart.fact_stock_balance fsb
LEFT JOIN core.dim_item di ON fsb.item_id = di.item_id
LEFT JOIN core.dim_warehouse dw ON fsb.warehouse_id = dw.warehouse_id
ORDER BY di.item_code, dw.warehouse_name
LIMIT 1000
"""

QUERY_LOW_STOCK_ITEMS = """
SELECT 
    COALESCE(di.item_code, 'Unknown') as item_code,
    COALESCE(di.item_name, 'Unknown') as item_name,
    COALESCE(dw.warehouse_name, 'Unknown') as warehouse,
    COALESCE(fsb.quantity, 0) as stock_qty,
    COALESCE(fsb.reorder_point, 0) as reorder_point,
    COALESCE(fsb.last_updated, NOW()) as last_checked
FROM mart.fact_stock_balance fsb
LEFT JOIN core.dim_item di ON fsb.item_id = di.item_id
LEFT JOIN core.dim_warehouse dw ON fsb.warehouse_id = dw.warehouse_id
WHERE COALESCE(fsb.quantity, 0) <= COALESCE(fsb.reorder_point, 0)
ORDER BY fsb.quantity ASC
"""

QUERY_EXPIRY_ITEMS = """
SELECT 
    COALESCE(di.item_code, 'Unknown') as item_code,
    COALESCE(di.item_name, 'Unknown') as item_name,
    COALESCE(dw.warehouse_name, 'Unknown') as warehouse,
    COALESCE(fim.expiry_date::date, CURRENT_DATE) as expiry_date,
    COALESCE(fim.quantity, 0) as stock_qty,
    (COALESCE(fim.expiry_date::date, CURRENT_DATE) - CURRENT_DATE) as days_to_expiry
FROM stg.fact_inventory_movement fim
LEFT JOIN core.dim_item di ON fim.item_id = di.item_id
LEFT JOIN core.dim_warehouse dw ON fim.warehouse_id = dw.warehouse_id
WHERE COALESCE(fim.expiry_date::date, CURRENT_DATE + INTERVAL '1 year') <= CURRENT_DATE + INTERVAL '90 days'
    AND COALESCE(fim.quantity, 0) > 0
ORDER BY fim.expiry_date ASC
"""

# ========== CONSUMPTION ANALYTICS ==========

QUERY_CONSUMPTION_DAILY = """
SELECT 
    date,
    total_quantity,
    total_value
FROM mart.sum_consumption_daily
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date DESC
"""

QUERY_CONSUMPTION_MONTHLY = """
SELECT 
    YEAR,
    MONTH,
    total_quantity,
    total_value
FROM mart.sum_consumption_monthly
WHERE YEAR = EXTRACT(YEAR FROM CURRENT_DATE)
   OR YEAR = EXTRACT(YEAR FROM CURRENT_DATE) - 1
ORDER BY YEAR DESC, MONTH DESC
"""

QUERY_CONSUMPTION_BY_ITEM = """
SELECT 
    di.item_code,
    di.item_name,
    SUM(fim.quantity) as total_consumed,
    SUM(fim.quantity * fim.unit_cost) as total_cost
FROM stg.fact_inventory_movement fim
LEFT JOIN core.dim_item di ON fim.item_id = di.item_id
WHERE fim.movement_type = 'CONSUMPTION'
    AND fim.movement_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY di.item_code, di.item_name
ORDER BY total_consumed DESC
LIMIT 50
"""

# ========== PROCUREMENT ==========

QUERY_PURCHASE_ORDERS_OPEN = """
SELECT 
    po_number,
    po_date,
    dv.vendor_name,
    total_amount,
    status
FROM stg.fact_purchase_order_line fpol
LEFT JOIN core.dim_vendor dv ON fpol.vendor_id = dv.vendor_id
WHERE status IN ('OPEN', 'PENDING', 'PARTIAL')
ORDER BY po_date DESC
"""

QUERY_GOODS_RECEIPT_PENDING = """
SELECT 
    reference_number,
    receipt_date,
    dv.vendor_name,
    total_quantity,
    status
FROM stg.fact_goods_receipt_line fgrl
LEFT JOIN core.dim_vendor dv ON fgrl.vendor_id = dv.vendor_id
WHERE status IN ('PENDING', 'PARTIAL', 'AWAITING_QC')
ORDER BY receipt_date DESC
"""

# ========== BUDGET ANALYSIS ==========

QUERY_BUDGET_BURN_MONTHLY = """
SELECT 
    MONTH::integer as month,
    COALESCE(allocated, 0) as budget_allocated,
    COALESCE(consumed, 0) as budget_consumed,
    COALESCE(remaining, 0) as budget_remaining,
    ROUND(100.0 * COALESCE(consumed, 0) / NULLIF(COALESCE(allocated, 1), 0), 2) as burn_percentage
FROM mart.sum_budget_burn_monthly
WHERE YEAR = EXTRACT(YEAR FROM CURRENT_DATE)
ORDER BY MONTH
"""

QUERY_BUDGET_SUMMARY = """
SELECT 
    COALESCE(category, 'Other') as category,
    COALESCE(SUM(allocated), 0) as allocated,
    COALESCE(SUM(consumed), 0) as consumed,
    COALESCE(SUM(remaining), 0) as remaining
FROM mart.sum_budget_burn_monthly
WHERE YEAR = EXTRACT(YEAR FROM CURRENT_DATE)
GROUP BY category
"""

# ========== QUALITY CONTROL ==========

QUERY_QUALITY_RESULTS_RECENT = """
SELECT 
    test_date,
    item_name,
    warehouse_name,
    test_type,
    result_status,
    notes
FROM stg.fact_quality_control
ORDER BY test_date DESC
LIMIT 100
"""

QUERY_QUALITY_SUMMARY = """
SELECT 
    result_status,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM stg.fact_quality_control
WHERE test_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY result_status
ORDER BY count DESC
"""

# ========== DEAD STOCK & EXPIRY ==========

QUERY_DEAD_STOCK = """
SELECT 
    di.item_code,
    di.item_name,
    dw.warehouse_name,
    SUM(fim.quantity) as stock_qty,
    MAX(fim.movement_date) as last_movement,
    CURRENT_DATE - MAX(fim.movement_date) as days_inactive
FROM stg.fact_inventory_movement fim
LEFT JOIN core.dim_item di ON fim.item_id = di.item_id
LEFT JOIN core.dim_warehouse dw ON fim.warehouse_id = dw.warehouse_id
GROUP BY di.item_code, di.item_name, dw.warehouse_name
HAVING MAX(fim.movement_date) < CURRENT_DATE - INTERVAL '90 days'
    AND SUM(fim.quantity) > 0
ORDER BY days_inactive DESC
"""

QUERY_EXPIRY_SUMMARY = """
SELECT 
    CASE 
        WHEN expiry_date::date - CURRENT_DATE <= 0 THEN 'Expired'
        WHEN expiry_date::date - CURRENT_DATE <= 30 THEN '0-30 Days'
        WHEN expiry_date::date - CURRENT_DATE <= 90 THEN '30-90 Days'
        WHEN expiry_date::date - CURRENT_DATE <= 180 THEN '90-180 Days'
        ELSE '180+ Days'
    END as expiry_range,
    COUNT(*) as item_count,
    SUM(quantity) as total_quantity
FROM stg.fact_inventory_movement
WHERE quantity > 0
GROUP BY expiry_range
ORDER BY 
    CASE 
        WHEN expiry_range = 'Expired' THEN 1
        WHEN expiry_range = '0-30 Days' THEN 2
        WHEN expiry_range = '30-90 Days' THEN 3
        WHEN expiry_range = '90-180 Days' THEN 4
        ELSE 5
    END
"""

# ========== INVENTORY MOVEMENT ==========

QUERY_INVENTORY_MOVEMENT_SUMMARY = """
SELECT 
    movement_type,
    COUNT(*) as transaction_count,
    SUM(quantity) as total_quantity,
    SUM(quantity * unit_cost) as total_value
FROM stg.fact_inventory_movement
WHERE movement_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY movement_type
ORDER BY transaction_count DESC
"""

QUERY_TOP_VENDORS = """
SELECT 
    dv.vendor_id,
    dv.vendor_name,
    COUNT(*) as order_count,
    SUM(fpol.line_amount) as total_amount,
    AVG(fpol.line_amount) as avg_order_value
FROM stg.fact_purchase_order_line fpol
LEFT JOIN core.dim_vendor dv ON fpol.vendor_id = dv.vendor_id
WHERE fpol.po_date >= CURRENT_DATE - INTERVAL '180 days'
GROUP BY dv.vendor_id, dv.vendor_name
ORDER BY total_amount DESC
LIMIT 10
"""

# ========== DATA FRESHNESS ==========

QUERY_DATA_FRESHNESS = """
SELECT 
    table_name,
    last_updated,
    CURRENT_TIMESTAMP - last_updated as time_since_update,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_updated))/3600 as hours_since_update
FROM stg.data_freshness
ORDER BY last_updated DESC
"""
