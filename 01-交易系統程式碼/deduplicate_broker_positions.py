"""
清理 broker_positions 中的重複行（同一時間戳的重複記錄）
"""
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sheets_utils import get_sheet, read_sheet_data_with_cache
import pandas as pd

def deduplicate_broker_positions():
    print("=" * 60)
    print("  清理 broker_positions 重複資料")
    print("=" * 60)

    # 讀取現有資料
    sheet = get_sheet("broker_positions")
    if sheet is None:
        print("[ERROR] 無法取得 broker_positions 分頁")
        sys.exit(1)

    try:
        vals = sheet.get_all_values()
    except Exception as e:
        print(f"[ERROR] 讀取失敗: {e}")
        sys.exit(1)

    if not vals or len(vals) < 2:
        print("[INFO] Sheet 為空或只有 Header，無需清理")
        return

    print(f"[INFO] 讀取 {len(vals)} 行（包含 Header）")

    header = vals[0]
    data_rows = vals[1:]

    # 建立去重查詢鍵（記錄時間 + 券商 + 代碼）
    seen = {}
    unique_rows = []
    duplicates_count = 0

    for row in data_rows:
        if not row or len(row) < 3:
            continue

        # 提取記錄時間、券商、代碼
        timestamp = row[0].strip() if len(row) > 0 else ""
        broker = row[1].strip() if len(row) > 1 else ""
        symbol = row[2].strip() if len(row) > 2 else ""

        # 組成去重鍵（只保留日期部分，時間精確到分鐘）
        if timestamp and len(timestamp) >= 16:
            # e.g., "2026-04-28 9:16:04" -> "2026-04-28 9:16"
            date_min = timestamp[:16]  # "2026-04-28 9:16"
        else:
            date_min = timestamp

        key = f"{date_min}|{broker}|{symbol}"

        if key not in seen:
            seen[key] = True
            unique_rows.append(row)
            print(f"  [OK] {broker} {symbol} {timestamp}")
        else:
            duplicates_count += 1
            print(f"  [DUP] {broker} {symbol} {timestamp}")

    print(f"\n[INFO] 發現重複 {duplicates_count} 筆")
    print(f"[INFO] 保留 {len(unique_rows)} 筆唯一記錄")

    if duplicates_count == 0:
        print("[OK] 無重複資料，保持原樣")
        return

    # 確認後清理
    confirm = input(f"\n確定刪除 {duplicates_count} 筆重複記錄？(y/n): ")
    if confirm.lower() != 'y':
        print("[取消] 未清理")
        return

    # 重新寫入
    print("\n[*] 正在重新寫入 broker_positions...")
    sheet.clear()
    sheet.insert_row(header, 1)

    if unique_rows:
        sheet.append_rows(unique_rows, value_input_option="RAW")

    print(f"[OK] 完成！保留 {len(unique_rows)} 筆資料")
    print("=" * 60)

if __name__ == "__main__":
    deduplicate_broker_positions()
