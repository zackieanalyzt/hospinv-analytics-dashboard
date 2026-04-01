# PRD v1 & v1.1  
## Inventory & Medical Supply Intelligence Dashboard  
### Based on MariaDB schema `invslee / invs2019`

**Version:** 1.1 Bundle  
**Status:** Build-Ready (Concept + Spec)  
**Last Updated:** 2026-04-01  

---

# ================================
# PART 1 — PRD v1 (PRODUCT LEVEL)
# ================================

# 1) BACKGROUND

ระบบคลังยาและเวชภัณฑ์มีข้อมูลจำนวนมาก แต่กระจัดกระจายในรูปแบบ transactional tables ทำให้:

- มองไม่เห็นภาพรวม inventory
- คาดการณ์ไม่ได้
- ไม่เห็นความเสี่ยง เช่น stockout / expiry
- วิเคราะห์ procurement / budget ไม่ได้เชิงบริหาร

ดังนั้นต้องมี **Dashboard เชิงวิเคราะห์ (Analytical Dashboard)**

---

# 2) PRODUCT VISION

สร้างระบบ Dashboard ที่:
- รวมข้อมูลจากทุก flow ของคลังยา
- แสดง insight เชิงบริหาร
- drill down ถึงระดับ item / lot / department
- รองรับทั้ง operational + strategic decision

---

# 3) BUSINESS OBJECTIVES

1. ลด stockout
2. ลด near-expiry / expired loss
3. เพิ่ม forecast accuracy
4. เพิ่ม efficiency procurement
5. คุมงบประมาณ
6. เพิ่ม visibility ของคลัง

---

# 4) SCOPE

## In Scope
- Dashboard 8 โมดูล
- KPI + Trend + Drilldown
- Export
- Filter

## Out of Scope
- Data entry
- Approval workflow
- AI forecasting ขั้นสูง (v1)
- External integrations

---

# 5) USERS

| Role | Needs |
|---|---|
| Executive | ภาพรวม + risk |
| Head Pharmacist | stock / expiry |
| Procurement | supplier / PO |
| Finance | budget |
| QC | quality |
| Department | usage |

---

# 6) CORE CONCEPT

> One Source → Multiple Decision Views

---

# 7) DASHBOARD MODULES

1. Executive Overview  
2. Stock Position  
3. Expiry & Dead Stock  
4. Consumption  
5. Procurement  
6. Receiving & QC  
7. Returns / Adjustment  
8. Planning & Budget  

---

# 8) DATA SOURCES

## Master
- drug_gn
- drug_vn
- company
- dept_id

## Transaction
- inv_md / inv_md_c
- card
- dispensed
- accr_disp

## Planning / Budget
- buyplan / buyplan_c
- bdg_amt / bdg_type

---

# 9) ARCHITECTURE

```
Source (MariaDB)
   ↓
Staging
   ↓
Data Mart (fact + dim)
   ↓
BI (Superset / Power BI)
```

---

# 10) RISKS

| Risk | Impact | Mitigation |
|---|---|---|
| KPI definition mismatch | ตัวเลขไม่ตรง | KPI dictionary |
| No FK | join ผิด | mart layer |
| mixed keys | duplication | canonical keys |
| snapshot overwrite | lost history | snapshot ETL |

---

# 11) DELIVERY PLAN

## Phase 1
- Executive
- Stock
- Consumption

## Phase 2
- Procurement
- QC
- Returns

## Phase 3
- Planning
- Budget

---

# ================================
# PART 2 — PRD v1.1 (SPEC LEVEL)
# ================================

# 12) KPI GOVERNANCE

## Canonical Keys
- WORKING_CODE
- TRADE_CODE
- DEPT_ID
- LOT_NO
- BUDGET_TYPE

---

## Source Authority

| Domain | Table |
|---|---|
| Inventory | inv_md_c |
| Movement | card |
| Consumption | dispensed |
| Planning | buyplan_c |
| Budget | bdg_amt |

---

# 13) KPI DICTIONARY

---

## KPI-001: Total Inventory Value
SUM(QTY_ON_HAND * COST)

Source:
- inv_md_c.LOT_VALUE
- inv_md_c.QTY_ON_HAND
- inv_md_c.LOT_COST

---

## KPI-002: Active SKU Count
COUNT(DISTINCT WORKING_CODE WHERE QTY > 0)

---

## KPI-003: Low Stock
QTY < REORDER_QTY or MIN_LEVEL

---

## KPI-004: Near Expiry
expiry <= 90 days

---

## KPI-005: Dead Stock
no movement >= 180 days

Source:
- card.OPERATE_DATE

---

## KPI-006: Consumption Qty
SUM(dispensed.DISP_QTY)

---

## KPI-007: Consumption Value
disp_qty * cost

---

## KPI-008: DOS
stock / avg_daily_usage

---

## KPI-009: Plan vs Actual
(actual - plan) / plan

---

## KPI-010: Budget Burn Rate
used / allocated

---

# 14) DATA MAPPING MATRIX

---

## Inventory

| KPI | Table | Column |
|---|---|---|
| stock | inv_md_c | QTY_ON_HAND |
| value | inv_md_c | LOT_VALUE |
| expiry | inv_md_c | EXPIRED_DATE |

---

## Movement

| KPI | Table | Column |
|---|---|---|
| movement | card | ACTIVE_QTY |
| value | card | VALUE |
| date | card | OPERATE_DATE |

---

## Consumption

| KPI | Table | Column |
|---|---|---|
| qty | dispensed | DISP_QTY |
| date | dispensed | DISP_DATE |
| dept | dispensed | DISP_DEPT |

---

## Planning

| KPI | Table | Column |
|---|---|---|
| plan qty | buyplan_c | QTY_THIS_YEAR |
| forecast | buyplan_c | QTY_FORECAST |
| buy value | buyplan_c | BUY_VALUE |

---

## Budget

| KPI | Table | Column |
|---|---|---|
| allocated | bdg_amt | BUDGET_AMOUNT |
| used | bdg_amt | TOTAL_BUY |
| remain | bdg_amt | BUDGET_REMAIN |

---

# 15) DASHBOARD SCREEN SPEC

---

# Screen 1: Executive

KPI:
- Inventory Value
- Low Stock
- Near Expiry
- Budget Burn

Charts:
- trend
- top items
- risk heatmap

---

# Screen 2: Stock

- stock by dept
- stock by location
- lot table

---

# Screen 3: Expiry

- expiry buckets
- dead stock

---

# Screen 4: Consumption

- monthly usage
- top items
- ABC

---

# Screen 5: Procurement

- spend by vendor
- lead time
- price trend

---

# Screen 6: QC

- pass rate
- fail rate

---

# Screen 7: Returns

- return trend
- return reason

---

# Screen 8: Planning / Budget

- plan vs actual
- budget usage

---

# 16) FILTERS

- date
- department
- item
- vendor
- budget
- expiry bucket

---

# 17) ALERT RULES

| Alert | Rule |
|---|---|
| Low Stock | qty < min |
| Out of Stock | qty = 0 |
| Near Expiry | <= 90 days |
| Dead Stock | no movement 180 days |
| Budget Risk | >85% used |

---

# 18) FINAL NOTE

Dashboard ที่ดี:
- ไม่ใช่แค่กราฟ
- ต้องตอบคำถาม
- และต้อง “ทำให้คนตัดสินใจได้”

---

# END