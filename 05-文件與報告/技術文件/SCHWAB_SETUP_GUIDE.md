# 🔌 Schwab API 整合完全指南

## 📋 當前狀態
- ✅ **Schwab OAuth 框架已完整實作** (`brokers/schwab_oauth.py`)
- ✅ **Schwab API 函數已完整實作** (`brokers/schwab_api.py`)
- ✅ **已整合到持倉同步系統** (`brokers/sync_positions.py`)
- ⏳ **等待 Schwab Client ID 審核通過**

---

## 🚀 準備步驟（審核通過後）

### Step 1️⃣: 申請 Schwab Developer App

1. 登入 [Schwab Developer Portal](https://developer.schwab.com)
2. 建立應用 (Application)
3. 獲取以下信息：
   - **Client ID**（例如：`abcd1234efgh5678`）
   - **Client Secret**（例如：`xyz789...`）
   - **Redirect URI**（設為：`http://127.0.0.1:8787/callback`）

### Step 2️⃣: 設定環境變數

在 `.env` 文件加入：

```bash
SCHWAB_CLIENT_ID=你的_client_id
SCHWAB_CLIENT_SECRET=你的_client_secret
SCHWAB_REDIRECT_URI=http://127.0.0.1:8787/callback
```

### Step 3️⃣: 首次 OAuth 認證（只需一次）

執行以下 Python 代碼：

```python
import os
from pathlib import Path
from dotenv import load_dotenv
from brokers.schwab_oauth import interactive_oauth_flow

load_dotenv()

client_id = os.getenv("SCHWAB_CLIENT_ID")
client_secret = os.getenv("SCHWAB_CLIENT_SECRET")
redirect_uri = os.getenv("SCHWAB_REDIRECT_URI")

# token 會保存到 secrets/schwab_token.json
token_path = "secrets/schwab_token.json"

try:
    tokens = interactive_oauth_flow(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        token_path=token_path,
        open_browser=True  # 自動打開瀏覽器
    )
    print("✅ Schwab OAuth 認證成功！")
    print(f"   • Access Token: {tokens.access_token[:30]}...")
    print(f"   • 過期時間: {tokens.expires_at}")
except Exception as e:
    print(f"❌ 認證失敗: {e}")
```

**會發生什麼：**
1. 瀏覽器打開 Schwab 登入頁面
2. 你輸入帳號密碼 + 驗證
3. 自動導向 `http://127.0.0.1:8787/callback`
4. Token 自動保存到 `secrets/schwab_token.json`
5. 控制台顯示 ✅ 成功

### Step 4️⃣: 測試 API 連線

```python
from brokers.schwab_api import (
    get_schwab_accounts,
    get_schwab_all_positions,
    get_schwab_balances,
    is_schwab_enabled
)

# 檢查是否啟用
if is_schwab_enabled():
    print("✅ Schwab 已啟用")

    # 獲取帳戶
    accounts = get_schwab_accounts()
    print(f"帳戶數: {len(accounts.get('accounts', []))}")
    print(accounts)

    # 獲取持倉
    positions = get_schwab_all_positions()
    print(f"持倉數: {len(positions)}")
    for pos in positions:
        print(f"  {pos['symbol']}: {pos['quantity']} @ {pos['averagePrice']}")

    # 獲取餘額
    balances = get_schwab_balances()
    print(f"餘額信息: {balances}")
else:
    print("❌ Schwab 未啟用或無有效 token")
```

### Step 5️⃣: 同步持倉到 Google Sheets

一旦認證成功，執行：

```bash
python brokers/sync_positions.py
```

**會執行：**
- 從 IB 拉取持倉
- 從 Schwab 拉取持倉 ✨
- 從元大拉取持倉
- 全部寫入 Google Sheets 的 `broker_positions`
- 記錄同步日誌到 `sync_logs`

---

## 🔧 Schwab API 函數參考

### 獲取帳戶

```python
from brokers.schwab_api import get_schwab_accounts

accounts = get_schwab_accounts()
# 回傳: {"accounts": [{...}, {...}]}

for acc in accounts["accounts"]:
    print(f"{acc['nickname']} ({acc['accountNumber']})")
```

### 獲取持倉（所有帳戶）

```python
from brokers.schwab_api import get_schwab_all_positions

positions = get_schwab_all_positions()
# 回傳: [
#   {
#     "symbol": "AAPL",
#     "quantity": 10,
#     "averagePrice": 150.25,
#     "marketValue": 1502.50,
#     ...
#   },
#   ...
# ]

for pos in positions:
    print(f"{pos['symbol']}: {pos['quantity']} shares @ ${pos['averagePrice']}")
```

### 獲取帳戶餘額

```python
from brokers.schwab_api import get_schwab_balances

balances = get_schwab_balances()
# 回傳:
# {
#   "accountNumber": "...",
#   "balances": {
#     "cash": {"value": 50000, "currency": "USD"},
#     "stocks": {"value": 100000, "currency": "USD"},
#     ...
#   }
# }
```

---

## 🔑 Token 管理

### Token 自動 Refresh

所有 API 函數會自動檢查 token 有效性，過期時自動 refresh：

```python
# 內部自動執行，無需手動調用
from brokers.schwab_oauth import get_valid_access_token

tokens = get_valid_access_token(client_id, client_secret, token_path)
# 自動 refresh 如果過期
```

### 手動 Refresh Token

```python
from brokers.schwab_oauth import (
    refresh_access_token,
    load_tokens,
    save_tokens
)

cfg = load_config_from_env()
tokens = load_tokens("secrets/schwab_token.json")

if tokens:
    new_tokens = refresh_access_token(
        cfg.client_id,
        cfg.client_secret,
        tokens.refresh_token
    )
    save_tokens("secrets/schwab_token.json", new_tokens)
    print("✅ Token 已刷新")
```

---

## 🐛 排查問題

### 問題 1: "OAuth error" / "timeout"

**原因：** OAuth 流程失敗或超時（通常是瀏覽器沒有正確授權）

**解決：**
```python
# 重新執行 OAuth（會清除舊 token）
from brokers.schwab_oauth import interactive_oauth_flow
import os

tokens = interactive_oauth_flow(
    client_id=os.getenv("SCHWAB_CLIENT_ID"),
    client_secret=os.getenv("SCHWAB_CLIENT_SECRET"),
    redirect_uri=os.getenv("SCHWAB_REDIRECT_URI"),
    token_path="secrets/schwab_token.json"
)
```

### 問題 2: "401 Unauthorized" / API 返回 None

**原因：** Token 無效或已過期且 refresh 失敗

**解決：**
1. 檢查環境變數是否正確
2. 檢查 `secrets/schwab_token.json` 是否存在
3. 重新執行 OAuth 認證
4. 檢查 Schwab 平台是否限制了 API 訪問

### 問題 3: "沒有持倉"

**原因：**
- Schwab 帳戶確實沒有持倉
- 或者帳戶權限不足（某些帳戶類型不支援 API）

**檢查：**
```python
from brokers.schwab_api import get_schwab_accounts, get_schwab_account_details

accounts = get_schwab_accounts()
for acc in accounts["accounts"]:
    details = get_schwab_account_details(acc["accountNumber"])
    print(f"{acc['nickname']}: {details.get('positions', [])}")
```

---

## 📚 相關文件

- **OAuth 實作**: `brokers/schwab_oauth.py` (197 行)
- **API 實作**: `brokers/schwab_api.py` (完整實作)
- **同步邏輯**: `brokers/sync_positions.py` (已集成)
- **IB 參考**: `brokers/ib_api.py` (架構參考)
- **元大參考**: `brokers/yuanta_api.py` (架構參考)

---

## ✅ 檢查清單

- [ ] Schwab Client ID 已申請
- [ ] Client ID / Secret / Redirect URI 已設定到 `.env`
- [ ] 執行過一次 `interactive_oauth_flow()`
- [ ] `secrets/schwab_token.json` 已生成
- [ ] `get_schwab_accounts()` 能正確回應
- [ ] `sync_positions.py` 能同步 Schwab 持倉
- [ ] Google Sheets 已收到 Schwab 持倉數據

---

## 🎯 下一步

當 Client ID 審核通過：
1. 填入 `.env`
2. 執行 OAuth 認證
3. 測試 API 連線
4. 運行 `sync_positions.py` 同步持倉

就這麼簡單！🚀
