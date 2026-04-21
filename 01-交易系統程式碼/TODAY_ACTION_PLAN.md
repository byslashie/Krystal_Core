# 🚀 今日行動計劃（4/7 星期一）

**時間**：現在開始  
**目標**：準備環境 + 第一階段開始（Token 系統）  
**預計用時**：2-3 小時

---

## ⏱️ 時間表

```
現在-10 分  → 步驟 1-3：環境驗證
10-30 分    → 步驟 4-5：檢查現有代碼
30-60 分    → 步驟 6-7：修復 init 腳本
60 分+      → 步驟 8：首次 OAuth 授權
```

---

## 📋 具體步驟

### 步驟 1️⃣：驗證 .env 配置（5 分鐘）

**目標**：確保環境變數已設置

```bash
# 檢查 .env 是否存在
ls -la "01-交易系統程式碼/.env"

# 檢查內容
cat "01-交易系統程式碼/.env" | grep SCHWAB

# 預期看到：
# SCHWAB_CLIENT_ID=xxx
# SCHWAB_CLIENT_SECRET=yyy
# SCHWAB_REDIRECT_URI=http://127.0.0.1:8787/callback
```

**如果沒有 .env**：
```bash
cd 01-交易系統程式碼
python setup_schwab_env.py
# 按照提示輸入 SCHWAB_CLIENT_ID 和 SECRET
```

---

### 步驟 2️⃣：驗證目錄結構（3 分鐘）

**目標**：確保所有必需的文件都存在

```bash
# 檢查 brokers 目錄
ls -la 01-交易系統程式碼/brokers/
# 應該看到：
#   schwab_oauth.py ✅
#   schwab_api.py ✅

# 檢查 dashboard_v8
ls -la 01-交易系統程式碼/dashboard_v8/ | grep -E "app.py|index.html"
# 應該看到：
#   app.py ✅
#   index.html ✅

# 檢查 .secrets 目錄（可能不存在）
ls -la 01-交易系統程式碼/.secrets/ 2>&1
# 不用擔心是否存在，init 腳本會創建
```

---

### 步驟 3️⃣：驗證 Python 依賴（2 分鐘）

**目標**：確保必需的 Python 包已安裝

```bash
# 檢查必需的包
python -c "import flask; import requests; import dotenv; print('✅ All packages installed')"

# 如果有缺失，安裝它們
pip install flask requests python-dotenv
```

---

### 步驟 4️⃣：閱讀 OAuth 框架（10 分鐘）

**目標**：理解 Schwab OAuth 的工作原理

```bash
# 查看 Token 管理的核心函數
head -50 01-交易系統程式碼/brokers/schwab_oauth.py

# 應該看到：
#   - SchwabTokens 類定義
#   - build_login_url() 函數
#   - exchange_code_for_refresh_token() 函數
#   - interactive_oauth_flow() 主函數
```

**核心概念**：
```
OAuth 流程：
1. 用戶點擊「登入」
2. 打開瀏覽器進入 Schwab 登入頁面
3. 用戶授權
4. Schwab 重定向回 http://127.0.0.1:8787/callback?code=xxx
5. 本地 HTTP server 捕獲 code
6. 用 code 交換 access_token 和 refresh_token
7. 保存 token 到 .secrets/schwab_token.json
```

---

### 步驟 5️⃣：檢查現有的 init 腳本（5 分鐘）

**目標**：看看 init_schwab_oauth.py 目前的狀態

```bash
# 查看文件
cat 01-交易系統程式碼/init_schwab_oauth.py

# 應該看到：
#   - 嘗試導入 brokers.schwab_oauth（這行會失敗）
#   - 調用 interactive_oauth_flow()
#   - 保存 token 到文件
```

**問題識別**：
```
❌ 第 15 行：from brokers.schwab_oauth import interactive_oauth_flow
   為什麼會失敗？
   Python 找不到 brokers 模塊

✅ 解決方法：
   在 01-交易系統程式碼/ 目錄執行，Python 會找到 brokers/
```

---

