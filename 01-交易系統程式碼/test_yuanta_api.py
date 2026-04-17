#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Yuanta API connection (32-bit Python)
"""
import sys
sys.path.insert(0, '.')

print("[TEST] Yuanta API Connection")
print("=" * 60)

try:
    from brokers.yuanta_api import yuanta_login, fetch_positions, query_stock_positions, register_events
    from dotenv import load_dotenv
    import os
    import time

    load_dotenv()

    account = os.getenv('YUANTA_ACCOUNT', '')
    password = os.getenv('YUANTA_PASSWORD', '')

    print(f"[INFO] Account: {account}")
    print(f"[INFO] Password: {'*' * len(password) if password else 'NOT SET'}\n")

    print("[STEP 1] Login to Yuanta API...")
    try:
        api = yuanta_login()
        print(f"[OK] Login command sent, waiting for session establishment...")
        print(f"  Waiting 30 seconds for Yuanta server to confirm login...")
        for i in range(30):
            time.sleep(1)
            if (i + 1) % 10 == 0:
                print(f"  ... {i + 1}s elapsed")
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        raise

    print("\n[STEP 2] Register event listeners...")
    try:
        register_events(api)
        print(f"[OK] Events registered")
    except Exception as e:
        print(f"[ERROR] Registration failed: {e}")
        raise

    print("\n[STEP 3] Send position query (with retry)...")
    max_retries = 3
    positions = []

    for attempt in range(1, max_retries + 1):
        try:
            print(f"  Attempt {attempt}/{max_retries}...")
            ok = query_stock_positions(api)
            print(f"  api.RQ() returned: {ok}")

            if ok:
                print(f"  Waiting 15 seconds for async response...")
                time.sleep(15)
            else:
                print(f"  RQ send failed, will retry in 10s...")
                if attempt < max_retries:
                    time.sleep(10)
                continue

            # Try to fetch positions
            positions = fetch_positions(api)
            if positions:
                print(f"  Got {len(positions)} positions on attempt {attempt}")
                break
            else:
                print(f"  No positions received, will retry in 10s...")
                if attempt < max_retries:
                    time.sleep(10)

        except Exception as e:
            print(f"  Attempt {attempt} exception: {e}")
            if attempt == max_retries:
                raise
            time.sleep(10)

    print("\n[STEP 4] Display positions...")
    print(f"[OK] Got {len(positions)} positions total")
    for pos in positions:
        print(f"  - {pos}")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n[DONE]")
