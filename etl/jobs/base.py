from pathlib import Path
import pandas as pd
from sqlalchemy import text
from utils.logging import logger
from db.mariadb import get_mariadb_engine
from db.postgres import get_postgres_engine
from utils.batch import log_table_run_start, log_table_run_finish
from config.settings import ETL_DEFAULT_LOOKBACK_DAYS
from utils.dates import days_ago, today_date

BASE_DIR = Path(__file__).resolve().parents[1]

class BaseETLJob:
    job_code = "ETL-000"
    job_name = "base_job"
    source_sql_file = None
    source_table = "unknown_source"
    target_schema = "stg"
    target_table = "unknown_target"
    load_mode = "append"
    lookback_days = ETL_DEFAULT_LOOKBACK_DAYS

    def run(self, etl_batch_id: int, mode: str = "incremental", **kwargs):
        self.load_mode = mode
        
        etl_table_run_id = log_table_run_start(
            etl_batch_id=etl_batch_id,
            target_schema=self.target_schema,
            target_table=self.target_table,
            source_table=self.source_table,
            load_mode=self.load_mode
        )

        try:
            watermark_from = kwargs.get("watermark_from")
            watermark_to = kwargs.get("watermark_to")
            
            if mode == "incremental" and not watermark_from:
                watermark_to = today_date()
                watermark_from = days_ago(self.lookback_days)
            
            df = self.extract(watermark_from=watermark_from, watermark_to=watermark_to, **kwargs)
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

    def extract(self, watermark_from=None, watermark_to=None, **kwargs) -> pd.DataFrame:
        if not self.source_sql_file:
            raise NotImplementedError("source_sql_file not defined")

        sql_path = BASE_DIR / "sql" / "source" / self.source_sql_file
        sql = sql_path.read_text(encoding="utf-8")

        engine = get_mariadb_engine()
        params = {}
        if watermark_from:
            params["watermark_from"] = watermark_from
        if watermark_to:
            params["watermark_to"] = watermark_to
        
        if params:
            return pd.read_sql(text(sql), engine, params=params)
        return pd.read_sql(text(sql), engine)

    def transform(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        return df

    def load(self, df: pd.DataFrame, etl_batch_id: int = None, **kwargs):
        from datetime import datetime
        engine = get_postgres_engine()
        
        if 'extracted_ts' not in df.columns:
            df['extracted_ts'] = datetime.now()
        
        inserted = len(df)
        updated = 0
        
        df.to_sql(self.target_table, engine, schema=self.target_schema, if_exists="append", index=False, method="multi", chunksize=1000)
        return inserted, updated
