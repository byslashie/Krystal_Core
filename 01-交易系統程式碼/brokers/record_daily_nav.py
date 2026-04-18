"""
record_daily_nav.py
每日收盤後（建議 13:40）記錄投資組合日終市值到 Google Sheets daily_nav 分頁。

資料來源：
  - 元大：data/yuanta_positions_snapshot.json（由 sync_yuanta_positions.py 產生）
  - IB  ：broker_positions 分頁最新一批 IB 資料

daily_nav 欄位：
  date | yuanta_market_value | yuanta_unrealized_pnl | yuanta_positions_count
       | ib_market_value     | ib_unrealized_pnl     | ib_positions_count
       | total_market_value  | total_unrealized_pnl

使用方式（64-bit Python）：
  python brokers/record_daily_nav.py
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

SNAPSHOT_PATH = PROJECT_ROOT / "data" / "yuanta_positions_snapshot.json"

NAV_COLUMNS = [
    "date",
    "yuanta_market_value",
    "yuanta_unrealized_pnl",
    "yuanta_positions_count",
    "ib_market_value",
    "ib_unrealized_pnl",
    "ib_positions_count",
    "total_market_value",
    "total_unrealized_pnl",
]


# ──────────────────────────────────────────────
# 讀取元大快照
# ──────────────────────────────────────────────

def _read_yuanta_snapshot() -> dict:
    if not SNAPSHOT_PATH.exists():
        print(f"[WARN] 找不到元大 snapshot：{SNAPSHOT_PATH}")
        return {}
    data = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    positions = data.get("positions", [])
    mv   = float(data.get("totalMarketValue", 0) or 0)
    pnl  = float(data.get("totalUnrealizedPnL", 0) or 0)
    # 若 snapshot 沒有彙總欄位，從持倉計算
    if mv == 0 and positions:
        mv  = sum(float(p.get("marketValue", 0) or 0) for p in positions)
        pnl = sum(float(p.get("unrealizedPnL", 0) or 0) for p in positions)
    ts = data.get("timestamp", "")
    print(f"元大 snapshot ({ts})：市值={mv:.0f}  未實現={pnl:.0f}  持倉={len(positions)} 檔")
    return {"market_value": mv, "unrealized_pnl": pnl, "count": len(positions)}


# ──────────────────────────────────────────────
# 讀取 IB（從 broker_positions 分頁最新資料）
# ──────────────────────────────────────────────

def _read_ib_from_sheets(sheet) -> dict:
    try:
        values: list[list[str]] = sheet.get_all_values()
        if len(values) < 2:
            return {}
        header: list[str] = values[0]
        idx = {h.strip(): i for i, h in enumerate(header)}

        def col(name: str) -> int | None:
            return idx.get(name)

        i_broker = col("券商")
        i_time   = col("時間")
        i_mv     = col("marketValue")
        i_pnl    = col("unrealizedPnL")

        if i_broker is None:
            return {}

        # 找最後一筆 IB 的時間戳
        last_ts = None
        for r in reversed(values[1:]):
            if len(r) > i_broker and r[i_broker] not in ("元大", ""):
                last_ts = r[i_time] if i_time is not None else None
                break

        if not last_ts:
            return {}

        ib_rows = [r for r in values[1:]
                   if len(r) > i_broker
                   and r[i_broker] not in ("元大", "")
                   and (i_time is None or r[i_time] == last_ts)]

        mv  = sum(float(r[i_mv]  or 0) for r in ib_rows if i_mv  is not None and len(r) > i_mv)
        pnl = sum(float(r[i_pnl] or 0) for r in ib_rows if i_pnl is not None and len(r) > i_pnl)
        print(f"IB ({last_ts})：市值={mv:.0f}  未實現={pnl:.0f}  持倉={len(ib_rows)} 檔")
        return {"market_value": mv, "unrealized_pnl": pnl, "count": len(ib_rows)}
    except Exception as e:
        print(f"[WARN] 讀取 IB 資料失敗：{e}")
        return {}


# ──────────────────────────────────────────────
# 確保 daily_nav header
# ──────────────────────────────────────────────

def _ensure_header(nav_sheet) -> None:
    try:
        values: list[list[str]] = nav_sheet.get_all_values()
        if not values:
            nav_sheet.append_row(NAV_COLUMNS, value_input_option="USER_ENTERED")
            print("已建立 portfolio_daily header")
        elif values[0][:len(NAV_COLUMNS)] != NAV_COLUMNS:
            missing = [c for c in NAV_COLUMNS if c not in values[0]]
            if missing:
                print(f"[INFO] portfolio_daily 缺少欄位：{missing}（請手動補齊 header）")
    except Exception as e:
        print(f"[WARN] 確認 header 失敗：{e}")


# ──────────────────────────────────────────────
# 檢查今日是否已有記錄
# ──────────────────────────────────────────────

def _today_exists(nav_sheet, today_str: str) -> bool:
    try:
        values: list[list[str]] = nav_sheet.get_all_values()
        if len(values) < 2:
            return False
        header: list[str] = values[0]
        i_date = next((i for i, h in enumerate(header) if h.strip() == "date"), None)
        if i_date is None:
            return False
        return any(r[i_date] == today_str for r in values[1:] if len(r) > i_date)
    except Exception as e:
        print(f"[WARN] 檢查重複日期失敗：{e}")
        return False


# ──────────────────────────────────────────────
# main
# ──────────────────────────────────────────────

def main() -> None:
    print("=" * 50)
    print(f"  每日市值記錄  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    today_str = date.today().isoformat()   # e.g. "2026-03-27"

    from sheets_utils import get_sheet

    nav_sheet = get_sheet("portfolio_daily")
    if nav_sheet is None:
        print("[ERROR] 無法取得 portfolio_daily 分頁（請先在 Google Sheets 建立此分頁）")
        sys.exit(1)
    assert nav_sheet is not None  # help type checker

    _ensure_header(nav_sheet)

    if _today_exists(nav_sheet, today_str):
        print(f"ℹ️  {today_str} 已有記錄，跳過寫入")
        return

    # 讀取各券商資料
    yuanta = _read_yuanta_snapshot()
    bp_sheet = get_sheet("broker_positions")
    ib = _read_ib_from_sheets(bp_sheet) if bp_sheet else {}

    y_mv  = yuanta.get("market_value", 0)
    y_pnl = yuanta.get("unrealized_pnl", 0)
    y_cnt = yuanta.get("count", 0)
    i_mv  = ib.get("market_value", 0)
    i_pnl = ib.get("unrealized_pnl", 0)
    i_cnt = ib.get("count", 0)

    row = [
        today_str,
        round(y_mv,  2),
        round(y_pnl, 2),
        y_cnt,
        round(i_mv,  2),
        round(i_pnl, 2),
        i_cnt,
        round(y_mv + i_mv,   2),
        round(y_pnl + i_pnl, 2),
    ]

    nav_sheet.append_row(row, value_input_option="USER_ENTERED")
    print(f"\n已寫入 {today_str}：")
    print(f"  元大  市值={y_mv:.0f}  未實現={y_pnl:.0f}  {y_cnt}檔")
    print(f"  IB    市值={i_mv:.0f}  未實現={i_pnl:.0f}  {i_cnt}檔")
    print(f"  合計  市值={y_mv+i_mv:.0f}  未實現={y_pnl+i_pnl:.0f}")
    print("完成")

    try:
        from modules.notifier import notify_daily_nav
        notify_daily_nav(today_str, y_mv, y_pnl, i_mv, i_pnl)
    except Exception as e:
        print(f"[notifier] {e}")


if __name__ == "__main__":
    main()
