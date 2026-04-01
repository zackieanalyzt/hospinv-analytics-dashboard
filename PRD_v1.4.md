# PRD v1.4 — Project Bootstrap Spec
## Inventory & Medical Supply Intelligence Dashboard
### Architecture: MariaDB (`invs2019`) → PostgreSQL → Dashboard App

**Version:** 1.4  
**Status:** Bootstrap / Build Initialization Spec  
**Last Updated:** 2026-04-01  
**Document Type:** Project Bootstrap Specification  

---

# 1) PURPOSE

เอกสารฉบับนี้กำหนดแนวทางเริ่มต้นโครงการ (Project Bootstrap) สำหรับระบบ:

# **Inventory & Medical Supply Intelligence Dashboard**

โดยมีเป้าหมายเพื่อให้ทีมสามารถ:
- เริ่มสร้างระบบได้ทันที
- เข้าใจโครงสร้างโปรเจกต์ตั้งแต่วันแรก
- ลดความสับสนระหว่าง ETL / DB / API / Frontend
- วางมาตรฐานสำหรับการพัฒนาแบบ maintainable

---

# 2) PROJECT OBJECTIVE

สร้างระบบ dashboard วิเคราะห์ข้อมูลคลังยาและเวชภัณฑ์ โดยใช้สถาปัตยกรรม:

```text
MariaDB (invs2019) [READ ONLY]
        ↓
Python ETL / Sync
        ↓
PostgreSQL Analytics
        ↓
Dashboard App (Next.js)
```

---

# 3) CORE DESIGN RULES

---

## R-01) No Write to Source DB
ห้ามเขียน / สร้าง / แก้ / alter / insert / update / delete บน `invs2019`

---

## R-02) PostgreSQL = Analytics Core
ทุกอย่างที่เป็น:
- mart
- KPI
- snapshot
- serve datasets

ต้องอยู่ใน PostgreSQL

---

## R-03) Dashboard App Must Not Query Source Directly
Dashboard app เชื่อมต่อ PostgreSQL เท่านั้น

---

## R-04) ETL and App Must Be Separate Concerns
แยก:
- ETL jobs
- dashboard app
- SQL model
- deployment config

ออกจากกันอย่างชัดเจน

---

# 4) RECOMMENDED TECH STACK

---

## Data Extraction / ETL
- Python 3.12+
- SQLAlchemy
- psycopg
- pymysql
- polars (preferred) or pandas
- APScheduler or cron

---

## Analytics Database
- PostgreSQL 16+

---

## Dashboard App
- Next.js 15
- TypeScript
- Tailwind CSS
- shadcn/ui
- Apache ECharts
- TanStack Table

---

## Deployment
- Docker Compose
- Debian Server
- Nginx reverse proxy

---

# 5) REPOSITORY STRATEGY

---

# 5.1 Recommended Repository Model

## Option A (Recommended)
# **Monorepo**

```text
inventory-dashboard-platform/
├── etl/
├── dashboard/
├── sql/
├── docs/
├── docker/
├── scripts/
├── .env.example
├── docker-compose.yml
└── README.md
```

### Why
- ดูแลง่าย
- versioning ชัด
- sync dev ง่าย
- เหมาะกับทีมเล็กถึงกลาง

---

## Option B
Multi-repo

### Use only if
- มีหลายทีมแยกกันชัดเจน
- DevOps mature แล้ว

### Recommendation
**ยังไม่จำเป็น**

---

# 6) RECOMMENDED PROJECT STRUCTURE

```text
inventory-dashboard-platform/
├── docs/
│   ├── PRD_v1.md
│   ├── PRD_v1.1.md
│   ├── PRD_v1.2.md
│   ├── PRD_v1.3.md
│   ├── PRD_v1.4.md
│   └── PRD_v1.5.md
│
├── etl/
│   ├── app/
│   │   ├── config/
│   │   ├── db/
│   │   ├── extractors/
│   │   ├── loaders/
│   │   ├── transforms/
│   │   ├── jobs/
│   │   ├── utils/
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── dashboard/
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── lib/
│   ├── services/
│   ├── hooks/
│   ├── types/
│   ├── public/
│   ├── package.json
│   ├── Dockerfile
│   └── .env.example
│
├── sql/
│   ├── staging/
│   ├── analytics/
│   ├── serve/
│   ├── indexes/
│   └── validation/
│
├── docker/
│   ├── etl/
│   ├── dashboard/
│   └── nginx/
│
├── scripts/
│   ├── bootstrap.sh
│   ├── run_etl.sh
│   └── backup_pg.sh
│
├── .env.example
├── docker-compose.yml
└── README.md
```

---

# 7) MODULE RESPONSIBILITY MAP

---

