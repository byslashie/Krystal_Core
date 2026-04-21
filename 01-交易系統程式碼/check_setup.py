#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""檢查 Schwab 設置是否完備"""
import os
import sys
from pathlib import Path

# 設置 UTF-8 編碼
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def check_setup():
    print("🔍 檢查 Schwab OAuth 設置...\n")

    # 檢查 .env 文件
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env 文件不存在")
        print("   請在項目根目錄創建 .env 文件，內容如下：")
        print("""
SCHWAB_CLIENT_ID=你的client_id
SCHWAB_CLIENT_SECRET=你的client_secret
SCHWAB_REDIRECT_URI=http://127.0.0.1:8787/callback
""")
        return False

    # 加載 .env
    from dotenv import load_dotenv
    load_dotenv()

    # 檢查必需的環境變數
    checks = {
        "SCHWAB_CLIENT_ID": "Schwab Client ID",
        "SCHWAB_CLIENT_SECRET": "Schwab Client Secret",
    }

    all_ok = True
    for var, desc in checks.items():
        val = os.getenv(var)
        if val and len(val) > 0:
            print(f"✅ {desc}: {val[:15]}...")
        else:
            print(f"❌ {desc}: 未設定")
            all_ok = False

    # 檢查必需的 Python 包
    print("\n🔍 檢查 Python 依賴...\n")
    required_packages = ["requests", "dotenv"]
    for pkg in required_packages:
        try:
            __import__(pkg.replace("-", "_"))
            print(f"✅ {pkg} 已安裝")
        except ImportError:
            print(f"❌ {pkg} 未安裝，請執行: pip install {pkg}")
            all_ok = False

    # 檢查 tokens 路徑
    print("\n🔍 檢查 token 保存路徑...\n")
    tokens_dir = Path(".secrets")
    if tokens_dir.exists():
        print(f"✅ {tokens_dir} 目錄存在")
    else:
        print(f"ℹ️  {tokens_dir} 目錄會在首次 OAuth 時自動創建")

    print("\n" + "="*50)
    if all_ok:
        print("✅ 所有檢查通過！可以運行 OAuth 初始化")
        print("   python init_schwab_oauth.py")
    else:
        print("❌ 有些設置不完整，請先修正上方的問題")

    return all_ok

if __name__ == "__main__":
    success = check_setup()
    sys.exit(0 if success else 1)
