"""
risk_control.py — 風控引擎
讀取真實帳戶資料，執行以下檢查：
  1. MDD（最大回撤）→ 超過 -10% 觸發暫停
  2. Daily Stop-Loss（每日虧損）→ 超過 -5% 觸發暫停
  3. Position Limit（單一持倉集中度）→ 超過 20% NAV 觸發減倉警告
  4. 所有警告自動寫入 risk_incidents sheet

閾值依 CLAUDE.md 規則：MDD -10%、每日 -5%、單倉 20%
注意：本模組只輸出訊號，不自動執行交易（需人工確認）
"""

import logging
import sys
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import pandas as pd

# 確保可以 import 上層模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nav_calculator import calculate_mdd
from sheets_utils import (
    read_daily_nav,
    read_sheet_data_with_cache,
    write_risk_incident,
)

logger = logging.getLogger(__name__)

# ── 預設閾值（依 CLAUDE.md） ──────────────────────────────────────────
MDD_THRESHOLD = -10.0        # % 最大回撤觸發暫停
DAILY_LOSS_THRESHOLD = -5.0  # % 每日虧損上限
POSITION_LIMIT_PCT = 20.0    # % 單一持倉佔總 NAV 上限
WARNING_BUFFER = 0.7         # 達到閾值 70% 時升為 WARNING（例如 MDD 達 -7% 先警告）


# ── 資料結構 ──────────────────────────────────────────────────────────

@dataclass
class RiskSignal:
    type: str           # MDD / DAILY_LOSS / POSITION_LIMIT
    level: str          # OK / WARNING / DANGER
    value: float        # 當前數值（%）
    threshold: float    # 閾值（%）
    action: str         # NONE / ALERT / STOP_TRADING / REDUCE_POSITION
    message: str
    timestamp: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "level": self.level,
            "value": self.value,
            "threshold": self.threshold,
            "action": self.action,
            "message": self.message,
            "timestamp": self.timestamp,
        }


@dataclass
class RiskReport:
    signals: List[RiskSignal]
    overall_level: str          # OK / WARNING / DANGER
    should_stop_trading: bool
    checked_at: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    def to_dict(self) -> dict:
        return {
            "overall_level": self.overall_level,
            "should_stop_trading": self.should_stop_trading,
            "checked_at": self.checked_at,
            "signals": [s.to_dict() for s in self.signals],
        }


# ── 主要類別 ──────────────────────────────────────────────────────────

