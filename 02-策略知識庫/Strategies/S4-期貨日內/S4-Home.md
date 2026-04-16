---
title: S4 期貨日內（模組首頁）
type: module
code: S4
category: Strategies
owner: Krystal
purpose: 策略邏輯參見版本摘要與 Backtests
inputs: 
outputs: s4_trades.csv; s4_daily_pnl.csv
update: 依版本
upstream: D1, M1, M2, N3
downstream: T1, N1
kpi: CAGR/MDD/Sharpe/換手
status: active
tags: [module, S4]
---

# S4 期貨日內（模組首頁）

## 🟩 最新版本摘要（Auto）
```dataviewjs
const pages = dv.pages("01-Modules/Strategies/S4-期貨日內/Versions")
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
FROM "01-Modules/Strategies/S4-期貨日內/Versions"
SORT version_seq DESC
```

## 📚 知識筆記
```dataview
LIST FROM "01-Modules/Strategies/S4-期貨日內/Knowledge"
SORT file.name ASC
```

## 🧭 決策紀錄
```dataview
TABLE file.link as "檔案", date as "日期", decision as "決策", reason as "理由"
FROM "01-Modules/Strategies/S4-期貨日內/Decisions"
SORT date DESC
```
