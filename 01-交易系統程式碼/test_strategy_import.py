#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test strategy import API
"""
import requests
import json
from pathlib import Path
import sys
import io

# 強制 UTF-8 輸出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 服務器地址
API_URL = "http://localhost:9000"

def test_strategy_import():
    """Test strategy import API"""

    # CSV 文件路徑
    csv_path = Path("G:\\我的雲端硬碟\\Krystal_完整系統\\02-策略知識庫\\Strategies\\260401_台股強勢股加碼-兩次_UTF8.csv")

    if not csv_path.exists():
        print(f"ERROR: File not found: {csv_path}")
        return

    print("=" * 80)
    print("TEST: Strategy Import API")
    print("=" * 80)
    print(f"File: {csv_path.name}")
    print(f"Size: {csv_path.stat().st_size:,} bytes")
    print()

    # Upload file
    try:
        with open(csv_path, 'rb') as f:
            files = {'file': (csv_path.name, f, 'text/csv')}

            print("Uploading...")
            response = requests.post(
                f"{API_URL}/api/strategy/import",
                files=files,
                timeout=30
            )

        print(f"HTTP {response.status_code}")

        # Parse response
        data = response.json()

        if response.status_code == 200 and data.get('status') == 'success':
            print("SUCCESS\n")

            preview = data.get('preview', {})
            print("Statistics:")
            print(f"  Total Trades: {preview.get('total_trades', 0)}")
            print(f"  Total Profit: {preview.get('total_profit', 0):,.2f}")
            print(f"  Win Rate: {preview.get('win_rate', 0):.2f}%")
            print(f"  Avg Return: {preview.get('avg_return', 0):.4f}%")
            print(f"  Total Return: {preview.get('total_return', 0):.2f}%")
            print(f"  Winning Trades: {preview.get('winning_trades', 0)}")

            # Show sample trades
            print("\nSample Trades (first 3):")
            for i, trade in enumerate(preview.get('sample_trades', [])[:3]):
                print(f"  {i+1}. {trade.get('name')} ({trade.get('symbol')})")
                print(f"     Entry: {trade.get('entry_price'):.2f} -> Exit: {trade.get('exit_price'):.2f}")
                print(f"     Qty: {trade.get('qty')} | Profit: {trade.get('profit'):,.0f} | Return: {trade.get('return_rate')*100:.4f}%")
        else:
            print(f"ERROR: {data.get('message', 'Unknown error')}")
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot connect to {API_URL}")
        print("Make sure Flask server is running")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_strategy_import()
