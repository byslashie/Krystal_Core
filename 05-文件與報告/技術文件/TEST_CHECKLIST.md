# ✅ Flask + Sheets + Schwab 整合測試清單

**日期**: 2026-03-04
**版本**: v1.0
**狀態**: 待測試

---

## 📋 測試環境準備

- [ ] Python 環境已安裝
- [ ] 依賴已安裝：`pip install flask pandas numpy gspread google-auth-oauthlib python-dotenv`
- [ ] `.env` 文件已配置 Google Sheets ID
- [ ] `credentials.json` 已放在項目根目錄
- [ ] 已確認 Google Sheets 有 11 個標準分頁

---

## 🚀 應用啟動測試

### 1. 啟動 Flask 應用

```bash
cd "g:/我的雲端硬碟/Krystal_AI_Trading_System"
python app_html_flask.py
```

**預期結果**：
```
[*] Flask 應用啟動...
[*] 訪問: http://localhost:5000
[*] 數據層狀態: OK / DISABLED
 * Running on http://localhost:5000
```

**檢查項**：
- [ ] 應用啟動無報錯
- [ ] 日誌顯示正確端口（5000）

---

## 🌐 儀表板測試 (http://localhost:5000)

### 2. 頁面加載

訪問 **http://localhost:5000**

**檢查項**：
- [ ] 頁面正常加載（無白屏）
- [ ] 標題顯示 "💎 Krystal AI 交易系統"
- [ ] 導航欄有 5 個按鈕 + "🔐 Schwab 連接" 鏈接

### 3. 儀表板數據

**檢查項**：
- [ ] 顯示 4 個指標卡片（總資產、年度報酬、Sharpe、最大回撤）
- [ ] 指標值非零（表示讀取了數據）
- [ ] 持倉表格顯示股票列表
- [ ] 圖表正常渲染

**故障排查**：
- 如果全是 0 或空 → 檢查 Sheets 連接
- 查看瀏覽器開發者工具 (F12) → Network 標籤 → 檢查 API 返回值

### 4. API 直接測試

在新標籤頁中訪問以下 URL，查看是否返回 JSON 數據：

#### 4.1 獲取指標
```
http://localhost:5000/api/metrics
```

**預期返回**：
```json
{
  "status": "success",
  "data": {
    "total_value": 125345.01,
    "annual_return": 15.5,
    "sharpe_ratio": 1.2,
    "max_drawdown": -5.2,
    "holdings": 4,
    "data_source": "sheets"
  }
}
```

**檢查項**：
- [ ] 返回 status = "success"
- [ ] `data_source` 顯示 "sheets"（表示讀取了真實數據）或 "demo"（使用了模擬數據）
- [ ] 數值合理（不是 NaN 或 null）

#### 4.2 獲取持倉
```
http://localhost:5000/api/holdings
```

**預期返回**：
```json
{
  "status": "success",
  "data": [
    {"symbol": "AAPL", "position": 100, "market_value": 18540, ...},
    ...
  ],
  "source": "sheets"
}
```

**檢查項**：
- [ ] 返回 status = "success"
- [ ] 持倉列表非空（或為空也可以，如果 Sheets 沒有數據）
- [ ] 欄位名稱正確

#### 4.3 獲取策略
```
http://localhost:5000/api/strategies
```

**預期返回**：
```json
{
  "status": "success",
  "data": [
    {"strategy_name": "momentum", "initial_capital": 100000, ...},
    ...
  ],
  "source": "sheets"
}
```

#### 4.4 系統狀態
```
http://localhost:5000/api/status
```

**預期返回**：
```json
{
  "app": "running",
  "data_layer": true/false,
  "timestamp": "2026-03-04T..."
}
```

---

## 🔐 Schwab 專頁測試 (/schwab)

### 5. 訪問 Schwab 頁面

點擊導航欄的 **"🔐 Schwab 連接"** 或直接訪問 http://localhost:5000/schwab

**檢查項**：
- [ ] 頁面正常加載
- [ ] 標題顯示 "🏦 Schwab 帳戶連接"
- [ ] 狀態卡片顯示 "✗ 未連接"（正常，因為還未授權）
- [ ] 功能列表顯示 4 個功能（實時監控、自動交易、成交同步、安全授權）

### 6. Schwab 連接狀態 API

訪問 **http://localhost:5000/api/schwab/status**

**預期返回**：
```json
{
  "status": "success",
  "connected": false,
  "has_token": false,
  "timestamp": "2026-03-04T..."
}
```

**檢查項**：
- [ ] `connected` = false（正常，尚未連接）
- [ ] 無報錯

### 7. 生成授權 URL

訪問 **http://localhost:5000/api/schwab/auth-url**

**預期返回**（若已配置 Schwab credentials）：
```json
{
  "status": "success",
  "auth_url": "https://api.schwabapi.com/v1/oauth/authorize?..."
}
```

**預期返回**（若未配置）：
```json
{
  "status": "error",
  "message": "SCHWAB_CLIENT_ID / SCHWAB_REDIRECT_URI 未設定..."
}
```

