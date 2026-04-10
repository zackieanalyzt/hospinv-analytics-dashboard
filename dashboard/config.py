"""
Configuration for Hospital Inventory Analytics Dashboard
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "analytics")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

# Streamlit Configuration
PAGE_ICON = "🏥"
LAYOUT = "wide"
THEME = "light"

# Chart Configuration
CHART_HEIGHT = 400
DEFAULT_DATE_RANGE_DAYS = 30

# Dashboard Refresh Configuration
CACHE_TTL = 300  # 5 minutes

# Company/Hospital Name
HOSPITAL_NAME = os.getenv("HOSPITAL_NAME", "Hospital Inventory Analytics")

# Report Settings
REPORT_CURRENCY = "฿"  # Thai Baht
DATE_FORMAT = "%d/%m/%Y"
DATETIME_FORMAT = "%d/%m/%Y %H:%M"
