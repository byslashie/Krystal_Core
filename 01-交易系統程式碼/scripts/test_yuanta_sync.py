#!/usr/bin/env python3
"""
🧪 Yuanta 庫存同步測試腳本
用於手動觸發和測試 Yuanta 持倉同步到 Google Sheets

使用方式:
    python scripts/test_yuanta_sync.py

注意：
    - 需要 32 位 Python 環境 (Yuanta DLL 依賴)
    - 確保 .env 已配置 YUANTA_ENV、YUANTA_ACCOUNT、Google Sheets 認證
"""

import sys
import os
from pathlib import Path

# 添加專案根目錄到 Python 路徑
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
import logging
from datetime import datetime

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加載環境變數
load_dotenv()

def main():
    """手動執行 Yuanta 同步"""
    print("\n" + "="*60)
    print("🧪 Yuanta 庫存同步測試")
    print("="*60)

    # 檢查環境配置
    print("\n📋 檢查環境配置...")
    env_vars = {
        'YUANTA_ENV': os.getenv('YUANTA_ENV'),
        'YUANTA_ACCOUNT': os.getenv('YUANTA_ACCOUNT'),
        'GOOGLE_SHEET_KEY': os.getenv('GOOGLE_SHEET_KEY'),
    }

    for key, value in env_vars.items():
        status = "✅" if value else "❌"
        print(f"  {status} {key}: {value if value else '未設定'}")

    if not all(env_vars.values()):
        print("\n❌ 環境變數未完全配置，請檢查 .env 文件")
        return False

    # 嘗試導入 Yuanta 同步模組
    print("\n🔗 導入 Yuanta 同步模組...")
    try:
        from brokers.sync_yuanta_positions import main as sync_yuanta_main
        print("  ✅ 模組導入成功")
    except ImportError as e:
        print(f"  ❌ 模組導入失敗: {e}")
        print(f"     提示: 確保使用 32 位 Python 環境 (Yuanta DLL 依賴)")
        return False
    except Exception as e:
        print(f"  ❌ 意外錯誤: {e}")
        return False

    # 執行同步
    print("\n⏳ 開始同步 Yuanta 庫存...")
    print(f"   時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    try:
        sync_yuanta_main()
        print("-" * 60)
        print("\n✅ 同步完成!")
        print(f"   結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n📊 檢查 Google Sheets:")
        print(f"   - 'broker_positions' 工作表已更新")
        print(f"   - 'sync_logs' 工作表已記錄同步日誌")
        return True
    except Exception as e:
        print("-" * 60)
        print(f"\n❌ 同步失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
