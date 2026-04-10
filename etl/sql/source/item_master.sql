SELECT
    g.WORKING_CODE AS source_item_code,
    g.DRUG_NAME AS item_name,
    g.DRUG_NAME_KEY AS generic_name,
    g.GROUP_CODE AS item_group,
    g.SUPPLY_TYPE AS item_type,
    g.GROUP_KEY AS item_category,
    g.VEN_FLAG AS ven_class,
    CASE WHEN g.HIDE = 'N' THEN true ELSE false END AS is_active,
    g.SALE_UNIT AS standard_unit,
    g.STRENGTH_UNIT AS strength_text,
    g.DOSAGE_FORM AS dosage_form,
    COALESCE(c.COMPANY_NAME, g.LAST_VENDOR_CODE) AS manufacturer_name,
    NOW() AS source_updated_ts
FROM drug_gn g
LEFT JOIN company c ON g.LAST_VENDOR_CODE = c.COMPANY_CODE;
