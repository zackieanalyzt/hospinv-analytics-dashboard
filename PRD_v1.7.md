# PRD v1.7 — ETL Job Spec

## Project: Hospital Drug & Medical Supply Analytics Dashboard

## Version: 1.7

## Status: Implementation-Ready

## Depends on: PRD v1.0, v1.1, v1.2, v1.3, v1.4, v1.5, v1.6

---

# 1) Purpose

เอกสารฉบับนี้กำหนด **ETL Job Specification** สำหรับ pipeline:

**MariaDB (`invs2019`) → Python ETL / Sync → PostgreSQL Analytics DB**

โดยมีเป้าหมายเพื่อให้ระบบสามารถ:

* ดึงข้อมูลจาก source แบบ **read-only only**
* sync เข้าสู่ PostgreSQL ได้อย่าง **เชื่อถือได้**
* รองรับ **incremental load**
* รองรับ **rerun / retry / recovery**
* รองรับ **data quality checks**
* รองรับ **dashboard refresh แบบ production-ready**

---

# 2) Locked Constraints

ข้อกำหนดต่อไปนี้ถือว่า “ล็อกแล้ว”:

* Source DB = MariaDB `invs2019`
* ห้ามสร้าง object ใด ๆ บน source DB
* ใช้ source DB ได้เฉพาะ `SELECT`
* Analytics ทั้งหมดต้องทำบน PostgreSQL
* ETL เขียนด้วย Python
* Dashboard query ต้องอิง PostgreSQL ไม่ใช่ source DB
* ห้ามออกแบบ ETL ที่ทำให้ source DB รับภาระ query หนักเกินจำเป็น

---

# 3) ETL Architecture Overview

## 3.1 Pipeline Stages

ETL แบ่งเป็น 5 ชั้น:

1. **Extract**

   * ดึงข้อมูลจาก MariaDB
   * แบบ full / incremental ตามลักษณะ table

2. **Land**

   * load ลง `stg.*` บน PostgreSQL

3. **Transform**

   * แปลงข้อมูลจาก staging → `core.*`

4. **Summarize**

   * refresh `mart.*`

5. **Validate & Publish**

   * ตรวจสอบความถูกต้อง / freshness
   * ทำให้ dashboard อ่านได้

---

# 4) ETL Operating Principles

## 4.1 Non-Negotiable Principles

* ETL ต้อง **idempotent**
* ETL ต้อง **resume / rerun ได้**
* ETL ต้อง **log ทุก job**
* ETL ต้อง **ไม่ผูกกับ source schema แบบเปราะ**
* ETL ต้อง **แยก concern** ระหว่าง extract / transform / summarize

## 4.2 Design Philosophy

ใช้แนวทาง:

* simple enough to run daily
* strict enough to trust
* flexible enough to evolve

พูดภาษาคนทำงาน:

> ETL ที่ “ฉลาดเกินไป” มักตายก่อนระบบเสร็จ
> เอาแบบ “แข็งแรงและซ่อมง่าย” ก่อน

---

# 5) ETL Run Modes

ระบบต้องรองรับอย่างน้อย 4 run modes:

## 5.1 FULL

ใช้สำหรับ:

* initial load
* schema rebuild
* major repair

ลักษณะ:

* ดึงข้อมูลทั้งหมดของ table/domain นั้น
* ใช้เฉพาะตอนจำเป็น

## 5.2 INCREMENTAL

ใช้สำหรับ:

* daily scheduled sync
* near-real production operation

ลักษณะ:

* ดึงเฉพาะข้อมูลใหม่ / เปลี่ยนแปลง

## 5.3 REPAIR

ใช้สำหรับ:

* rerun เฉพาะ domain / table ที่พัง
* reload date range ที่ผิดพลาด

## 5.4 BACKFILL

ใช้สำหรับ:

* เติม historical data ย้อนหลัง
* เติมช่วงที่ยังไม่เคยโหลด

---

# 6) ETL Domain Breakdown

ETL แบ่งเป็น 8 data domains:

1. item_master
2. warehouse_master
3. vendor_master
4. stock_balance
5. stock_lot_balance
6. inventory_movement
7. purchase_order_line
8. goods_receipt_line

