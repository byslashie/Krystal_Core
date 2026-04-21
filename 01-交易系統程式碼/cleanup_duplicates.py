#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理 broker_positions 中的重複 IB 數據
"""
import sys
sys.path.insert(0, '.')

from sheets_utils import get_sheet

print("[CLEAN] broker_positions duplicate IB data...")
sheet = get_sheet("broker_positions")

if not sheet:
    print("[ERROR] Cannot get broker_positions sheet")
    sys.exit(1)

# Get all data
values = sheet.get_all_values()
print(f"\n[ORIGINAL] {len(values)} rows")

# Identify duplicates
# Keep first occurrence of each IB timestamp, skip later ones
keep_rows = []
seen_ib_ts = set()

for i, row in enumerate(values):
    if i == 0:  # Keep header
        keep_rows.append(row)
        continue

    if len(row) < 2:
        keep_rows.append(row)
        continue

    ts = row[0]
    broker = row[1]

    # For IB data, check if timestamp already seen
    if broker.upper() == 'IB':
        key = (ts, broker.upper())
        if key in seen_ib_ts:
            print(f"  SKIP duplicate: row {i+1}")
            continue  # Skip this row
        seen_ib_ts.add(key)

    keep_rows.append(row)

print(f"\n[CLEANED] {len(keep_rows)} rows (removed {len(values) - len(keep_rows)} duplicates)")

# Clear and rewrite
print(f"\n[CLEARING] original sheet...")
sheet.clear()

print(f"[WRITING] {len(keep_rows)} rows...")
if keep_rows:
    sheet.batch_update([{
        'range': f'A1:I{len(keep_rows)}',
        'values': keep_rows
    }])

print(f"\n[DONE] Cleanup completed!")
