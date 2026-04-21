# 📋 Dashboard v8 - 後端完整需求說明書

**文檔日期**：2026-04-07  
**範圍**：App 層 + 數據層 + 外部集成  
**狀態**：規範版本 1.0

---

## 🎯 後端的三大任務

### 1. 數據聚合
```
Schwab API  ──┐
IB API      ──┼─→ Flask 應用 → SQLite 本地緩存
元大 API    ──┘
Google Sheets┘
```

### 2. API 服務
```
前端 index.html → REST API 請求 → Flask 應用 → 返回 JSON
```

### 3. 實時同步
```
經紀商持倉 → 定期拉取 → SQLite 更新 → 前端即時顯示
```

---

## 📌 後端必須提供的 API 列表

### 第 1 優先級（已完成 - 4/1）

#### 交易管理
```
GET /api/trades/open
  目的：獲取所有未平倉交易
  返回：[{symbol, quantity, entryPrice, currentPrice, pnl, ...}]
  狀態：✅ 已實現

GET /api/trades/realized
  目的：獲取所有已平倉交易
  返回：[{symbol, entryPrice, exitPrice, pnl, date, ...}]
  狀態：✅ 已實現
```

#### 投資組合
```
GET /api/ytd-returns
  目的：計算年初至今回報
  返回：{ytd_return: 15.5, monthly_returns: {...}}
  狀態：✅ 已實現

GET /api/portfolio-chart-data
  目的：淨值曲線數據
  返回：{dates: [...], equity: [...], drawdown: [...]}
  狀態：✅ 已實現

GET /api/positions-summary
  目的：持倉摘要
  返回：{total_value: 500000, positions_count: 8, ...}
  狀態：✅ 已實現
```

#### 市場數據
```
GET /api/market-indices
  目的：全球股市指數
  返回：{indices: [{name, symbol, value, change%},...]}
  狀態：✅ 已實現

GET /api/macro-indicators
  目的：經濟指標（利率、失業率、GDP 等）
  返回：{indicators: {fed_rate, cpi, unemployment, ...}}
  狀態：✅ 已實現

GET /api/yahoo-proxy?symbol=AAPL
  目的：實時股價代理
  返回：{symbol, price, change%, volume}
  狀態：✅ 已實現
```

#### 交易策略
```
GET /api/strategies
  目的：策略列表及績效
  返回：[{name, type, win_rate, sharpe, mdd, ...}]
  狀態：✅ 已實現
```

---

### 第 2 優先級（本週修復 - 4/7-4/13）

#### Schwab 經紀商集成 🔧 待完成

```
1. GET /api/schwab/token-status
   目的：檢查 Token 有效性
   返回：{status: 'valid'|'expired'|'invalid', message: '...'}
   需求：
     - 讀取 .secrets/schwab_token.json
     - 檢查過期時間
     - 如果過期，自動刷新
     - 返回 Token 狀態
   狀態：🔧 app.py 已有 Stub，待實現真實邏輯

2. GET /api/schwab-account-summary
   目的：帳戶摘要
   返回：{
     accounts: [
       {
         accountNumber: '123456789',
         accountHash: 'abc123...',
         liquidationValue: 50000,
         cashBalance: 5000,
         positions_count: 8
       }
     ]
   }
   需求：
     - 驗證 Token
     - 調用 Schwab API 獲取帳戶列表
     - 調用 Schwab API 獲取各帳戶詳情
     - 格式化並返回
   狀態：🔧 待實現

3. POST /api/schwab/sync-positions
   目的：同步 Schwab 持倉到本地 SQLite
   返回：{status: 'success', positions_synced: 8}
   需求：
     - 驗證 Token
     - 獲取所有帳戶的持倉
     - 格式化（symbol, quantity, price, pnl 等）
     - 寫入 SQLite broker_positions 表
     - 返回同步數量
   狀態：🔧 待實現

4. POST /api/schwab/sync-to-sheets
   目的：將 Schwab 持倉寫回 Google Sheets
   返回：{status: 'success', rows_written: 8, sheet: 'positions'}
   需求：
     - 先執行 /api/schwab/sync-positions
     - 讀取 SQLite 中 broker='schwab' 的所有持倉
     - 調用 Google Sheets API 寫入 positions 表
     - 返回寫入行數
   狀態：🔧 待實現
```

**完成期限**：2026-04-11

---

### 第 3 優先級（后續 - 4/14+）

#### IB 經紀商集成 ❌ 待實現

```
1. GET /api/query-ib
   目的：查詢 IB 帳戶
   返回：{accounts: [{accountId, equity, cash, ...}]}
   需求：
     - IBPy 連接
     - 帳戶查詢
   預計時間：4-5 小時
   ETA：4/20

2. POST /api/ib-sync
   目的：同步 IB 持倉
   返回：{status: 'success', positions_synced: N}
   需求：
     - 同步邏輯
     - 格式化
   預計時間：4-5 小時
   ETA：4/20
```

