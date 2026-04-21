@echo off
chcp 65001 >nul
cd /d "%~dp0"
color 0A
title Krystal AI - Dashboard v8 啟動器

echo.
echo ════════════════════════════════════════════════════
echo  🚀 Krystal AI 量化交易系統 v8
echo  策略導入管理 - 一鍵啟動
echo ════════════════════════════════════════════════════
echo.

REM 檢查是否在正確的目錄
if not exist "dashboard_v8" (
    echo ❌ 錯誤: 找不到 dashboard_v8 資料夾
    echo.
    echo 請確保在以下位置運行此腳本:
    echo G:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼\
    echo.
    pause
    exit /b 1
)

echo ✓ 檢查成功，開始啟動系統...
echo.

REM 0. 清除舊有的卡住 Port
echo ⏳ 0/3 正在清理舊有的連線 (Port 5000, 9000)...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5000 " ^| findstr LISTENING') do (taskkill /F /PID %%a >nul 2>nul)
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":9000 " ^| findstr LISTENING') do (taskkill /F /PID %%a >nul 2>nul)
timeout /t 1 /nobreak >nul


REM 1. 啟動 Flask 後端（dashboard_v8/start.py，Port 9000）
echo ⏳ 1/2 啟動 Flask 後端伺服器 (Port 9000)...
start /d "%~dp0dashboard_v8" "Dashboard v8 Flask Server" cmd /k "python start.py"
timeout /t 3 /nobreak

REM 2. 等待伺服器就緒後打開瀏覽器
echo ⏳ 2/2 等待伺服器就緒...
timeout /t 2 /nobreak

REM 3. 打開瀏覽器
echo.
echo ✓ 系統已啟動！正在打開瀏覽器...
echo.
start "" "http://localhost:9000"

echo.
echo ════════════════════════════════════════════════════
echo ✓ 啟動完成！
echo.
echo 📍 訪問地址:
echo    http://localhost:9000
echo.
echo 📋 運行的服務:
echo    ✓ Flask 後端伺服器 (埠口 9000)
echo.
echo 🎯 功能列表:
echo    📊 Dashboard - 完整的量化交易儀表板
echo    📤 策略導入 - 上傳、分析、決策、同步
echo    🔄 三向同步 - Google Sheets + 本地 + Git
echo.
echo 💡 提示:
echo    - 關閉任何窗口會停止該服務
echo    - 如需停止全部服務，關閉所有命令窗口
echo    - F12 打開開發者工具查看錯誤
echo.
echo ════════════════════════════════════════════════════
echo.
pause
