---
title: S6 可轉債低估篩選（模組首頁）
type: module
code: S6
category: Strategies
owner: Krystal
purpose: 在大盤大跌或正股超跌時，利用 CB 債底保護特性篩選低估標的。
inputs: TPEx CB Data, Equity Price Data
outputs: s6_screened_list.csv, s6_backtest_report.md
update: 每日/隨盤
upstream: M1, D1
downstream: A1, N1
kpi: MDD / Calmar Ratio / 獲利因子
status: active
tags: [module, S6, CB]
---

# S6 可轉債低估篩選（模組首頁）

> [!NOTE]
> 本模組核心邏輯：**「買在債底附近，賺取反彈溢價」**。在大盤崩跌時，CB 提供比正股更強的下檔支撐。

## 🟩 最新版本摘要（Auto）
```dataviewjs
const pages = dv.pages("01-Modules/Strategies/S6-可轉債低估篩選/Versions")
  .where(p => p.version_seq)
  .sort(p => p.version_seq, 'desc');
if (pages.length){
  const latest = pages[0];
  dv.header(3, `最新版：${latest.version}（seq ${latest.version_seq}）`);
  dv.paragraph(`![[${latest.file.path}#Summary]]`);
}else{
  dv.paragraph('（尚無版本）');
}
```

## 📦 版本列表
```dataview
TABLE version as "版本", version_seq as "序號", valid_from as "生效日", status as "狀態"
FROM "01-Modules/Strategies/S6-可轉債低估篩選/Versions"
SORT version_seq DESC
```

## 📊 回測表現 (Top 3)
```dataview
TABLE cagr as "CAGR", mdd as "MDD", sharpe as "Sharpe"
FROM "01-Modules/Strategies/S6-可轉債低估篩選/Backtests"
WHERE type = "backtest"
SORT cagr DESC
LIMIT 3
```

## 📚 知識筆記
```dataview
LIST FROM "01-Modules/Strategies/S6-可轉債低估篩選/Knowledge"
SORT file.name ASC
```
