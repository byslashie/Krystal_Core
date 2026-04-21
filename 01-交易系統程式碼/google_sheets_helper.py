# google_sheets_helper.py
import datetime
from typing import Dict, Any, List

import gspread
from oauth2client.service_account import ServiceAccountCredentials


# === 這兩個請改成你的設定 ===
SERVICE_ACCOUNT_FILE = "key/credentials.json"   # 你的 service account json 路徑
SPREADSHEET_ID = "1zpehl1bAZitFiQqMg7IcGWsPQxdhnQDhAeNtRvxzwn8"  # 「實盤交易管理」那份的 ID
# ============================

_SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_client() -> gspread.Client:
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_FILE, _SCOPE
    )
    return gspread.authorize(creds)


def _get_sheet(sheet_name: str) -> gspread.Worksheet:
    client = _get_client()
    sh = client.open_by_key(SPREADSHEET_ID)
    return sh.worksheet(sheet_name)


# -------- daily_nav --------
# 欄位：日期 | 策略 | NAV | 日報酬 | 累積報酬
def append_daily_nav_row(row: Dict[str, Any]) -> None:
    ws = _get_sheet("daily_nav")
    values = [
        row.get("日期"),
        row.get("策略"),
        row.get("NAV"),
        row.get("日報酬"),
        row.get("累積報酬"),
    ]
    ws.append_row(values, value_input_option="USER_ENTERED")


def get_last_nav(strategy: str) -> float | None:
    """
    從 daily_nav 讀取某策略最後一筆 NAV，沒有就回傳 None
    """
    ws = _get_sheet("daily_nav")
    records: List[Dict[str, Any]] = ws.get_all_records()

    filtered = [r for r in records if str(r.get("策略")) == strategy]
    if not filtered:
        return None

    last = filtered[-1]
    try:
        nav = float(str(last.get("NAV")).replace(",", ""))
        return nav
    except (TypeError, ValueError):
        return None


# -------- sync_logs --------
# 欄位：時間 | 類型 | 券商 | 新增筆數 | 狀態 | 備註
def append_sync_log(
    log_type: str,
    broker: str,
    count: int,
    status: str,
    note: str = "",
    ts: datetime.datetime | None = None,
) -> None:
    ws = _get_sheet("sync_logs")
    if ts is None:
        ts = datetime.datetime.now()
    row = [
        ts.strftime("%Y-%m-%d %H:%M:%S"),
        log_type,
        broker,
        count,
        status,
        note,
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")
