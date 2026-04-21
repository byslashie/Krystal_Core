@echo off
REM 一鍵同步元大庫存到 Google Sheets
REM 使用 32-bit Python 環境 + 元大 API

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo ========================================
echo   📊 元大庫存同步工具
echo ========================================
echo.

REM 絕對路徑
set PYTHON_EXE="%SCRIPT_DIR%.venv_yuanta32\Scripts\python.exe"
set SYNC_SCRIPT="%SCRIPT_DIR%brokers\sync_yuanta_positions.py"

REM 檢查 32-bit Python 環境
if not exist %PYTHON_EXE% (
    echo ❌ 錯誤：找不到 32-bit Python 環境
    echo 期望位置：%PYTHON_EXE%
    echo.
    echo 解決方案：
    echo 1. 確保 .venv_yuanta32 資料夾存在
    echo 2. 執行：%PYTHON_EXE% -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [1] 檢查環境... ✓
echo [2] 登入元大 API...
echo.

REM 執行同步腳本
%PYTHON_EXE% %SYNC_SCRIPT%

if errorlevel 1 (
    echo.
    echo ❌ 同步失敗，請查看上方錯誤信息
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ 同步完成！
echo ========================================
echo.
echo 📌 檢查結果：
echo   - Google Sheets 已更新：broker_positions 分頁
echo   - snapshot 已保存：data/yuanta_positions_snapshot.json
echo.
pause
