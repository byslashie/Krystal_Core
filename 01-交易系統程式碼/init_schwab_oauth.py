#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schwab OAuth 初始化腳本
首次運行時會打開瀏覽器進行登入，並保存 refresh_token
"""
import os
import sys
from pathlib import Path

# 設置 UTF-8 編碼
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from brokers.schwab_oauth import interactive_oauth_flow

def init_schwab():
    # 讀取環境變數
    client_id = os.getenv("SCHWAB_CLIENT_ID")
    client_secret = os.getenv("SCHWAB_CLIENT_SECRET")
    redirect_uri = os.getenv("SCHWAB_REDIRECT_URI", "http://127.0.0.1:8787/callback")

    if not client_id or not client_secret:
        print("❌ 缺少 SCHWAB_CLIENT_ID 或 SCHWAB_CLIENT_SECRET")
        print("請先在 .env 檔案中設定這些環境變數")
        return False

    # Token 保存路徑
    token_path = ".secrets/schwab_tokens.json"

    print(f"🔐 Schwab OAuth 初始化")
    print(f"   Client ID: {client_id[:10]}...")
    print(f"   Redirect URI: {redirect_uri}")
    print()

    try:
        # 運行互動式 OAuth 流程
        tokens = interactive_oauth_flow(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            token_path=token_path,
            open_browser=True
        )

        print(f"✅ OAuth 成功！")
        print(f"   Access Token: {tokens.access_token[:20]}...")
        print(f"   Refresh Token: {tokens.refresh_token[:20]}...")
        print(f"   Token 已保存到: {token_path}")
        print()
        print("💡 提示：Refresh token 有效期通常很長")
        print("   系統會自動使用它來更新 access token")
        return True

    except Exception as e:
        print(f"❌ OAuth 失敗: {e}")
        return False

if __name__ == "__main__":
    # 嘗試從 .env 加載環境變數
    from dotenv import load_dotenv
    load_dotenv()

    success = init_schwab()
    exit(0 if success else 1)
