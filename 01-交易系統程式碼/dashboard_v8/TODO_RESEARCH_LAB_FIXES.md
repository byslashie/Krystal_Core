# 研究室分頁待修清單

> 產生時間：2026-05-19 20:21
> 涉及檔案：`01-交易系統程式碼/dashboard_v8/index.html`、`01-交易系統程式碼/dashboard_v8/app.py`
> 範圍：研究室 (p_lab) 全部 9 個主分頁 + 下層 sub-tab

---

## 🎯 修復優先級總覽

| 優先級 | 數量 | 影響 |
| --- | --- | --- |
| **P0 — 顯示錯誤 / 邏輯反向** | 4 項 | 數字直接誤導決策 |
| **P1 — 空白頁面 / 未填值** | 5 項 | 用戶看不到內容 |
| **P2 — 體驗優化** | 3 項 | 不影響功能但體驗差 |

---

## 🔴 P0 — 立即修復（數字誤導）

### P0-1 ✅ 雙 MDD 顯示（KPI 卡片已完成 80%，剩抗風險頁）

**狀態**：上傳 & 分析 tab 的 MDD 卡片已加上「資產 / 獲利」雙副標，但 **抗風險頁面（finlab-risk-tab / fl-p12）的 MDD 卡片還沒同步**。

**需改**：
- [`index.html`](index.html) 約行 16056-16101 區（fl-p12 那塊）
- 找到 MDD 顯示元素，比照 KPI 卡片改成雙顯示
- hover tooltip 也要加

---

### P0-2 🔴 VaR / CVaR 達標邏輯反向

**症狀**：截圖顯示 VaR -0.2% 卻判定「未達」，但 -0.2% 是**低風險（好）**，應該判定「達標」。

**現有邏輯**（疑似在前端某處）：
```
VaR  需 <-7%   → 目前 -0.2% 不夠負 → 判「未達」 ❌
CVaR 需 <-10%  → 目前 -0.2% 不夠負 → 判「未達」 ❌
```

**正確邏輯**應該是：
```
VaR ≥ -7%（不能比 -7% 更深虧）→ 達標
CVaR ≥ -10%（不能比 -10% 更深虧）→ 達標
```

**需改**：
- 找出 VaR / CVaR 達標判斷的 JS（搜尋 `var95` / `cvar95` 結合 `達標` / `未達`）
- 把比較符號反向

---

### P0-3 🔴 VaR / CVaR 數值異常偏低（-0.2%）

**症狀**：正常策略 VaR 應在 -1% ~ -5%，CVaR -2% ~ -8%，目前顯示 **-0.2%**。

