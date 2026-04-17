#!/bin/bash
# Krystal AI 交易系統 - Mac/Linux 一鍵啟動

cd "$(dirname "$0")"

echo "=========================================="
echo "  Krystal AI 交易系統 - 啟動"
echo "=========================================="
echo ""

# 檢查虛擬環境
if [ ! -d ".venv" ]; then
    echo "❌ 錯誤：找不到虛擬環境 (.venv)"
    echo "請先運行: python3 -m venv .venv"
    exit 1
fi

# 啟動虛擬環境
source .venv/bin/activate

# 執行啟動腳本
python run_flask.py
