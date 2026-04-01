# PRD v1.2 — Field-Level Mapping Spec
## Inventory & Medical Supply Intelligence Dashboard
### Database Source: MariaDB schema `invs2019`

**Version:** 1.2  
**Status:** Working Draft / Build-Ready  
**Primary Use:** BI / Data Engineering / Dashboard Build  
**Last Updated:** 2026-04-01

---

# 1) PURPOSE

เอกสารฉบับนี้ใช้เพื่อระบุ **Field-Level Mapping Specification** สำหรับการพัฒนา Dashboard แสดง Insight ของระบบคลังยาและเวชภัณฑ์ โดยอิงจากฐานข้อมูล MariaDB ชุด `invs2019`

เป้าหมายหลัก:
- แปลง source schema ให้พร้อมใช้งานใน BI / Analytics
- นิยาม KPI ที่นำไป implement ได้จริง
- กำหนด authoritative source สำหรับตัวเลขสำคัญ
- ระบุ join logic / transformation / caveats อย่างชัดเจน

---

# 2) SCOPE

ครอบคลุม 8 กลุ่ม dashboard หลัก:

1. Executive Overview
2. Stock Position & Lot Intelligence
3. Expiry & Dead Stock
4. Consumption & Utilization
5. Procurement & Supplier Performance
6. Receiving & QC (เฉพาะส่วนที่มี source รองรับ)
7. Returns / Adjustments / Exceptions
8. Planning vs Actual / Budget

---

# 3) SOURCE SYSTEM OVERVIEW

---

## 3.1 Core Master Tables

| Table | Role |
|---|---|
| `drug_gn` | Item master (generic / working item) |
| `drug_vn` | Trade/vendor item master |
| `company` | Vendor / manufacturer master |
| `dept_id` | Department / stock owner master |
| `dept_map` | Mapping between inventory dept and HIS dept |
| `dosage_form` | Dosage form reference |
| `drug_compos` | Composition / ingredient reference |
| `ed_group` | Grouping / formulary grouping |
| `hosp_list` | Hospital item category |

---

## 3.2 Core Transaction / Inventory Tables

| Table | Role |
|---|---|
| `inv_md` | Inventory summary per item x dept |
| `inv_md_c` | Inventory lot/detail per item x trade x lot x dept |
| `card` | Inventory movement / stock card |
| `dispensed` | Dispense / usage transaction |
| `accr_disp` | Request / accrued dispensing transaction |

---

## 3.3 Planning / Budget / Procurement Tables

| Table | Role |
|---|---|
| `buyplan` | Purchase planning header / summary |
| `buyplan_c` | Purchase planning detail |
| `buyplan_log` | Planning change log |
| `buy_re_m` | Monthly purchase summary |
| `buy_re_y` | Yearly purchase summary |
| `bdg_amt` | Budget amount / usage summary |
| `bdg_type` | Budget type reference |
| `cnt` | Contract header |
| `cnt_c` | Contract detail |

---

## 3.4 Workflow / Operational Tables

| Table | Role |
|---|---|
| `doc_flow` | Document routing / workflow |
| `doc_flow_c` | Document routing detail |
| `adj_reason` | Adjustment reason reference |
| `focus_list` | User focus/watch list |
| `focus_list_c` | User focus/watch list detail |

---

# 4) DATA MODELING PRINCIPLES

---

## 4.1 Authoritative Data Sources

| Subject Area | Primary Table | Secondary / Support |
|---|---|---|
| Product Master | `drug_gn` | `drug_vn`, `dosage_form`, `drug_compos` |
| Vendor Master | `company` | `drug_vn` |
| Department Master | `dept_id` | `dept_map` |
| Inventory Snapshot | `inv_md_c` | `inv_md`, `drug_gn` |
| Inventory Movement | `card` | `adj_reason` |
| Consumption | `dispensed` | `accr_disp`, `dept_map`, `card` |
| Planning | `buyplan_c` | `buyplan`, `buyplan_log` |
| Budget | `bdg_amt` | `bdg_type` |
| Contract | `cnt_c` | `cnt` |

---

## 4.2 Canonical Business Keys

| Business Entity | Canonical Key |
|---|---|
| Item | `WORKING_CODE` |
| Trade Item | `TRADE_CODE` |
| Vendor | `COMPANY_CODE` / `VENDOR_CODE` |
| Department | `DEPT_ID` |
| Budget | `BUDGET_TYPE` |
| Contract | `CNT_NO` |
| Stock Movement | `RECORD_NUMBER` (in `card`) |
| Dispense Event | `RECORD_NUMBER` (in `dispensed`) |
| Lot | `TRADE_CODE + LOT_NO + EXPIRED_DATE + DEPT_ID` |

---

## 4.3 Date Normalization Rules

**Important:** หลายตารางเก็บวันที่เป็น `char(8)` เช่น `YYYYMMDD`

ต้อง normalize ให้เป็น `DATE` หรือ `DATETIME` ก่อนใช้งานใน mart

### Standard conversion pattern
```sql
STR_TO_DATE(char8_col, '%Y%m%d')
```

### Fields requiring normalization (not exhaustive)
- `DISP_DATE`
- `REQ_DATE`
- `CONFIRM_DATE`
- `R_S_DATE`
- `EXPIRED_DATE`
- `LAST_RCV_DATE`
- `AUTH_DATE`
- `CNT_DATE`
- `GF_DATE`

---

# 5) RECOMMENDED ANALYTICS LAYER

---

# 5.1 Dimensions

---

## DIM_PRODUCT

### Source
`drug_gn`

### Grain
1 row = 1 `WORKING_CODE`

