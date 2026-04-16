---
title: D1 決策引擎（模組首頁）
type: module
code: D1
category: Orchestration
owner: Krystal
purpose: macro_state.csv; seasonality_flags.csv; market_trend_state.csv; kpi_dashboard.md; risk_alerts.csv
inputs: 
outputs: decision_YYYYMM.yaml
update: 月初 + 事件
upstream: M1, M2, N3, T1, R1, R2
downstream: A1, N1, Strategies
kpi: 覆核完整度、決策一致性
status: active
tags: [module, D1]
---

# D1 決策引擎（模組首頁）

## 🟩 最新版本摘要（Auto）
```dataviewjs
const pages = dv.pages("01-Modules/Orchestration/D1-決策引擎/Versions")
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
FROM "01-Modules/Orchestration/D1-決策引擎/Versions"
SORT version_seq DESC
```

## 📚 知識筆記
```dataview
LIST FROM "01-Modules/Orchestration/D1-決策引擎/Knowledge"
SORT file.name ASC
```

## 🧭 決策紀錄
```dataview
TABLE file.link as "檔案", date as "日期", decision as "決策", reason as "理由"
FROM "01-Modules/Orchestration/D1-決策引擎/Decisions"
SORT date DESC
```
