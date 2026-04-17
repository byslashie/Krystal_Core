@echo off
set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"

if not exist "%PYTHON_EXE%" (
    echo Python not found at expected location!
    pause
    exit /b 1
)

echo Found Python at %PYTHON_EXE%

if exist ".venv_research64" (
    echo Backing up old venv...
    if exist "_OLD_.venv_research64_backup" rmdir /s /q "_OLD_.venv_research64_backup"
    rename ".venv_research64" "_OLD_.venv_research64_backup"
)

echo Creating new virtual environment...
"%PYTHON_EXE%" -m venv .venv_research64

echo Activating environment...
call .venv_research64\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo Requirements file not found! Using standard list...
    pip install streamlit pandas numpy matplotlib openai scikit-learn pyyaml seaborn yfinance xlsxwriter gspread plotly oauth2client watchdog
)

echo.
echo Setup complete. Starting Streamlit app...
streamlit run app.py