---

# 7) ETL Job Inventory

## 7.1 Job List

| Job Code | Job Name                 |      Source Domain | Target                                                      |
| -------- | ------------------------ | -----------------: | ----------------------------------------------------------- |
| ETL-001  | load_item_master         |        item master | `stg.item_master` → `core.dim_item`                         |
| ETL-002  | load_warehouse_master    |   warehouse master | `stg.warehouse_master` → `core.dim_warehouse`               |
| ETL-003  | load_vendor_master       |      vendor master | `stg.vendor_master` → `core.dim_vendor`                     |
| ETL-004  | load_stock_balance       |     stock snapshot | `stg.stock_balance` → `core.fact_stock_snapshot`            |
| ETL-005  | load_stock_lot_balance   | stock lot snapshot | `stg.stock_lot_balance` → `core.fact_stock_lot_snapshot`    |
| ETL-006  | load_inventory_movement  | inventory movement | `stg.inventory_movement` → `core.fact_inventory_movement`   |
| ETL-007  | load_purchase_order_line |            PO line | `stg.purchase_order_line` → `core.fact_purchase_order_line` |
| ETL-008  | load_goods_receipt_line  |            GR line | `stg.goods_receipt_line` → `core.fact_goods_receipt_line`   |
| ETL-009  | refresh_marts_daily      |          all marts | `mart.*`                                                    |
| ETL-010  | refresh_data_freshness   |   freshness status | `ops.etl_data_freshness`                                    |

---

# 8) Job Dependency Graph

## 8.1 Dependency Order

```text id="2g4m7d"
ETL-001 load_item_master
ETL-002 load_warehouse_master
ETL-003 load_vendor_master
        ↓
ETL-004 load_stock_balance
ETL-005 load_stock_lot_balance
ETL-006 load_inventory_movement
ETL-007 load_purchase_order_line
ETL-008 load_goods_receipt_line
        ↓
ETL-009 refresh_marts_daily
        ↓
ETL-010 refresh_data_freshness
```

## 8.2 Dependency Rule

* dimension jobs ต้องรันก่อน fact jobs
* mart jobs รันหลัง fact jobs
* freshness update รันสุดท้าย

---

# 9) ETL Schedule Recommendation

## 9.1 Recommended Schedule (Phase 1)

| Job Group          | Frequency | Recommended Time |
| ------------------ | --------: | ---------------: |
| Master Data        |     daily |            00:30 |
| Stock Snapshot     |     daily |            01:00 |
| Movement / PO / GR |     daily |            01:15 |
| Mart Refresh       |     daily |            02:00 |
| Freshness Update   |     daily |            02:15 |

## 9.2 Optional Future Upgrade

ถ้าต้องการ dashboard สดขึ้น:

* movement sync ทุก 1–2 ชั่วโมง
* mart refresh บางตัวทุก 2–4 ชั่วโมง

แต่สำหรับ phase 1:

> **daily batch = พอและปลอดภัยกว่า**

---

# 10) Batch Control Design

ทุก ETL run ต้องสร้าง record ใน `ops.etl_batch`

## 10.1 Batch Lifecycle

1. create batch record → status = `running`
2. run jobs
3. update per-table status ใน `ops.etl_table_run`
4. ถ้าทุกอย่างผ่าน → batch status = `success`
5. ถ้ามีบาง job fail → `failed` หรือ `partial`

## 10.2 Batch Status Standard

* `running`
* `success`
* `failed`
* `partial`

---

# 11) Watermark Strategy

## 11.1 Why Watermark Matters

ถ้าไม่มี watermark:

* incremental จะกลายเป็น full load ปลอม ๆ
* source จะโดน query หนัก
* ETL จะช้าแบบไม่มีศักดิ์ศรี

## 11.2 Watermark Source Priority

ใช้ลำดับนี้:

1. `source_updated_ts` (ดีที่สุด)
2. `txn_ts`
3. `txn_date`
4. `snapshot_date`
5. fallback = full reload window

## 11.3 Watermark Storage

เก็บช่วงที่ใช้ใน `ops.etl_batch`

