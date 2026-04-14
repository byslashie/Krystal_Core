# 📝 編碼轉換工具使用指南

**工具名稱**：convert_encoding.py  
**版本**：v1.0  
**用途**：將 CSV/Excel 檔案從 Big5、GB2312 等編碼轉換為 UTF-8

---

## 🚀 快速開始

### 1. 準備環境（第一次使用）

```bash
# 安裝必要的套件
pip install pandas chardet openpyxl

# 驗證安裝
python convert_encoding.py
```

### 2. 轉換檔案

```bash
# 最簡單的用法（自動偵測編碼）
python convert_encoding.py 260401_強勢股加碼-兩次.csv

# 指定輸出檔名
python convert_encoding.py input.csv output_utf8.csv

# 指定輸入編碼（如果自動偵測失敗）
python convert_encoding.py input.csv output.csv big5

# Excel 檔案
python convert_encoding.py 260401_強勢股加碼-兩次.xlsx
```

### 3. 輸出檔案

轉換後會產生：
- `260401_強勢股加碼-兩次_UTF8.csv` (UTF-8 編碼)
- `260401_強勢股加碼-兩次_UTF8.xlsx` (UTF-8 編碼)

---

## 🔧 工具功能

### 自動編碼偵測
```
✅ 支援的編碼格式：
  - UTF-8
  - Big5 (繁體中文 Windows)
  - GB2312 (簡體中文)
  - CP1252 (西歐)
  - Latin-1

工具會自動偵測檔案編碼並轉換
```

### 數據驗證
```
轉換完成後會自動驗證：
  ✅ 列數是否正確
  ✅ 行數是否完整
  ✅ 數據是否完全讀取
  ✅ 列名是否正確識別
  ✅ 前3行預覽確認
```

### 支援格式
```
CSV 檔案：
  輸入：任何編碼的 .csv
  輸出：UTF-8 編碼的 .csv

Excel 檔案：
  輸入：任何編碼的 .xlsx/.xls
  輸出：UTF-8 編碼的 .xlsx
```

---

## 📋 使用步驟

### 方案 1：拖拽執行（最簡單）

```
1. 將 convert_encoding.py 複製到你的檔案夾
2. 將要轉換的 CSV/Excel 放在同一資料夾
3. 在命令列執行：
   python convert_encoding.py 260401_強勢股加碼-兩次.csv
4. 等待完成 → 出現 output_UTF8.csv
```

### 方案 2：指定路徑執行

```bash
# 如果檔案不在同一資料夾
python convert_encoding.py "G:\我的雲端硬碟\...\input.csv" ".\output.csv"
```

### 方案 3：指定編碼（如果自動偵測失敗）

```bash
# Big5 編碼
python convert_encoding.py input.csv output.csv big5

# GB2312 編碼
python convert_encoding.py input.csv output.csv gb2312
```

---

## 📊 輸出範例

執行後會顯示：

```
============================================================
XQ 策略導入 - 編碼轉換工具
============================================================

📥 處理 CSV: 260401_強勢股加碼-兩次.csv
📍 偵測到編碼: Big5 (信心度: 95.2%)
✅ 使用編碼: Big5
📖 使用編碼 Big5 讀取...
✅ 讀取成功: 75 行, 17 列
   列名: ['策略名稱', '股票代碼', '批次序號', ...]
💾 轉換並保存為 UTF-8...
✅ 轉換完成: 260401_強勢股加碼-兩次_UTF8.csv

🔍 驗證數據完整性...
✅ 列數: 17
✅ 行數: 75
✅ 無空白列: True

📋 列名:
    1. 策略名稱
    2. 股票代碼
    3. 批次序號
   ...

📊 數據預覽 (前3行):
   策略名稱  股票代碼  批次序號 ...
0  台股強勢股加碼  2330.TW  1 ...
1  台股強勢股加碼  2330.TW  2 ...
2  光磊科技  2301.TW  1 ...

✅ 轉換完成！
```

---

## 🛠️ 故障排除

### 問題 1：找不到檔案
```
❌ 錯誤：FileNotFoundError: [Errno 2] No such file or directory

解決：
  1. 檢查檔案名稱是否正確
  2. 檢查檔案是否在指定路徑
  3. 使用完整路徑：python convert_encoding.py "完整路徑\檔案.csv"
```

### 問題 2：無法偵測編碼
```
❌ 錯誤：無法偵測或轉換編碼

解決：
  1. 嘗試指定編碼：python convert_encoding.py input.csv output.csv big5
  2. 或用 big5, gb2312, cp1252 試試
  3. 如果還是不行，檢查檔案是否損壞
```

### 問題 3：缺少套件
```
❌ 錯誤：ModuleNotFoundError: No module named 'pandas'

解決：
  pip install pandas chardet openpyxl
```

### 問題 4：Excel 讀取失敗
```
❌ 錯誤：openpyxl 無法讀取檔案

解決：
  1. 確認檔案格式是 .xlsx（不是 .xls）
  2. 嘗試先用 Excel 開啟並重新保存
  3. 或轉換為 CSV 再處理
```

### 問題 5：轉換後還是亂碼
```
❌ 問題：開啟轉換後的檔案還是看不懂

解決：
  1. 確認使用 UTF-8 兼容的編輯器（VS Code, Notepad++ 等）
  2. 或用 Excel 開啟（會自動識別 UTF-8）
  3. 如果還是亂碼，原始檔案可能已損壞
```

---

## ✅ 驗證轉換成功

轉換完成後，檢查：

- [ ] 輸出檔案存在（_UTF8.csv 或 _UTF8.xlsx）
- [ ] 行數和列數一致
- [ ] 列名正確識別（中文顯示正常）
- [ ] 數據預覽顯示正確
- [ ] 能用 Excel 或文字編輯器開啟

---

## 🔄 工作流程

```
你提供檔案
    ↓
我執行轉換工具
    ↓
自動偵測編碼
    ↓
轉換為 UTF-8
    ↓
驗證數據完整性
    ↓
輸出新檔案
    ↓
檢查列名和數據正確
```

---

## 📌 重要提醒

### 安全性
```
✅ 原始檔案不會被修改
✅ 轉換後的檔案會新增 "_UTF8" 後綴
✅ 所有操作都是本地執行，無上傳風險
```

### 兼容性
```
✅ 轉換後的 UTF-8 檔案可在任何地方使用
✅ Excel、Google Sheets、Python 都能讀取
✅ 可直接匯入 Dashboard v8
```

### 備份建議
```
建議保留原始檔案，不要直接覆蓋
原始: 260401_強勢股加碼-兩次.csv
轉換後: 260401_強勢股加碼-兩次_UTF8.csv
```

---

## 💡 進階用法

### 批量轉換多個檔案

創建 `batch_convert.py`：

```python
import os
import subprocess

# 轉換資料夾中的所有 CSV
folder = r"G:\我的雲端硬碟\Krystal_完整系統\02-策略知識庫\Strategies"
for file in os.listdir(folder):
    if file.endswith('.csv'):
        subprocess.run(['python', 'convert_encoding.py', 
                       os.path.join(folder, file)])
```

執行：
```bash
python batch_convert.py
```

---

## 📞 需要幫助

如果轉換失敗：

1. **告訴我檔案名稱和副檔名**
2. **我會執行轉換工具**
3. **自動偵測編碼並轉換**
4. **驗證數據完整性**
5. **給你轉換後的 UTF-8 檔案**

---

**版本**：v1.0  
**最後更新**：2026-04-07  
**維護者**：Krystal  
**工具狀態**：Ready ✅
