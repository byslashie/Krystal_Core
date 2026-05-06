"""
upload_yuanta_to_sheets.py
讀取 32-bit 進程存下的 yuanta_positions_snapshot.json，
用 64-bit Python 上傳到 Google Sheets broker_positions 分頁。

使用方式（64-bit Python）：
  python brokers/upload_yuanta_to_sheets.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# 載入 .env
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except Exception:
    pass

SNAPSHOT_PATH = PROJECT_ROOT / "data" / "yuanta_positions_snapshot.json"
BROKER_NAME = "元大"

# broker_positions 欄位順序（對應 Google Sheets header）
COLUMNS = [
    "timestamp", "broker", "symbol", "secType", "exchange", "currency",
    "position", "avgCost", "marketPrice",
    "marketValue", "unrealizedPNL",
    "sellable", "limitUp", "limitDown",
]


def _fingerprint(positions: list[dict], ts: str) -> str:
    """用 symbol + position + avgCost + currentPrice 做比對 key"""
    items = sorted(
        [
            {
                "symbol": str(p.get("symbol", "")),
                "position": round(float(p.get("position", 0) or 0), 8),
                "avgCost": round(float(p.get("avgCost", 0) or 0), 8),
                "currentPrice": round(float(p.get("currentPrice", 0) or 0), 2),
            }
            for p in positions
        ],
        key=lambda x: x["symbol"],
    )
    return json.dumps(items, sort_keys=True, separators=(",", ":"))


def _last_fingerprint(sheet) -> str | None:
    """讀取 broker_positions 最後一批元大資料的 fingerprint"""
    try:
        values = sheet.get_all_values()
        if len(values) < 2:
            return None

        header = values[0]
        idx = {h.strip(): i for i, h in enumerate(header)}

        def col(name):
            return idx.get(name)

        i_broker = col("券商")
        i_time   = col("時間")
        i_sym    = col("symbol")
        i_pos    = col("position")
        i_avg    = col("avgCost")
        i_price  = col("currentPrice")

        if i_broker is None or i_sym is None:
            return None

        # 找最後一筆元大時間戳
        last_ts = None
        for r in reversed(values[1:]):
            if len(r) > (i_broker or 0) and r[i_broker] == BROKER_NAME:
                last_ts = r[i_time] if i_time is not None else None
                break

        if not last_ts:
            return None

        last_positions = []
        for r in values[1:]:
            if len(r) <= (i_broker or 0):
                continue
            if r[i_broker] != BROKER_NAME or (i_time is not None and r[i_time] != last_ts):
                continue
            last_positions.append({
                "symbol":       r[i_sym] if i_sym is not None else "",
                "position":     r[i_pos] if i_pos is not None else 0,
                "avgCost":      r[i_avg] if i_avg is not None else 0,
                "currentPrice": r[i_price] if i_price is not None else 0,
            })

        if not last_positions:
            return None

        return _fingerprint(last_positions, last_ts)
    except Exception as e:
        print(f"[WARN] 讀取舊資料 fingerprint 失敗：{e}")
        return None


def _ensure_header(sheet) -> None:
    """若 broker_positions 第一列不符合新欄位，更新 header"""
    try:
        values = sheet.get_all_values()
        if values and values[0][:len(COLUMNS)] == COLUMNS:
            return  # header 已正確
        if not values:
            sheet.append_row(COLUMNS, value_input_option="USER_ENTERED")
            print("已建立 broker_positions header")
        else:
            # 只補缺少的欄位（避免覆蓋有資料的 sheet）
            current_header = values[0]
            missing = [c for c in COLUMNS if c not in current_header]
            if missing:
                print(f"[INFO] broker_positions 缺少欄位：{missing}（不自動修改 header，請手動新增）")
    except Exception as e:
        print(f"[WARN] 檢查 header 失敗：{e}")


def main() -> None:
    if not SNAPSHOT_PATH.exists():
        print(f"[ERROR] 找不到 snapshot 檔案：{SNAPSHOT_PATH}")
        sys.exit(1)

    data = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    positions = data.get("positions", [])
    ts = data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    if not positions:
        print("snapshot 無持股資料，不寫入")
        return

    print(f"讀取 snapshot：{ts}，{len(positions)} 檔持股")

    from sheets_utils import get_sheet

    sheet = get_sheet("broker_positions")
    if sheet is None:
        print("[ERROR] 無法取得 broker_positions 分頁")
        sys.exit(1)

    _ensure_header(sheet)

    # ── dedup：與上次寫入資料比對，完全一樣就跳過 ──
    current_fp = _fingerprint(positions, ts)
    last_fp    = _last_fingerprint(sheet)
    if last_fp is not None and current_fp == last_fp:
        print("ℹ️ 庫存與現價均未變動，跳過寫入")
        _log_sync(0)
        return

    # ── 計算帳戶彙總 ──
    total_market_value = sum(float(p.get("marketValue", 0) or 0) for p in positions)
    total_unrealized   = sum(float(p.get("unrealizedPnL", 0) or 0) for p in positions)

    rows = []
    for p in positions:
        rows.append([
            ts,
            BROKER_NAME,
            p.get("symbol", ""),
            p.get("secType", "STK"),
            p.get("exchange", "TWSE"),
            p.get("currency", "TWD"),
            p.get("position", 0),
            p.get("avgCost", 0),
            p.get("currentPrice", 0),
            p.get("marketValue", 0),
            p.get("unrealizedPnL", 0),
            p.get("sellable", p.get("position", 0)),
            p.get("limitUp", 0),
            p.get("limitDown", 0),
        ])

    # ── 先刪除現有的元大舊行，避免重複 ──
    _delete_broker_rows(sheet, BROKER_NAME)

    sheet.append_rows(rows, value_input_option="USER_ENTERED")
    print(f"已寫入 {len(rows)} 筆元大庫存至 broker_positions")
    print(f"帳戶總市值: {total_market_value:.0f} NTD  未實現損益: {total_unrealized:.0f} NTD")

    _log_sync(len(rows), total_market_value, total_unrealized)
    _notify_discord(positions, total_market_value, total_unrealized, ts)
    print("完成")


def _delete_broker_rows(sheet, broker_name: str) -> None:
    """刪除 broker_positions 中所有屬於 broker_name 的行，避免重複上傳。"""
    try:
        values = sheet.get_all_values()
        if len(values) < 2:
            return

        header = values[0]
        broker_col = None
        for candidate in ("broker", "券商"):
            if candidate in header:
                broker_col = header.index(candidate)
                break
        if broker_col is None:
            print("[WARN] 找不到 broker/券商 欄位，略過刪除舊行")
            return

        # 從後往前找，避免 row index 偏移
        rows_to_delete = [
            i + 2  # gspread row index 從 1 起，且 header 佔第 1 行
            for i, row in enumerate(values[1:])
            if len(row) > broker_col and row[broker_col] == broker_name
        ]

        if not rows_to_delete:
            return

        # 從後往前刪，避免 index 偏移
        for row_idx in reversed(rows_to_delete):
            sheet.delete_rows(row_idx)

        print(f"已刪除 {len(rows_to_delete)} 筆舊的「{broker_name}」庫存")
    except Exception as e:
        print(f"[WARN] 刪除舊行失敗：{e}")


def _notify_discord(positions: list, total_mv: float, total_pnl: float, ts: str) -> None:
    try:
        from modules.notifier import notify_yuanta_update
        notify_yuanta_update(positions, total_mv, total_pnl, ts)
    except Exception as e:
        print(f"[WARN] Discord 通知失敗：{e}")


def _log_sync(added: int, market_value: float = 0, unrealized: float = 0) -> None:
    try:
        from sheets_utils import get_sheet
        log_sheet = get_sheet("sync_logs")
        if log_sheet:
            log_sheet.append_row(
                [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "broker_positions_sync",
                    BROKER_NAME,
                    added,
                    "success" if added > 0 else "skipped",
                    f"總市值:{market_value:.0f} 未實現:{unrealized:.0f}" if added > 0 else "",
                ],
                value_input_option="USER_ENTERED",
            )
    except Exception as e:
        print(f"sync_logs 寫入失敗：{e}")


if __name__ == "__main__":
    main()