#### 元大經紀商集成 ❌ 待實現

```
1. POST /api/sync-yuanta
   目的：同步元大持倉
   返回：{status: 'success', positions_synced: N}
   需求：
     - API 認證
     - 帳戶查詢
     - 持倉同步
   預計時間：3-4 小時
   ETA：4/25
```

---

## 🗄️ 數據庫架構要求

### broker_positions 表
```sql
CREATE TABLE broker_positions (
  id INTEGER PRIMARY KEY,
  symbol TEXT NOT NULL,          -- AAPL, 2330.TW
  position REAL,                 -- 數量
  avgCost REAL,                  -- 平均成本
  marketPrice REAL,              -- 當前市價
  unrealizedPNL REAL,            -- 未實現損益
  broker TEXT,                   -- schwab, ib, yuanta
  currency TEXT,                 -- USD, TWD, JPY
  strategy TEXT,                 -- 策略名稱（可選）
  notes TEXT,                    -- 備註（可選）
  timestamp DATETIME,            -- 數據時間戳
  synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INDEX: broker, symbol, synced_at (用於快速查詢)
```

### realized_trades 表
```sql
CREATE TABLE realized_trades (
  id TEXT PRIMARY KEY,
  symbol TEXT,
  direction TEXT,               -- LONG, SHORT
  entry_price REAL,
  exit_price REAL,
  quantity REAL,
  pnl REAL,
  pnl_pct REAL,
  date TEXT,                    -- YYYY-MM-DD
  exit_date TEXT,
  broker TEXT,                  -- schwab, ib, yuanta
  strategy TEXT,
  status TEXT,                  -- CLOSED, PARTIAL
  synced_at DATETIME
);
```

### equity_snapshots 表
```sql
CREATE TABLE equity_snapshots (
  id INTEGER PRIMARY KEY,
  date TEXT NOT NULL UNIQUE,    -- YYYY-MM-DD
  ib_mv_usd REAL DEFAULT 0,     -- IB 市值（USD）
  schwab_mv_usd REAL DEFAULT 0, -- Schwab 市值（USD）
  yuanta_mv_twd REAL DEFAULT 0, -- 元大 市值（TWD）
  total_mv_twd REAL DEFAULT 0,  -- 總市值（TWD）
  total_pnl_twd REAL DEFAULT 0, -- 總損益（TWD）
  usd_twd_rate REAL DEFAULT 32, -- 匯率
  notes TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

PURPOSE：用於繪製投資組合淨值曲線
```

### sync_log 表
```sql
CREATE TABLE sync_log (
  id INTEGER PRIMARY KEY,
  sync_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  count INTEGER,               -- 同步數量
  status TEXT                  -- SUCCESS, PARTIAL, ERROR
);

PURPOSE：記錄每次同步操作，用於調試和監控
```

---

## 🔐 安全與認證要求

### Token 管理
```python
# 必須有以下功能：

def get_valid_access_token():
    """
    獲取有效的 access token
    - 檢查本地 token 是否過期
    - 如果過期，自動使用 refresh_token 更新
    - 返回有效的 token
    """

def save_token(token):
    """
    安全地保存 token 到 .secrets/ 目錄
    - 只可由當前用戶讀寫（chmod 600）
    - 絕不提交到 Git
    """

def load_token():
    """
    從 .secrets/ 讀取 token
    """
```

### 環境變數
```
必須的：
  SCHWAB_CLIENT_ID
  SCHWAB_CLIENT_SECRET
  SCHWAB_REDIRECT_URI

可選的：
  IB_ACCOUNT_ID
  IB_API_PORT
  YUANTA_ACCOUNT
  YUANTA_PASSWORD
  GOOGLE_SHEET_KEY
  GOOGLE_CREDENTIALS_JSON
  FLASK_ENV
  DEBUG
```

### CORS 配置
```
- 所有 /api/* 必須支持跨域
- 支持 GET, POST, PUT, DELETE, OPTIONS
- 返回正確的 CORS 頭
```

---

## 📊 API 返回格式標準

### 成功响應（status: 'success'）
```json
{
  "status": "success",
  "data": {...},
  "timestamp": "2026-04-07T15:30:00",
  "message": "操作成功"  // 可選
}
```

### 部分成功（status: 'partial_success'）
```json
{
  "status": "partial_success",
  "data": {...},
  "errors": ["Account 1 sync failed", "..."],
  "timestamp": "2026-04-07T15:30:00"
}
```

