---
title: R2 風控監控（模組首頁）
type: module
code: R2
category: Risk
owner: Krystal
purpose: VaR/CVaR、蒙卡、實時損益監控與警報
inputs: 
outputs: risk_alerts.csv; exposure_report.md
update: 日更+盤中
upstream: D1
downstream: S1, S3, S4, S5, A1, EXE
kpi: 告警準確率、處置時效
status: active
tags: [module, R2]
---

# R2 風控監控（模組首頁）

## 🟩 最新版本摘要（Auto）
```dataviewjs
const pages = dv.pages("01-Modules/Risk/R2-風控監控/Versions")
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
FROM "01-Modules/Risk/R2-風控監控/Versions"
SORT version_seq DESC
```

## 📚 知識筆記
```dataview
LIST FROM "01-Modules/Risk/R2-風控監控/Knowledge"
SORT file.name ASC
```

## 🧭 決策紀錄
```dataview
TABLE file.link as "檔案", date as "日期", decision as "決策", reason as "理由"
FROM "01-Modules/Risk/R2-風控監控/Decisions"
SORT date DESC
```
