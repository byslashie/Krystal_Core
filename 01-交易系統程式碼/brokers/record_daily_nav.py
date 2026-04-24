"""
record_daily_nav.py
每日記錄投資組合市值到 Google Sheets daily_nav_account 分頁。
每天只保留一筆（upsert），每次執行都更新當日最新數據。

欄位：
  datetime | total_mv_twd | total_unrealized_twd | total_unrealized_pct
  daily_pnl_twd | ytd_pnl_twd | ytd_pct
  ib_mv_usd | ib_unrealized_usd | ib_unrealized_pct
  schwab_mv_usd | schwab_unrealized_usd | schwab_unrealized_pct
  yuanta_mv_twd | yuanta_unrealized_twd | yuanta_unrealized_pct
  usd_twd_rate
"""
from __future__ import annotations

import sys
import sqlite3
import subprocess
import json as _json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

NAV_COLUMNS = [
    "記錄時間",
    "總市值(台幣)", "總未實現損益(台幣)", "總未實現損益%",
    "每日損益(台幣)",
    "YTD損益(台幣)", "YTD%",
    "IB市值(USD)", "IB未實現損益(USD)", "IB未實現損益%",
    "Schwab市值(USD)", "Schwab未實現損益(USD)", "Schwab未實現損益%",
    "元大市值(台幣)", "元大未實現損益(台幣)", "元大未實現損益%",
    "美元匯率",
]

USD_TWD_RATE = 32.0


def _safe_float(v) -> float:
    try:
        if v is None or str(v).strip() in ('', 'nan', 'None'):
            return 0.0
        cleaned = str(v).replace(',', '').replace('USD', '').replace('NT$', '').replace('$', '').strip()
        return float(cleaned)
    except:
        return 0.0


def _get_broker_summary(df, broker_name):
    """從 DataFrame 中提取特定券商的市值和未實現損益加總"""
    aliases = [broker_name.lower()]
    if broker_name.lower() == 'yuanta':
        aliases.append('元大')
    if broker_name.lower() == 'ib':
        aliases.extend(['ibkr', 'interactive brokers'])

    mask = df['broker'].apply(
        lambda x: str(x).lower() if str(x) not in ('元大',) else x
    ).isin(aliases) | df['broker'].isin(aliases)
    subset = df[mask]

    if subset.empty:
        return 0.0, 0.0

    pnl_col = 'unrealizedPNL' if 'unrealizedPNL' in subset.columns else 'unrealizedPnL'
    mv  = sum(_safe_float(v) for v in subset['marketValue'])
    pnl = sum(_safe_float(v) for v in subset[pnl_col]) if pnl_col in subset.columns else 0.0
    return round(mv, 2), round(pnl, 2)


