# ⚡ 快速開始（5 分鐘）

## ✅ 部署檢查清單

複製下面的清單，按順序完成：

```
部署步驟                                          狀態
┌────────────────────────────────────────┐
│ [ ] 1. 安裝 Python 依賴                  │
│ [ ] 2. 配置 Google Sheets API          │
│ [ ] 3. 測試 API 連接                    │
│ [ ] 4. 啟動系統                         │
│ [ ] 5. 上傳測試文件                     │
│ [ ] 6. 驗證同步流程                     │
└────────────────────────────────────────┘
```

---

## 🚀 逐步指南

### 步驟 1: 安裝依賴（2 分鐘）

```bash
cd "G:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"

pip install -r requirements.txt
```

如果 `requirements.txt` 不存在，直接運行：

```bash
pip install Flask Flask-CORS pandas numpy gspread google-auth-oauthlib google-auth-httplib2 APScheduler
```

### 步驟 2: 配置 Google Sheets（2 分鐘）

#### 2.1 獲取 credentials.json

1. 訪問 Google Cloud Console：https://console.cloud.google.com/
2. 確保有一個項目
3. 啟用 Google Sheets API（搜索並點擊「啟用」）
4. 建立服務帳號：
   - 導航 → 「服務帳號」
   - 建立服務帳號
   - 名稱：`krystal-strategy-sync`
5. 建立金鑰（JSON 格式）
6. 將下載的 JSON 檔案重命名為 `credentials.json`
7. 移動到 `01-交易系統程式碼/` 資料夾

#### 2.2 分享 Google Sheet

1. 打開你的 Google Sheets（使用提供的鏈接）
2. 點擊右上角「分享」
3. 複製服務帳號郵箱：
   ```
   krystal-strategy-sync@[PROJECT_ID].iam.gserviceaccount.com
   ```
   （從 credentials.json 的 `client_email` 欄位複製）
4. 添加為「編輯者」，點擊分享

#### 2.3 更新 Sheet ID

在以下位置更新你的 Sheet ID：

**文件 1**: `strategy_sync_api.py` 第 18 行
```python
SHEETS_ID = '你的_SHEET_ID'  # 從 Google Sheets URL 複製
```

**文件 2**: `sync_engine.py` 第 45 行
```python
SHEETS_ID = '你的_SHEET_ID'
```

**如何找到 Sheet ID**：
```
https://docs.google.com/spreadsheets/d/THIS_IS_YOUR_SHEET_ID/edit
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

### 步驟 3: 測試連接（1 分鐘）

建立 `test_connection.py`：

```python
"""測試 Google Sheets 連接"""

from pathlib import Path
import gspreach
from google.oauth2.service_account import Credentials

CREDS_PATH = Path('credentials.json')
SHEETS_ID = '你的_SHEET_ID'  # 更新這裡

