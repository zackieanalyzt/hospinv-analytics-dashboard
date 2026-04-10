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
                COALESCE(i.dim_item_id, -1),
                COALESCE(w.dim_warehouse_id, -1),
                COALESCE(v.dim_vendor_id, -1),
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
