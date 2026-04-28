@echo off
chcp 65001 > nul
cd /d "C:\Projects\Krystal_完整系統\01-交易系統程式碼"
if not exist "_logs" mkdir "_logs"

echo [%date% %time%] 元大盤中同步開始... >> _logs\yuanta_intraday.log 2>&1
"C:\Users\krystalchen\AppData\Local\Programs\Python\Python311\python.exe" wrapper\krystal_sync.py >> _logs\yuanta_intraday.log 2>&1
echo [%date% %time%] 元大同步 RC=%ERRORLEVEL% >> _logs\yuanta_intraday.log 2>&1

echo [%date% %time%] 更新每日 NAV... >> _logs\yuanta_intraday.log 2>&1
"C:\Users\krystalchen\AppData\Local\Programs\Python\Python311\python.exe" brokers\record_daily_nav.py >> _logs\yuanta_intraday.log 2>&1
echo [%date% %time%] NAV RC=%ERRORLEVEL% >> _logs\yuanta_intraday.log 2>&1

exit /b 0