* `watermark_from_ts`
* `watermark_to_ts`

## 11.4 Safety Buffer

สำหรับ incremental jobs ให้ใช้ **lookback buffer**
เช่น:

* watermark ล่าสุด = 2026-03-31 23:59:59
* รอบถัดไปให้ดึงย้อนหลังอีก 1–3 วัน

เหตุผล:

* กัน late-arriving records
* กัน source update ย้อนหลัง
* กันเวลาระบบต้นทาง “พูดไม่หมด”

### Recommended buffer

* movement = 3 วัน
* PO / GR = 7 วัน
* master data = 7 วัน
* stock snapshot = 1 วัน

---

# 12) Load Strategy by Domain

## 12.1 Master Data

### item_master

* Extract mode: incremental / full
* Source filter: `source_updated_ts >= watermark_from_ts - 7 days`
* STG load: upsert-ish append by batch
* CORE load: upsert into `core.dim_item`

### warehouse_master

* Extract mode: full / incremental
* CORE load: upsert into `core.dim_warehouse`

### vendor_master

* Extract mode: full / incremental
* CORE load: upsert into `core.dim_vendor`

---

## 12.2 Snapshot Data

### stock_balance

* Grain: daily snapshot by item + warehouse
* Extract mode: daily append
* Source filter: `snapshot_date >= current_date - 1`
* STG load: append by snapshot date
* CORE load: upsert by `(snapshot_date, dim_item_id, dim_warehouse_id)`

### stock_lot_balance

* Grain: daily snapshot by item + warehouse + lot
* Extract mode: daily append
* STG load: append by snapshot date
* CORE load: upsert by business key

---

## 12.3 Transaction Data

### inventory_movement

* Grain: transaction line
* Extract mode: incremental
* Source filter: `txn_ts` or `txn_date` with lookback 3 days
* STG load: append + dedupe
* CORE load: upsert / insert-if-not-exists by source business key

### purchase_order_line

* Grain: PO line
* Extract mode: incremental
* Lookback: 7 days
* CORE load: upsert by `(po_no, item)`

### goods_receipt_line

* Grain: GR line
* Extract mode: incremental
* Lookback: 7 days
* CORE load: upsert by `(gr_no, item, warehouse, lot)`

---

# 13) Extraction Rules

## 13.1 Source Query Principles

* SELECT only
* no temp object creation on source
* avoid long locking reads
* prefer indexed filter columns
* extract in chunks if row count สูง

## 13.2 Chunking Rule

ถ้าตารางใดเกิน ~500k rows / run:

* extract แบบ chunk
* ใช้ primary key range หรือ date range

## 13.3 Safe Query Pattern

แนว query ที่ควรใช้:

```sql id="7j8p3m"
SELECT ...
FROM source_table
WHERE updated_ts >= :from_ts
  AND updated_ts < :to_ts
ORDER BY updated_ts, primary_key;
```

ถ้าไม่มี timestamp:

```sql id="d2g8z0"
SELECT ...
FROM source_table
WHERE txn_date >= :from_date
  AND txn_date <= :to_date
ORDER BY txn_date, primary_key;
```

---

# 14) Staging Load Rules

## 14.1 STG Philosophy

staging มีไว้เพื่อ:

* เก็บ raw-ish landing
* support rerun
* support debugging
* decouple source จาก analytics

## 14.2 Required STG Columns

ทุก staging table ควรมี:

* `etl_batch_id`
* `source_pk_hash`
* `extracted_ts`

## 14.3 source_pk_hash Rule

สร้างจาก natural/business key ของ source row เช่น:

* item_master → item_code
* movement → txn_id + item_code + warehouse + lot
* stock snapshot → snapshot_date + item_code + warehouse

hash algorithm:

* SHA256 recommended

---

# 15) Core Transform Rules

## 15.1 Master Dimension Upsert

### core.dim_item

upsert key:

* `source_item_code`

update columns:

* item_name
* generic_name
* item_type
* item_group
* item_category
* abc_class
* ven_class
* standard_unit
* manufacturer_name
* last_seen_ts

### core.dim_warehouse

upsert key:

