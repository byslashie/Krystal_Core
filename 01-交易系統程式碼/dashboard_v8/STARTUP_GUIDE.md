# 🚀 Dashboard v8 啟動指南

## ✅ 系統狀態

**後端服務器**: Flask (Port 9000)  
**前端**: HTML5 + JavaScript  
**數據庫**: SQLite (本地 `broker_positions.db`)  
**狀態**: ✅ 正在運行

---

## 📍 訪問方式

### 方法 1: 直接訪問
```
http://127.0.0.1:9000
```

### 方法 2: 使用啟動腳本
```bash
# Windows (在 CMD 中)
python START_DASHBOARD_V8.sh

# 或直接運行 app.py
python app.py
```

### 方法 3: 使用 Python 啟動器
```bash
python start.py
```

---

## 🔧 修正清單

### 後端修正 (app.py)
- ✅ 修正 Flask 運行端口: **5000 → 9000**
- ✅ 安裝所有依賴: `flask`, `flask-cors`, `pandas`, `plotly`, `scipy`, `scikit-learn`
- ✅ 修正啟動提示信息

### 前端修正 (index.html)
- ✅ 確認 API_BASE 設置正確指向 `http://127.0.0.1:9000`
- ✅ 驗證所有 API 端點調用

### 依賴修正
- ✅ 安裝: `flask`, `flask-cors`, `pandas`, `plotly`, `scipy`, `scikit-learn`, `python-dotenv`, `yfinance`, `openpyxl`

---

## 📊 API 端點測試結果

| 端點 | 狀態 | 說明 |
|------|------|------|
| `/health` | ✅ OK | 健康檢查 |
| `/api/broker-positions` | ✅ OK | 獲取持倉數據 (17 筆) |
| `/api/strategy/sync-log` | ✅ OK | 同步日誌 |
| `/api/strategy/import` | ✅ OK | 策略上傳 |
| `/api/strategy/import/charts` | ✅ OK | 圖表生成 |

---

## 💻 系統要求

- Python 3.8+
- 依賴:
  - `flask` >= 2.0
  - `flask-cors` >= 3.0
  - `pandas` >= 1.0
  - `plotly` >= 5.0
  - `scipy` >= 1.5
  - `scikit-learn` >= 1.0
  - `yfinance` >= 0.2
  - `python-dotenv` >= 0.19

---

## 🎯 主要功能

### 📈 實時持倉監控
- 支持多券商整合 (Interactive Brokers, Charles Schwab, 元大)
- 實時價格更新
- 獲利虧損計算

### 📊 策略管理
- CSV 上傳導入
- 交易記錄分析
- P&L 計算
- 蒙地卡羅模擬

### 🔄 數據同步
- 本地 SQLite 數據庫
- 日誌記錄
- 自動備份

### 📉 分析工具
- 圖表生成
- 統計分析
- 風險評估

---

## 🐛 常見問題

### 1. Port 9000 已被佔用
```bash
# 查看佔用 port 9000 的進程
netstat -ano | findstr 9000

# 停止所有 Flask 進程
pkill -f "python app.py"
```

### 2. 依賴缺失
```bash
# 重新安裝所有依賴
pip install flask flask-cors pandas plotly scipy scikit-learn python-dotenv yfinance openpyxl
```

### 3. 數據庫錯誤
```bash
# 刪除損壞的數據庫並重新初始化
rm broker_positions.db
python app.py  # 會自動創建新的數據庫
```

---

## 📝 日誌位置

- **Flask 日誌**: `stdout` (運行時顯示)
- **Debug 日誌**: `debug_log.txt`
- **數據庫**: `broker_positions.db`

---

## 🔐 安全提示

- ✅ 敏感信息存放在 `.env`
- ✅ `.env` 已在 `.gitignore` 中
- ✅ CORS 已啟用以支持跨域請求
- ✅ 無自動交易執行（所有操作需手動確認）

---

## 📞 支援

如有問題，請檢查:
1. 日誌輸出 (Flask 控制台)
2. 瀏覽器開發者工具 (F12)
3. API 端點健康狀況

**最後更新**: 2026-04-14  
**維護者**: Krystal AI System
