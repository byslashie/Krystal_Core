# FinLab AI 量化回測系統 — 完整分析報告

> 來源：https://www.finlab.finance/blog/ai-quant-research
> 文章標題：AI 量化研究：5 個提示詞打造年化 48% 的選股系統
> 分析時間：2026-04-08

---

## 🎯 策略總覽：5 個 Skill 疊加架構

文章核心概念：透過 5 個 AI 提示詞（Skill），像「積木」一樣逐步堆疊選股條件，最終組合出一個高效益策略。

### 最終複合策略績效

| 指標 | 數值 |
|------|------|
| 年化報酬率 | **+48.17%** |
| 夏普比率 | **1.69** |
| 最大回撤 | **-30.38%** |

---

## 📋 Skill 1：營收創新高選股（基礎選股模組）

**AI 提示詞邏輯：**
> 幫我找出近 3 個月平均營收創 12 個月新高的股票，要有足夠的流動性（20 日平均成交量 > 500 張）

---

## 🗂️ 回測組件架構：2 大面板 × 各 5 個分頁

FinLab 的回測組件包含頂部 **5 個主類別標籤**，目前從截圖確認兩個大面板：

### 主類別標籤（共用於兩個面板）

| 類別名稱 | 評分 | 狀態 |
|----------|------|------|
| 獲利能力 | 40 | 🟡 部分達標 |
| 抗風險能力 | 33 | 🔴 未達標 |
| 風險報酬比 | 0 | 🔴 未達標 |
| 勝率期望值 | 40 | 🟡 部分達標 |
| 交易流動性 | 100 | 🟢 完全達標 |

---

## 📊 面板一：獲利能力（Profitability）的 5 個分頁

### 頂部 KPI 指標卡（共用）

| 指標名稱 | 實際值 | 門檻 | 狀態 |
|----------|--------|------|------|
| 年度回報 | **+21.0%** | 需 ≥ 15% | 🟢 達標 |
| ALPHA | **+4.9%** | 需 ≥ 10% | 🔴 未達 |
| BETA | **1.00** | 需介於 0~0.8 | 🔴 超標 |
| 平均持有股數 | **156 檔** | 需 ≥ 5 檔 | 🟢 達標 |
| 最多持有股數 | **405 檔** | 需 ≤ 20 檔 | 🔴 超標 |

> 🟢 綠點 = 達標、🔴 紅點 = 未達標

---

### 分頁 1：歷史績效（Historical Performance）

**圖表類型：** 累積報酬走勢折線圖

| 項目 | 說明 |
|------|------|
| 紫色線 | 策略累積報酬（最終 +714.42%） |
| 灰色線 | 大盤（加權指數）累積報酬（最終 +422.16%） |
| X 軸 | 時間（年份，如 2014 ~ 2026） |
| Y 軸 | 累積報酬百分比（0% ~ 800%+） |
| 互動功能 | 可點選下方年份按鈕聚焦特定年度 |

**說明文字（頁面原文）：**
> 策略的累計報酬走勢圖。紫色線為策略，灰色線為大盤。年化報酬率為 +21.0%，相對大盤產生了 +4.9% 的 Alpha，期間平均持有 156 股票。點選下方年份按鈕可聚焦到特定年度的表現。

---

### 分頁 2：月報酬（Monthly Returns）

**圖表類型：** 月度報酬熱力圖（Heatmap）

| 項目 | 說明 |
|------|------|
| 縱軸 | 年份（2014 ~ 2026） |
| 橫軸 | 月份（Jan ~ Dec）＋ 全年合計欄 |
| 最後一行 | 各月的歷史平均值 |
| 深綠色格 | 高正報酬月份 |
| 淺綠色格 | 小漲月份 |
| 淺紅色格 | 小跌月份 |
| 深紅色格 | 大跌月份 |

**用途：** 找出策略的「季節性規律」（哪個月容易大漲或大跌）

---

### 分頁 3：持股報酬（Stock Returns）

**圖表類型：** 橫向柱狀圖（單次交易報酬分佈）

