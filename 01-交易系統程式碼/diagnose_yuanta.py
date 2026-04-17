#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnose Yuanta API issues
"""
import sys
sys.path.insert(0, '.')

print("[DIAGNOSE] Yuanta API Issues")
print("=" * 60)

try:
    from brokers.yuanta_api import yuanta_login, register_events, query_stock_positions, fetch_positions
    from dotenv import load_dotenv
    import os
    import time

    load_dotenv()

    account = os.getenv('YUANTA_ACCOUNT', '')
    password = os.getenv('YUANTA_PASSWORD', '')
    env = os.getenv('YUANTA_ENV', 'PROD')

    print(f"[CONFIG]")
    print(f"  Account: {account}")
    print(f"  Password: {'*' * len(password) if password else 'NOT SET'}")
    print(f"  Environment: {env}")

    print(f"\n[STEP 1] Login...")
    api = yuanta_login()
    print(f"[OK] Login object created")

    print(f"\n[STEP 2] Register events...")
    register_events(api)
    print(f"[OK] Events registered")

    print(f"\n[STEP 3] Wait 20 seconds for login to settle...")
    for i in range(20):
        time.sleep(1)
        print(".", end="", flush=True)
    print()

    print(f"\n[STEP 4] Query stock positions (attempt 1)...")
    ok = query_stock_positions(api)
    print(f"[RESULT] ok={ok}")

    if not ok:
        print(f"[STEP 5] Retry after 10 seconds...")
        time.sleep(10)
        ok = query_stock_positions(api)
        print(f"[RESULT] ok={ok}")

    print(f"\n[STEP 6] Wait 15 seconds for response...")
    for i in range(15):
        time.sleep(1)
        print(".", end="", flush=True)
    print()

    print(f"\n[STEP 7] Fetch positions...")
    positions = fetch_positions(api)
    print(f"[RESULT] Got {len(positions)} positions")
    if positions:
        for pos in positions[:3]:
            print(f"  - {pos[:50]}")
    else:
        print(f"  (empty)")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