def main() -> None:
    now = datetime.now()
    today_str = now.date().isoformat()
    now_dt    = now.strftime('%Y-%m-%d %H:%M')

    print("=" * 55)
    print(f"  每日市值記錄  {now_dt}")
    print("=" * 55)

    from sheets_utils import get_sheet, read_sheet_data_with_cache
    import pandas as pd

    nav_sheet = get_sheet("daily_nav_account")
    if nav_sheet is None:
        print("[ERROR] 無法取得 daily_nav_account 分頁")
        sys.exit(1)

    try:
        vals = nav_sheet.get_all_values()
    except:
        vals = []

    # ── 1. 讀取 broker_positions ──────────────────────────────
    df = read_sheet_data_with_cache("broker_positions")
    if df is None or df.empty:
        print("[ERROR] 無法從 broker_positions 讀取數據")
        sys.exit(1)

    if '券商' in df.columns:
        df.rename(columns={'券商': 'broker'}, inplace=True)
    if 'unrealizedPNL' not in df.columns and 'unrealizedPnL' in df.columns:
        df.rename(columns={'unrealizedPnL': 'unrealizedPNL'}, inplace=True)

    y_mv, y_pnl = _get_broker_summary(df, 'yuanta')
    i_mv, i_pnl = _get_broker_summary(df, 'ib')
    s_mv, s_pnl = _get_broker_summary(df, 'schwab')

    # ── 2. Schwab PNL：從本地 DB 讀（API 同步後才準確）──────
    try:
        _db = PROJECT_ROOT / "dashboard_v8" / "broker_positions.db"
        if _db.exists():
            conn = sqlite3.connect(str(_db))
            c = conn.cursor()
            c.execute("SELECT SUM(unrealizedPnL), SUM(marketValue) FROM broker_positions WHERE lower(broker)='schwab'")
            row = c.fetchone()
            conn.close()
            if row and row[1]:
                s_pnl = round(float(row[0] or 0), 2)
                s_mv  = round(float(row[1] or s_mv), 2)
                print(f"[Schwab] DB PNL: ${s_pnl:,.2f}  MV: ${s_mv:,.2f}")
    except Exception as e:
        print(f"[Schwab] DB 查詢失敗: {e}")

    # ── 3. IB：用即時 NLV（含現金）────────────────────────────
    try:
        script = str(PROJECT_ROOT / 'query_ib_positions.py')
        result = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=20)
        ib_data = _json.loads(result.stdout.strip()) if result.stdout.strip() else {}
        if ib_data.get('status') == 'success':
            i_mv  = ib_data.get('net_liquidation_value', i_mv)
            i_pnl = ib_data.get('unrealized_pnl', i_pnl)
            print(f"[IB]     NLV: ${i_mv:,.2f}  PNL: ${i_pnl:,.2f}")
        else:
            print(f"[IB]     TWS 未連線，使用 Sheets: ${i_mv:,.2f}")
    except Exception as e:
        print(f"[IB]     查詢失敗: {e}")

    # ── 4. 計算合計 ────────────────────────────────────────────
    total_mv_twd          = round(y_mv + (i_mv + s_mv) * USD_TWD_RATE, 0)
    total_unrealized_twd  = round(y_pnl + (i_pnl + s_pnl) * USD_TWD_RATE, 0)
    yuanta_cost           = y_mv - y_pnl
    ib_cost_usd           = i_mv - i_pnl
    schwab_cost_usd       = s_mv - s_pnl
    total_cost_twd        = round(yuanta_cost + (ib_cost_usd + schwab_cost_usd) * USD_TWD_RATE, 0)
    total_unrealized_pct  = round(total_unrealized_twd / total_cost_twd * 100, 2) if total_cost_twd else 0.0
    ib_unrealized_pct     = round(i_pnl / (i_mv - i_pnl) * 100, 2) if (i_mv - i_pnl) else 0.0
    schwab_unrealized_pct = round(s_pnl / (s_mv - s_pnl) * 100, 2) if (s_mv - s_pnl) else 0.0
    yuanta_unrealized_pct = round(y_pnl / yuanta_cost * 100, 2) if yuanta_cost else 0.0

    # ── 5. 每日損益（今 - 昨市值）────────────────────────────
    daily_pnl_twd = 0.0
    try:
        prev_rows = [r for r in vals[1:] if r and r[0] and not r[0].startswith(today_str)]
        if prev_rows:
            hdr = vals[0]
            mv_idx = hdr.index('總市值(台幣)') if '總市值(台幣)' in hdr else 1
            prev_mv = _safe_float(prev_rows[-1][mv_idx])
            daily_pnl_twd = round(total_mv_twd - prev_mv, 0)
            print(f"[每日損益] {daily_pnl_twd:+,.0f} TWD  (昨 {prev_mv:,.0f} → 今 {total_mv_twd:,.0f})")
    except Exception as e:
        print(f"[每日損益] 計算失敗: {e}")

    # ── 6. YTD（今日市值 - 年初第一筆市值）──────────────────
    ytd_pnl_twd = 0.0
    ytd_pct     = 0.0
    try:
        year_start = f"{now.year}-01-01"
        year_rows  = [r for r in vals[1:] if r and r[0] and r[0] >= year_start]
        hdr = vals[0] if vals else NAV_COLUMNS
        mv_idx = hdr.index('總市值(台幣)') if '總市值(台幣)' in hdr else 1
        if year_rows:
            first_mv = _safe_float(year_rows[0][mv_idx])
            if first_mv:
                ytd_pnl_twd = round(total_mv_twd - first_mv, 0)
                ytd_pct     = round(ytd_pnl_twd / first_mv * 100, 2)
                print(f"[YTD]      {ytd_pnl_twd:+,.0f} TWD  ({ytd_pct:+.2f}%)  (年初 {first_mv:,.0f})")
        else:
            print("[YTD]      無年初基準資料（今日為年內第一筆）")
    except Exception as e:
        print(f"[YTD]      計算失敗: {e}")

    # ── 7. 組 row ──────────────────────────────────────────────
    row = [
        now_dt,
        total_mv_twd, total_unrealized_twd, total_unrealized_pct,
        daily_pnl_twd,
        ytd_pnl_twd, ytd_pct,
        i_mv, i_pnl, ib_unrealized_pct,
        s_mv, s_pnl, schwab_unrealized_pct,
        y_mv, y_pnl, yuanta_unrealized_pct,
        USD_TWD_RATE,
    ]

    # ── 8. 確保 Header ─────────────────────────────────────────
    if not vals or not vals[0] or vals[0][0] != '記錄時間' or len(vals[0]) < len(NAV_COLUMNS):
        nav_sheet.clear()
        nav_sheet.insert_row(NAV_COLUMNS, 1)
        vals = [NAV_COLUMNS]
        print("[Sheets] Header 已建立/更新")

    # ── 9. 刪除今日舊筆，寫入最新一筆 ─────────────────────────
    rows_to_delete = [
        idx + 2 for idx, r in enumerate(vals[1:])
        if r and r[0] and r[0].startswith(today_str)
    ]
    for r_idx in reversed(rows_to_delete):
        nav_sheet.delete_rows(r_idx)

    nav_sheet.append_row(row, value_input_option="RAW")

    print(f"\n{'='*55}")
    print(f"  [OK] 已寫入 {now_dt}")
    print(f"  元大:   {y_mv:>12,.0f} TWD  PNL: {y_pnl:>10,.0f}  ({yuanta_unrealized_pct:+.2f}%)")
    print(f"  IB:     {i_mv:>12,.2f} USD  PNL: {i_pnl:>10,.2f}  ({ib_unrealized_pct:+.2f}%)")
    print(f"  Schwab: {s_mv:>12,.2f} USD  PNL: {s_pnl:>10,.2f}  ({schwab_unrealized_pct:+.2f}%)")
    print(f"  {'─'*48}")
    print(f"  總市值: {total_mv_twd:>12,.0f} TWD")
    print(f"  總損益: {total_unrealized_twd:>12,.0f} TWD  ({total_unrealized_pct:+.2f}%)")
    print(f"  每日:   {daily_pnl_twd:>+12,.0f} TWD")
    print(f"  YTD:    {ytd_pnl_twd:>+12,.0f} TWD  ({ytd_pct:+.2f}%)")
    print(f"{'='*55}")

    # ── 10. 同步到 SQLite ──────────────────────────────────────
    try:
        DB_PATH = PROJECT_ROOT / "dashboard_v8" / "data" / "trading.db"
        if DB_PATH.exists():
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO equity_snapshots
                         (date, ib_mv_usd, schwab_mv_usd, yuanta_mv_twd, total_mv_twd, total_pnl_twd, usd_twd_rate)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (today_str, i_mv, s_mv, y_mv, total_mv_twd, total_unrealized_twd, USD_TWD_RATE))
            conn.commit()
            conn.close()
            print("[OK] SQLite equity_snapshots 已更新")
    except Exception as e:
        print(f"[WARN] SQLite 更新失敗: {e}")

    # ── 11. Discord 通知 ───────────────────────────────────────
    try:
        from modules.notifier import notify_daily_nav
        notify_daily_nav(today_str, y_mv, y_pnl, i_mv, i_pnl, s_mv, s_pnl, USD_TWD_RATE)
    except Exception as e:
        print(f"[WARN] Discord 通知失敗: {e}")


if __name__ == "__main__":
    main()
