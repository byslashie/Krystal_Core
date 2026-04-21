# 📊 Google Sheets 整理與重構指南

## 🚀 快速開始

### 第 1 步：掃描現有架構
```bash
python scan_sheets_schema.py
```

**這個工具會：**
- ✅ 連接你的 Google Sheets
- 📋 列出所有分頁名稱與欄位
- 🔢 顯示每個欄位的資料筆數與樣本值
- 💾 匯出 JSON 和 Markdown 報告（可選）

**預期輸出示例：**
```
[1] 📄 分頁名稱：trades
    📊 筆數：1,234
    📋 欄位數：13

    欄位清單：
      1. id                    | 型態：int64       | 非空：1234 | 樣本：12345
      2. date                  | 型態：object      | 非空：1234 | 樣本：2024-03-01
      ...
```

---

### 第 2 步：檢查整理建議
```bash
python cleanup_sheets_schema.py
```

**這個工具會：**
- 🔍 掃描現有架構
- ⚖️ 與 v3.1 標準架構對比
- 📝 生成整理報告 (`SHEETS_CLEANUP_REPORT.txt`)
- 💡 提供具體的整理步驟建議

**預期輸出示例：**
```
❌ 【缺少的分頁】
  • intel_events
    說明：第一層：情報快訊（USGS 地震、新聞事件）
    欄位：date, event_type, location, severity, ...

⚠️ 【多出來的分頁（建議刪除或備份）】
  • old_trades_backup
  • temp_data

🔧 【欄位結構不符】
  • trades
    缺少：entry_reason, exit_reason, currency
    多出：old_field_1, old_field_2
```

---

## 📘 v3.1 標準架構總覽

### 🎯 四層設計

#### **第一層：情報與總經感知層**

| 分頁名稱 | 說明 | 主要欄位 |
|---------|------|--------|
| `intel_events` | 外部情報事件 | date, event_type, location, severity, llm_risk_score, summary, impact_assets |
| `macro_state` | 總經狀態與風險開關 | date, regime, risk_on, notes |

#### **第二層：決策與風控層**

| 分頁名稱 | 說明 | 主要欄位 |
|---------|------|--------|
| `orders_queue` | 待執行指令池 | order_id, date, strategy, symbol, side, quantity, price_limit, r1_pass, r2_approved, status |
| `risk_incidents` | 風控攔截日誌 | date, strategy, reason_code, cool_down_until |

#### **第三層：交易歸因與績效層**

| 分頁名稱 | 說明 | 主要欄位 |
|---------|------|--------|
| `strategies` | 策略主檔 | strategy_name, initial_capital, broker, status, strategy_type, risk_level |
| `trades` | 交易主表 | id, date, entry_time, exit_time, broker, symbol, side, entry_price, exit_price, quantity, status, strategy, entry_reason, exit_reason |
| `daily_nav` | 每日淨值表 | date, strategy, nav, daily_return, cumulative_return |

#### **第四層：券商事實層（唯讀）**

| 分頁名稱 | 說明 | 主要欄位 |
|---------|------|--------|
| `broker_snapshot` | 帳戶快照 | timestamp, broker, net_liquidation, total_cash_value, equity_with_loan_value, currency |
| `broker_positions` | 即時持倉 | timestamp, broker, symbol, sec_type, exchange, currency, position, avg_cost |
| `broker_fills` | 原始成交紀錄 | exec_id, timestamp, broker, symbol, side, shares, price, currency, order_id |
| `sync_logs` | 同步日誌 | timestamp, sync_type, broker, record_count, status, notes |

---

## 🔧 手動整理步驟

### 👉 如果你想自己手動操作：

#### **1️⃣ 備份現有 Sheets**
```
建議步驟：
1. 右鍵點擊你的 Google Sheets
2. 選擇「複製」→ 建立備份版本
3. 備份檔名稱改為：「實盤交易管理_BACKUP_[日期]」
```

