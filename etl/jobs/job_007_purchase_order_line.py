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
                COALESCE(i.dim_item_id, -1),
                COALESCE(v.dim_vendor_id, -1),
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
