#!/bin/bash
# Krystal AI 交易系統 - Mac 開機自動啟動設定
# 使用方式：bash SETUP_AUTOSTART_MAC.sh

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Krystal 交易系統 - Mac 自動啟動設定   ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 取得腳本所在目錄 ─────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
START_SCRIPT="$SCRIPT_DIR/START_KRYSTAL.sh"
PLIST_NAME="com.krystal.trading"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

echo "專案路徑：$SCRIPT_DIR"
echo ""

# ── 確保啟動腳本有執行權限 ───────────────────────────────────
chmod +x "$START_SCRIPT"

# ── 找到 python3 路徑 ─────────────────────────────────────────
PYTHON3=$(which python3 2>/dev/null || which python 2>/dev/null || echo "/usr/bin/python3")
echo "Python：$PYTHON3"

# ── 移除舊的 plist ───────────────────────────────────────────
if [ -f "$PLIST_PATH" ]; then
    launchctl unload "$PLIST_PATH" 2>/dev/null
    rm "$PLIST_PATH"
fi

# ── 建立 LaunchAgent plist ────────────────────────────────────
echo "[1/3] 建立 LaunchAgent..."
mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$START_SCRIPT</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>

    <!-- 登入後延遲 30 秒再啟動 -->
    <key>StartInterval</key>
    <integer>0</integer>

    <key>RunAtLoad</key>
    <true/>

    <!-- 延遲啟動（秒） -->
    <key>ThrottleInterval</key>
    <integer>30</integer>

    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/krystal_trading.log</string>

    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/krystal_trading_error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
EOF

echo "      ✅ plist 已建立：$PLIST_PATH"

# ── 載入 LaunchAgent ─────────────────────────────────────────
echo "[2/3] 載入自動啟動任務..."
launchctl load "$PLIST_PATH" 2>/dev/null && echo "      ✅ 載入成功" || echo "      ⚠️  載入失敗（重新登入後生效）"

# ── 驗證 ────────────────────────────────────────────────────
echo "[3/3] 驗證..."
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "      ✅ 任務已在執行清單中"
else
    echo "      ℹ️  任務已設定，重新登入 Mac 後生效"
fi

echo ""
echo "✅ 設定完成！"
echo ""
echo "  下次登入 Mac 時，系統會自動啟動："
echo "    - 後端 API (port 8889)"
echo "    - 前端伺服器 (port 5000)"
echo "    - 瀏覽器開啟 http://localhost:5000"
echo ""
echo "  日誌位置："
echo "    ~/Library/Logs/krystal_trading.log"
echo "    ~/Library/Logs/krystal_trading_error.log"
echo ""
echo "════════════════════════════════════"
echo "  其他管理指令："
echo "    停用：launchctl unload $PLIST_PATH"
echo "    啟用：launchctl load $PLIST_PATH"
echo "    刪除：rm $PLIST_PATH"
echo "    立即執行：launchctl start $PLIST_NAME"
echo "    查看日誌：tail -f ~/Library/Logs/krystal_trading.log"
echo "════════════════════════════════════"
