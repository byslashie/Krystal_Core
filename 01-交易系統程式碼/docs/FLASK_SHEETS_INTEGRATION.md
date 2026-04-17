# 🚀 Flask + Google Sheets 整合完成指南

**更新時間**: 2026-03-04
**狀態**: ✅ 已完成實裝

---

## 📋 概覽

已成功完成以下整合：

1. ✅ **Google Sheets 連接** - Flask 儀表板直接讀取 Sheets 數據
2. ✅ **Schwab OAuth 頁面** - `/schwab` 專頁用於帳戶授權
3. ✅ **儀表板導航更新** - 添加 Schwab 鏈接到主導航

---

## 🔧 安裝與配置

### 1️⃣ 檢查環境配置

已自動更新 `.env` 文件：

```bash
# Google Sheets 配置
GOOGLE_SHEET_KEY=1zpehl1bAZitFiQqMg7IcGWsPQxdhnQDhAeNtRvxzwn8
GOOGLE_SHEET_NAME=實盤交易管理
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
DISABLE_SHEETS=0  # 設為 1 可跳過 Sheets 連線

# Schwab OAuth 配置（待審核）
# SCHWAB_CLIENT_ID=...
# SCHWAB_CLIENT_SECRET=...
# SCHWAB_REDIRECT_URI=http://localhost:5000/schwab/callback
```

### 2️⃣ 確保有 credentials.json

確保你在項目根目錄有 `credentials.json`（Google Service Account）：

```bash
# 如果沒有，需要：
# 1. 去 Google Cloud Console 建立 Service Account
# 2. 下載 JSON 鑰匙文件
# 3. 複製到項目根目錄
```

### 3️⃣ 啟動 Flask 應用

```bash
# 進入項目目錄
cd "g:/我的雲端硬碟/Krystal_AI_Trading_System"

# 安裝依賴（如果還沒安裝）
pip install flask pandas numpy gspread google-auth-oauthlib python-dotenv

# 啟動 Flask
python app_html_flask.py
```

訪問：**http://localhost:5000**

---

## 🎯 功能詳解

### 📊 儀表板首頁

| 功能 | 數據來源 | 優先級 |
|------|--------|--------|
| **總資產** | `broker_snapshot` (Google Sheets) | 🥇 |
| **年度報酬** | `daily_nav` 表 (Google Sheets) | 🥇 |
| **Sharpe 比率** | `daily_nav` 表 (Google Sheets) | 🥇 |
| **最大回撤** | `daily_nav` 表 (Google Sheets) | 🥇 |
| **持倉列表** | `broker_positions` (Google Sheets) | 🥇 |
| **策略清單** | `strategies` 表 (Google Sheets) | 🥇 |

**備選方案**：如果 Sheets 讀取失敗，自動降級到模擬數據。

---

### 🔐 Schwab 專頁 (`/schwab`)

#### 功能特性

| 功能 | 說明 |
|------|------|
| **連接狀態** | 實時顯示 OAuth 連接狀態 |
| **授權按鈕** | 點擊後跳轉到 Schwab OAuth 登入 |
| **回調處理** | `/schwab/callback` 自動捕獲授權碼 |
| **Token 管理** | 自動存儲在 `secrets/schwab_token.json` |

#### 頁面構成

```html
┌─────────────────────────────┐
│  🏦 Schwab 帳戶連接         │
│  授權 Schwab API...          │
└─────────────────────────────┘

┌─────────────────────────────┐
│  狀態: ✗ 未連接              │
└─────────────────────────────┘

┌─────────────────────────────┐
│  [🔗 連接 Schwab 帳戶]       │  ← 點擊開始 OAuth
│  授權後系統可以:             │
│  • 實時監控帳戶資金          │
│  • 執行自動化交易            │
│  • 同步成交紀錄              │
└─────────────────────────────┘

┌─────────────────────────────┐
│  🎯 Schwab 整合功能          │
│  💰 實時帳戶監控             │
│  📈 自動化交易執行           │
│  📊 成交紀錄同步             │
│  🔒 安全授權                 │
└─────────────────────────────┘
```

---

## 📡 API 端點清單

### 儀表板相關

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/metrics` | GET | 獲取關鍵績效指標（總資產、年報酬、Sharpe 等） |
| `/api/holdings` | GET | 獲取持倉列表 |
| `/api/strategies` | GET | 獲取所有策略 |
| `/api/trades/<strategy>` | GET | 獲取特定策略的交易 |
| `/api/nav/<strategy>` | GET | 獲取策略的 NAV 數據 |
| `/api/chart-data` | GET | 獲取圖表數據（價格走勢） |

### Schwab 相關

| 端點 | 方法 | 說明 |
|------|------|------|
| `/schwab` | GET | Schwab 連接頁面 |
| `/api/schwab/status` | GET | 查詢連接狀態 |
| `/api/schwab/auth-url` | GET | 生成 OAuth 授權 URL |
| `/schwab/callback` | GET | OAuth 回調端點 |

### 系統相關

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/status` | GET | 系統整體狀態 |
| `/api/upload-csv` | POST | 上傳 CSV 策略文件 |

