# Discord Bot 設定與使用文件

> 程式：`discord_bot.py` / 啟動：`start_discord_bot.bat`
> 最後更新：2026-05-12

---

## 🚦 當前狀態（2026-05-12）

| 項目 | 狀態 | 備註 |
|---|---|---|
| `DISCORD_BOT_TOKEN` | ✅ 已設定 | Bot 名稱：`Krystal#2019` |
| `DISCORD_CHANNEL_ID` | ❌ **未設定** | 自動排程無法發送 |
| `DISCORD_WEBHOOK_YUANTA` | ⚠️ 已設定但 **403 Forbidden** | Webhook 失效，需重建 |
| Bot 加入伺服器數 | ❌ **0** | Bot 未被邀請到任何 server |
| `ANTHROPIC_API_KEY` | ⚠️ 套件未裝 | 異動原因 fallback 為「新聞標題」 |
| yfinance 大盤抓取 | ✅ 正常 | TWII / GSPC / IXIC / DJI |
| yfinance 個股抓取 | ✅ 正常 | 含 0050、006208、00631L 自動補 0 |
| Sheet `broker_positions` | ✅ 可讀 | Schwab 現價是空字串（上游問題，待修） |

**結論：早報內容已能正確產生，但因 Bot 未進伺服器、Webhook 失效，目前無法投到 Discord。先完成下方「初始化」流程。**

---

## 🛠️ 初始化（首次設定，必做）

### 1. 邀請 Bot 進你的 Discord 伺服器

1. 前往 https://discord.com/developers/applications
2. 選你的 Application（對應 `Krystal#2019`）
3. 左側 **OAuth2 → URL Generator**
4. Scopes 勾：`bot`、`applications.commands`
5. Bot Permissions 勾：`Send Messages`、`Embed Links`、`Read Message History`、`Use Slash Commands`
6. 複製產生的 URL → 在瀏覽器打開 → 選擇要加入的伺服器 → 授權
7. 確認 server 裡看到 `Krystal#2019` 上線

### 2. 取得頻道 ID

1. Discord 內 **使用者設定 → 進階 → 開發者模式** 打開
2. 右鍵你要接收早報的頻道 → **複製頻道 ID**
3. 把 ID 寫進 `01-交易系統程式碼/.env`：
   ```env
   DISCORD_CHANNEL_ID=123456789012345678
   ```

### 3. （選用）重建 Webhook

若想保留另一個獨立的元大持倉 webhook 通道：

1. 在 Discord 頻道 → 右上齒輪 → **整合 → 建立 Webhook**
2. 複製 URL，替換 `.env` 裡的 `DISCORD_WEBHOOK_YUANTA`

### 4. 安裝 anthropic 套件（讓 AI 解釋異動原因）

```bash
pip install anthropic
```

並確認 `.env` 已有 `ANTHROPIC_API_KEY`。

### 5. 啟動 Bot

```bash
cd "c:/Projects/Krystal_完整系統/01-交易系統程式碼"
python discord_bot.py
```

或用既有的 `start_discord_bot.bat`（注意路徑寫死 `h:\我的雲端硬碟\...`，可能需要改成 `c:\Projects\...`）。

---

## 📅 自動排程

| 時間 (台北) | 任務 | 內容 |
|---|---|---|
| **07:00** | `morning_sync` | 跑 `sync_ib_to_sheets.py` + `sync_schwab_to_sheets.py`，發同步結果通知 |
| **08:00** | `morning_report` | 發送早報：大盤 + 持倉 + 異動標的（>±3%）原因 |

排程由 `discord.ext.tasks` 在 `on_ready` 時啟動，**Bot 需保持運行**（建議用 `start_discord_bot.bat` 加進 Windows 工作排程器，開機自動啟動）。

### 元大為什麼不一起 07:00 同步？

元大要等台股 09:00 開盤 → 09:15 後才有當日完整資料。現有 `run_yuanta_sync.bat` / `sync_yuanta_09h15.bat` 走另一條排程。

---

## ⌨️ Slash 指令

| 指令 | 用途 |
|---|---|
| `/早報` | 立即產生早報（大盤 + 持倉 + 異動原因） |
| `/同步` | 立即觸發 IB + Schwab 同步並通知 |
| `/今日報告` | 舊版持倉報告（不含大盤、不含 AI 解釋） |
| `/庫存` | 台股 snapshot 持倉清單 |
| `/損益` | 各持股未實現損益排序 |
| `/問 <問題>` | Claude AI 智能問答（需要 `anthropic` 套件） |

也可以在 Bot 所在頻道 `@Krystal` 直接對話，會帶上當前持倉作為 context。

---

## 📋 早報範本（2026-05-12 實測輸出）

