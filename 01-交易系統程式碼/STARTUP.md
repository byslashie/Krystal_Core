# 🚀 交易系統啟動指南

## 快速開始（3 步）

### 步驟 1：檢查環境

```bash
# 確認 Python 環境已就緒
python --version          # 應該是 3.9+
.venv_yuanta32\Scripts\python.exe --version  # 32-bit Python for Yuanta
```

### 步驟 2：啟動 Flask 主進程（命令窗口 1）

```bash
cd "g:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"
python app_html_flask.py
```

**預期輸出**：
```
 * Running on http://127.0.0.1:5000
 * Debug mode: off
```

### 步驟 3：啟動 IB 後台進程（命令窗口 2）

```bash
cd "g:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"
python workers/ib_background_worker.py
```

**預期輸出**：
```
[IB Worker] Starting IB background worker...
[IB Worker] Connected to IB Gateway at 127.0.0.1:7496
[IB Worker] Polling every 10 seconds...
```

### 步驟 4：啟動 Yuanta 後台進程（命令窗口 3）

```bash
cd "g:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"
python workers/yuanta_background_worker.py
```

**預期輸出**：
```
[Yuanta Worker] 元大背景查詢進程已啟動
[Yuanta Worker] 同步時間：每日台灣時間 09:15
[Yuanta Worker] 檢查間隔：60 秒
```

### 步驟 5：打開瀏覽器

訪問：`http://localhost:5000/dashboard_v6/index.html`

---

## 完整啟動流程

### 前置需求

#### 1. **Python 環境**
```bash
# 檢查主 Python
python --version  # 需要 3.9+

# 檢查 32-bit Python (元大用)
.venv_yuanta32\Scripts\python.exe --version
```

