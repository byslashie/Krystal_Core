@echo off
echo ===================================================
echo   Running with .venv_research64
echo ===================================================
echo.
cd /d "%~dp0"
call .venv_research64\Scripts\activate.bat

echo Using Python:
where python

echo Starting Streamlit...
streamlit run app.py --server.port=8501 --server.enableWebsocketCompression=false --server.enableCORS=false --server.enableXsrfProtection=false
pause
