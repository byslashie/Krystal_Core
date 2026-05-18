{=====================================================================
  策略：每月進場 × 雙動能 × 智能分級資金管理 × 雙重加碼攻擊版
  版本：v4.0-clean (2026/05/18)
  基於 v4.0 精簡：刪除實測零觸發條件，邏輯完全不變
  刪除清單：
    - B) 初始停損 UseInitStop          ← v4.0 預設 false，零觸發
    - C) 保本 UseBE                    ← v4.0 預設 false，零觸發
    - E) KAMA 大賺出場                  ← v4.0 回測零觸發
    - F.1) 動態 Vol 減碼 50%（已註解）   ← 直接刪
    - F.2) 固定移動減碼（已註解）        ← 直接刪
  保留：A 動態Vol停損 / D.1 時間上限 / D.2 相對弱勢 / G VIX+週壓
=====================================================================}
settotalBar(1000);
setbackBar(1000);

// ====================== 策略參數設定 ======================
Inputs:
    Money(1000, "單次名目金額（基準部位）"),
    BigWinThreshold(0.15, "上一筆大賺定義 (15%)"),
    Scale_BigWin(1.5, "上一筆大賺時，底倉倍數"),
    Scale_SmallWin(1.0, "上一筆小賺時，底倉倍數"),
    Scale_Loss(0.5, "上一筆賠錢時，底倉倍數"),
    Max_Scale_Cap(3.0, "最大口數倍數上限"),
    EnablePyramid(true, "是否啟用獲利加碼"),
    Pyramid_Threshold(0.10, "加碼觸發門檻 (10%)"),
    Pyramid_Scale(0.5, "加碼部位倍數 (0.5)"),
    Max_Pyramid_Times(2, "最大加碼次數"),
    N_Days(30, "時間停損觀察期"),
    TargetPct(0.05, "N 天內目標漲幅"),
    BigWinPct(50.0, "大賺例外門檻"),
    VixLookback(400, "VIX 回顧期"),
    Len_W(22, "週線 ATR 週期"),
    Multiplier_W(3, "週線 ATR 倍數"),

    // === 強勢股優化規則開關 ===
    Market_Type(1, "市場別: 1=台股, 2=美股"),
    Enable_Rule1(true, "規則1:大盤跌8%暫停加碼15天"),
    Enable_Rule2(true, "規則2:流動性門檻與加碼減半"),
    Enable_Rule5(true, "規則5:動態波動率停損(Vol*4)"),
    Enable_Rule6(true, "規則6:時間上限強制出場"),
    Enable_Rule7(true, "規則7:波動率縮放加碼規模");

// ===== 內部變數 =====
Vars:
    IntraBarPersist EntryPX(0),
    IntraBarPersist BarsFromEnt(0),
    IntraBarPersist MaxRunupPct(0),
    IntraBarPersist PeakSinceEntry(0),
    IntraBarPersist UseTimeStop(true),
    IntraBarPersist MonthlyBarCount(0),
    IntraBarPersist LastTradeReturn(0),
    IntraBarPersist HasTraded(false),
    IntraBarPersist BaseOrderQty(0),
    IntraBarPersist PyramidCount(0),
    OrderQty(0),
    MyEquity(0), CurrentPL(0),

    // 週線計算用變數
    W_High(0), W_Low(0), W_Close(0), W_ATR(0), W_Cnt(0),
    W_Up(0), W_Dw(0), W_Trend(1),
    _i(0), _sumTR(0), _tr(0),

    // 強勢股規則專用變數
    IdxClose(0), IdxDrop(0), MarketCrashBars(999), PausePyramid(false),
    AvgVol5(0), Rule2_Pass(true), Rule2_Scale(1.0), LimitVol(0), LimitDays(0),
    PriceRet(0), Vol20(0), Vol60(0), Rule7_Scale(1.0), addQty(0),
    StockRetFromEnt(0), IdxRetFromEnt(0);

// ====== 輔助函式：月初判定 ======
Vars: IntraBarPersist CurrMonth(0), IntraBarPersist PrevMonth(0), IsNewMonth(false);
if CurrentBar = 1 then begin
    PrevMonth = Month(Date);
    CurrMonth = Month(Date);
