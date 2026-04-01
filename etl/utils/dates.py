from datetime import datetime, timedelta

def today_date():
    return datetime.now().date()

def days_ago(days: int):
    return (datetime.now() - timedelta(days=days)).date()

def timestamp_now():
    return datetime.now()
