@echo off
REM Run script for NLU Parser API (Windows)
REM Activates virtual environment and starts the Flask server

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements are installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Dependencies not installed. Installing now...
    pip install -r requirements.txt
)

REM Start the server
echo.
echo 🚀 Starting NLU Parser API server...
echo    Server will be available at: http://localhost:5000
echo    Health check: http://localhost:5000/health
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