* `source_warehouse_code`

### core.dim_vendor

upsert key:

* `source_vendor_code`

---

## 15.2 Fact Transform Rules

### core.fact_inventory_movement

required transforms:

* lookup `dim_item_id`
* lookup `dim_warehouse_id`
* lookup `dim_vendor_id`
* derive `txn_date_id`
* normalize `movement_type`
* derive `movement_direction`
* derive `signed_qty`
* derive `signed_value`

### signed_qty logic

* receive / transfer_in / return_in / adjust_in → positive
* issue / transfer_out / return_out / adjust_out → negative
* other → based on business mapping

### core.fact_stock_snapshot

required transforms:

* lookup dimensions
* derive `snapshot_date_id`
* derive `stock_status`

### stock_status logic

* qty_on_hand > 0 → `normal`
* qty_on_hand = 0 → `zero`
* qty_on_hand < 0 → `negative`

### core.fact_stock_lot_snapshot

required transforms:

* derive `days_to_expiry`
* derive `expiry_status`

### expiry_status logic

* expiry_date is null → `no_expiry`
* expiry_date < snapshot_date → `expired`
* expiry_date <= snapshot_date + threshold_days → `near_expiry`
* else → `healthy`

**Recommended threshold_days = 90**

---

# 16) Mart Refresh Rules

mart layer ไม่ควร rely on frontend aggregation
ให้ precompute ใน DB

---

## 16.1 Refresh Window Strategy

### Daily marts

refresh ย้อนหลัง **120 วัน**
ใช้กับ:

* `mart.sum_inventory_daily`
* `mart.sum_stock_position_daily`
* `mart.sum_expiry_daily`
* `mart.sum_consumption_daily`
* `mart.sum_movement_daily`
* `mart.sum_dead_stock_daily`

### Monthly marts

refresh ย้อนหลัง **24 เดือน**
ใช้กับ:

* `mart.sum_consumption_monthly`
* `mart.sum_procurement_monthly`
* `mart.sum_budget_burn_monthly`

---

## 16.2 Refresh Mode

ใช้แนวทาง:

* `DELETE WHERE date/month in window`
* `INSERT SELECT ...`

ข้อดี:

* logic ชัด
* rerun ง่าย
* ลด merge complexity

---

# 17) Data Quality Rules

## 17.1 Severity Levels

ทุก data quality rule ให้จัดระดับ:

* `ERROR` = ต้อง fail job
* `WARN` = load ได้แต่ต้อง log
* `INFO` = monitor only

---

## 17.2 Domain Rules

### item_master

* `source_item_code is null` → ERROR
* `item_name is null/blank` → ERROR

### warehouse_master

* `source_warehouse_code is null` → ERROR

### vendor_master

* `source_vendor_code is null` → WARN (ขึ้นกับ source จริง)

### stock_balance

* duplicate `(snapshot_date, item_code, warehouse)` → ERROR
* `qty_on_hand is null` → ERROR
* `qty_on_hand < 0` → WARN

### stock_lot_balance

* duplicate business key → ERROR
* `expiry_date < '2000-01-01'` → WARN
* `qty_on_hand < 0` → WARN

### inventory_movement

* `source_txn_id is null` → ERROR
* `movement_type unknown` → WARN → map เป็น `other`
* `qty = 0` → WARN
* `qty is null` → ERROR

### purchase_order_line

* `po_no is null` → ERROR
* `ordered_qty is null` → ERROR

### goods_receipt_line

* `gr_no is null` → ERROR
* `received_qty is null` → ERROR

---

# 18) Error Handling Strategy

## 18.1 Error Categories

* Source connection error
* Query timeout
* Data mapping error
* Constraint violation
* Load error
* Mart refresh error

## 18.2 Failure Policy

* ถ้า **dimension job fail** → stop downstream dependent fact jobs
* ถ้า **fact job fail** → mart refresh ต้องไม่ run
* ถ้า mart บางตัว fail แต่ตัวอื่นผ่าน → batch = `partial`

## 18.3 Retry Policy

แนะนำ:

* connection error → retry 3 ครั้ง
* transient DB error → retry 3 ครั้ง
* data integrity error → **do not blind retry**