| 項目 | 說明 |
|------|------|
| X 軸 | 單筆交易報酬率（%） |
| Y 軸 | 個別股票 / 交易次數 |
| 最高報酬 | +50% ~ +80%（強勢股抓取） |
| 用途 | 判斷報酬是否集中在少數暴漲股 |

---

### 分頁 4：與大盤年報酬比較（Annual Return Comparison）

**圖表類型：** 分組柱狀圖（每年策略 vs 大盤）

| 顏色 | 含義 |
|------|------|
| 綠色柱 | 策略勝過大盤的年份 |
| 紅色柱 | 策略輸給大盤的年份 |

---

### 分頁 5：超額報酬（Excess Returns / Alpha Curve）

**圖表類型：** 累積超額報酬走勢線圖

| 項目 | 說明 |
|------|------|
| Y 軸 | 策略相對大盤的超額績效（%） |
| X 軸 | 時間（年份） |
| 曲線向上 | 持續跑贏大盤 |
| 曲線向下 | 跑輸大盤 |
| 用途 | 判斷 Alpha 是否長年穩定存在 |

---

## 🛡️ 面板二：抗風險能力（Risk Management）的 5 個分頁

### 頂部 KPI 指標卡（共用）

| 指標名稱 | 實際值 | 門檻 | 狀態 |
|----------|--------|------|------|
| 最大回撤 | **-37.1%** | 需 < 30% | 🔴 未達標 |
| 平均回檔幅度 | **-3.4%** | 需 < 10% | 🟢 達標 |
| 平均回檔時間 | **28.08 天** | 需 < 40 天 | 🟢 達標 |
| Value at Risk | **-9.7%** | 需 < 7% | 🔴 未達標 |
| Conditional VaR | **-12.6%** | 需 < 10% | 🔴 未達標 |

---

### 分頁 1：虧損歷史（Drawdown History）

**圖表類型：** 雙層區域填充圖 + 大盤折線圖

| 項目 | 說明 |
|------|------|
| 紫色填充區域 | 策略從高點的回撤幅度 |
| 灰色線 | 大盤同期累積報酬 |
| 特殊標記 | 恢復至新高所需天數（如 **720 天**） |

**歷史最大回撤前 5 名：**

| 排名 | 發生時期 | 最大回撤 |
|------|----------|----------|
| 1 | 2018 年 | **-37.1%** |
| 2 | 2024 年 | **-35.6%** |
| 3 | 2021 年 | **-30.7%** |
| 4 | 2015 年 | **-27.4%** |
| 5 | 2021 年 | **-21.4%** |

**說明文字（頁面原文）：**
> 歷史上最嚴重的回撤時期。最大回撤為 -37.1%，平均回撤持續 28 天。點選上方卡片可查看各次回撤的詳細走勢，並觀察策略從低點恢復到新高所需的時間。

---

### 分頁 2：持股報酬（Risk 視角下的虧損分佈）

**圖表類型：** 虧損部位的柱狀分佈圖

| 用途 | 說明 |
|------|------|
| 主要目的 | 觀察單一股票虧損是否失控 |
| 關注焦點 | 最大單筆虧損幅度 |

---

### 分頁 3：跌幅排名（Drawdown Ranking）

**圖表類型：** 橫向條狀排名圖

| 用途 | 說明 |
|------|------|
| 主要目的 | 列出歷史上最嚴重的跌幅事件 |
| 可識別 | 策略在極端行情（如 2020 疫情、2022 通膨）的承受力 |

---

### 分頁 4：再次創新高時間排名（Recovery Time Ranking）

**圖表類型：** 按天數排列的條狀圖

| 統計項目 | 數值 |
|----------|------|
| 最長恢復時間 | **720 天**（2018 年那次回撤） |
| 大部分回撤恢復時間 | **30 天內** |
| 用途 | 評估最壞情況下投資者需要「等多久才能回本」 |

---

### 分頁 5：回檔幅度（Drawdown Distribution）

**圖表類型：** 回撤幅度頻率分佈直方圖

