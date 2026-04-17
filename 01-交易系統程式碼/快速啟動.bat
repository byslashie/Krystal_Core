@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m http.server 5000
