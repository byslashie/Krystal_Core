@echo off
echo ========================================================
echo    Real Trading System Launcher  
echo    Krystal AI Trading System
echo ========================================================
echo.

echo [1/4] Switching to project folder...
cd /d "%~dp0"
echo Current path: %CD%
echo.

echo [2/4] Activating virtual environment...
if exist ".venv\Scripts\activate.bat" (
    echo Found .venv, activating...
    call ".venv\Scripts\activate.bat"
    echo Virtual environment activated (.venv)
    goto :venv_ok
)
if exist "venv\Scripts\activate.bat" (
    echo Found venv, activating...
    call "venv\Scripts\activate.bat"
    echo Virtual environment activated (venv)
    goto :venv_ok
)
echo ERROR: Virtual environment not found!
echo Please create .venv or venv first
pause
exit /b 1

:venv_ok
echo.

echo [3/4] Checking packages...
echo Upgrading pip and setuptools first...
python -m pip install --upgrade pip setuptools wheel --quiet

python -c "import streamlit; import pandas; import plotly" 2>nul
if errorlevel 1 (
    echo Installing required packages from binary wheels...
    echo This may take a few minutes on first run...
    python -m pip install --only-binary :all: streamlit pandas plotly gspread google-auth google-auth-oauthlib 2>nul
    if errorlevel 1 (
        echo Retrying with standard installation...
        python -m pip install streamlit pandas plotly gspread google-auth google-auth-oauthlib
    )
)
echo Packages ready
echo.

echo [4/4] Starting Streamlit Trading System...
echo --------------------------------------------------------
echo Application will open in your browser
echo Default URL: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo --------------------------------------------------------
echo.

streamlit run app.py --server.port=8501 --server.enableWebsocketCompression=false --server.enableCORS=false --server.enableXsrfProtection=false

echo.
echo ========================================================
echo Application closed
pause