### Fields

| Output Column | Source Table | Source Column | Rule / Note |
|---|---|---|---|
| product_key | generated | - | surrogate key |
| working_code | `drug_gn` | `WORKING_CODE` | canonical item key |
| drug_name | `drug_gn` | `DRUG_NAME` | English/main name |
| drug_name_th | `drug_gn` | `DRUG_NAME_TH` | Thai name if available |
| dosage_form_name | `drug_gn` | `DOSAGE_FORM` | raw dosage form text |
| sale_unit | `drug_gn` | `SALE_UNIT` | display unit |
| composition | `drug_gn` | `COMPOSITION` | composition text |
| group_code | `drug_gn` | `GROUP_CODE` | item group |
| group_key | `drug_gn` | `GROUP_KEY` | category key |
| supply_type | `drug_gn` | `SUPPLY_TYPE` | medicine / supply grouping |
| reorder_qty | `drug_gn` | `REORDER_QTY` | reorder threshold |
| min_level | `drug_gn` | `MIN_LEVEL` | min stock |
| max_level | `drug_gn` | `MAX_LEVEL` | max stock |
| rate_per_month | `drug_gn` | `RATE_PER_MONTH` | estimated usage |
| qty_unit | `drug_gn` | `QTY_UNIT` | quantity per pack or unit |
| pack_unit | `drug_gn` | `PACK_UNIT` | pack unit |
| std_price1 | `drug_gn` | `STD_PRICE1` | reference price |
| last_buy_cost | `drug_gn` | `LAST_BUY_COST` | last purchase cost |
| last_vendor_code | `drug_gn` | `LAST_VENDOR_CODE` | vendor linkage |
| is_ed | `drug_gn` | `IS_ED` | essential drug flag |
| hosp_list | `drug_gn` | `HOSP_LIST` | hospital list category |
| hide_flag | `drug_gn` | `HIDE` | active/inactive filter |
| abc_flag | `inv_md` | `ABC_FLAG` | optional denormalized latest ABC |
| active_flag | derived | - | `CASE WHEN HIDE IS NULL OR HIDE <> 'Y' THEN 1 ELSE 0 END` |

---

## DIM_TRADE_PRODUCT

### Source
`drug_vn`

### Grain
1 row = 1 `TRADE_CODE`

### Fields

| Output Column | Source Table | Source Column | Rule / Note |
|---|---|---|---|
| trade_product_key | generated | - | surrogate key |
| trade_code | `drug_vn` | `TRADE_CODE` | canonical trade key |
| working_code | `drug_vn` | `WORKING_CODE` | joins to `dim_product` |
| vendor_code | `drug_vn` | `VENDOR_CODE` | joins to vendor |
| manufac_code | `drug_vn` | `MANUFAC_CODE` | manufacturer |
| trade_name | `drug_vn` | `TRADE_NAME` | brand/trade name |
| pack_ratio | `drug_vn` | `PACK_RATIO` | pack conversion |
| buy_unit_cost | `drug_vn` | `BUY_UNIT_COST` | current purchase cost |
| sale_unit_price | `drug_vn` | `SALE_UNIT_PRICE` | optional display |
| unit_price | `drug_vn` | `UNIT_PRICE` | optional price |
| record_status | `drug_vn` | `RECORD_STATUS` | active record flag |
| bar_code | `drug_vn` | `BAR_CODE` | barcode |
| gtin | `drug_vn` | `GTIN` | GTIN |
| tmtid | `drug_vn` | `TMTID` | terminology mapping |
| atc | `drug_vn` | `ATC` | classification |
| import_flag | `drug_vn` | `IMPORT_FLAG` | import/local |
| issue_date | `drug_vn` | `ISSUE_DATE` | created date |
| hide_flag | `drug_vn` | `HIDE` | active/inactive |

---

## DIM_VENDOR

### Source
`company`

### Grain
1 row = 1 `COMPANY_CODE`

### Fields

| Output Column | Source Table | Source Column | Rule / Note |
|---|---|---|---|
| vendor_key | generated | - | surrogate key |
| company_code | `company` | `COMPANY_CODE` | canonical vendor key |
| company_name | `company` | `COMPANY_NAME` | vendor name |
| vendor_flag | `company` | `VENDOR_FLAG` | supplier flag |
| manufac_flag | `company` | `MANUFAC_FLAG` | manufacturer flag |
| tax_id | `company` | `TAX_ID` | optional |
| tel | `company` | `TEL` | optional |
| email | `company` | `EMAIL` | optional |
| due_days | `company` | `DUE_DAYS` | payment / due behavior |
| order_time | `company` | `ORDER_TIME` | potential lead time hint |
| business_type | `company` | `BUSINESS_TYPE` | classification |
| hide_flag | `company` | `HIDE` | active/inactive |

---

## DIM_DEPARTMENT

### Source
`dept_id`

### Grain
1 row = 1 `DEPT_ID`

### Fields

| Output Column | Source Table | Source Column | Rule / Note |
|---|---|---|---|
| department_key | generated | - | surrogate key |
| dept_id | `dept_id` | `DEPT_ID` | canonical department key |
| dept_name | `dept_id` | `DEPT_NAME` | department name |
| keep_inv | `dept_id` | `KEEP_INV` | keeps inventory flag |
| inv_type | `dept_id` | `INV_TYPE` | inventory type |
| dept_type | `dept_id` | `DEPT_TYPE` | department type |
| disp_dept | `dept_id` | `DISP_DEPT` | mapped dispensing dept |
| cost_center_id | `dept_id` | `cost_center_id` | finance alignment |
| hide_flag | `dept_id` | `HIDE` | active/inactive |

