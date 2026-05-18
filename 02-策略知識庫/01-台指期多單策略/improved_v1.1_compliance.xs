{
  【台指期多單策略 - XScript 改進版本 v1.1】
  日期：2026-05-15
  改進內容：合規性修復 + 變數規範化 + 多單邏輯確認

  新增功能：
    1. 時段限制：日盤 08:45-13:25 進場，13:25-15:00 禁止
    2. 每日進場次數限制：最多 2 次
    3. 週五禁止進場
    4. 變數規範化：camelCase 命名
    5. 邊界檢查：數據長度驗證

  下個版本（v2.0）計畫：
    1. ATR 波動分化（趨勢 vs 盤整）
    2. Trailing Stop 實現
    3. 績效日誌記錄
}

setbarBack(100);
settotalBar(1000);

{
  ============================================================================
  【參數宣告】 (Inputs) - 集中至頂部
  ============================================================================
}
input: _EXIT_TIME(134000, "離場時間");
input: _inputBBLength(20, "布林通道天數");
input: _inputBBRange(2, "上下寬度");
input: _inputMALength(200, "MA天期");
input: _inputLossPoint(200, "停損點");
input: _inputForeignPeriod(20, "外資觀察天數");
input: _inputVIXBBLength(100, "VIX布林長度");

{
  ============================================================================
  【全域變數與常數宣告】 (Vars) - 集中至頂部，統一使用 vars
  ============================================================================
}
vars:
    // 常數設定
    _ENTRY_TIME_START(084500),      // 進場時間開始：08:45
    _ENTRY_TIME_END(132500),        // 進場時間結束：13:25
    _FORBIDDEN_START(132500),       // 禁止時段開始：13:25
    _FORBIDDEN_END(150000),         // 禁止時段結束：15:00
    _MAX_ENTRIES_PER_DAY(2),        // 每日最多進場次數
    _VIX_THRESHOLD(17),             // VIX 高恐慌閾值
    
    // %B 指標相關
    _bbUpper(0),                    // 布林上軌
    _bbLower(0),                    // 布林下軌
    _bbPercent(0),                  // %B 數值
    _bbMA(0),                       // %B 移動平均

    // VIX 相關
    _vixUpper(0),                   // VIX 上軌
    _vixLower(0),                   // VIX 下軌
    _vixValue(0),                   // VIX 當前值

    // 委買委賣相關
    _committeeNetValue(0),          // 委賣成筆 - 委買成筆
    _committeePrev1(0),             // 前1根委成數
    _committeePrev2(0),             // 前2根委成數
    _committeePrev3(0),             // 前3根委成數

    // 外資相關
    _foreignBuyDaysCount(0),        // 外資買超天數計數
    _foreignBuyRatio(0),            // 外資買超比例

    // 進場條件相關
    _isDowntrendBelowEMA(false),    // 大盤在60EMA下方
    _isHighVIX(false),              // VIX > 17
    _isInvertedSpread(false),       // 逆價差
    _isHighVolatileDown(false),     // 高波動下跌K
    _isAboveAvgVolume(false),       // 成交量 > 5根均
    _isEntryConditionMet(false),    // 進場條件已滿足

    // 出場條件相關
    _isBBHighPositive(false),       // %B 高位 + 正價差
    _isPositiveSpread(false),       // 正價差

    // 時段限制相關
    _entryCountToday(0),            // 今日進場次數
    _lastEntryDate(0),              // 上次進場日期
    _isWithinEntryTime(false),      // 是否在允許進場時段
    _isForbiddenTime(false),        // 是否在禁止時段
    _isFriday(false);               // 是否為週五

{
  ============================================================================
  【主邏輯開始】
  ============================================================================
}

// 邊界檢查：確保資料長度足夠
if CurrentBar < _inputBBLength then begin
    return;  // 資料不足，直接返回
end;

{ --- 第一部分：%B 布林通道 --- }
_bbUpper = bollingerband(Close, _inputBBLength, _inputBBRange);
_bbLower = bollingerband(Close, _inputBBLength, -1 * _inputBBRange);

if _bbUpper - _bbLower = 0 then
    _bbPercent = 0
else
    _bbPercent = (Close - _bbLower) * 100 / (_bbUpper - _bbLower);

_bbMA = average(_bbPercent, _inputMALength);

{ --- 第二部分：外資淨買賣 --- }
_foreignBuyDaysCount = countif(getsymbolfield("TSE.TW", "外資買賣超金額", "D")[1] > 0, _inputForeignPeriod);
_foreignBuyRatio = _foreignBuyDaysCount / _inputForeignPeriod;

