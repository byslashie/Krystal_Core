@echo off
REM Dashboard V8 管理工具 - 啟動/停止/重啟

setlocal enabledelayedexpansion
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

:menu
cls
echo ========================================
echo   📊 Dashboard V8 管理工具
echo ========================================
echo.
echo [1] 🚀 啟動 Dashboard（新視窗）
echo [2] ⛔ 停止所有 Dashboard 進程
echo [3] 🔄 重啟 Dashboard
echo [4] 📋 查看後台日誌
echo [5] 🌐 在瀏覽器中打開（http://127.0.0.1:9000）
echo [6] ❌ 退出
echo.
set /p choice="請選擇操作 [1-6]: "

if "%choice%"=="1" goto start_service
if "%choice%"=="2" goto stop_service
if "%choice%"=="3" goto restart_service
if "%choice%"=="4" goto view_logs
if "%choice%"=="5" goto open_browser
if "%choice%"=="6" goto exit_program
goto menu

:start_service
echo [*] 啟動 Flask 服務中...
if exist flask_output.log del flask_output.log
start "Dashboard V8 Backend" cmd /k "cd /d "%SCRIPT_DIR%" && python app.py >> flask_output.log 2>&1"
timeout /t 3 /nobreak
echo [✓] 服務已啟動！
timeout /t 2 /nobreak
goto menu

:stop_service
echo [*] 停止服務中...
taskkill /FI "WINDOWTITLE eq Dashboard V8*" /T /F >nul 2>&1
taskkill /IM python.exe /F >nul 2>&1
echo [✓] 服務已停止！
timeout /t 2 /nobreak
goto menu

:restart_service
echo [*] 重啟服務中...
call :stop_service
timeout /t 2 /nobreak
call :start_service
goto menu

:view_logs
if exist flask_output.log (
    echo.
    echo [* 後台日誌內容 (最後 30 行):
    echo.
    for /f "skip=1 tokens=*" %%A in ('powershell -Command "Get-Content -Path '%SCRIPT_DIR%flask_output.log' -Tail 30"') do echo %%A
) else (
    echo [!] 尚未找到日誌文件
)
echo.
pause
goto menu

:open_browser
start http://127.0.0.1:9000/
timeout /t 2 /nobreak
goto menu

:exit_program
exit /b 0
