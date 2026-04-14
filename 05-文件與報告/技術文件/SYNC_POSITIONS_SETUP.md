# 🔄 持倉自動同步系統設置指南

## 📋 概述

本指南說明如何設置 **IB 和元大持倉自動同步系統**，使得：
- ✅ 每日自動從 IB 和元大獲取最新持倉
- ✅ 同步數據自動寫入 Google Sheets 的 `broker_positions` 分頁
- ✅ 前端應用自動顯示最新持倉
- ✅ 支持 Windows Task Scheduler 定時執行

---

## 📁 新增文件

```
brokers/
├── sync_positions.py              ← 核心同步模組（IB + Yuanta）
│
├── ib_api.py                      ← IB API（已有）
└── yuanta_api.py                  ← 元大 API（已有）

根目錄/
├── run_daily_sync.py              ← 每日同步排程（已更新）
├── setup_daily_sync_scheduler.py  ← Windows Task Scheduler 設置工具
└── SYNC_POSITIONS_SETUP.md        ← 本文件
```

---

## 🚀 快速開始（3 步）

### 1️⃣ 測試持倉同步（手動執行）

```bash
# 在專案根目錄執行
python brokers/sync_positions.py
```

預期輸出：
```
======================================================================
🔄 持倉同步開始
======================================================================

INFO - [IB] 開始獲取持倉...
✅ [IB] 成功獲取 X 筆持倉
INFO - [Yuanta] 開始獲取持倉...
✅ [Yuanta] 成功獲取 Y 筆持倉
✅ 成功寫入 Z 筆持倉到 Google Sheets

======================================================================
✅ 持倉同步完成
======================================================================

📊 同步結果：
   • IB: X 筆 (成功獲取 X 筆)
   • Yuanta: Y 筆 (成功獲取 Y 筆)
   • 總計: Z 筆
```

### 2️⃣ 設置 Windows 定時執行（推薦）

```bash
# 設置每天 09:00 自動執行同步
python setup_daily_sync_scheduler.py --windows --schedule-time 09:00
```

預期輸出：
```
======================================================================
⚙️  設置 Windows Task Scheduler 任務
======================================================================

✅ 任務建立成功！
   • 任務名: Krystal-AI-Daily-Sync
   • 執行時間: 每天 09:00
   • 執行指令: ...\run_daily_sync.py
```

### 3️⃣ 驗證前端顯示

訪問前端應用的「實盤交易」頁面：
- URL: `http://localhost:9999` (或你的服務器地址)
- 「當前持倉」應該顯示最新的同步數據

---

## ⚙️ 詳細配置

### A. IB API 配置

確保 `.env` 文件中有以下設置：

```env
# Interactive Brokers 連接設置
IB_HOST=127.0.0.1
IB_PORT=7496          # Live: 7496, Paper: 7497
IB_CLIENT_ID=99       # 避免與其他應用衝突
IB_TIMEOUT=5
```

**前置條件**：
- ✅ IB TWS 或 Gateway 必須正在運行
- ✅ IB API 必須開啟（TWS → 設置 → API）

### B. 元大 API 配置

確保 `.env` 文件中有以下設置：

```env
# 元大證券 API 配置
YUANTA_ACCOUNT=S989                # 你的證券帳號
YUANTA_PASSWORD=your_password      # 你的密碼
YUANTA_ENV=PROD                    # 或 UAT（測試環境）
```

**前置條件**：
- ✅ 僅支持 Windows (需要 .NET Framework)
- ✅ Python 3.10+ (32-bit 或 64-bit)
- ✅ pythonnet 和元大 DLL 已正確安裝

### C. Google Sheets 配置

確保 Google Sheets 有以下分頁：
- `broker_positions` - 存放持倉數據
- `sync_logs` - 記錄同步日誌

運行此命令建立新 Sheets（可選）：
```bash
python create_new_sheets_v3_1.py
```

---

## 🔄 同步流程細節

### 持倉同步流程圖

```
┌─────────────────────────────┐
│  每日 09:00 Task Scheduler   │
└──────────────┬──────────────┘
               │
               ▼
        ┌──────────────┐
        │ run_daily_sync.py
        └──────┬───────┘
               │
       ┌───────┴─────────┐
       │                 │
       ▼                 ▼
  ┌─────────┐      ┌────────────────┐
  │ NAV 同步 │     │ 持倉同步        │
  │sync_ib  │     │sync_positions  │
  │_nav.py  │     │                │
  └─────────┘     └────┬───────────┘
       │               │
       │        ┌──────┴──────┐
       │        │             │
       │        ▼             ▼
       │      ┌────┐      ┌────────┐
       │      │ IB │      │ Yuanta │
       │      │API │      │  API   │
       │      └────┘      └────────┘
       │        │             │
       │        └──────┬──────┘
       │               ▼
       │      ┌─────────────────┐
       │      │ 合併 & 轉換格式  │
       │      └────────┬────────┘
       │               ▼
       └──────► ┌──────────────────────┐
               │  Google Sheets 寫入   │
               │  broker_positions    │
               │  broker_snapshot     │
               │  sync_logs          │
               └──────────────────────┘
                       │
                       ▼
               ┌─────────────────┐
               │ Flask 應用讀取  │
               │ /api/holdings   │
               └────────┬────────┘
                       │
                       ▼
               ┌─────────────────┐
               │ 前端展示        │
               │ 當前持倉        │
               └─────────────────┘
```

### 數據轉換

**IB API 持倉格式** → **broker_positions 格式**：

| IB 字段 | Sheets 字段 | 對應關係 |
|--------|-----------|---------|
| symbol | 標的 | 股票代碼 |
| position | 數量 | 持股數量 |
| avgCost | 均價 | 平均成本 |
| exchange | 市場 | NASDAQ/TWSE |
| secType | 方向 | STK=多 |