| 分佈特徵 | 說明 |
|----------|------|
| 最頻繁回撤 | -1% ~ -10%（日常波動） |
| 極端回撤（>-30%） | 極少發生 |
| 用途 | 理解策略的「典型回撤幅度」 |

---

---

## 📐 面板三：風險報酬比（Risk-Reward Ratio）的 4 個分頁

衡量策略在承擔風險時所換取的報酬**品質與效率**。

### 頂部 KPI 指標卡（共用）

| 指標名稱 | 實際值 | 門檻 | 狀態 |
|----------|--------|------|------|
| 夏普值（Sharpe Ratio） | **0.91** | 需 > 1.3 | 🔴 未達標 |
| Sortino Ratio | **1.34** | 需 > 1.8 | 🔴 未達標 |
| Calmar Ratio | **0.57** | 需 > 0.9 | 🔴 未達標 |
| Profit Factor | **1.48** | 需 > 1.5 | 🔴 未達標 |
| Tail Ratio | **0.82** | 需 > 1.0 | 🔴 未達標 |

> 此面板整體評分為 **0**，是 Skill 1 策略最弱的面向，代表風報比效率偏低

---

### 分頁 1：夏普值（Sharpe Ratio）

**圖表類型：** 滾動夏普值折線圖（策略 vs 大盤）

| 項目 | 數值 |
|------|------|
| 策略滾動夏普值（當前） | **1.65**（紫色線） |
| 大盤當前夏普值 | **1.80**（灰色線） |
| Y 軸範圍 | -1.00 ~ 3.00 |
| X 軸 | 2022年 → 2026年 |
| 策略夏普大於大盤時間 | **50.99%**（即 5/11 年） |
| 互動功能 | 可切換「年 / 季 / 月」時間粒度 |

**說明文字（頁面原文）：**
> 滾動夏普比率為 0.91，衡量每承受一單位風險能獲得多少報酬。值越高代表風險調整後表現越好。右圖為每年的夏普值與大盤比較，可觀察策略在不同年份的風報比穩定性。

---

### 分頁 2：Tail Ratio

**圖表類型：** 滾動 Tail Ratio 折線圖（策略 vs 大盤）

| 項目 | 數值 |
|------|------|
| 策略 Tail Ratio（當前） | **0.95** |
| Y 軸範圍 | 0.60 ~ 1.40 |
| 策略大於大盤的時間 | **11.39%**（極少） |

**說明：** Tail Ratio = 右尾（獲利端）極端值 ÷ 左尾（虧損端）極端值；小於 1 代表極端虧損大於極端獲利，表示策略對尾部風險的保護不足

---

### 分頁 3：策略報酬率波動（Volatility）

**圖表類型：** 滾動波動度折線圖（策略 vs 大盤）

| 項目 | 數值 |
|------|------|
| 策略波動度 | **0.05** |
| 大盤波動度 | **0.03** |
| 策略波動大於大盤時間 | **77.10%** |

**說明：** 策略波動度持續高於大盤，代表在高報酬背後承擔了更大的日內震盪風險

---

### 分頁 4：策略與大盤相關性

**圖表類型：** 滾動相關係數折線圖（Correlation Curve）

| 項目 | 數值 |
|------|------|
| 當前相關係數 | **0.85**（高度正相關） |
| Y 軸範圍 | 0.85 ~ 1.00 |
| 趨勢 | 近年相關性持續升高 |

**說明文字（頁面原文）：**
> 策略報酬與大盤報酬的滾動相關係數。值接近 1 代表高度正相關，接近 0 代表策略走勢較獨立。低相關性的策略在資產配置中特別有價值，能有效分散風險。

---

## 🎯 面板四：勝率期望值（Win Rate & Expectancy）的 4 個分頁

分析每一筆交易的**統計特徵**與系統的**容錯空間**。

### 頂部 KPI 指標卡（共用）

