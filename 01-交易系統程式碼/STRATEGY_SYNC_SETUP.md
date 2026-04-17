# 📊 策略同步系統（方案 C）完整部署指南

**版本**: v1.0  
**日期**: 2026-03-31  
**狀態**: 準備就緒

---

## 📋 系統架構概覽

```
Excel 上傳 (Python 系統回測)
     ↓
HTML 前端分析 (strategy_import.html)
     ↓ 
[用戶手動確認預覽]
     ↓
Python 後端 (strategy_sync_api.py)
├─ 創建 Staging 資料夾
├─ 記錄分析結果
└─ 推送到 Google Sheets
     ↓
同步引擎監聽 (sync_engine.py)
├─ 監聽 Sheets 狀態變化
├─ 從 Staging 移動到 Strategies
├─ Git 自動提交
└─ 更新 Registry 和多個 Sheets
```

---

## 🚀 快速開始

### 1️⃣ 安裝依賴

```bash
pip install -r requirements.txt
```

**requirements.txt 內容**：
```
Flask==2.3.0
Flask-CORS==4.0.0
pandas==2.0.0
numpy==1.24.0
gspread==5.12.0
google-auth-oauthlib==1.0.0
google-auth-httplib2==0.2.0
APScheduler==3.10.4
```

### 2️⃣ 配置 Google Sheets API

#### 步驟 A: 取得服務帳號金鑰

