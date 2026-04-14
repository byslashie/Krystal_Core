---
title: R1 風控規則（模組首頁）
type: module
code: R1
category: Risk
owner: Krystal
purpose: 動態倉位、停損/停利、單日額度、連虧凍結
inputs: 
outputs: risk_rules.yaml; risk_checks.csv
update: 月更+事件
upstream: D1
downstream: EXE, N1
kpi: 合規零違規、MDD 受控
status: active
tags: [module, R1]
---

# R1 風控規則（模組首頁）

## 🟩 最新版本摘要（Auto）
```dataviewjs
const pages = dv.pages("01-Modules/Risk/R1-風控規則/Versions")
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
FROM "01-Modules/Risk/R1-風控規則/Versions"
SORT version_seq DESC
```

## 📚 知識筆記
```dataview
LIST FROM "01-Modules/Risk/R1-風控規則/Knowledge"
SORT file.name ASC
```

## 🧭 決策紀錄
```dataview
TABLE file.link as "檔案", date as "日期", decision as "決策", reason as "理由"
FROM "01-Modules/Risk/R1-風控規則/Decisions"
SORT date DESC
```
