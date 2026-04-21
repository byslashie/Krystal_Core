# 📋 CSV/Excel 導入集成計劃

**版本**：v1.1  
**日期**：2026-04-07  
**目標**：將 XQ 策略導入功能集成到 Dashboard v8  
**狀態**：🚀 階段 1 完成（後端 API + 前端上傳）

---

## 🎯 功能需求

### 核心功能
- ✅ 上傳 CSV/Excel 檔案
- ✅ 自動偵測並轉換編碼（Big5 → UTF-8）
- ✅ 驗證數據格式（17 列、必填欄位）
- ✅ 自動計算所有 P&L 指標
- ✅ 預覽轉換後的數據
- ✅ 一鍵導入到資料庫
- ✅ 顯示導入結果和摘要

### 顯示位置
1. **新增「策略導入」分頁** — 主要的導入界面
2. **已平倉交易** — 導入後顯示在交易列表
3. **投資組合分析** — 自動更新統計數據
4. **市場比較** — 更新超額回報

---

## 🏗️ 技術架構

```
前端 (index.html)
├─ 新增「策略導入」Tab
│  ├─ 檔案上傳區域（拖拽或點選）
│  ├─ 進度條（編碼轉換、數據驗證、計算）
│  ├─ 數據預覽表格（17 列）
│  ├─ 驗證結果（✅/❌）
│  └─ 導入按鈕（一鍵導入）
│
└─ 已平倉交易頁面
   └─ 標記「導入」來源的交易

後端 (app.py)
├─ POST /api/strategy/import
│  ├─ 接收上傳的檔案
│  ├─ 編碼偵測和轉換
│  ├─ 格式驗證
│  ├─ P&L 計算
│  └─ 返回預覽
│
├─ POST /api/strategy/import/confirm
│  └─ 確認並保存到 DB
│
└─ GET /api/strategy/imports
   └─ 查詢導入歷史

數據庫
├─ realized_trades（新增欄位）
│  ├─ source = "import"（標記來源）
│  ├─ import_batch_id（批次 ID）
│  └─ validation_status
│
└─ import_log（新表）
   ├─ import_id
   ├─ file_name
   ├─ file_encoding
   ├─ rows_imported
   ├─ calculation_status
   └─ imported_at
```

---

## 📊 API 端點規範

### 1. 上傳和預覽

**端點**：`POST /api/strategy/import`

**請求**：
```
Content-Type: multipart/form-data

File: [CSV 或 Excel 檔案]
```

**響應**：
```json
{
  "status": "success",
  "preview": {
    "file_name": "260401_強勢股加碼.csv",
    "detected_encoding": "Big5",
    "converted_encoding": "UTF-8",
    "row_count": 75,
    "column_count": 17,
    "columns": ["策略名稱", "股票代碼", ...],
    "data": [
      {
        "策略名稱": "台股強勢股加碼",
        "股票代碼": "2330.TW",
        "批次序號": 1,
        "進場日期時間": "2026-04-01 09:30",
        "進場價格": 450.00,
        "進場數量": 100,
        "出場日期時間": "2026-04-07 14:00",
        "出場價格": 465.50,
        "出場數量": 100,
        "持倉天數": 6,
        "毛利": 1550.00,
        "P&L": 1409.05,
        "P&L %": 0.0313,
        "累積P&L": 2800.00,
        "累積P&L %": 0.0312,
        "出場原因": "技術面獲利"
      }
    ],
    "validation": {
      "valid": true,
      "errors": [],
      "warnings": []
    },
    "summary": {
      "total_trades": 75,
      "symbols": ["2330.TW", "2301.TW", ...],
      "date_range": "2026-04-01 ~ 2026-04-07",
      "total_pnl": 123456.78,
      "total_return": 0.1234,
      "win_rate": 0.6222
    }
  }
}
```

### 2. 確認導入

**端點**：`POST /api/strategy/import/confirm`

