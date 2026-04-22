# pages/1_實盤交易管理系統.py
# ------------------------------------------------------------
# 實盤交易管理系統（Hybrid V2 - Daily NAV REAL + Dashboard + IB同步三按鈕 + SCHWAB骨架）
# + ✅ 交易原因直接寫回 trades（做法 #2）
# ------------------------------------------------------------

from __future__ import annotations

import os
import platform
import subprocess
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from concurrent.futures import ThreadPoolExecutor

# 导入UI主题
sys.path.append(str(Path(__file__).parent.parent))
from utils.ui_theme import apply_theme


# ============================================================
# 0) 外部依賴：Google Sheets / IB API / SCHWAB API
# ============================================================
SHEETS_OK = True
SHEETS_ERR = ""

try:
    from sheets_utils import (
        get_sheet,
        read_daily_nav,
        read_portfolio_daily,
        read_strategies,
        read_trades,
        read_sheet_data_with_cache,
    )  # type: ignore
except Exception as e:
    SHEETS_OK = False
    SHEETS_ERR = f"找不到 sheets_utils（或匯入失敗）：{e}"

    def get_sheet(name: str):
        raise RuntimeError("Google Sheets 尚未就緒：缺少 sheets_utils.get_sheet()")

    def read_daily_nav() -> pd.DataFrame:
        return pd.DataFrame()

    def read_portfolio_daily() -> pd.DataFrame:
        return pd.DataFrame()

    def read_strategies() -> pd.DataFrame:
        return pd.DataFrame()

    def read_trades() -> pd.DataFrame:
        return pd.DataFrame()

    def read_sheet_data_with_cache(name: str) -> pd.DataFrame:
        return pd.DataFrame()


# IB API（可選）
try:
    from brokers.ib_api import get_account_snapshot, get_open_positions, get_executions  # type: ignore

    HAS_IB_API = True
except Exception as e:
    HAS_IB_API = False
    IB_ERROR = str(e)
    print(f"[⚠️ IB API 導入失敗] {e}")

    def get_account_snapshot():
        raise RuntimeError(f"IB API 不可用（未設定或匯入失敗）：{IB_ERROR}")

    def get_open_positions():
        raise RuntimeError(f"IB API 不可用（未設定或匯入失敗）：{IB_ERROR}")

    def get_executions(days: int = 7):
        raise RuntimeError(f"IB API 不可用（未設定或匯入失敗）：{IB_ERROR}")


# Schwab（可選）
try:
    from brokers.schwab_api import (
        is_schwab_enabled,
        get_schwab_accounts,
        get_schwab_open_positions,
    )  # type: ignore

    HAS_SCHWAB_API = True
except Exception:
    HAS_SCHWAB_API = False

    def is_schwab_enabled() -> bool:
        return False

    def get_schwab_accounts():
        raise RuntimeError("Schwab API 不可用（未安裝/未設定/未通過審核）")

    def get_schwab_open_positions():
        raise RuntimeError("Schwab API 不可用（未安裝/未設定/未通過審核）")


# Yuanta（可選）
HAS_YUANTA_API = False
if platform.system() == "Windows":
    try:
        from brokers.yuanta_api import (
            yuanta_login,
            register_events,
            fetch_fills,
            query_stock_positions,
            fetch_positions,
        )  # type: ignore

        HAS_YUANTA_API = True
    except Exception:
        HAS_YUANTA_API = False

        def yuanta_login(*args, **kwargs):
            raise RuntimeError("Yuanta API 不可用")

        def register_events(*args, **kwargs):
            pass

        def fetch_fills(*args, **kwargs):
            raise RuntimeError("Yuanta API 不可用：請確認 Windows + pythonnet + DLL/憑證設定完成。")

        def query_stock_positions(*args, **kwargs):
            return False

        def fetch_positions(*args, **kwargs):
            return []
else:

    def yuanta_login(*args, **kwargs):
        return None

    def register_events(*args, **kwargs):
        pass

    def fetch_fills(*args, **kwargs):
        return []

    def query_stock_positions(*args, **kwargs):
        return False

    def fetch_positions(*args, **kwargs):
        return []


