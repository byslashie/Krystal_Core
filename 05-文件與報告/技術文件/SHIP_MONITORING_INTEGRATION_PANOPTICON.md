# 🌐 船舶監測 ↔ Project Panopticon 整合指南

## 📍 系統位置

波斯灣油輪監測系統是 **Project Panopticon** 架構中的 **INTEL-1 層** 的重要組成部分：

```
┌──────────────────────────────────────────────────────────────┐
│                    macOS (全視界大腦)                         │
│                                                              │
│  [ INTEL 層 ]                                               │
│  ├─ INTEL-1: OSINT 爬蟲                                      │
│  │  ├─ GDELT 新聞爬蟲 ✅                                     │
│  │  ├─ USGS 天災爬蟲 ✅                                      │
│  │  └─ 🚢 波斯灣油輪監測 ← YOU ARE HERE                      │
│  │                                                          │
│  └─ INTEL-2: 本地 Ollama (Llama3)                           │
│     └─ 評估所有 INTEL-1 信號 → 0-100 風險分數              │
│                                                              │
│  [ 交易邏輯層 ]                                              │
│  ├─ M1: 總經模組 (訂閱 INTEL-2 風險信號)                    │
│  └─ S5: 空頭對沖策略 (被動觸發)                             │
└──────────────────────────────────────────────────────────────┘
           ↓ (Google Sheets Message Bus)
┌──────────────────────────────────────────────────────────────┐
│         Google Sheets (核心資料庫與事件總線)                  │
│  - intel_events (新增 ship_movement 事件)                    │
│  - ship_tracking (新增分頁)                                  │
│  - macro_state (M1 輸出)                                     │
│  - orders_queue (S5 輸出)                                    │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 數據流向

```
┌─────────────────────────────────────────────────────────────┐
│         波斯灣油輪監測服務 (ship_monitoring/)                │
│  - AIS Hub API → 每 30 秒拉取油輪位置                       │
│  - 檢測異常：進/出區域、停止、速度變化                     │
│  - Telegram 告警推送                                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ [自動寫入]
                 ↓
┌─────────────────────────────────────────────────────────────┐
│         Google Sheets: ship_tracking 分頁                   │
│  timestamp | vessel_name | mmsi | latitude | longitude ...  │
│  2026-03-04 26:30 | PACIFIC OCEAN | 636012814 | 26.5 | 52.5│
│  2026-03-04 26:31 | ASIAN GLORY   | 211378570 | 27.2 | 51.8│
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ [每 1 分鐘檢查一次]
                 ↓
┌─────────────────────────────────────────────────────────────┐
│      Google Sheets: intel_events 分頁 (ship_movement)       │
│  date | event_type | location | severity | llm_risk_score   │
│  2026-03-04 26:33 | ship_movement | 波斯灣 (636012814) |  │
│               90 | 85 | 油輪停止不動 60 分鐘，供應中斷風險   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ [M1 & S5 訂閱讀取]
                 ↓
┌─────────────────────────────────────────────────────────────┐
│      M1 總經模組 (m1_macro_classifier.py)                   │
│  讀取 intel_events → 若風險分數 > 80 → risk_on = False      │
│  寫入 macro_state: "High_Risk_Event"                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ [自動觸發]
                 ↓
┌─────────────────────────────────────────────────────────────┐
│      S5 對沖策略 (s5_hedging.py)                            │
│  偵測到 M1 = High_Risk_Event                                │
│  impact_assets = "Oil, Energy ETFs, XLE, USO"              │
│  自動生成對沖指令：買入 SQQQ 100 股 (做空納斯達克)          │
│  寫入 orders_queue (status=pending, r1_pass=False)         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ [R1 風控檢查]
                 ↓
┌─────────────────────────────────────────────────────────────┐
│      R1 風控引擎 (r1_risk_engine.py)                        │
│  檢查系統 MDD、連虧次數                                     │
│  若通過 → r1_pass = True → 轉移至 Windows 執行              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 實施步驟

### Phase 1️⃣：確保 ship_monitoring 運作

1. **安裝依賴**
   ```bash
   pip install -r ship_monitoring/requirements.txt
   ```

