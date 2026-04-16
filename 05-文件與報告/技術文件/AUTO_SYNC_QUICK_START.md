# ⚡ 自動同步 5 分鐘快速開始

**目標**：設置 Windows 每天自動同步元大持倉到 Google Sheets

---

## 🚀 一鍵設置（推薦）

### 方式 1：使用 PowerShell 自動配置（最簡單）

**步驟**：

1. **按 `Win + X`，選擇 "Windows PowerShell (管理員)"**

2. **複製並粘貼以下命令**：

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force; cd "g:\我的雲端硬碟\Krystal_AI_Trading_System"; .\setup_task_scheduler.ps1
```

3. **按 Enter，等待完成**

**預期結果**：
```
╔══════════════════════════════════════════════════════════════╗
║  🔄 Windows Task Scheduler 自動配置                         ║
...
✅ 自動同步已成功配置！
═══════════════════════════════════════════════════════════════
📅 同步計劃：每天上午 09:00
📂 日誌位置：g:\...\logs\sync_*.txt
```

---

## ⚙️ 手動設置（如果 PowerShell 失敗）

### 步驟 1：打開工作排程器

1. 按 `Win + R`
2. 輸入 `taskschd.msc`
3. 按 Enter

### 步驟 2：創建基本任務

1. **右側面板** → **創建基本工作**
2. **名稱**：`Krystal AI - 元大持倉自動同步`
3. **描述**：`每天上午 9:00 自動同步元大持倉到 Google Sheets`
4. **點擊 Next**

### 步驟 3：設置觸發器

1. **選擇** "Daily"
2. **時間**：`09:00 AM`（或你想要的時間）
3. **點擊 Next**

### 步驟 4：設置操作

1. **選擇** "Start a program"
2. **程式**：
   ```
   cmd.exe
   ```
3. **參數**：
   ```
   /c "g:\我的雲端硬碟\Krystal_AI_Trading_System\sync_daily.bat"
   ```
4. **啟動目錄**：
   ```
   g:\我的雲端硬碟\Krystal_AI_Trading_System
   ```
5. **點擊 Next**

### 步驟 5：完成設置

1. **勾選** "Open the Properties dialog"
2. **點擊 Finish**

### 步驟 6：進階設置

在 Properties 對話框中：

1. **General 標籤**：
   - ✅ 勾選 "Run whether user is logged in or not"
   - ✅ 勾選 "Run with highest privileges"

2. **Conditions 標籤**：
   - ✅ 勾選 "Wake the computer to run this task"

3. **Settings 標籤**：
   - ✅ 勾選 "Allow task to be run on demand"
   - ✅ 勾選 "Run task as soon as possible after a scheduled start is missed"

4. **點擊 OK**

---

## 🧪 測試

### 方式 1：立即測試同步

在任務排程器中：

1. 找到 "Krystal AI - 元大持倉自動同步"
2. **右鍵** → **Run**
3. 等待 30 秒
4. 檢查 `logs\sync_*.txt` 看是否成功

### 方式 2：手動執行

```bash
cd "g:\我的雲端硬碟\Krystal_AI_Trading_System"
python sync_yuanta_to_sheets.py
```

---

## 📊 驗證同步結果

### 檢查日誌文件

```bash
# 打開日誌目錄
start g:\我的雲端硬碟\Krystal_AI_Trading_System\logs
```

預期看到：
```
✅ 元大 API 連接成功
✅ 帳戶快照已同步（待完善）
✅ 持倉已同步: 5 個持股
✅ 同步日誌已記錄
```

### 檢查 Google Sheets

打開你的 Sheets：
https://docs.google.com/spreadsheets/d/1zpehl1bAZitFiQqMg7IcGWsPQxdhnQDhAeNtRvxzwn8

檢查這些分頁是否有新數據：
- ✅ `broker_positions` - 最新持倉
- ✅ `broker_snapshot` - 帳戶快照
- ✅ `sync_logs` - 同步日誌

### 檢查 Flask 儀表板

訪問 **http://localhost:5000**

持倉表應該顯示真實的股票（替代之前的空表）

---

## 🔔 自定義同步時間

### 改為上午 8:00 同步

1. 打開工作排程器
2. 找到 "Krystal AI - 元大持倉自動同步"
3. **右鍵** → **Properties**
4. **Triggers 標籤** → **Edit**
5. 改為 `08:00 AM`
6. **OK**

### 改為下午 3:00 同步

同上，改為 `03:00 PM`

### 設置多次同步

如果想要**上午 9:00 和下午 3:00 各同步一次**：

1. **Properties** → **Triggers 標籤**
2. **New** 添加第二個觸發器
3. 時間設為 `03:00 PM`
4. **OK**

---

## 🛠️ 故障排查

### 問題：PowerShell 提示 "不允許執行"

**解決**：在 PowerShell 中先運行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
```

然後再執行 `setup_task_scheduler.ps1`

### 問題：任務顯示失敗，但手動運行成功

**原因**：Windows 帳户權限問題

**解決**：
1. 打開任務排程器
2. 右鍵任務 → **Properties**
3. **General 標籤** → 勾選 "Run with highest privileges"
4. **OK**

### 問題：每天 09:00 沒有執行

**檢查**：
1. 任務狀態是否為 "Ready"（不是 "Disabled"）
2. 計算機是否在 09:00 處於開啟狀態
3. 檢查日誌看是否有錯誤信息

**解決**：
1. 右鍵任務 → **Run** 測試是否手動可執行
2. 檢查 `logs\sync_history.log` 看過去的執行記錄

---

## 📈 效果示意

### 執行前

```
當前持倉
━━━━━━━━━━━━━━━━━━━━━━━
（空表，無數據）
```

### 執行後（每天 09:00）

```
當前持倉
━━━━━━━━━━━━━━━━━━━━━━━
代碼  | 數量 | 市值
─────────────────────
AAPL | 100  | $18,500
MSFT | 50   | $19,000
TSLA | 10   | $2,450
...
━━━━━━━━━━━━━━━━━━━━━━━
總資產: $125,345.01
```

---

## 💡 進階建議

1. **增加郵件通知**（可選）
   - 同步失敗時發送郵件告知
   - 在 `sync_daily.bat` 中添加郵件邏輯

2. **備份 Sheets 數據**（推薦）
   - 每週下載一份備份
   - 防止數據遺失

3. **監控同步日誌**（重要）
   - 定期檢查 `logs\sync_history.log`
   - 確保自動同步正常運行

4. **設置多個同步時間**
   - 上午 09:00 + 下午 16:00
   - 確保全天市場動態實時更新

---

## 📞 需要幫助？

檢查以下文件：
- **詳細指南**：`YUANTA_SYNC_GUIDE.md`
- **測試清單**：`TEST_CHECKLIST.md`
- **Flask 整合**：`FLASK_SHEETS_INTEGRATION.md`

---

**創建人**：Claude Code
**最後更新**：2026-03-04
**版本**：v1.0
