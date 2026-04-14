# 🚀 GitHub 部署指南 - 在家用 Mac 訪問項目

## 📌 目標
將項目上傳到 GitHub，這樣你在家用 Mac 時可以輕鬆拉取代碼並運行。

---

## 🔧 第 1 步：在 Windows 上初始化 Git 倉庫

### 1.1 進入項目目錄
```powershell
cd G:\我的雲端硬碟\Krystal_AI_Trading_System
```

### 1.2 初始化 Git
```powershell
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### 1.3 創建 `.gitignore` 文件
```powershell
# 創建 .gitignore 來排除不需要上傳的文件
$gitignore = @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
env/
.venv

# Flask
instance/
.webassets-cache

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
flask_app.log
*.log

# 敏感信息
credentials.json
.env
.env.local

# OS
.DS_Store
Thumbs.db

# 臨時文件
*.tmp
*.temp

# 只保留關鍵目錄
!pages/
!modules/
!brokers/
!utils/
!templates/
!static/
"@

Set-Content -Path .gitignore -Value $gitignore -Encoding UTF8
```

### 1.4 添加所有文件到 Git
```powershell
git add .
```

### 1.5 查看將要提交的文件
```powershell
git status
```

你應該看到類似的輸出：
```
On branch master
Changes to be committed:
  new file:   app_html_flask.py
  new file:   data_layer.py
  new file:   templates/dashboard.html
  new file:   static/css/dashboard.css
  new file:   static/js/dashboard.js
  ...（其他文件）
```

### 1.6 提交代碼
```powershell
git commit -m "Initial commit: HTML + Flask 多頁面儀表板系統

- Flask 後端應用（app_html_flask.py）
- 統一數據層（data_layer.py）
- 多頁面儀表板（5 個頁面）
- Google Sheets 集成
- Broker API 支持（IB、Yuanta、Schwab）
- 響應式設計（桌面、平板、手機）
- 9 個 REST API 端點
- 完整文檔"
```

---

## 📱 第 2 步：在 GitHub 上創建倉庫

### 2.1 訪問 GitHub
1. 進入 https://github.com
2. 登錄你的 GitHub 帳戶（如果沒有，請先註冊）

### 2.2 創建新倉庫
1. 點擊 **New Repository**（或 GitHub 首頁右上角的 **+** → **New repository**）

2. 填寫信息：
   - **Repository name**: `Krystal-AI-Trading-System`
   - **Description**: `Krystal AI 量化交易系統 - HTML + Flask 多頁面儀表板`
   - **Public** or **Private**: 選擇你喜歡的（公開更方便分享，私密更安全）
   - **Add .gitignore**: 不選（我們已經創建了）
   - **Add a README**: 暫時不選

3. 點擊 **Create repository**

### 2.3 你會看到類似的頁面，里面有命令
```
…or push an existing repository from the command line

git remote add origin https://github.com/YourUsername/Krystal-AI-Trading-System.git
git branch -m main
git push -u origin main
```

---

## 🔑 第 3 步：將代碼推送到 GitHub

### 3.1 添加遠程倉庫
```powershell
git remote add origin https://github.com/YourUsername/Krystal-AI-Trading-System.git
```

**替換 `YourUsername` 為你的 GitHub 用戶名！**

### 3.2 重命名分支（如果需要）
```powershell
git branch -m master main
```

或者保持 `master` 分支（GitHub 默認是 `main`，但都可以）

### 3.3 推送代碼
```powershell
git push -u origin main
```

**首次推送會要求認證：**
- 如果使用 HTTPS：輸入你的 GitHub 用戶名和密碼（或 Personal Access Token）
- 如果使用 SSH：需要提前設置 SSH 密鑰

### 3.4 驗證推送成功
在瀏覽器中進入你的倉庫頁面：
```
https://github.com/YourUsername/Krystal-AI-Trading-System
```

你應該看到所有的文件都已上傳！✅

---

## 💻 第 4 步：在 Mac 上克隆和運行項目

### 4.1 打開終端
```bash
# 在 Mac 上打開終端（Terminal.app 或 iTerm2）
```

### 4.2 選擇一個工作目錄
```bash
# 例如：進入文檔目錄
cd ~/Documents

# 或創建一個新目錄
mkdir Projects
cd Projects
```

### 4.3 克隆倉庫
```bash
git clone https://github.com/YourUsername/Krystal-AI-Trading-System.git
cd Krystal-AI-Trading-System
```

### 4.4 創建虛擬環境（推薦）
```bash
# 創建虛擬環境
python3 -m venv venv

# 激活虛擬環境
source venv/bin/activate

# 你應該看到終端提示符前有 (venv)
```

### 4.5 安裝依賴
```bash
# 升級 pip
pip install --upgrade pip