# ============================================================
# 1) Streamlit 基本設定 + CSS
# ============================================================
st.set_page_config(
    page_title="實盤交易管理系統",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 应用现代主题
apply_theme(st)

st.markdown(
    """
<style>
.stApp {
  background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
  color: #1F2937;
}

/* Sidebar - 现代科技紫蓝系 */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
  border-right: 1px solid #E5E7EB;
  box-shadow: 0 0 20px rgba(91, 71, 217, 0.05);
}

/* Cards - 现代卡片设计 */
.metric-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border: 1px solid #E5E7EB;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.metric-card:hover {
  border-color: #5B47D9;
  box-shadow: 0 0 20px rgba(91, 71, 217, 0.2);
  transform: translateY(-4px);
}

.metric-title {
  font-size: 12px;
  color: #9CA3AF;
  margin-bottom: 8px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: #5B47D9;
}

.metric-sub   {
  font-size: 12px;
  color: #06B6D4;
  margin-top: 6px;
  font-weight: 600;
}

.chart-box {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 20px;
  margin-top: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border: 1px solid #E5E7EB;
}

/* Buttons - 现代渐变按钮 */
.stButton>button {
  background: linear-gradient(135deg, #5B47D9 0%, #4F46E5 100%) !important;
  color: #FFFFFF !important;
  border-radius: 12px !important;
  border: none !important;
  padding: 10px 24px !important;
  font-weight: 600 !important;
  box-shadow: 0 4px 6px -1px rgba(91, 71, 217, 0.2) !important;
}

.stButton>button:hover {
  box-shadow: 0 10px 15px -3px rgba(91, 71, 217, 0.3) !important;
  transform: translateY(-2px) !important;
}

/* Select */
div[data-baseweb="select"] * { color: #1F2937 !important; }
.stSelectbox label, .stMultiSelect label { color: #1F2937 !important; }

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)


def metric_card(title: str, value: str, sub: str = "", variant: str = "neutral") -> str:
    color_map = {
        "positive": "#16a34a",
        "negative": "#dc2626",
        "neutral": "#0f172a",
    }
    value_color = color_map.get(variant, color_map["neutral"])
    return f"""
    <div class="metric-card">
      <div class="metric-title">{title}</div>
      <div class="metric-value" style="color:{value_color};">{value}</div>
      <div class="metric-sub">{sub}</div>
    </div>
    """


# ============================================================
# 2) 小工具：清欄位 / cache 讀取 / sync_logs
# ============================================================
def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    df = df.copy()
    df.columns = [str(c).replace("欄位：", "").strip() for c in df.columns]
    return df


@st.cache_data(ttl=60)
def load_strategies() -> pd.DataFrame:
    return _clean_columns(read_strategies())


@st.cache_data(ttl=60)
def load_daily_nav() -> pd.DataFrame:
    return _clean_columns(read_daily_nav())


@st.cache_data(ttl=300)
def load_portfolio_daily() -> pd.DataFrame:
    df = _clean_columns(read_portfolio_daily())
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    num_cols = [c for c in df.columns if c != "date"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)


@st.cache_data(ttl=60)
def load_trades() -> pd.DataFrame:
    return _clean_columns(read_trades())


@st.cache_data(ttl=60)
def load_sheet_df(sheet_name: str) -> pd.DataFrame:
    return _clean_columns(read_sheet_data_with_cache(sheet_name))


def is_offline_mode() -> bool:
    """檢查是否處於離線模式"""
    from sheets_utils import DISABLE_SHEETS
    return DISABLE_SHEETS or st.session_state.get("force_offline", False)


def preload_dashboard_data():
    """循序載入所有必要的 Sheets 資料 (暫時移除並行以提升穩定性)"""
    try:
        # 循序執行，避免並發導致的 Rate Limit 或 Auth 問題
        d1 = load_daily_nav()
        d2 = load_strategies()
        d3 = load_trades()
        d4 = load_sheet_df("round_trips")
        d5 = load_sheet_df("broker_positions")
        
        return d1, d2, d3, d4, d5

    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        st.error(f"資料載入失敗 (順序執行模式): {err_msg}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


def append_sync_log(log_type: str, broker: str, count: int, status: str, note: str = ""):
    """
    sync_logs 預設欄位建議：
    時間 / 類型 / 券商 / 新增筆數 / 狀態 / 備註
    """
    try:
        sh = get_sheet("sync_logs")
        if sh is None:
            return
        header = [h.strip() for h in sh.row_values(1)]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = {"時間": now_str, "類型": log_type, "券商": broker, "新增筆數": int(count), "狀態": status, "備註": note}
        ordered = [row.get(h, "") for h in header]
        sh.append_row(ordered, value_input_option="USER_ENTERED")
    except Exception as e:
        logger.warning(f"寫入 sync_logs 失敗（可忽略）：{e}")


def _run_snapshot_upload():
    """非同步執行 upload_yuanta_to_sheets.py，並在 UI 顯示結果。"""
    upload_script = Path(__file__).resolve().parents[1] / "brokers" / "upload_yuanta_to_sheets.py"
    snapshot = Path(__file__).resolve().parents[1] / "data" / "yuanta_positions_snapshot.json"

    if not snapshot.exists():
        st.info("ℹ️ 元大 snapshot JSON 不存在，跳過上傳")
        return

    with st.spinner("📤 同步元大 snapshot → Google Sheets..."):
        try:
            result = subprocess.run(
                [os.sys.executable, str(upload_script)],
                capture_output=True, text=True, timeout=60,
                cwd=str(upload_script.parent.parent),
            )
            output = (result.stdout + result.stderr).strip()
            if result.returncode == 0:
                st.success("✅ 元大 snapshot 已同步至 Google Sheets")
            else:
                st.warning(f"⚠️ snapshot 上傳結束（RC={result.returncode}）")
            if output:
                st.caption(output[-500:])  # 只顯示最後 500 字
        except subprocess.TimeoutExpired:
            st.warning("⚠️ snapshot 上傳超時（>60s）")
        except Exception as e:
            st.warning(f"⚠️ snapshot 上傳失敗：{e}")


# ============================================================
# ✅ 2.1) 合併欄位工具（修 KeyError 起始資金）
# ============================================================
def _coalesce_columns(df: pd.DataFrame, base_col: str, prefer: str = "y") -> pd.DataFrame:
    """
    pandas merge 若遇到同名欄位會產生 base_col_x / base_col_y
    這裡會把它們合併成單一 base_col。
    prefer="y" 表示優先用 _y（右表/策略表），沒有才用 _x。
    """
    if df is None or df.empty:
        return df
    df = df.copy()

    if base_col in df.columns:
        return df

    x = f"{base_col}_x"
    y = f"{base_col}_y"
    if x in df.columns or y in df.columns:
        if prefer.lower() == "y":
            df[base_col] = df[y] if y in df.columns else np.nan
            if x in df.columns:
                df[base_col] = df[base_col].where(~df[base_col].isna(), df[x])
        else:
            df[base_col] = df[x] if x in df.columns else np.nan
            if y in df.columns:
                df[base_col] = df[base_col].where(~df[base_col].isna(), df[y])

        for c in [x, y]:
            if c in df.columns:
                df.drop(columns=[c], inplace=True)

    return df


# ============================================================
# 2.2) ✅ trades（你原本就有）寫入/更新：進場原因 / 出場原因 / 備註
# ============================================================
TRADES_REQUIRED_COLS = [
    "id", "日期", "券商", "標的", "方向", "進場價", "出場價", "數量", "狀態",
    "策略", "進場原因", "出場原因", "備註",
    "entry_time", "exit_time", "currency", "source", "pnl"
]


def _col_to_letter(n: int) -> str:
    """1->A, 2->B ..."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _ensure_trades_header() -> List[str]:
    sh = get_sheet("trades")
    header = [h.strip() for h in sh.row_values(1)]
    if not header:
        raise RuntimeError("trades 分頁沒有表頭，請先建立表頭。")
    missing = [c for c in TRADES_REQUIRED_COLS if c not in header]
    if missing:
        raise RuntimeError(f"trades 缺少欄位：{missing}\n目前表頭：{header}")
    return header


def _sheet_find_row_by_value(sh, header: List[str], col_name: str, value: str) -> int | None:
    """回傳 sheet row index（1-based）；找不到回 None"""
    if col_name not in header:
        return None
    col_idx = header.index(col_name)  # 0-based
    values = sh.get_all_values()
    if len(values) <= 1:
        return None
    target = str(value).strip()
    if not target:
        return None
    for i in range(1, len(values)):  # skip header
        row = values[i]
        cell = row[col_idx] if col_idx < len(row) else ""
        if str(cell).strip() == target:
            return i + 1  # sheet row number
    return None


def _sheet_update_row(sh, header: List[str], row_idx: int, updates: Dict[str, Any]):
    """
    讀出整列 -> 更新指定欄位 -> 一次 update 整列
    """
    row_vals = sh.row_values(row_idx)
    if len(row_vals) < len(header):
        row_vals += [""] * (len(header) - len(row_vals))

    for k, v in updates.items():
        if k in header:
            j = header.index(k)
            row_vals[j] = v

    last_col_letter = _col_to_letter(len(header))
    rng = f"A{row_idx}:{last_col_letter}{row_idx}"
    sh.update(rng, [row_vals], value_input_option="USER_ENTERED")


def upsert_trade_reason_to_trades(
    *,
    source: str,
    broker: str,
    symbol: str,
    direction: str,
    qty: Any,
    entry_px: Any,
    exit_px: Any,
    currency: str,
    entry_time: str,
    exit_time: str,
    strategy: str,
    note_type: str,  # "Entry" / "Exit" / "Adjust" / "Review"
    reason_text: str,
    memo_text: str,
    pnl: Any = "",
):
    """
    - 用 source（fill_uid / exit_uid）對 trades.source 找 row
    - 找到就更新：進場原因/出場原因/備註/策略 等
    - 找不到就新增一列（能填多少填多少）
    """
    sh = get_sheet("trades")
    header = _ensure_trades_header()

    src = str(source).strip()
    row_idx = _sheet_find_row_by_value(sh, header, "source", src)

    now_id = f"N_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    today = datetime.now().strftime("%Y-%m-%d")

    entry_reason = ""
    exit_reason = ""
    memo_text = (memo_text or "").strip()
    reason_text = (reason_text or "").strip()

    if note_type == "Entry":
        entry_reason = reason_text
    elif note_type == "Exit":
        exit_reason = reason_text
    else:
        combo = f"[{note_type}] {reason_text}".strip()
        memo_text = (combo + ("\n" + memo_text if memo_text else "")).strip()

    if row_idx:
        updates = {
            "券商": broker,
            "標的": symbol,
            "方向": direction,
            "數量": qty,
            "進場價": entry_px,
            "出場價": exit_px,
            "currency": currency,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "策略": strategy,
            "pnl": pnl,
        }
        if entry_reason:
            updates["進場原因"] = entry_reason
        if exit_reason:
            updates["出場原因"] = exit_reason
        if memo_text:
            updates["備註"] = memo_text

        _sheet_update_row(sh, header, row_idx, updates)
        return {"action": "updated", "row": row_idx}

    new_row = {h: "" for h in header}
    new_row.update(
        {
            "id": now_id,
            "日期": today,
            "券商": broker,
            "標的": symbol,
            "方向": direction,
            "進場價": entry_px,
            "出場價": exit_px,
            "數量": qty,
            "狀態": "已成交",
            "策略": strategy,
            "進場原因": entry_reason,
            "出場原因": exit_reason,
            "備註": memo_text,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "currency": currency,
            "source": src,
            "pnl": pnl,
        }
    )
    ordered = [new_row.get(h, "") for h in header]
    sh.append_row(ordered, value_input_option="USER_ENTERED")
    return {"action": "appended", "row": None}


# ============================================================
# 3) fills -> round_trips（FIFO）同步
# ============================================================
REQUIRED_FILLS_COLS = ["時間", "券商", "symbol", "side", "shares", "price", "currency", "orderId"]


def _normalize_side(side: str) -> str:
    s = str(side).upper().strip()
    if s in ["BUY", "BOT", "B"]:
        return "BUY"
    if s in ["SELL", "SLD", "S"]:
        return "SELL"
    return s


def _make_fill_uid(row: pd.Series) -> str:
    t = str(row.get("時間", "")).strip()
    broker = str(row.get("券商", "")).strip()
    sym = str(row.get("symbol", "")).strip()
    side = str(row.get("side", "")).strip().upper()
    shares = str(row.get("shares", "")).strip()
    price = str(row.get("price", "")).strip()
    oid = str(row.get("orderId", "")).strip()
    return f"FILL|{broker}|{oid}|{t}|{sym}|{side}|{shares}|{price}"


def _roundtrip_source(entry_uid: str, exit_uid: str, qty: float) -> str:
    q = int(qty) if float(qty).is_integer() else float(qty)
    return f"PAIR|{entry_uid}|{exit_uid}|{q}"


def build_round_trips_from_fills(fills_df: pd.DataFrame) -> pd.DataFrame:
    if fills_df is None or fills_df.empty:
        return pd.DataFrame()

    missing = [c for c in REQUIRED_FILLS_COLS if c not in fills_df.columns]
    if missing:
        return pd.DataFrame()

    f = fills_df.copy()
    f["時間_dt"] = pd.to_datetime(f["時間"], errors="coerce")
    f = f.dropna(subset=["時間_dt"]).sort_values("時間_dt")

    f["shares_n"] = pd.to_numeric(f["shares"], errors="coerce")
    f["price_n"] = pd.to_numeric(f["price"], errors="coerce")
    f = f.dropna(subset=["shares_n", "price_n"])

    f["side_n"] = f["side"].apply(_normalize_side)

    trips: List[dict] = []
    group_cols = ["券商", "symbol", "currency"]

    for (broker, sym, ccy), g in f.groupby(group_cols, dropna=False):
        lots: List[dict] = []  # FIFO lots

        for _, r in g.iterrows():
            side = str(r.get("side_n", "")).strip()
            if side not in {"BUY", "SELL"}:
                continue

            qty = float(abs(r.get("shares_n", 0.0)))
            if qty <= 0:
                continue

            px = float(r.get("price_n"))
            dt = r.get("時間_dt")
            uid = _make_fill_uid(r)

            if not lots:
                lots.append({"side": side, "qty": qty, "px": px, "dt": dt, "uid": uid})
                continue

            if lots[0]["side"] == side:
                lots.append({"side": side, "qty": qty, "px": px, "dt": dt, "uid": uid})
                continue

            remaining = qty
            exit_uid = uid
            exit_side = side
            exit_dt = dt
            exit_px = px

            while remaining > 0 and lots:
                lot = lots[0]
                match_qty = min(remaining, float(lot["qty"]))

                entry_side = lot["side"]
                entry_px = float(lot["px"])
                entry_dt = lot["dt"]
                entry_uid = str(lot["uid"])

                direction = "多" if entry_side == "BUY" else "空"

                if entry_side == "BUY" and exit_side == "SELL":
                    pnl = (exit_px - entry_px) * match_qty
                elif entry_side == "SELL" and exit_side == "BUY":
                    pnl = (entry_px - exit_px) * match_qty
                else:
                    pnl = np.nan

                src = _roundtrip_source(entry_uid, exit_uid, match_qty)
                note = f"round-trip FIFO | entry={entry_uid} | exit={exit_uid}"

                trips.append(
                    {
                        "broker": str(broker).strip(),
                        "symbol": str(sym).strip(),
                        "currency": str(ccy).strip(),
                        "direction": direction,
                        "qty": match_qty,
                        "entry_time": pd.to_datetime(entry_dt).strftime("%Y-%m-%d %H:%M:%S") if pd.notna(entry_dt) else "",
                        "exit_time": pd.to_datetime(exit_dt).strftime("%Y-%m-%d %H:%M:%S") if pd.notna(exit_dt) else "",
                        "entry_px": entry_px,
                        "exit_px": exit_px,
                        "pnl": float(pnl) if pd.notna(pnl) else "",
                        "entry_uid": entry_uid,
                        "exit_uid": exit_uid,
                        "source": src,
                        "note": note,
                    }
                )

                lot["qty"] = float(lot["qty"]) - match_qty
                remaining -= match_qty

                if float(lot["qty"]) <= 1e-12:
                    lots.pop(0)

            if remaining > 1e-12:
                lots.append({"side": exit_side, "qty": remaining, "px": exit_px, "dt": exit_dt, "uid": exit_uid})

    return pd.DataFrame(trips) if trips else pd.DataFrame()


def sync_round_trips_to_sheet(dry_run: bool = False) -> dict:
    fills_df = load_sheet_df("broker_fills")
    if fills_df.empty:
        return {"added": 0, "skipped": 0, "error": None, "msg": "broker_fills 無資料"}

    trips_df = build_round_trips_from_fills(fills_df)
    if trips_df.empty:
        return {"added": 0, "skipped": 0, "error": None, "msg": "沒有可配對的 round_trips"}

    trades_df = load_trades()
    strategy_map: Dict[str, str] = {}
    if (not trades_df.empty) and ("source" in trades_df.columns) and ("策略" in trades_df.columns):
        t = trades_df[["source", "策略"]].copy()
        t["source"] = t["source"].astype(str).fillna("").str.strip()
        t["策略"] = t["策略"].astype(str).fillna("").str.strip()
        t = t[t["source"] != ""].drop_duplicates(subset=["source"], keep="first")
        strategy_map = dict(zip(t["source"].tolist(), t["策略"].tolist()))

    def _pick_strategy(entry_uid: str, exit_uid: str) -> str:
        s = ""
        if entry_uid:
            s = strategy_map.get(str(entry_uid).strip(), "")
        if (not s) and exit_uid:
            s = strategy_map.get(str(exit_uid).strip(), "")
        return s

    trips_df = trips_df.copy()
    trips_df["entry_uid"] = trips_df["entry_uid"].astype(str).fillna("").str.strip()
    trips_df["exit_uid"] = trips_df["exit_uid"].astype(str).fillna("").str.strip()
    trips_df["strategy"] = trips_df.apply(lambda r: _pick_strategy(r["entry_uid"], r["exit_uid"]), axis=1)

    sh = get_sheet("round_trips")
    header = [h.strip() for h in sh.row_values(1)]
    if "source" not in header:
        return {"added": 0, "skipped": 0, "error": "round_trips 分頁缺少 source 欄位（去重用）", "msg": ""}

    existing_sources = set()
    try:
        exist = sh.get_all_records()
        if exist:
            df0 = _clean_columns(pd.DataFrame(exist))
            if "source" in df0.columns:
                existing_sources = set(df0["source"].astype(str).fillna("").str.strip().tolist())
    except Exception:
        existing_sources = set()

    def _row_dict(r) -> dict:
        return {
            "entry_time": str(r.get("entry_time", "")).strip(),
            "exit_time": str(r.get("exit_time", "")).strip(),
            "broker": str(r.get("broker", "")).strip(),
            "symbol": str(r.get("symbol", "")).strip(),
            "currency": str(r.get("currency", "")).strip(),
            "direction": str(r.get("direction", "")).strip(),
            "qty": r.get("qty", ""),
            "entry_px": r.get("entry_px", ""),
            "exit_px": r.get("exit_px", ""),
            "pnl": r.get("pnl", ""),
            "strategy": str(r.get("strategy", "")).strip(),
            "entry_uid": str(r.get("entry_uid", "")).strip(),
            "exit_uid": str(r.get("exit_uid", "")).strip(),
            "source": str(r.get("source", "")).strip(),
            "note": str(r.get("note", "")).strip(),
        }

    rows_to_append: List[List[Any]] = []
    added, skipped = 0, 0

    for _, r in trips_df.iterrows():
        src = str(r.get("source", "")).strip()
        if (not src) or (src in existing_sources):
            skipped += 1
            continue
        rd = _row_dict(r)
        ordered = [rd.get(h, "") for h in header]
        rows_to_append.append(ordered)
        existing_sources.add(src)
        added += 1

    if dry_run:
        return {"added": added, "skipped": skipped, "error": None, "msg": f"dry_run: will append {added}"}

    try:
        if rows_to_append:
            sh.append_rows(rows_to_append, value_input_option="USER_ENTERED")
        return {"added": added, "skipped": skipped, "error": None, "msg": "round_trips 寫入完成"}
    except Exception as e:
        return {"added": 0, "skipped": skipped, "error": str(e), "msg": ""}


# ============================================================
# 4) ✅ IB：Snapshot / Field（寫入 broker_snapshot）
# ============================================================
def sync_ib_positions_to_broker_snapshot(dry_run: bool = False) -> dict:
    if not HAS_IB_API:
        return {"added": 0, "skipped": 0, "error": "IB API 不可用（未設定或匯入失敗）", "msg": ""}

    sh = get_sheet("broker_snapshot")
    if sh is None:
        return {"added": 0, "skipped": 0, "error": "無法連線至 Google Sheets (SSL/網路問題)", "msg": ""}
    header = [h.strip() for h in sh.row_values(1)]

    acct_cols = {"時間", "券商", "帳戶總資產", "可用現金", "含融資權益", "currency"}
    pos_cols = {"時間", "券商", "symbol", "secType", "exchange", "currency", "position", "avgCost"}

    is_account_schema = acct_cols.issubset(set(header))
    is_position_schema = pos_cols.issubset(set(header))

    if (not is_account_schema) and (not is_position_schema):
        return {
            "added": 0,
            "skipped": 0,
            "error": (
                "broker_snapshot 欄位格式無法辨識。\n"
                f"目前欄位：{header}\n"
                "請用『帳戶摘要』或『持倉快照』其中一種欄位格式。"
            ),
            "msg": "",
        }

    has_note = "備註" in header
    existing_notes = set()
    if has_note:
        try:
            exist = sh.get_all_records()
            if exist:
                df0 = _clean_columns(pd.DataFrame(exist))
                if "備註" in df0.columns:
                    existing_notes = set(df0["備註"].astype(str).fillna("").tolist())
        except Exception:
            existing_notes = set()

    now = datetime.now()
    asof_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # ---- Account schema
    if is_account_schema:
        try:
            snap = get_account_snapshot()
        except Exception as e:
            return {"added": 0, "skipped": 0, "error": str(e), "msg": "get_account_snapshot 失敗"}

        uid = f"IBACCT|{asof_str}"
        note = f"[uid]{uid} account_snapshot"

        if has_note and any(uid in n for n in existing_notes):
            return {"added": 0, "skipped": 1, "error": None, "msg": "已存在同一筆帳戶快照（uid 去重）"}

        row = {
            "時間": asof_str,
            "券商": "IBKR",
            "帳戶總資產": getattr(snap, "net_liquidation", ""),
            "可用現金": getattr(snap, "total_cash_value", ""),
            "含融資權益": getattr(snap, "equity_with_loan", ""),
            "currency": getattr(snap, "currency", "USD"),
        }
        if "換算台幣" in header:
            row["換算台幣"] = ""
        if has_note:
            row["備註"] = note

        ordered = [row.get(h, "") for h in header]

        if dry_run:
            return {"added": 1, "skipped": 0, "error": None, "msg": "dry_run: will append 1 account snapshot"}

        try:
            sh.append_row(ordered, value_input_option="USER_ENTERED")
            return {"added": 1, "skipped": 0, "error": None, "msg": "同步 IB 帳戶摘要到 broker_snapshot 完成"}
        except Exception as e:
            return {"added": 0, "skipped": 0, "error": str(e), "msg": ""}

    # ---- Positions schema
    try:
        positions = get_open_positions()
    except Exception as e:
        return {"added": 0, "skipped": 0, "error": str(e), "msg": "get_open_positions 失敗"}

    if not positions:
        return {"added": 0, "skipped": 0, "error": None, "msg": "目前沒有持倉（positions 空）"}

    asof_min = now.strftime("%Y-%m-%d %H:%M:00")

    rows_to_append: List[List[Any]] = []
    added, skipped = 0, 0

    for p in positions:
        d = p if isinstance(p, dict) else p.__dict__

        broker = str(d.get("broker", d.get("account", "IBKR"))).strip() or "IBKR"
        symbol = str(d.get("symbol", "")).strip()
        if not symbol:
            continue

        currency = str(d.get("currency", "USD")).strip() or "USD"
        secType = str(d.get("secType", d.get("sectype", "STK"))).strip() or "STK"
        exchange = str(d.get("exchange", d.get("primaryExchange", ""))).strip()

        position = d.get("position", d.get("qty", d.get("quantity", 0)))
        avgCost = d.get("avgCost", d.get("avg_cost", d.get("averageCost", "")))

        try:
            position_n = float(position)
        except Exception:
            continue
        if abs(position_n) < 1e-12:
            continue

        try:
            avgCost_n = float(avgCost) if avgCost not in ("", None) else ""
        except Exception:
            avgCost_n = ""

        uid = f"IBPOS|{broker}|{asof_min}|{symbol}|{currency}"
        note = f"[uid]{uid} position_snapshot"

        if has_note and any(uid in n for n in existing_notes):
            skipped += 1
            continue

        row = {
            "時間": asof_min,
            "券商": broker,
            "symbol": symbol,
            "secType": secType,
            "exchange": exchange,
            "currency": currency,
            "position": position_n,
            "avgCost": avgCost_n,
        }
        if has_note:
            row["備註"] = note

        ordered = [row.get(h, "") for h in header]
        rows_to_append.append(ordered)
        if has_note:
            existing_notes.add(note)
        added += 1

    if dry_run:
        return {"added": added, "skipped": skipped, "error": None, "msg": f"dry_run: will append {added} position rows"}

    try:
        if rows_to_append:
            sh.append_rows(rows_to_append, value_input_option="USER_ENTERED")
        return {"added": added, "skipped": skipped, "error": None, "msg": "同步 IB 持倉快照到 broker_snapshot 完成"}
    except Exception as e:
        return {"added": 0, "skipped": skipped, "error": str(e), "msg": ""}

def sync_ib_positions_to_broker_positions(dry_run: bool = False) -> dict:
    """
    ✅ 專門把 IB Open Positions 寫入 Google Sheets 的 broker_positions

    新增規則：
    - 如果同 (券商, symbol, currency) 的「position + avgCost」與最後一筆完全相同 → 不寫入（skip）

    預期 broker_positions 表頭至少包含：
    時間, 券商, symbol, secType, exchange, currency, position, avgCost
    """
    if not HAS_IB_API:
        return {"added": 0, "skipped": 0, "error": "IB API 不可用（未設定或匯入失敗）", "msg": ""}

    sh = get_sheet("broker_positions")
    header = [h.strip() for h in sh.row_values(1)]
    required = ["時間", "券商", "symbol", "secType", "exchange", "currency", "position", "avgCost"]
    missing = [c for c in required if c not in header]
    if missing:
        return {
            "added": 0,
            "skipped": 0,
            "error": f"broker_positions 缺少欄位：{missing}（請先補齊表頭）",
            "msg": "",
        }

    # ------------------------------------------------------------
    # 1) 讀取現有 broker_positions：建立「最後狀態」map
    #    key = (券商, symbol, currency) -> (last_position, last_avgCost)
    # ------------------------------------------------------------
    last_state: Dict[Tuple[str, str, str], Tuple[float, float]] = {}
    try:
        exist = sh.get_all_records()
        if exist:
            df0 = _clean_columns(pd.DataFrame(exist))
            # 保底欄位
            for c in ["時間", "券商", "symbol", "currency", "position", "avgCost"]:
                if c not in df0.columns:
                    df0[c] = ""

            df0["時間_dt"] = pd.to_datetime(df0["時間"], errors="coerce")
            df0["券商"] = df0["券商"].astype(str).str.strip()
            df0["symbol"] = df0["symbol"].astype(str).str.strip()
            df0["currency"] = df0["currency"].astype(str).str.strip()

            df0["position_n"] = pd.to_numeric(df0["position"], errors="coerce")
            df0["avgCost_n"] = pd.to_numeric(df0["avgCost"], errors="coerce")

            df0 = df0.dropna(subset=["時間_dt"])
            # 只留下有 key 的
            df0 = df0[(df0["券商"] != "") & (df0["symbol"] != "") & (df0["currency"] != "")]
            if not df0.empty:
                df0 = df0.sort_values("時間_dt")
                # 每個 key 取最後一筆
                for (b, s, c), g in df0.groupby(["券商", "symbol", "currency"], dropna=False):
                    last = g.iloc[-1]
                    pos = float(last["position_n"]) if pd.notna(last["position_n"]) else 0.0
                    ac = float(last["avgCost_n"]) if pd.notna(last["avgCost_n"]) else 0.0
                    last_state[(str(b).strip(), str(s).strip(), str(c).strip())] = (pos, ac)
    except Exception:
        # 讀不到就當作沒有歷史資料
        last_state = {}

    # ------------------------------------------------------------
    # 2) 拉 IB open positions
    # ------------------------------------------------------------
    try:
        positions = get_open_positions()
    except Exception as e:
        return {"added": 0, "skipped": 0, "error": str(e), "msg": "get_open_positions 失敗"}

    if not positions:
        return {"added": 0, "skipped": 0, "error": None, "msg": "目前沒有持倉（positions 空）"}

    now = datetime.now()
    asof_min = now.strftime("%Y-%m-%d %H:%M:00")  # 用分鐘級避免過度密集

    rows_to_append: List[List[Any]] = []
    added = skipped = 0

    # float 比較容忍（避免 625.145 vs 625.1450000001）
    EPS = 1e-9

    def _same(a: float, b: float) -> bool:
        try:
            return abs(float(a) - float(b)) <= EPS
        except Exception:
            return False

    for p in positions:
        d = p if isinstance(p, dict) else p.__dict__

        broker = str(d.get("broker", d.get("account", "IBKR"))).strip() or "IBKR"
        symbol = str(d.get("symbol", "")).strip()
        if not symbol:
            continue

        currency = str(d.get("currency", "USD")).strip() or "USD"
        secType = str(d.get("secType", d.get("sectype", "STK"))).strip() or "STK"
        exchange = str(d.get("exchange", d.get("primaryExchange", ""))).strip()

        position = d.get("position", d.get("qty", d.get("quantity", 0)))
        avgCost = d.get("avgCost", d.get("avg_cost", d.get("averageCost", "")))

        try:
            position_n = float(position)
        except Exception:
            continue
        if abs(position_n) < 1e-12:
            continue

        try:
            avgCost_n = float(avgCost) if avgCost not in ("", None) else 0.0
        except Exception:
            avgCost_n = 0.0

        # ✅ 新增：若 position + avgCost 與最後一筆相同 → skip
        k = (broker, symbol, currency)
        if k in last_state:
            last_pos, last_ac = last_state[k]
            if _same(position_n, last_pos) and _same(avgCost_n, last_ac):
                skipped += 1
                continue

        row = {
            "時間": asof_min,
            "券商": broker,
            "symbol": symbol,
            "secType": secType,
            "exchange": exchange,
            "currency": currency,
            "position": position_n,
            "avgCost": avgCost_n,
        }

        ordered = [row.get(h, "") for h in header]
        rows_to_append.append(ordered)
        added += 1

        # 更新 last_state，避免同一輪 positions 內重複（理論上不會，但保險）
        last_state[k] = (position_n, avgCost_n)

    if dry_run:
        return {"added": added, "skipped": skipped, "error": None, "msg": f"dry_run: will append {added} rows"}

    try:
        if rows_to_append:
            sh.append_rows(rows_to_append, value_input_option="USER_ENTERED")
        return {"added": added, "skipped": skipped, "error": None, "msg": "同步 IB 持倉 → broker_positions 完成（相同部位/均價已去重）"}
    except Exception as e:
        return {"added": 0, "skipped": skipped, "error": str(e), "msg": "寫入 broker_positions 失敗"}


def sync_ib_executions_to_broker_fills(dry_run: bool = False, days: int = 7) -> dict:
    """
    ✅ 同步 IB 成交紀錄 (Executions) 到 broker_fills
    欄位：時間, 券商, symbol, side, shares, price, currency, orderId
    """
    if not HAS_IB_API:
        return {"added": 0, "skipped": 0, "error": "IB API 不可用", "msg": ""}

    sh = get_sheet("broker_fills")
    header = [h.strip() for h in sh.row_values(1)]
    required = ["時間", "券商", "symbol", "side", "shares", "price", "currency", "orderId"]
    missing = [c for c in required if c not in header]
    if missing:
        return {"added": 0, "skipped": 0, "error": f"broker_fills 缺少欄位: {missing}", "msg": ""}

    # 1) 讀取現有 executions (用 orderId 或 fill_uid 去重)
    existing_ids = set()
    try:
        exist = sh.get_all_records()
        if exist:
            df0 = _clean_columns(pd.DataFrame(exist))
            # 優先用 orderId 去重
            if "orderId" in df0.columns:
                existing_ids = set(df0["orderId"].astype(str).str.strip().tolist())
    except Exception:
        pass

    # 2) Get IB Executions
    try:
        execs = get_executions(days=days)
    except Exception as e:
        return {"added": 0, "skipped": 0, "error": str(e), "msg": "get_executions 失敗"}

    if not execs:
        return {"added": 0, "skipped": 0, "error": None, "msg": "無新成交紀錄"}

    rows_to_append: List[List[Any]] = []
    added = skipped = 0

    for e in execs:
        # e is dict: execId, time, symbol, secType, exchange, currency, side, shares, price, permId, orderId
        oid = str(e.get("orderId", "")).strip()
        # 若 orderId 為空，改用 execId 或其他組合
        if not oid:
            oid = str(e.get("execId", "")).strip()
        
        if oid in existing_ids:
            skipped += 1
            continue
        
        # 轉換 side: BOT/SLD -> BUY/SELL (ib_api 應該已經回傳 BUY/SELL or BOT/SLD)
        # 這裡為了保險再轉一次
        raw_side = str(e.get("side", "")).upper()
        if raw_side in ["BOT", "B", "BUY"]:
            side = "BUY"
        elif raw_side in ["SLD", "S", "SELL"]:
            side = "SELL"
        else:
            side = raw_side

        row = {
            "時間": e.get("time", ""),
            "券商": "IBKR",
            "symbol": e.get("symbol", ""),
            "side": side,
            "shares": e.get("shares", 0),
            "price": e.get("price", 0),
            "currency": e.get("currency", "USD"),
            "orderId": oid,
        }
        
        ordered = [row.get(h, "") for h in header]
        rows_to_append.append(ordered)
        existing_ids.add(oid)
        added += 1

    if dry_run:
        return {"added": added, "skipped": skipped, "error": None, "msg": f"dry_run: will append {added} fills"}

    try:
        if rows_to_append:
            sh.append_rows(rows_to_append, value_input_option="USER_ENTERED")
        return {"added": added, "skipped": skipped, "error": None, "msg": "同步 IB Fills 完成"}
    except Exception as e:
        return {"added": 0, "skipped": skipped, "error": str(e), "msg": "寫入 broker_fills 失敗"}

# ============================================================
# ✅ 4.x) SCHWAB：Account / Positions（stub + guard）
# ============================================================
def sync_schwab_account_to_broker_snapshot(dry_run: bool = False) -> dict:
    """
    寫入 broker_snapshot：帳戶摘要（類似 IB Field）
    目前：未啟用就直接回報，避免噴錯。
    """
    if (not HAS_SCHWAB_API) or (not is_schwab_enabled()):
        return {"added": 0, "skipped": 0, "error": None, "msg": "SCHWAB 未啟用（API 審核中或未完成 OAuth）"}

    # TODO: 審核通過後改成真的 API call
    try:
        _ = get_schwab_accounts()
    except Exception as e:
        return {"added": 0, "skipped": 0, "error": str(e), "msg": "get_schwab_accounts 失敗（尚未實作）"}

    return {"added": 0, "skipped": 0, "error": "Schwab accounts mapping 尚未實作", "msg": ""}


def sync_schwab_positions_to_broker_positions(dry_run: bool = False) -> dict:
    """
    寫入 broker_positions：持倉快照（類似 IB Snapshot/positions）
    目前：未啟用就直接回報，避免噴錯。
    """
    if (not HAS_SCHWAB_API) or (not is_schwab_enabled()):
        return {"added": 0, "skipped": 0, "error": None, "msg": "SCHWAB 未啟用（API 審核中或未完成 OAuth）"}

    # TODO: 審核通過後改成真的 API call
    try:
        _ = get_schwab_open_positions()
    except Exception as e:
        return {"added": 0, "skipped": 0, "error": str(e), "msg": "get_schwab_open_positions 失敗（尚未實作）"}

    return {"added": 0, "skipped": 0, "error": "Schwab positions mapping 尚未實作", "msg": ""}


def sync_yuanta_positions_to_broker_positions(raw_list: List[str]) -> dict:
    """
    ✅ 解析元大 0015 庫存字串並寫入 broker_positions
    """
    if not raw_list:
        return {"added": 0, "skipped": 0, "error": None, "msg": "沒有原始資料可解析"}

    try:
        sh = get_sheet("broker_positions")
        if sh is None:
            return {"added": 0, "skipped": 0, "error": "無法連線至 Google Sheets (SSL/網路問題)", "msg": ""}
        header = [h.strip() for h in sh.row_values(1)]
    except Exception as e:
        return {"added": 0, "skipped": 0, "error": f"開啟 broker_positions 失敗: {e}", "msg": ""}

    rows_to_append = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for raw in raw_list:
        if not raw or "尚未登入" in raw:
            continue
        # yuanta_api.py 回傳格式：0,0,0,0,{stk_code},0,{stk_nos},{stk_price},{stk_cost_raw}
        parts = [p.strip() for p in raw.replace(";", ",").split(",")]
        if len(parts) < 7:
            continue

        symbol = parts[4]   # 股票代碼在 index 4
        try:
            qty = float(parts[6])  # 股數在 index 6
        except (ValueError, IndexError):
            continue

        if qty <= 0:
            continue

        # avgCost: 優先用均價欄位 (parts[7] = stk_price_raw/100，e.g. 151.68)
        # 若均價為 0，fallback 用 成本raw ÷ 股數（parts[8] / qty）
        try:
            avg_price = float(parts[7]) if len(parts) > 7 else 0.0
        except (ValueError, IndexError):
            avg_price = 0.0

        stk_cost_raw_val = 0.0
        try:
            stk_cost_raw_val = float(parts[8]) if len(parts) > 8 else 0.0
        except (ValueError, IndexError):
            stk_cost_raw_val = 0.0

        if avg_price > 0:
            avg_cost = avg_price
        elif stk_cost_raw_val > 0 and qty > 0:
            avg_cost = stk_cost_raw_val / qty  # 成本raw ÷ 股數
        else:
            avg_cost = 0.0

        row = {
            "時間": now_str,
            "券商": "YUANTA",
            "symbol": f"'{symbol}" if str(symbol).isdigit() else symbol,
            "secType": "STK",
            "exchange": "TWSE",
            "currency": "TWD",
            "position": qty,
            "avgCost": avg_cost,
            "備註": f"均價={avg_price} 成本raw={stk_cost_raw_val:.0f} | RAW:{raw}",
        }
        ordered = [row.get(h, "") for h in header]
        rows_to_append.append(ordered)

    if rows_to_append:
        try:
            sh.append_rows(rows_to_append, value_input_option="USER_ENTERED")
            return {
                "added": len(rows_to_append),
                "skipped": 0,
                "error": None,
                "msg": f"成功從元大資料中同步 {len(rows_to_append)} 筆持倉",
            }
        except Exception as e:
            return {"added": 0, "skipped": 0, "error": f"寫入失敗: {e}", "msg": ""}

    return {"added": 0, "skipped": 0, "error": None, "msg": "未在回傳字串中發現有效持倉數據"}


# ============================================================
# 5) ✅ Daily NAV REAL：sync_daily_nav_real_per_strategy
# ============================================================
def _get_sheet_all_values(sh) -> List[List[str]]:
    try:
        return sh.get_all_values()
    except Exception:
        recs = sh.get_all_records()
        if not recs:
            return []
        header = list(recs[0].keys())
        values = [header]
        for r in recs:
            values.append([str(r.get(h, "")) for h in header])
        return values


def _to_date_str(x) -> str:
    dt = pd.to_datetime(x, errors="coerce")
    if pd.isna(dt):
        return ""
    return dt.strftime("%Y-%m-%d")


def _safe_num(x, default=0.0) -> float:
    try:
        v = float(pd.to_numeric(x, errors="coerce"))
        if np.isnan(v):
            return float(default)
        return float(v)
    except Exception:
        return float(default)


def sync_daily_nav_real_per_strategy(dry_run: bool = False, days_back: int = 365, mode: str = "REAL") -> dict:
    """
    ✅ 每策略每天 1 筆寫入 daily_nav
    REAL value = 起始資金 + 已實現累積(round_trips) + 未實現(broker_positions; 不足則 0)

    寫入欄位（若 daily_nav 表頭存在就填）：
    日期, 策略, mode, value, NAV, 日報酬, 累積報酬, realized_pnl, unrealized_pnl, position_value, 備註
    """
    if not SHEETS_OK:
        return {"added": 0, "updated": 0, "skipped": 0, "error": SHEETS_ERR}

    try:
        strategies_df = load_strategies()
        if strategies_df is None or strategies_df.empty:
            return {"added": 0, "updated": 0, "skipped": 0, "error": "strategies 無資料"}

        for c in ["策略名稱", "起始資金", "狀態"]:
            if c not in strategies_df.columns:
                strategies_df[c] = ""

        strategies_df = strategies_df.copy()
        strategies_df["策略名稱"] = strategies_df["策略名稱"].astype(str).str.strip()
        strategies_df["起始資金"] = pd.to_numeric(strategies_df["起始資金"], errors="coerce").fillna(0.0)
        strategies_df["狀態"] = strategies_df["狀態"].astype(str).str.strip()

        strat_pool = strategies_df[strategies_df["狀態"].eq("運行中")].copy()
        if strat_pool.empty:
            strat_pool = strategies_df.copy()

        strat_names = sorted(strat_pool["策略名稱"].dropna().astype(str).unique().tolist())
        if not strat_names:
            return {"added": 0, "updated": 0, "skipped": 0, "error": "strategies 找不到策略名稱"}

        start_cap_map = dict(zip(strat_pool["策略名稱"].tolist(), strat_pool["起始資金"].astype(float).tolist()))

        end_dt = pd.Timestamp(datetime.now().date())
        start_dt = end_dt - pd.Timedelta(days=int(days_back))
        date_index = pd.date_range(start=start_dt, end=end_dt, freq="D")

        # 1) & 2) 並行讀取已實現與未實現資料
        with ThreadPoolExecutor(max_workers=3) as executor:
            f_rt = executor.submit(load_sheet_df, "round_trips")
            f_bp = executor.submit(load_sheet_df, "broker_positions")
            rt_df = f_rt.result()
            bp_df = f_bp.result()

        realized_daily = pd.DataFrame({"日期": [], "策略": [], "realized_pnl": []})

        if rt_df is not None and (not rt_df.empty):
            strat_col = "strategy" if "strategy" in rt_df.columns else ("策略" if "策略" in rt_df.columns else None)
            time_col = "exit_time" if "exit_time" in rt_df.columns else ("出場時間" if "出場時間" in rt_df.columns else None)
            pnl_col = "pnl" if "pnl" in rt_df.columns else ("已實現損益" if "已實現損益" in rt_df.columns else None)

            if strat_col and time_col and pnl_col:
                tmp = rt_df[[strat_col, time_col, pnl_col]].copy()
                tmp.rename(columns={strat_col: "策略", time_col: "exit_time", pnl_col: "pnl"}, inplace=True)
                tmp["策略"] = tmp["策略"].astype(str).str.strip()
                tmp["exit_dt"] = pd.to_datetime(tmp["exit_time"], errors="coerce")
                tmp["日期"] = tmp["exit_dt"].dt.strftime("%Y-%m-%d")
                tmp["pnl"] = pd.to_numeric(tmp["pnl"], errors="coerce").fillna(0.0)
                tmp = tmp.dropna(subset=["exit_dt"])
                tmp = tmp[tmp["策略"].isin(strat_names)]
                realized_daily = tmp.groupby(["日期", "策略"], as_index=False)["pnl"].sum()
                realized_daily.rename(columns={"pnl": "realized_pnl"}, inplace=True)

        realized_pivot = realized_daily.pivot_table(index="日期", columns="策略", values="realized_pnl", aggfunc="sum").fillna(0.0)
        realized_pivot = realized_pivot.reindex([d.strftime("%Y-%m-%d") for d in date_index], fill_value=0.0)
        realized_cum = realized_pivot.cumsum()

        # 2) 未實現：已於上方並行讀取
        unreal_daily = pd.DataFrame(index=[d.strftime("%Y-%m-%d") for d in date_index], columns=strat_names, data=0.0)
        posval_daily = pd.DataFrame(index=[d.strftime("%Y-%m-%d") for d in date_index], columns=strat_names, data=0.0)

        if bp_df is not None and (not bp_df.empty):
            strat_col = "策略" if "策略" in bp_df.columns else ("strategy" if "strategy" in bp_df.columns else None)
            time_col = "日期" if "日期" in bp_df.columns else ("時間" if "時間" in bp_df.columns else None)

            unreal_col = None
            for cand in ["unrealized_pnl", "未實現損益", "unrealized", "UnrealizedPnL"]:
                if cand in bp_df.columns:
                    unreal_col = cand
                    break

            posval_col = None
            for cand in ["position_value", "持倉市值", "market_value", "MarketValue"]:
                if cand in bp_df.columns:
                    posval_col = cand
                    break

            if strat_col and time_col:
                tmp = bp_df.copy()
                tmp[strat_col] = tmp[strat_col].astype(str).str.strip()
                tmp["日期"] = tmp[time_col].apply(_to_date_str)
                tmp = tmp[tmp[strat_col].isin(strat_names)]
                tmp = tmp[tmp["日期"] != ""]

                if unreal_col:
                    tmp["unreal"] = pd.to_numeric(tmp[unreal_col], errors="coerce").fillna(0.0)
                    u = tmp.groupby(["日期", strat_col], as_index=False)["unreal"].sum()
                    u.rename(columns={strat_col: "策略"}, inplace=True)
                    u_piv = u.pivot_table(index="日期", columns="策略", values="unreal", aggfunc="sum").fillna(0.0)
                    unreal_daily.loc[u_piv.index, u_piv.columns] = u_piv

                if posval_col:
                    tmp["posval"] = pd.to_numeric(tmp[posval_col], errors="coerce").fillna(0.0)
                    p = tmp.groupby(["日期", strat_col], as_index=False)["posval"].sum()
                    p.rename(columns={strat_col: "策略"}, inplace=True)
                    p_piv = p.pivot_table(index="日期", columns="策略", values="posval", aggfunc="sum").fillna(0.0)
                    posval_daily.loc[p_piv.index, p_piv.columns] = p_piv

        # 3) 組合 daily_nav rows（每策略每天一筆）
        rows: List[Dict[str, Any]] = []
        for strat in strat_names:
            cap0 = float(start_cap_map.get(strat, 0.0))
            nav_series = []

            for d in [x.strftime("%Y-%m-%d") for x in date_index]:
                rc = float(realized_cum.loc[d, strat]) if (d in realized_cum.index and strat in realized_cum.columns) else 0.0
                un = float(unreal_daily.loc[d, strat]) if (d in unreal_daily.index and strat in unreal_daily.columns) else 0.0
                pv = float(posval_daily.loc[d, strat]) if (d in posval_daily.index and strat in posval_daily.columns) else 0.0

                value = cap0 + rc + un
                nav = (value / cap0) if cap0 else np.nan
                nav_series.append(nav)

                # 取得該策略的基本資訊
                s_info = strat_pool[strat_pool["策略名稱"] == strat].iloc[0] if strat in strat_pool["策略名稱"].values else {}
                
                rows.append(
                    {
                        "日期": d,
                        "策略": strat,
                        "幣別": s_info.get("幣別", s_info.get("幣別(USD/TWD)", "TWD")),
                        "起始資金": cap0,
                        "value": float(value) if np.isfinite(value) else "",
                        "NAV": float(nav) if np.isfinite(nav) else "",
                        "realized_pnl": float(rc) if np.isfinite(rc) else 0.0,
                        "unrealized_pnl": float(un) if np.isfinite(un) else 0.0,
                        "cash": float(value - pv) if np.isfinite(value - pv) else 0.0,
                        "position_value": float(pv) if np.isfinite(pv) else 0.0,
                        "broker": s_info.get("券商", ""),
                        "account": s_info.get("帳號", ""),
                        "mode": str(mode).strip(),
                        "source": "Streamlit_Sync",
                        "備註": f"REAL: cap0={cap0}",
                        "更新時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                )

            nav_s = pd.Series(nav_series, index=[x.strftime("%Y-%m-%d") for x in date_index], dtype=float)
            day_ret = nav_s.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)
            cum_ret = (nav_s - 1.0).replace([np.inf, -np.inf], np.nan)

            for i, d in enumerate([x.strftime("%Y-%m-%d") for x in date_index]):
                idx = i + (len(date_index) * strat_names.index(strat))
                rows[idx]["日報酬"] = float(day_ret.loc[d]) if np.isfinite(day_ret.loc[d]) else 0.0
                rows[idx]["累積報酬"] = float(cum_ret.loc[d]) if np.isfinite(cum_ret.loc[d]) else ""

        out_df = pd.DataFrame(rows)

        # 4) Upsert 寫回 daily_nav（key = 日期 + 策略 + mode）
        sh = get_sheet("daily_nav_strategy")
        if sh is None:
            return {"added": 0, "updated": 0, "skipped": 0, "error": "無法連線至 Google Sheets (SSL/網路問題)"}
        values = _get_sheet_all_values(sh)
        if not values:
            return {"added": 0, "updated": 0, "skipped": 0, "error": "daily_nav 工作表是空的（需要先有表頭）"}

        header = [h.strip() for h in values[0]]
        if not header:
            return {"added": 0, "updated": 0, "skipped": 0, "error": "daily_nav 表頭為空"}

        key_to_row: Dict[Tuple[str, str, str], int] = {}
        for i in range(1, len(values)):
            row = values[i]
            row_dict = {header[j]: (row[j] if j < len(row) else "") for j in range(len(header))}
            k = (str(row_dict.get("日期", "")).strip(), str(row_dict.get("策略", "")).strip(), str(row_dict.get("mode", "")).strip())
            if k[0] and k[1] and k[2]:
                key_to_row[k] = i + 1

        def _to_ordered_row(rec: Dict[str, Any]) -> List[Any]:
            return [rec.get(h, "") for h in header]

        to_append: List[List[Any]] = []
        updates: List[Tuple[int, List[Any]]] = []
        added = updated = skipped = 0

        for _, r in out_df.iterrows():
            k = (str(r.get("日期", "")).strip(), str(r.get("策略", "")).strip(), str(r.get("mode", "")).strip())
            if not (k[0] and k[1] and k[2]):
                skipped += 1
                continue

            rec = dict(r)
            ordered = _to_ordered_row(rec)

            if k in key_to_row:
                updates.append((key_to_row[k], ordered))
                updated += 1
            else:
                to_append.append(ordered)
                added += 1

        if dry_run:
            return {"added": added, "updated": updated, "skipped": skipped, "error": None, "msg": f"dry_run: will append {added}, update {updated}"}

        try:
            if to_append:
                sh.append_rows(to_append, value_input_option="USER_ENTERED")

            if updates:
                last_col_letter = _col_to_letter(len(header))
                # 優化：改用 batch_update 減少 API 請求次數
                batch_data = []
                for row_idx, row_vals in updates:
                    rng = f"A{row_idx}:{last_col_letter}{row_idx}"
                    batch_data.append({
                        'range': rng,
                        'values': [row_vals]
                    })
                
                if batch_data:
                    sh.batch_update(batch_data, value_input_option="USER_ENTERED")

            return {"added": added, "updated": updated, "skipped": skipped, "error": None, "msg": "daily_nav REAL upsert 完成"}
        except Exception as e:
            return {"added": 0, "updated": 0, "skipped": skipped, "error": str(e), "msg": "寫入 daily_nav 失敗"}

    except Exception as e:
        return {"added": 0, "updated": 0, "skipped": 0, "error": str(e)}


# ============================================================
# 6) Dashboard 計算：Portfolio / MDD / Real vs Unreal
# ============================================================
def _calc_mdd(series: pd.Series) -> float:
    if series is None or len(series) == 0:
        return 0.0
    s = series.astype(float)
    roll_max = s.cummax()
    dd = s / roll_max - 1.0
    return float(dd.min())


def _build_portfolio_from_nav(nav_df: pd.DataFrame, strategies_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    merged = nav_df.merge(
        strategies_df[["策略名稱", "起始資金"]],
        left_on="策略",
        right_on="策略名稱",
        how="left",
        suffixes=("_x", "_y"),
    )

    merged = _coalesce_columns(merged, "起始資金", prefer="y")

    if "起始資金" not in merged.columns:
        merged["起始資金"] = 0.0

    merged["起始資金"] = pd.to_numeric(merged["起始資金"], errors="coerce").fillna(0.0)
    merged["NAV"] = pd.to_numeric(merged["NAV"], errors="coerce")
    merged["市值"] = merged["NAV"] * merged["起始資金"]
    pv = merged.groupby("日期_dt")["市值"].sum().sort_index()
    return merged, pv


def _build_real_unreal_curves(nav_df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    if nav_df is None or nav_df.empty:
        return pd.Series(dtype=float), pd.Series(dtype=float)

    df = nav_df.copy()
    df["realized_pnl"] = pd.to_numeric(df.get("realized_pnl", 0), errors="coerce").fillna(0.0)
    df["unrealized_pnl"] = pd.to_numeric(df.get("unrealized_pnl", 0), errors="coerce").fillna(0.0)

    realized = df.groupby("日期_dt")["realized_pnl"].sum().sort_index()
    unreal = df.groupby("日期_dt")["unrealized_pnl"].sum().sort_index()
    return realized, unreal


# ============================================================
# 7) Sidebar 導航
# ============================================================
with st.sidebar:
    # 收合提示
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(91, 71, 217, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 12px;
        text-align: center;
        font-size: 12px;
        color: #6B7280;
    ">
        💡 點擊左上角 ≡ 收合此面板
    </div>
    """, unsafe_allow_html=True)

    st.title("📈 實盤管理")
    page = st.radio(
        "導航",
        ["🏠 Dashboard", "🔄 同步", "📝 交易原因", "💹 IB 即時監控"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Daily NAV REAL + 策略線 + Portfolio + MDD")
    st.caption("Timezone: Asia/Taipei")

    st.markdown("---")
    st.markdown("### ❄️ 離線模式設定")
    if "force_offline" not in st.session_state:
        st.session_state["force_offline"] = (os.getenv("DISABLE_SHEETS", "0") == "1")

    force_off = st.toggle("🧊 強制離線模式", value=st.session_state["force_offline"], 
                          help="開啟後將跳過 Google Sheets 直接讀取本地緩存。")
    if force_off != st.session_state["force_offline"]:
        st.session_state["force_offline"] = force_off
        os.environ["DISABLE_SHEETS"] = "1" if force_off else "0"
        import sheets_utils
        sheets_utils.DISABLE_SHEETS = force_off
        st.rerun()

    from sheets_utils import DISABLE_SHEETS
    if DISABLE_SHEETS:
        st.info("🔵 離線模式：使用緩存資料")
    else:
        st.success("🟢 在線模式：連線正常")

    st.markdown("---")
    st.markdown("### ⏱ 自動同步狀態")
    _last_ib_ts = st.session_state.get("last_ib_auto_sync", 0)
    _last_yu_ts = st.session_state.get("last_yuanta_auto_sync", 0)
    st.caption(f"IB 上次自動同步：{datetime.fromtimestamp(_last_ib_ts).strftime('%m/%d %H:%M') if _last_ib_ts else '尚未同步'}")
    st.caption(f"元大上次自動同步：{datetime.fromtimestamp(_last_yu_ts).strftime('%m/%d %H:%M') if _last_yu_ts else '尚未同步'}")
    st.caption("每 4 小時自動同步一次（需連線且已登入）")


# ============================================================
# 自動同步（每 4 小時，非離線模式且已連線時觸發）
# ============================================================
_AUTO_SYNC_INTERVAL = 4 * 3600  # 4 小時

if not st.session_state.get("force_offline", False):
    _now = time.time()

    # IB 自動同步
    if HAS_IB_API:
        if _now - st.session_state.get("last_ib_auto_sync", 0) > _AUTO_SYNC_INTERVAL:
            try:
                _res = sync_ib_positions_to_broker_positions()
                if not _res.get("error"):
                    st.session_state["last_ib_auto_sync"] = _now
                    st.toast("✅ IB 自動同步完成", icon="🔄")
            except Exception:
                pass

    # 元大：若尚未登入且 .env 有帳密，嘗試自動登入（每 session 只試一次）
    if HAS_YUANTA_API and "yuanta_api" not in st.session_state:
        if not st.session_state.get("yuanta_auto_login_attempted", False):
            _yu_acc = os.getenv("YUANTA_ACCOUNT", "").strip()
            _yu_pw = os.getenv("YUANTA_PASSWORD", "").strip()
            if _yu_acc and _yu_pw:
                try:
                    with st.spinner("🔐 元大 API 自動連線中..."):
                        _api = yuanta_login()
                        register_events(_api)
                        st.session_state["yuanta_api"] = _api
                except Exception:
                    pass
            st.session_state["yuanta_auto_login_attempted"] = True

    # 元大自動同步（需已登入）
    if "yuanta_api" in st.session_state:
        if _now - st.session_state.get("last_yuanta_auto_sync", 0) > _AUTO_SYNC_INTERVAL:
            try:
                if query_stock_positions(st.session_state["yuanta_api"]):
                    _pos = []
                    for _ in range(5):  # 最多等 5 秒讓 API 回傳
                        time.sleep(1)
                        _pos = fetch_positions(st.session_state["yuanta_api"])
                        if _pos:
                            break
                    if _pos:
                        _res = sync_yuanta_positions_to_broker_positions(_pos)
                        if not _res.get("error"):
                            st.session_state["last_yuanta_auto_sync"] = _now
                            st.toast("✅ 元大自動同步完成", icon="🔄")
            except Exception:
                pass


# ============================================================
# 8) 頁面：Dashboard
# ============================================================
if page == "🏠 Dashboard":
    st.markdown("## 📊 實盤績效儀表板")

    if not SHEETS_OK:
        st.error(SHEETS_ERR)
        st.stop()

    # 使用並行預載優化效能
    nav_df, strategies_df, _, _, _ = preload_dashboard_data()

    if strategies_df is None or strategies_df.empty:
        st.warning("⚠️ `strategies` 分頁目前沒有資料。")
        st.info("💡 **建議做法**：如果您的 Google Sheets 連網緩慢，請在左側邊欄開啟『**🧊 強制離線模式**』以使用本地緩存。")
        if st.button("🔄 重新載入數據", key="btn_reload_missing_strat"):
            st.rerun()
        st.stop()

    for c in ["策略名稱", "起始資金", "狀態"]:
        if c not in strategies_df.columns:
            strategies_df[c] = ""

    strategies_df = strategies_df.copy()
    strategies_df["策略名稱"] = strategies_df["策略名稱"].astype(str).str.strip()
    strategies_df["起始資金"] = pd.to_numeric(strategies_df["起始資金"], errors="coerce").fillna(0.0)
    strategies_df["狀態"] = strategies_df["狀態"].astype(str).str.strip()

    st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
    c0, c1, c2, c3 = st.columns([1.2, 1.2, 1.2, 1.4])
    with c0:
        active_only = st.toggle("只看運行中策略", value=True)
    with c1:
        mode_options = ["ALL"]
        if nav_df is not None and (not nav_df.empty) and ("mode" in nav_df.columns):
            mode_options += sorted(nav_df["mode"].astype(str).fillna("").replace("", "UNKNOWN").unique().tolist())
        sel_mode = st.selectbox("NAV 模式", options=mode_options, index=0)
    with c2:
        show_real_unreal = st.toggle("顯示已實現/未實現曲線", value=True)
    with c3:
        top_n = st.slider("概覽表顯示筆數", 5, 100, 30, 5)
    st.markdown("</div>", unsafe_allow_html=True)

    strat_pool = strategies_df.copy()
    if active_only:
        strat_pool = strat_pool[strat_pool["狀態"].eq("運行中")]
    strat_names = sorted(strat_pool["策略名稱"].dropna().astype(str).unique().tolist())

    if not strat_names:
        st.info("沒有可用策略（請確認 strategies 狀態=運行中）。")
        st.stop()

    selected = st.multiselect("策略篩選", options=strat_names, default=strat_names)
    if not selected:
        st.info("請至少選一個策略。")
        st.stop()

    if nav_df is None or nav_df.empty:
        st.warning("daily_nav 目前沒有資料（請到『🔄 同步』頁先補 REAL）。")
        st.stop()

    nav_df = nav_df.copy()
    if "日期" not in nav_df.columns or "策略" not in nav_df.columns or "NAV" not in nav_df.columns:
        st.error("daily_nav 缺必要欄位：日期 / 策略 / NAV")
        st.stop()

    nav_df["日期_dt"] = pd.to_datetime(nav_df["日期"], errors="coerce")
    nav_df["策略"] = nav_df["策略"].astype(str).str.strip()
    nav_df["NAV"] = pd.to_numeric(nav_df["NAV"], errors="coerce")
    nav_df = nav_df.dropna(subset=["日期_dt", "NAV"]).sort_values("日期_dt")

    nav_df2 = nav_df.copy()
    if sel_mode != "ALL" and "mode" in nav_df2.columns:
        nav_df2["mode"] = nav_df2["mode"].astype(str).fillna("").replace("", "UNKNOWN")
        nav_df2 = nav_df2[nav_df2["mode"] == sel_mode]

    nav_sel = nav_df2[nav_df2["策略"].isin(selected)].copy()
    if nav_sel.empty:
        st.info("選定策略在 daily_nav 沒資料（或 mode 篩選後為空）。")
        st.stop()

    _, portfolio_value = _build_portfolio_from_nav(nav_sel, strategies_df)
    last_val = float(portfolio_value.iloc[-1]) if len(portfolio_value) else 0.0
    mdd = _calc_mdd(portfolio_value)

    today_ret = None
    if "日報酬" in nav_sel.columns:
        nav_sel["日報酬"] = pd.to_numeric(nav_sel["日報酬"], errors="coerce")
        last_day = nav_sel["日期_dt"].max()
        tmp = nav_sel[nav_sel["日期_dt"] == last_day].merge(
            strategies_df[["策略名稱", "起始資金"]],
            left_on="策略",
            right_on="策略名稱",
            how="left",
            suffixes=("_x", "_y"),
        )
        tmp = _coalesce_columns(tmp, "起始資金", prefer="y")
        if "起始資金" not in tmp.columns:
            tmp["起始資金"] = 0.0

        tmp["起始資金"] = pd.to_numeric(tmp["起始資金"], errors="coerce").fillna(0.0)
        w = tmp["起始資金"].sum()
        tmp["加權"] = tmp["起始資金"] / (w if w else 1.0)
        tmp["加權日報酬"] = tmp["日報酬"].fillna(0.0) * tmp["加權"]
        today_ret = float(tmp["加權日報酬"].sum())

    cap_limit = float(strat_pool["起始資金"].sum())

    cards = [
        {"title": "Total Value", "value": f"${last_val:,.0f}", "sub": "目前組合市值", "variant": "neutral"},
        {
            "title": "Today Return",
            "value": "--" if today_ret is None else f"{today_ret*100:,.2f}%",
            "sub": "加權日報酬" if today_ret is not None else "daily_nav 未提供",
            "variant": "neutral"
            if today_ret is None
            else ("positive" if today_ret > 0 else ("negative" if today_ret < 0 else "neutral")),
        },
        {"title": "Max Drawdown", "value": f"{mdd*100:,.2f}%", "sub": "以市值計算", "variant": "negative" if mdd < 0 else "neutral"},
        {"title": "Active Strategies", "value": f"{len(strat_pool)}", "sub": "狀態：運行中" if active_only else "全部", "variant": "neutral"},
        {"title": "Capital Limit", "value": f"${cap_limit:,.0f}", "sub": "策略起始資金總和", "variant": "neutral"},
    ]

    cols = st.columns(len(cards))
    for col, c in zip(cols, cards):
        with col:
            st.markdown(metric_card(c["title"], c["value"], c["sub"], c["variant"]), unsafe_allow_html=True)

    st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
    st.markdown("### 📈 Portfolio Value")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=portfolio_value.index, y=portfolio_value.values, mode="lines", name="Portfolio Value"))
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
    st.markdown("### 🧵 每策略 NAV")
    figS = go.Figure()
    for strat in selected:
        g = nav_sel[nav_sel["策略"] == strat].sort_values("日期_dt")
        figS.add_trace(go.Scatter(x=g["日期_dt"], y=g["NAV"], mode="lines", name=strat))
    figS.update_layout(height=360, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(figS, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if show_real_unreal:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("### 🧾 已實現 vs 未實現（Portfolio 加總）")
        realized, unreal = _build_real_unreal_curves(nav_sel)
        figRU = go.Figure()
        if len(realized):
            figRU.add_trace(go.Scatter(x=realized.index, y=realized.values, mode="lines", name="Realized (Cum)"))
        if len(unreal):
            figRU.add_trace(go.Scatter(x=unreal.index, y=unreal.values, mode="lines", name="Unrealized"))
        figRU.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(figRU, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
    st.markdown("### 📉 Drawdown（Portfolio）")
    roll_max = portfolio_value.cummax()
    dd = portfolio_value / roll_max - 1.0
    figDD = go.Figure()
    figDD.add_trace(go.Scatter(x=dd.index, y=dd.values * 100, mode="lines", name="Drawdown (%)"))
    figDD.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(figDD, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── 每日市值記錄圖表（portfolio_daily）──────────────────
    pf_df = load_portfolio_daily()
    if not pf_df.empty and "date" in pf_df.columns:
        # 圖1：總市值趨勢
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("### 💰 每日總資產趨勢（portfolio_daily）")
        fig_total = go.Figure()
        if "total_market_value" in pf_df.columns:
            fig_total.add_trace(go.Scatter(
                x=pf_df["date"], y=pf_df["total_market_value"],
                mode="lines+markers", name="總市值",
                line=dict(color="#6366f1", width=2),
                marker=dict(size=5),
                fill="tozeroy", fillcolor="rgba(99,102,241,0.08)",
            ))
        fig_total.update_layout(
            height=300, margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="white", paper_bgcolor="white",
            yaxis=dict(tickformat=",.0f"),
        )
        st.plotly_chart(fig_total, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 圖2：各券商堆疊面積圖
        broker_cols = {
            "yuanta_market_value": "元大",
            "ib_market_value": "IB",
            "schwab_market_value": "Schwab",
        }
        available = {k: v for k, v in broker_cols.items() if k in pf_df.columns and pf_df[k].notna().any()}
        if available:
            st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
            st.markdown("### 🏦 各券商市值分布（堆疊）")
            palette = [
                ("#06b6d4", "rgba(6,182,212,0.55)"),
                ("#8b5cf6", "rgba(139,92,246,0.55)"),
                ("#f59e0b", "rgba(245,158,11,0.55)"),
                ("#10b981", "rgba(16,185,129,0.55)"),
            ]
            colors = [p[0] for p in palette]
            fig_broker = go.Figure()
            for (col, label), (stroke, fill) in zip(available.items(), palette):
                fig_broker.add_trace(go.Scatter(
                    x=pf_df["date"], y=pf_df[col].fillna(0),
                    mode="lines", name=label,
                    stackgroup="one",
                    line=dict(color=stroke, width=1),
                    fillcolor=fill,
                ))
            fig_broker.update_layout(
                height=300, margin=dict(l=0, r=0, t=10, b=0),
                plot_bgcolor="white", paper_bgcolor="white",
                yaxis=dict(tickformat=",.0f"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_broker, use_container_width=True)

            # 最新一天的各券商佔比（Pie）
            last_row = pf_df.iloc[-1]
            pie_labels = [v for k, v in available.items()]
            pie_values = [float(last_row.get(k, 0) or 0) for k in available]
            if sum(pie_values) > 0:
                fig_pie = go.Figure(go.Pie(
                    labels=pie_labels, values=pie_values,
                    hole=0.4,
                    marker=dict(colors=list(colors[:len(pie_labels)])),
                    textinfo="label+percent",
                ))
                fig_pie.update_layout(
                    height=260, margin=dict(l=0, r=0, t=10, b=0),
                    paper_bgcolor="white",
                    showlegend=False,
                    annotations=[dict(text=f"{last_row['date'].strftime('%m/%d')}", x=0.5, y=0.5, font_size=13, showarrow=False)],
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 🧾 策略概覽（最新 NAV / 市值 / 已實現 / 未實現）")
    last_date = nav_sel["日期_dt"].max()
    latest = nav_sel[nav_sel["日期_dt"] == last_date].copy()

    latest = latest.merge(
        strategies_df[["策略名稱", "起始資金", "狀態"]],
        left_on="策略",
        right_on="策略名稱",
        how="left",
        suffixes=("_x", "_y"),
    )
    latest = _coalesce_columns(latest, "起始資金", prefer="y")
    if "起始資金" not in latest.columns:
        latest["起始資金"] = 0.0

    latest["起始資金"] = pd.to_numeric(latest["起始資金"], errors="coerce").fillna(0.0)
    latest["市值"] = latest["NAV"] * latest["起始資金"]

    show_cols = [c for c in ["策略", "狀態", "起始資金", "NAV", "市值", "日報酬", "累積報酬", "realized_pnl", "unrealized_pnl"] if c in latest.columns]
    if "市值" in show_cols:
        st.dataframe(latest[show_cols].sort_values("市值", ascending=False).head(top_n), use_container_width=True, height=420)
    else:
        st.dataframe(latest[show_cols].head(top_n), use_container_width=True, height=420)


# ============================================================
# 9) 頁面：同步
# ============================================================
elif page == "🔄 同步":
    st.markdown("## 🔄 同步（Daily NAV REAL：已實現 + 未實現）")

    if not SHEETS_OK:
        st.error(SHEETS_ERR)
        st.stop()

    st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
    st.markdown("### ✅ 同步 daily_nav REAL（每策略每天 1 筆）")
    st.caption("REAL = 起始資金 + 已實現累積(round_trips) + 未實現(broker_positions；欄位不足時 unreal=0)")
    days_back = st.number_input("回補天數 days_back", min_value=7, max_value=2000, value=365, step=30)

    cA, cB = st.columns([1, 1])
    with cA:
        if st.button("🧾 同步 daily_nav REAL（寫入）", use_container_width=True, key="sync_nav_real"):
            with st.spinner("同步 daily_nav REAL 中..."):
                res = sync_daily_nav_real_per_strategy(dry_run=False, days_back=int(days_back), mode="REAL")
            if res.get("error"):
                st.error(f"❌ 同步失敗：{res['error']}")
                append_sync_log("sync_daily_nav_real", "SYSTEM", 0, "failed", note=str(res.get("error")))
            else:
                st.success(f"✅ 完成：新增 {res['added']}｜更新 {res['updated']}｜略過 {res['skipped']}")
                append_sync_log(
                    "sync_daily_nav_real",
                    "SYSTEM",
                    int(res.get("added", 0)) + int(res.get("updated", 0)),
                    "success",
                    note=f"added={res.get('added',0)} updated={res.get('updated',0)} skipped={res.get('skipped',0)}",
                )
                st.cache_data.clear()
                st.rerun()

    with cB:
        if st.button("🧪 Dry Run（不寫入）", use_container_width=True, key="sync_nav_dry"):
            r = sync_daily_nav_real_per_strategy(dry_run=True, days_back=int(days_back), mode="REAL")
            if r.get("error"):
                st.error(f"Dry Run 失敗：{r['error']}")
            else:
                st.info(f"Dry Run：將新增 {r['added']}｜將更新 {r['updated']}｜略過 {r['skipped']}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
    # ── 每日市值快照 ──────────────────────────────────
    st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
    st.markdown("### 📸 記錄每日投資組合市值")
    st.caption("讀取 broker_positions 彙總各券商市值，寫入 portfolio_daily（一天一筆，重複執行會更新當日資料）。")
    st.caption("⏰ 已設排程：每日 13:40 自動執行。亦可手動觸發。")

    if st.button("📸 記錄今日市值快照", use_container_width=True, key="record_portfolio_daily"):
        with st.spinner("記錄中..."):
            try:
                result = subprocess.run(
                    [os.sys.executable,
                     str(Path(__file__).resolve().parents[1] / "brokers" / "record_daily_nav.py")],
                    capture_output=True, text=True, timeout=60,
                    cwd=str(Path(__file__).resolve().parents[1]),
                )
                out = (result.stdout + result.stderr).strip()
                if result.returncode == 0:
                    st.success("✅ 今日市值已記錄至 portfolio_daily")
                else:
                    st.warning(f"⚠️ 執行結束（RC={result.returncode}）")
                if out:
                    st.caption(out[-600:])
                st.cache_data.clear()
            except Exception as e:
                st.error(f"❌ 執行失敗：{e}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 🧩 IB 同步（Snapshot / Field / RoundTrips）")
    st.caption("Snapshot/Field 都寫入 broker_snapshot（靠表頭判斷 schema）；RoundTrips 寫入 round_trips。")

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        if st.button("📌 Snapshot（IB 持倉快照）", use_container_width=True, key="sync_ib_snapshot"):
            if not HAS_IB_API:
                st.error("IB API 不可用（或尚未完成設定）")
            else:
                with st.spinner("同步 IB Snapshot..."):
                    res = sync_ib_positions_to_broker_snapshot(dry_run=False)
                if res.get("error"):
                    st.error(f"❌ 失敗：{res['error']}")
                    append_sync_log("ib_snapshot", "IBKR", 0, "failed", note=str(res.get("error")))
                else:
                    st.success(f"✅ 完成：新增 {res.get('added',0)}｜略過 {res.get('skipped',0)}")
                    append_sync_log("ib_snapshot", "IBKR", int(res.get("added", 0)), "success", note=res.get("msg", ""))

    with c2:
        if st.button("🧾 Field（IB 帳戶欄位快照）", use_container_width=True, key="sync_ib_field"):
            if not HAS_IB_API:
                st.error("IB API 不可用（或尚未完成設定）")
            else:
                with st.spinner("同步 IB Field..."):
                    res = sync_ib_positions_to_broker_snapshot(dry_run=False)
                if res.get("error"):
                    st.error(f"❌ 失敗：{res['error']}")
                    append_sync_log("ib_field", "IBKR", 0, "failed", note=str(res.get("error")))
                else:
                    st.success(f"✅ 完成：新增 {res.get('added',0)}｜略過 {res.get('skipped',0)}")
                    append_sync_log("ib_field", "IBKR", int(res.get("added", 0)), "success", note=res.get("msg", ""))

    with c3:
        if st.button("📥 IB Fills (同步 IB 成交)", use_container_width=True, key="sync_ib_fills"):
            if not HAS_IB_API:
                 st.error("IB API 不可用")
            else:
                with st.spinner("同步 IB Executions (7 days)..."):
                    res = sync_ib_executions_to_broker_fills(dry_run=False, days=7)
                
                if res.get("error"):
                    st.error(f"❌ 失敗: {res['error']}")
                    append_sync_log("ib_fills", "IBKR", 0, "failed", note=str(res.get("error")))
                else:
                    st.success(f"✅ 完成: 新增 {res.get('added', 0)} | 略過 {res.get('skipped', 0)}")
                    append_sync_log("ib_fills", "IBKR", int(res.get("added", 0)), "success", note=res.get("msg", ""))
                    st.cache_data.clear()
                    st.rerun()

    with c4:
        if st.button("🔁 RoundTrips（FIFO 已平倉配對）", use_container_width=True, key="sync_round_trips"):
            with st.spinner("建立 round_trips 並寫入 Google Sheets..."):
                res = sync_round_trips_to_sheet(dry_run=False)
            if res.get("error"):
                st.error(f"❌ 失敗：{res['error']}")
                append_sync_log("sync_round_trips_to_sheet", "SYSTEM", 0, "failed", note=str(res.get("error")))
            else:
                st.success(f"✅ 完成：新增 {res.get('added',0)}｜略過 {res.get('skipped',0)}（去重）")
                append_sync_log(
                    "sync_round_trips_to_sheet",
                    "SYSTEM",
                    int(res.get("added", 0)),
                    "success",
                    note=f"added={res.get('added',0)} skipped={res.get('skipped',0)}",
                )
                st.cache_data.clear()
                st.rerun()

    with c5:
        if st.button("📌 IB → broker_positions", use_container_width=True, key="sync_ib_positions"):
            if not HAS_IB_API:
                st.error("IB API 不可用（或尚未完成設定）")
            else:
                with st.spinner("同步 IB positions → broker_positions..."):
                    res = sync_ib_positions_to_broker_positions(dry_run=False)

                if res.get("error"):
                    st.error(f"❌ 失敗：{res['error']}")
                    append_sync_log("ib_positions_to_broker_positions", "IBKR", 0, "failed", note=str(res.get("error")))
                else:
                    st.success(f"✅ 完成：新增 {res.get('added',0)}｜略過 {res.get('skipped',0)}")
                    append_sync_log(
                        "ib_positions_to_broker_positions",
                        "IBKR",
                        int(res.get("added", 0)),
                        "success",
                        note=res.get("msg", ""),
                    )
                    st.cache_data.clear()
                    st.rerun()

    # --- 元大同步按鈕 ---
    st.markdown("---")
    st.markdown("### 🏹 元大同步 (Yuanta One API)")
    st.caption("點擊「元大登入並註冊監聽」後，系統將實時接收成交。之後可點擊「同步元大成交」將緩存寫入 Sheets。")

    with st.expander("🔑 證券憑證安裝指南 (解決 RtnCode=141)", expanded=False):
        st.markdown("""
        如果您看到 **RtnCode=141 (執行異常，憑證不存在)**，請按照以下步驟操作：
        1. **找到憑證**：請找到您的元大證券憑證檔案 (通常為 `.pfx` 或 `.p12` 副檔名)。
        2. **開始安裝**：連點兩下該檔案，啟動「憑證匯入精靈」。
        3. **存放位置**：選擇 **「目前使用者」**。
        4. **輸入密碼**：輸入申請憑證時設定的密碼。
        5. **自動存放**：讓精靈自動根據憑證類型選擇存放區，或手動選擇 **「個別」 (Personal)**。
        6. **完成**：重啟此頁面並再次點擊「元大登入」。
        """)
        if st.button("📁 開啟專案資料夾 (方便查找憑證)", key="btn_open_pfx_dir"):
            os.startfile(os.getcwd())

    cY1, cY2, cY3, cY4 = st.columns(4)
    with cY1:
        if st.button("🔐 元大登入並註冊監聽", use_container_width=True):
            if not HAS_YUANTA_API:
                st.error("此系統環境不支援元大 API (需 Windows + DLL)")
            else:
                try:
                    with st.spinner("元大連線登入中..."):
                        # 存入 session_state 避免重複連線
                        if "yuanta_api" not in st.session_state:
                            api = yuanta_login()
                            register_events(api)
                            st.session_state["yuanta_api"] = api
                            st.success("✅ 元大 API 登入並註冊監聽成功！")
                        else:
                            st.info("ℹ️ 元大 API 已在連線狀態。")
                except Exception as e:
                    st.error(f"❌ 元大登入失敗：{e}")

    with cY2:
        if st.button("📥 同步元大成交 (Fills)", use_container_width=True):
            if "yuanta_api" not in st.session_state:
                st.warning("請先點擊「元大登入」")
            else:
                with st.spinner("讀取緩存成交中..."):
                    fills = fetch_fills(st.session_state["yuanta_api"])
                
                if not fills:
                    st.info("目前緩存中無新成交內容。")
                else:
                    st.success(f"✅ 成功抓取 {len(fills)} 筆新成交！")
                    st.json([str(f) for f in fills]) 

    with cY3:
        if st.button("🔍 元大庫存查詢 (Query)", use_container_width=True):
            if "yuanta_api" not in st.session_state:
                st.warning("請先點擊「元大登入」")
            else:
                ok = query_stock_positions(st.session_state["yuanta_api"])
                if ok:
                    st.success("✅ 庫存查詢指令已送出，請等候數秒後點擊「同步」。")
                else:
                    st.error("❌ 查詢指令發送失敗。")

    with cY4:
        if st.button("🏹 元大庫存 → Sheets", use_container_width=True):
            if "yuanta_api" not in st.session_state:
                st.warning("請先點擊「元大登入」")
            else:
                with st.spinner("讀取庫存數據中..."):
                    pos_data = fetch_positions(st.session_state["yuanta_api"])
                    res = sync_yuanta_positions_to_broker_positions(pos_data)

                if res.get("error"):
                    st.error(f"❌ 失敗：{res['error']}")
                else:
                    st.success(res.get("msg", "完成"))
                    append_sync_log(
                        "yuanta_positions_to_broker_positions",
                        "YUANTA",
                        int(res.get("added", 0)),
                        "success",
                        note=res.get("msg", ""),
                    )
                    st.cache_data.clear()

            # ── 無論 API 是否登入，也同步 JSON snapshot → Sheets ──
            _run_snapshot_upload()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
    st.markdown("### 🟦 SCHWAB 同步（Account / Positions）")
    st.caption("尚未完成 Schwab OAuth/API 前會顯示「SCHWAB 未啟用」；完成後可寫入 broker_snapshot / broker_positions。")
    st.caption(f"SCHWAB enabled? {is_schwab_enabled()} | HAS_SCHWAB_API={HAS_SCHWAB_API}")

    cS1, cS2 = st.columns(2)

    with cS1:
        if st.button("🧾 Account（SCHWAB 帳戶快照）", use_container_width=True):
            with st.spinner("同步 SCHWAB Account..."):
                res = sync_schwab_account_to_broker_snapshot(dry_run=False)

            if res.get("msg") and "未啟用" in str(res.get("msg")):
                st.info(res.get("msg"))
                append_sync_log("schwab_account", "SCHWAB", 0, "disabled", note=res.get("msg", ""))
            elif res.get("error"):
                st.error(f"❌ 失敗：{res['error']}")
                append_sync_log("schwab_account", "SCHWAB", 0, "failed", note=str(res.get("error")))
            else:
                st.success(res.get("msg", "完成"))
                append_sync_log("schwab_account", "SCHWAB", int(res.get("added", 0)), "success", note=res.get("msg", ""))

    with cS2:
        if st.button("📌 Positions（SCHWAB 持倉快照）", use_container_width=True):
            with st.spinner("同步 SCHWAB Positions..."):
                res = sync_schwab_positions_to_broker_positions(dry_run=False)

            if res.get("msg") and "未啟用" in str(res.get("msg")):
                st.info(res.get("msg"))
                append_sync_log("schwab_positions", "SCHWAB", 0, "disabled", note=res.get("msg", ""))
            elif res.get("error"):
                st.error(f"❌ 失敗：{res['error']}")
                append_sync_log("schwab_positions", "SCHWAB", 0, "failed", note=str(res.get("error")))
            else:
                st.success(res.get("msg", "完成"))
                append_sync_log("schwab_positions", "SCHWAB", int(res.get("added", 0)), "success", note=res.get("msg", ""))

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 🔎 daily_nav_strategy 最近資料（預覽）")
    try:
        df = load_daily_nav()
        if df is None or df.empty:
            st.info("daily_nav 無資料")
        else:
            show_cols = [
                c
                for c in ["日期", "策略", "mode", "value", "NAV", "日報酬", "累積報酬", "realized_pnl", "unrealized_pnl", "position_value", "備註"]
                if c in df.columns
            ]
            st.dataframe(df[show_cols].tail(120).astype(str), use_container_width=True, height=420)
    except Exception as e:
        st.error(f"讀取 daily_nav 失敗：{e}")

    st.markdown("### 🔎 最近 broker_snapshot / broker_positions / round_trips（預覽）")
    cA, cB, cC = st.columns(3)

    with cA:
        try:
            snap_df = load_sheet_df("broker_snapshot")
            if snap_df.empty:
                st.info("broker_snapshot 無資料")
            else:
                st.dataframe(snap_df.tail(40).astype(str), use_container_width=True, height=260)
        except Exception as e:
            st.error(f"讀取 broker_snapshot 失敗：{e}")

    with cB:
        try:
            pos_df = load_sheet_df("broker_positions")
            if pos_df.empty:
                st.info("broker_positions 無資料")
            else:
                st.dataframe(pos_df.tail(40).astype(str), use_container_width=True, height=260)
        except Exception as e:
            st.error(f"讀取 broker_positions 失敗：{e}")

    with cC:
        try:
            rt_df = load_sheet_df("round_trips")
            if rt_df.empty:
                st.info("round_trips 無資料")
            else:
                st.dataframe(rt_df.tail(40).astype(str), use_container_width=True, height=260)
        except Exception as e:
            st.error(f"讀取 round_trips 失敗：{e}")


# ============================================================
# ✅ 9.5) 頁面：交易原因（直接寫回 trades）
# ============================================================
elif page == "📝 交易原因":
    st.markdown("## 📝 交易原因（直接寫回 trades）")

    if not SHEETS_OK:
        st.error(SHEETS_ERR)
        st.stop()

    st.caption("做法 #2：不新增分頁，直接用 source(FILL uid / exit_uid) 去更新 trades 的 進場原因 / 出場原因 / 備註 / 策略。")

    try:
        strategies_df = load_strategies()
        if strategies_df is None or strategies_df.empty:
            strategies_df = pd.DataFrame({"策略名稱": []})
        if "策略名稱" not in strategies_df.columns:
            strategies_df["策略名稱"] = ""
        strategies_df["策略名稱"] = strategies_df["策略名稱"].astype(str).str.strip()
        strat_list = sorted([s for s in strategies_df["策略名稱"].dropna().unique().tolist() if str(s).strip() != ""])
    except Exception:
        strat_list = []

    tab1, tab2, tab3 = st.tabs(["✅ 依 broker_fills（成交）", "✅ 依 round_trips（平倉）", "🔎 trades 預覽"])

    # ----------------------------
    # Tab1: broker_fills（用 fill_uid 寫 trades）
    # ----------------------------
    with tab1:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("### ✅ 選一筆成交 → 寫回 trades")

        fills_df = load_sheet_df("broker_fills")
        if fills_df is None or fills_df.empty:
            st.info("broker_fills 無資料。")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            # 基本欄位保底
            for c in ["時間", "券商", "symbol", "side", "shares", "price", "currency", "orderId"]:
                if c not in fills_df.columns:
                    fills_df[c] = ""

            fills_df = fills_df.copy()
            fills_df["時間_dt"] = pd.to_datetime(fills_df["時間"], errors="coerce")
            fills_df = fills_df.dropna(subset=["時間_dt"]).sort_values("時間_dt", ascending=False)

            c1, c2, c3, c4 = st.columns([1.1, 1.2, 1.0, 1.7])
            with c1:
                broker_opt = ["ALL"] + sorted(fills_df["券商"].astype(str).fillna("").replace("", "UNKNOWN").unique().tolist())
                sel_broker = st.selectbox("券商", broker_opt, index=0)
            with c2:
                symbol_opt = ["ALL"] + sorted(fills_df["symbol"].astype(str).fillna("").replace("", "UNKNOWN").unique().tolist())
                sel_symbol = st.selectbox("標的", symbol_opt, index=0)
            with c3:
                note_type = st.selectbox("寫入類型", ["Entry", "Exit", "Adjust", "Review"], index=0)
            with c4:
                strategy = st.selectbox("策略（寫回 trades.策略）", [""] + strat_list, index=0)

            dfv = fills_df.copy()
            if sel_broker != "ALL":
                dfv = dfv[dfv["券商"].astype(str).str.strip() == sel_broker]
            if sel_symbol != "ALL":
                dfv = dfv[dfv["symbol"].astype(str).str.strip() == sel_symbol]

            dfv["fill_uid"] = dfv.apply(_make_fill_uid, axis=1)
            dfv["label"] = (
                dfv["時間_dt"].dt.strftime("%Y-%m-%d %H:%M:%S").astype(str)
                + " | "
                + dfv["券商"].astype(str)
                + " | "
                + dfv["symbol"].astype(str)
                + " | "
                + dfv["side"].astype(str)
                + " | "
                + dfv["shares"].astype(str)
                + "@"
                + dfv["price"].astype(str)
            )

            max_show = min(len(dfv), 300)
            dfv = dfv.head(max_show)

            sel_label = st.selectbox("選擇成交（最新在最上）", dfv["label"].tolist(), index=0 if len(dfv) else None)

            r = None
            if sel_label and len(dfv):
                r = dfv[dfv["label"] == sel_label].iloc[0]

            reason = st.text_area("原因（會寫入 進場原因 / 出場原因 或備註）", height=80, placeholder="例如：突破、回測不破、停損規則、資金流...等")
            memo = st.text_area("備註（可選）", height=80, placeholder="補充：盤勢、風控、情緒、執行細節...")

            cW1, cW2 = st.columns([1, 1])
            with cW1:
                if st.button("✅ 寫回 trades（以成交）", use_container_width=True, disabled=(r is None)):
                    try:
                        fill_uid = str(r.get("fill_uid", "")).strip()
                        res = upsert_trade_reason_to_trades(
                            source=fill_uid,  # ✅ 對 trades.source
                            broker=str(r.get("券商", "")).strip(),
                            symbol=str(r.get("symbol", "")).strip(),
                            direction=str(r.get("side", "")).strip(),
                            qty=str(r.get("shares", "")).strip(),
                            entry_px=str(r.get("price", "")).strip() if note_type == "Entry" else "",
                            exit_px=str(r.get("price", "")).strip() if note_type == "Exit" else "",
                            currency=str(r.get("currency", "")).strip(),
                            entry_time=str(r.get("時間", "")).strip() if note_type == "Entry" else "",
                            exit_time=str(r.get("時間", "")).strip() if note_type == "Exit" else "",
                            strategy=str(strategy).strip(),
                            note_type=note_type,
                            reason_text=str(reason).strip(),
                            memo_text=str(memo).strip(),
                            pnl="",
                        )
                        st.success(f"✅ trades 寫入完成：{res['action']}")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"寫回 trades 失敗：{e}")

            with cW2:
                show_n = st.slider("broker_fills 預覽筆數", 10, 200, 40, 10)
                st.dataframe(dfv.head(show_n).drop(columns=["label"]).astype(str), use_container_width=True, height=320)

            st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------
    # Tab2: round_trips（用 exit_uid 寫出場原因）
    # ----------------------------
    with tab2:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("### ✅ 選一筆 round_trip → 將原因寫到 trades（exit_uid 那筆）")
        st.caption("建議：出場原因寫到 exit_uid 對應的 trades.source。若 round_trips 表頭沒有 exit_uid，請先補表頭並重新同步。")

        rt_df = load_sheet_df("round_trips")
        if rt_df is None or rt_df.empty:
            st.info("round_trips 無資料。")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            for c in ["exit_time", "broker", "symbol", "qty", "entry_px", "exit_px", "pnl", "strategy", "exit_uid"]:
                if c not in rt_df.columns:
                    rt_df[c] = ""

            rt_df = rt_df.copy()
            rt_df["exit_dt"] = pd.to_datetime(rt_df["exit_time"], errors="coerce")
            rt_df = rt_df.sort_values("exit_dt", ascending=False)

            c1, c2, c3, c4 = st.columns([1.0, 1.2, 1.0, 1.8])
            with c1:
                broker_opt = ["ALL"] + sorted(rt_df["broker"].astype(str).fillna("").replace("", "UNKNOWN").unique().tolist())
                sel_broker = st.selectbox("券商", broker_opt, index=0, key="rt_broker")
            with c2:
                symbol_opt = ["ALL"] + sorted(rt_df["symbol"].astype(str).fillna("").replace("", "UNKNOWN").unique().tolist())
                sel_symbol = st.selectbox("標的", symbol_opt, index=0, key="rt_symbol")
            with c3:
                note_type = st.selectbox("寫入類型", ["Exit", "Review", "Adjust"], index=0, key="rt_note_type")
            with c4:
                strategy = st.selectbox("策略（寫回 trades.策略）", [""] + strat_list, index=0, key="rt_strategy")

            dfv = rt_df.copy()
            if sel_broker != "ALL":
                dfv = dfv[dfv["broker"].astype(str).str.strip() == sel_broker]
            if sel_symbol != "ALL":
                dfv = dfv[dfv["symbol"].astype(str).str.strip() == sel_symbol]

            dfv["label"] = (
                dfv["exit_dt"].fillna(pd.Timestamp("1970-01-01")).dt.strftime("%Y-%m-%d %H:%M:%S").astype(str)
                + " | "
                + dfv["broker"].astype(str)
                + " | "
                + dfv["symbol"].astype(str)
                + " | qty="
                + dfv["qty"].astype(str)
                + " | pnl="
                + dfv["pnl"].astype(str)
            )

            max_show = min(len(dfv), 300)
            dfv = dfv.head(max_show)

            sel_label = st.selectbox("選擇 round_trip（最新在最上）", dfv["label"].tolist(), index=0 if len(dfv) else None, key="rt_pick")
            r = None
            if sel_label and len(dfv):
                r = dfv[dfv["label"] == sel_label].iloc[0]

            reason = st.text_area("原因（建議填「出場原因」）", height=90, key="rt_reason")
            memo = st.text_area("備註（可選）", height=90, key="rt_memo")

            cW1, cW2 = st.columns([1, 1])
            with cW1:
                if st.button("✅ 寫回 trades（出場原因寫到 exit_uid）", use_container_width=True, disabled=(r is None), key="rt_write"):
                    try:
                        exit_uid = str(r.get("exit_uid", "")).strip()
                        if not exit_uid:
                            st.error("round_trips 缺 exit_uid，無法對應到 trades.source（請先補表頭並重新同步 round_trips）。")
                        else:
                            res = upsert_trade_reason_to_trades(
                                source=exit_uid,
                                broker=str(r.get("broker", "")).strip(),
                                symbol=str(r.get("symbol", "")).strip(),
                                direction="EXIT",
                                qty=str(r.get("qty", "")).strip(),
                                entry_px=str(r.get("entry_px", "")).strip(),
                                exit_px=str(r.get("exit_px", "")).strip(),
                                currency=str(r.get("currency", "")).strip(),
                                entry_time=str(r.get("entry_time", "")).strip(),
                                exit_time=str(r.get("exit_time", "")).strip(),
                                strategy=str(strategy).strip() or str(r.get("strategy", "")).strip(),
                                note_type=note_type,
                                reason_text=str(reason).strip(),
                                memo_text=str(memo).strip(),
                                pnl=str(r.get("pnl", "")).strip(),
                            )
                            st.success(f"✅ trades 寫入完成：{res['action']}")
                            st.cache_data.clear()
                            st.rerun()
                    except Exception as e:
                        st.error(f"寫回 trades 失敗：{e}")

            with cW2:
                show_n = st.slider("round_trips 預覽筆數", 10, 200, 40, 10, key="rt_show_n")
                st.dataframe(dfv.head(show_n).drop(columns=["label"]).astype(str), use_container_width=True, height=320)

            st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------
    # Tab3: trades preview
    # ----------------------------
    with tab3:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("### 🔎 trades 最新資料（預覽）")
        try:
            tdf = load_trades()
            if tdf is None or tdf.empty:
                st.info("trades 無資料")
            else:
                cols = [c for c in TRADES_REQUIRED_COLS if c in tdf.columns]
                st.dataframe(tdf[cols].tail(200).astype(str), use_container_width=True, height=520)
        except Exception as e:
            st.error(f"讀取 trades 失敗：{e}")
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# 10) 頁面：IB 即時監控（可選）
# ============================================================
elif page == "💹 IB 即時監控":
    st.markdown("## 💹 IB 即時監控（唯讀）")

    if not HAS_IB_API:
        st.info("IB API 未啟用或不可用（可忽略）。")
        st.stop()

    st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
    st.markdown("### 📌 帳戶摘要（IB API）")

    try:
        snap = get_account_snapshot()
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                metric_card("Net Liquidation", f"{getattr(snap,'net_liquidation',0):,.2f} {getattr(snap,'currency','')}", "帳戶總資產"),
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                metric_card("Total Cash", f"{getattr(snap,'total_cash_value',0):,.2f} {getattr(snap,'currency','')}", "可動用現金"),
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                metric_card("Equity w/ Loan", f"{getattr(snap,'equity_with_loan',0):,.2f} {getattr(snap,'currency','')}", "含融資權益"),
                unsafe_allow_html=True,
            )
    except Exception as e:
        st.error(f"讀取帳戶摘要失敗：{e}")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
    st.markdown("### 📌 目前持倉（IB API）")
    try:
        positions = get_open_positions()
        if positions:
            st.dataframe(pd.DataFrame(positions).astype(str), use_container_width=True, height=520)
        else:
            st.info("目前沒有持倉。")
    except Exception as e:
        st.error(f"讀取持倉失敗：{e}")
    st.markdown("</div>", unsafe_allow_html=True)
