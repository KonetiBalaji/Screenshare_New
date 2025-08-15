@echo off
echo ========================================
echo    Global Screen Share Server
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://python.org
    pause
    exit /b 1
)

echo Checking dependencies...
python -c "import flask, cv2, numpy" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Starting Global Screen Share Server...
echo.
echo If you see "OpenSSL not found" warning, the server will start without SSL
echo This is fine for local testing but not recommended for production
echo.
echo To install OpenSSL on Windows:
echo 1. Download from: https://slproweb.com/products/Win32OpenSSL.html
echo 2. Install and add to PATH
echo 3. Restart this script
echo.

python global_server.py

echo.
echo Server stopped. Press any key to exit...
pause >nul

