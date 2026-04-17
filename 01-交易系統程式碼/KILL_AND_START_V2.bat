@echo off
REM Kill all Python processes and start DashboardV2 cleanly

echo.
echo ========================================
echo Krystal DashboardV2 - Clean Restart
echo ========================================
echo.

REM Kill all Python processes
echo [1/3] Killing all Python processes...
taskkill /F /IM python.exe /T >nul 2>&1
echo.      Done
echo.

REM Wait a moment for cleanup
timeout /t 2 /nobreak >nul

REM Change to the correct directory
cd /d "%~dp0"

REM Start the new Flask app
echo [2/3] Starting Flask server...
echo [3/3] Opening browser to http://localhost:8888/v2
echo.

python app_dashboard_v2.py

pause
