@echo off
REM 元大同步排程管理工具

setlocal enabledelayedexpansion
set TASK_NAME="元大庫存自動同步"

:menu
cls
echo ========================================
echo   📅 元大同步排程管理
echo ========================================
echo.
echo [1] ✅ 啟用排程（每天 09:00）
echo [2] ⛔ 停用排程
echo [3] 🔄 手動立即同步
echo [4] 📋 查看排程狀態
echo [5] 🕐 修改同步時間
echo [6] 🗑️  刪除排程
echo [7] ❌ 退出
echo.
set /p choice="請選擇操作 [1-7]: "

if "%choice%"=="1" goto enable
if "%choice%"=="2" goto disable
if "%choice%"=="3" goto run_now
if "%choice%"=="4" goto view_status
if "%choice%"=="5" goto change_time
if "%choice%"=="6" goto delete_task
if "%choice%"=="7" goto exit_prog
goto menu

:enable
echo.
echo [*] 啟用排程...
net session >nul 2>&1
if errorlevel 1 (
    echo ❌ 需要管理員權限！
    echo 請以管理員身份執行此批次檔
    timeout /t 3 /nobreak
    goto menu
)
schtasks /change /tn %TASK_NAME% /enable >nul 2>&1
if errorlevel 1 (
    echo [!] 排程不存在，請先執行 schedule_yuanta_sync.bat 建立
) else (
    echo ✅ 排程已啟用！
)
timeout /t 2 /nobreak
goto menu

:disable
echo.
echo [*] 停用排程...
schtasks /change /tn %TASK_NAME% /disable >nul 2>&1
if errorlevel 1 (
    echo [!] 排程不存在
) else (
    echo ✅ 排程已停用！
)
timeout /t 2 /nobreak
goto menu

:run_now
echo.
echo [*] 立即執行同步...
cd /d "%~dp0"
".venv_yuanta32\Scripts\python.exe" "brokers\sync_yuanta_positions.py"
echo.
pause
goto menu

:view_status
echo.
echo [*] 查看排程狀態...
echo.
schtasks /query /tn %TASK_NAME% /v /fo list 2>nul
if errorlevel 1 (
    echo [!] 排程不存在（尚未建立）
)
echo.
pause
goto menu

:change_time
echo.
set /p new_time="輸入新的同步時間 (格式 HH:MM，例如 09:00): "
net session >nul 2>&1
if errorlevel 1 (
    echo ❌ 需要管理員權限！
    timeout /t 3 /nobreak
    goto menu
)
schtasks /change /tn %TASK_NAME% /st %new_time% >nul 2>&1
if errorlevel 1 (
    echo ❌ 修改失敗！
) else (
    echo ✅ 已修改為 %new_time%
)
timeout /t 2 /nobreak
goto menu

:delete_task
echo.
set /p confirm="確定要刪除排程嗎？(Y/N): "
if /i "%confirm%"=="Y" (
    net session >nul 2>&1
    if errorlevel 1 (
        echo ❌ 需要管理員權限！
        timeout /t 3 /nobreak
        goto menu
    )
    schtasks /delete /tn %TASK_NAME% /f >nul 2>&1
    echo ✅ 排程已刪除！
) else (
    echo [取消] 未刪除排程
)
timeout /t 2 /nobreak
goto menu

:exit_prog
exit /b 0
