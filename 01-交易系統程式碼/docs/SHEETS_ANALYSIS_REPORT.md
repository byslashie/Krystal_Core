# 📊 Google Sheets 架構掃描與整理報告

**掃描日期**：2026-03-03
**當前狀態**：14 個分頁，共 ~450+ 筆資料

---

## 🔍 掃描結果概覽

### ✅ 已有的分頁（符合 v3.1 的有 7 個）

| # | 分頁名稱 | 筆數 | 欄位數 | 狀態 | 備註 |
|---|---------|------|--------|------|------|
| 1 | **trades** | 9 | 18 | ✅ 主核心 | 交易主表，有進出場時間 |
| 2 | **daily_nav** | 17 | 18 | ✅ 主核心 | 每日淨值表，含策略名稱 |
| 3 | **strategies** | 8 | 12 | ✅ 主核心 | 策略主檔，有資金配置 |
| 4 | **broker_positions** | 13 | 8 | ✅ 第四層 | 即時持倉（IBKR） |
| 5 | **broker_snapshot** | 23 | 7 | ✅ 第四層 | 帳戶快照（23 天歷史） |
| 6 | **broker_fills** | 6 | 13 | ✅ 第四層 | 原始成交紀錄（6 筆） |
| 7 | **sync_logs** | 152 | 6 | ✅ 第四層 | 同步日誌（152 筆，大部分 failed） |

### ❌ 缺少的分頁（必須新建）

根據 v3.1 資料字典，以下 4 個分頁**完全缺少**：

| # | 分頁名稱 | 說明 | 優先級 |
|---|---------|------|--------|
| 1 | **intel_events** | 外部情報事件（地震、新聞等） | 🔴 高 |
| 2 | **macro_state** | 總經狀態與 risk_on 開關 | 🔴 高 |
| 3 | **orders_queue** | 待執行指令池（Mac→Windows） | 🔴 高 |
| 4 | **risk_incidents** | 風控攔截日誌與冷卻紀錄 | 🟠 中 |

### ⚠️ 多出來的分頁（建議清理或備份）

| # | 分頁名稱 | 筆數 | 建議 | 理由 |
|---|---------|------|------|------|
| 1 | **大盤配置** | 4 | 備份/整合 | 市場環境配置，應整合入 macro_state |
| 2 | **「trades」的副本** | 16 | 刪除 | 重複資料，測試用 |
| 3 | **強勢個股歸因分析-7x7** | 7 | 備份 | 交易分析矩陣，應移至 analysis sheet |
| 4 | **round_trips** | 1 | 評估 | 往返交易配對，可作為 trades 的衍生表 |
| 5 | **(未命名 sheet - 亂碼)** | 13 | 刪除 | 垃圾數據，無用 |
| 6 | **monthly_strategy_report** | 0 | 刪除 | 空檔案，預留但未使用 |
| 7 | **daily_nav_old** | 42 | 備份 | 舊版 NAV 數據，應另存備份檔 |

---

## 📋 欄位結構分析

### 1. **trades** 分頁（現有 9 筆）
**現有欄位**：
- `id`, `日期`, `券商`, `標的`, `方向`, `進場價`, `出場價`
- `數量`, `狀態`, `策略`, `進場原因`, `出場原因`, `備註`
- `entry_time`, `exit_time`, `currency`, `source`, `pnl`

**評價**：✅ 結構良好，涵蓋 v3.1 所有必需欄位

**缺失**：
- `id` 應為 unique key（目前混用 `F_877...` 和 `T001` 等格式）
- `source` 欄位有數據但用途不清

---

### 2. **daily_nav** 分頁（現有 17 筆）
**現有欄位**：
- `日期`, `策略`, `NAV`, `日報酬`, `累積報酬`, `value`
- `realized_pnl`, `unrealized_pnl`, `cash`, `position_value`
- `broker`, `account`, `mode`, `source`, `備註`, `啟始淨值`

