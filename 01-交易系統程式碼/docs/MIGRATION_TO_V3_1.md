# 📊 遷移到 Google Sheets v3.1 完整指南

## 🎯 目標

用一個**全新、干淨的 Google Sheets（符合 v3.1 標準）**替換現有的混亂版本。
舊的 Sheets 保留作為備份。

---

## 📋 步驟概覽

### **總耗時**：約 1-2 小時
```
步驟 1：建立新 Sheets（5 分鐘）
步驟 2：自動新增標準分頁（3 分鐘）
步驟 3：驗證新 Sheets 結構（10 分鐘）
步驟 4：遷移關鍵數據（30-45 分鐘）
步驟 5：切換配置並測試（15 分鐘）
```

---

## 🚀 詳細步驟

### **步驟 1：手動建立新 Google Sheets**

1. 開啟 [Google Sheets](https://sheets.google.com)
2. 點擊左上角「+ 建立」→「試算表」
3. 命名為：`實盤交易管理_v3.1_新版`
4. 建立後，複製 URL 中的試算表 ID
   ```
   URL: https://docs.google.com/spreadsheets/d/【這裡是 ID】/edit
   ```
5. 記下 ID（例如：`1A2B3C4D5E6F7G8H9I...`）

---

### **步驟 2：自動新增標準分頁**

執行以下命令（將 `<SHEET_ID>` 替換為你的 ID）：

```bash
cd "g:/我的雲端硬碟/Krystal_AI_Trading_System"
python create_new_sheets_v3_1.py <SHEET_ID>
```

**預期輸出：**
```
📝 正在新增分頁到 Google Sheets...

[1] ✅ intel_events
    說明：第一層：情報與總經感知 - 外部情報事件
    欄位數：7

[2] ✅ macro_state
    說明：第一層：情報與總經感知 - 總經狀態與風險開關
    欄位數：4

...（共 11 個分頁）

✅ 完成！已新增 11 個標準分頁
```

🎉 **完成！新 Sheets 已自動建立所有分頁和欄位。**

---

### **步驟 3：驗證新 Sheets 結構**

1. 打開新 Sheets：`實盤交易管理_v3.1_新版`
2. 檢查以下分頁是否都存在：

| # | 分頁名稱 | 欄位數 | 優先級 |
|---|---------|--------|--------|
| 1 | intel_events | 7 | 🔴 高 |
| 2 | macro_state | 4 | 🔴 高 |
| 3 | orders_queue | 11 | 🔴 高 |
| 4 | risk_incidents | 4 | 🟠 中 |
| 5 | strategies | 10 | 🔴 高 |
| 6 | trades | 19 | 🔴 高 |
| 7 | daily_nav | 11 | 🔴 高 |
| 8 | broker_snapshot | 8 | 🟠 中 |
| 9 | broker_positions | 10 | 🟠 中 |
| 10 | broker_fills | 12 | 🟠 中 |
| 11 | sync_logs | 7 | 🟠 中 |

✅ 檢查清單：
- [ ] 所有 11 個分頁都存在
- [ ] 每個分頁的第一列都是欄位標題
- [ ] 沒有多餘的「Sheet1」或垃圾分頁

---

### **步驟 4：遷移關鍵數據**

#### **方案 A：手動複製（推薦，給你完整控制）**

**4.1 遷移 `strategies`（最重要）**

1. 打開舊 Sheets 的 `strategies` 分頁
2. 選中所有資料（A:L，共 8 個策略）
3. 複製（Ctrl+C）
4. 打開新 Sheets 的 `strategies` 分頁
5. 點擊 A2（第一列下面）
6. 粘貼（Ctrl+V）
7. 手動驗證資料是否正確

**4.2 遷移 `trades`**

1. 舊 Sheets：`trades` 分頁 → 複製所有資料（A:Q，9 筆）
2. 新 Sheets：`trades` 分頁 → A2 粘貼
3. **重點**：新增欄位「pnl_pct」（出場價-進場價)/進場價*數量/進場價）

**4.3 遷移 `daily_nav`**

1. 舊 Sheets：`daily_nav` 分頁 → 複製（A:E，17 筆）
2. 新 Sheets：`daily_nav` 分頁 → A2 粘貼
3. **建議**：清除所有 NAV 為 1.0 的資料（因為沒有計算過）

