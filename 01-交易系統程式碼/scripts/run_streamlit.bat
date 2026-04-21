@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONDONTWRITEBYTECODE=1
cd /d "g:\我的雲端硬碟\Krystal_AI_Trading_System"
call .venv\Scripts\activate.bat
streamlit run app.py --server.port=8501 --server.headless=false
pause
