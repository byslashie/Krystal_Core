# 🚀 V3.1 遷移快速參考卡

## 一句話總結
用新 Sheets 替換舊的，乾淨、標準、無混亂。舊的留作備份。

---

## 5 分鐘快速步驟

### 1️⃣ 建立新 Sheets
```
https://sheets.google.com → 建立 → 命名為「實盤交易管理_v3.1_新版」
記下 ID（URL 中 /d/ 後的字串）
```

### 2️⃣ 自動新增分頁
```bash
cd "g:/我的雲端硬碟/Krystal_AI_Trading_System"
python create_new_sheets_v3_1.py <SHEET_ID>
```

### 3️⃣ 遷移數據（複製貼上）
```
舊 Sheets → strategies（全選複製） → 新 Sheets → A2 貼上
舊 Sheets → trades（全選複製） → 新 Sheets → A2 貼上
...其他 sheets 重複相同步驟
```

### 4️⃣ 更新 .env
```
GOOGLE_SHEET_KEY=新的_ID
GOOGLE_SHEET_NAME=實盤交易管理_v3.1_新版
```

### 5️⃣ 驗證
```bash
python simple_scan_sheets.py
# 應該看到 11 個分頁，沒有錯誤
```

---

## 11 個標準分頁一覽

| # | 分頁 | 筆數 | 優先級 | 說明 |
|---|-----|------|--------|------|
| 1 | **intel_events** | - | 🔴高 | 外部風險事件 |
| 2 | **macro_state** | - | 🔴高 | 總經狀態 |
| 3 | **orders_queue** | - | 🔴高 | Mac 待執行指令 |
| 4 | **risk_incidents** | - | 🟠中 | 風控攔截日誌 |
| 5 | **strategies** | 8 | 🔴高 | 策略配置 ✅ |
| 6 | **trades** | 9 | 🔴高 | 交易紀錄 ✅ |
| 7 | **daily_nav** | 17 | 🔴高 | 每日淨值 ✅ |
| 8 | **broker_snapshot** | 23 | 🟠中 | 帳戶快照 ✅ |
| 9 | **broker_positions** | 13 | 🟠中 | 即時持倉 ✅ |
| 10 | **broker_fills** | 6 | 🟠中 | 成交紀錄 ✅ |
| 11 | **sync_logs** | 0 | 🟠中 | 同步日誌 |

✅ = 需要從舊 Sheets 複製
- = 新建後開始使用

---

## 遷移時間表

```
Day 1:
├─ 09:00 建立新 Sheets (5 min)
├─ 09:05 執行 create_new_sheets_v3_1.py (3 min)
└─ 09:10 驗證 11 個分頁 (5 min)

Day 2:
├─ 09:00 複製 strategies (10 min)
├─ 09:10 複製 trades (10 min)
├─ 09:20 複製 daily_nav (10 min)
└─ 09:30 複製 broker_* (20 min)

Day 3:
├─ 09:00 驗證數據完整性 (15 min)
├─ 09:15 更新 .env (5 min)
└─ 09:20 測試 Python 連接 (10 min)

✅ Done! 預計 1-2 小時完成
```

---

## 檔案位置

| 文件 | 用途 |
|------|------|
| `create_new_sheets_v3_1.py` | 自動建立分頁 |
| `MIGRATION_TO_V3_1.md` | 詳細遷移指南 |
| `simple_scan_sheets.py` | 驗證工具 |
| `SHEETS_ANALYSIS_REPORT.md` | 舊 Sheets 分析 |
| `.env` | 配置文件（需更新） |

---

## 常見問題

**Q: 新 Sheets 什麼時候可以用？**
A: 數據複製完成並驗證後立即切換。

**Q: 舊 Sheets 刪除嗎？**
A: 不要。留作備份，改名「_BACKUP_」即可。

**Q: Python 要改嗎？**
A: 不用改代碼，只改 .env 的 ID。

**Q: 複製時發現欄位不符怎麼辦？**
A: 參考 MIGRATION_TO_V3_1.md 中的欄位對應表。

---

## 下一步工作

遷移完成後的優先事項：

### 立即（這週）
- [ ] 開始記錄 intel_events（市場風險）
- [ ] 每日更新 macro_state（總經狀態）
- [ ] 測試 orders_queue → broker_fills 流程

### 本週末
- [ ] 實現自動 daily_nav 計算
- [ ] 實現 risk_incidents 自動檢測
- [ ] 驗證所有同步流程

### 下週
- [ ] 集成決策引擎
- [ ] 集成 LLM 風險評分
- [ ] 實現自動資金配置

---

## 緊急回退方案

如果新 Sheets 出問題：

```bash
# 1. 立即停止使用新 Sheets
# 2. 改 .env 的 ID 回到舊 Sheets
# 3. 恢復運行（無資料遺失）

# 新 Sheets 可以刪除重新來過
```

---

## 聯繫方式

有問題隨時問。我已經準備好幫忙：
- 自動化遷移數據
- 修復欄位對應問題
- 調試 Python 連接
- 優化新 Sheets 結構

---

**開始遷移吧！🚀**

執行第一步：打開 Google Sheets 建立新試算表
