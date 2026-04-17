# brokers/ib/sync_ib_snapshot.py
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
import os
import logging


BROKER_NAME = "IBKR"

# 避免 ib_insync INFO 洗版
logging.getLogger().setLevel(logging.INFO)
for _name in ("ib_insync", "ib_insync.client", "ib_insync.wrapper", "ib_insync.ib"):
    logging.getLogger(_name).setLevel(logging.WARNING)


def _now_ts_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _as_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        try:
            return float(str(x).replace(",", "").strip())
        except Exception:
            return None


def _num(x: Any) -> Any:
    v = _as_float(x)
    return round(v, 2) if v is not None else ""


def append_sync_log(
    log_type: str,
    broker: str,
    count: int,
    status: str,
    note: str = "",
) -> None:
    """
    sync_logs 建議表頭：
    時間 | 類型 | 券商 | 新增筆數 | 狀態 | 備註
    """
    from sheets_utils import get_sheet

    sheet = get_sheet("sync_logs")
    if sheet is None:
        return

    row = [_now_ts_str(), log_type, broker, int(count), status, note]
    sheet.append_row(row, value_input_option="USER_ENTERED")


def _build_snapshot_row_fixed(header: List[str], snap: Any) -> List[Any]:
    """
    broker_snapshot 固定寫入（比照 broker_positions 的「固定順序 append」策略）
    你的表頭目前是：
    ['時間', '券商', '帳戶總資產', '可用現金', '含融資權益', 'currency', '換算台幣']

    這裡不再使用「用 header 當 key」去 row.get(header)，避免任何不可見字元/空白導致 mapping 失敗。
    直接用欄名判斷要放哪個值。
    """

    ts = _now_ts_str()

    # ✅ 這三個一定要用你 dataclass 的 snake_case 欄位
    nlv = _num(getattr(snap, "net_liquidation", None))
    cash = _num(getattr(snap, "total_cash_value", None))
    ewl = _num(getattr(snap, "equity_with_loan", None))
    ccy = getattr(snap, "currency", "") or ""

    values: List[Any] = []

    for col in header:
        col = str(col).strip()

        if col == "時間":
            values.append(ts)
        elif col == "券商":
            values.append(BROKER_NAME)
        elif col == "帳戶總資產":
            values.append(nlv)
        elif col == "可用現金":
            values.append(cash)
        elif col == "含融資權益":
            values.append(ewl)
        elif col.lower() == "currency" or col == "幣別":
            values.append(ccy)
        elif "換算" in col or "台幣" in col or col.lower() == "twd":
            # 讓 sheet 公式自己算
            values.append("")
        else:
            # 不認得的欄位就留空
            values.append("")

    return values


def append_broker_snapshot(snap: Any) -> int:
    from sheets_utils import get_sheet

    sheet = get_sheet("broker_snapshot")
    if sheet is None:
        return 0

    header = sheet.row_values(1)
    values = _build_snapshot_row_fixed(header, snap)

    # Debug：你要確認「真的有寫入值」→ 先看 values
    if os.getenv("DEBUG_SHEETS") == "1":
        try:
            wb = getattr(sheet, "spreadsheet", None)
            print("[DEBUG] spreadsheet_title=", getattr(wb, "title", None))
            print("[DEBUG] spreadsheet_id=", getattr(wb, "id", None))
        except Exception:
            pass
        print("[DEBUG] worksheet_title=", getattr(sheet, "title", None))
        print("[DEBUG] worksheet_id=", getattr(sheet, "id", None))
        print("[DEBUG] header=", header)
        print("[DEBUG] values=", values)

    sheet.append_row(values, value_input_option="USER_ENTERED")
    return 1


def main() -> None:
    try:
        # 延遲 import，避免 import-time side effects
        from brokers.ib_api import get_account_snapshot

        snap = get_account_snapshot()

        # 確認 snapshot 真有值
        print(
            f"[snapshot] nlv={getattr(snap, 'net_liquidation', None)} "
            f"cash={getattr(snap, 'total_cash_value', None)} "
            f"ewl={getattr(snap, 'equity_with_loan', None)} "
            f"ccy={getattr(snap, 'currency', '')}",
            flush=True,
        )

        added = append_broker_snapshot(snap)

        note = (
            f"NLV={_num(getattr(snap, 'net_liquidation', None))} "
            f"CASH={_num(getattr(snap, 'total_cash_value', None))} "
            f"EWL={_num(getattr(snap, 'equity_with_loan', None))} "
            f"{getattr(snap, 'currency', '')}"
        ).strip()

        append_sync_log(
            log_type="broker_snapshot_sync",
            broker=BROKER_NAME,
            count=added,
            status="success" if added > 0 else "skipped",
            note=note,
        )

        print(f"[broker_snapshot] appended={added}", flush=True)

    except Exception as e:
        try:
            append_sync_log(
                log_type="broker_snapshot_sync",
                broker=BROKER_NAME,
                count=0,
                status="fail",
                note=f"error={repr(e)}",
            )
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()