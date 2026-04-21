# ✅ Dashboard v8 後端完整檢查清單

**日期**：2026-04-07  
**目的**：確保 v8 具備所有必要的後端功能  
**對標**：Dashboard v7 已有的功能

---

## 📋 後端功能清單

### 1️⃣ 核心 Flask 應用

#### 應用初始化 ✅ 已有
- [x] Flask app 創建
- [x] CORS 跨域配置
- [x] 錯誤處理中間件
- [x] 日誌記錄系統
- [x] 環境變數加載（dotenv）

**檔案位置**：`app.py` 第 1-50 行

#### 靜態文件服務
- [x] 主路由 `/` → `index.html`
- [x] 靜態文件路由 `/static/*`
- [x] `*.css` 、`*.js` 服務
- [x] 圖表文件服務 `/charts/*`

**需確認**：
```python
# app.py 應包含
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)
```

---

### 2️⃣ 數據庫系統

#### SQLite 本地緩存 ✅ 已有
- [x] 數據庫初始化
- [x] 表結構設計

**現有表**：
```
✅ broker_positions       (持倉表)
✅ realized_trades        (已平倉交易表)
✅ equity_snapshots       (每日權益快照)
✅ sync_log               (同步日誌)
✅ positions_snapshot     (持倉快照)
```

**需檢查**：
- [ ] 數據庫檔案位置：`.../dashboard_v8/broker_positions.db`
- [ ] 所有表都正確創建
- [ ] 有適當的索引（symbol, broker, date）
- [ ] 自動清理舊快照（> 90 天）

#### 數據庫連接管理
- [x] 連接池配置（可選，開發環境暫無需）
- [x] 連接超時設置
- [x] 異常處理

**檔案位置**：`app.py` 第 144-150 行

---

### 3️⃣ 核心 API 端點

#### A. 交易管理 API ✅ 已有

| 端點 | 狀態 | 檔案位置 |
|------|------|---------|
| `GET /api/trades/open` | ✅ | app.py |
| `GET /api/trades/realized` | ✅ | app.py |

**需驗證**：
```python
# 應返回格式
{
  "status": "success",
  "data": [
    {
      "symbol": "AAPL",
      "position": 100,
      "entryPrice": 150,
      "currentPrice": 155,
      "pnl": 500,
      ...
    }
  ]
}
```

#### B. 投資組合 API ✅ 已有

| 端點 | 狀態 | 說明 |
|------|------|------|
| `GET /api/ytd-returns` | ✅ | 年初至今回報 |
| `GET /api/portfolio-chart-data` | ✅ | 淨值曲線 |
| `GET /api/positions-summary` | ✅ | 持倉摘要 |

**需檢查**：
- [ ] 返回值包含 equity curve 數據
- [ ] 包含月度回報（monthly returns）
- [ ] 包含回撤數據（drawdown）
- [ ] 時間序列正確

#### C. 市場數據 API ✅ 已有

| 端點 | 狀態 | 說明 |
|------|------|------|
| `GET /api/market-indices` | ✅ | 全球股市指數 |
| `GET /api/macro-indicators` | ✅ | 宏觀經濟指標 |
| `GET /api/yahoo-proxy` | ✅ | Yahoo Finance 代理 |

**需檢查**：
- [ ] 支持台股 (2330.TW) 和美股 (AAPL) 查詢
- [ ] 實時價格每 5 分鐘更新
- [ ] 緩存機制正常（避免 API 配額消耗）

#### D. 交易策略 API ✅ 已有

| 端點 | 狀態 | 說明 |
|------|------|------|
| `GET /api/strategies` | ✅ | 策略列表 |

**需檢查**：
- [ ] 返回至少 4 個策略
- [ ] 包含性能指標（Sharpe、勝率等）

---

### 4️⃣ 經紀商集成 API（本週修復）

#### A. Schwab 集成 🔧 待修復

| 端點 | 狀態 | 預期完成 |
|------|------|---------|
| `GET /api/schwab/token-status` | 🔧 | 4/8 |
| `GET /api/schwab-account-summary` | 🔧 | 4/9 |
| `POST /api/schwab/sync-positions` | 🔧 | 4/10 |
| `POST /api/schwab/sync-to-sheets` | 🔧 | 4/11 |

