# PRD v1.3 — Hybrid Analytics Implementation Blueprint
## Inventory & Medical Supply Intelligence Dashboard
### Architecture: MariaDB (`invs2019`) → PostgreSQL → Dashboard App

**Version:** 1.3  
**Status:** Implementation Blueprint  
**Last Updated:** 2026-04-01  
**Document Type:** Technical Product Requirements + Solution Architecture  
**Target Environment:** Debian 64-bit Server / Containerized App Deployment  

---

# 1) PURPOSE

เอกสารฉบับนี้กำหนดแนวทางการพัฒนา **ระบบ Dashboard วิเคราะห์คลังยาและเวชภัณฑ์** ภายใต้ข้อจำกัดสำคัญว่า:

> **ห้ามสร้าง object ใด ๆ บนฐานข้อมูล MariaDB `invs2019` โดยเด็ดขาด**

ดังนั้นระบบจะถูกออกแบบใหม่ให้ใช้แนวทาง:

# **MariaDB (`invs2019`) → PostgreSQL (Analytics Core) → Dashboard App**

โดย:
- `invs2019` = Source of Truth (Read Only)
- `PostgreSQL` = Analytics / Data Mart / KPI / History / Serving Layer
- `Dashboard App` = ระบบแสดงผลหลักสำหรับผู้ใช้

---

# 2) ARCHITECTURAL DECISION

## Final Chosen Architecture

```text
MariaDB (invs2019) [READ ONLY]
        ↓
Python ETL / Sync Jobs
        ↓
PostgreSQL Analytics DB
        ↓
Dashboard API / App
        ↓
Web Dashboard UI
```

---

# 3) DESIGN PRINCIPLES

---

## P-01) Source Database is Untouchable
ฐานข้อมูล `invs2019` ใช้เพื่อ:
- `SELECT`
- metadata inspection
- read-only extraction only

**Forbidden**
- CREATE
- VIEW
- TEMP OBJECT
- INSERT
- UPDATE
- DELETE
- ALTER
- DROP
- FUNCTION / PROCEDURE

---

## P-02) All Transformations Must Happen Outside Source
การแปลงข้อมูล / aggregate / KPI / mart / serving layer  
ต้องเกิดขึ้นใน **PostgreSQL** หรือใน **ETL layer** เท่านั้น

---

## P-03) Analytics Must Not Depend on Live Complex Queries to Source
Dashboard ต้องไม่พึ่ง query analytics หนัก ๆ ตรงจาก source DB แบบ runtime

---

## P-04) Historical Analytics Requires Snapshot Persistence
ข้อมูลบางชุดใน source มีลักษณะ current-state  
ดังนั้นต้องมีการเก็บ **snapshot history** ใน PostgreSQL

---

## P-05) Dashboard Must Be Productized, Not Just a BI Canvas
ระบบต้องพร้อมพัฒนาไปสู่:
- role-based access
- app-style navigation
- alerting
- export
- UX ที่เหมาะกับผู้บริหารและผู้ปฏิบัติงาน

---

# 4) BUSINESS GOALS

1. ลด stockout
2. ลด near expiry / expired loss
3. เพิ่มความแม่นยำของแผนจัดซื้อ
4. ควบคุม budget utilization
5. มองเห็น usage / movement / anomalies
6. สร้าง dashboard ที่ใช้งานได้จริงในองค์กร

---

# 5) NON-FUNCTIONAL REQUIREMENTS

---

## 5.1 Security
- Source DB ต้องเป็น read-only only
- Dashboard app ต้องไม่เก็บ credential source DB ฝั่ง frontend
- ทุก access ผ่าน API/backend only
- แยก secret ผ่าน `.env` หรือ secret manager

---

## 5.2 Performance
- Dashboard หน้า executive ต้องตอบสนอง < 3 วินาที (เป้าหมาย)
- หน้า detail / table-heavy ต้องตอบสนอง < 5 วินาที (เป้าหมาย)
- ห้าม query fact raw ขนาดใหญ่ทุกครั้งที่เปิดหน้า

---

## 5.3 Maintainability
- แยก ETL / Analytics / UI ชัดเจน
- รองรับ incremental refresh
- รองรับ future expansion เช่น alerts / APIs / mobile

---

