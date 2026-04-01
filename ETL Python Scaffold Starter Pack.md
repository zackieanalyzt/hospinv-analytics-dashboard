# ETL Python Scaffold — Starter Pack

## Project: Hospital Drug & Medical Supply Analytics Dashboard

## Status: Bootstrap-Ready

## Purpose: ใช้เป็นโครงตั้งต้นสำหรับ ETL จริง (MariaDB → PostgreSQL)

> วิธีใช้:
>
> * copy ไฟล์แต่ละก้อนไปวางตาม path ที่ระบุ
> * แล้วค่อยเติม source SQL จริงตาม schema ของ `invs2019`
> * scaffold นี้ intentionally ทำให้ “เริ่มวิ่งได้จริง” ก่อน แล้วค่อยเติม logic ลึกทีละ job

---

# 1) Project Structure

```text id="31q4lq"
etl/
├─ .env.example
├─ requirements.txt
├─ README.md
├─ main.py
├─ config/
│  ├─ __init__.py
│  ├─ env.py
│  └─ settings.py
├─ db/
│  ├─ __init__.py
│  ├─ mariadb.py
│  └─ postgres.py
├─ utils/
│  ├─ __init__.py
│  ├─ hashing.py
│  ├─ dates.py
│  ├─ logging.py
│  ├─ validation.py
│  └─ batch.py
├─ jobs/
│  ├─ __init__.py
│  ├─ base.py
│  ├─ job_001_item_master.py
│  ├─ job_002_warehouse_master.py
│  ├─ job_003_vendor_master.py
│  ├─ job_004_stock_balance.py
│  ├─ job_005_stock_lot_balance.py
│  ├─ job_006_inventory_movement.py
│  ├─ job_007_purchase_order_line.py
│  ├─ job_008_goods_receipt_line.py
│  ├─ job_009_refresh_marts.py
│  └─ job_010_refresh_freshness.py
├─ runners/
│  ├─ __init__.py
│  ├─ daily_pipeline.py
│  ├─ repair_runner.py
│  └─ backfill_runner.py
└─ sql/
   ├─ source/
   │  ├─ README.md
   │  ├─ item_master.sql
   │  ├─ warehouse_master.sql
   │  ├─ vendor_master.sql
   │  ├─ stock_balance.sql
   │  ├─ stock_lot_balance.sql
   │  ├─ inventory_movement.sql
   │  ├─ purchase_order_line.sql
   │  └─ goods_receipt_line.sql
   ├─ core/
   │  ├─ upsert_dim_item.sql
   │  ├─ upsert_dim_warehouse.sql
   │  └─ upsert_dim_vendor.sql
   └─ mart/
      ├─ refresh_sum_inventory_daily.sql
      ├─ refresh_sum_stock_position_daily.sql
      ├─ refresh_sum_expiry_daily.sql
      ├─ refresh_sum_consumption_daily.sql
      ├─ refresh_sum_consumption_monthly.sql
      ├─ refresh_sum_movement_daily.sql
      ├─ refresh_sum_dead_stock_daily.sql
      ├─ refresh_sum_procurement_monthly.sql
      └─ refresh_sum_budget_burn_monthly.sql
```

---

# 2) File: `.env.example`

```env id="lyz7m4"
MARIADB_HOST=127.0.0.1
MARIADB_PORT=3306
MARIADB_DB=invs2019
MARIADB_USER=readonly_user
MARIADB_PASSWORD=change_me

PG_HOST=127.0.0.1
PG_PORT=5432
PG_DB=analytics_db
PG_USER=analytics_etl_rw
PG_PASSWORD=change_me

ETL_BATCH_TRIGGER=system
ETL_DEFAULT_LOOKBACK_DAYS=3
EXPIRY_NEAR_THRESHOLD_DAYS=90
ETL_LOG_LEVEL=INFO
```

---

# 3) File: `requirements.txt`

```text id="31n48u"
sqlalchemy>=2.0.0
pymysql>=1.1.0
psycopg2-binary>=2.9.9
pandas>=2.2.0
python-dotenv>=1.0.1
tenacity>=8.2.3
loguru>=0.7.2
```

---

# 4) File: `README.md`

````markdown id="db96mz"
# ETL Starter Pack

## Quick Start

