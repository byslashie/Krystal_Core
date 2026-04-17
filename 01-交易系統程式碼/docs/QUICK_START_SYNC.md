# ⚡ 持倉同步系統 - 5 分鐘快速開始

**目標**: 立即啟用 IB/元大持倉自動同步系統

---

## 🎯 3 步啟動

### 1️⃣ 診斷系統（2 分鐘）
```bash
python test_sync_system.py
```

✅ **期望結果**：
```
✅ 環境配置
✅ Google Sheets
✅ IB API (或 ⚠️ 不可用)
✅ API 端點
```

❌ **如果有紅燈**：
- 檢查 `credentials.json` 是否存在
- 確認 IB TWS/Gateway 是否運行
- 查看詳細文檔：`SYNC_POSITIONS_SETUP.md`

---

### 2️⃣ 手動測試（1 分鐘）
```bash
python brokers/sync_positions.py
```

✅ **期望結果**：
```
🔄 持倉同步開始

✅ [IB] 成功獲取 X 筆持倉
✅ [Yuanta] 成功獲取 Y 筆持倉
✅ 成功寫入 Z 筆持倉到 Google Sheets

📊 同步結果：
   • IB: X 筆
   • Yuanta: Y 筆
   • 總計: Z 筆
```

---

### 3️⃣ 設置自動執行（2 分鐘）

#### 選項 A：Windows Task Scheduler（推薦）
```bash
# 每天 09:00 執行
python setup_daily_sync_scheduler.py --windows --schedule-time 09:00
```

#### 選項 B：自定義時間
```bash
# 每天 14:30 執行
python setup_daily_sync_scheduler.py --windows --schedule-time 14:30
```

✅ **驗證設置**：
```bash
python setup_daily_sync_scheduler.py --windows --list
```

應該看到：
```
Krystal-AI-Daily-Sync
   狀態: 已啟用
   觸發器: 每天 09:00
```

---

## 📱 驗證前端顯示

1. **啟動 Flask 應用**：
   ```bash
   python app_simple.py
   # 或使用 API Wrapper
   python api_wrapper_server.py
   ```

2. **訪問前端**：
   - URL: `http://localhost:9999`
   - 導航: 「實盤交易」 → 「當前持倉」

3. **驗證數據**：
   - ✅ 應該看到最新的 IB + 元大持倉
   - ✅ 顯示 標的、數量、均價、現價、損益

---

## 🔄 日常使用

### 自動執行（設置後）
- ✅ 每天指定時間自動同步
- ✅ 無需手動操作
- ✅ 日誌自動記錄到 Google Sheets

### 手動同步（臨時需求）
```bash
python brokers/sync_positions.py
```

### 檢查同步狀態
1. 打開 Google Sheets
2. 查看 `broker_positions` 分頁 → 最新持倉
3. 查看 `sync_logs` 分頁 → 同步歷史

---

## 🛠️ 常見命令

| 命令 | 功用 |
|------|------|
| `python test_sync_system.py` | 診斷系統狀態 |
| `python brokers/sync_positions.py` | 手動同步持倉 |
| `python setup_daily_sync_scheduler.py --windows --schedule-time HH:MM` | 設置定時執行 |
| `python setup_daily_sync_scheduler.py --windows --list` | 查看排程任務 |
| `python setup_daily_sync_scheduler.py --windows --remove` | 刪除排程任務 |

---

## ❌ 故障快速排除

### 問題：同步失敗
```bash
# 1. 驗證環境
python test_sync_system.py

# 2. 檢查 IB/Yuanta 連接
# - IB: 確認 TWS/Gateway 運行
# - Yuanta: 確認帳號密碼正確

# 3. 手動執行測試
python brokers/sync_positions.py
```

### 問題：Task Scheduler 不執行
```bash
# 1. 驗證任務存在
python setup_daily_sync_scheduler.py --windows --list

# 2. 手動執行任務
schtasks /run /tn "Krystal-AI-Daily-Sync"

# 3. 查看錯誤日誌
# Windows 事件檢視器 → Windows 日誌 → 系統
```

### 問題：前端沒有顯示持倉
```bash
# 1. 驗證同步成功
python brokers/sync_positions.py

# 2. 檢查 Google Sheets
# 打開 broker_positions 分頁，確認有數據

# 3. 重啟 Flask 應用
# Ctrl+C 停止
# 重新運行 python app_simple.py
```

---

## 📊 期望數據格式

同步完成後，Google Sheets 應該看起來像：

### broker_positions 分頁
```
時間                   券商    市場      標的   方向 數量  均價   現價  帳面損益  損益率
2026-03-10 09:00:00   IB    NASDAQ    QQQ    多   10   350.5  352.3  18.00   0.51%
2026-03-10 09:00:00   Yuanta TWSE     2330   多  100   850.0  855.0 500.00   0.59%
```

### sync_logs 分頁
```
時間                   類型              券商    新增筆數  狀態     備註
2026-03-10 09:00:05   broker_positions  IB     5        success  成功獲取 5 筆
2026-03-10 09:00:15   broker_positions  Yuanta 3        success  成功獲取 3 筆
```

---

## 🎓 下一步

### 了解詳細信息
- 📖 [詳細設置指南](SYNC_POSITIONS_SETUP.md) - 所有選項和故障排除
- 📋 [完成總結](SYNC_SYSTEM_SUMMARY.md) - 系統架構和性能

### 高級功能（可選）
- 實現增量同步（加速）
- 添加 Webhook 通知
- 集成 Schwab API
- 多帳戶聚合

---

## 📞 快速幫助

**系統不工作？** → 運行診斷
```bash
python test_sync_system.py
```

**需要詳細步驟？** → 查看設置指南
```
SYNC_POSITIONS_SETUP.md
```

**想了解架構？** → 查看完成總結
```
SYNC_SYSTEM_SUMMARY.md
```

---

✅ **完成！你現在有了自動持倉同步系統。**

每天指定時間，系統會自動：
1. 從 IB API 獲取持倉
2. 從元大 API 獲取持倉
3. 同步數據到 Google Sheets
4. 前端自動顯示最新持倉

**無需手動操作，全自動化！**

---

**快速開始完成**: 2026-03-10
**預計總時間**: 5 分鐘
**難度級別**: ⭐ 簡單