---

## 🔄 數據流程

### 儀表板載入流程

```
1. 用戶訪問 http://localhost:5000
   ↓
2. 加載 dashboard.html
   ↓
3. JavaScript 調用 API 端點：
   • /api/metrics      → 獲取指標卡片數據
   • /api/holdings     → 獲取持倉表格
   • /api/strategies   → 獲取策略列表
   • /api/chart-data   → 獲取圖表數據
   ↓
4. 每個 API 優先嘗試讀取 Google Sheets：
   • 成功 → 返回真實數據
   • 失敗 → 降級到模擬數據或空列表
   ↓
5. 前端渲染數據到頁面
```

### Schwab 授權流程

```
1. 用戶點擊 "🔗 連接 Schwab 帳戶"
   ↓
2. 調用 /api/schwab/auth-url 生成授權 URL
   ↓
3. 跳轉到 Schwab OAuth 登入頁面
   ↓
4. 用戶輸入帳號密碼，授予權限
   ↓
5. Schwab 重定向回 /schwab/callback?code=XXX&state=krystal
   ↓
6. 交換 code 為 access_token（待實裝）
   ↓
7. 存儲 token 到 secrets/schwab_token.json
   ↓
8. 重定向回 /schwab，顯示 "✓ 已連接"
```

---

## ⚠️ 已知限制與待辦

### ✅ 已完成

- [x] Google Sheets 數據讀取集成
- [x] Schwab OAuth 授權頁面
- [x] Schwab 連接狀態檢查
- [x] 導航菜單更新

### ⏳ 待實裝

- [ ] Schwab OAuth code → token 交換邏輯
- [ ] Token 刷新機制
- [ ] 斷開連接功能
- [ ] Schwab API 調用（帳戶、持倉、訂單）
- [ ] 自動同步 Schwab 數據到 Google Sheets

### 📋 常見問題

**Q: 為什麼儀表板顯示模擬數據？**
A: 通常是 Google Sheets 連線失敗。檢查：
- `credentials.json` 是否存在
- `GOOGLE_SHEET_KEY` 是否正確
- 網路連接是否正常
- 設定 `DISABLE_SHEETS=0` 以查看詳細日誌

**Q: Schwab 連接一直顯示"未連接"？**
A: 這是正常的，因為 Schwab API 還未正式審核通過。需要：
- 從 Schwab 獲得 `client_id` 和 `client_secret`
- 在 `.env` 配置這些憑證
- 完成 code → token 交換邏輯

**Q: 如何查看詳細日誌？**
A: Flask 會在控制台輸出日誌：
```bash
INFO:__main__:GET /api/metrics
INFO:__main__:從 Sheets 讀取指標失敗: ...
```

---

## 🛠️ 調試與開發

### 查看 Google Sheets 原始數據

```python
from sheets_utils import read_sheet

# 讀取 daily_nav 表
df = read_sheet('daily_nav')
print(df.head())

# 讀取 strategies 表
df = read_sheet('strategies')
print(df.to_dict('records'))
```

### 在本地測試 API

```bash
# 測試 /api/metrics
curl http://localhost:5000/api/metrics

# 測試 /api/schwab/status
curl http://localhost:5000/api/schwab/status

# 測試 /api/holdings
curl http://localhost:5000/api/holdings
```

### 啟用詳細日誌

修改 `app_html_flask.py` 第 32 行：

```python
logging.basicConfig(
    level=logging.DEBUG,  # 改為 DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

## 📁 新增文件清單

| 檔案 | 說明 |
|------|------|
| `.env` | 更新 - 添加 Google Sheets & Schwab 配置 |
| `app_html_flask.py` | 更新 - Sheets 集成 + Schwab 路由 |
| `templates/schwab.html` | 新建 - Schwab 授權頁面 |
| `templates/dashboard.html` | 更新 - 導航菜單 |

---

## 🚀 下一步

### 短期（1-2 周）
1. 從 Schwab 申請 API 存取權限
2. 實裝 OAuth code → token 交換邏輯
3. 測試實際 Schwab API 調用

### 中期（2-4 周）
1. 完成 Schwab 帳戶、持倉、訂單查詢
2. 自動同步 Schwab 數據到 Google Sheets
3. 集成 Schwab 成交紀錄到交易主表

### 長期（1-3 月）
1. 實現 Schwab 自動下單邏輯
2. 跨券商（IB + 元大 + Schwab）帳戶聚合
3. 實時風控和風險監控

---

## 📞 支持

如有問題，請參考：
- `FLASK_SETUP_GUIDE.md` - Flask 基礎配置
- `MIGRATION_TO_V3_1.md` - Google Sheets v3.1 結構
- `app_html_flask.py` 代碼註釋
