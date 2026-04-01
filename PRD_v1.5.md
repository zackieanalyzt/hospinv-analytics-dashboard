# PRD v1.5 — ETL + PostgreSQL Schema + App Scaffold Blueprint
## Inventory & Medical Supply Intelligence Dashboard
### Architecture: MariaDB (`invs2019`) → PostgreSQL → Dashboard App

**Version:** 1.5  
**Status:** Build Scaffold Blueprint  
**Last Updated:** 2026-04-01  
**Document Type:** Technical Build Blueprint  

---

# 1) PURPOSE

เอกสารฉบับนี้กำหนดรายละเอียดเชิงลงมือสร้างจริงสำหรับ:

1. ETL Layer
2. PostgreSQL Schema
3. SQL Build Order
4. Dashboard App Scaffold
5. API Scaffold
6. Initial Build Sequence

เป้าหมายคือให้ทีมสามารถเริ่ม implement ได้จริงโดยไม่ต้องเดาสถาปัตยกรรม

---

# 2) IMPLEMENTATION TARGET

---

## Source
MariaDB `invs2019` (READ ONLY)

## Target Analytics DB
PostgreSQL

## ETL
Python

## Dashboard App
Next.js + TypeScript

---

# 3) ETL IMPLEMENTATION BLUEPRINT

---

# 3.1 ETL Execution Flow

```text
Extract from MariaDB
        ↓
Load into PostgreSQL stg.*
        ↓
Transform into analytics.*
        ↓
Aggregate into serve.*
        ↓
Dashboard App reads from serve.*
```

---

# 3.2 ETL Job Build Order

---

## JOB-01: Sync Master Data
### Source Tables
- drug_gn
- drug_vn
- company
- dept_id
- dept_map
- bdg_type

### Target
- stg.*

---

## JOB-02: Sync Inventory State
### Source Tables
- inv_md
- inv_md_c

### Target
- stg.inv_md
- stg.inv_md_c

---

## JOB-03: Sync Transaction Data
### Source Tables
- card
- dispensed
- accr_disp
- buyplan_log

### Target
- stg.*

---

## JOB-04: Sync Planning / Budget / Contract
### Source Tables
- buyplan
- buyplan_c
- bdg_amt
- cnt
- cnt_c

### Target
- stg.*

---

## JOB-05: Build Dimensions
### Target
- analytics.dim_*

---

## JOB-06: Build Facts
### Target
- analytics.fact_*

---

## JOB-07: Build Serve Layer
### Target
- serve.*

---

# 4) POSTGRESQL SCHEMA BOOTSTRAP

---

# 4.1 Create Schemas

```sql
CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS serve;
```

---

# 4.2 STAGING TABLE STRATEGY

## Rule
Staging tables should:
- preserve source columns as much as possible
- add ETL metadata fields
- avoid premature business logic

---

# 4.3 Recommended Common ETL Metadata Columns

เพิ่มในทุก `stg.*` table:

| Column | Type | Purpose |
|---|---|---|
| etl_loaded_at | timestamp | เวลาโหลด |
| etl_batch_id | text | batch tracking |
| etl_source_system | text | source identifier |

---

# 5) RECOMMENDED STAGING TABLES

---

# 5.1 `stg.drug_gn`
### Purpose
item master

### Minimum Key
- `working_code`

---

# 5.2 `stg.drug_vn`
### Purpose
trade/vendor item master

### Minimum Key
- `trade_code`

---

# 5.3 `stg.company`
### Purpose
vendor master

### Minimum Key
- `company_code`

---

# 5.4 `stg.dept_id`
### Purpose
department master

### Minimum Key
- `dept_id`

---

# 5.5 `stg.inv_md`
### Purpose
inventory summary

---

# 5.6 `stg.inv_md_c`
### Purpose
inventory lot detail

---

# 5.7 `stg.card`
### Purpose
inventory movement

### Recommended PK candidate
- `record_number`

---

# 5.8 `stg.dispensed`
### Purpose
dispensing transaction

### Recommended PK candidate
- `record_number`

---

# 5.9 `stg.accr_disp`
### Purpose
requested dispensing

---

# 5.10 `stg.buyplan`
### Purpose
planning header

---

# 5.11 `stg.buyplan_c`
### Purpose
planning detail

---

# 5.12 `stg.bdg_amt`
### Purpose
budget summary

---

# 5.13 `stg.bdg_type`
### Purpose
budget type

---

# 5.14 `stg.cnt`
### Purpose
contract header

---

# 5.15 `stg.cnt_c`
### Purpose
contract detail

---

# 6) ANALYTICS TABLE BLUEPRINT

---

# 6.1 DIMENSIONS