**請求**：
```json
{
  "file_name": "260401_強勢股加碼.csv",
  "import_batch_id": "batch_20260407_001",
  "strategy_name": "台股強勢股加碼",
  "confirmed": true
}
```

**響應**：
```json
{
  "status": "success",
  "import_id": "import_001",
  "rows_imported": 75,
  "new_trades": 75,
  "duplicates_skipped": 0,
  "message": "成功導入 75 筆交易"
}
```

### 3. 查詢導入歷史

**端點**：`GET /api/strategy/imports`

**響應**：
```json
{
  "status": "success",
  "imports": [
    {
      "import_id": "import_001",
      "file_name": "260401_強勢股加碼.csv",
      "strategy_name": "台股強勢股加碼",
      "rows_imported": 75,
      "imported_at": "2026-04-07 15:30:00",
      "total_pnl": 123456.78,
      "total_return": 0.1234
    }
  ]
}
```

---

## 📝 P&L 計算規則

### 自動計算的欄位

當用戶上傳 CSV 時，後端自動計算：

| 欄位 | 公式 | 範例 |
|------|------|------|
| 毛利 | (出場價 - 進場價) × 數量 | 1550.00 |
| 買進手續費 | 進場價 × 進場數量 × 0.001425% | 0.64 |
| 賣出手續費 | 出場價 × 出場數量 × 0.001425% | 0.66 |
| 稅費 | 出場價 × 出場數量 × 0.3% (台股) | 139.65 |
| P&L | 毛利 - 手續費 - 稅費 | 1409.05 |
| P&L % | P&L / (進場價 × 數量) | 0.0313 |
| 持倉天數 | exit_date - entry_date | 6 |
| 累積 P&L | ∑ 同股票所有批次 | 2800.00 |
| 累積 P&L % | 累積 P&L / 累積投入 | 0.0312 |

### 驗證的欄位

檢查上傳的 CSV 是否包含或正確：

```
✅ 必填欄位：
  - 策略名稱（非空）
  - 股票代碼（符合格式：6碼.TW 或美股代碼）
  - 進場日期時間（有效日期）
  - 進場價格（> 0）
  - 進場數量（正整數）
  - 出場日期時間（>= 進場時間）
  - 出場價格（> 0）
  - 出場數量（正整數）
  
✅ 數據一致性：
  - 出場日期 >= 進場日期
  - 出場價格和進場價格合理（無異常波動）
  - 數量匹配（通常出場數 <= 進場數）
```

---

## 🖼️ 前端 UI 設計

### 策略導入分頁布局

```
┌─────────────────────────────────────────────────┐
│  策略導入                                         │
├─────────────────────────────────────────────────┤
│                                                 │
│  📁 檔案上傳區域                                 │
│  ┌─────────────────────────────────────────┐   │
│  │  拖拽檔案到此  或  點選選擇              │   │
│  │  支援格式：.csv, .xlsx                  │   │
│  │                                         │   │
│  │  [選擇檔案按鈕]                         │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  📊 轉換進度                                     │
│  ├─ 編碼偵測  ████████░░ 80%                  │
│  ├─ 格式驗證  ████████░░ 80%                  │
│  ├─ P&L 計算  ████░░░░░░ 40%                  │
│  └─ 總進度    ████░░░░░░ 40%                  │
│                                                 │
│  📋 數據預覽 (前 5 行)                          │
│  ┌──────────────────────────────────────────┐  │
│  │ 策略名稱 │ 代碼  │ 進場價 │ 出場價 │ P&L % │  │
│  ├──────────────────────────────────────────┤  │
│  │ 強勢股加碼│2330.TW│450.00 │465.50 │3.13% │  │
│  │ 強勢股加碼│2330.TW│448.00 │465.50 │3.91% │  │
│  │ 光磊科技│2301.TW│520.00 │512.50 │-1.13%│  │
│  │ ......  │ .... │ ...   │ ...   │ ...  │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ✅ 驗證結果                                     │
│  ✓ 共 75 筆交易                                 │
│  ✓ 17 列格式正確                                │
│  ✓ 編碼: Big5 → UTF-8 轉換成功                  │
│  ✓ 日期格式: 全部有效                           │
│  ⚠ 警告: 5 筆交易缺少「出場原因」               │
│                                                 │
│  📈 摘要統計                                     │
│  ├─ 總交易: 75 筆                              │
│  ├─ 涵蓋日期: 2026-04-01 ~ 2026-04-07         │
│  ├─ 總 P&L: ¥123,456.78                       │
│  ├─ 回報率: 12.34%                            │
│  └─ 勝率: 62.22%                              │
│                                                 │
│  [取消]  [導入到資料庫]                         │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 導入完成提示

```
✅ 導入成功！

