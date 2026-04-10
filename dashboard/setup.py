"""
Hospital Inventory Analytics Dashboard - Setup and Installation Guide
=====================================================================

This script provides interactive setup for the dashboard.
Run: python setup.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header(text):
    """Print colored header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")

def create_venv():
    """Create virtual environment"""
    print_header("Creating Virtual Environment")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print_info("Virtual environment already exists")
        return True
    
    try:
        print("Creating venv...")
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        print_success("Virtual environment created successfully")
        return True
    except Exception as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print_header("Installing Dependencies")
    
    # Detect Python executable in venv
    if platform.system() == "Windows":
        python_exe = "venv\\Scripts\\python.exe"
        pip_exe = "venv\\Scripts\\pip.exe"
    else:
        python_exe = "venv/bin/python"
        pip_exe = "venv/bin/pip"
    
    if not Path(pip_exe).exists():
        print_error("pip not found in virtual environment")
        return False
    
    try:
        print("Upgrading pip...")
        subprocess.check_call([pip_exe, "install", "--upgrade", "pip"])
        
        print("Installing requirements...")
        subprocess.check_call([pip_exe, "install", "-r", "requirements.txt"])
        
        print_success("Dependencies installed successfully")
        return True
    except Exception as e:
        print_error(f"Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file from template"""
    print_header("Configuring Environment")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print_info(".env file already exists")
        return True
    
    if not env_example.exists():
        print_error(".env.example file not found")
        return False
    
    try:
        # Copy template
        env_file.write_text(env_example.read_text())
        print_success(".env file created from template")
        
        # Prompt for configuration
        print("\nEnter your PostgreSQL database configuration:")
        
        host = input("PostgreSQL Host [localhost]: ").strip() or "localhost"
        port = input("PostgreSQL Port [5432]: ").strip() or "5432"
        db = input("PostgreSQL Database [analytics]: ").strip() or "analytics"
        user = input("PostgreSQL User [postgres]: ").strip() or "postgres"
        password = input("PostgreSQL Password: ").strip()
        hospital_name = input("Hospital Name [Hospital Inventory Analytics]: ").strip() or "Hospital Inventory Analytics"
        
        # Read current .env content
        env_content = env_file.read_text()
        
        # Replace values
        replacements = {
            "POSTGRES_HOST=localhost": f"POSTGRES_HOST={host}",
            "POSTGRES_PORT=5432": f"POSTGRES_PORT={port}",
            "POSTGRES_DB=analytics": f"POSTGRES_DB={db}",
            "POSTGRES_USER=postgres": f"POSTGRES_USER={user}",
            "POSTGRES_PASSWORD=your_password_here": f"POSTGRES_PASSWORD={password}",
            "HOSPITAL_NAME=Hospital Inventory Analytics": f"HOSPITAL_NAME={hospital_name}",
        }
        
        for old, new in replacements.items():
            env_content = env_content.replace(old, new)
        
        env_file.write_text(env_content)
        print_success(".env file configured successfully")
        return True
    
    except Exception as e:
        print_error(f"Failed to configure environment: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print_header("Testing Database Connection")
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        
        load_dotenv()
        
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "analytics")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "")
        
        print(f"Connecting to {user}@{host}:{port}/{db}...")
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=db,
            user=user,
            password=password,
            connect_timeout=5
        )
        conn.close()
        
        print_success("Database connection successful!")
        return True
    
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        print_info("You can test the connection later when running the dashboard")
        return False

def main():
    """Main setup function"""
    print_header("Hospital Inventory Analytics Dashboard - Setup")
    
    print("""
    This script will help you set up the analytics dashboard.
    
    Steps:
    1. Create Python virtual environment
    2. Install Python dependencies
    3. Configure environment variables
    4. Test database connection
    """)
    
    input("Press Enter to continue...")
    
    # Step 1: Create venv
    if not create_venv():
        print_error("Setup failed at virtual environment creation")
        sys.exit(1)
    
    # Step 2: Install dependencies
    if not install_dependencies():
        print_error("Setup failed at dependency installation")
        sys.exit(1)
    
    # Step 3: Configure environment
    if not create_env_file():
        print_error("Setup failed at environment configuration")
        sys.exit(1)
    
    # Step 4: Test connection
    test_database_connection()
    
    print_header("Setup Complete!")
    
    print("""
    Your dashboard is ready to run!
    
    Next steps:
    
    📊 To start the dashboard:
    
    On Windows:
      run.bat
    
    On Linux/Mac:
      bash run.sh
    
    Or manually:
      source venv/bin/activate  # Linux/Mac
      venv\\Scripts\\activate    # Windows
      streamlit run app.py
    
    The dashboard will be available at:
      http://localhost:8501
    
    📚 For more information, see README.md
    
    ✅ Setup completed successfully!
    """)

if __name__ == "__main__":
    main()