| 指標名稱 | 實際值 | 門檻 | 狀態 |
|----------|--------|------|------|
| 逐筆交易勝率 | **49.0%** | 需 > 55% | 🔴 未達標 |
| 使用策略 12 個月勝率 | **75.4%** | 需 > 70% | 🟢 達標 |
| 期望值（單筆） | **+1.9%** | 需 ≥ 2% | 🔴 未達標 |
| 最大不利偏移（MAE） | **-7.1%** | 需 < 10% | 🟢 達標 |
| 最大有利偏移（MFE） | **+9.4%** | 需 ≥ 10% | 🔴 未達標 |

---

### 分頁 1：報酬分布（Reward Distribution）

**圖表類型：** 單筆交易報酬率直方圖

| 項目 | 數值 |
|------|------|
| 整體勝率 | **49.0%** |
| 單筆期望值 | **+1.9%** |
| 風險警示 | 有 **5% 的機率**，交易將面臨 **-11.6% 以上**的虧損 |
| 分佈形狀 | 右尾偏長（正偏態），代表少數強勢股貢獻大額獲利 |

**說明文字（頁面原文）：**
> 策略所有交易的報酬分布直方圖。整體勝率為 49.0%，單筆期望值為 +1.9%。可觀察報酬是否呈現正偏態（右尾較長），以及大部分交易集中在哪個報酬區間。

---

### 分頁 2：模擬停損（Stop Loss Simulation）

**圖表類型：** 停損點 vs 總報酬／MDD 雙折線圖

| 項目 | 數值 |
|------|------|
| 最佳模擬停損點 | **-35%** |
| 說明 | 設定 -35% 停損時，報酬與回撤的平衡最佳 |

> **用途：** 測試「如果加入停損機制，什麼幅度最有效？」

---

### 分頁 3：模擬停利（Take Profit Simulation）

**圖表類型：** 停利點 vs 總報酬折線圖

| 項目 | 數值 |
|------|------|
| 最佳模擬停利點 | **+40%** |
| 說明 | 設定 +40% 停利能鎖住最優報酬 |

> **用途：** 找出何時「停利」能最大化整體績效

---

### 分頁 4：交易最大偏移（MFE / MAE）

**圖表類型：** 散點圖（每筆交易的最高點 vs 最低點）

| 指標 | 策略 | 大盤比較 |
|------|------|----------|
| 平均最有利偏移（MFE） | **+9.4%** | 大盤 +10.3% |
| 平均最不利偏移（MAE） | **-7.1%** | 大盤 -9.1% |

> **用途：** 分析策略的平均「浮盈空間」與「浮虧忍受度」，輔助設定合理的停損停利範圍

---

## 💧 面板五：交易流動性（Trading Liquidity）的 3 個分頁

評估策略在**真實市場執行時的可行性**與資金容量承載力。

### 頂部 KPI 指標卡（共用）

| 指標名稱 | 實際值 | 門檻 | 狀態 |
|----------|--------|------|------|
| 平均胃納量 | **5,353 萬** | 需 ≥ 50 萬 | 🟢 達標 |
| 處置股比例 | **0.4%** | 需 < 5% | 🟢 達標 |
| 警告股比例 | **4.5%** | 需 < 5% | 🟢 達標（邊緣） |
| 全額交付股比例 | **0.1%** | 需 < 5% | 🟢 達標 |
| 買在漲停比例 | **2.1%** | 需 < 5% | 🟢 達標 |

> 此面板評分為 **100**，是 5 個面板中**唯一滿分**的項目，代表策略的標的流動性非常充足

---

### 分頁 1：投資組合胃納量（Portfolio Capacity）

**圖表類型：** 資金規模 × 低流動性遭遇率曲線圖

| 資金規模 | 遭遇低流動性機率 |
|----------|------------------|
| **1,000 萬（10M）** | **0.2%**（極低） |
| 更大規模 | 逐漸升高 |

**說明：** 此策略理論上能支撐至少 **1,000 萬**的資金，不需要擔心流動性衝擊

---

### 分頁 2：進場當天成交量

**圖表類型：** 成交量分佈柱狀圖

| 成交量門檻 | 交易佔比 |
|-----------|----------|
| ≥ 1,000 張 | **98.4%** |
| < 1,000 張 | 1.6% |

