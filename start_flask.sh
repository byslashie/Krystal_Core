#!/bin/bash
# Flask 交易儀表板啟動腳本 (Mac/Linux)

# 設置顏色輸出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 獲取當前目錄並切換到交易系統目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRADING_DIR="$SCRIPT_DIR/01-交易系統程式碼"

cd "$TRADING_DIR" || {
    echo -e "${RED}❌ 無法進入交易系統目錄：$TRADING_DIR${NC}"
    exit 1
}

echo -e "${GREEN}📂 當前目錄：$TRADING_DIR${NC}"

# 檢查 Python 是否安裝
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安裝${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python 版本：$(python3 --version)${NC}"

# 檢查虛擬環境
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ 找到虛擬環境，激活中...${NC}"
    source venv/bin/activate
fi

# 檢查 Flask 是否已安裝
if ! python3 -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}⚠️ Flask 未安裝，嘗試安裝...${NC}"
    pip3 install flask
fi

# 啟動 Flask 應用
echo -e "${GREEN}🚀 正在啟動 Flask 應用...${NC}"
echo -e "${GREEN}📊 訪問地址: http://127.0.0.1:8888${NC}"
echo -e "${YELLOW}💡 按 Ctrl+C 停止應用${NC}"
echo ""

python3 app_html_flask.py
