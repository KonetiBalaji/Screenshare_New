@echo off
echo ========================================
echo    Viewer Test - Screen Share
echo ========================================
echo.

echo Starting web client for viewer testing...
echo.
echo Instructions:
echo 1. Start the web client: python web_client.py
echo 2. Open http://localhost:5000/host in one browser
echo 3. Open http://localhost:5000/test in another browser
echo 4. Start sharing on the host page
echo 5. Copy the session ID and paste it in the test page
echo 6. Click "Join Session" to test viewer functionality
echo.

python web_client.py

echo.
echo Web client stopped. Press any key to exit...
pause >nul
