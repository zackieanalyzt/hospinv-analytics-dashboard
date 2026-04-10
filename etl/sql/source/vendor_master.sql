SELECT
    c.COMPANY_CODE AS source_vendor_code,
    c.COMPANY_NAME AS vendor_name,
    CASE 
        WHEN c.VENDOR_FLAG = 'Y' AND c.MANUFAC_FLAG = 'Y' THEN 'both'
        WHEN c.VENDOR_FLAG = 'Y' THEN 'vendor'
        WHEN c.MANUFAC_FLAG = 'Y' THEN 'manufacturer'
        ELSE 'other'
    END AS vendor_type,
    CASE WHEN c.HIDE = 'N' THEN true ELSE false END AS is_active,
    NOW() AS source_updated_ts
FROM company c;
