@echo off
:: 每日市值記錄 - 每日 13:40 執行（在元大 13:35 同步完成後）
:: 使用 64-bit Python

set PROJECT_ROOT=h:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼
set PYTHON64=python
set NAV_SCRIPT=%PROJECT_ROOT%\brokers\record_daily_nav.py
set LOG_DIR=%PROJECT_ROOT%\logs

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set dt=%%a
set TIMESTAMP=%dt:~0,8%_%dt:~8,6%
set LOGFILE=%LOG_DIR%\daily_nav_%TIMESTAMP%.log

echo [%date% %time%] 開始記錄每日市值... >> "%LOGFILE%"
echo [%date% %time%] 開始記錄每日市值...

"%PYTHON64%" "%NAV_SCRIPT%" >> "%LOGFILE%" 2>&1
set EXITCODE=%ERRORLEVEL%

if %EXITCODE% == 0 (
    echo [%date% %time%] 完成 >> "%LOGFILE%"
    echo [%date% %time%] 完成
) else (
    echo [%date% %time%] 失敗 RC=%EXITCODE% >> "%LOGFILE%"
    echo [%date% %time%] 失敗 RC=%EXITCODE%
)

exit /b %EXITCODE%
