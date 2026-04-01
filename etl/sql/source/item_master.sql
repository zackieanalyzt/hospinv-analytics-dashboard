-- TODO: Replace with real invs2019 source query
SELECT
    item_code AS source_item_code,
    item_name,
    generic_name,
    item_type,
    item_group,
    item_category,
    abc_class,
    ven_class,
    is_active,
    standard_unit,
    strength_text,
    dosage_form,
    manufacturer_name,
    updated_at AS source_updated_ts
FROM your_item_master_table;
