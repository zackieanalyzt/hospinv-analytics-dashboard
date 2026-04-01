INSERT INTO core.dim_warehouse (
    source_warehouse_code,
    warehouse_name,
    warehouse_type,
    parent_warehouse_code,
    is_active,
    first_seen_ts,
    last_seen_ts,
    current_record_flag
)
SELECT
    s.source_warehouse_code,
    s.warehouse_name,
    s.warehouse_type,
    s.parent_warehouse_code,
    COALESCE(s.is_active, TRUE),
    NOW(),
    NOW(),
    TRUE
FROM stg.warehouse_master s
WHERE s.etl_batch_id = :etl_batch_id
ON CONFLICT (source_warehouse_code)
DO UPDATE SET
    warehouse_name = EXCLUDED.warehouse_name,
    warehouse_type = EXCLUDED.warehouse_type,
    parent_warehouse_code = EXCLUDED.parent_warehouse_code,
    is_active = EXCLUDED.is_active,
    last_seen_ts = NOW(),
    current_record_flag = TRUE;
