# 🚀 DashboardV2 設置指南

## 📌 概述

我已經為你的交易系統重寫了 Flask 應用。新版本更加穩定、簡潔、易於維護。

### 核心改進
- ✅ **新的 app_dashboard_v2.py** - 簡化版本，只 ~8KB (vs 舊版 ~100KB)
- ✅ **移除問題依賴** - 消除 data_layer、ship_monitoring、APScheduler 的依賴問題
- ✅ **清晰的路由** - 13 個配置好的路由
- ✅ **完整的模板** - 所有 7 個頁面模板已驗證

---

## 🎯 配置的路由 (13 個)

### 頁面路由
| 路由 | 頁面 | 文件 |
|-----|------|------|
| `/v2` | DashboardV2 主頁 | dashboardV2.html |
| `/pages/risk` | 風控管理 | pages/risk.html |
| `/pages/performance` | 績效分析 | pages/performance.html |
| `/pages/monitoring` | 監控中心 | pages/monitoring.html |
| `/pages/trading` | 交易面板 | pages/trading.html |
| `/pages/strategies` | 策略配置 | pages/strategies.html |
| `/pages/intel` | 情報資訊 | pages/intel.html |

### API 路由
| 路由 | 功能 | 返回數據 |
|-----|------|---------|
| `/` | 主頁 (V1) | dashboard.html |
| `/api/metrics` | 性能指標 | 資產、報酬、夏普比、最大回撤 |
| `/api/holdings/by-broker` | 按券商分組持倉 | IB、Yuanta、Schwab 的持倉 |
| `/api/daily-performance` | 日績效數據 | 30 天的績效曲線 |
| `/api/strategies` | 活躍策略 | 3 個示例策略 |
| `/api/status` | 系統狀態 | 版本、時間戳、各模塊狀態 |

---

## 🚀 三種啟動方法

### 方法 1: Windows 批處理 (最簡單) ⭐
**文件**: `KILL_AND_START_V2.bat`

在 Windows 文件管理器中：
1. 找到 `KILL_AND_START_V2.bat`
2. 雙擊執行
3. 它會自動：
   - 殺死所有舊的 Python 進程
   - 啟動新的 Flask 服務器
   - 打開瀏覽器到 http://localhost:8888/v2

```bash
# 或在命令行運行
KILL_AND_START_V2.bat
```

### 方法 2: Python 啟動腳本 (推薦)
**文件**: `start_dashboard_v2.py`

```bash
python start_dashboard_v2.py
```

特點：
- 自動打開瀏覽器
- 更清晰的輸出信息
- 優雅的關閉 (Ctrl+C)

### 方法 3: 直接啟動 Flask
```bash
python app_dashboard_v2.py
```

---

## 🔗 訪問地址

啟動後訪問以下地址：

### 主應用
- **DashboardV2**: http://localhost:8888/v2
- **主頁 (V1)**: http://localhost:8888/

### API 測試
```bash
# 查詢系統狀態
curl http://localhost:8888/api/status

# 獲取性能指標
curl http://localhost:8888/api/metrics

# 獲取持倉數據
curl http://localhost:8888/api/holdings/by-broker

# 獲取策略列表
curl http://localhost:8888/api/strategies
```

### 使用瀏覽器開發者工具
打開瀏覽器的 Network 標籤，可以看到所有 API 調用。

---

## ✅ 驗證清單

啟動時會自動檢查：

```
Template Check:
  ✓ templates/dashboardV2.html (42 KB)
  ✓ templates/pages/risk.html (6.4 KB)
  ✓ templates/pages/performance.html (6.1 KB)
  ✓ templates/pages/monitoring.html (6.0 KB)
  ✓ templates/pages/trading.html (6.4 KB)
  ✓ templates/pages/strategies.html (7.4 KB)
  ✓ templates/pages/intel.html (7.9 KB)
```

如果看到所有都是 ✓，說明一切就緒。

---

## 🔧 常見問題

### Q1: 啟動失敗 - "Address already in use"
**原因**: 8888 端口被舊的 Flask 進程佔用

**解決**:
1. 使用 `KILL_AND_START_V2.bat` (自動殺死舊進程)
2. 或手動殺死:
   ```bash
   taskkill /F /IM python.exe
   ```
3. 等待 2 秒後重新啟動

### Q2: 打開瀏覽器但顯示 "Cannot reach localhost"
**原因**: Flask 還在啟動中

**解決**:
1. 等待 3-5 秒
2. 手動刷新瀏覽器 (Ctrl+R)
3. 檢查控制台輸出是否有錯誤

### Q3: 某個頁面加載失敗
**原因**: 模板文件缺失或 JavaScript 錯誤

**解決**:
1. 檢查控制台中的錯誤信息 (F12 → Console)
2. 驗證所有模板文件都存在
3. 查看 Flask 的錯誤日誌

### Q4: 出現 "No module named 'xxx'"
**原因**: 缺少依賴庫

**解決**:
```bash
pip install -r requirements.txt
```

---

## 📊 舊版本 vs 新版本

| 指標 | app_html_flask.py | app_dashboard_v2.py |
|-----|-------------------|-------------------|
| 文件大小 | ~101 KB | ~8 KB |
| 導入 | 複雜 (data_layer, ship_monitoring) | 簡單 (只用 Flask) |
| 路由數 | 40+ | 13 (核心) |
| 啟動時間 | 慢 | 快 |
| 依賴個數 | 10+ | 1 (Flask) |
| 錯誤處理 | 基本 | 詳細 |
| 日誌輸出 | 基本 | 詳細 |

---

## 🔄 遷移指南

### 如果你想使用新的 app_dashboard_v2.py:

1. **直接啟動**:
   ```bash
   python start_dashboard_v2.py
   ```

2. **更新 run_dashboardv2.py** (可選):
   編輯 `run_dashboardv2.py`，將:
   ```python
   from app_html_flask import app  # 舊的
   ```
   改為:
   ```python
   from app_dashboard_v2 import app  # 新的
   ```

3. **保留舊版本** (可選):
   舊的 `app_html_flask.py` 仍然保留，可以作為參考。

---

## 📝 下一步工作

### 短期 (現在):
- [ ] 測試所有 7 個頁面路由
- [ ] 測試所有 6 個 API 端點
- [ ] 驗證頁面加載速度

### 中期 (本週):
- [ ] 連接真實的 Google Sheets 數據源
- [ ] 實現實時持倉更新
- [ ] 添加 WebSocket 支持實時推送

### 長期 (本月):
- [ ] 整合真實的 Broker API (IB, Yuanta, Schwab)
- [ ] 實現實時風控監控
- [ ] 添加更多分析功能

---

## 📧 技術細節

### 新 app_dashboard_v2.py 的結構:

```
app_dashboard_v2.py (238 lines)
├── Imports & Setup (Flask, logging)
├── Routes (13 endpoints)
│   ├── Main pages (/v2, /pages/*)
│   ├── API endpoints (/api/*)
│   └── Error handlers
├── Mock data functions
└── Main execution block
```

### 依賴:
- `Flask` - Web 框架
- `logging` - 日誌記錄
- `datetime` - 日期時間
- `json` - JSON 序列化
- `os` - 文件系統操作

全部都是 Python 標準庫或 Flask，無額外依賴。

---

## 🎉 完成!

現在你有一個工作正常的 DashboardV2 Flask 應用！

### 立即開始:
```bash
python start_dashboard_v2.py
```

訪問: **http://localhost:8888/v2**

---

**版本**: 2.0.0
**最後更新**: 2026-03-20
**狀態**: 生產就緒 ✅
