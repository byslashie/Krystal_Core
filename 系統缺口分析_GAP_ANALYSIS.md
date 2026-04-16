# Krystal 交易系統缺口分析
> 掃描日期：2026-03-20 ｜ 系統版本：v1.0

---

## 總覽

| 層級 | 模組數 | 已完成 | 部分完成 | 空殼/未實作 |
|------|--------|--------|----------|------------|
| Broker 整合 | 3 | 2 (IB, Yuanta) | 1 (Schwab) | 0 |
| 核心模組 | 10 | 2 | 2 | 6 |
| UI 頁面 | 5 | 5 | 0 | 0 |
| 通知系統 | 1 | 0 | 1 (ship only) | 0 |
| 分類器 | 3 | 0 | 0 | 3 |

---

## 🔴 嚴重缺口（空殼模組 — 0 行程式碼）

### 1. `modules/risk_control.py` — 風控引擎
**為什麼重要：** 這是保護資金最關鍵的防線。目前完全靠手動紀律，沒有自動保護。

缺少功能：
- [ ] 最大回撤（MDD）自動觸發暫停交易
- [ ] 每日最大虧損截斷（Daily Stop-Loss）
- [ ] 單策略部位上限檢查
- [ ] 緊急平倉訊號

---

### 2. `modules/allocator.py` — 資金分配器
**為什麼重要：** S1~S6 六個策略之間如何分配資金完全沒有程式邏輯，目前靠手動判斷。

缺少功能：
- [ ] 各策略初始權重設定
- [ ] 動態再平衡觸發（偏離閾值 > X%）
- [ ] 現金緩衝區保留邏輯
- [ ] 總部位上限控制（不超過淨值某%）

---

### 3. `modules/notifier.py` — 通知系統
**為什麼重要：** 目前 Telegram 通知只存在於 `ship_monitoring/`，整個交易系統沒有統一通知框架。

缺少功能：
- [ ] 交易執行通知（成交確認）
- [ ] 風控觸發告警
- [ ] 每日 NAV 摘要推送
- [ ] 策略訊號通知
- [ ] 錯誤/異常告警

---

### 4. `modules/econ_classifier.py` — 總經分類器
**為什麼重要：** M1（總經循環）、M2（季節性）、N3（技術面）的文件寫得非常完整，但完全沒有對應程式。策略切換目前 100% 手動。

缺少功能：
- [ ] M1 — 總經循環判斷（擴張/過熱/衰退/復甦）
- [ ] M2 — 季節性因子（月份/節假日效應）
- [ ] N3 — 技術面訊號（均線、動能指標）
- [ ] 三者綜合輸出「市場情境」標籤
- [ ] 情境 → 策略切換對應表

---

### 5. `modules/monte_carlo.py` — 蒙地卡羅模擬
**為什麼重要：** `nav_calculator.py` 有框架但主體未實作，無法做風險模擬與策略壓力測試。

缺少功能：
- [ ] 歷史報酬隨機抽樣
- [ ] N 次模擬路徑生成
- [ ] 95% / 99% VaR 計算
- [ ] 最差情境 MDD 分佈圖

---

### 6. `modules/perf_tracker.py` — 績效追蹤器
**為什麼重要：** 目前績效數據需要手動上傳 CSV，沒有自動從券商抓取成交記錄的機制。

缺少功能：
- [ ] 自動從 IB/Yuanta 抓取每日成交
- [ ] 策略標籤貼附（哪筆交易屬於哪個策略）
- [ ] 滾動式 Win Rate / Sharpe 計算
- [ ] 績效數據自動寫入 Google Sheets

---

### 7. `modules/gpt_summary.py` — AI 摘要
**為什麼重要：** 系統設計有此節點，但未實作。

缺少功能：
- [ ] 每日市場狀況 AI 摘要
- [ ] 每週策略績效 AI 解讀
- [ ] 異常警示事件說明

---

### 8. `modules/channel_plot.py` — KPI 通道圖
**為什麼重要：** UI 頁面有引用此模組但無內容，導致視覺化功能不完整。

缺少功能：
- [ ] Bollinger-style KPI 通道視覺化
- [ ] 報酬/風險指標趨勢圖

