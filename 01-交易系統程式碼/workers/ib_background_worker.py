"""
IB Gateway 背景查詢進程
- 獨立進程運行，避免 Flask 多線程問題
- 每 10 秒查詢一次 IB 帳戶信息
- 將變化數據寫入 Google Sheets
"""

import logging
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [IB Worker] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/ib_worker.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# 確保路徑正確
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from brokers.ib_api import get_ib_connection, get_account_summary, get_positions


# ============================
# 工具函數
# ============================

def _norm_pos(p: Dict[str, Any]) -> Dict[str, Any]:
    """規範化持倉數據"""
    return {
        "symbol": str(p.get("symbol", "")).strip(),
        "secType": str(p.get("secType", "")).strip(),
        "exchange": str(p.get("exchange", "")).strip(),
        "currency": str(p.get("currency", "")).strip(),
        "position": round(float(p.get("position", 0) or 0), 8),
        "avgCost": round(float(p.get("avgCost", 0) or 0), 8),
    }


def _fingerprint(positions: List[Dict[str, Any]]) -> str:
    """生成持倉指紋以檢測變化"""
    normed = [_norm_pos(p) for p in positions]
    normed.sort(key=lambda x: (x["symbol"], x["secType"], x["exchange"], x["currency"]))
    return json.dumps(normed, sort_keys=True, separators=(",", ":"))


def _read_last_snapshot(sheet) -> Optional[str]:
    """從 Google Sheets 讀取最後一次快照"""
    try:
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

        # 找最後一筆 IB 數據的時間戳
        last_ts = None
        for r in reversed(rows):
            if not r or len(r) <= i_broker:
                continue
            if i_time >= len(r):
                continue
            broker_val = r[i_broker].upper() if isinstance(r[i_broker], str) else ""
            if broker_val == "IB":
                last_ts = r[i_time]
                break

        if not last_ts:
            return None

        # 讀取該時間戳的所有持倉
        last_positions = []
        max_idx = max([i for i in [i_time, i_broker, i_symbol, i_sec, i_ex, i_ccy, i_pos, i_avg] if i is not None])

        for r in rows:
            if not r or len(r) <= max_idx:
                continue
            broker_val = r[i_broker].upper() if isinstance(r[i_broker], str) else ""
            if broker_val != "IB" or r[i_time] != last_ts:
                continue
            last_positions.append({
                "symbol": r[i_symbol] if i_symbol is not None and i_symbol < len(r) else "",
                "secType": r[i_sec] if i_sec is not None and i_sec < len(r) else "",
                "exchange": r[i_ex] if i_ex is not None and i_ex < len(r) else "",
                "currency": r[i_ccy] if i_ccy is not None and i_ccy < len(r) else "",
                "position": float(r[i_pos]) if i_pos is not None and i_pos < len(r) and str(r[i_pos]).strip() else 0,
                "avgCost": float(r[i_avg]) if i_avg is not None and i_avg < len(r) and str(r[i_avg]).strip() else 0,
            })

        if not last_positions:
            return None

        return _fingerprint(last_positions)
    except Exception as e:
        logger.warning(f"無法讀取 Google Sheets 快照：{e}")
        return None


def _write_positions_to_sheets(positions: List[Dict[str, Any]]) -> bool:
    """寫入持倉到 Google Sheets"""
    try:
        from sheets_utils import get_sheet

        sheet = get_sheet("broker_positions")
        if sheet is None:
            logger.error("無法取得 broker_positions 分頁")
            return False

        # 檢查是否有變化
        current_fp = _fingerprint(positions)
        last_fp = _read_last_snapshot(sheet)

        if last_fp is not None and current_fp == last_fp:
            logger.debug("✓ 持倉未變動，跳過寫入")
            return False

        # 準備寫入數據
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rows = []
        for p in positions:
            p = _norm_pos(p)
            rows.append([
                ts,
                "IB",
                p["symbol"],
                p["secType"],
                p["exchange"],
                p["currency"],
                p["position"],
                p["avgCost"],
            ])

        if rows:
            sheet.append_rows(rows, value_input_option="USER_ENTERED")
            logger.info(f"✅ 已寫入 {len(rows)} 筆 IB 持倉至 Google Sheets")
            return True
        return False

    except Exception as e:
        logger.error(f"寫入 Google Sheets 失敗：{e}")
        return False