#### **2️⃣ 新建缺少的分頁**
根據掃描報告，逐一在 Google Sheets 中新增分頁，並設定正確的欄位。

**建議順序：**
- 先建 `intel_events` 和 `macro_state`（第一層）
- 再建 `orders_queue` 和 `risk_incidents`（第二層）
- 然後建 `strategies`（第三層）
- 最後確認 `trades` 和 `daily_nav` 的欄位結構
- 第四層為自動同步，通常由程式維護

#### **3️⃣ 遷移現有資料**
對於已經有資料的分頁，使用 VLOOKUP 或 INDEX+MATCH 進行欄位對應。

**示例 VLOOKUP：**
```
=VLOOKUP(A2, old_trades!A:Z, 3, FALSE)
```

#### **4️⃣ 驗證資料完整性**
再次執行 `scan_sheets_schema.py`，確認所有欄位都已正確配置。

#### **5️⃣ 刪除舊分頁**
確認資料無誤後，可安全刪除多餘或過期的分頁。

---

## 💻 Python API 使用

如果你想在程式中直接使用，可以用 `sheets_utils.py` 的函數：

```python
from sheets_utils import read_trades, read_broker_fills, append_trade

# 讀取交易主表
trades_df = read_trades()

# 讀取券商成交紀錄
fills_df = read_broker_fills()

# 新增交易記錄
new_trade = {
    "id": 12345,
    "date": "2024-03-03",
    "symbol": "2330.TW",
    "side": "BUY",
    "quantity": 10,
    # ... 其他欄位
}
append_trade(new_trade)
```

---

## ⚙️ 環境變數設定

確保你的 `.env` 檔案包含以下設定：

```bash
# Google Sheets 設定
GOOGLE_SHEET_KEY=你的_Sheets_ID
GOOGLE_SHEET_NAME=實盤交易管理
GOOGLE_APPLICATION_CREDENTIALS=credentials.json

# 如果網路不穩定，可設為 1 以使用本地緩存
DISABLE_SHEETS=0
```

---

## 🐛 常見問題

### Q1: 掃描時出現 SSL 錯誤？
```bash
# 臨時禁用 Sheets，使用本地緩存
$env:DISABLE_SHEETS="1"
python scan_sheets_schema.py
```

### Q2: credentials.json 找不到？
確保 `credentials.json` 在專案根目錄，或在 `.env` 中設定完整路徑：
```bash
GOOGLE_APPLICATION_CREDENTIALS=C:/path/to/credentials.json
```

### Q3: 如何在 macOS 上執行？
```bash
python3 scan_sheets_schema.py
python3 cleanup_sheets_schema.py
```

### Q4: 可以自動完成整理嗎？
目前工具只提供掃描和報告。實際的 Sheets 修改（新建分頁、遷移資料）需要手動操作，以避免意外資料損失。

---

## 📊 資金管理部分補充

根據你提到的「資金管理部分」，這涉及以下欄位和邏輯：

### 相關分頁：
- **`strategies`** - 策略初始資金與狀態
- **`daily_nav`** - 每日淨值（用於計算資金曲線）
- **`broker_snapshot`** - 帳戶總資產變化
- **`orders_queue`** - 待執行的資金配置指令

### 建議的資金管理流程：
```
1. 在 strategies 中定義各策略的初始資金
2. 根據 daily_nav 計算每日收益
3. 根據風控邏輯自動調整資金分配
4. 將調整指令寫入 orders_queue
5. Windows 端執行並記錄至 broker_fills
```

---

## ✅ 完成檢查清單

掃描完成後，檢查以下項目：

- [ ] 所有 11 個分頁都已建立
- [ ] 每個分頁的欄位與文件一致
- [ ] 現有資料已正確遷移
- [ ] 沒有多餘的舊分頁需要刪除
- [ ] 本地緩存已更新（可選：`data/cache/` 資料夾）

---

**祝你整理順利！有問題隨時詢問。** 🚀
