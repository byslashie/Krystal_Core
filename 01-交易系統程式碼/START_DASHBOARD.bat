@echo off
chcp 65001 >nul

echo.
echo ════════════════════════════════════════════════════
echo  🚀 Krystal AI Dashboard v8
echo ════════════════════════════════════════════════════
echo.

cd /d "%~dp0"
cd dashboard_v8

echo ✓ 工作目錄: %cd%
echo ✓ 啟動伺服器: http://localhost:5000/index.html
echo.
echo ⏳ 啟動中... 請稍候
timeout /t 2 /nobreak

echo ✅ 伺服器已啟動！
echo 📍 打開瀏覽器訪問: http://localhost:5000/index.html
echo.
echo 💡 提示: 按 Ctrl+C 停止伺服器
echo.

python -m http.server 5000