### 步驟 6️⃣：修復 init_schwab_oauth.py（10 分鐘）

**目標**：修復 import 問題，讓腳本可以執行

```bash
# 方案 A：在項目根目錄創建 __init__.py
touch 01-交易系統程式碼/brokers/__init__.py

# 方案 B：修改 sys.path
# 編輯 init_schwab_oauth.py，在頂部添加：
cat > "01-交易系統程式碼/init_schwab_oauth_fixed.py" << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent))

from brokers.schwab_oauth import interactive_oauth_flow
from dotenv import load_dotenv

def init_schwab():
    load_dotenv()
    
    client_id = os.getenv("SCHWAB_CLIENT_ID")
    client_secret = os.getenv("SCHWAB_CLIENT_SECRET")
    redirect_uri = os.getenv("SCHWAB_REDIRECT_URI", "http://127.0.0.1:8787/callback")

    if not client_id or not client_secret:
        print("❌ 缺少 SCHWAB_CLIENT_ID 或 SCHWAB_CLIENT_SECRET")
        return False

    token_path = ".secrets/schwab_tokens.json"

    try:
        print(f"🔐 Schwab OAuth 初始化")
        print(f"   Client ID: {client_id[:10]}...")
        print(f"   Redirect URI: {redirect_uri}")
        
        tokens = interactive_oauth_flow(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            token_path=token_path,
            open_browser=True
        )

        print(f"✅ OAuth 成功！")
        print(f"   Access Token: {tokens.access_token[:20]}...")
        print(f"   Token 已保存到: {token_path}")
        return True

    except Exception as e:
        print(f"❌ OAuth 失敗: {e}")
        return False

if __name__ == "__main__":
    success = init_schwab()
    sys.exit(0 if success else 1)
EOF

# 測試新腳本
cd 01-交易系統程式碼
python init_schwab_oauth_fixed.py
```

**預期輸出**：
```
🔐 Schwab OAuth 初始化
   Client ID: xxxxxxxx...
   Redirect URI: http://127.0.0.1:8787/callback

[瀏覽器會自動打開登入頁面]

✅ OAuth 成功！
   Access Token: eyJhbGciOiJIUzI1NiI...
   Token 已保存到: .secrets/schwab_tokens.json
```

---

### 步驟 7️⃣：驗證 Token 文件（3 分鐘）

**目標**：確認 token 已正確保存

```bash
# 檢查文件是否存在
ls -la 01-交易系統程式碼/.secrets/schwab_tokens.json

# 查看內容（不要全部顯示敏感信息）
cat 01-交易系統程式碼/.secrets/schwab_tokens.json | head -5

# 預期看到：
# {
#   "access_token": "...",
#   "refresh_token": "...",
#   "expires_at": 1712500000
# }
```

**檢查清單**：
- [ ] 文件存在於 `.secrets/schwab_tokens.json`
- [ ] 包含 `access_token`
- [ ] 包含 `refresh_token`
- [ ] 包含 `expires_at`（Unix timestamp）

---

### 步驟 8️⃣：驗證 Token 加載（5 分鐘）

**目標**：確認系統能正確讀取和驗證 token

```bash
# 創建測試腳本
cat > "01-交易系統程式碼/test_token_load.py" << 'EOF'
#!/usr/bin/env python3
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from brokers.schwab_oauth import load_tokens, get_valid_access_token
from dotenv import load_dotenv

load_dotenv()

# 測試 1：加載 token
print("測試 1：加載 token...")
tokens = load_tokens(".secrets/schwab_tokens.json")
if tokens:
    print(f"✅ Token 加載成功")
    print(f"   Access Token: {tokens.access_token[:30]}...")
    print(f"   Refresh Token: {tokens.refresh_token[:30]}...")
    print(f"   Expires at: {tokens.expires_at}")
else:
    print(f"❌ Token 加載失敗")
    sys.exit(1)

# 測試 2：驗證有效性
print("\n測試 2：驗證 token 有效性...")
try:
    valid_token = get_valid_access_token(
        os.getenv("SCHWAB_CLIENT_ID"),
        os.getenv("SCHWAB_CLIENT_SECRET"),
        ".secrets/schwab_tokens.json"
    )
    print(f"✅ Token 驗證成功（有效）")
except Exception as e:
    print(f"❌ Token 驗證失敗: {e}")
    sys.exit(1)

print("\n✅ 所有測試通過！Token 系統就緒。")
EOF

# 運行測試
python test_token_load.py
```

