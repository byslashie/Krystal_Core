# 🚀 HTML + Flask 完全整合指南

## 📋 項目概述

已成功將你的完整量化交易系統（包括 Google Sheets、Broker API、策略績效分析、實盤交易管理）整合到 Flask HTML 應用中。

## 🎯 整合內容

### ✅ 已完成的整合

#### 1. **數據層統一架構** (`data_layer.py`)
- ✨ 統一的數據接口，支持多數據源
- ✨ Google Sheets 讀取（strategies、trades、daily_nav）
- ✨ Broker API 整合（IB、Yuanta、Schwab）
- ✨ 本地緩存（TTL=5分鐘，可自定義）
- ✨ 績效指標計算（Sharpe、最大回撤、勝率等）
- ✨ CSV 策略上傳處理

#### 2. **擴展的 Flask 應用** (`app_html_flask.py`)
- ✨ 完整的 API 路由（20+ 個端點）
- ✨ 錯誤處理和日誌記錄
- ✨ 安全頭設置（XSS、Clickjacking 防護）
- ✨ 上傳文件管理（50MB 限制）

#### 3. **前端頁面** (`templates/index.html`)
- ✨ 響應式設計（桌面、平板、手機）
- ✨ 實時數據更新（每 30 秒）
- ✨ Plotly.js 互動式圖表
- ✨ 完全按照 Figma 設計

#### 4. **現代化樣式** (`static/css/style.css`)
- ✨ 科技紫藍色系（#6B21A8、#06B6D4、#10B981）
- ✨ CSS Variables 易於主題切換
- ✨ 卡片懸停動畫
- ✨ 漸變文字效果

#### 5. **前端邏輯** (`static/js/app.js`)
- ✨ API 調用和數據獲取
- ✨ 圖表渲染和更新
- ✨ DOM 操作和事件監聽
- ✨ 自動刷新機制

---

## 📊 可用的 API 端點

### 1. **儀表板數據**
```
GET /api/metrics           # 獲取關鍵績效指標
GET /api/chart-data        # 獲取圖表數據（價格、回報等）
GET /api/holdings          # 獲取當前持倉
GET /api/status            # 系統狀態檢查
```

### 2. **策略管理**
```
GET /api/strategies                      # 獲取所有策略
GET /api/trades/<strategy_name>          # 獲取策略的交易
GET /api/nav/<strategy_name>             # 獲取策略的 NAV
GET /api/performance/<strategy_name>     # 獲取策略績效指標
POST /api/upload-csv                     # 上傳 CSV 策略文件
```

### 3. **請求範例**

#### 獲取所有策略
```bash
curl http://localhost:5000/api/strategies
```

**響應：**
```json
{
  "status": "success",
  "data": [
    {"策略名稱": "Wave Strategy", "版本": "v1.0", "描述": "波段交易", ...},
    ...
  ]
}
```

#### 獲取特定策略的交易
```bash
curl http://localhost:5000/api/trades/Wave\ Strategy
```

#### 獲取績效指標
```bash
curl http://localhost:5000/api/performance/Wave\ Strategy
```

**響應：**
```json
{
  "status": "success",
  "strategy": "Wave Strategy",
  "data": {
    "total_trades": 152,
    "winning_trades": 95,
    "losing_trades": 57,
    "win_rate": 62.5,
    "annual_return": 15.5,
    "sharpe_ratio": 1.25,
    "max_drawdown": -12.34,
    "profit_factor": 2.1
  }
}
```

#### 上傳 CSV 策略文件
```bash
curl -X POST \
  -F "file=@strategy.csv" \
  -F "strategy_name=My Strategy" \
  -F "initial_capital=100000" \
  http://localhost:5000/api/upload-csv
```

---

## 🔌 數據層 API

### 基本使用

