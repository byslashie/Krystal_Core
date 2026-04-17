@echo off
echo ===================================================
echo   FIXING SSL CONNECTION ISSUES
echo   Downgrading urllib3 to <2.0 to ensure stability
echo ===================================================
echo.
cd /d "%~dp0"
call .venv_research64\Scripts\activate.bat

echo Uninstalling current urllib3...
python -m pip uninstall -y urllib3

echo Installing urllib3 1.26.18 (Stable)...
python -m pip install "urllib3<2.0"

echo Verifying versions...
python -m pip list | findstr "urllib3 requests"

echo.
echo Done. You can now restart the system.
pause
