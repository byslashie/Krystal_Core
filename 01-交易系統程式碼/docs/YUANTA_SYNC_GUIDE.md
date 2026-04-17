# 🔄 元大持倉自動同步指南

**日期**: 2026-03-04
**狀態**: ✅ 已實裝
**目標**: 從元大帳戶自動同步持倉到 Google Sheets

---

## 📋 概覽

`sync_yuanta_to_sheets.py` 會自動：
1. 連接你的元大券商帳戶（使用 .env 中的憑證）
2. 獲取實時持倉列表
3. 同步到 Google Sheets 的以下分頁：
   - `broker_positions` - 持倉列表
   - `broker_snapshot` - 帳戶快照
   - `sync_logs` - 同步日誌

---

## 🚀 快速開始

### 前置條件
- ✅ Windows 環境（元大 API 只支援 Windows）
- ✅ 已配置 `.env` 中的元大憑證：
  ```
  YUANTA_ACCOUNT=S989C0316437
  YUANTA_PASSWORD=Kk3353636
  YUANTA_ENV=PROD
  YUANTA_CERT_PATH=...
  ```
- ✅ 已安裝 `pythonnet` 和其他依賴

### 執行同步

**方式 1：手動執行**
```bash
cd "g:/我的雲端硬碟/Krystal_AI_Trading_System"
python sync_yuanta_to_sheets.py
```

**預期輸出**：
```
============================================================
🔄 元大持倉同步開始
============================================================
📍 步驟 1：連接元大 API...
✅ 元大 API 連接成功

📍 步驟 2：獲取帳戶快照...
✅ 帳戶快照已同步（待完善）

📍 步驟 3：獲取持倉列表...
✅ 持倉已同步: 5 個持股

📊 持倉清單：
timestamp              broker symbol position avg_cost market_value
2026-03-04T...        YUANTA AAPL       100    185.5        18550
2026-03-04T...        YUANTA MSFT        50    380.0        19000
...

============================================================
✅ 同步完成！
============================================================
📊 持倉數量: 5
💰 帳戶快照: 1
⏰ 同步時間: 2026-03-04T10:30:45.123456
```

---

## ⏰ 定時同步（Windows Task Scheduler）

### 設置自動每日同步

**步驟 1：創建批次文件** (`sync_daily.bat`)

在項目根目錄創建 `sync_daily.bat`：

```batch
@echo off
cd "g:\我的雲端硬碟\Krystal_AI_Trading_System"
python sync_yuanta_to_sheets.py > sync_log_%date:~10,4%%date:~4,2%%date:~7,2%.txt 2>&1
```

**步驟 2：打開 Windows Task Scheduler**

1. 按 `Win + R`，輸入 `taskschd.msc`，按 Enter
2. 點擊 **Create Basic Task**
3. **名稱**：`Krystal AI - 元大持倉同步`
4. **觸發器**：
   - 選擇 "Daily"
   - 時間：09:00 (或你想要的時間)
5. **操作**：
   - 程式：`C:\Windows\System32\cmd.exe`
   - 參數：`/c "g:\我的雲端硬碟\Krystal_AI_Trading_System\sync_daily.bat"`

**步驟 3：測試任務**

右擊新建的任務 → **Run** → 檢查是否執行成功

---

## 📊 Google Sheets 數據格式

### broker_positions 表

| 欄位 | 說明 | 例子 |
|------|------|------|
| `timestamp` | 同步時間 | `2026-03-04T10:30:45` |
| `broker` | 券商代碼 | `YUANTA` |
| `symbol` | 股票代碼 | `AAPL` |
| `sec_type` | 證券類型 | `STK` (股票) |
| `exchange` | 交易所 | `TWSE` (台灣) |
| `currency` | 幣別 | `TWD` |
| `position` | 持股數量 | `100` |
| `avg_cost` | 平均成本 | `185.50` |
| `market_value` | 市場價值 | `18550` |
| `notes` | 備註 | `元大實時持倉: AAPL` |

### broker_snapshot 表（帳戶快照）