**檢查項**：
- [ ] API 能正常響應（无 500 錯誤）
- [ ] 若返回 error，檢查 `.env` 配置

---

## 📊 Google Sheets 數據讀取測試

### 8. 本地 Python 測試

```bash
python
>>> from sheets_utils import read_sheet
>>>
>>> # 測試讀取 strategies
>>> df = read_sheet('strategies')
>>> print(df.head())
>>> print(df.shape)
>>>
>>> # 測試讀取 daily_nav
>>> df = read_sheet('daily_nav')
>>> print(df.columns.tolist())
```

**檢查項**：
- [ ] 無 SSL 或連接錯誤
- [ ] 能正常讀取至少 1 個分頁
- [ ] 欄位名稱匹配 v3.1 標準

### 9. 禁用 Sheets 測試

在 `.env` 中設置 `DISABLE_SHEETS=1`，然後訪問儀表板：

```bash
# 修改 .env
DISABLE_SHEETS=1

# 重啟 Flask
python app_html_flask.py

# 訪問儀表板
http://localhost:5000
```

**預期結果**：
- [ ] 儀表板仍能加載（降級到模擬數據）
- [ ] API 返回 `data_source: "demo"`

**檢查項**：
- [ ] 備選方案工作正常
- [ ] 用戶即使無 Sheets 連接也能使用系統

---

## 🔧 調試模式

### 10. 查看詳細日誌

修改 `app_html_flask.py` 第 32 行，設置日誌級別為 DEBUG：

```python
logging.basicConfig(
    level=logging.DEBUG,  # 改為 DEBUG
    ...
)
```

重啟應用，訪問儀表板，查看控制台輸出：

```
DEBUG:__main__:GET /api/metrics
DEBUG:__main__:從 Sheets 讀取指標成功
DEBUG:__main__:GET /api/holdings
DEBUG:__main__:GET /api/strategies
...
```

**檢查項**：
- [ ] 能看到每個 API 調用的日誌
- [ ] Sheets 讀取成功/失敗信息明確

---

## 📝 測試結果記錄

### 測試環境信息

| 項目 | 值 |
|------|-----|
| 測試時間 | ___ |
| 操作系統 | Windows 11 |
| Python 版本 | ___ |
| Flask 版本 | ___ |
| 網絡連接 | 正常 / 有代理 / VPN |

### 測試結果

| 項目 | 結果 | 備註 |
|------|------|------|
| Flask 啟動 | ✅ / ❌ | ___ |
| 儀表板加載 | ✅ / ❌ | ___ |
| API /metrics | ✅ / ❌ | data_source: ___ |
| API /holdings | ✅ / ❌ | ___ |
| API /strategies | ✅ / ❌ | ___ |
| Schwab 頁面 | ✅ / ❌ | ___ |
| Sheets 讀取 | ✅ / ❌ | 分頁：___ |
| 備選模式 | ✅ / ❌ | ___ |

### 已知問題

1. **問題**：儀表板顯示全 0 或空數據
   **原因**：Google Sheets 連接失敗
   **解決**：
   - 檢查 `credentials.json` 是否存在
   - 檢查 `GOOGLE_SHEET_KEY` 是否正確
   - 設置 `DISABLE_SHEETS=0` 查看詳細日誌
   - 檢查網絡連接（是否需要代理）

2. **問題**：Schwab 授權 URL 返回 error
   **原因**：未配置 Schwab credentials
   **解決**：
   - 從 Schwab 申請 API 存取權限
   - 在 `.env` 配置 `SCHWAB_CLIENT_ID` 等參數

3. **問題**：Python 導入 sheets_utils 出錯
   **原因**：缺少依賴或路徑問題
   **解決**：
   - 確認在項目根目錄執行
   - 檢查 `.env` 是否在根目錄
   - 重新安裝依賴：`pip install -r requirements.txt`

---

## ✅ 驗收標準

當以下條件全部滿足時，整合視為成功：

- [x] Flask 應用能正常啟動
- [x] 儀表板能加載並顯示數據
- [x] 所有 API 端點能正常返回 JSON
- [x] Google Sheets 數據能正確讀取
- [x] Schwab 專頁能正常載入
- [x] 備選模式（mock 數據）能正常工作
- [x] 無持續的 500 錯誤或崩潰

---

## 📞 後續步驟

若所有測試都通過：

1. ✅ 提交代碼到 Git
2. 部署到服務器（可選）
3. 開始 Schwab API 實裝（需要申請 API 審核）
4. 完成自動同步邏輯

若有失敗：

1. ❌ 收集詳細日誌（見「調試模式」部分）
2. ❌ 查看 `.env` 配置
3. ❌ 檢查 Google Sheets 權限
4. ❌ 根據本文「已知問題」進行排查

---

**創建人**：Claude Code
**最後更新**：2026-03-04
**文件路徑**：`TEST_CHECKLIST.md`
