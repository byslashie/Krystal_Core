"""
Google Sheets 實盤交易管理工具模組 (完整整合版)
- 保留所有原始業務邏輯 (read/append/overwrite/update/log)
- 新增：DISABLE_SHEETS 開關（遇到公司網路/SSL/代理問題時可跳過 Sheets）
- 優化：Mac / Windows 絕對路徑偵測、環境變數自動載入
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from functools import lru_cache
from typing import Dict, Any, Optional

try:
    import pandas as pd
except ImportError:
    pd = None
    # logger is not initialized yet, but we can print or just ignore if not used


# ✅ 只要在 PowerShell 設定：$env:DISABLE_SHEETS="1"
# 就會完全跳過 Google Sheets 的連線與寫入，避免 SSL/代理問題卡死整個同步流程
DISABLE_SHEETS = os.getenv("DISABLE_SHEETS", "0") == "1"

# 本地緩存相關設定
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "cache")
if not os.path.exists(CACHE_DIR):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
    except:
        pass

# Google 相關套件（可能因網路/SSL 會出錯，所以保留在下方，並搭配 DISABLE_SHEETS 使用）
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# ========================================================
# 🔧 Mac / Windows 自動路徑修正 (確保能找到 .env 與 credentials.json)
# ========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# =========================
# 基本設定 (讀取 .env)
# =========================
SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "實盤交易管理")
SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_KEY")

_creds_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
CREDENTIALS_FILE = _creds_env if os.path.isabs(_creds_env) else os.path.join(BASE_DIR, _creds_env)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =========================
# Internal helpers
# =========================

@lru_cache(maxsize=1)
def get_gspread_client() -> gspread.Client:
    """建立 gspread client"""
    if DISABLE_SHEETS:
        raise RuntimeError("DISABLE_SHEETS=1 (skip gspread client)")

    if not os.path.exists(CREDENTIALS_FILE):
        error_msg = f"❌ 找不到憑證檔案：{CREDENTIALS_FILE}。請確認檔案已放置於：{BASE_DIR}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    logger.info("✅ gspread client 已建立")
    return client


@lru_cache(maxsize=1)
def get_workbook() -> gspread.Spreadsheet:
    """取得試算表物件"""
    if DISABLE_SHEETS:
        raise RuntimeError("DISABLE_SHEETS=1 (skip workbook)")

    client = get_gspread_client()
    try:
        if SPREADSHEET_ID:
            wb = client.open_by_key(SPREADSHEET_ID)
            logger.info("✅ 以 ID 開啟試算表")
        else:
            wb = client.open(SHEET_NAME)
            logger.info(f"✅ 以名稱開啟試算表：{SHEET_NAME}")
        return wb
    except Exception as e:
        # 捕捉特別嚴重的連線/SSL 錯誤，避免整頁崩潰
        err_str = str(e)
        if "SSL" in err_str or "TransportError" in err_str or "EOF" in err_str:
            logger.error(f"📡 Google Sheets 網路/SSL 連線超時或遭阻斷：{err_str}")
        else:
            logger.error(f"❌ 開啟試算表失敗：{e}")
        return None


def get_sheet(sheet_name: str) -> Optional[gspread.Worksheet]:
    """抓取指定分頁；若 DISABLE_SHEETS=1 則回傳 None"""
    if DISABLE_SHEETS:
        logger.warning(f"⚠️ DISABLE_SHEETS=1 → skip get_sheet('{sheet_name}')")
        return None

    wb = get_workbook()
    if wb is None:
        return None
    try:
        sheet = wb.worksheet(sheet_name)
        return sheet
    except gspread.WorksheetNotFound:
        logger.error(f"❌ 分頁 '{sheet_name}' 不存在")
        raise
    except Exception as e:
        logger.error(f"❌ 取得分頁 '{sheet_name}' 失敗：{e}")
        raise


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """把欄位前面的『欄位：』去掉"""
    if df is None or df.empty:
        return df
    df = df.copy()
    df.columns = [str(c).replace("欄位：", "").strip() for c in df.columns]
    return df


import socket
socket.setdefaulttimeout(5)  # ⚡ 縮短逾時至 5 秒，確保在網路不佳時能快速切換至離線緩存

def _worksheet_to_df(sheet: Optional[gspread.Worksheet]) -> pd.DataFrame:
    """將 worksheet 轉成 DataFrame (改用 get_all_values 提升穩定度)"""
    if sheet is None:
        return pd.DataFrame()

    try:
        # get_all_values 回傳的是 list of lists，第一列通常是 header
        rows = sheet.get_all_values()
        if not rows:
            return pd.DataFrame()

        header = rows[0]
        data = rows[1:]
        
        # 處理重複欄位名稱 (pandas 不允許重複 columns)
        # 用 dict 紀錄出現次數
        seen_count = {}
        new_header = []
        for col in header:
            c = str(col).strip()
            if c in seen_count:
                seen_count[c] += 1
                new_header.append(f"{c}_{seen_count[c]}")
            else:
                seen_count[c] = 0
                new_header.append(c)
        
        df = pd.DataFrame(data, columns=new_header)
        return _clean_columns(df)
    except Exception as e:
        logger.error(f"❌ _worksheet_to_df 轉換失敗：{e}")
        return pd.DataFrame()


def _get_cache_path(name: str) -> str:
    return os.path.join(CACHE_DIR, f"{name}.csv")


def _save_to_cache(name: str, df: pd.DataFrame):
    """將資料存入本地 CSV 緩存"""
    if df is None or df.empty:
        return
    try:
        path = _get_cache_path(name)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        logger.info(f"💾 已緩存 {name} 至本地")
    except Exception as e:
        logger.warning(f"⚠️ 緩存 {name} 失敗: {e}")


def _load_from_cache(name: str) -> pd.DataFrame:
    """從本地 CSV 讀取緩存"""
    try:
        path = _get_cache_path(name)
        if os.path.exists(path):
            df = pd.read_csv(path, encoding="utf-8-sig")
            logger.info(f"📂 從本地離線緩存讀取 {name} ({len(df)} 筆)")
            return df
    except Exception as e:
        logger.error(f"❌ 讀取緩存 {name} 失敗: {e}")
    return pd.DataFrame()


def _read_with_fallback(name: str, func):
    """
    通用讀取邏輯：優先嘗試在線讀取，失敗則切換至離線緩存。
    """
    if DISABLE_SHEETS:
        return _load_from_cache(name)

    try:
        # 這裡的 func 通常是實際去調用 API 的內部 lambda
        df = func()
        if not df.empty:
            _save_to_cache(name, df)
            return df
        else:
            # 如果回傳空，可能也是一種異常，嘗試讀緩存
            return _load_from_cache(name)
    except Exception as e:
        logger.warning(f"📡 在線讀取 {name} 失敗 ({e})，切換至離線模式...")
        return _load_from_cache(name)


# =========================
# TRADES
# =========================

def read_trades() -> pd.DataFrame:
    def _read():
        sheet = get_sheet("trades")
        return _worksheet_to_df(sheet) if sheet else pd.DataFrame()
    return _read_with_fallback("trades", _read)


def append_trade(trade_dict: Dict[str, Any]) -> bool:
    try:
        sheet = get_sheet("trades")
        if sheet is None:
            logger.warning("⚠️ Sheets disabled → skip append_trade")
            return True

        cols = [
            "id", "日期", "券商", "標的", "方向", "進場價", "出場價",
            "數量", "狀態", "策略", "進場原因", "出場原因", "備註"
        ]
        row = [trade_dict.get(c, "") for c in cols]
        sheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info("✅ 新增 trade 完成")
        return True
    except Exception as e:
        logger.error(f"❌ 新增 trade 失敗：{e}")
        return False


def overwrite_trades(df: pd.DataFrame) -> bool:
    try:
        sheet = get_sheet("trades")
        if sheet is None:
            logger.warning("⚠️ Sheets disabled → skip overwrite_trades")
            return True

        sheet.clear()
        values = [df.columns.tolist()] + df.astype(str).values.tolist()
        sheet.update(values, value_input_option="USER_ENTERED")
        logger.info("✅ trades 覆寫完成")
        return True
    except Exception as e:
        logger.error(f"❌ trades 覆寫失敗：{e}")
        return False


# =========================
# DAILY_NAV
# =========================

def read_daily_nav() -> pd.DataFrame:
    def _read():
        sheet = get_sheet("daily_nav")
        return _worksheet_to_df(sheet) if sheet else pd.DataFrame()
    return _read_with_fallback("daily_nav", _read)


def append_daily_nav(nav_dict: Dict[str, Any]) -> bool:
    try:
        sheet = get_sheet("daily_nav")
        if sheet is None:
            logger.warning("⚠️ Sheets disabled → skip append_daily_nav")
            return True

        cols = ["日期", "策略", "NAV", "日報酬", "累積報酬"]
        row = [nav_dict.get(c, "") for c in cols]
        sheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info("✅ daily_nav 新增成功")
        return True
    except Exception as e:
        logger.error(f"❌ daily_nav 新增失敗：{e}")
        return False


# =========================
# STRATEGIES
# =========================

def read_strategies() -> pd.DataFrame:
    def _read():
        sheet = get_sheet("strategies")
        return _worksheet_to_df(sheet) if sheet else pd.DataFrame()
    return _read_with_fallback("strategies", _read)


# =========================
# SYNC_LOGS
# =========================

def log_sync(sync_type: str, broker: str, count: int,
             status: str = "成功", remark: str = "") -> bool:
    try:
        sheet = get_sheet("sync_logs")
        if sheet is None:
            logger.warning("⚠️ Sheets disabled → skip log_sync")
            return True

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sync_type, broker, count, status, remark
        ]
        sheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info("✅ sync_logs 寫入成功")
        return True
    except Exception as e:
        logger.error(f"❌ sync_logs 寫入失敗：{e}")
        return False


# =========================
# 依 id 更新單筆 trade
# =========================

def update_trade_by_id(trade_id: str, update_dict: dict) -> bool:
    try:
        sheet = get_sheet("trades")
        if sheet is None:
            logger.warning("⚠️ Sheets disabled → skip update_trade_by_id")
            return True

        records = sheet.get_all_records()
        target_row = None
        for idx, rec in enumerate(records, start=2):
            if str(rec.get("id", "")).strip() == str(trade_id).strip():
                target_row = idx
                break

        if target_row is None:
            logger.error(f"❌ 找不到 id={trade_id} 的交易")
            return False

        header = sheet.row_values(1)
        for col_name, new_value in update_dict.items():
            try:
                col_index = header.index(col_name) + 1
                sheet.update_cell(target_row, col_index, new_value)
            except ValueError:
                logger.warning(f"⚠️ 欄位不存在：{col_name}")

        logger.info(f"✅ 成功更新 trade_id={trade_id}")
        return True
    except Exception as e:
        logger.error(f"❌ update_trade_by_id 失敗：{e}")
        return False


def read_sheet_data_with_cache(sheet_name: str) -> pd.DataFrame:
    """
    通用分頁讀取函式，支援緩存機制。
    """
    def _read():
        sheet = get_sheet(sheet_name)
        return _worksheet_to_df(sheet) if sheet else pd.DataFrame()
    return _read_with_fallback(sheet_name, _read)


if __name__ == "__main__":
    print(read_trades().head())


# ======================
# broker_snapshot 寫入
# ======================

def append_broker_snapshot(snapshot_dict: Dict[str, Any]) -> bool:
    """
    寫入券商帳戶快照到 broker_snapshot sheet
    欄位：timestamp | broker | net_liquidation | total_cash_value | currency
    """
    try:
        sheet = get_sheet("broker_snapshot")
        if sheet is None:
            return False

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [
            snapshot_dict.get("timestamp", now_str),
            snapshot_dict.get("broker", "IBKR"),
            snapshot_dict.get("net_liquidation", 0),
            snapshot_dict.get("total_cash_value", 0),
            snapshot_dict.get("currency", "USD")
        ]
        sheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info(f"✅ broker_snapshot 新增成功 ({snapshot_dict.get('broker', 'IBKR')})")
        return True
    except Exception as e:
        logger.error(f"❌ append_broker_snapshot 失敗：{e}")
        return False


def read_broker_positions() -> pd.DataFrame:
    """
    從 Google Sheets 讀取 broker_positions（當元大同步失敗時的備份）
    """
    try:
        if DISABLE_SHEETS:
            logger.warning("⚠️ DISABLE_SHEETS=1，跳過 Google Sheets 讀取")
            return pd.DataFrame()

        sheet = get_sheet("broker_positions")
        if sheet is None:
            logger.warning("⚠️ 找不到 broker_positions sheet")
            return pd.DataFrame()

        data = sheet.get_all_values()
        if not data or len(data) < 1:
            logger.warning("⚠️ broker_positions sheet 為空")
            return pd.DataFrame()

        # 第一行是 header
        header = data[0]
        rows = data[1:]

        df = pd.DataFrame(rows, columns=header)
        logger.info(f"✅ 從 Google Sheets 讀取 broker_positions：{len(df)} 筆")
        return df
    except FileNotFoundError:
        logger.warning("⚠️ 找不到 credentials.json，無法從 Google Sheets 讀取")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ 讀取 broker_positions 失敗：{e}")
        return pd.DataFrame()


def overwrite_broker_positions(positions_list: List[Dict[str, Any]]) -> bool:
    """
    根據最新數據覆寫 broker_positions sheet
    """
    try:
        sheet = get_sheet("broker_positions")
        if sheet is None:
            return False

        # 保留原本在 Sheet 上的其他券商數據 (除了 IB)，或者直接全覆寫
        # 這裡建議先讀取現有的，過濾掉 IB，再加入新的 IB
        from .sheets_utils import read_sheet_data_with_cache # 避免循環引用
    except Exception:
        pass

    try:
        sheet = get_sheet("broker_positions")
        if sheet is None: return False
        
        # 簡單起見：目前的邏輯可能是全量替換，或按券商替換
        # 為了穩定，我們先實作「全量覆寫」，這要求傳入所有的持倉（包含 Yuanta, Schwab 等）
        # 如果只想替換 IB，需要更複雜的 logic。我們先實作全量寫入。
        header = ["symbol", "broker", "position", "avgCost", "marketPrice", "marketValue", "unrealizedPNL", "currency", "timestamp"]
        rows = [header]
        for p in positions_list:
            rows.append([p.get(c, "") for c in header])
        
        sheet.clear()
        sheet.update(rows, value_input_option="USER_ENTERED")
        logger.info(f"✅ broker_positions 覆寫成功 (共 {len(positions_list)} 筆)")
        return True
    except Exception as e:
        logger.error(f"❌ overwrite_broker_positions 失敗：{e}")
        return False


# ======================
# ship_tracking 寫入 (波斯灣油輪監測)
# ======================

def write_ship_tracking(vessel_data: Dict[str, Any]) -> bool:
    """
    寫入油輪追踪數據到 ship_tracking sheet
    欄位需包含：
    timestamp | vessel_name | mmsi | imo | vessel_type | flag | latitude | longitude | speed | heading | last_update | status | alert_type
    """
    try:
        sheet = get_sheet("ship_tracking")
        if sheet is None:
            logger.warning("⚠️ Sheets disabled → skip write_ship_tracking")
            return True

        cols = [
            "timestamp", "vessel_name", "mmsi", "imo", "vessel_type", "flag",
            "latitude", "longitude", "speed", "heading", "last_update", "status", "alert_type"
        ]
        row = [vessel_data.get(c, "") for c in cols]
        sheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info(f"✅ ship_tracking 新增成功：{vessel_data.get('vessel_name', 'Unknown')}")
        return True
    except Exception as e:
        logger.error(f"❌ write_ship_tracking 失敗：{e}")
        return False


def read_ship_tracking() -> pd.DataFrame:
    """讀取 ship_tracking 分頁數據"""
    def _read():
        sheet = get_sheet("ship_tracking")
        return _worksheet_to_df(sheet) if sheet else pd.DataFrame()
    return _read_with_fallback("ship_tracking", _read)


# ======================
# intel_events 寫入 (情報層事件)
# ======================

def write_intel_event(event_data: Dict[str, Any]) -> bool:
    """
    寫入情報事件到 intel_events sheet
    欄位需包含：
    date | event_type | location | severity | llm_risk_score | summary | impact_assets
    """
    try:
        sheet = get_sheet("intel_events")
        if sheet is None:
            logger.warning("⚠️ Sheets disabled → skip write_intel_event")
            return True

        cols = [
            "date", "event_type", "location", "severity", "llm_risk_score", "summary", "impact_assets"
        ]
        row = [event_data.get(c, "") for c in cols]
        sheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info(f"✅ intel_events 新增成功：{event_data.get('event_type', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"❌ write_intel_event 失敗：{e}")
        return False


def read_intel_events() -> pd.DataFrame:
    """讀取 intel_events 分頁數據"""
    def _read():
        sheet = get_sheet("intel_events")
        return _worksheet_to_df(sheet) if sheet else pd.DataFrame()
    return _read_with_fallback("intel_events", _read)


def get_latest_intel_risk(hours: int = 24) -> Optional[float]:
    """
    取得最近 N 小時內的最高風險分數
    用於 M1 決策引擎
    """
    try:
        df = read_intel_events()
        if df.empty:
            return None

        # 篩選最近 N 小時的記錄
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 假設 'date' 欄位是 ISO 8601 格式
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df[df['date'] > cutoff_time]

        if df.empty:
            return None

        # 取最高的 llm_risk_score
        max_risk = pd.to_numeric(df['llm_risk_score'], errors='coerce').max()
        return max_risk if not pd.isna(max_risk) else None

    except Exception as e:
        logger.warning(f"⚠️ get_latest_intel_risk 失敗：{e}")
        return None


# ======================
# risk_incidents 讀寫
# ======================

def read_risk_incidents() -> pd.DataFrame:
    """讀取 risk_incidents 分頁（風控日誌）"""
    def _read():
        sheet = get_sheet("risk_incidents")
        return _worksheet_to_df(sheet) if sheet else pd.DataFrame()
    return _read_with_fallback("risk_incidents", _read)


def write_risk_incident(incident_dict: Dict[str, Any]) -> bool:
    """寫入風控事件到 risk_incidents sheet"""
    try:
        sheet = get_sheet("risk_incidents")
        if sheet is None:
            logger.warning("⚠️ Sheets disabled → skip write_risk_incident")
            return True

        cols = ["時間", "事件類型", "嚴重程度", "涉及策略", "描述", "推薦行動", "狀態"]
        row = [incident_dict.get(c, "") for c in cols]
        sheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info("✅ risk_incident 新增成功")
        return True
    except Exception as e:
        logger.error(f"❌ write_risk_incident 失敗：{e}")
        return False


# ======================
# macro_state 讀寫
# ======================

def read_macro_state() -> pd.DataFrame:
    """讀取 macro_state 分頁（宏觀經濟狀態）"""
    def _read():
        sheet = get_sheet("macro_state")
        return _worksheet_to_df(sheet) if sheet else pd.DataFrame()
    return _read_with_fallback("macro_state", _read)


def write_macro_state(state_dict: Dict[str, Any]) -> bool:
    """寫入或更新宏觀狀態到 macro_state sheet"""
    try:
        sheet = get_sheet("macro_state")
        if sheet is None:
            logger.warning("⚠️ Sheets disabled → skip write_macro_state")
            return True

        cols = ["更新時間", "risk_on", "VIX_level", "油價_影響", "最高_intel_risk", "市場_信號", "備註"]
        row = [state_dict.get(c, "") for c in cols]
        sheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info("✅ macro_state 更新成功")
        return True
    except Exception as e:
        logger.error(f"❌ write_macro_state 失敗：{e}")
        return False


# ======================
# portfolio_daily 讀取
# ======================

def read_portfolio_daily() -> pd.DataFrame:
    """讀取 portfolio_daily 分頁（每日各券商市值快照）"""
    def _read():
        sheet = get_sheet("portfolio_daily")
        return _worksheet_to_df(sheet) if sheet else pd.DataFrame()
    return _read_with_fallback("portfolio_daily", _read)


# ======================
# strategy_performance 版本管理
# ======================

def read_strategy_performance() -> pd.DataFrame:
    """讀取 strategy_performance 版本記錄"""
    def _read():
        sheet = get_sheet("strategy_performance")
        return _worksheet_to_df(sheet) if sheet else pd.DataFrame()
    return _read_with_fallback("strategy_performance", _read)

def append_strategy_version(version_dict: Dict[str, Any]) -> bool:
    """添加策略版本到 strategy_performance"""
    try:
        sheet = get_sheet("strategy_performance")
        if sheet is None:
            logger.warning("⚠️ Sheets disabled → skip append_strategy_version")
            return True

        cols = [
            "strategy_id", "strategy_name", "version", "run_date", "start_date", "end_date",
            "cagr_pct", "sharpe", "sortino", "mdd_pct", "calmar", "win_rate_pct",
            "trades", "avg_profit_pct", "avg_loss_pct", "ev_pct", "kelly_half", "kelly_full",
            "file_name", "uploaded_at"
        ]
        row = [version_dict.get(c, "") for c in cols]
        sheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info(f"✅ 策略版本已保存: {version_dict.get('strategy_name')} {version_dict.get('version')}")
        return True
    except Exception as e:
        logger.error(f"❌ 保存策略版本失敗：{e}")
        return False
