# ⚡ GitHub 快速設置（5 分鐘）

## 🟢 在 Windows 上（現在做）

### 步驟 1: 打開 PowerShell，進入項目目錄
```powershell
cd G:\我的雲端硬碟\Krystal_AI_Trading_System
```

### 步驟 2: 初始化 Git
```powershell
git init
git config user.name "Your Name"
git config user.email "your@email.com"
```

### 步驟 3: 添加所有文件
```powershell
git add .
```

### 步驟 4: 提交
```powershell
git commit -m "Initial commit: Krystal AI Trading System"
```

### 步驟 5: 創建 GitHub 倉庫
1. 進入 https://github.com
2. 點擊 **New Repository**
3. 命名為 `Krystal-AI-Trading-System`
4. 點擊 **Create repository**

### 步驟 6: 連接到 GitHub（複製以下命令）
```powershell
# 替換 YourUsername 為你的 GitHub 用戶名
git remote add origin https://github.com/YourUsername/Krystal-AI-Trading-System.git
git branch -m main
git push -u origin main
```

✅ **完成！** 你的代碼現在在 GitHub 上了。

---

## 🟠 在 Mac 上（回家時）

### 步驟 1: 打開終端，克隆倉庫
```bash
cd ~/Documents
git clone https://github.com/YourUsername/Krystal-AI-Trading-System.git
cd Krystal-AI-Trading-System
```

### 步驟 2: 設置虛擬環境
```bash
python3 -m venv venv
source venv/bin/activate
```

### 步驟 3: 安裝依賴
```bash
pip install flask pandas numpy gspread google-auth-oauthlib
```

### 步驟 4: 運行應用
```bash
python app_html_flask.py
```

### 步驟 5: 訪問應用
在瀏覽器中進入：
```
http://localhost:5000
```

✅ **完成！** 應用現在在 Mac 上運行了。

---

## 💡 關鍵點

| 操作 | Windows | Mac |
|------|---------|-----|
| 進入項目 | `cd G:\我的雲端硬碟\...` | `cd ~/Documents/...` |
| 激活虛擬環境 | `venv\Scripts\activate` | `source venv/bin/activate` |
| 運行應用 | `python app_html_flask.py` | `python app_html_flask.py` |
| 訪問 | http://localhost:5000 | http://localhost:5000 |

---

## 📞 需要幫助？

詳細指南：👉 **[GITHUB_DEPLOYMENT_GUIDE.md](GITHUB_DEPLOYMENT_GUIDE.md)**

---

**現在就開始吧！** 🚀
