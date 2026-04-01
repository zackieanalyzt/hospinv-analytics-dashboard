import pandas as pd

def require_columns(df: pd.DataFrame, required_cols: list[str], job_name: str):
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"{job_name}: missing required columns: {missing}")

def require_not_null(df: pd.DataFrame, col: str, job_name: str):
    if df[col].isnull().any():
        raise ValueError(f"{job_name}: null values found in required column: {col}")