---

## DIM_BUDGET

### Source
`bdg_type`

### Grain
1 row = 1 `BUDGET_TYPE`

### Fields

| Output Column | Source Table | Source Column | Rule / Note |
|---|---|---|---|
| budget_key | generated | - | surrogate key |
| budget_type | `bdg_type` | `BUDGET_TYPE` | canonical budget key |
| budget_name | `bdg_type` | `BUDGET_NAME` | display name |
| budget_amount_default | `bdg_type` | `BUDGET_AMOUNT` | optional |
| total_buy_default | `bdg_type` | `TOTAL_BUY` | optional |
| express_type | `bdg_type` | `EXPRESS_TYPE` | optional grouping |
| default_flag | `bdg_type` | `DEFAULT_FLAG` | optional |
| hide_flag | `bdg_type` | `HIDE` | active/inactive |

---

## DIM_DATE

Standard calendar dimension.

### Minimum fields
- date_key
- full_date
- day
- month
- month_name
- quarter
- year
- fiscal_year
- month_start_flag
- quarter_start_flag
- year_start_flag

---

# 5.2 Facts

---

## FACT_INVENTORY_SNAPSHOT

### Source
Primary: `inv_md_c`  
Secondary: `inv_md`, `drug_gn`, `drug_vn`

### Grain
1 row = 1 item x trade x lot x dept x location x snapshot_date

### Snapshot Strategy
**Recommended:** daily snapshot ETL  
เพราะ source table ดูมีลักษณะ current-state มากกว่า history-preserved

### Fields

| Output Column | Source Table | Source Column | Rule / Note |
|---|---|---|---|
| snapshot_date | ETL | runtime date | date of extraction |
| working_code | `inv_md_c` | `WORKING_CODE` | item key |
| trade_code | `inv_md_c` | `TRADE_CODE` | trade key |
| dept_id | `inv_md_c` | `DEPT_ID` | department |
| location | `inv_md_c` | `LOCATION` | physical location |
| lot_no | `inv_md_c` | `LOT_NO` | lot number |
| expired_date | `inv_md_c` | `EXPIRED_DATE` | parse to date |
| vendor_code | `inv_md_c` | `VENDOR_CODE` | supplier |
| manufac_code | `inv_md_c` | `MANUFAC_CODE` | manufacturer |
| pack_ratio | `inv_md_c` | `PACK_RATIO` | pack ratio |
| qty_on_hand | `inv_md_c` | `QTY_ON_HAND` | stock quantity |
| lot_cost | `inv_md_c` | `LOT_COST` | lot-level cost |
| pack_cost | `inv_md_c` | `PACK_COST` | pack-level cost |
| lot_value | `inv_md_c` | `LOT_VALUE` | preferred current lot value |
| record_status | `inv_md_c` | `RECORD_STATUS` | active/inactive |
| days_to_expiry | derived | - | `DATEDIFF(expired_date, snapshot_date)` |
| expiry_bucket | derived | - | bucket logic |
| stock_status | derived | - | in-stock / low / out |
| dead_stock_flag | derived | - | based on last movement |
| low_stock_flag | derived | - | compare against threshold |
| out_of_stock_flag | derived | - | qty <= 0 |

### Preferred Value Logic
```sql
stock_value =
COALESCE(inv_md_c.LOT_VALUE,
         inv_md_c.QTY_ON_HAND * inv_md_c.LOT_COST,
         inv_md_c.QTY_ON_HAND * inv_md_c.PACK_COST)
```

### Preferred Threshold Logic
```sql
reorder_threshold =
COALESCE(drug_gn.REORDER_QTY, drug_gn.MIN_LEVEL, inv_md.MIN_LEVEL)
```

---

## FACT_INVENTORY_MOVEMENT

### Source
`card`

### Grain
1 row = 1 movement record

### Fields

| Output Column | Source Table | Source Column | Rule / Note |
|---|---|---|---|
| movement_id | `card` | `RECORD_NUMBER` | unique movement key |
| operate_datetime | `card` | `OPERATE_DATE` | movement timestamp |
| operate_date | derived | - | date part |
| working_code | `card` | `WORKING_CODE` | item key |
| trade_code | `card` | `TRADE_CODE` | trade key |
| dept_id | `card` | `DEPT_ID` | department |
| stock_id | `card` | `STOCK_ID` | stock location |
| lot_no | `card` | `LOT_NO` | lot number |
| expired_date | `card` | `EXPIRED_DATE` | parse to date |
| vendor_code | `card` | `VENDOR_CODE` | vendor |
| budget_type | `card` | `BDG_TYPE` | budget source |
| rs_status | `card` | `R_S_STATUS` | movement type code |
| rs_number | `card` | `R_S_NUMBER` | source document number |
| value | `card` | `VALUE` | movement value |
| cost | `card` | `COST` | movement cost |
| active_qty | `card` | `ACTIVE_QTY` | movement quantity |
| active_pack | `card` | `ACTIVE_PACK` | movement pack |
| remain_qty | `card` | `REMAIN_QTY` | running remaining qty |
| remain_value | `card` | `REMAIN_VALUE` | running remaining value |
| remain_cost | `card` | `REMAIN_COST` | running remaining cost |
| free_flag | `card` | `FREE_FLAG` | free goods |
| cancel_flag | `card` | `CANCEL_FLAG` | cancelled movement |
| hn | `card` | `HN` | patient linkage if any |
| vn | `card` | `VN` | visit linkage if any |
| disp_no | `card` | `DISP_NO` | dispense linkage if any |
| movement_direction | derived | - | IN / OUT / ADJ |
| movement_qty_abs | derived | - | absolute qty |
| valid_flag | derived | - | exclude cancelled |

