from utils.logging import logger
from utils.batch import create_batch, mark_batch_success, mark_batch_failed
from runners.daily_pipeline import JOB_REGISTRY

def run_backfill(args: dict):
    from_date = args.get("from-date")
    to_date = args.get("to-date")

    etl_batch_id = create_batch("backfill_inventory_pipeline", "backfill")
    logger.info(f"Started backfill batch_id={etl_batch_id}, from={from_date}, to={to_date}")

    try:
        JOB_REGISTRY["ETL-001"].run(etl_batch_id, from_date=from_date, to_date=to_date)
        JOB_REGISTRY["ETL-002"].run(etl_batch_id, from_date=from_date, to_date=to_date)
        JOB_REGISTRY["ETL-003"].run(etl_batch_id, from_date=from_date, to_date=to_date)

        JOB_REGISTRY["ETL-004"].run(etl_batch_id, from_date=from_date, to_date=to_date)
        JOB_REGISTRY["ETL-005"].run(etl_batch_id, from_date=from_date, to_date=to_date)
        JOB_REGISTRY["ETL-006"].run(etl_batch_id, from_date=from_date, to_date=to_date)
        JOB_REGISTRY["ETL-007"].run(etl_batch_id, from_date=from_date, to_date=to_date)
        JOB_REGISTRY["ETL-008"].run(etl_batch_id, from_date=from_date, to_date=to_date)

        JOB_REGISTRY["ETL-009"].run(etl_batch_id, from_date=from_date, to_date=to_date)
        JOB_REGISTRY["ETL-010"].run(etl_batch_id)

        mark_batch_success(etl_batch_id)
        logger.info(f"Backfill batch_id={etl_batch_id} completed successfully")
    except Exception as e:
        mark_batch_failed(etl_batch_id, str(e))
        logger.exception(f"Backfill batch_id={etl_batch_id} failed")
        raise
