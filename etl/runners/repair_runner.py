from utils.logging import logger
from utils.batch import create_batch, mark_batch_success, mark_batch_failed
from runners.daily_pipeline import JOB_REGISTRY

def run_repair(args: dict):
    job_code = args.get("job")
    from_date = args.get("from-date")
    to_date = args.get("to-date")

    if not job_code:
        raise ValueError("repair requires --job")

    if job_code not in JOB_REGISTRY:
        raise ValueError(f"Unknown job code: {job_code}")

    etl_batch_id = create_batch(f"repair_{job_code}", "repair")
    logger.info(f"Started repair batch_id={etl_batch_id}, job={job_code}")

    try:
        JOB_REGISTRY[job_code].run(etl_batch_id, from_date=from_date, to_date=to_date)
        mark_batch_success(etl_batch_id)
        logger.info(f"Repair batch_id={etl_batch_id} completed successfully")
    except Exception as e:
        mark_batch_failed(etl_batch_id, str(e))
        logger.exception(f"Repair batch_id={etl_batch_id} failed")
        raise
