# PRD v1.6 — PostgreSQL DDL Pack

## Project: Hospital Drug & Medical Supply Analytics Dashboard

## Version: 1.6

## Status: Implementation-Ready

## Depends on: PRD v1.0, v1.1, v1.2, v1.3, v1.4, v1.5

---

# 1) Purpose

เอกสารฉบับนี้กำหนด **PostgreSQL analytics schema** สำหรับระบบ Dashboard วิเคราะห์คลังยาและเวชภัณฑ์ของโรงพยาบาล
โดยรองรับสถาปัตยกรรมที่ล็อกไว้แล้ว:

**MariaDB (`invs2019`) → Python ETL / Sync → PostgreSQL → Dashboard App**

เป้าหมายของ DDL pack นี้คือ:

* ใช้เป็นฐานข้อมูล analytics ที่ query เร็วและ maintain ได้
* รองรับ dashboard รุ่นแรกแบบ production-ready
* รองรับ ETL แบบ incremental / rerun / retry
* รองรับการขยายต่อไปยัง forecasting / anomaly / planning

---

# 2) Locked Constraints

ข้อกำหนดต่อไปนี้ถือว่า “ล็อกแล้ว” และห้ามเสนอแนวทางย้อนกลับ:

* Source DB คือ MariaDB ชื่อ `invs2019`
* ห้ามสร้าง table / view / function / procedure / object ใด ๆ บน `invs2019`
* ใช้ `invs2019` ได้เฉพาะ read-only (SELECT)
* Analytics ทั้งหมดต้องทำ **นอก source DB**
* PostgreSQL เป็น analytics database หลัก
* Dashboard App ใช้:

  * Next.js + TypeScript
  * Apache ECharts
  * Tailwind + shadcn/ui
* ETL ใช้ Python
* แนวทาง architecture คือ:

  * **MariaDB (`invs2019`) → Python ETL / Sync → PostgreSQL → Dashboard App**

---

# 3) PostgreSQL Layering Strategy

PostgreSQL แบ่งเป็น 4 schema หลัก:

* `stg` = staging tables จาก source
* `core` = cleansed / conformed analytics model
* `mart` = dashboard-ready summary tables
* `ops` = ETL control / metadata / logging

---

# 4) Naming Convention

## 4.1 Table Naming

* ใช้ `snake_case`
* dimension = `dim_*`
* fact = `fact_*`
* summary = `sum_*`
* ETL / control = `etl_*`

## 4.2 Column Naming

* PK = `<table_name>_id`
* source natural key = `source_<name>`
* date = `<something>_date`
* timestamp = `<something>_ts`
* qty = `numeric(18,4)`
* amount / value = `numeric(18,2)`

---

# 5) Design Principles

## 5.1 Principles

* dashboard ต้อง query จาก PostgreSQL เป็นหลัก
* หลีกเลี่ยง query หนักที่ source
* ทุก metric สำคัญต้อง trace กลับได้ถึง:

  * source key
  * ETL batch
  * snapshot date / transaction date

## 5.2 Modeling Style

ใช้แนวทาง **Pragmatic Hybrid Warehouse**

* staging = table-per-source-domain
* core = reusable analytics model
* mart = denormalized dashboard-serving layer

## 5.3 Time Grain

รองรับอย่างน้อย:

* stock snapshot รายวัน
* movement ราย transaction / รายวัน
* consumption รายวัน / รายเดือน
* expiry status ณ วันประมวลผล
* budget burn รายเดือน

---

# 6) SQL Deployment Pack (Run Order)

ลำดับการ deploy ที่แนะนำ:

1. Create schemas
2. Create extensions
3. Create `ops.*`
4. Create `stg.*`
5. Create `core.dim_*`
6. Seed unknown dimension rows
7. Create `core.fact_*`
8. Create `mart.*`
9. Apply indexes
10. Apply grants

---

# 7) Full PostgreSQL DDL (Single Run Pack)

> หมายเหตุ:
>
> * ไฟล์นี้คือ **single-file deployment pack**
> * สามารถแยกเป็นหลาย `.sql` ภายหลังได้ แต่ตอนนี้ออกแบบมาให้ **copy ครั้งเดียว**
> * ถ้ามี table บางตัวที่ยังไม่ใช้ใน phase 1 ก็ปล่อยไว้ได้ ไม่เสียหาย

