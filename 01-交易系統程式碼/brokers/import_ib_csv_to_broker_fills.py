# brokers/import_ib_csv_to_broker_fills.py
# Usage:
#   python -m brokers.import_ib_csv_to_broker_fills brokers/ib_trades_2025-11-13.csv

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sheets_utils import get_sheet  # 你專案裡已經在用這個

BROKER_NAME = "IBKR"
LOG_TYPE = "broker_fills_csv_import"
DEFAULT_CURRENCY = "USD"

# 你的 CSV 是「轉賬歷史」這個 section
IB_SECTION_CANDIDATES = {
    "轉賬歷史", "交易歷史", "交易", "成交",
    "Trades", "Trade History", "Transactions", "Activity",
}


def append_sync_log(log_type: str, broker: str, count: int, status: str, note: str = "") -> None:
    """
    Append one row into Google Sheets `sync_logs`.

    sync_logs 表頭必須是（文字需完全一致）：
      - 時間
      - 類型
      - 券商
      - 新增筆數
      - 狀態
      - 備註
    """
    ws = get_sheet("sync_logs")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = {
        "時間": now_str,
        "類型": log_type,
        "券商": broker,
        "新增筆數": int(count),
        "狀態": status,
        "備註": note,
    }

    header = [h.strip() for h in ws.row_values(1) if h and str(h).strip()]
    if not header:
        raise RuntimeError("sync_logs 工作表第一列必須是表頭")

    values = [row.get(col, "") for col in header]
    ws.append_row(values, value_input_option="USER_ENTERED")


def _to_float(x: object) -> float:
    if x is None:
        return 0.0
    s = str(x).strip()
    if s in ("", "-", "--"):
        return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


def _to_str(x: object) -> str:
    return "" if x is None else str(x).strip()


def _normalize_time(date_str: str) -> str:
    """Normalize to 'YYYY-MM-DD HH:MM:SS' if possible."""
    s = _to_str(date_str)
    if not s:
        return ""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d 00:00:00")
    except Exception:
        return s


def _make_stable_id(date: str, symbol: str, tx_type: str, qty: float, price: float, net_amount: float) -> str:
    """IB statement CSV 沒有 execId，用內容組合出穩定唯一鍵。"""
    def safe(s: str) -> str:
        s = s.replace(" ", "_").replace("/", "_").replace("\\", "_")
        s = s.replace(".", "p").replace("-", "m")
        return s

    key = f"{date}|{symbol}|{tx_type}|{qty:.6f}|{price:.6f}|{net_amount:.6f}"
    return ("IBCSV_" + safe(key))[:180]


def parse_ib_statement_csv(csv_path: Path) -> List[Dict[str, str]]:
    """
    Supports:
    1) Statement style: <Section>,Header/Data,<...>
    2) Plain CSV table: first row is header
    """
    records: List[Dict[str, str]] = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        return records

    is_statement_style = len(rows[0]) >= 2 and rows[0][1].strip() in {"Header", "Data"}

    if is_statement_style:
        header: Optional[List[str]] = None
        active_section: Optional[str] = None

        for row in rows:
            if not row or len(row) < 2:
                continue

            section, kind = row[0].strip(), row[1].strip()

            if kind == "Header" and section in IB_SECTION_CANDIDATES:
                active_section = section
                header = [c.strip() for c in row[2:]]
                continue

            if kind == "Data" and header and active_section and section == active_section:
                data = [c.strip() for c in row[2:]]
                if len(data) < len(header):
                    data = data + [""] * (len(header) - len(data))
                records.append(dict(zip(header, data)))

        return records

    # Plain table CSV
    header = [c.strip() for c in rows[0]]
    for row in rows[1:]:
        if not row or all(not str(c).strip() for c in row):
            continue
        data = [str(c).strip() for c in row]
        if len(data) < len(header):
            data = data + [""] * (len(header) - len(data))
        records.append(dict(zip(header, data)))

    return records


def _get_any(rec: Dict[str, str], keys: List[str]) -> str:
    for k in keys:
        if k in rec and str(rec.get(k)).strip() != "":
            return str(rec.get(k)).strip()
    return ""