end else begin
    CurrMonth = Month(Date);
    if CurrMonth <> PrevMonth then begin
        IsNewMonth = true;
        MonthlyBarCount = 0;
        PrevMonth = CurrMonth;
    end else begin
        IsNewMonth = false;
    end;
end;
MonthlyBarCount = MonthlyBarCount + 1;

{ ===== kama 日k / 週k ===== }
var:KAMA(0),SCt(0),d(0),vo(0),ER(0),f(0),s(0);
input:fastest(2,"快線"),slowest(30,"慢線"),N(8,"週期");
d = absValue(c-c[N]);
vo =Summation(absValue(c-c[1]),N);
If vo <> 0 then ER = d/vo;
f = 2/(fastest+1); s = 2/(slowest+1);
Sct = ER *square((f-s)+s);
KAMA = KAMA[1] +Sct*(c-KAMA[1]);

var:KAMA_W(0),SCt_W(0),d_W(0),vo_W(0),ER_W(0),W_f(0),s_W(0);
input:fastest_W(2,"快線"),slowest_W(30,"慢線"),N_W(8,"週期");
d_W = absValue(GetField("收盤價", "W")-GetField("收盤價", "W")[N_W]);
vo_W =Summation(absValue(GetField("收盤價", "W")-GetField("收盤價", "W")[1]),N_W);
If vo_W <> 0 then ER_W = d_W/vo_W;
W_f = 2/(fastest_W+1); s_W = 2/(slowest_W+1);
Sct_W = ER_W *square((W_f-s_W)+s_W);
KAMA_W = KAMA_W[1] +Sct_W*(GetField("收盤價", "W")-KAMA_W[1]);

{ ===== 手動計算週級別 ATR ===== }
_sumTR = 0;
For _i = 0 to Len_W - 1 Begin
    _tr = MaxList(
        GetField("最高價", "W")[_i] - GetField("最低價", "W")[_i],
        AbsValue(GetField("最高價", "W")[_i] - GetField("收盤價", "W")[_i+1]),
        AbsValue(GetField("最低價", "W")[_i] - GetField("收盤價", "W")[_i+1])
    );
    _sumTR = _sumTR + _tr;
End;
W_ATR = _sumTR / Len_W;

W_High = GetField("最高價", "W");
W_Low = GetField("最低價", "W");
W_Close = GetField("收盤價", "W");
W_Cnt = (W_High + W_Low) / 2;

// 週超級趨勢計算
If CurrentBar = 1 then begin
    W_Up = W_Cnt; W_Dw = W_Cnt;
end;

If W_Trend = 1 Then Begin
    W_Up = MaxList(W_Up[1], W_Cnt - W_ATR * Multiplier_W);
    If W_Close < W_Up Then Begin
        W_Trend = -1;
        W_Dw = W_Cnt + W_ATR * Multiplier_W;
    End;
End Else Begin
    W_Dw = MinList(W_Dw[1], W_Cnt + W_ATR * Multiplier_W);
    If W_Close > W_Dw Then Begin
        W_Trend = 1;
        W_Up = W_Cnt - W_ATR * Multiplier_W;
    End;
End;

{ ===== 強勢股規則計算 ===== }
if Market_Type = 1 then begin
    IdxClose = GetSymbolField("TSE.TW", "收盤價", "D");
    LimitVol = 1000;
    LimitDays = 110;
end else begin
    IdxClose = GetSymbolField("FISX*1.TF", "收盤價", "D");
    LimitVol = 500000;
    LimitDays = 252;
end;

// 規則1：大盤環境過濾
if IdxClose[20] > 0 then IdxDrop = (IdxClose - IdxClose[20]) / IdxClose[20] else IdxDrop = 0;
if IdxDrop < -0.08 then MarketCrashBars = 0 else MarketCrashBars = MarketCrashBars + 1;
if Enable_Rule1 and MarketCrashBars <= 15 then PausePyramid = true else PausePyramid = false;

// 規則2：流動性門檻
AvgVol5 = Average(Volume, 5);
if Enable_Rule2 then begin
    if AvgVol5 < LimitVol then Rule2_Pass = false else Rule2_Pass = true;
    if Market_Type = 1 and AvgVol5 <= 3000 then Rule2_Scale = 0.5 else Rule2_Scale = 1.0;
