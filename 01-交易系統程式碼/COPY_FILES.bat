@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ════════════════════════════════════════════════════
echo  📁 複製相關檔案到 dashboard_v8
echo ════════════════════════════════════════════════════
echo.

REM 建立 dashboard_v8 子資料夾
mkdir dashboard_v8\modules 2>nul

REM 複製 Python 檔案
echo ⏳ 複製 strategy_sync_api.py...
copy /Y strategy_sync_api.py dashboard_v8\ >nul

echo ⏳ 複製 sync_engine.py...
copy /Y sync_engine.py dashboard_v8\ >nul

echo ⏳ 複製 integrate_strategy_import.py...
copy /Y integrate_strategy_import.py dashboard_v8\ >nul

echo ⏳ 複製 strategyupload.py...
copy /Y modules\strategyupload.py dashboard_v8\modules\ >nul

REM 複製 HTML 檔案
echo ⏳ 複製 strategy_import_page.html...
copy /Y strategy_import_page.html dashboard_v8\ >nul

REM 複製配置檔案（如果存在）
if exist credentials.json (
    echo ⏳ 複製 credentials.json...
    copy /Y credentials.json dashboard_v8\ >nul
)

if exist .env (
    echo ⏳ 複製 .env...
    copy /Y .env dashboard_v8\ >nul
)

echo.
echo ════════════════════════════════════════════════════
echo ✅ 複製完成！
echo ════════════════════════════════════════════════════
echo.
echo 📂 dashboard_v8 現在包含:
echo    ✓ index.html
echo    ✓ app.py
echo    ✓ strategy_sync_api.py
echo    ✓ sync_engine.py
echo    ✓ strategy_import_page.html
echo    ✓ modules/strategyupload.py
echo.
echo 💡 提示: 現在你可以執行 START_DASHBOARD.bat 啟動系統
echo.
pause