```sql
/* =========================================================
   PRD v1.6 — PostgreSQL DDL Pack
   Project: Hospital Drug & Medical Supply Analytics Dashboard
   ========================================================= */

/* =========================================================
   01) SCHEMAS
   ========================================================= */
CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE SCHEMA IF NOT EXISTS ops;

/* =========================================================
   02) EXTENSIONS
   ========================================================= */
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS btree_gin;

/* =========================================================
   03) OPS LAYER
   ========================================================= */

/* 03.01 ops.etl_batch */
CREATE TABLE IF NOT EXISTS ops.etl_batch (
    etl_batch_id          BIGSERIAL PRIMARY KEY,
    pipeline_name         VARCHAR(100) NOT NULL,
    source_system         VARCHAR(100) NOT NULL DEFAULT 'invs2019',
    batch_type            VARCHAR(50) NOT NULL,   -- full / incremental / repair / backfill
    batch_status          VARCHAR(30) NOT NULL,   -- running / success / failed / partial
    started_ts            TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_ts              TIMESTAMP NULL,
    triggered_by          VARCHAR(100) NULL,
    watermark_from_ts     TIMESTAMP NULL,
    watermark_to_ts       TIMESTAMP NULL,
    note                  TEXT NULL,
    created_ts            TIMESTAMP NOT NULL DEFAULT NOW()
);

/* 03.02 ops.etl_table_run */
CREATE TABLE IF NOT EXISTS ops.etl_table_run (
    etl_table_run_id      BIGSERIAL PRIMARY KEY,
    etl_batch_id          BIGINT NOT NULL REFERENCES ops.etl_batch(etl_batch_id),
    target_schema         VARCHAR(50) NOT NULL,
    target_table          VARCHAR(100) NOT NULL,
    source_table          VARCHAR(100) NOT NULL,
    load_mode             VARCHAR(30) NOT NULL,   -- truncate_insert / upsert / append
    row_extracted         BIGINT NOT NULL DEFAULT 0,
    row_inserted          BIGINT NOT NULL DEFAULT 0,
    row_updated           BIGINT NOT NULL DEFAULT 0,
    row_deleted           BIGINT NOT NULL DEFAULT 0,
    row_rejected          BIGINT NOT NULL DEFAULT 0,
    run_status            VARCHAR(30) NOT NULL,   -- running / success / failed
    started_ts            TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_ts              TIMESTAMP NULL,
    error_message         TEXT NULL
);

/* 03.03 ops.etl_data_freshness */
CREATE TABLE IF NOT EXISTS ops.etl_data_freshness (
    data_freshness_id     BIGSERIAL PRIMARY KEY,
    data_domain           VARCHAR(100) NOT NULL,
    table_name            VARCHAR(150) NOT NULL,
    last_success_batch_id BIGINT NULL REFERENCES ops.etl_batch(etl_batch_id),
    last_data_ts          TIMESTAMP NULL,
    last_checked_ts       TIMESTAMP NOT NULL DEFAULT NOW(),
    freshness_status      VARCHAR(30) NOT NULL DEFAULT 'unknown',
    note                  TEXT NULL,
    UNIQUE (data_domain, table_name)
);

/* =========================================================
   04) STAGING LAYER
   ========================================================= */

/* 04.01 stg.item_master */
CREATE TABLE IF NOT EXISTS stg.item_master (
    stg_item_master_id    BIGSERIAL PRIMARY KEY,
    etl_batch_id          BIGINT NOT NULL REFERENCES ops.etl_batch(etl_batch_id),
    source_pk_hash        VARCHAR(64) NOT NULL,
    source_item_code      VARCHAR(100) NOT NULL,
    item_name             TEXT NOT NULL,
    generic_name          TEXT NULL,
    item_type             VARCHAR(50) NULL,
    item_group            VARCHAR(100) NULL,
    item_category         VARCHAR(100) NULL,
    abc_class             VARCHAR(10) NULL,
    ven_class             VARCHAR(10) NULL,
    is_active             BOOLEAN NULL,
    standard_unit         VARCHAR(50) NULL,
    strength_text         VARCHAR(100) NULL,
    dosage_form           VARCHAR(100) NULL,
    manufacturer_name     TEXT NULL,
    source_updated_ts     TIMESTAMP NULL,
    extracted_ts          TIMESTAMP NOT NULL DEFAULT NOW()
);

/* 04.02 stg.warehouse_master */
CREATE TABLE IF NOT EXISTS stg.warehouse_master (
    stg_warehouse_master_id BIGSERIAL PRIMARY KEY,
    etl_batch_id            BIGINT NOT NULL REFERENCES ops.etl_batch(etl_batch_id),
    source_pk_hash          VARCHAR(64) NOT NULL,
    source_warehouse_code   VARCHAR(100) NOT NULL,
    warehouse_name          TEXT NOT NULL,
    warehouse_type          VARCHAR(50) NULL,
    parent_warehouse_code   VARCHAR(100) NULL,
    is_active               BOOLEAN NULL,
    source_updated_ts       TIMESTAMP NULL,
    extracted_ts            TIMESTAMP NOT NULL DEFAULT NOW()
);

/* 04.03 stg.vendor_master */
CREATE TABLE IF NOT EXISTS stg.vendor_master (
    stg_vendor_master_id   BIGSERIAL PRIMARY KEY,
    etl_batch_id           BIGINT NOT NULL REFERENCES ops.etl_batch(etl_batch_id),
    source_pk_hash         VARCHAR(64) NOT NULL,
    source_vendor_code     VARCHAR(100) NOT NULL,
    vendor_name            TEXT NOT NULL,
    vendor_type            VARCHAR(50) NULL,
    is_active              BOOLEAN NULL,
    source_updated_ts      TIMESTAMP NULL,
    extracted_ts           TIMESTAMP NOT NULL DEFAULT NOW()
);

/* 04.04 stg.stock_balance */
CREATE TABLE IF NOT EXISTS stg.stock_balance (
    stg_stock_balance_id   BIGSERIAL PRIMARY KEY,
    etl_batch_id           BIGINT NOT NULL REFERENCES ops.etl_batch(etl_batch_id),
    source_pk_hash         VARCHAR(64) NOT NULL,
    snapshot_date          DATE NOT NULL,
    source_item_code       VARCHAR(100) NOT NULL,
    source_warehouse_code  VARCHAR(100) NOT NULL,
    qty_on_hand            NUMERIC(18,4) NOT NULL DEFAULT 0,
    avg_unit_cost          NUMERIC(18,6) NULL,
    stock_value            NUMERIC(18,2) NULL,
    source_updated_ts      TIMESTAMP NULL,
    extracted_ts           TIMESTAMP NOT NULL DEFAULT NOW()
);

/* 04.05 stg.stock_lot_balance */
CREATE TABLE IF NOT EXISTS stg.stock_lot_balance (
    stg_stock_lot_balance_id BIGSERIAL PRIMARY KEY,
    etl_batch_id             BIGINT NOT NULL REFERENCES ops.etl_batch(etl_batch_id),
    source_pk_hash           VARCHAR(64) NOT NULL,
    snapshot_date            DATE NOT NULL,
    source_item_code         VARCHAR(100) NOT NULL,
    source_warehouse_code    VARCHAR(100) NOT NULL,
    lot_no                   VARCHAR(100) NULL,
    expiry_date              DATE NULL,
    qty_on_hand              NUMERIC(18,4) NOT NULL DEFAULT 0,
    avg_unit_cost            NUMERIC(18,6) NULL,
    stock_value              NUMERIC(18,2) NULL,
    source_updated_ts        TIMESTAMP NULL,
    extracted_ts             TIMESTAMP NOT NULL DEFAULT NOW()
);

/* 04.06 stg.inventory_movement */
CREATE TABLE IF NOT EXISTS stg.inventory_movement (
    stg_inventory_movement_id BIGSERIAL PRIMARY KEY,
    etl_batch_id              BIGINT NOT NULL REFERENCES ops.etl_batch(etl_batch_id),
    source_pk_hash            VARCHAR(64) NOT NULL,
    source_txn_id             VARCHAR(100) NOT NULL,
    txn_date                  DATE NOT NULL,
    txn_ts                    TIMESTAMP NULL,
    source_item_code          VARCHAR(100) NOT NULL,
    source_warehouse_code     VARCHAR(100) NOT NULL,
    movement_type             VARCHAR(50) NOT NULL,
    ref_doc_no                VARCHAR(100) NULL,
    ref_doc_type              VARCHAR(50) NULL,
    lot_no                    VARCHAR(100) NULL,
    expiry_date               DATE NULL,
    qty                       NUMERIC(18,4) NOT NULL,
    unit_cost                 NUMERIC(18,6) NULL,
    line_value                NUMERIC(18,2) NULL,
    source_vendor_code        VARCHAR(100) NULL,
    source_updated_ts         TIMESTAMP NULL,
    extracted_ts              TIMESTAMP NOT NULL DEFAULT NOW()
);

/* 04.07 stg.purchase_order_line */
CREATE TABLE IF NOT EXISTS stg.purchase_order_line (
    stg_purchase_order_line_id BIGSERIAL PRIMARY KEY,
    etl_batch_id               BIGINT NOT NULL REFERENCES ops.etl_batch(etl_batch_id),
    source_pk_hash             VARCHAR(64) NOT NULL,
    po_no                      VARCHAR(100) NOT NULL,
    po_date                    DATE NOT NULL,
    source_item_code           VARCHAR(100) NOT NULL,
    source_vendor_code         VARCHAR(100) NULL,
    ordered_qty                NUMERIC(18,4) NOT NULL DEFAULT 0,
    ordered_unit_cost          NUMERIC(18,6) NULL,
    ordered_value              NUMERIC(18,2) NULL,
    po_status                  VARCHAR(50) NULL,
    source_updated_ts          TIMESTAMP NULL,
    extracted_ts               TIMESTAMP NOT NULL DEFAULT NOW()
);

/* 04.08 stg.goods_receipt_line */
CREATE TABLE IF NOT EXISTS stg.goods_receipt_line (
    stg_goods_receipt_line_id BIGSERIAL PRIMARY KEY,
    etl_batch_id              BIGINT NOT NULL REFERENCES ops.etl_batch(etl_batch_id),
    source_pk_hash            VARCHAR(64) NOT NULL,
    gr_no                     VARCHAR(100) NOT NULL,
    gr_date                   DATE NOT NULL,
    po_no                     VARCHAR(100) NULL,
    source_item_code          VARCHAR(100) NOT NULL,
    source_warehouse_code     VARCHAR(100) NOT NULL,
    source_vendor_code        VARCHAR(100) NULL,
    lot_no                    VARCHAR(100) NULL,
    expiry_date               DATE NULL,
    received_qty              NUMERIC(18,4) NOT NULL DEFAULT 0,
    received_unit_cost        NUMERIC(18,6) NULL,
    received_value            NUMERIC(18,2) NULL,
    source_updated_ts         TIMESTAMP NULL,
    extracted_ts              TIMESTAMP NOT NULL DEFAULT NOW()
);

/* =========================================================
   05) CORE DIMENSIONS
   ========================================================= */

/* 05.01 core.dim_date */
CREATE TABLE IF NOT EXISTS core.dim_date (
    date_id                INTEGER PRIMARY KEY, -- YYYYMMDD
    full_date              DATE NOT NULL UNIQUE,
    day_of_month           INTEGER NOT NULL,
    month_no               INTEGER NOT NULL,
    month_name_en          VARCHAR(20) NOT NULL,
    quarter_no             INTEGER NOT NULL,
    year_no                INTEGER NOT NULL,
    week_no                INTEGER NOT NULL,
    day_name_en            VARCHAR(20) NOT NULL,
    is_weekend             BOOLEAN NOT NULL,
    month_start_date       DATE NOT NULL,
    month_end_date         DATE NOT NULL,
    quarter_start_date     DATE NOT NULL,
    quarter_end_date       DATE NOT NULL,
    year_start_date        DATE NOT NULL,
    year_end_date          DATE NOT NULL
);

/* 05.02 core.dim_item */
CREATE TABLE IF NOT EXISTS core.dim_item (
    dim_item_id            BIGSERIAL PRIMARY KEY,
    source_item_code       VARCHAR(100) NOT NULL UNIQUE,
    item_name              TEXT NOT NULL,
    generic_name           TEXT NULL,
    item_type              VARCHAR(50) NULL,
    item_group             VARCHAR(100) NULL,
    item_category          VARCHAR(100) NULL,
    abc_class              VARCHAR(10) NULL,
    ven_class              VARCHAR(10) NULL,
    standard_unit          VARCHAR(50) NULL,
    strength_text          VARCHAR(100) NULL,
    dosage_form            VARCHAR(100) NULL,
    manufacturer_name      TEXT NULL,
    is_active              BOOLEAN NOT NULL DEFAULT TRUE,
    is_drug                BOOLEAN NOT NULL DEFAULT FALSE,
    is_supply              BOOLEAN NOT NULL DEFAULT FALSE,
    first_seen_ts          TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen_ts           TIMESTAMP NOT NULL DEFAULT NOW(),
    current_record_flag    BOOLEAN NOT NULL DEFAULT TRUE
);

/* 05.03 core.dim_warehouse */
CREATE TABLE IF NOT EXISTS core.dim_warehouse (
    dim_warehouse_id       BIGSERIAL PRIMARY KEY,
    source_warehouse_code  VARCHAR(100) NOT NULL UNIQUE,
    warehouse_name         TEXT NOT NULL,
    warehouse_type         VARCHAR(50) NULL,
    parent_warehouse_code  VARCHAR(100) NULL,
    is_active              BOOLEAN NOT NULL DEFAULT TRUE,
    first_seen_ts          TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen_ts           TIMESTAMP NOT NULL DEFAULT NOW(),
    current_record_flag    BOOLEAN NOT NULL DEFAULT TRUE
);

/* 05.04 core.dim_vendor */
CREATE TABLE IF NOT EXISTS core.dim_vendor (
    dim_vendor_id          BIGSERIAL PRIMARY KEY,
    source_vendor_code     VARCHAR(100) NOT NULL UNIQUE,
    vendor_name            TEXT NOT NULL,
    vendor_type            VARCHAR(50) NULL,
    is_active              BOOLEAN NOT NULL DEFAULT TRUE,
    first_seen_ts          TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen_ts           TIMESTAMP NOT NULL DEFAULT NOW(),
    current_record_flag    BOOLEAN NOT NULL DEFAULT TRUE
);

/* =========================================================
   06) UNKNOWN DIMENSION SEED
   ========================================================= */
INSERT INTO core.dim_item (
    dim_item_id, source_item_code, item_name, is_active, is_drug, is_supply
)
VALUES
    (0, 'UNKNOWN', 'Unknown Item', FALSE, FALSE, FALSE)
ON CONFLICT (source_item_code) DO NOTHING;

INSERT INTO core.dim_warehouse (
    dim_warehouse_id, source_warehouse_code, warehouse_name, is_active
)
VALUES
    (0, 'UNKNOWN', 'Unknown Warehouse', FALSE)
ON CONFLICT (source_warehouse_code) DO NOTHING;

INSERT INTO core.dim_vendor (
    dim_vendor_id, source_vendor_code, vendor_name, is_active
)
VALUES
    (0, 'UNKNOWN', 'Unknown Vendor', FALSE)
ON CONFLICT (source_vendor_code) DO NOTHING;

/* reset sequences after manual id=0 inserts */
SELECT setval(pg_get_serial_sequence('core.dim_item', 'dim_item_id'),
              GREATEST((SELECT MAX(dim_item_id) FROM core.dim_item), 1), true);

SELECT setval(pg_get_serial_sequence('core.dim_warehouse', 'dim_warehouse_id'),
              GREATEST((SELECT MAX(dim_warehouse_id) FROM core.dim_warehouse), 1), true);

SELECT setval(pg_get_serial_sequence('core.dim_vendor', 'dim_vendor_id'),
              GREATEST((SELECT MAX(dim_vendor_id) FROM core.dim_vendor), 1), true);

/* =========================================================
   07) CORE FACTS
   ========================================================= */

/* 07.01 core.fact_inventory_movement */
CREATE TABLE IF NOT EXISTS core.fact_inventory_movement (
    fact_inventory_movement_id BIGSERIAL PRIMARY KEY,
    etl_batch_id               BIGINT NOT NULL REFERENCES ops.etl_batch(etl_batch_id),

    source_txn_id              VARCHAR(100) NOT NULL,
    ref_doc_no                 VARCHAR(100) NULL,
    ref_doc_type               VARCHAR(50) NULL,

    txn_date                   DATE NOT NULL,
    txn_ts                     TIMESTAMP NULL,
    txn_date_id                INTEGER NOT NULL REFERENCES core.dim_date(date_id),

    dim_item_id                BIGINT NOT NULL REFERENCES core.dim_item(dim_item_id),
    dim_warehouse_id           BIGINT NOT NULL REFERENCES core.dim_warehouse(dim_warehouse_id),
    dim_vendor_id              BIGINT NULL REFERENCES core.dim_vendor(dim_vendor_id),

    movement_type              VARCHAR(50) NOT NULL,
    movement_direction         VARCHAR(10) NOT NULL, -- in / out / neutral

    lot_no                     VARCHAR(100) NULL,
    expiry_date                DATE NULL,

    qty                        NUMERIC(18,4) NOT NULL,
    signed_qty                 NUMERIC(18,4) NOT NULL,
    unit_cost                  NUMERIC(18,6) NULL,
    line_value                 NUMERIC(18,2) NULL,
    signed_value               NUMERIC(18,2) NULL,

    source_row_hash            VARCHAR(64) NOT NULL,
    created_ts                 TIMESTAMP NOT NULL DEFAULT NOW()
);

/* 07.02 core.fact_stock_snapshot */
CREATE TABLE IF NOT EXISTS core.fact_stock_snapshot (
    fact_stock_snapshot_id BIGSERIAL PRIMARY KEY,
    etl_batch_id           BIGINT NOT NULL REFERENCES ops.etl_batch(etl_batch_id),

    snapshot_date          DATE NOT NULL,
    snapshot_date_id       INTEGER NOT NULL REFERENCES core.dim_date(date_id),

    dim_item_id            BIGINT NOT NULL REFERENCES core.dim_item(dim_item_id),
    dim_warehouse_id       BIGINT NOT NULL REFERENCES core.dim_warehouse(dim_warehouse_id),

    qty_on_hand            NUMERIC(18,4) NOT NULL DEFAULT 0,
    avg_unit_cost          NUMERIC(18,6) NULL,
    stock_value            NUMERIC(18,2) NULL,

    stock_status           VARCHAR(30) NULL,
    created_ts             TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE (snapshot_date, dim_item_id, dim_warehouse_id)
);

/* 07.03 core.fact_stock_lot_snapshot */
CREATE TABLE IF NOT EXISTS core.fact_stock_lot_snapshot (
    fact_stock_lot_snapshot_id BIGSERIAL PRIMARY KEY,
    etl_batch_id               BIGINT NOT NULL REFERENCES ops.etl_batch(etl_batch_id),

    snapshot_date              DATE NOT NULL,
    snapshot_date_id           INTEGER NOT NULL REFERENCES core.dim_date(date_id),

    dim_item_id                BIGINT NOT NULL REFERENCES core.dim_item(dim_item_id),
    dim_warehouse_id           BIGINT NOT NULL REFERENCES core.dim_warehouse(dim_warehouse_id),

    lot_no                     VARCHAR(100) NULL,
    expiry_date                DATE NULL,

    qty_on_hand                NUMERIC(18,4) NOT NULL DEFAULT 0,
    avg_unit_cost              NUMERIC(18,6) NULL,
    stock_value                NUMERIC(18,2) NULL,

    days_to_expiry             INTEGER NULL,
    expiry_status              VARCHAR(30) NULL,

    created_ts                 TIMESTAMP NOT NULL DEFAULT NOW()
);

/* 07.04 core.fact_purchase_order_line */
CREATE TABLE IF NOT EXISTS core.fact_purchase_order_line (
    fact_purchase_order_line_id BIGSERIAL PRIMARY KEY,
    etl_batch_id                BIGINT NOT NULL REFERENCES ops.etl_batch(etl_batch_id),

    po_no                       VARCHAR(100) NOT NULL,
    po_date                     DATE NOT NULL,
    po_date_id                  INTEGER NOT NULL REFERENCES core.dim_date(date_id),

    dim_item_id                 BIGINT NOT NULL REFERENCES core.dim_item(dim_item_id),
    dim_vendor_id               BIGINT NULL REFERENCES core.dim_vendor(dim_vendor_id),

    ordered_qty                 NUMERIC(18,4) NOT NULL DEFAULT 0,
    ordered_unit_cost           NUMERIC(18,6) NULL,
    ordered_value               NUMERIC(18,2) NULL,
    po_status                   VARCHAR(50) NULL,

    source_row_hash             VARCHAR(64) NOT NULL,
    created_ts                  TIMESTAMP NOT NULL DEFAULT NOW()
);

/* 07.05 core.fact_goods_receipt_line */
CREATE TABLE IF NOT EXISTS core.fact_goods_receipt_line (
    fact_goods_receipt_line_id BIGSERIAL PRIMARY KEY,
    etl_batch_id               BIGINT NOT NULL REFERENCES ops.etl_batch(etl_batch_id),

    gr_no                      VARCHAR(100) NOT NULL,
    gr_date                    DATE NOT NULL,
    gr_date_id                 INTEGER NOT NULL REFERENCES core.dim_date(date_id),

    po_no                      VARCHAR(100) NULL,

    dim_item_id                BIGINT NOT NULL REFERENCES core.dim_item(dim_item_id),
    dim_warehouse_id           BIGINT NOT NULL REFERENCES core.dim_warehouse(dim_warehouse_id),
    dim_vendor_id              BIGINT NULL REFERENCES core.dim_vendor(dim_vendor_id),

    lot_no                     VARCHAR(100) NULL,
    expiry_date                DATE NULL,

    received_qty               NUMERIC(18,4) NOT NULL DEFAULT 0,
    received_unit_cost         NUMERIC(18,6) NULL,
    received_value             NUMERIC(18,2) NULL,

    source_row_hash            VARCHAR(64) NOT NULL,
    created_ts                 TIMESTAMP NOT NULL DEFAULT NOW()
);

/* =========================================================
   08) MART TABLES
   ========================================================= */

/* 08.01 mart.sum_inventory_daily */
CREATE TABLE IF NOT EXISTS mart.sum_inventory_daily (
    summary_date              DATE PRIMARY KEY,
    total_sku_count           INTEGER NOT NULL DEFAULT 0,
    active_sku_count          INTEGER NOT NULL DEFAULT 0,
    warehouse_count           INTEGER NOT NULL DEFAULT 0,
    total_qty_on_hand         NUMERIC(18,4) NOT NULL DEFAULT 0,
    total_stock_value         NUMERIC(18,2) NOT NULL DEFAULT 0,
    zero_stock_sku_count      INTEGER NOT NULL DEFAULT 0,
    negative_stock_sku_count  INTEGER NOT NULL DEFAULT 0,
    near_expiry_sku_count     INTEGER NOT NULL DEFAULT 0,
    expired_sku_count         INTEGER NOT NULL DEFAULT 0,
    dead_stock_sku_count      INTEGER NOT NULL DEFAULT 0,
    created_ts                TIMESTAMP NOT NULL DEFAULT NOW()
);

/* 08.02 mart.sum_stock_position_daily */
CREATE TABLE IF NOT EXISTS mart.sum_stock_position_daily (
    summary_date            DATE NOT NULL,
    dim_item_id             BIGINT NOT NULL REFERENCES core.dim_item(dim_item_id),
    dim_warehouse_id        BIGINT NOT NULL REFERENCES core.dim_warehouse(dim_warehouse_id),

    qty_on_hand             NUMERIC(18,4) NOT NULL DEFAULT 0,
    avg_unit_cost           NUMERIC(18,6) NULL,
    stock_value             NUMERIC(18,2) NULL,

    stock_status            VARCHAR(30) NULL,
    days_of_stock_est       NUMERIC(18,2) NULL,
    reorder_flag            BOOLEAN NOT NULL DEFAULT FALSE,
    overstock_flag          BOOLEAN NOT NULL DEFAULT FALSE,

    created_ts              TIMESTAMP NOT NULL DEFAULT NOW(),

    PRIMARY KEY (summary_date, dim_item_id, dim_warehouse_id)
);

/* 08.03 mart.sum_expiry_daily */
CREATE TABLE IF NOT EXISTS mart.sum_expiry_daily (
    sum_expiry_daily_id     BIGSERIAL PRIMARY KEY,
    summary_date            DATE NOT NULL,
    dim_item_id             BIGINT NOT NULL REFERENCES core.dim_item(dim_item_id),
    dim_warehouse_id        BIGINT NOT NULL REFERENCES core.dim_warehouse(dim_warehouse_id),

    lot_no                  VARCHAR(100) NULL,
    expiry_date             DATE NULL,
    days_to_expiry          INTEGER NULL,
    expiry_status           VARCHAR(30) NOT NULL,

    qty_on_hand             NUMERIC(18,4) NOT NULL DEFAULT 0,
    stock_value             NUMERIC(18,2) NULL,

    created_ts              TIMESTAMP NOT NULL DEFAULT NOW()
);

/* 08.04 mart.sum_consumption_daily */
CREATE TABLE IF NOT EXISTS mart.sum_consumption_daily (
    summary_date              DATE NOT NULL,
    dim_item_id               BIGINT NOT NULL REFERENCES core.dim_item(dim_item_id),
    dim_warehouse_id          BIGINT NOT NULL REFERENCES core.dim_warehouse(dim_warehouse_id),

    issue_qty                 NUMERIC(18,4) NOT NULL DEFAULT 0,
    issue_value               NUMERIC(18,2) NOT NULL DEFAULT 0,
    avg_daily_consumption_30d NUMERIC(18,4) NULL,
    avg_daily_consumption_90d NUMERIC(18,4) NULL,

    created_ts                TIMESTAMP NOT NULL DEFAULT NOW(),

    PRIMARY KEY (summary_date, dim_item_id, dim_warehouse_id)
);

/* 08.05 mart.sum_consumption_monthly */
CREATE TABLE IF NOT EXISTS mart.sum_consumption_monthly (
    year_month              INTEGER NOT NULL,
    dim_item_id             BIGINT NOT NULL REFERENCES core.dim_item(dim_item_id),
    dim_warehouse_id        BIGINT NOT NULL REFERENCES core.dim_warehouse(dim_warehouse_id),

    issue_qty               NUMERIC(18,4) NOT NULL DEFAULT 0,
    issue_value             NUMERIC(18,2) NOT NULL DEFAULT 0,
    movement_days           INTEGER NOT NULL DEFAULT 0,

    created_ts              TIMESTAMP NOT NULL DEFAULT NOW(),

    PRIMARY KEY (year_month, dim_item_id, dim_warehouse_id)
);

/* 08.06 mart.sum_movement_daily */
CREATE TABLE IF NOT EXISTS mart.sum_movement_daily (
    summary_date            DATE NOT NULL,
    dim_item_id             BIGINT NOT NULL REFERENCES core.dim_item(dim_item_id),
    dim_warehouse_id        BIGINT NOT NULL REFERENCES core.dim_warehouse(dim_warehouse_id),
    movement_type           VARCHAR(50) NOT NULL,

    movement_qty            NUMERIC(18,4) NOT NULL DEFAULT 0,
    movement_value          NUMERIC(18,2) NOT NULL DEFAULT 0,
    txn_count               INTEGER NOT NULL DEFAULT 0,

    created_ts              TIMESTAMP NOT NULL DEFAULT NOW(),

    PRIMARY KEY (summary_date, dim_item_id, dim_warehouse_id, movement_type)
);

/* 08.07 mart.sum_dead_stock_daily */
CREATE TABLE IF NOT EXISTS mart.sum_dead_stock_daily (
    summary_date            DATE NOT NULL,
    dim_item_id             BIGINT NOT NULL REFERENCES core.dim_item(dim_item_id),
    dim_warehouse_id        BIGINT NOT NULL REFERENCES core.dim_warehouse(dim_warehouse_id),

    qty_on_hand             NUMERIC(18,4) NOT NULL DEFAULT 0,
    stock_value             NUMERIC(18,2) NULL,
    last_issue_date         DATE NULL,
    days_since_last_issue   INTEGER NULL,
    dead_stock_flag         BOOLEAN NOT NULL DEFAULT FALSE,
    slow_moving_flag        BOOLEAN NOT NULL DEFAULT FALSE,

    created_ts              TIMESTAMP NOT NULL DEFAULT NOW(),

    PRIMARY KEY (summary_date, dim_item_id, dim_warehouse_id)
);

/* 08.08 mart.sum_procurement_monthly */
CREATE TABLE IF NOT EXISTS mart.sum_procurement_monthly (
    sum_procurement_monthly_id BIGSERIAL PRIMARY KEY,
    year_month              INTEGER NOT NULL,
    dim_item_id             BIGINT NOT NULL REFERENCES core.dim_item(dim_item_id),
    dim_vendor_id           BIGINT NULL REFERENCES core.dim_vendor(dim_vendor_id),

    ordered_qty             NUMERIC(18,4) NOT NULL DEFAULT 0,
    ordered_value           NUMERIC(18,2) NOT NULL DEFAULT 0,
    received_qty            NUMERIC(18,4) NOT NULL DEFAULT 0,
    received_value          NUMERIC(18,2) NOT NULL DEFAULT 0,
    po_count                INTEGER NOT NULL DEFAULT 0,
    gr_count                INTEGER NOT NULL DEFAULT 0,

    created_ts              TIMESTAMP NOT NULL DEFAULT NOW()
);

/* 08.09 mart.sum_budget_burn_monthly */
CREATE TABLE IF NOT EXISTS mart.sum_budget_burn_monthly (
    year_month              INTEGER PRIMARY KEY,
    budget_amount           NUMERIC(18,2) NULL,
    actual_spend_amount     NUMERIC(18,2) NOT NULL DEFAULT 0,
    variance_amount         NUMERIC(18,2) NULL,
    burn_rate_pct           NUMERIC(10,2) NULL,
    ytd_actual_spend        NUMERIC(18,2) NULL,
    created_ts              TIMESTAMP NOT NULL DEFAULT NOW()
);

/* =========================================================
   09) INDEXES
   ========================================================= */

/* OPS */
CREATE INDEX IF NOT EXISTS idx_etl_batch_pipeline_started
ON ops.etl_batch (pipeline_name, started_ts DESC);

CREATE INDEX IF NOT EXISTS idx_etl_table_run_batch
ON ops.etl_table_run (etl_batch_id);

CREATE INDEX IF NOT EXISTS idx_etl_table_run_target
ON ops.etl_table_run (target_schema, target_table, started_ts DESC);

/* STG */
CREATE UNIQUE INDEX IF NOT EXISTS uq_stg_item_master_batch_hash
ON stg.item_master (etl_batch_id, source_pk_hash);

CREATE INDEX IF NOT EXISTS idx_stg_item_master_code
ON stg.item_master (source_item_code);

CREATE UNIQUE INDEX IF NOT EXISTS uq_stg_warehouse_master_batch_hash
ON stg.warehouse_master (etl_batch_id, source_pk_hash);

CREATE INDEX IF NOT EXISTS idx_stg_warehouse_master_code
ON stg.warehouse_master (source_warehouse_code);

CREATE UNIQUE INDEX IF NOT EXISTS uq_stg_vendor_master_batch_hash
ON stg.vendor_master (etl_batch_id, source_pk_hash);

CREATE INDEX IF NOT EXISTS idx_stg_vendor_master_code
ON stg.vendor_master (source_vendor_code);

CREATE UNIQUE INDEX IF NOT EXISTS uq_stg_stock_balance_batch_hash
ON stg.stock_balance (etl_batch_id, source_pk_hash);

CREATE INDEX IF NOT EXISTS idx_stg_stock_balance_snapshot
ON stg.stock_balance (snapshot_date);

CREATE INDEX IF NOT EXISTS idx_stg_stock_balance_item_wh
ON stg.stock_balance (source_item_code, source_warehouse_code);

CREATE UNIQUE INDEX IF NOT EXISTS uq_stg_stock_lot_balance_batch_hash
ON stg.stock_lot_balance (etl_batch_id, source_pk_hash);

CREATE INDEX IF NOT EXISTS idx_stg_stock_lot_balance_snapshot
ON stg.stock_lot_balance (snapshot_date);

CREATE INDEX IF NOT EXISTS idx_stg_stock_lot_balance_expiry
ON stg.stock_lot_balance (expiry_date);

CREATE UNIQUE INDEX IF NOT EXISTS uq_stg_inventory_movement_batch_hash
ON stg.inventory_movement (etl_batch_id, source_pk_hash);

CREATE INDEX IF NOT EXISTS idx_stg_inventory_movement_txn_date
ON stg.inventory_movement (txn_date);

CREATE INDEX IF NOT EXISTS idx_stg_inventory_movement_item_wh
ON stg.inventory_movement (source_item_code, source_warehouse_code);

CREATE INDEX IF NOT EXISTS idx_stg_inventory_movement_type
ON stg.inventory_movement (movement_type);

CREATE UNIQUE INDEX IF NOT EXISTS uq_stg_purchase_order_line_batch_hash
ON stg.purchase_order_line (etl_batch_id, source_pk_hash);

CREATE INDEX IF NOT EXISTS idx_stg_purchase_order_line_po_date
ON stg.purchase_order_line (po_date);

CREATE INDEX IF NOT EXISTS idx_stg_purchase_order_line_item
ON stg.purchase_order_line (source_item_code);

CREATE UNIQUE INDEX IF NOT EXISTS uq_stg_goods_receipt_line_batch_hash
ON stg.goods_receipt_line (etl_batch_id, source_pk_hash);

CREATE INDEX IF NOT EXISTS idx_stg_goods_receipt_line_gr_date
ON stg.goods_receipt_line (gr_date);

CREATE INDEX IF NOT EXISTS idx_stg_goods_receipt_line_item_wh
ON stg.goods_receipt_line (source_item_code, source_warehouse_code);

/* CORE */
CREATE INDEX IF NOT EXISTS idx_dim_date_year_month
ON core.dim_date (year_no, month_no);

CREATE INDEX IF NOT EXISTS idx_dim_item_type
ON core.dim_item (item_type);

CREATE INDEX IF NOT EXISTS idx_dim_item_group
ON core.dim_item (item_group);

CREATE INDEX IF NOT EXISTS idx_dim_item_category
ON core.dim_item (item_category);

CREATE INDEX IF NOT EXISTS idx_dim_item_abc_ven
ON core.dim_item (abc_class, ven_class);

CREATE INDEX IF NOT EXISTS idx_dim_warehouse_type
ON core.dim_warehouse (warehouse_type);

CREATE INDEX IF NOT EXISTS idx_dim_vendor_type
ON core.dim_vendor (vendor_type);

CREATE INDEX IF NOT EXISTS idx_fact_inventory_movement_date
ON core.fact_inventory_movement (txn_date);

CREATE INDEX IF NOT EXISTS idx_fact_inventory_movement_item
ON core.fact_inventory_movement (dim_item_id);

CREATE INDEX IF NOT EXISTS idx_fact_inventory_movement_wh
ON core.fact_inventory_movement (dim_warehouse_id);

CREATE INDEX IF NOT EXISTS idx_fact_inventory_movement_type
ON core.fact_inventory_movement (movement_type);

CREATE INDEX IF NOT EXISTS idx_fact_inventory_movement_item_date
ON core.fact_inventory_movement (dim_item_id, txn_date);

CREATE INDEX IF NOT EXISTS idx_fact_inventory_movement_wh_date
ON core.fact_inventory_movement (dim_warehouse_id, txn_date);

CREATE INDEX IF NOT EXISTS idx_fact_stock_snapshot_date
ON core.fact_stock_snapshot (snapshot_date);

CREATE INDEX IF NOT EXISTS idx_fact_stock_snapshot_item
ON core.fact_stock_snapshot (dim_item_id);

CREATE INDEX IF NOT EXISTS idx_fact_stock_snapshot_wh
ON core.fact_stock_snapshot (dim_warehouse_id);

CREATE INDEX IF NOT EXISTS idx_fact_stock_lot_snapshot_date
ON core.fact_stock_lot_snapshot (snapshot_date);

CREATE INDEX IF NOT EXISTS idx_fact_stock_lot_snapshot_expiry
ON core.fact_stock_lot_snapshot (expiry_date);

CREATE INDEX IF NOT EXISTS idx_fact_stock_lot_snapshot_expiry_status
ON core.fact_stock_lot_snapshot (expiry_status);

CREATE INDEX IF NOT EXISTS idx_fact_stock_lot_snapshot_item
ON core.fact_stock_lot_snapshot (dim_item_id);

CREATE INDEX IF NOT EXISTS idx_fact_purchase_order_line_po_date
ON core.fact_purchase_order_line (po_date);

CREATE INDEX IF NOT EXISTS idx_fact_purchase_order_line_item
ON core.fact_purchase_order_line (dim_item_id);

CREATE INDEX IF NOT EXISTS idx_fact_goods_receipt_line_gr_date
ON core.fact_goods_receipt_line (gr_date);

CREATE INDEX IF NOT EXISTS idx_fact_goods_receipt_line_item
ON core.fact_goods_receipt_line (dim_item_id);

CREATE INDEX IF NOT EXISTS idx_fact_goods_receipt_line_wh
ON core.fact_goods_receipt_line (dim_warehouse_id);

/* MART */
CREATE INDEX IF NOT EXISTS idx_sum_inventory_daily_date
ON mart.sum_inventory_daily (summary_date DESC);

CREATE INDEX IF NOT EXISTS idx_sum_stock_position_daily_wh
ON mart.sum_stock_position_daily (dim_warehouse_id);

CREATE INDEX IF NOT EXISTS idx_sum_stock_position_daily_item
ON mart.sum_stock_position_daily (dim_item_id);

CREATE INDEX IF NOT EXISTS idx_sum_stock_position_daily_flags
ON mart.sum_stock_position_daily (reorder_flag, overstock_flag);

CREATE UNIQUE INDEX IF NOT EXISTS uq_sum_expiry_daily_business
ON mart.sum_expiry_daily (
    summary_date,
    dim_item_id,
    dim_warehouse_id,
    COALESCE(lot_no, ''),
    expiry_status,
    COALESCE(expiry_date, DATE '1900-01-01')
);

CREATE INDEX IF NOT EXISTS idx_sum_expiry_daily_status
ON mart.sum_expiry_daily (summary_date, expiry_status);

CREATE INDEX IF NOT EXISTS idx_sum_expiry_daily_expiry_date
ON mart.sum_expiry_daily (expiry_date);

CREATE INDEX IF NOT EXISTS idx_sum_consumption_daily_item
ON mart.sum_consumption_daily (dim_item_id);

CREATE INDEX IF NOT EXISTS idx_sum_consumption_daily_wh
ON mart.sum_consumption_daily (dim_warehouse_id);

CREATE INDEX IF NOT EXISTS idx_sum_consumption_monthly_item
ON mart.sum_consumption_monthly (dim_item_id);

CREATE INDEX IF NOT EXISTS idx_sum_movement_daily_type
ON mart.sum_movement_daily (summary_date, movement_type);

CREATE INDEX IF NOT EXISTS idx_sum_dead_stock_daily_flags
ON mart.sum_dead_stock_daily (summary_date, dead_stock_flag, slow_moving_flag);

CREATE UNIQUE INDEX IF NOT EXISTS uq_sum_procurement_monthly_business
ON mart.sum_procurement_monthly (
    year_month,
    dim_item_id,
    COALESCE(dim_vendor_id, -1)
);

CREATE INDEX IF NOT EXISTS idx_sum_procurement_monthly_vendor
ON mart.sum_procurement_monthly (dim_vendor_id);

/* =========================================================
   10) GRANTS
   ========================================================= */
/* Example only — adjust role names in real environment */

GRANT USAGE ON SCHEMA core, mart TO dashboard_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA core, mart TO dashboard_ro;

GRANT USAGE ON SCHEMA stg, core, mart, ops TO analytics_etl_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA stg, core, mart, ops TO analytics_etl_rw;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA stg, core, mart, ops TO analytics_etl_rw;
```

