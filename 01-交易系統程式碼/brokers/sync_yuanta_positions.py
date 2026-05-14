# brokers/sync_yuanta_positions.py
"""
元大證券庫存 → Google Sheets broker_positions 同步腳本

使用方式（需 32-bit Python + pythonnet）：
  .venv_yuanta32\Scripts\python.exe brokers\sync_yuanta_positions.py

流程：
  1. 登入元大 API
  2. 發送 RQ("0015") 查詢庫存
  3. 等待非同步回應
  4. 解析原始資料字串
  5. 寫入 Google Sheets broker_positions 分頁
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List

# 確保能 import 專案根目錄的模組 (sheets_utils 等)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from brokers.yuanta_api import (
    yuanta_login,
    register_events,
    query_stock_positions,
    fetch_positions,
)

BROKER_NAME = "元大"
WAIT_SECONDS = 15  # 等待非同步庫存回應的秒數


# =========================
# 解析原始資料
# =========================

def parse_position_string(raw: str) -> dict | None:
    """
    將元大 OnResponse 回傳的原始字串解析為結構化 dict。
    適用於 Function ID: 20.103.0.22 (SummaryReport)

    CSV 格式（由 yuanta_api.py on_response 產生）：
      [0-3]:  保留欄位
      [4]:    股票代號 (stk_code)
      [5]:    保留
      [6]:    庫存股數 (stk_nos)
      [7]:    均價/股 = 總成本 / 股數 (avg_cost)
      [8]:    總成本 NTD (stk_total_cost)
      [9]:    欄位 offset 105（avgCost × 10000，冗餘）
      [10-11]:保留 (0)
      [12]:   可賣股數 (sellable)
      [13]:   現價 (currentPrice)
      [14]:   買入價 (bidPrice)
      [15]:   賣出價 (askPrice)
      [16]:   漲停 (limitUp)
      [17]:   跌停 (limitDown)
    """
    if not raw or "執行異常" in raw:
        return None

    parts = [p.strip() for p in raw.split(",")]
    if len(parts) < 8:
        print(f"⚠️ 格式不符（欄位數 {len(parts)}）：{raw}")
        return None

    try:
        symbol = parts[4]
        position = float(parts[6]) if parts[6] else 0
        avg_cost = float(parts[7]) if parts[7] else 0

        if position == 0:
            return None

        result = {
            "symbol": symbol,
            "secType": "STK",
            "exchange": "TWSE",
            "currency": "TWD",
            "position": position,
            "avgCost": avg_cost,
            "totalCost": float(parts[8]) if len(parts) > 8 and parts[8] else 0,
        }

        # 現價相關欄位（off=161 以後解碼）
        if len(parts) > 13 and parts[13]:
            current_price = float(parts[13])
            result["currentPrice"] = current_price
            result["marketValue"] = round(current_price * position, 2)
            if avg_cost > 0:
                result["unrealizedPnL"] = round((current_price - avg_cost) * position, 2)
            else:
                result["unrealizedPnL"] = 0.0

        if len(parts) > 14 and parts[14]:
            result["bidPrice"] = float(parts[14])
        if len(parts) > 15 and parts[15]:
            result["askPrice"] = float(parts[15])
        if len(parts) > 16 and parts[16]:
            result["limitUp"] = float(parts[16])
        if len(parts) > 17 and parts[17]:
            result["limitDown"] = float(parts[17])
        if len(parts) > 12 and parts[12]:
            result["sellable"] = float(parts[12])

        return result
    except (ValueError, IndexError) as e:
        print(f"⚠️ 解析失敗：{e}  raw={raw}")
        return None


# =========================
# fingerprint（與 IB 同邏輯）
# =========================

def _norm_pos(p: dict) -> dict:
    return {
        "symbol": str(p.get("symbol", "")).strip(),
        "secType": str(p.get("secType", "")).strip(),
        "exchange": str(p.get("exchange", "")).strip(),
        "currency": str(p.get("currency", "")).strip(),
        "position": round(float(p.get("position", 0) or 0), 8),
        "avgCost": round(float(p.get("avgCost", 0) or 0), 8),
        "currentPrice": round(float(p.get("currentPrice", 0) or 0), 2),
    }


def _fingerprint(positions: List[dict]) -> str:
    normed = [_norm_pos(p) for p in positions]
    normed.sort(key=lambda x: (x["symbol"], x["secType"], x["exchange"], x["currency"]))
    return json.dumps(normed, sort_keys=True, separators=(",", ":"))


# =========================
# 讀取最後快照（與 IB 同邏輯）
# =========================

def _read_last_snapshot(sheet) -> str | None:
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
    i_price = col("currentPrice")

    if i_time is None or i_broker is None or i_symbol is None:
        return None

    last_ts = None
    for r in reversed(rows):
        if r[i_broker] == BROKER_NAME:
            last_ts = r[i_time]
            break

    if not last_ts:
        return None

    last_positions = []
    for r in rows:
        if r[i_broker] != BROKER_NAME or r[i_time] != last_ts:
            continue
        last_positions.append({
            "symbol": r[i_symbol],
            "secType": r[i_sec] if i_sec is not None else "",
            "exchange": r[i_ex] if i_ex is not None else "",
            "currency": r[i_ccy] if i_ccy is not None else "",
            "position": r[i_pos] if i_pos is not None else 0,
            "avgCost": r[i_avg] if i_avg is not None else 0,
            "currentPrice": r[i_price] if i_price is not None else 0,
        })

    if not last_positions:
        return None

    return _fingerprint(last_positions)


# =========================
# 寫入 Google Sheets
# =========================

def append_broker_positions(positions: List[dict]) -> int:
    """Upsert 元大庫存至 broker_positions（同 symbol 更新，新 symbol 新增，已出清刪除）"""
    from sheets_utils import sync_broker_positions_and_log_trades

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_positions = []
    
    for p in positions:
        formatted_positions.append({
            "timestamp": ts,
            "broker": BROKER_NAME,
            "symbol": p.get("symbol", ""),
            "secType": p.get("secType", "STK"),
            "exchange": p.get("exchange", "TWSE"),
            "currency": p.get("currency", "TWD"),
            "position": p.get("position", 0),
            "avgCost": p.get("avgCost", 0),
            "marketPrice": p.get("currentPrice", 0),
            "marketValue": p.get("marketValue", 0),
            "unrealizedPNL": p.get("unrealizedPnL", 0),
            "sellable": p.get("sellable", p.get("position", 0)),
            "limitUp": p.get("limitUp", 0),
            "limitDown": p.get("limitDown", 0)
        })
        
    ok = sync_broker_positions_and_log_trades(BROKER_NAME, formatted_positions)
    return len(formatted_positions) if ok else 0


# =========================
# 同步日誌
# =========================

def _log_sync(added: int) -> None:
    try:
        from sheets_utils import get_sheet
        sheet = get_sheet("sync_logs")
        if sheet:
            sheet.append_row(
                [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "broker_positions_sync",
                    BROKER_NAME,
                    added,
                    "success" if added > 0 else "skipped",
                    "",
                ],
                value_input_option="USER_ENTERED",
            )
    except Exception as e:
        print(f"sync_logs 寫入失敗：{e}")


# =========================
# main
# =========================

def main() -> bool:
    print("=" * 50)
    print(f"  元大庫存同步  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 1) 登入
    api = yuanta_login()
    register_events(api)

    # 增加等待登入生效的時間 (從 5s 增加到 40s)
    # 某些系統可能需要更長時間等待登入完全生效
    print("等待 40 秒確保登入完全生效和認證...")
    for i in range(40):
        time.sleep(1)
        if i % 10 == 0:
            print(f"  ... {i}s")

    # 2) 發送庫存查詢 (增加重試機制)
    ok = False
    for attempt in range(1, 4):
        print(f"嘗試發送庫存查詢 (第 {attempt} 次)...")
        ok = query_stock_positions(api)
        if ok:
            break
        print("尚未登入或發送失敗，等待 10 秒後重試...")
        time.sleep(10)

    if not ok:
        print("庫存查詢指令多次發送失敗")
        _log_sync(0)
        return False

    # 3) 等待非同步回應
    print(f"等待 {WAIT_SECONDS} 秒接收庫存回應...")
    for i in range(WAIT_SECONDS):
        time.sleep(1)
        print(".", end="", flush=True)
    print()

    # 4) 取得並解析結果
    raw_list = fetch_positions(api)
    if not raw_list:
        print("未收到任何庫存回應")
        _log_sync(0)
        return False

    print(f"收到 {len(raw_list)} 筆原始庫存資料")

    positions = []
    for raw in raw_list:
        parsed = parse_position_string(raw)
        if parsed and parsed["position"] != 0:
            positions.append(parsed)

    if not positions:
        print("ℹ️ 無有效庫存（可能全部已出清）")
        _log_sync(0)
        return

    print(f"解析完成：{len(positions)} 檔有效庫存")
    total_market_value = 0.0
    total_unrealized = 0.0
    for p in positions:
        mv = p.get("marketValue", 0) or 0
        pnl = p.get("unrealizedPnL", 0) or 0
        total_market_value += mv
        total_unrealized += pnl
        print(f"   {p['symbol']}  {p['position']}股  均價:{p['avgCost']:.2f}  現價:{p.get('currentPrice',0):.2f}  市值:{mv:.0f}  未實現:{pnl:.0f}")
    print(f"   ── 帳戶總市值: {total_market_value:.0f} NTD  未實現損益: {total_unrealized:.0f} NTD")

    # 5) 先存 JSON snapshot（32-bit SSL 可能無法直連 Google OAuth）
    snapshot_path = PROJECT_ROOT / "data" / "yuanta_positions_snapshot.json"
    snapshot_path.parent.mkdir(exist_ok=True)
    snapshot = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "broker": BROKER_NAME,
        "totalMarketValue": round(total_market_value, 2),
        "totalUnrealizedPnL": round(total_unrealized, 2),
        "positions": positions,
    }
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已儲存庫存 snapshot → {snapshot_path}")

    # Step 1 完成通知已移除（避免與 Step 2「📈 元大庫存更新」重複）
    # 改由 upload_yuanta_to_sheets.py 統一通知（含均價，較完整）
    # 2026-05-14 cleanup by Krystal + Claude

    # 6) 嘗試直接寫入 Google Sheets（若 SSL 失敗則留給 upload_yuanta_to_sheets.py 處理）
    try:
        added = append_broker_positions(positions)
        _log_sync(added)
        print(f"\n{'成功' if added > 0 else '略過'} 同步完成，寫入 {added} 筆")
    except Exception as e:
        print(f"\n[WARN] Google Sheets 寫入失敗（{e}），已存 JSON snapshot，請執行 upload_yuanta_to_sheets.py")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
