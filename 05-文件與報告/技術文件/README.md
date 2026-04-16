# 🚀 Krystal AI × 總經交易決策系統

## 📖 專案簡介

**Krystal AI × 總經交易決策系統**是一套基於總體經濟數據、策略績效、風控邏輯的**量化資金配置系統**，集成多家券商 API、AI 輔助決策與實時儀表板，打造半自動化投資決策流程。

### 核心特性
- ✅ **多券商集成**：Interactive Brokers、元大證券、Schwab（支持實時持倉同步）
- ✅ **AI 決策引擎**：基於 OpenRouter 的 GPT 摘要與決策建議
- ✅ **實時儀表板**：Streamlit 多頁面應用 + Flask 瀏覽器仪表板
- ✅ **Google Sheets 樞紐**：統一資料交換平台（11 個標準分頁）
- ✅ **風控與績效追蹤**：自動計算 Sharpe、MDD、VaR 等指標
- ✅ **跨平台支持**：Mac/Windows 相同開發體驗

---

## 🏗️ 系統架構（四層設計）

系統採用**四層架構**，對應 Google Sheets 的 11 個標準分頁：

```
┌─────────────────────────────────────────────────────┐
│  第一層：情報與總經感知 (Intelligence & Macro)      │
│  ├─ intel_events       (USGS 地震、新聞、油輪事件)  │
│  └─ macro_state        (GDP、PMI、risk_on 開關)     │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  第二層：決策與風控 (Decision & Risk Control)       │
│  ├─ orders_queue       (待執行指令池)               │
│  └─ risk_incidents     (風控攔截日誌)              │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  第三層：交易歸因與績效 (Performance Attribution)  │
│  ├─ strategies         (策略主檔)                   │
│  ├─ trades            (交易主表)                    │
│  └─ daily_nav         (每日淨值表)                  │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  第四層：券商事實與同步 (Broker Sync)              │
│  ├─ broker_snapshot    (帳戶快照)                   │
│  ├─ broker_positions   (即時持倉)                   │
│  ├─ broker_fills       (原始成交紀錄)               │
│  └─ sync_logs         (同步日誌)                    │
└─────────────────────────────────────────────────────┘
```

---

## 📁 專案檔案結構

```
Krystal_AI_Trading_System/
│
├── 📄 主應用程式
│   ├── app.py                           # Streamlit 主應用
│   ├── app2.py                          # 備用應用版本
│   ├── app_simple.py                    # Flask 簡化儀表板
│   └── README.md                        # 本文件
│
├── 📁 pages/                            # Streamlit 多頁面應用
│   ├── 0_🏠_home.py                     # 首頁儀表板
│   ├── 1_💹_實盤交易管理系統.py         # 核心交易管理（105 KB）
│   ├── 2_📁_策略上傳與績效.py           # 策略績效分析（93 KB）
│   ├── 3_📊_多策略績效比較.py           # 多策略對比
│   └── 4_📈_全能策略管理與比較.py       # 全能策略管理
│
├── 📁 brokers/                          # 券商 API 整合層
│   ├── ib_api.py                        # Interactive Brokers API
│   ├── yuanta_api.py                    # 元大證券 API
│   ├── schwab_api.py                    # Schwab API
│   ├── sync_yuanta_positions.py         # 元大持倉同步
│   ├── import_ib_csv_to_broker_fills.py # IB CSV 匯入工具
│   └── ib/                              # IB 專用模組
│       ├── sync_ib_snapshot.py
│       ├── sync_ib_positions.py
│       └── sync_ib_fills.py
│
├── 📁 modules/                          # 核心功能模組
│   ├── strategyupload.py                # 策略上傳邏輯 ✅ 已實作
│   ├── allocator.py                     # 資金分配邏輯 (空)
│   ├── risk_control.py                  # 風控邏輯設定 (空)
│   ├── decision_engine.py               # 自動決策引擎 (空)
│   ├── econ_classifier.py               # 總經分類器 (空)
│   ├── perf_tracker.py                  # 績效追蹤計算 (空)
│   ├── channel_plot.py                  # 預期報酬通道圖 (空)
│   ├── monte_carlo.py                   # Monte Carlo 模擬 (空)
│   ├── gpt_summary.py                   # GPT 摘要模組 (空)
│   └── notifier.py                      # LINE/Obsidian 通知 (空)
│
├── 📁 utils/                            # 工具與輔助函式
│   ├── ui_theme.py                      # UI 主題系統（科技紫藍系）
│   ├── ui_theme_dark.py                 # 暗黑主題
│   ├── ui_theme_modern.py               # 現代主題
│   ├── ui_components_figma.py           # Figma 設計組件
│   ├── helpers.py                       # 通用輔助函式
│   ├── apply_theme_to_pages.py          # 主題應用工具
│   └── theme_switcher.py                # 主題切換器
│
├── 📁 data/                             # 數據輸入與快取
│   ├── strategies/                      # 策略文件存儲
│   ├── Benchmark/                       # 基準數據
│   └── cache/                           # 快取文件（5 分鐘更新）
│
├── 📁 config/                           # 設定檔與權重配置
│
├── 📁 outputs/                          # 輸出與報告
│   ├── logs/                            # 執行日誌
│   └── reports/                         # 視覺化報告與圖表
│
├── 📁 ship_monitoring/                  # 波斯灣油輪監測系統
│   ├── templates/                       # HTML 模板
│   └── ship_tracking_dashboard.py       # 油輪監測主應用
│
├── 📁 intel_engine/                     # 情報引擎（總經感知）
│
├── 📁 templates/                        # Flask HTML 模板
│
├── 📁 static/                           # 靜態資源
│   ├── css/                             # 樣式表
│   └── js/                              # JavaScript 腳本
│
├── 📁 logs/                             # 應用日誌
│
├── 📁 key/                              # 金鑰與認證文件
│
├── 📁 lib/                              # 第三方庫
│   └── 元大CA.pfx                       # 元大數位憑證
│
├── 🔧 環境與配置
│   ├── .env                             # 環境變數配置
│   ├── requirements.txt                 # Python 依賴
│   ├── credentials.json                 # Google OAuth 認證
│   └── .gitignore                       # Git 忽略規則
│
└── 📚 文檔與指南 (30+ MD 檔案)
    ├── MIGRATION_TO_V3_1.md             # Sheets 遷移指南
    ├── QUICK_START_V3_1.md              # 5 分鐘快速啟動
    ├── UI_UX_DESIGN_GUIDE.md            # UI/UX 設計規範
    ├── SHIP_MONITORING_QUICK_START.md   # 油輪監測快速啟動
    ├── FLASK_SHEETS_INTEGRATION.md      # Flask 整合指南
    ├── AUTO_SYNC_QUICK_START.md         # 自動同步快速啟動
    └── ... (其他技術文檔)
```

