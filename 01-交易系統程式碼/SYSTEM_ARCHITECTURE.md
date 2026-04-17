# Krystal AI 交易系統架構文件

> 更新日期：2026-03-30

---

## 一、啟動方式

| 服務 | 啟動指令 | Port | 用途 |
|------|---------|------|------|
| **前端 HTML 伺服器** | `python dashboard_v7/app.py` | **5000** | 提供 index.html 給瀏覽器 |
| **後端 API 伺服器** | `python app_html_flask.py` | **8889** | 所有 API、Broker 連線、Sheets 讀寫 |

瀏覽器打開：`http://localhost:5000`
API 位址：`http://localhost:8889`（前端 index.html 內 `API_BASE` 已設定）

---

## 二、核心檔案

```
01-交易系統程式碼/
│
├── app_html_flask.py          ← 後端主程式（port 8889）
│                                 - 所有 /api/* 路由
│                                 - Google Sheets 讀寫
│                                 - Broker 連線（IB / 元大 / Schwab）
│                                 - APScheduler 定時任務
│
├── dashboard_v7/
│   ├── app.py                 ← 前端靜態伺服器（port 5000）
│   └── index.html             ← 主要儀表板 UI（單頁應用）
│       └── API_BASE = 'http://localhost:8889'
│
└── brokers/
    ├── ib_api.py              ← IB (Interactive Brokers) 連線
    ├── schwab_api.py          ← Schwab OAuth2 + API
    ├── schwab_oauth.py        ← Schwab 授權流程
    ├── yuanta_api.py          ← 元大 API 連線
    ├── sync_yuanta_positions.py  ← 元大庫存同步到 Sheets（含 upsert）
    ├── ib_sync_to_sheets.py   ← IB 庫存同步到 Sheets
    └── sync_positions.py      ← 通用庫存同步
```

---

## 三、API 路由分類

### 持倉 & 帳戶
| 路由 | 說明 |
|------|------|
| `GET /api/broker-positions` | 從 Sheets 讀取三家券商持倉（IB/元大/Schwab） |
| `GET /api/ib-account-summary` | IB 帳戶摘要（需 TWS 開啟） |
| `GET /api/yuanta-account-summary` | 元大帳戶摘要 |
| `GET /api/schwab-account-summary` | Schwab 帳戶摘要（需有效 Token） |
| `GET /api/query-ib` | 即時查詢 IB 持倉（需 TWS port 7496） |
| `POST /api/sync-yuanta` | 同步元大庫存到 Sheets |
| `POST /api/ib-sync` | 同步 IB 資料到 Sheets |
| `POST /api/schwab/sync-to-sheets` | 同步 Schwab 資料到 Sheets |

### YTD & 績效
| 路由 | 說明 |
|------|------|
| `GET /api/ytd-returns` | 各券商年初至今報酬率（從 broker_snapshot 計算） |
| `GET /api/daily-performance` | 每日績效資料 |
| `GET /api/portfolio-chart-data` | 投組走勢圖資料 |

### 交易紀錄
| 路由 | 說明 |
|------|------|
| `GET /api/trades/open` | 當前持倉交易（from Sheets） |
| `GET /api/trades/realized` | 已實現交易紀錄 |
| `POST /api/trades/update` | 更新交易備註/狀態 |
| `POST /api/upload-csv` | 上傳 CSV 匯入交易 |

### Schwab OAuth
| 路由 | 說明 |
|------|------|
| `GET /api/schwab/token-status` | 檢查 Token 有效期 |
| `GET /api/schwab/auth-url` | 取得 OAuth 授權 URL |
| `GET /schwab/callback` | OAuth callback 處理 |
| `GET /api/schwab/status` | Schwab 連線狀態 |

### 市場 & 風險
| 路由 | 說明 |
|------|------|
| `GET /api/market-indices` | 主要市場指數 |
| `GET /api/macro-indicators` | 總體經濟指標 |
| `GET /api/risk-metrics` | 風險指標 |
| `GET /api/risk/score` | 風險評分 |

---

## 四、Google Sheets 資料表

| 工作表名稱 | 用途 | 主要欄位 |
|-----------|------|---------|
| `broker_positions` | 三家券商持倉（upsert） | 時間, 券商, symbol, secType, exchange, currency, position, avgCost, totalCost, currentPrice, marketValue, unrealizedPnl, sellable |
| `broker_snapshot` | 帳戶淨值快照 | 時間, 券商, 帳戶總資產(NLV), 可用現金, 含融資權益, currency, 換算台幣 |
| `open_trades` | 當前持倉交易 | 日期, 標的, 券商, 市場, 幣別, 數量, 進場價, 進場原因, 策略 |
| `realized_trades` | 已實現交易 | — |

> **upsert 規則**：同一 symbol + 同一券商 → 更新該列；新 symbol → 新增；已出清 → 刪除

---

## 五、Broker 連線狀態

| 券商 | 連線方式 | 需求 | TWS 未開時 |
|------|---------|------|-----------|
| **IB** | ibapi → localhost:7496 | TWS/IBG 開啟 | fallback 讀 Sheets |
| **元大** | 元大 API (憑證登入) | 憑證 `.pfx` + 密碼 | fallback 讀 Sheets |
| **Schwab** | OAuth2 REST API | Token 有效（每 7 天更新） | Token 過期需重新授權 |

---

## 六、定時任務（APScheduler）

| 時間 | 任務 |
|------|------|
| 09:15 每日 | 元大庫存同步 |
| 15:30 每日 | 記錄每日績效 |

---

## 七、快速啟動指令

```bash
# 1. 啟動後端 API（port 8889）
cd "G:/我的雲端硬碟/Krystal_完整系統/01-交易系統程式碼"
python app_html_flask.py

# 2. 啟動前端（port 5000）
cd dashboard_v7
python app.py

# 3. 開瀏覽器
http://localhost:5000
```

---

## 八、憑證 & 環境變數

| 檔案 | 用途 |
|------|------|
| `credentials.json` | Google Sheets API 憑證 |
| `api.env` | 環境變數（Schwab key/secret、Sheets ID 等） |
| `D222061405.pfx` | 元大憑證 |
| `brokers/schwab_token.json` | Schwab OAuth Token（自動產生） |
