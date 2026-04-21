"""
decision_engine.py - Krystal AI Trading System 決策引擎

功能：
1. 從 Google Sheets intel_events 讀取 CRITICAL 風險事件
2. 根據事件類型，產生對應的交易訊號（JSON）
3. 目前規則：Oil_Supply_Shock_Risk + CRITICAL → BUY XLE (weight=0.2)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ============================================================================
# 導入依賴
# ============================================================================

try:
    from sheets_utils import read_intel_events
    SHEETS_OK = True
except Exception as e:
    logger.warning(f"sheets_utils 導入失敗，將使用離線緩存模式: {e}")
    SHEETS_OK = False

# ============================================================================
# 訊號規則定義
# ============================================================================

# 每條規則：匹配 event_type + severity → 產生 signal
SIGNAL_RULES: List[Dict] = [
    {
        "event_type": "Oil_Supply_Shock_Risk",
        "severity": "CRITICAL",
        "signal": {"ticker": "XLE", "action": "BUY", "weight": 0.2},
    },
]

# ============================================================================
# 主類
# ============================================================================

class DecisionEngine:
    """
    決策引擎：讀取 intel_events，依規則產生交易訊號。
    不含任何資料庫連線，純邏輯轉換。
    """

    def __init__(self, lookback_hours: int = 24):
        """
        Args:
            lookback_hours: 往回看幾小時內的事件（預設 24 小時）
        """
        self.lookback_hours = lookback_hours
        logger.info(f"[DecisionEngine] 初始化完成，lookback={lookback_hours}h")

    # ──────────────────────────────────────────────────────────────────────
    # 公開介面
    # ──────────────────────────────────────────────────────────────────────

    def run(self) -> List[Dict]:
        """
        主入口：讀取事件 → 篩選 CRITICAL → 匹配規則 → 回傳訊號列表

        Returns:
            List[Dict]: 訊號列表，每筆格式：
                {
                    "ticker": str,
                    "action": str,
                    "weight": float,
                    "source_event": str,
                    "generated_at": str (ISO 8601)
                }
        """
        logger.info("[DecisionEngine] 開始執行決策流程")

        events = self._fetch_critical_events()
        if not events:
            logger.info("[DecisionEngine] 無 CRITICAL 事件，不產生訊號")
            return []

        signals = self._evaluate_rules(events)
        logger.info(f"[DecisionEngine] 完成，共產生 {len(signals)} 個訊號")
        return signals

    # ──────────────────────────────────────────────────────────────────────
    # 內部方法
    # ──────────────────────────────────────────────────────────────────────

    def _fetch_critical_events(self) -> List[Dict]:
        """
        從 Google Sheets intel_events 讀取近 N 小時的 CRITICAL 事件。

        Returns:
            List[Dict]: 每筆包含 event_type, severity, date, summary 等欄位
        """
        try:
            df = read_intel_events()
        except Exception as e:
            logger.error(f"[DecisionEngine] 讀取 intel_events 失敗: {e}")
            return []

        if df is None or df.empty:
            logger.info("[DecisionEngine] intel_events 為空")
            return []

        # 確認必要欄位存在
        required_cols = {"event_type", "severity", "date"}
        missing = required_cols - set(df.columns)
        if missing:
            logger.error(f"[DecisionEngine] intel_events 缺少欄位: {missing}")
            return []

        # 篩選時間窗口
        cutoff = datetime.now() - timedelta(hours=self.lookback_hours)
        try:
            import pandas as pd
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df[df["date"] > cutoff]
        except Exception as e:
            logger.warning(f"[DecisionEngine] 時間篩選失敗，略過時間過濾: {e}")

        # 篩選 CRITICAL
        critical_df = df[df["severity"].str.upper() == "CRITICAL"]

        if critical_df.empty:
            logger.info(f"[DecisionEngine] 近 {self.lookback_hours}h 無 CRITICAL 事件")
            return []

        events = critical_df.to_dict(orient="records")
        logger.info(f"[DecisionEngine] 讀取到 {len(events)} 筆 CRITICAL 事件")
        for ev in events:
            logger.debug(
                f"  → [{ev.get('event_type')}] severity={ev.get('severity')} "
                f"date={ev.get('date')} summary={str(ev.get('summary', ''))[:60]}"
            )

        return events

    def _evaluate_rules(self, events: List[Dict]) -> List[Dict]:
        """
        對每個事件套用 SIGNAL_RULES，產生訊號。
        同一規則只會觸發一次（去重），避免重複下單。

        Args:
            events: CRITICAL 事件列表

        Returns:
            List[Dict]: 去重後的訊號列表
        """
        triggered_tickers = set()  # 防止同一 ticker 在同批事件中重複觸發
        signals = []
        now_iso = datetime.now().isoformat()

        for event in events:
            event_type = str(event.get("event_type", "")).strip()
            severity = str(event.get("severity", "")).strip().upper()

            for rule in SIGNAL_RULES:
                if event_type != rule["event_type"]:
                    continue
                if severity != rule["severity"]:
                    continue

                ticker = rule["signal"]["ticker"]
                if ticker in triggered_tickers:
                    logger.debug(
                        f"[DecisionEngine] {ticker} 訊號已存在，略過重複觸發 "
                        f"(event_type={event_type})"
                    )
                    continue

                signal = {
                    **rule["signal"],
                    "source_event": event_type,
                    "generated_at": now_iso,
                }
                signals.append(signal)
                triggered_tickers.add(ticker)

                logger.info(
                    f"[DecisionEngine] 訊號觸發: {signal['action']} {ticker} "
                    f"weight={signal['weight']} ← {event_type} ({severity})"
                )

        return signals


# ============================================================================
# 模組層級便利函式
# ============================================================================

def get_signals(lookback_hours: int = 24) -> List[Dict]:
    """
    快速呼叫入口。

    Args:
        lookback_hours: 往回看的時間窗口（小時）

    Returns:
        List[Dict]: 交易訊號列表
    """
    engine = DecisionEngine(lookback_hours=lookback_hours)
    return engine.run()


# ============================================================================
# 手動測試
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    import json

    signals = get_signals(lookback_hours=24)

    if signals:
        print("\n=== 產生的交易訊號 ===")
        for s in signals:
            print(json.dumps(s, ensure_ascii=False, indent=2))
    else:
        print("\n[無訊號] 近 24 小時內無 CRITICAL 觸發事件")