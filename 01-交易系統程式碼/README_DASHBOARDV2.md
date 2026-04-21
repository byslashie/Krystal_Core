# DashboardV2 - 新的 Flask 應用

## 📋 概述

我已經為你重寫了 Flask 應用代碼，創建了一個簡化、清晰、更加穩定的版本。

## 📁 新文件

### 核心應用
- **app_dashboard_v2.py** - 新的 Flask 應用（推薦使用）
  - 簡化版本，只包含必要的依賴
  - 包含所有必要的路由: `/v2`, `/pages/*`, `/api/*`
  - 更好的錯誤處理和日誌記錄

### 啟動腳本
1. **KILL_AND_START_V2.bat** - Windows 批處理文件
   - 自動殺死所有 Python 進程
   - 啟動新的 Flask 應用
   - 在 CMD 或 PowerShell 中雙擊運行

2. **start_dashboard_v2.py** - Python 啟動腳本
   - 自動打開瀏覽器
   - 更好的輸出信息
   - 命令行: `python start_dashboard_v2.py`

## 🚀 快速開始

### 方法 1: 使用批處理文件 (推薦)
```bash
# 雙擊 KILL_AND_START_V2.bat
```
或在命令行運行:
```bash
KILL_AND_START_V2.bat
```

### 方法 2: 直接運行 Python 腳本
```bash
python start_dashboard_v2.py
```

### 方法 3: 手動啟動
```bash
# 先殺死所有 Python 進程
taskkill /F /IM python.exe

# 然後啟動 Flask
python app_dashboard_v2.py
```

## 🌐 訪問地址

- **DashboardV2**: http://localhost:8888/v2
- **主頁 (V1)**: http://localhost:8888/
- **API 狀態**: http://localhost:8888/api/status

## 📄 新的路由

### 頁面路由
- `/v2` - DashboardV2 主頁
- `/pages/risk` - 風控管理
- `/pages/performance` - 績效分析
- `/pages/monitoring` - 監控中心
- `/pages/trading` - 交易面板
- `/pages/strategies` - 策略配置
- `/pages/intel` - 情報資訊

### API 路由
- `/api/metrics` - 性能指標
- `/api/holdings/by-broker` - 按券商分組持倉
- `/api/daily-performance` - 日常績效數據
- `/api/strategies` - 活躍策略列表
- `/api/status` - 系統狀態

## 🔍 檢查清單

啟動後會檢查以下文件:
- ✓ templates/dashboardV2.html
- ✓ templates/pages/risk.html
- ✓ templates/pages/performance.html
- ✓ templates/pages/monitoring.html
- ✓ templates/pages/trading.html
- ✓ templates/pages/strategies.html
- ✓ templates/pages/intel.html

## 🔧 解決方案

### 問題 1: 多個 Flask 進程運行在同一個端口
**解決**: KILL_AND_START_V2.bat 會自動殺死所有舊進程

### 問題 2: 模板渲染問題
**解決**: 新應用有更好的錯誤處理和驗證

### 問題 3: 依賴問題
**解決**: 移除了所有可選的、可能導致啟動失敗的依賴
- 移除了 `data_layer` 導入
- 移除了 `ship_monitoring` 導入
- 移除了 `APScheduler` 依賴
- 簡化了 Google Sheets 集成

## 📊 與舊版本的差異

| 特性 | app_html_flask.py | app_dashboard_v2.py |
|-----|------------------|-------------------|
| 文件大小 | ~100KB | ~8KB |
| 依賴 | 複雜 | 最小化 |
| 啟動時間 | 較慢 | 快 |
| 錯誤處理 | 基礎 | 增強 |
| 日誌 | 基礎 | 詳細 |
| 路由數 | 40+ | 14 |

## ⚠️ 注意事項

1. **第一次啟動**: 瀏覽器可能需要 2-3 秒才會自動打開
2. **端口問題**: 如果 8888 端口被佔用，啟動會失敗
3. **舊進程**: 如果遇到連接問題，使用 KILL_AND_START_V2.bat

## 🔗 相關文件

- `app_html_flask.py` - 舊的完整版本（保留以供參考）
- `run_dashboardv2.py` - 可以改為使用新的 app_dashboard_v2.py
- `templates/dashboardV2.html` - 主 UI 文件
- `templates/pages/*.html` - 各個頁面 UI

## 📝 下一步

1. 測試所有路由確保運作正常
2. 連接真實數據源（Google Sheets、Broker API）
3. 實現實時數據更新
4. 添加更多 API 端點

---

**版本**: 2.0.0
**最後更新**: 2026-03-20
**作者**: Claude Code