---

# 8) Logical Coverage of This DDL

DDL ชุดนี้ครอบคลุม domain สำคัญที่ระบบ dashboard ต้องใช้ ได้แก่:

## 8.1 Master / Reference

* item
* warehouse
* vendor
* date

## 8.2 Inventory Position

* current stock
* stock value
* stock status

## 8.3 Inventory Movement

* receive
* issue
* transfer / adjustment / return (ผ่าน movement_type)

## 8.4 Batch / Lot / Expiry

* lot-level stock
* expiry date
* near-expiry / expired analytics

## 8.5 Procurement / Budget

* PO lines
* GR lines
* procurement monthly
* budget burn monthly

## 8.6 Dashboard Summary

* executive summary
* stock position
* expiry
* consumption
* movement
* dead stock
* procurement

---

# 9) Recommended Controlled Value Standards

## 9.1 movement_type

แนะนำให้ normalize ใน ETL เป็นค่าเหล่านี้:

* `receive`
* `issue`
* `transfer_in`
* `transfer_out`
* `adjust_in`
* `adjust_out`
* `return_in`
* `return_out`
* `other`

## 9.2 movement_direction

* `in`
* `out`
* `neutral`

## 9.3 expiry_status

* `expired`
* `near_expiry`
* `healthy`
* `no_expiry`

