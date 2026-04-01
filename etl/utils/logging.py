import sys
from loguru import logger
from config.settings import ETL_LOG_LEVEL

logger.remove()
logger.add(sys.stdout, level=ETL_LOG_LEVEL, backtrace=True, diagnose=True)