> retry error data เดิมซ้ำ ๆ คือ automation เวอร์ชัน “ตีหัวตัวเอง”

---

# 19) Idempotency Strategy

ETL ต้อง rerun ได้โดยไม่สร้างข้อมูลซ้ำ

## 19.1 Idempotency Rules

### STG

* ใช้ `source_pk_hash` + `etl_batch_id` สำหรับ dedupe

### CORE

* ใช้ business key upsert / delete-in-window + insert

### MART

* ใช้ refresh-by-window เสมอ

## 19.2 Recommended Rule

ถ้าสงสัยว่า “append ดีไหม”
ให้ถามกลับว่า:

> rerun แล้วข้อมูลจะซ้ำไหม?

ถ้าคำตอบคือ “อาจจะ”
แปลว่าอย่า append แบบมึน ๆ

---

# 20) Logging & Observability

## 20.1 Mandatory Logs Per Job

ทุก job ต้อง log:

* batch id
* job code
* start time
* end time
* source row count
* inserted count
* updated count
* rejected count
* status
* error summary

## 20.2 Log Storage

เก็บลง:

* `ops.etl_batch`
* `ops.etl_table_run`

## 20.3 Recommended App Logging

ใน Python layer ควร log เพิ่ม:

* SQL execution time
* chunk size
* memory usage (optional)
* extracted date range

---

# 21) Data Freshness Rules

หลัง ETL เสร็จ ให้ update `ops.etl_data_freshness`

## 21.1 Freshness Status Standard

* `fresh`
* `stale`
* `failed`
* `unknown`

## 21.2 Suggested Threshold

* stock snapshot > 2 วันไม่อัปเดต → stale
* movement > 2 วันไม่อัปเดต → stale
* master data > 7 วันไม่อัปเดต → stale

---

# 22) Suggested Python Project Structure

```text id="11j4qz"
etl/
  config/
    settings.py
    env.py

  db/
    mariadb.py
    postgres.py

  utils/
    hashing.py
    dates.py
    logging.py
    validation.py

  jobs/
    job_001_item_master.py
    job_002_warehouse_master.py
    job_003_vendor_master.py
    job_004_stock_balance.py
    job_005_stock_lot_balance.py
    job_006_inventory_movement.py
    job_007_purchase_order_line.py
    job_008_goods_receipt_line.py
    job_009_refresh_marts.py
    job_010_refresh_freshness.py

  sql/
    source/
    staging/
    core/
    mart/

  runners/
    daily_pipeline.py
    repair_runner.py
    backfill_runner.py

  main.py
```

---

# 23) Environment Variables

```env id="fqkcz5"
MARIADB_HOST=
MARIADB_PORT=3306
MARIADB_DB=invs2019
MARIADB_USER=
MARIADB_PASSWORD=

PG_HOST=
PG_PORT=5432
PG_DB=
PG_USER=
PG_PASSWORD=

ETL_BATCH_TRIGGER=system
ETL_DEFAULT_LOOKBACK_DAYS=3
EXPIRY_NEAR_THRESHOLD_DAYS=90
```

---

# 24) Recommended Python Libraries

```text id="lyy3n7"
sqlalchemy
pymysql
psycopg2-binary
pandas
python-dotenv
tenacity
loguru
```

## Why these

* `sqlalchemy` = DB abstraction
* `pymysql` = MariaDB connector
* `psycopg2-binary` = PostgreSQL connector
* `pandas` = transform helper
* `python-dotenv` = env config
* `tenacity` = retry logic
* `loguru` = clean logging

---

# 25) Pseudocode — Daily Pipeline

```python id="5y1y0r"
def run_daily_pipeline():
    batch_id = create_batch(pipeline_name="daily_inventory_pipeline", batch_type="incremental")

    try:
        run_job_001_item_master(batch_id)
        run_job_002_warehouse_master(batch_id)
        run_job_003_vendor_master(batch_id)

        run_job_004_stock_balance(batch_id)
        run_job_005_stock_lot_balance(batch_id)
        run_job_006_inventory_movement(batch_id)
        run_job_007_purchase_order_line(batch_id)
        run_job_008_goods_receipt_line(batch_id)

        run_job_009_refresh_marts(batch_id)
        run_job_010_refresh_freshness(batch_id)

        mark_batch_success(batch_id)

    except Exception as e:
        mark_batch_failed(batch_id, str(e))
        raise
```

