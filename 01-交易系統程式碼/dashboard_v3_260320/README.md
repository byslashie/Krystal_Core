# 📊 Dashboard v3 (2026-03-20)

## 🎯 概述

Krystal AI 量化交易系統的新一代儀表板架構。采用 **模板繼承模式** 實現多頁面應用，支持高效的代碼複用和維護。

## 📁 結構

```
dashboard_v3_260320/
├── README.md
└── templates/
    ├── base.html              ← 所有頁面的母板（導航、側邊欄、頁腳）
    ├── portfolio.html         ← 投資組合管理（資產概覽、持倉分析、績效追蹤）
    ├── risk.html              ← 風險控制（風險指標、單筆持倉風險分析）
    ├── allocation.html        ← 資金配置（資產配置、推薦配置）
    ├── performance.html       ← 績效分析（年度報酬、月均報酬、勝率、走勢圖）
    ├── trading.html           ← 交易管理（系統狀態、當前交易、已實現交易）
    ├── strategies.html        ← 策略管理（活躍策略、策略績效排行）
    └── dashboard_new.html     ← 舊版本參考（保留用於對比分析）
```

## 🚀 快速開始

### 訪問頁面

| 功能 | URL | 說明 |
|------|-----|------|
| 主頁 | `http://127.0.0.1:8000/` | 投資組合概覽 |
| 投資組合 | `http://127.0.0.1:8000/portfolio` | 詳細持倉分析 |
| 風險控制 | `http://127.0.0.1:8000/risk` | 風險管理 |
| 資金配置 | `http://127.0.0.1:8000/allocation` | 資產配置優化 |
| 績效分析 | `http://127.0.0.1:8000/performance` | 績效統計 |
| 交易管理 | `http://127.0.0.1:8000/trading` | 交易監控 |
| 策略管理 | `http://127.0.0.1:8000/strategies` | 策略績效 |

## 🏗️ 架構設計

### 模板繼承

所有頁面都繼承自 `base.html`，實現：
- 統一的 header 導航
- 統一的 sidebar 控制面板
- 統一的 footer
- 共用的 CSS 和 JavaScript

```html
{% extends "base.html" %}

{% block title %}頁面標題{% endblock %}

{% block page_controls %}
<!-- 特定頁面的控制面板 -->
{% endblock %}

{% block content %}
<!-- 頁面內容 -->
{% endblock %}
```

## 📡 API 集成

每個頁面都通過以下 API 端點獲取數據：

| 端點 | 說明 | 回傳 |
|------|------|------|
| `/api/metrics` | 資產指標 | JSON |
| `/api/holdings` | 當前持倉 | JSON |
| `/api/holdings/by-broker` | 按券商分類持倉 | JSON |
| `/api/chart-data` | 圖表數據 | JSON |
| `/api/daily-performance` | 每日績效 | JSON |
| `/api/strategies` | 策略列表 | JSON |

## 🔧 開發規則

### 代碼提交

遵循 Krystal 三重身份系統的提交規則：

```bash
# 交易系統更新
git commit -m "📈 交易: 添加新的風控指標到 risk.html"

# 功能添加
git commit -m "✨ 交易: 完成 portfolio.html 持倉分析頁面"

# Bug 修復
git commit -m "🐛 交易Bug: 修復圖表加載失敗問題"
```

### 時間規劃

根據優先級安排開發時段：

```
優先級 1 (P0) - 人生管理 & 健康
優先級 2 (P1) - 交易機會 & 市場監控 ← 此項目適用時段：09:00-12:00, 21:30-23:00
優先級 3 (P2) - PM 項目交付           ← 時段：13:00-17:00
優先級 4 (P3) - 內容創作
```

## 📋 檢查清單

- [x] 創建 base.html 框架
- [x] 創建多頁面模板（portfolio, risk, trading 等）
- [x] 配置 Flask 多目錄支持
- [ ] 集成所有 API 端點
- [ ] 測試所有頁面功能
- [ ] 添加單元測試
- [ ] 部署到生產環境
- [ ] 監控性能指標

## 🔗 相關資源

- 全局工作規則：`../../CLAUDE.md`
- 交易系統規則：`../CLAUDE.md`
- Flask 應用：`../app_html_flask.py`
- 靜態資源：`../static/`

## 📝 更新日誌

### 2026-03-20
- 創建 dashboard_v3_260320 架構
- 實現 base.html 模板繼承系統
- 創建 7 個功能頁面（portfolio, risk, trading 等）
- 配置 Flask 多模板目錄支持

## 👤 維護者

Krystal AI Trading System

---

**最後更新**：2026-03-20 18:15 UTC