### Valid Movement Rule
```sql
valid_flag = CASE WHEN CANCEL_FLAG = 'Y' THEN 0 ELSE 1 END
```

### Movement Direction Rule (v1 provisional)
> ต้อง validate กับ business mapping ของ `R_S_STATUS`

```sql
CASE
  WHEN R_S_STATUS IN ('R','I','B') THEN 'IN'
  WHEN R_S_STATUS IN ('S','D','O') THEN 'OUT'
  WHEN R_S_STATUS IN ('A','C','X') THEN 'ADJ'
  ELSE 'UNKNOWN'
END
```

**NOTE:** รายการ status code ต้องยืนยันจากระบบจริงก่อน production

---

## FACT_DISPENSING

### Source
Primary: `dispensed`  
Secondary: `dept_map`, `drug_gn`, `drug_vn`

### Grain
1 row = 1 dispense record

### Fields

| Output Column | Source Table | Source Column | Rule / Note |
|---|---|---|---|
| dispense_id | `dispensed` | `RECORD_NUMBER` | unique dispense key |
| disp_date | `dispensed` | `DISP_DATE` | parse to date |
| operate_datetime | `dispensed` | `operate_date` | if available |
| med_code | `dispensed` | `MED_CODE` | may map to item code |
| working_code | derived | - | resolved item code |
| disp_qty | `dispensed` | `DISP_QTY` | quantity dispensed |
| disp_dept | `dispensed` | `DISP_DEPT` | dispensing department |
| process_flag | `dispensed` | `PROCESS_FLAG` | processed status |
| sub_po_no | `dispensed` | `SUB_PO_NO` | source request / issue |
| med_name | `dispensed` | `MED_NAME` | raw name |
| hn | `dispensed` | `hn` | patient id |
| vn | `dispensed` | `vn` | visit id |
| qty_normalized | derived | - | normalize if needed |
| unit_cost_basis | derived | - | from latest stock / item cost |
| disp_value | derived | - | qty × cost |

### MED_CODE Resolution Rule
**Preferred logic**
1. If `dispensed.MED_CODE = drug_gn.WORKING_CODE` → direct map
2. Else try map via `inv_has_his` if available in actual data environment
3. Else keep unresolved bucket for QA

### Dispense Value Logic
```sql
disp_value = disp_qty * unit_cost_basis
```

### Unit Cost Basis (recommended v1)
Priority:
1. latest lot/stock weighted cost from mart
2. `inv_md.WA_COST`
3. `drug_gn.LAST_BUY_COST`

---

## FACT_REQUESTED_DISPENSING

### Source
`accr_disp`

### Grain
1 row = 1 request line

### Fields

| Output Column | Source Table | Source Column | Rule / Note |
|---|---|---|---|
| req_no | `accr_disp` | `REQ_NO` | request number |
| working_code | `accr_disp` | `WORKING_CODE` | item |
| qty_req | `accr_disp` | `QTY_REQ` | requested qty |
| pack_ratio | `accr_disp` | `PACK_RATIO` | pack ratio |
| req_date | `accr_disp` | `REQ_DATE` | parse to date |
| confirm_date | `accr_disp` | `CONFIRM_DATE` | parse to date |
| dept_id | `accr_disp` | `DEPT_ID` | requesting dept |
| stock_id | `accr_disp` | `STOCK_ID` | stock location |
| dist_no | `accr_disp` | `DIST_NO` | distribution ref |
| qty_dist | `accr_disp` | `QTY_DIST` | distributed qty |
| del_flag | `accr_disp` | `DEL_FLAG` | deleted flag |
| fill_rate | derived | - | qty_dist / qty_req |
| pending_qty | derived | - | qty_req - qty_dist |

---

## FACT_PLAN_BUDGET

### Source
Primary: `buyplan_c`  
Secondary: `buyplan`, `bdg_amt`, `bdg_type`

### Grain
1 row = 1 year x item x dept

### Fields

