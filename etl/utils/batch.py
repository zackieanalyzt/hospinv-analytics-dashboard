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
