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