**評價**：✅ 資料完整，包含策略級別的淨值追蹤

**建議**：
- 統一 `NAV` 的計算邏輯（目前都是 1.0，表示沒有計算）
- 新增 `MDD`（最大回撤）欄位，用於風控監控

---

### 3. **strategies** 分頁（現有 8 個策略）
**現有欄位**：
- `策略名稱`, `起始資金`, `貨幣`, `參與券商`, `狀態`
- `策略類型`, `風險等級`, `策略說明`, `最大單筆`, `使用的標的`
- `NAV更新`, `備註`

**評價**：✅ 包含基本配置，但缺少

**缺失**：
- 策略的「初始資金分配比例」（應與 allocator.py 連動）
- 策略的「風控參數」（MDD 上限、停損邏輯等）

---

### 4. **sync_logs** 分頁（現有 152 筆）
**關鍵發現** 🔴：
- **大量失敗** (`status = failed`)
- 主要失敗原因：`"broker_fills missing keys: ['時間', '券商']"`

**解釋**：
- broker_fills 的 key 是英文（timestamp, broker）
- 但 sync_logs 期望中文（時間、券商）
- 造成同步流程中斷

**建議**：修復 broker_fills 和其他 sheets 的欄位命名一致性

---

## 🚨 當前系統問題與瓶頸

### 🔴 問題 1：欄位命名混亂
- 中文 vs 英文混用（日期/date、時間/timestamp、券商/broker）
- 導致跨 sheet 同步失敗

### 🔴 問題 2：缺少決策與風控層
- 沒有 `intel_events`（無法記錄外部風險事件）
- 沒有 `orders_queue`（Mac 無法將指令傳給 Windows）
- 沒有 `risk_incidents`（無法追蹤被攔截的訂單）

### 🟠 問題 3：資金流向不清晰
- `daily_nav` 的 `NAV` 欄都是 1.0，沒有實際計算
- 無法追蹤策略資金曲線的變化
- 無法自動計算 MDD（最大回撤）

### 🟠 問題 4：備份與舊數據混亂
- `daily_nav_old`（42 筆舊資料）
- `「trades」的副本`（重複數據）
- 應另外存放在「備份」sheet

---

## ✅ 建議的整理方案

### **第 1 階段：新建缺少的 4 個分頁**（高優先級）

```
1. intel_events
   欄位：date | event_type | location | severity | llm_risk_score | summary | impact_assets

2. macro_state
   欄位：date | regime | risk_on | notes

3. orders_queue
   欄位：order_id | date | strategy | symbol | side | quantity | price_limit | r1_pass | r2_approved | status | note

4. risk_incidents
   欄位：date | strategy | reason_code | cool_down_until
```

### **第 2 階段：欄位命名統一化**（中等優先級）

建立欄位命名規範：
- **日期/時間**：使用 `timestamp` (英文) 或統一用 `date`
- **券商**：統一用 `broker`（英文）
- **標的代碼**：統一用 `symbol`（英文）
- **方向**：統一用 `side`（BUY/SELL，英文）

受影響的 sheets：
- [ ] trades - 改用英文欄位
- [ ] daily_nav - 改用英文欄位
- [ ] broker_positions - 已是英文 ✅
- [ ] broker_snapshot - 改用英文欄位
- [ ] broker_fills - 已是英文 ✅

### **第 3 階段：清理多餘分頁**（低優先級）

1. **備份現有數據**
   ```
   新建 sheet: "_BACKUP_2026_03_03"
   - 複製 「trades」的副本 → _BACKUP_2026_03_03
   - 複製 daily_nav_old → _BACKUP_2026_03_03
   - 複製 強勢個股歸因分析 → _BACKUP_2026_03_03
   ```

2. **刪除多餘分頁**
   - 刪除：「trades」的副本
   - 刪除：(未命名亂碼 sheet)
   - 刪除：monthly_strategy_report（空檔案）
   - 保留：daily_nav_old（用途待評估）

