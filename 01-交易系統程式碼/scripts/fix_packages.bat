@echo off
echo ========================================================
echo    Quick Fix - Installing Required Packages
echo    Krystal AI Trading System
echo ========================================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else (
    echo ERROR: Virtual environment not found!
    pause
    exit /b 1
)

echo.
echo Step 1: Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel

echo.
echo Step 2: Installing packages (using pre-built binaries)...
python -m pip install --only-binary :all: streamlit pandas numpy plotly 2>nul

if errorlevel 1 (
    echo Binary installation failed, trying standard installation...
    python -m pip install streamlit pandas numpy plotly
)

echo.
echo Step 3: Installing Google Sheets packages...
python -m pip install gspread google-auth google-auth-oauthlib

echo.
echo Step 4: Verifying installation...
python -c "import streamlit; import pandas; import plotly; import gspread; print('All packages installed successfully!')"

echo.
echo ========================================================
echo Installation complete!
echo You can now run run_trading_system.bat
echo ========================================================
pause