**需檢查清單**：

```python
# ✅ 應該有的程式碼結構

# 1. Token 驗證函數
def get_schwab_token():
    token = load_tokens('.secrets/schwab_token.json')
    if not token or not token.access_token:
        return None
    # 檢查過期並自動刷新
    return token

# 2. API 調用函數
def query_schwab_accounts(access_token):
    # 調用 Schwab API
    # 返回帳戶列表
    pass

# 3. 持倉同步函數
def sync_schwab_positions(access_token):
    # 從 Schwab API 拉取持倉
    # 寫入 SQLite broker_positions 表
    # 返回同步數量
    pass

# 4. Google Sheets 寫回函數
def write_to_sheets(positions):
    # 將持倉數據寫入 Google Sheets
    pass

# 5. API 端點（應該已有）
@app.route('/api/schwab-account-summary', methods=['GET'])
def api_schwab_summary():
    token = get_schwab_token()
    if not token:
        return jsonify({'status': 'error', 'message': 'Token not available'}), 401
    accounts = query_schwab_accounts(token.access_token)
    return jsonify({'status': 'success', 'accounts': accounts})
```

**詳細計劃**：查看 `SCHWAB_OAUTH_FIX_PLAN.md`

#### B. IB 集成 ❌ 待實現（4/14 後）

| 端點 | 狀態 | 預期完成 |
|------|------|---------|
| `GET /api/query-ib` | ❌ | 4/20 |
| `POST /api/ib-sync` | ❌ | 4/20 |

**應實現的功能**：
- [ ] IBPy 連接管理
- [ ] 帳戶查詢
- [ ] 持倉同步
- [ ] 交易歷史查詢

#### C. 元大集成 ❌ 待實現（4/21 後）

| 端點 | 狀態 | 預期完成 |
|------|------|---------|
| `POST /api/sync-yuanta` | ❌ | 4/25 |

**應實現的功能**：
- [ ] API 認證
- [ ] 帳戶查詢
- [ ] 持倉同步

---

### 5️⃣ 文件上傳與處理

#### 文件上傳 API
- [x] `POST /api/upload` — CSV/Excel 上傳
- [x] 文件驗證（大小、類型）
- [x] 臨時文件存儲

**需檢查**：
```python
# app.py 應包含
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
UPLOAD_FOLDER = Path(__file__).parent / 'temp_uploads'

@app.route('/api/upload', methods=['POST'])
def upload_file():
    # 檢查文件
    # 儲存到 temp_uploads
    # 返回文件 ID
    pass
```

#### 圖表生成 API
- [x] `POST /api/generate-charts` — 根據上傳的 CSV 生成圖表
- [x] 圖表存儲到 `/charts` 目錄
- [x] 返回圖表 HTML 連結

---

### 6️⃣ Google Sheets 集成

#### Sheets API 連接 ✅ 應有框架

- [x] Google Sheets API 初始化
- [x] 認證（服務帳戶或 OAuth）
- [x] 讀取 trades 表
- [x] 寫回 positions 表

**需檢查**：

```python
# app.py 應有 Google Sheets 函數
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def get_sheets_client():
    credentials = Credentials.from_service_account_file(
        os.getenv('GOOGLE_CREDENTIALS_JSON')
    )
    return build('sheets', 'v4', credentials=credentials)

def read_trades_from_sheets():
    # 從 Google Sheets 讀取 trades 表
    pass

def write_positions_to_sheets(positions):
    # 寫入 positions 表
    pass
```

---

### 7️⃣ 環境變數與配置

#### .env 檔案 ✅ 應有

```bash
# Schwab OAuth
SCHWAB_CLIENT_ID=
SCHWAB_CLIENT_SECRET=
SCHWAB_REDIRECT_URI=http://127.0.0.1:8787/callback

# IB (待填)
IB_ACCOUNT_ID=
IB_API_PORT=7496

# 元大 (待填)
YUANTA_ACCOUNT=
YUANTA_PASSWORD=

# Google Sheets
GOOGLE_SHEET_KEY=
GOOGLE_CREDENTIALS_JSON=

# Flask
FLASK_ENV=development
DEBUG=True
```