## 5.4 Deployability
- Dashboard app และ ETL ต้อง deploy ผ่าน container ได้สะดวก
- PostgreSQL ใช้ native deployment ได้
- รองรับ Docker Compose บน Debian

---

# 6) TARGET SOLUTION STACK

---

# 6.1 Source Database
## MariaDB
### Database:
`invs2019`

### Role:
- Read-only source of truth

---

# 6.2 Analytics Core
## PostgreSQL 16+

### Role:
- staging
- normalized analytics model
- historical snapshots
- KPI logic
- serving datasets

---

# 6.3 ETL / Sync Layer
## Python 3.12+

### Recommended Libraries
- `sqlalchemy`
- `psycopg`
- `pymysql` or `mysqlclient`
- `polars` or `pandas`
- `python-dotenv`
- `APScheduler` or cron
- `loguru` (optional)

### Role
- extract data from MariaDB
- transform / clean / normalize
- load into PostgreSQL
- build snapshots / refresh serve layer

---

# 6.4 Dashboard App
## Recommended Stack
### Frontend / Fullstack:
# **Next.js + TypeScript**

### UI:
- Tailwind CSS
- shadcn/ui

### Charts:
# **Apache ECharts**

### Tables:
- TanStack Table
- optional AG Grid (if needed later)

### Role:
- modern dashboard UI
- filters / drilldown / export
- API access to PostgreSQL datasets

---

# 6.5 Reverse Proxy / Web Serving
- `nginx` or `traefik`

---

# 7) SYSTEM ARCHITECTURE

---

## 7.1 Logical Architecture

```text
[ MariaDB invs2019 ]
    └── Source Operational Database (Read Only)

[ Python ETL / Sync ]
    ├── Full Extract Jobs
    ├── Incremental Extract Jobs
    ├── Snapshot Builder
    └── Serve Dataset Refresher

[ PostgreSQL ]
    ├── stg schema
    ├── analytics schema
    └── serve schema

[ Dashboard App ]
    ├── API layer
    ├── Auth / Session
    ├── Dashboard pages
    ├── Drilldown / Detail pages
    └── Export / Filters / UI logic
```

---

# 8) POSTGRESQL DATABASE DESIGN

---

# 8.1 Schema Strategy

PostgreSQL จะแบ่งเป็น 3 schema หลัก

---

## SCHEMA 1: `stg`
### Purpose
เก็บข้อมูลจาก source ในสภาพ “ใกล้เคียงต้นฉบับที่สุด”

### Example Tables
- `stg.drug_gn`
- `stg.drug_vn`
- `stg.company`
- `stg.dept_id`
- `stg.inv_md`
- `stg.inv_md_c`
- `stg.card`
- `stg.dispensed`
- `stg.accr_disp`
- `stg.buyplan`
- `stg.buyplan_c`
- `stg.bdg_amt`
- `stg.bdg_type`
- `stg.cnt`
- `stg.cnt_c`

---

## SCHEMA 2: `analytics`
### Purpose
เก็บ cleaned / normalized / conformed data model

### Example Dimensions
- `analytics.dim_product`
- `analytics.dim_trade_product`
- `analytics.dim_vendor`
- `analytics.dim_department`
- `analytics.dim_budget`
- `analytics.dim_date`

### Example Facts
- `analytics.fact_inventory_snapshot`
- `analytics.fact_inventory_movement`
- `analytics.fact_dispensing`
- `analytics.fact_requested_dispensing`
- `analytics.fact_plan_budget`
- `analytics.fact_budget_summary`
- `analytics.fact_contract`

---

## SCHEMA 3: `serve`
### Purpose
เก็บ pre-aggregated datasets สำหรับ dashboard app

### Example Tables / Views
- `serve.exec_dashboard_daily`
- `serve.inventory_risk_daily`
- `serve.expiry_lot_detail`
- `serve.consumption_monthly`
- `serve.department_usage_summary`
- `serve.plan_vs_actual_summary`
- `serve.budget_burn_summary`
- `serve.movement_exception_summary`

---

# 9) DATA FLOW DESIGN

---

# 9.1 Data Pipeline Stages

## Stage 1 — Extract
อ่านข้อมูลจาก MariaDB (`invs2019`) แบบ read-only

## Stage 2 — Load to Staging
โหลดข้อมูลเข้า PostgreSQL schema `stg`

