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
        
        if "is_active" in df.columns:
            df["is_active"] = df["is_active"].astype(bool)
        
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