**說明：** 幾乎所有進場標的在買入當天的成交量都很充足，不會有「買不到」的問題

---

### 分頁 3：出場當天成交量

**圖表類型：** 成交量分佈柱狀圖

| 成交量門檻 | 交易佔比 |
|-----------|----------|
| ≥ 1,000 張 | **96.6%** |
| < 1,000 張 | 3.4% |

**說明：** 出場流動性略低於進場，但整體仍非常充足，策略不存在「賣不掉」的流動性風險

---

## 🔄 5 個 Skill 的完整堆疊邏輯

```
Skill 1（基礎篩選）
  → 3 個月平均營收創 12 個月新高
  → 20 日平均成交量 > 500 張

Skill 2（法人籌碼）
  → 投信連續買超 5 天以上

Skill 3（技術趨勢確認）
  → RSI > 50 && 股價在 60MA 以上

Skill 4（價值安全邊際）
  → PE < 15 && PB < 2

Skill 5（穩定性加強）
  → sustain(2) 函數：營收創高需連續 2 個月才進場
```

---

## 💻 套用至 Krystal 系統的實作代碼

### 1. 指標計算器

```python
import pandas as pd
import numpy as np

class BacktestMetrics:
    """FinLab 風格回測指標計算器"""

    def __init__(self, strategy_returns: pd.Series,
                 benchmark_returns: pd.Series,
                 risk_free_rate: float = 0.02):
        self.strategy = strategy_returns
        self.benchmark = benchmark_returns
        self.rf = risk_free_rate / 252
        self.n_years = len(strategy_returns) / 252
        self.cum = (1 + strategy_returns).cumprod()

    def annualized_return(self) -> float:
        return self.cum.iloc[-1] ** (1 / self.n_years) - 1

    def sharpe_ratio(self) -> float:
        excess = self.strategy - self.rf
        return (excess.mean() / excess.std()) * np.sqrt(252)

    def max_drawdown(self) -> float:
        drawdown = (self.cum - self.cum.cummax()) / self.cum.cummax()
        return drawdown.min()

    def avg_drawdown(self) -> float:
        drawdown = (self.cum - self.cum.cummax()) / self.cum.cummax()
        return drawdown[drawdown < 0].mean()

    def alpha(self) -> float:
        bm_ann = (1 + self.benchmark).cumprod().iloc[-1] ** (1 / self.n_years) - 1
        return self.annualized_return() - bm_ann

    def beta(self) -> float:
        cov = np.cov(self.strategy, self.benchmark)[0][1]
        return cov / np.var(self.benchmark)

    def value_at_risk(self, confidence: float = 0.95) -> float:
        return np.percentile(self.strategy, (1 - confidence) * 100)

    def conditional_var(self, confidence: float = 0.95) -> float:
        var = self.value_at_risk(confidence)
        return self.strategy[self.strategy <= var].mean()

    def get_all_metrics(self) -> dict:
        return {
            "年化報酬率": f"{self.annualized_return():.1%}",
            "Alpha": f"{self.alpha():.1%}",
            "Beta": f"{self.beta():.2f}",
            "夏普比率": f"{self.sharpe_ratio():.2f}",
            "最大回撤": f"{self.max_drawdown():.1%}",
            "平均回撤幅度": f"{self.avg_drawdown():.1%}",
            "VaR (95%)": f"{self.value_at_risk():.1%}",
            "CVaR (95%)": f"{self.conditional_var():.1%}",
        }
```

### 2. 月報酬熱力圖

```python
import seaborn as sns
import matplotlib.pyplot as plt

def plot_monthly_heatmap(daily_returns: pd.Series, title: str = "月報酬熱力圖"):
    monthly = (1 + daily_returns).resample('ME').prod() - 1
    monthly_df = monthly.reset_index()
    monthly_df['year'] = monthly_df.iloc[:, 0].dt.year
    monthly_df['month'] = monthly_df.iloc[:, 0].dt.month
    pivot = monthly_df.pivot(index='year', columns='month', values=monthly_df.columns[1])
    pivot.columns = ['Jan','Feb','Mar','Apr','May','Jun',
                     'Jul','Aug','Sep','Oct','Nov','Dec']
    pivot['全年'] = (1 + pivot.fillna(0)).prod(axis=1) - 1

    plt.figure(figsize=(16, 8))
    sns.heatmap(pivot, annot=True, fmt='.1%', cmap='RdYlGn',
                center=0, linewidths=0.5)
    plt.title(title)
    plt.tight_layout()
    plt.show()
```