| Output Column | Source Table | Source Column | Rule / Note |
|---|---|---|---|
| plan_year | `buyplan_c` | `YEAR` | plan year |
| working_code | `buyplan_c` | `WORKING_CODE` | item |
| trade_code | `buyplan_c` | `TRADE_CODE` | optional trade |
| dept_id | `buyplan_c` | `DEPT_ID` | department |
| pack_ratio | `buyplan_c` | `PACK_RATIO` | pack ratio |
| avg_3_year | `buyplan_c` | `AVG_3_YEAR` | historical avg |
| rate_1_year | `buyplan_c` | `RATE_1_YEAR` | usage history |
| rate_2_year | `buyplan_c` | `RATE_2_YEAR` | usage history |
| rate_3_year | `buyplan_c` | `RATE_3_YEAR` | usage history |
| min_level | `buyplan_c` | `MIN_LEVEL` | min stock |
| qty_this_year | `buyplan_c` | `QTY_THIS_YEAR` | planned annual qty |
| value_this_year | `buyplan_c` | `VALUE_THIS_YEAR` | planned annual value |
| remain_qty | `buyplan_c` | `REMAIN_QTY` | remaining qty |
| remain_value | `buyplan_c` | `REMAIN_VALUE` | remaining value |
| buy_qty | `buyplan_c` | `BUY_QTY` | purchased qty |
| buy_value | `buyplan_c` | `BUY_VALUE` | purchased value |
| qty_on_hand | `buyplan_c` | `QTY_ON_HAND` | current qty |
| pack_unit_cost | `buyplan_c` | `PACK_UNIT_COST` | cost |
| forecast_value | `buyplan_c` | `FORECAST` | forecast |
| qty_forecast | `buyplan_c` | `QTY_FORECAST` | forecast qty |
| qty_pre_plan | `buyplan_c` | `QTY_PRE_PLAN` | pre-plan qty |
| qty_tri1 | `buyplan_c` | `QTY_TRI1` | trimester 1 qty |
| qty_tri2 | `buyplan_c` | `QTY_TRI2` | trimester 2 qty |
| qty_tri3 | `buyplan_c` | `QTY_TRI3` | trimester 3 qty |
| qty_tri4 | `buyplan_c` | `QTY_TRI4` | trimester 4 qty |
| qty_buy_tri1 | `buyplan_c` | `QTY_BUY_TRI1` | bought qty T1 |
| qty_buy_tri2 | `buyplan_c` | `QTY_BUY_TRI2` | bought qty T2 |
| qty_buy_tri3 | `buyplan_c` | `QTY_BUY_TRI3` | bought qty T3 |
| qty_buy_tri4 | `buyplan_c` | `QTY_BUY_TRI4` | bought qty T4 |
| qty_rcv_tri1 | `buyplan_c` | `QTY_RCV_TRI1` | received qty T1 |
| qty_rcv_tri2 | `buyplan_c` | `QTY_RCV_TRI2` | received qty T2 |
| qty_rcv_tri3 | `buyplan_c` | `QTY_RCV_TRI3` | received qty T3 |
| qty_rcv_tri4 | `buyplan_c` | `QTY_RCV_TRI4` | received qty T4 |
| approve_flag | `buyplan_c` | `APPROVE` | approved |
| buy_method_code | `buyplan_c` | `BUYMET_CODE` | procurement method |
| adj_reason | `buyplan_c` | `ADJ_REASON` | planning adjustment |
| hide_flag | `buyplan_c` | `HIDE` | active/inactive |

---

## FACT_BUDGET_SUMMARY

### Source
Primary: `bdg_amt`  
Secondary: `bdg_type`

### Grain
1 row = 1 fiscal year x budget type

### Fields

| Output Column | Source Table | Source Column | Rule / Note |
|---|---|---|---|
| fiscal_year | `bdg_amt` | `FISCAL_YEAR` | year |
| budget_type | `bdg_amt` | `BUDGET_TYPE` | budget code |
| budget_amount | `bdg_amt` | `BUDGET_AMOUNT` | total allocated |
| total_buy | `bdg_amt` | `TOTAL_BUY` | used / purchased |
| budget_remain | `bdg_amt` | `BUDGET_REMAIN` | remaining |
| debt | `bdg_amt` | `DEBT` | debt exposure |
| tri1_budget | `bdg_amt` | `BUDGET_AMT_TRI1` | trimester 1 |
| tri2_budget | `bdg_amt` | `BUDGET_AMT_TRI2` | trimester 2 |
| tri3_budget | `bdg_amt` | `BUDGET_AMT_TRI3` | trimester 3 |
| tri4_budget | `bdg_amt` | `BUDGET_AMT_TRI4` | trimester 4 |
| tri1_buy | `bdg_amt` | `TOTAL_BUY_TRI1` | trimester 1 spend |
| tri2_buy | `bdg_amt` | `TOTAL_BUY_TRI2` | trimester 2 spend |
| tri3_buy | `bdg_amt` | `TOTAL_BUY_TRI3` | trimester 3 spend |
| tri4_buy | `bdg_amt` | `TOTAL_BUY_TRI4` | trimester 4 spend |
| tri1_remain | `bdg_amt` | `BUDGET_RM_TRI1` | trimester 1 remain |
| tri2_remain | `bdg_amt` | `BUDGET_RM_TRI2` | trimester 2 remain |
| tri3_remain | `bdg_amt` | `BUDGET_RM_TRI3` | trimester 3 remain |
| tri4_remain | `bdg_amt` | `BUDGET_RM_TRI4` | trimester 4 remain |
| limit_flag | `bdg_amt` | `LIMIT_FLAG` | budget control |
| burn_rate | derived | - | total_buy / budget_amount |

### Burn Rate Logic
```sql
CASE
  WHEN budget_amount > 0 THEN total_buy / budget_amount
  ELSE NULL
END
```

---

## FACT_CONTRACT

### Source
Primary: `cnt_c`  
Secondary: `cnt`

### Grain
1 row = 1 contract line

### Fields

| Output Column | Source Table | Source Column | Rule / Note |
|---|---|---|---|
| cnt_no | `cnt_c` | `CNT_NO` | contract number |
| working_code | `cnt_c` | `WORKING_CODE` | item |
| trade_code | `cnt_c` | `TRADE_CODE` | trade |
| buy_unit_cost | `cnt_c` | `BUY_UNIT_COST` | contract unit cost |
| qty_cnt | `cnt_c` | `QTY_CNT` | contracted qty |
| pack_ratio | `cnt_c` | `PACK_RATIO` | pack ratio |
| cost_cnt | `cnt_c` | `COST_CNT` | contract line value |
| qty_remain | `cnt_c` | `QTY_REMAIN` | remaining qty |
| cost_remain | `cnt_c` | `COST_REMAIN` | remaining value |
| end_date | `cnt_c` | `END_DATE` | parse to date |
| vendor_contract_ref | `cnt` | `PARTIES_CODE` | vendor/party |
| effective_date | `cnt` | `EFFECTIVE_DATE` | parse to date |
| contract_end_date | `cnt` | `END_DATE` | parse to date |
| buy_method | `cnt` | `BUY_METHOD` | procurement method |
| buy_common | `cnt` | `BUY_COMMON` | procurement common type |
| lead_time | `cnt` | `LEAD_TIME` | expected lead time |
| total_contract_cost | `cnt` | `TOTAL_COST` | header total |
| remain_contract_cost | `cnt` | `REMAIN_COST` | header remaining |

