@echo off
chcp 65001 > nul
title 元大庫存同步 → Google Sheets

set PROJECT_ROOT=h:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼
set PYTHON64=C:\Users\jrenw\AppData\Local\Programs\Python\Python311\python.exe
set UPLOAD_SCRIPT=%PROJECT_ROOT%\brokers\upload_yuanta_to_sheets.py
set LOG_DIR=%PROJECT_ROOT%\logs

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set dt=%%a
set LOGFILE=%LOG_DIR%\yuanta_upload_%dt:~0,8%_%dt:~8,4%.log

echo.
echo ========================================
echo  元大庫存同步 - %date% %time%
echo ========================================
echo.

cd /d "%PROJECT_ROOT%"
"%PYTHON64%" "%UPLOAD_SCRIPT%" 2>&1 | tee "%LOGFILE%"

if %ERRORLEVEL% == 0 (
    echo.
    echo [OK] 同步完成
) else (
    echo.
    echo [FAIL] 同步失敗，請查看 log：%LOGFILE%
)

echo.
timeout /t 3 > nul