**4.4 直接複製（欄位相同）**

以下分頁可以直接複製：
- [ ] broker_snapshot（23 筆）→ 新 Sheets
- [ ] broker_positions（13 筆）→ 新 Sheets
- [ ] broker_fills（6 筆）→ 新 Sheets

#### **方案 B：Python 自動遷移（可選，更快）**

我可以寫一個腳本自動遷移，執行：

```bash
python migrate_data_to_v3_1.py <OLD_SHEET_ID> <NEW_SHEET_ID>
```

但**建議先手動做一遍**，這樣你能驗證數據完整性。

---

### **步驟 5：更新 Python 配置**

編輯 `.env` 檔案，更新 Google Sheets ID：

```bash
# 舊 Sheets（備份）
GOOGLE_SHEET_NAME_OLD=實盤交易管理
GOOGLE_SHEET_KEY_OLD=【舊的 ID】

# 新 Sheets（當前使用）
GOOGLE_SHEET_NAME=實盤交易管理_v3.1_新版
GOOGLE_SHEET_KEY=【新的 ID】
```

---

### **步驟 6：驗證 Python 連接**

運行掃描工具驗證新 Sheets 是否正確連接：

```bash
python simple_scan_sheets.py
```

**預期輸出：**
```
Found 11 sheets in Google Sheets

[1] Sheet: intel_events
    Rows: 0
    Columns: 7

[2] Sheet: macro_state
    Rows: 0
    Columns: 4

... （共 11 個分頁）

Scan Complete - 11 sheets with data
```

✅ 如果顯示 11 個分頁，表示連接成功！

---

## 📊 v3.1 標準分頁詳細說明

### **第一層：情報與總經感知層**

#### `intel_events` - 外部情報事件
```
日期 | 事件類型 | 位置 | 嚴重程度 | LLM風險分數 | 摘要 | 影響資產

例如：
2026-03-03 | Earthquake | Taiwan | 6 | 45 | 台灣南投淺層地震... | 台灣股票, 台幣
2026-03-02 | News | US | 3 | 25 | Fed 升息預期... | US 債券, 科技股
```

#### `macro_state` - 總經狀態與風險開關
```
日期 | 環境 | risk_on | 備註

例如：
2026-03-03 | expansion | TRUE | 消費強勁，失業率低
2026-02-01 | contraction | FALSE | 衰退信號，降息預期
```

### **第二層：決策與風控層**

#### `orders_queue` - 待執行指令池
```
order_id | 日期 | 策略 | 標的 | 方向 | 數量 | 價格限制 | R1通過 | R2核准 | 狀態 | 備註

例如：
ORD_20260303_001 | 2026-03-03 | ETF輪動 | QQQ | BUY | 10 | 450 | TRUE | TRUE | pending | 等待執行
ORD_20260303_002 | 2026-03-03 | 強勢股 | AAPL | SELL | 5 | 220 | FALSE | FALSE | rejected | MDD超限
```

#### `risk_incidents` - 風控攔截日誌
```
日期 | 策略 | 原因代碼 | 冷卻截止

例如：
2026-03-01 | 動能美股 | MDD_EXCEEDED | 2026-03-04
2026-02-28 | 強勢股 | LOSS_STREAK_3 | 2026-03-01
```

### **第三層：交易歸因與績效層**

#### `strategies` - 策略主檔
```
策略名稱 | 起始資金 | 資金比例 | 券商 | 狀態 | 類型 | 風險等級 | MDD限制 | 單筆限制 | 備註

例如：
ETF輪動 | 100000 | 40% | IBKR | active | momentum | medium | -15% | -2000 | 每週檢查
強勢股 | 100000 | 30% | IBKR | active | momentum | high | -20% | -3000 | 技術面進場
```

#### `trades` - 交易主表
```
交易ID | 日期 | 進場時間 | 出場時間 | 券商 | 標的 | 方向 | 進場價 | 出場價 | 數量 | 狀態 | 策略 | 進場原因 | 出場原因 | 損益 | 損益% | 幣別 | 來源 | 備註

例如：
T_20260303_001 | 2026-03-03 | 2026-03-03 09:30 | 2026-03-03 14:00 | IBKR | QQQ | BUY | 450 | 455 | 10 | closed | ETF輪動 | 突破20日高 | 止利 | 50 | 1.1% | USD | FILL|IBKR | 成功出場
```

