#!/bin/bash
echo "========================================="
echo "  開始自動初始化量化交易開發環境 (macOS)..."
echo "========================================="
echo ""
echo "[1/3] 正在建立 Python 虛擬環境 (.venv)..."
python3 -m venv .venv
echo "[2/3] 正在更新核心安裝工具 (pip)..."
.venv/bin/python -m pip install --upgrade pip > /dev/null 2>&1
echo "[3/3] 正在依照 requirements.txt 安裝所需套件..."
.venv/bin/pip install -r requirements.txt
echo ""
echo "========================================="
echo "  安裝大功告成！您可以開始撰寫程式碼了！"
echo "========================================="
