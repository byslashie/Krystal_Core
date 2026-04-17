@echo off
chcp 65001 >nul
title Krystal AI 交易系統
setlocal enabledelayedexpansion

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   Krystal AI 交易系統  啟動中...    ║
echo  ╚══════════════════════════════════════╝
echo.

:: 切換到腳本所在目錄
cd /d "%~dp0"

:: ── 0. 環境檢查 ──────────────────────────────────────────────
echo [0/4] 檢查 Python 環境與依賴套件...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤: 找不到 Python！請確保已安裝 Python 並加入 PATH。
    pause
    exit /b 1
)

:: 檢查並安裝必要套件
for %%p in (flask flask-cors pandas numpy python-dotenv gspread google-auth yfinance) do (
    python -c "import %%p" >nul 2>&1
    if errorlevel 1 (
        echo ⚠️ 正在安裝缺失套件: %%p ...
        python -m pip install %%p
    )
)

:: ── 1. 關閉舊進程 ──────────────────────────────────────────
echo [1/4] 清除舊進程 (Port 8889, 5000)...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8889 " ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5000 " ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

:: ── 2. 啟動後端 API（port 8889）─────────────────────────────
echo [2/4] 啟動後端 API (port 8889)...
set "BACKEND_DIR=%~dp0"
powershell -NoProfile -Command "Start-Process python -ArgumentList 'app_html_flask.py' -WorkingDirectory '%BACKEND_DIR%' -WindowStyle Normal"
timeout /t 5 /nobreak >nul

:: ── 3. 啟動前端伺服器（port 5000）───────────────────────────
echo [3/4] 啟動前端伺服器 (port 5000)...
set "FRONTEND_DIR=%~dp0dashboard_v7"
powershell -NoProfile -Command "Start-Process python -ArgumentList 'app.py' -WorkingDirectory '%FRONTEND_DIR%' -WindowStyle Normal"
timeout /t 3 /nobreak >nul

:: ── 4. 開啟瀏覽器 ───────────────────────────────────────────
echo [4/4] 開啟瀏覽器...
start http://localhost:5000

echo.
echo  ✅ 啟動完成！
echo.
echo  前端：http://localhost:5000
echo  後端：http://localhost:8889
echo.
echo  💡 提示：如果網頁沒有自動顯示資料，請檢查後端視窗是否有紅字報錯。
echo.
pause
