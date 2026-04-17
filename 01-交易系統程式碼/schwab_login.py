#!/usr/bin/env python3
"""Schwab 首次登入腳本 - 執行一次即可取得 token（Windows 相容）"""
import os, sys, pathlib
sys.stdout.reconfigure(encoding='utf-8')

def main():
    from dotenv import load_dotenv
    load_dotenv()

    API_KEY    = os.getenv('SCHWAB_CLIENT_ID', '')
    APP_SECRET = os.getenv('SCHWAB_CLIENT_SECRET', '')
    CALLBACK   = os.getenv('SCHWAB_REDIRECT_URI', 'https://127.0.0.1:8787/callback')
    TOKEN_FILE = pathlib.Path(__file__).parent / '.secrets' / 'schwab_token.json'

    if not API_KEY or not APP_SECRET:
        print("❌ 找不到 SCHWAB_CLIENT_ID / SCHWAB_CLIENT_SECRET，請確認 .env 已設定")
        sys.exit(1)

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    print(f"API Key : {API_KEY[:10]}...")
    print(f"Callback: {CALLBACK}")
    print(f"Token 將存至: {TOKEN_FILE}")
    print()
    print("⏳ 即將開啟瀏覽器，請登入 Schwab 帳號並允許授權...")
    print("   登入後瀏覽器會自動跳轉，程式會自動接收 code")

    import schwab
    client = schwab.auth.easy_client(
        api_key=API_KEY,
        app_secret=APP_SECRET,
        callback_url=CALLBACK,
        token_path=str(TOKEN_FILE),
        interactive=False,
    )

    print()
    print("✅ 登入成功！Token 已儲存。")
    print(f"   位置: {TOKEN_FILE}")

    # 快速測試：抓帳戶列表
    try:
        resp = client.get_account_numbers()
        accounts = resp.json()
        print(f"\n📋 找到 {len(accounts)} 個帳戶：")
        for a in accounts:
            print(f"   • {a.get('accountNumber','?')}  hash={a.get('hashValue','?')[:12]}...")
    except Exception as e:
        print(f"⚠️  帳戶查詢: {e}")

if __name__ == '__main__':
    main()
