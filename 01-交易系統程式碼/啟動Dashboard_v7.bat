@echo off
chcp 65001 >nul
title Krystal Dashboard v7

echo ================================================
echo   Krystal AI 交易系統 - Dashboard v7 啟動中
echo ================================================
echo.

:: 切換到腳本所在目錄
cd /d "%~dp0"

:: 釋放 port 8889 (後端 API)
echo [1/4] 清理 port 8889...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8889 "') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: 釋放 port 5000 (前端 Dashboard)
echo [2/4] 清理 port 5000...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5000 "') do (
    taskkill /PID %%a /F >nul 2>&1
)

timeout /t 1 /nobreak >nul

:: 啟動後端 API (port 8889)
echo [3/4] 啟動後端 API (port 8889)...
start "API Backend :8889" python app_html_flask.py

:: 等待後端啟動
timeout /t 3 /nobreak >nul

:: 啟動前端 Dashboard (port 5000)
echo [4/4] 啟動前端 Dashboard (port 5000)...
start "Dashboard :5000" python dashboard_v7\app.py

:: 等待前端啟動
timeout /t 2 /nobreak >nul

:: 開啟瀏覽器
echo.
echo ================================================
echo   開啟瀏覽器: http://localhost:5000
echo ================================================
start "" "http://localhost:5000"

echo.
echo 兩個伺服器已在背景運行：
echo   前端 Dashboard  → http://localhost:5000
echo   後端 API        → http://localhost:8889
echo.
echo 關閉此視窗不會停止伺服器。
echo 如需停止，請關閉 "API Backend" 和 "Dashboard" 視窗。
pause