2. **配置 Telegram**
   ```bash
   # .env 中設定
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

3. **啟動監測服務**
   ```bash
   cd ship_monitoring
   python service.py --mode continuous
   ```

4. **驗證數據流入 Google Sheets**
   - 檢查 `ship_tracking` 分頁是否有新記錄
   - 檢查 `intel_events` 分頁是否有 "ship_movement" 事件

---

### Phase 2️⃣：擴充 M1 模組（讀取船舶信號）

編輯 `brain/m1_macro_classifier.py`，添加船舶風險評估：

```python
# 在 m1_macro_classifier.py 中添加

from sheets_utils import get_latest_intel_risk

class MacroClassifier:
    def __init__(self):
        self.risk_threshold = 80  # 風險分數閾值

    def classify(self):
        """分類總經狀態"""

        # 1. 讀取最新的 intel_risk (包括船舶監測信號)
        latest_risk = get_latest_intel_risk(hours=24)

        if latest_risk is None:
            latest_risk = 50  # 預設中性

        logger.info(f"📊 最近 24h 最高風險分數：{latest_risk}")

        # 2. 若風險分數 > 80，觸發高風險狀態
        if latest_risk > self.risk_threshold:
            logger.warning(f"🚨 高風險事件！分數：{latest_risk}")

            # 讀取具體事件（例如船舶停止）
            df_intel = read_intel_events()
            high_risk_events = df_intel[df_intel['llm_risk_score'] > 80]

            if not high_risk_events.empty:
                for idx, event in high_risk_events.iterrows():
                    logger.warning(f"⚠️ {event['event_type']}: {event['summary']}")

            # 設定 risk_on = False
            self.regime = "high_risk"
            self.risk_on = False  # 轉向防守

            return {
                "regime": "high_risk",
                "risk_on": False,
                "notes": f"高風險事件（船舶/地緣政治），暫停進場",
                "trigger_events": [e['event_type'] for e in high_risk_events.values]
            }

        # 3. 正常情況
        return {
            "regime": "normal",
            "risk_on": True,
            "notes": "正常交易",
        }
```

### Phase 3️⃣：擴充 S5 對沖策略（自動生成對沖指令）

編輯 `brain/s5_hedging.py`，訂閱船舶監測事件：

```python
# 在 s5_hedging.py 中添加

from sheets_utils import write_order_to_queue, read_intel_events

class HedgingStrategy:
    def __init__(self):
        self.hedge_symbols = {
            "Oil": ["USO", "XLE"],           # 石油相關
            "Energy": ["XLE", "SLV"],        # 能源相關
            "Tech": ["SQQQ", "PSQ"],         # 科技空頭
        }

    def check_ship_movement_alerts(self):
        """檢查船舶監測告警，生成對沖指令"""

        df_intel = read_intel_events()

        # 篩選最近的船舶事件（過去 2 小時）
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(hours=2)
        df_intel['date'] = pd.to_datetime(df_intel['date'], errors='coerce')

        ship_events = df_intel[
            (df_intel['event_type'] == 'ship_movement') &
            (df_intel['date'] > cutoff) &
            (df_intel['llm_risk_score'] > 75)
        ]

        if ship_events.empty:
            logger.info("✅ 無需對沖：波斯灣油輪狀態正常")
            return []

        logger.warning(f"🚨 偵測到 {len(ship_events)} 個高風險船舶事件，生成對沖指令")

        orders = []

        for idx, event in ship_events.iterrows():
            risk_score = float(event['llm_risk_score'])
            impact_assets = str(event.get('impact_assets', '')).split(',')

            # 根據影響資產選擇對沖工具
            if 'Oil' in impact_assets or 'Energy' in impact_assets:
                # 石油供應中斷 → 買 USO（賭油價上漲）或 XLE（能源 ETF）
                symbol = "USO"
                side = "BUY"
                quantity = int(risk_score / 20) * 10  # 風險越高買越多
                reason = f"石油供應風險 (風險分數:{risk_score})"

            elif 'Tech' in impact_assets or risk_score > 85:
                # 地緣政治風險高 → 做空科技股（SQQQ）
                symbol = "SQQQ"
                side = "BUY"
                quantity = int(risk_score / 25) * 5
                reason = f"地緣政治對沖 (風險分數:{risk_score})"

            else:
                continue

            # 生成指令
            order = {
                "order_id": f"S5_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "date": datetime.now().isoformat(),
                "strategy": "S5_hedging",
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price_limit": None,  # 市價單
                "r1_pass": False,  # 待 R1 檢查
                "status": "pending",
                "note": reason,
            }

            # 寫入 orders_queue
            write_order_to_queue(order)
            logger.info(f"✅ 生成對沖指令：{symbol} {side} {quantity} 股 ({reason})")

            orders.append(order)

        return orders
