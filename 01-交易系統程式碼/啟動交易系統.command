#!/bin/bash
# Krystal AI 交易系統 - 一鍵啟動
# 雙擊此檔案即可啟動

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$PROJECT_DIR/.venv_macib64/bin/python"
APP_FILE="$PROJECT_DIR/app_html_flask.py"
PORT=5501
LOG_FILE="$PROJECT_DIR/logs/startup.log"

echo "=========================================="
echo "  Krystal AI 交易系統 - 啟動中..."
echo "=========================================="
echo ""

# 建立 logs 資料夾
mkdir -p "$PROJECT_DIR/logs"

# 檢查虛擬環境
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ 找不到虛擬環境：$VENV_PYTHON"
    read -p "按 Enter 關閉..."
    exit 1
fi

# 檢查是否已在運行
EXISTING_PID=$(lsof -ti :$PORT 2>/dev/null)
if [ -n "$EXISTING_PID" ]; then
    echo "⚠️  端口 $PORT 已被使用 (PID: $EXISTING_PID)"
    echo "   正在終止舊程序..."
    kill $EXISTING_PID 2>/dev/null
    sleep 2
    echo "   ✅ 已終止舊程序"
fi

# 啟動 Flask 應用
echo "🚀 啟動 Flask 應用..."
echo "   Python: $VENV_PYTHON"
echo "   應用: $APP_FILE"
echo "   端口: $PORT"
echo ""

cd "$PROJECT_DIR"
"$VENV_PYTHON" "$APP_FILE" > "$LOG_FILE" 2>&1 &
APP_PID=$!

# 等待啟動
echo "⏳ 等待服務啟動..."
for i in {1..15}; do
    sleep 1
    if lsof -ti :$PORT > /dev/null 2>&1; then
        echo ""
        echo "✅ 服務已成功啟動！"
        echo "=========================================="
        echo "  📱 訪問地址: http://localhost:$PORT"
        echo "  📋 日誌檔案: $LOG_FILE"
        echo "  🔧 PID: $APP_PID"
        echo "=========================================="

        # 自動開啟瀏覽器
        sleep 1
        open "http://localhost:$PORT"

        echo ""
        echo "按 Ctrl+C 可停止服務..."
        wait $APP_PID
        exit 0
    fi
    echo -n "."
done

echo ""
echo "❌ 服務啟動逾時，請檢查日誌："
echo "   $LOG_FILE"
echo ""
tail -20 "$LOG_FILE"
read -p "按 Enter 關閉..."
exit 1
