---
title: A1 資金配置器（模組首頁）
type: module
code: A1
category: Orchestration
owner: Krystal
purpose: decision_YYYYMM.yaml, risk_limits.yaml
inputs: 
outputs: allocation_YYYYMM.csv; constraints.yaml
update: 月初
upstream: D1
downstream: S1, S3, S4, S5, EXE, N1
kpi: 權重落地正確率、換手成本
status: active
tags: [module, A1]
---

# A1 資金配置器（模組首頁）

## 🟩 最新版本摘要（Auto）
```dataviewjs
const pages = dv.pages("01-Modules/Orchestration/A1-資金配置器/Versions")
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
FROM "01-Modules/Orchestration/A1-資金配置器/Versions"
SORT version_seq DESC
```

## 📚 知識筆記
```dataview
LIST FROM "01-Modules/Orchestration/A1-資金配置器/Knowledge"
SORT file.name ASC
```

## 🧭 決策紀錄
```dataview
TABLE file.link as "檔案", date as "日期", decision as "決策", reason as "理由"
FROM "01-Modules/Orchestration/A1-資金配置器/Decisions"
SORT date DESC
```
