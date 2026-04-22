"""
record_daily_nav.py
每日記錄投資組合日終市值到 Google Sheets daily_nav 分頁。

資料來源：
  - 從 Google Sheets 的 broker_positions 分頁讀取最新持倉，按券商歸類計算。

daily_nav 欄位：
  date | yuanta_mv_twd | yuanta_pnl_twd | ib_mv_usd | ib_pnl_usd | schwab_mv_usd | schwab_pnl_usd | total_mv_twd | total_pnl_twd | usd_twd_rate
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

NAV_COLUMNS = [
    "date",
    "yuanta_mv_twd", "yuanta_pnl_twd",
    "ib_mv_usd", "ib_pnl_usd",
    "schwab_mv_usd", "schwab_pnl_usd",
    "total_mv_twd", "total_pnl_twd",
    "usd_twd_rate"
]

USD_TWD_RATE = 32.0

def _get_broker_summary(df, broker_name):
    """從 DataFrame 中提取特定券商的彙總數據"""
    # 支援多種券商名稱寫法
    aliases = [broker_name.lower()]
    if broker_name.lower() == 'yuanta': aliases.append('元大')
    if broker_name.lower() == 'ib': aliases.extend(['ibkr', 'interactive brokers'])
    
    subset = df[df['broker'].str.lower().isin(aliases)]
    if subset.empty:
        return 0.0, 0.0, 0
    
    def safe_float(v):
        try: return float(v) if v and str(v) != 'nan' else 0.0
        except: return 0.0

    mv  = sum(safe_float(v) for v in subset['marketValue'])
    pnl = sum(safe_float(v) for v in subset['unrealizedPnL'])
    return round(mv, 2), round(pnl, 2), len(subset)

def main() -> None:
    print("=" * 50)
    print(f"  每日市值記錄 (含 Schwab)  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    today_str = date.today().isoformat()

    from sheets_utils import get_sheet, read_sheet_data_with_cache
    import pandas as pd

    nav_sheet = get_sheet("daily_nav_account")
    if nav_sheet is None:
        print("[ERROR] 無法取得 daily_nav 分頁")
        sys.exit(1)

    # 檢查今日是否已有記錄 (簡單比對第一欄)
    try:
        vals = nav_sheet.get_all_values()
        if len(vals) > 1 and any(r[0] == today_str for r in vals[1:]):
            print(f"ℹ️ {today_str} 已有記錄，跳過寫入")
            # return # 測試期間先不跳過，或者允許覆蓋
    except: pass

    # 讀取所有持倉
    df = read_sheet_data_with_cache("broker_positions")
    if df is None or df.empty:
        print("[ERROR] 無法從 broker_positions 讀取數據")
        sys.exit(1)

    # 標準化欄位名
    if '券商' in df.columns: df.rename(columns={'券商': 'broker'}, inplace=True)
    if 'marketPrice' in df.columns and 'currentPrice' not in df.columns: df.rename(columns={'marketPrice': 'currentPrice'}, inplace=True)
    if 'unrealizedPNL' in df.columns: df.rename(columns={'unrealizedPNL': 'unrealizedPnL'}, inplace=True)

    y_mv, y_pnl, y_cnt = _get_broker_summary(df, 'yuanta')
    i_mv, i_pnl, i_cnt = _get_broker_summary(df, 'ib')
    s_mv, s_pnl, s_cnt = _get_broker_summary(df, 'schwab')

    total_mv_twd  = round(y_mv + (i_mv + s_mv) * USD_TWD_RATE, 0)
    total_pnl_twd = round(y_pnl + (i_pnl + s_pnl) * USD_TWD_RATE, 0)

    row = [
        today_str,
        y_mv, y_pnl,
        i_mv, i_pnl,
        s_mv, s_pnl,
        total_mv_twd, total_pnl_twd,
        USD_TWD_RATE
    ]

    # 確保 Header
    if not vals or not vals[0] or vals[0][0] != "date":
        nav_sheet.insert_row(NAV_COLUMNS, 1)
        print("已建立 daily_nav Header")

    nav_sheet.append_row(row, value_input_option="USER_ENTERED")
    
    print(f"\n[OK] 已寫入 {today_str}：")
    print(f"  元大:   {y_mv:12.0f} TWD (PNL: {y_pnl:10.0f})")
    print(f"  IB:     {i_mv:12.2f} USD (PNL: {i_pnl:10.2f})")
    print(f"  Schwab: {s_mv:12.2f} USD (PNL: {s_pnl:10.2f})")
    print(f"  --------------------------------------------------")
    print(f"  總計:   {total_mv_twd:12.0f} TWD (PNL: {total_pnl_twd:10.0f})")
    
    # 同步到 SQLite 供 Dashboard 圖表使用
    try:
        import sqlite3
        DB_PATH = PROJECT_ROOT / "dashboard_v8" / "data" / "trading.db"
        if DB_PATH.exists():
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO equity_snapshots 
                         (date, ib_mv_usd, schwab_mv_usd, yuanta_mv_twd, total_mv_twd, total_pnl_twd, usd_twd_rate)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                      (today_str, i_mv, s_mv, y_mv, total_mv_twd, total_pnl_twd, USD_TWD_RATE))
            conn.commit()
            conn.close()
            print("[OK] 已同步至本地 SQLite (equity_snapshots)")
    except Exception as e:
        print(f"[WARN] 同步 SQLite 失敗: {e}")

    # Discord 通知
    try:
        from modules.notifier import notify_daily_nav
        notify_daily_nav(today_str, y_mv, y_pnl, i_mv + s_mv, i_pnl + s_pnl)
    except Exception as e:
        print(f"[WARN] Discord 通知失敗: {e}")

if __name__ == "__main__":
    main()
