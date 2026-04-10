from utils.logging import logger
from utils.batch import create_batch, mark_batch_success, mark_batch_failed
from utils.dates import days_ago, today_date
from runners.daily_pipeline import JOB_REGISTRY
from datetime import datetime, timedelta

def run_backfill(args: dict):
    from_date_str = args.get("from-date")
    to_date_str = args.get("to-date")
    
    if not from_date_str or not to_date_str:
        raise ValueError("backfill requires --from-date and --to-date")
    
    from_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d").date()
    
    logger.info(f"Starting backfill from={from_date}, to={to_date}")
    
    current_date = from_date
    while current_date <= to_date:
        date_str = current_date.strftime("%Y-%m-%d")
        etl_batch_id = create_batch(f"backfill_{date_str}", "backfill")
        logger.info(f"Backfill batch_id={etl_batch_id}, date={date_str}")
        
        try:
            JOB_REGISTRY["ETL-001"].run(etl_batch_id, watermark_from=date_str, watermark_to=date_str, mode="incremental")
            JOB_REGISTRY["ETL-002"].run(etl_batch_id, watermark_from=date_str, watermark_to=date_str, mode="incremental")
            JOB_REGISTRY["ETL-003"].run(etl_batch_id, watermark_from=date_str, watermark_to=date_str, mode="incremental")
            
            JOB_REGISTRY["ETL-004"].run(etl_batch_id, watermark_from=date_str, watermark_to=date_str, mode="incremental")
            JOB_REGISTRY["ETL-005"].run(etl_batch_id, watermark_from=date_str, watermark_to=date_str, mode="incremental")
            JOB_REGISTRY["ETL-006"].run(etl_batch_id, watermark_from=date_str, watermark_to=date_str, mode="incremental")
            JOB_REGISTRY["ETL-007"].run(etl_batch_id, watermark_from=date_str, watermark_to=date_str, mode="incremental")
            JOB_REGISTRY["ETL-008"].run(etl_batch_id, watermark_from=date_str, watermark_to=date_str, mode="incremental")
            
            JOB_REGISTRY["ETL-009"].run(etl_batch_id, from_date=date_str, to_date=date_str)
            JOB_REGISTRY["ETL-010"].run(etl_batch_id)
            
            mark_batch_success(etl_batch_id)
            logger.info(f"Backfill for {date_str} completed successfully")
        except Exception as e:
            mark_batch_failed(etl_batch_id, str(e))
            logger.exception(f"Backfill for {date_str} failed")
            raise
        
        current_date += timedelta(days=1)
    
    logger.info(f"Full backfill from={from_date} to={to_date} completed")
