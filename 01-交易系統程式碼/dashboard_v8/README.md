# 🎯 Dashboard v8 - 專業量化交易儀表板

**版本**：v8.0 Production Ready  
**狀態**：✅ 30 個 API 端點已實現 | ✅ 3 經紀商集成 | ✅ 6 個數據表  
**數據**：12 個活躍持倉 | 3 個經紀商 (Schwab, IB, 元大)

---

## 🚀 快速開始

### 1️⃣ 啟動應用（30 秒）

```bash
cd dashboard_v8
python app.py
# 訪問 http://localhost:9000
```

### 2️⃣ 測試 API（1 分鐘）

```bash
python test_all_apis.py
```

### 3️⃣ 查看持倉（立即）

打開瀏覽器：http://localhost:9000

---

## 📊 核心功能

### ✅ 實時持倉監控
- **12 個活躍持倉** — 美股、台股、多經紀商
- **實時市值計算** — 基於最新股價
- **損益追蹤** — 已平倉 & 未平倉

### ✅ 交易記錄管理
- **已平倉交易** — 完整的損益歷史
- **開倉交易** — 實時未平倉列表
- **交易搜索** — 按策略、日期、標的

### ✅ 投資組合分析
- **YTD 回報** — 年初至今績效
- **月度回報** — 每月損益統計
- **淨值曲線** — 投資組合歷史走勢
- **回撤分析** — 最大回撤、恢復期

### ✅ 市場數據
- **全球股市指數** — 美股、台股、日股等
- **宏觀經濟指標** — 利率、失業率、GDP 等
- **實時股價** — Yahoo Finance 集成
- **交易策略** — 4 個策略績效對標

### ✅ 經紀商集成
- **Schwab** — OAuth 認證、帳戶查詢、持倉同步
- **Interactive Brokers** — 帳戶集成、持倉追蹤
- **元大** — 台股持倉管理

---

## 🏗️ 系統架構

```
┌─────────────────────────────────┐
│    前端（7,831 行 HTML/CSS/JS）  │
│                                 │
│  - 持倉儀表板                    │
│  - 交易記錄                      │
│  - 投資組合分析                  │
│  - 市場數據                      │
│  - 實時警報                      │
└────────────┬────────────────────┘
             │ REST API (30 個端點)
┌────────────▼────────────────────┐
│    後端（1,465 行 Python Flask）  │
│                                 │
│  - 交易管理 API                  │
│  - 投資組合 API                  │
│  - 市場數據 API                  │
│  - 經紀商集成                    │
│  - 數據驗證 & 轉換               │
└────────────┬────────────────────┘
             │ SQLite & 外部 API
┌────────────▼────────────────────┐
│    數據層（SQLite + 外部服務）    │
│                                 │
│  - broker_positions (持倉)      │
│  - realized_trades (交易)       │
│  - equity_snapshots (快照)      │
│  - Yahoo Finance (實時股價)     │
│  - Schwab/IB/元大 API           │
└─────────────────────────────────┘
```

---

## 📋 API 列表（30 個端點）

### 交易管理（4 個）
- `GET /api/trades/open` — 未平倉交易
- `GET /api/trades/realized` — 已平倉交易
- `POST /api/trades/add` — 新增交易
- `POST /api/trades/realized/sync` — 同步已平倉

### 持倉管理（4 個）
- `GET /api/positions` — 所有持倉
- `GET /api/broker-positions` — 按經紀商持倉
- `POST /api/positions/<id>/close` — 平倉
- `PUT /api/positions/<id>/meta` — 更新備註

### 投資組合（4 個）
- `GET /api/ytd-returns` — YTD 回報
- `GET /api/portfolio-chart-data` — 投資組合圖表
- `GET /api/equity-history` — 權益歷史
- `POST /api/snapshot` — 拍攝快照

### 市場數據（3 個）
- `GET /api/market-indices` — 全球股市指數
- `GET /api/macro-indicators` — 宏觀經濟指標
- `GET /api/yahoo-proxy` — 實時股價查詢

### 交易策略（1 個）
- `GET /api/strategies` — 策略列表 & 績效

### 經紀商集成（5 個）
- `GET /api/schwab/token-status` — Schwab Token 狀態
- `GET /api/schwab-account-summary` — Schwab 帳戶摘要
- `POST /api/schwab/sync-positions` — Schwab 同步持倉
- `POST /api/schwab/sync-to-sheets` — 同步到 Google Sheets
- `GET /api/query-ib` — IB 帳戶查詢
- `POST /api/ib-sync` — IB 同步
- `POST /api/sync-yuanta` — 元大同步