---

# 6) KPI FIELD-LEVEL MAPPING

---

# 6.1 INVENTORY POSITION KPIs

---

## KPI-001: Total Inventory Value

### Business Definition
มูลค่าคงคลังรวม ณ snapshot date ที่เลือก

### Source
`fact_inventory_snapshot`

### Formula
```sql
SUM(stock_value)
```

### Field Mapping

| Semantic | Source |
|---|---|
| quantity | `inv_md_c.QTY_ON_HAND` |
| cost basis | `inv_md_c.LOT_COST` or `inv_md_c.PACK_COST` |
| value | `inv_md_c.LOT_VALUE` preferred |

### Notes
ใช้ lot-level value ก่อนเสมอ เพราะแม่นกว่าการเอา average cost ถู ๆ ไถ ๆ

---

## KPI-002: Total SKU Count

### Business Definition
จำนวน SKU ระดับ item (`WORKING_CODE`) ทั้งหมดที่ active

### Formula
```sql
COUNT(DISTINCT working_code)
```

### Source
`dim_product`

### Filter Rule
```sql
active_flag = 1
```

---

## KPI-003: Active Stocked SKU Count

### Business Definition
จำนวน SKU ที่มี stock > 0

### Formula
```sql
COUNT(DISTINCT working_code)
WHERE qty_on_hand > 0
```

### Source
`fact_inventory_snapshot`

---

## KPI-004: Low Stock SKU Count

### Business Definition
จำนวน SKU ที่ stock ต่ำกว่าระดับเตือน

### Formula
```sql
COUNT(DISTINCT working_code)
WHERE qty_on_hand < reorder_threshold
```

### Threshold Rule
```sql
reorder_threshold =
COALESCE(drug_gn.REORDER_QTY, drug_gn.MIN_LEVEL, inv_md.MIN_LEVEL)
```

### Sources
- `inv_md_c.QTY_ON_HAND`
- `drug_gn.REORDER_QTY`
- `drug_gn.MIN_LEVEL`
- `inv_md.MIN_LEVEL`

---

## KPI-005: Out of Stock SKU Count

### Formula
```sql
COUNT(DISTINCT working_code)
WHERE qty_on_hand <= 0
```

### Source
`fact_inventory_snapshot`

---

## KPI-006: Near Expiry Value

### Business Definition
มูลค่าสินค้าที่หมดอายุภายใน threshold วัน

### Default Threshold
90 วัน

### Formula
```sql
SUM(stock_value)
WHERE days_to_expiry BETWEEN 0 AND 90
```

### Source Fields
- `inv_md_c.EXPIRED_DATE`
- `inv_md_c.LOT_VALUE`
- `inv_md_c.QTY_ON_HAND`

---

## KPI-007: Expired Stock Value

### Formula
```sql
SUM(stock_value)
WHERE expired_date < snapshot_date
  AND qty_on_hand > 0
```

### Source
`fact_inventory_snapshot`

---

## KPI-008: Dead Stock Value

### Business Definition
มูลค่าสินค้าที่ไม่มี movement เกิน threshold วัน

### Default Threshold
180 วัน

### Formula
```sql
SUM(stock_value)
WHERE DATEDIFF(snapshot_date, last_movement_date) >= 180
```

### Source Tables
- `inv_md_c`
- `card`

### Last Movement Logic
```sql
MAX(card.OPERATE_DATE)
GROUP BY working_code, trade_code, dept_id, lot_no
```

---

## KPI-009: Days of Stock (DOS)

### Business Definition
จำนวนวันที่ stock ปัจจุบันจะเพียงพอ

### Formula
```sql
qty_on_hand / avg_daily_consumption
```

### Consumption Window
90 วันย้อนหลัง (default)

### Mapping

| Semantic | Source |
|---|---|
| stock | `inv_md_c.QTY_ON_HAND` |
| consumption | `dispensed.DISP_QTY` |
| date | `dispensed.DISP_DATE` |

### Rule
```sql
avg_daily_consumption = SUM(disp_qty_last_90d) / 90
```

---

# 6.2 CONSUMPTION / UTILIZATION KPIs

---

## KPI-010: Consumption Quantity

### Formula
```sql
SUM(disp_qty)
```

### Source
`dispensed.DISP_QTY`

### Notes
ถ้ามี unit mismatch ต้อง normalize ตาม pack/unit rule

---

## KPI-011: Consumption Value

### Formula
```sql
SUM(disp_qty * unit_cost_basis)
```

### Cost Basis Priority
1. latest stock weighted cost
2. `inv_md.WA_COST`
3. `drug_gn.LAST_BUY_COST`

---

## KPI-012: Average Monthly Usage (AMU)

### Formula
```sql
SUM(consumption_qty over N months) / N
```

### Default N
3 เดือน

### Source
`fact_dispensing`

---

## KPI-013: Fast Moving Item

### Business Definition
สินค้าที่มีการใช้สูงกว่าค่าที่กำหนด

### Recommended Rule (v1)
Top 20% by rolling 90-day consumption value or quantity

### Source
`fact_dispensing`

---

## KPI-014: Slow Moving Item

### Rule
Bottom usage + still has stock

### Formula Example
```sql
qty_on_hand > 0
AND consumption_qty_last_90d <= threshold
```

---

## KPI-015: Department Consumption Share