### 1) Create virtual environment
```bash id="t6xjgw"
python -m venv .venv
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate
````

### 2) Install dependencies

```bash id="iw3gr5"
pip install -r requirements.txt
```

### 3) Create env file

```bash id="u14ofj"
cp .env.example .env
```

### 4) Run daily pipeline

```bash id="1i1wga"
python main.py daily
```

### 5) Run specific job

```bash id="wmm2ng"
python main.py job ETL-001
```

### 6) Run repair

```bash id="yuyfb8"
python main.py repair --job ETL-006 --from-date 2026-03-25 --to-date 2026-03-31
```

## Notes

* Replace SQL in `sql/source/*.sql` with real source queries from `invs2019`
* Do NOT write anything to source DB
* PostgreSQL DDL must already be deployed (PRD v1.6)

````

---

# 5) File: `main.py`

```python id="m17fd6"
import sys
from loguru import logger
from runners.daily_pipeline import run_daily_pipeline
from runners.repair_runner import run_repair
from runners.backfill_runner import run_backfill

def main():
    if len(sys.argv) < 2:
        logger.error("Usage: python main.py [daily|repair|backfill|job]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "daily":
        run_daily_pipeline()

    elif command == "repair":
        args = parse_args(sys.argv[2:])
        run_repair(args)

    elif command == "backfill":
        args = parse_args(sys.argv[2:])
        run_backfill(args)

    elif command == "job":
        if len(sys.argv) < 3:
            logger.error("Usage: python main.py job ETL-001")
            sys.exit(1)
        from runners.daily_pipeline import run_single_job
        run_single_job(sys.argv[2])

    else:
        logger.error(f"Unknown command: {command}")
        sys.exit(1)

def parse_args(argv):
    args = {}
    i = 0
    while i < len(argv):
        if argv[i].startswith("--"):
            key = argv[i][2:]
            value = argv[i + 1] if i + 1 < len(argv) else None
            args[key] = value
            i += 2
        else:
            i += 1
    return args

if __name__ == "__main__":
    main()
````

---

# 6) File: `config/__init__.py`

```python id="8g2hvm"
# config package
```

---

# 7) File: `config/env.py`

```python id="0b8zsq"
from dotenv import load_dotenv
load_dotenv()
```

---

# 8) File: `config/settings.py`

```python id="pajwn4"
import os
from config.env import *

MARIADB = {
    "host": os.getenv("MARIADB_HOST"),
    "port": int(os.getenv("MARIADB_PORT", 3306)),
    "db": os.getenv("MARIADB_DB"),
    "user": os.getenv("MARIADB_USER"),
    "password": os.getenv("MARIADB_PASSWORD"),
}

POSTGRES = {
    "host": os.getenv("PG_HOST"),
    "port": int(os.getenv("PG_PORT", 5432)),
    "db": os.getenv("PG_DB"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
}

ETL_BATCH_TRIGGER = os.getenv("ETL_BATCH_TRIGGER", "system")
ETL_DEFAULT_LOOKBACK_DAYS = int(os.getenv("ETL_DEFAULT_LOOKBACK_DAYS", 3))
EXPIRY_NEAR_THRESHOLD_DAYS = int(os.getenv("EXPIRY_NEAR_THRESHOLD_DAYS", 90))
ETL_LOG_LEVEL = os.getenv("ETL_LOG_LEVEL", "INFO")
```

---

# 9) File: `db/__init__.py`

```python id="jlwm1r"
# db package
```

---

# 10) File: `db/mariadb.py`

```python id="0mx8zl"
from sqlalchemy import create_engine
from config.settings import MARIADB

def get_mariadb_engine():
    url = (
        f"mysql+pymysql://{MARIADB['user']}:{MARIADB['password']}"
        f"@{MARIADB['host']}:{MARIADB['port']}/{MARIADB['db']}"
        f"?charset=utf8mb4"
    )
    return create_engine(url, pool_pre_ping=True)
```

---

# 11) File: `db/postgres.py`

```python id="tq8i5x"
from sqlalchemy import create_engine
from config.settings import POSTGRES

def get_postgres_engine():
    url = (
        f"postgresql+psycopg2://{POSTGRES['user']}:{POSTGRES['password']}"
        f"@{POSTGRES['host']}:{POSTGRES['port']}/{POSTGRES['db']}"
    )
    return create_engine(url, pool_pre_ping=True)
```

---

# 12) File: `utils/__init__.py`

```python id="53afoc"
# utils package
```

---

# 13) File: `utils/hashing.py`

```python id="icfkn6"
import hashlib

def sha256_hash(*parts):
    raw = "||".join("" if p is None else str(p).strip() for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
```

---

# 14) File: `utils/dates.py`

```python id="byhfws"
from datetime import datetime, timedelta

def today_date():
    return datetime.now().date()

def days_ago(days: int):
    return (datetime.now() - timedelta(days=days)).date()

def timestamp_now():
    return datetime.now()
```

---

# 15) File: `utils/logging.py`

```python id="x4znfd"
import sys
from loguru import logger
from config.settings import ETL_LOG_LEVEL

logger.remove()
logger.add(sys.stdout, level=ETL_LOG_LEVEL, backtrace=True, diagnose=True)
```

---

# 16) File: `utils/validation.py`

```python id="9k74tw"
import pandas as pd

def require_columns(df: pd.DataFrame, required_cols: list[str], job_name: str):
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"{job_name}: missing required columns: {missing}")

def require_not_null(df: pd.DataFrame, col: str, job_name: str):
    if df[col].isnull().any():
        raise ValueError(f"{job_name}: null values found in required column: {col}")
```

---

# 17) File: `utils/batch.py`

```python id="zzjlwm"
from sqlalchemy import text
from db.postgres import get_postgres_engine
from config.settings import ETL_BATCH_TRIGGER

def create_batch(pipeline_name: str, batch_type: str = "incremental") -> int:
    engine = get_postgres_engine()
    sql = text("""
        INSERT INTO ops.etl_batch (
            pipeline_name, batch_type, batch_status, triggered_by
        )
        VALUES (
            :pipeline_name, :batch_type, 'running', :triggered_by
        )
        RETURNING etl_batch_id
    """)
    with engine.begin() as conn:
        result = conn.execute(sql, {
            "pipeline_name": pipeline_name,
            "batch_type": batch_type,
            "triggered_by": ETL_BATCH_TRIGGER
        })
        return result.scalar_one()

def mark_batch_success(etl_batch_id: int):
    engine = get_postgres_engine()
    sql = text("""
        UPDATE ops.etl_batch
        SET batch_status = 'success',
            ended_ts = NOW()
        WHERE etl_batch_id = :etl_batch_id
    """)
    with engine.begin() as conn:
        conn.execute(sql, {"etl_batch_id": etl_batch_id})

def mark_batch_failed(etl_batch_id: int, note: str | None = None):
    engine = get_postgres_engine()
    sql = text("""
        UPDATE ops.etl_batch
        SET batch_status = 'failed',
            ended_ts = NOW(),
            note = :note
        WHERE etl_batch_id = :etl_batch_id
    """)
    with engine.begin() as conn:
        conn.execute(sql, {"etl_batch_id": etl_batch_id, "note": note})

def log_table_run_start(etl_batch_id: int, target_schema: str, target_table: str, source_table: str, load_mode: str) -> int:
    engine = get_postgres_engine()
    sql = text("""
        INSERT INTO ops.etl_table_run (
            etl_batch_id, target_schema, target_table, source_table, load_mode, run_status
        )
        VALUES (
            :etl_batch_id, :target_schema, :target_table, :source_table, :load_mode, 'running'
        )
        RETURNING etl_table_run_id
    """)
    with engine.begin() as conn:
        result = conn.execute(sql, {
            "etl_batch_id": etl_batch_id,
            "target_schema": target_schema,
            "target_table": target_table,
            "source_table": source_table,
            "load_mode": load_mode
        })
        return result.scalar_one()

def log_table_run_finish(etl_table_run_id: int, row_extracted=0, row_inserted=0, row_updated=0, row_deleted=0, row_rejected=0, run_status="success", error_message=None):
    engine = get_postgres_engine()
    sql = text("""
        UPDATE ops.etl_table_run
        SET row_extracted = :row_extracted,
            row_inserted = :row_inserted,
            row_updated = :row_updated,
            row_deleted = :row_deleted,
            row_rejected = :row_rejected,
            run_status = :run_status,
            error_message = :error_message,
            ended_ts = NOW()
        WHERE etl_table_run_id = :etl_table_run_id
    """)
    with engine.begin() as conn:
        conn.execute(sql, {
            "etl_table_run_id": etl_table_run_id,
            "row_extracted": row_extracted,
            "row_inserted": row_inserted,
            "row_updated": row_updated,
            "row_deleted": row_deleted,
            "row_rejected": row_rejected,
            "run_status": run_status,
            "error_message": error_message
        })
```

---

# 18) File: `jobs/__init__.py`

```python id="hfw67n"
# jobs package
```

---

# 19) File: `jobs/base.py`

```python id="7mvwcz"
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from utils.logging import logger
from db.mariadb import get_mariadb_engine
from db.postgres import get_postgres_engine
from utils.batch import log_table_run_start, log_table_run_finish

BASE_DIR = Path(__file__).resolve().parents[1]

class BaseETLJob:
    job_code = "ETL-000"
    job_name = "base_job"
    source_sql_file = None
    source_table = "unknown_source"
    target_schema = "stg"
    target_table = "unknown_target"
    load_mode = "append"

    def run(self, etl_batch_id: int, **kwargs):
        etl_table_run_id = log_table_run_start(
            etl_batch_id=etl_batch_id,
            target_schema=self.target_schema,
            target_table=self.target_table,
            source_table=self.source_table,
            load_mode=self.load_mode
        )

        try:
            df = self.extract(**kwargs)
            extracted = len(df)

            if extracted == 0:
                logger.warning(f"[{self.job_code}] No data extracted.")
                log_table_run_finish(etl_table_run_id, row_extracted=0, run_status="success")
                return

            df = self.transform(df, etl_batch_id=etl_batch_id, **kwargs)
            inserted, updated = self.load(df, etl_batch_id=etl_batch_id, **kwargs)

            log_table_run_finish(
                etl_table_run_id,
                row_extracted=extracted,
                row_inserted=inserted,
                row_updated=updated,
                run_status="success"
            )

            logger.info(f"[{self.job_code}] Success. extracted={extracted}, inserted={inserted}, updated={updated}")

        except Exception as e:
            logger.exception(f"[{self.job_code}] Failed: {e}")
            log_table_run_finish(
                etl_table_run_id,
                run_status="failed",
                error_message=str(e)
            )
            raise

    def extract(self, **kwargs) -> pd.DataFrame:
        if not self.source_sql_file:
            raise NotImplementedError("source_sql_file not defined")

        sql_path = BASE_DIR / "sql" / "source" / self.source_sql_file
        sql = sql_path.read_text(encoding="utf-8")

        engine = get_mariadb_engine()
        return pd.read_sql(text(sql), engine)

    def transform(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        return df

    def load(self, df: pd.DataFrame, **kwargs):
        engine = get_postgres_engine()
        inserted = len(df)
        updated = 0
        df.to_sql(self.target_table, engine, schema=self.target_schema, if_exists="append", index=False, method="multi")
        return inserted, updated
```

---

# 20) File: `jobs/job_001_item_master.py`

```python id="th3xft"
import pandas as pd
from jobs.base import BaseETLJob
from utils.hashing import sha256_hash
from utils.validation import require_columns, require_not_null
from sqlalchemy import text
from db.postgres import get_postgres_engine

class Job001ItemMaster(BaseETLJob):
    job_code = "ETL-001"
    job_name = "load_item_master"
    source_sql_file = "item_master.sql"
    source_table = "item_master"
    target_schema = "stg"
    target_table = "item_master"
    load_mode = "append"

    def transform(self, df: pd.DataFrame, etl_batch_id: int, **kwargs) -> pd.DataFrame:
        require_columns(df, ["source_item_code", "item_name"], self.job_name)
        require_not_null(df, "source_item_code", self.job_name)
        require_not_null(df, "item_name", self.job_name)

        df["etl_batch_id"] = etl_batch_id
        df["source_pk_hash"] = df["source_item_code"].apply(lambda x: sha256_hash(x))
        return df

    def load(self, df: pd.DataFrame, etl_batch_id: int, **kwargs):
        engine = get_postgres_engine()

        with engine.begin() as conn:
            conn.execute(text("DELETE FROM stg.item_master WHERE etl_batch_id = :etl_batch_id"), {"etl_batch_id": etl_batch_id})

        inserted, updated = super().load(df, etl_batch_id=etl_batch_id)

        upsert_sql = (self._base_dir() / "sql" / "core" / "upsert_dim_item.sql").read_text(encoding="utf-8")
        with engine.begin() as conn:
            conn.execute(text(upsert_sql), {"etl_batch_id": etl_batch_id})

        return inserted, updated

    def _base_dir(self):
        from pathlib import Path
        return Path(__file__).resolve().parents[1]
```

---

# 21) File: `jobs/job_002_warehouse_master.py`

```python id="d9yxpk"
import pandas as pd
from jobs.base import BaseETLJob
from utils.hashing import sha256_hash
from utils.validation import require_columns, require_not_null
from sqlalchemy import text
from db.postgres import get_postgres_engine

class Job002WarehouseMaster(BaseETLJob):
    job_code = "ETL-002"
    job_name = "load_warehouse_master"
    source_sql_file = "warehouse_master.sql"
    source_table = "warehouse_master"
    target_schema = "stg"
    target_table = "warehouse_master"
    load_mode = "append"

    def transform(self, df: pd.DataFrame, etl_batch_id: int, **kwargs) -> pd.DataFrame:
        require_columns(df, ["source_warehouse_code", "warehouse_name"], self.job_name)
        require_not_null(df, "source_warehouse_code", self.job_name)
        require_not_null(df, "warehouse_name", self.job_name)

        df["etl_batch_id"] = etl_batch_id
        df["source_pk_hash"] = df["source_warehouse_code"].apply(lambda x: sha256_hash(x))
        return df

    def load(self, df: pd.DataFrame, etl_batch_id: int, **kwargs):
        engine = get_postgres_engine()

        with engine.begin() as conn:
            conn.execute(text("DELETE FROM stg.warehouse_master WHERE etl_batch_id = :etl_batch_id"), {"etl_batch_id": etl_batch_id})

        inserted, updated = super().load(df, etl_batch_id=etl_batch_id)

        upsert_sql = (self._base_dir() / "sql" / "core" / "upsert_dim_warehouse.sql").read_text(encoding="utf-8")
        with engine.begin() as conn:
            conn.execute(text(upsert_sql), {"etl_batch_id": etl_batch_id})

        return inserted, updated

    def _base_dir(self):
        from pathlib import Path
        return Path(__file__).resolve().parents[1]
```

---

# 22) File: `jobs/job_003_vendor_master.py`

```python id="d5m7n2"
import pandas as pd
from jobs.base import BaseETLJob
from utils.hashing import sha256_hash
from utils.validation import require_columns, require_not_null
from sqlalchemy import text
from db.postgres import get_postgres_engine

class Job003VendorMaster(BaseETLJob):
    job_code = "ETL-003"
    job_name = "load_vendor_master"
    source_sql_file = "vendor_master.sql"
    source_table = "vendor_master"
    target_schema = "stg"
    target_table = "vendor_master"
    load_mode = "append"

    def transform(self, df: pd.DataFrame, etl_batch_id: int, **kwargs) -> pd.DataFrame:
        require_columns(df, ["source_vendor_code", "vendor_name"], self.job_name)
        require_not_null(df, "source_vendor_code", self.job_name)
        require_not_null(df, "vendor_name", self.job_name)

        df["etl_batch_id"] = etl_batch_id
        df["source_pk_hash"] = df["source_vendor_code"].apply(lambda x: sha256_hash(x))
        return df

    def load(self, df: pd.DataFrame, etl_batch_id: int, **kwargs):
        engine = get_postgres_engine()

        with engine.begin() as conn:
            conn.execute(text("DELETE FROM stg.vendor_master WHERE etl_batch_id = :etl_batch_id"), {"etl_batch_id": etl_batch_id})

        inserted, updated = super().load(df, etl_batch_id=etl_batch_id)

        upsert_sql = (self._base_dir() / "sql" / "core" / "upsert_dim_vendor.sql").read_text(encoding="utf-8")
        with engine.begin() as conn:
            conn.execute(text(upsert_sql), {"etl_batch_id": etl_batch_id})

        return inserted, updated

    def _base_dir(self):
        from pathlib import Path
        return Path(__file__).resolve().parents[1]
```

---

# 23) File: `jobs/job_004_stock_balance.py`

```python id="1esg1z"
import pandas as pd
from jobs.base import BaseETLJob
from utils.hashing import sha256_hash
from utils.validation import require_columns, require_not_null
from sqlalchemy import text
from db.postgres import get_postgres_engine

class Job004StockBalance(BaseETLJob):
    job_code = "ETL-004"
    job_name = "load_stock_balance"
    source_sql_file = "stock_balance.sql"
    source_table = "stock_balance"
    target_schema = "stg"
    target_table = "stock_balance"
    load_mode = "append"

    def transform(self, df: pd.DataFrame, etl_batch_id: int, **kwargs) -> pd.DataFrame:
        require_columns(df, ["snapshot_date", "source_item_code", "source_warehouse_code", "qty_on_hand"], self.job_name)
        require_not_null(df, "snapshot_date", self.job_name)
        require_not_null(df, "source_item_code", self.job_name)
        require_not_null(df, "source_warehouse_code", self.job_name)
        require_not_null(df, "qty_on_hand", self.job_name)

        df["etl_batch_id"] = etl_batch_id
        df["source_pk_hash"] = df.apply(
            lambda r: sha256_hash(r["snapshot_date"], r["source_item_code"], r["source_warehouse_code"]),
            axis=1
        )
        return df

    def load(self, df: pd.DataFrame, etl_batch_id: int, **kwargs):
        engine = get_postgres_engine()
        snapshot_dates = tuple(df["snapshot_date"].astype(str).unique().tolist())

        with engine.begin() as conn:
            conn.execute(text("DELETE FROM stg.stock_balance WHERE etl_batch_id = :etl_batch_id"), {"etl_batch_id": etl_batch_id})

        inserted, updated = super().load(df, etl_batch_id=etl_batch_id)

        # core refresh window by snapshot dates
        delete_sql = text("""
            DELETE FROM core.fact_stock_snapshot
            WHERE snapshot_date = ANY(:snapshot_dates)
        """)
        insert_sql = text("""
            INSERT INTO core.fact_stock_snapshot (
                etl_batch_id, snapshot_date, snapshot_date_id,
                dim_item_id, dim_warehouse_id,
                qty_on_hand, avg_unit_cost, stock_value, stock_status, created_ts
            )
            SELECT
                s.etl_batch_id,
                s.snapshot_date,
                TO_CHAR(s.snapshot_date, 'YYYYMMDD')::INTEGER,
                COALESCE(i.dim_item_id, 0),
                COALESCE(w.dim_warehouse_id, 0),
                s.qty_on_hand,
                s.avg_unit_cost,
                s.stock_value,
                CASE
                    WHEN s.qty_on_hand > 0 THEN 'normal'
                    WHEN s.qty_on_hand = 0 THEN 'zero'
                    ELSE 'negative'
                END,
                NOW()
            FROM stg.stock_balance s
            LEFT JOIN core.dim_item i ON s.source_item_code = i.source_item_code
            LEFT JOIN core.dim_warehouse w ON s.source_warehouse_code = w.source_warehouse_code
            WHERE s.etl_batch_id = :etl_batch_id
        """)

        with engine.begin() as conn:
            conn.execute(delete_sql, {"snapshot_dates": list(snapshot_dates)})
            conn.execute(insert_sql, {"etl_batch_id": etl_batch_id})

        return inserted, updated
```

---

# 24) File: `jobs/job_005_stock_lot_balance.py`

```python id="h8cl61"
import pandas as pd
from jobs.base import BaseETLJob
from utils.hashing import sha256_hash
from utils.validation import require_columns, require_not_null
from sqlalchemy import text
from db.postgres import get_postgres_engine
from config.settings import EXPIRY_NEAR_THRESHOLD_DAYS

class Job005StockLotBalance(BaseETLJob):
    job_code = "ETL-005"
    job_name = "load_stock_lot_balance"
    source_sql_file = "stock_lot_balance.sql"
    source_table = "stock_lot_balance"
    target_schema = "stg"
    target_table = "stock_lot_balance"
    load_mode = "append"

    def transform(self, df: pd.DataFrame, etl_batch_id: int, **kwargs) -> pd.DataFrame:
        require_columns(df, ["snapshot_date", "source_item_code", "source_warehouse_code", "qty_on_hand"], self.job_name)
        require_not_null(df, "snapshot_date", self.job_name)
        require_not_null(df, "source_item_code", self.job_name)
        require_not_null(df, "source_warehouse_code", self.job_name)
        require_not_null(df, "qty_on_hand", self.job_name)

        df["etl_batch_id"] = etl_batch_id
        df["source_pk_hash"] = df.apply(
            lambda r: sha256_hash(r["snapshot_date"], r["source_item_code"], r["source_warehouse_code"], r.get("lot_no"), r.get("expiry_date")),
            axis=1
        )
        return df

    def load(self, df: pd.DataFrame, etl_batch_id: int, **kwargs):
        engine = get_postgres_engine()
        snapshot_dates = tuple(df["snapshot_date"].astype(str).unique().tolist())

        with engine.begin() as conn:
            conn.execute(text("DELETE FROM stg.stock_lot_balance WHERE etl_batch_id = :etl_batch_id"), {"etl_batch_id": etl_batch_id})

        inserted, updated = super().load(df, etl_batch_id=etl_batch_id)

        delete_sql = text("""
            DELETE FROM core.fact_stock_lot_snapshot
            WHERE snapshot_date = ANY(:snapshot_dates)
        """)

        insert_sql = text("""
            INSERT INTO core.fact_stock_lot_snapshot (
                etl_batch_id, snapshot_date, snapshot_date_id,
                dim_item_id, dim_warehouse_id,
                lot_no, expiry_date,
                qty_on_hand, avg_unit_cost, stock_value,
                days_to_expiry, expiry_status, created_ts
            )
            SELECT
                s.etl_batch_id,
                s.snapshot_date,
                TO_CHAR(s.snapshot_date, 'YYYYMMDD')::INTEGER,
                COALESCE(i.dim_item_id, 0),
                COALESCE(w.dim_warehouse_id, 0),
                s.lot_no,
                s.expiry_date,
                s.qty_on_hand,
                s.avg_unit_cost,
                s.stock_value,
                CASE
                    WHEN s.expiry_date IS NULL THEN NULL
                    ELSE (s.expiry_date - s.snapshot_date)
                END,
                CASE
                    WHEN s.expiry_date IS NULL THEN 'no_expiry'
                    WHEN s.expiry_date < s.snapshot_date THEN 'expired'
                    WHEN s.expiry_date <= s.snapshot_date + :threshold_days THEN 'near_expiry'
                    ELSE 'healthy'
                END,
                NOW()
            FROM stg.stock_lot_balance s
            LEFT JOIN core.dim_item i ON s.source_item_code = i.source_item_code
            LEFT JOIN core.dim_warehouse w ON s.source_warehouse_code = w.source_warehouse_code
            WHERE s.etl_batch_id = :etl_batch_id
        """)

        with engine.begin() as conn:
            conn.execute(delete_sql, {"snapshot_dates": list(snapshot_dates)})
            conn.execute(insert_sql, {
                "etl_batch_id": etl_batch_id,
                "threshold_days": EXPIRY_NEAR_THRESHOLD_DAYS
            })

        return inserted, updated
```

---

# 25) File: `jobs/job_006_inventory_movement.py`

```python id="c3tpxc"
import pandas as pd
from jobs.base import BaseETLJob
from utils.hashing import sha256_hash
from utils.validation import require_columns, require_not_null
from sqlalchemy import text
from db.postgres import get_postgres_engine

class Job006InventoryMovement(BaseETLJob):
    job_code = "ETL-006"
    job_name = "load_inventory_movement"
    source_sql_file = "inventory_movement.sql"
    source_table = "inventory_movement"
    target_schema = "stg"
    target_table = "inventory_movement"
    load_mode = "append"

    def transform(self, df: pd.DataFrame, etl_batch_id: int, **kwargs) -> pd.DataFrame:
        require_columns(df, ["source_txn_id", "txn_date", "source_item_code", "source_warehouse_code", "movement_type", "qty"], self.job_name)
        require_not_null(df, "source_txn_id", self.job_name)
        require_not_null(df, "txn_date", self.job_name)
        require_not_null(df, "source_item_code", self.job_name)
        require_not_null(df, "source_warehouse_code", self.job_name)
        require_not_null(df, "movement_type", self.job_name)
        require_not_null(df, "qty", self.job_name)

        df["etl_batch_id"] = etl_batch_id
        df["source_pk_hash"] = df.apply(
            lambda r: sha256_hash(r["source_txn_id"], r["source_item_code"], r["source_warehouse_code"], r.get("lot_no"), r["movement_type"]),
            axis=1
        )
        return df

    def load(self, df: pd.DataFrame, etl_batch_id: int, **kwargs):
        engine = get_postgres_engine()

        with engine.begin() as conn:
            conn.execute(text("DELETE FROM stg.inventory_movement WHERE etl_batch_id = :etl_batch_id"), {"etl_batch_id": etl_batch_id})

        inserted, updated = super().load(df, etl_batch_id=etl_batch_id)

        insert_sql = text("""
            INSERT INTO core.fact_inventory_movement (
                etl_batch_id,
                source_txn_id, ref_doc_no, ref_doc_type,
                txn_date, txn_ts, txn_date_id,
                dim_item_id, dim_warehouse_id, dim_vendor_id,
                movement_type, movement_direction,
                lot_no, expiry_date,
                qty, signed_qty, unit_cost, line_value, signed_value,
                source_row_hash, created_ts
            )
            SELECT
                s.etl_batch_id,
                s.source_txn_id, s.ref_doc_no, s.ref_doc_type,
                s.txn_date, s.txn_ts, TO_CHAR(s.txn_date, 'YYYYMMDD')::INTEGER,
                COALESCE(i.dim_item_id, 0),
                COALESCE(w.dim_warehouse_id, 0),
                COALESCE(v.dim_vendor_id, 0),
                LOWER(s.movement_type),
                CASE
                    WHEN LOWER(s.movement_type) IN ('receive','transfer_in','return_in','adjust_in') THEN 'in'
                    WHEN LOWER(s.movement_type) IN ('issue','transfer_out','return_out','adjust_out') THEN 'out'
                    ELSE 'neutral'
                END,
                s.lot_no, s.expiry_date,
                s.qty,
                CASE
                    WHEN LOWER(s.movement_type) IN ('receive','transfer_in','return_in','adjust_in') THEN s.qty
                    WHEN LOWER(s.movement_type) IN ('issue','transfer_out','return_out','adjust_out') THEN -1 * s.qty
                    ELSE s.qty
                END,
                s.unit_cost,
                s.line_value,
                CASE
                    WHEN LOWER(s.movement_type) IN ('receive','transfer_in','return_in','adjust_in') THEN COALESCE(s.line_value, 0)
                    WHEN LOWER(s.movement_type) IN ('issue','transfer_out','return_out','adjust_out') THEN -1 * COALESCE(s.line_value, 0)
                    ELSE COALESCE(s.line_value, 0)
                END,
                s.source_pk_hash,
                NOW()
            FROM stg.inventory_movement s
            LEFT JOIN core.dim_item i ON s.source_item_code = i.source_item_code
            LEFT JOIN core.dim_warehouse w ON s.source_warehouse_code = w.source_warehouse_code
            LEFT JOIN core.dim_vendor v ON s.source_vendor_code = v.source_vendor_code
            WHERE s.etl_batch_id = :etl_batch_id
            ON CONFLICT DO NOTHING
        """)

        with engine.begin() as conn:
            conn.execute(insert_sql, {"etl_batch_id": etl_batch_id})

        return inserted, updated
```

---

# 26) File: `jobs/job_007_purchase_order_line.py`

```python id="rd8a0j"
import pandas as pd
from jobs.base import BaseETLJob
from utils.hashing import sha256_hash
from utils.validation import require_columns, require_not_null
from sqlalchemy import text
from db.postgres import get_postgres_engine

class Job007PurchaseOrderLine(BaseETLJob):
    job_code = "ETL-007"
    job_name = "load_purchase_order_line"
    source_sql_file = "purchase_order_line.sql"
    source_table = "purchase_order_line"
    target_schema = "stg"
    target_table = "purchase_order_line"
    load_mode = "append"

    def transform(self, df: pd.DataFrame, etl_batch_id: int, **kwargs) -> pd.DataFrame:
        require_columns(df, ["po_no", "po_date", "source_item_code", "ordered_qty"], self.job_name)
        require_not_null(df, "po_no", self.job_name)
        require_not_null(df, "po_date", self.job_name)
        require_not_null(df, "source_item_code", self.job_name)
        require_not_null(df, "ordered_qty", self.job_name)

        df["etl_batch_id"] = etl_batch_id
        df["source_pk_hash"] = df.apply(
            lambda r: sha256_hash(r["po_no"], r["source_item_code"]),
            axis=1
        )
        return df

    def load(self, df: pd.DataFrame, etl_batch_id: int, **kwargs):
        engine = get_postgres_engine()

        with engine.begin() as conn:
            conn.execute(text("DELETE FROM stg.purchase_order_line WHERE etl_batch_id = :etl_batch_id"), {"etl_batch_id": etl_batch_id})

        inserted, updated = super().load(df, etl_batch_id=etl_batch_id)

        delete_sql = text("""
            DELETE FROM core.fact_purchase_order_line f
            USING stg.purchase_order_line s
            LEFT JOIN core.dim_item i ON s.source_item_code = i.source_item_code
            WHERE s.etl_batch_id = :etl_batch_id
              AND f.po_no = s.po_no
              AND f.dim_item_id = COALESCE(i.dim_item_id, 0)
        """)

        insert_sql = text("""
            INSERT INTO core.fact_purchase_order_line (
                etl_batch_id, po_no, po_date, po_date_id,
                dim_item_id, dim_vendor_id,
                ordered_qty, ordered_unit_cost, ordered_value, po_status,
                source_row_hash, created_ts
            )
            SELECT
                s.etl_batch_id,
                s.po_no,
                s.po_date,
                TO_CHAR(s.po_date, 'YYYYMMDD')::INTEGER,
                COALESCE(i.dim_item_id, 0),
                COALESCE(v.dim_vendor_id, 0),
                s.ordered_qty,
                s.ordered_unit_cost,
                s.ordered_value,
                s.po_status,
                s.source_pk_hash,
                NOW()
            FROM stg.purchase_order_line s
            LEFT JOIN core.dim_item i ON s.source_item_code = i.source_item_code
            LEFT JOIN core.dim_vendor v ON s.source_vendor_code = v.source_vendor_code
            WHERE s.etl_batch_id = :etl_batch_id
        """)

        with engine.begin() as conn:
            conn.execute(delete_sql, {"etl_batch_id": etl_batch_id})
            conn.execute(insert_sql, {"etl_batch_id": etl_batch_id})

        return inserted, updated
```

---

# 27) File: `jobs/job_008_goods_receipt_line.py`

```python id="6z5ux0"
import pandas as pd
from jobs.base import BaseETLJob
from utils.hashing import sha256_hash
from utils.validation import require_columns, require_not_null
from sqlalchemy import text
from db.postgres import get_postgres_engine

class Job008GoodsReceiptLine(BaseETLJob):
    job_code = "ETL-008"
    job_name = "load_goods_receipt_line"
    source_sql_file = "goods_receipt_line.sql"
    source_table = "goods_receipt_line"
    target_schema = "stg"
    target_table = "goods_receipt_line"
    load_mode = "append"

    def transform(self, df: pd.DataFrame, etl_batch_id: int, **kwargs) -> pd.DataFrame:
        require_columns(df, ["gr_no", "gr_date", "source_item_code", "source_warehouse_code", "received_qty"], self.job_name)
        require_not_null(df, "gr_no", self.job_name)
        require_not_null(df, "gr_date", self.job_name)
        require_not_null(df, "source_item_code", self.job_name)
        require_not_null(df, "source_warehouse_code", self.job_name)
        require_not_null(df, "received_qty", self.job_name)

        df["etl_batch_id"] = etl_batch_id
        df["source_pk_hash"] = df.apply(
            lambda r: sha256_hash(r["gr_no"], r["source_item_code"], r["source_warehouse_code"], r.get("lot_no")),
            axis=1
        )
        return df

    def load(self, df: pd.DataFrame, etl_batch_id: int, **kwargs):
        engine = get_postgres_engine()

        with engine.begin() as conn:
            conn.execute(text("DELETE FROM stg.goods_receipt_line WHERE etl_batch_id = :etl_batch_id"), {"etl_batch_id": etl_batch_id})

        inserted, updated = super().load(df, etl_batch_id=etl_batch_id)

        delete_sql = text("""
            DELETE FROM core.fact_goods_receipt_line f
            USING stg.goods_receipt_line s
            LEFT JOIN core.dim_item i ON s.source_item_code = i.source_item_code
            LEFT JOIN core.dim_warehouse w ON s.source_warehouse_code = w.source_warehouse_code
            WHERE s.etl_batch_id = :etl_batch_id
              AND f.gr_no = s.gr_no
              AND f.dim_item_id = COALESCE(i.dim_item_id, 0)
              AND f.dim_warehouse_id = COALESCE(w.dim_warehouse_id, 0)
        """)

        insert_sql = text("""
            INSERT INTO core.fact_goods_receipt_line (
                etl_batch_id, gr_no, gr_date, gr_date_id,
                po_no,
                dim_item_id, dim_warehouse_id, dim_vendor_id,
                lot_no, expiry_date,
                received_qty, received_unit_cost, received_value,
                source_row_hash, created_ts
            )
            SELECT
                s.etl_batch_id,
                s.gr_no,
                s.gr_date,
                TO_CHAR(s.gr_date, 'YYYYMMDD')::INTEGER,
                s.po_no,
                COALESCE(i.dim_item_id, 0),
                COALESCE(w.dim_warehouse_id, 0),
                COALESCE(v.dim_vendor_id, 0),
                s.lot_no,
                s.expiry_date,
                s.received_qty,
                s.received_unit_cost,
                s.received_value,
                s.source_pk_hash,
                NOW()
            FROM stg.goods_receipt_line s
            LEFT JOIN core.dim_item i ON s.source_item_code = i.source_item_code
            LEFT JOIN core.dim_warehouse w ON s.source_warehouse_code = w.source_warehouse_code
            LEFT JOIN core.dim_vendor v ON s.source_vendor_code = v.source_vendor_code
            WHERE s.etl_batch_id = :etl_batch_id
        """)

        with engine.begin() as conn:
            conn.execute(delete_sql, {"etl_batch_id": etl_batch_id})
            conn.execute(insert_sql, {"etl_batch_id": etl_batch_id})

        return inserted, updated
```

---

# 28) File: `jobs/job_009_refresh_marts.py`

```python id="52ghh1"
from pathlib import Path
from sqlalchemy import text
from db.postgres import get_postgres_engine
from utils.logging import logger
from utils.batch import log_table_run_start, log_table_run_finish

BASE_DIR = Path(__file__).resolve().parents[1]

class Job009RefreshMarts:
    job_code = "ETL-009"
    job_name = "refresh_marts"

    def run(self, etl_batch_id: int, from_date: str = None, to_date: str = None, from_month: int = None, to_month: int = None):
        engine = get_postgres_engine()

        daily_files = [
            ("mart", "sum_inventory_daily", "refresh_sum_inventory_daily.sql"),
            ("mart", "sum_stock_position_daily", "refresh_sum_stock_position_daily.sql"),
            ("mart", "sum_expiry_daily", "refresh_sum_expiry_daily.sql"),
            ("mart", "sum_consumption_daily", "refresh_sum_consumption_daily.sql"),
            ("mart", "sum_movement_daily", "refresh_sum_movement_daily.sql"),
            ("mart", "sum_dead_stock_daily", "refresh_sum_dead_stock_daily.sql"),
        ]

        monthly_files = [
            ("mart", "sum_consumption_monthly", "refresh_sum_consumption_monthly.sql"),
            ("mart", "sum_procurement_monthly", "refresh_sum_procurement_monthly.sql"),
            ("mart", "sum_budget_burn_monthly", "refresh_sum_budget_burn_monthly.sql"),
        ]

        for schema, table, filename in daily_files:
            table_run_id = log_table_run_start(etl_batch_id, schema, table, "core", "refresh")
            try:
                sql = (BASE_DIR / "sql" / "mart" / filename).read_text(encoding="utf-8")
                with engine.begin() as conn:
                    conn.execute(text(sql), {"from_date": from_date, "to_date": to_date})
                log_table_run_finish(table_run_id, run_status="success")
                logger.info(f"[{self.job_code}] Refreshed {table}")
            except Exception as e:
                log_table_run_finish(table_run_id, run_status="failed", error_message=str(e))
                raise

        for schema, table, filename in monthly_files:
            table_run_id = log_table_run_start(etl_batch_id, schema, table, "core", "refresh")
            try:
                sql = (BASE_DIR / "sql" / "mart" / filename).read_text(encoding="utf-8")
                with engine.begin() as conn:
                    conn.execute(text(sql), {"from_month": from_month, "to_month": to_month})
                log_table_run_finish(table_run_id, run_status="success")
                logger.info(f"[{self.job_code}] Refreshed {table}")
            except Exception as e:
                log_table_run_finish(table_run_id, run_status="failed", error_message=str(e))
                raise
```

---

# 29) File: `jobs/job_010_refresh_freshness.py`

```python id="2oyn1s"
from sqlalchemy import text
from db.postgres import get_postgres_engine

class Job010RefreshFreshness:
    job_code = "ETL-010"
    job_name = "refresh_data_freshness"

    def run(self, etl_batch_id: int, **kwargs):
        engine = get_postgres_engine()

        sql = text("""
            INSERT INTO ops.etl_data_freshness (
                data_domain, table_name, last_success_batch_id, last_data_ts, last_checked_ts, freshness_status, note
            )
            VALUES
                ('inventory', 'core.fact_stock_snapshot', :etl_batch_id, NOW(), NOW(), 'fresh', 'updated by ETL-010'),
                ('inventory', 'core.fact_stock_lot_snapshot', :etl_batch_id, NOW(), NOW(), 'fresh', 'updated by ETL-010'),
                ('inventory', 'core.fact_inventory_movement', :etl_batch_id, NOW(), NOW(), 'fresh', 'updated by ETL-010'),
                ('procurement', 'core.fact_purchase_order_line', :etl_batch_id, NOW(), NOW(), 'fresh', 'updated by ETL-010'),
                ('procurement', 'core.fact_goods_receipt_line', :etl_batch_id, NOW(), NOW(), 'fresh', 'updated by ETL-010')
            ON CONFLICT (data_domain, table_name)
            DO UPDATE SET
                last_success_batch_id = EXCLUDED.last_success_batch_id,
                last_data_ts = EXCLUDED.last_data_ts,
                last_checked_ts = EXCLUDED.last_checked_ts,
                freshness_status = EXCLUDED.freshness_status,
                note = EXCLUDED.note
        """)

        with engine.begin() as conn:
            conn.execute(sql, {"etl_batch_id": etl_batch_id})
```

---

# 30) File: `runners/__init__.py`

```python id="qk7bnc"
# runners package
```

---

# 31) File: `runners/daily_pipeline.py`

```python id="b9c3s2"
from utils.logging import logger
from utils.batch import create_batch, mark_batch_success, mark_batch_failed
from utils.dates import days_ago, today_date

from jobs.job_001_item_master import Job001ItemMaster
from jobs.job_002_warehouse_master import Job002WarehouseMaster
from jobs.job_003_vendor_master import Job003VendorMaster
from jobs.job_004_stock_balance import Job004StockBalance
from jobs.job_005_stock_lot_balance import Job005StockLotBalance
from jobs.job_006_inventory_movement import Job006InventoryMovement
from jobs.job_007_purchase_order_line import Job007PurchaseOrderLine
from jobs.job_008_goods_receipt_line import Job008GoodsReceiptLine
from jobs.job_009_refresh_marts import Job009RefreshMarts
from jobs.job_010_refresh_freshness import Job010RefreshFreshness

JOB_REGISTRY = {
    "ETL-001": Job001ItemMaster(),
    "ETL-002": Job002WarehouseMaster(),
    "ETL-003": Job003VendorMaster(),
    "ETL-004": Job004StockBalance(),
    "ETL-005": Job005StockLotBalance(),
    "ETL-006": Job006InventoryMovement(),
    "ETL-007": Job007PurchaseOrderLine(),
    "ETL-008": Job008GoodsReceiptLine(),
    "ETL-009": Job009RefreshMarts(),
    "ETL-010": Job010RefreshFreshness(),
}

def run_daily_pipeline():
    etl_batch_id = create_batch("daily_inventory_pipeline", "incremental")
    logger.info(f"Started ETL batch_id={etl_batch_id}")

    try:
        JOB_REGISTRY["ETL-001"].run(etl_batch_id)
        JOB_REGISTRY["ETL-002"].run(etl_batch_id)
        JOB_REGISTRY["ETL-003"].run(etl_batch_id)

        JOB_REGISTRY["ETL-004"].run(etl_batch_id)
        JOB_REGISTRY["ETL-005"].run(etl_batch_id)
        JOB_REGISTRY["ETL-006"].run(etl_batch_id)
        JOB_REGISTRY["ETL-007"].run(etl_batch_id)
        JOB_REGISTRY["ETL-008"].run(etl_batch_id)

        from_date = str(days_ago(120))
        to_date = str(today_date())
        from_month = int(str(days_ago(730)).replace("-", "")[:6])
        to_month = int(str(today_date()).replace("-", "")[:6])

        JOB_REGISTRY["ETL-009"].run(
            etl_batch_id,
            from_date=from_date,
            to_date=to_date,
            from_month=from_month,
            to_month=to_month
        )

        JOB_REGISTRY["ETL-010"].run(etl_batch_id)

        mark_batch_success(etl_batch_id)
        logger.info(f"ETL batch_id={etl_batch_id} completed successfully")

    except Exception as e:
        mark_batch_failed(etl_batch_id, str(e))
        logger.exception(f"ETL batch_id={etl_batch_id} failed")
        raise

def run_single_job(job_code: str):
    if job_code not in JOB_REGISTRY:
        raise ValueError(f"Unknown job code: {job_code}")

    etl_batch_id = create_batch(f"single_{job_code}", "repair")
    try:
        JOB_REGISTRY[job_code].run(etl_batch_id)
        mark_batch_success(etl_batch_id)
    except Exception as e:
        mark_batch_failed(etl_batch_id, str(e))
        raise
```

---

# 32) File: `runners/repair_runner.py`

```python id="jlwm9h"
from utils.logging import logger
from utils.batch import create_batch, mark_batch_success, mark_batch_failed
from runners.daily_pipeline import JOB_REGISTRY

def run_repair(args: dict):
    job_code = args.get("job")
    from_date = args.get("from-date")
    to_date = args.get("to-date")

    if not job_code:
        raise ValueError("repair requires --job")

    if job_code not in JOB_REGISTRY:
        raise ValueError(f"Unknown job code: {job_code}")

    etl_batch_id = create_batch(f"repair_{job_code}", "repair")
    logger.info(f"Started repair batch_id={etl_batch_id}, job={job_code}")

    try:
        JOB_REGISTRY[job_code].run(etl_batch_id, from_date=from_date, to_date=to_date)
        mark_batch_success(etl_batch_id)
        logger.info(f"Repair batch_id={etl_batch_id} completed successfully")
    except Exception as e:
        mark_batch_failed(etl_batch_id, str(e))
        logger.exception(f"Repair batch_id={etl_batch_id} failed")
        raise
```

---

# 33) File: `runners/backfill_runner.py`

```python id="v4k9sl"
from utils.logging import logger
from utils.batch import create_batch, mark_batch_success, mark_batch_failed
from runners.daily_pipeline import JOB_REGISTRY

def run_backfill(args: dict):
    from_date = args.get("from-date")
    to_date = args.get("to-date")

    etl_batch_id = create_batch("backfill_inventory_pipeline", "backfill")
    logger.info(f"Started backfill batch_id={etl_batch_id}, from={from_date}, to={to_date}")

    try:
        JOB_REGISTRY["ETL-001"].run(etl_batch_id, from_date=from_date, to_date=to_date)
        JOB_REGISTRY["ETL-002"].run(etl_batch_id, from_date=from_date, to_date=to_date)
        JOB_REGISTRY["ETL-003"].run(etl_batch_id, from_date=from_date, to_date=to_date)

        JOB_REGISTRY["ETL-004"].run(etl_batch_id, from_date=from_date, to_date=to_date)
        JOB_REGISTRY["ETL-005"].run(etl_batch_id, from_date=from_date, to_date=to_date)
        JOB_REGISTRY["ETL-006"].run(etl_batch_id, from_date=from_date, to_date=to_date)
        JOB_REGISTRY["ETL-007"].run(etl_batch_id, from_date=from_date, to_date=to_date)
        JOB_REGISTRY["ETL-008"].run(etl_batch_id, from_date=from_date, to_date=to_date)

        JOB_REGISTRY["ETL-009"].run(etl_batch_id, from_date=from_date, to_date=to_date)
        JOB_REGISTRY["ETL-010"].run(etl_batch_id)

        mark_batch_success(etl_batch_id)
        logger.info(f"Backfill batch_id={etl_batch_id} completed successfully")
    except Exception as e:
        mark_batch_failed(etl_batch_id, str(e))
        logger.exception(f"Backfill batch_id={etl_batch_id} failed")
        raise
```

---

# 34) File: `sql/source/README.md`

```markdown id="ghqpg6"
# Source SQL Folder

ไฟล์ในโฟลเดอร์นี้คือ SQL ที่ยิงไปยัง MariaDB `invs2019`

## Important Rules
- SELECT only
- ห้าม CREATE / UPDATE / DELETE / ALTER
- ห้าม temp object ถ้าไม่จำเป็น
- ให้ map column names ให้ตรงกับ staging contract ตั้งแต่ query source เลย
```

---

# 35) File: `sql/source/item_master.sql`

```sql id="9y2r4h"
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
```

---

# 36) File: `sql/source/warehouse_master.sql`

```sql id="1hkpqs"
-- TODO: Replace with real invs2019 source query
SELECT
    warehouse_code AS source_warehouse_code,
    warehouse_name,
    warehouse_type,
    parent_warehouse_code,
    is_active,
    updated_at AS source_updated_ts
FROM your_warehouse_master_table;
```

---

# 37) File: `sql/source/vendor_master.sql`

```sql id="7d6x3t"
-- TODO: Replace with real invs2019 source query
SELECT
    vendor_code AS source_vendor_code,
    vendor_name,
    vendor_type,
    is_active,
    updated_at AS source_updated_ts
FROM your_vendor_master_table;
```

---

# 38) File: `sql/source/stock_balance.sql`

```sql id="rj4a0j"
-- TODO: Replace with real invs2019 source query
SELECT
    snapshot_date,
    item_code AS source_item_code,
    warehouse_code AS source_warehouse_code,
    qty_on_hand,
    avg_unit_cost,
    stock_value,
    updated_at AS source_updated_ts
FROM your_stock_balance_table;
```

---

# 39) File: `sql/source/stock_lot_balance.sql`

```sql id="j3q2ln"
-- TODO: Replace with real invs2019 source query
SELECT
    snapshot_date,
    item_code AS source_item_code,
    warehouse_code AS source_warehouse_code,
    lot_no,
    expiry_date,
    qty_on_hand,
    avg_unit_cost,
    stock_value,
    updated_at AS source_updated_ts
FROM your_stock_lot_balance_table;
```

---

# 40) File: `sql/source/inventory_movement.sql`

```sql id="vl8x65"
-- TODO: Replace with real invs2019 source query
SELECT
    txn_id AS source_txn_id,
    txn_date,
    txn_ts,
    item_code AS source_item_code,
    warehouse_code AS source_warehouse_code,
    movement_type,
    ref_doc_no,
    ref_doc_type,
    lot_no,
    expiry_date,
    qty,
    unit_cost,
    line_value,
    vendor_code AS source_vendor_code,
    updated_at AS source_updated_ts
FROM your_inventory_movement_table;
```

---

# 41) File: `sql/source/purchase_order_line.sql`

```sql id="t9t4sv"
-- TODO: Replace with real invs2019 source query
SELECT
    po_no,
    po_date,
    item_code AS source_item_code,
    vendor_code AS source_vendor_code,
    ordered_qty,
    ordered_unit_cost,
    ordered_value,
    po_status,
    updated_at AS source_updated_ts
FROM your_purchase_order_line_table;
```

---

# 42) File: `sql/source/goods_receipt_line.sql`

```sql id="pn5mrg"
-- TODO: Replace with real invs2019 source query
SELECT
    gr_no,
    gr_date,
    po_no,
    item_code AS source_item_code,
    warehouse_code AS source_warehouse_code,
    vendor_code AS source_vendor_code,
    lot_no,
    expiry_date,
    received_qty,
    received_unit_cost,
    received_value,
    updated_at AS source_updated_ts
FROM your_goods_receipt_line_table;
```

---

# 43) File: `sql/core/upsert_dim_item.sql`

```sql id="qyk4zq"
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

# 44) File: `sql/core/upsert_dim_warehouse.sql`

```sql id="izx4wy"
INSERT INTO core.dim_warehouse (
    source_warehouse_code,
    warehouse_name,
    warehouse_type,
    parent_warehouse_code,
    is_active,
    first_seen_ts,
    last_seen_ts,
    current_record_flag
)
SELECT
    s.source_warehouse_code,
    s.warehouse_name,
    s.warehouse_type,
    s.parent_warehouse_code,
    COALESCE(s.is_active, TRUE),
    NOW(),
    NOW(),
    TRUE
FROM stg.warehouse_master s
WHERE s.etl_batch_id = :etl_batch_id
ON CONFLICT (source_warehouse_code)
DO UPDATE SET
    warehouse_name = EXCLUDED.warehouse_name,
    warehouse_type = EXCLUDED.warehouse_type,
    parent_warehouse_code = EXCLUDED.parent_warehouse_code,
    is_active = EXCLUDED.is_active,
    last_seen_ts = NOW(),
    current_record_flag = TRUE;
```

---

# 45) File: `sql/core/upsert_dim_vendor.sql`

```sql id="j4i5je"
INSERT INTO core.dim_vendor (
    source_vendor_code,
    vendor_name,
    vendor_type,
    is_active,
    first_seen_ts,
    last_seen_ts,
    current_record_flag
)
SELECT
    s.source_vendor_code,
    s.vendor_name,
    s.vendor_type,
    COALESCE(s.is_active, TRUE),
    NOW(),
    NOW(),
    TRUE
FROM stg.vendor_master s
WHERE s.etl_batch_id = :etl_batch_id
ON CONFLICT (source_vendor_code)
DO UPDATE SET
    vendor_name = EXCLUDED.vendor_name,
    vendor_type = EXCLUDED.vendor_type,
    is_active = EXCLUDED.is_active,
    last_seen_ts = NOW(),
    current_record_flag = TRUE;
```

---

# 46) File: `sql/mart/refresh_sum_inventory_daily.sql`

```sql id="p9h2df"
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
    COUNT(DISTINCT f.dim_item_id),
    COUNT(DISTINCT CASE WHEN i.is_active THEN f.dim_item_id END),
    COUNT(DISTINCT f.dim_warehouse_id),
    COALESCE(SUM(f.qty_on_hand), 0),
    COALESCE(SUM(f.stock_value), 0),
    COUNT(DISTINCT CASE WHEN f.qty_on_hand = 0 THEN f.dim_item_id END),
    COUNT(DISTINCT CASE WHEN f.qty_on_hand < 0 THEN f.dim_item_id END),
    0,
    0,
    0,
    NOW()
FROM core.fact_stock_snapshot f
LEFT JOIN core.dim_item i ON f.dim_item_id = i.dim_item_id
WHERE f.snapshot_date >= :from_date
  AND f.snapshot_date <= :to_date
GROUP BY f.snapshot_date;
```

---

# 47) File: `sql/mart/refresh_sum_stock_position_daily.sql`

```sql id="qgq2zz"
DELETE FROM mart.sum_stock_position_daily
WHERE summary_date >= :from_date
  AND summary_date <= :to_date;

INSERT INTO mart.sum_stock_position_daily (
    summary_date,
    dim_item_id,
    dim_warehouse_id,
    qty_on_hand,
    avg_unit_cost,
    stock_value,
    stock_status,
    days_of_stock_est,
    reorder_flag,
    overstock_flag,
    created_ts
)
SELECT
    snapshot_date,
    dim_item_id,
    dim_warehouse_id,
    qty_on_hand,
    avg_unit_cost,
    stock_value,
    stock_status,
    NULL,
    FALSE,
    FALSE,
    NOW()
FROM core.fact_stock_snapshot
WHERE snapshot_date >= :from_date
  AND snapshot_date <= :to_date;
```

---

# 48) File: `sql/mart/refresh_sum_expiry_daily.sql`

```sql id="squr6d"
DELETE FROM mart.sum_expiry_daily
WHERE summary_date >= :from_date
  AND summary_date <= :to_date;

INSERT INTO mart.sum_expiry_daily (
    summary_date,
    dim_item_id,
    dim_warehouse_id,
    lot_no,
    expiry_date,
    days_to_expiry,
    expiry_status,
    qty_on_hand,
    stock_value,
    created_ts
)
SELECT
    snapshot_date,
    dim_item_id,
    dim_warehouse_id,
    lot_no,
    expiry_date,
    days_to_expiry,
    expiry_status,
    qty_on_hand,
    stock_value,
    NOW()
FROM core.fact_stock_lot_snapshot
WHERE snapshot_date >= :from_date
  AND snapshot_date <= :to_date;
```

---

# 49) File: `sql/mart/refresh_sum_consumption_daily.sql`

```sql id="d3ktzz"
DELETE FROM mart.sum_consumption_daily
WHERE summary_date >= :from_date
  AND summary_date <= :to_date;

INSERT INTO mart.sum_consumption_daily (
    summary_date,
    dim_item_id,
    dim_warehouse_id,
    issue_qty,
    issue_value,
    avg_daily_consumption_30d,
    avg_daily_consumption_90d,
    created_ts
)
SELECT
    txn_date,
    dim_item_id,
    dim_warehouse_id,
    COALESCE(SUM(CASE WHEN movement_direction = 'out' THEN ABS(signed_qty) ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN movement_direction = 'out' THEN ABS(signed_value) ELSE 0 END), 0),
    NULL,
    NULL,
    NOW()
FROM core.fact_inventory_movement
WHERE txn_date >= :from_date
  AND txn_date <= :to_date
GROUP BY txn_date, dim_item_id, dim_warehouse_id;
```

---

# 50) File: `sql/mart/refresh_sum_consumption_monthly.sql`

```sql id="efzwxk"
DELETE FROM mart.sum_consumption_monthly
WHERE year_month >= :from_month
  AND year_month <= :to_month;

INSERT INTO mart.sum_consumption_monthly (
    year_month,
    dim_item_id,
    dim_warehouse_id,
    issue_qty,
    issue_value,
    movement_days,
    created_ts
)
SELECT
    TO_CHAR(txn_date, 'YYYYMM')::INTEGER AS year_month,
    dim_item_id,
    dim_warehouse_id,
    COALESCE(SUM(CASE WHEN movement_direction = 'out' THEN ABS(signed_qty) ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN movement_direction = 'out' THEN ABS(signed_value) ELSE 0 END), 0),
    COUNT(DISTINCT txn_date),
    NOW()
FROM core.fact_inventory_movement
WHERE TO_CHAR(txn_date, 'YYYYMM')::INTEGER >= :from_month
  AND TO_CHAR(txn_date, 'YYYYMM')::INTEGER <= :to_month
GROUP BY TO_CHAR(txn_date, 'YYYYMM')::INTEGER, dim_item_id, dim_warehouse_id;
```

---

# 51) File: `sql/mart/refresh_sum_movement_daily.sql`

```sql id="jthzj3"
DELETE FROM mart.sum_movement_daily
WHERE summary_date >= :from_date
  AND summary_date <= :to_date;

INSERT INTO mart.sum_movement_daily (
    summary_date,
    dim_item_id,
    dim_warehouse_id,
    movement_type,
    movement_qty,
    movement_value,
    txn_count,
    created_ts
)
SELECT
    txn_date,
    dim_item_id,
    dim_warehouse_id,
    movement_type,
    COALESCE(SUM(ABS(qty)), 0),
    COALESCE(SUM(ABS(COALESCE(line_value, 0))), 0),
    COUNT(*),
    NOW()
FROM core.fact_inventory_movement
WHERE txn_date >= :from_date
  AND txn_date <= :to_date
GROUP BY txn_date, dim_item_id, dim_warehouse_id, movement_type;
```

---

# 52) File: `sql/mart/refresh_sum_dead_stock_daily.sql`

```sql id="dyd78u"
DELETE FROM mart.sum_dead_stock_daily
WHERE summary_date >= :from_date
  AND summary_date <= :to_date;

INSERT INTO mart.sum_dead_stock_daily (
    summary_date,
    dim_item_id,
    dim_warehouse_id,
    qty_on_hand,
    stock_value,
    last_issue_date,
    days_since_last_issue,
    dead_stock_flag,
    slow_moving_flag,
    created_ts
)
SELECT
    f.snapshot_date,
    f.dim_item_id,
    f.dim_warehouse_id,
    f.qty_on_hand,
    f.stock_value,
    x.last_issue_date,
    CASE
        WHEN x.last_issue_date IS NULL THEN NULL
        ELSE (f.snapshot_date - x.last_issue_date)
    END AS days_since_last_issue,
    CASE
        WHEN x.last_issue_date IS NULL AND f.qty_on_hand > 0 THEN TRUE
        WHEN x.last_issue_date IS NOT NULL AND (f.snapshot_date - x.last_issue_date) >= 180 AND f.qty_on_hand > 0 THEN TRUE
        ELSE FALSE
    END AS dead_stock_flag,
    CASE
        WHEN x.last_issue_date IS NOT NULL AND (f.snapshot_date - x.last_issue_date) BETWEEN 90 AND 179 AND f.qty_on_hand > 0 THEN TRUE
        ELSE FALSE
    END AS slow_moving_flag,
    NOW()
FROM core.fact_stock_snapshot f
LEFT JOIN (
    SELECT
        dim_item_id,
        dim_warehouse_id,
        MAX(txn_date) AS last_issue_date
    FROM core.fact_inventory_movement
    WHERE movement_direction = 'out'
    GROUP BY dim_item_id, dim_warehouse_id
) x
    ON f.dim_item_id = x.dim_item_id
   AND f.dim_warehouse_id = x.dim_warehouse_id
WHERE f.snapshot_date >= :from_date
  AND f.snapshot_date <= :to_date;
```

---

# 53) File: `sql/mart/refresh_sum_procurement_monthly.sql`

```sql id="bw6ahk"
DELETE FROM mart.sum_procurement_monthly
WHERE year_month >= :from_month
  AND year_month <= :to_month;

INSERT INTO mart.sum_procurement_monthly (
    year_month,
    dim_item_id,
    dim_vendor_id,
    ordered_qty,
    ordered_value,
    received_qty,
    received_value,
    po_count,
    gr_count,
    created_ts
)
WITH po AS (
    SELECT
        TO_CHAR(po_date, 'YYYYMM')::INTEGER AS year_month,
        dim_item_id,
        dim_vendor_id,
        SUM(ordered_qty) AS ordered_qty,
        SUM(COALESCE(ordered_value, 0)) AS ordered_value,
        COUNT(DISTINCT po_no) AS po_count
    FROM core.fact_purchase_order_line
    WHERE TO_CHAR(po_date, 'YYYYMM')::INTEGER >= :from_month
      AND TO_CHAR(po_date, 'YYYYMM')::INTEGER <= :to_month
    GROUP BY TO_CHAR(po_date, 'YYYYMM')::INTEGER, dim_item_id, dim_vendor_id
),
gr AS (
    SELECT
        TO_CHAR(gr_date, 'YYYYMM')::INTEGER AS year_month,
        dim_item_id,
        dim_vendor_id,
        SUM(received_qty) AS received_qty,
        SUM(COALESCE(received_value, 0)) AS received_value,
        COUNT(DISTINCT gr_no) AS gr_count
    FROM core.fact_goods_receipt_line
    WHERE TO_CHAR(gr_date, 'YYYYMM')::INTEGER >= :from_month
      AND TO_CHAR(gr_date, 'YYYYMM')::INTEGER <= :to_month
    GROUP BY TO_CHAR(gr_date, 'YYYYMM')::INTEGER, dim_item_id, dim_vendor_id
)
SELECT
    COALESCE(po.year_month, gr.year_month) AS year_month,
    COALESCE(po.dim_item_id, gr.dim_item_id) AS dim_item_id,
    COALESCE(po.dim_vendor_id, gr.dim_vendor_id) AS dim_vendor_id,
    COALESCE(po.ordered_qty, 0),
    COALESCE(po.ordered_value, 0),
    COALESCE(gr.received_qty, 0),
    COALESCE(gr.received_value, 0),
    COALESCE(po.po_count, 0),
    COALESCE(gr.gr_count, 0),
    NOW()
FROM po
FULL OUTER JOIN gr
    ON po.year_month = gr.year_month
   AND po.dim_item_id = gr.dim_item_id
   AND COALESCE(po.dim_vendor_id, -1) = COALESCE(gr.dim_vendor_id, -1);
```

---

# 54) File: `sql/mart/refresh_sum_budget_burn_monthly.sql`

```sql id="8b0trr"
DELETE FROM mart.sum_budget_burn_monthly
WHERE year_month >= :from_month
  AND year_month <= :to_month;

INSERT INTO mart.sum_budget_burn_monthly (
    year_month,
    budget_amount,
    actual_spend_amount,
    variance_amount,
    burn_rate_pct,
    ytd_actual_spend,
    created_ts
)
WITH monthly_spend AS (
    SELECT
        TO_CHAR(gr_date, 'YYYYMM')::INTEGER AS year_month,
        SUM(COALESCE(received_value, 0)) AS actual_spend_amount
    FROM core.fact_goods_receipt_line
    WHERE TO_CHAR(gr_date, 'YYYYMM')::INTEGER >= :from_month
      AND TO_CHAR(gr_date, 'YYYYMM')::INTEGER <= :to_month
    GROUP BY TO_CHAR(gr_date, 'YYYYMM')::INTEGER
)
SELECT
    year_month,
    NULL AS budget_amount,
    actual_spend_amount,
    NULL AS variance_amount,
    NULL AS burn_rate_pct,
    SUM(actual_spend_amount) OVER (ORDER BY year_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ytd_actual_spend,
    NOW()
FROM monthly_spend;
```

---

# 55) What You Must Edit First (Critical)

ก่อนรันจริง พี่ต้องแก้ 3 จุดก่อน ไม่งั้นมันจะ “ดูดีแต่ไม่ทำงาน”:

## 55.1 Replace Source SQL

แก้ไฟล์ใน:

```text id="j2v8cl"
sql/source/*.sql
```

ให้ชี้ไปยัง table จริงใน `invs2019`

---

## 55.2 Seed `core.dim_date`

ต้องมีข้อมูลใน `core.dim_date` ก่อน
ไม่งั้น fact load จะพังตอน insert `date_id`

---

## 55.3 Check PostgreSQL DDL

ต้อง deploy PRD v1.6 ก่อน
ไม่งั้น table/schema จะไม่มี

---

# 56) Recommended First Run Order

```bash id="y08mlc"
python main.py job ETL-001
python main.py job ETL-002
python main.py job ETL-003

python main.py job ETL-004
python main.py job ETL-005
python main.py job ETL-006
python main.py job ETL-007
python main.py job ETL-008

python main.py job ETL-009
python main.py job ETL-010
```

ถ้าทุกอย่างผ่าน ค่อยรัน:

```bash id="a7xk7p"
python main.py daily
```

---

# 57) Immediate Next Best Step

ตอนนี้สิ่งที่ “คุ้มค่าที่สุด” ไม่ใช่เขียนเพิ่มมั่ว ๆ
แต่คือ:

# 👉 ทำ “Source SQL Mapping Pack” ต่อทันที

เพราะตอนนี้ scaffold พร้อมแล้ว
สิ่งที่ยังขาดจริง ๆ คือ:

* source table ไหนของ `invs2019` ใช้แทน `item_master`
* movement มาจาก table ไหน
* stock snapshot มาจาก table ไหน
* lot / expiry อยู่ table ไหน
* PO / GR อยู่ table ไหน

พูดตรง ๆ:

> ตอนนี้โครงสร้างพร้อมรบแล้ว
> เหลือแค่ “ใส่กระสุนให้ตรงลำกล้อง”

---

# 58) Final Note

starter pack นี้ถูกออกแบบให้:

* practical
* copy เป็นไฟล์ได้
* เริ่ม implement จริงได้
* ไม่แตะ source DB
* รองรับ production-friendly ETL pattern ตั้งแต่วันแรก

---

# END OF FILE
