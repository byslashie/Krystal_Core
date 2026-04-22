import sys
import re
from sheets_utils import get_sheet

def fix_daily_nav_account():
    print("--- 正在修復 daily_nav_account 數據與格式 ---")
    
    s = get_sheet('daily_nav_account')
    if not s:
        print("找不到 daily_nav_account")
        return

    all_values = s.get_all_values()
    if not all_values:
        print("表格是空的")
        return

    HEADER = ["date", "yuanta_mv_twd", "yuanta_pnl_twd", "ib_mv_usd", "ib_pnl_usd", "schwab_mv_usd", "schwab_pnl_usd", "total_mv_twd", "total_pnl_twd", "usd_twd_rate"]
    fixed_rows = []
    
    for row in all_values[1:]:
        if not row or not any(row): continue
        
        new_row = [""] * 10
        new_row[0] = row[0] # date
        
        # 輔助函式：清理貨幣字串轉為純數字
        def clean_val(v):
            if not v: return "0"
            # 移除 NT$, $, %, 逗號, 空格
            return re.sub(r'[^\d\.-]', '', str(v))

        is_old_format = False
        try:
            if len(row) >= 9:
                val3 = clean_val(row[3])
                if val3.isdigit() and int(val3) < 100:
                    is_old_format = True
        except:
            pass
            
        if is_old_format:
            print(f"修正舊格式紀錄: {row[0]}")
            new_row[1] = clean_val(row[1])
            new_row[2] = clean_val(row[2])
            new_row[3] = clean_val(row[4])
            new_row[4] = clean_val(row[5])
            new_row[5] = "0"
            new_row[6] = "0"
            new_row[7] = clean_val(row[7])
            new_row[8] = clean_val(row[8])
            new_row[9] = "32"
        else:
            for i in range(min(len(row), 10)):
                val = clean_val(row[i])
                # 如果是 total_mv_twd 欄位且被放大了一百倍
                if i == 7 and val:
                    try:
                        f_val = float(val)
                        if f_val > 50000000:
                             val = str(f_val / 100.0)
                    except:
                        pass
                new_row[i] = val

        fixed_rows.append(new_row)

    s.clear()
    s.append_row(HEADER)
    if fixed_rows:
        s.append_rows(fixed_rows, value_input_option="USER_ENTERED")
    
    print("--- 修復完成 ---")

if __name__ == "__main__":
    fix_daily_nav_account()