**根因**：[`index.html:9141-9143`](index.html#L9141) `calculateKPIs` 用 `pnl / initialCapital` 算單筆報酬率：

```javascript
if (initialCapital > 0) {
  returns.push(pnl / initialCapital);  // ← 用 1,371 萬當分母
}
```

單筆獲利 ±10 萬 ÷ 1,371 萬 = ±0.73%，所有交易報酬都被壓得很小，95% 分位自然只有 -0.2%。

**建議改法**：
- 方案 A：用 `pnl / 該筆部位名目` 算個筆報酬（最準）
- 方案 B：用 `每日 NAV 變化率`（xlsx 才有）
- 方案 C：把現在的 `pnl / initialCapital` 加註「相對於本金的單筆衝擊」，不要當作報酬率

---

### P0-4 🟡 「超額報酬 (Alpha Curve)」永久顯示空白

**截圖**：累積超額報酬區塊顯示「需後端逐年資料才能計算 Alpha 曲線」

**位置**：獲利能力 tab → 超額報酬 sub-panel

**需改**：
- 後端 [`app.py`](app.py) `/api/strategy/import/charts` 增加「年度報酬 vs 大盤」資料
- 或在前端加 fallback：用 yfinance 抓 TAIEX 對比
- 至少先顯示「策略累積 vs 大盤累積」差值曲線

---

## 🟡 P1 — 空白頁面填值

### P1-1 📅 月報酬熱力圖空白

**位置**：獲利能力 → 「月報酬」sub-tab
**DOM ID**：`fl-monthly` 容器、`fl-heatmap-body` tbody

**原因**：邏輯有（[index.html 約 12918 行](index.html#L12918) 有填 heatmap），但**填值的條件**可能沒觸發。

**需改**：
- 確認 `currentChartsData.heatmap` 或月度報酬資料來源
- 若後端沒回傳，改用前端從 trades 直接算（df.groupby('exit_month')）

---

### P1-2 📋 持股報酬明細空白

**位置**：獲利能力 → 「持股報酬」sub-tab
**DOM ID**：`fl-holdings-tbody`

**原因**：[行 12955-13008](index.html#L12955) 有渲染邏輯，但若 `holdings` 資料來源是空，就一片空白。

**需改**：
- 從 csv trades 直接 group by 商品代碼，渲染表格
- 不用依賴後端 holdings 欄位

---

### P1-3 📊 年報酬比較（與大盤）空白

**位置**：獲利能力 → 「年報酬比較」sub-tab
**DOM ID**：`fl-yearly-summary-body`

**需改**：
- 前端從 trades 算每年累計獲利
- 大盤資料：yfinance 抓 ^TWII 或內建 TAIEX 緩存

---

### P1-4 📈 報酬分布 sub-tab 未驗證

**位置**：獲利能力 → 「報酬分布」sub-tab
**DOM ID**：`fl-dist`

**需驗證**：
- 截圖沒看到，需要上傳後切換到該 tab 確認
- 若空白，需從 trades.pnl 畫直方圖

---

### P1-5 📉 虧損歷史 sub-tab 未驗證

**位置**：獲利能力 → 「虧損歷史」sub-tab
**DOM ID**：`fl-drawdown`

**需驗證**：
- 從 cum_profit 算每筆 dd 序列，渲染折線圖

---

## 🟢 P2 — 三個主分頁需深度檢查

這三個 tab **預設是空 div**（[`index.html:3154-3156`](index.html#L3154)）：

```html
<div id="finlab-rr-tab" class="tab-content" style="display:none"></div>
<div id="finlab-win-tab" class="tab-content" style="display:none"></div>
<div id="finlab-liq-tab" class="tab-content" style="display:none"></div>
```

內容透過 [`switchLabTab` 邏輯](index.html#L12830) 從 `p13` / `p14` / `p15` 動態移入。**取決於 `window.currentChartsData` 是否齊全**。

### P2-1 ⚡ 風險報酬比 (finlab-rr-tab / p13)

**DOM 元素**：
- `fl-p13-sharpe-strat` 夏普值
- `fl-p13-sortino-strat` Sortino
- `fl-p13-tail-ratio` 尾部比率
- `fl-p13-vol-strat` 波動度
- `fl-p13-warn-banner` 達標提示

**已實作邏輯**：[index.html:13341-13383](index.html#L13341)
**依賴**：`window.currentChartsData.metrics`（sharpe / sortino / calmar）+ `holdings[].return_pct`

**驗證項**：
- [ ] 上傳檔案後切到此 tab，是否顯示所有 KPI
- [ ] 若空白，檢查 `currentChartsData` 是否有 holdings

---

### P2-2 🏆 勝率期望值 (finlab-win-tab / p14)

**已實作邏輯**：[index.html:13467](index.html#L13467) 起
**需驗證**：上傳後切到該 tab 看 KPI 是否填滿

---

### P2-3 💧 交易流動性 (finlab-liq-tab / p15)

**已實作邏輯**：[index.html:13608](index.html#L13608) 起
**需驗證**：上傳後切到該 tab 看 KPI 是否填滿

---

### P2-4 🌡️ 景氣適配 (sc-regime-tab)

**位置**：[index.html:3380](index.html#L3380) 起
**狀態**：UI 存在但需確認是否有資料

---

## 🛠️ 建議修復順序

### Phase 1（30 分鐘內可完成）
1. **P0-2** VaR/CVaR 達標邏輯反向（5 分鐘）
2. **P0-1** 抗風險頁雙 MDD 同步（10 分鐘）
3. 紅框 VaR/CVaR hover tooltip 加入（5 分鐘）
4. **P0-3** VaR 數值算法修正（10 分鐘）

### Phase 2（1 小時）
5. **P1-1** 月報酬熱力圖填值
6. **P1-2** 持股報酬明細填值
7. **P0-4** 超額報酬 Alpha 曲線（需要大盤資料來源）

### Phase 3（驗證 + 補洞）
8. **P2-1 ~ P2-3** 上傳後逐 tab 驗證 + 補缺
9. **P1-3 ~ P1-5** 同 Phase 3 一起做

---

## 📊 已完成項目（本次 session）

- ✅ `calculateKPIs` 加上 `mddProfit`（獲利角度 MDD）回傳
- ✅ KPI 卡片 MDD 改成雙顯示（資產 / 獲利）
- ✅ MDD 卡片加上 hover tooltip 說明公式差異
- ✅ kpis Object.assign 補上 mddProfit 相關欄位避免合併丟失

**已改動行數**：[index.html:2543-2552, 9233-9286, 9303-9304, 11055-11070, 11080-11082](index.html)

---

## 💡 給 Krystal 的建議

從你的策略選擇角度，**P0 才是真正影響決策的**：
- P0-2/P0-3 直接影響你對「策略風險高低」的判斷
- P0-1 影響你對 MDD 的解讀

P1/P2 主要是「資料完整性」問題，可以分批處理。

**最佳行動**：先把 P0 全修完，跑一次完整的「每月進場 / V4 / V4.1 / 歸因分析」四份檔案分析，看修完後三個策略的 真實風險畫像 才出得來。
