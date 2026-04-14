---
title: T1 KPI / 通道圖（模組首頁）
type: module
code: T1
category: Monitoring
owner: Krystal
purpose: s1_perf.csv…（各策略績效）
inputs: 
outputs: kpi_dashboard.md; sigma_events.csv
update: 週更/月更
upstream: S1, S3, S4, S5
downstream: D1, N1
kpi: 偏離偵測準確率、誤報率
status: active
tags: [module, T1]
---

# T1 KPI / 通道圖（模組首頁）

## 🟩 最新版本摘要（Auto）
```dataviewjs
const pages = dv.pages("01-Modules/Monitoring/T1-KPI_通道圖/Versions")
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
FROM "01-Modules/Monitoring/T1-KPI_通道圖/Versions"
SORT version_seq DESC
```

## 📚 知識筆記
```dataview
LIST FROM "01-Modules/Monitoring/T1-KPI_通道圖/Knowledge"
SORT file.name ASC
```

## 🧭 決策紀錄
```dataview
TABLE file.link as "檔案", date as "日期", decision as "決策", reason as "理由"
FROM "01-Modules/Monitoring/T1-KPI_通道圖/Decisions"
SORT date DESC
```
