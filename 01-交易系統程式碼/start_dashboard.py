#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Krystal AI Dashboard v8 啟動器
簡單可靠的 Web 伺服器啟動腳本
"""

import os
import sys
import webbrowser
import time
import subprocess
from pathlib import Path

def main():
    # 獲取腳本所在目錄
    script_dir = Path(__file__).parent.absolute()
    dashboard_dir = script_dir / "dashboard_v8"

    print("\n" + "="*50)
    print("🚀 Krystal AI Dashboard v8 啟動器")
    print("="*50 + "\n")

    # 檢查 dashboard_v8 資料夾
    if not dashboard_dir.exists():
        print(f"❌ 錯誤: 找不到 {dashboard_dir}")
        print(f"📍 期望位置: {dashboard_dir}")
        input("\n按 Enter 鍵退出...")
        sys.exit(1)

    index_file = dashboard_dir / "index.html"
    if not index_file.exists():
        print(f"❌ 錯誤: 找不到 {index_file}")
        print(f"\n📂 dashboard_v8 資料夾內容:")
        for item in dashboard_dir.iterdir():
            print(f"  - {item.name}")
        input("\n按 Enter 鍵退出...")
        sys.exit(1)

    print(f"✓ 找到 dashboard_v8: {dashboard_dir}")
    print(f"✓ 找到 index.html: {index_file}")

    # 改變工作目錄到 dashboard_v8
    original_dir = os.getcwd()
    os.chdir(dashboard_dir)
    print(f"✓ 工作目錄: {os.getcwd()}\n")

    # 啟動 HTTP 伺服器
    host = "127.0.0.1"
    port = 9000
    url = f"http://{host}:{port}"

    print(f"⏳ 在埠口 {port} 啟動伺服器...")
    print(f"📍 訪問地址: {url}\n")

    try:
        # 使用 Python -m http.server
        # 這樣可以確保在正確的目錄中執行
        print("✅ 伺服器已啟動！")
        print("💡 提示: 按 Ctrl+C 停止伺服器\n")

        # 打開瀏覽器
        time.sleep(1)
        try:
            webbrowser.open(url)
            print("📱 已打開瀏覽器")
        except Exception as e:
            print(f"⚠️ 無法自動打開瀏覽器: {e}")
            print(f"📍 請手動訪問: {url}")

        # 執行 Flask 伺服器（支援圖表生成）
        # 使用 subprocess 確保在正確的目錄中執行
        subprocess.run([
            sys.executable, "app.py"
        ])

    except KeyboardInterrupt:
        print("\n\n⏹️  伺服器已停止")
        os.chdir(original_dir)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        os.chdir(original_dir)
        sys.exit(1)

if __name__ == "__main__":
    main()
