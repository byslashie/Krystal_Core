@echo off
:: 元大庫存同步 - 每日 09:15 執行
:: 使用 32-bit Python venv (.venv_yuanta32_new)

set PROJECT_ROOT=h:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼
set PYTHON32=%PROJECT_ROOT%\.venv_yuanta32_new\Scripts\python.exe
set PYTHON64=python
set SYNC_SCRIPT=%PROJECT_ROOT%\brokers\sync_yuanta_positions.py
set UPLOAD_SCRIPT=%PROJECT_ROOT%\brokers\upload_yuanta_to_sheets.py
set LOG_DIR=%PROJECT_ROOT%\logs

:: 建立 logs 目錄
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:: 產生時間戳
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set dt=%%a
set TIMESTAMP=%dt:~0,8%_%dt:~8,6%
set LOGFILE=%LOG_DIR%\yuanta_sync_%TIMESTAMP%.log

echo [%date% %time%] 開始元大庫存同步... >> "%LOGFILE%"
echo [%date% %time%] 開始元大庫存同步...

:: Step 1: 32-bit Python 抓庫存 → 存 JSON snapshot
echo [%date% %time%] [Step1] 32-bit 抓庫存... >> "%LOGFILE%"

if not exist "%PYTHON32%" (
    echo [%date% %time%] [Step1] 32-bit Python 不存在，跳過直接用現有 snapshot >> "%LOGFILE%"
    goto :step2
)

if not exist "%SYNC_SCRIPT%" (
    echo [%date% %time%] [Step1] sync_yuanta_positions.py 不存在，跳過直接用現有 snapshot >> "%LOGFILE%"
    goto :step2
)

"%PYTHON32%" "%SYNC_SCRIPT%" >> "%LOGFILE%" 2>&1
set EXITCODE=%ERRORLEVEL%

if %EXITCODE% NEQ 0 (
    echo [%date% %time%] [Step1] 失敗 RC=%EXITCODE%，改用現有 snapshot 繼續 >> "%LOGFILE%"
) else (
    echo [%date% %time%] [Step1] 完成 >> "%LOGFILE%"
)

:step2

:: Step 2: 64-bit Python 上傳 snapshot → Google Sheets
echo [%date% %time%] [Step2] 上傳至 Google Sheets... >> "%LOGFILE%"
"%PYTHON64%" "%UPLOAD_SCRIPT%" >> "%LOGFILE%" 2>&1
set EXITCODE2=%ERRORLEVEL%

if %EXITCODE2% == 0 (
    echo [%date% %time%] 全部完成 (RC=0) >> "%LOGFILE%"
    echo [%date% %time%] 同步完成
) else (
    echo [%date% %time%] [Step2] 上傳失敗 RC=%EXITCODE2%（庫存 JSON 已存） >> "%LOGFILE%"
    echo [%date% %time%] 庫存已存 JSON，上傳失敗 RC=%EXITCODE2%
)

exit /b %EXITCODE2%
