@echo off
chcp 65001 >nul

echo.
echo ════════════════════════════════════════════════════
echo  📦 安裝 Krystal Dashboard 依賴
echo ════════════════════════════════════════════════════
echo.

REM 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤: 未找到 Python
    echo 請先安裝 Python 3.7+ 並將其添加到 PATH
    pause
    exit /b 1
)

echo ✓ Python 已檢測到
echo.
echo ⏳ 正在安裝依賴包...
echo.

REM 安裝依賴
pip install flask plotly pandas scipy scikit-learn openpyxl -q

if errorlevel 1 (
    echo.
    echo ❌ 依賴安裝失敗
    pause
    exit /b 1
)

echo.
echo ════════════════════════════════════════════════════
echo ✅ 所有依賴已安裝成功！
echo ════════════════════════════════════════════════════
echo.
echo 已安裝的包:
echo  • Flask (web 框架)
echo  • Plotly (互動式圖表)
echo  • Pandas (數據處理)
echo  • SciPy (統計分析)
echo  • Scikit-learn (機器學習)
echo.
echo 現在可以執行 START_DASHBOARD.bat 啟動系統
echo.
pause