---

## 🔧 技術棧

| 組件 | 技術 | 說明 |
|------|------|------|
| **UI 框架** | Streamlit | 多頁面應用 + 儀表板 |
| **瀏覽器儀表板** | Flask | 輕量級 Web 應用 |
| **資料處理** | pandas, numpy | 數據轉換與分析 |
| **數據存儲** | Google Sheets | 唯一資料交換樞紐 |
| **券商 API** | IB SDK, 元大 RQ, Schwab | 實時持倉同步 |
| **AI 模型** | OpenRouter API | 5 個免費模型支持 |
| **視覺化** | plotly, matplotlib | 互動式圖表與報告 |
| **認證** | Google OAuth | Google Sheets 連接 |
| **排程** | APScheduler | 自動同步排程 |

---

## 🚀 快速啟動

### 1️⃣ 環境準備

```bash
# 創建虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 2️⃣ 配置環境變數

編輯 `.env` 文件：

```env
# 元大證券配置
YUANTA_ENV=PROD
YUANTA_ACCOUNT=S989C0316437
YUANTA_PASSWORD=your_password
YUANTA_CERT_PATH=/path/to/元大CA.pfx
YUANTA_CERT_PASSWORD=your_cert_password

# Google Sheets 配置
GOOGLE_SHEET_KEY=1zpehl1bAZitFiQqMg7IcGWsPQxdhnQDhAeNtRvxzwn8
GOOGLE_SHEET_NAME=實盤交易管理
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
DISABLE_SHEETS=0

# Schwab OAuth (可選)
# SCHWAB_CLIENT_ID=your_client_id
# SCHWAB_CLIENT_SECRET=your_client_secret
```

### 3️⃣ 啟動應用

#### Streamlit 應用（推薦）
```bash
streamlit run app.py
```
- 多頁面應用：首頁 + 5 個功能頁面
- 實時策略管理、績效比較、交易記錄
- 訪問地址：`http://localhost:8501`

#### Flask 儀表板
```bash
python app_simple.py
```
- 輕量級瀏覽器儀表板
- 展示實時持倉與績效指標
- 訪問地址：`http://localhost:8000`

#### 波斯灣油輪監測（可選）
```bash
cd ship_monitoring
python ship_tracking_dashboard.py
```

---

## 📊 五個 Streamlit 頁面說明

### 🏠 0. 首頁儀表板 (`0_🏠_home.py`)
- 系統狀態概覽
- 關鍵績效指標 (KPI) 卡片
- 實時賬戶快照

### 💹 1. 實盤交易管理系統 (`1_💹_實盤交易管理系統.py`) - **核心功能**
- **持倉管理**：實時持倉展示、風險監控
- **訂單管理**：待執行訂單池、執行記錄
- **交易日誌**：成交記錄、成交成本分析
- **策略配置**：啟用/禁用策略、資金分配
- **風控監控**：虧損警告、曝險限制

