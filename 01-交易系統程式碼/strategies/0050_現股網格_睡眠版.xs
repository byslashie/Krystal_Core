// ======================================================
// 0050 / 006208 現股網格策略 - 睡眠版
// 標的：0050、006208（ETF 現股，不會歸零）
// 週期：日線 K（網格不需要分鐘級）
// 設計：底倉 + 等距網格 + 熊市保護
// ======================================================

setbarBack(250);
settotalBar(2000);

// ===== 網格參數 =====
input:
    GridPct      (3.0,  "網格間距 %"),       // 每跌 3% 加 1 格、每漲 3% 減 1 格
    BasePosition (3,    "底倉張數"),          // 永遠持有的底倉
    MaxGrids     (10,   "最大網格數"),        // 最多再加 10 格
    EachGridSize (1,    "每格張數");

// ===== 熊市保護參數 =====
input:
    BearMA       (200,  "熊市判定均線（日）"),  // 跌破 200 日線 = 熊市
    BearStopAdd  (1,    "熊市是否停止加倉 1=停"),
    DrawdownPct  (-30,  "最大回撤 %（強制減倉）");

// ===== 鎖利參數 =====
input:
    ProfitLockPct(20.0, "單格獲利 % 賣出"),    // 每格漲 20% 就賣
    TotalLockPct (25.0, "總部位獲利 % 部分賣出");

// ======================================================
// 變數
// ======================================================
Vars:
    anchorPrice(0),       // 網格錨點（上次成交價）
    gridLevel(0),         // 目前在第幾格（正=加倉中、負=減倉中）
    ma200(0),
    isBear(false),
    avgCost(0),
    drawdown(0);

ma200    = Average(Close, BearMA);
isBear   = Close < ma200;
avgCost  = FilledAvgPrice;

if Filled > 0 and avgCost > 0 then
    drawdown = (Close - avgCost) / avgCost * 100
else
    drawdown = 0;

// ======================================================
// 初始化：第一次跑時建立底倉
// ======================================================
if Position = 0 and Filled = 0 then begin
    Buy(BasePosition, Close, label:="建立底倉");
    anchorPrice = Close;
    gridLevel   = 0;
    return;
end;

// 第一次設定錨點（避免重啟後 anchorPrice 為 0）
if anchorPrice = 0 then anchorPrice = avgCost;

// ======================================================
// 網格加倉：每跌 GridPct% 買 1 格
// ======================================================
if Close <= anchorPrice * (1 - GridPct / 100)
   and gridLevel < MaxGrids
   and not (isBear and BearStopAdd = 1)        // 熊市不加倉
then begin
    Buy(EachGridSize, Close, label:="網格加倉");
    anchorPrice = Close;
    gridLevel   = gridLevel + 1;
end;

// ======================================================
// 網格鎖利：每漲 GridPct% 賣 1 格（保留底倉）
// ======================================================
if Close >= anchorPrice * (1 + GridPct / 100)
   and Filled > BasePosition
then begin
    Sell(EachGridSize, Close, label:="網格鎖利");
    anchorPrice = Close;
    gridLevel   = gridLevel - 1;
end;

// ======================================================
// 熊市防爆：回撤 > 30% 時，賣掉一半加倉部位（保留底倉）
// ======================================================
if drawdown <= DrawdownPct and Filled > BasePosition then begin
    Sell((Filled - BasePosition) / 2, Close, label:="熊市防爆減倉");
    anchorPrice = Close;
end;

// ======================================================
// 牛市鎖利：總部位獲利 > 25% 時，賣掉 1/3 加倉部位
// ======================================================
if Filled > BasePosition and avgCost > 0
   and (Close - avgCost) / avgCost * 100 >= TotalLockPct
then begin
    Sell((Filled - BasePosition) / 3, Close, label:="牛市分批鎖利");
    anchorPrice = Close;
end;