## 7.1 `etl/`
### Responsibility
- ดึงข้อมูลจาก MariaDB
- แปลงข้อมูล
- โหลดเข้า PostgreSQL
- สร้าง snapshot
- refresh serving datasets

---

## 7.2 `dashboard/`
### Responsibility
- UI / UX
- charts
- filters
- drilldown
- role-based dashboard pages
- export / print

---

## 7.3 `sql/`
### Responsibility
- SQL definitions
- table creation scripts
- indexes
- serving datasets
- validation queries

---

## 7.4 `docs/`
### Responsibility
- PRD
- technical notes
- onboarding docs
- deployment notes

---

# 8) ENVIRONMENT STRATEGY

---

# 8.1 Recommended Environments

| Environment | Purpose |
|---|---|
| local | development |
| dev | shared testing |
| staging | pre-production |
| prod | production |

---

# 8.2 Environment Variables Strategy

ใช้ `.env` แยกแต่ละ service

---

## Root `.env.example`
```env
APP_ENV=development
TZ=Asia/Bangkok
```

---

## `etl/.env.example`
```env
SRC_DB_HOST=192.168.x.x
SRC_DB_PORT=3306
SRC_DB_NAME=invs2019
SRC_DB_USER=readonly_user
SRC_DB_PASSWORD=changeme

PG_HOST=192.168.x.x
PG_PORT=5432
PG_DB=inventory_analytics
PG_USER=analytics_writer
PG_PASSWORD=changeme

LOG_LEVEL=INFO
BATCH_SIZE=5000
```

---

## `dashboard/.env.example`
```env
NEXT_PUBLIC_APP_NAME=Inventory Intelligence Dashboard
NEXT_PUBLIC_API_BASE_URL=http://localhost:3000/api

PG_HOST=192.168.x.x
PG_PORT=5432
PG_DB=inventory_analytics
PG_USER=dashboard_reader
PG_PASSWORD=changeme

APP_SECRET=changeme
```

---

# 9) NAMING CONVENTIONS

---

# 9.1 General Rules
- ใช้ `snake_case` สำหรับ DB / Python
- ใช้ `kebab-case` สำหรับ URL / folder ที่เหมาะสม
- ใช้ `PascalCase` สำหรับ React components
- ใช้ `camelCase` สำหรับ JS/TS variables/functions

---

# 9.2 PostgreSQL Naming
### Schemas
- `stg`
- `analytics`
- `serve`

### Tables
- `dim_*`
- `fact_*`
- `*_summary`
- `*_daily`
- `*_monthly`

### Examples
- `analytics.dim_product`
- `analytics.fact_inventory_snapshot`
- `serve.exec_dashboard_daily`

---

# 9.3 API Naming
### Pattern
```text
/api/v1/dashboard/{module-name}
```

### Examples
- `/api/v1/dashboard/executive`
- `/api/v1/dashboard/inventory-risk`
- `/api/v1/dashboard/consumption`

---

# 9.4 React Component Naming
### Examples
- `KpiCard.tsx`
- `InventoryRiskTable.tsx`
- `ConsumptionTrendChart.tsx`
- `BudgetBurnGauge.tsx`

---

# 10) ETL APPLICATION DESIGN

---

# 10.1 ETL Folder Structure

```text
etl/app/
├── config/
│   ├── settings.py
│   └── logging.py
├── db/
│   ├── source_mariadb.py
│   └── target_postgres.py
├── extractors/
│   ├── master_extractor.py
│   ├── inventory_extractor.py
│   └── transaction_extractor.py
├── loaders/
│   ├── staging_loader.py
│   └── analytics_loader.py
├── transforms/
│   ├── normalize_dates.py
│   ├── build_dimensions.py
│   ├── build_facts.py
│   └── build_serve.py
├── jobs/
│   ├── sync_master.py
│   ├── sync_transactions.py
│   ├── snapshot_inventory.py
│   └── refresh_serve.py
├── utils/
│   ├── validators.py
│   └── helpers.py
└── main.py
```

---

# 10.2 ETL Job Categories

| Job | Purpose |
|---|---|
| sync_master | sync master tables |
| sync_transactions | incremental transaction sync |
| snapshot_inventory | daily stock snapshot |
| snapshot_budget | daily budget snapshot |
| build_analytics | build fact/dim |
| refresh_serve | refresh serving datasets |

---

# 11) DASHBOARD APPLICATION DESIGN

---

# 11.1 Dashboard App Structure

