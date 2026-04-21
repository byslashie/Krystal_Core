# 📋 Dashboard 修改紀錄

---

## v6 — `index.html` _(進行中 2026-03-21)_

### 新增
- 10 頁完整架構：總覽 / 總經羅盤 / 資金配置 / 投資組合 / 風控 / 交易管理 / 策略管理 / 策略比對 / 績效 / Schwab
- 🌐 **總經羅盤**：財經M平方 5步驟框架、4象限景氣羅盤互動圖、PMI/CPI/非農指標面板
- 💰 **資金配置**：景氣象限自動對應建議配置、凱利公式計算器（含景氣係數調整）
- ⚠️ **風控**：每策略風險明細、凱利倉位利用率進度條、三條紅線警示
- 📁 **策略管理**：分兩區塊（實盤策略 vs 研發策略）、實盤 vs 回測 NAV 曲線對比
- 📊 **策略比對**：多策略 NAV 疊加圖、回測 vs 實盤落差圖、凱利加碼建議
- 💹 **交易管理**：參考 Port 9999 實盤系統、搜尋過濾、策略標籤

### 修改
- 頁面順序重新排列（宏觀→部位→執行→回顧）
- 移除側邊欄「時間範圍」和「風險級別」控件
- 總覽頁新增景氣象限標示 + 風控警示摘要

---

## v5 — `mockup_v5_multipage.html` _(2026-03-21)_

### 新增
- 8 頁多頁切換架構（首次實現頁面路由）
- 每頁點擊導覽列即切換，帶 fade-in 動畫
- Chart.js 4.4 圖表懶加載（切換到該頁才初始化）
- 💼 投資組合：Yahoo Finance API 走勢比較（0050.TW / ^TWII + 自訂輸入）
- 📊 資產配置圓餅圖加上方圖例文字
- 今日損益區塊加入「🔔 記錄今日」按鈕
- 總覽頁加入「💼 當前持倉」表格（活躍策略之前）

### 修改
- Port 從 1234 → 9999（app_html_flask.py）

---

## v4 Pro — `mockup_v4_pro.html` _(2026-03-21)_

### 新增
- 亮色 / 暗色主題切換（🌙/☀️，localStorage 記憶）
- HSL 色彩系統（ui-ux-pro-max skill 設計規範）
- Inter + JetBrains Mono 字型
- 主題切換時圖表自動重建（顏色跟著更新）
- 即時時鐘（JetBrains Mono 顯示）
- 移除側邊欄時間範圍 / 風險級別

### 設計來源
- [ui-ux-pro-max skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) — 161色盤、fintech dashboard 規範
- [visualize skill](https://github.com/careerhackeralex/visualize) — dark/light/auto 主題架構

---

## v4 — `mockup_v4.html` _(2026-03-21)_

### 新增
- 第一版深色主題 Mockup（暗色）
- 基於 v3_260320 模板架構重新設計
- Plotly.js 圖表（走勢、配置、損益）
- 黃色虛線框標示「v4 新增設計點」
- 按券商分欄持倉（IB / 元大）
- 雙幣別 P&L 追蹤（USD + TWD 雙 Y 軸）

---

## v3 — `../dashboard_v3_260320/` _(2026-03-20)_

### 新增
- Flask 模板繼承架構（base.html + 7 子頁）
- 多頁路由：portfolio / risk / allocation / performance / trading / strategies
- 側邊欄：時間範圍 / 風險級別 / Broker 同步按鈕
- 每日損益追蹤（IB USD + 元大 TWD 雙 Y 軸圖）
- 按券商分類持倉表（IB + 元大）

---

## v2 — `../DashboardV2.html` _(歷史版本)_

- 基礎 Flask HTML 版本
- 單頁結構
- 基本 KPI 卡片 + 持倉表

---

## 待辦（v6 完成後）

- [ ] 串接 Port 9999 真實 API（/api/metrics、/api/holdings、/api/strategies）
- [ ] 總經羅盤指標從 MacroMicro API 自動拉取
- [ ] 凱利計算器數值從策略歷史交易自動計算
- [ ] 策略管理回測結果從 Google Sheets 讀取
- [ ] PWA 支援（手機可安裝）
- [ ] 暗色/亮色主題記憶 per-user
