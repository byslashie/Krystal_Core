# 🚀 Krystal AI 交易系統 - 快速啟動指南

## Windows 用戶

### 方式 1：最簡單（推薦）✨
1. 打開 `scripts/` 資料夾
2. 找到 `start_krystal.bat`
3. **雙擊** 即可啟動
4. Flask 會自動在 http://localhost:5501（或其他可用端口）啟動
5. 關閉黑色視窗即停止應用

### 方式 2：Command Prompt/PowerShell
```cmd
cd "G:\我的雲端硬碟\Krystal_AI_Trading_System\scripts"
start_krystal.bat
```

---

## Mac / Linux 用戶

### 方式 1：Terminal 執行（推薦）✨
1. 打開 **Terminal**
2. 執行以下命令：
```bash
cd "/Volumes/GoogleDrive/My Drive/Krystal_AI_Trading_System/scripts"
./start_krystal.sh
```

3. 或直接用路徑執行：
```bash
bash ~/GoogleDrive/Krystal_AI_Trading_System/scripts/start_krystal.sh
```

### 方式 2：Finder 雙擊（需要額外設置）
如果想在 Finder 中雙擊 `start_krystal.sh`：
1. 打開 `scripts/` 資料夾
2. 右鍵點擊 `start_krystal.sh`
3. 選擇 **「打開方式」** → **「其他」**
4. 選擇 **「Terminal.app」** 或 **「Script Editor」**

---

## 兩個平台都需要的準備

### 首次設置
確保已安裝依賴：
```bash
# Windows
.venv\Scripts\pip install -r requirements.txt

# Mac/Linux
source .venv/bin/activate
pip install -r requirements.txt
```

### 虛擬環境檢查
確保虛擬環境存在：
- **Windows**：`.venv\Scripts\activate.bat` 存在
- **Mac/Linux**：`.venv/bin/activate` 存在

如果不存在，運行：
```bash
# Windows
python -m venv .venv

# Mac/Linux
python3 -m venv .venv
```

---

## 訪問應用

### 首次啟動
1. 執行啟動腳本後，會看到類似的輸出：
```
==================================================
  Krystal AI 交易系統 - Flask 應用
==================================================
✅ 使用端口: 5501
📱 訪問地址: http://localhost:5501
==================================================
```

2. 在瀏覽器打開 http://localhost:5501

### 如果 5501 被佔用
應用會自動選擇下一個可用端口（5502、5503 等），注意控制台的輸出訊息。

---

## 常見問題

### Q: 無法連接到 http://localhost:5501？
**A:**
- 檢查控制台輸出，應用可能在其他端口
- 確保防火牆允許本地連接
- 嘗試 http://127.0.0.1:5501

### Q: "ModuleNotFoundError: No module named 'flask'"？
**A:** 虛擬環境未正確激活或缺少依賴
```bash
# Windows
.venv\Scripts\pip install flask

# Mac/Linux
source .venv/bin/activate
pip install flask
```

### Q: Mac 上執行 .sh 時顯示 "Permission denied"？
**A:** 設置執行權限：
```bash
chmod +x start_krystal.sh
```

### Q: 如何停止應用？
- **Windows**：關閉 CMD 視窗，或按 Ctrl+C
- **Mac/Linux**：在 Terminal 按 Ctrl+C

---

## 進階：後台運行（Mac/Linux）

如果想應用在後台運行：
```bash
nohup ./start_krystal.sh > krystal.log 2>&1 &
```

查看日誌：
```bash
tail -f krystal.log
```

停止後台應用：
```bash
ps aux | grep python
kill -9 [PID]
```

---

## 支持的環境

| 系統 | 版本 | 啟動文件 | 狀態 |
|------|------|---------|------|
| Windows | 10/11 | `start_krystal.bat` | ✅ 完全支持 |
| Mac | 10.14+ | `start_krystal.sh` | ✅ 完全支持 |
| Linux | 任意 | `start_krystal.sh` | ✅ 完全支持 |

---

**祝您使用愉快！** 🎉
