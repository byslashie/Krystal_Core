# ⚡ Dashboard v8 - 快速開始指南

**用時**：5 分鐘啟動 + 3 分鐘測試 = 8 分鐘完整上手

---

## 1️⃣ 啟動應用（1 分鐘）

```bash
cd "G:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼\dashboard_v8"
python app.py
```

**預期輸出**：
```
 * Running on http://127.0.0.1:9000
 * WARNING: This is a development server...
```

---

## 2️⃣ 打開前端（1 分鐘）

在瀏覽器中訪問：
```
http://localhost:9000
```

**應該看到**：
```
✅ Dashboard v8 頁面加載
✅ 左側：3 個經紀商的持倉卡片
   • US Interactive Brokers (3 個持倉)
   • TW 元大券商 (4 個持倉)
   • [Schwab 部分]
✅ 右側：市場指數、經濟數據
✅ 中央：持倉列表、交易記錄
```

---

## 3️⃣ 測試所有 API（3 分鐘）

在另一個終端：

```bash
cd dashboard_v8
python test_all_apis.py
```

**結果應該顯示**：
```
✅ 可用    - 約 25 個 API 端點
🔴 Stub   - 4 個 Schwab 端點（等服務恢復）
❌ 錯誤   - 0 個
```

---

## 4️⃣ 驗證持倉數據（1 分鐘）

```bash
# 查詢所有持倉
curl http://localhost:9000/api/positions | python -m json.tool

# 預期看到：
# {
#   "status": "success",
#   "data": [
#     {
#       "symbol": "MU",
#       "broker": "schwab",
#       "position": 4,
#       "avgCost": 325.38,
#       "marketValue": 1301.52,
#       "unrealizedPNL": 0
#     },
#     ...
#   ]
# }
```

---

## 5️⃣ 驗證市場數據（1 分鐘）

```bash
# 查詢股市指數
curl http://localhost:9000/api/market-indices | python -m json.tool

# 預期看到：
# {
#   "status": "success",
#   "indices": [
#     {
#       "name": "S&P 500",
#       "value": 5234.56,
#       "change": 0.45
#     },
#     ...
#   ]
# }
```

---

## ✅ 完成檢查清單

完成後檢查：

- [ ] Flask 應用啟動成功
- [ ] 前端頁面加載正常
- [ ] 可以看到 12 個持倉
- [ ] 持倉數據顯示正確（股票代碼、數量、價格、損益）
- [ ] 市場指數更新正常
- [ ] 台股數據完整（元大 4 個持倉）
- [ ] 美股數據完整（Schwab + IB 現價正確）
- [ ] test_all_apis.py 顯示 25+ 可用端點
- [ ] 無報錯或警告

如果全部 ✅，**系統已就緒！**

---

## 🎯 接下來可以做什麼

### 查詢數據
```bash
# 查詢未平倉交易
curl http://localhost:9000/api/trades/open

# 查詢年初至今回報
curl http://localhost:9000/api/ytd-returns

# 查詢投資組合圖表
curl http://localhost:9000/api/portfolio-chart-data
```

### 新增交易
```bash
# 新增一筆交易
curl -X POST http://localhost:9000/api/trades/add \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "direction": "LONG",
    "entry_price": 150.00,
    "quantity": 10,
    "date": "2026-04-07"
  }'
```

### 查看實時股價
```bash
# 查詢 AAPL 實時股價
curl "http://localhost:9000/api/yahoo-proxy?symbol=AAPL"
```

---

## ⚠️ 常見問題

**Q：頁面空白或無法加載？**
```
A：確認 Flask 正在運行（看控制台輸出）
   清除瀏覽器緩存（Ctrl+Shift+Delete）
   檢查 http://localhost:9000 是否能訪問
```

**Q：持倉數據顯示為 0？**
```
A：這是正常的，表示數據庫為空
   使用 /api/trades/add 新增交易
   或從 Google Sheets 同步數據
```

**Q：市場數據無更新？**
```
A：Yahoo Finance 可能返回遲延數據
   等待 5 分鐘後刷新
   或檢查網路連接
```

**Q：Schwab 相關 API 返回錯誤？**
```
A：這是預期的（Schwab 服務故障）
   使用 Mock 數據進行開發
   等待服務恢復後再集成
```

---

## 📖 進階使用

如果想深入了解，查看：
- `README.md` — 完整功能介紹
- `SYSTEM_ARCHITECTURE.md` — 系統設計
- `BACKEND_REQUIREMENTS.md` — API 詳細規範
- `CURRENT_STATUS.md` — 當前狀態 & 已知問題

---

## 🎉 大功告成！

現在你已經：
✅ 啟動了 Dashboard v8  
✅ 驗證了所有 API  
✅ 確認了持倉數據  
✅ 測試了市場數據  

**系統已完全就緒！**

需要幫助？查看 README.md 或 CURRENT_STATUS.md 🚀
