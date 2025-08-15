@echo off
echo ========================================
echo    Web Screen Share - HTTPS Mode
echo ========================================
echo.

echo Starting web client with HTTPS support...
echo This will generate self-signed certificates for testing.
echo.

python web_client.py --https

echo.
echo Web client stopped. Press any key to exit...
pause >nul