{ --- 第三部分：VIX 恐慌指數 --- }
_vixUpper = bollingerBand(getsymbolField("VIX.TF", "收盤價", "60"), _inputVIXBBLength, 1.6);
_vixLower = bollingerBand(getsymbolField("VIX.TF", "收盤價", "60"), _inputVIXBBLength, -1.6);
_vixValue = getsymbolField("VIX.TF", "收盤價", "5");

{ --- 第四部分：大盤累委買賣成筆 --- }
if CurrentBar >= 3 then begin
    _committeeNetValue = GetField("累賣成筆", "D") - GetField("累買成筆", "D");
    _committeePrev1 = _committeeNetValue[1];
    _committeePrev2 = _committeeNetValue[2];
    _committeePrev3 = _committeeNetValue[3];
end;

{ --- 進場條件判斷 --- }
_isDowntrendBelowEMA = getsymbolField("TSE.TW", "收盤價", "D") < EMA(getsymbolField("TSE.TW", "收盤價", "D"), 60) * 0.997;
_isHighVIX = _vixValue > _VIX_THRESHOLD;
_isInvertedSpread = (Close - getsymbolField("TSE.TW", "收盤價", "D")) < 0;
_isHighVolatileDown = Close < Open and ((High - Low) / Close) * 100 > 0.13;
_isAboveAvgVolume = Volume > average(Volume, 5);

_isEntryConditionMet = _isDowntrendBelowEMA and _isHighVIX and _isInvertedSpread
                       and _isHighVolatileDown and _isAboveAvgVolume;

{ --- 時段限制判斷 --- }
_isWithinEntryTime = CurrentTime >= _ENTRY_TIME_START and CurrentTime < _ENTRY_TIME_END;
_isForbiddenTime = CurrentTime >= _FORBIDDEN_START and CurrentTime < _FORBIDDEN_END;
_isFriday = DayOfWeek(Date) = 5;

if CurrentDate <> _lastEntryDate then begin
    _entryCountToday = 0;  // 新的一天，計數器重置
end;

{
  ============================================================================
  【進場邏輯】
  ============================================================================
}
if position = 0 and filled = 0 and getfield("Volume") > 0 then begin
    if _isEntryConditionMet
       and _isWithinEntryTime
       and not _isForbiddenTime
       and not _isFriday
       and _entryCountToday < _MAX_ENTRIES_PER_DAY then begin

        SetPosition(1, addSpread(Close, 0), label:="多進場");
        _entryCountToday = _entryCountToday + 1;
        _lastEntryDate = CurrentDate;

        print(file("[StrategyName][Symbol][StartTime].log"),
              DateToString(Date), TimeToString(Time),
              "★【進場】多單進場價:", NumToStr(Close, 2),
              " 今日進場次數:", NumToStr(_entryCountToday, 0));
    end;
end;

{
  ============================================================================
  【出場邏輯】
  ============================================================================
}
if position <> 0 and filled <> 0 then begin

    // 出場方式1：%B高位反轉 + 正價差 (多單獲利了結)
    _isBBHighPositive = _bbPercent > 72 and _bbPercent < 120;
    _isPositiveSpread = (Close - getsymbolField("TSE.TW", "收盤價", "D")) > 0;

    if _isBBHighPositive and _isPositiveSpread then begin
        SetPosition(0, addspread(Close, 0), label:="%B高+正價差");
        print(file("[StrategyName][Symbol][StartTime].log"),
              DateToString(Date), TimeToString(Time),
              "★【出場】%B高位反轉，多單獲利出場價:", NumToStr(Close, 2));
    end;

    // 出場方式2：尾盤強制平倉
    if (CurrentDate = FilledEntryDate and CurrentTime >= _EXIT_TIME)
       or (CurrentDate > FilledEntryDate) then begin
        SetPosition(0, addspread(Close, 0), label:="尾盤平倉");
        print(file("[StrategyName][Symbol][StartTime].log"),
              DateToString(Date), TimeToString(Time),
              "★【出場】尾盤強制平倉，出場價:", NumToStr(Close, 2));
    end;

    // 出場方式3：停損 (多單價格往下為虧損)
    if _inputLossPoint > 0 and Close <= FilledAvgPrice - _inputLossPoint then begin
        SetPosition(0, label:="停損");
        print(file("[StrategyName][Symbol][StartTime].log"),
              DateToString(Date), TimeToString(Time),
              "★【出場】多單停損觸發，出場價:", NumToStr(Close, 2));
    end;

end;
