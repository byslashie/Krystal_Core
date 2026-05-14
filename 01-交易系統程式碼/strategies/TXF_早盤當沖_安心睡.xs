// ======================================================
// 台指期 早盤當沖策略 - 安心睡版本
// 進場窗口：09:00 - 10:30
// 強制平倉：11:30（不留倉、不過午、不過夜）
// 週期：1分K
// ======================================================

input: _p1(1.5, "最低點以下");
setbarBack(100);
settotalBar(1000);

// ===== 早盤當沖時間參數 =====
input:
    EntryStart(090000,   "進場開始時間 09:00"),
    EntryEnd  (103000,   "進場結束時間 10:30"),
    ForceExit (113000,   "強制平倉時間 11:30");

// ===== 出場參數 =====
input:
    ATRLen      (14,  "ATR 週期"),
    ATRMultSL   (1.5, "初始停損 ×ATR"),
    LockATR1    (0.5, "保本觸發 ×ATR"),
    LockATR2    (1.0, "跟蹤鎖利 ×ATR");

// ===== 1. 均線斜率 =====
input: day1(5, "MA週期"), freq1(3, "斜率長度"), Ave1(3, "斜率平均");
value11 = average(close, day1);
value12 = LinearRegSlope(value11, freq1);
condition11 = value12 >= value12[1];
condition12 = close >= average(close, 2) and close >= open[1];

// ===== 2. RSI =====
input: Length1(10, "RSI短"), Length2(12, "RSI長"), day(2, "RSI平均");
value21 = RSI(Close, Length1);
condition21 = value21 <= 50.001 and value21 >= value21[1] and value21[1] > 39.999;

// ===== 3. 大紅K =====
value31 = High - Low;
condition31 = close > open and value31 >= value31[1] and close[1] - open[1] <= 0
              and open <= Average(close, 3) and close >= high[1];

// ===== 4. 恐慌指數 =====
value41 = (Highest(Close,22) - Low) / (Highest(Close,22)) * 100;
condition41 = value41 <= 0.25;

// ===== 5. 跳空 =====
condition33 = getField("最低價","60") > getField("最高價","60")[1] and c > 0;
condition32 = getField("最高價","60") < getField("最低價","60")[1];
If condition33 then value33 = getField("最低價","60") * ((100 - _P1) * 0.01);
If condition32 then value32 = getField("最低價","60") * ((100 - _P1) * 0.01);

// ======================================================
// ===== 進場：只在早盤 09:00 - 10:30 =====
// ======================================================
if  condition11 and condition12 and condition21 and condition31 and condition41
    and value32 <= value33
    and TSE_Long(300,60,8) = 1
    and TSE_FLAT(90,20)   = 1
    and TSE_updown(1.5,7) = 1
    and Position >= 0 and Filled >= 0
    and currentTime >= EntryStart
    and currentTime <= EntryEnd
    and DayOfWeek(Date) <> 5         // 週五不進場（避免結算波動）
then begin
    buy(1, close - 2, label:="早盤進場");
end;

// ======================================================
// ===== 出場模組（只在持倉時運作）=====
// ======================================================
if position = 0 or filled = 0 then return;

Vars:
    atr(0), entryPx(0),
    highestSinceEntry(0),
    trailLine(0);

atr     = ATR(ATRLen);
entryPx = FilledAvgPrice;

// 進場後最高價追蹤
if filled <> 0 then
    highestSinceEntry = MaxList(highestSinceEntry, High)
else
    highestSinceEntry = High;

// ---- (A) 初始硬停損：-1.5×ATR =====
if filled >= 1 and Close <= entryPx - ATRMultSL * atr then begin
    SetPosition(0, label:="硬停損 -1.5ATR");
    return;
end;

// ---- (B) 保本：獲利 >=0.5×ATR 後，回到成本就出 =====
if filled >= 1 and highestSinceEntry >= entryPx + LockATR1 * atr then begin
    if Close <= entryPx then begin
        SetPosition(0, label:="保本出場");
        return;
    end;
end;

// ---- (C) 跟蹤鎖利：獲利 >=1.0×ATR 後，高點回落 1×ATR 就出 =====
if filled >= 1 and highestSinceEntry >= entryPx + LockATR2 * atr then begin
    trailLine = highestSinceEntry - LockATR2 * atr;
    if Close <= trailLine then begin
        SetPosition(0, label:="跟蹤鎖利");
        return;
    end;
end;

// ---- (D) 早盤結束強制平倉：11:30 一定空手 =====
if filled >= 1 and currentTime >= ForceExit then begin
    SetPosition(0, label:="11:30強制平倉");
    return;
end;
