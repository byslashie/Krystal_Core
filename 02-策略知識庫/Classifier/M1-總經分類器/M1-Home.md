---
title: M1 總經分類器（模組首頁）
type: module
code: M1
category: Classifier
owner: Krystal
purpose: 以 GDP/PMI/CPI/失業率 等判斷象限（擴張/放緩/衰退/復甦）
inputs: macro_data.xlsx; fred.yaml
outputs: macro_state.csv; macro_regime.json
update: 月更
upstream: —
downstream: A1, D1, S1, S5
kpi: 準確度/穩健性；錯誤率<5%
status: active
tags: [module, M1]
---

# M1 總經分類器（模組首頁）

## 🟩 最新版本摘要（Auto）
```dataviewjs
const pages = dv.pages("01-Modules/Classifier/M1-總經分類器/Versions")
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
FROM "01-Modules/Classifier/M1-總經分類器/Versions"
SORT version_seq DESC
```

## 📚 知識筆記
```dataview
LIST FROM "01-Modules/Classifier/M1-總經分類器/Knowledge"
SORT file.name ASC
```

## 🧭 決策紀錄
```dataview
TABLE file.link as "檔案", date as "日期", decision as "決策", reason as "理由"
FROM "01-Modules/Classifier/M1-總經分類器/Decisions"
SORT date DESC
```