#### 2. **IB Gateway 運行**
- 確保 **IB Gateway** 已啟動（或 IB TWS）
- 地址：127.0.0.1:7496（查看 IB 設置確認）
- **狀態檢查**：在 [IB 網關頁面](https://127.0.0.1:7496) 看到 "Connected" 字樣

#### 3. **Google Sheets 認證**
```bash
# 確認 credentials.json 存在
ls key/credentials.json  # 若無，請放入該文件
```

#### 4. **.env 配置**
```bash
# 檢查 .env 文件
cat .env | grep -E "IB_|YUANTA_|GOOGLE_"
```

應該看到類似：
```env
IB_HOST=127.0.0.1
IB_PORT=7496
IB_CLIENT_ID=99

YUANTA_ENV=PROD
YUANTA_ACCOUNT=D222061405
YUANTA_PASSWORD=xxxxx

GOOGLE_SHEET_KEY=1zpehl1bAZitFiQqMg7IcGWsPQxdhnQDhAeNtRvxzwn8
```

---

### 啟動順序（重要！）

#### 推薦順序

```
1️⃣ IB Gateway (外部應用)
    ↓
2️⃣ Flask 主進程 (命令窗口 1)
    ↓
3️⃣ IB 後台進程 (命令窗口 2)
    ↓
4️⃣ Yuanta 後台進程 (命令窗口 3)
    ↓
5️⃣ 打開瀏覽器訪問儀表板
```

#### 為什麼這個順序？

| 進程 | 等待誰 | 說明 |
|------|--------|------|
| IB Gateway | 無 | 外部應用，需先啟動 |
| Flask | IB Gateway（可選） | 可以先啟動，後面才連 IB |
| IB Worker | Flask + IB Gateway | 需要 Flask 的 API，IB Gateway 的連接 |
| Yuanta Worker | 無硬性依賴 | 獨立進程，可在任何時候啟動 |
| 瀏覽器 | 所有後台進程 | 等待前面的進程都準備好 |

---

## 各進程詳細啟動

### 進程 1：Flask 主服務器

**文件**：`app_html_flask.py`

**啟動命令**：
```bash
cd "g:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"
python app_html_flask.py
```

**檢查清單**：
- [ ] 看到 `Running on http://127.0.0.1:5000`
- [ ] 沒有錯誤信息
- [ ] APScheduler 已初始化（會輸出 "APScheduler started"）

**常見問題**：
```
問題：Address already in use
原因：端口 5000 被佔用
解決：
  1. 殺死舊進程：taskkill /F /IM python.exe
  2. 或改用其他端口：FLASK_PORT=5001 python app_html_flask.py
```

**停止方式**：按 `Ctrl+C`

---

### 進程 2：IB 後台查詢進程

**文件**：`workers/ib_background_worker.py`（需創建）

**啟動命令**：
```bash
cd "g:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"
python workers/ib_background_worker.py
```

**檢查清單**：
- [ ] 看到 `[IB Worker] Starting IB background worker...`
- [ ] 看到 `[IB Worker] Connected to IB Gateway`
- [ ] 每 10 秒看到一次 `[IB Worker] Polling...`

**常見問題**：
```
問題：Connection refused to IB Gateway
原因：IB Gateway 未啟動
解決：
  1. 打開 IB Gateway（或 TWS）
  2. 確認監聽地址是 127.0.0.1:7496
  3. 檢查防火牆

問題：asyncio RuntimeError
原因：多個 ib_insync 進程衝突
解決：
  1. 只保留一個 IB Worker 進程
  2. 殺死其他 python.exe：taskkill /F /IM python.exe /T
```

**停止方式**：按 `Ctrl+C`

---

### 進程 3：Yuanta 後台定時同步進程

**文件**：`workers/yuanta_background_worker.py`

**啟動命令**：
```bash
cd "g:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"
python workers/yuanta_background_worker.py
```

**檢查清單**：
- [ ] 看到 `[Yuanta Worker] 元大背景查詢進程已啟動`
- [ ] 看到 `[Yuanta Worker] 同步時間：每日台灣時間 09:15`
- [ ] 每 60 秒看到一次 `[Yuanta Worker] 檢查 #...`

**功能**：
- 每天 09:15 台灣時間自動檢查並執行同步
- 使用 32-bit Python 運行 `sync_yuanta_positions.py`
- 日誌記錄到 `logs/yuanta_worker.log`

**常見問題**：
```
問題：找不到 32-bit Python
原因：.venv_yuanta32 未正確設置
解決：
  1. 確認 .venv_yuanta32 目錄存在
  2. 重新創建環境：python -m venv .venv_yuanta32
```

**停止方式**：按 `Ctrl+C`

---

### 進程 4：元大庫存手動同步（按需）

**手動同步方式**：
- 方法 1：打開儀表板，點「🔄 同步」按鈕（推薦）
- 方法 2：命令行直接運行
  ```bash
  .venv_yuanta32\Scripts\python.exe brokers/sync_yuanta_positions.py
  ```

**說明**：
- 後台進程每日 09:15 自動同步
- 可隨時手動觸發以獲取最新數據
- 手動同步不會影響後台進程的自動調度

---

## 驗證系統運行狀態

### 1. 檢查 Flask 服務

```bash
# 在瀏覽器打開（或用 curl）
http://localhost:5000/api/health
```

預期回應：
```json
{"status": "ok", "timestamp": "2026-03-23T10:15:30"}
```

### 2. 檢查 IB 連接

打開儀表板 → 交易管理頁面 → 查看 IB 帳戶卡片

預期顯示：
- 帳戶權益：$xxxxx
- 現金：$xxxxx
- 浮盈：$xxxxx
- 持倉數：X

### 3. 檢查元大連接

打開儀表板 → 交易管理頁面 → 查看元大帳戶卡片

預期顯示：
- 帳戶權益：¥xxxxx
- 現金：¥xxxxx
- 浮盈：¥xxxxx
- 持倉數：X

### 4. 檢查 Google Sheets

訪問 [Google Sheets](https://docs.google.com/spreadsheets/d/1zpehl1bAZitFiQqMg7IcGWsPQxdhnQDhAeNtRvxzwn8)

檢查以下表單：
- `broker_positions`：最新持倉數據
- `sync_logs`：同步日誌
- `daily_nav`：日均資產淨值

---

## 使用快速啟動腳本 (Windows)

### 方式 1：批處理腳本

創建 `startup_all.bat`：
```batch
@echo off
cd /d "%~dp0"

REM Kill old processes
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

REM Start Flask in window 1
start "Krystal Trading - Flask" python app_html_flask.py

REM Wait for Flask to start
timeout /t 3 /nobreak

REM Start IB Worker in window 2
start "Krystal Trading - IB Worker" python workers/ib_background_worker.py

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start Yuanta Worker in window 3
start "Krystal Trading - Yuanta Worker" python workers/yuanta_background_worker.py

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Open browser
start http://localhost:5000/dashboard_v6/index.html

echo.
echo ========================================
echo 啟動完成！
echo.
echo 📍 Flask 服務:     http://localhost:5000
echo 📊 仪表板:        http://localhost:5000/dashboard_v6/index.html
echo 🔌 IB Worker:    [獨立進程運行中]
echo 📈 Yuanta Worker: [獨立進程運行中，每日 09:15 同步]
echo.
echo ========================================
echo.
pause
```

**使用方式**：
```bash
# 雙擊 startup_all.bat 或命令行執行
startup_all.bat
```

### 方式 2：PowerShell 腳本（待創建）

---

## 日誌查看

### Flask 日誌
```
日誌位置：終端窗口輸出
查看命令：在 Flask 窗口中查看實時輸出
```

### IB Worker 日誌
```
日誌位置：終端窗口輸出 + logs/ib_worker.log
查看命令：
  tail -f logs/ib_worker.log
```

### 元大同步日誌
```
日誌位置：Google Sheets (sync_logs 表單)
查看方式：打開 Google Sheets，進入 sync_logs 分頁
```

---

## 關閉系統

### 正常關閉

1. **關閉瀏覽器**（可選）
2. **終止 IB Worker**：在 IB Worker 窗口按 `Ctrl+C`
3. **終止 Flask**：在 Flask 窗口按 `Ctrl+C`
4. **關閉命令窗口**

### 強制關閉（緊急情況）

```bash
# 殺死所有 Python 進程
taskkill /F /IM python.exe /T
```

---

## 常見啟動問題排查表

| 症狀 | 可能原因 | 解決方案 |
|------|---------|---------|
| Flask 無法啟動 | 依賴缺失 | 運行 `pip install -r requirements.txt` |
| IB Worker 連接失敗 | IB Gateway 未啟動 | 打開 IB Gateway 或 TWS |
| Yuanta Worker 無法啟動 | 32-bit Python 未設置 | 確認 `.venv_yuanta32` 存在並正確 |
| 儀表板顯示空白 | Flask 未啟動或端口錯誤 | 檢查 `http://localhost:5000` 是否可訪問 |
| IB 數據不更新 | IB Worker 未啟動 | 啟動 IB Worker 進程 |
| 元大數據未同步（非 09:15） | Yuanta Worker 未啟動 | 啟動 Yuanta Worker 進程 |
| 元大同步失敗 | 憑證問題或登入失敗 | 檢查 .env 中的帳戶和密碼，查看 `logs/yuanta_worker.log` |
| Google Sheets 連接失敗 | SSL 或認證問題 | 檢查 credentials.json 和網絡連接 |

---

## 後續監控

### 定期檢查

- **每天開盤前**：確認 Flask + IB Worker 運行
- **09:15 前後**：檢查元大同步是否完成
- **每小時**：檢查 IB 數據是否更新
- **每週**：查看 Google Sheets 中的完整日誌

### 告警設置（待實現）

- [ ] IB 連接中斷時通知
- [ ] 元大同步失敗時通知
- [ ] 異常交易時通知

---

**版本**: 2.0
**最後更新**: 2026-03-23
**維護者**: Krystal
