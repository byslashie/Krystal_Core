# 🎨 統一儀表板啟動指南

## 概述

已將 **波斯灣油輪監測系統** 與現有的 **port 5000 Flask 應用** 統一為一個儀表板。

| 功能 | 位置 | 訪問地址 |
|------|------|---------|
| 📊 投資組合 | 儀表板首頁 | http://localhost:5000 |
| 🚢 波斯灣油輪 | 導航菜單 | http://localhost:5000 (選擇菜單) |
| 💹 實盤交易 | 導航菜單 | http://localhost:5000 (選擇菜單) |
| 📁 策略管理 | 導航菜單 | http://localhost:5000 (選擇菜單) |

---

## 🚀 快速啟動 (3 步)

### 步驟 1: 安裝依賴

```bash
# 如果還沒有安裝 ship_monitoring 的依賴
pip install -r ship_monitoring/requirements.txt
```

### 步驟 2: 配置環境

編輯 `.env` 檔案，確保包含：

```bash
# Google Sheets
GOOGLE_SHEET_NAME=實盤交易管理
GOOGLE_SHEET_KEY=your_sheet_id
GOOGLE_APPLICATION_CREDENTIALS=credentials.json

# Telegram（如果要啟用告警）
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 步驟 3: 啟動應用

```bash
# Mac/Linux
python app_html_flask.py

# Windows (PowerShell)
python app_html_flask.py

# 訪問
# 瀏覽器打開：http://localhost:5000
```

---

## 🎨 UI/UX 統一說明

所有頁面使用 **紫藍科技感設計**：

- **主色**：#6B21A8 (紫色)
- **輔助色**：#06B6D4 (青色)
- **背景**：深色主題（#1a1f3a）
- **圓角**：12px 統一設計

### 頁面導航

```
┌─────────────────────────────────────────────────────┐
│ 💎 Krystal AI 交易系統                              │
├─────────────────────────────────────────────────────┤
│ [📊 投資組合] [🚢 波斯灣油輪] [💹 實盤] [📁 策略]    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [側邊欄]                  [主內容區域]              │
│  • 時間範圍                 • 頁面標題               │
│  • 風險級別                 • 關鍵指標               │
│  • 系統狀態                 • 圖表 & 表格            │
│                           • 操作按鈕               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 📊 波斯灣油輪監測頁面功能

### 1️⃣ 統計卡片
```
🚢 監測油輪    📍 波斯灣內    🔴 24h 告警    ⚠️ 嚴重事件
   12          8              3              1
```

### 2️⃣ 實時地圖
- Leaflet.js 交互式地圖
- 油輪位置標記（綠=移動, 黃=停止）
- 波斯灣邊界標示

### 3️⃣ 實時告警日誌
- 過去 24 小時的所有事件
- 顏色編碼：🔴 紅(高)、🟡 黃(中)、🟢 綠(低)

### 4️⃣ 油輪列表
表格顯示：
- 船名
- MMSI
- 速度(節)
- 位置(經緯度)
- 狀態(移動/停止)
- 船旗(國家)

### 5️⃣ 控制面板
- 🔄 手動刷新
- ⏱️ 自動刷新切換（30秒）
- ❓ 幫助

---

## 🔌 後台數據同步

即使儀表板不運行，以下服務也可獨立運行：

```bash
# 後台持續監測油輪（不需要 Flask）
cd ship_monitoring
python service.py --mode continuous

# 或同時啟動監測 + 儀表板
python run_ship_monitor.py --parallel
```

---

## 🛠️ 故障排除

### 問題：無法訪問 http://localhost:5000

**檢查步驟**：
1. 確認 Flask 應用已啟動
```bash
ps aux | grep app_html_flask.py
```

2. 檢查 port 5000 是否被占用
```bash
# Windows
netstat -ano | findstr :5000

# Mac/Linux
lsof -i :5000
```

3. 查看日誌
```
Console 應顯示：
[*] Flask 應用啟動...
[*] 訪問: http://localhost:5000
```

### 問題：波斯灣油輪頁面加載失敗

**檢查步驟**：
1. 確認 ship_monitoring 模組已安裝
```bash
python -c "from ship_monitoring.ais_scraper import fetch_gulf_tankers; print('OK')"
```

2. 檢查 API 端點
```bash
curl http://localhost:5000/api/ship-monitoring/statistics
# 應返回 JSON 結果
```

3. 檢查網路連接（AIS Hub API）
```bash
python -c "from ship_monitoring.ais_scraper import fetch_gulf_tankers; print(fetch_gulf_tankers())"
```

### 問題：儀表板顯示「加載中...」

這通常表示：
1. API 連接緩慢（檢查網路）
2. AIS Hub API 無回應（稍等片刻重試）
3. 啟用調試模式查看詳情
```bash
# 編輯 app_html_flask.py，改為
# app.run(debug=True, port=5000)
```

---

## 📈 性能優化

### 啟用緩存（減少 API 呼叫）

編輯 `ship_monitoring/config.py`：
```python
SCRAPER_CONFIG = {
    "update_interval": 60,  # 改為 60 秒（預設 30 秒）
}
```

### 限制儀表板刷新

JavaScript 中修改自動刷新間隔：
```javascript
autoRefreshInterval = setInterval(() => loadShipMonitorPage(), 60000); // 改為 60 秒
```

---

## 🔐 安全性

✅ **本地運行**：所有操作均在 localhost 進行
✅ **無外部洩露**：數據僅存儲在用戶的 Google Sheets
✅ **隔離網絡**：Mac 端決策，Windows 端執行（物理隔離）
✅ **風控審核**：R1 風控模塊把關所有交易指令

---

## 🎯 下一步

### 立即可做
1. ✅ 啟動統一儀表板
2. ✅ 配置 Telegram 告警（可選）
3. ✅ 驗證油輪數據同步

### 下周實施
4. 在 M1 模塊中集成 `get_latest_intel_risk()` 邏輯
5. 在 S5 模塊中自動觸發對沖指令
6. 端到端集成測試

### 未來優化
7. 在 3D Globe Dashboard (Next.js) 中展示油輪位置
8. 添加衛星影像數據層
9. 支援多個監測區域

---

## 📞 聯繫支援

- 📖 詳細文檔：`SHIP_MONITORING_QUICK_START.md`
- 🔗 整合指南：`SHIP_MONITORING_INTEGRATION_PANOPTICON.md`
- 📝 實施總結：`SHIP_MONITORING_IMPLEMENTATION_SUMMARY.md`

---

**🎉 統一儀表板已準備就緒！**

訪問 **http://localhost:5000** 開始監測全球油輪與管理投資組合。

