@echo off
cd /d "C:\Projects\Krystal_完整系統\01-交易系統程式碼"
if not exist "_logs" mkdir "_logs"

echo [%date% %time%] Step 1: 元大庫存同步... >> _logs\daily_nav.log 2>&1
".venv_yuanta32\Scripts\python.exe" brokers\sync_yuanta_positions.py >> _logs\daily_nav.log 2>&1

echo [%date% %time%] Step 2: IB 持倉同步（需 TWS 運行）... >> _logs\daily_nav.log 2>&1
"C:\Projects\Krystal_完整系統\.venv\Scripts\python.exe" sync_ib_to_sheets.py >> _logs\daily_nav.log 2>&1

echo [%date% %time%] Step 3: Schwab 持倉同步（需有效 token）... >> _logs\daily_nav.log 2>&1
"C:\Projects\Krystal_完整系統\.venv\Scripts\python.exe" sync_schwab_to_sheets.py >> _logs\daily_nav.log 2>&1

echo [%date% %time%] Step 4: 記錄每日 NAV... >> _logs\daily_nav.log 2>&1
"C:\Projects\Krystal_完整系統\.venv\Scripts\python.exe" brokers\record_daily_nav.py >> _logs\daily_nav.log 2>&1
