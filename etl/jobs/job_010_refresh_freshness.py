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