## Stage 3 — Transform
clean / normalize / join / derive fields เข้า `analytics`

## Stage 4 — Aggregate / Serve
เตรียม dataset พร้อมใช้สำหรับ dashboard เข้า `serve`

## Stage 5 — Present
Dashboard app query จาก `serve` เป็นหลัก

---

# 10) EXTRACTION STRATEGY

---

# 10.1 Extraction Categories

---

## Category A — Full Refresh Master Data
ตารางขนาดเล็ก / เปลี่ยนไม่ถี่

### Tables
- `drug_gn`
- `drug_vn`
- `company`
- `dept_id`
- `dept_map`
- `bdg_type`
- `dosage_form`
- `drug_compos`
- `ed_group`
- `hosp_list`

### Frequency
- Daily (nightly)
- or on-demand

---

## Category B — Incremental Transaction Extraction
ตาราง transaction ที่มีข้อมูลเพิ่มเรื่อย ๆ

### Tables
- `card`
- `dispensed`
- `accr_disp`
- `buyplan_log`

### Incremental Keys (recommended)
- `RECORD_NUMBER`
- `OPERATE_DATE`
- `DISP_DATE`
- `REQ_DATE`
- `LOG_DATE`

### Frequency
- every 1–4 hours (recommended)
- configurable

---

## Category C — Snapshot Extraction
ตาราง current-state ที่ต้องเก็บประวัติไว้เอง

### Tables
- `inv_md`
- `inv_md_c`
- `buyplan`
- `buyplan_c`
- `bdg_amt`
- `cnt`
- `cnt_c`

### Frequency
- Daily snapshot
- Optional additional daytime refresh (e.g. noon)

---

# 11) RECOMMENDED REFRESH SCHEDULE

---

## Nightly Master Sync
**Time:** 00:30
- sync master tables

---

## Nightly Snapshot Build
**Time:** 01:00
- snapshot inventory / budget / planning / contract

---

## Incremental Transactions
**Time:** every 2 hours (recommended)
- card
- dispensed
- accr_disp

---

## Serve Layer Refresh
**Time:** after each successful ETL cycle
- rebuild aggregated dashboard datasets

---

# 12) ANALYTICS DATA MODEL

---

# 12.1 Dimensions

---

## `analytics.dim_product`
### Grain
1 row = 1 `WORKING_CODE`

### Core Fields
- product_key
- working_code
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

---

## `analytics.dim_trade_product`
### Grain
1 row = 1 `TRADE_CODE`

### Core Fields
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

---

## `analytics.dim_vendor`
### Grain
1 row = 1 vendor

### Core Fields
- vendor_key
- company_code
- company_name
- vendor_flag
- manufac_flag
- due_days
- business_type
- active_flag

---

## `analytics.dim_department`
### Grain
1 row = 1 `DEPT_ID`

### Core Fields
- department_key
- dept_id
- dept_name
- keep_inv
- inv_type
- dept_type
- disp_dept
- cost_center_id
- active_flag

---

## `analytics.dim_budget`
### Grain
1 row = 1 `BUDGET_TYPE`

### Core Fields
- budget_key
- budget_type
- budget_name
- active_flag

---

## `analytics.dim_date`
### Grain
1 row = 1 date

### Core Fields
- date_key
- full_date
- day
- month
- quarter
- year
- fiscal_year
- month_name

---

# 12.2 Facts

---

## `analytics.fact_inventory_snapshot`
### Grain
1 row = 1 item x trade x lot x dept x location x snapshot_date

### Core Fields
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
- low_stock_flag
- out_of_stock_flag
- dead_stock_flag

---

## `analytics.fact_inventory_movement`
### Grain
1 row = 1 movement event

### Core Fields
- movement_id
- operate_datetime
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

---

## `analytics.fact_dispensing`
### Grain
1 row = 1 dispense event

### Core Fields
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

---

## `analytics.fact_requested_dispensing`
### Grain
1 row = 1 request line

### Core Fields
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

---

## `analytics.fact_plan_budget`
### Grain
1 row = 1 year x item x dept

### Core Fields
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
- qty_tri1-4
- qty_buy_tri1-4
- qty_rcv_tri1-4
- approve_flag

---

## `analytics.fact_budget_summary`
### Grain
1 row = 1 fiscal year x budget type

