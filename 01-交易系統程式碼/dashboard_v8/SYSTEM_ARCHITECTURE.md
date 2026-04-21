# 🏗️ Dashboard v8 - 整體系統架構設計

**文檔日期**：2026-04-07  
**版本**：v8.0 Production Ready  
**狀態**：📋 架構規劃

---

## 📊 v7 vs v8 對比

### Dashboard v7 - 專注型
```
應用場景：單一使用者、實時監控
程式規模：輕量級
├── 前端：4,481 行 HTML/CSS
├── JS API：163 行 (宏觀羅盤集成)
└── 後端：基礎 Flask (app.py)
主要功能：宏觀經濟指標監控
```

### Dashboard v8 - 企業級
```
應用場景：多經紀商、複雜分析
程式規模：企業級應用
├── 前端：7,831 行 HTML/CSS/JS (2x v7)
├── 後端：1,465 行 Python (重型業務邏輯)
├── 數據庫：SQLite (4 個核心表)
└── API：13 個端點 (交易/投資組合/市場/經紀商)
主要功能：投資組合管理 + 多經紀商集成
```

---

## 🎯 Dashboard v8 核心功能清單

### ✅ 已實現（4/1 完成）

#### 交易管理
- [x] `/api/trades/open` — 未平倉交易列表
- [x] `/api/trades/realized` — 已平倉交易列表
- [x] Google Sheets `trades` 表集成
- [x] 8 筆樣本交易數據

#### 投資組合分析
- [x] `/api/ytd-returns` — 年初至今回報計算
- [x] `/api/portfolio-chart-data` — 淨值曲線數據
- [x] 30 天歷史數據
- [x] 月度回報統計

#### 市場數據
- [x] `/api/market-indices` — 全球股市指數
- [x] `/api/macro-indicators` — 宏觀經濟指標
- [x] Yahoo Finance 集成
- [x] FRED API 框架

#### 交易策略
- [x] `/api/strategies` — 策略列表
- [x] 4 個樣本策略
- [x] 性能指標計算

#### 經紀商集成（Stub）
- [x] `/api/schwab-account-summary` (Stub)
- [x] `/api/schwab/token-status` (Stub)
- [x] `/api/ib-accounts` (Stub)
- [x] `/api/sync-yuanta` (Stub)

---

### 🔴 待實現（P0-P1）

#### P0 - 核心功能（本週 4/7-4/13）

**1. Schwab OAuth 完整集成**
- [ ] Token 系統修復 + 自動刷新
- [ ] 帳戶查詢 API 實現
- [ ] 持倉同步邏輯
- [ ] Google Sheets 寫回
- **預期時間**：13-15 小時
- **詳見**：`SCHWAB_OAUTH_FIX_PLAN.md`

**2. Yahoo Finance 實時價格**
- [ ] 替換 yfinance 樣本數據
- [ ] 實現真實股價查詢
- [ ] 美股 + 台股支持
- **預期時間**：2-3 小時

**3. Google Sheets 交易同步**
- [ ] 從 Sheets 讀取完整交易記錄
- [ ] 驗證數據完整性
- [ ] 處理格式不一致
- **預期時間**：2-3 小時

#### P1 - 經紀商集成（4/14 後）

**IB (Interactive Brokers)**
- [ ] IBPy 連接實現
- [ ] 帳戶查詢
- [ ] 持倉同步
- [ ] 交易歷史
- **預期時間**：10-12 小時

**元大 (Yuanta)**
- [ ] API 認證
- [ ] 帳戶查詢
- [ ] 持倉同步
- **預期時間**：8-10 小時

#### P2 - 進階功能（5 月後）

- [ ] Redis 快取層
- [ ] 定期同步排程（cron）
- [ ] 實時警報系統
- [ ] 高級分析報告

---

