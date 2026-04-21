@echo off
cd /d "%~dp0"

echo Activating virtual environment...
call .venv_research64\Scripts\activate.bat

echo Starting Streamlit...
python -m streamlit run app.py --server.port=8502 --server.enableWebsocketCompression=false --server.enableCORS=false --server.enableXsrfProtection=false

pause
