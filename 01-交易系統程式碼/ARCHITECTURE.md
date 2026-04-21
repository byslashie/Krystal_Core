# 交易系統架構設計 (Flask + 後台進程)

## 系統概述

混合架構，結合 **Flask Web 服務**與**獨立後台進程**，避免多線程衝突，同時支持 IB 和元大實時查詢。

```
┌──────────────────────────────────────────────────────────────┐
│              用戶 (瀏覽器 / HTTP)                              │
└────────────────────┬─────────────────────────────────────────┘
                     │
        ┌────────────▼──────────────┐
        │     Flask Web (主進程)     │  port: 5000
        │  - 仪表板 (HTML/JS)       │
        │  - REST API               │
        │  - 讀取 Google Sheets      │
        └────────────┬──────────────┘
                     │
        ┌────────────▼──────────────────────────────────────────┐
        │          Google Sheets (共享數據層)                    │
        │  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐ │
        │  │broker_positions│ sync_logs    │  daily_nav     │ │
        │  └──────────────┘ └──────────────┘ └────────────────┘ │
        └────────────┬───────────────────────────────────────────┘
                     │
      ┌──────────────┴──────────────────────────────┐
      │                                             │
      │                                             │
  ┌───▼────────────────┐              ┌───────────▼──────────┐
  │ 後台進程 A:        │              │ 後台進程 B:          │
  │ IB Gateway 查詢     │              │ 元大庫存定時同步     │
  │                    │              │                     │
  │ • 連接 IB Gateway  │              │ • 32-bit Python    │
  │ • 實時查詢帳戶      │              │ • 每日 09:15 自動   │
  │ • 寫入 broker_     │              │   運行同步腳本      │
  │   positions        │              │ • 寫入 broker_     │
  │ • 每 10 秒更新     │              │   positions        │
  └────────────────────┘              │ • 按需手動同步      │
                                      │   (Flask 按鈕)      │
                                      └────────────────────┘
```

---

## 各層功能詳解

### 1. Flask Web 層 (主進程)

**職責**：
- 提供 Web 界面（dashboard_v6）
- 提供 REST API 端點
- 從 Google Sheets 讀取 IB/元大最新數據
- 觸發後台進程（元大同步按鈕）

**關鍵文件**：
- `app_html_flask.py` - Flask 應用主體
- `dashboard_v6/index.html` - 前端仪表板
- `google_sheets_helper.py` - Google Sheets 工具

**API 端點**：
```
GET  /api/ib-account-summary        → 讀取 Google Sheets 的 IB 數據
GET  /api/yuanta-account-summary    → 讀取 Google Sheets 的元大數據
POST /api/sync-yuanta               → 觸發元大後台同步
```

**狀態**：
- IB 實時查詢被禁用（Flask 線程問題）→ 改由後台進程提供
- 元大手動同步仍由 Flask 觸發 → 由後台進程執行

---

### 2. Google Sheets 數據層

**表單結構**：

#### broker_positions （經紀商持倉）
| 時間 | 券商 | symbol | secType | exchange | currency | position | avgCost |
|------|------|--------|---------|----------|----------|----------|---------|
| 2026-03-23 10:15:30 | 元大 | 0050 | STK | TWSE | TWD | 1000 | 151.68 |
| 2026-03-23 10:15:45 | IB | AAPL | STK | NASDAQ | USD | 50 | 175.23 |

**寫入方式**：
- 元大：`sync_yuanta_positions.py` (後台進程 B)
- IB：`ib_background_worker.py` (後台進程 A，待實現)

---

### 3. 後台進程 A：IB Gateway 查詢

**文件**：`workers/ib_background_worker.py` (待創建)

**功能**：
- 單獨進程運行 ib_insync（解決 Flask 線程問題）
- 連接 IB Gateway (127.0.0.1:7496)
- 每 10 秒自動查詢一次帳戶信息
- 將結果寫入 Google Sheets `broker_positions` 表
- 日誌記錄到 `sync_logs` 表

**啟動方式**：
```bash
python workers/ib_background_worker.py
```

**流程**：
```
1. 啟動 IB 連接 (singleton)
2. 進入無限循環，每 10 秒：
   a. 查詢 account summary
   b. 查詢 positions
   c. 比對 fingerprint（檢查是否變化）
   d. 若變化，寫入 Google Sheets
   e. 紀錄日誌
3. 異常處理：自動重連
```

---

### 4. 後台進程 B：元大庫存定時同步

