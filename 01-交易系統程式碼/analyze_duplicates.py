#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析重複數據
"""
import sys
sys.path.insert(0, '.')

from sheets_utils import get_sheet
from collections import defaultdict

# 檢查 broker_positions 中的重複 IB 數據
print("[分析] broker_positions 中的 IB 重複數據...")
sheet = get_sheet("broker_positions")
values = sheet.get_all_values()

ib_data = defaultdict(list)
for i, row in enumerate(values[1:], start=2):
    if len(row) > 1 and row[1].upper() == 'IB':
        ts = row[0]  # 時間戳
        ib_data[ts].append(i)  # 記錄行號

print(f"\n[找到] {len(ib_data)} 個不同的時間戳")
duplicates = {ts: rows for ts, rows in ib_data.items() if len(rows) > 1}

if duplicates:
    print(f"\n[重複數據] {len(duplicates)} 個時間戳有重複：")
    for ts, rows in sorted(duplicates.items()):
        print(f"  {ts}: {len(rows)} 筆 (行 {rows})")
        # 顯示詳情
        for row_idx in rows[:2]:  # 只顯示前 2 筆
            row = values[row_idx - 1]
            print(f"    - {row[:5]}")
else:
    print("\n[OK] 沒有重複的 IB 數據")

# 檢查 broker_snapshot 中的重複 IBKR 數據
print("\n" + "="*60)
print("[分析] broker_snapshot 中的 IBKR 重複數據...")
sheet2 = get_sheet("broker_snapshot")
values2 = sheet2.get_all_values()

ibkr_data = defaultdict(list)
for i, row in enumerate(values2[1:], start=2):
    if len(row) > 1 and row[1].upper() == 'IBKR':
        ts = row[0]  # 時間戳
        ibkr_data[ts].append(i)  # 記錄行號

print(f"\n[找到] {len(ibkr_data)} 個不同的時間戳")
duplicates2 = {ts: rows for ts, rows in ibkr_data.items() if len(rows) > 1}

if duplicates2:
    print(f"\n[重複數據] {len(duplicates2)} 個時間戳有重複：")
    for ts, rows in sorted(duplicates2.items()):
        print(f"  {ts}: {len(rows)} 筆 (行 {rows})")
else:
    print("\n[OK] 沒有重複的 IBKR 數據")

# 統計摘要
print("\n" + "="*60)
print("[摘要]:")
print(f"  broker_positions IB 重複: {len(duplicates)}")
print(f"  broker_snapshot IBKR 重複: {len(duplicates2)}")