**預期輸出**：
```
測試 1：加載 token...
✅ Token 加載成功
   Access Token: eyJhbGciOiJIUzI1NiI...
   Refresh Token: REFRESH_TOKEN_VALUE...
   Expires at: 1712500000

測試 2：驗證 token 有效性...
✅ Token 驗證成功（有效）

✅ 所有測試通過！Token 系統就緒。
```

---

## 🎯 今日成果檢查

完成後，檢查以下項目：

- [ ] .env 已設置 SCHWAB_CLIENT_ID 和 SECRET
- [ ] brokers/ 目錄下有 schwab_oauth.py 和 schwab_api.py
- [ ] 執行 init_schwab_oauth_fixed.py 成功（打開瀏覽器登入）
- [ ] .secrets/schwab_tokens.json 已創建
- [ ] Token 包含 access_token、refresh_token、expires_at
- [ ] test_token_load.py 測試通過

**如果都通過了 ✅，Token 系統就緒！**

---

## ❌ 常見問題（遇到就看）

### Q1：「No module named 'brokers'」

**原因**：Python 找不到 brokers 模塊  
**解決**：
```bash
# 方案 1：在 01-交易系統程式碼/ 目錄執行
cd 01-交易系統程式碼
python init_schwab_oauth.py

# 方案 2：創建 __init__.py
touch brokers/__init__.py
```

### Q2：「Failed to establish a connection」

**原因**：本地 HTTP server (port 8787) 無法監聽  
**解決**：
```bash
# 檢查 port 是否被占用
# Windows: netstat -ano | findstr :8787
# macOS/Linux: lsof -i :8787

# 改用其他 port
export SCHWAB_REDIRECT_URI="http://127.0.0.1:8888/callback"
python init_schwab_oauth.py
```

### Q3：「Timeout waiting for OAuth callback」

**原因**：瀏覽器沒有打開或授權過程超時  
**解決**：
```bash
# 手動打開瀏覽器
# 查看控制台輸出的登入 URL
# 手動訪問這個 URL
# 授權後瀏覽器會自動重定向回 localhost:8787
```

### Q4：「Token 已保存但驗證失敗」

**原因**：Token 格式不正確或已過期  
**解決**：
```bash
# 刪除舊 token，重新授權
rm .secrets/schwab_tokens.json
python init_schwab_oauth.py
```

---

## 🎉 下一步

完成今日任務後（✅ Token 系統就緒）：

### 明天（4/8）
- [ ] 實現 `GET /api/schwab/token-status` 端點
- [ ] 測試 Token 自動刷新機制

### 後天（4/9）
- [ ] 實現 `GET /api/schwab-account-summary` 端點
- [ ] 查詢 Schwab 帳戶列表

### 下個週期（4/10-4/11）
- [ ] 實現持倉同步和 Google Sheets 寫回

---

## 💾 文件位置速查

```
.env                                    ← 環境變數（必須）
01-交易系統程式碼/
├── brokers/
│   ├── schwab_oauth.py                ✅ Token 管理（不需改）
│   └── schwab_api.py                  📝 稍後實現
├── init_schwab_oauth_fixed.py         📝 今天修復的版本
├── test_token_load.py                 📝 測試腳本
├── .secrets/
│   └── schwab_tokens.json             ❌ 待創建（OAuth 後自動建）
└── dashboard_v8/
    └── app.py                         📝 稍後實現端點
```

---

**開始時間**：現在 🚀  
**預計用時**：2-3 小時  
**目標**：Token 系統就緒 ✅

**加油！** 💪
