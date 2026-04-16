# 🚀 HTML + Flask 交易儀表板 - 啟動指南

## 📋 項目結構

```
Krystal_AI_Trading_System/
├── app_html_flask.py              # Flask 後端應用
├── templates/
│   └── index.html                 # HTML 主頁面
├── static/
│   ├── css/
│   │   └── style.css             # 主要樣式表
│   └── js/
│       └── app.js                # 前端 JavaScript
├── FLASK_SETUP_GUIDE.md           # 本文檔
└── [其他 Streamlit 原始文件]
```

## ⚡ 快速開始

### 1️⃣ 安裝依賴

```bash
# 確保已安裝 Flask 和其他必要包
pip install flask pandas numpy
```

### 2️⃣ 運行 Flask 應用

```bash
python app_html_flask.py
```

應用將在 `http://localhost:5000` 啟動

### 3️⃣ 訪問儀表板

在瀏覽器中打開：
```
http://localhost:5000
```

你應該看到完整的交易儀表板，包括：
- 📊 資產概覽 (4 個關鍵指標卡片)
- 📈 資產走勢 (價格圖表)
- 📊 詳細分析 (累積回報 + 日回報分佈)
- 💼 當前持倉 (股票表格)

## 🎨 設計特點

### 色彩系統 (科技紫藍系)

| 元素 | 色值 | 說明 |
|------|------|------|
| 主色 | #6B21A8 | 紫色 - 用於標題、重點文字 |
| 次色 | #06B6D4 | 青色 - 用於漸變 |
| 成功 | #10B981 | 綠色 - 用於正面指標 |
| 背景 | #F5F0FF | 淡紫粉色 - 頁面背景 |
| 卡片 | #FFFFFF | 白色 - 卡片背景 |
| 邊框 | #E8E0FF | 淡紫 - 卡片邊框 |

### 佈局特點

- **固定頭部** - 280px 側邊欄 + 64px 頂部導航
- **響應式設計** - 自動適配各種屏幕尺寸
- **現代化卡片** - 圓角、陰影、懸停效果
- **交互式圖表** - 使用 Plotly.js 渲染
- **實時數據** - 通過 API 調用獲取最新數據

## 🔌 API 端點

Flask 應用提供以下 REST API 端點：

### `GET /`
主頁面 - 返回 HTML 模板

### `GET /api/metrics`
返回關鍵績效指標

**響應示例：**
```json
{
    "total_value": 125345.01,
    "annual_return": 15.50,
    "sharpe_ratio": 1.25,
    "max_drawdown": 12.34,
    "win_rate": 55.23,
    "daily_change": 2.34,
    "holdings": 4
}
```

### `GET /api/chart-data`
返回圖表數據

**響應示例：**
```json
{
    "dates": ["2024-01-01", "2024-01-02", ...],
    "prices": [100.00, 100.50, ...],
    "cumulative_returns": [0.00, 0.50, ...],
    "daily_returns": [0.50, 0.25, ...]
}
```

### `GET /api/holdings`
返回持倉列表

**響應示例：**
```json
[
    {
        "symbol": "AAPL",
        "price": "$185.40",
        "quantity": "100",
        "value": "$18,540",
        "change": "+2.5%"
    },
    ...
]
```

## 🎯 功能説明

### 側邊欄控制

- **時間範圍選擇**：切換不同的時間周期（1日、7日、30日、90日、全年）
- **風險級別**：選擇風險偏好（低、中、高）

### 指標卡片

四個主要指標卡片顯示：
- **💰 總資產** - 投資組合的總價值
- **📈 年度報酬** - 年化投資回報率
- **📊 持倉數** - 當前持倉的股票數量
- **⚡ 風險評分** - 基於最大回撤的風險等級

### 圖表

1. **資產走勢圖** - 顯示過去 12 個月的價格變化
2. **累積回報圖** - 顯示投資的累積回報曲線
3. **日回報分佈** - 直方圖顯示日回報的分佈情況

### 持倉表格

顯示當前所有持倉的詳細信息：
- 股票代碼、現價、持倉數量、市值、漲跌百分比

## 🔧 自定義

### 修改顏色系統

編輯 `static/css/style.css` 中的 CSS 變量：

```css
:root {
    --primary: #6B21A8;           /* 改成你想要的主色 */
    --secondary: #06B6D4;         /* 改成你想要的次色 */
    --success: #10B981;           /* 改成你想要的成功色 */
    ...
}
```

### 修改數據

編輯 `app_html_flask.py` 中的數據生成函數：

```python
def generate_portfolio_data(days=365):
    # 修改這個函數來改變生成的數據
    ...
```

### 添加新的 API 端點

在 `app_html_flask.py` 中添加新的路由：

```python
@app.route('/api/custom-endpoint')
def custom_endpoint():
    return jsonify({'data': 'your_data'})
```

然後在 `static/js/app.js` 中調用它。

## 📱 響應式設計

應用在以下屏幕尺寸下進行了優化：

- **桌面** (>1200px) - 4 列指標卡片，並排圖表
- **平板** (768px-1200px) - 2 列指標卡片，堆疊圖表
- **手機** (<768px) - 單列佈局，隱藏側邊欄菜單

## 🚨 常見問題

### Q: 為什麼圖表不顯示？
A: 確保 Flask 應用正在運行，檢查瀏覽器控制台的錯誤信息。可能是 API 調用失敗。

### Q: 如何更新實時數據？
A: 應用會每 30 秒自動刷新指標和持倉數據。可以在 `static/js/app.js` 中修改時間間隔。

### Q: 如何部署到生產環境？
A: 使用 WSGI 服務器（如 Gunicorn）代替 Flask 開發服務器：
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app_html_flask:app
```

### Q: 如何添加身份驗證？
A: 可以使用 Flask-Login 或其他認證庫：
```python
from flask_login import LoginManager, login_required

@app.route('/api/metrics')
@login_required
def api_metrics():
    ...
```

## 📚 技術棧

| 組件 | 技術 |
|------|------|
| 後端 | Python Flask |
| 前端 | HTML5 + CSS3 + JavaScript |
| 圖表 | Plotly.js |
| 數據處理 | Pandas + NumPy |
| 樣式系統 | CSS Variables (CSS Custom Properties) |

## 🔄 數據流

```
Frontend (HTML/JS)
    ↓ (API 請求)
Flask Backend
    ↓ (Pandas/NumPy 計算)
Portfolio Data
    ↓ (JSON 響應)
Frontend (更新 DOM + 渲染圖表)
```

## 🛠️ 開發提示

### 調試

啟用 Flask 調試模式以獲取詳細的錯誤信息：

```python
if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### 監控 API 調用

打開瀏覽器開發者工具 (F12) → Network 標籤，可以看到所有 API 調用。

### 修改圖表

Plotly.js 配置在 `static/js/app.js` 的圖表函數中。查看 [Plotly 文檔](https://plotly.com/javascript/) 了解更多選項。

## 📞 支援

如有任何問題，請檢查：
1. 確保 Python 版本 >= 3.7
2. 確保所有依賴已正確安裝
3. 檢查 Flask 應用日誌中的錯誤信息
4. 確保端口 5000 未被占用

## 📄 許可證

© 2026 Krystal AI Trading System. All rights reserved.

---

**祝你使用愉快！🎉**

由 Claude Code 設計 | HTML + Flask 現代化儀表板
