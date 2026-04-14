# 實施計畫 (Implementation Plan) - 實盤系統優化與元大 API 接軌

## 1. 儀表板效能優化 (Dashboard Performance)
### 問題：
目前 Dashboard 載入時會序列 (Serial) 讀取多個 Google Sheets 分頁，加上 `daily_nav` 同步時採用逐行更新，導致耗時過長。

### 解決方案：
1. **並行讀取 (Parallel Loading)**：
   - 在 `pages/1_實盤交易管理系統.py` 引入 `concurrent.futures.ThreadPoolExecutor`。
   - 建立並行載入函式，同時抓取 `strategies`, `daily_nav`, `trades`, `round_trips`, `broker_positions`。
2. **批次更新 (Batch Update)**：
   - 修改 `sync_daily_nav_real_per_strategy` 函式。
   - 使用 `gspread` 的 `sh.batch_update()` 或將所有更新合併為一個巨大的 list 進行一次性寫入，避免 API 請求次數過多被 Rate Limit 或網路延遲。

## 2. 元大券商 API 接軌 (Yuanta API Integration)
### 目前進度：
登入流程已建立，但尚未實作成交回報 (Fills/Execution) 的即時接收與存儲。

### 解決方案：
1. **事件監聽 (Event Handling)**：
   - 在 `brokers/yuanta_api.py` 中利用 pythonnet 註冊 `.NET` 事件：`api.OnExecution`。
   - 建立一個執行期容器類別，用來暫存從 API 送來的成交物件。
2. **資料標準化**：
   - 將元大原始成交物件轉換為專案通用的 CSV/DataFrame 格式。
3. **介面對接**：
   - 在 Streamlit 介面增加「同步元大成交」按鈕，呼叫上述邏輯並更新至 Sheets 的 `broker_fills` 分頁。

## 3. 預期效果
- Dashboard 初始載入速度提升 50% 以上。
- `daily_nav` 同步時間從分鐘級縮短至秒級。
- 實現元大成交資料自動化同步，不再需要手動補單。
