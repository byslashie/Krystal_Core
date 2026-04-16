@echo off
REM Flask 交易儀表板啟動腳本 (Windows)
REM 用於 Windows 工作排程器自動執行

cd /d "G:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"

REM 檢查 Python 是否安裝
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安裝或未在 PATH 中
    exit /b 1
)

REM 檢查 Flask 是否已安裝
python -c "import flask" > nul 2>&1
if errorlevel 1 (
    echo ⚠️ Flask 未安裝，嘗試安裝...
    pip install flask
)

REM 啟動 Flask 應用
echo ✅ 正在啟動 Flask 應用...
python app_html_flask.py

REM 保持窗口打開（可選）
pause
