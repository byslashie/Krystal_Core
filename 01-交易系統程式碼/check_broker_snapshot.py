#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
檢查 broker_snapshot 表中的數據
"""
import sys
sys.path.insert(0, '.')

try:
    from sheets_utils import get_sheet

    print("[檢查] broker_snapshot 表...")
    sheet = get_sheet("broker_snapshot")

    if not sheet:
        print("[ERROR] 無法取得 broker_snapshot 表")
        sys.exit(1)

    print("[OK] 連接成功")

    # 取得所有數據
    values = sheet.get_all_values()
    print(f"\n[數據] 總共 {len(values)} 行")

    if len(values) > 0:
        # 顯示表頭
        print(f"\n[表頭]: {values[0]}")

        # 顯示所有內容
        print(f"\n[所有數據]:")
        for i, row in enumerate(values[1:], start=2):
            print(f"  行 {i}: {row}")
    else:
        print("[WARNING] 表中無數據")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