### Core Fields
- fiscal_year
- budget_type
- budget_amount
- total_buy
- budget_remain
- debt
- tri1-4 budget
- tri1-4 spend
- burn_rate

---

## `analytics.fact_contract`
### Grain
1 row = 1 contract line

### Core Fields
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

---

# 13) SERVING DATASETS FOR DASHBOARD

> Dashboard app ควร query จาก `serve` เป็นหลัก  
> ไม่ควรยิง fact ดิบขนาดใหญ่ทุกหน้า

---

## `serve.exec_dashboard_daily`
### Purpose
Executive KPI summary รายวัน

### Fields
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

## `serve.inventory_risk_daily`
### Purpose
Risk table / heatmap / action items

### Fields
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

## `serve.expiry_lot_detail`
### Purpose
Lot-level expiry dashboard

### Fields
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

## `serve.consumption_monthly`
### Purpose
Consumption trend & top items

### Fields
- year_month
- working_code
- dept_id
- total_disp_qty
- total_disp_value
- avg_monthly_usage
- movement_class

---

## `serve.department_usage_summary`
### Purpose
Department utilization dashboard

### Fields
- year_month
- dept_id
- total_usage_qty
- total_usage_value
- usage_share_pct
- active_item_count

---

## `serve.plan_vs_actual_summary`
### Purpose
Planning & procurement monitoring

### Fields
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

## `serve.budget_burn_summary`
### Purpose
Budget dashboard

### Fields
- fiscal_year
- budget_type
- budget_name
- budget_amount
- total_buy
- budget_remain
- debt
- burn_rate

---

## `serve.movement_exception_summary`
### Purpose
Movement / adjustment / exception dashboard

### Fields
- movement_date
- dept_id
- working_code
- movement_direction
- rs_status
- movement_qty
- movement_value
- exception_flag
- exception_reason

---

# 14) DASHBOARD APP REQUIREMENTS

---

# 14.1 Technology Decision

## Recommended
# **Next.js + TypeScript**

### Why
- modern UI
- container-friendly
- SSR/CSR flexibility
- API route support
- strong ecosystem
- easy deployment on Debian

---

# 14.2 UI Stack

## Required
- Tailwind CSS
- shadcn/ui
- Apache ECharts

## Optional
- TanStack Table
- React Query / TanStack Query
- Zustand (state management)

---

# 14.3 Design Principles

- modern executive dashboard style
- responsive layout
- high readability
- color-coded risks
- consistent filter behavior
- printable / export-friendly
- mobile usable (at least read mode)

---

# 15) DASHBOARD MODULES

---

# 15.1 Executive Overview

### Purpose
แสดงภาพรวมคลังยา / ความเสี่ยง / งบประมาณ / การใช้

### Widgets
- KPI cards
- inventory trend
- consumption vs budget
- top high-risk items
- risk heatmap
- department summary

### Data Source
- `serve.exec_dashboard_daily`
- `serve.inventory_risk_daily`
- `serve.department_usage_summary`

---

# 15.2 Stock Position & Lot Intelligence

### Purpose
ดู stock คงเหลือแบบลงลึกถึง lot

### Widgets
- stock by department
- stock by location
- top value items
- lot detail table
- stock distribution

### Data Source
- `analytics.fact_inventory_snapshot`
- `serve.expiry_lot_detail`

---

# 15.3 Expiry & Dead Stock

### Purpose
ดูสินค้าหมดอายุ / ใกล้หมดอายุ / dead stock

### Widgets
- expiry buckets
- near expiry trend
- expired stock value
- dead stock table
- risk action table

### Data Source
- `serve.expiry_lot_detail`
- `serve.inventory_risk_daily`

---

# 15.4 Consumption & Utilization

### Purpose
วิเคราะห์การใช้จริง

### Widgets
- monthly usage trend
- top used items
- department comparison
- ABC / movement class
- DOS distribution

### Data Source
- `serve.consumption_monthly`
- `serve.department_usage_summary`

---

# 15.5 Planning & Budget

### Purpose
ดูแผนเทียบการใช้จริงและงบ

### Widgets
- plan vs actual trend
- budget burn
- variance by department
- overplanned / underplanned items

### Data Source
- `serve.plan_vs_actual_summary`
- `serve.budget_burn_summary`

