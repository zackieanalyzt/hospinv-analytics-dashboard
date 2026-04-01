import os
from config.env import *

MARIADB = {
    "host": os.getenv("MARIADB_HOST"),
    "port": int(os.getenv("MARIADB_PORT", 3306)),
    "db": os.getenv("MARIADB_DB"),
    "user": os.getenv("MARIADB_USER"),
    "password": os.getenv("MARIADB_PASSWORD"),
}

POSTGRES = {
    "host": os.getenv("PG_HOST"),
    "port": int(os.getenv("PG_PORT", 5432)),
    "db": os.getenv("PG_DB"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
}

ETL_BATCH_TRIGGER = os.getenv("ETL_BATCH_TRIGGER", "system")
ETL_DEFAULT_LOOKBACK_DAYS = int(os.getenv("ETL_DEFAULT_LOOKBACK_DAYS", 3))
EXPIRY_NEAR_THRESHOLD_DAYS = int(os.getenv("EXPIRY_NEAR_THRESHOLD_DAYS", 90))
ETL_LOG_LEVEL = os.getenv("ETL_LOG_LEVEL", "INFO")
