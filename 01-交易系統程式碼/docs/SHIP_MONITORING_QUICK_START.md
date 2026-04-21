# 🚢 波斯灣油輪監測系統 - 快速開始指南

## 📋 系統功能概述

- ✅ **實時 AIS 數據爬蟲**：每 30 秒自動更新波斯灣油輪位置
- ✅ **智能異常檢測**：進/出區域、速度異常、長時間停止
- ✅ **Telegram 即時告警**：高優先級事件立即推送
- ✅ **實時儀表板**：交互式地圖 + 告警日誌
- ✅ **Google Sheets 集成**：自動存儲到 `ship_tracking` 和 `intel_events` 分頁
- ✅ **Project Panopticon 支持**：作為 INTEL-1 層自動饋送 M1/S5 決策引擎

---

## 🔧 第 1 步：Telegram 設定（5 分鐘）

### 1.1 建立 Bot

1. 在 Telegram 中找 **@BotFather**
2. 發送 `/newbot`
3. 按提示設定名稱和用戶名
4. **保存 Token**（格式：`123456789:ABCDEFGHIJKLMNOPqrstuvwxyz`）

### 1.2 獲取 Chat ID

訪問瀏覽器：
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe
```

向 Bot 發送任何訊息，然後訪問：
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

複製 JSON 中的 `"id"` 值（例如：`-123456789`）

### 1.3 保存到 .env

編輯 `.env` 檔案：
```bash
TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPqrstuvwxyz
TELEGRAM_CHAT_ID=-123456789
```

---

## 🚀 第 2 步：安裝依賴

```bash
# 創建虛擬環境
python -m venv .venv_ship

# 激活
# Windows:
.venv_ship\Scripts\activate
# Mac/Linux:
source .venv_ship/bin/activate

# 安裝依賴
pip install -r ship_monitoring/requirements.txt
```

如果沒有 `requirements.txt`，手動安裝：
```bash
pip install requests python-telegram-bot gspread google-auth-oauthlib google-auth-httplib2 pandas flask leaflet
```

---

## 📊 第 3 步：配置 Google Sheets

在現有的 Google Sheets 中新增兩個分頁（如果還沒有）：

### 分頁 1：`ship_tracking`
```
timestamp | vessel_name | mmsi | imo | vessel_type | flag | latitude | longitude | speed | heading | last_update | status | alert_type
```

### 分頁 2：`intel_events`（如果用於 Project Panopticon）
```
date | event_type | location | severity | llm_risk_score | summary | impact_assets
```

---

## ▶️ 第 4 步：啟動系統

### 選項 A：單次掃描（測試）
```bash
cd ship_monitoring
python service.py --mode once --test
```

### 選項 B：連續監測（後台服務）
```bash
cd ship_monitoring
python service.py --mode continuous
```

### 選項 C：啟動實時儀表板
```bash
cd ship_monitoring
python dashboard.py
```

訪問：**http://localhost:5001**

---

## 🗺️ 第 5 步：查看儀表板

地址：**http://localhost:5001**

### 儀表板功能：
- 🗺️ **左側地圖**：波斯灣油輪實時位置（綠=移動，黃=停止）
- 📢 **右側告警面板**：過去 24 小時的所有告警
- 📊 **統計卡片**：監測油輪數、在區域內數量、告警統計
- 🔄 **刷新按鈕**：手動更新數據

---

## 🧪 第 6 步：測試 Telegram 告警

運行測試：
```bash
cd ship_monitoring
python -c "
from telegram_alerter import TelegramAlerter
alerter = TelegramAlerter()
if alerter.test_connection():
    print('✅ Telegram 連接成功！')
"
```

如果成功，你會在 Telegram 收到確認訊息。

---

## 📁 文件結構

```
ship_monitoring/
├── __init__.py                    # 模組初始化
├── config.py                      # 配置檔（監測區域、告警規則等）
├── ais_scraper.py                 # AIS 數據爬蟲
├── movement_detector.py           # 移動檢測器
├── telegram_alerter.py            # Telegram 告警器
├── service.py                     # 主監測服務
├── dashboard.py                   # Flask 儀表板
├── templates/
│   └── ship_dashboard.html        # 前端 HTML
├── static/                        # (自動生成)
└── logs/                          # 日誌目錄
```

---

## 🔐 環境變數完整清單

```bash
# Telegram 配置
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Google Sheets（繼承自現有配置）
GOOGLE_SHEET_NAME=實盤交易管理
GOOGLE_SHEET_KEY=your_sheet_id
GOOGLE_APPLICATION_CREDENTIALS=credentials.json