```
🌅 Krystal 早報 2026-05-12 (週二) 19:16

═══ 🌐 大盤 ═══
🇹🇼 加權指數     41,898.32  🔴+0.26%  (+108.3)
🇺🇸 S&P 500      7,412.84   🔴+0.19%  (+13.9)
🇺🇸 Nasdaq      26,274.13   🔴+0.10%  (+27.1)
🇺🇸 道瓊        49,704.47   🔴+0.19%  (+95.3)

═══ 🇹🇼 台股持倉 ═══
代碼       股數    均價     現價     今日%    損益
─────────────────────────────────────────────
50      1,391   66.08    96.85   -0.05%  +42,804
6208    1,471  112.03   224.55   +0.11%  +165,524
00631L 15,000   27.69    32.52   -0.43%  +72,448
2360       50 2183.52  2440.00   +3.39%  +12,824 🚀
2383       20 4706.15  4900.00   +1.03%   +3,877
3037      130  744.11   875.00   +1.63%  +17,016
6515       12 9391.75  9950.00   -1.39%   +6,699
8046       80  819.45   900.00   -0.88%   +6,444
─────────────────────────────────────────────
合計                                     +327,637

═══ 🇺🇸 美股（IB + Schwab）═══
代碼   券商    股數    均價     現價    今日%    損益$
─────────────────────────────────────────────────
ACWX   IB      60   65.81   75.70   -0.13%  +593
LITE   IB       2  965.74 1059.65  +16.52%  +188   🚀
SNDK   IB       2  592.46 1538.00   -0.95% +1,891
NVDA   Schwab  32   31.50    0.00   +1.97%      0
WDC    Schwab   2  132.38    0.00   +7.46%      0  🚀
QQQ    Schwab   8  686.09    0.00   +0.29%      0
TQQQ   Schwab 149   69.62    0.00   +0.89%      0
─────────────────────────────────────────────────
合計                                          +2,672

═══ 📰 異動標的（>±3%）═══

🚀 2360 +3.39%
  Chroma Ate Inc (TPE:2360) Q1 2026 Earnings Call Highlights: Record Sales...

🚀 LITE +16.52%
  Lumentum AI pivot triggers massive Nasdaq 100 shakeup

🚀 WDC +7.46%
  Bull of the Day: Western Digital (WDC)

═══ 📅 今日提醒 ═══
🇹🇼 09:00 台股開盤  |  🇺🇸 21:30 美股開盤
```

### 顏色說明（Discord 內無原生顏色，用 emoji 代替）

- 🔴 漲（台股慣例：紅=漲）
- 🟢 跌
- 🚀 漲幅 ≥ +3%
- ⚠️ 跌幅 ≤ -3%

### AI 解釋格式（裝 anthropic 後）

當異動標的 ≥ ±3% 時，Claude API 會接收 (代碼 + 漲跌% + 新聞標題) 並回 2 行：

```
🚀 2360 +3.39%
  Q1 法說毛利優於預期，營收續創新高
  外資調升目標價，AI 測試設備接單能見度延伸至 Q3
```

未裝 anthropic 時自動降級為「顯示新聞標題」（如上方範本所示）。

---

## ⚙️ 環境變數一覽（`.env`）

```env
# 必填
DISCORD_BOT_TOKEN=<Bot Token>
DISCORD_CHANNEL_ID=<頻道 ID, 18 位數字>
ANTHROPIC_API_KEY=<Claude API Key>

# 選用
DISCORD_WEBHOOK_YUANTA=<獨立 webhook，用於元大持倉通知>
```

---

## 🐛 已知問題與待辦

| 項目 | 影響 | 處理方式 |
|---|---|---|
| Schwab 現價在 Sheet 是空字串 | 損益顯示 0 | 修 `sync_schwab_to_sheets.py` 把 marketPrice 寫入 |
| `DISCORD_WEBHOOK_YUANTA` 403 | webhook 無法發送 | 在 Discord 重建 webhook |
| Bot 未進伺服器 | 自動排程無法發送 | 跑「初始化 步驟 1」 |
| anthropic 未裝 | 異動只顯示新聞標題 | `pip install anthropic` |
| `start_discord_bot.bat` 路徑寫死 `H:\` | 從 C: 啟動會失敗 | 改 `PROJECT_ROOT` 為 `c:\Projects\...` |
| 元大代碼補 0 用 fallback 試 4 碼/6 碼 | 第一次抓多一次 API call | 已加 `_tw_resolve_cache` 緩存 |

---

## 📁 相關檔案

- [discord_bot.py](../discord_bot.py) — 主程式
- [start_discord_bot.bat](../start_discord_bot.bat) — 啟動腳本
- [sync_ib_to_sheets.py](../sync_ib_to_sheets.py) — 07:00 IB 同步
- [sync_schwab_to_sheets.py](../sync_schwab_to_sheets.py) — 07:00 Schwab 同步
- [sheets_utils.py](../sheets_utils.py) — `broker_positions` Sheet 讀寫
- `.env` — 不在 Git，需自行維護
