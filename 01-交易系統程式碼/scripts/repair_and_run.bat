@echo off
echo ===================================================
echo   REPAIR AND RUN TRADING SYSTEM (DEEP FIX)
echo ===================================================
echo.
cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo [1/3] Fixing core dependencies (pyparsing, packaging, etc)...
python -m pip install --only-binary :all: pyparsing packaging cycler kiwi-solver fonttools pillow python-dateutil six
if errorlevel 1 (
    echo Binary install failed, trying standard install...
    python -m pip install pyparsing packaging cycler kiwi-solver fonttools pillow python-dateutil six
)

echo.
echo [2/3] Verifying main libraries...
python -m pip install --only-binary :all: matplotlib yfinance openai "streamlit>=1.35.0" watchdog

echo.
echo [3/3] Starting Dashboard...
call start_streamlit.bat
