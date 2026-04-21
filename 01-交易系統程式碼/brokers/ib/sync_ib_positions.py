# brokers/ib/sync_ib_positions.py
from __future__ import annotations

from datetime import datetime
from typing import Any, List
import json

from brokers.ib_api import get_open_positions
from sheets_utils import get_sheet

BROKER_NAME = "IBKR"


# =========================
# utils
# =========================
def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _norm_pos(p: dict) -> dict:
    """Normalize position for stable comparison."""
    return {
        "symbol": str(p.get("symbol", "")).strip(),
        "secType": str(p.get("secType", "")).strip(),
        "exchange": str(p.get("exchange", "")).strip(),
        "currency": str(p.get("currency", "")).strip(),
        "position": round(float(p.get("position", 0) or 0), 8),
        "avgCost": round(float(p.get("avgCost", 0) or 0), 8),
    }


def _fingerprint(positions: List[dict]) -> str:
    """Deterministic fingerprint of full inventory."""
    normed = [_norm_pos(p) for p in positions]
    normed.sort(key=lambda x: (x["symbol"], x["secType"], x["exchange"], x["currency"]))
    return json.dumps(normed, sort_keys=True, separators=(",", ":"))


# =========================
# read last snapshot
# =========================
def _read_last_snapshot(sheet) -> str | None:
    """
    Read the most recent snapshot (same timestamp) for this broker
    and rebuild fingerprint.
    """
    values = sheet.get_all_values()
    if len(values) < 2:
        return None

    header = values[0]
    rows = values[1:]

    idx = {h.strip(): i for i, h in enumerate(header)}

    def col(*names):
        for n in names:
            if n in idx:
                return idx[n]
        return None

    i_time = col("時間")
    i_broker = col("券商")
    i_symbol = col("symbol")
    i_sec = col("secType")
    i_ex = col("exchange")
    i_ccy = col("currency")
    i_pos = col("position")
    i_avg = col("avgCost")

    if i_time is None or i_broker is None or i_symbol is None:
        return None

    # 找最後一筆 timestamp（同 broker）
    last_ts = None
    for r in reversed(rows):
        if r[i_broker] == BROKER_NAME:
            last_ts = r[i_time]
            break

    if not last_ts:
        return None

    last_positions = []
    for r in rows:
        if r[i_broker] != BROKER_NAME:
            continue
        if r[i_time] != last_ts:
            continue

        last_positions.append(
            {
                "symbol": r[i_symbol],
                "secType": r[i_sec] if i_sec is not None else "",
                "exchange": r[i_ex] if i_ex is not None else "",
                "currency": r[i_ccy] if i_ccy is not None else "",
                "position": r[i_pos] if i_pos is not None else 0,
                "avgCost": r[i_avg] if i_avg is not None else 0,
            }
        )

    if not last_positions:
        return None

    return _fingerprint(last_positions)


# =========================
# main append logic
# =========================
def append_broker_positions(positions: List[dict]) -> int:
    sheet = get_sheet("broker_positions")
    if sheet is None:
        return 0

    current_fp = _fingerprint(positions)
    last_fp = _read_last_snapshot(sheet)

    # 🔒 核心：完全一樣就直接跳過
    if last_fp is not None and current_fp == last_fp:
        return 0

    ts = _now_ts()
    rows = []

    for p in positions:
        p = _norm_pos(p)
        rows.append(
            [
                ts,
                BROKER_NAME,
                p["symbol"],
                p["secType"],
                p["exchange"],
                p["currency"],
                p["position"],
                p["avgCost"],
            ]
        )

    # 一次寫入（同 timestamp）
    sheet.append_rows(rows, value_input_option="USER_ENTERED")
    return len(rows)


# =========================
# entry
# =========================
def main() -> None:
    positions = get_open_positions()
    added = append_broker_positions(positions)

    # optional log
    sheet = get_sheet("sync_logs")
    if sheet:
        sheet.append_row(
            [
                _now_ts(),
                "broker_positions_sync",
                BROKER_NAME,
                added,
                "success" if added > 0 else "skipped",
                "",
            ],
            value_input_option="USER_ENTERED",
        )


if __name__ == "__main__":
    main()