@echo off
REM Discord Bot 排程管理工具

setlocal enabledelayedexpansion
set BOOT_TASK="Krystal_Discord_Bot_Boot"
set WATCH_TASK="Krystal_Discord_Bot_Watchdog"
set BOT_SCRIPT="c:\Projects\Krystal_完整系統\01-交易系統程式碼\discord_bot_autostart.bat"

:menu
cls
echo ========================================
echo   🤖 Discord Bot 排程管理
echo ========================================
echo.
echo [1] ✅ 安裝自動啟動 + 守護排程
echo [2] ⛔ 移除排程
echo [3] 🔄 手動立即啟動 Bot
echo [4] 📋 查看排程狀態
echo [5] 📝 查看最新 log
echo [6] 🛑 停止 Bot 進程
echo [7] ❌ 退出
echo.
set /p choice="請選擇操作 [1-7]: "

if "%choice%"=="1" goto install
if "%choice%"=="2" goto uninstall
if "%choice%"=="3" goto run_now
if "%choice%"=="4" goto view_status
if "%choice%"=="5" goto view_log
if "%choice%"=="6" goto stop_bot
if "%choice%"=="7" goto exit_prog
goto menu

:install
echo.
net session >nul 2>&1
if errorlevel 1 (
    echo ❌ 需要管理員權限！請以管理員身份執行。
    timeout /t 3 /nobreak
    goto menu
)

echo [*] 清除舊排程...
schtasks /delete /tn %BOOT_TASK% /f >nul 2>&1
schtasks /delete /tn %WATCH_TASK% /f >nul 2>&1

echo [*] 建立登入啟動排程（登入後 1 分鐘啟動）...
schtasks /create ^
  /tn %BOOT_TASK% ^
  /tr %BOT_SCRIPT% ^
  /sc onlogon ^
  /delay 0000:01 ^
  /f

if errorlevel 1 (
    echo ❌ 登入排程建立失敗！錯誤碼 %errorlevel%
    timeout /t 3 /nobreak
    goto menu
)
echo ✓ 登入排程建立成功

echo [*] 建立守護排程（每 5 分鐘檢查）...
schtasks /create ^
  /tn %WATCH_TASK% ^
  /tr %BOT_SCRIPT% ^
  /sc minute ^
  /mo 5 ^
  /f

if errorlevel 1 (
    echo ❌ 守護排程建立失敗！錯誤碼 %errorlevel%
    timeout /t 3 /nobreak
    goto menu
)
echo ✓ 守護排程建立成功

echo.
echo ✅ 排程建立成功！
echo   - 開機自動啟動：開機後 1 分鐘啟動 Bot
echo   - 守護機制：每 5 分鐘檢查，若停止會自動重啟
echo.
echo [*] 立即執行一次啟動 Bot...
call %BOT_SCRIPT%
echo.
pause
goto menu

:uninstall
echo.
net session >nul 2>&1
if errorlevel 1 (
    echo ❌ 需要管理員權限！
    timeout /t 3 /nobreak
    goto menu
)
set /p confirm="確定要移除排程嗎？(Y/N): "
if /i not "%confirm%"=="Y" goto menu

schtasks /delete /tn %BOOT_TASK% /f >nul 2>&1
schtasks /delete /tn %WATCH_TASK% /f >nul 2>&1
echo ✅ 排程已移除
timeout /t 2 /nobreak
goto menu

:run_now
echo.
echo [*] 立即啟動 Bot...
call %BOT_SCRIPT%
echo ✅ 啟動指令已送出（背景執行）
timeout /t 3 /nobreak
goto menu

:view_status
echo.
echo ========== 排程狀態 ==========
schtasks /query /tn %BOOT_TASK% /fo list 2>nul | findstr /i "TaskName Status Next"
echo.
schtasks /query /tn %WATCH_TASK% /fo list 2>nul | findstr /i "TaskName Status Next"
echo.
echo ========== Bot 進程 ==========
wmic process where "name='python.exe' or name='pythonw.exe'" get processid,commandline 2>nul | findstr /i "discord_bot"
if errorlevel 1 echo ❌ Bot 目前沒在運行
echo.
pause
goto menu

:view_log
echo.
if exist "c:\Projects\Krystal_完整系統\01-交易系統程式碼\logs\discord_bot.log" (
    echo ========== 最新 20 行 log ==========
    powershell -Command "Get-Content 'c:\Projects\Krystal_完整系統\01-交易系統程式碼\logs\discord_bot.log' -Tail 20"
) else (
    echo [!] log 檔案不存在
)
echo.
pause
goto menu

:stop_bot
echo.
echo [*] 停止 Discord Bot...
for /f "tokens=2 delims==" %%i in ('wmic process where "(name='python.exe' or name='pythonw.exe') and commandline like '%%discord_bot.py%%'" get processid /value 2^>nul ^| findstr "="') do (
    echo 停止 PID %%i
    taskkill /pid %%i /f >nul 2>&1
)
echo ✅ 已停止
timeout /t 2 /nobreak
goto menu

:exit_prog
exit /b 0
