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
