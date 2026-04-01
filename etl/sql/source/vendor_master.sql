-- TODO: Replace with real invs2019 source query
SELECT
    vendor_code AS source_vendor_code,
    vendor_name,
    vendor_type,
    is_active,
    updated_at AS source_updated_ts
FROM your_vendor_master_table;
