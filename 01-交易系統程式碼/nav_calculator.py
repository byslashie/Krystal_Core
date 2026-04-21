# nav_calculator.py
"""
NAV 與策略績效計算工具
- 計算報酬率、MDD
- 日報酬序列
- Sharpe Ratio
- 單一策略完整統計
"""

from typing import Optional, Dict, Any, List

import numpy as np
import pandas as pd


def _to_series(x) -> pd.Series:
    """把輸入轉成 float Series，並去掉 NaN。"""
    return pd.Series(x, dtype="float64").dropna()


# ========== 基本指標 ==========

def calculate_mdd(nav_series) -> float:
    """
    傳入 NAV 或 資產曲線，回傳 MDD（單位：%）
    """
    s = _to_series(nav_series)
    if s.empty:
        return 0.0

    cummax = s.cummax()
    drawdown = (s / cummax) - 1.0
    return float(drawdown.min() * 100)  # %


def calculate_return(start_value: float, end_value: float) -> float:
    """
    計算起點到終點的總報酬率（%）
    """
    if start_value <= 0:
        return 0.0
    return float((end_value / start_value - 1.0) * 100.0)


# ========== 日報酬 & Sharpe ==========

def calculate_daily_return(nav_series) -> pd.Series:
    """
    從 NAV 序列計算「日報酬率」。
    回傳單位為「小數」，例如 +1% = 0.01
    """
    s = _to_series(nav_series)
    return s.pct_change().dropna()


def calculate_sharpe(daily_returns, periods: int = 252) -> float:
    """
    計算夏普比率（無風險利率視為 0）
    daily_returns：日報酬（小數，例如 +1% = 0.01）
    periods：一年有幾個交易日（預設 252）
    """
    r = _to_series(daily_returns)
    if r.empty:
        return 0.0

    mean_annual = r.mean() * periods
    vol_annual = r.std(ddof=0) * np.sqrt(periods)

    if vol_annual <= 0:
        return 0.0
    return float(mean_annual / vol_annual)


# ========== 舊版簡易 stats（Dashboard 目前有在用） ==========

def strategy_stats(nav_df: pd.DataFrame, strategy_name: str) -> Optional[Dict[str, Any]]:
    """
    給定 daily_nav DataFrame（內含欄位：策略, NAV），
    回傳單一策略的：
        - 最新 NAV 倍數
        - 總報酬率（%）
        - MDD（%）
    （供 Dashboard 目前的 Strategy Performance 使用）
    """
    if nav_df is None or nav_df.empty:
        return None

    strat_nav = nav_df[nav_df["策略"] == strategy_name]["NAV"]
    strat_nav = pd.to_numeric(strat_nav, errors="coerce").dropna()

    if len(strat_nav) < 2:
        return None

    start = float(strat_nav.iloc[0])
    end = float(strat_nav.iloc[-1])

    ret_pct = calculate_return(start, end)
    mdd_pct = calculate_mdd(strat_nav)

    return {
        "strategy": strategy_name,
        "latest_value": end,
        "return_pct": ret_pct,
        "mdd_pct": mdd_pct,
    }


# ========== Day 11：完整統計用（可以之後接到 UI） ==========

def strategy_full_stats(nav_df: pd.DataFrame, strategy_name: str) -> Optional[Dict[str, Any]]:
    """
    計算單一策略的完整統計：
        - 起始 NAV
        - 結束 NAV
        - 報酬率（%）
        - MDD（%）
        - Sharpe
        - 日均報酬（%）
    目前先回傳「已格式化字串」，方便直接丟到表格。
    若之後要做更進階分析，可以再改成回傳數值。
    """
    if nav_df is None or nav_df.empty:
        return None

    strat = nav_df[nav_df["策略"] == strategy_name].copy()
    if strat.empty or "NAV" not in strat.columns:
        return None

    nav = pd.to_numeric(strat["NAV"], errors="coerce").dropna()
    if len(nav) < 2:
        return None

    start = float(nav.iloc[0])
    end = float(nav.iloc[-1])

    daily_ret = calculate_daily_return(nav)
    avg_daily = daily_ret.mean() * 100  # 轉成百分比
    sharpe = calculate_sharpe(daily_ret)

    return {
        "策略": strategy_name,
        "起始NAV": f"{start:,.2f}",
        "結束NAV": f"{end:,.2f}",
        "報酬率": f"{calculate_return(start, end):.2f}%",
        "MDD": f"{calculate_mdd(nav):.2f}%",
        "Sharpe": f"{sharpe:.2f}",
        "日均報酬": f"{avg_daily:.3f}%",
    }


if __name__ == "__main__":
    # 簡單自測
    demo = pd.Series([1.0, 1.01, 0.99, 1.03, 1.05])
    dr = calculate_daily_return(demo)
    print("Daily ret:", dr.values)
    print("Sharpe:", calculate_sharpe(dr))
    print("MDD:", calculate_mdd(demo))