**元大 API 持倉格式** 類似

---

## 🛠️ 命令參考

### 手動同步

```bash
# 執行持倉同步
python brokers/sync_positions.py

# 執行完整日常同步（NAV + 持倉）
python run_daily_sync.py
```

### Windows Task Scheduler 管理

```bash
# 建立任務 - 每天 09:00
python setup_daily_sync_scheduler.py --windows --schedule-time 09:00

# 建立任務 - 每天 14:30
python setup_daily_sync_scheduler.py --windows --schedule-time 14:30

# 移除任務
python setup_daily_sync_scheduler.py --windows --remove

# 列出所有任務
python setup_daily_sync_scheduler.py --windows --list
```

### APScheduler（備選方案）

```bash
# 建立 APScheduler 配置（需先安裝 apscheduler）
pip install apscheduler
python setup_daily_sync_scheduler.py --apscheduler

# 啟動 APScheduler 背景服務
python run_scheduled_sync.py
```

---

## 📊 Google Sheets 數據格式

### broker_positions 分頁結構

| 時間 | 券商 | 市場 | 標的 | 方向 | 數量 | 均價 | 現價 | 帳面損益 | 損益率 |
|------|------|------|------|------|------|------|------|---------|--------|
| 2026-03-10 09:00:00 | IB | NASDAQ | QQQ | 多 | 10 | 350.50 | 352.30 | 18.00 | 0.51% |
| 2026-03-10 09:00:00 | Yuanta | TWSE | 2330 | 多 | 100 | 850.00 | 855.00 | 500.00 | 0.59% |

### sync_logs 分頁結構

| 時間 | 類型 | 券商 | 新增筆數 | 狀態 | 備註 |
|------|------|------|---------|-------|-------|
| 2026-03-10 09:00:05 | broker_positions | IB | 5 | success | 成功獲取 5 筆 |
| 2026-03-10 09:00:15 | broker_positions | Yuanta | 3 | success | 成功獲取 3 筆 |

---

## ❌ 故障排除

### 問題 1: sync_positions.py 執行失敗

**症狀**：
```
❌ [IB] 無法導入 IB API
```

**解決**：
1. 檢查 TWS/Gateway 是否運行
2. 驗證 IB API 設置
3. 確認 ib_insync 已安裝：
   ```bash
   pip install ib-insync
   ```

### 問題 2: 元大 API 初始化失敗

**症狀**：
```
❌ 無法 import clr（pythonnet 未正常安裝）
```

**解決**（僅限 Windows）：
```bash
# 卸載並重新安裝
pip uninstall pythonnet -y
pip install pythonnet

# 或使用 32-bit Python
py -3.10-32 -m pip install pythonnet
```

### 問題 3: Google Sheets 連接失敗

**症狀**：
```
❌ 無法導入 sheets_utils
```

**解決**：
1. 驗證 credentials.json 位置
2. 檢查 .env 中的 GOOGLE_SHEET_KEY
3. 測試連接：
   ```bash
   python -c "from sheets_utils import get_workbook; print(get_workbook())"
   ```

### 問題 4: Task Scheduler 任務不執行

**症狀**：排定時間內沒有執行

**檢查**：
```bash
# 查看任務狀態
schtasks /query /tn "Krystal-AI-Daily-Sync" /v

# 手動執行測試
schtasks /run /tn "Krystal-AI-Daily-Sync"

# 查看最後運行日期/時間
schtasks /query /tn "Krystal-AI-Daily-Sync" /v /fo list
```

---

## 📈 性能優化

### 快速同步（只同步改變的位置）

如果要優化同步速度，可以在 `sync_positions.py` 中實現增量同步：

```python
def get_positions_hash(positions):
    """計算持倉的哈希值，用於檢測變化"""
    import hashlib
    import json
    data = json.dumps(positions, sort_keys=True, default=str)
    return hashlib.md5(data.encode()).hexdigest()

# 只在持倉改變時才寫入 Sheets
last_hash = None
def sync_positions_incremental():
    global last_hash
    positions = get_all_positions()
    current_hash = get_positions_hash(positions)

    if current_hash != last_hash:
        write_to_sheets(positions)
        last_hash = current_hash
```

### 並行同步

使用 ThreadPool 並行獲取多個經紀商的持倉：

```python
from concurrent.futures import ThreadPoolExecutor

def sync_all_positions_parallel():
    with ThreadPoolExecutor(max_workers=2) as executor:
        ib_future = executor.submit(sync_ib_positions)
        yuanta_future = executor.submit(sync_yuanta_positions)

        ib_result = ib_future.result(timeout=30)
        yuanta_result = yuanta_future.result(timeout=30)
```

---

## 📝 日誌

### 日誌位置

同步日誌存放在：
- **主日誌**：`sync_logs` Google Sheets 分頁
- **系統日誌**：Windows 事件檢視器（Task Scheduler）

### 查看 Task Scheduler 日誌

```bash
# PowerShell
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-TaskScheduler/Operational'} | Select TimeCreated, Message | Head -20
```

---

## 🔐 安全性注意事項

⚠️ **敏感信息保護**：
- `.env` 文件包含敏感信息，不應提交到 Git
- 在 `.gitignore` 中確保排除了 `.env` 和 `credentials.json`
- Task Scheduler 任務運行的是你的 Windows 帳戶，確保帳戶安全

---

## 📞 支持

如遇到問題，請檢查：
1. `/api/status` 端點確認系統狀態
2. Google Sheets 的 `sync_logs` 分頁查看同步歷史
3. 運行 `python brokers/sync_positions.py` 進行手動測試
4. 查看控制台輸出的詳細錯誤信息

---

**最後更新**: 2026-03-10
**版本**: 1.0
