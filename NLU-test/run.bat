@echo off
REM Script to run both NLU API server and test web page (Windows)

echo 🚀 Starting Valio Aimo NLU Test Environment
echo ==========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python first.
    pause
    exit /b 1
)

REM Check if Flask is installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Flask is not installed. Installing dependencies...
    cd ..\NLU
    pip install -r requirements.txt
    cd ..\NLU-test
)

echo 📦 Starting NLU API server...
echo    API will be available at: http://localhost:5000
echo.

REM Start the Flask server
cd ..\NLU
start "NLU API Server" python app.py

REM Wait a moment for server to start
timeout /t 3 /nobreak >nul

echo ✅ NLU API server started
echo.
echo 🌐 Opening test web page...
echo.

REM Open the HTML file in the default browser
start index.html

echo.
echo ✨ Test environment is ready!
echo.
echo To stop the server, close the "NLU API Server" window
echo.
pause