# 可選開關
DEBUG=False              # 調試模式
MOCK_DATA=False         # 使用模擬數據
SHIP_DATA_SOURCE=aishub # 數據源：aishub, vesseltracker
DISABLE_SHEETS=0        # 禁用 Google Sheets（遇到網路問題時設為 1）
```

---

## 🎯 監測參數

在 `ship_monitoring/config.py` 中自定義：

```python
# 監測區域
GULF_REGION = {
    "lat_min": 25.0,
    "lat_max": 30.0,
    "lon_min": 48.0,
    "lon_max": 57.0,
}

# 告警規則（嚴格模式）
ALERT_RULES = {
    "enter_region": True,           # 進入時告警
    "exit_region": True,            # 離開時告警
    "stationary_duration": 60,      # 停留 60 分鐘告警
    "speed_increase_threshold": 50, # 速度增加 >50% 告警
}

# 爬蟲頻率
SCRAPER_CONFIG = {
    "update_interval": 30,  # 每 30 秒更新
    "request_timeout": 10,  # 超時 10 秒
}
```

---

## 🔗 與 Project Panopticon 整合

船舶監測數據會自動流向 V3 決策引擎：

```
AIS 數據 → ship_tracking (Google Sheets)
         ↓
ship_monitoring/service.py → intel_events (Google Sheets)
         ↓
INTEL-2 (LLM) → 風險評分 (0-100)
         ↓
M1/S5 → 自動生成對沖指令
```

**例如**：若波斯灣油輪大規模停止→石油供應風險→LLM 風險分數 ↑→M1 設定 risk_on=False→S5 自動買入 SQQQ

---

## 📞 常見問題

### Q1: Telegram 消息沒有收到？
**A**:
1. 檢查 `.env` 中的 Token 和 Chat ID
2. 確保已向 Bot 發送過訊息（授權）
3. 執行測試：`python telegram_alerter.py`

### Q2: 無法連接 AIS Hub？
**A**:
1. 檢查網路連接
2. 在 `config.py` 中改為 `MOCK_DATA=True` 進行測試
3. 設置 `DISABLE_SHEETS=1` 避免 Sheets 延遲

### Q3: 地圖上看不到油輪？
**A**:
1. 確認儀表板訪問地址正確：http://localhost:5001
2. 檢查瀏覽器控制台是否有錯誤（F12）
3. 確保 Flask 服務正常運行

### Q4: 如何改變監測區域？
**A**: 編輯 `ship_monitoring/config.py`：
```python
GULF_REGION = {
    "lat_min": 新_南緯,
    "lat_max": 新_北緯,
    "lon_min": 新_西經,
    "lon_max": 新_東經,
}
```

---

## 📚 進階設定

### 自訂告警規則（嚴格 → 寬鬆）

在 `config.py` 中修改：
```python
# 寬鬆模式（只告警重大事件）
ALERT_RULES = {
    "enter_region": False,          # 關閉進入告警
    "exit_region": False,           # 關閉離開告警
    "stationary_duration": 360,     # 只在 6 小時不動時告警
    "speed_increase_threshold": 100,# 速度增加 >100% 才告警
}
```

### 使用不同的 AIS 數據源

```python
# 在 config.py 中
DATA_SOURCE = "vesseltracker"  # 改為其他來源（如果已實現）
```

### 調整爬蟲頻率

```python
SCRAPER_CONFIG = {
    "update_interval": 60,  # 改為 60 秒更新一次
}
```

---

## 🚨 生產環境部署建議

1. **後台運行**（Linux/Mac）：
```bash
nohup python service.py --mode continuous > ship_monitor.log 2>&1 &
```

2. **Windows 任務排程**：
   - 新增排程任務 → 執行：`python service.py --mode continuous`

3. **Docker 容器化**（可選）：
```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r ship_monitoring/requirements.txt
CMD ["python", "ship_monitoring/service.py", "--mode", "continuous"]
```

4. **監控服務健康**：
   - 定期檢查日誌：`tail -f ship_monitoring/logs/ship_monitor.log`
   - Telegram 狀態報告（每小時自動發送）

---

## 📞 支持

- 查看日誌：`ship_monitoring/logs/ship_monitor.log`
- 測試爬蟲：`python ship_monitoring/ais_scraper.py`
- 測試檢測器：`python ship_monitoring/movement_detector.py`
- 測試 Telegram：`python ship_monitoring/telegram_alerter.py`

---

**🎉 系統已準備就緒！享受波斯灣油輪實時監測！**