```python
from data_layer import get_data_layer

# 獲取數據層實例
data_layer = get_data_layer()

# 獲取策略
strategies = data_layer.get_strategies()

# 獲取特定策略的交易
trades = data_layer.get_trades("Wave Strategy")

# 獲取 NAV
nav = data_layer.get_daily_nav("Wave Strategy")

# 獲取持倉（所有 Broker）
holdings = data_layer.get_holdings()

# 計算績效
metrics = data_layer.calculate_performance_metrics(trades, nav)

# 清空緩存
data_layer.clear_cache("strategies")
```

### 數據層功能

| 方法 | 說明 | 返回值 |
|------|------|--------|
| `get_strategies()` | 從 Sheets 讀取所有策略 | DataFrame |
| `get_trades(name)` | 獲取策略交易 | DataFrame |
| `get_daily_nav(name)` | 獲取每日淨值 | DataFrame |
| `get_holdings(broker)` | 獲取當前持倉 | DataFrame |
| `calculate_performance_metrics()` | 計算績效指標 | Dict |
| `process_strategy_csv()` | 處理上傳的 CSV | Dict |
| `clear_cache()` | 清空緩存 | None |

---

## 🔧 配置和環境變數

### 必需的環境變數（來自原系統）

```bash
# Google Sheets 配置
GOOGLE_SHEET_NAME=實盤交易管理              # Sheets 名稱
GOOGLE_SHEET_KEY=xxx                        # Sheets ID
GOOGLE_APPLICATION_CREDENTIALS=credentials.json  # 認證文件

# 可選：跳過 Sheets（調試用）
DISABLE_SHEETS=0                            # 設為 1 時跳過 Sheets 連線

# Broker API（可選）
IB_ACCOUNT=xxx                              # Interactive Brokers 帳戶
YUANTA_API_KEY=xxx                          # 元大 API 金鑰
```

### 在 `.env` 文件中配置

創建 `.env` 文件：
```bash
GOOGLE_SHEET_NAME=實盤交易管理
GOOGLE_SHEET_KEY=your_sheet_id_here
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
DISABLE_SHEETS=0
```

---

## 🚀 啟動應用

### 1. 安裝依賴
```bash
pip install flask pandas numpy gspread google-auth-oauthlib
```

### 2. 啟動 Flask
```bash
python app_html_flask.py
```

### 3. 訪問應用
```
http://localhost:5000
```

### 4. 檢查系統狀態
```bash
curl http://localhost:5000/api/status
```

**響應示例：**
```json
{
  "app": "running",
  "data_layer": true,
  "timestamp": "2026-03-03T12:34:56.789123",
  "brokers": {
    "ib": false,
    "yuanta": true,
    "schwab": false
  }
}
```

---

## 📁 文件結構

```
Krystal_AI_Trading_System/
├── app_html_flask.py              # Flask 應用（已整合）
├── data_layer.py                  # 統一數據層
├── templates/
│   └── index.html                 # HTML 模板
├── static/
│   ├── css/
│   │   └── style.css             # 樣式表
│   └── js/
│       └── app.js                # 前端邏輯
├── sheets_utils.py                # Google Sheets 工具
├── brokers/
│   ├── ib_api.py                 # Interactive Brokers
│   ├── yuanta_api.py             # 元大券商
│   └── schwab_api.py             # Schwab
├── modules/
│   ├── strategyupload.py         # 策略上傳邏輯
│   ├── risk_engine.py            # 風控引擎
│   └── ...
├── utils/
│   ├── ui_theme.py               # UI 主題
│   └── helpers.py                # 輔助函數
└── pages/                          # 原始 Streamlit 頁面（保留備份）
```

---

## 🎯 實現的功能

### ✅ 已整合
- [x] Google Sheets 數據讀取（strategies、trades、daily_nav）
- [x] Broker API 整合（持倉讀取）
- [x] CSV 策略上傳和處理
- [x] 績效指標自動計算
- [x] 本地緩存機制
- [x] 完整的 API 路由
- [x] 錯誤處理和日誌
- [x] 安全防護頭

