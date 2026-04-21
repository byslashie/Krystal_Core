@echo off
chcp 65001 >nul
cd /d "G:\我的雲端硬碟\Krystal_AI_Trading_System"

REM 啟動虛擬環境
call .venv\Scripts\activate.bat

REM 執行啟動腳本（自動選擇可用端口）
python run_flask.py

pause
