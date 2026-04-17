@echo off
REM 清理所有 Python 進程並啟動 DashboardV2
REM 一鍵執行腳本

echo.
echo ========================================
echo DashboardV2 一鍵啟動
echo ========================================
echo.

REM 殺死所有 Python 進程
echo [1/3] 清理舊的 Python 進程...
taskkill /F /IM python.exe /T >nul 2>&1
echo       已清理完成

REM 暫停一下
timeout /t 2 /nobreak >nul

REM 切換到工作目錄
echo [2/3] 啟動 Flask 伺服器...
cd /d "g:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"

REM 啟動 Flask
echo [3/3] 伺服器啟動中...
echo.
echo ========================================
echo URL: http://localhost:8888/v2
echo 按 CTRL+C 停止伺服器
echo ========================================
echo.

python run_dashboardv2.py

pause