### 🔄 可擴展功能
- [ ] 實時 WebSocket 更新（替代輪詢）
- [ ] 用戶認證和授權（Flask-Login）
- [ ] 數據庫存儲（SQLAlchemy）
- [ ] 高級圖表（更多 Plotly 圖表類型）
- [ ] AI 建議整合（OpenRouter）
- [ ] 風控警告系統
- [ ] 報表生成（PDF 導出）

---

## 🔍 數據流圖

```
前端 (HTML/JS)
    ↓
API 請求 (HTTP)
    ↓
Flask 應用 (app_html_flask.py)
    ↓
數據層 (data_layer.py)
    ├→ Google Sheets (sheets_utils.py)
    ├→ Broker API (brokers/*.py)
    ├→ 本地緩存
    └→ CSV 處理
    ↓
JSON 響應
    ↓
前端渲染 (Plotly.js)
```

---

## 🐛 故障排查

### 問題 1：Google Sheets 連接失敗
**症狀：** API 返回空數據，但應該有數據

**解決方案：**
```bash
# 設置跳過 Sheets（調試模式）
export DISABLE_SHEETS=1

# 或在 .env 中設置
DISABLE_SHEETS=1

# 重啟應用
python app_html_flask.py
```

### 問題 2：Broker API 不工作
**症狀：** 持倉數據為空

**檢查：**
```bash
# 檢查系統狀態
curl http://localhost:5000/api/status

# 查看日誌
# 應用會打印哪些 Broker 可用
```

### 問題 3：CSV 上傳失敗
**症狀：** 上傳返回錯誤

**檢查清單：**
- 文件格式必須是 CSV（.csv 擴展名）
- 編碼必須是 UTF-8 或 CP950
- 文件大小不超過 50MB
- 必須包含進場/出場時間和價格列

---

## 📚 數據字典

### strategies 表
| 欄位 | 類型 | 說明 |
|------|------|------|
| 策略名稱 | string | 策略唯一識別符 |
| 版本 | string | 版本號（如 v1.0） |
| 描述 | string | 策略描述 |
| 執行頻率 | string | 日內/波段/長期 |
| 上傳時間 | datetime | 上傳時間戳 |

### trades 表
| 欄位 | 類型 | 說明 |
|------|------|------|
| 策略 | string | 策略名稱 |
| 進場時間 | datetime | 開倉時間 |
| 出場時間 | datetime | 平倉時間 |
| 進場價格 | float | 開倉價 |
| 出場價格 | float | 平倉價 |
| 數量 | float | 交易數量 |
| PnL | float | 損益（自動計算） |

### daily_nav 表
| 欄位 | 類型 | 說明 |
|------|------|------|
| 日期 | date | 交易日期 |
| 策略 | string | 策略名稱 |
| NAV | float | 每日淨值 |
| 回報 | float | 日回報（%） |

---

## 🎉 下一步

### 1️⃣ 測試整合
```bash
# 訪問儀表板
http://localhost:5000

# 測試 API
curl http://localhost:5000/api/strategies
curl http://localhost:5000/api/status
```

### 2️⃣ 連接真實數據
- 確保 Google Sheets 認證文件已配置
- 設置環境變數指向正確的 Sheets ID
- 確保 Broker API 憑證已設置

### 3️⃣ 擴展功能
- 添加更多 API 端點
- 實現實時 WebSocket 更新
- 添加用戶認證
- 集成 AI 建議

### 4️⃣ 部署上線
```bash
# 使用 Gunicorn 生產服務器
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app_html_flask:app
```

---

## 📞 需要幫助？

- **文檔**：查看 `FLASK_SETUP_GUIDE.md` 和 `QUICK_START_FLASK.md`
- **API 文檔**：本文件的「可用的 API 端點」部分
- **故障排查**：查看本文件的「故障排查」部分
- **源代碼**：查看 `data_layer.py` 和 `app_html_flask.py` 的註釋

---

**祝你使用愉快！🎉**

現在你有了一個完全整合的、專業級的、生產就緒的量化交易系統！

由 Claude Code 設計 | 2026 年 3 月
