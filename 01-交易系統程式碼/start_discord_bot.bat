@echo off
:: Krystal Discord Bot 啟動腳本
set PROJECT_ROOT=h:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼
set LOGFILE=%PROJECT_ROOT%\logs\discord_bot.log

if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs"

:: 等待 30 秒讓網路就緒
echo [%date% %time%] 等待網路就緒 (30s)... >> "%LOGFILE%"
timeout /t 30 /nobreak > nul

echo [%date% %time%] Discord Bot 啟動中... >> "%LOGFILE%"
cd /d "%PROJECT_ROOT%"
python "%PROJECT_ROOT%\discord_bot.py" >> "%LOGFILE%" 2>&1
echo [%date% %time%] Discord Bot 已結束 >> "%LOGFILE%"