### 📁 2. 策略上傳與績效 (`2_📁_策略上傳與績效.py`)
- 上傳策略回測數據（CSV/Excel）
- 自動解析績效指標
- 月度績效分析與視覺化
- 策略排序與篩選

### 📊 3. 多策略績效比較 (`3_📊_多策略績效比較.py`)
- 並列對比多個策略
- 繪製收益曲線、Sharpe 比率對比
- 風險指標儀表板（MDD、勝率等）

### 📈 4. 全能策略管理與比較 (`4_📈_全能策略管理與比較.py`)
- 統一管理所有策略
- 高級篩選與排序
- 導出報告與分析結果

---

## 🔌 券商集成

### Interactive Brokers (IB)
- ✅ 實時持倉同步
- ✅ 成交記錄導入
- ✅ 支持 CSV 批量匯入
- 📁 位置：`brokers/ib/`

### 元大證券 (Yuanta)
- ✅ 數位憑證認證
- ✅ 實時持倉查詢
- ✅ 自動同步（`sync_yuanta_positions.py`）
- 📁 位置：`brokers/yuanta_api.py`

### Schwab
- ⏳ OAuth 集成開發中
- 📁 位置：`brokers/schwab_api.py`

---

## 💾 Google Sheets 11 個標準分頁

| 分頁名稱 | 層級 | 功能說明 |
|---------|------|---------|
| `intel_events` | 第一層 | USGS 地震、新聞、油輪事件 |
| `macro_state` | 第一層 | GDP、PMI、CPI、risk_on 開關 |
| `orders_queue` | 第二層 | 待執行指令池 |
| `risk_incidents` | 第二層 | 風控攔截日誌 |
| `strategies` | 第三層 | 策略主檔 |
| `trades` | 第三層 | 交易主表 |
| `daily_nav` | 第三層 | 每日淨值與績效 |
| `broker_snapshot` | 第四層 | 帳戶快照 |
| `broker_positions` | 第四層 | 即時持倉 |
| `broker_fills` | 第四層 | 原始成交紀錄 |
| `sync_logs` | 第四層 | 同步日誌與錯誤追蹤 |

💡 **快速遷移指南**：見 `MIGRATION_TO_V3_1.md`

---

## 📌 核心功能模組（開發進度）

### ✅ 已實作
- `strategyupload.py` - 策略上傳與解析

### ⏳ 開發中
- 資金配置引擎（allocator）
- 自動決策引擎（decision_engine）
- 績效追蹤計算（perf_tracker）

### 📋 計劃中
- 總經分類器（econ_classifier）
- 風控邏輯（risk_control）
- 預期報酬通道圖（channel_plot）
- Monte Carlo 模擬（monte_carlo）
- AI 摘要（gpt_summary）
- 通知系統（notifier）

---

## 🎨 UI/UX 設計

### 主題系統
- **配色方案**：科技紫藍系（專業、現代、科技感）
- **主色**：`#5B47D9`（紫）| **輔助色**：`#06B6D4`（青）
- **強調色**：`#EC4899`（粉紅）| **成功**：`#10B981`（綠）
- **文件**：`utils/ui_theme.py`

### 主題變體
- 📱 現代亮色系（預設）
- 🌙 暗黑模式（`ui_theme_dark.py`）
- 🎨 現代設計（`ui_theme_modern.py`）

---

## 🔐 安全與認證

### Google OAuth
- 自動讀取 `credentials.json`
- 支持 Google Sheets API 無縫連接
- 環境變數：`GOOGLE_APPLICATION_CREDENTIALS`

### 數位憑證
- 元大 CA 憑證存儲在 `lib/元大CA.pfx`
- 支持密碼保護與過期檢查
- 自動更新機制（`brokers/delete_expired_certs.py`）

### 環境變數管理
- 敏感資訊存儲於 `.env`（**不要提交到 Git**）
- 支持多環境配置（PROD/TEST/DEV）

---

## 📚 重要文檔

| 文檔名稱 | 用途 |
|---------|------|
| `MIGRATION_TO_V3_1.md` | Sheets 遷移步驟（詳細） |
| `QUICK_START_V3_1.md` | 5 分鐘快速參考 |
| `UI_UX_DESIGN_GUIDE.md` | UI 設計規範與使用 |
| `SHIP_MONITORING_QUICK_START.md` | 油輪監測系統 |
| `FLASK_SHEETS_INTEGRATION.md` | Flask 儀表板文檔 |
| `AUTO_SYNC_QUICK_START.md` | 自動同步排程 |
| `DIAGNOSTICS_GUIDE.md` | 故障排除指南 |
| `HOW_TO_DEBUG_PAGES.md` | 頁面調試方法 |

