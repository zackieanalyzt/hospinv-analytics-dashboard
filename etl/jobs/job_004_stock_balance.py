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
        snapshot_dates = [str(d) for d in df["snapshot_date"].unique().tolist()]

        with engine.begin() as conn:
            conn.execute(text("DELETE FROM stg.stock_balance WHERE etl_batch_id = :etl_batch_id"), {"etl_batch_id": etl_batch_id})

        inserted, updated = super().load(df, etl_batch_id=etl_batch_id)

        delete_sql = text("""
            DELETE FROM core.fact_stock_snapshot
            WHERE snapshot_date::text = ANY(:snapshot_dates)
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
                COALESCE(i.dim_item_id, -1),
                COALESCE(w.dim_warehouse_id, -1),
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
