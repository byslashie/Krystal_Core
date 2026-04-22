# 📊 Krystal 交易系統：Google Sheets 完整分頁與欄位手冊

本文件詳細記錄了 Krystal 交易系統中 Google Sheets 各分頁的定義、欄位意義及計算邏輯。

---

## 1. 帳戶層級淨值紀錄 (`daily_nav_account`)
**用途**：追蹤整體帳戶資產變化，用於繪製總資產曲線。

| 欄位名稱 | 意義 | 計算邏輯與來源 |
| :--- | :--- | :--- |
| **date** | 紀錄日期 | 腳本執行當日的日期 (YYYY-MM-DD)。 |
| **yuanta_mv_twd** | 元大總市值 (TWD) | `broker_positions` 中所有 `broker='yuanta'` 的 `marketValue` 總和。 |
| **yuanta_pnl_twd** | 元大未實現損益 (TWD) | `broker_positions` 中所有 `broker='yuanta'` 的 `unrealizedPNL` 總和。 |
| **ib_mv_usd** | IB 總市值 (USD) | `broker_positions` 中所有 `broker='ib'` 的 `marketValue` 總和。 |
| **ib_pnl_usd** | IB 未實現損益 (USD) | `broker_positions` 中所有 `broker='ib'` 的 `unrealizedPNL` 總和。 |
| **schwab_mv_usd** | Schwab 總市值 (USD) | `broker_positions` 中所有 `broker='schwab'` 的 `marketValue` 總和。 |
| **schwab_pnl_usd** | Schwab 未實現損益 (USD) | `broker_positions` 中所有 `broker='schwab'` 的 `unrealizedPNL` 總和。 |
| **total_mv_twd** | **全帳戶總市值 (TWD)** | `yuanta_mv_twd + (ib_mv_usd + schwab_mv_usd) * usd_twd_rate`。 |
| **total_pnl_twd** | **全帳戶總損益 (TWD)** | `yuanta_pnl_twd + (ib_pnl_usd + schwab_pnl_usd) * usd_twd_rate`。 |
| **usd_twd_rate** | 使用匯率 | 目前程式內固定為 `32.0`。 |

*   **更新來源**：`brokers/record_daily_nav.py`

---

## 2. 策略層級績效紀錄 (`daily_nav_strategy`)
**用途**：追蹤個別交易策略的表現與淨值 (NAV)。

| 欄位名稱 | 意義 | 計算邏輯與來源 |
| :--- | :--- | :--- |
| **日期** | 紀錄日期 | 該筆紀錄對應的交易日期。 |
| **策略** | 策略名稱 | 來自 `strategies` 設定的名稱。 |
| **幣別** | 策略貨幣 | USD 或 TWD。 |
| **起始資金** | 策略本金 | 來自 `strategies` 的原始投入資金。 |
| **value** | **當前總資產** | `起始資金 + 累積已實現損益 + 當前未實現損益`。 |
| **NAV** | **單位淨值** | `value / 起始資金`。起始值為 1.0。 |
| **日報酬** | 當日報酬率 | `(今日NAV / 昨日NAV) - 1`。 |
| **累積報酬** | 總回報率 | `NAV - 1`。 |
| **realized_pnl** | 累計已實現損益 | 從 `round_trips` 或 `trades` 統計該策略歷史總盈虧。 |
| **unrealized_pnl**| 當前未實現損益 | 從 `broker_positions` 統計該策略目前持倉損益。 |
| **cash** | 策略剩餘現金 | `value - position_value`。 |
| **position_value**| 持倉市值 | 該策略目前持有的部位總市值。 |
| **broker** | 所屬券商 | 該策略主要的下單券商。 |
| **account** | 帳號 | 所屬券商帳號。 |
| **mode** | 模式 | REAL (實盤) 或 PAPER (模擬)。 |
| **source** | 來源 | 寫入此資料的系統模組。 |
| **更新時間** | 資料更新時間 | 寫入 Google Sheets 的精確時間。 |

*   **更新來源**：Streamlit 儀表板「同步」功能。

---

## 3. 即時持倉快照 (`broker_positions`)
**用途**：系統所有部位的單一真實來源 (SSOT)。

| 欄位名稱 | 意義 | 計算邏輯與來源 |
| :--- | :--- | :--- |
| **timestamp** | 更新時間 | 部位同步的精確時間。 |
| **broker** | 券商 | 元大、IB 或 Schwab。 |
| **symbol** | 標的代碼 | 股票、ETF 或期權代碼。 |
| **position** | 持股數量 | 目前持有股數。 |
| **avgCost** | 平均持倉成本 | 平均買入成本。 |
| **marketPrice** | 當前市價 | 同步時的即時市場價格。 |
| **marketValue** | 市值 | `position * marketPrice`。 |
| **unrealizedPNL** | 未實現損益 | `(marketPrice - avgCost) * position`。 |

*   **更新來源**：`brokers/sync_yuanta_positions.py` (元大), `app_html_flask.py` (IB/Schwab)。

---

## 4. 其他輔助分頁
| 分頁名稱 | 功能說明 |
| :--- | :--- |
| **`trades`** | **交易日誌**：記錄所有進出場動作與原因。 |
| **`strategies`** | **策略定義**：設定本金、狀態、帳號等參數。 |
| **`broker_snapshot`**| **帳戶摘要**：記錄各帳戶購買力與現金餘額。 |
| **`broker_fills`** | **成交明細**：券商 API 回傳的原始成交紀錄。 |
| **`sync_logs`** | **同步日誌**：監控 API 同步狀態。 |
| **`orders_queue`** | **訂單隊列**：待執行的交易訊號。 |

---

## ⚙️ 計算與同步流程
1.  **同步層**：各券商 API 將即時數據寫入 `broker_positions`。
2.  **彙總層**：`record_daily_nav.py` 從 `broker_positions` 計算總資產並寫入 `daily_nav_account`。
3.  **分析層**：Streamlit 整合持倉、本金與歷史交易，計算策略 NAV 並寫入 `daily_nav_strategy`。

---
*文件更新日期：2026-04-22*