## 9.4 stock_status

* `normal`
* `zero`
* `negative`
* `overstock_candidate`

---

# 10) Data Quality Rules Required in ETL

DDL นี้อย่างเดียว “ยังไม่กันข้อมูลพัง”
ETL ต้อง enforce อย่างน้อย:

## 10.1 Item Rules

* `source_item_code` ต้องไม่ null
* `item_name` ต้องไม่ว่าง

## 10.2 Warehouse Rules

* `source_warehouse_code` ต้องไม่ null

## 10.3 Stock Rules

* `qty_on_hand` อาจติดลบได้ ถ้า source มีจริง
* แต่ต้องถูก flag เพื่อ dashboard

## 10.4 Movement Rules

* `movement_type` ต้อง map เข้า controlled list

## 10.5 Expiry Rules

* `expiry_date < snapshot_date` = expired
* `expiry_date within threshold` = near_expiry

## 10.6 Value Rules

* ถ้า `qty > 0` แต่ `unit_cost is null` → flag review
* ถ้า `line_value` เบี้ยวจาก `qty × unit_cost` เกิน tolerance → flag review

---

# 11) Refresh Strategy (Required for v1.7 ETL)

## 11.1 STG

* master tables = upsert
* stock snapshot tables = append per snapshot_date
* movement / PO / GR = append + dedupe/upsert