class RiskController:
    def __init__(
        self,
        mdd_threshold: float = MDD_THRESHOLD,
        daily_loss_threshold: float = DAILY_LOSS_THRESHOLD,
        position_limit_pct: float = POSITION_LIMIT_PCT,
        warning_buffer: float = WARNING_BUFFER,
    ):
        self.mdd_threshold = mdd_threshold
        self.daily_loss_threshold = daily_loss_threshold
        self.position_limit_pct = position_limit_pct
        self.warning_buffer = warning_buffer

    # ── 1. MDD 檢查 ───────────────────────────────────────────────────

    def check_mdd(self) -> RiskSignal:
        """
        從 broker_snapshot 或 daily_nav 取得 NAV 序列，計算 MDD。
        broker_snapshot 優先（帳戶總資產更準確）。
        """
        try:
            nav_series = self._get_nav_series()
            if nav_series is None or len(nav_series) < 2:
                return self._ok("MDD", 0.0, self.mdd_threshold, "NAV 資料不足（< 2 筆）")

            mdd = calculate_mdd(nav_series)
            return self._evaluate(
                "MDD", mdd, self.mdd_threshold,
                is_upper_bound=False,
                danger_action="STOP_TRADING",
            )
        except Exception as e:
            logger.error(f"check_mdd 失敗：{e}")
            return self._ok("MDD", 0.0, self.mdd_threshold, f"計算錯誤：{e}")

    # ── 2. 每日虧損檢查 ───────────────────────────────────────────────

    def check_daily_loss(self) -> RiskSignal:
        """
        比較最近兩個交易日的 NAV，計算今日損益 %。
        """
        try:
            nav_series = self._get_nav_series()
            if nav_series is None or len(nav_series) < 2:
                return self._ok("DAILY_LOSS", 0.0, self.daily_loss_threshold, "NAV 資料不足")

            yesterday = float(nav_series.iloc[-2])
            today = float(nav_series.iloc[-1])

            if yesterday <= 0:
                return self._ok("DAILY_LOSS", 0.0, self.daily_loss_threshold, "昨日 NAV 異常（≤ 0）")

            daily_pct = (today / yesterday - 1.0) * 100.0
            return self._evaluate(
                "DAILY_LOSS", daily_pct, self.daily_loss_threshold,
                is_upper_bound=False,
                danger_action="STOP_TRADING",
            )
        except Exception as e:
            logger.error(f"check_daily_loss 失敗：{e}")
            return self._ok("DAILY_LOSS", 0.0, self.daily_loss_threshold, f"計算錯誤：{e}")

    # ── 3. 單一持倉集中度 ─────────────────────────────────────────────

    def check_position_limits(self) -> List[RiskSignal]:
        """
        讀取 broker_positions 最新快照，計算每筆持倉市值佔總 NAV 比例。
        超過 20% 的持倉回傳 WARNING 或 DANGER 訊號。
        """
        signals: List[RiskSignal] = []
        try:
            pos_df = read_sheet_data_with_cache("broker_positions")
            if pos_df.empty:
                return [self._ok("POSITION_LIMIT", 0.0, self.position_limit_pct, "無持倉資料")]

            # 找欄位
            mv_col = next(
                (c for c in pos_df.columns if "市值" in c or c.lower() == "marketvalue"), None
            )
            sym_col = next(
                (c for c in pos_df.columns if "標的" in c or "symbol" in c.lower()), None
            )

            if not mv_col:
                return [self._ok("POSITION_LIMIT", 0.0, self.position_limit_pct, "找不到市值欄位")]

            # 只取最新時間戳的快照
            if "時間" in pos_df.columns:
                pos_df["時間"] = pd.to_datetime(pos_df["時間"], errors="coerce")
                latest = pos_df["時間"].max()
                pos_df = pos_df[pos_df["時間"] == latest].copy()

            pos_df[mv_col] = pd.to_numeric(pos_df[mv_col], errors="coerce").fillna(0)
            total_nav = pos_df[mv_col].sum()

            if total_nav <= 0:
                return [self._ok("POSITION_LIMIT", 0.0, self.position_limit_pct, "總市值為零")]

            for _, row in pos_df.iterrows():
                mv = float(row[mv_col])
                if mv <= 0:
                    continue
                symbol = str(row[sym_col]) if sym_col else "unknown"
                pct = (mv / total_nav) * 100.0

                sig = self._evaluate(
                    "POSITION_LIMIT", pct, self.position_limit_pct,
                    is_upper_bound=True,
                    danger_action="REDUCE_POSITION",
                    context=symbol,
                )
                if sig.level != "OK":
                    signals.append(sig)

            if not signals:
                signals.append(
                    self._ok("POSITION_LIMIT", 0.0, self.position_limit_pct, "所有持倉集中度正常")
                )

        except Exception as e:
            logger.error(f"check_position_limits 失敗：{e}")
            signals.append(
                self._ok("POSITION_LIMIT", 0.0, self.position_limit_pct, f"計算錯誤：{e}")
            )

        return signals

    # ── 4. 全部執行 ───────────────────────────────────────────────────

    def run_all_checks(self) -> RiskReport:
        """執行所有風控檢查，回傳 RiskReport。WARNING 以上自動寫入 risk_incidents。"""
        mdd_sig = self.check_mdd()
        daily_sig = self.check_daily_loss()
        pos_sigs = self.check_position_limits()

        all_signals = [mdd_sig, daily_sig] + pos_sigs

        levels = [s.level for s in all_signals]
        if "DANGER" in levels:
            overall = "DANGER"
        elif "WARNING" in levels:
            overall = "WARNING"
        else:
            overall = "OK"

        should_stop = any(s.action == "STOP_TRADING" for s in all_signals)

        # 寫入風控日誌（只記錄 WARNING 以上）
        for sig in all_signals:
            if sig.level != "OK":
                self._log_incident(sig)

        return RiskReport(
            signals=all_signals,
            overall_level=overall,
            should_stop_trading=should_stop,
        )

    # ── 內部工具 ──────────────────────────────────────────────────────

    def _get_nav_series(self) -> Optional[pd.Series]:
        """
        優先從 broker_snapshot 取帳戶總資產時間序列；
        若無則 fallback 到 daily_nav 的 NAV 欄位每日加總。
        """
        # 方法 A：broker_snapshot（帳戶總資產，每日最後一筆）
        try:
            snap_df = read_sheet_data_with_cache("broker_snapshot")
            if not snap_df.empty and "帳戶總資產" in snap_df.columns:
                snap_df["時間"] = pd.to_datetime(snap_df["時間"], errors="coerce")
                snap_df = snap_df.dropna(subset=["時間"])
                snap_df["date"] = snap_df["時間"].dt.date
                snap_df["帳戶總資產"] = pd.to_numeric(snap_df["帳戶總資產"], errors="coerce")
                series = snap_df.groupby("date")["帳戶總資產"].last().sort_index()
                if len(series) >= 2:
                    return series
        except Exception as e:
            logger.warning(f"broker_snapshot 讀取失敗，嘗試 daily_nav：{e}")

        # 方法 B：daily_nav（策略 NAV 每日加總）
        try:
            df = read_daily_nav()
            if not df.empty and "NAV" in df.columns and "日期" in df.columns:
                df["NAV"] = pd.to_numeric(df["NAV"], errors="coerce")
                series = df.groupby("日期")["NAV"].sum().sort_index()
                if len(series) >= 2:
                    return series
        except Exception as e:
            logger.warning(f"daily_nav 讀取失敗：{e}")

        return None

    def _evaluate(
        self,
        type_: str,
        value: float,
        threshold: float,
        is_upper_bound: bool = False,
        danger_action: str = "STOP_TRADING",
        context: str = "",
    ) -> RiskSignal:
        """
        is_upper_bound=False → 值越小越危險（MDD, DAILY_LOSS）
        is_upper_bound=True  → 值越大越危險（POSITION_LIMIT）
        warning_buffer=0.7   → 達到閾值 70% 時升 WARNING
        """
        if not is_upper_bound:
            warn_line = threshold * self.warning_buffer  # 例如 -10% * 0.7 = -7%
            if value <= threshold:
                level, action = "DANGER", danger_action
            elif value <= warn_line:
                level, action = "WARNING", "ALERT"
            else:
                level, action = "OK", "NONE"
        else:
            warn_line = threshold * self.warning_buffer  # 例如 20% * 0.7 = 14%
            if value >= threshold:
                level, action = "DANGER", danger_action
            elif value >= warn_line:
                level, action = "WARNING", "ALERT"
            else:
                level, action = "OK", "NONE"

        ctx = f"[{context}] " if context else ""
        msg = f"{ctx}{type_} {value:+.2f}%（閾值 {threshold:+.1f}%）→ {level}"

        return RiskSignal(
            type=type_, level=level, value=round(value, 2),
            threshold=threshold, action=action, message=msg,
        )

    def _ok(self, type_: str, value: float, threshold: float, reason: str = "") -> RiskSignal:
        return RiskSignal(
            type=type_, level="OK", value=value, threshold=threshold,
            action="NONE",
            message=f"{type_} 正常" + (f"（{reason}）" if reason else ""),
        )

    def _log_incident(self, sig: RiskSignal):
        """WARNING / DANGER 自動寫入 risk_incidents sheet"""
        try:
            write_risk_incident({
                "時間": sig.timestamp,
                "事件類型": sig.type,
                "嚴重程度": sig.level,
                "涉及策略": "整體帳戶",
                "描述": sig.message,
                "推薦行動": sig.action,
                "狀態": "待處理",
            })
        except Exception as e:
            logger.warning(f"risk_incident 寫入失敗（不影響系統運作）：{e}")


