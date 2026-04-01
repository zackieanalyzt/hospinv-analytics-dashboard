INSERT INTO core.dim_vendor (
    source_vendor_code,
    vendor_name,
    vendor_type,
    is_active,
    first_seen_ts,
    last_seen_ts,
    current_record_flag
)
SELECT
    s.source_vendor_code,
    s.vendor_name,
    s.vendor_type,
    COALESCE(s.is_active, TRUE),
    NOW(),
    NOW(),
    TRUE
FROM stg.vendor_master s
WHERE s.etl_batch_id = :etl_batch_id
ON CONFLICT (source_vendor_code)
DO UPDATE SET
    vendor_name = EXCLUDED.vendor_name,
    vendor_type = EXCLUDED.vendor_type,
    is_active = EXCLUDED.is_active,
    last_seen_ts = NOW(),
    current_record_flag = TRUE;
