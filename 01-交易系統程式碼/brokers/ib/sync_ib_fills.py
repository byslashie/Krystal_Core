from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Set

from brokers.ib_api import get_executions
from sheets_utils import get_sheet


BROKER_NAME = "IBKR"
SHEET_FILLS = "broker_fills"
SHEET_LOGS = "sync_logs"
DEFAULT_DAYS = 360


def _now_ts_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _clean_header(header: List[str]) -> List[str]:
    return [str(c).replace("欄位：", "").strip() for c in header]


def append_sync_log(
    log_type: str,
    broker: str,
    count: int,
    status: str,
    note: str = "",
) -> None:
    sheet = get_sheet(SHEET_LOGS)
    if sheet is None:
        # Sheets disabled → silent skip
        return

    sheet.append_row(
        [_now_ts_str(), log_type, broker, int(count), status, note],
        value_input_option="USER_ENTERED",
    )


def _read_existing_exec_ids() -> Set[str]:
    sheet = get_sheet(SHEET_FILLS)
    if sheet is None:
        return set()

    records = sheet.get_all_records()
    if not records:
        return set()

    exec_ids: Set[str] = set()
    for r in records:
        v = r.get("execId") or r.get("execID") or r.get("ExecId") or r.get("ExecID")
        if v is not None:
            exec_ids.add(str(v).strip())
    return exec_ids


def _append_rows(rows: List[Dict[str, Any]]) -> int:
    if not rows:
        return 0

    sheet = get_sheet(SHEET_FILLS)
    if sheet is None:
        return 0

    header = _clean_header(sheet.row_values(1))

    required = {"execId", "time", "broker", "symbol", "side", "shares", "price", "source"}
    if not required.issubset(set(header)):
        raise RuntimeError(
            f"broker_fills header invalid, need {sorted(required)}, got {header}"
        )

    values: List[List[Any]] = []
    for row in rows:
        values.append([row.get(col, "") for col in header])

    sheet.append_rows(values, value_input_option="USER_ENTERED")
    return len(values)


def main(days: int = DEFAULT_DAYS) -> None:
    try:
        fills = get_executions(days=days)

        if not fills:
            append_sync_log(
                "broker_fills_sync",
                BROKER_NAME,
                0,
                "success",
                f"no_data | days={days}",
            )
            return

        existing = _read_existing_exec_ids()
        new_rows: List[Dict[str, Any]] = []

        for f in fills:
            exec_id = str(f.get("execId", "")).strip()
            if not exec_id or exec_id in existing:
                continue

            new_rows.append(
                {
                    "execId": exec_id,
                    "time": f.get("time", ""),
                    "broker": BROKER_NAME,
                    "symbol": f.get("symbol", ""),
                    "secType": f.get("secType", ""),
                    "exchange": f.get("exchange", ""),
                    "currency": f.get("currency", ""),
                    "side": f.get("side", ""),
                    "shares": f.get("shares", ""),
                    "price": f.get("price", ""),
                    "orderId": f.get("orderId", ""),
                    "permId": f.get("permId", ""),
                    "account": f.get("account", ""),
                    "source": "ib_insync",
                    "note": "",
                }
            )

        inserted = _append_rows(new_rows)

        append_sync_log(
            "broker_fills_sync",
            BROKER_NAME,
            inserted,
            "success" if inserted > 0 else "skipped",
            f"insert={inserted} | days={days}",
        )

    except Exception as e:
        try:
            append_sync_log(
                "broker_fills_sync",
                BROKER_NAME,
                0,
                "fail",
                f"error={repr(e)}",
            )
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