---

## `analytics.dim_product`
### Source
`stg.drug_gn`

### Suggested Columns
- product_key (bigserial PK)
- working_code (unique)
- drug_name
- dosage_form
- sale_unit
- supply_type
- reorder_qty
- min_level
- max_level
- rate_per_month
- last_buy_cost
- is_ed
- active_flag
- created_at
- updated_at

---

## `analytics.dim_trade_product`
### Source
`stg.drug_vn`

### Suggested Columns
- trade_product_key
- trade_code
- working_code
- vendor_code
- manufac_code
- trade_name
- pack_ratio
- buy_unit_cost
- bar_code
- gtin
- tmtid
- atc
- active_flag
- created_at
- updated_at

---

## `analytics.dim_vendor`
### Source
`stg.company`

### Suggested Columns
- vendor_key
- company_code
- company_name
- vendor_flag
- manufac_flag
- due_days
- business_type
- active_flag
- created_at
- updated_at

---

## `analytics.dim_department`
### Source
`stg.dept_id`

### Suggested Columns
- department_key
- dept_id
- dept_name
- keep_inv
- inv_type
- dept_type
- disp_dept
- cost_center_id
- active_flag
- created_at
- updated_at

---

## `analytics.dim_budget`
### Source
`stg.bdg_type`

### Suggested Columns
- budget_key
- budget_type
- budget_name
- active_flag
- created_at
- updated_at

---

## `analytics.dim_date`
### Suggested Columns
- date_key
- full_date
- day
- month
- quarter
- year
- fiscal_year
- month_name
- week_of_year
- is_month_end
- is_year_end

---

# 6.2 FACT TABLES

---

## `analytics.fact_inventory_snapshot`
### Grain
item x trade x lot x dept x location x snapshot_date

### Suggested Columns
- snapshot_date
- working_code
- trade_code
- dept_id
- location
- lot_no
- expired_date
- vendor_code
- qty_on_hand
- lot_cost
- pack_cost
- stock_value
- days_to_expiry
- expiry_bucket
- reorder_threshold
- low_stock_flag
- out_of_stock_flag
- dead_stock_flag
- last_movement_date
- created_at

---

## `analytics.fact_inventory_movement`
### Grain
1 movement record

### Suggested Columns
- movement_id
- operate_datetime
- operate_date
- working_code
- trade_code
- dept_id
- stock_id
- lot_no
- expired_date
- vendor_code
- budget_type
- rs_status
- rs_number
- value
- cost
- active_qty
- remain_qty
- movement_direction
- valid_flag
- created_at

---

## `analytics.fact_dispensing`
### Grain
1 dispense record

### Suggested Columns
- dispense_id
- disp_date
- working_code
- disp_qty
- disp_dept
- process_flag
- hn
- vn
- unit_cost_basis
- disp_value
- created_at

---

## `analytics.fact_requested_dispensing`
### Grain
1 request line

### Suggested Columns
- req_no
- req_date
- confirm_date
- working_code
- dept_id
- stock_id
- qty_req
- qty_dist
- fill_rate
- pending_qty
- created_at

---

## `analytics.fact_plan_budget`
### Grain
1 year x item x dept

### Suggested Columns
- plan_year
- working_code
- trade_code
- dept_id
- avg_3_year
- qty_this_year
- value_this_year
- remain_qty
- remain_value
- buy_qty
- buy_value
- qty_forecast
- forecast_value
- approve_flag
- created_at

---

## `analytics.fact_budget_summary`
### Grain
1 fiscal year x budget type

### Suggested Columns
- fiscal_year
- budget_type
- budget_amount
- total_buy
- budget_remain
- debt
- burn_rate
- created_at

---

## `analytics.fact_contract`
### Grain
1 contract line

### Suggested Columns
- cnt_no
- working_code
- trade_code
- buy_unit_cost
- qty_cnt
- cost_cnt
- qty_remain
- cost_remain
- end_date
- vendor_contract_ref
- contract_utilization_rate
- created_at

---

# 7) SERVE LAYER BLUEPRINT

---

# 7.1 `serve.exec_dashboard_daily`
### Purpose
Executive summary cards + trends

### Suggested Columns
- snapshot_date
- total_inventory_value
- active_stocked_sku_count
- low_stock_sku_count
- near_expiry_value
- expired_stock_value
- dead_stock_value
- monthly_consumption_value
- budget_used
- budget_remaining
- budget_burn_rate

---

# 7.2 `serve.inventory_risk_daily`
### Purpose
Risk table / drilldown

### Suggested Columns
- snapshot_date
- working_code
- trade_code
- dept_id
- lot_no
- qty_on_hand
- stock_value
- days_to_expiry
- dos
- risk_type
- risk_score
- suggested_action