已導入 75 筆交易
├─ 新增: 75 筆
├─ 跳過重複: 0 筆
└─ 失敗: 0 筆

📊 統計更新
├─ 已平倉交易: +75
├─ 年初至今回報: 12.34% (已更新)
├─ Sharpe 比率: 1.45 (已更新)
└─ 最大回撤: -8.45% (已更新)

相關交易已顯示在「已平倉交易」頁面
檢視 →
```

---

## 💾 資料庫更新

### realized_trades 表新增欄位

```sql
ALTER TABLE realized_trades ADD COLUMN (
  source VARCHAR(20),              -- "import" 或 "manual"
  import_batch_id VARCHAR(50),     -- 導入批次 ID
  validation_status VARCHAR(20),   -- "valid" 或 "warning"
  original_file_name VARCHAR(255)  -- 原始檔案名稱
);
```

### 新建 import_log 表

```sql
CREATE TABLE import_log (
  id INTEGER PRIMARY KEY,
  import_id VARCHAR(50) UNIQUE,
  file_name VARCHAR(255),
  file_encoding VARCHAR(20),
  rows_total INTEGER,
  rows_imported INTEGER,
  rows_skipped INTEGER,
  rows_failed INTEGER,
  total_pnl REAL,
  total_return REAL,
  win_rate REAL,
  calculation_status VARCHAR(20),
  validation_errors TEXT,
  imported_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔧 後端實現步驟

### Step 1: 新增 CSV 處理模塊

創建 `csv_processor.py`：

```python
# -*- coding: utf-8 -*-
import pandas as pd
import chardet
from pathlib import Path
from datetime import datetime

class CSVProcessor:
    def __init__(self):
        self.supported_encodings = ['utf-8', 'big5', 'gb2312', 'cp1252']
    
    def detect_encoding(self, file_path):
        """偵測檔案編碼"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(100000)
        
        result = chardet.detect(raw_data)
        return result['encoding'], result['confidence']
    
    def load_csv(self, file_path, encoding=None):
        """載入 CSV"""
        if encoding is None:
            encoding, _ = self.detect_encoding(file_path)
        
        return pd.read_csv(file_path, encoding=encoding)
    
    def validate_schema(self, df):
        """驗證 17 列格式"""
        required_columns = [
            '策略名稱', '股票代碼', '批次序號', '進場日期時間',
            '進場價格', '進場數量', '出場日期時間', '出場價格',
            '出場數量', '持倉天數', '毛利', 'P&L', 'P&L %',
            '累積P&L', '累積P&L %', '出場原因'
        ]
        
        missing = set(required_columns) - set(df.columns)
        if missing:
            return False, f"缺少列: {missing}"
        
        return True, "格式正確"
    
    def calculate_pnl(self, row):
        """計算 P&L 指標"""
        # 根據 BACKTESTING_CALCULATIONS.md 的公式
        entry_price = row['進場價格']
        exit_price = row['出場價格']
        quantity = row['進場數量']
        
        gross_pnl = (exit_price - entry_price) * quantity
        
        # 手續費（台股 0.001425%）
        entry_fee = entry_price * quantity * 0.001425 / 100
        exit_fee = exit_price * quantity * 0.001425 / 100
        
        # 稅費（台股賣出 0.3%）
        tax = exit_price * quantity * 0.3 / 100
        
        net_pnl = gross_pnl - entry_fee - exit_fee - tax
        pnl_pct = net_pnl / (entry_price * quantity)
        
        return {
            'gross_pnl': gross_pnl,
            'entry_fee': entry_fee,
            'exit_fee': exit_fee,
            'tax': tax,
            'pnl': net_pnl,
            'pnl_pct': pnl_pct
        }
```

### Step 2: 新增 Flask 路由

在 `app.py` 中添加：

```python
from flask import request, jsonify
from werkzeug.utils import secure_filename
import uuid

@app.route('/api/strategy/import', methods=['POST'])
def import_strategy():
    """上傳並預覽 CSV/Excel"""
    if 'file' not in request.files:
        return jsonify({'error': '未找到檔案'}), 400
    
    file = request.files['file']
    
    # 保存臨時檔案
    filename = secure_filename(file.filename)
    temp_path = f"temp_uploads/{uuid.uuid4()}_{filename}"
    file.save(temp_path)
    
    try:
        # 處理檔案
        processor = CSVProcessor()
        df = processor.load_csv(temp_path)
        
        # 驗證格式
        valid, msg = processor.validate_schema(df)
        if not valid:
            return jsonify({'error': msg}), 400
        
        # 計算 P&L
        for idx, row in df.iterrows():
            pnl_calc = processor.calculate_pnl(row)
            for key, val in pnl_calc.items():
                df.loc[idx, key] = val
        
        # 返回預覽
        return jsonify({
            'status': 'success',
            'preview': {
                'file_name': filename,
                'row_count': len(df),
                'data': df.head(10).to_dict('records'),
                'summary': {
                    'total_pnl': df['pnl'].sum(),
                    'win_rate': (df['pnl'] > 0).sum() / len(df)
                }
            }
        })
    
    finally:
        os.remove(temp_path)
```

---

## 🎯 實施優先級

### Phase 1（第 1 週）— 核心功能
- [ ] CSV 上傳端點 (`POST /api/strategy/import`)
- [ ] 編碼轉換邏輯
- [ ] P&L 計算邏輯
- [ ] 數據預覽接口

### Phase 2（第 2 週）— UI 和確認
- [ ] 前端「策略導入」分頁
- [ ] 檔案拖拽上傳
- [ ] 進度條和驗證結果顯示
- [ ] 導入確認邏輯

### Phase 3（第 3 週）— 集成和優化
- [ ] 數據保存到資料庫
- [ ] 自動更新統計數據
- [ ] 導入歷史查詢
- [ ] 錯誤恢復機制

---

## 📌 關鍵要點

### 編碼轉換
```
原始檔案（Big5）
    ↓ [自動偵測]
CSV Processor
    ↓ [轉換為 UTF-8]
內存 DataFrame
    ↓ [驗證格式]
計算 P&L
    ↓ [預覽]
用戶確認
    ↓ [導入]
資料庫
```

### P&L 計算準確性
```
✅ 必須使用 BACKTESTING_CALCULATIONS.md 的公式
✅ 台股手續費: 0.001425%
✅ 台股稅費: 0.3% (賣出)
✅ 美股手續費: 根據券商（預設 0.001%）
✅ 美股稅費: 0%
```

### 數據驗證層級
```
1️⃣ 檔案格式（CSV/Excel）
2️⃣ 編碼有效性
3️⃣ 列數和列名
4️⃣ 必填欄位
5️⃣ 數據類型（日期、數字、整數）
6️⃣ 邏輯驗證（日期順序、價格合理性）
```

---

## 📚 相關文檔

- `XQ_STRATEGY_IMPORT_TEMPLATE.md` — 導入格式規範
- `BACKTESTING_CALCULATIONS.md` — P&L 計算公式
- `convert_encoding.py` — 編碼轉換工具
- `ENCODING_CONVERSION_GUIDE.md` — 轉換工具使用指南

---

**版本**：v1.0  
**完成度**：計劃階段  
**下一步**：開始 Phase 1 實施