---

## 🟡 部分實作（有程式碼但功能不完整）

### 9. `modules/decision_engine.py` — 決策引擎（現況：226 行）
缺少功能：
- [ ] 只有 1 條規則（Oil_Supply_Shock_Risk → BUY XLE），需要擴充至所有 intel_events 類型
- [ ] 沒有與 `econ_classifier.py` 整合（情境輸入 → 決策輸出）
- [ ] 沒有訊號優先級排序邏輯
- [ ] 沒有互斥訊號處理（買賣訊號衝突時的處理）

---

### 10. `brokers/schwab_api.py` — Schwab 券商（現況：~150 行 skeleton）
缺少功能：
- [ ] OAuth 流程完整實作（Token refresh 尚未測試）
- [ ] 帳戶資訊查詢
- [ ] 持倉同步到 Google Sheets
- [ ] 下單功能
> **注意：** 目前是等待 Schwab API 審核通過後才能繼續

---

### 11. 績效追蹤（自動化）
缺少功能：
- [ ] 每日自動從 IB 抓取成交（目前手動上傳 CSV）
- [ ] 策略標籤自動對應
- [ ] NAV 自動更新（目前需手動在 Google Sheets 填寫）

---

## 🟠 架構問題（非空殼，但設計缺陷）

### 12. 缺乏 Broker 抽象層
**現狀：** IB、Yuanta、Schwab 三個接口格式各自不同，UI 直接呼叫 broker API。
**影響：** 難以測試、難以新增第四個券商、UI 與業務邏輯耦合。
**建議：** 建立 `brokers/base_broker.py` 定義統一介面（`get_positions()`, `get_executions()`, `place_order()`）。

---

### 13. 策略切換邏輯缺失
**現狀：** M1/M2/N3 分類器文件寫得很完整（在 `02-策略知識庫/Classifier/`），但沒有對應的程式邏輯連接到策略切換。
**影響：** 市場情境改變時，策略切換完全靠交易者手動判斷，無法自動化。

---

### 14. 通知系統分散
**現狀：** Telegram Bot 邏輯只在 `ship_monitoring/` 裡，整個主交易系統沒有通知。
**影響：** 交易執行、風控觸發、NAV 異常都無法即時收到推播。
**建議：** 實作 `modules/notifier.py` 並讓 ship_monitoring 也改用它。

---

### 15. 缺乏統一 Logging
**現狀：** 程式碼充斥 `print()` debug 輸出（尤其是 `yuanta_api.py`、`sync_ib_*.py`）。
**影響：** 正式環境難以除錯，無法追蹤歷史錯誤。
**建議：** 統一改用 Python `logging` 模組，分 INFO/WARNING/ERROR 層級。

---

## 優先實作建議

```
優先級 1（保護資金）
└── risk_control.py  ← 最緊急

優先級 2（系統能跑起來）
├── allocator.py
├── perf_tracker.py（自動化部分）
└── notifier.py

優先級 3（智慧化）
├── econ_classifier.py  ← 把現有 M1/M2/N3 文件轉成程式
├── decision_engine.py 規則擴充
└── monte_carlo.py

優先級 4（錦上添花）
├── gpt_summary.py
├── channel_plot.py
└── Broker 抽象層重構
```

---

## 檔案位置索引

| 模組 | 路徑 |
|------|------|
| risk_control | `01-交易系統程式碼/modules/risk_control.py` |
| allocator | `01-交易系統程式碼/modules/allocator.py` |
| notifier | `01-交易系統程式碼/modules/notifier.py` |
| econ_classifier | `01-交易系統程式碼/modules/econ_classifier.py` |
| monte_carlo | `01-交易系統程式碼/modules/monte_carlo.py` |
| perf_tracker | `01-交易系統程式碼/modules/perf_tracker.py` |
| decision_engine | `01-交易系統程式碼/modules/decision_engine.py` |
| schwab_api | `01-交易系統程式碼/brokers/schwab_api.py` |
| 總經分類器文件 | `02-策略知識庫/Classifier/` |
| ship_monitoring (Telegram 參考) | `01-交易系統程式碼/ship_monitoring/` |
