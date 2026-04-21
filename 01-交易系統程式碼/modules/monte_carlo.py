import numpy as np


def run_monte_carlo(trade_pnls, initial_capital: float, n_simulations: int = 50000, seed: int = 42):
    """
    蒙地卡羅模擬：打亂歷史交易順序，模擬不同路徑（Permutation Bootstrap）

    Args:
        trade_pnls:       各筆交易損益陣列
        initial_capital:  初始資金
        n_simulations:    模擬次數（預設 50,000）
        seed:             隨機種子

    Returns:
        dict with results, or None if insufficient data (< 5 trades).
    """
    arr = np.asarray(trade_pnls, dtype=float)
    arr = arr[arr != 0]          # 濾掉佔位的零值
    n_trades = len(arr)
    if n_trades < 5:
        return None

    rng = np.random.default_rng(seed)

    # 分批執行，控制記憶體上限（每批最多 10,000 條路徑）
    chunk_size = 10_000
    all_finals: list[np.ndarray] = []
    all_mdds: list[np.ndarray] = []

    remaining = n_simulations
    while remaining > 0:
        batch = min(chunk_size, remaining)

        # 打亂重組：對每條路徑隨機排列交易順序
        rand_m = rng.random((batch, n_trades))
        idx = np.argsort(rand_m, axis=1)
        shuffled = arr[idx]                            # (batch, n_trades)

        # 計算每條路徑的資產曲線
        cum_pnl = np.cumsum(shuffled, axis=1)
        equity = np.hstack([
            np.full((batch, 1), initial_capital),
            initial_capital + cum_pnl
        ])                                             # (batch, n_trades+1)

        all_finals.append(equity[:, -1])

        # 最大回撤（絕對金額，負值）
        running_max = np.maximum.accumulate(equity, axis=1)
        all_mdds.append((equity - running_max).min(axis=1))

        remaining -= batch

    final_assets = np.concatenate(all_finals)
    max_drawdowns = np.concatenate(all_mdds)

    return {
        # 最終資產統計
        "final_median": float(np.median(final_assets)),
        "final_p5":     float(np.percentile(final_assets, 5)),    # 最差 5%
        "final_p95":    float(np.percentile(final_assets, 95)),   # 最好 5%
        "final_p1":     float(np.percentile(final_assets, 1)),
        "final_p99":    float(np.percentile(final_assets, 99)),
        # 最大回撤統計（負值）
        "mdd_median":   float(np.median(max_drawdowns)),
        "mdd_p5":       float(np.percentile(max_drawdowns, 5)),   # 最差 5% 回撤
        "mdd_p95":      float(np.percentile(max_drawdowns, 95)),  # 最好 5% 回撤
        # 虧損機率
        "ruin_prob":    float(np.mean(final_assets < initial_capital) * 100),
        # 完整分布（供繪圖）
        "final_assets":  final_assets,
        "max_drawdowns": max_drawdowns,
        # 元資訊
        "n_simulations": n_simulations,
        "n_trades":      n_trades,
        "initial_capital": initial_capital,
    }
