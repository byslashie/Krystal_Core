@echo off
cd /d "C:\Projects\Krystal_完整系統\01-交易系統程式碼"
"C:\Projects\Krystal_完整系統\.venv\Scripts\python.exe" brokers\record_daily_nav.py >> _logs\daily_nav.log 2>&1