---

# 15.6 Movement & Exceptions

### Purpose
ติดตาม movement ผิดปกติ / adjustment / anomalies

### Widgets
- movement trend
- exception counts
- movement type distribution
- adjustment detail table

### Data Source
- `serve.movement_exception_summary`
- `analytics.fact_inventory_movement`

---

# 16) API DESIGN

> Dashboard app ควรเข้าถึง PostgreSQL ผ่าน API layer  
> ไม่ควรให้ frontend เข้าฐานโดยตรง

---

# 16.1 API Style
REST API (v1)

---

# 16.2 Example Endpoints

---

## Executive
```http
GET /api/v1/dashboard/executive?date=2026-04-01
```

---

## Inventory Risk
```http
GET /api/v1/dashboard/inventory-risk?dept=ER&expiry_bucket=90
```

---

## Stock Position
```http
GET /api/v1/dashboard/stock-position?dept=WARD01&item=12345
```

---

## Consumption
```http
GET /api/v1/dashboard/consumption?from=2025-01-01&to=2026-03-31&dept=OPD
```

---

## Plan vs Budget
```http
GET /api/v1/dashboard/plan-budget?year=2026
```

---

## Movement Exceptions
```http
GET /api/v1/dashboard/movement-exceptions?from=2026-03-01&to=2026-03-31
```

---

# 16.3 API Response Format (recommended)

```json
{
  "success": true,
  "data": [],
  "meta": {
    "generated_at": "2026-04-01T09:00:00+07:00"
  }
}
```

---

# 17) AUTHORIZATION & ACCESS CONTROL

---

# 17.1 User Roles (recommended)

| Role | Access |
|---|---|
| EXEC | executive summary only |
| PHARM_HEAD | full pharmacy dashboards |
| STOCK_ADMIN | stock / movement / expiry |
| PLAN_BUDGET | planning / budget |
| ANALYST | advanced analytics |
| ADMIN | all modules |

---

# 17.2 Security Rules
- source DB credential never exposed to app users
- PostgreSQL app user should have least privilege
- ETL user separated from app read user
- all credentials via environment variables

---

# 18) PERFORMANCE DESIGN

---

# 18.1 Performance Principles

1. Query from `serve` first
2. Avoid raw full-table scans in app runtime
3. Use indexes on PostgreSQL for filter columns
4. Pre-aggregate monthly / daily datasets
5. Paginate large detail tables

---

# 18.2 Suggested PostgreSQL Index Targets

## Inventory Snapshot
- `snapshot_date`
- `working_code`
- `dept_id`
- `expired_date`

## Dispensing
- `disp_date`
- `working_code`
- `disp_dept`

## Budget
- `fiscal_year`
- `budget_type`

## Movement
- `operate_datetime`
- `working_code`
- `dept_id`
- `rs_status`

---

# 19) DATA QUALITY & VALIDATION

---

# 19.1 Validation Rules

## Rule DQ-01
Reject invalid date formats

## Rule DQ-02
Flag negative stock

## Rule DQ-03
Flag missing item master linkage

## Rule DQ-04
Flag missing department linkage

## Rule DQ-05
Flag missing vendor linkage

## Rule DQ-06
Flag null cost when quantity exists

## Rule DQ-07
Track unresolved MED_CODE → WORKING_CODE mappings

---

# 19.2 Reconciliation Checks

ควรมีรายงานตรวจสอบอย่างน้อย:

1. Total stock value by day
2. Total dispense qty by day
3. Budget used vs source
4. Count of orphan records
5. Count of invalid dates
6. Count of null critical keys

---

# 20) DEPLOYMENT ARCHITECTURE

---

# 20.1 Deployment Model

## Native Services
- PostgreSQL (native on Debian)

## Containerized Services
- ETL / Sync Service
- Dashboard App
- optional Reverse Proxy

---

# 20.2 Recommended Runtime Components

```text
postgresql-native
etl-sync-container
dashboard-app-container
nginx-container (optional)
```

---

# 20.3 Recommended Folder Structure

```text
project-root/
├── etl/
│   ├── jobs/
│   ├── loaders/
│   ├── transforms/
│   ├── config/
│   └── main.py
├── dashboard/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── services/
│   └── package.json
├── sql/
│   ├── staging/
│   ├── analytics/
│   └── serve/
├── docker/
│   ├── etl/
│   ├── dashboard/
│   └── nginx/
├── .env
└── docker-compose.yml
```