3. **整合優化**
   - 「大盤配置」→ 遷移至 macro_state
   - 「強勢個股歸因分析」→ 建新 sheet: analysis_matrix
   - round_trips → 考慮作為 trades 的檢視表

---

## 💰 資金管理部分的改進

### 現有狀況
- ✅ strategies 有初始資金（8 個策略）
- ✅ daily_nav 有淨值追蹤（17 天歷史）
- ✅ broker_snapshot 有帳戶資產（23 天歷史）
- ❌ 缺少「資金配置建議」欄位
- ❌ 缺少「風控參數」（MDD 上限、停損點）

### 建議改進
1. **在 strategies 中新增欄位**
   - `allocation_pct`：當前資金分配比例（%）
   - `mdd_limit`：最大回撤限制（%）
   - `max_single_loss`：單筆最大虧損（$）
   - `cool_down_days`：冷卻天數（當 MDD 超限時）

2. **在 daily_nav 中新增欄位**
   - `mdd_pct`：該策略的最大回撤（%）
   - `allocation_change`：該日的資金配置變化

3. **新建 capital_allocation sheet**
   - date | strategy | allocated_capital | allocation_pct | reason
   - 用來記錄每次資金重配的決策日誌

---

## 📅 建議的整理時程

| 時程 | 任務 | 工作量 | 風險 |
|------|------|--------|------|
| **第 1 天** | 新建 4 個缺少分頁 + 欄位定義 | 1-2 小時 | 低 |
| **第 2 天** | 遷移「大盤配置」→ macro_state | 30 分鐘 | 低 |
| **第 3 天** | 統一欄位命名（trades/daily_nav/etc） | 2-3 小時 | 中（需驗證資料） |
| **第 4 天** | 備份 + 刪除多餘分頁 | 1 小時 | 低 |
| **第 5 天** | 驗證同步流程（sync_logs） | 1-2 小時 | 中 |

---

## 🔗 與 Python 模組的銜接

### 目前的同步流程

```
yuanta_api.py → broker_fills（成交紀錄）
                    ↓
            sync_logs（記錄同步狀態）
            ❌ 但經常失敗！

broker_positions 和 broker_snapshot 也有類似問題
```

### 建議的新流程

```
1. Mac 端（MacIB）
   - 讀取 strategies（決策參數）
   - 執行策略計算 S1-S8
   - 寫入 orders_queue（待執行指令）

2. Windows 端（WinYuanta）
   - 讀取 orders_queue
   - R1 風控檢查 → 寫入 r1_pass
   - 執行訂單 → 寫入 broker_fills
   - 更新 broker_positions

3. 日終結算
   - 讀取 broker_fills + broker_positions
   - 計算 daily_nav（通過 nav_calculator.py）
   - 寫入 daily_nav
   - 評估是否觸發 risk_incidents（R2 檢查）
```

---

## ✨ 下一步行動建議

### 立即可做
- [ ] 新建 4 個缺少分頁（intel_events, macro_state, orders_queue, risk_incidents）
- [ ] 驗證現有 sheets 的欄位與樣本數據是否正確

### 本週完成
- [ ] 統一欄位命名（中文 → 英文）
- [ ] 修復 sync_logs 的失敗原因
- [ ] 備份舊數據

### 下週完成
- [ ] 測試完整的資料流（Mac → orders_queue → Windows → broker_fills）
- [ ] 實現自動的 daily_nav 計算
- [ ] 實現風控 R1/R2 邏輯

---

## 📎 相關檔案

- `sheets_utils.py` - Sheets API 工具
- `nav_calculator.py` - 淨值計算
- `scan_sheets_schema.py` / `simple_scan_sheets.py` - 掃描工具
- `SHEETS_CLEANUP_GUIDE.md` - 整理指南

**祝你整理順利！** 🚀