**文件**：
- `workers/yuanta_background_worker.py` - 後台監視進程（負責定時觸發）
- `brokers/sync_yuanta_positions.py` - 實際同步腳本（被後台進程調用）

**功能**：
- 獨立進程運行（32-bit Python）
- 每天 09:15 台灣時間自動檢查並執行同步
- 調用 `sync_yuanta_positions.py` 實際執行同步
- 支持從 Flask 按鈕進行手動同步（直接調用 sync 腳本）
- 日誌記錄到 `logs/yuanta_worker.log`

**啟動方式**：
```bash
# 後台進程啟動（獨立進程，每日自動同步）
python workers/yuanta_background_worker.py

# 手動同步（臨時，由 Flask 按鈕觸發）
.venv_yuanta32\Scripts\python.exe brokers/sync_yuanta_positions.py
```

**流程**：
```
後台進程每 60 秒檢查一次
  ↓
如果是 09:15±5 分鐘且今天未同步過
  ↓
呼叫 sync_yuanta_positions.py（32-bit Python）
  ↓
登入元大 API → 查詢庫存 → 寫入 Google Sheets
  ↓
標記今天已同步，避免重複
```

---

## 數據流向

### IB 數據流
```
IB Gateway
    ↓
[後台進程 A: ib_background_worker.py]
    ↓
Google Sheets (broker_positions)
    ↓
[Flask] 讀取 /api/ib-account-summary
    ↓
前端顯示 (dashboard_v6)
```

### 元大數據流
```
元大 API
    ↓
[後台進程 B: sync_yuanta_positions.py]
↓ 觸發方式：
  ├─ APScheduler (每日 09:15)
  ├─ Flask 手動按鈕 (/api/sync-yuanta)
  └─ 命令行直接運行
    ↓
Google Sheets (broker_positions)
    ↓
[Flask] 讀取 /api/yuanta-account-summary
    ↓
前端顯示 (dashboard_v6)
```

---

## 進程管理策略

### 本地開發 (Windows)

**啟動順序**：
1. **Flask 主進程**
   ```bash
   cd "g:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"
   python app_html_flask.py
   ```

2. **IB 後台進程**（新開命令窗口）
   ```bash
   cd "g:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"
   python workers/ib_background_worker.py
   ```

3. **訪問網頁**
   ```
   http://localhost:5000/dashboard_v6/index.html
   ```

### 生產環境建議

使用 **Windows Task Scheduler** 或 **Systemd**（Linux）管理後台進程：
- Flask：開機自啟，持續運行
- IB worker：開機自啟，持續運行
- 元大 sync：由 APScheduler 定時觸發（無需獨立進程）

---

## 配置文件

### .env 環境變數
```env
# IB 配置
IB_HOST=127.0.0.1
IB_PORT=7496
IB_CLIENT_ID=99

# 元大配置
YUANTA_ENV=PROD
YUANTA_ACCOUNT=D222061405
YUANTA_PASSWORD=xxxx

# Google Sheets
GOOGLE_SHEET_KEY=1zpehl1bAZitFiQqMg7IcGWsPQxdhnQDhAeNtRvxzwn8
```

---

## 故障排查

### IB 後台進程無法連接
```
問題：連接超時
原因：IB Gateway 未運行或端口錯誤
解決：
  1. 確認 IB Gateway 已啟動 (127.0.0.1:7496)
  2. 檢查防火牆設置
  3. 查看 IB Gateway 日誌
```

### 元大查詢失敗 (ResultNo=7)
```
問題：尚未登入
原因：
  1. 帳戶填充問題（已修復）
  2. 憑證異常 (RtnCode=141)
  3. 會話過期
解決：
  1. 檢查 .env 中的帳戶和密碼
  2. 檢查 Windows Cert Store 憑證
  3. 增加登入等待時間
```

### Google Sheets 連接失敗
```
問題：SSL 超時
原因：網絡連接問題
解決：
  1. 檢查網絡連接
  2. 檢查 credentials.json 權限
  3. 重新認證 Google Sheets API
```

---

## 未來擴展

1. **Streamlit 管理面板** - 額外的監控和管理工具
2. **WebSocket 實時推送** - 用 WebSocket 替代輪詢，提升性能
3. **多經紀商支持** - 添加 Charles Schwab、東證等
4. **告警系統** - 位置變化時自動通知
5. **績效分析** - 基於 Google Sheets 數據的分析儀表板

---

**最後更新**: 2026-03-23
**維護者**: Krystal
**版本**: 2.0 (Flask + Background Workers)
