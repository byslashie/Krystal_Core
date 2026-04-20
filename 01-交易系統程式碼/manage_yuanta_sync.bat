@echo off
REM 元大 ↔ Google Sheets 同步管理工具

setlocal enabledelayedexpansion
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

:menu
cls
echo ========================================
echo   📊 元大庫存同步管理工具
echo ========================================
echo.
echo [1] 🔄 同步元大 → Google Sheets（完整）
echo [2] ⚡ 快速同步（無提示）
echo [3] 📋 檢查最後同步結果
echo [4] 🌐 打開 Google Sheets
echo [5] 📁 打開 snapshot 資料夾
echo [6] ❌ 退出
echo.
set /p choice="請選擇操作 [1-6]: "

if "%choice%"=="1" goto sync_full
if "%choice%"=="2" goto sync_quick
if "%choice%"=="3" goto check_result
if "%choice%"=="4" goto open_sheets
if "%choice%"=="5" goto open_data
if "%choice%"=="6" goto exit_prog
goto menu

:sync_full
echo.
echo [*] 啟動完整同步流程...
echo.
.venv_yuanta32\Scripts\python.exe brokers\sync_yuanta_positions.py
if errorlevel 1 (
    echo.
    echo ❌ 同步失敗，請檢查元大 API 連線
) else (
    echo.
    echo ✅ 同步成功！
)
timeout /t 3 /nobreak
goto menu

:sync_quick
echo.
echo [*] 快速同步中...
.venv_yuanta32\Scripts\python.exe brokers\sync_yuanta_positions.py >nul 2>&1
if errorlevel 1 (
    echo ❌ 快速同步失敗
) else (
    echo ✅ 快速同步完成！
)
timeout /t 2 /nobreak
goto menu

:check_result
if exist "data\yuanta_positions_snapshot.json" (
    echo.
    echo 📋 最後同步結果 (snapshot):
    echo ────────────────────────────
    for /f %%A in ('powershell -Command "Get-Item -Path 'data\yuanta_positions_snapshot.json' | Select-Object -ExpandProperty LastWriteTime"') do echo 最後更新: %%A
    echo.
    powershell -Command "Get-Content 'data\yuanta_positions_snapshot.json' | ConvertFrom-Json | Select-Object timestamp, totalMarketValue, totalUnrealizedPnL | Format-Table -AutoSize"
) else (
    echo [!] 尚未找到 snapshot 資料，請先執行同步
)
echo.
pause
goto menu

:open_sheets
echo.
echo [*] 打開 Google Sheets...
REM 需要填入你的 Google Sheets ID
REM 範例：https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
start https://docs.google.com/spreadsheets/d/1zpehl1bAZitFiQqMg7IcGWsPQxdhnQDhAeNtRvxzwn8/edit#gid=0
echo ✅ Google Sheets 已開啟
timeout /t 2 /nobreak
goto menu

:open_data
explorer.exe "data\"
timeout /t 1 /nobreak
goto menu

:exit_prog
exit /b 0