### 3. 虧損歷史圖

```python
def plot_drawdown_history(strategy_cum: pd.Series, benchmark_cum: pd.Series):
    drawdown = (strategy_cum / strategy_cum.cummax() - 1) * 100

    fig, ax = plt.subplots(figsize=(14, 5), facecolor='#0d1117')
    ax.set_facecolor('#0d1117')
    ax.fill_between(drawdown.index, drawdown, 0,
                    alpha=0.5, color='#7c3aed', label='策略回撤')
    ax.plot(drawdown.index, drawdown, color='#a855f7', linewidth=0.8)

    bm_scaled = (benchmark_cum / benchmark_cum.iloc[0] - 1) * 100
    ax2 = ax.twinx()
    ax2.plot(bm_scaled.index, bm_scaled, color='gray', linewidth=0.8, label='大盤')

    ax.axhline(0, color='white', linewidth=0.5, linestyle='--')
    ax.set_ylabel('回撤幅度 (%)', color='white')
    ax.tick_params(colors='white')
    ax2.tick_params(colors='white')
    plt.title('虧損歷史（Drawdown History）', color='white')
    plt.tight_layout()
    plt.show()
```

### 4. 年度報酬比較

```python
def plot_annual_comparison(strategy_returns: pd.Series, benchmark_returns: pd.Series):
    annual_s = (1 + strategy_returns).resample('YE').prod() - 1
    annual_b = (1 + benchmark_returns).resample('YE').prod() - 1

    df = pd.DataFrame({'策略': annual_s.values, '大盤': annual_b.values},
                      index=annual_s.index.year)

    fig, ax = plt.subplots(figsize=(14, 5))
    x = np.arange(len(df))
    w = 0.35
    ax.bar(x - w/2, df['策略'] * 100, w, label='策略', color='#7c3aed', alpha=0.85)
    ax.bar(x + w/2, df['大盤'] * 100, w, label='大盤', color='gray', alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(df.index)
    ax.set_ylabel('年化報酬率 (%)')
    ax.set_title('與大盤年報酬比較')
    ax.legend()
    ax.axhline(0, color='black', linewidth=0.5)
    plt.tight_layout()
    plt.show()
```

---

## ✅ 移植優先順序建議

| 優先級 | 功能模組 | 對應分頁 | 難度 | 預估工時 |
|--------|----------|----------|------|----------|
| 🔴 P0 | KPI 指標卡（年化報酬、夏普、最大回撤） | 共用頂部 | 低 | 0.5 天 |
| 🔴 P0 | 歷史績效累積報酬走勢圖 | 獲利分頁 1 | 低 | 0.5 天 |
| 🟡 P1 | 月報酬熱力圖 | 獲利分頁 2 | 中 | 1 天 |
| 🟡 P1 | 虧損歷史 + 回撤卡片 | 抗風險分頁 1 | 中 | 1 天 |
| 🟡 P1 | 與大盤年報酬比較 | 獲利分頁 4 | 中 | 0.5 天 |
| 🟢 P2 | 超額報酬（Alpha Curve） | 獲利分頁 5 | 中 | 0.5 天 |
| 🟢 P2 | 跌幅排名 + 恢復時間排名 | 抗風險分頁 3/4 | 中 | 1 天 |
| 🔵 P3 | 持股報酬分佈（個股層級） | 兩面板分頁 3 | 高 | 2 天 |

---

> ⚠️ **注意**：後半段的 Skill 2~5 詳細策略、完整程式碼以及年化 48% 的最終複合策略需要**登入 FinLab 帳號**才能查看完整內容。
