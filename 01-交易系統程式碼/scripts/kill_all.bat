@echo off
echo Killing all python processes...
taskkill /F /IM python.exe /T
echo Killing all streamlit processes...
taskkill /F /IM streamlit.exe /T
echo.
echo Done. You can now run run_trading_system.bat again.
pause
