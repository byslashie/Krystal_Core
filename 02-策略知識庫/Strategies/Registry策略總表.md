---
title: Strategies Registry（總表）
type: registry
---
# 策略總表（可篩選）

## 上線中

```dataviewjs
// 根目錄
var ROOT = "01-Modules/Strategies";

// 取得所有直層策略資料夾（排除 ROOT 與 /Registry）
var pages = dv.pages('"01-Modules/Strategies"');
var folderSet = new Set();
for (var p of pages) {
  if (p.file && p.file.folder && p.file.folder.startsWith(ROOT)) {
    var f = p.file.folder;
    if (f !== ROOT && !f.endsWith("/Registry") &&
        f.split("/").length === ROOT.split("/").length + 1) {
      folderSet.add(f);
    }
  }
}
var folders = Array.from(folderSet);

// 🔽 這段是關鍵：依 S<number>- 的數字排序（S1、S2、S3…）
function stratOrder(folderPath) {
  var name = folderPath.split("/").pop();        // e.g. "S1-美股 ETF 輪動"
  var m = /^S(\d+)\b/.exec(name);
  return m ? parseInt(m[1], 10) : 9999;          // 沒抓到就放最後
}
folders.sort(function(a,b){
  var oa = stratOrder(a), ob = stratOrder(b);
  if (oa !== ob) return oa - ob;
  // 次排序：名稱
  var na = a.split("/").pop(), nb = b.split("/").pop();
  return na.localeCompare(nb, "zh-Hant");
});

// 樣式小工具
function colorBadge(val, good, mid, suffix) {
  if (val == null) return "—";
  return (val >= good ? "🟢 " : val >= mid ? "🟡 " : "🔴 ")
         + (Number(val).toFixed(2) + (suffix || ""));
}
function mddBadge(val) {
  if (val == null) return "—";
  var absPct = Math.abs(Number(val)) * 100; // -0.1545 -> 15.45%
  return (absPct <= 10 ? "🟢 " : absPct <= 20 ? "🟡 " : "🔴 ") + absPct.toFixed(2) + "%";
}

// （以下與你現行版本相同）
var rows = [];

for (var i = 0; i < folders.length; i++) {
  var folder = folders[i];
  var name = folder.split("/").pop();

  // HOME（檔名以 -Home 結尾或 frontmatter type: module）
  var home = dv.pages()
    .where(function(p){ return p.file && p.file.folder === folder; })
    .where(function(p){ return (p.file && p.file.name && p.file.name.endsWith("-Home")) || p.type === "module"; })
    .first();

  // 最新版本（/Versions 內 version_seq 最大）
  var latestVer = dv.pages()
    .where(function(p){ return p.file && p.file.folder === folder + "/Versions" && p.version_seq != null; })
    .sort(function(p){ return p.version_seq; }, "desc")
    .first();

  // Backtests：抓最新一筆
  var btPages = dv.pages()
    .where(function(p){ return p.file && p.file.folder && p.file.folder.startsWith(folder + "/Backtests"); })
    .array();

  var latestBt = null;
  if (btPages && btPages.length > 0) {
    btPages.sort(function(a, b){
      var va = (a.version_seq != null ? a.version_seq : -1);
      var vb = (b.version_seq != null ? b.version_seq : -1);
      if (vb !== va) return vb - va;
      var ra = (a.run_date || a.end_date || (a.file ? a.file.ctime : null));
      var rb = (b.run_date || b.end_date || (b.file ? b.file.ctime : null));
      return new Date(rb) - new Date(ra);
    });
    latestBt = btPages[0];
  }

  // KPI 來源：回測頁（支援中英欄位）
  var cagrRaw   = latestBt ? (latestBt.cagr != null ? latestBt.cagr : latestBt["年化報酬率_CAGR"]) : null;
  var cagrPct   = (cagrRaw == null) ? null : Number(cagrRaw) * 100;
  var sharpeVal = latestBt ? (latestBt.sharpe != null ? latestBt.sharpe : latestBt["夏普比率_Sharpe"]) : null;
  var mddVal    = latestBt ? (latestBt.mdd != null ? latestBt.mdd : latestBt["最大回檔_MDD"]) : null;

  // EV 可能已是百分比或小數；做容錯：<=3 視為小數再 *100
  var evRaw     = latestBt ? (latestBt.ev_pct != null ? latestBt.ev_pct : latestBt["期望值_EV"]) : null;
  var evPct     = (evRaw == null) ? null : (Math.abs(Number(evRaw)) <= 3 ? Number(evRaw)*100 : Number(evRaw));
  var trades    = latestBt ? (latestBt.trades != null ? latestBt.trades : latestBt["交易數量_Trades"]) : null;

  rows.push([
    "[[" + folder + "|" + name + "]]",
    latestVer ? (latestVer.version + "（seq " + latestVer.version_seq + "）") : "—",
    cagrPct == null ? "—" : colorBadge(cagrPct, 15, 8, "%"),
    sharpeVal == null ? "—" : colorBadge(sharpeVal, 1.5, 1.0, ""),
    mddBadge(mddVal),
    evPct == null ? "—" : colorBadge(evPct, 5, 0, "%"),
    trades == null ? "—" : String(trades),
    home ? "[[" + home.file.path + "|HOME]]" : "—",
    latestVer ? "[[" + latestVer.file.path + "|版本頁]]" : "—",
    latestBt ? "[[" + latestBt.file.path + "|回測頁]]" : "—"
  ]);
}

dv.table(["策略", "最新版", "CAGR_%", "Sharpe", "MDD_%", "EV_%", "交易數", "HOME", "最新版本頁", "回測頁"], rows);
```



**已下線**
```dataview
TABLE strategy, version, uploaded, asset_class, frequency, status, notes
FROM "01-Modules/Strategies/Registry"
WHERE status = "offline"
SORT uploaded DESC
```

**自訂條件（例）**
```dataview
TABLE strategy, version, frequency, asset_class, round(cagr,2) as "CAGR_%", round(mdd,2) as "MDD_%", round(ev_pct,2) as "EV_%"
FROM "01-Modules/Strategies/Registry"
WHERE frequency = "日內" AND asset_class = "海外個股(股)" AND cagr >= 10 AND mdd >= -20
SORT cagr DESC
```
