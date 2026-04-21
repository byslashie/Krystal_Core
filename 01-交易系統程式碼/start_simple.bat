@echo off
REM Simple HTTP server for DashboardV2 - no Flask

cd /d "%~dp0"

taskkill /F /IM python.exe /T >nul 2>&1

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo DashboardV2 HTTP Server
echo ========================================
echo.
echo URL: http://localhost:8888/v2
echo.
echo Press CTRL+C to stop
echo.

python server_v2.py

pause