---

# 26) SQL Pattern — Upsert into Dimensions

## 26.1 Example: core.dim_item

```sql id="fw8nsi"
INSERT INTO core.dim_item (
    source_item_code,
    item_name,
    generic_name,
    item_type,
    item_group,
    item_category,
    abc_class,
    ven_class,
    standard_unit,
    strength_text,
    dosage_form,
    manufacturer_name,
    is_active,
    is_drug,
    is_supply,
    first_seen_ts,
    last_seen_ts,
    current_record_flag
)
SELECT
    s.source_item_code,
    s.item_name,
    s.generic_name,
    s.item_type,
    s.item_group,
    s.item_category,
    s.abc_class,
    s.ven_class,
    s.standard_unit,
    s.strength_text,
    s.dosage_form,
    s.manufacturer_name,
    COALESCE(s.is_active, TRUE),
    CASE WHEN LOWER(COALESCE(s.item_type, '')) = 'drug' THEN TRUE ELSE FALSE END,
    CASE WHEN LOWER(COALESCE(s.item_type, '')) = 'supply' THEN TRUE ELSE FALSE END,
    NOW(),
    NOW(),
    TRUE
FROM stg.item_master s
WHERE s.etl_batch_id = :etl_batch_id
ON CONFLICT (source_item_code)
DO UPDATE SET
    item_name = EXCLUDED.item_name,
    generic_name = EXCLUDED.generic_name,
    item_type = EXCLUDED.item_type,
    item_group = EXCLUDED.item_group,
    item_category = EXCLUDED.item_category,
    abc_class = EXCLUDED.abc_class,
    ven_class = EXCLUDED.ven_class,
    standard_unit = EXCLUDED.standard_unit,
    strength_text = EXCLUDED.strength_text,
    dosage_form = EXCLUDED.dosage_form,
    manufacturer_name = EXCLUDED.manufacturer_name,
    is_active = EXCLUDED.is_active,
    is_drug = EXCLUDED.is_drug,
    is_supply = EXCLUDED.is_supply,
    last_seen_ts = NOW(),
    current_record_flag = TRUE;
```

---

# 27) SQL Pattern — Refresh Mart by Window

## 27.1 Example: mart.sum_inventory_daily

```sql id="59wtqa"
DELETE FROM mart.sum_inventory_daily
WHERE summary_date >= :from_date
  AND summary_date <= :to_date;

INSERT INTO mart.sum_inventory_daily (
    summary_date,
    total_sku_count,
    active_sku_count,
    warehouse_count,
    total_qty_on_hand,
    total_stock_value,
    zero_stock_sku_count,
    negative_stock_sku_count,
    near_expiry_sku_count,
    expired_sku_count,
    dead_stock_sku_count,
    created_ts
)
SELECT
    f.snapshot_date AS summary_date,
    COUNT(DISTINCT f.dim_item_id) AS total_sku_count,
    COUNT(DISTINCT CASE WHEN i.is_active THEN f.dim_item_id END) AS active_sku_count,
    COUNT(DISTINCT f.dim_warehouse_id) AS warehouse_count,
    COALESCE(SUM(f.qty_on_hand), 0) AS total_qty_on_hand,
    COALESCE(SUM(f.stock_value), 0) AS total_stock_value,
    COUNT(DISTINCT CASE WHEN f.qty_on_hand = 0 THEN f.dim_item_id END) AS zero_stock_sku_count,
    COUNT(DISTINCT CASE WHEN f.qty_on_hand < 0 THEN f.dim_item_id END) AS negative_stock_sku_count,
    0 AS near_expiry_sku_count,
    0 AS expired_sku_count,
    0 AS dead_stock_sku_count,
    NOW()
FROM core.fact_stock_snapshot f
LEFT JOIN core.dim_item i
    ON f.dim_item_id = i.dim_item_id
WHERE f.snapshot_date >= :from_date
  AND f.snapshot_date <= :to_date
GROUP BY f.snapshot_date;
```

