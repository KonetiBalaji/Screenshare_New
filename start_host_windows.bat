@echo off
echo ========================================
echo    Global Screen Share - Host Mode
echo ========================================
echo.

set /p SERVER="Enter server IP/hostname (default: localhost): "
if "%SERVER%"=="" set SERVER=localhost

set /p USERNAME="Enter username (default: admin): "
if "%USERNAME%"=="" set USERNAME=admin

set /p PASSWORD="Enter password (default: admin123): "
if "%PASSWORD%"=="" set PASSWORD=admin123

echo.
echo Starting as host on server: %SERVER%
echo Username: %USERNAME%
echo.
echo Press Ctrl+C to stop sharing
echo.

python global_client.py --server %SERVER% --port 8443 --username %USERNAME% --password %PASSWORD% --mode host --no-ssl

echo.
echo Host stopped. Press any key to exit...
pause >nul
