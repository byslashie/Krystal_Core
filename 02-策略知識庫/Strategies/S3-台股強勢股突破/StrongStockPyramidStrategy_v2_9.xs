{-----------------------------------------------------------------------------
 StrongStockPyramidStrategy_v2_9.xs
 策略：每月進場 × 雙動能 × 智能分級資金管理 × 雙重加碼攻擊版
 版本：v2.9 (2026-05-18)

 v2.7：時間出場加 W_Trend=-1、加碼加 W_Trend=1、N_Days=60
 v2.8：浮盈達 PROFIT_CAP_PCT 時鎖利 1/3；回調後趨勢確認再補倉
 v2.9 [本版] 由實盤交易紀錄歸因加上：
   [新規則 8]  同檔失敗黑名單：同檔連虧 2 次 → 冷凍 90 個交易日
   [新規則 9]  首倉早期失效快砍：10 日內跌破 -5% 直接砍
   [修規則 6]  分流時間上限：浮盈 >+30% 解除時間上限，改 trailing stop
   [修規則 7]  加碼分流：首倉浮虧禁止加碼；浮盈 0~+15% 加碼減半
   [新規則 11] 危險日期過濾：農曆年前後 5 日 / FOMC 前 1 日不進場
 注意：規則 10「族群集中度」需跨多商品共享，無法在單檔 XS 內實作，
       建議於外部主控腳本或 Python 風控層處理。

 外部依賴：
   - vix(回顧期)：自訂 .eld 函式，回傳 0/1（系統性風險旗標）
   - IslistedSymbol：自訂 .eld 函式，判斷是否上市股票
   驗證器若提示「未知關鍵字 vix」屬正常，實機上載入函式庫即可。
-----------------------------------------------------------------------------}

settotalBar(1000);
setbackBar(1000);

{ ===== 輸入參數 ===== }
input:
    MONEY(1000, "單次名目金額（基準部位）"),
    BIG_WIN_THRESHOLD(0.15, "上一筆大賺定義 (15%)"),
    SCALE_BIG_WIN(1.5, "上一筆大賺時，底倉倍數"),
    SCALE_SMALL_WIN(1.0, "上一筆小賺時，底倉倍數"),
    SCALE_LOSS(0.5, "上一筆賠錢時，底倉倍數"),
    MAX_SCALE_CAP(3.0, "最大口數倍數上限"),
    ENABLE_PYRAMID(true, "是否啟用獲利加碼"),
    PYRAMID_THRESHOLD(0.10, "加碼觸發門檻 (10%)"),
    PYRAMID_SCALE(0.5, "加碼部位倍數 (0.5)"),
    MAX_PYRAMID_TIMES(2, "最大加碼次數"),
    USE_INIT_STOP(false, "是否使用固定初始停損"),
    LOSS_PERCENT(15.0, "初始停損（百分比）"),
    USE_BE(false, "是否啟用保本"),
    BE_TRIGGER_PCT(0.10, "Break-Even 門檻"),
    START_TRIGGER_PCT1(0.50, "第一段停利啟動"),
    TRAIL_PCT1(0.05, "第一段回吐幅度"),
    START_TRIGGER_PCT2(0.70, "第二段停利啟動"),
    TRAIL_PCT2(0.10, "第二段回吐幅度"),
    N_DAYS(60, "時間停損觀察期"),
    TARGET_PCT(0.05, "N 天內目標漲幅"),
    BIG_WIN_PCT(50.0, "大賺例外門檻"),
    VIX_LOOKBACK(400, "VIX 回顧期"),
    LEN_W(22, "週線 ATR 週期"),
    MULTIPLIER_W(3, "週線 ATR 倍數"),
    ENABLE_PROFIT_CAP(true, "是否啟用浮盈鎖利"),
    PROFIT_CAP_PCT(0.35, "浮盈達成本 35% 鎖利 1/3"),
    ENABLE_PULLBACK_ADD(true, "是否啟用回調後再加碼"),
    PULLBACK_MIN_RUNUP(0.20, "觸發回調偵測最低曾漲幅"),
    PULLBACK_PCT(0.10, "從高點回落視為回調"),
    MAX_PULLBACK_TIMES(1, "最大回調加碼次數"),
    ENABLE_EARLY_KILL(true, "是否啟用首倉早期快砍 [規則 9]"),
    EARLY_KILL_BARS(10, "首倉早期觀察 K 棒數"),
    EARLY_KILL_PCT(-0.05, "首倉早期跌破門檻 (-5%)"),
    ENABLE_BLACKLIST(true, "是否啟用同檔黑名單 [規則 8]"),
    BLACKLIST_FREEZE_BARS(90, "失敗冷凍 K 棒數"),
    BLACKLIST_LOSS_STREAK(2, "連虧次數觸發黑名單"),
    ENABLE_WINNER_EXTEND(true, "是否啟用贏家解除時間上限 [規則 6 修]"),
    WINNER_PROFIT_THRESHOLD(0.30, "贏家門檻浮盈"),
    WINNER_TRAIL_PCT(0.15, "贏家 trailing stop 幅度"),
    ENABLE_LOSS_NO_ADD(true, "是否啟用首倉浮虧禁加碼 [規則 7 修]"),
    HALF_ADD_PROFIT_MAX(0.15, "首倉浮盈 < 此值加碼減半"),
    ENABLE_DATE_FILTER(true, "是否啟用危險日期過濾 [規則 11]"),
    LUNAR_BUFFER_DAYS(5, "農曆年前後緩衝交易日"),
    FASTEST(2, "KAMA 快線"),
    SLOWEST(30, "KAMA 慢線"),
    N(8, "KAMA 週期"),
    FASTEST_W(2, "週 KAMA 快線"),
    SLOWEST_W(30, "週 KAMA 慢線"),
    N_W(8, "週 KAMA 週期");