**檢查項**：
- [ ] .env 存在於項目根目錄
- [ ] .env 在 .gitignore 中（絕不提交敏感信息）
- [ ] 所有必需的環境變數都已設置

---

### 8️⃣ 錯誤處理 & 日誌

#### 全局錯誤處理 ✅ 應有

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': '端點不存在'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'status': 'error', 'message': '服務器錯誤'}), 500
```

#### 日誌記錄 ✅ 應有

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
```

**檢查項**：
- [ ] 所有 API 調用都有日誌
- [ ] 錯誤都被捕獲並記錄
- [ ] 日誌文件在 `app.log` 中

---

### 9️⃣ CORS 和安全

#### CORS 配置 ✅ 已有

```python
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

**檢查項**：
- [x] 所有 `/api/*` 都支持跨域
- [x] 支持 OPTIONS 預檢請求
- [x] 返回正確的 CORS 頭

#### 安全頭 ⚠️ 生產時添加

```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

---

### 🔟 性能優化

#### 快取機制 ⚠️ 後期優化

- [ ] API 響應快取（5 分鐘）
- [ ] 數據庫查詢快取
- [ ] CDN 快取靜態資源

#### 響應時間目標

| 端點 | 目標 | 現狀 |
|------|------|------|
| `/api/trades/open` | < 100ms | ? |
| `/api/portfolio-chart-data` | < 500ms | ? |
| `/api/schwab-account-summary` | < 2s | ? |
| `/api/market-indices` | < 300ms | ? |

---

## 🎯 驗證步驟

### 第一步：靜態檢查
```bash
# 檢查 app.py 是否包含所有必需的導入
grep -c "from flask import" app.py
grep -c "def api_" app.py  # 應該 ≥ 13 個 API 函數

# 檢查所有端點
grep -n "@app.route" app.py
```

### 第二步：動態測試
```bash
# 啟動 Flask
python app.py

# 在另一個終端測試各端點
curl http://localhost:9000/api/trades/open
curl http://localhost:9000/api/market-indices
curl http://localhost:9000/api/schwab-account-summary  # 應失敗（無 token）
```

### 第三步：集成測試
```bash
# 運行測試文件（如果有）
python -m pytest test_*.py -v

# 或手動測試
python test_flask.py
```

---

## 📊 進度追蹤表

### 已完成（4/1）

| 功能 | 完成度 | 檢查 |
|------|--------|------|
| Flask 應用 | 100% | ✅ |
| SQLite 數據庫 | 100% | ✅ |
| 交易 API | 100% | ✅ |
| 投資組合 API | 100% | ✅ |
| 市場數據 API | 100% | ✅ |
| 策略 API | 100% | ✅ |

### 進行中（4/7-4/13）

| 功能 | 進度 | ETA |
|------|------|-----|
| Schwab OAuth | 🔧 30% | 4/11 |
| Google Sheets 同步 | 🔧 20% | 4/12 |

### 待實現（4/14+）

| 功能 | 進度 | ETA |
|------|------|-----|
| IB 集成 | ❌ 0% | 4/20 |
| 元大集成 | ❌ 0% | 4/25 |

---

## 🚀 最終檢查清單

完成以下項目時視為「後端完整」：

### 核心功能
- [x] Flask 應用正常運行
- [x] SQLite 數據庫正常
- [x] 所有已完成的 API 都可調用
- [ ] Schwab OAuth 完整實現
- [ ] Google Sheets 同步正常
- [ ] 錯誤處理覆蓋所有情況

### 集成
- [ ] 與前端 index.html 集成完美
- [ ] API 返回格式與前端期望一致
- [ ] CORS 配置正確

### 文檔
- [ ] API 文檔完整
- [ ] 部署文檔清晰
- [ ] 代碼有適當註解

### 測試
- [ ] 所有端點都測試過
- [ ] 邊界情況都考慮過
- [ ] 錯誤消息清晰

---

**版本**：v1.0  
**最後更新**：2026-04-07  
**維護者**：Krystal  
**狀態**：進行中