#### `daily_nav` - 每日淨值表
```
日期 | 策略 | 淨值倍數 | 淨值USD | 日報酬% | 累積報酬% | MDD% | Sharpe | 現金 | 持倉值 | 總值 | 備註

例如：
2026-03-03 | ETF輪動 | 1.05 | 105000 | 0.5% | 5.0% | -8.5% | 1.2 | 10000 | 95000 | 105000 | 運行中
```

### **第四層：券商事實層（唯讀，自動同步）**

#### `broker_snapshot` - 帳戶快照
```
時間 | 券商 | 淨清算值 | 現金總額 | 融資股權 | 幣別 | 台幣換算 | 備註

例如：
2026-03-03 23:59 | IBKR | 205000 | 10000 | 195000 | USD | NT$6,500,000 | 日終快照
```

#### `broker_positions` - 即時持倉
```
時間 | 券商 | 代碼 | 證券類型 | 交易所 | 幣別 | 數量 | 平均成本 | 市場價值 | 備註

例如：
2026-03-03 | IBKR | QQQ | STK | NASDAQ | USD | 10 | 450 | 4550 | 持倉中
```

#### `broker_fills` - 原始成交紀錄
```
執行ID | 時間 | 券商 | 代碼 | 方向 | 股數 | 成交價 | 幣別 | 手續費 | 凈金額 | 訂單ID | 備註

例如：
IBKR_20260303_001 | 2026-03-03 09:31 | IBKR | QQQ | BUY | 10 | 450 | USD | -2.5 | -4502.5 | ORD_001 | 自動成交
```

#### `sync_logs` - 同步日誌
```
時間 | 同步類型 | 券商 | 新增筆數 | 狀態 | 錯誤訊息 | 備註

例如：
2026-03-03 16:00 | positions | IBKR | 2 | success |  | 日常同步
2026-03-03 15:30 | fills | IBKR | 1 | success |  | 自動同步
```

---

## ✅ 完成檢查清單

完成以下所有項目表示遷移成功：

- [ ] 新 Sheets 已建立（11 個標準分頁）
- [ ] strategies 資料已複製（8 個策略）
- [ ] trades 資料已複製（9 筆交易）
- [ ] daily_nav 資料已複製（17 天歷史）
- [ ] broker_* 分頁已複製（positions, snapshot, fills）
- [ ] .env 配置已更新（新 Sheets ID）
- [ ] simple_scan_sheets.py 驗證成功（11 個分頁）
- [ ] Python 模組可正常讀取新 Sheets

---

## 🔄 後續工作

### 立即
1. **新增 intel_events 數據** - 開始記錄市場風險事件
2. **新增 macro_state 數據** - 定期更新總經狀態
3. **完善 risk_incidents** - 記錄被風控攔截的訂單

### 本週
1. **實現自動 daily_nav 計算** - 通過 nav_calculator.py
2. **實現 orders_queue → broker_fills 流程** - Mac → Windows
3. **實現風控 R1/R2 檢查** - 自動在 orders_queue 中標記

### 本月
1. **集成決策引擎** - 自動產生交易信號
2. **集成 AI 評分** - LLM 風險評估
3. **實現自動資金配置** - 根據績效調整 allocation_pct

---

## 💡 Q&A

**Q: 舊 Sheets 怎麼辦？**
A: 保留作為備份。建議重命名為 `實盤交易管理_備份_202603` 以區分。

**Q: 如果遷移中出錯怎麼辦？**
A: 舊 Sheets 還在，可以隨時回退。新 Sheets 出問題可以刪除重新來過。

**Q: Python 模組需要修改嗎？**
A: 不需要。sheets_utils.py 會讀取 .env 的 GOOGLE_SHEET_KEY，改個配置就行。

**Q: 什麼時候才能用新 Sheets？**
A: 數據遷移完成並驗證後，改 .env 配置，立即切換使用。

---

**祝遷移順利！🚀**

有任何問題隨時問。