---

# 7.3 `serve.expiry_lot_detail`
### Purpose
Expiry lot dashboard

### Suggested Columns
- snapshot_date
- working_code
- trade_code
- lot_no
- expired_date
- days_to_expiry
- qty_on_hand
- stock_value
- dept_id
- location

---

# 7.4 `serve.consumption_monthly`
### Purpose
Consumption trends

### Suggested Columns
- year_month
- working_code
- dept_id
- total_disp_qty
- total_disp_value
- avg_monthly_usage
- movement_class

---

# 7.5 `serve.department_usage_summary`
### Purpose
Department usage summary

### Suggested Columns
- year_month
- dept_id
- total_usage_qty
- total_usage_value
- usage_share_pct
- active_item_count

---

# 7.6 `serve.plan_vs_actual_summary`
### Purpose
Planning dashboard

### Suggested Columns
- plan_year
- working_code
- dept_id
- planned_qty
- planned_value
- actual_buy_qty
- actual_buy_value
- actual_rcv_qty
- variance_pct
- completion_rate

---

# 7.7 `serve.budget_burn_summary`
### Purpose
Budget dashboard

### Suggested Columns
- fiscal_year
- budget_type
- budget_name
- budget_amount
- total_buy
- budget_remain
- debt
- burn_rate

---

# 8) SQL BUILD ORDER

---

# Step 1
Create schemas:
- stg
- analytics
- serve

---

# Step 2
Create staging tables

---

# Step 3
Create dimension tables

---

# Step 4
Create fact tables

---

# Step 5
Create serve tables / materialized views / refresh SQL

---

# Step 6
Create indexes

---

# Step 7
Create validation SQL

---

# 9) ETL FILE IMPLEMENTATION PLAN

---

# 9.1 Suggested Python Files

```text
etl/app/
├── config/
│   ├── settings.py
│   └── logging.py
├── db/
│   ├── source_mariadb.py
│   └── target_postgres.py
├── extractors/
│   ├── extract_master.py
│   ├── extract_inventory.py
│   ├── extract_transactions.py
│   └── extract_budget.py
├── loaders/
│   ├── load_staging.py
│   └── upsert_helpers.py
├── transforms/
│   ├── build_dim_product.py
│   ├── build_dim_vendor.py
│   ├── build_fact_inventory_snapshot.py
│   ├── build_fact_dispensing.py
│   ├── build_fact_budget.py
│   └── build_serve_layer.py
├── jobs/
│   ├── run_master_sync.py
│   ├── run_inventory_snapshot.py
│   ├── run_transaction_sync.py
│   ├── run_budget_sync.py
│   └── run_all.py
└── main.py
```

---

# 9.2 ETL Entry Points

## Recommended Commands
```bash
python -m app.jobs.run_master_sync
python -m app.jobs.run_inventory_snapshot
python -m app.jobs.run_transaction_sync
python -m app.jobs.run_budget_sync
python -m app.jobs.run_all
```

---

# 10) DASHBOARD APP SCAFFOLD

---

# 10.1 Recommended App Folder Structure

```text
dashboard/
├── app/
│   ├── (dashboard)/
│   │   ├── executive/
│   │   │   └── page.tsx
│   │   ├── stock/
│   │   │   └── page.tsx
│   │   ├── expiry/
│   │   │   └── page.tsx
│   │   ├── consumption/
│   │   │   └── page.tsx
│   │   ├── planning/
│   │   │   └── page.tsx
│   │   ├── budget/
│   │   │   └── page.tsx
│   │   └── movement/
│   │       └── page.tsx
│   │
│   ├── api/
│   │   └── v1/
│   │       └── dashboard/
│   │           ├── executive/route.ts
│   │           ├── inventory-risk/route.ts
│   │           ├── stock-position/route.ts
│   │           ├── consumption/route.ts
│   │           ├── plan-budget/route.ts
│   │           └── movement-exceptions/route.ts
│   │
│   └── layout.tsx
│
├── components/
│   ├── cards/
│   │   └── KpiCard.tsx
│   ├── charts/
│   │   ├── InventoryTrendChart.tsx
│   │   ├── BudgetBurnGauge.tsx
│   │   ├── ExpiryBucketChart.tsx
│   │   └── UsageBarChart.tsx
│   ├── filters/
│   │   ├── DateRangeFilter.tsx
│   │   ├── DepartmentFilter.tsx
│   │   └── ItemFilter.tsx
│   └── tables/
│       ├── InventoryRiskTable.tsx
│       └── LotExpiryTable.tsx
│
├── services/
│   ├── executive.service.ts
│   ├── stock.service.ts
│   ├── expiry.service.ts
│   ├── consumption.service.ts
│   ├── planning.service.ts
│   └── budget.service.ts
│
├── lib/
│   ├── db.ts
│   ├── query.ts
│   └── utils.ts
│
├── hooks/
├── types/
└── public/
```

