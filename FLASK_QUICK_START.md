# 🚀 Flask 快速啟動指南

## 快速命令（方案 3）

### Windows
```bash
# 方法 1：直接運行 BAT
./start_flask.bat

# 方法 2：PowerShell
powershell -ExecutionPolicy Bypass -File ./start_flask.ps1

# 方法 3：使用 cd 命令
cd 01-交易系統程式碼 && python app_html_flask.py
```

### Mac/Linux
```bash
# 給腳本添加執行權限（首次運行）
chmod +x start_flask.sh

# 運行腳本
./start_flask.sh
```

---

## 設置別名（可選 - 一次性設置）

### Windows (PowerShell)

1. **找到 PowerShell 配置文件位置**：
   ```powershell
   $PROFILE
   ```

2. **編輯配置文件**（如不存在則創建）：
   ```powershell
   notepad $PROFILE
   ```

3. **添加以下內容**：
   ```powershell
   # Flask 快速啟動
   function Start-Flask {
       Set-Location "G:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼"
       python app_html_flask.py
   }

   Set-Alias -Name flask-start -Value Start-Flask
   ```

4. **保存並重啟 PowerShell**

5. **使用別名**：
   ```powershell
   flask-start
   ```

### Mac/Linux (Bash)

1. **編輯 bash 配置文件**：
   ```bash
   nano ~/.bash_profile
   # 或
   nano ~/.bashrc
   ```

2. **添加以下內容**：
   ```bash
   # Flask 快速啟動
   alias flask-start='bash ~/path/to/start_flask.sh'
   ```

3. **使用配置**：
   ```bash
   source ~/.bash_profile
   ```

4. **使用別名**：
   ```bash
   flask-start
   ```

---

## 在 Claude Code 中快速啟動

### 使用 /loop 命令（定時啟動）

每 2 小時自動檢查並運行 Flask：
```bash
/loop 2h cd "01-交易系統程式碼" && python app_html_flask.py
```

### 使用背景運行

```bash
# Windows - 後台運行不顯示窗口
start /B start_flask.bat

# Mac/Linux - 後台運行
nohup ./start_flask.sh > /dev/null 2>&1 &
```

---

## 訪問儀表板

啟動後，在瀏覽器訪問：

🌐 **本地地址**：`http://127.0.0.1:8888`

或 **遠程訪問**（如配置）：
- 檢查 Flask 應用中的 `app.run(host='0.0.0.0', port=8888)`

---

## ⚡ 一鍵啟動流程

### Windows 最簡單方案
1. 雙擊 `start_flask.bat` 文件
2. 等待 Flask 啟動
3. 訪問 `http://127.0.0.1:8888`

### Mac 最簡單方案
1. 打開終端
2. 運行：`cd ~/path/to/Krystal_完整系統 && ./start_flask.sh`
3. 訪問 `http://127.0.0.1:8888`

---

## 🛑 停止 Flask

- **命令行**：按 `Ctrl+C`
- **Windows BAT 窗口**：關閉窗口或按 `Ctrl+C`
- **後台運行**（需要強制停止）：
  ```bash
  # Windows
  taskkill /F /IM python.exe

  # Mac/Linux
  pkill -f "python.*app_html_flask"
  ```

---

## 🔍 故障排查

### Flask 沒有啟動？

1. **檢查 Python 路徑**：
   ```bash
   which python3        # Mac/Linux
   where python         # Windows
   ```

2. **檢查依賴**：
   ```bash
   pip list | grep flask
   ```

3. **檢查端口占用**：
   ```bash
   # Windows
   netstat -ano | findstr :8888

   # Mac/Linux
   lsof -i :8888
   ```

4. **嘗試更改端口**（編輯 `app_html_flask.py`）：
   ```python
   if __name__ == '__main__':
       app.run(host='127.0.0.1', port=9999)  # 改為 9999
   ```

---

## 📌 推薦配置

| 場景 | 推薦方案 |
|------|--------|
| 🖥️ 每日自動啟動 | 工作排程器（Windows）或 Launchd（Mac） |
| ⚡ 快速手動啟動 | 雙擊 BAT 或運行腳本 |
| 🔄 定時監控啟動 | `/loop 2h` 命令 |
| 🎯 開發測試 | 直接運行 Python 命令 |

---

**最後更新**：2026-03-20
