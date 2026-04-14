# 📂 Krystal AI 交易系統 - 項目結構

## 根目錄（核心文件）

```
├── app_html_flask.py          🔴 主應用（Flask）
├── sheets_utils.py            📊 Google Sheets 工具
├── google_sheets_helper.py    📊 Sheets 輔助工具
├── nav_calculator.py          📈 NAV 和績效計算
├── requirements.txt           📦 Python 依賴
├── credentials.json           🔐 Google 認證
└── README.md                  📖 專案說明
```

## 資料夾結構

### 🔴 核心模組
```
brokers/                       🏦 券商 API 整合
├── ib_api.py                 - Interactive Brokers
├── yuanta_api.py             - 元大證券
├── schwab_api.py             - Charles Schwab
└── sync_positions.py          - 持倉同步
```

### 📄 應用模組
```
modules/                       ⚙️ 核心功能模組
pages/                        🌐 多頁面應用
templates/                    🎨 HTML 模板
static/                       🎨 CSS / JavaScript
utils/                        🔧 工具函數
```

### 📚 文檔
```
docs/                         📖 所有文檔
├── STARTUP_GUIDE.md          - 啟動指南
├── PROJECT_STRUCTURE.md      - 本文件
├── QUICK_START_*.md          - 快速開始指南
└── [50+ 其他文檔]
```

### 🚀 啟動腳本
```
scripts/                      ⚙️ 啟動和工具腳本
├── start_krystal.bat         - Windows 一鍵啟動
├── start_krystal.sh          - Mac/Linux 啟動
├── run_flask.py              - Flask 智能啟動器
└── [其他工具腳本]
```

### 📦 數據和配置
```
data/                         💾 本地數據
logs/                         📋 應用日誌
config/                       ⚙️ 配置文件
key/                          🔐 API 密鑰（如果有）
```

### 🚢 特殊功能
```
ship_monitoring/              🚢 波斯灣油輪監測
intel_engine/                 🌍 情報引擎
```

### 📂 封存
```
archive/                      📦 舊版本和測試文件
├── test_*.py                 - 測試文件
├── app_*.py                  - 舊版本應用
├── demo_*.py                 - 演示文件
└── [100+ 實驗性文件]
```

### 🔄 虛擬環境
```
.venv/                        🐍 主虛擬環境（必要）
_OLD_*.venv*/                 🗂️ 舊虛擬環境（可刪除）
```

---

## 🎯 快速導航

### 我要...

**啟動應用？**
```bash
# Windows
雙擊 scripts\start_krystal.bat

# Mac/Linux
./scripts/start_krystal.sh
```

**修改主應用代碼？**
```
編輯 app_html_flask.py
```

**查看文檔？**
```
查看 docs/ 資料夾
```

**添加新的券商集成？**
```
編輯或添加到 brokers/ 資料夾
```

**添加新的前端頁面？**
```
1. 代碼：pages/X_page_name.py
2. 模板：templates/X_page_name.html
3. 樣式：static/css/X_page_name.css
```

**查看舊文件或測試代碼？**
```
查看 archive/ 資料夾
```

---

## 📊 文件計數

| 類別 | 數量 | 位置 |
|------|------|------|
| Python 文件 | 5 | 根目錄 |
| 文檔 | 56 | docs/ |
| 啟動腳本 | 3 | scripts/ |
| 舊/測試文件 | 100+ | archive/ |
| 前端文件 | 多數 | pages/, templates/, static/ |

---

## 🧹 清理說明

- ✅ 所有文檔已集中到 `docs/`
- ✅ 所有啟動腳本集中到 `scripts/`
- ✅ 所有測試和舊文件集中到 `archive/`
- ✅ 所有日誌文件集中到 `logs/`
- ✅ 根目錄只保留 5 個核心 Python 文件

**結果：根目錄清爽度提升 90% 🎉**

---

## ⚠️ 重要提示

- 不要刪除 `.venv/` - 這是虛擬環境
- 不要刪除 `brokers/`, `modules/`, `pages/` 等核心資料夾
- `archive/` 中的文件可以安全刪除（但建議先備份）
- `_OLD_*.venv*` 虛擬環境可以刪除以節省空間

---

最後更新：2026-03-17