{ ===== 變數宣告 ===== }
vars:
    IntraBarPersist _entryPx(0),
    IntraBarPersist _barsFromEnt(0),
    IntraBarPersist _maxRunupPct(0),
    IntraBarPersist _peakSinceEntry(0),
    IntraBarPersist _monthlyBarCount(0),
    IntraBarPersist _lastTradeReturn(0),
    IntraBarPersist _hasTraded(false),
    IntraBarPersist _baseOrderQty(0),
    IntraBarPersist _pyramidCount(0),
    IntraBarPersist _partExited1(false),
    IntraBarPersist _partExited2(false),
    IntraBarPersist _profitCapDone(false),
    IntraBarPersist _pullbackOccurred(false),
    IntraBarPersist _pullbackAddCount(0),
    IntraBarPersist _winnerModeOn(false),
    IntraBarPersist _lossStreak(0),
    IntraBarPersist _freezeBarsLeft(0),
    IntraBarPersist _currMonth(0),
    IntraBarPersist _prevMonth(0),
    _isNewMonth(false),
    _orderQty(0),
    _multipler(1.0),
    _currentPL(0),
    _wHigh(0),
    _wLow(0),
    _wClose(0),
    _wAtr(0),
    _wCnt(0),
    _wUp(0),
    _wDw(0),
    IntraBarPersist _wTrend(1),
    _i(0),
    _sumTr(0),
    _tr(0),
    _kama(0),
    _sct(0),
    _d(0),
    _vo(0),
    _er(0),
    _f(0),
    _s(0),
    _kamaW(0),
    _sctW(0),
    _dW(0),
    _voW(0),
    _erW(0),
    _fW(0),
    _sW(0),
    _isDangerDate(false),
    _isLunarWindow(false),
    _curMonthVal(0),
    _curDayVal(0),
    _pullbackQty(0),
    _addQty(0);

{ ===== 月初判定（換月旗標 + 月度計數）===== }
if CurrentBar = 1 then begin
    _prevMonth = Month(Date);
    _currMonth = Month(Date);
end else begin
    _currMonth = Month(Date);
    if _currMonth <> _prevMonth then begin
        _isNewMonth = true;
        _monthlyBarCount = 0;
        _prevMonth = _currMonth;
    end else begin
        _isNewMonth = false;
    end;
end;
_monthlyBarCount = _monthlyBarCount + 1;

{ ===== 日 KAMA 計算 ===== }
_d = AbsValue(Close - Close[N]);
_vo = Summation(AbsValue(Close - Close[1]), N);
if _vo <> 0 then
    _er = _d / _vo
