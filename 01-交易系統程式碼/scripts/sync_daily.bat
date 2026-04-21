@echo off
REM 元大持倉每日自動同步批次文件

cd /d "g:\我的雲端硬碟\Krystal_AI_Trading_System"

REM 生成日期時間戳
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)

REM 執行同步並記錄日誌
python sync_yuanta_to_sheets.py >> logs\sync_%mydate%_%mytime%.txt 2>&1

REM 檢查執行結果
if %errorlevel% equ 0 (
    echo [SUCCESS] 元大持倉同步成功 - %date% %time% >> logs\sync_history.log
) else (
    echo [FAILED] 元大持倉同步失敗 - %date% %time% >> logs\sync_history.log
)

exit /b %errorlevel%
