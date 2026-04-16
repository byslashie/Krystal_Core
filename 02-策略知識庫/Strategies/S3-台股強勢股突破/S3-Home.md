---
title: S3 強勢股突破（模組首頁）
type: module
code: S3
category: Strategies
owner: Krystal
purpose: 策略邏輯參見版本摘要與 Backtests
inputs: 
outputs: s3_positions.csv; s3_perf.csv
update: 依版本
upstream: D1, M1, M2, N3
downstream: T1, N1
kpi: CAGR/MDD/Sharpe/換手
status: active
tags: [module, S3]
---

# S3 強勢股突破（模組首頁）

## 🟩 最新版本摘要（Auto）
```dataviewjs
// 🟩 S1 最新版本摘要（不寫 DQL，純 JS 過濾最穩）
const VERSION_FOLDER = '01-Modules/Strategies/S3-台股強勢股突破/Versions';

// 抓到「Versions」資料夾內，且有 version_seq 的頁
const vers = dv.pages()
  .where(p => p.file && p.file.folder === VERSION_FOLDER)
  .where(p => p.version_seq != null)
  .sort(p => p.version_seq, 'desc');

if (vers.length) {
  const latest = vers[0];
  dv.header(3, `最新版：${latest.version}（seq ${latest.version_seq}）`);
  // 內嵌該版本頁裡的 #Summary 區塊（若沒有則顯示整頁連結）
  if (latest.file && latest.file.path) {
    dv.paragraph(`![[${latest.file.path}#Summary]]`);
  } else {
    dv.paragraph(`[[${latest.file.name}]]`);
  }
} else {
  dv.paragraph('（尚無版本）');
}
```


## 🔬 回測（Backtests）
```dataview
TABLE file.link as "Backtest", version, tag, run_date, cagr_pct, sharpe, mdd, calmar, trades
FROM "01-Modules/Strategies/S3-台股強勢股突破/Backtests"
SORT run_date DESC
```




## 📦 回測版本列表
```dataview
TABLE version as "版本", version_seq as "序號", valid_from as "生效日", status as "狀態"
FROM "01-Modules/Strategies/S3-台股強勢股突破/Backtests"
SORT version_seq DESC
```

## 📚 知識筆記
```dataview
LIST FROM "01-Modules/Strategies/S1-美股 ETF 輪動/Knowledge"
SORT file.name ASC
```

## 🧭 決策紀錄![[Code_Generated_Image.png]]