end else begin
    Rule2_Pass = true;
    Rule2_Scale = 1.0;
end;

// 規則5 & 7：波動率計算
if Close[1] > 0 then PriceRet = (Close - Close[1]) / Close[1] else PriceRet = 0;
Vol20 = StandardDev(PriceRet, 40, 1);
Vol60 = StandardDev(PriceRet, 60, 1);
if Enable_Rule7 and Vol20 > 0 then Rule7_Scale = Vol60 / Vol20 else Rule7_Scale = 1.0;


{ ===== 1. 進場邏輯 ===== }
If filled = 0 and IsNewMonth and isSessionFirstBar and isfirstcall("RealBar") then begin
    If IslistedSymbol = true and vix(VixLookback) = 0 and c > KAMA AND Month(Date) <> 9 and W_Trend = 1 and Rule2_Pass
    then begin
       OrderQty = Money / Close;
       var: Multipler(1);
       if HasTraded then begin
           if LastTradeReturn >= BigWinThreshold then Multipler = Scale_BigWin
           else if LastTradeReturn > 0 then Multipler = Scale_SmallWin
           else Multipler = Scale_Loss;
           if Multipler > Max_Scale_Cap then Multipler = Max_Scale_Cap;
       end else Multipler = 1;

       SetPosition(OrderQty * Multipler, label:="● 進場");
       BaseOrderQty = OrderQty * Multipler;
       PyramidCount = 0;
    end;
end;

{ ===== 2. 獲利加碼 (Pyramiding) ===== }
if EnablePyramid and filled > 0 and PyramidCount < Max_Pyramid_Times then begin
    if (Close - filledAvgPrice) / filledAvgPrice >= Pyramid_Threshold and PausePyramid = false then begin
        addQty = BaseOrderQty * Pyramid_Scale * Rule2_Scale * Rule7_Scale;
        SetPosition(filled + addQty, label:="★ 加碼");
        PyramidCount = PyramidCount + 1;
    end;
end;

{ ===== 3. 出場管理 ===== }
if filled <> 0 then begin
    BarsFromEnt = getBarOffset(FilledRecordDate(FilledRecordCount));
    PeakSinceEntry = MaxList(PeakSinceEntry, High);
    MaxRunupPct = (PeakSinceEntry - filledAvgPrice) / filledAvgPrice * 100.0;
    CurrentPL = (Close - filledAvgPrice) * filled;

    // 計算進場以來的個股與大盤漲幅（用於相對強弱淘汰）
    if BarsFromEnt > 0 then begin
        StockRetFromEnt = (Close - Close[BarsFromEnt]) / Close[BarsFromEnt];
        IdxRetFromEnt = (IdxClose - IdxClose[BarsFromEnt]) / IdxClose[BarsFromEnt];
    end;

    // A) 規則5：動態波動率防守停損
    if Enable_Rule5 and Close <= filledAvgPrice * (1 - (Vol20 * 4)) then begin
        LastTradeReturn = (Close - filledAvgPrice) / filledAvgPrice;
        SetPosition(0, label:="動態Vol停損");
    end else

    // D.1) 規則6：時間上限強制出場 + 相對強弱特赦
    if Enable_Rule6 and BarsFromEnt >= LimitDays and StockRetFromEnt < IdxRetFromEnt then begin
        LastTradeReturn = (Close - filledAvgPrice) / filledAvgPrice;
        SetPosition(0, label:="時間上限且轉弱出場");
    end else

    // D.2) 相對強弱淘汰法
    if BarsFromEnt >= N_Days and StockRetFromEnt < IdxRetFromEnt then begin
        LastTradeReturn = (Close - filledAvgPrice) / filledAvgPrice;
        SetPosition(0, label:="相對弱勢踢除");
    end else

    // G) VIX + 週線壓力出場（金雞母出場條件）
    if vix(VixLookback) = 1 and W_Trend = -1 then begin
        LastTradeReturn = (Close - filledAvgPrice) / filledAvgPrice;
        SetPosition(0, label:="VIX+週壓力");
        print(file("[StrategyName].log"),DateToString(date),"★【出場】VIX+週壓力");
    end;

end;
