{=====================================================================
  策略：每月進場 × 雙動能 × 智能分級資金管理 × 雙重加碼攻擊版
  版本：v4.1 (2026/05/18)
  v4.0 → v4.1 變更：
    1. [改 A] 動態 Vol 停損改雙錨：成本錨 4σ 保本 + 高點錨 6σ 保獲利
    2. [改 D.2] 相對弱勢踢除門檻 30→60 天，並加日 KAMA 跌破確認
    3. [打開 F.1] 動態 Vol 高點減碼 50%
    4. [新增] 贏家 trailing：浮盈 > 30% 改高點 -15% 出場（規則 6 修）
    5. [新增] 浮盈鎖利：浮盈 ≥ 35% 鎖 1/3 部位（PROFIT_CAP）
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
    UseInitStop(false, "是否使用固定初始停損"),
    Loss_Percent(15, "初始停損（百分比）"),
    UseBE(false, "是否啟用保本"),
    BE_TriggerPct(0.10, "Break-Even 門檻 (10%)"),
    StartTriggerPct1(0.50, "第一段停利啟動 (50%)"),
    TrailPct1(0.05, "第一段回吐幅度 (5%)"),
    StartTriggerPct2(0.70, "第二段停利啟動 (70%)"),
    TrailPct2(0.10, "第二段回吐幅度 (10%)"),
    N_Days(60, "時間停損觀察期（v4.1 30→60）"),
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
    Enable_Rule7(true, "規則7:波動率縮放加碼規模"),

    // === v4.1 新增參數 ===
    VolStop_CostMult(4.0, "成本錨 Vol 倍數（保本）"),
    VolStop_PeakMult(6.0, "高點錨 Vol 倍數（保獲利）"),
    Enable_VolPartExit(true, "是否啟用動態 Vol 高點減碼 (F.1)"),
    VolPartExit_KeepRatio(0.5, "減碼後保留比例"),
    Enable_RelStrength(true, "是否啟用相對強弱踢除"),
    RelStrength_KamaConfirm(true, "相對弱勢需同時跌破日 KAMA"),
    Enable_WinnerTrail(true, "是否啟用贏家 trailing（規則 6 修）"),
    Winner_ProfitThreshold(0.30, "贏家門檻浮盈 (30%)"),
    Winner_TrailPct(0.15, "贏家 trailing 幅度 (15%)"),
    Enable_ProfitCap(true, "是否啟用浮盈鎖利 1/3"),
    ProfitCap_Pct(0.35, "浮盈鎖利門檻 (35%)"),
    ProfitCap_KeepRatio(0.667, "鎖利後保留比例 (2/3)");

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
    IntraBarPersist PartExited1(false),
    IntraBarPersist PartExited2(false),
    IntraBarPersist VolPartExited(false),
    IntraBarPersist WinnerModeOn(false),       // v4.1 新增：贏家模式
    IntraBarPersist ProfitCapDone(false),      // v4.1 新增：鎖利完成
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
    StockRetFromEnt(0), IdxRetFromEnt(0),

    // v4.1 新增：雙錨停損用
    CostStopLine(0), PeakStopLine(0), ProfitPct(0);

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
       PartExited1 = false; PartExited2 = false; VolPartExited = false;
       WinnerModeOn = false; ProfitCapDone = false;   // v4.1 重置
       PeakSinceEntry = Close;
       MaxRunupPct = 0;
    end;
end;

{ ===== 2. 獲利加碼 (Pyramiding) ===== }
if EnablePyramid and filled > 0 and PyramidCount < Max_Pyramid_Times and PartExited1 = false then begin
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
    ProfitPct = (Close - filledAvgPrice) / filledAvgPrice;

    // v4.1 雙錨停損線
    CostStopLine = filledAvgPrice * (1 - Vol20 * VolStop_CostMult);
    PeakStopLine = PeakSinceEntry * (1 - Vol20 * VolStop_PeakMult);

    // 計算進場以來的個股與大盤漲幅
    if BarsFromEnt > 0 then begin
        StockRetFromEnt = (Close - Close[BarsFromEnt]) / Close[BarsFromEnt];
        IdxRetFromEnt = (IdxClose - IdxClose[BarsFromEnt]) / IdxClose[BarsFromEnt];
    end;

    { ----- 贏家模式標記：浮盈過 30% 切換為 trailing 防守 ----- }
    if Enable_WinnerTrail and WinnerModeOn = false and ProfitPct >= Winner_ProfitThreshold then begin
        WinnerModeOn = true;
    end;

    { ----- 浮盈鎖利 1/3（PROFIT_CAP）：浮盈 ≥ 35% 鎖 1/3 部位 ----- }
    if Enable_ProfitCap and ProfitCapDone = false and filled > 1
       and ProfitPct >= ProfitCap_Pct
    then begin
        SetPosition(Round(filled * ProfitCap_KeepRatio, 0), label:="鎖利1/3");
        ProfitCapDone = true;
    end else

    { ----- 贏家 trailing：高點回吐 15% 出場（取代雙錨防守，避免重複觸發） ----- }
    if WinnerModeOn and (PeakSinceEntry - Close) / PeakSinceEntry >= Winner_TrailPct then begin
        LastTradeReturn = ProfitPct;
        SetPosition(0, label:="贏家回吐");
    end else

    { ----- A) 動態 Vol 雙錨停損（v4.1 改）-----
       未進贏家模式才生效；用「成本錨 vs 高點錨」較高者當底線：
       - 早期沒漲：高點接近成本，由成本錨保護本金
       - 已經漲過：高點錨拉高，跌破才出 ----- }
    if Enable_Rule5 and WinnerModeOn = false
       and Close <= MaxList(CostStopLine, PeakStopLine)
    then begin
        LastTradeReturn = ProfitPct;
        SetPosition(0, label:="動態Vol停損");
    end else

    { ----- B) 原本初始停損 ----- }
    if UseInitStop and Close <= filledAvgPrice * (1 - Loss_Percent * 0.01) then begin
        LastTradeReturn = ProfitPct;
        SetPosition(0, label:="停損");
    end else

    { ----- C) 保本 ----- }
    if UseBE and MaxRunupPct >= BE_TriggerPct * 100 and Close <= filledAvgPrice then begin
        LastTradeReturn = ProfitPct;
        SetPosition(0, label:="保本");
    end else

    { ----- D.1) 規則6：時間上限且轉弱出場（贏家模式不適用） ----- }
    if Enable_Rule6 and WinnerModeOn = false
       and BarsFromEnt >= LimitDays and StockRetFromEnt < IdxRetFromEnt
    then begin
        LastTradeReturn = ProfitPct;
        SetPosition(0, label:="時間上限且轉弱出場");
    end else

    { ----- D.2) 相對強弱淘汰（v4.1 改：60 天 + 日 KAMA 確認） ----- }
    if Enable_RelStrength and WinnerModeOn = false
       and BarsFromEnt >= N_Days and StockRetFromEnt < IdxRetFromEnt
       and (RelStrength_KamaConfirm = false or Close < KAMA)
    then begin
        LastTradeReturn = ProfitPct;
        SetPosition(0, label:="相對弱勢踢除");
    end else

    { ----- E) KAMA 大賺出場 ----- }
    if Close >= filledAvgPrice * (1 + BigWinPct * 0.01) and c cross Below kama_W and time >=1300 then begin
        LastTradeReturn = ProfitPct;
        SetPosition(0, label:="KAMA大賺出場");
    end else

    { ----- G) VIX + 週線壓力出場（底線防護，贏家也適用） ----- }
    if vix(VixLookback) = 1 and W_Trend = -1 then begin
        LastTradeReturn = ProfitPct;
        SetPosition(0, label:="VIX+週壓力");
        print(file("[StrategyName].log"),DateToString(date),"★【出場】VIX+週壓力");
    end;

    { ================= 部分出場（減碼）邏輯 ================= }

    { ----- F.1) 動態 Vol 高點減碼 50%（v4.1 打開）-----
       未進贏家模式時，從高點回吐 Vol*VolStop_PeakMult 先鎖一半獲利 ----- }
    if Enable_VolPartExit and WinnerModeOn = false and VolPartExited = false
       and filled > 1 and MaxRunupPct >= 10
       and Close <= PeakSinceEntry * (1 - Vol20 * VolStop_PeakMult)
    then begin
        SetPosition(Round(filled * VolPartExit_KeepRatio, 0), label:="動態Vol減碼50%");
        VolPartExited = true;
    end;

end;
