"""
Utility functions for formatting and common operations
"""
import pandas as pd
from datetime import datetime, timedelta
from config import DATE_FORMAT, DATETIME_FORMAT, REPORT_CURRENCY
import streamlit as st

def format_currency(value):
    """Format number as currency"""
    if pd.isna(value):
        return f"{REPORT_CURRENCY}0.00"
    try:
        return f"{REPORT_CURRENCY}{float(value):,.2f}"
    except:
        return f"{REPORT_CURRENCY}0.00"

def format_number(value, decimals=0):
    """Format number with thousand separators"""
    if pd.isna(value):
        return "0"
    try:
        if decimals == 0:
            return f"{int(value):,}"
        else:
            return f"{float(value):,.{decimals}f}"
    except:
        return str(value)

def format_date(date_obj):
    """Format date object to string"""
    if pd.isna(date_obj):
        return "N/A"
    try:
        if isinstance(date_obj, str):
            return date_obj
        return date_obj.strftime(DATE_FORMAT)
    except:
        return str(date_obj)

def format_datetime(dt_obj):
    """Format datetime object to string"""
    if pd.isna(dt_obj):
        return "N/A"
    try:
        if isinstance(dt_obj, str):
            return dt_obj
        return dt_obj.strftime(DATETIME_FORMAT)
    except:
        return str(dt_obj)

def get_status_color(status):
    """Get color for status badge"""
    status_lower = str(status).lower()
    
    if 'critical' in status_lower or 'expired' in status_lower:
        return 'red'
    elif 'warning' in status_lower or 'pending' in status_lower:
        return 'orange'
    elif 'success' in status_lower or 'approved' in status_lower or 'received' in status_lower:
        return 'green'
    elif 'open' in status_lower or 'active' in status_lower:
        return 'blue'
    else:
        return 'gray'

def days_until(target_date):
    """Calculate days until a target date"""
    if pd.isna(target_date):
        return None
    try:
        target = pd.to_datetime(target_date).date()
        today = pd.Timestamp.now().date()
        return (target - today).days
    except:
        return None

def get_date_range_days(days):
    """Get date range tuple (start_date, end_date) for last N days"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date

def safe_divide(numerator, denominator, default=0):
    """Safe division that handles zero division"""
    try:
        if denominator == 0 or pd.isna(denominator):
            return default
        return numerator / denominator
    except:
        return default

def format_dataframe_display(df):
    """Format dataframe columns for display"""
    df_display = df.copy()
    
    # Format numeric columns
    for col in df_display.columns:
        if df_display[col].dtype in ['float64', 'float32']:
            if 'price' in col.lower() or 'cost' in col.lower() or 'amount' in col.lower() or 'value' in col.lower():
                df_display[col] = df_display[col].apply(format_currency)
            else:
                df_display[col] = df_display[col].apply(lambda x: format_number(x, decimals=2) if not pd.isna(x) else 'N/A')
        elif col.lower().endswith('date') or col.lower().endswith('_at'):
            df_display[col] = df_display[col].apply(format_datetime)
    
    return df_display

def create_metric_card(label, value, subtext="", delta=None, color="blue"):
    """Create a metric card for display"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.metric(label=label, value=value, delta=delta)
    with col2:
        if subtext:
            st.caption(subtext)
    return True

def get_trend(current, previous):
    """Calculate trend indicator"""
    if previous == 0 or pd.isna(previous):
        return None
    try:
        pct_change = ((current - previous) / abs(previous)) * 100
        if pct_change > 0:
            return f"↑ {pct_change:+.1f}%"
        elif pct_change < 0:
            return f"↓ {pct_change:+.1f}%"
        else:
            return "→ 0%"
    except:
        return None
