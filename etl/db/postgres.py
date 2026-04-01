from sqlalchemy import create_engine
from config.settings import POSTGRES

def get_postgres_engine():
    url = (
        f"postgresql+psycopg2://{POSTGRES['user']}:{POSTGRES['password']}"
        f"@{POSTGRES['host']}:{POSTGRES['port']}/{POSTGRES['db']}"
    )
    return create_engine(url, pool_pre_ping=True)
