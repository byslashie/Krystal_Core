@echo off
echo =========================================
echo   開始自動初始化量化交易開發環境 (Windows)...
echo =========================================
echo.
echo [1/3] 正在建立 Python 虛擬環境 (.venv)...
python -m venv .venv
echo [2/3] 正在更新核心安裝工具 (pip)...
.venv\Scripts\python.exe -m pip install --upgrade pip >nul
echo [3/3] 正在依照 requirements.txt 安裝所需套件...
.venv\Scripts\pip.exe install -r requirements.txt
echo.
echo =========================================
echo   安裝大功告成！您可以開始撰寫程式碼了！
echo =========================================
pause