## 11.2 CORE

* dimensions = upsert
* facts = append/upsert by business key

## 11.3 MART

* refresh by date window
* daily marts = refresh last 120 days
* monthly marts = refresh last 24 months

---

# 12) Retention Strategy

## 12.1 Recommended

* `stg.*` = 90–180 วัน
* `core.*` = เก็บยาว
* `mart.*` = เก็บยาว
* `ops.*` = อย่างน้อย 1–2 ปี

---

# 13) Security / Access Model

## 13.1 Suggested Roles

* `analytics_etl_rw` = ETL read/write role
* `dashboard_ro` = dashboard read-only role
* `analytics_admin` = schema / DDL / maintenance role

## 13.2 Access Principle

* Dashboard query ใช้ `mart` เป็นหลัก
* ถ้าจำเป็นจริงค่อย query `core`
* หลีกเลี่ยง dashboard query ตรง `stg`

---

# 14) Deployment Recommendation

แนะนำให้ deploy บน PostgreSQL ตามลำดับนี้:

1. Run full DDL file นี้
2. Seed `core.dim_date`
3. Run ETL รอบแรก
4. Validate row counts
5. Build mart refresh jobs
6. ต่อด้วย dashboard API / frontend

---

# 15) Important Notes

## 15.1 This File Is Intentionally Practical

