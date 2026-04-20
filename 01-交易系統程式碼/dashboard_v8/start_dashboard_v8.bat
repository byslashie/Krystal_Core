@echo off
REM Dashboard V8 啟動腳本 - 同時啟動前後台
REM 將此檔案放在 dashboard_v8 文件夾中

setlocal enabledelayedexpansion

REM 設定變數
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
cd /d "%SCRIPT_DIR%"

REM 清空之前的 LOG
if exist flask_output.log del flask_output.log
if exist browser_output.log del browser_output.log

REM 檢查 Python 是否已安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤：未檢測到 Python，請先安裝 Python 3.8+
    pause
    exit /b 1
)

echo ========================================
echo   🚀 Dashboard V8 啟動中...
echo ========================================
echo.

REM 1️⃣  啟動 Flask 後台服務
echo [1] 啟動 Flask 後台服務 (Port 9000)...
start "Dashboard V8 Backend" cmd /k "cd /d "%SCRIPT_DIR%" && python app.py >> flask_output.log 2>&1"

REM 等待 Flask 啟動完成（最多 10 秒）
echo [2] 等待後台服務啟動...
timeout /t 3 /nobreak

REM 2️⃣  用預設瀏覽器打開前台
echo [3] 在瀏覽器中打開前台...
timeout /t 2 /nobreak

REM 嘗試用預設瀏覽器打開
start http://127.0.0.1:9000/

REM 或者，如果想用特定瀏覽器（Chrome），取消註解下面這行：
REM start chrome http://127.0.0.1:9000/

echo.
echo ========================================
echo   ✅ Dashboard V8 已啟動！
echo ========================================
echo.
echo 📍 前台地址：http://127.0.0.1:9000/
echo 📝 後台日誌：%SCRIPT_DIR%flask_output.log
echo.
echo 💡 提示：
echo   - 關閉「Dashboard V8 Backend」黑窗口即可停止服務
echo   - 查看後台日誌：cat flask_output.log
echo   - 刷新瀏覽器查看最新數據
echo.
pause