```

### Phase 4️⃣：更新 R1 風控引擎（把關對沖指令）

`brain/r1_risk_engine.py` 已在現有系統中，確保它能讀取 S5 生成的對沖指令：

```python
# r1_risk_engine.py 中確保包含以下邏輯

def check_orders():
    """檢查 orders_queue 中的待執行指令"""

    df_queue = read_orders_queue()
    pending_orders = df_queue[df_queue['status'] == 'pending']

    for idx, order in pending_orders.iterrows():
        # 獲取系統 MDD
        mdd = calculate_system_mdd()

        if mdd > 10:  # MDD 超過 10%
            logger.warning(f"❌ 拒絕指令 {order['order_id']}：系統 MDD {mdd}% > 10%")
            update_order_status(order['order_id'], 'rejected', '系統 MDD 超限')
            continue

        # 檢查連虧
        consecutive_losses = check_consecutive_losses(order['strategy'])
        if consecutive_losses >= 3:
            logger.warning(f"❌ 拒絕指令：{order['strategy']} 連虧 {consecutive_losses} 次")
            update_order_status(order['order_id'], 'rejected', '連虧超限')
            continue

        # 通過檢查
        logger.info(f"✅ 指令 {order['order_id']} 通過 R1 檢查")
        update_order_status(order['order_id'], 'pending', r1_pass=True)
```

---

## 📊 Google Sheets 配置

確保你的 Google Sheets 包含以下分頁（Project Panopticon v3.1 標準）：

### 必要分頁清單

| 分頁 | 層級 | 欄位 | 用途 |
|------|------|------|------|
| `intel_events` | INTEL-1 | date, event_type, location, severity, llm_risk_score, summary, impact_assets | 存儲所有情報信號（包括 ship_movement） |
| `ship_tracking` | INTEL-1 | timestamp, vessel_name, mmsi, latitude, longitude, speed, status | 存儲船舶位置歷史 |
| `macro_state` | M1 | date, regime, risk_on, notes | M1 的決策輸出 |
| `orders_queue` | S5 | order_id, strategy, symbol, side, quantity, r1_pass, status | 待執行的交易指令 |
| `risk_incidents` | R1 | date, strategy, reason_code, cool_down_until | 風控攔截日誌 |
| `trades` | 執行層 | date, symbol, side, quantity, price | 實際成交紀錄 |
| `daily_nav` | 績效層 | date, nav, daily_return, cumulative_return | 帳戶淨值與績效 |

---

## 🧪 整合測試計畫

### 測試 1️⃣：船舶監測 → intel_events

```bash
# 啟動監測服務
cd ship_monitoring
python service.py --mode once --test

# 驗證
# ✅ Google Sheets intel_events 分頁有新記錄 (event_type = "ship_movement")
# ✅ Telegram 收到告警
```

### 測試 2️⃣：intel_events → M1 決策

```python
# 在 Mac 端運行
from brain.m1_macro_classifier import MacroClassifier
from sheets_utils import get_latest_intel_risk

m1 = MacroClassifier()
risk = get_latest_intel_risk()
print(f"風險分數：{risk}")

result = m1.classify()
print(f"M1 決策：{result}")

# ✅ 若 risk > 80，M1 應返回 risk_on = False
```

### 測試 3️⃣：M1 決策 → S5 對沖

```python
# 在 Mac 端運行
from brain.s5_hedging import HedgingStrategy

s5 = HedgingStrategy()
orders = s5.check_ship_movement_alerts()
print(f"生成 {len(orders)} 個對沖指令")

# ✅ Google Sheets orders_queue 應有新記錄
```

### 測試 4️⃣：S5 指令 → R1 風控

```python
# 在 Mac 端運行
from brain.r1_risk_engine import check_orders

check_orders()

