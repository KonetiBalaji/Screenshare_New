@echo off
echo ========================================
echo    Global Screen Share - Viewer Mode
echo ========================================
echo.

set /p SERVER="Enter server IP/hostname (default: localhost): "
if "%SERVER%"=="" set SERVER=localhost

set /p USERNAME="Enter username (default: admin): "
if "%USERNAME%"=="" set USERNAME=admin

set /p PASSWORD="Enter password (default: admin123): "
if "%PASSWORD%"=="" set PASSWORD=admin123

set /p SESSION="Enter session ID: "
if "%SESSION%"=="" (
    echo ERROR: Session ID is required for viewer mode
    pause
    exit /b 1
)

echo.
echo Joining session: %SESSION%
echo Server: %SERVER%
echo Username: %USERNAME%
echo.
echo Press 'q' in the viewer window to exit
echo.

python global_client.py --server %SERVER% --port 8443 --username %USERNAME% --password %PASSWORD% --mode viewer --session %SESSION% --no-ssl

echo.
echo Viewer stopped. Press any key to exit...
pause >nul
