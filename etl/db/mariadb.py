from sqlalchemy import create_engine
from config.settings import MARIADB

def get_mariadb_engine():
    url = (
        f"mysql+pymysql://{MARIADB['user']}:{MARIADB['password']}"
        f"@{MARIADB['host']}:{MARIADB['port']}/{MARIADB['db']}"
        f"?charset=utf8mb4"
    )
    return create_engine(url, pool_pre_ping=True)