# ✅ 若通過檢查，orders_queue 中的 r1_pass 應改為 True
```

### 測試 5️⃣：整體流程（端到端）

```bash
# 步驟 1: 啟動監測服務（後台）
cd ship_monitoring
python service.py --mode continuous &

# 步驟 2: 每 5 分鐘執行一次 M1 & S5 檢查
# （可配置為 cron job 或 systemd timer）
cd brain
python m1_macro_classifier.py
python s5_hedging.py
python r1_risk_engine.py

# 驗證流程：
# 1. ship_tracking 有最新船舶位置 ✅
# 2. intel_events 有 ship_movement 事件 ✅
# 3. macro_state 显示 risk_on 状态 ✅
# 4. orders_queue 有待執行指令 ✅
# 5. risk_incidents 有風控日誌 ✅
```

---

## 🚀 生產環境部署

### macOS 定時任務（使用 launchd）

建立 `/Library/LaunchAgents/com.krystal.ship-monitor.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.krystal.ship-monitor</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/ship_monitoring/run_ship_monitor.py</string>
        <string>--mode</string>
        <string>continuous</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardErrorPath</key>
    <string>/tmp/ship-monitor.err</string>

    <key>StandardOutPath</key>
    <string>/tmp/ship-monitor.log</string>
</dict>
</plist>
```

啟動：
```bash
launchctl load /Library/LaunchAgents/com.krystal.ship-monitor.plist
```

### Windows 任務排程

1. 開啟「工作排程程式」
2. 建立基本工作 → 「ship-monitor」
3. 觸發：啟動時 + 每 30 秒重複
4. 動作：執行程式 → `python` → 引數：`C:\path\ship_monitoring\run_ship_monitor.py --mode continuous`

---

## 📈 監控儀表板

訪問：**http://localhost:5001**

### 關鍵指標

| 指標 | 含義 | 告警條件 |
|------|------|---------|
| 🚢 監測油輪 | 波斯灣內偵測到的油輪數 | < 3 （可能服務異常）|
| 📍 波斯灣內 | 目前在監測區域內的油輪數 | > 前 24h 平均 +50% |
| 🔴 24h 告警 | 過去 24 小時的告警數 | > 10 (異常頻繁) |
| ⚠️ 嚴重事件 | 高優先級告警 (severity=high) | > 3 |

---

## 🔗 API 集成清單

確保以下 API 都已配置：

- ✅ **AIS Hub** (波斯灣油輪)：`http://www.aishub.net/api/ref/index.php`
- ✅ **Google Sheets API**：讀寫 intel_events, ship_tracking, orders_queue
- ✅ **Telegram Bot API**：推送告警
- ✅ **本地 Ollama** (可選)：INTEL-2 LLM 評分
- ⚙️ **券商 API** (IB/元大)：執行對沖指令

---

## 📞 故障排除

### 問題：ship_tracking 沒有數據

```bash
# 1. 檢查爬蟲是否在運行
ps aux | grep service.py

# 2. 檢查日誌
tail -f ship_monitoring/logs/ship_monitor.log

# 3. 測試爬蟲
python ship_monitoring/ais_scraper.py

# 4. 檢查 Sheets 權限
python -c "from sheets_utils import get_sheet; print(get_sheet('ship_tracking'))"
```

### 問題：M1 沒有讀取到船舶信號

```bash
# 檢查 intel_events 是否有數據
python -c "from sheets_utils import read_intel_events; print(read_intel_events().tail())"

# 檢查 get_latest_intel_risk 函數
python -c "from sheets_utils import get_latest_intel_risk; print(f'Latest risk: {get_latest_intel_risk()}')"
```

### 問題：S5 沒有生成對沖指令

```bash
# 驗證 M1 的 risk_on 狀態
python -c "from sheets_utils import read_macro_state; print(read_macro_state().tail())"

# 檢查 orders_queue
python -c "from sheets_utils import read_orders_queue; print(read_orders_queue())"
```

---

## 🎯 下一步

1. ✅ **安裝船舶監測系統**
2. ✅ **驗證 intel_events 數據流**
3. 📝 **實施 M1 & S5 訂閱邏輯**
4. 🧪 **端到端測試**
5. 🚀 **上線後台服務**
6. 📊 **監控儀表板和指標**

---

**🎉 波斯灣油輪監測已整合至 Project Panopticon！**
