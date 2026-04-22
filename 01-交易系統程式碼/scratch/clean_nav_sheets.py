import sys
import pandas as pd
from sheets_utils import get_sheet

def clean_sheets():
    print("--- 正在清理 Google Sheets ---")
    
    s_acc = get_sheet('daily_nav_account')
    s_str = get_sheet('daily_nav_strategy')
    
    if not s_acc:
        print("找不到 daily_nav_account")
        return

    all_rows = s_acc.get_all_values()
    if not all_rows:
        print("daily_nav_account 是空的")
        return

    # 定義帳戶層級的 Header
    ACC_HEADER = [
        "date", "yuanta_mv_twd", "yuanta_pnl_twd", "ib_mv_usd", "ib_pnl_usd", 
        "schwab_mv_usd", "schwab_pnl_usd", "total_mv_twd", "total_pnl_twd", "usd_twd_rate"
    ]
    
    # 定義策略層級的 Header (從截圖中提取)
    STR_HEADER = [
        "日期", "策略", "幣別", "起始資金", "value", "NAV", "日報酬", "累積報酬", 
        "realized_pnl", "unrealized_pnl", "cash", "position_value", "broker", "account", "mode", "source", "備註", "更新時間"
    ]

    acc_data = []
    str_data = []

    for row in all_rows:
        if not row or not any(row): continue
        
        # 判定是否為 Header 行
        first_cell = row[0].strip()
        if first_cell in ("date", "日期"):
            continue
            
        # 判定是否為策略行 (第二欄通常是策略名稱，非數字)
        try:
            # 嘗試把第二欄轉為數字，如果失敗則可能是策略名稱
            float(row[1])
            # 如果成功，且第一欄看起來像日期，則是帳戶行
            # 但要注意 2026-03-27 那幾行格式跑掉了
            if len(row) >= 10 and "-" in row[0]:
                # 這是帳戶行
                acc_data.append(row[:len(ACC_HEADER)])
            else:
                # 可能是舊格式或垃圾資料
                pass
        except:
            # 轉換失敗 -> 第二欄是文字 -> 策略行
            if len(row) >= 5:
                str_data.append(row[:len(STR_HEADER)])

    # 1. 重新寫入 daily_nav_account
    print(f"寫入 daily_nav_account ({len(acc_data)} 筆)...")
    s_acc.clear()
    s_acc.append_row(ACC_HEADER)
    if acc_data:
        s_acc.append_rows(acc_data, value_input_option="USER_ENTERED")

    # 2. 重新寫入 daily_nav_strategy
    print(f"寫入 daily_nav_strategy ({len(str_data)} 筆)...")
    s_str.clear()
    s_str.append_row(STR_HEADER)
    if str_data:
        s_str.append_rows(str_data, value_input_option="USER_ENTERED")

    print("--- 清理完成 ---")

if __name__ == "__main__":
    clean_sheets()