> หมายเหตุ:
> รอบแรกใช้ค่า `0` สำหรับบาง KPI ได้ก่อน
> แล้วค่อย enrich ใน mart refresh logic รุ่นถัดไป
> อย่าพยายามทำ “จักรวาล KPI ครบทุกมิติ” ใน commit แรก เดี๋ยวระบบจะสาปกลับ

---

# 28) Repair / Rerun Strategy

## 28.1 Supported Repair Scenarios

ต้องรองรับอย่างน้อย:

* rerun job เดียว
* rerun domain เดียว
* rerun date range
* rerun full mart refresh

## 28.2 Repair Examples

### Example A — repair movement ย้อนหลัง 7 วัน

* run ETL-006 only
* date range = today - 7 ถึง today
* then rerun mart refresh window 7–30 วัน

### Example B — stock snapshot พังเฉพาะวันเดียว

* rerun ETL-004 / ETL-005 for target snapshot date
* rerun mart refresh for that date

---

# 29) Backfill Strategy

## 29.1 Recommended Historical Load Order

เวลาทำ backfill ให้โหลดตามลำดับนี้:

1. master data
2. stock snapshot
3. stock lot snapshot
4. movement
5. PO
6. GR
7. marts

## 29.2 Backfill Chunk Recommendation

ถ้าย้อนหลายปี:

* movement = backfill ทีละ 1 เดือน
* stock snapshot = ทีละ 1 เดือน
* lot snapshot = ทีละ 1 เดือน
* PO / GR = ทีละ 1–3 เดือน

---

# 30) Acceptance Criteria

ETL v1.7 ถือว่า “พร้อมใช้งานจริง” เมื่อผ่านเงื่อนไขต่อไปนี้:

## 30.1 Functional

* ดึงข้อมูลจาก source ได้ครบตาม domain
* load ลง staging ได้
* transform ลง core ได้
* refresh mart ได้

## 30.2 Reliability

* rerun แล้วไม่ duplicate
* fail แล้ว trace ได้
* retry แล้ว recover ได้ในกรณี transient error

## 30.3 Observability

* ทุก job มี log
* มี batch history
* มี freshness status

## 30.4 Performance (Phase 1 baseline)

* daily batch ต้องจบได้ในช่วง maintenance window ที่กำหนด
* dashboard query ไม่ต้องวิ่งกลับ source

---

# 31) Immediate Implementation Plan

ลำดับ implementation ที่แนะนำหลังจากเอกสารนี้:

1. สร้าง Python ETL project scaffold
2. เขียน DB connection layer
3. เขียน batch control helpers
4. implement master jobs (ETL-001..003)
5. implement stock jobs (ETL-004..005)
6. implement movement / PO / GR jobs (ETL-006..008)
7. implement mart refresh (ETL-009)
8. implement freshness update (ETL-010)
9. test full load
10. test incremental load
11. test rerun / repair

---

# 32) Recommended Next Deliverable

หลังจาก v1.7 เสร็จ ควรทำต่อทันที:

# 👉 PRD v1.8 — Dashboard UI/UX Spec

ควรครอบคลุม:

* executive summary screen
* stock position screen
* expiry screen
* dead stock screen
* consumption screen
* movement screen
* procurement / planning screen
* filters / drilldowns / chart behavior

---

# 33) Final Approval Statement

PRD v1.7 ฉบับนี้ถือเป็น **ETL execution blueprint** สำหรับระบบ Dashboard วิเคราะห์คลังยาและเวชภัณฑ์
และพร้อมใช้เป็น baseline สำหรับการเริ่ม implement Python ETL จริง

เอกสารนี้ยึดข้อกำหนดหลักของโครงการครบถ้วน:

* ไม่แตะ `invs2019`
* ใช้ source แบบ read-only only
* analytics ทั้งหมดทำบน PostgreSQL
* รองรับ pipeline ที่ maintain ได้, rerun ได้, และ production-friendly

---

# END OF FILE
