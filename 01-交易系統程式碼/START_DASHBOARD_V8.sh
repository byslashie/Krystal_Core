#!/bin/bash
# 啟動 Dashboard v8 的快速腳本

echo "🚀 Krystal AI Dashboard v8 啟動器"
echo "=================================="

cd "$(dirname "$0")/dashboard_v8" || exit 1

# 確保依賴已安裝
echo "📦 檢查依賴..."
python -m pip install flask flask-cors pandas plotly scipy scikit-learn openpyxl python-dotenv -q 2>/dev/null

# 啟動 Flask 伺服器
echo "✅ 啟動 Flask 後端服務器..."
echo "📍 訪問地址: http://127.0.0.1:9000"
echo "💡 按 Ctrl+C 停止伺服器"
echo ""

python app.py
