from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sheets_utils import get_sheet


def _now_ts_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def append_sync_log(log_type: str, broker: str, count: int, status: str, note: str = "") -> None:
    """sync_logs columns: 時間 / 類型 / 券商 / 新增筆數 / 狀態 / 備註"""
    sheet = get_sheet("sync_logs")
    sheet.append_row([
        _now_ts_str(),
        log_type,
        broker,
        int(count),
        status,
        note,
    ], value_input_option="USER_ENTERED")


def append_row_by_header(tab_name: str, row: Dict[str, Any]) -> None:
    """Append row aligning to existing header order."""
    sheet = get_sheet(tab_name)
    header = sheet.row_values(1)
    ordered = [row.get(h, "") for h in header]
    sheet.append_row(ordered, value_input_option="USER_ENTERED")