# 安裝必要的包
pip install flask pandas numpy gspread google-auth-oauthlib
```

### 4.6 啟動 Flask 應用
```bash
python app_html_flask.py
```

**預期輸出：**
```
[*] Flask 應用啟動...
[*] 訪問: http://localhost:5000
[*] 數據層狀態: OK
 * Running on http://127.0.0.1:5000
```

### 4.7 訪問應用
在瀏覽器中進入：
```
http://localhost:5000
```

✅ 完成！你的應用應該在 Mac 上正常運行！

---

## 📋 完整工作流程總結

### **在 Windows 上（現在）:**
```powershell
# 1. 初始化 Git
git init
git config user.name "Your Name"
git config user.email "your@email.com"

# 2. 添加文件
git add .

# 3. 提交
git commit -m "Initial commit: ..."

# 4. 添加遠程
git remote add origin https://github.com/YourUsername/Krystal-AI-Trading-System.git

# 5. 推送
git push -u origin main
```

### **在 Mac 上（回家時）:**
```bash
# 1. 克隆倉庫
git clone https://github.com/YourUsername/Krystal-AI-Trading-System.git

# 2. 進入目錄
cd Krystal-AI-Trading-System

# 3. 創建虛擬環境
python3 -m venv venv
source venv/bin/activate

# 4. 安裝依賴
pip install flask pandas numpy gspread google-auth-oauthlib

# 5. 運行應用
python app_html_flask.py

# 6. 訪問
# 在瀏覽器中進入 http://localhost:5000
```

---

## 🔄 後續更新（在任何地方）

### **當你在 Mac 上修改代碼後想要同步回 Windows：**

```bash
# 在 Mac 上
git add .
git commit -m "修改描述"
git push origin main

# 然後在 Windows 上
git pull origin main
```

### **當你在 Windows 上修改代碼後想要同步到 Mac：**

```powershell
# 在 Windows 上
git add .
git commit -m "修改描述"
git push origin main

# 然後在 Mac 上
git pull origin main
```

---

## 🐛 常見問題

### Q1: 推送時出現 "fatal: not a git repository" 錯誤
**原因:** 沒有初始化 Git
**解決:** 重新運行 `git init`

### Q2: 推送時要求輸入密碼
**解決方案 A:** 輸入你的 GitHub 密碼（新版 GitHub 需要使用 Personal Access Token）
**解決方案 B:** 設置 SSH 密鑰（更安全，推薦）

### Q3: 克隆時出現 "Could not resolve host" 錯誤
**原因:** 網絡連接問題或 Git 未安裝
**解決:**
- 檢查網絡連接
- 在 Mac 上安裝 Git：`brew install git`

### Q4: 在 Mac 上運行 Flask 時出現 "ModuleNotFoundError: No module named 'flask'"
**解決:** 確保虛擬環境已激活並安裝了依賴
```bash
source venv/bin/activate
pip install flask pandas numpy
```

---

## 🔐 安全提示

### **不要上傳的敏感文件：**
- ❌ `credentials.json` - Google API 認證
- ❌ `.env` - 環境變數
- ❌ API 密鑰或個人令牌

**我們已經在 `.gitignore` 中排除了這些文件。**

### **如果不小心上傳了敏感文件：**
```bash
# 從 Git 歷史中移除該文件
git rm --cached credentials.json
git commit -m "Remove sensitive file"
git push
```

然後立即更改你的 API 密鑰！

---

## 💡 進階技巧

### **創建分支進行實驗：**
```bash
# 創建並切換到新分支
git checkout -b feature/new-feature

# 進行修改...

# 推送分支
git push origin feature/new-feature

# 然後在 GitHub 上創建 Pull Request
```

### **查看提交歷史：**
```bash
git log --oneline
```

### **撤銷最後一個提交：**
```bash
git reset --soft HEAD~1
```

---

## 📚 有用的 GitHub 功能

### **README.md - 項目主頁**
在根目錄創建 `README.md` 文件來描述項目：

```markdown
# Krystal AI 量化交易系統

## 簡介
完整的企業級量化交易儀表板...

## 安裝
1. 克隆倉庫
2. 安裝依賴
3. 運行應用

## 使用
訪問 http://localhost:5000

## 功能
- 5 個功能頁面
- 9 個 REST API 端點
- ...
```

### **Issues - 追蹤問題**
在 GitHub 上創建 Issue 來追蹤 Bug 或功能請求

### **Wiki - 文檔**
在倉庫的 Wiki 標籍中添加詳細文檔

---

## 🎉 完成！

現在你可以：
✅ 在 Windows 上開發
✅ 推送到 GitHub
✅ 在 Mac 上克隆和運行
✅ 在兩台電腦之間同步代碼

---

## 📱 快速參考

```bash
# Mac 上快速啟動應用的完整命令
cd ~/Documents/Krystal-AI-Trading-System
source venv/bin/activate
python app_html_flask.py
# 然後訪問 http://localhost:5000
```

---

**祝你在 Mac 上使用愉快！** 🚀🍎

有任何 Git 或 GitHub 問題，可以隨時詢問！
