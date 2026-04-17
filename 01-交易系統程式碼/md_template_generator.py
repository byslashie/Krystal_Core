"""
MD 文件範本生成器 - 按照用戶格式生成完整的 frontmatter 和內容
"""

from datetime import datetime
from typing import Dict, Any

def generate_home_md(strategy_name: str, kpis: Dict[str, Any], meta: Dict[str, Any]) -> str:
    """
    生成 Home.md 文件（包含完整雙語 frontmatter）

    Args:
        strategy_name: 策略名稱
        kpis: KPI 字典
        meta: 元數據（包含 initial_capital, start_date, end_date 等）
    """

    # 提取 KPI 值（支持多種欄位名）
    def get_kpi(key, default=0, divisor=1):
        val = kpis.get(key) or kpis.get(key.replace('_', '')) or default
        return val / divisor if isinstance(val, (int, float)) else default

    cagr = get_kpi('cagr')
    sharpe = get_kpi('sharpe')
    sortino = get_kpi('sortino')
    mdd = get_kpi('mdd')
    calmar = get_kpi('calmar')
    kelly = get_kpi('kelly')
    win_rate = get_kpi('win_rate')
    profit_factor = get_kpi('profitFactor', 1)
    net_profit = get_kpi('netProfit')
    avg_profit_pct = get_kpi('avgWinPct')
    avg_loss_pct = get_kpi('avgLossPct')
    ev = get_kpi('ev')
    trades = int(kpis.get('profitableTrades', 0) + kpis.get('lossCount', 0))
    var95 = get_kpi('var95')
    cvar95 = get_kpi('cvar95')
    skewness = get_kpi('skewness')
    kurtosis = get_kpi('kurtosis')
    tail_right = get_kpi('tailRight')
    tail_left = get_kpi('tailLeft')

    # 从 meta 提取日期
    run_date = meta.get('run_date', datetime.now().strftime('%Y-%m-%d'))
    start_date = meta.get('start_date', '2008-06-02')
    end_date = meta.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    initial_capital = meta.get('initial_capital', 100000)

    # 計算額外指標
    avg_profit = kpis.get('avgWin', 0) if trades > 0 else 0
    avg_loss = kpis.get('avgLoss', 0) if trades > 0 else 0

    # Frontmatter（完整雙語）
    frontmatter = f"""---
title: {strategy_name} Backtest – v1.0
type: backtest
module: {strategy_name}
version: v1.1
tags:
  - backtest
  - baseline
run_date: {run_date}
start_date: {start_date}
end_date: {end_date}
kelly_full: {kelly:.4f}
凱利公式_Kelly: {kelly:.4f}
cagr: {cagr:.4f}
年化報酬率_CAGR: {cagr:.4f}
sharpe: {sharpe:.2f}
夏普比率_Sharpe: {sharpe:.2f}
sortino: {sortino:.2f}
索提諾比率_Sortino: {sortino:.2f}
mdd: {mdd:.4f}
最大回撤_MDD: {mdd:.4f}
calmar: {calmar:.2f}
卡瑪比率_Calmar: {calmar:.2f}
win_rate: {win_rate:.2f}
勝率_WinRate: {win_rate:.2f}
trades: {trades}
交易數量_Trades: {trades}
net_profit: {net_profit:.2f}
淨利_$: {net_profit:.2f}
avg_profit_pct: {avg_profit_pct * 100:.2f}
平均獲利_%: {avg_profit_pct * 100:.2f}
avg_loss_pct: {avg_loss_pct * 100:.2f}
平均損失_%: {avg_loss_pct * 100:.2f}
ev_pct: {ev * 100:.2f}
期望值EV_%: {ev * 100:.2f}
cagr_pct: {cagr * 100:.2f}
年化報酬率_CAGR%: {cagr * 100:.2f}
mdd_pct: {mdd * 100:.2f}
最大回撤_MDD%: {mdd * 100:.2f}
win_rate_pct: {win_rate * 100:.2f}
勝率_WinRate%: {win_rate * 100:.2f}
---
"""

    # 內容部分
    content = f"""
# 📊 Summary
* 區間：{start_date} → {end_date}（回測於 {run_date}）
* 成果：CAGR **{cagr * 100:.1f}%** | Sharpe **{sharpe:.1f}** | MDD **{mdd * 100:.1f}%** | Calmar **{calmar:.1f}** | 勝率 **{win_rate * 100:.1f}%** | 交易數 **{trades}**

## ⚙️ 核心品質指標

| 指標 | 數值 |
| --- | --- |
| 品質（勝率/交易數） | {win_rate * 100:.1f}% / {trades} |
| 淨利 ($) | ${net_profit:,.2f} |
| 初始投入 ($) | ${initial_capital:,.0f} |
| 最大投入報酬率 (%) | {(net_profit / initial_capital * 100):.2f}% |
| 賺賠比 | {profit_factor:.2f} |
| 期望值 ($) | ${ev * initial_capital:,.2f} |
| 平均每筆報酬 (%) | {avg_profit_pct * 100:.2f}% |
| Kelly 值 | {kelly * 100:.2f}% |
| 平均獲利 (%) | {avg_profit_pct * 100:.2f}% |
| 平均損失 (%) | {avg_loss_pct * 100:.2f}% |

### 平均獲利與虧損

| 指標 | 數值 |
| --- | --- |
| 平均獲利 | {avg_profit:,.2f} |
| 平均虧損 | {avg_loss:,.2f} |

## 📑 風險統計與尾部摘要

| 指標 | 參數 | 數值 | 解讀 |
| --- | --- | --- | --- |
| VaR | 95% | {var95 * 100:.2f}% | 在 95% 置信水準下的最大可能單期損失 |
| CVaR | 95% | {cvar95 * 100:.2f}% | 超過 VaR 的最壞情況下，平均損失 |
| 右尾 | Σ(≥q0.95) | {tail_right * 100:.1f}% | 最佳 5% 的極端大賺事件總貢獻 |
| 左尾 | Σ(≤q0.05) | {tail_left * 100:.1f}% | 最差 5% 的極端大虧事件總損失 |
| 偏態 | Skew | {skewness:.2f} | {'分布偏右，正極端貢獻大' if skewness > 0 else '分布偏左，負極端貢獻大'} |
| 超峰度 | Excess Kurt | {kurtosis:.2f} | 尾部肥厚程度 |

## 策略描述
（在此添加策略邏輯和參數說明）

## 版本歷史
- v1.0：{run_date} 初始導入（Staging）
"""

    return frontmatter + content