---

# 10.2 Minimum App Pages for MVP

1. Executive Overview
2. Stock Position
3. Expiry & Dead Stock
4. Consumption & Utilization
5. Planning & Budget

---

# 11) API SCAFFOLD BLUEPRINT

---

# 11.1 API Layer Responsibility
- query PostgreSQL
- validate query params
- transform response
- return clean JSON

---

# 11.2 Service Layer Pattern

### Example
- `executive.service.ts` → query `serve.exec_dashboard_daily`
- `stock.service.ts` → query `analytics.fact_inventory_snapshot`
- `expiry.service.ts` → query `serve.expiry_lot_detail`

---

# 11.3 API Rules
- no raw SQL in UI components
- no DB access from client browser
- all DB calls via server-side only

---

# 12) INITIAL UI BUILD ORDER

---

## UI-01
Executive Overview

---

## UI-02
Stock Position

---

## UI-03
Expiry Dashboard

---

## UI-04
Consumption Dashboard

---

## UI-05
Budget / Planning Dashboard

---

# 13) INDEX STRATEGY

---

## Recommended PostgreSQL Index Targets

### `analytics.fact_inventory_snapshot`
- `(snapshot_date)`
- `(working_code)`
- `(dept_id)`
- `(expired_date)`

### `analytics.fact_dispensing`
- `(disp_date)`
- `(working_code)`
- `(disp_dept)`

### `analytics.fact_budget_summary`
- `(fiscal_year)`
- `(budget_type)`

### `analytics.fact_inventory_movement`
- `(operate_date)`
- `(working_code)`
- `(dept_id)`
- `(rs_status)`

### `serve.inventory_risk_daily`
- `(snapshot_date)`
- `(dept_id)`
- `(risk_type)`

---

# 14) VALIDATION & QA BLUEPRINT

---

# 14.1 Required Validation Queries

1. Count rows loaded per staging table
2. Count rows transformed per fact/dim
3. Sum inventory value by day
4. Sum dispensing qty by day
5. Budget totals by year
6. Missing key / orphan checks

---

# 14.2 Recommended QA Tables (Optional)
ใน PostgreSQL สามารถมี:
- `analytics.qa_load_audit`
- `analytics.qa_reconciliation_log`

---

# 15) DEPLOYMENT SCAFFOLD

---

# 15.1 Services to Deploy

| Service | Deployment |
|---|---|
| PostgreSQL | Native on Debian |
| ETL | Docker container |
| Dashboard App | Docker container |
| Nginx | Optional container |

---

# 15.2 Build Sequence

## Step 1
Provision PostgreSQL DB + user

## Step 2
Create schemas + base tables

## Step 3
Run ETL master sync

## Step 4
Run ETL inventory snapshot

## Step 5
Build analytics layer

## Step 6
Build serve layer

## Step 7
Run dashboard app

---

# 16) MVP IMPLEMENTATION CHECKLIST

- [ ] PostgreSQL schemas created
- [ ] staging tables created
- [ ] ETL can connect to MariaDB
- [ ] ETL can load to PostgreSQL
- [ ] dimensions built
- [ ] inventory snapshot built
- [ ] serve datasets built
- [ ] dashboard app boots
- [ ] executive page renders
- [ ] stock page renders
- [ ] expiry page renders

---

# 17) DEFINITION OF DONE (v1.5)

ถือว่า v1.5 พร้อม implement เมื่อ:

- schema design ถูกล็อก
- ETL scaffold พร้อม
- app scaffold พร้อม
- build order ชัด
- service responsibility ชัด
- dev สามารถเริ่ม coding ได้ทันที

---

# 18) FINAL RECOMMENDATION

v1.5 คือจุดเปลี่ยนจาก:
> “เอกสารวางแผน”

ไปเป็น:
> “โครงสร้างที่พร้อมให้ dev เริ่มลงมือทำจริง”

ถ้าข้ามขั้นนี้ไปแล้วเริ่มเขียนมั่ว  
อีกไม่นานโปรเจกต์จะเต็มไปด้วย:
- SQL ฝังทุกที่
- endpoint ซ้ำ
- chart สวยแต่ตัวเลขคนละโลก

ดังนั้น scaffold ที่ดี = ประหยัดเวลาแก้ระบบในอนาคต

---

# END OF DOCUMENT