"""
Database connection utilities for PostgreSQL analytics database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from contextlib import contextmanager
import streamlit as st
from sqlalchemy import create_engine, text
from config import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB,
    POSTGRES_USER, POSTGRES_PASSWORD, CACHE_TTL
)

class DatabaseConnection:
    """Manages PostgreSQL database connections"""
    
    def __init__(self):
        self.host = POSTGRES_HOST
        self.port = POSTGRES_PORT
        self.database = POSTGRES_DB
        self.user = POSTGRES_USER
        self.password = POSTGRES_PASSWORD
        
        # Create SQLAlchemy engine for pandas operations
        self.engine = create_engine(
            f"postgresql://{ POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
            pool_pre_ping=True,
            echo=False
        )
    
    @contextmanager
    def get_connection(self):
        """Get a database connection context manager"""
        conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query, params=None):
        """Execute a SELECT query and return results as dict"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params or ())
                return cur.fetchall()
    
    def fetch_dataframe(self, query, params=None):
        """Execute query and return results as pandas DataFrame"""
        try:
            # Use SQLAlchemy engine for pandas operations (recommended)
            if params:
                # If params provided, use parameterized query
                df = pd.read_sql_query(
                    text(query),
                    self.engine,
                    params=params
                )
            else:
                # Direct query without params
                df = pd.read_sql_query(query, self.engine)
            return df
        except Exception as e:
            # Fallback for compatibility
            import logging
            logging.error(f"Error fetching dataframe: {str(e)}")
            return pd.DataFrame()
    
    def test_connection(self):
        """Test database connectivity"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return True, "Connection successful"
        except Exception as e:
            return False, str(e)

@st.cache_resource
def get_db():
    """Get cached database connection instance"""
    return DatabaseConnection()

@st.cache_data(ttl=CACHE_TTL)
def cached_query(query, query_hash=None):
    """Cache query results for performance"""
    db = get_db()
    return db.fetch_dataframe(query)