---

# 20.4 Docker Compose Concept

## Services
- `dashboard-app`
- `etl-sync`
- optional `nginx`

> PostgreSQL ใช้ native service เดิม ไม่จำเป็นต้อง containerize ถ้าเครื่องพร้อมอยู่แล้ว

---

# 21) BUILD PLAN

---

# Phase 1 — Data Foundation
### Deliverables
- ETL master sync
- ETL inventory snapshot
- PostgreSQL schemas
- dimensions + core facts

### Outcome
พร้อมทำ dashboard พื้นฐาน

---

# Phase 2 — Core Dashboard MVP
### Deliverables
- Executive Overview
- Stock Position
- Expiry Dashboard
- Consumption Dashboard

### Outcome
เริ่มใช้งานจริงได้

---

# Phase 3 — Planning / Budget / Movement
### Deliverables
- Planning dashboard
- Budget dashboard
- Movement / exception dashboard

### Outcome
พร้อมใช้เชิงบริหารเต็มรูปแบบ

---

# Phase 4 — Productization
### Deliverables
- role-based access
- export
- print
- alert center
- watchlists
- optional API integrations

---

# 22) MVP BUILD PRIORITY

ให้เริ่มจากของที่ “impact สูง + data ชัด + build แล้วใช้ได้ทันที”

1. Inventory Value
2. Active Stocked SKU Count
3. Low Stock SKU Count
4. Near Expiry Value
5. Expired Stock Value
6. Dead Stock Value
7. Consumption Quantity
8. Consumption Value
9. DOS
10. Budget Used
11. Budget Remaining
12. Budget Burn Rate
13. Plan vs Actual
14. Top Risk Items
15. Department Usage Summary

---

# 23) RECOMMENDED TEAM WORK SPLIT

---

## Data / ETL
- Python ETL jobs
- PostgreSQL load
- snapshot logic
- validation / reconciliation

---

## Analytics / BI Logic
- fact / dim model
- serve datasets
- KPI formulas
- metric governance

---

## App / Frontend
- dashboard pages
- charts
- filters
- drilldown
- export / UX

---

## Infra / DevOps
- Docker deployment
- environment config
- reverse proxy
- backup / logs / monitoring

---

# 24) RISKS & MITIGATIONS

| Risk | Impact | Mitigation |
|---|---|---|
| Source schema changes | sync fails | schema inspection + ETL validation |
| MED_CODE mapping inconsistency | wrong usage KPI | mapping QA table |
| snapshot not retained | no trend | enforce daily snapshot job |
| direct query temptation | source load | app only connects to PostgreSQL |
| duplicated KPI logic | inconsistent numbers | centralize logic in `analytics` / `serve` |
| slow dashboard | poor adoption | pre-aggregate serve layer |

---

# 25) FINAL ARCHITECTURE DECISION SUMMARY

## Chosen Production Architecture

### Source
**MariaDB `invs2019`**
- Read-only only
- no object creation
- no analytics dependency at runtime

### Analytics
**PostgreSQL**
- staging
- data mart
- KPI logic
- snapshots
- serving datasets

### ETL
**Python**
- sync / transform / refresh

### Dashboard App
**Next.js + TypeScript**
- executive-grade UI
- charts
- filters
- responsive
- container-friendly

### Charts
**Apache ECharts**
- modern / flexible / beautiful

### Deployment
**Docker Compose on Debian**
- practical
- maintainable
- production-friendly

---

# 26) FINAL RECOMMENDATION

สถาปัตยกรรมนี้เป็นแนวทางที่เหมาะสมที่สุดภายใต้ข้อจำกัดจริงของระบบ และเหมาะกับบริบทโรงพยาบาล / องค์กรที่ต้องการ:

- ความปลอดภัย
- ความเสถียร
- ความสามารถในการขยาย
- dashboard ที่ดูดีและใช้งานได้จริง

มันไม่ใช่แค่ “ทำ dashboard ให้ขึ้น”
แต่มันคือการวางฐานให้ระบบ analytics โตต่อได้อย่างมีวินัย

---

# END OF DOCUMENT