---

## 🛠️ 常見問題與故障排除

### Q: 連接不到 Google Sheets？
**A:** 檢查以下項目：
```bash
# 1. 驗證 credentials.json 存在
ls credentials.json

# 2. 檢查環境變數配置
echo $GOOGLE_APPLICATION_CREDENTIALS

# 3. 測試連接
python -c "import gspread; auth = gspread.service_account(); print('✅ Google Auth OK')"

# 4. 如遇網路問題，可臨時禁用 Sheets
export DISABLE_SHEETS=1
```

### Q: 元大API 連接失敗？
**A:** 檢查數位憑證：
```bash
# 驗證憑證路徑
ls $YUANTA_CERT_PATH

# 測試憑證密碼
python brokers/probe_yuanta_cert.py
```

### Q: 頁面加載緩慢？
**A:** 檢查緩存：
```bash
# 清除快取
rm -rf .streamlit/cache/
python -m streamlit cache clear

# 查看快取狀態
ls data/cache/
```

---

## 📈 開發進度與路線圖

### MVP (2026 Q1)
- ✅ Streamlit 多頁面應用框架
- ✅ Google Sheets 11 分頁結構
- ✅ 多券商 API 集成（IB、元大、Schwab）
- ✅ 基礎績效追蹤
- ✅ 波斯灣油輪監測系統
- ✅ Flask 儀表板

### Phase 2 (2026 Q2)
- 📋 完整風控引擎
- 📋 自動決策系統
- 📋 實時通知系統
- 📋 AI 摘要與建議

### Phase 3 (2026 Q3+)
- 📋 高級績效歸因
- 📋 Monte Carlo 風險模擬
- 📋 機器學習策略推薦

---

## 👨‍💻 開發建議

### 工作流程
1. **本地開發**：使用 `.venv` 虛擬環境
2. **測試**：Streamlit 實時熱重載 + Flask 單元測試
3. **提交**：檢查 `.env` 未上傳，運行 linter 與測試
4. **部署**：使用 Streamlit Cloud 或自建伺服器

### 代碼組織原則
- `brokers/` - 多家券商 API，保持解耦
- `modules/` - 獨立功能模組，支持單元測試
- `pages/` - Streamlit 頁面組件（避免複雜邏輯）
- `utils/` - 共用工具函式

### 調試技巧
- 啟用 Streamlit 調試日誌：`streamlit run app.py --logger.level=debug`
- 查看頁面加載時間：`STREAMLIT_LOGGER_LEVEL=debug`
- 檢查 Google Sheets 操作：見 `HOW_TO_DEBUG_PAGES.md`

---

## 🤝 貢獻與支持

### 報告問題
1. 檢查 `DIAGNOSTICS_GUIDE.md`
2. 查看相關日誌：`outputs/logs/`
3. 提供詳細錯誤信息與環境配置

### 功能建議
歡迎提交 Issue 或 Pull Request！

### 聯繫與支持
- 📧 Email: [contact]
- 📱 LINE Notify: 配置於 `modules/notifier.py`
- 🔔 Obsidian 同步：自動備份至本地筆記

---

## 📝 版本歷史

### v3.1 (2026-03-04) - 當前版本
- ✅ 完整 11 分頁 Google Sheets 結構
- ✅ 多券商 API 完整集成
- ✅ Streamlit 多頁面應用上線
- ✅ Flask 儀表板修復
- ✅ 波斯灣油輪監測系統上線
- ✅ UI/UX 設計系統完成

### v3.0 (2026-03-01)
- 四層架構設計完成
- Google Sheets 遷移完成

### v2.x
- 初期架構探索
- 單頁面應用

---

## 📄 授權與免責聲明

本系統用於**教育與研究目的**。所有交易決策由投資人自行負責，開發團隊不承擔投資損失責任。

---

## 🎯 快速導航

| 我想要... | 請看文檔 |
|---------|--------|
| 5 分鐘快速啟動 | `QUICK_START_V3_1.md` |
| 遷移到新 Sheets | `MIGRATION_TO_V3_1.md` |
| 配置波斯灣監測 | `SHIP_MONITORING_QUICK_START.md` |
| 啟動 Flask 儀表板 | `FLASK_SHEETS_INTEGRATION.md` |
| 設置自動同步 | `AUTO_SYNC_QUICK_START.md` |
| 調試頁面問題 | `HOW_TO_DEBUG_PAGES.md` |
| 故障排除 | `DIAGNOSTICS_GUIDE.md` |
| UI 設計細節 | `UI_UX_DESIGN_GUIDE.md` |

---

**最後更新**：2026-03-04
**維護者**：Krystal AI Trading Team
**狀態**：🟢 Active Development
