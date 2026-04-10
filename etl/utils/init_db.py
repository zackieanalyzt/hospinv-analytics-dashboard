import os
import sys
from pathlib import Path
import re
from sqlalchemy import text
from loguru import logger

# Add parent directory to sys.path to import from sibling packages
sys.path.append(str(Path(__file__).resolve().parents[1]))

from db.postgres import get_postgres_engine

def extract_sql_from_prd(prd_path: Path):
    """
    Extracts the SQL block from the PRD markdown file.
    """
    content = prd_path.read_text(encoding="utf-8")
    # Search for SQL block starting after "01) SCHEMAS" or similar
    # In PRD_v1.6.md, it's inside a ```sql ... ``` block
    match = re.search(r"```sql\n(.*?)\n```", content, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find SQL block in {prd_path}")
    
    return match.group(1)

def init_db():
    base_dir = Path(__file__).resolve().parents[2]
    prd_path = base_dir / "PRD_v1.6.md"
    
    logger.info(f"Extracting DDL from {prd_path}...")
    try:
        sql_script = extract_sql_from_prd(prd_path)
    except Exception as e:
        logger.error(f"Failed to extract SQL: {e}")
        return

    # Split the script into individual statements to handle errors better
    # and because some drivers/engines might not support multi-statement execution in one go
    # However, standard PostgreSQL/psycopg2 handles multi-statement if needed.
    # We'll use a transaction block.
    
    engine = get_postgres_engine()
    
    logger.info("Connecting to PostgreSQL and executing DDL...")
    try:
        with engine.begin() as conn:
            # We execute the whole script as one unit if possible
            # or we could split by ';' but that's tricky with comments/triggers
            conn.execute(text(sql_script))
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

if __name__ == "__main__":
    init_db()
