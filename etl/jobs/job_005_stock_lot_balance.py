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
