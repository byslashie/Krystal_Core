#!/bin/bash
# Krystal AI 交易系統 - Mac 一鍵啟動
# 使用方式：雙擊此檔案，或終端執行 bash START_KRYSTAL.sh

# 切換到腳本所在目錄
cd "$(dirname "$0")"
PROJ_DIR="$(pwd)"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   Krystal AI 交易系統  啟動中...    ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── 1. 關閉舊進程 ──────────────────────────────────────────
echo "[1/4] 清除舊進程..."
lsof -ti :8889 | xargs kill -9 2>/dev/null
lsof -ti :5000 | xargs kill -9 2>/dev/null
sleep 1

# ── 2. 啟動後端 API（port 8889）─────────────────────────────
echo "[2/4] 啟動後端 API (port 8889)..."
osascript -e "tell application \"Terminal\"
    do script \"cd '$PROJ_DIR' && echo '=== 後端 API (port 8889) ===' && python3 app_html_flask.py\"
    set custom title of front window to \"Krystal - Backend 8889\"
end tell"
sleep 5

# ── 3. 啟動前端伺服器（port 5000）───────────────────────────
echo "[3/4] 啟動前端伺服器 (port 5000)..."
osascript -e "tell application \"Terminal\"
    do script \"cd '$PROJ_DIR/dashboard_v7' && echo '=== 前端 (port 5000) ===' && python3 app.py\"
    set custom title of front window to \"Krystal - Frontend 5000\"
end tell"
sleep 3

# ── 4. 開啟瀏覽器 ───────────────────────────────────────────
echo "[4/4] 開啟瀏覽器..."
open http://localhost:5000

echo ""
echo "✅ 啟動完成！"
echo ""
echo "  前端：http://localhost:5000"
echo "  後端：http://localhost:8889"
echo ""
echo "  關閉系統：直接關閉兩個 Terminal 視窗即可"