```text
dashboard/
├── app/
│   ├── (auth)/
│   ├── (dashboard)/
│   │   ├── executive/
│   │   ├── stock/
│   │   ├── expiry/
│   │   ├── consumption/
│   │   ├── planning/
│   │   ├── budget/
│   │   └── movement/
│   ├── api/
│   │   └── v1/
│   │       └── dashboard/
│   └── layout.tsx
│
├── components/
│   ├── ui/
│   ├── charts/
│   ├── tables/
│   ├── filters/
│   └── cards/
│
├── features/
│   ├── executive/
│   ├── stock/
│   ├── expiry/
│   ├── consumption/
│   ├── planning/
│   ├── budget/
│   └── movement/
│
├── lib/
│   ├── db.ts
│   ├── auth.ts
│   ├── query.ts
│   └── utils.ts
│
├── services/
│   ├── executive.service.ts
│   ├── stock.service.ts
│   ├── expiry.service.ts
│   └── ...
│
├── hooks/
├── types/
└── public/
```

---

# 11.2 App Routing Strategy

### Dashboard Pages
- `/dashboard/executive`
- `/dashboard/stock`
- `/dashboard/expiry`
- `/dashboard/consumption`
- `/dashboard/planning`
- `/dashboard/budget`
- `/dashboard/movement`

---

# 12) COMPONENT DESIGN STANDARDS

---

## Reusable UI Components
- `KpiCard`
- `SectionHeader`
- `DateRangeFilter`
- `DepartmentFilter`
- `InventoryTable`
- `TrendLineChart`
- `RiskHeatmap`
- `TopItemsBarChart`

---

## Chart Components
- `InventoryValueTrendChart`
- `BudgetBurnGauge`
- `ExpiryBucketChart`
- `DepartmentUsageChart`
- `PlanVsActualChart`

---

# 13) SQL MANAGEMENT STRATEGY

---

# 13.1 SQL Folder Rules

```text
sql/
├── staging/
├── analytics/
├── serve/
├── indexes/
└── validation/
```

---

## Purpose
- `staging/` = raw/staging create scripts
- `analytics/` = dim/fact build scripts
- `serve/` = serving layer SQL
- `indexes/` = indexes for performance
- `validation/` = QA / reconciliation SQL

---

# 14) CONFIGURATION MANAGEMENT

---

## Required Config Domains
- database connection
- batch size
- timezone
- logging level
- refresh schedule
- app branding

---

# 15) LOGGING STRATEGY

---

## ETL Logs
ควร log อย่างน้อย:
- job start / end
- row count
- duration
- failures
- retry attempts

---

## App Logs
ควร log:
- API error
- query failure
- auth failure
- page error

---

# 16) ERROR HANDLING RULES

---

## ETL
- ถ้า master sync fail → stop downstream jobs
- ถ้า transaction sync fail → retry ได้
- ถ้า serve refresh fail → แจ้งเตือนแต่ไม่ล้มทั้งระบบ

---

## Dashboard App
- ถ้า query fail → show graceful error
- ถ้า dataset ว่าง → show “no data”
- ห้ามโชว์ raw DB error บน UI

---

# 17) TESTING STRATEGY

---

## ETL Tests
- source connection test
- target connection test
- row count validation
- schema validation
- date normalization validation

---

## App Tests
- route render test
- API response test
- filter behavior test
- chart render test

---

# 18) SECURITY BOOTSTRAP CHECKLIST

- [ ] source DB user = read only
- [ ] PostgreSQL ETL user separated from app reader user
- [ ] secrets not committed to git
- [ ] `.env.example` only, not real secrets
- [ ] app uses backend-only DB access
- [ ] HTTPS planned for production

---

# 19) INITIAL DEVELOPMENT ROADMAP

---

## Sprint 0 — Bootstrap
- initialize repo
- setup folder structure
- setup Python ETL project
- setup Next.js dashboard app
- setup PostgreSQL schemas
- setup Docker Compose

---

## Sprint 1 — Data Foundation
- sync master tables
- sync inventory snapshot
- build dimensions
- build inventory fact

---

## Sprint 2 — Dashboard MVP
- executive page
- stock page
- expiry page

---

## Sprint 3 — Consumption / Budget
- consumption page
- budget page
- plan vs actual

---

## Sprint 4 — Hardening
- auth
- logging
- validation
- performance tuning

---

# 20) DEFINITION OF DONE (BOOTSTRAP)

Project bootstrap ถือว่า “เสร็จ” เมื่อ:

- repo structure พร้อม
- ETL project รันได้
- dashboard app รันได้
- PostgreSQL schema พร้อม
- `.env.example` พร้อม
- Docker build ผ่าน
- README พร้อมสำหรับ onboard dev

---

# 21) FINAL RECOMMENDATION

อย่ากระโดดไปเขียน dashboard ก่อนโดยไม่มี bootstrap ที่ชัด  
เพราะสุดท้ายจะได้ “เว็บสวย + SQL กระจัดกระจาย + deploy แล้วร้องไห้”

Project Bootstrap ที่ดี คือสิ่งที่ทำให้:
- โค้ดไม่เละ
- คนใหม่เข้าทีมแล้วไม่หลง
- ระบบโตต่อได้

---

# END OF DOCUMENT