def _log_sync_to_sheets(added: int, status: str, note: str = "") -> None:
    """記錄同步日誌"""
    try:
        from sheets_utils import get_sheet

        sheet = get_sheet("sync_logs")
        if sheet:
            sheet.append_row(
                [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "ib_positions_sync",
                    "IB",
                    added,
                    status,
                    note,
                ],
                value_input_option="USER_ENTERED",
            )
    except Exception as e:
        logger.debug(f"無法寫入同步日誌：{e}")


# ============================
# 主要邏輯
# ============================

class IBBackgroundWorker:
    """IB 背景工作進程"""

    def __init__(self, poll_interval: int = 10, reconnect_delay: int = 30):
        self.poll_interval = poll_interval  # 輪詢間隔（秒）
        self.reconnect_delay = reconnect_delay  # 重連延遲（秒）
        self.last_positions = None
        self.last_account_summary = None

    def run(self) -> None:
        """主循環"""
        logger.info("=" * 60)
        logger.info("🚀 IB 背景查詢進程已啟動")
        logger.info("=" * 60)

        poll_count = 0

        while True:
            try:
                poll_count += 1
                logger.debug(f"📊 輪詢 #{poll_count} ({datetime.now().strftime('%H:%M:%S')})")

                # 1) 嘗試連接 IB
                ib = get_ib_connection()
                if not ib or not ib.isConnected():
                    logger.warning("⚠️ IB 未連接，等待 {0}s 後重試...".format(self.reconnect_delay))
                    time.sleep(self.reconnect_delay)
                    continue

                # 2) 查詢帳戶信息
                try:
                    account_summary = ib.accountSummary()
                    if account_summary:
                        logger.debug(f"✓ 收到帳戶摘要 ({len(list(account_summary))} 項)")
                except Exception as e:
                    logger.warning(f"⚠️ 無法查詢帳戶摘要：{e}")
                    account_summary = None

                # 3) 查詢持倉
                try:
                    positions = ib.positions()
                    if positions:
                        positions = list(positions)
                        logger.debug(f"✓ 收到 {len(positions)} 筆持倉資料")

                        # 轉換為字典格式
                        formatted_positions = []
                        for pos in positions:
                            if pos.position != 0:  # 只保留非零持倉
                                formatted_positions.append({
                                    "symbol": pos.contract.symbol,
                                    "secType": pos.contract.secType,
                                    "exchange": pos.contract.exchange,
                                    "currency": pos.contract.currency,
                                    "position": pos.position,
                                    "avgCost": pos.avgCost,
                                })

                        # 4) 寫入 Google Sheets
                        if formatted_positions:
                            added = _write_positions_to_sheets(formatted_positions)
                            if added:
                                _log_sync_to_sheets(len(formatted_positions), "success")
                            else:
                                logger.debug("✓ 持倉未變動")
                        else:
                            logger.debug("ℹ️ 無非零持倉")

                except Exception as e:
                    logger.warning(f"⚠️ 無法查詢持倉：{e}")

                # 5) 等待下一次輪詢
                logger.debug(f"💤 等待 {self.poll_interval}s 後進行下一次輪詢...")
                time.sleep(self.poll_interval)

            except KeyboardInterrupt:
                logger.info("\n⏹️  IB 背景進程已停止 (Ctrl+C)")
                break
            except Exception as e:
                logger.error(f"❌ 背景進程異常：{e}", exc_info=True)
                logger.warning(f"⚠️ 等待 {self.reconnect_delay}s 後重試...")
                time.sleep(self.reconnect_delay)


def main():
    """入口函數"""
    # 創建日誌目錄
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    worker = IBBackgroundWorker(poll_interval=10, reconnect_delay=30)
    worker.run()


if __name__ == "__main__":
    main()
