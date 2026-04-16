---
title: EXE 執行器（模組首頁）
type: module
code: EXE
category: Execution
owner: Krystal
purpose: orders.yaml; broker_api_keys
inputs: 
outputs: fills.csv; exe_log.csv
update: 事件觸發
upstream: D1, R1, R2
downstream: N1, T1
kpi: 失敗率<0.5% & 延遲<200ms
status: active
tags: [module, EXE]
---

# EXE 執行器（模組首頁）

## 🟩 最新版本摘要（Auto）
```dataviewjs
const pages = dv.pages("01-Modules/Execution/EXE-執行器/Versions")
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
FROM "01-Modules/Execution/EXE-執行器/Versions"
SORT version_seq DESC
```

## 📚 知識筆記
```dataview
LIST FROM "01-Modules/Execution/EXE-執行器/Knowledge"
SORT file.name ASC
```

## 🧭 決策紀錄
```dataview
TABLE file.link as "檔案", date as "日期", decision as "決策", reason as "理由"
FROM "01-Modules/Execution/EXE-執行器/Decisions"
SORT date DESC
```
