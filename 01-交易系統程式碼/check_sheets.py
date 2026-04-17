#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
檢查 Google Sheets 中的數據
"""
import sys
sys.path.insert(0, '.')

try:
    from sheets_utils import get_sheet

    print("[檢查] broker_positions 表...")
    sheet = get_sheet("broker_positions")

    if not sheet:
        print("[ERROR] 無法取得 broker_positions 表")
        sys.exit(1)

    print("[OK] 連接成功")

    # 取得所有數據
    values = sheet.get_all_values()
    print(f"\n[數據] 總共 {len(values)} 行")

    if len(values) > 0:
        # 顯示表頭
        print(f"\n[表頭]: {values[0]}")

        # 顯示最後 5 行
        print(f"\n[最後 5 行]:")
        for i, row in enumerate(values[-5:], start=len(values)-4):
            print(f"  行 {i}: {row}")

        # 統計元大和 IB 的數據
        yuanta_count = sum(1 for row in values[1:] if len(row) > 1 and row[1].lower() == 'yuanta')
        ib_count = sum(1 for row in values[1:] if len(row) > 1 and row[1].lower() == 'ib')

        print(f"\n[統計]:")
        print(f"  元大 (Yuanta): {yuanta_count} 筆")
        print(f"  IB: {ib_count} 筆")
    else:
        print("[WARNING] 表中無數據")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