### Formula
```sql
dept_consumption / total_consumption
```

### Source
`dispensed.DISP_DEPT`, `dispensed.DISP_QTY`

---

# 6.3 PROCUREMENT / CONTRACT KPIs

---

## KPI-016: Contracted Item Count

### Formula
```sql
COUNT(DISTINCT working_code)
```

### Source
`cnt_c`

---

## KPI-017: Contract Value

### Formula
```sql
SUM(cost_cnt)
```

### Source
`cnt_c.COST_CNT`

---

## KPI-018: Remaining Contract Value

### Formula
```sql
SUM(cost_remain)
```

### Source
`cnt_c.COST_REMAIN`

---

## KPI-019: Vendor Contract Spend Potential

### Formula
```sql
SUM(cost_cnt)
GROUP BY vendor_contract_ref
```

### Source
- `cnt.PARTIES_CODE`
- `cnt_c.COST_CNT`

---

## KPI-020: Contract Utilization Rate

### Formula
```sql
(cost_cnt - cost_remain) / cost_cnt
```

### Source
`fact_contract`

---

# 6.4 REQUEST / DISTRIBUTION KPIs

---

## KPI-021: Requested Quantity

### Formula
```sql
SUM(qty_req)
```

### Source
`accr_disp.QTY_REQ`

---

## KPI-022: Distributed Quantity

### Formula
```sql
SUM(qty_dist)
```

### Source
`accr_disp.QTY_DIST`

---

## KPI-023: Request Fill Rate

### Formula
```sql
SUM(qty_dist) / SUM(qty_req)
```

### Source
`accr_disp`

---

## KPI-024: Pending Request Quantity

### Formula
```sql
SUM(qty_req - qty_dist)
```

### Source
`accr_disp`

---

# 6.5 MOVEMENT / EXCEPTION KPIs

---

## KPI-025: Movement Count

### Formula
```sql
COUNT(*)
```

### Source
`card`

### Filter
```sql
cancel_flag IS NULL OR cancel_flag <> 'Y'
```

---

## KPI-026: Inventory Adjustment Count

### Formula
```sql
COUNT(*)
WHERE movement_direction = 'ADJ'
```

### Source
`fact_inventory_movement`

### Note
ต้อง validate status mapping ก่อน production

---

## KPI-027: Inventory Movement Value

### Formula
```sql
SUM(value)
```

### Source
`card.VALUE`

---

## KPI-028: Free Goods Movement Value

### Formula
```sql
SUM(value)
WHERE free_flag = 'Y'
```

### Source
`card.FREE_FLAG`, `card.VALUE`

---

# 6.6 PLANNING / FORECAST KPIs

---

## KPI-029: Planned Annual Quantity

### Formula
```sql
SUM(qty_this_year)
```

### Source
`buyplan_c.QTY_THIS_YEAR`

---

## KPI-030: Planned Annual Value

### Formula
```sql
SUM(value_this_year)
```

### Source
`buyplan_c.VALUE_THIS_YEAR`

---

## KPI-031: Forecast Quantity

### Formula
```sql
SUM(qty_forecast)
```

### Source
`buyplan_c.QTY_FORECAST`

---

## KPI-032: Forecast Value

### Formula
```sql
SUM(forecast_value)
```

### Source
`buyplan_c.FORECAST`

---

## KPI-033: Buy Value (Plan Tracking)

### Formula
```sql
SUM(buy_value)
```

### Source
`buyplan_c.BUY_VALUE`

---

## KPI-034: Plan Completion Rate

### Formula
```sql
SUM(buy_qty) / SUM(qty_this_year)
```

### Source
`buyplan_c`

---

## KPI-035: Trimester Plan Completion

### Formula Example (T1)
```sql
SUM(qty_buy_tri1) / SUM(qty_tri1)
```

### Source
`buyplan_c`

---

# 6.7 BUDGET KPIs

---

## KPI-036: Budget Allocated

### Formula
```sql
SUM(budget_amount)
```

### Source
`bdg_amt.BUDGET_AMOUNT`

---

## KPI-037: Budget Used

### Formula
```sql
SUM(total_buy)
```

### Source
`bdg_amt.TOTAL_BUY`

---

## KPI-038: Budget Remaining

### Formula
```sql
SUM(budget_remain)
```

### Source
`bdg_amt.BUDGET_REMAIN`

---

## KPI-039: Budget Burn Rate

### Formula
```sql
SUM(total_buy) / SUM(budget_amount)
```

### Source
`bdg_amt`

---

## KPI-040: Budget Debt Exposure

### Formula
```sql
SUM(debt)
```

### Source
`bdg_amt.DEBT`

---

# 7) JOIN LOGIC SPECIFICATION

---

# 7.1 Core Join Rules

---

## Rule J-01: Product Join
```sql
drug_gn.WORKING_CODE = inv_md.WORKING_CODE
drug_gn.WORKING_CODE = inv_md_c.WORKING_CODE
drug_gn.WORKING_CODE = card.WORKING_CODE
drug_gn.WORKING_CODE = buyplan_c.WORKING_CODE
drug_gn.WORKING_CODE = cnt_c.WORKING_CODE
```

---

## Rule J-02: Trade Product Join
```sql
drug_vn.TRADE_CODE = inv_md_c.TRADE_CODE
drug_vn.TRADE_CODE = card.TRADE_CODE
drug_vn.TRADE_CODE = buyplan_c.TRADE_CODE
drug_vn.TRADE_CODE = cnt_c.TRADE_CODE
```

---

