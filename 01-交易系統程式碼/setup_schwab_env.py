#!/usr/bin/env python3
"""安全的 Schwab 环境变量设置工具"""
import os
from pathlib import Path
from getpass import getpass

def setup_env():
    print("="*60)
    print("🔐 Schwab OAuth 環境變數設置")
    print("="*60)
    print()
    print("⚠️  警告：client_secret 是高度敏感的信息")
    print("   請勿分享給任何人，也勿提交到 Git")
    print()

    # 檢查是否已存在 .env
    env_file = Path(".env")
    if env_file.exists():
        print(f"📁 .env 文件已存在: {env_file.absolute()}")
        overwrite = input("要覆蓋現有的 .env 嗎？(y/n): ").strip().lower()
        if overwrite != "y":
            print("✋ 已取消")
            return False

    # 輸入 client_id
    print()
    print("📝 請從 Schwab Developer Portal 複製以下信息：")
    print()
    client_id = input("1️⃣  輸入 client_id: ").strip()
    if not client_id:
        print("❌ client_id 不能為空")
        return False

    # 輸入 client_secret（隱藏輸入）
    print()
    client_secret = getpass("2️⃣  輸入 client_secret (輸入時不顯示): ").strip()
    if not client_secret:
        print("❌ client_secret 不能為空")
        return False

    # 確認 redirect_uri
    redirect_uri = "http://127.0.0.1:8787/callback"
    print()
    print(f"3️⃣  Redirect URI (預設): {redirect_uri}")
    custom = input("要更改嗎？(y/n): ").strip().lower()
    if custom == "y":
        redirect_uri = input("輸入自訂 redirect_uri: ").strip()
        if not redirect_uri:
            redirect_uri = "http://127.0.0.1:8787/callback"

    # 確認信息
    print()
    print("="*60)
    print("📋 確認以下信息：")
    print(f"   client_id:     {client_id[:20]}...")
    print(f"   client_secret: {'*' * len(client_secret)}")
    print(f"   redirect_uri:  {redirect_uri}")
    print("="*60)
    print()

    confirm = input("確認無誤？(y/n): ").strip().lower()
    if confirm != "y":
        print("✋ 已取消")
        return False

    # 寫入 .env
    env_content = f"""# Schwab OAuth Configuration
SCHWAB_CLIENT_ID={client_id}
SCHWAB_CLIENT_SECRET={client_secret}
SCHWAB_REDIRECT_URI={redirect_uri}

# 禁用 Google Sheets（可選）
# DISABLE_SHEETS=0
"""

    try:
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)

        # 設置文件權限（Unix 風格）
        os.chmod(env_file, 0o600)

        print()
        print(f"✅ .env 文件已創建！")
        print(f"   位置: {env_file.absolute()}")
        print(f"   權限: 600 (只有你可以讀取)")
        print()
        print("💡 下一步：運行以下命令驗證設置")
        print("   python check_setup.py")
        print()
        print("✅ 然後運行 OAuth 初始化：")
        print("   python init_schwab_oauth.py")
        return True

    except Exception as e:
        print(f"❌ 寫入 .env 失敗: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = setup_env()
    sys.exit(0 if success else 1)
