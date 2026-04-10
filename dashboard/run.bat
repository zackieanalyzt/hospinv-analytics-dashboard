@echo off
REM Hospital Inventory Analytics Dashboard - Windows Startup Script

setlocal enabledelayedexpansion

REM Change to dashboard directory
cd /d "%~dp0"

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo Creating .env from template...
    copy .env.example .env
    echo Please edit .env with your database credentials
    pause
)

REM Run Streamlit app
echo Starting Hospital Inventory Analytics Dashboard...
echo Dashboard will open at: http://localhost:8501
start http://localhost:8501

streamlit run app.py

pause
