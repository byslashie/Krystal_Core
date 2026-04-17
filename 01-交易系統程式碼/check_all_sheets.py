#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
列出 Google Sheets 中的所有工作表
"""
import sys
sys.path.insert(0, '.')

try:
    from sheets_utils import get_workbook

    print("[檢查] Google Sheets 中的所有表...")

    wb = get_workbook()

    if wb is None:
        print("[ERROR] 無法取得試算表")
        sys.exit(1)

    sheets = wb.worksheets()
    print(f"\n[找到] {len(sheets)} 個表:")
    for i, sheet in enumerate(sheets, 1):
        print(f"  {i}. {sheet.title}")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
