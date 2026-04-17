# Discord Bot 設定步驟

## 目標
- 每天早上 09:00 自動發送今日持倉報告
- 在 Discord 頻道裡直接 @Bot 問問題（Claude AI 回答）
- Slash 指令：`/今日報告` `/庫存` `/損益` `/問`

---

## Step 1：建立 Discord Bot（瀏覽器操作，約 5 分鐘）

1. 打開 https://discord.com/developers/applications
2. 點右上角「**New Application**」
3. 名稱填：`Krystal Trading Bot` → 點 Create
4. 左側選「**Bot**」
   - 點「**Reset Token**」→ 複製 Token（只顯示一次，請立即貼到記事本）
   - 往下找「**Privileged Gateway Intents**」
   - 開啟 **Message Content Intent**（必須）
5. 左側選「**OAuth2**」→「**URL Generator**」
   - Scopes 勾：`bot`
   - Bot Permissions 勾：
     - `Send Messages`
     - `Read Message History`
     - `View Channels`
6. 複製頁面底部產生的 URL，貼到瀏覽器
7. 選擇你的 Discord Server → 點「授權」→ Bot 加入成功

---

## Step 2：取得頻道 ID

1. 打開 Discord
2. 右上角設定 → 「進階」→ 開啟「**開發者模式**」
3. 在你想讓 Bot 發報告的頻道上**按右鍵** → 「**複製頻道 ID**」
4. 把這串數字記下來

---

## Step 3：設定 .env 檔案

打開 `c:\Projects\Krystal_完整系統\01-交易系統程式碼\.env`，加入以下三行：

```
DISCORD_BOT_TOKEN=你在Step1複製的Token
DISCORD_CHANNEL_ID=你在Step2複製的頻道ID
ANTHROPIC_API_KEY=你的Claude_API_Key
```

> ANTHROPIC_API_KEY 在 https://console.anthropic.com/ 取得（已有帳號直接登入）

---

## Step 4：安裝套件

打開 PowerShell 或 CMD，切換到專案目錄執行：

```bash
cd c:\Projects\Krystal_完整系統\01-交易系統程式碼
pip install "discord.py[voice]" anthropic python-dotenv
```

---

## Step 5：啟動 Bot

```bash
cd c:\Projects\Krystal_完整系統\01-交易系統程式碼
python discord_bot.py
```

看到以下訊息代表成功：
```
[Bot] 上線：Krystal Trading Bot#xxxx | 每日報告頻道：123456789
```

---

## Step 6：測試功能

在 Discord 頻道輸入：

| 指令 | 功能 |
|------|------|
| `/今日報告` | 立即產生今日持倉報告 |
| `/庫存` | 查台股持倉清單 |
| `/損益` | 查未實現損益 |
| `/問 今天該注意什麼？` | Claude AI 智能回答 |
| `@Krystal Trading Bot 我的持倉健康嗎？` | 直接對話 |

---

## Step 7：設定開機自動啟動（選用）

建立 `start_discord_bot.bat`（已存在，確認內容）：

```bat
@echo off
cd /d c:\Projects\Krystal_完整系統\01-交易系統程式碼
python discord_bot.py
```

加入 Windows 工作排程器：
1. 開始 → 搜尋「工作排程器」
2. 建立基本工作 → 觸發器選「登入時」
3. 動作選「啟動程式」→ 選 `start_discord_bot.bat`

---

## 常見問題

**Q: Bot 上線但 Slash 指令沒出現**
A: 等 1 分鐘讓 Discord 同步，或重新啟動 Bot

**Q: `/問` 指令回 "Claude API 未設定"**
A: 確認 .env 裡有 `ANTHROPIC_API_KEY`，重新啟動 Bot

**Q: 每日報告沒有自動發**
A: 確認 `.env` 裡有 `DISCORD_CHANNEL_ID`，且 Bot 有該頻道的發訊息權限

**Q: 台股持倉顯示空的**
A: 需要先執行元大庫存同步（`同步元大庫存.bat`）產生 snapshot

---

## 檔案位置

```
01-交易系統程式碼/
├── discord_bot.py          ← Bot 主程式
├── start_discord_bot.bat   ← 啟動腳本
├── .env                    ← Token 設定（不上傳 GitHub）
└── data/
    └── yuanta_positions_snapshot.json  ← 台股持倉快照
```

---

**建立日期**：2026-04-17
**維護者**：Krystal