### 失敗响應（status: 'error'）
```json
{
  "status": "error",
  "message": "详细的错误信息",
  "code": "ERROR_CODE",
  "timestamp": "2026-04-07T15:30:00"
}
```

---

## ⚠️ 錯誤處理

### 必須捕獲的異常

```python
# 1. Token 異常
if not token:
    return {'status': 'error', 'message': 'Token not configured'}, 401

# 2. API 調用失敗
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
except requests.Timeout:
    return {'status': 'error', 'message': 'API call timeout'}, 504
except requests.HTTPError as e:
    return {'status': 'error', 'message': str(e)}, 502

# 3. 數據庫錯誤
try:
    cursor.execute(sql)
    conn.commit()
except sqlite3.OperationalError:
    return {'status': 'error', 'message': 'Database error'}, 500

# 4. 數據驗證
if not validate_symbol(symbol):
    return {'status': 'error', 'message': 'Invalid symbol'}, 400
```

---

## 🧪 測試要求

### 單元測試
```python
def test_api_trades_open():
    response = client.get('/api/trades/open')
    assert response.status_code == 200
    assert response.json['status'] == 'success'

def test_schwab_token_missing():
    response = client.get('/api/schwab-account-summary')
    assert response.status_code == 401

def test_sync_positions():
    response = client.post('/api/schwab/sync-positions')
    assert response.json['status'] == 'success'
```

### 集成測試
```
1. 啟動 Flask 應用
2. 執行完整的 Schwab OAuth 流程
3. 驗證所有 API 端點都可調用
4. 檢查數據庫中的數據正確性
```

---

## 📈 性能要求

### API 響應時間目標

| 端點 | 目標 | 說明 |
|------|------|------|
| `/api/trades/*` | < 100ms | 本地 SQLite 查詢 |
| `/api/portfolio-chart-data` | < 500ms | 涉及計算 |
| `/api/market-indices` | < 300ms | 外部 API 調用 |
| `/api/schwab-account-summary` | < 2s | Schwab API 調用 |
| `/api/schwab/sync-positions` | < 5s | 同步操作 |

### 併發能力

- 開發環境：支持 50 併發
- 生產環境：支持 500+ 併發（需 Gunicorn/uWSGI）

---

## 📝 日誌記錄要求

每個 API 調用都應記錄：
```
[2026-04-07 15:30:00] INFO  GET /api/trades/open - 200 OK - 45ms
[2026-04-07 15:31:00] INFO  POST /api/schwab/sync-positions - 200 OK - 2.3s
[2026-04-07 15:32:00] ERROR GET /api/schwab-account-summary - 401 Unauthorized - Token expired
```

---

## 🚀 部署要求

### 開發環境
- Python 3.7+
- Flask
- SQLite
- 可選：Virtual Environment

### 生產環境（建議）
- Gunicorn / uWSGI
- Nginx（反向代理）
- PostgreSQL（可選，更可靠的數據庫）
- Redis（可選，快取層）
- SSL 證書

---

## 📋 完成檢查清單

### 第 1 階段（4/1 - 已完成）
- [x] Flask 應用初始化
- [x] SQLite 數據庫設計
- [x] 基本 API 端點（交易、投資組合、市場）
- [x] Google Sheets 框架

### 第 2 階段（4/7-4/13 - 進行中）
- [ ] Schwab OAuth 完整實現
- [ ] Google Sheets 同步功能
- [ ] 錯誤處理完善
- [ ] 日誌記錄完善

### 第 3 階段（4/14-4/27）
- [ ] IB 集成
- [ ] 元大集成
- [ ] 多經紀商統一視圖

### 第 4 階段（5 月+）
- [ ] 性能優化
- [ ] 定期同步排程
- [ ] 實時警報系統

---

## 🎯 驗收標準

後端視為「完成」當且僅當：

1. **所有 P0 API 都實現**
   - ✅ 13 個已完成的端點都可用
   - 🔧 4 個 Schwab 端點都實現

2. **數據庫正常工作**
   - 可以寫入和讀取數據
   - 查詢速度快（< 100ms）

3. **與前端集成完美**
   - 前端 index.html 的所有 API 調用都成功
   - 返回的數據格式與前端期望一致

4. **錯誤處理健全**
   - 沒有 500 錯誤（除非真的有問題）
   - 所有錯誤都有清晰的消息

5. **安全性達標**
   - 敏感信息存儲在 .env 或 .secrets/
   - CORS 配置正確
   - 沒有明顯的安全漏洞

6. **文檔完整**
   - API 文檔清晰
   - 部署說明可行
   - 代碼有適當註解

---

**文檔版本**：1.0  
**最後更新**：2026-04-07  
**維護者**：Krystal  
**狀態**：規範版本