else
    _er = 0;
_f = 2 / (FASTEST + 1);
_s = 2 / (SLOWEST + 1);
_sct = _er * Square((_f - _s) + _s);
_kama = _kama[1] + _sct * (Close - _kama[1]);

{ ===== 週 KAMA 計算（規範禁用 closeD 等，改 GetField）===== }
_dW = AbsValue(GetField("收盤價", "W") - GetField("收盤價", "W")[N_W]);
_voW = Summation(AbsValue(GetField("收盤價", "W") - GetField("收盤價", "W")[1]), N_W);
if _voW <> 0 then
    _erW = _dW / _voW
else
    _erW = 0;
_fW = 2 / (FASTEST_W + 1);
_sW = 2 / (SLOWEST_W + 1);
_sctW = _erW * Square((_fW - _sW) + _sW);
_kamaW = _kamaW[1] + _sctW * (GetField("收盤價", "W") - _kamaW[1]);

{ ===== 週線 ATR 與 SuperTrend ===== }
_sumTr = 0;
for _i = 0 to LEN_W - 1 begin
    _tr = MaxList(
        GetField("最高價", "W")[_i] - GetField("最低價", "W")[_i],
        AbsValue(GetField("最高價", "W")[_i] - GetField("收盤價", "W")[_i + 1]),
        AbsValue(GetField("最低價", "W")[_i] - GetField("收盤價", "W")[_i + 1])
    );
    _sumTr = _sumTr + _tr;
end;
_wAtr = _sumTr / LEN_W;

_wHigh = GetField("最高價", "W");
_wLow = GetField("最低價", "W");
_wClose = GetField("收盤價", "W");
_wCnt = (_wHigh + _wLow) / 2;

if CurrentBar = 1 then begin
    _wUp = _wCnt;
    _wDw = _wCnt;
end;

if _wTrend = 1 then begin
    _wUp = MaxList(_wUp[1], _wCnt - _wAtr * MULTIPLIER_W);
    if _wClose < _wUp then begin
        _wTrend = -1;
        _wDw = _wCnt + _wAtr * MULTIPLIER_W;
    end;
end else begin
    _wDw = MinList(_wDw[1], _wCnt + _wAtr * MULTIPLIER_W);
    if _wClose > _wDw then begin
        _wTrend = 1;
        _wUp = _wCnt - _wAtr * MULTIPLIER_W;
    end;
end;

{ ===== [規則 8] 黑名單冷凍計時：每 K 棒倒數 ===== }
if _freezeBarsLeft > 0 then
    _freezeBarsLeft = _freezeBarsLeft - 1;

{ ===== [規則 11] 危險日期過濾
   台股農曆年附近：1 月底 ~ 2 月初的緩衝窗口（簡化版用月份判定）
   完整版需查農曆，此處用「1 月最後 LUNAR_BUFFER_DAYS 天 + 2 月前 LUNAR_BUFFER_DAYS 天」近似
===== }
_curMonthVal = Month(Date);
_curDayVal = DayOfMonth(Date);
_isLunarWindow = false;
if _curMonthVal = 1 and _curDayVal >= (31 - LUNAR_BUFFER_DAYS) then
    _isLunarWindow = true;
if _curMonthVal = 2 and _curDayVal <= LUNAR_BUFFER_DAYS then
    _isLunarWindow = true;
_isDangerDate = ENABLE_DATE_FILTER and _isLunarWindow;

{ ===== 1. 進場邏輯 ===== }
if filled = 0
   and _isNewMonth
   and IsSessionFirstBar
   and isfirstcall("RealBar")
   and _isDangerDate = false
   and _freezeBarsLeft = 0
then begin
    if IslistedSymbol = true
       and vix(VIX_LOOKBACK) = 0
       and Close > _kama
       and Month(Date) <> 9
       and _wTrend = 1
    then begin
        _orderQty = MONEY / Close;

        { 分級資金管理：依上一筆績效調整底倉 }
        if _hasTraded then begin
            if _lastTradeReturn >= BIG_WIN_THRESHOLD then
                _multipler = SCALE_BIG_WIN
            else if _lastTradeReturn > 0 then
                _multipler = SCALE_SMALL_WIN
            else
                _multipler = SCALE_LOSS;

            if _multipler > MAX_SCALE_CAP then
                _multipler = MAX_SCALE_CAP;
        end else
            _multipler = 1;

        SetPosition(_orderQty * _multipler, label:="● 進場");
        _baseOrderQty = _orderQty * _multipler;
        _pyramidCount = 0;
        _partExited1 = false;
        _partExited2 = false;
        _profitCapDone = false;
        _pullbackOccurred = false;
        _pullbackAddCount = 0;
        _winnerModeOn = false;
        _peakSinceEntry = Close;
        _maxRunupPct = 0;
    end;