| 欄位 | 說明 | 例子 |
|------|------|------|
| `timestamp` | 快照時間 | `2026-03-04T10:30:45` |
| `broker` | 券商代碼 | `YUANTA` |
| `net_liquidation` | 淨清算價值 | `125000` |
| `total_cash_value` | 現金餘額 | `50000` |
| `equity_with_loan_value` | 融資股權 | `75000` |
| `currency` | 幣別 | `TWD` |
| `converted_twd` | 台幣金額 | `125000` |
| `notes` | 備註 | `元大帳號: S989C0316437` |

### sync_logs 表（同步日誌）

| 欄位 | 說明 | 例子 |
|------|------|------|
| `timestamp` | 同步時間 | `2026-03-04T10:30:45` |
| `sync_type` | 同步類型 | `positions` |
| `broker` | 券商 | `YUANTA` |
| `record_count` | 記錄數 | `5` |
| `status` | 狀態 | `success` / `failed` |
| `error_msg` | 錯誤信息 | `(空或錯誤信息)` |
| `notes` | 備註 | `已同步 5 個持股和帳戶快照` |

---

## 🔧 故障排查

### 問題 1：找不到元大 API

```
❌ 無法導入元大 API: ...
```

**解決**：
- 確認 `lib/` 目錄存在並有元大 DLL 文件
- 確認 `brokers/yuanta_api.py` 存在
- 檢查是否在 Windows 環境

### 問題 2：登入失敗

```
❌ 同步失敗: 無法連接到元大伺服器
```

**解決**：
- 檢查 `.env` 中的帳號密碼是否正確
- 確認 `YUANTA_CERT_PATH` 指向正確的憑證文件
- 確認網絡連接正常
- 嘗試手動登入投資先生確認帳號

### 問題 3：Google Sheets 連接失敗

```
❌ 無法導入 sheets_utils: ...
```

**解決**：
- 檢查 `credentials.json` 是否存在
- 確認 `.env` 中 `GOOGLE_SHEET_KEY` 是否正確
- 確認 Google Sheets 允許服務帳號存取

### 問題 4：持倉為空

```
⚠️ 未能獲取持倉列表
```

**解決**：
- 確認元大帳戶中有持倉
- 檢查元大系統是否正常
- 嘗試在投資先生中確認持倉信息

---

## 📈 效果示意

執行同步後，Flask 儀表板會自動讀取最新的持倉數據：

```
當前持倉
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
代碼  | 價格  | 數量 | 市值    | 漲跌
────────────────────────────────────
AAPL | $185 |  100 | $18,500 | +2.5%
MSFT | $380 |   50 | $19,000 | +1.8%
TSLA | $245 |   10 |  $2,450 | +3.2%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
總資產: $125,345.01
```

---

## 🚀 進階用法

### 只同步持倉（不同步帳戶快照）

```python
from sync_yuanta_to_sheets import sync_yuanta_to_sheets

result = sync_yuanta_to_sheets()
print(f"同步結果: {result['status']}")
```

### 集成到現有 Flask 應用

在 `app_html_flask.py` 中添加路由：

```python
@app.route('/api/sync-yuanta')
def api_sync_yuanta():
    """手動觸發元大同步"""
    try:
        from sync_yuanta_to_sheets import sync_yuanta_to_sheets
        result = sync_yuanta_to_sheets()
        return jsonify({
            'status': 'success' if result['status'] == 'success' else 'error',
            'data': result
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
```

然後在儀表板中添加一個 "🔄 同步元大" 按鈕，點擊時調用 `/api/sync-yuanta`。

---

## 💡 最佳實踐

1. **每日自動同步**：使用 Task Scheduler 每天上午 9:00 自動同步
2. **手動同步**：重要操作後（下單、平倉）手動執行同步
3. **監控日誌**：定期檢查 `sync_logs` 分頁，確保同步正常
4. **備份 Google Sheets**：每週備份一份 Sheets 數據

---

## 📞 技術支持

若遇到問題，請檢查：
1. `.env` 配置是否正確
2. 元大系統是否正常
3. 網絡連接是否穩定
4. `sync_logs` 中的錯誤信息

---

**創建人**：Claude Code
**最後更新**：2026-03-04
**版本**：v1.0
