-- TODO: Replace with real invs2019 source query
SELECT
    warehouse_code AS source_warehouse_code,
    warehouse_name,
    warehouse_type,
    parent_warehouse_code,
    is_active,
    updated_at AS source_updated_ts
FROM your_warehouse_master_table;