### 圖表 & 工具（4 個）
- `POST /api/generate-charts` — 生成圖表
- `GET /api/charts/<filename>` — 獲取圖表
- `GET /api/test` — 測試端點
- `GET /health` — 健康檢查

---

## 💾 數據庫架構

### broker_positions（持倉表）
```sql
id | symbol | position | avgCost | marketPrice | unrealizedPNL 
   | broker | currency | strategy | notes | synced_at
```
- **12 個記錄** — 當前活躍持倉
- **3 個經紀商** — Schwab, IB, 元大

### realized_trades（交易表）
```sql
id | symbol | direction | entry_price | exit_price | quantity
   | pnl | pnl_pct | date | exit_date | broker | strategy | status
```
- 完整的交易歷史
- 包含進出場價格、損益等

### equity_snapshots（權益快照）
```sql
date | ib_mv_usd | schwab_mv_usd | yuanta_mv_twd
   | total_mv_twd | total_pnl_twd | usd_twd_rate
```
- 每日權益變化
- 用於繪製淨值曲線

### 其他表
- `positions_snapshot` — 持倉快照
- `sync_log` — 同步日誌

---

## ⚡ 核心特性

### 🔄 實時更新
- WebSocket 推送持倉變化
- 5 分鐘自動刷新市場數據
- 智能快取避免 API 配額消耗

### 🔐 安全
- OAuth 2.0 認證（Schwab）
- API Key 存儲在 .env（不提交 Git）
- CORS 配置允許跨域請求
- 無自動交易執行（需人工確認）

### 📊 完整的分析
- 18 個 KPI 指標（Sharpe, Kelly, VaR 等）
- 4 種專業圖表（Equity Curve, MAE/MFE, P/L Distribution）
- 深度診斷 & 改進建議

### 🌍 多經紀商
- **美股** — Schwab, Interactive Brokers
- **台股** — 元大證券
- 統一的數據格式 & 計算邏輯

---

## 📖 文檔導航

| 文檔 | 用途 |
|------|------|
| **SYSTEM_ARCHITECTURE.md** | 🏗️ 系統設計 & 架構圖 |
| **BACKEND_REQUIREMENTS.md** | 📋 API 詳細規範 |
| **BACKEND_CHECKLIST.md** | ✅ 後端功能檢查清單 |
| **SCHWAB_OAUTH_FIX_PLAN.md** | 🔐 OAuth 集成指南 |
| **SCHWAB_QUICK_REFERENCE.md** | ⚡ Schwab 快速參考 |
| **TODO.md** | 📝 待做優先清單 |

---

## 🎯 部署

### 開發環境
```bash
cd dashboard_v8
python app.py
# 訪問 http://localhost:9000
```

### 生產環境（推薦）
```bash
# 使用 Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:9000 app:app

# 或使用 Docker
docker build -t dashboard-v8 .
docker run -p 9000:9000 dashboard-v8
```

---

## 📊 數據統計

| 項目 | 值 |
|------|-----|
| 前端代碼 | 7,831 行 |
| 後端代碼 | 1,465 行 |
| API 端點 | 30 個 |
| 數據表 | 6 個 |
| 當前持倉 | 12 個 |
| 經紀商 | 3 個 |
| KPI 指標 | 18 個 |

---

## 🚀 下一步

### 即時（本週 4/7-4/13）
- ✅ 驗證所有 API 端點
- ✅ 完整測試持倉同步
- ✅ Google Sheets 集成

### 近期（4/14-4/30）
- 🔧 完整 Schwab OAuth 集成
- 🔧 IB 帳戶連接優化
- 🔧 實時警報系統

### 中期（5 月+）
- 📈 性能優化（快取、批量操作）
- 📈 進階分析（機器學習）
- 📈 社群情緒集成

---

## 💡 常見問題

**Q：如何新增交易？**  
A：使用 `POST /api/trades/add` 或在前端表單中輸入。

**Q：持倉數據從哪裡來？**  
A：SQLite 本地緩存。使用 `/api/schwab/sync-positions` 等從經紀商同步。

**Q：如何修改持倉備註？**  
A：使用 `PUT /api/positions/<id>/meta` API。

**Q：支持哪些股票？**  
A：美股、台股、期貨等。只要 Yahoo Finance 有報價就支持。

---

## 📞 支持

- 📖 查看 SYSTEM_ARCHITECTURE.md 了解系統設計
- 🔧 查看 BACKEND_REQUIREMENTS.md 了解 API 詳情
- ⚡ 查看 SCHWAB_QUICK_REFERENCE.md 解決 Schwab 問題
- 📝 查看 TODO.md 了解待做項目

---

**版本**：v8.0  
**最後更新**：2026-04-07  
**維護者**：Krystal  
**狀態**：Production Ready ✅

🎉 **Ready to trade！**