เอกสารนี้ถูกออกแบบให้:

* พร้อมเริ่ม implementation จริง
* ไม่แตะ `invs2019`
* รองรับ ETL แบบ read-only source
* ไม่ over-engineer ตั้งแต่วันแรก

## 15.2 This File Is Not the ETL Spec

DDL นี้เป็น “ฐานข้อมูล”
แต่ยังไม่ใช่:

* ETL job design
* mapping execution logic
* incremental watermark strategy
* retry / idempotency flow

สิ่งเหล่านี้จะอยู่ใน:

# 👉 PRD v1.7 — ETL Job Spec

---

# 16) Final Approval Statement

PRD v1.6 ฉบับนี้ถือเป็น **PostgreSQL DDL baseline** สำหรับระบบ Dashboard วิเคราะห์คลังยาและเวชภัณฑ์
และพร้อมใช้เป็นฐานสำหรับ:

* ETL implementation
* dashboard backend queries
* KPI mart construction
* phase 1 production deployment

เอกสารนี้ยึดตามข้อจำกัดหลักของโครงการครบถ้วน:

* ไม่แตะ source DB
* analytics ทั้งหมดอยู่ภายนอก `invs2019`
* รองรับ stack และ architecture ที่เลือกไว้แล้ว

---

# END OF FILE
