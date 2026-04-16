# Flask 自動啟動設置指南

## 📋 目錄

- [Windows 工作排程器設置](#windows-工作排程器設置)
- [Mac 自動啟動設置](#mac-自動啟動設置)
- [快速啟動命令](#快速啟動命令)

---

## Windows 工作排程器設置

### 步驟 1：打開工作排程器
1. 按 `Win + R`，輸入 `taskschd.msc` 並按 Enter
2. 或直接搜索「工作排程器」

### 步驟 2：建立新任務

1. **右側面板** → 點擊「建立工作」
2. **常規標籤**：
   - 名稱：`Flask 交易儀表板`
   - 描述：`自動啟動交易系統 Flask 應用`
   - ☑️ 勾選「不論使用者是否登入都執行」
   - ☑️ 以最高權限執行

### 步驟 3：設置觸發時間

1. **觸發程序標籤** → 點擊「新增」
2. **設定**選項：
   - 開始工作：**按排程**
   - 設定：**每日**
   - 時間：
     - **09:00**（交易開盤前）
     - **21:30**（美股開盤前）

3. 重複以上步驟，為每個時間點建立一個觸發程序

### 步驟 4：設置操作

1. **操作標籤** → 點擊「新增」
2. **操作**：選擇「啟動程式」
3. **程式或指令碼**：
   ```
   C:\Windows\System32\cmd.exe
   ```
4. **新增引數**：
   ```
   /c "G:\我的雲端硬碟\Krystal_完整系統\start_flask.bat"
   ```
5. **起始於**：
   ```
   G:\我的雲端硬碟\Krystal_完整系統
   ```

### 步驟 5：設置條件（可選）

- **電源**：☑️ 喚醒電腦以執行此工作

### 步驟 6：完成

點擊「確定」並輸入密碼確認

---

## Mac 自動啟動設置

### 方案 A：使用 Launchd（推薦）

1. **編輯 plist 文件**：
   ```bash
   nano ~/.config/launch/com.krystal.flask.plist
   ```

2. **粘貼以下內容**：
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.krystal.flask</string>

       <key>ProgramArguments</key>
       <array>
           <string>/bin/bash</string>
           <string>/Users/YOUR_USERNAME/path/to/start_flask.sh</string>
       </array>

       <key>StartCalendarInterval</key>
       <array>
           <!-- 09:00 AM -->
           <dict>
               <key>Hour</key>
               <integer>9</integer>
               <key>Minute</key>
               <integer>0</integer>
           </dict>
           <!-- 21:30 PM -->
           <dict>
               <key>Hour</key>
               <integer>21</integer>
               <key>Minute</key>
               <integer>30</integer>
           </dict>
       </array>

       <key>StandardOutPath</key>
       <string>/var/log/flask_startup.log</string>
       <key>StandardErrorPath</key>
       <string>/var/log/flask_startup.err</string>
   </dict>
   </plist>
   ```

3. **加載啟動代理**：
   ```bash
   launchctl load ~/.config/launch/com.krystal.flask.plist
   ```

4. **測試**：
   ```bash
   launchctl start com.krystal.flask
   ```

### 方案 B：使用 Cron

1. **打開 crontab**：
   ```bash
   crontab -e
   ```

2. **添加以下行**：
   ```cron
   # 台股開盤前 09:00
   0 9 * * 1-5 /path/to/start_flask.sh

   # 美股開盤前 21:30
   30 21 * * 0-4 /path/to/start_flask.sh
   ```

3. **保存並退出** (Vim: `:wq`)

---

## 快速啟動命令

### Windows
```bash
# 使用 BAT 文件
start_flask.bat

# 或使用 PowerShell
powershell -ExecutionPolicy Bypass -File start_flask.ps1
```

### Mac/Linux
```bash
# 給腳本執行權限
chmod +x start_flask.sh

# 運行腳本
./start_flask.sh

# 或直接用 bash
bash start_flask.sh
```

---

## 🔍 故障排查

### Windows 工作排程器
- **檢查任務運行狀態**：打開工作排程器 → 檢查「最後運行結果」
- **查看日誌**：Windows 事件檢視器 → Windows 記錄 → 系統
- **手動測試**：右擊任務 → 執行

### Mac/Linux
- **檢查日誌**：
  ```bash
  tail -f /var/log/flask_startup.log
  ```
- **驗證 plist 語法**：
  ```bash
  plutil -lint ~/.config/launch/com.krystal.flask.plist
  ```
- **查看已加載的代理**：
  ```bash
  launchctl list | grep flask
  ```

---

## ⏰ 工作時段設置

根據 CLAUDE.md，推薦的啟動時間：

| 時段 | 時間 | 用途 |
|------|------|------|
| 🌅 早盤 | 09:00 | 台股開盤前準備 |
| 🌙 美股 | 21:30 | 美股開盤前監控 |
| 📊 額外 | 14:00 | 中午回顧（可選） |

---

## ✅ 驗證設置

1. **確認應用啟動**：
   - 訪問 `http://127.0.0.1:8888`
   - 檢查是否能看到儀表板

2. **確認日誌**：
   - Windows：檢查任務排程器歷史
   - Mac：檢查 `/var/log/flask_startup.log`

3. **確認性能**：
   - 應用不應佔用過多內存
   - 應該允許多個實例運行（或配置重啟邏輯）

---

## 🚀 高級配置

### 自動重啟機制
編輯 `start_flask.bat` 或 `start_flask.sh`，添加檢查邏輯：

```bash
#!/bin/bash
# 檢查 Flask 是否已運行
if pgrep -f "python.*app_html_flask.py" > /dev/null; then
    echo "Flask 已運行，跳過啟動"
    exit 0
fi

# 啟動 Flask
python3 app_html_flask.py
```

### 背景運行（不顯示窗口）

**Windows**：
```batch
start "" /B start_flask.bat
```

**Mac/Linux**：
```bash
nohup ./start_flask.sh > /dev/null 2>&1 &
```

---

**最後更新**：2026-03-20
**配置者**：Krystal