try:
    print('🔐 正在連接 Google Sheets...')
    
    creds = Credentials.from_service_account_file(
        CREDS_PATH,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    
    client = gspread.authorize(creds)
    workbook = client.open_by_key(SHEETS_ID)
    
    print('✓ 連接成功！')
    print(f'  工作簿名稱: {workbook.title}')
    print(f'  工作表數量: {len(workbook.worksheets())}')
    
    for i, ws in enumerate(workbook.worksheets()):
        print(f'    [{i}] {ws.title}')
    
except Exception as e:
    print(f'✗ 連接失敗: {e}')
    print('\n檢查清單:')
    print('  [ ] credentials.json 存在嗎？')
    print('  [ ] Sheet ID 正確嗎？')
    print('  [ ] Google Sheets 已分享給服務帳號嗎？')
```

運行測試：
```bash
python test_connection.py
```

### 步驟 4: 啟動系統（1 分鐘）

#### 方式 A: 使用批文件（推薦，Windows）

建立 `start_system.bat`：

```batch
@echo off
cd /d "G:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"

echo.
echo 🚀 Krystal 策略同步系統啟動中...
echo.

start "Strategy Sync API" cmd /k python strategy_sync_api.py
timeout /t 3 /nobreak

start "Sync Engine" cmd /k python sync_engine.py
timeout /t 2 /nobreak

echo ✓ 系統啟動完成！
echo.
echo 打開瀏覽器訪問：http://localhost:5000/templates/pages/strategy_import.html
echo.
echo 日誌文件：
echo - API: 命令行窗口 1
echo - 引擎: 命令行窗口 2 或 Staging\sync_engine.log
echo.
pause
```

雙擊 `start_system.bat` 來啟動。

#### 方式 B: 手動啟動

**終端 1**：
```bash
cd "G:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"
python strategy_sync_api.py
```

**終端 2**：
```bash
cd "G:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"
python sync_engine.py
```

**瀏覽器**：
```
http://localhost:5000/templates/pages/strategy_import.html
```

### 步驟 5: 測試上傳（不計時）

#### 準備測試 CSV

建立 `test_backtest.csv`：

```csv
Date,Close,PnL,Return
2026-01-01,100000,1000,0.01
2026-01-02,101000,1500,0.015
2026-01-03,102500,2100,0.021
2026-01-04,104600,1800,0.017
2026-01-05,106400,2500,0.023
2026-01-06,108900,1200,0.011
2026-01-07,110100,3000,0.027
2026-01-08,113100,2200,0.019
2026-01-09,115300,2800,0.024
2026-01-10,118100,3500,0.030
```

#### 上傳並測試

1. 打開 HTML 頁面（http://localhost:5000/...）
2. 拖拽或選擇 `test_backtest.csv`
3. 輸入策略名稱：`Test Strategy`
4. 點擊「🔍 分析」
5. 應該看到 KPI 計算結果：
   - CAGR: ~18%
   - Sharpe: ~2.0
   - MDD: ~0%
   - Win Rate: 100%
6. 點擊「✅ 確認」進入預覽
7. 查看資料夾結構預覽
8. 點擊「✅ 批准導入」

---

## ✨ 驗證成功的標誌

如果看到以下信息，說明系統運行正常：

### API 窗口（strategy_sync_api.py）
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### 同步引擎窗口（sync_engine.py）
```
============================================================
Krystal 策略同步引擎 v1.0
啟動時間: 2026-03-31 15:25:30
============================================================
✓ Google Sheets 連接成功
✓ 定時任務已啟動
  - Sheets → 本地：每 5 分鐘
  - Registry 更新：每 10 分鐘
  - 完整同步：每天 23:00
```

### HTML 頁面
- 同步狀態面板顯示「✓」和時間戳
- 能夠上傳文件
- 能夠計算 KPI 並顯示圖表

### Google Sheets
- SyncLog 工作表有新記錄（例如：`analyze`, `confirm`）
- BacktestPool 有新策略行

### 本地文件夾
```
02-策略知識庫/
└── Staging/
    ├── uploads/
    │   └── T001_meta.json              ✓ 生成
    ├── drafts/
    │   └── S7-Test Strategy/           ✓ 生成
    └── sync.log                        ✓ 記錄
```

---

## 🐛 常見問題快速排查

| 問題 | 檢查項 | 解決方案 |
|------|--------|--------|
| 無法訪問 HTML 頁面 | API 運行中？ | 確認 strategy_sync_api.py 窗口運行 |
| 上傳後沒有結果 | CSV 格式正確？ | 確保有 `Close` 或 `淨值` 列 |
| Sheets 無法連接 | credentials.json？ | 確認文件存在且路徑正確 |
| 同步引擎沒反應 | Sheets 連接？ | 檢查 sync_engine.log 窗口 |
| Git 錯誤 | Git 已安裝？ | 運行 `git --version` 檢查 |

---

## 📊 首次運行檢查清單

```
系統啟動後，驗證：

□ API 服務器運行（http://localhost:5000 可訪問）
□ 同步引擎啟動（看到「✓ Google Sheets 連接成功」）
□ HTML 頁面能加載
□ 同步狀態面板顯示時間戳（表示連接正常）
□ 能上傳 CSV 文件
□ KPI 能正確計算顯示
□ 點擊確認後 Staging 資料夾被創建
□ Google Sheets BacktestPool 有新行添加
□ sync.log 有記錄（表示系統在運作）
```

---

## 🎯 下一步

1. ✅ **首次測試成功** → 開始用你的實際回測 CSV
2. 📊 **在 Sheets 中批准** → 監看同步引擎自動導入
3. 🔍 **檢查 Strategies 資料夾** → 驗證新資料夾被創建
4. 📈 **更新實盤績效** → 在 LiveStrategies 中手動添加實盤數據

---

**祝你使用愉快！有任何問題，參考 `STRATEGY_SYNC_SETUP.md` 的詳細文檔。** 🚀
