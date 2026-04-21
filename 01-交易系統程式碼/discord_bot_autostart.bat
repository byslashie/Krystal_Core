@echo off
REM Krystal Discord Bot 自動啟動 + 守護腳本
REM 用途：
REM   1. 開機後由 Task Scheduler 呼叫一次（開機自動啟動）
REM   2. 每 5 分鐘由 Task Scheduler 呼叫一次（守護：沒跑就啟動）

setlocal enabledelayedexpansion
set PROJECT_ROOT=c:\Projects\Krystal_完整系統\01-交易系統程式碼
set LOGFILE=%PROJECT_ROOT%\logs\discord_bot.log
set PIDFILE=%PROJECT_ROOT%\logs\discord_bot.pid

if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs"

REM ── 檢查是否已在運行（用 wmic 找 python 進程命令行含 discord_bot.py）──
for /f "tokens=2 delims==" %%i in ('wmic process where "name='python.exe' and commandline like '%%discord_bot.py%%'" get processid /value 2^>nul ^| findstr "="') do (
    echo [%date% %time%] Discord Bot 已在運行 (PID %%i)，跳過 >> "%LOGFILE%"
    exit /b 0
)

REM ── 沒在跑：啟動 ──
echo [%date% %time%] Discord Bot 未運行，正在啟動... >> "%LOGFILE%"
cd /d "%PROJECT_ROOT%"

REM 使用 pythonw.exe（無視窗），背景啟動
start "" /B pythonw.exe "%PROJECT_ROOT%\discord_bot.py" >> "%LOGFILE%" 2>&1

echo [%date% %time%] Discord Bot 已啟動 >> "%LOGFILE%"
exit /b 0