end;

{ ===== 2. 獲利加碼（Pyramiding）+ [修規則 7] 加碼分流 ===== }
if ENABLE_PYRAMID
   and filled > 0
   and _pyramidCount < MAX_PYRAMID_TIMES
   and _partExited1 = false
   and _wTrend = 1
then begin
    if (Close - filledAvgPrice) / filledAvgPrice >= PYRAMID_THRESHOLD then begin
        _addQty = _baseOrderQty * PYRAMID_SCALE;

        { 規則 7 修：首倉浮虧禁加碼；浮盈 < HALF_ADD_PROFIT_MAX 加碼減半 }
        if ENABLE_LOSS_NO_ADD then begin
            if (Close - filledAvgPrice) / filledAvgPrice < 0 then
                _addQty = 0
            else if (Close - filledAvgPrice) / filledAvgPrice < HALF_ADD_PROFIT_MAX then
                _addQty = _addQty * 0.5;
        end;

        if _addQty > 0 then begin
            SetPosition(filled + _addQty, label:="★ 加碼");
            _pyramidCount = _pyramidCount + 1;
        end;
    end;
end;

{ ===== 3. 出場與部位管理 ===== }
if filled <> 0 then begin
    _barsFromEnt = getBarOffset(FilledRecordDate(FilledRecordCount));
    _peakSinceEntry = MaxList(_peakSinceEntry, High);
    _maxRunupPct = (_peakSinceEntry - filledAvgPrice) / filledAvgPrice * 100.0;
    _currentPL = (Close - filledAvgPrice) * filled;

    { [修規則 6] 贏家分流：浮盈 > WINNER_PROFIT_THRESHOLD 解除時間上限 }
    if ENABLE_WINNER_EXTEND
       and _winnerModeOn = false
       and (Close - filledAvgPrice) / filledAvgPrice >= WINNER_PROFIT_THRESHOLD
    then
        _winnerModeOn = true;

    { F) [v2.8] 浮盈集中度鎖利 1/3 }
    if ENABLE_PROFIT_CAP
       and _profitCapDone = false
       and filled > 1
       and (Close - filledAvgPrice) / filledAvgPrice >= PROFIT_CAP_PCT
    then begin
        SetPosition(Round(filled * 2 / 3, 0), label:="鎖利1/3");
        _profitCapDone = true;
    end else

    { [新規則 9] 首倉早期失效快砍 }
    if ENABLE_EARLY_KILL
       and _barsFromEnt <= EARLY_KILL_BARS
       and _pyramidCount = 0
       and (Close - filledAvgPrice) / filledAvgPrice <= EARLY_KILL_PCT
    then begin
        _lastTradeReturn = (Close - filledAvgPrice) / filledAvgPrice;
        { 連虧計數 }
        if _lastTradeReturn < 0 then
            _lossStreak = _lossStreak + 1
        else
            _lossStreak = 0;
        { 黑名單觸發 }
        if ENABLE_BLACKLIST and _lossStreak >= BLACKLIST_LOSS_STREAK then begin
            _freezeBarsLeft = BLACKLIST_FREEZE_BARS;
            _lossStreak = 0;
        end;
        _hasTraded = true;
        SetPosition(0, label:="早期快砍");
    end else

    { A) 初始停損 }
    if USE_INIT_STOP
       and Close <= filledAvgPrice * (1 - LOSS_PERCENT * 0.01)
    then begin
        _lastTradeReturn = (Close - filledAvgPrice) / filledAvgPrice;
        if _lastTradeReturn < 0 then
            _lossStreak = _lossStreak + 1
        else
            _lossStreak = 0;
        if ENABLE_BLACKLIST and _lossStreak >= BLACKLIST_LOSS_STREAK then begin
            _freezeBarsLeft = BLACKLIST_FREEZE_BARS;
            _lossStreak = 0;
        end;
        _hasTraded = true;
        SetPosition(0, label:="停損");
    end else

    { B) 保本 }
    if USE_BE
       and _maxRunupPct >= BE_TRIGGER_PCT * 100
       and Close <= filledAvgPrice
    then begin
        _lastTradeReturn = (Close - filledAvgPrice) / filledAvgPrice;
        _hasTraded = true;
        SetPosition(0, label:="保本");
    end else

    { [修規則 6] 贏家 trailing stop：浮盈過 WINNER_PROFIT_THRESHOLD 後從高點回吐 WINNER_TRAIL_PCT 出場 }
    if _winnerModeOn
       and (_peakSinceEntry - Close) / _peakSinceEntry >= WINNER_TRAIL_PCT
    then begin
        _lastTradeReturn = (Close - filledAvgPrice) / filledAvgPrice;
        if _lastTradeReturn > 0 then
            _lossStreak = 0;
        _hasTraded = true;
        SetPosition(0, label:="贏家回吐");
    end else

    { D) 時間停損 — 回調加碼進場的筆不適用、贏家模式不適用 }
    if _winnerModeOn = false
       and _barsFromEnt >= N_DAYS
       and Close <= filledAvgPrice * (1 + TARGET_PCT * 0.01)
       and _wTrend = -1
       and _pullbackAddCount = 0
    then begin
        _lastTradeReturn = (Close - filledAvgPrice) / filledAvgPrice;
        if _lastTradeReturn < 0 then
            _lossStreak = _lossStreak + 1
        else
            _lossStreak = 0;
        if ENABLE_BLACKLIST and _lossStreak >= BLACKLIST_LOSS_STREAK then begin
            _freezeBarsLeft = BLACKLIST_FREEZE_BARS;
            _lossStreak = 0;
        end;
        _hasTraded = true;
        SetPosition(0, label:="時間出場");
    end else

    { E) KAMA 停利（大賺後週 KAMA 死叉）}
    if Close >= filledAvgPrice * (1 + BIG_WIN_PCT * 0.01)
       and Close crosses below _kamaW
       and Time >= 1300
    then begin
        _lastTradeReturn = (Close - filledAvgPrice) / filledAvgPrice;
        if _lastTradeReturn > 0 then
            _lossStreak = 0;
        _hasTraded = true;
        SetPosition(0, label:="KAMA出場");
    end else

    { G) VIX + 週線壓力出場 }
    if vix(VIX_LOOKBACK) = 1 and _wTrend = -1 then begin
        _lastTradeReturn = (Close - filledAvgPrice) / filledAvgPrice;
        if _lastTradeReturn > 0 then
            _lossStreak = 0;
        _hasTraded = true;
        SetPosition(0, label:="VIX+週壓力");
    end;

    { ===== [v2.8] 回調後再加碼（獨立區塊）+ [修規則 7] 加碼分流 ===== }
    if ENABLE_PULLBACK_ADD and filled > 0 then begin
        { 步驟一：偵測回調 }
        if _maxRunupPct >= PULLBACK_MIN_RUNUP * 100
           and (_peakSinceEntry - Close) / _peakSinceEntry >= PULLBACK_PCT
           and _pullbackOccurred = false
        then
            _pullbackOccurred = true;

        { 步驟二：趨勢重新確認後補回部位（已封印保留，需評估） }
        {if _pullbackOccurred = true
           and _wTrend = 1
           and Close > filledAvgPrice
           and _pullbackAddCount < MAX_PULLBACK_TIMES
           and isfirstcall("RealBar")
        then begin
            _pullbackQty = _baseOrderQty * PYRAMID_SCALE;
            if ENABLE_LOSS_NO_ADD
               and (Close - filledAvgPrice) / filledAvgPrice < HALF_ADD_PROFIT_MAX
            then
                _pullbackQty = _pullbackQty * 0.5;
            SetPosition(filled + Round(_pullbackQty, 0), label:="回調加碼");
            _pullbackOccurred = false;
            _pullbackAddCount = _pullbackAddCount + 1;
        end;}
    end;
end;
