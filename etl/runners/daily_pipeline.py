from utils.logging import logger
from utils.batch import create_batch, mark_batch_success, mark_batch_failed
from utils.dates import days_ago, today_date

from jobs.job_001_item_master import Job001ItemMaster
from jobs.job_002_warehouse_master import Job002WarehouseMaster
from jobs.job_003_vendor_master import Job003VendorMaster
from jobs.job_004_stock_balance import Job004StockBalance
from jobs.job_005_stock_lot_balance import Job005StockLotBalance
from jobs.job_006_inventory_movement import Job006InventoryMovement
from jobs.job_007_purchase_order_line import Job007PurchaseOrderLine
from jobs.job_008_goods_receipt_line import Job008GoodsReceiptLine
from jobs.job_009_refresh_marts import Job009RefreshMarts
from jobs.job_010_refresh_freshness import Job010RefreshFreshness

JOB_REGISTRY = {
    "ETL-001": Job001ItemMaster(),
    "ETL-002": Job002WarehouseMaster(),
    "ETL-003": Job003VendorMaster(),
    "ETL-004": Job004StockBalance(),
    "ETL-005": Job005StockLotBalance(),
    "ETL-006": Job006InventoryMovement(),
    "ETL-007": Job007PurchaseOrderLine(),
    "ETL-008": Job008GoodsReceiptLine(),
    "ETL-009": Job009RefreshMarts(),
    "ETL-010": Job010RefreshFreshness(),
}

def run_daily_pipeline(mode: str = "incremental"):
    etl_batch_id = create_batch("daily_inventory_pipeline", mode)
    logger.info(f"Started ETL batch_id={etl_batch_id}, mode={mode}")

    try:
        JOB_REGISTRY["ETL-001"].run(etl_batch_id, mode=mode)
        JOB_REGISTRY["ETL-002"].run(etl_batch_id, mode=mode)
        JOB_REGISTRY["ETL-003"].run(etl_batch_id, mode=mode)

        JOB_REGISTRY["ETL-004"].run(etl_batch_id, mode=mode)
        JOB_REGISTRY["ETL-005"].run(etl_batch_id, mode=mode)
        JOB_REGISTRY["ETL-006"].run(etl_batch_id, mode=mode)
        JOB_REGISTRY["ETL-007"].run(etl_batch_id, mode=mode)
        JOB_REGISTRY["ETL-008"].run(etl_batch_id, mode=mode)

        from_date = str(days_ago(120))
        to_date = str(today_date())
        from_month = int(str(days_ago(730)).replace("-", "")[:6])
        to_month = int(str(today_date()).replace("-", "")[:6])

        JOB_REGISTRY["ETL-009"].run(
            etl_batch_id,
            from_date=from_date,
            to_date=to_date,
            from_month=from_month,
            to_month=to_month
        )

        JOB_REGISTRY["ETL-010"].run(etl_batch_id)

        mark_batch_success(etl_batch_id)
        logger.info(f"ETL batch_id={etl_batch_id} completed successfully")

    except Exception as e:
        mark_batch_failed(etl_batch_id, str(e))
        logger.exception(f"ETL batch_id={etl_batch_id} failed")
        raise

def run_single_job(job_code: str, mode: str = "incremental"):
    if job_code not in JOB_REGISTRY:
        raise ValueError(f"Unknown job code: {job_code}")

    batch_type = "full" if mode == "full" else "repair"
    etl_batch_id = create_batch(f"single_{job_code}", batch_type)
    try:
        JOB_REGISTRY[job_code].run(etl_batch_id, mode=mode)
        mark_batch_success(etl_batch_id)
    except Exception as e:
        mark_batch_failed(etl_batch_id, str(e))
        raise
