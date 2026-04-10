SELECT
    d.DEPT_ID AS source_warehouse_code,
    d.DEPT_NAME AS warehouse_name,
    d.DEPT_TYPE AS warehouse_type,
    CASE WHEN d.HIDE = 'N' THEN true ELSE false END AS is_active,
    NOW() AS source_updated_ts
FROM dept_id d;
