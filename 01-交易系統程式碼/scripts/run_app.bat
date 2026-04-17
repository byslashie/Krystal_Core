@echo off
echo [1/3] 切換到專案資料夾...
cd /d D:\2025_Krystal_AI_Tool\2025_06_23_Krystal_AI_Trading_System\Krystal_AI_Trading_System

echo [2/3] 啟動虛擬環境...
call .venv_research64\Scripts\activate.bat

echo [3/3] 啟動 Streamlit 應用程式...
streamlit run app.py --server.port=8502

pause