# ── 全局實例（供 Flask 直接 import） ──────────────────────────────────

_controller = RiskController()


def get_risk_report() -> dict:
    """執行全部風控檢查，回傳完整 report dict（供 Flask API 使用）"""
    return _controller.run_all_checks().to_dict()


def get_risk_metrics() -> dict:
    """回傳精簡版風控指標（相容舊 /api/risk-metrics 格式）"""
    report = _controller.run_all_checks()
    mdd_sig = next((s for s in report.signals if s.type == "MDD"), None)
    daily_sig = next((s for s in report.signals if s.type == "DAILY_LOSS"), None)
    pos_sigs = [s for s in report.signals if s.type == "POSITION_LIMIT" and s.level != "OK"]

    return {
        "overall_risk_level": report.overall_level,
        "should_stop_trading": report.should_stop_trading,
        "max_drawdown": mdd_sig.value if mdd_sig else 0.0,
        "daily_pnl_pct": daily_sig.value if daily_sig else 0.0,
        "position_alerts": len(pos_sigs),
        "checked_at": report.checked_at,
    }


# ── 直接執行時的簡單測試 ──────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== 風控引擎測試 ===")
    report = _controller.run_all_checks()
    print(f"整體風險等級：{report.overall_level}")
    print(f"是否暫停交易：{report.should_stop_trading}")
    for sig in report.signals:
        print(f"  [{sig.level}] {sig.message}")