## 🏗️ 系統架構總覽

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端層 (Browser)                         │
│  ┌─────────────────────────────────────────────────────────────┐
│  │ index.html (7,831 行)                                       │
│  │ ├─ 交易儀表板 TAB                                            │
│  │ ├─ 投資組合分析 TAB                                          │
│  │ ├─ 市場指標 TAB                                              │
│  │ ├─ 經紀商連接 TAB (Schwab/IB/元大)                           │
│  │ └─ 設置 TAB                                                  │
│  └─────────────────────────────────────────────────────────────┘
│                                ↓ (REST API / JSON)
├─────────────────────────────────────────────────────────────────┤
│                        API 層 (Flask)                            │
│  ┌─────────────────────────────────────────────────────────────┐
│  │ app.py (1,465 行)                                           │
│  │                                                             │
│  │ 交易 API              投資組合 API      市場 API             │
│  │ ├─ /api/trades/open   ├─ /api/ytd-returns  ├─ /api/indices  │
│  │ └─ /api/trades/real   └─ /api/portfolio    └─ /api/macro    │
│  │                                                             │
│  │ 經紀商 API (本週修復)                                        │
│  │ ├─ /api/schwab/*      (P0 - 13h)                            │
│  │ ├─ /api/ib/*          (P1 - 10h)                            │
│  │ └─ /api/yuanta/*      (P1 - 8h)                             │
│  │                                                             │
│  │ CORS 中間件 ↔ 錯誤處理 ↔ 數據驗證                              │
│  └─────────────────────────────────────────────────────────────┘
│                                ↓
├─────────────────────────────────────────────────────────────────┤
│                     數據層 & 外部服務                             │
│  ┌──────────────┬────────────────┬──────────────┬───────────────┐
│  │ SQLite DB    │ Google Sheets  │ Yahoo Finance│ Schwab API    │
│  │ broker_      │ API            │ + yfinance   │ (OAuth)       │
│  │ positions.db │ (Google Sheets)│              │ 即時帳戶數據  │
│  │              │ trades, pos    │ 股票實時價格 │               │
│  │ 4 核心表     │ 數據源         │              │ P0 優先       │
│  └──────────────┴────────────────┴──────────────┴───────────────┘
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 目錄結構

```
dashboard_v8/
├── app.py                              (1,465 行) 主應用
├── index.html                          (7,831 行) 前端
│
├── brokers/                            經紀商集成
│   ├── schwab_oauth.py                 ✅ Token 管理
│   ├── schwab_api.py                   🔧 待完善
│   ├── ib_client.py                    ❌ 待實現
│   └── yuanta_api.py                   ❌ 待實現
│
├── .env                                環境變數（Git ignore）
├── .secrets/
│   └── schwab_token.json               ❌ 待建立
│
├── charts/                             生成的圖表
│   ├── equity_curve.html
│   ├── mae_mfe.html
│   └── ...
│
├── temp_uploads/                       臨時上傳
│
├── broker_positions.db                 SQLite 本地緩存
│
├── 文檔/
│   ├── SYSTEM_ARCHITECTURE.md          ← 本文件
│   ├── SCHWAB_OAUTH_FIX_PLAN.md       本週計劃
│   ├── SCHWAB_QUICK_REFERENCE.md      快速參考
│   ├── TODO.md                         待做清單
│   ├── README.md                       專案介紹
│   └── ...
│
└── 測試/
    ├── test_strategy.csv               樣本數據
    └── test_flask.py                   單元測試

```

---

## 🔌 API 端點總覽

### 交易管理（已完成）

| 端點 | 方法 | 說明 | 狀態 |
|------|------|------|------|
| `/api/trades/open` | GET | 未平倉交易 | ✅ |
| `/api/trades/realized` | GET | 已平倉交易 | ✅ |

### 投資組合（已完成）

| 端點 | 方法 | 說明 | 狀態 |
|------|------|------|------|
| `/api/ytd-returns` | GET | 年初至今回報 | ✅ |
| `/api/portfolio-chart-data` | GET | 淨值曲線 | ✅ |
| `/api/positions-summary` | GET | 持倉摘要 | ✅ |

### 市場數據（已完成）

| 端點 | 方法 | 說明 | 狀態 |
|------|------|------|------|
| `/api/market-indices` | GET | 全球股市指數 | ✅ |
| `/api/macro-indicators` | GET | 宏觀經濟指標 | ✅ |
| `/api/yahoo-proxy` | GET | 實時股價代理 | ✅ |

### 交易策略（已完成）

| 端點 | 方法 | 說明 | 狀態 |
|------|------|------|------|
| `/api/strategies` | GET | 策略列表 | ✅ |

### Schwab 集成（**本週修復**）

| 端點 | 方法 | 說明 | 狀態 | ETA |
|------|------|------|------|-----|
| `/api/schwab/token-status` | GET | Token 驗證 | 🔧 | 4/8 |
| `/api/schwab-account-summary` | GET | 帳戶摘要 | 🔧 | 4/9 |
| `/api/schwab/sync-positions` | POST | 持倉同步 | 🔧 | 4/10 |
| `/api/schwab/sync-to-sheets` | POST | Sheets 寫回 | 🔧 | 4/11 |

### IB 集成（4 月後）

| 端點 | 方法 | 說明 | 狀態 | ETA |
|------|------|------|------|-----|
| `/api/query-ib` | GET | 查詢帳戶 | ❌ | 4/20 |
| `/api/ib-sync` | POST | 同步持倉 | ❌ | 4/20 |

### 元大集成（4 月後）

| 端點 | 方法 | 說明 | 狀態 | ETA |
|------|------|------|------|-----|
| `/api/sync-yuanta` | POST | 同步持倉 | ❌ | 4/25 |

---

## 💾 數據庫架構

### broker_positions（持倉表）
```sql
CREATE TABLE broker_positions (
  id INTEGER PRIMARY KEY,
  symbol TEXT,           -- AAPL, 2330.TW
  position REAL,         -- 數量
  avgCost REAL,          -- 平均成本
  marketPrice REAL,      -- 當前價格
  unrealizedPNL REAL,    -- 未實現損益
  broker TEXT,           -- schwab, ib, yuanta
  currency TEXT,         -- USD, TWD
  strategy TEXT,         -- 策略名稱
  notes TEXT,            -- 備註
  synced_at DATETIME     -- 同步時間
);
```

### realized_trades（已平倉表）
```sql
CREATE TABLE realized_trades (
  id TEXT PRIMARY KEY,
  symbol TEXT,
  direction TEXT,        -- LONG, SHORT
  entry_price REAL,
  exit_price REAL,
  quantity REAL,
  pnl REAL,
  pnl_pct REAL,
  date TEXT,
  exit_date TEXT,
  broker TEXT,
  strategy TEXT,
  status TEXT            -- CLOSED, PARTIAL
);
```

### equity_snapshots（每日權益快照）
```sql
CREATE TABLE equity_snapshots (
  id INTEGER PRIMARY KEY,
  date TEXT UNIQUE,
  ib_mv_usd REAL,        -- IB 市值（USD）
  schwab_mv_usd REAL,    -- Schwab 市值（USD）
  yuanta_mv_twd REAL,    -- 元大 市值（TWD）
  total_mv_twd REAL,     -- 總市值（TWD）
  total_pnl_twd REAL,    -- 總損益（TWD）
  usd_twd_rate REAL      -- 匯率
);
```

### sync_log（同步日誌）
```sql
CREATE TABLE sync_log (
  id INTEGER PRIMARY KEY,
  sync_time DATETIME,
  count INTEGER,         -- 同步數量
  status TEXT            -- SUCCESS, PARTIAL, ERROR
);
```

---

## 🔐 認證與安全

### 環境變數（.env）

```bash
# Schwab OAuth
SCHWAB_CLIENT_ID=xxx
SCHWAB_CLIENT_SECRET=yyy
SCHWAB_REDIRECT_URI=http://127.0.0.1:8787/callback

# Interactive Brokers
IB_ACCOUNT_ID=xxx
IB_API_PORT=7496

# 元大
YUANTA_ACCOUNT=xxx
YUANTA_PASSWORD=yyy

# Google Sheets
GOOGLE_SHEET_KEY=xxx
GOOGLE_CREDENTIALS_JSON=/path/to/creds.json

# 其他
FLASK_ENV=production
DEBUG=false
MAX_UPLOAD_SIZE=104857600  # 100MB
```

### Token 管理

```python
# Token 自動刷新機制
if token_expired():
    new_token = refresh_token(refresh_token_old)
    save_token_to_file(new_token)
```

### CORS 策略

- 所有 `/api/*` 端點允許跨域請求
- 支持 GET, POST, PUT, DELETE, OPTIONS
- 響應頭包含適當的 CORS 標籤

---

## 📊 數據流

### 場景 1：查詢 Schwab 持倉

```
1. 用戶訪問 Dashboard → 點擊「Schwab 帳戶」
   ↓
2. 前端發送 GET /api/schwab-account-summary
   ↓
3. 後端檢查 Token 有效性
   ↓
4. 後端調用 Schwab API 獲取帳戶信息
   ↓
5. 後端返回 JSON { accounts: [...], updated: ... }
   ↓
6. 前端解析 JSON，更新 UI 顯示帳戶列表
```

### 場景 2：同步持倉到本地

```
1. 用戶點擊「同步持倉」按鈕
   ↓
2. 前端發送 POST /api/schwab/sync-positions
   ↓
3. 後端從 Schwab API 拉取所有帳戶的持倉
   ↓
4. 後端格式化並寫入 SQLite broker_positions 表
   ↓
5. 後端返回 { status: 'success', positions_synced: 8 }
   ↓
6. 前端顯示「同步完成」提示
```

### 場景 3：Google Sheets 同步

```
1. 用戶點擊「同步到 Sheets」
   ↓
2. 前端發送 POST /api/schwab/sync-to-sheets
   ↓
3. 後端從 SQLite 讀取所有持倉
   ↓
4. 後端調用 Google Sheets API 更新 positions 表
   ↓
5. 後端返回 { status: 'success', rows_written: 12 }
   ↓
6. 用戶可在 Google Sheets 中看到最新數據
```

---

## 🚀 部署架構

### 開發環境（本地）

```
localhost:9000
├── Flask 開發服務器
├── SQLite 本地數據庫
├── .env 本地配置
└── Hot reload 開啟
```

### 生產環境（建議）

```
production.example.com
├── Gunicorn / uWSGI (WSGI 服務器)
├── Nginx (反向代理)
├── PostgreSQL / MySQL (生產數據庫)
├── Redis (快取層)
├── SSL 證書
└── 定期備份
```

---

## 📈 性能指標

### 當前性能

| 指標 | 值 | 說明 |
|------|-----|------|
| 前端加載時間 | < 2s | 首頁加載 |
| API 响應時間 | < 500ms | 平均 |
| 數據庫查詢 | < 100ms | SQLite 查詢 |
| 最大並發 | 50 | 開發環境 |

### 優化空間

- [ ] 前端 Code Splitting（減少 HTML 大小）
- [ ] API 響應快取（Redis）
- [ ] 數據庫連接池
- [ ] 異步任務隊列（Celery）
- [ ] CDN 分發靜態資源

---

## 🔄 整體時間表

### 第 1 週（4/7-4/13）- P0 Schwab 修復

```
4/7  計劃確認
4/8  Token 系統 ✅
4/9  帳戶查詢 ✅
4/10 持倉同步 ✅
4/11 Sheets 寫回 ✅
4/12 測試驗證 ✅
4/13 文檔完成 ✅
```

### 第 2 週（4/14-4/20）- P1 IB 集成

```
4/14 環境準備
4/15 IBPy 連接
4/17 帳戶查詢
4/19 持倉同步
4/20 測試完成
```

### 第 3 週（4/21-4/27）- 元大集成

```
4/21 API 認證
4/23 帳戶查詢
4/25 持倉同步
4/27 測試完成
```

### 第 4 週（4/28-5/4）- 統一整合

```
4/28 多經紀商儀表板
4/30 定期同步排程
5/2  實時警報系統
5/4  性能優化完成
```

---

## ✅ 完成標準

### 代碼質量
- [ ] 所有函數都有文檔字符串
- [ ] 異常處理覆蓋率 > 95%
- [ ] 無已知的內存泄漏
- [ ] 代碼符合 PEP 8 規範

### 功能完整性
- [ ] 所有列出的 API 端點都實現
- [ ] 所有數據庫表都正確設計
- [ ] CORS、認證、授權都完善
- [ ] 錯誤消息清晰有用

### 測試覆蓋
- [ ] 單元測試 > 80%
- [ ] 集成測試覆蓋主流程
- [ ] 壓力測試通過（100 併發）
- [ ] 安全測試（無 SQL 注入、XSS）

### 文檔完善
- [ ] API 文檔完整
- [ ] 部署指南清晰
- [ ] 故障排除指南完善
- [ ] 維護者註解充分

---

## 🎓 技術棧

### 前端
- HTML5 + CSS3（原生，無框架）
- 微框架 + 原生 JavaScript
- Chart.js（圖表庫）

### 後端
- Python 3.7+
- Flask（輕量級框架）
- SQLite（本地緩存）

### 外部服務
- Schwab OAuth 2.0 API
- Interactive Brokers API
- 元大 REST API
- Google Sheets API
- Yahoo Finance / yfinance
- FRED API

### 工具
- Git（版本控制）
- Docker（可選，部署）
- Gunicorn/uWSGI（生產服務器）
- Nginx（反向代理）

---

## 📞 支援與維護

### 問題報告
1. 查看 `TODO.md`（已知問題）
2. 查看 `SCHWAB_OAUTH_FIX_PLAN.md`（故障排除）
3. 檢查後端日誌（Flask 控制台）
4. 檢查 JavaScript 控制台（前端日誌）

### 定期維護
- 每週檢查 API 可用性
- 每月輪換 Token（Schwab/IB）
- 每月備份數據庫
- 每季度更新依賴

---

## 🎉 下一步

優先順序：
1. **立即**（4/7-4/13）：完成 Schwab OAuth 修復
2. **短期**（4/14-4/27）：IB + 元大 集成
3. **中期**（5 月）：性能優化 + 定期同步
4. **長期**（6 月+）：高級功能 + AI 輔助

---

**文檔版本**：v1.0  
**最後更新**：2026-04-07  
**維護者**：Krystal  
**狀態**：📋 規劃完成，待實施
