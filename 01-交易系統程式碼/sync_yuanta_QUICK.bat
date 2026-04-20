@echo off
cd /d "%~dp0"
"%~dp0.venv_yuanta32\Scripts\python.exe" "%~dp0brokers\sync_yuanta_positions.py"
pause