1. 訪問 [Google Cloud Console](https://console.cloud.google.com/)
2. 選擇或建立項目
3. 啟用 Google Sheets API
4. 建立服務帳號
5. 下載 JSON 金鑰
6. 保存為 `01-交易系統程式碼/credentials.json`

#### 步驟 B: 分享 Google Sheet

1. 打開你的 Google Sheets：`Krystal-策略管理系統`
2. 點擊分享
3. 添加服務帳號郵箱為編輯者：
   ```
   krystal-strategy-sync@[PROJECT_ID].iam.gserviceaccount.com
   ```

#### 步驟 C: 更新 Sheet ID

在以下文件中更新 `SHEETS_ID`：
- `strategy_sync_api.py` 第 18 行
- `sync_engine.py` 第 45 行

### 3️⃣ 啟動系統

#### 方式 A: 開發模式（測試）

```bash
# 終端 1: 啟動 Flask API
python strategy_sync_api.py

# 終端 2: 啟動同步引擎
python sync_engine.py

# 終端 3: 打開瀏覽器
http://localhost:5000/templates/pages/strategy_import.html
```

#### 方式 B: 生產模式（使用 Gunicorn）

```bash
pip install gunicorn

# 啟動 Flask API
gunicorn -w 4 -b 0.0.0.0:5000 strategy_sync_api:app

# 在另一個終端啟動同步引擎
python sync_engine.py
```

#### 方式 C: 使用 Windows 批文件（推薦用於你的系統）

建立 `start_sync_system.bat`：

```batch
@echo off
cd /d "G:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"

REM 啟動 Flask API（後台）
start "Strategy Sync API" python strategy_sync_api.py

REM 等待 API 啟動
timeout /t 3 /nobreak

REM 啟動同步引擎（後台）
start "Sync Engine" python sync_engine.py

REM 等待 2 秒
timeout /t 2 /nobreak

REM 打開瀏覽器
start http://localhost:5000/templates/pages/strategy_import.html

echo.
echo ✓ 系統啟動完成！
echo.
echo 日誌位置：
echo - API 日誌：命令行窗口
echo - 同步引擎日誌：02-策略知識庫/Staging/sync_engine.log
echo.
pause
```

---

## 📖 使用流程

### 工作流程 1: 上傳並分析策略

#### 第 1 步: 準備 Excel 文件

你的 Python 回測系統輸出的 CSV 文件，應包含以下欄位（至少）：

```
Date        | Close  | PnL  | Return
2026-01-01  | 100000 | 1000 | 0.01
2026-01-02  | 101000 | 1500 | 0.015
...
```

**支持的欄位名稱**（不區分大小寫）：
- 淨值: `close`, `equity`, `nav`, `淨值`
- 損益: `pnl`, `profit`, `損益`
- 日期: `date`, `datetime`, `日期`

#### 第 2 步: 訪問 HTML 頁面

打開瀏覽器：
```
http://localhost:5000/templates/pages/strategy_import.html
```

#### 第 3 步: 上傳並分析

1. **拖拽上傳** CSV 文件或點擊選擇
2. 輸入**策略名稱**（例：Wave Strategy）
3. 確認 Python 版本號（例：1.0.3）
4. 點擊 **🔍 分析（計算 KPI）**
5. 系統自動計算 6 個 KPI：
   - CAGR（年化報酬）
   - Sharpe Ratio（風險調整報酬）
   - MDD（最大回檔）
   - Win Rate（勝率）
   - Profit Factor（獲利因子）
   - 交易數量

#### 第 4 步: 預覽決策

1. 點擊 **✅ 確認 → 進入預覽決策**
2. 查看資料夾結構預覽
3. 查看 Home.md 內容預覽
4. 決定：
   - **✅ 批准導入**：創建資料夾 → 同步到 Sheets → Git 提交
   - **📝 駁回**：保留在 Staging，標記為需優化

---

### 工作流程 2: 在 Google Sheets 審批

#### BacktestPool 工作表（回測候選池）

| ID | 策略名稱 | CAGR | Sharpe | 狀態 | 資料夾ID |
|----|---------|------|--------|------|---------|
| T001 | Wave Strategy | 24.5% | 2.15 | ⏳ 待審 | — |
| T002 | Momentum | 18.3% | 1.80 | ✅ 已批准 | S6 |

**決策步驟**：

1. 在 Sheets 中找到你上傳的策略（ID = T001）
2. 編輯「狀態」欄位：
   - 將 `⏳ 待審` 改為 `✅ 已批准` 或 `❌ 駁回`
3. 添加備註（可選）
4. **同步引擎會自動檢測**（每 5 分鐘）
5. 如果批准：
   - ✅ 自動從 Staging 移動到 Strategies
   - ✅ 創建完整資料夾結構（Home.md, Versions, Backtests）
   - ✅ Git 自動提交 `📊 新策略導入: S6-Momentum`
   - ✅ 資料夾 ID 自動填回 Sheets

#### LiveStrategies 工作表（已上線策略）

已批准的策略會自動出現在這裡，顯示：
- 資料夾 ID
- 策略名稱
- 版本號
- 上線日期
- 實盤績效（需手動更新）

---

## 📁 本地資料夾結構

### Staging 草稿區（待決策）

```
02-策略知識庫/
└── Staging/
    ├── uploads/                          # 上傳的原始 CSV
    │   ├── T001_meta.json               # 分析元數據
    │   ├── T002_meta.json
    │   └── ...
    │
    ├── drafts/                          # 待決策的資料夾
    │   ├── S6-Wave Strategy/            # 預覽後生成
    │   │   ├── S6-Wave Strategy-Home.md
    │   │   ├── Versions/
    │   │   ├── Backtests/baseline/
    │   │   └── Knowledge/
    │   └── S7-Momentum/
    │
    ├── sync.log                          # 同步日誌（JSONL 格式）
    └── sync_engine.log                   # 引擎運行日誌
```

### Strategies 上線區（已批准）

```
02-策略知識庫/
└── Strategies/
    ├── S1-美股 ETF 輪動/
    ├── S2-台股 ETF 輪動/
    ├── ...
    ├── S6-Wave Strategy/                # 批准後自動移過來
    │   ├── S6-Wave Strategy-Home.md     # 包含最新 KPI
    │   ├── Versions/
    │   │   ├── S6-Wave Strategy-v1.0.md
    │   │   └── S6-Wave Strategy-v1.1.md
    │   ├── Backtests/
    │   │   ├── baseline/
    │   │   │   ├── Wave_Strategy_backtest.csv
    │   │   │   └── backtest_report.md
    │   │   └── v1.1/
    │   └── Knowledge/
    │       ├── 260331.md                # 交易筆記
    │       └── optimization_log.md
    │
    └── Registry策略總表.md              # 自動生成，包含所有上線策略
```

---

## 🔄 同步流程詳細說明

### 事件 1: 用戶上傳和確認

```
時間點        | 操作位置    | 動作
-------------|-----------|-----
15:25:00     | HTML 頁面  | 用戶上傳 CSV
15:25:15     | 後端 API   | 計算 KPI，生成 T001 分析記錄
15:25:30     | HTML 頁面  | 用戶查看預覽
15:25:45     | HTML 頁面  | 用戶點擊「批准導入」
15:26:00     | 後端 API   | 創建 Staging/drafts/S6-Wave/
            |           | 生成 Home.md, Home.md, Backtests/
15:26:15     | 後端 API   | 推送到 Sheets BacktestPool
            |           | 新增行：T001, Wave, 24.5%, 待審
```

### 事件 2: 同步引擎監聽並導入

```
時間點        | 同步引擎   | 動作
-------------|-----------|-----
23:00:00     | 定時觸發   | 開始 Sheets → 本地 同步
23:00:05     | 讀取 Sheets| 掃描 BacktestPool
23:00:10     | 檢測變化   | 發現 T001 狀態為「✅ 已批准」
23:00:15     | 文件操作   | 複製 Staging/S6-Wave → Strategies/S6-Wave
23:00:20     | Git        | git add . && git commit -m "📊 新策略導入: S6-Wave"
23:00:25     | Sheets     | 更新 BacktestPool: S6-Wave 資料夾 ID = S6
23:00:30     | Sheets     | 新增行到 LiveStrategies: S6, Wave, v1.0, ...
23:00:35     | Sheets     | 新增行到 SyncLog: approved_and_imported, 成功
23:00:40     | Registry   | 更新 Registry策略總表.md，掃描本地資料夾
```

---

## 📊 Google Sheets 工作表設計

### Sheet 1: BacktestPool（回測候選池）

**列定義**：

```
A  | ID           | T001, T002, ...（自動編號）
B  | 策略名稱     | Wave Strategy
C  | 上傳日期     | 2026-03-31
D  | Python版本   | 1.0.3
E  | CAGR%        | 24.5
F  | Sharpe       | 2.15
G  | MDD%         | -15.2
H  | 勝率%        | 62
I  | 交易數       | 148
J  | 獲利因子     | 2.15
K  | 上傳人       | Krystal
L  | 決策狀態     | ⏳ 待審 / ✅ 已批准 / ❌ 駁回
M  | 決策人       | （審批人填寫）
N  | 決策時間     | （自動填充）
O  | 資料夾ID     | （同步後自動填 S6）
P  | 備註         | （可選）
```

### Sheet 2: LiveStrategies（已上線策略）

已批准的策略自動複製到這裡。

### Sheet 3: VersionHistory（版本歷史）

追蹤每個策略的版本演進。

### Sheet 4: SyncLog（同步日誌）

記錄所有系統事件。

---

## 🔧 配置文件

### Python 系統集成（你的回測 CSV）

你的 Python 回測系統需要輸出如下格式的 CSV：

```python
# 你的回測系統
import pandas as pd

# 假設你的回測結果
backtest_results = {
    'Date': ['2026-01-01', '2026-01-02', ...],
    'Close': [100000, 101000, ...],      # 淨值
    'PnL': [1000, 1500, ...],            # 單筆損益
    'Return': [0.01, 0.015, ...],        # 報酬率
}

df = pd.DataFrame(backtest_results)

# 保存為 CSV
df.to_csv('Wave_Strategy_backtest.csv', index=False)

# 上傳到 HTML 頁面
# file: Wave_Strategy_backtest.csv
```

---

## 📈 監控和故障排除

### 查看同步日誌

```bash
# 本地同步日誌
cat "G:\我的雲端硬碟\Krystal_完整系統\02-策略知識庫\Staging\sync_engine.log"

# 實時日誌（同步引擎窗口）
# 查看運行中的命令行窗口
```

### 常見問題

#### Q1: 上傳後沒有看到分析結果？

**A**: 
- 確認 CSV 有效列（Close / 淨值 / Equity）
- 檢查瀏覽器控制台日誌
- 查看 API 日誌窗口

#### Q2: 同步引擎沒有自動導入？

**A**:
- 確認 Google Sheets 連接正常（檢查 sync_engine.log）
- 確認 Sheets 中的狀態為 `✅ 已批准`（完整匹配，區分空格）
- 同步引擎每 5 分鐘檢查一次，最多等待 5 分鐘

#### Q3: Git 提交失敗？

**A**:
- 確保 Git 已安裝
- 確認資料夾是 Git 倉庫（有 `.git/` 資料夾）
- 檢查 Git 配置：
  ```bash
  git config --global user.name "Krystal"
  git config --global user.email "your@email.com"
  ```

#### Q4: Google Sheets API 無法連接？

**A**:
- 確認 `credentials.json` 存在於正確位置
- 確認 Sheet ID 正確（用戶提供的鏈接中的 ID）
- 確認 Sheets 已分享給服務帳號
- 檢查 Google Cloud 配額

---

## 🎯 下一步計劃

### 已實現（v1.0）
- ✅ HTML 上傳和分析
- ✅ 手動確認預覽
- ✅ Staging 資料夾生成
- ✅ Google Sheets 同步（單向）
- ✅ Git 自動提交

### 待實現（v1.1）
- [ ] 實時同步狀態指示器（WebSocket）
- [ ] Excel 文件支持（目前只有 CSV）
- [ ] 批量導入（多個文件）
- [ ] 策略版本比較工具
- [ ] 自動回測報告生成（從 Sheets 數據）

### 未來計劃（v2.0）
- [ ] 實盤績效自動追蹤（從交易賬戶同步）
- [ ] 策略性能警報（KPI 下降自動通知）
- [ ] A/B 測試框架
- [ ] 自動參數優化建議

---

## 📞 支持和反饋

遇到問題時，請檢查：

1. **日誌文件**
   - `Staging/sync_engine.log` - 同步引擎日誌
   - 瀏覽器控制台 - 前端日誌
   - 命令行窗口 - Flask API 日誌

2. **Google Sheets**
   - 確認 SyncLog 工作表的最新事件
   - 檢查錯誤消息

3. **本地文件夾**
   - 確認 Staging 和 Strategies 資料夾結構

---

**系統已準備就緒！享受無縫的策略管理體驗。** 🚀
