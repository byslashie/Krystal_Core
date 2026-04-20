@echo off
REM 設定元大庫存定時同步排程（Windows 工作排程器）

setlocal enabledelayedexpansion
set SCRIPT_DIR=%~dp0
set PYTHON_EXE="%SCRIPT_DIR%.venv_yuanta32\Scripts\python.exe"
set SYNC_SCRIPT="%SCRIPT_DIR%brokers\sync_yuanta_positions.py"
set TASK_NAME="元大庫存自動同步"

echo ========================================
echo   📊 設定元大庫存定時同步排程
echo ========================================
echo.

REM 檢查管理員權限
net session >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤：需要管理員權限！
    echo.
    echo 請以管理員身份執行此批次檔：
    echo 1. 右鍵點擊 schedule_yuanta_sync.bat
    echo 2. 選擇「以管理員身份執行」
    echo.
    pause
    exit /b 1
)

echo ✓ 管理員權限已確認
echo.

REM 建立排程工作
echo [*] 正在建立每日 09:00 同步任務...
echo.

REM 刪除舊的任務（如果存在）
schtasks /delete /tn %TASK_NAME% /f >nul 2>&1

REM 建立新的每日排程（台灣時間 09:00）
schtasks /create ^
  /tn %TASK_NAME% ^
  /tr "%PYTHON_EXE% %SYNC_SCRIPT%" ^
  /sc daily ^
  /st 09:00 ^
  /ru "%USERNAME%" ^
  /f

if errorlevel 1 (
    echo ❌ 建立排程失敗！
    pause
    exit /b 1
)

echo ✅ 排程已建立！
echo.
echo 📋 排程詳情：
echo   - 工作名稱：%TASK_NAME%
echo   - 觸發時間：每天 09:00
echo   - 執行內容：同步元大庫存到 Google Sheets
echo.

REM 顯示現有排程
echo [*] 檢查排程狀態...
schtasks /query /tn %TASK_NAME% /v /fo list

echo.
echo ========================================
echo   ✅ 排程設定完成！
echo ========================================
echo.
echo 管理選項：
echo   - 編輯：schtasks /change /tn "%TASK_NAME%" /st 09:00
echo   - 刪除：schtasks /delete /tn "%TASK_NAME%" /f
echo   - 手動執行：schtasks /run /tn "%TASK_NAME%"
echo.
pause
