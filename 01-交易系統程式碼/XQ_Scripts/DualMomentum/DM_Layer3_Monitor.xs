// ============================================================
// [SKILL 3] 持倉監控 / 出場警示
// 檔名：DM_Layer3_Monitor
// 用途：月中監控現有持股，動能轉負時發出警示
//       不是每天換股，是「提前示警」用
//
// 使用方式：
//   候選池 = 目前持有的持股清單
//   每週跑一次，或設 XS 盤後自動執行
//   出現 EXIT 訊號 → 下月調整時優先處理
// ============================================================

Var:
  mom3(0), mom6(0), mom12(0), score(0);
  weakSignal(0), exitSignal(0);

mom3  := RateOfChange(C, 63);
mom6  := RateOfChange(C, 126);
mom12 := RateOfChange(C, 252);
score := (mom3 + mom6 + mom12) / 3;

// 出場訊號（任一週期轉負）
If (mom3 < 0) OR (mom6 < 0) OR (mom12 < 0) Then
  exitSignal := 1
Else
  exitSignal := 0;

// 弱化警示（分數低於閾值，但尚未轉負）
// 分數低於 20% 代表動能正在衰減
If (score > 0) AND (score < 20) Then
  weakSignal := 1
Else
  weakSignal := 0;

// 篩出需要注意的持股
If (exitSignal = 1) OR (weakSignal = 1) Then ret := 1;

// 輸出欄位
OutputField1(score,       "動能分數");
OutputField2(exitSignal,  "出場訊號(1=是)");
OutputField3(weakSignal,  "弱化警示(1=是)");
OutputField4(mom3,        "近3月%");
OutputField5(mom6,        "近6月%");
OutputField6(mom12,       "近12月%");
OutputField7(RateOfChange(C, 5),  "近5日%");
OutputField8(RateOfChange(C, 20), "近月%");
