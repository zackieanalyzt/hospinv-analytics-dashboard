#!/bin/bash
# Hospital Inventory Analytics Dashboard - Linux/Mac Startup Script

set -e

# Change to dashboard directory
cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "Please edit .env with your database credentials"
    read -p "Press Enter to continue..."
fi

# Run Streamlit app
echo "Starting Hospital Inventory Analytics Dashboard..."
echo "Dashboard will open at: http://localhost:8501"

# Try to open browser if available
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8501
elif command -v open &> /dev/null; then
    open http://localhost:8501
fi

streamlit run app.py