def map_record_to_broker_fills_row(rec: Dict[str, str]) -> Dict[str, object]:
    # Date/Time
    date = _get_any(rec, ["日期", "Date/Time", "DateTime", "Date Time", "Date", "TradeDate", "Report Date", "Time"])
    time_str = _normalize_time(date)

    # Symbol
    symbol = _get_any(rec, ["代碼", "Symbol", "Underlying", "Ticker"])
    if symbol in ("", "-"):
        symbol = "CASH"

    # Side (Buy/Sell/Deposit/Withdraw)
    tx = _get_any(rec, ["交易類型", "Transaction Type", "Type"])
    side_raw = _get_any(rec, ["方向", "Side", "Buy/Sell", "Action"])

    side_map = {
        "買": "BUY",
        "賣": "SELL",
        "Buy": "BUY",
        "BUY": "BUY",
        "Sell": "SELL",
        "SELL": "SELL",
        "存款": "DEPOSIT",
        "出金": "WITHDRAW",
        "Deposit": "DEPOSIT",
        "Withdrawal": "WITHDRAW",
        "Withdraw": "WITHDRAW",
    }

    side = side_map.get(side_raw, side_raw) if side_raw else side_map.get(tx, tx)

    # Qty / Price
    shares = _to_float(_get_any(rec, ["交易量", "Quantity", "Qty", "Shares"]))
    price = _to_float(_get_any(rec, ["價格", "Price", "Trade Price"]))

    # Amount / Fee / Net
    amount = _to_float(_get_any(rec, ["總額", "Gross", "Proceeds", "Amount"]))
    fee = _to_float(_get_any(rec, ["佣金", "Commission", "Fees", "Fee"]))
    net_amount = _to_float(_get_any(rec, ["淨金額", "Net Amount", "Net", "NetProceeds"]))

    currency = _get_any(rec, ["幣別", "Currency", "CCY"]) or DEFAULT_CURRENCY
    note = _get_any(rec, ["說明", "Description", "Details"])

    row_id = _make_stable_id(date, symbol, tx or side, shares, price, net_amount)

    return {
        "ID": row_id,
        "時間": time_str,
        "券商": BROKER_NAME,
        "symbol": symbol,
        "side": side,
        "shares": shares,
        "price": price,
        "currency": currency,
        "orderId": "",
        "備註": note,
        "amount": amount,
        "fee": fee,
        "net_amount": net_amount,
    }


def _get_header(ws) -> List[str]:
    header = ws.row_values(1)
    return [h.strip() for h in header if h is not None and str(h).strip()]


def _get_existing_ids(ws, id_col_name: str = "ID") -> set:
    header = _get_header(ws)
    if id_col_name not in header:
        return set()
    idx = header.index(id_col_name) + 1
    col_vals = ws.col_values(idx)
    return set([v.strip() for v in col_vals[1:] if v and str(v).strip()])


def _append_rows_in_header_order(ws, rows: List[Dict[str, object]]) -> int:
    if not rows:
        return 0

    header = _get_header(ws)
    if not header:
        raise RuntimeError("broker_fills 工作表第一列必須是表頭")

    values = [[r.get(col, "") for col in header] for r in rows]
    ws.append_rows(values, value_input_option="USER_ENTERED")
    return len(values)


def import_csv(csv_path: str) -> int:
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV 不存在：{csv_file}")

    ws_fills = get_sheet("broker_fills")

    raw = parse_ib_statement_csv(csv_file)
    parsed_count = len(raw)

    mapped_all = [map_record_to_broker_fills_row(r) for r in raw]
    existing = _get_existing_ids(ws_fills, "ID")

    # 只要 ID 非空 & 不在 existing 就寫入
    to_insert = [
        r for r in mapped_all
        if str(r.get("ID", "")).strip() and str(r["ID"]) not in existing
    ]
    inserted = _append_rows_in_header_order(ws_fills, to_insert) if to_insert else 0

    append_sync_log(
        log_type=LOG_TYPE,
        broker=BROKER_NAME,
        count=inserted,
        status="success",
        note=f"file={csv_file.name} | parsed={parsed_count} | insert={inserted}",
    )

    print(f"✅ CSV 匯入完成：{inserted} 筆（{csv_file.name}）")
    if inserted == 0:
        header = _get_header(ws_fills)
        print(f"   (debug) parsed={parsed_count}, mapped={len(mapped_all)}, existing_ids={len(existing)}")
        print(f"   (debug) broker_fills header={header}")

    return inserted


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("csv", help="Path to IB statement CSV")
    args = p.parse_args()

    try:
        import_csv(args.csv)
    except Exception as e:
        try:
            append_sync_log(
                log_type=LOG_TYPE,
                broker=BROKER_NAME,
                count=0,
                status="fail",
                note=str(e),
            )
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()