## Rule J-03: Vendor Join
```sql
company.COMPANY_CODE = CAST(drug_vn.VENDOR_CODE AS UNSIGNED)
company.COMPANY_CODE = CAST(inv_md_c.VENDOR_CODE AS UNSIGNED)
company.COMPANY_CODE = CAST(card.VENDOR_CODE AS UNSIGNED)
```

> NOTE: บาง table เก็บ vendor code เป็น char, บาง table เป็น int  
> ต้อง normalize datatype ก่อน join

---

## Rule J-04: Department Join
```sql
dept_id.DEPT_ID = inv_md.DEPT_ID
dept_id.DEPT_ID = inv_md_c.DEPT_ID
dept_id.DEPT_ID = card.DEPT_ID
dept_id.DEPT_ID = buyplan_c.DEPT_ID
dept_id.DEPT_ID = accr_disp.DEPT_ID
dept_id.DEPT_ID = dispensed.DISP_DEPT
```

---

## Rule J-05: Lot-Level Join
```sql
inv_md_c.WORKING_CODE = card.WORKING_CODE
AND inv_md_c.TRADE_CODE = card.TRADE_CODE
AND inv_md_c.LOT_NO = card.LOT_NO
AND inv_md_c.DEPT_ID = card.DEPT_ID
```

### Optional Stronger Join
```sql
... AND inv_md_c.EXPIRED_DATE = card.EXPIRED_DATE
```

> ใช้เมื่อ quality ของ expiry date ดีพอ

---

## Rule J-06: Planning Join
```sql
buyplan_c.WORKING_CODE = drug_gn.WORKING_CODE
buyplan_c.DEPT_ID = dept_id.DEPT_ID
buyplan_c.TRADE_CODE = drug_vn.TRADE_CODE
```

---

## Rule J-07: Budget Join
```sql
bdg_amt.BUDGET_TYPE = bdg_type.BUDGET_TYPE
```

---

## Rule J-08: Contract Join
```sql
cnt.CNT_NO = cnt_c.CNT_NO
```

---

# 8) DATA QUALITY RULES

---

## DQ-01: Invalid Date Check
Reject or quarantine records where:
- date field is not 8 chars
- parse result is NULL
- date is unrealistic

### Example
```sql
CASE
  WHEN LENGTH(EXPIRED_DATE) = 8
   AND STR_TO_DATE(EXPIRED_DATE, '%Y%m%d') IS NOT NULL
  THEN 1 ELSE 0
END AS valid_expiry_flag
```

---

## DQ-02: Negative Stock Check
Flag records where:
```sql
QTY_ON_HAND < 0
```

---

## DQ-03: Missing Item Master Check
Flag any transaction where:
```sql
WORKING_CODE not found in drug_gn
```

---

## DQ-04: Missing Department Check
Flag any transaction where:
```sql
DEPT_ID not found in dept_id
```

---

## DQ-05: Orphan Trade Code Check
Flag any trade record where:
```sql
TRADE_CODE not found in drug_vn
```

---

## DQ-06: Invalid Vendor Code Type
Normalize and validate vendor code before joins

---

## DQ-07: Cost Null Check
Flag records where:
- quantity exists
- but no usable cost exists

---

# 9) RECOMMENDED MART BUILD ORDER

---

## Sprint 1 — Foundation
Build:
- `dim_product`
- `dim_trade_product`
- `dim_vendor`
- `dim_department`
- `dim_budget`
- `dim_date`

---

## Sprint 2 — Core Facts
Build:
- `fact_inventory_snapshot`
- `fact_inventory_movement`
- `fact_dispensing`
- `fact_requested_dispensing`

---

## Sprint 3 — Planning / Budget
Build:
- `fact_plan_budget`
- `fact_budget_summary`

---

## Sprint 4 — Procurement / Contract
Build:
- `fact_contract`

---

# 10) MVP DASHBOARD BUILD PRIORITY

แนะนำให้ build KPI เหล่านี้ก่อน เพราะให้ impact สูงและ source ชัด

1. Total Inventory Value
2. Active Stocked SKU Count
3. Low Stock SKU Count
4. Near Expiry Value
5. Expired Stock Value
6. Dead Stock Value
7. Consumption Quantity
8. Consumption Value
9. DOS
10. Request Fill Rate
11. Planned Annual Value
12. Budget Used
13. Budget Remaining
14. Budget Burn Rate
15. Contract Utilization Rate

---

# 11) IMPLEMENTATION NOTES

---

## 11.1 What should NOT be done
- อย่าทำ dashboard ยิงจาก source tables ตรงทุกหน้า
- อย่ากระจาย business logic ไปคนละ SQL คนละ chart
- อย่าปล่อยให้ cost basis เปลี่ยนไปตามคนเขียน query

---

## 11.2 What MUST be finalized before production
1. Mapping จริงของ `R_S_STATUS`
2. Mapping จริงของ `MED_CODE` → `WORKING_CODE`
3. Cost basis กลางของระบบ
4. Rule กลางของ low stock / reorder / dead stock
5. Snapshot retention policy

---

# 12) FINAL RECOMMENDATION

ระบบนี้มีโครงสร้างข้อมูลดีพอสำหรับการทำ dashboard ระดับใช้งานจริง  
แต่การทำให้ “ตัวเลขนิ่งและเถียงกันน้อย” ขึ้นกับการทำ data mart ที่ disciplined

ถ้าจะให้ระบบนี้ไม่กลายเป็น “Power BI ที่สวยแต่ตัวเลขกัดกันเอง”  
ต้องยึดเอกสารนี้เป็นตัวกลางระหว่าง:
- business
- data engineer
- BI developer
- ผู้บริหาร

---

# END OF DOCUMENT